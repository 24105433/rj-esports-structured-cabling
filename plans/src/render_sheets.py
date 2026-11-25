"""Offline high-resolution SVG -> PNG rasterizer via headless Microsoft Edge (--no-sandbox).

Renders all 8 CAD engineering sheets (A-1..C-2), plus any SVG diagrams/backgrounds
to crisp 1680 x 1120 (or native SVG size) PNGs with zero network dependency.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

from model import SHEETS_DIR, SVG_DIR

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def find_browser() -> str:
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Microsoft Edge or Google Chrome not found for headless SVG rasterization.")


def svg_dimensions(svg_path: Path) -> tuple[int, int]:
    head = svg_path.read_text(encoding="utf-8")[:1500]
    mw = re.search(r'width="(\d+(?:\.\d+)?)"', head)
    mh = re.search(r'height="(\d+(?:\.\d+)?)"', head)
    if mw and mh:
        return int(float(mw.group(1))), int(float(mh.group(1)))
    return 1680, 1120


def render_svg_to_png(svg_path: Path, png_path: Path, scale: float = 1.0) -> None:
    browser = find_browser()
    w, h = svg_dimensions(svg_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    # Build tiny self-contained HTML wrapper so Edge never adds scrollbars or margins
    html_tmp = png_path.with_suffix(".render.html")
    svg_text = svg_path.read_text(encoding="utf-8")
    html_tmp.write_text(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>html,body{{margin:0;padding:0;overflow:hidden;background:#fff;width:{w}px;height:{h}px;}}"
        f"svg{{display:block;width:{w}px;height:{h}px;}}</style></head>"
        f"<body>{svg_text}</body></html>",
        encoding="utf-8",
    )
    url = "file:///" + quote(str(html_tmp.resolve()).replace("\\", "/"), safe="/:")
    cmd = [
        browser,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--window-size={w},{h}",
        f"--screenshot={str(png_path.resolve())}",
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    html_tmp.unlink(missing_ok=True)
    if res.returncode != 0 or not png_path.exists() or png_path.stat().st_size < 5000:
        raise RuntimeError(f"Failed rendering {svg_path.name}: rc={res.returncode}, stderr={res.stderr}")


def render_all_sheets() -> None:
    sheets = ["A-1", "A-2", "A-3", "E-1", "E-2", "L-1", "C-1", "C-2"]
    for code in sheets:
        svg = SVG_DIR / f"{code}.svg"
        png = SHEETS_DIR / f"{code}.png"
        render_svg_to_png(svg, png, scale=1.5)
        print(f"Rendered {png.name} ({png.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render_all_sheets()
