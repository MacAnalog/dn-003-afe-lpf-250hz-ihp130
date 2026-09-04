#!/usr/bin/env python
"""Figure: the layout of record on a white ground, with the capacitors and the
two biquad stages labelled -- the companion of `fig_layout_record.py` for the
prose that walks a reader through the floorplan.

Input is `figures/layout_record_inverted.png`, the colour-inverted KLayout
render `fig_layout_record.py` produces (run that first); this script adds
annotation only, so the layout pixels are the same ones the unlabelled paper
figure shows. Positions come from `iterations/it14/gen.py` -- the cap banks are
the `CAPS` table placed by `cap_array` -- and were cross-checked against the
instance bounding boxes of the GDS (`klayout.db`), so a label sits on the
array it names; nothing is recomputed from geometry at run time.

What is labelled, and why these names:

* every MIM array, by its **role** (the schematic instances -- `xc13`, `xc17`,
  `xc19`, `xc1`, `xc10`, `xc12` in `decks/reference/lpf_core.sp` and the device
  table of `doc/design-reference.md` section 2 -- stay in the `CAPS` comments,
  not on the figure)
  (`C1` = internal node to that half's output, `C2` = differential across the
  biquad outputs; subscript A/B = the biquad; P/N = the half). `xc19` is drawn
  as two mirror halves, one each side of the axis, so it carries two labels.
* the two stages: **biquad #1** (A, `vinp/vinn` -> `vout_1/vout_2`) is bank A
  plus the device island below the grounded shield band; **biquad #2** (B,
  -> `voutp/voutn`) is the island above the band plus bank B. The outlines
  follow the islands' and banks' extents (gen.py PLAN section 1), not any
  drawn shape; the dashed box is a reading aid, not a layer.

    PDK_ROOT=~/local/pdks .venv/bin/python doc/paper/scripts/fig_layout_record_labelled.py

Two variants: `layout_record_labelled` (no scale bar) and
`layout_record_labelled_scale`, which adds a white strip under the layout with a
100 um bar (6 px/um, so it is exactly 600 px of the raster).

Outputs: doc/paper/figures/layout_record_labelled{,_scale}.png / .pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
# IEEE (Times-compatible) text and math: STIX is the Times-metric family matplotlib ships.
matplotlib.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix"})
import matplotlib.image as mpimg      # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt       # noqa: E402
import numpy as np                    # noqa: E402

HERE = Path(__file__).resolve().parent
FIGS = HERE.parent / "figures"
SRC = FIGS / "layout_record_inverted.png"

# --- the raster's frame, from fig_layout_record.py (cell bbox + 2 % border) ---
CELL = (-216.01, -8.83, 216.01, 519.14)     # um: left, bottom, right, top
MARGIN_FRAC, PX_PER_UM, DPI = 0.02, 6.0, 600

# --- capacitor arrays: centre (um), label. From gen.py CAPS + the GDS bboxes ---
CAPS = [
    # bank A (bottom): xc19 = c2_a split in two mirror halves, xc13/xc17 = c1_a
    ((-107.0, 51.0), r"$C_{2A}$ (½)"),
    ((107.0, 51.0), r"$C_{2A}$ (½)"),
    ((-25.0, 84.0), r"$C_{1A,P}$"),   # stacked: the two arrays straddle the axis
    ((25.0, 36.0), r"$C_{1A,N}$"),
    # bank B (top): xc1/xc10 = c1_b (16 units each), xc12 = c2_b (7 units)
    ((-108.5, 352.0), r"$C_{1B,P}$"),
    ((108.5, 352.0), r"$C_{1B,N}$"),
    ((0.0, 489.0), r"$C_{2B}$"),
]

# --- stage outlines (um): bank + device island of each biquad ---
STAGES = [
    dict(box=(-214.0, -6.0, 214.0, 188.0), name="Biquad #1 (A)",
         sub=r"$v_{in,p}/v_{in,n} \rightarrow v_{out1}/v_{out2}$", color="#00695c"),
    dict(box=(-214.0, 194.0, 214.0, 517.0), name="Biquad #2 (B)",
         sub=r"$v_{out1}/v_{out2} \rightarrow v_{out,p}/v_{out,n}$", color="#6a1b9a"),
]

PAD_IN = 0.75   # white column added on the left for the stage brackets
PAD_BOTTOM_IN = 0.32   # white strip under the layout for the scale bar
SCALE_UM = 100.0       # scale-bar length; 6 px/um makes it exactly 600 px


def um_to_px(x: float, y: float) -> tuple[float, float]:
    """Layout coordinates -> pixel coordinates of the inverted raster."""
    l, b, r, t = CELL
    m = MARGIN_FRAC * max(r - l, t - b)
    return (x - (l - m)) * PX_PER_UM, ((t + m) - y) * PX_PER_UM


def render(scale_bar: bool) -> None:
    img = mpimg.imread(SRC)[:, :, :3]
    h, w = img.shape[:2]
    pad = int(PAD_IN * DPI)
    padb = int(PAD_BOTTOM_IN * DPI) if scale_bar else 0
    canvas = np.ones((h + padb, w + pad, 3), dtype=img.dtype)
    canvas[:h, pad:, :] = img

    fig = plt.figure(figsize=((w + pad) / DPI, (h + padb) / DPI), dpi=DPI)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.imshow(canvas, interpolation="none")
    ax.set_xlim(0, w + pad)
    ax.set_ylim(h + padb, 0)
    ax.axis("off")

    if scale_bar:
        # scale bar in the bottom strip, left-aligned with the cell's left edge
        x0, _ = um_to_px(CELL[0], 0.0)
        xs, ys = x0 + pad, h + padb * 0.45
        bar = SCALE_UM * PX_PER_UM
        ax.plot([xs, xs + bar], [ys, ys], color="black", lw=2.2, solid_capstyle="butt", zorder=6)
        for xx in (xs, xs + bar):
            ax.plot([xx, xx], [ys - padb * 0.10, ys + padb * 0.10], color="black", lw=1.2, zorder=6)
        ax.text(xs + bar / 2, ys - padb * 0.16, f"{SCALE_UM:g} µm", ha="center", va="bottom",
                fontsize=9, color="black", zorder=6)

    box_kw = dict(boxstyle="round,pad=0.35,rounding_size=0.6", fc="white", alpha=0.96, lw=0.6)
    for (x, y), text in CAPS:
        px, py = um_to_px(x, y)
        ax.text(px + pad, py, text, ha="center", va="center", fontsize=9, color="black",
                bbox=dict(ec="#444444", **box_kw), zorder=5)

    for s in STAGES:
        l, b, r, t = s["box"]
        (x0, y0), (x1, y1) = um_to_px(l, t), um_to_px(r, b)
        ax.add_patch(mpatches.Rectangle((x0 + pad, y0), x1 - x0, y1 - y0, fill=False,
                                        ec=s["color"], lw=1.4, ls=(0, (6, 3)), zorder=4))
        # bracket + rotated label in the white column
        xb = pad * 0.62
        ax.plot([xb, xb], [y0, y1], color=s["color"], lw=1.2, zorder=4)
        for yy in (y0, y1):
            ax.plot([xb, xb + pad * 0.12], [yy, yy], color=s["color"], lw=1.2, zorder=4)
        ax.text(pad * 0.40, (y0 + y1) / 2, s["name"], rotation=90, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color=s["color"])
        ax.text(pad * 0.22, (y0 + y1) / 2, s["sub"], rotation=90, ha="center", va="center",
                fontsize=7.5, color=s["color"])

    stem = "layout_record_labelled" + ("_scale" if scale_bar else "")
    for ext in ("png", "pdf"):
        out = FIGS / f"{stem}.{ext}"
        fig.savefig(out, dpi=DPI, pad_inches=0, metadata={"CreationDate": None} if ext == "pdf" else None)
        print(f"  {out.name:32s} {out.stat().st_size / 1e6:5.2f} MB")
    plt.close(fig)


def main() -> None:
    render(scale_bar=False)   # layout_record_labelled: the figure as merged
    render(scale_bar=True)    # layout_record_labelled_scale: + the 100 um bar


if __name__ == "__main__":
    main()
