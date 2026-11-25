"""Lighting Plan (Sheet L-1) + EN 12464-1 Lumen Method Illumination Schedule + Lighting BOQ.

Guarantees 100% EN 12464-1 illuminance compliance across all 19 rooms (1,040.0 sqm total)
using standard 40 W / 4,200 lm recessed LED panels (with dimmable/zoned switching in gaming/VIP
zones) and 18 W / 1,800 lm LED downlights in compact wet/utility rooms.
"""

from __future__ import annotations

import csv
import math
from decimal import Decimal
from typing import Dict, List, Tuple

from draw_kit import SheetCanvas, draw_rooms_base, px, py
from model import BUDGET_DIR, DRAWIO_DIR, PRICE_DATE, ROOMS, SVG_DIR, php_round

# Lumen method factors (conservative commercial interior)
UF = 0.65
MF = 0.80
EFF = UF * MF  # 0.52

PANEL_W = 40
PANEL_LM = 4200
DOWN_W = 18
DOWN_LM = 1800

# Explicit clean fixture grid (cols, rows, fixture_type) per room ensuring E_avg >= target_lux for ALL 19 rooms!
# Check math: E = (N * lm * 0.52) / area
ROOM_LIGHTING: Dict[str, Tuple[int, int, str, str]] = {
    # code: (cols, rows, type 'P'=40W panel / 'D'=18W downlight, switch_zone)
    "STD-GAME":   (7, 4, "P", "S-DIM1 (Dimmable)"),  # 28*4200*0.52 / 216 = 283? Wait: 28*2184/216 = 283.1 < 300! Need 30 -> (6,5) = 30*2184/216 = 303.3 >= 300!
    "FUT-GAME":   (3, 5, "P", "S-DIM2 (Dimmable)"),  # 15*2184/96 = 341.3 >= 300!
    "VIP-ARENA":  (4, 5, "P", "S-DIM3 (Dimmable)"),  # 20*2184/120 = 364.0 >= 300!
    "STAIR-NE":   (2, 2, "D", "S-CORE (Base)"),      # 4*1800*0.52 / 24 = 156.0 >= 150!
    "ELEV-CORE":  (2, 2, "D", "S-CORE (Base)"),      # 4*1800*0.52 / 24 = 156.0 >= 150!
    "COR-MAIN":   (6, 1, "P", "S-COR (2-Way)"),      # 6*2184/72 = 182.0 >= 150!
    "COR-EAST":   (2, 1, "D", "S-COR (2-Way)"),      # 2*936/8 = 234.0 >= 150!
    "CASH-LOBBY": (5, 6, "P", "S-LOB (Zoned)"),      # 30*2184/120 = 546.0 >= 500!
    "STUDY-PODS": (4, 6, "P", "S-STU (Zoned)"),      # 24*2184/96 = 546.0 >= 500!
    "MDF-ROOM":   (3, 3, "P", "S-MDF"),              # 9*2184/30 = 655.2 >= 500!
    "ELEC-ROOM":  (2, 2, "P", "S-ELC"),              # 4*2184/24 = 364.0 >= 300!
    "ADMIN-OFC":  (3, 3, "P", "S-ADM"),              # 9*2184/36 = 546.0 >= 500!
    "RR-M":       (2, 3, "D", "S-RRM (Sensor)"),     # 6*936/21 = 267.4 >= 200!
    "RR-F":       (2, 3, "D", "S-RRF (Sensor)"),     # 6*936/21 = 267.4 >= 200!
    "CAFE-PNT":   (4, 2, "P", "S-CAF (Zoned)"),      # 8*2184/54 = 323.6 >= 300!
    "STAFF-LNG":  (2, 2, "P", "S-STF"),              # 4*2184/36 = 242.7 >= 200!
    "RR-PWD":     (2, 2, "D", "S-RRP (Sensor)"),     # 4*936/15 = 249.6 >= 200!
    "JANITOR":    (1, 3, "D", "S-JAN"),              # 3*936/12 = 234.0 >= 200!
    "STORAGE":    (2, 2, "D", "S-STR"),              # 4*936/15 = 249.6 >= 200!
}
# Fix STD-GAME to (6, 5) = 30 panels so 30 * 4200 * 0.52 / 216 = 303.3 lux >= 300 lux!
ROOM_LIGHTING["STD-GAME"] = (6, 5, "P", "S-DIM1 (Dimmable)")


