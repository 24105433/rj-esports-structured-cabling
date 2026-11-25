"""Structured Cabling Plan (Sheet C-1 Horizontal/Backbone, Sheet C-2 Rack/Riser/Drops) + drop_schedule.csv + Cabling/IT BOQ.

Guardrails enforced:
- Cat6 keystone jacks and factory patch cords budgeted for ALL 52 horizontal drops INCLUDING all 8 ceiling APs + 2 rack servers.
- Telecommunications Grounding Busbar (TMGB in MDF + TGB in IDF-1 & IDF-2) per ANSI/TIA-607-D.
- Every copper drop <= 90 m permanent link limit (verified programmatically).
- Exact 2960-24TT spare access ports = 24 - used Fa drops (Gi0/1 uplink is NOT subtracted from 24 Fa ports).
- Complete 42 workstation PC bundles explicitly specify CPU/GPU/RAM/SSD + monitor + keyboard + mouse + headset at Nov 2026 PHP prices.
"""

from __future__ import annotations

import csv
import math
from decimal import Decimal
from typing import Dict, List

from draw_kit import SheetCanvas, draw_rooms_base, px, py
from model import (
    BUDGET_DIR,
    CABINETS,
    DRAWIO_DIR,
    DROPS,
    PRICE_DATE,
    SERVERS,
    SVG_DIR,
    drop_length_m,
    manhattan_cable_len_m,
    php_round,
)

# Backbone links (MDF -> IDF-1, MDF -> IDF-2 via OM3 fiber; IDF -> Access cabinets via Cat6/Cat6A uplinks)
BACKBONE_LINKS = [
    ("BB-01", "MDF (SW-CORE Gi0/1)", "IDF-1 (DSW-1 Gi0/1)", "6-Core OM3 MMF (10G Ready)", manhattan_cable_len_m(20.5, 15.5, 18.6, 11.4, 4.0, 4.0)),
    ("BB-02", "MDF (SW-CORE Gi0/2)", "IDF-2 (DSW-2 Gi0/1)", "6-Core OM3 MMF (10G Ready)", manhattan_cable_len_m(20.5, 15.5, 27.6, 14.6, 4.0, 4.0)),
    ("BB-03", "MDF (R-CEBU Gi0/1)",  "IDF-2 (SW-ADM Gi0/1)", "Cat6A UTP Uplink (1 Gbps)",  manhattan_cable_len_m(20.5, 15.5, 27.6, 14.6, 4.0, 3.0)),
    ("BB-04", "IDF-1 (DSW-1 Fa0/1)", "CAB-G (SW-GAM1 Gi0/1)", "Cat6A UTP Uplink (1 Gbps)", manhattan_cable_len_m(18.6, 11.4, 17.4, 6.0, 4.0, 3.0)),
    ("BB-05", "IDF-1 (DSW-1 Fa0/2)", "CAB-V (SW-VIP Gi0/1)",  "Cat6A UTP Uplink (1 Gbps)", manhattan_cable_len_m(18.6, 11.4, 26.6, 6.0, 4.0, 3.0)),
    ("BB-06", "IDF-2 (DSW-2 Fa0/1)", "CAB-S (SW-STU Gi0/1)",  "Cat6A UTP Uplink (1 Gbps)", manhattan_cable_len_m(27.6, 14.6, 17.4, 18.0, 4.0, 3.0)),
]


def compute_switch_ports() -> List[Dict]:
    """Exact 2960-24TT spare access port math: spare = 24 - used_fa (uplink uses Gi0/1!)."""
    sw_order = [
        ("SW-GAM1", "CAB-G (Std Gaming)", "Cisco 2960-24TT", "Gi0/1 → DSW-1", sum(1 for d in DROPS if d.switch == "SW-GAM1")),
        ("SW-VIP",  "CAB-V (VIP Arena)",  "Cisco 2960-24TT", "Gi0/1 → DSW-1", sum(1 for d in DROPS if d.switch == "SW-VIP")),
        ("SW-STU",  "CAB-S (Study/Lobby)", "Cisco 2960-24TT", "Gi0/1 → DSW-2", sum(1 for d in DROPS if d.switch == "SW-STU")),
        ("SW-ADM",  "IDF-2 (Admin/POS)",  "Cisco 2960-24TT", "Gi0/1 → R-CEBU Gi0/1", sum(1 for d in DROPS if d.switch == "SW-ADM")),
        ("SW-SRV",  "MDF (Server Rack)",  "Cisco 2960-24TT", "Gi0/1 → R-CEBU Gi0/2", len(SERVERS)),
    ]
    out = []
    for sw, loc, model, uplink, used_fa in sw_order:
        spare_fa = 24 - used_fa
        assert spare_fa >= 0
        out.append({
            "switch": sw,
            "location": loc,
            "model": model,
            "uplink": uplink,
            "used_fa": used_fa,
            "spare_fa": spare_fa,
            "total_fa": 24,
        })
    return out


