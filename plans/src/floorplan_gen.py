"""Architectural Floor Plans (Sheet A-1 Original Shell, Sheet A-2 Modified Fit-Out) + Floor Plan BOQ."""

from __future__ import annotations

import csv
from decimal import Decimal
from typing import List, Dict

from draw_kit import SheetCanvas, draw_rooms_base, px, py, SCALE
from model import (
    BUDGET_DIR,
    BUILDING_H_M,
    BUILDING_W_M,
    DRAWIO_DIR,
    ORIGINAL_ZONES,
    PRICE_DATE,
    ROOMS,
    SVG_DIR,
    php_round,
)

# Realistic Nov 2026 Philippine commercial interior fit-out costs (excludes base building shell/structure!)
FLOOR_BOQ_ITEMS = [
    ("Gypsum Board Drywall Partition w/ Metal Studs & Acoustic Batt (12 mm, double-sided)", 196, "sqm", 1850, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Tempered Acoustic Glass Partition (12 mm) w/ Aluminum Frame — VIP Arena & Study Pods", 56, "sqm", 5200, f"CW Home Depot PH ({PRICE_DATE})"),
    ("2-Hour Fire-Rated Concrete Hollow Block Wall (150 mm) — MDF & Electrical Room Separation", 36, "sqm", 2450, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Commercial Porcelain Floor Tiles (600×600 mm, Matte) w/ Adhesive & Grout — Lobby, Corridor, Pantry", 254, "sqm", 1180, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Heavy-Duty Commercial Vinyl Plank Flooring (5 mm SPC) — Standard Gaming, Future Bay, Admin, Lounge", 384, "sqm", 1320, f"CW Home Depot PH ({PRICE_DATE})"),
    ("Acoustic Modular Carpet Tiles (500×500 mm) — VIP Esports Arena & Study/Work Pods", 216, "sqm", 1450, f"CW Home Depot PH ({PRICE_DATE})"),
    ("Anti-Static ESD Conductive Vinyl Flooring w/ Copper Grid — Central MDF / Server Room", 30, "sqm", 2950, f"RS Components / Lazada Mall PH ({PRICE_DATE})"),
    ("Industrial Non-Slip Epoxy Floor Coating — Electrical Room & Storage", 39, "sqm", 1150, f"Boysen / Wilcon Depot PH ({PRICE_DATE})"),
    ("Anti-Slip Ceramic Restroom & Janitor Floor/Wall Tiles", 69, "sqm", 980, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Acoustic Mineral Fiber Suspended Ceiling Grid (600×600 mm, T-Runner)", 992, "sqm", 860, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Frameless Double Tempered Glass Main Entrance Door w/ Floor Closer & Access Control Strike", 1, "set", 48500, f"CW Home Depot PH ({PRICE_DATE})"),
    ("2-Hour Fire-Rated Steel Doors w/ Panic Bar & Closer — MDF, Electrical Room, West Fire Exit", 3, "sets", 24500, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Solid-Core Flush Timber Interior Doors w/ Heavy-Duty Lever Locksets", 11, "sets", 9800, f"Wilcon Depot PH ({PRICE_DATE})"),
    ("Interior Elastomeric Low-VOC Paint (2 Coats Primer + Topcoat, Walls & Trim)", 640, "sqm", 340, f"Boysen / Wilcon Depot PH ({PRICE_DATE})"),
    ("Illuminated Wayfinding, Room Plates, Fire-Exit & Safety Signage Package", 1, "lot", 28500, f"Cebu Commercial Signage ({PRICE_DATE})"),
    ("Interior Fit-Out Labor, Hauling, Supervision & Site Cleanup (12% Trade Allowance)", 1, "lot", 295000, f"Cebu Fit-Out Contractor Est. ({PRICE_DATE})"),
]


def write_floor_boq() -> List[Dict]:
    rows = []
    out = BUDGET_DIR / "floor_boq.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item / specification", "Quantity", "Unit", "Unit cost (PHP)", "Subtotal (PHP)", "Price source / date"])
        for item, qty, unit, uc, src in FLOOR_BOQ_ITEMS:
            sub = php_round(Decimal(qty) * Decimal(uc))
            w.writerow([item, qty, unit, f"{Decimal(uc):.2f}", f"{sub:.2f}", src])
            rows.append({"item": item, "qty": qty, "unit": unit, "unit_cost": Decimal(uc), "subtotal": sub, "source": src})
    return rows