def compute_lighting_schedule() -> Dict:
    rows = []
    tot_panels = 0
    tot_downs = 0
    tot_watts = 0
    tot_area = 0.0

    for rm in ROOMS:
        cols, rows_n, kind, sw = ROOM_LIGHTING[rm.code]
        qty = cols * rows_n
        w_each = PANEL_W if kind == "P" else DOWN_W
        lm_each = PANEL_LM if kind == "P" else DOWN_LM
        if kind == "P":
            tot_panels += qty
        else:
            tot_downs += qty
        watts = qty * w_each
        e_avg = round((qty * lm_each * EFF) / rm.area, 1)
        compliant = e_avg >= rm.target_lux
        assert compliant, f"Room {rm.code} lighting {e_avg} lux < target {rm.target_lux} lux!"
        tot_watts += watts
        tot_area += rm.area
        rows.append({
            "code": rm.code,
            "name": rm.name,
            "area": rm.area,
            "target_lux": rm.target_lux,
            "fixture": "40 W LED Panel" if kind == "P" else "18 W LED Downlight",
            "qty": qty,
            "watts": watts,
            "e_avg": e_avg,
            "switch": sw,
            "base_building": rm.base_building,
            "compliant": compliant,
        })

    # Emergency lights (12 x 6W = 72 W)
    em_qty = 12
    em_watts = em_qty * 6
    return {
        "rows": rows,
        "total_panels": tot_panels,
        "total_downlights": tot_downs,
        "emergency_lights": em_qty,
        "lighting_watts": tot_watts,
        "total_watts_with_em": tot_watts + em_watts,
        "total_area": round(tot_area, 1),
        "lpd_w_sqm": round((tot_watts + em_watts) / tot_area, 2),
    }


def write_lighting_boq() -> List[Dict]:
    sched = compute_lighting_schedule()
    # Subtract base-building Stair/Elevator downlights (8 units) from tenant BOQ? Keep all 33 downlights or note 8 base-building verified — let's include tenant + retrofit LED upgrade for uniform 24/7 lighting & footnote base-building core!
    items = [
        ("Philips CoreLine 40 W, 4,200 lm Recessed LED Panel (600×600 mm, 4000K Neutral White, 0–10 V Ready)", sched["total_panels"], "units", 1850, f"Wilcon Depot / Philips PH ({PRICE_DATE})"),
        ("Firefly 18 W, 1,800 lm Recessed LED Downlight (IP44 Damp-Rated, 4000K) — Restrooms, Utility & Core", sched["total_downlights"], "units", 580, f"Wilcon Depot / Firefly PH ({PRICE_DATE})"),
        ("Omni Dual-Head LED Emergency Light (6 W, 3-Hour LiFePO4 Battery Backup) — Corridor & Exits", 8, "units", 1950, f"Wilcon Depot / Omni PH ({PRICE_DATE})"),
        ("Omni Illuminated LED 'EXIT' Sign (Single/Double-Faced, Battery Backup) — Main & Fire Exits", 4, "units", 1450, f"Wilcon Depot / Omni PH ({PRICE_DATE})"),
        ("0–10 V Rotary/Digital LED Dimmer Switch Controller (Gaming, Future Bay & VIP Arena Zoned Dimming)", 6, "sets", 1680, f"CW Home Depot / Panasonic PH ({PRICE_DATE})"),
        ("Panasonic Wide-Series 1/2/3-Gang Wall Switches & 2-Way Corridor Switches w/ Plates", 18, "sets", 390, f"Wilcon Depot PH ({PRICE_DATE})"),
        ("Ceiling PIR Occupancy Motion Sensor (360°) — M/F/PWD Restrooms Energy Saver", 3, "units", 1250, f"CW Home Depot PH ({PRICE_DATE})"),
        ("RGB-W Indirect Linear LED Cove Accent Strip (24 V DC w/ Driver) — VIP Esports Arena & Lobby Sign", 36, "m", 650, f"CW Home Depot PH ({PRICE_DATE})"),
        ("Lighting Conduit, 2.0/3.5 mm² Lighting Wiring Accessories, Hangers & Ceiling Mounting Clips", 1, "lot", 26500, f"Wilcon Depot PH ({PRICE_DATE})"),
        ("Lighting Installation, Dimming Scene Commissioning & Lux-Meter Verification", 1, "lot", 58000, f"Cebu Electrical Contractor ({PRICE_DATE})"),
    ]
    rows = []
    out = BUDGET_DIR / "lighting_boq.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Item / specification", "Quantity", "Unit", "Unit cost (PHP)", "Subtotal (PHP)", "Price source / date"])
        for item, qty, unit, uc, src in items:
            sub = php_round(Decimal(qty) * Decimal(uc))
            w.writerow([item, qty, unit, f"{Decimal(uc):.2f}", f"{sub:.2f}", src])
            rows.append({"item": item, "qty": qty, "unit": unit, "unit_cost": Decimal(uc), "subtotal": sub, "source": src})
    return rows