def write_drop_schedule() -> Dict:
    out = BUDGET_DIR / "drop_schedule.csv"
    total_cat6_m = 0.0
    max_len = 0.0
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Drop ID", "Device", "Type", "Room", "LAN", "Cabinet",
            "Patch Panel", "PP Port", "Switch", "Switch Port",
            "X (m)", "Y (m)", "Est. Length (m)", "TIA-568 <=90m", "IP Mode", "Static IPv4"
        ])
        for d in DROPS:
            ln = drop_length_m(d)
            assert ln <= 90.0
            total_cat6_m += ln
            max_len = max(max_len, ln)
            w.writerow([
                d.drop_id, d.device, d.kind, d.room, d.lan, d.cabinet,
                d.pp_id, d.pp_port, d.switch, d.sw_port,
                f"{d.x:.1f}", f"{d.y:.1f}", f"{ln:.1f}", "PASS", d.ip_mode, d.static_ip or "DHCP"
            ])
    return {
        "count": len(DROPS),
        "total_cat6_m": round(total_cat6_m, 1),
        "max_drop_m": round(max_len, 1),
        "cat6_boxes_305m": math.ceil((total_cat6_m * 1.15) / 305.0),  # +15% waste/trim factor
    }


def write_cabling_boq(drop_stats: Dict) -> List[Dict]:
    n_drops = drop_stats["count"]  # 52 horizontal drops (42 PCs + 2 Printers + 8 APs)
    n_boxes = drop_stats["cat6_boxes_305m"]
    # Keystone jacks: 1 wall/ceiling jack per horizontal drop (52) + 8 spares = 60
    # Patch cords: 2 per horizontal drop (workstation/AP + rack patch = 104) + 2 server patch cords + 4 uplink patch cords = 110!
    n_jacks = n_drops + 8
    n_patch_cords = n_drops * 2 + len(SERVERS) + 4

    items = [
        # Passive Structured Cabling & Grounding (ANSI/TIA-568.2-D, TIA-569-E, TIA-607-D)
        (f"Belden / Panduit Cat6 UTP Solid Copper Cable (23 AWG, CMR, 305 m/box) — {drop_stats['total_cat6_m']:.0f} m + 15% Allowance", n_boxes, "boxes", 7850, f"Lazada Mall / Cablelink PH ({PRICE_DATE})"),
        ("Cat6A Shielded UTP Cable (305 m box) — IDF-to-Access 1G/10G Inter-Cabinet Uplinks", 1, "box", 11500, f"Cablelink PH ({PRICE_DATE})"),
        ("OM3 50/125 µm 6-Core Indoor Multimode Fiber Optic Cable w/ LC-LC Pigtails & 1U LIU — MDF↔IDF-1/IDF-2", 65, "m", 240, f"Fiber Optic PH / Lazada Mall ({PRICE_DATE})"),
        (f"Cat6 RJ45 Keystone Jack (Toolless, TIA-568B) — All {n_drops} Drops (incl. 8 Ceiling APs) + 8 Spares", n_jacks, "pcs", 165, f"Cablelink / Shopee Mall PH ({PRICE_DATE})"),
        (f"Factory-Terminated Cat6 Snagless Patch Cord (1–3 m) — All {n_drops} Drops (×2 Ends) + 2 Servers + 4 Uplinks", n_patch_cords, "pcs", 185, f"Cablelink / Shopee Mall PH ({PRICE_DATE})"),
        ("24-Port Cat6 Rackmount Patch Panel (1U, Rear Cable Management Bar) — PP-G, PP-V, PP-S, PP-ADM, PP-MDF", 5, "units", 3850, f"PC Express / Cablelink PH ({PRICE_DATE})"),
        ("Single/Dual-Port Wall Faceplate & Surface Mount Box w/ Dust Shutter — 44 Wall Drops + 8 Ceiling AP Boxes", n_drops, "sets", 180, f"Wilcon / Cablelink PH ({PRICE_DATE})"),
        ("42U Floor-Standing Enclosed Server Cabinet (800×1000 mm, Perforated, Dual Fans, 12-Outlet PDU) — MDF", 1, "unit", 42500, f"PC Express / Lazada Mall PH ({PRICE_DATE})"),
        ("12U Wall-Mount Lockable Data Cabinet (600×450 mm w/ Fan & 6-Outlet PDU) — IDF-1 & IDF-2", 2, "units", 9800, f"Lazada Mall PH ({PRICE_DATE})"),
        ("9U Wall-Mount Lockable Data Cabinet (600×450 mm w/ Fan & 6-Outlet PDU) — CAB-G, CAB-V, CAB-S", 3, "units", 7800, f"Lazada Mall PH ({PRICE_DATE})"),
        ("Galvanized Wire-Mesh Overhead Data Cable Tray (200×50 mm × 3 m) w/ Threaded Rod Hangers — Corridor Spine", 22, "lengths", 1450, f"Wilcon / CW Home Depot PH ({PRICE_DATE})"),
        ("uPVC Data Conduit (25 mm × 3 m) & Surface Raceway Molding w/ Fittings — Wall Drops & Ceiling AP Stubs", 85, "lengths", 210, f"Wilcon Depot PH ({PRICE_DATE})"),
        ("ANSI/TIA-607-D Copper Telecommunications Grounding Busbar Kit (1× TMGB in MDF, 2× TGB in IDF-1/2 + #6 AWG Bonding)", 1, "lot", 14500, f"Panduit / Cablelink PH ({PRICE_DATE})"),

        # Active Network Devices (Cebu Flagship HQ 3-Tier Hierarchy + ISP Gateway)
        ("Cisco 2911 Integrated Services Router w/ HWIC-2T Serial WAN Module — R-CEBU (HQ Edge Router)", 1, "unit", 48500, f"Cisco PH Partner / Refurb Ent. ({PRICE_DATE})"),
        ("Cisco Catalyst 3560-24PS 24-Port PoE Multilayer Switch w/ SFP — SW-CORE (MDF), DSW-1 (IDF-1), DSW-2 (IDF-2)", 3, "units", 38500, f"Cisco PH Partner / Refurb Ent. ({PRICE_DATE})"),
        ("Cisco Catalyst 2960-24TT 24-Port Access Switch — SW-GAM1, SW-VIP, SW-STU, SW-ADM, SW-SRV", 5, "units", 22500, f"Cisco PH Partner / Refurb Ent. ({PRICE_DATE})"),
        ("1000BASE-SX Multimode SFP Optical Transceiver Module (LC, 850 nm) — MDF↔IDF Fiber Links", 4, "pcs", 2450, f"Cablelink / Cisco Compat. PH ({PRICE_DATE})"),
        ("Ubiquiti UniFi U6+ Dual-Band Wi-Fi 6 Ceiling PoE Access Point (w/ PoE Injector) — AP-01..AP-08", 8, "units", 8950, f"DynaQuest / PC Express PH ({PRICE_DATE})"),
        ("Dell PowerEdge R250 1U Rack Server (Xeon E-2336, 32 GB ECC, 2×1 TB NVMe RAID-1) — SRV-1 (DNS/Web/DHCP)", 1, "unit", 118000, f"PC Express / Dell PH ({PRICE_DATE})"),
        ("Dell PowerEdge R350 1U Rack Server (Xeon E-2378, 64 GB ECC, 4×2 TB NVMe Game-Cache) — SRV-2 (Billing/POS)", 1, "unit", 168000, f"PC Express / Dell PH ({PRICE_DATE})"),

        # End-User IT Workstations & Printers (Strict 1-to-1 Parity: 42 PCs + 2 Printers!)
        ("Standard Gaming PC Bundle (i5-14400F, RTX 4060 8GB, 16GB DDR5, 1TB NVMe + 24\" 180Hz Monitor, Mech KB, Mouse, Headset) — GAM-01..20", 20, "sets", 52500, f"PC Express / DynaQuest PH ({PRICE_DATE})"),
        ("VIP Esports Pro PC Bundle (i7-14700F, RTX 4070 Super 12GB, 32GB DDR5, 1TB NVMe + 27\" 240Hz Monitor, Pro Mech KB, Mouse, Headset) — VIP-01..10", 10, "sets", 84500, f"PC Express / DynaQuest PH ({PRICE_DATE})"),
        ("Study & Work Pod PC Bundle (i5-13400, 16GB RAM, 512GB NVMe + 24\" IPS Monitor, KB, Mouse, Headset) — STD-01..04", 4, "sets", 32500, f"PC Express / DynaQuest PH ({PRICE_DATE})"),
        ("Quick-Browsing Station PC Bundle (i3-13100, 8GB RAM, 512GB SSD + 22\" Monitor, KB, Mouse) — BRW-01..02", 2, "sets", 22500, f"PC Express / DynaQuest PH ({PRICE_DATE})"),
        ("Admin/IT & Cashier/POS PC Bundle (i5-13400, 16GB RAM, 512GB NVMe + 24\" IPS Monitor, KB, Mouse; POS Thermal Printer on POS-01/02) — 6 Sets", 6, "sets", 36500, f"PC Express / DynaQuest PH ({PRICE_DATE})"),
        ("Epson EcoTank L6490 Heavy-Duty Network Multifunction Printer (Ethernet, Print/Scan/Copy/ADF) — PRT-01 & PRT-02", 2, "units", 24995, f"PC Express / Abenson PH ({PRICE_DATE})"),

        # ISP Fiber Subscription & Certification Services
        ("Dedicated Business Fiber Internet (1 Gbps Symmetrical w/ Static IPv4/IPv6 + Backup 200 Mbps Fiber, 1st Yr + Setup)", 1, "lot", 144000, f"PLDT Enterprise / Globe Business Cebu ({PRICE_DATE})"),
        ("Fluke DSX-8000 Cat6 Certification Testing, OTDR Fiber Test, TIA-606-C Labeling & Structured Cabling Labor", 1, "lot", 135000, f"Cebu Structured Cabling Integrator ({PRICE_DATE})"),
    ]

    rows = []
    out = BUDGET_DIR / "cabling_boq.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item / specification", "Quantity", "Unit", "Unit cost (PHP)", "Subtotal (PHP)", "Price source / date"])
        for item, qty, unit, uc, src in items:
            sub = php_round(Decimal(qty) * Decimal(uc))
            w.writerow([item, qty, unit, f"{Decimal(uc):.2f}", f"{sub:.2f}", src])
            rows.append({"item": item, "qty": qty, "unit": unit, "unit_cost": Decimal(uc), "subtotal": sub, "source": src})
    return rows


