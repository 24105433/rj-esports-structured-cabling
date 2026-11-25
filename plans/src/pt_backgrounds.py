"""Generates:
1. Scaled Packet Tracer Physical Workspace background PNGs in `pt/backgrounds/` (with clear drop markers):
   - intercity_3_sites.png, city_cebu.png, city_clark.png, city_davao.png, floor_hq.png, floor_clark.png, floor_davao.png
2. Clean publication-grade Report Figures in `report/figs/` (ZERO PT setup instructions!):
   - fig_intercity_map.png, fig_topology.png,
   - fig_floor_clark_orig.png, fig_floor_clark_mod.png, fig_floor_davao_orig.png, fig_floor_davao_mod.png

Uses Natural Earth 50m Philippines coastline GeoJSON (`plans/src/data/phl_50m_naturalearth.json`).
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import List, Tuple

from model import (
    BG_DIR,
    BUILDING_H_M,
    BUILDING_W_M,
    CABINETS,
    DROPS,
    FIGS_DIR,
    GROUP_ID,
    ORG_NAME,
    PLANS_DIR,
    ROOMS,
    SITES,
)
from render_sheets import render_svg_to_png

GEO_PATH = PLANS_DIR / "src" / "data" / "phl_50m_naturalearth.json"


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _save_and_render(svg_text: str, png_path: Path, scale: float = 1.0) -> None:
    svg_tmp = png_path.with_suffix(".svg")
    svg_tmp.parent.mkdir(parents=True, exist_ok=True)
    svg_tmp.write_text(svg_text, encoding="utf-8")
    render_svg_to_png(svg_tmp, png_path, scale=scale)


def _build_intercity_svg(for_pt: bool) -> str:
    W, H = 1200, 900
    geo = json.loads(GEO_PATH.read_text(encoding="utf-8"))
    # Map bounds: lon 116.5..127.5, lat 4.8..19.6
    lon0, lon1 = 116.5, 127.5
    lat0, lat1 = 4.8, 19.6

    def proj(lon: float, lat: float) -> Tuple[float, float]:
        x = 90 + (lon - lon0) / (lon1 - lon0) * (W - 440)
        y = H - 70 - (lat - lat0) / (lat1 - lat0) * (H - 140)
        return x, y

    paths = []
    for poly in geo["coordinates"]:
        for ring in poly:
            pts = " ".join(f"{proj(lo, la)[0]:.1f},{proj(lo, la)[1]:.1f}" for lo, la in ring)
            paths.append(f'<polygon points="{pts}" fill="#E2E8F0" stroke="#64748B" stroke-width="1.0"/>')

    clark_xy = proj(120.5597, 15.1859)
    cebu_xy = proj(123.9064, 10.3303)
    davao_xy = proj(125.6128, 7.0731)

    elems = [
        f'<rect width="{W}" height="{H}" fill="#EFF6FF"/>',
        f'<rect x="16" y="16" width="{W-32}" height="{H-32}" fill="none" stroke="#1B2A4A" stroke-width="2.2"/>',
        f'<rect x="16" y="16" width="{W-32}" height="52" fill="#1B2A4A"/>',
        f'<text x="{W/2}" y="44" font-family="Segoe UI, Arial" font-size="18" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">'
        f'RJ INTERNET CAFÉ &amp; ESPORTS INC. — PHILIPPINES MULTI-BRANCH WAN TOPOLOGY (CEBU ISP HUB)</text>',
        "".join(paths),
    ]

    # WAN Links (Primary solid + Backup dashed)
    # Clark <-> Cebu
    elems.append(f'<line x1="{clark_xy[0]:.1f}" y1="{clark_xy[1]:.1f}" x2="{cebu_xy[0]:.1f}" y2="{cebu_xy[1]:.1f}" stroke="#2563EB" stroke-width="3.6"/>')
    elems.append(f'<line x1="{clark_xy[0]-8:.1f}" y1="{clark_xy[1]+4:.1f}" x2="{cebu_xy[0]-8:.1f}" y2="{cebu_xy[1]+4:.1f}" stroke="#60A5FA" stroke-width="2.0" stroke-dasharray="7,5"/>')
    # Davao <-> Cebu
    elems.append(f'<line x1="{davao_xy[0]:.1f}" y1="{davao_xy[1]:.1f}" x2="{cebu_xy[0]:.1f}" y2="{cebu_xy[1]:.1f}" stroke="#059669" stroke-width="3.6"/>')
    elems.append(f'<line x1="{davao_xy[0]+8:.1f}" y1="{davao_xy[1]-4:.1f}" x2="{cebu_xy[0]+8:.1f}" y2="{cebu_xy[1]-4:.1f}" stroke="#34D399" stroke-width="2.0" stroke-dasharray="7,5"/>')

    # Site Markers
    markers = [
        ("BLDG 1: CLARK, PAMPANGA (LUZON)", "R-CLARK | 10.10.1.0/24 | RIPv2 + Floating AD 130", clark_xy, "#1D4ED8", 18, -24),
        ("BLDG 2: CEBU IT PARK (VISAYAS HQ + ISP)", "R-CEBU & ISP-CEBU | 10.10.0.0/24 | Static + Redist.", cebu_xy, "#DC2626", -312, 8),
        ("BLDG 3: DAVAO CITY (MINDANAO)", "R-DAVAO | 10.10.2.0/24 | EIGRP AS 100 + Floating AD 180", davao_xy, "#047857", -265, 28),
    ]
    for title, sub, (mx, my), col, dx, dy in markers:
        elems.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="11" fill="{col}" stroke="#FFFFFF" stroke-width="3"/>')
        bx, by = mx + dx, my + dy - 16
        bw = 285
        elems.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw}" height="42" rx="5" fill="#FFFFFF" stroke="{col}" stroke-width="1.6" fill-opacity="0.95"/>')
        elems.append(f'<text x="{bx+10:.1f}" y="{by+14:.1f}" font-family="Segoe UI, Arial" font-size="10.5" font-weight="700" fill="{col}">{_esc(title)}</text>')
        elems.append(f'<text x="{bx+10:.1f}" y="{by+30:.1f}" font-family="Segoe UI, Arial" font-size="9.2" fill="#334155">{_esc(sub)}</text>')

    # Right Info Card (Clean for report; PT instructions ONLY if for_pt=True)
    rx, ry, rw = 835, 92, 330
    elems.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="480" rx="6" fill="#FFFFFF" stroke="#1B2A4A" stroke-width="1.4"/>')
    elems.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="32" rx="4" fill="#1B2A4A"/>')
    elems.append(f'<text x="{rx+rw/2}" y="{ry+16}" font-family="Segoe UI, Arial" font-size="11.5" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">INTER-REGIONAL WAN ARCHITECTURE</text>')

    info_lines = [
        ("Supernet (IPv4):", "10.10.0.0/22 (Clean /24 per site)"),
        ("Supernet (IPv6):", "2001:DB8:ACAD::/48 (/52 per site)"),
        ("Central ISP Hub:", "ISP-CEBU (Cebu City, Visayas)"),
        ("Internet Loopback:", "203.0.113.1/24 | 2001:DB8:FFFF::1/64"),
        ("WAN-CEBU-PRI:", "10.10.3.0/30 — Static Summary/Default"),
        ("WAN-CLARK-PRI:", "10.10.3.4/30 — RIPv2 / RIPng"),
        ("WAN-CLARK-BAK:", "10.10.3.12/30 — Floating Static (AD 130)"),
        ("WAN-DAVAO-PRI:", "10.10.3.8/30 — EIGRP AS 100 / EIGRPv6"),
        ("WAN-DAVAO-BAK:", "10.10.3.16/30 — Floating Static (AD 180)"),
        ("Redistribution:", "Single Point on ISP-CEBU (RIP ↔ EIGRP)"),
        ("Floor Plate:", "1,040 sqm (40×26 m) per building"),
    ]
    iy = ry + 54
    for k, v in info_lines:
        elems.append(f'<text x="{rx+14}" y="{iy}" font-family="Segoe UI, Arial" font-size="9.8" font-weight="700" fill="#1E293B">{_esc(k)}</text>')
        elems.append(f'<text x="{rx+14}" y="{iy+14}" font-family="Segoe UI, Arial" font-size="9.5" fill="#475569">{_esc(v)}</text>')
        iy += 35

    if for_pt:
        elems.append(f'<rect x="{rx}" y="592" width="{rw}" height="110" rx="6" fill="#FEF3C7" stroke="#B45309" stroke-width="1.3"/>')
        elems.append(f'<text x="{rx+14}" y="614" font-family="Segoe UI, Arial" font-size="10.5" font-weight="700" fill="#92400E">PT PHYSICAL WORKSPACE SETUP</text>')
        elems.append(f'<text x="{rx+14}" y="636" font-family="Segoe UI, Arial" font-size="9.2" fill="#78350F">In PT: Physical &gt; Intercity &gt; Set Background</text>')
        elems.append(f'<text x="{rx+14}" y="654" font-family="Segoe UI, Arial" font-size="9.2" fill="#78350F">Drag Clark_Luzon, Cebu_Visayas, Davao_Mindanao</text>')
        elems.append(f'<text x="{rx+14}" y="672" font-family="Segoe UI, Arial" font-size="9.2" fill="#78350F">cities onto the red/blue/green site dots.</text>')

    # Attribution footnote (Natural Earth)
    elems.append(f'<text x="32" y="{H-26}" font-family="Segoe UI, Arial" font-size="9.2" fill="#475569">Coastline Geometry: Natural Earth (n.d.), 1:50m Cultural Vectors (Public Domain) | {GROUP_ID} — {ORG_NAME}</text>')

    return f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(elems)}</svg>'


def _build_city_svg(city_title: str, subtitle: str, bldg_name: str, accent: str, has_isp: bool = False) -> str:
    W, H = 1000, 680
    elems = [
        f'<rect width="{W}" height="{H}" fill="#F8FAFC"/>',
        f'<rect x="16" y="16" width="{W-32}" height="{H-32}" fill="#FFFFFF" stroke="#1B2A4A" stroke-width="2"/>',
        f'<rect x="16" y="16" width="{W-32}" height="48" fill="{accent}"/>',
        f'<text x="{W/2}" y="40" font-family="Segoe UI, Arial" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">{_esc(city_title)}</text>',
        f'<text x="{W/2}" y="82" font-family="Segoe UI, Arial" font-size="11.5" fill="#475569" text-anchor="middle">{_esc(subtitle)}</text>',
    ]
    # Clean street grid
    for gx in range(120, 920, 140):
        elems.append(f'<line x1="{gx}" y1="110" x2="{gx}" y2="610" stroke="#E2E8F0" stroke-width="14"/>')
    for gy in range(160, 600, 130):
        elems.append(f'<line x1="60" y1="{gy}" x2="940" y2="{gy}" stroke="#E2E8F0" stroke-width="14"/>')

    # Main Building Drop Zone
    bx = 260 if has_isp else 380
    elems.append(f'<rect x="{bx}" y="220" width="240" height="160" rx="8" fill="#EFF6FF" stroke="{accent}" stroke-width="2.5" stroke-dasharray="8,4"/>')
    elems.append(f'<text x="{bx+120}" y="286" font-family="Segoe UI, Arial" font-size="13" font-weight="700" fill="{accent}" text-anchor="middle">{_esc(bldg_name)}</text>')
    elems.append(f'<text x="{bx+120}" y="310" font-family="Segoe UI, Arial" font-size="10.5" fill="#334155" text-anchor="middle">40 m × 26 m = 1,040 sqm</text>')
    elems.append(f'<text x="{bx+120}" y="334" font-family="Segoe UI, Arial" font-size="9.5" fill="#64748B" text-anchor="middle">Place PT Building Here</text>')

    if has_isp:
        elems.append(f'<rect x="610" y="220" width="220" height="160" rx="8" fill="#FEF2F2" stroke="#DC2626" stroke-width="2.5" stroke-dasharray="8,4"/>')
        elems.append(f'<text x="720" y="286" font-family="Segoe UI, Arial" font-size="13" font-weight="700" fill="#B91C1C" text-anchor="middle">Cebu_ISP_POP</text>')
        elems.append(f'<text x="720" y="310" font-family="Segoe UI, Arial" font-size="10.5" fill="#334155" text-anchor="middle">ISP-CEBU Convergence Hub</text>')
        elems.append(f'<text x="720" y="334" font-family="Segoe UI, Arial" font-size="9.5" fill="#64748B" text-anchor="middle">Place PT ISP Building Here</text>')
        elems.append(f'<line x1="500" y1="300" x2="610" y2="300" stroke="#DC2626" stroke-width="3"/>')

    elems.append(f'<text x="32" y="{H-28}" font-family="Segoe UI, Arial" font-size="9.5" fill="#64748B">PT Background: City View — {GROUP_ID} | {ORG_NAME}</text>')
    return f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(elems)}</svg>'


def _build_floor_hq_pt_svg() -> str:
    """Scaled 40 x 26 m PT floor background for Cebu Flagship HQ with clear closet & drop markers."""
    W, H = 1280, 860
    ox, oy, sc = 40.0, 56.0, 30.0  # 40*30=1200, 26*30=780
    elems = [
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
        f'<rect x="0" y="0" width="{W}" height="40" fill="#1B2A4A"/>',
        f'<text x="{W/2}" y="20" font-family="Segoe UI, Arial" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">'
        f'PT PHYSICAL WORKSPACE — RJ CEBU FLAGSHIP HQ (40 × 26 m = 1,040 sqm) | DRAG DEVICES ONTO MARKERS</text>',
    ]
    for rm in ROOMS:
        x, y, w, h = ox + rm.x * sc, oy + rm.y * sc, rm.w * sc, rm.h * sc
        elems.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{rm.zone_color}" stroke="#334155" stroke-width="1.6"/>')
        elems.append(f'<text x="{x+6:.1f}" y="{y+15:.1f}" font-family="Segoe UI, Arial" font-size="9.5" font-weight="700" fill="#334155">{_esc(rm.code)} ({rm.area:.0f}m²)</text>')
    # Corridor bend-point routing guide line
    elems.append(f'<line x1="{ox+1.5*sc:.1f}" y1="{oy+12.5*sc:.1f}" x2="{ox+35*sc:.1f}" y2="{oy+12.5*sc:.1f}" stroke="#2563EB" stroke-width="2.5" stroke-dasharray="8,4"/>')
    elems.append(f'<text x="{ox+10*sc:.1f}" y="{oy+12.9*sc:.1f}" font-family="Segoe UI, Arial" font-size="9" font-weight="700" fill="#1D4ED8">ROUTE COPPER CABLES ALONG CORRIDOR USING BEND POINTS (≤90m)</text>')
    # Cabinet drop markers
    for k, c in CABINETS.items():
        cx, cy = ox + c["x"] * sc, oy + c["y"] * sc
        elems.append(f'<rect x="{cx-22:.1f}" y="{cy-12:.1f}" width="44" height="24" rx="3" fill="#1E3A8A" stroke="#0F172A" stroke-width="1.5"/>')
        elems.append(f'<text x="{cx:.1f}" y="{cy+1:.1f}" font-family="Segoe UI, Arial" font-size="9" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">{_esc(k)}</text>')
    # Workstation / AP markers
    for d in DROPS:
        dx, dy = ox + d.x * sc, oy + d.y * sc
        col = "#0369A1" if d.kind == "AP" else ("#059669" if d.lan == "HQ-ADMIN-LAN" else "#1D4ED8")
        elems.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="9" fill="#FFFFFF" stroke="{col}" stroke-width="1.6"/>')
        elems.append(f'<text x="{dx:.1f}" y="{dy+0.5:.1f}" font-family="Segoe UI, Arial" font-size="6.8" font-weight="700" fill="{col}" text-anchor="middle" dominant-baseline="central">{_esc(d.drop_id)}</text>')
    return f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(elems)}</svg>'


def _build_branch_floor_svg(branch_name: str, region: str, prefix: str, modified: bool, for_pt: bool) -> str:
    """Builds 40 x 26 m = 1,040 sqm branch floor plan (Original Shell vs Modified Layout, Clean Report or PT Background)."""
    W, H = 1280, 860
    ox, oy, sc = 40.0, 56.0, 30.0
    title_mode = "MODIFIED FLOOR PLAN (AFTER FIT-OUT)" if modified else "ORIGINAL BASE COMMERCIAL SHELL (BEFORE MODIFICATION)"
    if for_pt:
        title_mode = "PT PHYSICAL WORKSPACE FLOOR PLAN (DRAG DEVICES TO MARKERS)"
    elems = [
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
        f'<rect x="0" y="0" width="{W}" height="42" fill="#1B2A4A"/>',
        f'<text x="{W/2}" y="21" font-family="Segoe UI, Arial" font-size="13.5" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">'
        f'RJ INTERNET CAFÉ &amp; ESPORTS INC. — {_esc(branch_name.upper())} ({_esc(region.upper())}) | 40×26 m = 1,040 sqm | {title_mode}</text>',
    ]

    if not modified:
        shell_zones = [
            ("OPEN COMMERCIAL SHELL (WEST)", 0, 0, 26, 26, "#FAFAFA"),
            ("OPEN COMMERCIAL SHELL (EAST)", 26, 0, 10, 26, "#FAFAFA"),
            ("BASE STAIRWELL", 36, 0, 4, 8, "#ECEFF1"),
            ("BASE ELEVATOR", 36, 8, 4, 8, "#ECEFF1"),
            ("BASE UTILITY CORE", 36, 16, 4, 10, "#ECEFF1"),
        ]
        for nm, x, y, w, h, col in shell_zones:
            elems.append(f'<rect x="{ox+x*sc:.1f}" y="{oy+y*sc:.1f}" width="{w*sc:.1f}" height="{h*sc:.1f}" fill="{col}" stroke="#475569" stroke-width="1.8" stroke-dasharray="6,4"/>')
            elems.append(f'<text x="{ox+(x+w/2)*sc:.1f}" y="{oy+(y+h/2)*sc:.1f}" font-family="Segoe UI, Arial" font-size="13" font-weight="700" fill="#475569" text-anchor="middle">{_esc(nm)} ({w*h:.0f} m²)</text>')
    else:
        # Modified Branch Layout (40 x 26 m = 1,040 sqm exact!)
        b_rooms = [
            ("BR-GAME",  "Branch Gaming Arena (16 PCs + 2 APs)", 0, 0, 22, 12, "#E3F2FD"),
            ("BR-FUT",   "Future Gaming / Tournament Expansion (16 Seats)", 22, 0, 14, 12, "#EDF7ED"),
            ("BR-STAIR", "Fire Exit Stair (Base)", 36, 0, 4, 6, "#ECEFF1"),
            ("BR-ELEV",  "Elevator Core (Base)", 36, 6, 4, 6, "#ECEFF1"),
            ("BR-COR",   "Main Circulation Corridor (2.0 m Clear — Fire Exit West)", 0, 12, 40, 2, "#F5F5F5"),
            ("BR-CASH",  "Cashier / POS, Printing & Lobby", 0, 14, 12, 12, "#FFF8E1"),
            ("BR-CAFE",  "Café & Snack Pantry", 12, 14, 10, 12, "#FFF3E0"),
            ("BR-MDF",   f"{prefix}-MDF / Telecom Room", 22, 14, 5, 6, "#FFEBEE"),
            ("BR-ELEC",  "Electrical Room", 27, 14, 4, 6, "#FBE9E7"),
            ("BR-ADM",   f"Admin / IT ({prefix}-IT-PC)", 31, 14, 5, 6, "#E0F2F1"),
            ("BR-RR",    "Restrooms (M / F / PWD)", 36, 14, 4, 12, "#E0F7FA"),
            ("BR-STF",   "Staff Lounge & Storage", 22, 20, 14, 6, "#F3E5F5"),
        ]
        assert sum(w * h for _, _, _, _, w, h, _ in b_rooms) == 1040
        for code, nm, x, y, w, h, col in b_rooms:
            elems.append(f'<rect x="{ox+x*sc:.1f}" y="{oy+y*sc:.1f}" width="{w*sc:.1f}" height="{h*sc:.1f}" fill="{col}" stroke="#334155" stroke-width="1.6"/>')
            cy_txt = oy + (y + h / 2) * sc
            fs = 11.5 if w >= 10 else 8.8
            elems.append(f'<text x="{ox+(x+w/2)*sc:.1f}" y="{cy_txt-6:.1f}" font-family="Segoe UI, Arial" font-size="{fs}" font-weight="700" fill="#0F172A" text-anchor="middle">{_esc(nm)}</text>')
            elems.append(f'<text x="{ox+(x+w/2)*sc:.1f}" y="{cy_txt+12:.1f}" font-family="Segoe UI, Arial" font-size="9.5" fill="#475569" text-anchor="middle">{w} m × {h} m ({w*h} sqm)</text>')

        if for_pt:
            # Show PT closet & host markers
            pts = [
                (f"{prefix}-MDF", 24.5, 16.5, "#1E3A8A"),
                (f"{prefix}-GAM-01", 6.0, 5.0, "#1D4ED8"),
                (f"{prefix}-GAM-02", 14.0, 5.0, "#1D4ED8"),
                (f"{prefix}-IT-PC", 33.5, 17.5, "#059669"),
                (f"{prefix}-POS-01", 6.0, 18.0, "#059669"),
            ]
            for lbl, mx, my, col in pts:
                elems.append(f'<rect x="{ox+mx*sc-38:.1f}" y="{oy+my*sc-11:.1f}" width="76" height="22" rx="3" fill="{col}" stroke="#FFFFFF" stroke-width="1.4"/>')
                elems.append(f'<text x="{ox+mx*sc:.1f}" y="{oy+my*sc+1:.1f}" font-family="Segoe UI, Arial" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">{_esc(lbl)}</text>')

    elems.append(f'<rect x="{ox}" y="{oy}" width="{BUILDING_W_M*sc}" height="{BUILDING_H_M*sc}" fill="none" stroke="#0F172A" stroke-width="3.0"/>')
    elems.append(f'<text x="{ox}" y="{H-10}" font-family="Segoe UI, Arial" font-size="9.5" fill="#475569">Scale: 1:100 (40.0 m × 26.0 m = 1,040.0 sqm) | Conceptual Plate by {GROUP_ID} ({ORG_NAME}, Nov 2026)</text>')
    return f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(elems)}</svg>'


def _build_logical_topology_svg() -> str:
    """Clean high-resolution logical topology diagram (`report/figs/fig_topology.png`)."""
    W, H = 1440, 860
    e = [
        f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
        f'<rect x="14" y="14" width="{W-28}" height="{H-28}" fill="#F8FAFC" stroke="#1B2A4A" stroke-width="2"/>',
        f'<rect x="14" y="14" width="{W-28}" height="46" fill="#1B2A4A"/>',
        f'<text x="{W/2}" y="37" font-family="Segoe UI, Arial" font-size="15.5" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">'
        f'RJ INTERNET CAFÉ &amp; ESPORTS INC. — MULTI-BRANCH DUAL-STACK LOGICAL NETWORK TOPOLOGY ({GROUP_ID})</text>',
    ]

    def box(x, y, w, h, title, sub, fc, ec, title_col="#0F172A"):
        e.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fc}" stroke="{ec}" stroke-width="1.8"/>')
        sub_lines = str(sub).split("\n")
        title_y = y + 18 if len(sub_lines) >= 2 else y + h / 2 - 8
        e.append(f'<text x="{x+w/2}" y="{title_y:.1f}" font-family="Segoe UI, Arial" font-size="10.0" font-weight="700" fill="{title_col}" text-anchor="middle">{_esc(title)}</text>')
        for idx_l, sl in enumerate(sub_lines):
            sy_l = (title_y + 16 + idx_l * 13.5) if len(sub_lines) >= 2 else (y + h / 2 + 10)
            e.append(f'<text x="{x+w/2}" y="{sy_l:.1f}" font-family="Segoe UI, Arial" font-size="8.0" fill="#334155" text-anchor="middle">{_esc(sl)}</text>')

    def zone_bg(x, y, w, h, title, fc, ec):
        e.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fc}" stroke="{ec}" stroke-width="1.5" stroke-dasharray="6,3"/>')
        e.append(f'<text x="{x+12}" y="{y+20}" font-family="Segoe UI, Arial" font-size="11" font-weight="700" fill="{ec}">{_esc(title)}</text>')

    # Zone containers
    zone_bg(32,  250, 340, 560, "BLDG 1: CLARK BRANCH (LUZON) — RIPv2 / RIPng", "#EFF6FF", "#1D4ED8")
    zone_bg(392, 250, 656, 560, "BLDG 2: CEBU FLAGSHIP HQ (VISAYAS) — 3-TIER HIERARCHY & STATIC", "#F0FDF4", "#15803D")
    zone_bg(1068, 250, 340, 560, "BLDG 3: DAVAO BRANCH (MINDANAO) — EIGRP AS 100", "#FAF5FF", "#7E22CE")

    # Central ISP Convergence Hub
    box(530, 82, 380, 74, "ISP-CEBU (Cisco 2911 — Central Convergence Hub)",
        "Single Redistribution: RIPv2 ↔ EIGRP 100 ↔ Static | Lo0: 203.0.113.1/24 & 2001:DB8:FFFF::1/64", "#FEE2E2", "#B91C1C", "#991B1B")

    # Site Routers
    box(95,  290, 210, 62, "R-CLARK (Cisco 2911)", "Summary: 10.10.1.0/24 | :2000::/52", "#DBEAFE", "#1D4ED8")
    box(615, 290, 210, 62, "R-CEBU (Cisco 2911)",  "Summary: 10.10.0.0/24 | :1000::/52", "#DCFCE7", "#15803D")
    box(1135, 290, 210, 62, "R-DAVAO (Cisco 2911)", "Summary: 10.10.2.0/24 | :3000::/52", "#F3E8FF", "#7E22CE")

    # WAN Links (Primary + Backup Floating Static)
    # ISP <-> Clark
    e.append('<polyline points="530,115 200,115 200,290" fill="none" stroke="#1D4ED8" stroke-width="2.6"/>')
    e.append('<polyline points="530,132 165,132 165,290" fill="none" stroke="#60A5FA" stroke-width="1.8" stroke-dasharray="6,4"/>')
    e.append('<text x="215" y="106" font-family="Segoe UI, Arial" font-size="8.8" font-weight="700" fill="#1E40AF">WAN-CLARK-PRI: 10.10.3.4/30 (RIPv2 / RIPng)</text>')
    e.append('<text x="215" y="150" font-family="Segoe UI, Arial" font-size="8.4" fill="#3B82F6">WAN-CLARK-BAK: 10.10.3.12/30 (Floating AD 130)</text>')

    # ISP <-> Cebu
    e.append('<line x1="720" y1="156" x2="720" y2="290" stroke="#15803D" stroke-width="2.8"/>')
    e.append('<text x="732" y="205" font-family="Segoe UI, Arial" font-size="8.8" font-weight="700" fill="#166534">WAN-CEBU-PRI: 10.10.3.0/30</text>')
    e.append('<text x="732" y="220" font-family="Segoe UI, Arial" font-size="8.4" fill="#15803D">Static Summary + Default Route</text>')

    # ISP <-> Davao
    e.append('<polyline points="910,115 1240,115 1240,290" fill="none" stroke="#7E22CE" stroke-width="2.6"/>')
    e.append('<polyline points="910,132 1275,132 1275,290" fill="none" stroke="#C084FC" stroke-width="1.8" stroke-dasharray="6,4"/>')
    e.append('<text x="955" y="106" font-family="Segoe UI, Arial" font-size="8.8" font-weight="700" fill="#6B21A8">WAN-DAVAO-PRI: 10.10.3.8/30 (EIGRP 100)</text>')
    e.append('<text x="955" y="150" font-family="Segoe UI, Arial" font-size="8.4" fill="#9333EA">WAN-DAVAO-BAK: 10.10.3.16/30 (Floating AD 180)</text>')

    # Clark LANs
    box(48,  420, 145, 56, "SW-CLK-GAM (2960)", "Gi0/0: 10.10.1.0/26", "#FFFFFF", "#2563EB")
    box(212, 420, 145, 56, "SW-CLK-ADM (2960)", "Gi0/1: 10.10.1.64/28", "#FFFFFF", "#059669")
    e.append('<line x1="160" y1="352" x2="120" y2="420" stroke="#1D4ED8" stroke-width="1.8"/>')
    e.append('<line x1="240" y1="352" x2="284" y2="420" stroke="#059669" stroke-width="1.8"/>')
    box(48,  530, 145, 76, "CLK-GAMING-LAN", "16 Gaming PCs + 3 APs\nACL: No Admin, No SRV-2/FTP", "#DBEAFE", "#1D4ED8")
    box(212, 530, 145, 76, "CLK-ADMIN-LAN",  "CLK-IT-PC (.70 SSH)\n3 Staff/POS + Prt + AP", "#ECFDF5", "#059669")
    e.append('<line x1="120" y1="476" x2="120" y2="530" stroke="#1D4ED8" stroke-width="1.6"/>')
    e.append('<line x1="284" y1="476" x2="284" y2="530" stroke="#059669" stroke-width="1.6"/>')
    box(48, 650, 309, 130, "Clark Physical Path & DHCP",
        "PC → Wall Mount → PP-CLK → Switch → R-CLARK\nDHCPv4: Router Pools | IPv6: Stateful DHCPv6\nPassive LANs: Gi0/0, Gi0/1, Se0/0/1 (RIPv2)", "#FFFFFF", "#94A3B8")

    # Cebu HQ 3-Tier Hierarchy
    box(418, 405, 195, 54, "SW-CORE (3560-24PS)", "MDF Core — Gi0/0: 10.10.0.0/26", "#EDE9FE", "#6D28D9")
    box(642, 405, 185, 54, "SW-ADM (2960-24TT)",  "IDF-2 — Gi0/1: 10.10.0.64/27", "#ECFDF5", "#059669")
    box(846, 405, 185, 54, "SW-SRV (2960-24TT)",  "MDF — Gi0/2: 10.10.0.96/28", "#FEF3C7", "#B45309")
    e.append('<line x1="660" y1="352" x2="515" y2="405" stroke="#6D28D9" stroke-width="2.0"/>')
    e.append('<line x1="720" y1="352" x2="734" y2="405" stroke="#059669" stroke-width="2.0"/>')
    e.append('<line x1="780" y1="352" x2="938" y2="405" stroke="#B45309" stroke-width="2.0"/>')

    # Distribution Layer
    box(410, 500, 145, 50, "DSW-1 (IDF-1)", "3560-24PS (OM3 Fiber)", "#DBEAFE", "#1D4ED8")
    box(570, 500, 145, 50, "DSW-2 (IDF-2)", "3560-24PS (OM3 Fiber)", "#DBEAFE", "#1D4ED8")
    e.append('<line x1="485" y1="459" x2="482" y2="500" stroke="#EA580C" stroke-width="2.4"/>')
    e.append('<line x1="545" y1="459" x2="642" y2="500" stroke="#EA580C" stroke-width="2.4"/>')

    # Access Layer (HQ)
    box(404, 595, 118, 72, "SW-GAM1", "20 PCs + 2 APs\nPP-G → WM", "#FFFFFF", "#0284C7")
    box(530, 595, 118, 72, "SW-VIP",  "10 VIP + 2 APs\nPP-V → WM", "#FFFFFF", "#0284C7")
    box(656, 595, 118, 72, "SW-STU",  "6 PCs + 3 APs\nPP-S → WM", "#FFFFFF", "#0284C7")
    box(782, 595, 120, 72, "Admin/POS", "IT-PC (.70 SSH)\nPOS/Prt/AP-08", "#ECFDF5", "#059669")
    box(910, 595, 124, 72, "SRV-1 & SRV-2", ".98 DNS/DHCP\n.99 Billing/POS", "#FEF9C3", "#B45309")

    e.append('<line x1="465" y1="550" x2="463" y2="595" stroke="#7C3AED" stroke-width="1.6"/>')
    e.append('<line x1="505" y1="550" x2="589" y2="595" stroke="#7C3AED" stroke-width="1.6"/>')
    e.append('<line x1="642" y1="550" x2="715" y2="595" stroke="#7C3AED" stroke-width="1.6"/>')
    e.append('<line x1="734" y1="459" x2="842" y2="595" stroke="#059669" stroke-width="1.6"/>')
    e.append('<line x1="938" y1="459" x2="972" y2="595" stroke="#B45309" stroke-width="1.6"/>')

    box(408, 692, 624, 98, "Security Enforcement (4 Inbound ACL Objectives — IPv4 + IPv6 Mirror, VTY 0 15)",
        "1) SSH VTY 0 15: IT-PC, CLK-IT-PC, DVO-IT-PC only | 2) SRV-2 (.99): HQ-ADMIN-LAN only (Gaming/Study/Branches blocked)\n"
        "3) Branch Gaming blocked from Branch Admin | 4) FTP (20/21) to SRV-1 blocked for Gaming while HTTP (80) & DNS (53) permitted",
        "#FEF2F2", "#DC2626", "#991B1B")

    # Davao LANs
    box(1084, 420, 145, 56, "SW-DVO-GAM (2960)", "Gi0/0: 10.10.2.0/26", "#FFFFFF", "#7E22CE")
    box(1248, 420, 145, 56, "SW-DVO-ADM (2960)", "Gi0/1: 10.10.2.64/28", "#FFFFFF", "#059669")
    e.append('<line x1="1200" y1="352" x2="1156" y2="420" stroke="#7E22CE" stroke-width="1.8"/>')
    e.append('<line x1="1280" y1="352" x2="1320" y2="420" stroke="#059669" stroke-width="1.8"/>')
    box(1084, 530, 145, 76, "DVO-GAMING-LAN", "16 Gaming PCs + 3 APs\nACL: No Admin, No SRV-2/FTP", "#F3E8FF", "#7E22CE")
    box(1248, 530, 145, 76, "DVO-ADMIN-LAN",  "DVO-IT-PC (.70 SSH)\n3 Staff/POS + Prt + AP", "#ECFDF5", "#059669")
    e.append('<line x1="1156" y1="476" x2="1156" y2="530" stroke="#7E22CE" stroke-width="1.6"/>')
    e.append('<line x1="1320" y1="476" x2="1320" y2="530" stroke="#059669" stroke-width="1.6"/>')
    box(1084, 650, 309, 130, "Davao Physical Path & DHCP",
        "PC → Wall Mount → PP-DVO → Switch → R-DAVAO\nDHCPv4: Router Pools | IPv6: Stateful DHCPv6\nPassive LANs: Gi0/0, Gi0/1 (EIGRP AS 100)", "#FFFFFF", "#94A3B8")

    return f'<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(e)}</svg>'


def main() -> None:
    # 1. Packet Tracer Physical Workspace Backgrounds (`pt/backgrounds/`)
    _save_and_render(_build_intercity_svg(for_pt=True), BG_DIR / "intercity_3_sites.png")
    _save_and_render(_build_city_svg("CEBU CITY (VISAYAS) — FLAGSHIP HQ & ISP CONVERGENCE", "Cebu IT Park, Apas, Cebu City | Building 2 + Central ISP Hub", "RJ_Cebu_Flagship_HQ", "#15803D", has_isp=True), BG_DIR / "city_cebu.png")
    _save_and_render(_build_city_svg("CLARK FREEPORT ZONE (LUZON) — BRANCH CAFÉ", "Angeles City, Pampanga | Building 1 (RIPv2 / RIPng Branch)", "RJ_Clark_Branch", "#1D4ED8", has_isp=False), BG_DIR / "city_clark.png")
    _save_and_render(_build_city_svg("DAVAO CITY (MINDANAO) — BRANCH CAFÉ", "Matina IT Park / Poblacion District, Davao City | Building 3 (EIGRP AS 100)", "RJ_Davao_Branch", "#7E22CE", has_isp=False), BG_DIR / "city_davao.png")
    _save_and_render(_build_floor_hq_pt_svg(), BG_DIR / "floor_hq.png")
    _save_and_render(_build_branch_floor_svg("Clark Branch Café", "Luzon", "CLK", modified=True, for_pt=True), BG_DIR / "floor_clark.png")
    _save_and_render(_build_branch_floor_svg("Davao Branch Café", "Mindanao", "DVO", modified=True, for_pt=True), BG_DIR / "floor_davao.png")

    # 2. Clean Report Figures (`report/figs/` — ZERO PT setup instructions!)
    _save_and_render(_build_intercity_svg(for_pt=False), FIGS_DIR / "fig_intercity_map.png", scale=1.5)
    _save_and_render(_build_logical_topology_svg(), FIGS_DIR / "fig_topology.png", scale=1.5)
    _save_and_render(_build_branch_floor_svg("Clark Branch Café", "Luzon", "CLK", modified=False, for_pt=False), FIGS_DIR / "fig_floor_clark_orig.png", scale=1.2)
    _save_and_render(_build_branch_floor_svg("Clark Branch Café", "Luzon", "CLK", modified=True, for_pt=False), FIGS_DIR / "fig_floor_clark_mod.png", scale=1.2)
    _save_and_render(_build_branch_floor_svg("Davao Branch Café", "Mindanao", "DVO", modified=False, for_pt=False), FIGS_DIR / "fig_floor_davao_orig.png", scale=1.2)
    _save_and_render(_build_branch_floor_svg("Davao Branch Café", "Mindanao", "DVO", modified=True, for_pt=False), FIGS_DIR / "fig_floor_davao_mod.png", scale=1.2)
    print("Generated all 7 PT backgrounds + 6 clean report figures.")


if __name__ == "__main__":
    main()