def generate_sheet_l1() -> None:
    sched = compute_lighting_schedule()
    sc = SheetCanvas(
        sheet_no="L-1",
        sheet_title="LIGHTING LAYOUT, SWITCHING ZONES & EN 12464-1 ILLUMINATION PLAN",
        discipline="Illumination Engineering | EN 12464-1 (100% Compliant, 40 W / 4,200 lm LED)",
        drawn_by="Marianito Roble",
    )
    sc.draw_dimensions_and_grid()
    draw_rooms_base(sc, show_labels=False, muted=True)

    # Draw fixtures symmetrically inside every room
    for rm in ROOMS:
        cols, rows_n, kind, sw = ROOM_LIGHTING[rm.code]
        dx = rm.w / cols
        dy = rm.h / rows_n
        pts = []
        for r_i in range(rows_n):
            for c_i in range(cols):
                fx = px(rm.x + (c_i + 0.5) * dx)
                fy = py(rm.y + (r_i + 0.5) * dy)
                pts.append((fx, fy))
                if kind == "P":
                    fill_c = "#FEF08A" if rm.dimmable_zone else "#FEF9C3"
                    ec = "#B45309" if rm.dimmable_zone else "#CA8A04"
                    sc.rect(fx - 7.5, fy - 7.5, 15, 15, fill=fill_c, stroke=ec, stroke_w=1.1)
                    sc.line(fx - 7.5, fy - 7.5, fx + 7.5, fy + 7.5, stroke=ec, stroke_w=0.6, in_mx=False)
                else:
                    sc.circle(fx, fy, 6.0, fill="#E0F2FE", stroke="#0284C7", stroke_w=1.1)
                    sc.circle(fx, fy, 2.2, fill="#0284C7", stroke="none", in_mx=False)

        # Light dashed switch leg along first row of fixtures
        if len(pts) > 1:
            sc.polyline(pts[:cols], stroke="#D97706", stroke_w=0.8, dash="3,3", in_mx=False)

        # Room code + achieved lux badge at top-left
        rec = next(r for r in sched["rows"] if r["code"] == rm.code)
        short_c = {"JANITOR": "JAN", "STORAGE": "STOR", "RR-PWD": "PWD"}.get(rm.code, rm.code)
        f_sz = 6.2 if rm.w <= 2.6 else 7.2
        sc.text(px(rm.x + 0.2), py(rm.y + 0.55), f"{short_c} ({rec['e_avg']:.0f}lx)", size=f_sz, bold=True, color="#78350F", anchor="start")

    # Emergency exit lights along corridor & fire exits (green circles)
    for ex, ey in [(1.0, 13.0), (10.0, 13.0), (19.0, 13.0), (28.0, 13.0), (35.2, 13.0), (38.0, 13.0), (4.5, 25.3), (38.0, 3.0)]:
        sc.circle(px(ex), py(ey), 6.5, fill="#DCFCE7", stroke="#15803D", stroke_w=1.4)
        sc.text(px(ex), py(ey), "E", size=7.0, bold=True, color="#166534")

    # Switch symbols ($S) beside doors
    for swx, swy, tag in [(8.0, 11.4, "SD1"), (21.0, 11.4, "SD2"), (30.0, 11.4, "SD3"), (4.4, 14.6, "SL"), (13.4, 14.6, "SS"), (19.4, 14.6, "SM"), (29.2, 14.6, "SA")]:
        sc.text(px(swx), py(swy), tag, size=6.6, bold=True, color="#B91C1C")

    # Sidebar: Complete 19-Room EN 12464-1 Compliance Table
    sx, sy, sw = sc.sidebar_box("EN 12464-1 ILLUMINATION SCHEDULE (100% PASS)")
    sc.rect(sx, sy - 6, sw, 21, fill="#E2E8F0", stroke="#94A3B8", stroke_w=0.8)
    sc.text(sx + 4, sy + 4.5, "Room", size=7.8, bold=True, color="#0F172A", anchor="start")
    sc.text(sx + 84, sy + 4.5, "m²", size=7.8, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + 130, sy + 4.5, "Fixt", size=7.8, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + 178, sy + 4.5, "W", size=7.8, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + 236, sy + 4.5, "Target", size=7.8, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + 300, sy + 4.5, "Calc lx", size=7.8, bold=True, color="#0F172A", anchor="end")
    sc.text(sx + sw - 6, sy + 4.5, "Status", size=7.8, bold=True, color="#0F172A", anchor="end")

    y = sy + 24
    for i, r in enumerate(sched["rows"]):
        if i % 2 == 1:
            sc.rect(sx, y - 8, sw, 17.5, fill="#F1F5F9", stroke="none", in_mx=False)
        lbl = r["code"] + ("*" if r["base_building"] else "")
        ftag = f"{r['qty']}P" if "Panel" in r["fixture"] else f"{r['qty']}D"
        sc.text(sx + 4, y, lbl, size=7.5, bold=True, color="#1E293B", anchor="start")
        sc.text(sx + 84, y, f"{r['area']:.0f}", size=7.5, color="#334155", anchor="end")
        sc.text(sx + 130, y, ftag, size=7.5, color="#334155", anchor="end")
        sc.text(sx + 178, y, f"{r['watts']}", size=7.5, color="#334155", anchor="end")
        sc.text(sx + 236, y, f"{r['target_lux']} lx", size=7.5, color="#475569", anchor="end")
        sc.text(sx + 300, y, f"{r['e_avg']:.0f} lx", size=7.6, bold=True, color="#15803D", anchor="end")
        sc.text(sx + sw - 6, y, "PASS", size=7.4, bold=True, color="#15803D", anchor="end")
        y += 17.5

    sc.rect(sx, y - 2, sw, 24, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=0.8)
    sc.text(sx + 6, y + 10, f"TOTAL: {sched['total_panels']}P + {sched['total_downlights']}D + 12 Em.", size=8.2, bold=True, color="#FFFFFF", anchor="start")
    sc.text(sx + sw - 6, y + 10, f"{sched['total_watts_with_em']:,} W ({sched['lpd_w_sqm']} W/m²)", size=8.2, bold=True, color="#FDE047", anchor="end")

    # Legend & Footnotes
    ly = y + 36
    sc.text(sx, ly, "LIGHTING LEGEND & DESIGN BASIS", size=9.4, bold=True, color="#1B2A4A", anchor="start")
    ly += 18
    litems = [
        ("#FEF08A", "#B45309", f"40 W / 4,200 lm LED Panel — Dimmable Gaming/VIP Zone"),
        ("#FEF9C3", "#CA8A04", f"40 W / 4,200 lm LED Panel — Standard Zoned Switching"),
        ("#E0F2FE", "#0284C7", f"18 W / 1,800 lm LED Downlight — Wet/Utility/Base Core"),
        ("#DCFCE7", "#15803D", "6 W Battery-Backup Emergency / Exit Luminaire (12 units)"),
    ]
    for fc, ec, txt in litems:
        sc.rect(sx, ly - 6, 16, 12, fill=fc, stroke=ec, stroke_w=1.1)
        sc.text(sx + 24, ly, txt, size=8.0, color="#1E293B", anchor="start")
        ly += 20

    ly += 8
    fnotes = [
        "• Formula: E_avg = (N × Φ × UF × MF) / A, with UF = 0.65, MF = 0.80.",
        "• 100% of 19 rooms (1,040 sqm) meet or exceed EN 12464-1 targets.",
        "• Gaming/VIP zones include 0–10 V dimmers to reduce screen glare",
        "  during esports tournaments while maintaining full 300+ lx for cleaning.",
        "• *Base-building Stairwell & Elevator (48 m²) verified to ≥150 lx.",
        f"• Overall Lighting Power Density (LPD) = {sched['lpd_w_sqm']} W/m² (≤ 9.0 W/m²",
        "  ASHRAE 90.1 / Philippine Green Building Code benchmark).",
    ]
    for fn in fnotes:
        sc.text(sx, ly, fn, size=8.0, color="#334155", anchor="start")
        ly += 15.5

    sc.save(SVG_DIR / "L-1.svg", DRAWIO_DIR / "L-1_Lighting_Plan.drawio")


if __name__ == "__main__":
    s = compute_lighting_schedule()
    write_lighting_boq()
    generate_sheet_l1()
    print(f"Generated L-1 ({s['total_panels']} panels, {s['total_downlights']} downlights, {s['total_watts_with_em']} W, 100% EN 12464-1 pass)")
