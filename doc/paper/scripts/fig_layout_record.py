#!/usr/bin/env python
"""Figure: the layout of record, rendered in the PDK's own layer colours.

Re-renders `layout/H12-pdk-cap/iterations/it14/layout.gds` -- round 4, the
layout of record (sha `1607b803d9..`, 228 093.6 um^2, 0 design-rule violations,
LVS matched, 69 extracted capacitors) -- through KLayout with the PDK layer
properties, and ships it as **PDF as well as PNG**, in two colour renderings:

  `layout_record`            the render as the PDK colours it: light traces on a
                             dark ground;
  `layout_record_inverted`   the same raster, colour-inverted -- a white ground
                             for a printed page, which is what a paper figure
                             usually wants.

Two deliberate differences from `figures/static/layout_lpf_core.png`, the
1600x1200 viewer capture this supersedes. The frame is the cell's own bounding
box plus a 2 % border, not a 4:3 letterbox, so none of the figure is spent on
background; and the **viewport grid and the automatic labels are off**. Those
labels are the viewer's, not the design's -- device names and capacitor values
that overlap each other and clip at the frame edge -- and the pin names they
also carry are better set in the caption than rendered at 4 pt. The labelled
capture stays where it is for anyone who wants it.

The GDS is the only input; nothing is simulated and no geometry is recomputed,
so the figure cannot drift from the delivered cell. Both renderings come from
one KLayout pass, so they are the same pixels.

    PDK_ROOT=~/local/pdks .venv/bin/python doc/paper/scripts/fig_layout_record.py

Outputs: doc/paper/figures/layout_record{,_inverted}.png / .pdf
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg   # noqa: E402
import matplotlib.pyplot as plt    # noqa: E402
import numpy as np                 # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FIGS = HERE.parent / "figures"

GDS = REPO / "layout/H12-pdk-cap/iterations/it14/layout.gds"
PDK = "ihp-sg13g2"

#: Render scale. The cell is 432.02 x 527.97 um, so 6 px/um puts ~2.7 kpx across
#: it -- ~780 dpi once the PDF is placed at IEEE single-column width.
PX_PER_UM = 6.0
#: Background border, as a fraction of the larger cell dimension.
MARGIN_FRAC = 0.02
#: 3 is KLayout's maximum; it renders each output pixel from 3x3 virtual ones,
#: which is what keeps a 0.16 um metal edge from aliasing at this scale.
OVERSAMPLING = 3
#: 600 dpi -> a 4.53 x 5.49 in page at this scale.
DPI = 600


def pdk_lyp(pdk: str = PDK) -> Path | None:
    """The PDK's KLayout layer-properties file, from `$PDK_ROOT`."""
    root = Path(os.environ.get("PDK_ROOT", os.path.expanduser("~/local/pdks")))
    hits = sorted((root / pdk / "libs.tech" / "klayout" / "tech").glob("*.lyp"))
    return hits[0] if hits else None


def render(gds: Path, png: Path) -> tuple[int, int]:
    """Headless KLayout render with the PDK layer colours, framed on the cell."""
    import klayout.db as kdb
    import klayout.lay as klay

    lyp = pdk_lyp()
    if lyp is None:
        raise SystemExit(f"no .lyp under $PDK_ROOT for {PDK} -- is PDK_ROOT set?")

    ly = kdb.Layout()
    ly.read(str(gds))
    b = ly.top_cell().dbbox()
    m = MARGIN_FRAC * max(b.width(), b.height())
    box = kdb.DBox(b.left - m, b.bottom - m, b.right + m, b.top + m)
    size = (round(box.width() * PX_PER_UM), round(box.height() * PX_PER_UM))

    lv = klay.LayoutView()
    lv.load_layout(str(gds), 0)          # type: ignore[call-overload]
    lv.load_layer_props(str(lyp))
    lv.max_hier_levels = 20
    lv.set_config("grid-visible", "false")
    lv.set_config("text-visible", "false")
    lv.zoom_fit()
    # width, height, linewidth=0, oversampling, resolution=0, target box
    lv.save_image_with_options(str(png), *size, 0, OVERSAMPLING, 0, box, False)
    return size


def to_pdf(img: np.ndarray, pdf: Path) -> None:
    """Wrap a raster as a full-bleed PDF page, losslessly and unresampled.

    matplotlib's PDF backend Flate-encodes the array; `interpolation="none"`
    stops it resampling on the way in. (An image library's own PDF writer
    typically JPEG-encodes RGB, which smears every one-pixel layer edge.)

    `CreationDate: None` drops the timestamp the backend would otherwise stamp
    into the file, so re-running this script on an unchanged GDS reproduces both
    PDFs byte for byte instead of showing up as a diff.
    """
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.imshow(np.clip(img, 0.0, 1.0), interpolation="none")
    ax.axis("off")
    fig.savefig(pdf, dpi=DPI, pad_inches=0, metadata={"CreationDate": None})
    plt.close(fig)


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    native = FIGS / "layout_record.png"
    w, h = render(GDS, native)
    print(f"rendered {w} x {h} px at {PX_PER_UM:g} px/um (oversampling {OVERSAMPLING}) "
          f"from {GDS.relative_to(REPO)}")
    print(f"  page {w / DPI:.2f} x {h / DPI:.2f} in at {DPI} dpi")

    img = mpimg.imread(native)[:, :, :3]
    inverted = 1.0 - img
    plt.imsave(FIGS / "layout_record_inverted.png", inverted)
    for arr, name in ((img, "layout_record"), (inverted, "layout_record_inverted")):
        to_pdf(arr, FIGS / f"{name}.pdf")
    for f in ("layout_record.png", "layout_record.pdf",
              "layout_record_inverted.png", "layout_record_inverted.pdf"):
        print(f"  {f:34s} {(FIGS / f).stat().st_size / 1e6:5.2f} MB")


if __name__ == "__main__":
    main()