def generate_sheet_a1() -> None:
    sc = SheetCanvas(
        sheet_no="A-1",
        sheet_title="ORIGINAL FLOOR PLAN — BASE COMMERCIAL SHELL (BEFORE MODIFICATION)",
        discipline="Architectural Base Shell | Conceptual 40×26 m Plate (Cebu IT Park)",
        drawn_by="Francis RJ Velasco",
    )
    sc.draw_dimensions_and_grid()

    for code, name, x, y, w, h, col in ORIGINAL_ZONES:
        sc.rect(px(x), py(y), w * SCALE, h * SCALE, fill=col, stroke="#475569", stroke_w=1.6, dash="6,4" if "OPEN" in code else "")
        if w <= 4.5:
            short_n = name.replace("Base-Building ", "Base-Bldg\n").replace(" Stairwell", "\nStairwell").replace(" Elevator Shaft", "\nElevator").replace(" Lobby Vestibule", "\nVestibule").replace(" Electrical Stub-In", "\nElec. Stub")
            sc.text(px(x + w / 2), py(y + h / 2) - 10, short_n, size=7.8, bold=True, color="#334155")
            sc.text(px(x + w / 2), py(y + h / 2) + 18, f"{w:.0f}×{h:.0f} m ({w * h:.0f} m²)", size=7.4, color="#64748B")
        else:
            dy_off = 32 if "OPEN" in code else 0
            sc.text(px(x + w / 2), py(y + h / 2) - 8 + dy_off, name, size=11.5, bold=True, color="#334155")
            sc.text(px(x + w / 2), py(y + h / 2) + 14 + dy_off, f"{w:.1f} m × {h:.1f} m ({w * h:.0f} sqm)", size=9.5, color="#64748B")

    # Structural columns inside open shell
    for gx in [8, 16, 24, 32]:
        for gy in [6.5, 13.0, 19.5]:
            sc.rect(px(gx) - 6, py(gy) - 6, 12, 12, fill="#334155", stroke="#0F172A", stroke_w=1.0)

    sc.rect(px(0), py(0), BUILDING_W_M * SCALE, BUILDING_H_M * SCALE, fill="none", stroke="#0F172A", stroke_w=3.2)

    # Sidebar notes
    sx, sy, sw = sc.sidebar_box("ORIGINAL SHELL NOTES (BEFORE MODIFICATION)")
    notes = [
        ("Plan Source & Status:", "Conceptual commercial warm-shell floor plate designed by Group 1 (2026) representing a typical 1,040 sqm single-floor IT-park tenancy in Cebu IT Park."),
        ("Gross Floor Area:", "40.0 m × 26.0 m = 1,040.0 sqm (base building core: 56.0 sqm stairwell, elevator & east vestibule; leasable tenant shell: 984.0 sqm)."),
        ("Structural Grid:", "8.0 m × 6.5 m reinforced-concrete column bays (450×450 mm columns shown solid). Ceiling slab soffit at 3.8 m; proposed suspended ceiling at 3.2 m."),
        ("Existing Utilities:", "Base-building electrical stub-in at South-Central bay (23–27 m X, 14–20 m Y) and plumbing wet-wall along East-South core (33–40 m X)."),
        ("Why Modification Is Needed:", "The bare shell lacks acoustic zoning for 24/7 esports/gaming, a fire-rated central MDF server room separated from electrical feeders, 2.0 m life-safety corridors, study pods, and café pantry service zones."),
    ]
    y = sy
    for hdr, body in notes:
        sc.text(sx, y, hdr, size=10.5, bold=True, color="#1B2A4A", anchor="start")
        y += 18
        # Word wrap manually to ~54 chars
        words, line = body.split(), ""
        for wd in words:
            if len(line) + len(wd) + 1 > 54:
                sc.text(sx, y, line, size=9.3, color="#334155", anchor="start")
                y += 14.5
                line = wd
            else:
                line = (line + " " + wd).strip()
        if line:
            sc.text(sx, y, line, size=9.3, color="#334155", anchor="start")
            y += 24

    # Summary box at bottom of sidebar
    sc.rect(sx, 770, sw, 140, fill="#EFF6FF", stroke="#1D4ED8", stroke_w=1.2, rx=4)
    sc.text(sx + sw / 2, 792, "BASE SHELL SUMMARY", size=10.5, bold=True, color="#1E3A8A")
    sc.text(sx + 12, 818, "• Building Dimensions: 40.0 m × 26.0 m", size=9.5, color="#1E293B", anchor="start")
    sc.text(sx + 12, 838, "• Total Gross Area: 1,040.0 sqm (≥ 1,000 sqm req.)", size=9.5, color="#1E293B", anchor="start")
    sc.text(sx + 12, 858, "• Base Core (Stair/Elev/Vest): 56.0 sqm", size=9.5, color="#1E293B", anchor="start")
    sc.text(sx + 12, 878, "• Fit-Out Tenant Area: 984.0 sqm", size=9.5, color="#1E293B", anchor="start")
    sc.text(sx + 12, 898, "• Building Shell Construction: EXCLUDED from BOQ", size=9.2, bold=True, color="#B91C1C", anchor="start")

    sc.save(SVG_DIR / "A-1.svg", DRAWIO_DIR / "A-1_Original_Floor_Plan.drawio")


