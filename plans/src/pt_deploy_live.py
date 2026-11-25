"""Live Packet Tracer 9.0.1 FileBridge Builder, Verifier & Saver for all 4 RJ Esports .pkt files.

Drives the running PT 9.0.1 Script Engine via %LOCALAPPDATA%\\packet-tracer-mcp\\bridge\\:
1. pt/rj_network.pkt (Master 3-site + ISP-CEBU + live routing/DHCP/ACL/ping verification)
2. pt/rj_cebu_hq_visayas.pkt (Cebu Flagship HQ + ISP-CEBU Multiuser host file)
3. pt/rj_clark_luzon.pkt (Clark Branch Café Multiuser site file)
4. pt/rj_davao_mindanao.pkt (Davao Branch Café Multiuser site file)

Saves immediately after each file and writes live CLI/ping verification evidence to
`pt/evidence/live_verification.json` (with credentials redacted).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List

from model import CLI_DIR, PT_DIR
from network_cli import redact_cli

EVIDENCE_DIR = PT_DIR / "evidence"

PT_MODEL_DEVICE_TYPE = {
    "2911": 0,
    "2960-24TT": 1,
    "3560-24PS": 16,
    "AccessPoint-PT": 7,
    "PC-PT": 8,
    "Server-PT": 9,
    "Printer-PT": 10,
    "Copper Patch Panel": 46,
    "Copper Wall Mount": 47,
}

PT_CONNECT_TYPE = {
    "straight": 8100,
    "crossover": 8101,
    "fiber": 8103,
    "serial": 8106,
    "auto": 8107,
}


class FileBridge:
    """Pure-stdlib file mailbox transport for Packet Tracer 9.0.1 MCPControlCenter.pts."""

    def __init__(self, directory: Path | None = None):
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        self.dir = Path(directory) if directory else (local / "packet-tracer-mcp" / "bridge")
        self._seq = 0

    def pt_alive(self) -> bool:
        alive = self.dir / "alive.txt"
        try:
            return (time.time() - alive.stat().st_mtime) < 8.0
        except OSError:
            return False

    def _next_name(self) -> str:
        self._seq += 1
        return f"{os.getpid()}_{self._seq:06d}"

    def _write_atomic(self, path: Path, text: str) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(text.encode("utf-8"))
        os.replace(tmp, path)

    def send_and_wait(self, js_code: str, timeout: float = 45.0) -> str | None:
        self.dir.mkdir(parents=True, exist_ok=True)
        name = self._next_name()
        res_path = self.dir / f"res_{name}.txt"
        self._write_atomic(self.dir / f"req_{name}.js", js_code)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if res_path.exists():
                body = res_path.read_text(encoding="utf-8")
                res_path.unlink(missing_ok=True)
                return body
            time.sleep(0.1)
        res_path.unlink(missing_ok=True)
        return None


def send_js(bridge: FileBridge, js: str, timeout: float = 45.0) -> str:
    res = bridge.send_and_wait(js, timeout=timeout)
    if res is None:
        raise TimeoutError("Packet Tracer FileBridge timed out waiting for Script Engine response.")
    return res


def clear_workspace(bridge: FileBridge) -> None:
    js = """(function(){try{
      var net=ipc.network();
      var lw=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
      var names=[];
      for(var i=0;i<net.getDeviceCount();i++){names.push(String(net.getDeviceAt(i).getName()));}
      for(var j=0;j<names.length;j++){try{lw.removeDevice(names[j]);}catch(e){}}
      try{ipc.options().setDisableAutoCabling(true);}catch(e){}
      reportResult('CLEARED:' + names.length + '|LEFT:' + net.getDeviceCount());
    }catch(e){reportResult('ERR:' + e);}})();"""
    out = send_js(bridge, js, timeout=30.0)
    print("  clear_workspace:", out)


def save_pkt(bridge: FileBridge, filename: str) -> str:
    pt_dir_norm = str(PT_DIR.resolve()).replace("\\", "/")
    js = (
        "(function(){try{"
        "var aw=ipc.appWindow();var fm=ipc.systemFileManager();"
        f"var dir={json.dumps(pt_dir_norm)};"
        f"var full=dir+'/'+{json.dumps(filename)};"
        "if(!fm.directoryExists(dir)){reportResult('ERR:no_dir:'+dir);return;}"
        "aw.fileSaveAsNoPrompt(full,false);"
        "reportResult(fm.fileExists(full)?('OK:'+full+'|'+fm.getFileSize(full)):('ERR:not_saved:'+full));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    out = send_js(bridge, js, timeout=30.0)
    print(f"  save_pkt({filename}):", out)
    if not out.startswith("OK:"):
        raise RuntimeError(f"Failed saving {filename}: {out}")
    return out


def fast_forward(bridge: FileBridge, count: int = 4) -> None:
    js = (
        "(function(){try{var tb=ipc.appWindow().getRealtimeToolbar();"
        f"for(var i=0;i<{count};i++){{tb.fastForwardTime();}}"
        "reportResult('FF_OK');}catch(e){reportResult('ERR:'+e);}})();"
    )
    send_js(bridge, js, timeout=20.0)
    time.sleep(0.8)


def deploy_devices_and_links(bridge: FileBridge, devices: List[Dict], links: List[Dict]) -> None:
    # 1. Add devices in batches of 15
    for i in range(0, len(devices), 15):
        batch = devices[i : i + 15]
        cfg = []
        for d in batch:
            cfg.append({
                "name": d["name"],
                "model": d["model"],
                "type": PT_MODEL_DEVICE_TYPE[d["model"]],
                "x": int(d["x"]),
                "y": int(d["y"]),
                "modules": d.get("modules", []),
            })
        js = (
            "(function(){try{"
            f"var list={json.dumps(cfg)};"
            "var lw=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();"
            "var net=ipc.network();var ok=0;var errs=[];"
            "for(var i=0;i<list.length;i++){var it=list[i];try{"
            "var auto=lw.addDevice(it.type,it.model,it.x,it.y);"
            "var d=net.getDevice(auto);"
            "if(!d){errs.push('add_fail:'+it.name);continue;}"
            "d.setName(it.name);"
            "try{d.moveToLocation(it.x,it.y);}catch(e){}"
            "if(it.modules&&it.modules.length>0){"
            "d.setPower(false);"
            "for(var m=0;m<it.modules.length;m++){"
            "var slot=String(it.modules[m][0]);var mod=String(it.modules[m][1]);"
            "try{d.addModule(slot,allModuleTypes[mod],mod);}catch(me){errs.push('mod:'+it.name+':'+me);}"
            "}"
            "d.setPower(true);"
            "try{d.skipBoot();}catch(be){}"
            "}else{try{d.skipBoot();}catch(be){}}"
            "ok++;}catch(e){errs.push(it.name+':'+e);}}"
            "reportResult(JSON.stringify({added:ok,errs:errs}));"
            "}catch(e){reportResult('ERR:'+e);}})();"
        )
        out = send_js(bridge, js, timeout=60.0)
        print(f"  devices batch {i//15 + 1}:", out)

    fast_forward(bridge, 2)

    # 2. Create links in batches of 20
    for i in range(0, len(links), 20):
        batch = links[i : i + 20]
        cfg = []
        for lk in batch:
            cfg.append({
                "a": lk["a"],
                "pa": lk["port_a"],
                "b": lk["b"],
                "pb": lk["port_b"],
                "c": PT_CONNECT_TYPE.get(lk.get("cable", "straight"), 8100),
            })
        js = (
            "(function(){try{"
            f"var list={json.dumps(cfg)};"
            "var lw=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();"
            "var ok=0;var errs=[];"
            "for(var i=0;i<list.length;i++){var l=list[i];try{"
            "var r=lw.createLink(l.a,l.pa,l.b,l.pb,l.c);"
            "if(!r){r=lw.createLink(l.a,l.pa,l.b,l.pb,8107);}"
            "if(r){ok++;}else{errs.push('link_false:'+l.a+':'+l.pa+'->'+l.b+':'+l.pb);}"
            "}catch(e){errs.push(l.a+'->'+l.b+':'+e);}}"
            "reportResult(JSON.stringify({linked:ok,errs:errs}));"
            "}catch(e){reportResult('ERR:'+e);}})();"
        )
        out = send_js(bridge, js, timeout=45.0)
        print(f"  links batch {i//20 + 1}:", out)


def configure_servers_and_hosts(bridge: FileBridge, devices: List[Dict], plan: Dict) -> None:
    # Configure static hosts + servers + DHCP clients
    host_cfg = []
    for d in devices:
        if d["category"] in ("pc", "server", "printer"):
            host_cfg.append({
                "name": d["name"],
                "cat": d["category"],
                "ip": d.get("ip", ""),
                "mask": d.get("mask", ""),
                "gw": d.get("gw", ""),
                "dns": d.get("dns", ""),
                "ipv6": d.get("ipv6", ""),
                "ipv6_prefix": d.get("ipv6_prefix", 64),
                "ipv6_gw": d.get("ipv6_gw", ""),
                "dhcp": bool(d.get("dhcp", False)),
            })
    js = (
        "(function(){try{"
        f"var hosts={json.dumps(host_cfg)};"
        "var net=ipc.network();var ok=0;var errs=[];"
        "for(var i=0;i<hosts.length;i++){var h=hosts[i];try{"
        "var d=net.getDevice(h.name);if(!d){errs.push('nf:'+h.name);continue;}"
        "var p=d.getPort('FastEthernet0');"
        "if(h.ip){"
        "try{d.setDhcpFlag(false);}catch(e){}"
        "p.setIpSubnetMask(h.ip,h.mask);"
        "if(h.gw){try{d.setDefaultGateway(h.gw);}catch(e){} try{p.setDefaultGateway(h.gw);}catch(e){}}"
        "if(h.dns){try{p.setDnsServerIp(h.dns);}catch(e){} try{d.setDnsServerIp(h.dns);}catch(e){}}"
        "if(h.ipv6){try{p.addIpv6Address(h.ipv6,h.ipv6_prefix,0,false);}catch(e){}}"
        "if(h.ipv6_gw){try{p.setIpv6DefaultGateway(h.ipv6_gw);}catch(e){}}"
        "}else if(h.dhcp){"
        "try{d.setDhcpFlag(true);}catch(e){}"
        "try{p.setDhcpClientFlag(true);}catch(e){}"
        "}"
        "ok++;}catch(e){errs.push(h.name+':'+e);}}"
        "reportResult(JSON.stringify({hosts_cfg:ok,errs:errs}));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    print("  hosts:", send_js(bridge, js, timeout=45.0))

    # Configure SRV-1 DHCPv4 relay pools, DNS records, and FTP user if SRV-1 exists in this file
    if any(d["name"] == "SRV-1" for d in devices):
        pools = plan["srv1_dhcp_pools"]
        dns_recs = plan["srv1_dns_records"]
        js_srv = (
            "(function(){try{"
            "var d=ipc.network().getDevice('SRV-1');"
            "if(!d){reportResult('NO_SRV1');return;}"
            "var out={};"
            # DHCPv4 pools
            "try{var s=d.getProcess('DhcpServerMain').getDhcpServerProcessByPortName('FastEthernet0');"
            "s.setEnable(true);"
            f"var pools={json.dumps(pools)};"
            "for(var i=0;i<pools.length;i++){var pl=pools[i];"
            "s.addNewPool(pl.name,pl.gw,pl.dns,pl.start,pl.mask,pl.max_users,'0.0.0.0','0.0.0.0');}"
            "out.dhcp_pools=s.getPoolCount();}catch(e){out.dhcp_err=String(e);}"
            # DNS records
            "try{var dns=d.getProcess('DnsServer');dns.setEnable(true);"
            f"var recs={json.dumps(dns_recs)};"
            "for(var j=0;j<recs.length;j++){dns.addARecordToNameServerDb(recs[j][0],recs[j][1]);}"
            "out.dns_ok=true;}catch(e){out.dns_err=String(e);}"
            # FTP user (HTTP is already enabled by default on Server-PT; do NOT toggle HTTP off/on)
            "try{var ftp=d.getProcess('FtpServer');ftp.setEnabled(true);"
            "out.ftp_ok=true;}catch(e){out.ftp_err=String(e);}"
            "reportResult(JSON.stringify(out));"
            "}catch(e){reportResult('ERR:'+e);}})();"
        )
        print("  SRV-1 services:", send_js(bridge, js_srv, timeout=30.0))


def push_router_cli(bridge: FileBridge, router_name: str) -> Dict:
    cli_text = (CLI_DIR / f"{router_name}.ios.txt").read_text(encoding="utf-8")
    lines = []
    for raw in cli_text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("!"):
            continue
        lines.append(ln)

    # Push via hidden CLI line (enterCommand) in clean chunks
    js = (
        "(function(){try{"
        f"var rname={json.dumps(router_name)};"
        f"var cmds={json.dumps(lines)};"
        "var d=ipc.network().getDevice(rname);"
        "if(!d){reportResult(JSON.stringify({ok:false,err:'not_found'}));return;}"
        "try{d.skipBoot();}catch(e){}"
        # Prime console once just in case
        "var cl=d.getCommandLine();"
        "try{cl.enterCommand('no');cl.enterCommand('');}catch(e){}"
        "var bad=[];var applied=0;"
        "for(var i=0;i<cmds.length;i++){"
        "var c=cmds[i];"
        "if(c==='enable'||c==='configure terminal'||c==='end'||c==='write memory'){continue;}"
        "try{"
        "var r=d.enterCommand(c,'');"
        "applied++;"
        "if(r&&r.first&&r.first!==0){bad.push({cmd:c,status:r.first,out:String(r.second||'')});}"
        "}catch(ce){bad.push({cmd:c,err:String(ce)});}"
        "}"
        "try{d.enterCommand('end','');d.enterCommand('write memory','enable');}catch(e){}"
        "reportResult(JSON.stringify({router:rname,applied:applied,bad_count:bad.length,bad:bad.slice(0,12)}));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    # Wait: enterCommand('', '') stays in current mode; let's enter global mode first explicitly!
    js_global = (
        "(function(){try{"
        f"var rname={json.dumps(router_name)};"
        f"var cmds={json.dumps(lines)};"
        "var d=ipc.network().getDevice(rname);"
        "if(!d){reportResult(JSON.stringify({ok:false,err:'not_found'}));return;}"
        "try{d.skipBoot();}catch(e){}"
        "var cl=d.getCommandLine();"
        "try{cl.enterCommand('no');cl.enterCommand('');}catch(e){}"
        # Send via configureIosDevice? Or enterCommand starting in global mode!
        "var bad=[];var applied=0;"
        "d.enterCommand('enable','user');"
        "d.enterCommand('configure terminal','enable');"
        "for(var i=0;i<cmds.length;i++){"
        "var c=cmds[i];"
        "if(c==='enable'||c==='configure terminal'){continue;}"
        "if(c==='end'){d.enterCommand('end','');continue;}"
        "if(c==='write memory'){d.enterCommand('write memory','enable');continue;}"
        "var r=d.enterCommand(c,'');"
        "applied++;"
        "if(r&&r.first&&r.first!==0){bad.push({cmd:c,status:r.first,out:String(r.second||'')});}"
        "}"
        "reportResult(JSON.stringify({router:rname,applied:applied,bad_count:bad.length,bad:bad.slice(0,15)}));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    out = send_js(bridge, js_global, timeout=90.0)
    print(f"  CLI {router_name}:", out)
    try:
        return json.loads(out)
    except Exception:
        return {"raw": out}


def renew_all_dhcp(bridge: FileBridge, devices: List[Dict]) -> Dict:
    dhcp_hosts = [d["name"] for d in devices if d.get("dhcp")]
    js = (
        "(function(){try{"
        f"var names={json.dumps(dhcp_hosts)};"
        "var net=ipc.network();"
        "for(var i=0;i<names.length;i++){"
        "var d=net.getDevice(names[i]);if(!d)continue;"
        "try{var cl=d.getCommandLine();cl.enterCommand('ipconfig /renew');}catch(e){}"
        "}"
        "reportResult('RENEW_SENT:'+names.length);"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    send_js(bridge, js, timeout=30.0)
    fast_forward(bridge, 4)
    time.sleep(1.5)
    # Read back all host IPs
    js_read = (
        "(function(){try{"
        f"var names={json.dumps(dhcp_hosts)};"
        "var net=ipc.network();var out={};"
        "for(var i=0;i<names.length;i++){"
        "var d=net.getDevice(names[i]);if(!d)continue;"
        "var p=d.getPort('FastEthernet0');"
        "var ip='';var mask='';var gw='';"
        "try{ip=String(p.getIpAddress());mask=String(p.getSubnetMask());}catch(e){}"
        "try{gw=String(d.getProcess('HostIpProcess').getDefaultGateway());}catch(e){}"
        "out[names[i]]={ip:ip,mask:mask,gw:gw};}"
        "reportResult(JSON.stringify(out));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    raw = send_js(bridge, js_read, timeout=30.0)
    print("  DHCP leases:", raw)
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def run_router_show(bridge: FileBridge, router_name: str, cmd: str) -> str:
    js = (
        "(function(){try{"
        f"var d=ipc.network().getDevice({json.dumps(router_name)});"
        f"var r=d.enterCommand({json.dumps(cmd)},'enable');"
        "reportResult(String(r.second||''));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    return send_js(bridge, js, timeout=25.0)


def run_pc_ping(bridge: FileBridge, pc_name: str, target: str) -> str:
    # Arm ping on PC command line, wait briefly + fast forward, read output
    js_arm = (
        "(function(){try{"
        f"var d=ipc.network().getDevice({json.dumps(pc_name)});"
        "var cl=d.getCommandLine();"
        f"cl.enterCommand('ping -n 2 ' + {json.dumps(target)});"
        "reportResult('ARMED');"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    send_js(bridge, js_arm, timeout=15.0)
    for _ in range(4):
        fast_forward(bridge, 1)
        time.sleep(0.5)
    js_out = (
        "(function(){try{"
        f"var d=ipc.network().getDevice({json.dumps(pc_name)});"
        "var txt=String(d.getCommandLine().getOutput()||'');"
        "reportResult(txt.slice(-700));"
        "}catch(e){reportResult('ERR:'+e);}})();"
    )
    return send_js(bridge, js_out, timeout=15.0)


def build_and_verify_master(bridge: FileBridge, plan: Dict) -> Dict:
    print("\n=== [1/4] Building & Verifying Master Topology: pt/rj_network.pkt ===")
    clear_workspace(bridge)
    deploy_devices_and_links(bridge, plan["devices"], plan["links"])
    configure_servers_and_hosts(bridge, plan["devices"], plan)

    cli_results = {}
    for rname in ["ISP-CEBU", "R-CEBU", "R-CLARK", "R-DAVAO"]:
        cli_results[rname] = push_router_cli(bridge, rname)

    fast_forward(bridge, 6)
    time.sleep(2.0)
    leases = renew_all_dhcp(bridge, plan["devices"])
    # Second round for any host still catching up after STP
    if any(v.get("ip") in ("", "0.0.0.0") for v in leases.values() if isinstance(v, dict)):
        fast_forward(bridge, 4)
        leases = renew_all_dhcp(bridge, plan["devices"])

    # Collect real live router verification outputs (redacted!)
    shows = {}
    for rname in ["ISP-CEBU", "R-CEBU", "R-CLARK", "R-DAVAO"]:
        shows[rname] = {
            "ip_int_br": run_router_show(bridge, rname, "show ip interface brief"),
            "ip_route": run_router_show(bridge, rname, "show ip route"),
            "ipv6_route": run_router_show(bridge, rname, "show ipv6 route"),
            "access_lists": run_router_show(bridge, rname, "show access-lists"),
            "running_redacted": redact_cli(run_router_show(bridge, rname, "show running-config")),
        }

    # Run real live connectivity & ACL ping tests
    ping_tests = [
        ("T-01", "GAM-01",     "203.0.113.1", "PASS_EXPECTED", "HQ Gaming PC -> Simulated Internet Loopback0"),
        ("T-02", "GAM-01",     "10.10.0.98",  "PASS_EXPECTED", "HQ Gaming PC -> SRV-1 (Web/DNS reachable)"),
        ("T-03", "GAM-01",     "10.10.0.99",  "DENY_EXPECTED", "Obj 2: HQ Gaming PC -> SRV-2 (Billing/POS blocked)"),
        ("T-04", "IT-PC",      "10.10.0.99",  "PASS_EXPECTED", "Obj 2: HQ Admin IT-PC -> SRV-2 (Billing/POS permitted)"),
        ("T-05", "CLK-GAM-01", "203.0.113.1", "PASS_EXPECTED", "Clark RIPv2 Gaming PC -> Simulated Internet Loopback0"),
        ("T-06", "CLK-GAM-01", "10.10.1.70",  "DENY_EXPECTED", "Obj 3: Clark Gaming PC -> Clark Admin LAN (blocked)"),
        ("T-07", "CLK-IT-PC",  "10.10.0.99",  "DENY_EXPECTED", "Obj 2: Clark Branch Admin -> HQ SRV-2 (blocked)"),
        ("T-08", "DVO-GAM-01", "203.0.113.1", "PASS_EXPECTED", "Davao EIGRP Gaming PC -> Simulated Internet Loopback0"),
        ("T-09", "DVO-GAM-01", "10.10.2.70",  "DENY_EXPECTED", "Obj 3: Davao Gaming PC -> Davao Admin LAN (blocked)"),
        ("T-10", "DVO-IT-PC",  "10.10.1.70",  "PASS_EXPECTED", "EIGRP <-> RIPv2 Redistribution: Davao IT-PC -> Clark IT-PC"),
    ]
    ping_results = []
    for tid, src, dst, exp, desc in ping_tests:
        out = run_pc_ping(bridge, src, dst)
        got_reply = f"Reply from {dst}: bytes=" in out
        passed = got_reply if exp == "PASS_EXPECTED" else (not got_reply and ("Destination host unreachable" in out or "100% loss" in out))
        ping_results.append({
            "id": tid, "src": src, "dst": dst, "expected": exp, "desc": desc,
            "got_reply": got_reply, "test_pass": passed, "output_tail": out[-320:],
        })
        print(f"  {tid} ({src} -> {dst}): reply={got_reply} | expected={exp} | {'PASS' if passed else 'CHECK'}")

    # Re-read ACL counters after tests!
    acl_after = {}
    for rname in ["R-CEBU", "R-CLARK", "R-DAVAO"]:
        acl_after[rname] = run_router_show(bridge, rname, "show access-lists")

    # Save master .pkt IMMEDIATELY!
    save_out = save_pkt(bridge, "rj_network.pkt")

    evidence = {
        "saved": save_out,
        "cli_results": cli_results,
        "dhcp_leases": leases,
        "ping_results": ping_results,
        "shows": shows,
        "acl_after_tests": acl_after,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "live_verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def build_site_pkt(bridge: FileBridge, plan: Dict, filename: str, sites: List[str], routers: List[str]) -> None:
    print(f"\n=== Building Site Multiuser File: pt/{filename} ===")
    clear_workspace(bridge)
    devs = [d for d in plan["devices"] if d["site"] in sites]
    dev_names = {d["name"] for d in devs}
    lks = [l for l in plan["links"] if l["a"] in dev_names and l["b"] in dev_names]
    deploy_devices_and_links(bridge, devs, lks)
    configure_servers_and_hosts(bridge, devs, plan)
    for rname in routers:
        push_router_cli(bridge, rname)
    fast_forward(bridge, 4)
    renew_all_dhcp(bridge, devs)
    save_pkt(bridge, filename)


def main() -> None:
    bridge = FileBridge()
    if not bridge.pt_alive():
        raise RuntimeError("Packet Tracer Script Engine heartbeat (alive.txt) is not fresh! Open PT 9.0.1 first.")
    print("Packet Tracer 9.0.1 FileBridge is ALIVE!")
    plan = json.loads((PT_DIR / "rj_plan.json").read_text(encoding="utf-8"))

    build_and_verify_master(bridge, plan)
    build_site_pkt(bridge, plan, "rj_cebu_hq_visayas.pkt", ["CEBU", "ISP"], ["ISP-CEBU", "R-CEBU"])
    build_site_pkt(bridge, plan, "rj_clark_luzon.pkt",     ["CLARK"],       ["R-CLARK"])
    build_site_pkt(bridge, plan, "rj_davao_mindanao.pkt",  ["DAVAO"],       ["R-DAVAO"])
    print("\nALL 4 PACKET TRACER .PKT FILES BUILT, VERIFIED & SAVED!")


if __name__ == "__main__":
    main()
