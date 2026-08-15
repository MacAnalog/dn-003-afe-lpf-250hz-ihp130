"""Render xschem schematics to PNG on a host whose xschem has no cairo.

The conda-forge xschem exports SVG with complete geometry but a broken
document header: everything is scaled into the 1x1 Tk window that never maps
under Xvfb (`width="1" height="1"`, no viewBox), and the CSS stroke-width is
left in screen pixels -- rasterize that as-is and you get solid-colour blobs
(doc/journal/xschem-no-cairo-silent-export.md).  Both defects are repairable
after the fact, which is what this script does:

    1. export SVG headlessly:  Xvfb + `xschem -q --plotfile f.svg --svg f.sch`
    2. repair the header:      real bounding box (path data + text anchors)
                               becomes the viewBox; width scales to PX wide
    3. rescale strokes:        CSS stroke-width -> ~1.7 px at target width
    4. rasterize:              cairosvg (rsvg-convert drops the text elements
                               at these sub-unit font sizes; cairosvg keeps
                               them)

    uv run python scripts/render_sch.py <sheet.sch> [...] [--px 2400]

Writes `<sheet>.png` beside each input.  Requires: xschem, Xvfb, and a python
with cairosvg (the ai_env conda python is the default; override with
LPF_CAIROSVG_PY).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CAIROSVG_PY = os.environ.get(
    "LPF_CAIROSVG_PY", "/home/noorizad/miniconda3/envs/ai_env/bin/python")

_NUM = r"-?\d+\.?\d*(?:e-?\d+)?"


def _rcfile(schdir: Path, work: Path) -> Path:
    """A native rcfile for this schematic dir (same recipe as lab.xsch)."""
    xschem = os.environ.get("LPF_XSCHEM") or "xschem"
    prefix = Path(subprocess.run(["which", xschem], capture_output=True,
                                 text=True, check=True).stdout.strip()).parents[1]
    pdk = Path(os.environ.get("PDK_ROOT", "/opt/pdk")) / "ihp-sg13g2" / "libs.tech" / "xschem"
    rc = work / "xschemrc_render"
    rc.write_text(
        f"set XSCHEM_LIBRARY_PATH {prefix}/share/xschem/xschem_library\n"
        f"append XSCHEM_LIBRARY_PATH :{pdk}\n"
        f"append XSCHEM_LIBRARY_PATH :{schdir}\n"
        f"set netlist_dir {schdir}\n"
        # the PDK live annotator's text tcleval-s display_fet_params; source
        # the PDK menu tcl so an annotated sheet exports cleanly (values
        # render as NaN without a loaded raw, which is correct for a bare
        # render -- the committed numbers are the baked text blocks).
        f"catch {{ source {pdk}/xschem-menu }}\n")
    return rc


def _export_svg(sch: Path, work: Path, display: str) -> str:
    svg = work / (sch.stem + ".svg")
    svg.unlink(missing_ok=True)
    xschem = os.environ.get("LPF_XSCHEM") or "xschem"
    subprocess.run(
        [xschem, "--rcfile", str(_rcfile(sch.parent, work)), "-q",
         "--plotfile", str(svg), "--svg", str(sch)],
        env={**os.environ, "DISPLAY": display},
        check=True, capture_output=True, text=True)
    if not svg.exists() or svg.stat().st_size < 500:
        raise RuntimeError(f"{sch}: svg export produced nothing -- "
                           "cairo-less xschem needs a live X display (Xvfb)")
    return svg.read_text()


def _repair(svg: str, px: int) -> str:
    pts = []
    for d in re.findall(r'\sd="([^"]+)"', svg):
        v = [float(x) for x in re.findall(_NUM, d)]
        pts += list(zip(v[::2], v[1::2]))
    if not pts:
        raise RuntimeError("no path geometry in svg")
    # Text anchors extend the bbox (the title block sits above the top wire);
    # keep only plausible ones -- rotation matrices would poison the box.
    for tx, ty in re.findall(rf'translate\(({_NUM}),\s*({_NUM})\)', svg):
        x, y = float(tx), float(ty)
        if -0.5 <= x <= 1.5 and -0.5 <= y <= 1.5:
            pts.append((x, y))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    mx, my = (x1 - x0) * 0.02, (y1 - y0) * 0.03
    x0, y0 = x0 - mx, y0 - my
    w, h = (x1 - x0) + 2 * mx, (y1 - y0) + 2 * my
    hpx = max(1, int(px * h / w))
    svg = svg.replace(
        'width="1" height="1"',
        f'width="{px}" height="{hpx}" viewBox="{x0:.6f} {y0:.6f} {w:.6f} {h:.6f}"', 1)
    svg = re.sub(r'stroke-width:\s*[\d.]+;',
                 f'stroke-width: {w / px * 1.7:.6f};', svg)
    # Render timestamp, bottom-right corner of the computed viewport: every
    # committed picture names the moment it was produced.
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime(
        "rendered %Y-%m-%d %H:%M UTC -- scripts/render_sch.py")
    stamp = (f'<text fill="#999999" font-size="{w * 0.007:.6f}" '
             f'text-anchor="end" transform="translate({x0 + w * 0.995:.6f}, '
             f'{y0 + h * 0.99:.6f})">{ts}</text>')
    return svg.replace("</svg>", stamp + "\n</svg>")


def render(sheets: list[Path], px: int) -> None:
    with tempfile.TemporaryDirectory(prefix="lpf_render_") as td:
        work = Path(td)
        xvfb = subprocess.Popen(
            ["Xvfb", ":93", "-screen", "0", "1600x1200x24"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(1.0)
            for sch in sheets:
                sch = sch.resolve()
                fixed = work / (sch.stem + "_fixed.svg")
                fixed.write_text(_repair(_export_svg(sch, work, ":93"), px))
                out = sch.with_suffix(".png")
                subprocess.run(
                    [CAIROSVG_PY, "-c",
                     "import cairosvg,sys;"
                     "cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2])",
                     str(fixed), str(out)],
                    check=True, capture_output=True, text=True)
                print(f"rendered {out}")
        finally:
            xvfb.terminate()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheets", nargs="+", type=Path)
    ap.add_argument("--px", type=int, default=2400, help="output width in px")
    a = ap.parse_args()
    render(a.sheets, a.px)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
