"""Single source of truth for RJ Internet Cafe & Esports Inc. (Cebu Flagship HQ & 3-Branch Network).

All room geometries (40.0 m x 26.0 m = 1,040.0 sqm), workstation drops, ceiling APs,
cabinets, dedicated appliances, AC units, switches, and project metadata live here so
Architectural (A-1..A-3), Electrical (E-1, E-2), Lighting (L-1), Cabling (C-1, C-2),
VLSM/IPv6/ACL, Packet Tracer, Excel Budget, and Word Report maintain strict 1-to-1 parity.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Tuple

BASE_DIR = Path(r"D:\Junior Year\first sem\COMPUTER NETWORKS AND SECURITY\RJ esports")
PLANS_DIR = BASE_DIR / "plans"
DRAWIO_DIR = PLANS_DIR / "drawio"
SVG_DIR = PLANS_DIR / "svg"
SHEETS_DIR = PLANS_DIR / "sheets"
BUDGET_DIR = BASE_DIR / "budget"
PT_DIR = BASE_DIR / "pt"
CLI_DIR = PT_DIR / "cli"
BG_DIR = PT_DIR / "backgrounds"
REPORT_DIR = BASE_DIR / "report"
FIGS_DIR = REPORT_DIR / "figs"
SCREENSHOTS_DIR = REPORT_DIR / "screenshots"

# Project identity
GROUP_ID = "Group1"
GROUP_DISPLAY = "Group 1"
ORG_NAME = "RJ Internet Café & Esports Inc."
ORG_SHORT = "RJ Esports"
COURSE = "CPE 3105 – Computer Networks and Security"
INSTRUCTOR = "Dr. Godwin S. Monserate"
SUBMISSION_DATE = "November 29, 2026"
PRESENTATION_DATES = "December 1–4, 2026"
PRICE_DATE = "Nov 2026"
CEILING_HEIGHT_M = 3.2

BUILDING_W_M = 40.0
BUILDING_H_M = 26.0
BUILDING_AREA_SQM = BUILDING_W_M * BUILDING_H_M  # 1,040.0 sqm

MEMBERS = [
    ("Francis RJ Velasco", "Research, Organization Profile, Floor Plan (Sheets A-1, A-2), Chapters 1–2"),
    ("Armanpreet Talwar", "Furniture & Fixtures (Sheet A-3), Electrical Plan (Sheets E-1, E-2), Costing"),
    ("Marianito Roble", "Lighting Plan (Sheet L-1), Structured Cabling Plan (Sheets C-1, C-2), Consolidated Budget"),
    ("Marchen Viterbo", "VLSM/IPv6 Addressing, Routing & Redistribution (RIPv2, EIGRP, Static/Floating), Router/Switch CLI & Packet Tracer Logical Build"),
    ("Andre Merkel Sepe", "Network Security (IPv4/IPv6 ACLs, SSH Hardening), Packet Tracer Physical Workspace, Connectivity Testing, Troubleshooting & Verification"),
]

SITES = [
    {
        "code": "BLDG-1",
        "name": "Clark Branch Café (Luzon)",
        "region": "Luzon",
        "location": "Clark Freeport Zone, Angeles City, Pampanga",
        "role": "Branch Commercial Internet Café & Gaming Hub",
        "area_sqm": 1040,
        "source": "Conceptual (Group 1, 2026; 40 × 26 m plate)",
        "router": "R-CLARK",
        "protocol": "RIPv2 / RIPng + Floating Static (AD 130)",
        "lat": 15.1859,
        "lon": 120.5597,
        "pcs": 20,
        "aps": 4,
    },
    {
        "code": "BLDG-2",
        "name": "Cebu Flagship HQ & Esports Arena (Visayas)",
        "region": "Visayas",
        "location": "Cebu IT Park, Apas, Cebu City, Cebu",
        "role": "Flagship HQ, Esports Bootcamp Arena & ISP Convergence (Selected Detailed Site)",
        "area_sqm": 1040,
        "source": "Conceptual (Group 1, 2026; 40 × 26 m plate)",
        "router": "R-CEBU",
        "protocol": "Static Default + ISP Summary Route",
        "lat": 10.3303,
        "lon": 123.9064,
        "pcs": 42,
        "aps": 8,
    },
    {
        "code": "BLDG-3",
        "name": "Davao Branch Café (Mindanao)",
        "region": "Mindanao",
        "location": "Matina IT Park / Poblacion District, Davao City",
        "role": "Branch Commercial Internet Café & Gaming Hub",
        "area_sqm": 1040,
        "source": "Conceptual (Group 1, 2026; 40 × 26 m plate)",
        "router": "R-DAVAO",
        "protocol": "EIGRP AS 100 / EIGRPv6 + Floating Static (AD 180)",
        "lat": 7.0731,
        "lon": 125.6128,
        "pcs": 20,
        "aps": 4,
    },
]


def php_round(val: float | int | Decimal) -> Decimal:
    """Standard half-up rounding to 2 decimal places (used identically in Excel & Word)."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def php_int(val: float | int | Decimal) -> int:
    """Standard half-up rounding to nearest whole PHP."""
    return int(Decimal(str(val)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fmt_php(val: float | int | Decimal, decimals: int = 2) -> str:
    q = Decimal("0.01") if decimals == 2 else Decimal("1")
    d = Decimal(str(val)).quantize(q, rounding=ROUND_HALF_UP)
    return f"₱{d:,.{decimals}f}"


@dataclass(frozen=True)
class Room:
    code: str
    name: str
    short: str
    x: float
    y: float
    w: float
    h: float
    zone_color: str
    target_lux: int
    base_building: bool = False
    dimmable_zone: bool = False
    flooring: str = "Porcelain Tile 600×600"

    @property
    def area(self) -> float:
        return round(self.w * self.h, 2)

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0


# Exact non-overlapping tiling of 40.0 m x 26.0 m = 1,040.0 sqm
ROOMS: List[Room] = [
    # North Wing (Y = 0..12, 480 sqm)
    Room("STD-GAME", "Standard Gaming Zone", "Standard Gaming\n(20 PCs)", 0.0, 0.0, 18.0, 12.0, "#E3F2FD", 300, dimmable_zone=True, flooring="Commercial Vinyl Plank"),
    Room("FUT-GAME", "Future Gaming Bay (10 Seats)", "Future Gaming\nBay (10 Seats)", 18.0, 0.0, 8.0, 12.0, "#EDF7ED", 300, dimmable_zone=True, flooring="Commercial Vinyl Plank"),
    Room("VIP-ARENA", "VIP / Esports Bootcamp Arena", "VIP / Esports\nArena (10 PCs)", 26.0, 0.0, 10.0, 12.0, "#EDE7F6", 300, dimmable_zone=True, flooring="Acoustic Carpet Tile"),
    Room("STAIR-NE", "Fire Exit Stairwell (East)", "Fire Exit\nEast", 36.0, 0.0, 4.0, 6.0, "#ECEFF1", 150, base_building=True, flooring="Base Concrete"),
    Room("ELEV-CORE", "Passenger Elevator & Shaft", "Elevator\nCore", 36.0, 6.0, 4.0, 6.0, "#ECEFF1", 150, base_building=True, flooring="Base Concrete"),

    # Central Corridor Spine (Y = 12..14, 80 sqm)
    Room("COR-MAIN", "Main Circulation Corridor (2.0 m)", "Main Corridor (2.0 m Clear — Fire Exit West)", 0.0, 12.0, 36.0, 2.0, "#F5F5F5", 150, flooring="Porcelain Tile 600×600"),
    Room("COR-EAST", "East Exit Vestibule", "East\nVest.", 36.0, 12.0, 4.0, 2.0, "#F5F5F5", 150, flooring="Porcelain Tile 600×600"),

    # South Wing (Y = 14..26, 480 sqm)
    Room("CASH-LOBBY", "Cashier, Printing & Browsing Lobby", "Cashier / POS,\nPrinting & Browsing", 0.0, 14.0, 10.0, 12.0, "#FFF8E1", 500, flooring="Porcelain Tile 600×600"),
    Room("STUDY-PODS", "Study & Work Pods", "Study & Work\nPods (4 PCs)", 10.0, 14.0, 8.0, 12.0, "#E8F5E9", 500, flooring="Acoustic Carpet Tile"),
    Room("MDF-ROOM", "Central MDF / Server Room", "Central MDF /\nServer Room", 18.0, 14.0, 5.0, 6.0, "#FFEBEE", 500, flooring="Anti-Static ESD Vinyl"),
    Room("ELEC-ROOM", "Main Electrical Room", "Electrical\nRoom", 23.0, 14.0, 4.0, 6.0, "#FBE9E7", 300, flooring="Epoxy Non-Slip"),
    Room("ADMIN-OFC", "Admin / Manager & IT Office", "Admin / IT\nOffice (4 PCs)", 27.0, 14.0, 6.0, 6.0, "#E0F2F1", 500, flooring="Commercial Vinyl Plank"),
    Room("RR-M", "Men's Restroom", "Restroom\n(M)", 33.0, 14.0, 3.5, 6.0, "#E0F7FA", 200, flooring="Anti-Slip Ceramic Tile"),
    Room("RR-F", "Women's Restroom", "Restroom\n(F)", 36.5, 14.0, 3.5, 6.0, "#E0F7FA", 200, flooring="Anti-Slip Ceramic Tile"),
    Room("CAFE-PNT", "Café & Snack Pantry", "Café & Snack\nPantry", 18.0, 20.0, 9.0, 6.0, "#FFF3E0", 300, flooring="Porcelain Tile 600×600"),
    Room("STAFF-LNG", "Staff Lounge", "Staff\nLounge", 27.0, 20.0, 6.0, 6.0, "#F3E5F5", 200, flooring="Commercial Vinyl Plank"),
    Room("RR-PWD", "PWD Restroom", "PWD\nRR", 33.0, 20.0, 2.5, 6.0, "#E0F7FA", 200, flooring="Anti-Slip Ceramic Tile"),
    Room("JANITOR", "Janitor's Closet", "Jan.", 35.5, 20.0, 2.0, 6.0, "#EFEBE9", 200, flooring="Anti-Slip Ceramic Tile"),
    Room("STORAGE", "Equipment & Supplies Storage", "Stor.", 37.5, 20.0, 2.5, 6.0, "#EFEBE9", 200, flooring="Epoxy Non-Slip"),
]

ROOM_BY_CODE = {r.code: r for r in ROOMS}

# Validate exact 1,040 sqm tiling immediately on import
assert abs(sum(r.area for r in ROOMS) - BUILDING_AREA_SQM) < 1e-6, "Room areas must sum to 1,040.0 sqm"

# Original Shell (Before Modification — Sheet A-1):
# Base commercial shell leased at Cebu IT Park: open tenant shell (36 x 26 m) + East base core (4 x 12 m) + shell restrooms stub.
ORIGINAL_ZONES = [
    ("OPEN-SHELL-N", "Unpartitioned Open Commercial Floor (North)", 0.0, 0.0, 36.0, 14.0, "#FAFAFA"),
    ("OPEN-SHELL-S", "Unpartitioned Open Commercial Floor (South)", 0.0, 14.0, 23.0, 12.0, "#FAFAFA"),
    ("BASE-ELEC", "Base-Building Electrical Stub-In", 23.0, 14.0, 4.0, 6.0, "#F5F5F5"),
    ("OPEN-SHELL-SE", "Unpartitioned Back-of-House Shell", 27.0, 14.0, 13.0, 12.0, "#FAFAFA"),
    ("BASE-STAIR", "Base-Building Fire Exit Stairwell (East)", 36.0, 0.0, 4.0, 6.0, "#ECEFF1"),
    ("BASE-ELEV", "Base-Building Passenger Elevator Shaft", 36.0, 6.0, 4.0, 6.0, "#ECEFF1"),
    ("BASE-VEST", "Base-Building East Lobby Vestibule", 36.0, 12.0, 4.0, 2.0, "#ECEFF1"),
]

# Telecommunications Enclosures / Cabinets (exact floor positions in meters)
CABINETS = {
    "MDF": {"name": "MDF (42U Floor Rack)", "room": "MDF-ROOM", "x": 20.5, "y": 15.5, "role": "Core Layer — R-CEBU, SW-CORE (3560-24PS), SW-SRV (2960-24TT), SRV-1, SRV-2, PP-MDF"},
    "IDF-1": {"name": "IDF-1 (12U Wall Cabinet)", "room": "FUT-GAME", "x": 18.6, "y": 11.4, "role": "Distribution Layer North — DSW-1 (3560-24PS), Fiber Patch Panel"},
    "IDF-2": {"name": "IDF-2 (12U Wall Cabinet)", "room": "ADMIN-OFC", "x": 27.6, "y": 14.6, "role": "Distribution Layer South — DSW-2 (3560-24PS), SW-ADM (2960-24TT), PP-ADM"},
    "CAB-G": {"name": "CAB-G (9U Wall Cabinet)", "room": "STD-GAME", "x": 17.4, "y": 6.0, "role": "Access Layer Gaming — SW-GAM1 (2960-24TT), PP-G (24-port)"},
    "CAB-V": {"name": "CAB-V (9U Wall Cabinet)", "room": "VIP-ARENA", "x": 26.6, "y": 6.0, "role": "Access Layer VIP Arena — SW-VIP (2960-24TT), PP-V (24-port)"},
    "CAB-S": {"name": "CAB-S (9U Wall Cabinet)", "room": "STUDY-PODS", "x": 17.4, "y": 18.0, "role": "Access Layer Study/Lobby — SW-STU (2960-24TT), PP-S (24-port)"},
}


@dataclass(frozen=True)
class Drop:
    drop_id: str
    device: str
    kind: str         # Gaming-PC | VIP-PC | Study-PC | Browsing-PC | Admin-PC | POS-PC | Printer | AP
    room: str
    lan: str          # HQ-GAMING-LAN | HQ-ADMIN-LAN
    cabinet: str      # CAB-G | CAB-V | CAB-S | IDF-2
    switch: str       # SW-GAM1 | SW-VIP | SW-STU | SW-ADM
    sw_port: str      # Fa0/1..Fa0/24
    pp_id: str        # PP-G | PP-V | PP-S | PP-ADM
    pp_port: int
    x: float
    y: float
    watt: int         # Electrical power draw (W)
    ip_mode: str      # DHCP | Static
    static_ip: str = ""
    static_ipv6: str = ""


def _build_drops() -> List[Drop]:
    drops: List[Drop] = []

    # 1. Standard Gaming Zone: 20 PCs (4 rows x 5 cols inside X=1.8..15.8, Y=2.0..10.2)
    idx = 0
    xs_gam = [2.2, 5.2, 8.2, 11.2, 14.2]
    ys_gam = [2.2, 4.6, 7.2, 9.6]
    for r_i, yy in enumerate(ys_gam):
        for c_i, xx in enumerate(xs_gam):
            idx += 1
            drops.append(Drop(
                drop_id=f"G-{idx:02d}",
                device=f"GAM-{idx:02d}",
                kind="Gaming-PC",
                room="STD-GAME",
                lan="HQ-GAMING-LAN",
                cabinet="CAB-G",
                switch="SW-GAM1",
                sw_port=f"FastEthernet0/{idx}",
                pp_id="PP-G",
                pp_port=idx,
                x=xx,
                y=yy,
                watt=550,
                ip_mode="DHCP",
            ))

    # 2 Ceiling APs in Standard Gaming Zone on SW-GAM1 (ports 21, 22 -> 22 used, 2 spare)
    drops.append(Drop("AP-01", "AP-01", "AP", "STD-GAME", "HQ-GAMING-LAN", "CAB-G", "SW-GAM1", "FastEthernet0/21", "PP-G", 21, 5.5, 6.0, 15, "DHCP"))
    drops.append(Drop("AP-02", "AP-02", "AP", "STD-GAME", "HQ-GAMING-LAN", "CAB-G", "SW-GAM1", "FastEthernet0/22", "PP-G", 22, 13.0, 6.0, 15, "DHCP"))

    # 2. VIP / Esports Bootcamp Arena: 10 PCs (2 facing 5v5 teams inside X=27.5..35.0, Y=2.5..9.5)
    ys_vip = [2.2, 4.0, 5.8, 7.6, 9.4]
    for side_i, xx in enumerate([28.6, 33.4]):
        for s_i, yy in enumerate(ys_vip):
            v_num = side_i * 5 + s_i + 1
            drops.append(Drop(
                drop_id=f"V-{v_num:02d}",
                device=f"VIP-{v_num:02d}",
                kind="VIP-PC",
                room="VIP-ARENA",
                lan="HQ-GAMING-LAN",
                cabinet="CAB-V",
                switch="SW-VIP",
                sw_port=f"FastEthernet0/{v_num}",
                pp_id="PP-V",
                pp_port=v_num,
                x=xx,
                y=yy,
                watt=650,
                ip_mode="DHCP",
            ))

    # 2 Ceiling APs on SW-VIP (AP-03 in Future Gaming Bay, AP-04 in VIP Arena -> 12 used, 12 spare)
    drops.append(Drop("AP-03", "AP-03", "AP", "FUT-GAME", "HQ-GAMING-LAN", "CAB-V", "SW-VIP", "FastEthernet0/11", "PP-V", 11, 22.0, 6.0, 15, "DHCP"))
    drops.append(Drop("AP-04", "AP-04", "AP", "VIP-ARENA", "HQ-GAMING-LAN", "CAB-V", "SW-VIP", "FastEthernet0/12", "PP-V", 12, 31.0, 6.0, 15, "DHCP"))

    # 3. Study & Work Pods (4 PCs) + Quick Browsing Kiosks (2 PCs) + 3 Customer APs on SW-STU (9 used, 15 spare)
    study_coords = [(12.2, 16.5), (15.5, 16.5), (12.2, 22.0), (15.5, 22.0)]
    for i, (xx, yy) in enumerate(study_coords, 1):
        drops.append(Drop(f"S-{i:02d}", f"STD-{i:02d}", "Study-PC", "STUDY-PODS", "HQ-GAMING-LAN", "CAB-S", "SW-STU", f"FastEthernet0/{i}", "PP-S", i, xx, yy, 250, "DHCP"))

    drops.append(Drop("B-01", "BRW-01", "Browsing-PC", "CASH-LOBBY", "HQ-GAMING-LAN", "CAB-S", "SW-STU", "FastEthernet0/5", "PP-S", 5, 6.8, 16.5, 200, "DHCP"))
    drops.append(Drop("B-02", "BRW-02", "Browsing-PC", "CASH-LOBBY", "HQ-GAMING-LAN", "CAB-S", "SW-STU", "FastEthernet0/6", "PP-S", 6, 8.6, 16.5, 200, "DHCP"))
    drops.append(Drop("AP-05", "AP-05", "AP", "CASH-LOBBY", "HQ-GAMING-LAN", "CAB-S", "SW-STU", "FastEthernet0/7", "PP-S", 7, 5.0, 20.0, 15, "DHCP"))
    drops.append(Drop("AP-06", "AP-06", "AP", "STUDY-PODS", "HQ-GAMING-LAN", "CAB-S", "SW-STU", "FastEthernet0/8", "PP-S", 8, 14.0, 19.5, 15, "DHCP"))
    drops.append(Drop("AP-07", "AP-07", "AP", "CAFE-PNT", "HQ-GAMING-LAN", "CAB-S", "SW-STU", "FastEthernet0/9", "PP-S", 9, 22.5, 23.0, 15, "DHCP"))

    # 4. Admin, Cashier/POS, Staff & Printers + 1 Staff AP on SW-ADM in IDF-2 (9 used, 15 spare)
    adm_items = [
        ("A-01", "IT-PC",  "Admin-PC", "ADMIN-OFC",  28.5, 16.2, 300, "Static", "10.10.0.70", "2001:DB8:ACAD:1002::70"),
        ("A-02", "MGR-PC", "Admin-PC", "ADMIN-OFC",  31.5, 16.2, 250, "Static", "10.10.0.71", "2001:DB8:ACAD:1002::71"),
        ("A-03", "STF-01", "Admin-PC", "ADMIN-OFC",  28.5, 18.6, 250, "DHCP",   "",           ""),
        ("A-04", "STF-02", "Admin-PC", "ADMIN-OFC",  31.5, 18.6, 250, "DHCP",   "",           ""),
        ("A-05", "POS-01", "POS-PC",   "CASH-LOBBY",  2.2, 16.2, 250, "Static", "10.10.0.72", "2001:DB8:ACAD:1002::72"),
        ("A-06", "POS-02", "POS-PC",   "CASH-LOBBY",  4.2, 16.2, 250, "Static", "10.10.0.73", "2001:DB8:ACAD:1002::73"),
        ("A-07", "PRT-01", "Printer",  "CASH-LOBBY",  2.2, 19.0, 600, "Static", "10.10.0.74", "2001:DB8:ACAD:1002::74"),
        ("A-08", "PRT-02", "Printer",  "CASH-LOBBY",  4.2, 19.0, 600, "Static", "10.10.0.75", "2001:DB8:ACAD:1002::75"),
        ("AP-08", "AP-08", "AP",       "ADMIN-OFC",  30.0, 17.5,  15, "DHCP",   "",           ""),
    ]
    for i, (did, dev, kind, rm, xx, yy, w, mode, sip, sip6) in enumerate(adm_items, 1):
        drops.append(Drop(did, dev, kind, rm, "HQ-ADMIN-LAN", "IDF-2", "SW-ADM", f"FastEthernet0/{i}", "PP-ADM", i, xx, yy, w, mode, sip, sip6))

    return drops


DROPS: List[Drop] = _build_drops()

# Verify drop parity counts
assert len(DROPS) == 52, f"Expected 52 horizontal drops, got {len(DROPS)}"
assert sum(1 for d in DROPS if d.kind.endswith("PC")) == 42
assert sum(1 for d in DROPS if d.kind == "Printer") == 2
assert sum(1 for d in DROPS if d.kind == "AP") == 8

# MDF Rack Servers (patched in-rack on SW-SRV)
SERVERS = [
    {"id": "SRV-1", "role": "DNS, Web Portal & DHCPv4 Server", "room": "MDF-ROOM", "lan": "HQ-SERVER-LAN", "ip": "10.10.0.98", "ipv6": "2001:DB8:ACAD:1003::98", "watt": 450},
    {"id": "SRV-2", "role": "Billing/POS & Game-Cache Server", "room": "MDF-ROOM", "lan": "HQ-SERVER-LAN", "ip": "10.10.0.99", "ipv6": "2001:DB8:ACAD:1003::99", "watt": 550},
]

# Dedicated Appliances (1-to-1 parity between electrical.py and furniture.py!)
APPLIANCES = [
    {"id": "APP-MW1", "name": "Commercial Microwave Oven (1,200 W)", "room": "CAFE-PNT", "x": 19.5, "y": 21.2, "watt": 1200, "qty": 1, "unit_php": 7495, "source": "Abenson PH (Nov 2026)"},
    {"id": "APP-RF1", "name": "Commercial Glass-Door Beverage Chiller (350 L)", "room": "CAFE-PNT", "x": 21.8, "y": 21.2, "watt": 380, "qty": 1, "unit_php": 28995, "source": "Abenson / Fujidenzo PH (Nov 2026)"},
    {"id": "APP-RF2", "name": "Two-Door Inverter Pantry Refrigerator (250 L)", "room": "CAFE-PNT", "x": 23.6, "y": 21.2, "watt": 220, "qty": 1, "unit_php": 21495, "source": "Abenson / Midea PH (Nov 2026)"},
    {"id": "APP-ESP", "name": "Commercial Espresso & Coffee Maker (1,450 W)", "room": "CAFE-PNT", "x": 25.4, "y": 21.2, "watt": 1450, "qty": 1, "unit_php": 32500, "source": "Lazada Mall PH (Nov 2026)"},
    {"id": "APP-WTR1", "name": "Hot & Cold Water Dispenser (Café Pantry)", "room": "CAFE-PNT", "x": 26.2, "y": 24.5, "watt": 550, "qty": 1, "unit_php": 7995, "source": "Abenson / Fujidenzo PH (Nov 2026)"},
    {"id": "APP-WTR2", "name": "Hot & Cold Water Dispenser (Staff Lounge)", "room": "STAFF-LNG", "x": 32.0, "y": 21.2, "watt": 550, "qty": 1, "unit_php": 7995, "source": "Abenson / Fujidenzo PH (Nov 2026)"},
    {"id": "APP-TV1", "name": "65\" 4K Smart Spectator Display TV (VIP Arena North)", "room": "VIP-ARENA", "x": 31.0, "y": 0.6, "watt": 180, "qty": 1, "unit_php": 36995, "source": "Abenson / TCL PH (Nov 2026)"},
    {"id": "APP-TV2", "name": "65\" 4K Smart Spectator Display TV (VIP Arena South)", "room": "VIP-ARENA", "x": 31.0, "y": 11.4, "watt": 180, "qty": 1, "unit_php": 36995, "source": "Abenson / TCL PH (Nov 2026)"},
    {"id": "APP-TV3", "name": "55\" 4K Digital Rate-Board & Menu TV (Lobby)", "room": "CASH-LOBBY", "x": 5.0, "y": 14.5, "watt": 140, "qty": 1, "unit_php": 24995, "source": "Abenson / TCL PH (Nov 2026)"},
]

# Air-Conditioning Units (1-to-1 parity between electrical.py Panel ACP and furniture.py!)
AC_UNITS = [
    {"id": "AC-01", "room": "STD-GAME",   "model": "Midea 5.0 HP Floor-Standing Inverter AC", "hp": 5.0, "va": 4600, "amps": 20.0, "breaker": 30, "x": 1.0,  "y": 0.8,  "unit_php": 124995, "source": "Midea PH / Abenson (Nov 2026)"},
    {"id": "AC-02", "room": "STD-GAME",   "model": "Midea 5.0 HP Floor-Standing Inverter AC", "hp": 5.0, "va": 4600, "amps": 20.0, "breaker": 30, "x": 16.5, "y": 0.8,  "unit_php": 124995, "source": "Midea PH / Abenson (Nov 2026)"},
    {"id": "AC-03", "room": "FUT-GAME",   "model": "Midea 3.0 HP Floor-Standing Inverter AC", "hp": 3.0, "va": 3220, "amps": 14.0, "breaker": 20, "x": 22.0, "y": 0.8,  "unit_php": 84995,  "source": "Midea PH / Abenson (Nov 2026)"},
    {"id": "AC-04", "room": "VIP-ARENA",  "model": "Midea 5.0 HP Floor-Standing Inverter AC", "hp": 5.0, "va": 4600, "amps": 20.0, "breaker": 30, "x": 35.0, "y": 0.8,  "unit_php": 124995, "source": "Midea PH / Abenson (Nov 2026)"},
    {"id": "AC-05", "room": "CASH-LOBBY", "model": "Midea 3.0 HP Floor-Standing Inverter AC", "hp": 3.0, "va": 3220, "amps": 14.0, "breaker": 20, "x": 0.8,  "y": 24.8, "unit_php": 84995,  "source": "Midea PH / Abenson (Nov 2026)"},
    {"id": "AC-06", "room": "STUDY-PODS", "model": "Daikin 2.5 HP Split-Type Inverter AC",    "hp": 2.5, "va": 2530, "amps": 11.0, "breaker": 20, "x": 14.0, "y": 25.2, "unit_php": 62500,  "source": "Daikin PH / Wilcon (Nov 2026)"},
    {"id": "AC-07", "room": "MDF-ROOM",   "model": "Daikin 2.0 HP Split-Type Inverter AC (24/7 Duty)", "hp": 2.0, "va": 2070, "amps": 9.0,  "breaker": 20, "x": 20.5, "y": 19.4, "unit_php": 52995,  "source": "Daikin PH / Wilcon (Nov 2026)"},
    {"id": "AC-08", "room": "MDF-ROOM",   "model": "Daikin 2.0 HP Split-Type Inverter AC (Redundant)", "hp": 2.0, "va": 2070, "amps": 9.0,  "breaker": 20, "x": 22.0, "y": 19.4, "unit_php": 52995,  "source": "Daikin PH / Wilcon (Nov 2026)"},
    {"id": "AC-09", "room": "ADMIN-OFC",  "model": "Daikin 2.0 HP Split-Type Inverter AC",    "hp": 2.0, "va": 2070, "amps": 9.0,  "breaker": 20, "x": 30.0, "y": 19.4, "unit_php": 52995,  "source": "Daikin PH / Wilcon (Nov 2026)"},
    {"id": "AC-10", "room": "CAFE-PNT",   "model": "Daikin 2.5 HP Split-Type Inverter AC",    "hp": 2.5, "va": 2530, "amps": 11.0, "breaker": 20, "x": 22.5, "y": 25.2, "unit_php": 62500,  "source": "Daikin PH / Wilcon (Nov 2026)"},
    {"id": "AC-11", "room": "STAFF-LNG",  "model": "Daikin 1.5 HP Split-Type Inverter AC",    "hp": 1.5, "va": 1610, "amps": 7.0,  "breaker": 20, "x": 30.0, "y": 25.2, "unit_php": 42995,  "source": "Daikin PH / Wilcon (Nov 2026)"},
]


def manhattan_cable_len_m(x1: float, y1: float, x2: float, y2: float, rise_drop_m: float = 6.5, slack_m: float = 3.0) -> float:
    """Orthogonal wall/corridor pathway length in meters + vertical rise/drop + service slack."""
    horiz = abs(x2 - x1) + abs(y2 - y1)
    return round(horiz + rise_drop_m + slack_m, 1)


def drop_length_m(d: Drop) -> float:
    cab = CABINETS[d.cabinet]
    # APs are ceiling-mounted (less vertical drop)
    rise = 3.5 if d.kind == "AP" else 6.5
    return manhattan_cable_len_m(d.x, d.y, cab["x"], cab["y"], rise_drop_m=rise, slack_m=3.0)


# Validate every copper drop <= 90 m permanent link limit
for _d in DROPS:
    _l = drop_length_m(_d)
    assert _l <= 90.0, f"Drop {_d.drop_id} length {_l} m exceeds 90 m TIA-568 limit!"