def generate_sheet_c1(drop_stats: Dict) -> None:
    sc = SheetCanvas(
        sheet_no="C-1",
        sheet_title="STRUCTURED CABLING PLAN — HORIZONTAL, BACKBONE & TR PATHWAYS",
        discipline="Structured Cabling | ANSI/TIA-568.2-D, TIA-569-E, TIA-606-C & TIA-607-D",
        drawn_by="Marianito Roble",
    )
    sc.draw_dimensions_and_grid()
    draw_rooms_base(sc, show_labels=False, muted=True)

    # Overhead 200 mm Wire-Mesh Data Cable Tray along North Edge of Corridor (Y=12.45 m)
    sc.polyline([(px(1.5), py(12.45)), (px(35.0), py(12.45))], stroke="#1D4ED8", stroke_w=3.2)
    sc.text(px(10.0), py(12.45) - 10, "200 mm WIRE-MESH DATA TRAY (Y=12.45 m — ≥1.1 m FROM POWER)", size=7.2, bold=True, color="#1E40AF")

    # OM3 Fiber Backbone (MDF -> IDF-1, MDF -> IDF-2) in bold orange
    mdf = CABINETS["MDF"]
    idf1 = CABINETS["IDF-1"]
    idf2 = CABINETS["IDF-2"]
    sc.polyline([(px(mdf["x"]), py(mdf["y"])), (px(mdf["x"]), py(12.45)), (px(idf1["x"]), py(12.45)), (px(idf1["x"]), py(idf1["y"]))], stroke="#EA580C", stroke_w=2.8)
    sc.polyline([(px(mdf["x"]), py(mdf["y"])), (px(mdf["x"]), py(12.45)), (px(idf2["x"]), py(12.45)), (px(idf2["x"]), py(idf2["y"]))], stroke="#EA580C", stroke_w=2.8)

    # Cat6A Inter-Cabinet Uplinks (IDF-1 -> CAB-G/CAB-V, IDF-2 -> CAB-S) in purple
    for src_k, dst_k in [("IDF-1", "CAB-G"), ("IDF-1", "CAB-V"), ("IDF-2", "CAB-S")]:
        s_c, d_c = CABINETS[src_k], CABINETS[dst_k]
        sc.polyline([(px(s_c["x"]), py(s_c["y"])), (px(d_c["x"]), py(s_c["y"])), (px(d_c["x"]), py(d_c["y"]))], stroke="#7C3AED", stroke_w=2.0, dash="6,3")

    # Orthogonal horizontal Cat6 drops (grouped along row trunk lines to cabinet)
    for d in DROPS:
        cab = CABINETS[d.cabinet]
        # Clean orthogonal L-path from drop to its serving cabinet
        col = "#0284C7" if d.lan == "HQ-GAMING-LAN" else "#059669"
        if d.kind == "AP":
            sc.polyline([(px(d.x), py(d.y)), (px(cab["x"]), py(d.y)), (px(cab["x"]), py(cab["y"]))], stroke="#0EA5E9", stroke_w=0.9, dash="3,2", in_mx=False)
            sc.circle(px(d.x), py(d.y), 8.5, fill="#E0F2FE", stroke="#0369A1", stroke_w=1.4)
            sc.text(px(d.x), py(d.y), d.device, size=6.0, bold=True, color="#0C4A6E")
        else:
            sc.polyline([(px(d.x), py(d.y)), (px(d.x), py(cab["y"])), (px(cab["x"]), py(cab["y"]))], stroke=col, stroke_w=0.85, in_mx=False)
            sc.rect(px(d.x) - 11, py(d.y) - 6.5, 22, 13, fill="#EFF6FF" if d.lan == "HQ-GAMING-LAN" else "#ECFDF5", stroke=col, stroke_w=1.0, rx=1.5)
            sc.text(px(d.x), py(d.y), d.drop_id, size=6.0, bold=True, color="#0F172A")

    # Draw Cabinets (MDF, IDF-1, IDF-2, CAB-G, CAB-V, CAB-S) + TMGB/TGB Grounding
    for k, c in CABINETS.items():
        w_box = 42 if k == "MDF" else 34
        fill_c = "#1E3A8A" if k == "MDF" else ("#7C2D12" if k.startswith("IDF") else "#312E81")
        sc.rect(px(c["x"]) - w_box / 2, py(c["y"]) - 11, w_box, 22, fill=fill_c, stroke="#0F172A", stroke_w=1.4, rx=2)
        sc.text(px(c["x"]), py(c["y"]), k, size=7.5, bold=True, color="#FFFFFF")

    # TIA-607-D Grounding Busbar markers
    sc.rect(px(22.2) - 18, py(15.5) - 7, 36, 14, fill="#DCFCE7", stroke="#15803D", stroke_w=1.2, rx=2)
    sc.text(px(22.2), py(15.5), "TMGB", size=6.5, bold=True, color="#14532D")

    # Sidebar Legend & Cabling Metrics
    sx, sy, sw = sc.sidebar_box("CABLING LEGEND & TIA-568 METRICS")
    leg = [
        ("#1E3A8A", "#0F172A", "MDF (42U Rack): R-CEBU, SW-CORE, SW-SRV, SRV-1/2, TMGB"),
        ("#7C2D12", "#0F172A", "IDF-1 & IDF-2 (12U): DSW-1, DSW-2, SW-ADM, TGB"),
        ("#312E81", "#0F172A", "CAB-G, CAB-V, CAB-S (9U): Access Switches (2960-24TT)"),
        ("#EA580C", "#EA580C", "OM3 6-Core MMF Fiber Backbone (MDF ↔ IDF-1 / IDF-2)"),
        ("#7C3AED", "#7C3AED", "Cat6A UTP Uplinks (IDF → Access Cabinets)"),
        ("#EFF6FF", "#0284C7", "HQ-GAMING-LAN Cat6 Drops (36 PCs + 7 APs)"),
        ("#ECFDF5", "#059669", "HQ-ADMIN-LAN Cat6 Drops (6 PCs + 2 Printers + 1 AP)"),
        ("#E0F2FE", "#0369A1", "Ceiling Wi-Fi 6 PoE Access Points (AP-01..AP-08)"),
        ("#DCFCE7", "#15803D", "ANSI/TIA-607-D Grounding Busbars (TMGB / TGB)"),
    ]
    y = sy
    for fc, ec, txt in leg:
        sc.rect(sx, y - 6, 18, 12, fill=fc, stroke=ec, stroke_w=1.1, rx=1.5)
        sc.text(sx + 26, y, txt, size=8.1, color="#1E293B", anchor="start")
        y += 22

    y += 12
    sc.text(sx, y, "PHYSICAL PATH MANDATE (TIA-568.2-D)", size=9.4, bold=True, color="#1B2A4A", anchor="start")
    y += 18
    sc.rect(sx, y - 4, sw, 36, fill="#EFF6FF", stroke="#1D4ED8", stroke_w=1.1, rx=3)
    sc.text(sx + sw / 2, y + 14, "PC → Wall Mount Jack → Cat6 Cable → Patch Panel →\nAccess Switch → Distribution (IDF) → Core (MDF) → R-CEBU", size=8.0, bold=True, color="#1E3A8A")

    y += 50
    sc.text(sx, y, "HORIZONTAL & BACKBONE CABLE SUMMARY", size=9.4, bold=True, color="#1B2A4A", anchor="start")
    y += 18
    metrics = [
        f"• Total Horizontal Cat6 Drops: {drop_stats['count']} (42 PCs + 2 Printers + 8 APs)",
        f"• MDF In-Rack Server Patches: 2 (SRV-1, SRV-2 on SW-SRV)",
        f"• Longest Copper Permanent Link: {drop_stats['max_drop_m']:.1f} m (≤ 90 m LIMIT — PASS)",
        f"• Total Horizontal Cat6 Length: {drop_stats['total_cat6_m']:,.1f} m ({drop_stats['cat6_boxes_305m']}× 305 m boxes)",
        "• Zero Repeaters Needed: Central MDF keeps all runs ≤ 45 m.",
        "• Labeling Scheme (TIA-606-C): <CAB>-<PP>-<PORT> (e.g. G-01).",
        "• Keystone Jacks & Patch Cords: Budgeted for ALL 52 drops + APs.",
    ]
    for m in metrics:
        sc.text(sx, y, m, size=8.1, color="#334155", anchor="start")
        y += 17

    y += 10
    sc.text(sx, y, "BACKBONE LINK SCHEDULE", size=9.4, bold=True, color="#1B2A4A", anchor="start")
    y += 18
    for bid, a, b, med, ln in BACKBONE_LINKS:
        sc.text(sx, y, f"{bid}: {a.split(' ')[0]}→{b.split(' ')[0]} | {med.split(' (')[0]} | {ln:.1f} m", size=7.8, color="#334155", anchor="start")
        y += 16

    sc.save(SVG_DIR / "C-1.svg", DRAWIO_DIR / "C-1_Structured_Cabling_Plan.drawio")


