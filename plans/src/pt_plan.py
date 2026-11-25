"""Packet Tracer Deployment Plan JSON (pt/rj_plan.json) + Manual Physical Workspace Guide.

100% 1-to-1 parity across EVERY PC, Network Printer, Ceiling AP, and Server:
- Building 2 (Cebu Flagship HQ): ALL 42 PCs + 2 Printers + 8 APs (= all 52 horizontal drops from
  drop_schedule.csv) + 2 MDF Rack Servers (SRV-1, SRV-2), full 3-tier hierarchy, every horizontal drop
  wired PC/Printer/AP -> Copper Wall Mount (Jack1/PunchDown1) -> Copper Patch Panel (PunchDownN/JackN) -> Access Switch.
- Building 1 (Clark Branch, Luzon): ALL 16 Gaming PCs + 3 Customer APs + 4 Admin/POS PCs + 1 Printer + 1 Staff AP (25 drops).
- Building 3 (Davao Branch, Mindanao): ALL 16 Gaming PCs + 3 Customer APs + 4 Admin/POS PCs + 1 Printer + 1 Staff AP (25 drops).
- Master (rj_network.pkt): All 3 sites + ISP-CEBU (82 PCs, 4 Printers, 16 APs, 2 Servers, 102 Wall Mounts, 8 Patch Panels).
"""

from __future__ import annotations

import ipaddress
import json
from typing import Dict, List

from cabling import compute_switch_ports
from model import DROPS, PT_DIR
from vlsm import SUBNET_BY_NAME, validate_addressing