def generate_sheet_a2() -> None:
    sc = SheetCanvas(
        sheet_no="A-2",
        sheet_title="MODIFIED ARCHITECTURAL FLOOR PLAN — ROOM SCHEDULE & CIRCULATION",
        discipline="Architectural Fit-Out | NBCP / RA 9514 Fire Code & TIA-569 Space Planning",
        drawn_by="Francis RJ Velasco",
    )
    sc.draw_dimensions_and_grid()
    draw_rooms_base(sc, show_labels=True, muted=False)

    # Sidebar: Complete 19-Room Area Schedule
    sx, sy, sw = sc.sidebar_box("ROOM AREA SCHEDULE (1,040.0 SQM TOTAL)")
    # Table header
    sc.rect(sx, sy - 6, sw, 22, fill="#E2E8F0", stroke="#94A3B8", stroke_w=0.8)
    sc.text(sx + 6, sy + 5, "Code", size=8.5, bold=True, color="#0F172A", anchor="start")
    sc.text(sx + 74, sy + 5, "Room / Zone Name", size=8.5, bold=True, color="#0F172A", anchor="start")
    sc.text(sx + sw - 74, sy + 5, "Dim (m)", size=8.5, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + sw - 6, sy + 5, "Area", size=8.5, bold=True, color="#0F172A", anchor="end")

    y = sy + 27
    for i, rm in enumerate(ROOMS):
        if i % 2 == 1:
            sc.rect(sx, y - 9, sw, 19, fill="#F1F5F9", stroke="none", in_mx=False)
        sc.rect(sx + 4, y - 5, 10, 10, fill=rm.zone_color, stroke="#64748B", stroke_w=0.6, in_mx=False)
        sc.text(sx + 18, y, rm.code, size=8.0, bold=True, color="#1E293B", anchor="start")
        nm = rm.name if len(rm.name) <= 27 else rm.name[:25] + "…"
        sc.text(sx + 74, y, nm, size=8.0, color="#334155", anchor="start")
        sc.text(sx + sw - 74, y, f"{rm.w:.1f}×{rm.h:.0f}", size=8.0, color="#475569", anchor="end")
        sc.text(sx + sw - 6, y, f"{rm.area:.0f} m²", size=8.2, bold=True, color="#0F172A", anchor="end")
        y += 19.5

    # Total bar
    sc.rect(sx, y - 4, sw, 24, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=0.8)
    sc.text(sx + 10, y + 8, "TOTAL GROSS FLOOR AREA (19 ZONES)", size=9.0, bold=True, color="#FFFFFF", anchor="start")
    sc.text(sx + sw - 8, y + 8, "1,040 m²", size=9.5, bold=True, color="#FFFFFF", anchor="end")

    # Key Modifications summary
    ky = y + 38
    sc.text(sx, ky, "KEY ARCHITECTURAL MODIFICATIONS (A-1 → A-2)", size=9.8, bold=True, color="#1B2A4A", anchor="start")
    mods = [
        "1. Central 2.0 m clear circulation spine linking West Fire Exit to East Core.",
        "2. North Gaming Wing: 20-PC Standard Gaming, 10-seat Future Bay, 10-PC VIP Arena.",
        "3. Central MDF (30 m²) directly beside Electrical Room (24 m²) w/ 2-hr firewall.",
        "4. Quiet South-West Study/Work Pods (4 PCs) & Cashier/POS/Printing Lobby.",
        "5. Full 24/7 amenities: Café Pantry, Staff Lounge, M/F/PWD Restrooms, Storage.",
        "6. Base-building Stair/Elevator (48 m²) retained; fit-out BOQ covers interior only.",
    ]
    ky += 18
    for m in mods:
        words, line = m.split(), ""
        for wd in words:
            if len(line) + len(wd) + 1 > 56:
                sc.text(sx, ky, line, size=8.6, color="#334155", anchor="start")
                ky += 13.5
                line = "   " + wd
            else:
                line = (line + " " + wd).strip()
        if line:
            sc.text(sx, ky, line, size=8.6, color="#334155", anchor="start")
            ky += 16.5

    sc.save(SVG_DIR / "A-2.svg", DRAWIO_DIR / "A-2_Modified_Floor_Plan.drawio")


if __name__ == "__main__":
    write_floor_boq()
    generate_sheet_a1()
    generate_sheet_a2()
    print("Generated A-1, A-2, and floor_boq.csv")
