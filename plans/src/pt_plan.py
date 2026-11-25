"""Packet Tracer Deployment Plan JSON (pt/rj_plan.json) + Manual Physical Workspace Guide (pt/PT_MANUAL_PHYSICAL_GUIDE.md).

Builds a validated structured topology plan covering:
- Master 3-site + ISP-CEBU topology (`rj_network.pkt`) with full 3-tier Cebu HQ hierarchy
  (MDF Core -> IDF-1/IDF-2 Distribution -> Zone Access switches) and mandatory physical path
  `PC -> Copper Wall Mount (Jack/PunchDown) -> Copper Patch Panel (PunchDown/Jack) -> Switch -> Router`.
- Three separate Multiuser-ready site sub-plans (`rj_cebu_hq_visayas.pkt`, `rj_clark_luzon.pkt`, `rj_davao_mindanao.pkt`).
- Asserts programmatically that EVERY host IP is strictly between network+1 and broadcast-1.
"""

from __future__ import annotations

import ipaddress
import json
from typing import Dict, List

from cabling import compute_switch_ports
from model import CABINETS, DROPS, PT_DIR, SERVERS, drop_length_m
from vlsm import STATIC_HOSTS, SUBNET_BY_NAME, validate_addressing


def build_master_plan() -> Dict:
    validate_addressing()

    # Master logical topology: all 4 routers, full Cebu HQ 3-tier hierarchy + Copper Wall Mounts & Patch Panels,
    # plus Clark & Davao branches with their Patch Panels, Wall Mounts, switches, APs, and representative/full hosts.
    # For PT performance & clean logical/physical readability while maintaining full 3-tier & physical path fidelity:
    # Cebu HQ includes core/distribution/access switches + MDF servers + representative PCs per zone + static IT/POS/Printers + APs,
    # all routed through Copper Patch Panels and Copper Wall Mounts!
    devices: List[Dict] = []
    links: List[Dict] = []

    def add_dev(name: str, model: str, cat: str, site: str, closet: str, x: int, y: int, **extra):
        d = {"name": name, "model": model, "category": cat, "site": site, "closet": closet, "x": x, "y": y}
        d.update(extra)
        devices.append(d)

    def add_link(a: str, pa: str, b: str, pb: str, cable: str = "straight"):
        links.append({"a": a, "port_a": pa, "b": b, "port_b": pb, "cable": cable})

    # --- Central ISP in Cebu ---
    add_dev("ISP-CEBU", "2911", "router", "ISP", "ISP-RACK", 680, 90, modules=[("0/0", "HWIC-2T"), ("0/1", "HWIC-2T"), ("0/2", "HWIC-2T")])

    # --- Building 2: Cebu Flagship HQ (3-Tier Hierarchy + Physical Path PC -> WM -> PP -> SW -> DSW -> CORE -> R-CEBU) ---
    add_dev("R-CEBU",   "2911",      "router",            "CEBU", "MDF",   680, 240, modules=[("0/0", "HWIC-2T")])
    add_dev("SW-CORE",  "3560-24PS", "multilayer_switch", "CEBU", "MDF",   540, 350)
    add_dev("SW-SRV",   "2960-24TT", "switch",            "CEBU", "MDF",   820, 350)
    add_dev("DSW-1",    "3560-24PS", "multilayer_switch", "CEBU", "IDF-1", 400, 460)
    add_dev("DSW-2",    "3560-24PS", "multilayer_switch", "CEBU", "IDF-2", 620, 460)
    add_dev("SW-GAM1",  "2960-24TT", "switch",            "CEBU", "CAB-G", 300, 570)
    add_dev("SW-VIP",   "2960-24TT", "switch",            "CEBU", "CAB-V", 460, 570)
    add_dev("SW-STU",   "2960-24TT", "switch",            "CEBU", "CAB-S", 620, 570)
    add_dev("SW-ADM",   "2960-24TT", "switch",            "CEBU", "IDF-2", 780, 460)

    # Patch Panels in Cebu HQ cabinets
    add_dev("PP-G",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-G", 300, 650)
    add_dev("PP-V",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-V", 460, 650)
    add_dev("PP-S",   "Copper Patch Panel", "patch_panel", "CEBU", "CAB-S", 620, 650)
    add_dev("PP-ADM", "Copper Patch Panel", "patch_panel", "CEBU", "IDF-2", 780, 560)

    # MDF Servers (Static on HQ-SERVER-LAN 10.10.0.96/28)
    add_dev("SRV-1", "Server-PT", "server", "CEBU", "MDF", 900, 440,
            lan="HQ-SERVER-LAN", ip="10.10.0.98", mask="255.255.255.240", gw="10.10.0.97", dns="10.10.0.98",
            ipv6="2001:DB8:ACAD:1003::98", ipv6_prefix=64, ipv6_gw="FE80::1", services=["DHCP", "DNS", "HTTP", "FTP"])
    add_dev("SRV-2", "Server-PT", "server", "CEBU", "MDF", 980, 440,
            lan="HQ-SERVER-LAN", ip="10.10.0.99", mask="255.255.255.240", gw="10.10.0.97", dns="10.10.0.98",
            ipv6="2001:DB8:ACAD:1003::99", ipv6_prefix=64, ipv6_gw="FE80::1", services=["HTTP"])

    # Cebu HQ End Hosts + Wall Mounts (mandatory path PC -> WM -> PP -> Access Switch!)
    hq_hosts = [
        # (host, model, cat, lan, sw, pp, port_idx, wm_name, x, y, static_ip, ipv6)
        ("GAM-01", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-GAM1", "PP-G", 1, "WM-G01", 230, 770, None, None),
        ("GAM-02", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-GAM1", "PP-G", 2, "WM-G02", 310, 770, None, None),
        ("AP-01",  "AccessPoint-PT", "accesspoint", "HQ-GAMING-LAN", "SW-GAM1", "PP-G", 3, "WM-AP1", 370, 770, None, None),
        ("VIP-01", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-VIP",  "PP-V", 1, "WM-V01", 440, 770, None, None),
        ("VIP-02", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-VIP",  "PP-V", 2, "WM-V02", 510, 770, None, None),
        ("STD-01", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-STU",  "PP-S", 1, "WM-S01", 590, 770, None, None),
        ("BRW-01", "PC-PT", "pc", "HQ-GAMING-LAN", "SW-STU",  "PP-S", 2, "WM-B01", 660, 770, None, None),
        ("IT-PC",  "PC-PT", "pc", "HQ-ADMIN-LAN",  "SW-ADM",  "PP-ADM", 1, "WM-IT",  750, 690, "10.10.0.70", "2001:DB8:ACAD:1002::70"),
        ("POS-01", "PC-PT", "pc", "HQ-ADMIN-LAN",  "SW-ADM",  "PP-ADM", 2, "WM-POS", 830, 690, "10.10.0.72", "2001:DB8:ACAD:1002::72"),
        ("PRT-01", "Printer-PT", "printer", "HQ-ADMIN-LAN", "SW-ADM", "PP-ADM", 3, "WM-PRT", 900, 690, "10.10.0.74", "2001:DB8:ACAD:1002::74"),
        ("AP-08",  "AccessPoint-PT", "accesspoint", "HQ-ADMIN-LAN", "SW-ADM", "PP-ADM", 4, "WM-AP8", 970, 690, None, None),
    ]

    # WAN Links (ISP-CEBU <-> 3 Site Routers: Primary + Floating Backup)
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

    for hname, hmod, hcat, lan, sw, pp, pidx, wm, hx, hy, sip, sip6 in hq_hosts:
        spec = SUBNET_BY_NAME[lan]
        add_dev(wm, "Copper Wall Mount", "wall_mount", "CEBU", f"ZONE-{sw}", hx, hy - 55)
        extra = {"lan": lan}
        if sip:
            extra.update({"ip": sip, "mask": str(spec.net4.netmask), "gw": spec.gateway_v4, "dns": "10.10.0.98",
                          "ipv6": sip6, "ipv6_prefix": 64, "ipv6_gw": "FE80::1"})
        elif hcat in ("pc", "printer"):
            extra.update({"dhcp": True, "ipv6_dhcp": True})
        add_dev(hname, hmod, hcat, "CEBU", f"ZONE-{sw}", hx, hy, **extra)
        # Physical path: Switch Fa0/i -> Patch Panel Jack{i} -> PunchDown{i} -> Wall Mount PunchDown1 -> Jack1 -> Host
        host_port = "Port 0" if hcat == "accesspoint" else "FastEthernet0"
        add_link(sw, f"FastEthernet0/{pidx}", pp, f"Jack{pidx}", "straight")
        add_link(pp, f"PunchDown{pidx}", wm, "PunchDown1", "straight")
        add_link(wm, "Jack1", hname, host_port, "straight")

    # --- Building 1: Clark Branch (Luzon — RIPv2 / RIPng + Floating AD 130) ---
    add_dev("R-CLARK",    "2911",               "router",      "CLARK", "CLK-MDF", 160, 240, modules=[("0/0", "HWIC-2T")])
    add_dev("SW-CLK-GAM", "2960-24TT",          "switch",      "CLARK", "CLK-MDF", 80,  380)
    add_dev("SW-CLK-ADM", "2960-24TT",          "switch",      "CLARK", "CLK-MDF", 220, 380)
    add_dev("PP-CLK",     "Copper Patch Panel", "patch_panel", "CLARK", "CLK-MDF", 150, 460)
    add_link("R-CLARK", "GigabitEthernet0/0", "SW-CLK-GAM", "GigabitEthernet0/1", "straight")
    add_link("R-CLARK", "GigabitEthernet0/1", "SW-CLK-ADM", "GigabitEthernet0/1", "straight")

    clk_hosts = [
        ("CLK-GAM-01", "PC-PT", "pc", "CLK-GAMING-LAN", "SW-CLK-GAM", 1, 0, "WM-CG1", 40,  580, None, None),
        ("CLK-GAM-02", "PC-PT", "pc", "CLK-GAMING-LAN", "SW-CLK-GAM", 2, 1, "WM-CG2", 110, 580, None, None),
        ("CLK-IT-PC",  "PC-PT", "pc", "CLK-ADMIN-LAN",  "SW-CLK-ADM", 1, 2, "WM-CI1", 190, 580, "10.10.1.70", "2001:DB8:ACAD:2002::70"),
        ("CLK-POS-01", "PC-PT", "pc", "CLK-ADMIN-LAN",  "SW-CLK-ADM", 2, 3, "WM-CP1", 260, 580, None, None),
    ]
    for hname, hmod, hcat, lan, sw, swp, ppp, wm, hx, hy, sip, sip6 in clk_hosts:
        spec = SUBNET_BY_NAME[lan]
        add_dev(wm, "Copper Wall Mount", "wall_mount", "CLARK", "CLK-FLOOR", hx, hy - 55)
        extra = {"lan": lan}
        if sip:
            extra.update({"ip": sip, "mask": str(spec.net4.netmask), "gw": spec.gateway_v4, "dns": "10.10.0.98",
                          "ipv6": sip6, "ipv6_prefix": 64, "ipv6_gw": "FE80::1"})
        else:
            extra.update({"dhcp": True, "ipv6_dhcp": True})
        add_dev(hname, hmod, hcat, "CLARK", "CLK-FLOOR", hx, hy, **extra)
        add_link(sw, f"FastEthernet0/{swp}", "PP-CLK", f"Jack{ppp + 1}", "straight")
        add_link("PP-CLK", f"PunchDown{ppp + 1}", wm, "PunchDown1", "straight")
        add_link(wm, "Jack1", hname, "FastEthernet0", "straight")

    # --- Building 3: Davao Branch (Mindanao — EIGRP AS 100 / EIGRPv6 + Floating AD 180) ---
    add_dev("R-DAVAO",    "2911",               "router",      "DAVAO", "DVO-MDF", 1180, 240, modules=[("0/0", "HWIC-2T")])
    add_dev("SW-DVO-GAM", "2960-24TT",          "switch",      "DAVAO", "DVO-MDF", 1110, 380)
    add_dev("SW-DVO-ADM", "2960-24TT",          "switch",      "DAVAO", "DVO-MDF", 1250, 380)
    add_dev("PP-DVO",     "Copper Patch Panel", "patch_panel", "DAVAO", "DVO-MDF", 1180, 460)
    add_link("R-DAVAO", "GigabitEthernet0/0", "SW-DVO-GAM", "GigabitEthernet0/1", "straight")
    add_link("R-DAVAO", "GigabitEthernet0/1", "SW-DVO-ADM", "GigabitEthernet0/1", "straight")

    dvo_hosts = [
        ("DVO-GAM-01", "PC-PT", "pc", "DVO-GAMING-LAN", "SW-DVO-GAM", 1, 0, "WM-DG1", 1070, 580, None, None),
        ("DVO-GAM-02", "PC-PT", "pc", "DVO-GAMING-LAN", "SW-DVO-GAM", 2, 1, "WM-DG2", 1140, 580, None, None),
        ("DVO-IT-PC",  "PC-PT", "pc", "DVO-ADMIN-LAN",  "SW-DVO-ADM", 1, 2, "WM-DI1", 1220, 580, "10.10.2.70", "2001:DB8:ACAD:3002::70"),
        ("DVO-POS-01", "PC-PT", "pc", "DVO-ADMIN-LAN",  "SW-DVO-ADM", 2, 3, "WM-DP1", 1290, 580, None, None),
    ]
    for hname, hmod, hcat, lan, sw, swp, ppp, wm, hx, hy, sip, sip6 in dvo_hosts:
        spec = SUBNET_BY_NAME[lan]
        add_dev(wm, "Copper Wall Mount", "wall_mount", "DAVAO", "DVO-FLOOR", hx, hy - 55)
        extra = {"lan": lan}
        if sip:
            extra.update({"ip": sip, "mask": str(spec.net4.netmask), "gw": spec.gateway_v4, "dns": "10.10.0.98",
                          "ipv6": sip6, "ipv6_prefix": 64, "ipv6_gw": "FE80::1"})
        else:
            extra.update({"dhcp": True, "ipv6_dhcp": True})
        add_dev(hname, hmod, hcat, "DAVAO", "DVO-FLOOR", hx, hy, **extra)
        add_link(sw, f"FastEthernet0/{swp}", "PP-DVO", f"Jack{ppp + 1}", "straight")
        add_link("PP-DVO", f"PunchDown{ppp + 1}", wm, "PunchDown1", "straight")
        add_link(wm, "Jack1", hname, "FastEthernet0", "straight")

    # Programmatic assertion: EVERY static host IP in plan is strictly network+1 .. broadcast-1
    for d in devices:
        if "ip" in d and "lan" in d:
            net = SUBNET_BY_NAME[d["lan"]].net4
            addr = ipaddress.IPv4Address(d["ip"])
            assert net.network_address < addr < net.broadcast_address, f"Invalid host IP {d['ip']} on {d['name']}"
            assert d["ip"] != SUBNET_BY_NAME[d["lan"]].gateway_v4, f"{d['name']} collides with gateway"

    # SRV-1 DHCPv4 relay pools (for HQ-GAMING-LAN & HQ-ADMIN-LAN + HQ-SERVER-LAN default)
    srv1_dhcp_pools = [
        {"name": "HQ-GAMING-POOL", "gw": "10.10.0.1",  "dns": "10.10.0.98", "start": "10.10.0.11", "mask": "255.255.255.192", "max_users": 50},
        {"name": "HQ-ADMIN-POOL",  "gw": "10.10.0.65", "dns": "10.10.0.98", "start": "10.10.0.76", "mask": "255.255.255.224", "max_users": 18},
    ]

    plan = {
        "project": "RJ Internet Cafe & Esports Inc. — Multi-Branch Network (Group1)",
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
    return plan


def write_manual_physical_guide() -> None:
    sw_ports = compute_switch_ports()
    lines = [
        "# Packet Tracer Manual Physical Workspace & Screenshot Guide",
        "**Project:** RJ Internet Café & Esports Inc. (`Group1`) — CPE 3105",
        "**Owners:** Marchen Viterbo (Logical Build & Routing) & Andre Merkel Sepe (Physical Workspace, ACLs & Testing)",
        "",
        "---",
        "",
        "## 1. Packet Tracer Files Included (`pt/`)",
        "| File | Scope | Role |",
        "|---|---|---|",
        "| `pt/rj_network.pkt` | All 3 Buildings + `ISP-CEBU` | Master end-to-end simulation & verification topology |",
        "| `pt/rj_cebu_hq_visayas.pkt` | Building 2 — Cebu Flagship HQ + `ISP-CEBU` | Multiuser Host (listens on **TCP 38000**, password `rjesports`) |",
        "| `pt/rj_clark_luzon.pkt` | Building 1 — Clark Branch Café (Luzon) | Multiuser Peer connecting to HQ WAN `WAN-CLARK-PRI` / `BAK` |",
        "| `pt/rj_davao_mindanao.pkt` | Building 3 — Davao Branch Café (Mindanao) | Multiuser Peer connecting to HQ WAN `WAN-DAVAO-PRI` / `BAK` |",
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
        "| Closet 1A | `CLK-MDF` | Main rack inside Clark MDF Room |",
        "| City 2 | `Cebu_Visayas` | `city_cebu.png` |",
        "| Building 2 | `RJ_Cebu_Flagship_HQ` | `floor_hq.png` (40 × 26 m = 1,040 sqm) |",
        "| Building 2B | `Cebu_ISP_POP` | Central ISP node (`ISP-CEBU`) in Cebu City |",
        "| Closets 2A–2F | `MDF`, `IDF-1`, `IDF-2`, `CAB-G`, `CAB-V`, `CAB-S` | Placed on exact cabinet markers on `floor_hq.png` |",
        "| City 3 | `Davao_Mindanao` | `city_davao.png` |",
        "| Building 3 | `RJ_Davao_Branch` | `floor_davao.png` (40 × 26 m = 1,040 sqm) |",
        "| Closet 3A | `DVO-MDF` | Main rack inside Davao MDF Room |",
        "",
        "---",
        "",
        "## 3. Exact Device-to-Closet & Drop Placement Table (Cebu Flagship HQ)",
        "Drag each device in **Physical Workspace** directly onto its labeled blue/green drop marker on `floor_hq.png`:",
        "",
        "| Device(s) | Exact Closet / Room | Coordinates on Floor Plate | Mandatory Physical Path |",
        "|---|---|---|---|",
        "| `R-CEBU`, `SW-CORE`, `SW-SRV`, `SRV-1`, `SRV-2` | `MDF` (`MDF-ROOM`) | (20.5 m, 15.5 m) | Rack-mounted in 42U MDF cabinet |",
        "| `DSW-1` (3560-24PS) | `IDF-1` (`FUT-GAME` corner) | (18.6 m, 11.4 m) | OM3 fiber to `MDF` `SW-CORE`; **zero PCs directly on `DSW-1`** |",
        "| `DSW-2` (3560-24PS), `SW-ADM` (2960-24TT), `PP-ADM` | `IDF-2` (`ADMIN-OFC`) | (27.6 m, 14.6 m) | OM3 fiber to `MDF` `SW-CORE`; `SW-ADM` feeds Admin/POS drops |",
        "| `SW-GAM1` (2960-24TT), `PP-G` | `CAB-G` (`STD-GAME`) | (17.4 m, 6.0 m) | `GAM-01..20` & `AP-01..02` → Wall Mount → `PP-G` → `SW-GAM1` |",
        "| `SW-VIP` (2960-24TT), `PP-V` | `CAB-V` (`VIP-ARENA`) | (26.6 m, 6.0 m) | `VIP-01..10` & `AP-03..04` → Wall Mount → `PP-V` → `SW-VIP` |",
        "| `SW-STU` (2960-24TT), `PP-S` | `CAB-S` (`STUDY-PODS`) | (17.4 m, 18.0 m) | `STD-01..04`, `BRW-01..02`, `AP-05..07` → Wall Mount → `PP-S` → `SW-STU` |",
        "| `IT-PC`, `POS-01`, `PRT-01`, `AP-08` | `ADMIN-OFC` / `CASH-LOBBY` | See Sheet `C-1` markers | Host → Wall Mount → `PP-ADM` → `SW-ADM` → `R-CEBU Gi0/1` |",
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
        "   `PC -> Copper Wall Mount (Jack 0 / PunchDown 0) -> Copper Patch Panel (PunchDown N / Jack N) -> Access Switch -> Distribution Switch -> Core Switch -> Router`.",
        "3. **No diagonal cables:** Right-click any copper wire running across a room → select **Create Bend Point** and drag the vertex along room perimeter walls and the central 2.0 m corridor (`Y = 12.45 m` north tray).",
        "4. Hover over each horizontal cable run to confirm length **≤ 90 m permanent link** (**≤ 100 m total channel**). All designed Cebu HQ drops measure **12.7 m – 39.3 m** (zero repeaters required).",
        "5. **Multiuser Linking (optional live split demo):** On `rj_cebu_hq_visayas.pkt`, open **Extensions → Multiuser → Listen** on **TCP port `38000`** (`Allow New Remote Networks: Always Allow`, password `rjesports`). On `rj_clark_luzon.pkt` and `rj_davao_mindanao.pkt`, connect their Multiuser Cloud (`Peer0`) to `127.0.0.1:38000`.",
        "",
        "---",
        "",
        "## 5. Exact 6-Screenshot Capture Checklist (Auto-Embed Pipeline)",
        "Save screenshots using these **exact filenames** inside `report/screenshots/`, then run ONE rebuild command to regenerate the `.docx` and `.pdf` with updated TOC, List of Figures, and List of Tables:",
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
    print(f"Generated pt/rj_plan.json ({len(plan['devices'])} devices, {len(plan['links'])} links) & pt/PT_MANUAL_PHYSICAL_GUIDE.md")


if __name__ == "__main__":
    main()