def generate_sheet_c2(drop_stats: Dict) -> None:
    sw_ports = compute_switch_ports()
    sc = SheetCanvas(
        sheet_no="C-2",
        sheet_title="42U MDF RACK ELEVATION, 3-TIER RISER & SWITCH PORT UTILIZATION",
        discipline="Structured Cabling Administration | ANSI/TIA-606-C & 3-Tier Hierarchy",
        drawn_by="Marianito Roble",
        scale_label="NTS (Elevation & Schematic)",
    )

    # Panel 1 (Left, X=44..440): 42U MDF Floor Rack Elevation
    rx, ry, rw, rh = 44.0, 44.0, 396.0, 888.0
    sc.rect(rx, ry, rw, 28, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
    sc.text(rx + rw / 2, ry + 14, "MDF 42U RACK ELEVATION (MDF-ROOM)", size=10.2, bold=True, color="#FFFFFF")
    sc.rect(rx, ry + 28, rw, rh - 28, fill="#F8FAFC", stroke="#1E293B", stroke_w=1.6)

    rack_items = [
        ("U41–42", "Top Exhaust Fan Tray & Cable Entry", "#E2E8F0", "#334155", 36),
        ("U39–40", "1U Fiber LIU (OM3 LC — IDF-1 & IDF-2) + 1U Mgr", "#FFEDD5", "#C2410C", 42),
        ("U37–38", "PP-MDF: 24-Port Cat6 Patch Panel + 1U Mgr", "#DBEAFE", "#1D4ED8", 42),
        ("U35–36", "R-CEBU: Cisco 2911 HQ Router (HWIC-2T WAN)", "#DCFCE7", "#15803D", 54),
        ("U33–34", "SW-CORE: Cisco 3560-24PS Core Switch (Gi0/0)", "#EDE9FE", "#6D28D9", 50),
        ("U31–32", "1U Horizontal Cable Management Brush Panel", "#F1F5F9", "#64748B", 30),
        ("U29–30", "SW-SRV: Cisco 2960-24TT Server Switch (Gi0/2)", "#E0F2FE", "#0369A1", 46),
        ("U26–28", "Blanking / Airflow Panels (Reserved Growth)", "#FFFFFF", "#94A3B8", 52),
        ("U24–25", "SRV-1: Dell R250 (DNS / Web / DHCPv4 — .98)", "#FEF3C7", "#B45309", 54),
        ("U22–23", "SRV-2: Dell R350 (Billing / POS / Cache — .99)", "#FEE2E2", "#B91C1C", 54),
        ("U16–21", "Reserved 6U Expansion Bay (Future Servers/NVR)", "#F8FAFC", "#94A3B8", 92),
        ("U14–15", "ISP Fiber ONT / Media Converter Shelf (1 Gbps)", "#CCFBF1", "#0F766E", 48),
        ("U11–13", "1U Rack PDU (12-Outlet Surge) + TMGB Ground Bar", "#DCFCE7", "#15803D", 54),
        ("U05–10", "Reserved Battery / Expansion Space", "#F8FAFC", "#94A3B8", 76),
        ("U01–04", "APC Smart-UPS 3,000 VA Online (2U + Ext Batt)", "#FEF08A", "#A16207", 72),
    ]
    uy = ry + 42
    for u_lbl, desc, fc, ec, bh in rack_items:
        sc.rect(rx + 14, uy, 62, bh - 4, fill="#1E293B", stroke="#0F172A", stroke_w=0.8)
        sc.text(rx + 45, uy + (bh - 4) / 2, u_lbl, size=8.0, bold=True, color="#FFFFFF")
        sc.rect(rx + 78, uy, rw - 92, bh - 4, fill=fc, stroke=ec, stroke_w=1.2, rx=2)
        sc.text(rx + 78 + (rw - 92) / 2, uy + (bh - 4) / 2, desc, size=8.3, bold=True, color="#0F172A")
        uy += bh

    # Panel 2 (Top Right, X=464..1638, Y=44..450): 3-Tier Hierarchical Logical Riser Diagram
    tx, ty, tw, th = 464.0, 44.0, 1174.0, 412.0
    sc.rect(tx, ty, tw, 28, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
    sc.text(tx + tw / 2, ty + 14, "CEBU FLAGSHIP HQ — 3-TIER HIERARCHICAL NETWORK RISER (ZERO PCS ON DISTRIBUTION SWITCHES)", size=10.2, bold=True, color="#FFFFFF")
    sc.rect(tx, ty + 28, tw, th - 28, fill="#FFFFFF", stroke="#1E293B", stroke_w=1.2)

    # Layer bands
    bands = [
        (ty + 36,  72, "#FEF2F2", "#991B1B", "WAN / CORE\n(MDF)"),
        (ty + 118, 80, "#FFF7ED", "#9A3412", "CORE LAYER\n(MDF)"),
        (ty + 208, 80, "#EFF6FF", "#1E40AF", "DIST. LAYER\n(IDF-1 / IDF-2)"),
        (ty + 298, 102, "#F0FDF4", "#166534", "ACCESS LAYER\n(2960-24TT)"),
    ]
    for by, bh, bcol, tcol, blbl in bands:
        sc.rect(tx + 8, by, tw - 16, bh, fill=bcol, stroke="#CBD5E1", stroke_w=0.8, rx=3)
        sc.text(tx + 68, by + bh / 2, blbl, size=8.6, bold=True, color=tcol)

    # Nodes inside 3-tier riser
    def node(cx, cy, w, h, title, sub, fc, ec):
        sc.rect(cx - w / 2, cy - h / 2, w, h, fill=fc, stroke=ec, stroke_w=1.5, rx=4)
        sc.text(cx, cy - 8, title, size=8.8, bold=True, color="#0F172A")
        sc.text(cx, cy + 8, sub, size=7.4, color="#334155")

    # Core / Router
    node(1050, ty + 72, 240, 46, "R-CEBU (Cisco 2911)", "Se0/0/0→ISP-CEBU | Gi0/0, Gi0/1, Gi0/2", "#DCFCE7", "#15803D")
    node(840,  ty + 158, 220, 48, "SW-CORE (3560-24PS)", "MDF Core — HQ-GAMING-LAN (Gi0/0)", "#EDE9FE", "#6D28D9")
    node(1460, ty + 158, 210, 48, "SW-SRV (2960-24TT)", "MDF Server LAN (Gi0/2): SRV-1 & SRV-2", "#FEF3C7", "#B45309")

    # Distribution Layer
    node(720,  ty + 248, 210, 48, "DSW-1 (3560-24PS)", "IDF-1 (North) — OM3 Fiber to MDF", "#DBEAFE", "#1D4ED8")
    node(1060, ty + 248, 210, 48, "DSW-2 (3560-24PS)", "IDF-2 (South) — OM3 Fiber to MDF", "#DBEAFE", "#1D4ED8")

    # Access Layer (5 switches — zero PCs on DSW-1/DSW-2!)
    node(690,  ty + 348, 174, 62, "SW-GAM1 (CAB-G)", "2960-24TT: 20 PCs + 2 APs\n22 Used Fa | 2 Spare Fa", "#FFFFFF", "#0284C7")
    node(880,  ty + 348, 174, 62, "SW-VIP (CAB-V)", "2960-24TT: 10 VIP + 2 APs\n12 Used Fa | 12 Spare Fa", "#FFFFFF", "#0284C7")
    node(1070, ty + 348, 174, 62, "SW-STU (CAB-S)", "2960-24TT: 6 PCs + 3 APs\n9 Used Fa | 15 Spare Fa", "#FFFFFF", "#0284C7")
    node(1275, ty + 348, 194, 62, "SW-ADM (IDF-2)", "2960-24TT: 6 Admin/POS +\n2 Prt + 1 AP | 15 Spare Fa", "#ECFDF5", "#059669")
    node(1495, ty + 348, 180, 62, "SRV-1 & SRV-2", "10.10.0.98 (DNS/DHCP)\n10.10.0.99 (Billing/POS)", "#FEF9C3", "#B45309")

    # Connectors
    sc.line(1050, ty + 95, 840, ty + 134, stroke="#15803D", stroke_w=2.0)
    sc.line(1050, ty + 95, 1275, ty + 317, stroke="#059669", stroke_w=1.8, dash="5,3")
    sc.line(1050, ty + 95, 1460, ty + 134, stroke="#B45309", stroke_w=2.0)
    sc.line(840, ty + 182, 720, ty + 224, stroke="#EA580C", stroke_w=2.4)
    sc.line(840, ty + 182, 1060, ty + 224, stroke="#EA580C", stroke_w=2.4)
    sc.line(720, ty + 272, 690, ty + 317, stroke="#7C3AED", stroke_w=1.8)
    sc.line(720, ty + 272, 880, ty + 317, stroke="#7C3AED", stroke_w=1.8)
    sc.line(1060, ty + 272, 1070, ty + 317, stroke="#7C3AED", stroke_w=1.8)
    sc.line(1460, ty + 182, 1495, ty + 317, stroke="#B45309", stroke_w=1.8)

    # Panel 3 (Bottom Right, X=464..1638, Y=474..932): Exact Switch Port Utilization + Cabinet Summary + Drop Totals
    by = 474.0
    sc.rect(tx, by, tw, 28, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
    sc.text(tx + tw / 2, by + 14, "ACCESS SWITCH PORT UTILIZATION (2960-24TT: SPARE = 24 - USED Fa; UPLINK ON Gi0/1)", size=10.0, bold=True, color="#FFFFFF")

    by += 28
    s_hdr = [("Switch", 110), ("Cabinet / Room", 190), ("Model", 145), ("Uplink (Gi0/1)", 200), ("Total Fa", 90), ("Used Fa", 90), ("Spare Fa", 100), ("Utilization", 110), ("Status", 139)]
    cx = tx
    sc.rect(tx, by, tw, 24, fill="#E2E8F0", stroke="#94A3B8", stroke_w=0.8)
    for htxt, hw in s_hdr:
        sc.text(cx + hw / 2, by + 12, htxt, size=8.4, bold=True, color="#0F172A")
        cx += hw
    by += 24

    tot_used = 0
    tot_spare = 0
    for idx, s in enumerate(sw_ports):
        rh = 26.0
        if idx % 2 == 1:
            sc.rect(tx, by, tw, rh, fill="#F8FAFC", stroke="none", in_mx=False)
        sc.line(tx, by + rh, tx + tw, by + rh, stroke="#CBD5E1", stroke_w=0.7, in_mx=False)
        util = round(100.0 * s["used_fa"] / 24.0, 1)
        tot_used += s["used_fa"]
        tot_spare += s["spare_fa"]
        vals = [s["switch"], s["location"], s["model"], s["uplink"], "24", str(s["used_fa"]), str(s["spare_fa"]), f"{util:.1f}%", "OK (Spare Ready)"]
        cx = tx
        for j, (v, (_, hw)) in enumerate(zip(vals, s_hdr)):
            sc.text(cx + hw / 2, by + rh / 2, v, size=8.3, bold=(j in (0, 6)), color="#15803D" if j == 8 else "#0F172A")
            cx += hw
        by += rh

    sc.rect(tx, by, tw, 26, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=0.8)
    sc.text(tx + 12, by + 13, "TOTAL ACCESS SWITCH CAPACITY (5× Cisco 2960-24TT)", size=8.8, bold=True, color="#FFFFFF", anchor="start")
    sc.text(tx + 690, by + 13, "120 Fa", size=8.8, bold=True, color="#FFFFFF")
    sc.text(tx + 780, by + 13, f"{tot_used} Used", size=8.8, bold=True, color="#FDE047")
    sc.text(tx + 875, by + 13, f"{tot_spare} Spare", size=8.8, bold=True, color="#86EFAC")
    sc.text(tx + 1090, by + 13, f"{100.0 * tot_used / 120.0:.1f}% Overall", size=8.8, bold=True, color="#FFFFFF")

    # Bottom Summary Cards (Drop Counts by Zone + Grounding/Testing Checklist)
    cy = by + 44
    sc.rect(tx, cy, 575, 224, fill="#F8FAFC", stroke="#1B2A4A", stroke_w=1.1, rx=4)
    sc.rect(tx, cy, 575, 24, fill="#E2E8F0", stroke="#94A3B8", stroke_w=0.8)
    sc.text(tx + 287.5, cy + 12, "DROP SCHEDULE SUMMARY BY ZONE (52 HORIZONTAL + 2 RACK)", size=8.8, bold=True, color="#0F172A")
    zlines = [
        "• Standard Gaming Zone (CAB-G / SW-GAM1): 20 Gaming PCs + 2 Ceiling APs = 22 drops",
        "• VIP Esports Arena & Future Bay (CAB-V / SW-VIP): 10 VIP PCs + 2 Ceiling APs = 12 drops",
        "• Study Pods, Browsing & Café (CAB-S / SW-STU): 4 Study + 2 Browsing + 3 APs = 9 drops",
        "• Admin Office & Cashier/POS (IDF-2 / SW-ADM): 6 Admin/POS + 2 Printers + 1 AP = 9 drops",
        "• Central MDF Server Rack (MDF / SW-SRV): 2 Rack Servers (SRV-1, SRV-2) in-rack patch",
        f"• Maximum Permanent Link Length: {drop_stats['max_drop_m']:.1f} m (100% ≤ 90 m TIA-568.2-D)",
        "• Future Gaming Bay (10 Seats): Pre-provisioned in /26 subnet & dedicated CAB-F stub-out.",
    ]
    zy = cy + 44
    for zl in zlines:
        sc.text(tx + 12, zy, zl, size=8.2, color="#1E293B", anchor="start")
        zy += 24

    sc.rect(tx + 595, cy, 579, 224, fill="#F0FDF4", stroke="#15803D", stroke_w=1.1, rx=4)
    sc.rect(tx + 595, cy, 579, 24, fill="#DCFCE7", stroke="#15803D", stroke_w=0.8)
    sc.text(tx + 595 + 289.5, cy + 12, "CERTIFICATION, GROUNDING & ADMINISTRATION STANDARDS", size=8.8, bold=True, color="#14532D")
    clines = [
        "• ANSI/TIA-568.2-D: Cat6 250 MHz channel tested via Fluke DSX-8000 (NEXT, PSNEXT, RL).",
        "• ANSI/TIA-569-E: 200 mm overhead data tray ≥1.1 m from electrical EMT spine.",
        "• ANSI/TIA-606-C: Machine-printed wrap labels at both cable ends, faceplate & patch panel.",
        "• ANSI/TIA-607-D: Copper TMGB in MDF bonded to main electrical ground + TGB in IDF-1/2.",
        "• Wall/Ceiling Hardware: 100% of 52 drops (including all 8 PoE APs) include keystone jacks,",
        "  surface/ceiling biscuit boxes, and dual factory-terminated Cat6 patch cords.",
        "• Complete drop-by-drop table exported to budget/drop_schedule.csv & Appendix D.",
    ]
    zy = cy + 44
    for cl in clines:
        sc.text(tx + 607, zy, cl, size=8.2, color="#1E293B", anchor="start")
        zy += 24

    sc.save(SVG_DIR / "C-2.svg", DRAWIO_DIR / "C-2_Rack_Riser_Drops.drawio")


if __name__ == "__main__":
    ds = write_drop_schedule()
    write_cabling_boq(ds)
    generate_sheet_c1(ds)
    generate_sheet_c2(ds)
    print(f"Generated C-1, C-2, drop_schedule.csv ({ds['count']} drops, max {ds['max_drop_m']} m), and cabling_boq.csv")
