"""Dual-output CAD sheet engine: native multi-layer .drawio XML + crisp paired SVG.

Produces publication-grade 1680 x 1120 engineering sheets with consistent borders,
architectural scale (27 px/m for 40 x 26 m floor plate), dimension chains, legend sidebar,
north arrow, scale bar, and Group1 title block with zero clipped or overlapping text.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import List, Optional, Tuple

from model import (
    BUILDING_H_M,
    BUILDING_W_M,
    GROUP_ID,
    ORG_NAME,
    PRICE_DATE,
)

SHEET_W = 1680
SHEET_H = 1120

# Architectural floorplan viewport inside the sheet
OX = 92.0
OY = 96.0
SCALE = 27.0  # 40 m -> 1080 px (X=92..1172), 26 m -> 702 px (Y=96..798)

# Right sidebar & title block bounds
SIDE_X = 1208.0
SIDE_Y = 38.0
SIDE_W = 434.0
SIDE_H = 898.0

TB_X = 22.0
TB_Y = 954.0
TB_W = 1636.0
TB_H = 144.0


def px(xm: float) -> float:
    return OX + xm * SCALE


def py(ym: float) -> float:
    return OY + ym * SCALE


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


class SheetCanvas:
    """Simultaneously records native draw.io mxCells and paired SVG primitives."""

    def __init__(
        self,
        sheet_no: str,
        sheet_title: str,
        discipline: str,
        drawn_by: str,
        scale_label: str = "1:100 (A3) / 1:150 (1/8 Board)",
    ):
        self.sheet_no = sheet_no
        self.sheet_title = sheet_title
        self.discipline = discipline
        self.drawn_by = drawn_by
        self.scale_label = scale_label

        self.svg_defs: List[str] = []
        self.svg_elems: List[str] = []
        self.mx_cells: List[str] = []
        self._id = 10

        # Draw outer frame + title block base
        self._init_frame()

    def _nid(self) -> str:
        self._id += 1
        return f"c{self._id}"

    def _init_frame(self) -> None:
        # Sheet background & border
        self.rect(0, 0, SHEET_W, SHEET_H, fill="#FFFFFF", stroke="none", in_mx=False)
        self.rect(22, 22, SHEET_W - 44, SHEET_H - 44, fill="#FFFFFF", stroke="#1B2A4A", stroke_w=2.4)
        self.rect(27, 27, SHEET_W - 54, SHEET_H - 54, fill="none", stroke="#1B2A4A", stroke_w=0.8)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "#FFFFFF",
        stroke: str = "#1E293B",
        stroke_w: float = 1.0,
        dash: str = "",
        rx: float = 0.0,
        opacity: float = 1.0,
        in_mx: bool = True,
    ) -> None:
        da = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' fill-opacity="{opacity}"' if opacity < 1.0 else ""
        rxa = f' rx="{rx}" ry="{rx}"' if rx > 0 else ""
        self.svg_elems.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"{da}{op}{rxa}/>'
        )
        if in_mx:
            cid = self._nid()
            fc = "none" if fill == "none" else fill
            sc = "none" if stroke == "none" else stroke
            dashed = "dashed=1;" if dash else ""
            rnd = "rounded=1;" if rx > 0 else "rounded=0;"
            style = f"{rnd}whiteSpace=wrap;html=1;fillColor={fc};strokeColor={sc};strokeWidth={stroke_w};{dashed}"
            self.mx_cells.append(
                f'<mxCell id="{cid}" value="" style="{style}" vertex="1" parent="1">'
                f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/>'
                f"</mxCell>"
            )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = "#1E293B",
        stroke_w: float = 1.2,
        dash: str = "",
        in_mx: bool = True,
    ) -> None:
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.svg_elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{stroke_w}"{da} stroke-linecap="round"/>'
        )
        if in_mx:
            cid = self._nid()
            dashed = "dashed=1;" if dash else ""
            style = f"endArrow=none;html=1;strokeColor={stroke};strokeWidth={stroke_w};{dashed}"
            self.mx_cells.append(
                f'<mxCell id="{cid}" value="" style="{style}" edge="1" parent="1">'
                f'<mxGeometry relative="1" as="geometry">'
                f'<mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
                f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/>'
                f"</mxGeometry></mxCell>"
            )

    def polyline(
        self,
        pts: List[Tuple[float, float]],
        stroke: str = "#1D4ED8",
        stroke_w: float = 1.6,
        dash: str = "",
        in_mx: bool = True,
    ) -> None:
        if len(pts) < 2:
            return
        pstr = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.svg_elems.append(
            f'<polyline points="{pstr}" fill="none" stroke="{stroke}" stroke-width="{stroke_w}"'
            f'{da} stroke-linejoin="round" stroke-linecap="round"/>'
        )
        if in_mx:
            for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
                cid = self._nid()
                dashed = "dashed=1;" if dash else ""
                style = f"endArrow=none;html=1;strokeColor={stroke};strokeWidth={stroke_w};{dashed}"
                self.mx_cells.append(
                    f'<mxCell id="{cid}" value="" style="{style}" edge="1" parent="1">'
                    f'<mxGeometry relative="1" as="geometry">'
                    f'<mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
                    f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/>'
                    f"</mxGeometry></mxCell>"
                )

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = "#FFFFFF",
        stroke: str = "#1E293B",
        stroke_w: float = 1.2,
        dash: str = "",
        in_mx: bool = True,
    ) -> None:
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.svg_elems.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"{da}/>'
        )
        if in_mx:
            cid = self._nid()
            fc = "none" if fill == "none" else fill
            sc = "none" if stroke == "none" else stroke
            dashed = "dashed=1;" if dash else ""
            style = f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={fc};strokeColor={sc};strokeWidth={stroke_w};{dashed}"
            self.mx_cells.append(
                f'<mxCell id="{cid}" value="" style="{style}" vertex="1" parent="1">'
                f'<mxGeometry x="{cx - r:.1f}" y="{cy - r:.1f}" width="{2*r:.1f}" height="{2*r:.1f}" as="geometry"/>'
                f"</mxCell>"
            )

    def text(
        self,
        x: float,
        y: float,
        txt: str,
        size: float = 11.0,
        color: str = "#0F172A",
        bold: bool = False,
        anchor: str = "middle",
        italic: bool = False,
        line_h: float = 1.22,
        in_mx: bool = True,
    ) -> None:
        lines = str(txt).split("\n")
        fw = "700" if bold else "400"
        fs = "italic" if italic else "normal"
        # Vertical centering for multi-line block around y
        start_y = y - (len(lines) - 1) * (size * line_h) / 2.0
        tspans = []
        for i, ln in enumerate(lines):
            yy = start_y + i * size * line_h
            tspans.append(f'<tspan x="{x:.1f}" y="{yy:.1f}">{_esc(ln)}</tspan>')
        self.svg_elems.append(
            f'<text font-family="Segoe UI, Arial, sans-serif" font-size="{size:.1f}" '
            f'font-weight="{fw}" font-style="{fs}" fill="{color}" text-anchor="{anchor}" '
            f'dominant-baseline="central">{"".join(tspans)}</text>'
        )
        if in_mx:
            cid = self._nid()
            align = {"start": "left", "middle": "center", "end": "right"}.get(anchor, "center")
            fstyle = (1 if bold else 0) + (2 if italic else 0)
            w = max(40.0, max(len(ln) for ln in lines) * size * 0.62 + 8.0)
            h = max(14.0, len(lines) * size * line_h + 4.0)
            bx = x if align == "left" else (x - w if align == "right" else x - w / 2.0)
            by = y - h / 2.0
            val = _esc("<br>".join(lines))
            style = (
                f"text;html=1;strokeColor=none;fillColor=none;align={align};"
                f"verticalAlign=middle;whiteSpace=wrap;fontFamily=Arial;fontSize={int(round(size))};"
                f"fontColor={color};fontStyle={fstyle};"
            )
            self.mx_cells.append(
                f'<mxCell id="{cid}" value="{val}" style="{style}" vertex="1" parent="1">'
                f'<mxGeometry x="{bx:.1f}" y="{by:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/>'
                f"</mxCell>"
            )

    def draw_dimensions_and_grid(self) -> None:
        """Outer building dimension chains, north arrow, and graphic scale bar."""
        x0, y0 = px(0), py(0)
        x1, y1 = px(BUILDING_W_M), py(BUILDING_H_M)

        # Structural column markers (8 m x 6.5 m grid)
        for gx in [0, 8, 16, 24, 32, 40]:
            self.line(px(gx), y0 - 14, px(gx), y0 - 4, stroke="#94A3B8", stroke_w=0.8)
            col_lbl = chr(ord("A") + gx // 8)
            self.circle(px(gx), y0 - 24, 9.5, fill="#F8FAFC", stroke="#64748B", stroke_w=1.0)
            self.text(px(gx), y0 - 24, col_lbl, size=9.5, bold=True, color="#334155")
        for idx, gy in enumerate([0, 6.5, 13.0, 19.5, 26.0], 1):
            self.line(x0 - 14, py(gy), x0 - 4, py(gy), stroke="#94A3B8", stroke_w=0.8)
            self.circle(x0 - 24, py(gy), 9.5, fill="#F8FAFC", stroke="#64748B", stroke_w=1.0)
            self.text(x0 - 24, py(gy), str(idx), size=9.5, bold=True, color="#334155")

        # Overall top dimension (40.00 m)
        dy_top = y0 - 46
        self.line(x0, dy_top, x1, dy_top, stroke="#0F172A", stroke_w=1.1)
        self.line(x0, dy_top - 6, x0, dy_top + 6, stroke="#0F172A", stroke_w=1.1)
        self.line(x1, dy_top - 6, x1, dy_top + 6, stroke="#0F172A", stroke_w=1.1)
        self.rect((x0 + x1) / 2 - 58, dy_top - 9, 116, 18, fill="#FFFFFF", stroke="none")
        self.text((x0 + x1) / 2, dy_top, "40.00 m (1,040.0 sqm)", size=10.5, bold=True, color="#0F172A")

        # Overall left dimension (26.00 m)
        dx_left = x0 - 48
        self.line(dx_left, y0, dx_left, y1, stroke="#0F172A", stroke_w=1.1)
        self.line(dx_left - 6, y0, dx_left + 6, y0, stroke="#0F172A", stroke_w=1.1)
        self.line(dx_left - 6, y1, dx_left + 6, y1, stroke="#0F172A", stroke_w=1.1)
        self.rect(dx_left - 16, (y0 + y1) / 2 - 14, 32, 28, fill="#FFFFFF", stroke="none")
        self.text(dx_left, (y0 + y1) / 2, "26.0\nm", size=9.5, bold=True, color="#0F172A")

        # Bottom sub-dimensions along X
        dy_bot = y1 + 26
        segs = [(0, 10), (10, 18), (18, 23), (23, 27), (27, 33), (33, 40)]
        self.line(x0, dy_bot, x1, dy_bot, stroke="#475569", stroke_w=0.9)
        for a, b in segs:
            self.line(px(a), dy_bot - 5, px(a), dy_bot + 5, stroke="#475569", stroke_w=0.9)
            self.line(px(b), dy_bot - 5, px(b), dy_bot + 5, stroke="#475569", stroke_w=0.9)
            self.text((px(a) + px(b)) / 2, dy_bot + 13, f"{b - a:.1f} m", size=9.0, color="#334155")

        # Entrance & Fire Exit Callouts
        self.rect(px(2.5), y1 - 3, px(6.5) - px(2.5), 7, fill="#0EA5E9", stroke="#0369A1", stroke_w=1.0)
        self.text(px(4.5), y1 + 52, "MAIN GLASS ENTRANCE (SOUTH)", size=9.5, bold=True, color="#0369A1")

        self.rect(x0 - 4, py(12.2), 7, py(13.8) - py(12.2), fill="#EF4444", stroke="#991B1B", stroke_w=1.0)
        self.text(x0 + 62, py(13.0), "FIRE EXIT W", size=8.5, bold=True, color="#B91C1C")

        # Graphic Scale Bar (bottom left below floor plan)
        sb_x, sb_y = x0, y1 + 78
        self.text(sb_x, sb_y - 12, "GRAPHIC SCALE (METERS)", size=8.5, bold=True, color="#334155", anchor="start")
        for i in range(5):
            fill_c = "#1E293B" if i % 2 == 0 else "#FFFFFF"
            self.rect(sb_x + i * (2 * SCALE), sb_y, 2 * SCALE, 8, fill=fill_c, stroke="#1E293B", stroke_w=0.9)
            self.text(sb_x + i * (2 * SCALE), sb_y + 18, f"{i * 2}", size=8.5, color="#334155")
        self.text(sb_x + 5 * (2 * SCALE), sb_y + 18, "10 m", size=8.5, bold=True, color="#334155")

        # North Arrow (bottom right below floor plan)
        nx, ny = x1 - 45, y1 + 72
        self.circle(nx, ny, 22, fill="#F8FAFC", stroke="#1E293B", stroke_w=1.2)
        self.svg_elems.append(
            f'<polygon points="{nx:.1f},{ny-18:.1f} {nx-7:.1f},{ny+4:.1f} {nx:.1f},{ny-2:.1f} {nx+7:.1f},{ny+4:.1f}" '
            f'fill="#1B2A4A" stroke="#1B2A4A" stroke-width="0.8"/>'
        )
        self.text(nx, ny + 12, "N", size=11.0, bold=True, color="#1B2A4A")

    def draw_title_block(self) -> None:
        """Crisp USC/Engineering Title Block with Group1 (zero placeholders, zero clipping)."""
        self.rect(TB_X, TB_Y, TB_W, TB_H, fill="#F8FAFC", stroke="#1B2A4A", stroke_w=1.8)
        # Vertical dividers
        cols = [TB_X, 500, 1020, 1340, 1510, TB_X + TB_W]
        for cx in cols[1:-1]:
            self.line(cx, TB_Y, cx, TB_Y + TB_H, stroke="#1B2A4A", stroke_w=1.2)
        # Horizontal split in cols 2 & 3
        mid_y = TB_Y + 72
        self.line(500, mid_y, 1510, mid_y, stroke="#94A3B8", stroke_w=0.9)

        # Col 1: Project & Organization
        self.rect(TB_X, TB_Y, 500 - TB_X, 32, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
        self.text((TB_X + 500) / 2, TB_Y + 16, "PROPOSED STRUCTURED CABLING & NETWORK INFRASTRUCTURE", size=10.0, bold=True, color="#FFFFFF")
        self.text(38, TB_Y + 56, ORG_NAME, size=14.5, bold=True, color="#0F172A", anchor="start")
        self.text(38, TB_Y + 84, "Building 2 (Visayas — Flagship HQ): Cebu IT Park, Cebu City", size=10.5, color="#334155", anchor="start")
        self.text(38, TB_Y + 106, "Floor Plate: 40.0 m × 26.0 m = 1,040.0 sqm (Single Floor, 24/7 Operations)", size=9.8, color="#475569", anchor="start")
        self.text(38, TB_Y + 127, "University of San Carlos — Dept. of Computer Engineering (CPE 3105)", size=9.2, italic=True, color="#64748B", anchor="start")

        # Col 2: Sheet Title & Discipline
        self.text(516, TB_Y + 18, "SHEET TITLE", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(516, TB_Y + 46, self.sheet_title, size=10.8, bold=True, color="#1B2A4A", anchor="start")
        self.text(516, mid_y + 18, "DISCIPLINE / STANDARD COMPLIANCE", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(516, mid_y + 45, self.discipline, size=10.2, color="#1E293B", anchor="start")

        # Col 3: Group Name & Responsible Member
        self.text(1036, TB_Y + 18, "DESIGN TEAM / GROUP", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(1036, TB_Y + 46, f"{GROUP_ID}  (CPE 3105 — Dr. G. S. Monserate)", size=10.5, bold=True, color="#0F172A", anchor="start")
        self.text(1036, mid_y + 18, "RESPONSIBLE MEMBER", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(1036, mid_y + 45, self.drawn_by, size=11.0, bold=True, color="#1E293B", anchor="start")

        # Col 4: Scale & Date
        self.text(1354, TB_Y + 18, "SCALE", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(1354, TB_Y + 45, self.scale_label, size=9.2, bold=True, color="#0F172A", anchor="start")
        self.text(1354, mid_y + 18, "DATE / REV", size=8.5, bold=True, color="#64748B", anchor="start")
        self.text(1354, mid_y + 45, f"{PRICE_DATE} | Rev 1.0", size=10.0, color="#0F172A", anchor="start")

        # Col 5: Sheet Number Badge
        self.rect(1510, TB_Y, TB_X + TB_W - 1510, TB_H, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
        self.text(1584, TB_Y + 34, "SHEET NO.", size=9.5, bold=True, color="#CBD5E1")
        self.text(1584, TB_Y + 86, self.sheet_no, size=32.0, bold=True, color="#FFFFFF")

    def sidebar_box(self, title: str) -> Tuple[float, float, float]:
        """Draws the right-hand legend/notes panel and returns (x_pad, y_cursor, inner_w)."""
        self.rect(SIDE_X, SIDE_Y, SIDE_W, SIDE_H, fill="#F8FAFC", stroke="#1B2A4A", stroke_w=1.4)
        self.rect(SIDE_X, SIDE_Y, SIDE_W, 34, fill="#1B2A4A", stroke="#1B2A4A", stroke_w=1.0)
        self.text(SIDE_X + SIDE_W / 2, SIDE_Y + 17, title, size=11.5, bold=True, color="#FFFFFF")
        return SIDE_X + 16, SIDE_Y + 52, SIDE_W - 32

    def save(self, svg_path: Path, drawio_path: Path) -> None:
        self.draw_title_block()
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        drawio_path.parent.mkdir(parents=True, exist_ok=True)

        svg_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}" height="{SHEET_H}" '
            f'viewBox="0 0 {SHEET_W} {SHEET_H}">\n'
            f'<defs>{"".join(self.svg_defs)}</defs>\n'
            + "\n".join(self.svg_elems)
            + "\n</svg>\n"
        )
        svg_path.write_text(svg_xml, encoding="utf-8")

        mx_xml = (
            f'<mxfile host="app.diagrams.net" modified="2026-11-25T15:00:00.000Z" agent="Group1-RJ-Esports" version="24.0.0">\n'
            f'  <diagram id="sheet-{self.sheet_no}" name="{_esc(self.sheet_no + " - " + self.sheet_title)}">\n'
            f'    <mxGraphModel dx="{SHEET_W}" dy="{SHEET_H}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{SHEET_W}" pageHeight="{SHEET_H}" background="#FFFFFF">\n'
            f'      <root>\n'
            f'        <mxCell id="0"/>\n'
            f'        <mxCell id="1" parent="0"/>\n'
            + "\n".join("        " + c for c in self.mx_cells)
            + "\n      </root>\n"
            f"    </mxGraphModel>\n"
            f"  </diagram>\n"
            f"</mxfile>\n"
        )
        drawio_path.write_text(mx_xml, encoding="utf-8")


def draw_rooms_base(sc: SheetCanvas, show_labels: bool = True, muted: bool = False) -> None:
    """Draw the 19 architectural rooms of Cebu Flagship HQ with crisp walls & door breaks."""
    from model import ROOMS

    for rm in ROOMS:
        x, y, w, h = px(rm.x), py(rm.y), rm.w * SCALE, rm.h * SCALE
        fill = "#FAFAFA" if muted else rm.zone_color
        sc.rect(x, y, w, h, fill=fill, stroke="#334155", stroke_w=1.5 if not muted else 1.1)
        if show_labels:
            if rm.code == "COR-MAIN":
                sc.text(x + w / 2, y + h / 2, rm.short, size=10.5, bold=True, color="#334155")
            elif rm.w <= 2.6:
                sc.text(x + w / 2, y + h / 2 - 14, rm.short, size=9.0, bold=True, color="#0F172A")
                sc.text(x + w / 2, y + h / 2 + 12, f"{rm.w:.1f}×{rm.h:.0f}m", size=8.0, color="#475569")
                sc.text(x + w / 2, y + h / 2 + 25, f"{rm.area:.0f}m²", size=8.0, bold=True, color="#1E293B")
            elif rm.w <= 4.0 and rm.h <= 6.0:
                sc.text(x + w / 2, y + h / 2 - 16, rm.short, size=9.2, bold=True, color="#0F172A")
                sc.text(x + w / 2, y + h / 2 + 16, f"{rm.w:.1f}×{rm.h:.0f}m\n({rm.area:.0f} sqm)", size=8.2, color="#475569")
            else:
                sc.text(x + w / 2, y + h / 2 - 14, rm.short, size=11.0, bold=True, color="#0F172A")
                sc.text(x + w / 2, y + h / 2 + 18, f"{rm.w:.1f} m × {rm.h:.1f} m  |  {rm.area:.0f} sqm", size=9.2, color="#475569")

    # Thick exterior perimeter wall
    sc.rect(px(0), py(0), BUILDING_W_M * SCALE, BUILDING_H_M * SCALE, fill="none", stroke="#0F172A", stroke_w=3.2)

    # Interior door openings along central corridor (white wall breaks + door swing ticks)
    corridor_doors = [
        (8.5, 12.0), (21.5, 12.0), (30.5, 12.0),  # North rooms to corridor
        (5.0, 14.0), (14.0, 14.0), (20.0, 14.0), (24.8, 14.0), (29.8, 14.0), (34.5, 14.0), (38.0, 14.0),  # South rooms
    ]
    for dx, dy in corridor_doors:
        sc.line(px(dx - 0.65), py(dy), px(dx + 0.65), py(dy), stroke="#FFFFFF", stroke_w=3.6, in_mx=False)
        sc.line(px(dx - 0.65), py(dy), px(dx - 0.65), py(dy + (0.9 if dy == 14.0 else -0.9)), stroke="#0F172A", stroke_w=1.2, in_mx=False)
