"""Furniture & Fixtures Plan (Sheet A-3) + Furniture & Fixtures BOQ (1-to-1 parity with Drops, Appliances, ACs)."""

from __future__ import annotations

import csv
from decimal import Decimal
from typing import Dict, List

from draw_kit import SheetCanvas, draw_rooms_base, px, py
from model import (
    AC_UNITS,
    APPLIANCES,
    BUDGET_DIR,
    DRAWIO_DIR,
    DROPS,
    PRICE_DATE,
    SVG_DIR,
    php_round,
)


def build_furniture_boq_items():
    # Verify exact workstation counts from DROPS
    n_gam = sum(1 for d in DROPS if d.kind == "Gaming-PC")    # 20
    n_vip = sum(1 for d in DROPS if d.kind == "VIP-PC")       # 10
    n_stu = sum(1 for d in DROPS if d.kind == "Study-PC")     # 4
    n_brw = sum(1 for d in DROPS if d.kind == "Browsing-PC")  # 2
    n_adm = sum(1 for d in DROPS if d.kind == "Admin-PC")     # 4
    n_pos = sum(1 for d in DROPS if d.kind == "POS-PC")       # 2
    assert n_gam + n_vip + n_stu + n_brw + n_adm + n_pos == 42

    items = [
        # Desks & Seating (strict 1-to-1 match with 42 PCs!)
        ("Heavy-Duty Steel/MDF Gaming Desk (1200×600 mm) w/ Cable Grommet & Headset Hook — Standard Gaming", n_gam, "units", 5850, f"Mandaue Foam / Lazada Mall PH ({PRICE_DATE})"),
        ("Ergonomic PU-Leather High-Back Gaming Chair w/ Lumbar Cushion — Standard Gaming", n_gam, "units", 6495, f"Mandaue Foam / Shopee Mall PH ({PRICE_DATE})"),
        ("Pro Esports Tournament Desk (1400×700 mm, Carbon Finish) w/ Power Tray — VIP Arena", n_vip, "units", 8950, f"Lazada Mall PH ({PRICE_DATE})"),
        ("Pro Esports Racing Ergonomic Chair (4D Armrest, Steel Base) — VIP Arena", n_vip, "units", 10995, f"PC Express / Lazada Mall PH ({PRICE_DATE})"),
        ("Enclosed Acoustic Study & Work Pod Desk Module (1400×700 mm w/ Divider) — Study Pods", n_stu, "units", 14500, f"Office Warehouse PH ({PRICE_DATE})"),
        ("Mesh Ergonomic Task Chair w/ Adjustable Headrest — Study Pods", n_stu, "units", 4950, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Quick-Browsing Station Counter Desk (2-Seat Compact Bay) — Cashier/Lobby", n_brw, "seats", 4200, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Compact Swivel Browsing Task Chair — Quick-Browsing Station", n_brw, "units", 2850, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Executive / Admin L-Shape Office Desk (1500×700 mm w/ Mobile Pedestal) — Admin/IT Office", n_adm, "units", 11500, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Mid-Back Ergonomic Mesh Office Chair — Admin/IT Office", n_adm, "units", 4650, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Custom Laminated Cashier, POS & Printing Service Counter (4.2 m, 2 POS Bays + Printer Bay)", 1, "unit", 48000, f"Cebu Custom Millwork ({PRICE_DATE})"),
        ("High-Back Cashier Swivel Task Chair — POS-01 & POS-02", n_pos, "units", 3850, f"Mandaue Foam PH ({PRICE_DATE})"),

        # Café, Staff Lounge, Lobby & Storage Furniture
        ("Café Snack Pantry Service Counter w/ Stainless Sink & Under-Counter Cabinets (4.5 m)", 1, "set", 42000, f"CW Home Depot / Millwork ({PRICE_DATE})"),
        ("Café Dining Table (800×800 mm) w/ 4 Stackable Café Chairs — Café Pantry", 5, "sets", 9800, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Staff Lounge 3-Seater Fabric Sofa & Coffee Table Set", 1, "set", 24500, f"Mandaue Foam PH ({PRICE_DATE})"),
        ("Staff Lounge Break Table w/ 6 Chairs & 12-Door Steel Staff Locker", 1, "set", 28500, f"Office Warehouse PH ({PRICE_DATE})"),
        ("Lobby Waiting 3-Seater Steel-Frame Bench — Cashier/Lobby", 2, "units", 8950, f"Office Warehouse PH ({PRICE_DATE})"),
        ("Heavy-Duty 5-Tier Boltless Steel Storage Rack (1800×900×450 mm) — Storage & MDF", 4, "units", 4850, f"Wilcon Depot PH ({PRICE_DATE})"),
        ("4-Drawer Vertical Steel Filing Cabinet w/ Central Lock — Admin Office", 2, "units", 7950, f"Office Warehouse PH ({PRICE_DATE})"),
        ("Restroom Fixture Set (Water Closets, Lavatories, Urinals, PWD Grab Bars, Mirrors, Hand Dryers)", 1, "lot", 96500, f"Wilcon Depot PH ({PRICE_DATE})"),
    ]

    # Add ALL 9 dedicated appliances (strict 1-to-1 match with electrical.py!)
    for app in APPLIANCES:
        items.append((app["name"], app["qty"], "unit", app["unit_php"], app["source"]))

    # Group AC units by model (strict 1-to-1 match with electrical.py Panel ACP!)
    ac_groups: Dict[str, List[dict]] = {}
    for ac in AC_UNITS:
        ac_groups.setdefault(ac["model"], []).append(ac)
    for model_name, grp in ac_groups.items():
        items.append((
            f"{model_name} (w/ Copper Tubing, Drain Line & Bracket Installation)",
            len(grp),
            "units" if len(grp) > 1 else "unit",
            grp[0]["unit_php"],
            grp[0]["source"],
        ))

    return items


def write_furniture_boq() -> List[Dict]:
    rows = []
    out = BUDGET_DIR / "furniture_boq.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item / specification", "Quantity", "Unit", "Unit cost (PHP)", "Subtotal (PHP)", "Price source / date"])
        for item, qty, unit, uc, src in build_furniture_boq_items():
            sub = php_round(Decimal(qty) * Decimal(uc))
            w.writerow([item, qty, unit, f"{Decimal(uc):.2f}", f"{sub:.2f}", src])
            rows.append({"item": item, "qty": qty, "unit": unit, "unit_cost": Decimal(uc), "subtotal": sub, "source": src})
    return rows