def build_master_plan() -> Dict:
    validate_addressing()

    devices: List[Dict] = []
    links: List[Dict] = []

    def add_dev(name: str, model: str, cat: str, site: str, closet: str, x: int, y: int, **extra):
        d = {"name": name, "model": model, "category": cat, "site": site, "closet": closet, "x": x, "y": y}
        d.update(extra)
        devices.append(d)

    def add_link(a: str, pa: str, b: str, pb: str, cable: str = "straight"):
        links.append({"a": a, "port_a": pa, "b": b, "port_b": pb, "cable": cable})

    # =========================================================================
    # CENTRAL ISP IN CEBU
    # =========================================================================
    add_dev("ISP-CEBU", "2911", "router", "ISP", "ISP-RACK", 1600, 90,
            modules=[("0/0", "HWIC-2T"), ("0/1", "HWIC-2T"), ("0/2", "HWIC-2T")])

    # =========================================================================
    # BUILDING 2: CEBU FLAGSHIP HQ (100% of all 52 drops from DROPS + 2 Servers)
    # =========================================================================
    add_dev("R-CEBU",  "2911",      "router",            "CEBU", "MDF",   1600, 260, modules=[("0/0", "HWIC-2T")])
    add_dev("SW-CORE", "3560-24PS", "multilayer_switch", "CEBU", "MDF",   1320, 390)
    add_dev("SW-SRV",  "2960-24TT", "switch",            "CEBU", "MDF",   2160, 390)
    add_dev("DSW-1",   "3560-24PS", "multilayer_switch", "CEBU", "IDF-1", 1120, 510)
    add_dev("DSW-2",   "3560-24PS", "multilayer_switch", "CEBU", "IDF-2", 1640, 510)

    add_dev("SW-GAM1", "2960-24TT", "switch", "CEBU", "CAB-G", 920,  640)
    add_dev("SW-VIP",  "2960-24TT", "switch", "CEBU", "CAB-V", 1360, 640)
    add_dev("SW-STU",  "2960-24TT", "switch", "CEBU", "CAB-S", 1680, 640)
    add_dev("SW-ADM",  "2960-24TT", "switch", "CEBU", "IDF-2", 1960, 510)

    # 4 Patch Panels (24-port Copper Patch Panel matching CAB-G, CAB-V, CAB-S, IDF-2)
    add_dev("PP-G",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-G", 920,  730)
    add_dev("PP-V",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-V", 1360, 730)
    add_dev("PP-S",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-S", 1680, 730)
    add_dev("PP-ADM", "Copper Patch Panel", "patch_panel", "CEBU", "IDF-2", 1960, 620)

    # MDF Rack Servers (Static on HQ-SERVER-LAN 10.10.0.96/28)
    add_dev("SRV-1", "Server-PT", "server", "CEBU", "MDF", 2120, 510,
            lan="HQ-SERVER-LAN", ip="10.10.0.98", mask="255.255.255.240", gw="10.10.0.97", dns="10.10.0.98",
            ipv6="2001:DB8:ACAD:1003::98", ipv6_prefix=64, ipv6_gw="FE80::1", services=["DHCP", "DNS", "HTTP", "FTP"])
    add_dev("SRV-2", "Server-PT", "server", "CEBU", "MDF", 2220, 510,
            lan="HQ-SERVER-LAN", ip="10.10.0.99", mask="255.255.255.240", gw="10.10.0.97", dns="10.10.0.98",
            ipv6="2001:DB8:ACAD:1003::99", ipv6_prefix=64, ipv6_gw="FE80::1", services=["HTTP"])

    # WAN Links (ISP-CEBU <-> 3 Site Routers)
    add_link("ISP-CEBU", "Serial0/0/0", "R-CEBU",  "Serial0/0/0", "serial")
    add_link("ISP-CEBU", "Serial0/0/1", "R-CLARK", "Serial0/0/0", "serial")
    add_link("ISP-CEBU", "Serial0/1/0", "R-DAVAO", "Serial0/0/0", "serial")
    add_link("ISP-CEBU", "Serial0/1/1", "R-CLARK", "Serial0/0/1", "serial")
    add_link("ISP-CEBU", "Serial0/2/0", "R-DAVAO", "Serial0/0/1", "serial")

    # Cebu HQ 3-Tier Backbone Links (Zero PCs on Core or Distribution!)
    add_link("R-CEBU",  "GigabitEthernet0/0", "SW-CORE", "GigabitEthernet0/1", "straight")
    add_link("R-CEBU",  "GigabitEthernet0/1", "SW-ADM",  "GigabitEthernet0/1", "straight")
    add_link("R-CEBU",  "GigabitEthernet0/2", "SW-SRV",  "GigabitEthernet0/1", "straight")
    add_link("SW-CORE", "FastEthernet0/1",    "DSW-1",   "FastEthernet0/1",    "crossover")
    add_link("SW-CORE", "FastEthernet0/2",    "DSW-2",   "FastEthernet0/1",    "crossover")
    add_link("DSW-1",   "FastEthernet0/2",    "SW-GAM1", "GigabitEthernet0/1", "crossover")
    add_link("DSW-1",   "FastEthernet0/3",    "SW-VIP",  "GigabitEthernet0/1", "crossover")
    add_link("DSW-2",   "FastEthernet0/2",    "SW-STU",  "GigabitEthernet0/1", "crossover")
    add_link("SW-SRV",  "FastEthernet0/1",    "SRV-1",   "FastEthernet0",      "straight")
    add_link("SW-SRV",  "FastEthernet0/2",    "SRV-2",   "FastEthernet0",      "straight")

    # ALL 52 Cebu HQ horizontal drops directly from model.DROPS!
    # Neatly laid out in clean logical rows below each patch panel so nothing piles up on the canvas
    sw_grid_origin = {
        "SW-GAM1": (680,  840, 6),  # 22 drops -> 4 rows x 6 cols
        "SW-VIP":  (1180, 840, 4),  # 12 drops -> 3 rows x 4 cols
        "SW-STU":  (1540, 840, 3),  # 9 drops  -> 3 rows x 3 cols
        "SW-ADM":  (1860, 740, 3),  # 9 drops  -> 3 rows x 3 cols
    }
    sw_counter = {k: 0 for k in sw_grid_origin}

    for dr in DROPS:
        idx = sw_counter[dr.switch]
        sw_counter[dr.switch] += 1
        ox, oy, cols = sw_grid_origin[dr.switch]
        r_i, c_i = divmod(idx, cols)
        hx = ox + c_i * 78
        hy = oy + r_i * 125

        if dr.kind == "AP":
            hmod, hcat, hport = "AccessPoint-PT", "accesspoint", "Port 0"
        elif dr.kind == "Printer":
            hmod, hcat, hport = "Printer-PT", "printer", "FastEthernet0"
        else:
            hmod, hcat, hport = "PC-PT", "pc", "FastEthernet0"

        wm_name = f"WM-{dr.drop_id}"
        add_dev(wm_name, "Copper Wall Mount", "wall_mount", "CEBU", f"ZONE-{dr.room}", hx, hy - 48)

        spec = SUBNET_BY_NAME[dr.lan]
        extra: Dict = {"lan": dr.lan, "room": dr.room, "drop_id": dr.drop_id}
        if dr.ip_mode == "Static" and dr.static_ip:
            extra.update({
                "ip": dr.static_ip, "mask": str(spec.net4.netmask), "gw": spec.gateway_v4, "dns": "10.10.0.98",
                "ipv6": dr.static_ipv6, "ipv6_prefix": 64, "ipv6_gw": "FE80::1",
            })
        elif hcat in ("pc", "printer"):
            extra.update({"dhcp": True, "ipv6_dhcp": True})

        add_dev(dr.device, hmod, hcat, "CEBU", f"ZONE-{dr.room}", hx, hy, **extra)
        # Mandatory physical path: Switch Fa0/p -> Patch Panel Jack{p} -> PunchDown{p} -> WM PunchDown1 -> WM Jack1 -> Host
        add_link(dr.switch, dr.sw_port, dr.pp_id, f"Jack{dr.pp_port}", "straight")
        add_link(dr.pp_id, f"PunchDown{dr.pp_port}", wm_name, "PunchDown1", "straight")
        add_link(wm_name, "Jack1", dr.device, hport, "straight")

    # =========================================================================
    # HELPER FOR FULL BRANCH SITES (Clark = 25 drops, Davao = 25 drops)
    # =========================================================================
    def add_branch(site_code: str, prefix: str, rname: str, gam_lan: str, adm_lan: str, base_x: int):
        sw_g = f"SW-{prefix}-GAM"
        sw_a = f"SW-{prefix}-ADM"
        pp_g = f"PP-{prefix}-G"
        pp_a = f"PP-{prefix}-A"

        add_dev(rname, "2911",               "router",      site_code, f"{prefix}-MDF", base_x + 240, 260, modules=[("0/0", "HWIC-2T")])
        add_dev(sw_g,  "2960-24TT",          "switch",      site_code, f"{prefix}-MDF", base_x + 120, 420)
        add_dev(sw_a,  "2960-24TT",          "switch",      site_code, f"{prefix}-MDF", base_x + 420, 420)
        add_dev(pp_g,  "Copper Patch Panel", "patch_panel", site_code, f"{prefix}-MDF", base_x + 120, 520)
        add_dev(pp_a,  "Copper Patch Panel", "patch_panel", site_code, f"{prefix}-MDF", base_x + 420, 520)

        add_link(rname, "GigabitEthernet0/0", sw_g, "GigabitEthernet0/1", "straight")
        add_link(rname, "GigabitEthernet0/1", sw_a, "GigabitEthernet0/1", "straight")

        # 16 Gaming PCs + 3 Customer APs = 19 drops on Gaming Switch / Patch Panel
        gam_endpoints = [(f"{prefix}-GAM-{i:02d}", "PC-PT", "pc", "FastEthernet0") for i in range(1, 17)] + [
            (f"{prefix}-AP-{i:02d}", "AccessPoint-PT", "accesspoint", "Port 0") for i in range(1, 4)
        ]
        for idx, (hname, hmod, hcat, hport) in enumerate(gam_endpoints, 1):
            r_i, c_i = divmod(idx - 1, 5)
            hx = base_x + c_i * 74
            hy = 660 + r_i * 125
            wm = f"WM-{prefix}-G{idx:02d}"
            add_dev(wm, "Copper Wall Mount", "wall_mount", site_code, f"{prefix}-GAMING", hx, hy - 48)
            extra = {"lan": gam_lan}
            if hcat == "pc":
                extra.update({"dhcp": True, "ipv6_dhcp": True})
            add_dev(hname, hmod, hcat, site_code, f"{prefix}-GAMING", hx, hy, **extra)
            add_link(sw_g, f"FastEthernet0/{idx}", pp_g, f"Jack{idx}", "straight")
            add_link(pp_g, f"PunchDown{idx}", wm, "PunchDown1", "straight")
            add_link(wm, "Jack1", hname, hport, "straight")

        # 4 Admin/POS PCs + 1 Network Printer + 1 Staff AP = 6 drops on Admin Switch / Patch Panel
        adm_spec = SUBNET_BY_NAME[adm_lan]
        oct3 = "1" if prefix == "CLK" else "2"
        v6_sub = "2002" if prefix == "CLK" else "3002"
        adm_endpoints = [
            (f"{prefix}-IT-PC",  "PC-PT",          "pc",          "FastEthernet0", f"10.10.{oct3}.70", f"2001:DB8:ACAD:{v6_sub}::70"),
            (f"{prefix}-PRT-01", "Printer-PT",     "printer",     "FastEthernet0", f"10.10.{oct3}.71", f"2001:DB8:ACAD:{v6_sub}::71"),
            (f"{prefix}-MGR-PC", "PC-PT",          "pc",          "FastEthernet0", None, None),
            (f"{prefix}-POS-01", "PC-PT",          "pc",          "FastEthernet0", None, None),
            (f"{prefix}-POS-02", "PC-PT",          "pc",          "FastEthernet0", None, None),
            (f"{prefix}-AP-04",  "AccessPoint-PT", "accesspoint", "Port 0",        None, None),
        ]
        for idx, (hname, hmod, hcat, hport, sip, sip6) in enumerate(adm_endpoints, 1):
            r_i, c_i = divmod(idx - 1, 2)
            hx = base_x + 390 + c_i * 78
            hy = 660 + r_i * 125
            wm = f"WM-{prefix}-A{idx:02d}"
            add_dev(wm, "Copper Wall Mount", "wall_mount", site_code, f"{prefix}-ADMIN", hx, hy - 48)
            extra = {"lan": adm_lan}
            if sip:
                extra.update({
                    "ip": sip, "mask": str(adm_spec.net4.netmask), "gw": adm_spec.gateway_v4, "dns": "10.10.0.98",
                    "ipv6": sip6, "ipv6_prefix": 64, "ipv6_gw": "FE80::1",
                })
            elif hcat in ("pc", "printer"):
                extra.update({"dhcp": True, "ipv6_dhcp": True})
            add_dev(hname, hmod, hcat, site_code, f"{prefix}-ADMIN", hx, hy, **extra)
            add_link(sw_a, f"FastEthernet0/{idx}", pp_a, f"Jack{idx}", "straight")
            add_link(pp_a, f"PunchDown{idx}", wm, "PunchDown1", "straight")
            add_link(wm, "Jack1", hname, hport, "straight")

    # Building 1 (Clark — Luzon) & Building 3 (Davao — Mindanao)
    add_branch("CLARK", "CLK", "R-CLARK", "CLK-GAMING-LAN", "CLK-ADMIN-LAN", base_x=60)
    add_branch("DAVAO", "DVO", "R-DAVAO", "DVO-GAMING-LAN", "DVO-ADMIN-LAN", base_x=2360)

    # Programmatic assertion: EVERY static host IP strictly between network+1 and broadcast-1
    for d in devices:
        if "ip" in d and "lan" in d:
            net = SUBNET_BY_NAME[d["lan"]].net4
            addr = ipaddress.IPv4Address(d["ip"])
            assert net.network_address < addr < net.broadcast_address, f"Invalid host IP {d['ip']} on {d['name']}"
            assert d["ip"] != SUBNET_BY_NAME[d["lan"]].gateway_v4, f"{d['name']} collides with gateway"

    # Parity count assertions
    assert sum(1 for d in devices if d["site"] == "CEBU" and d["category"] == "pc") == 42
    assert sum(1 for d in devices if d["site"] == "CEBU" and d["category"] == "printer") == 2
    assert sum(1 for d in devices if d["site"] == "CEBU" and d["category"] == "accesspoint") == 8
    assert sum(1 for d in devices if d["site"] == "CEBU" and d["category"] == "server") == 2
    assert sum(1 for d in devices if d["site"] == "CLARK" and d["category"] == "pc") == 20
    assert sum(1 for d in devices if d["site"] == "CLARK" and d["category"] == "printer") == 1
    assert sum(1 for d in devices if d["site"] == "CLARK" and d["category"] == "accesspoint") == 4
    assert sum(1 for d in devices if d["site"] == "DAVAO" and d["category"] == "pc") == 20
    assert sum(1 for d in devices if d["site"] == "DAVAO" and d["category"] == "printer") == 1
    assert sum(1 for d in devices if d["site"] == "DAVAO" and d["category"] == "accesspoint") == 4

    srv1_dhcp_pools = [
        {"name": "HQ-GAMING-POOL", "gw": "10.10.0.1",  "dns": "10.10.0.98", "start": "10.10.0.11", "mask": "255.255.255.192", "max_users": 50},
        {"name": "HQ-ADMIN-POOL",  "gw": "10.10.0.65", "dns": "10.10.0.98", "start": "10.10.0.76", "mask": "255.255.255.224", "max_users": 18},
    ]

    return {
        "project": "RJ Internet Cafe & Esports Inc. — Full 1-to-1 Multi-Branch Network (Group1)",
        "parity": {
            "cebu_hq": {"pcs": 42, "printers": 2, "aps": 8, "servers": 2, "horizontal_drops": 52},
            "clark_branch": {"pcs": 20, "printers": 1, "aps": 4, "horizontal_drops": 25},
            "davao_branch": {"pcs": 20, "printers": 1, "aps": 4, "horizontal_drops": 25},
            "total_endpoints": 104,
        },
        "pkt_files": {
            "master": "pt/rj_network.pkt",
            "cebu_hq": "pt/rj_cebu_hq_visayas.pkt",
            "clark_branch": "pt/rj_clark_luzon.pkt",
            "davao_branch": "pt/rj_davao_mindanao.pkt",
        },
        "srv1_dhcp_pools": srv1_dhcp_pools,
        "srv1_dns_records": [
            ("portal.rjesports.local", "10.10.0.98"),
            ("billing.rjesports.local", "10.10.0.99"),
            ("isp.rjesports.local", "203.0.113.1"),
        ],
        "devices": devices,
        "links": links,
    }


def write_manual_physical_guide() -> None:
    sw_ports = compute_switch_ports()
    lines = [
        "# Packet Tracer Manual Physical Workspace & Screenshot Guide",
        "**Project:** RJ Internet Café & Esports Inc. (`Group1`) — CPE 3105",
        "**Owners:** Marchen Viterbo (Logical Build & Routing) & Andre Merkel Sepe (Physical Workspace, ACLs & Testing)",
        "",
        "---",
        "",
        "## 1. Packet Tracer Files Included (`pt/` — Full 1-to-1 Endpoint Parity)",
        "| File | Scope | Endpoints Included (100% Parity w/ Plans & BOQ) |",
        "|---|---|---|",
        "| `pt/rj_network.pkt` | All 3 Buildings + `ISP-CEBU` | **82 PCs, 4 Printers, 16 APs, 2 Servers** (102 horizontal drops + 2 rack servers) |",
        "| `pt/rj_cebu_hq_visayas.pkt` | Building 2 — Cebu Flagship HQ + `ISP-CEBU` (Multiuser TCP 38000 Host) | **42 PCs, 2 Printers (`PRT-01..02`), 8 APs (`AP-01..08`), 2 Servers (`SRV-1..2`)** |",
        "| `pt/rj_clark_luzon.pkt` | Building 1 — Clark Branch Café (Luzon) | **20 PCs (`CLK-GAM-01..16`, `CLK-IT-PC`, `CLK-MGR-PC`, `CLK-POS-01..02`), 1 Printer (`CLK-PRT-01`), 4 APs** |",
        "| `pt/rj_davao_mindanao.pkt` | Building 3 — Davao Branch Café (Mindanao) | **20 PCs (`DVO-GAM-01..16`, `DVO-IT-PC`, `DVO-MGR-PC`, `DVO-POS-01..02`), 1 Printer (`DVO-PRT-01`), 4 APs** |",
        "",
        "---",
        "",
        "## 2. Exact Physical Workspace Hierarchy (Cities, Buildings, Wiring Closets)",
        "Switch to **Physical Workspace (`Shift+P`)** and set the scaled background images from `pt/backgrounds/` at each level:",
        "",
        "| Level | Exact PT Name | Background Image (`pt/backgrounds/`) |",
        "|---|---|---|",
        "| Intercity | `Philippines Intercity` | `intercity_3_sites.png` |",
        "| City 1 | `Clark_Luzon` | `city_clark.png` |",
        "| Building 1 | `RJ_Clark_Branch` | `floor_clark.png` (40 × 26 m = 1,040 sqm) |",
        "| Closet 1A | `CLK-MDF` | Main rack inside Clark MDF Room (`R-CLARK`, `SW-CLK-GAM/ADM`, `PP-CLK-G/A`) |",
        "| City 2 | `Cebu_Visayas` | `city_cebu.png` |",
        "| Building 2 | `RJ_Cebu_Flagship_HQ` | `floor_hq.png` (40 × 26 m = 1,040 sqm) |",
        "| Building 2B | `Cebu_ISP_POP` | Central ISP node (`ISP-CEBU`) in Cebu City |",
        "| Closets 2A–2F | `MDF`, `IDF-1`, `IDF-2`, `CAB-G`, `CAB-V`, `CAB-S` | Placed on exact cabinet markers on `floor_hq.png` |",
        "| City 3 | `Davao_Mindanao` | `city_davao.png` |",
        "| Building 3 | `RJ_Davao_Branch` | `floor_davao.png` (40 × 26 m = 1,040 sqm) |",
        "| Closet 3A | `DVO-MDF` | Main rack inside Davao MDF Room (`R-DAVAO`, `SW-DVO-GAM/ADM`, `PP-DVO-G/A`) |",
        "",
        "---",
        "",
        "## 3. Exact Device-to-Closet & Drop Placement Table (Cebu Flagship HQ — All 52 Drops)",
        "Drag each device + its matching Copper Wall Mount (`WM-<DropID>`) in **Physical Workspace** directly onto its labeled marker on `floor_hq.png`:",
        "",
        "| Device(s) | Exact Closet / Room | Coordinates | Mandatory Physical Path |",
        "|---|---|---|---|",
        "| `R-CEBU`, `SW-CORE`, `SW-SRV`, `SRV-1`, `SRV-2` | `MDF` (`MDF-ROOM`) | (20.5 m, 15.5 m) | Rack-mounted in 42U MDF cabinet |",
        "| `DSW-1` (3560-24PS) | `IDF-1` (`FUT-GAME`) | (18.6 m, 11.4 m) | OM3 fiber to `MDF` `SW-CORE`; **zero PCs directly on `DSW-1`** |",
        "| `DSW-2` (3560-24PS), `SW-ADM` (2960-24TT), `PP-ADM` | `IDF-2` (`ADMIN-OFC`) | (27.6 m, 14.6 m) | OM3 fiber to `MDF` `SW-CORE`; `SW-ADM` serves Admin/POS/Printers |",
        "| `SW-GAM1`, `PP-G` + `GAM-01..20`, `AP-01..02` | `CAB-G` (`STD-GAME`) | (17.4 m, 6.0 m) | 22 drops: Host → `WM-G01..20`/`WM-AP-01..02` → `PP-G` → `SW-GAM1` |",
        "| `SW-VIP`, `PP-V` + `VIP-01..10`, `AP-03..04` | `CAB-V` (`VIP-ARENA`) | (26.6 m, 6.0 m) | 12 drops: Host → `WM-V01..10`/`WM-AP-03..04` → `PP-V` → `SW-VIP` |",
        "| `SW-STU`, `PP-S` + `STD-01..04`, `BRW-01..02`, `AP-05..07` | `CAB-S` (`STUDY-PODS`) | (17.4 m, 18.0 m) | 9 drops: Host → `WM-S01..04`/`B01..02`/`AP-05..07` → `PP-S` → `SW-STU` |",
        "| `IT-PC`, `MGR-PC`, `STF-01..02`, `POS-01..02`, `PRT-01..02`, `AP-08` | `ADMIN-OFC` / `CASH-LOBBY` | See Sheet `C-1` | 9 drops: Host → `WM-A01..08`/`WM-AP-08` → `PP-ADM` → `SW-ADM` |",
        "",
        "### Access Switch Spare Port Check (`2960-24TT`: `24 - Used Fa`, uplink on `Gi0/1`)",
        "| Switch | Cabinet | Used Fa Ports | Spare Fa Ports | Uplink |",
        "|---|---|---|---|---|",
    ]
    for s in sw_ports:
        lines.append(f"| `{s['switch']}` | {s['location']} | {s['used_fa']} | **{s['spare_fa']}** | `{s['uplink']}` |")

    lines += [
        "",
        "---",
        "",
        "## 4. Wall Cabling, Bend Points & Cable Length Verification Checklist",
        "1. Enable **Options → Preferences → Miscellaneous → Enable Cable Length Effects** (checked **ON**).",
        "2. Verify every host follows the mandatory structured cabling path:",
        "   `PC/Printer/AP -> Copper Wall Mount (Jack1 / PunchDown1) -> Copper Patch Panel (PunchDownN / JackN) -> Access Switch -> Distribution Switch -> Core Switch -> Router`.",
        "3. **No diagonal cables:** Right-click any copper wire running across a room → select **Create Bend Point** and drag the vertex along room perimeter walls and the central 2.0 m corridor (`Y = 12.45 m` north tray).",
        "4. Hover over each horizontal cable run to confirm length **≤ 90 m permanent link** (**≤ 100 m total channel**). All designed Cebu HQ drops measure **12.7 m – 39.3 m** (zero repeaters required).",
        "5. **Multiuser Linking:** On `rj_cebu_hq_visayas.pkt`, open **Extensions → Multiuser → Listen** on **TCP port `38000`** (`Allow New Remote Networks: Always Allow`, password `rjesports`). On `rj_clark_luzon.pkt` and `rj_davao_mindanao.pkt`, connect their Multiuser Cloud (`Peer0`) to `127.0.0.1:38000`.",
        "",
        "---",
        "",
        "## 5. Exact 6-Screenshot Capture Checklist (Auto-Embed Pipeline)",
        "Save screenshots using these **exact filenames** inside `report/screenshots/`, then run ONE rebuild command to regenerate `.docx` and `.pdf` with updated TOC/LOF/LOT:",
        "",
        "| Filename (`report/screenshots/`) | Report Section | What Must Be Visible |",
        "|---|---|---|",
        "| `01_phys_clark.png` | §4.2 | Building 1 (Clark) Physical Workspace on `floor_clark.png` with bend-point wall cabling & `CLK-MDF` |",
        "| `02_phys_cebu_hq.png` | §4.3 | Building 2 (Cebu HQ) Physical Workspace on `floor_hq.png` with `MDF`, `IDF-1/2`, `CAB-G/V/S` & bend points |",
        "| `03_phys_davao.png` | §4.4 | Building 3 (Davao) Physical Workspace on `floor_davao.png` with bend-point wall cabling & `DVO-MDF` |",
        "| `04_logical_isp.png` | §4.5 | Logical Workspace of `rj_network.pkt` showing all 3 branches converging at `ISP-CEBU` (green link lights) |",
        "| `05_cli_routes.png` | §4.7 / App. F | Router CLI output showing `show ip route` & `show ipv6 route` on `ISP-CEBU`, `R-CLARK` (RIP), `R-DAVAO` (EIGRP) |",
        "| `06_cli_acls_ping.png` | §4.8 / App. F | PC Command Prompt + `show access-lists` proving SSH allow/deny, `SRV-2` block, HTTP/DNS allow, FTP deny, and `203.0.113.1` ping |",
        "",
        "### One-Command Report Rebuild After Dropping Screenshots",
        "```powershell",
        '& "C:\\Users\\Marianito Roble\\AppData\\Local\\Python\\bin\\python.exe" "D:\\Junior Year\\first sem\\COMPUTER NETWORKS AND SECURITY\\RJ esports\\plans\\src\\report_build.py"',
        "```",
    ]
    (PT_DIR / "PT_MANUAL_PHYSICAL_GUIDE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plan = build_master_plan()
    PT_DIR.mkdir(parents=True, exist_ok=True)
    (PT_DIR / "rj_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    write_manual_physical_guide()
    print(f"Generated FULL 1-to-1 pt/rj_plan.json ({len(plan['devices'])} devices, {len(plan['links'])} links) & pt/PT_MANUAL_PHYSICAL_GUIDE.md")


if __name__ == "__main__":
    main()