def generate_sheet_a3() -> None:
    sc = SheetCanvas(
        sheet_no="A-3",
        sheet_title="FURNITURE, FIXTURES, APPLIANCES & HVAC EQUIPMENT PLAN",
        discipline="Interior FF&E & HVAC | 1-to-1 Parity w/ Cabling & Electrical Plans",
        drawn_by="Armanpreet Talwar",
    )
    sc.draw_dimensions_and_grid()
    draw_rooms_base(sc, show_labels=False, muted=True)

    # Subtle room tags in corners so furniture never collides
    from model import ROOMS
    for rm in ROOMS:
        if rm.code == "COR-MAIN":
            sc.text(px(rm.cx), py(rm.cy), "MAIN CIRCULATION CORRIDOR (2.0 m CLEAR)", size=9.0, bold=True, color="#64748B")
        elif rm.code == "STD-GAME":
            sc.text(px(rm.x + 3.0), py(rm.y + 0.55), rm.code, size=7.8, bold=True, color="#64748B", anchor="start")
        else:
            sc.text(px(rm.x + 0.3), py(rm.y + 0.55), rm.code, size=7.8, bold=True, color="#64748B", anchor="start")

    # Draw desks & chairs for all 42 PCs + 2 Printers
    for d in DROPS:
        if d.kind == "AP":
            continue
        cx, cy = px(d.x), py(d.y)
        if d.kind == "Gaming-PC":
            sc.rect(cx - 17, cy - 9, 34, 15, fill="#DBEAFE", stroke="#1D4ED8", stroke_w=1.0, rx=2)
            sc.circle(cx, cy + 12, 6, fill="#93C5FD", stroke="#1E40AF", stroke_w=0.9)
            sc.text(cx, cy - 1.5, d.device, size=6.2, bold=True, color="#1E3A8A")
        elif d.kind == "VIP-PC":
            sc.rect(cx - 19, cy - 9, 38, 16, fill="#EDE9FE", stroke="#6D28D9", stroke_w=1.1, rx=2)
            sc.circle(cx + (27 if d.x < 31 else -27), cy, 6, fill="#C4B5FD", stroke="#5B21B6", stroke_w=0.9)
            sc.text(cx, cy - 1.0, d.device, size=6.2, bold=True, color="#4C1D95")
        elif d.kind == "Study-PC":
            sc.rect(cx - 22, cy - 14, 44, 24, fill="#DCFCE7", stroke="#15803D", stroke_w=1.1, rx=3)
            sc.circle(cx, cy + 16, 6, fill="#86EFAC", stroke="#166534", stroke_w=0.9)
            sc.text(cx, cy - 2, d.device, size=6.6, bold=True, color="#14532D")
        elif d.kind == "Browsing-PC":
            sc.rect(cx - 15, cy - 9, 30, 15, fill="#FEF3C7", stroke="#B45309", stroke_w=1.0, rx=2)
            sc.circle(cx, cy + 12, 5.5, fill="#FDE68A", stroke="#92400E", stroke_w=0.9)
            sc.text(cx, cy - 1.5, d.device, size=6.0, bold=True, color="#78350F")
        elif d.kind in ("Admin-PC", "POS-PC"):
            sc.rect(cx - 18, cy - 10, 36, 17, fill="#CCFBF1", stroke="#0F766E", stroke_w=1.1, rx=2)
            sc.circle(cx, cy + 13, 6, fill="#99F6E4", stroke="#115E59", stroke_w=0.9)
            sc.text(cx, cy - 1.5, d.device, size=6.2, bold=True, color="#134E4A")
        elif d.kind == "Printer":
            sc.rect(cx - 14, cy - 10, 28, 20, fill="#F1F5F9", stroke="#334155", stroke_w=1.1, rx=2)
            sc.text(cx, cy, d.device, size=6.2, bold=True, color="#0F172A")

    # Future Gaming Bay dashed outline (10 future desks)
    for r_i, yy in enumerate([2.5, 5.5, 8.5]):
        for c_i, xx in enumerate([19.8, 22.2, 24.4]):
            sc.rect(px(xx) - 14, py(yy) - 7, 28, 13, fill="none", stroke="#94A3B8", stroke_w=0.9, dash="3,2")
    sc.text(px(22.0), py(10.6), "FUTURE 10-SEAT BAY\n(CONDUIT STUBBED)", size=7.8, italic=True, color="#64748B")

    # Café Tables (5 sets), Staff Lounge Sofa/Table, Lobby Benches, Storage Racks
    for tx, ty in [(19.8, 23.6), (21.6, 23.6), (23.4, 23.6), (25.0, 23.6), (21.6, 25.0)]:
        sc.rect(px(tx) - 11, py(ty) - 9, 22, 18, fill="#FFEDD5", stroke="#C2410C", stroke_w=0.9, rx=2)
    sc.rect(px(27.8), py(21.2), 68, 26, fill="#F3E8FF", stroke="#7E22CE", stroke_w=1.0, rx=3)
    sc.text(px(29.0), py(21.7), "SOFA", size=6.8, bold=True, color="#581C87")
    sc.rect(px(28.0), py(23.5), 54, 24, fill="#F3E8FF", stroke="#7E22CE", stroke_w=1.0, rx=2)
    sc.text(px(29.0), py(23.95), "BREAK TBL", size=6.4, bold=True, color="#581C87")
    sc.rect(px(1.2), py(22.5), 76, 16, fill="#E2E8F0", stroke="#475569", stroke_w=1.0, rx=2)
    sc.text(px(2.6), py(22.8), "WAITING BENCH", size=6.4, color="#334155")
    sc.rect(px(37.8), py(21.5), 48, 86, fill="#E7E5E4", stroke="#57534E", stroke_w=1.0)
    sc.text(px(38.7), py(23.1), "RACKS", size=6.5, bold=True, color="#44403C")

    # Dedicated Appliances (amber diamond/badge)
    for app in APPLIANCES:
        ax, ay = px(app["x"]), py(app["y"])
        sc.rect(ax - 14, ay - 8, 28, 16, fill="#FEF08A", stroke="#A16207", stroke_w=1.1, rx=2)
        sc.text(ax, ay, app["id"].replace("APP-", ""), size=6.2, bold=True, color="#713F12")

    # All 11 AC Units (cyan equipment block)
    for ac in AC_UNITS:
        ax, ay = px(ac["x"]), py(ac["y"])
        sc.rect(ax - 17, ay - 9, 34, 18, fill="#CFFAFE", stroke="#0E7490", stroke_w=1.3, rx=2)
        sc.text(ax, ay, ac["id"], size=6.6, bold=True, color="#155E75")

    # Sidebar Legend & Parity Summary
    sx, sy, sw = sc.sidebar_box("FF&E AND HVAC LEGEND & PARITY CHECK")
    legend = [
        ("#DBEAFE", "#1D4ED8", "Standard Gaming Desk + Chair (20 sets: GAM-01..20)"),
        ("#EDE9FE", "#6D28D9", "VIP Pro Esports Desk + Chair (10 sets: VIP-01..10)"),
        ("#DCFCE7", "#15803D", "Acoustic Study Pod Desk + Chair (4 sets: STD-01..04)"),
        ("#FEF3C7", "#B45309", "Quick-Browsing Desk + Chair (2 sets: BRW-01..02)"),
        ("#CCFBF1", "#0F766E", "Admin/IT & Cashier/POS Desks + Chairs (6 sets)"),
        ("#F1F5F9", "#334155", "Network Multifunction Printers (2 units: PRT-01..02)"),
        ("#FEF08A", "#A16207", "Dedicated Appliances (9 units — 1:1 w/ Electrical E-1/E-2)"),
        ("#CFFAFE", "#0E7490", "Inverter AC Units (11 units: AC-01..11 — 1:1 w/ Panel ACP)"),
    ]
    y = sy
    for fc, ec, lbl in legend:
        sc.rect(sx, y - 7, 22, 14, fill=fc, stroke=ec, stroke_w=1.1, rx=2)
        sc.text(sx + 30, y, lbl, size=8.6, color="#1E293B", anchor="start")
        y += 24

    y += 14
    sc.text(sx, y, "AIR-CONDITIONING SCHEDULE (11 INVERTER UNITS)", size=9.6, bold=True, color="#1B2A4A", anchor="start")
    y += 18
    for ac in AC_UNITS:
        sc.text(sx, y, f"{ac['id']} ({ac['room']}): {ac['hp']:.1f} HP — {ac['va']:,} VA ({ac['amps']:.0f} A)", size=8.2, color="#334155", anchor="start")
        y += 16

    y += 14
    sc.text(sx, y, "DEDICATED APPLIANCES (9 UNITS — 1:1 W/ E-2)", size=9.6, bold=True, color="#1B2A4A", anchor="start")
    y += 18
    for app in APPLIANCES:
        nm = app["name"][:38] + ("…" if len(app["name"]) > 38 else "")
        sc.text(sx, y, f"{app['id'].replace('APP-','')}: {nm} ({app['watt']} W)", size=8.0, color="#334155", anchor="start")
        y += 15.5

    y += 14
    sc.rect(sx, y, sw, 82, fill="#F0FDF4", stroke="#15803D", stroke_w=1.1, rx=4)
    sc.text(sx + sw / 2, y + 18, "1-TO-1 WORKSTATION & APPLIANCE PARITY", size=9.5, bold=True, color="#166534")
    sc.text(sx + 12, y + 40, "• 42 Desks & 42 Chairs = 42 PCs in drop_schedule.csv & PT", size=8.5, color="#1E293B", anchor="start")
    sc.text(sx + 12, y + 58, "• 9 Appliances + 11 ACs = exact match in Panel PP-1 & ACP", size=8.5, color="#1E293B", anchor="start")

    sc.save(SVG_DIR / "A-3.svg", DRAWIO_DIR / "A-3_Furniture_Fixtures_Plan.drawio")


if __name__ == "__main__":
    write_furniture_boq()
    generate_sheet_a3()
    print("Generated A-3 and furniture_boq.csv")
