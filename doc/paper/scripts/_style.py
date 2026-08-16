"""Shared paper-figure style for `doc/paper/scripts/*`.

One place for the things every figure in the pack has to get right:

* **Paper size.** `COL` = 3.5 in (IEEE single column), `WIDE` = 7.2 in (double
  column). A figure with three or more panels uses `WIDE`; everything else `COL`.
* **Type size.** 8 pt body, 9 pt axes titles — the range a two-column IEEE page
  can still read after the figure is scaled to the column width.
* **`constrained_layout`.** Always on, so a `suptitle` reserves its own band and
  can never land on a panel title, and long tick labels push the axes in rather
  than off the canvas.
* **Grayscale survival.** `CYCLE` pairs every colour with its own dash pattern
  and marker, so the curves stay distinguishable when the paper is printed in
  black and white. `GREY`/`OK`/`BAD` are the only other colours used.

`save(fig, name)` writes `<figures>/<name>.png` and `.pdf` at 200 dpi and prints
the pixel size, so an unreadable figure can be spotted from the log.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

FIGS = Path(__file__).resolve().parents[1] / "figures"

COL = 3.5          # IEEE single column, inches
WIDE = 7.2         # IEEE double column, inches
DPI = 200

OK, BAD, GREY = "#1b7837", "#c0392b", "#5d6d7e"

#: colour + dash + marker per series, so the figure survives a grayscale print
CYCLE = (
    dict(color="#1f4e9c", ls="-", marker="o", ms=3.2),
    dict(color="#c0392b", ls="--", marker="s", ms=3.0),
    dict(color="#e08214", ls=":", marker="^", ms=3.4),
    dict(color="#6a3d9a", ls="-.", marker="D", ms=2.8),
)


def use() -> None:
    """Apply the pack's rcParams. Call once, before creating any figure."""
    plt.rcParams.update({
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.045,
        "figure.constrained_layout.w_pad": 0.045,
        "figure.constrained_layout.hspace": 0.06,
        "figure.constrained_layout.wspace": 0.06,
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.titlelocation": "left",
        "axes.labelsize": 8,
        "axes.linewidth": 0.7,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.fontsize": 7,
        "legend.framealpha": 0.92,
        "legend.borderpad": 0.35,
        "legend.labelspacing": 0.32,
        "legend.handlelength": 2.4,
        "lines.linewidth": 1.4,
        "figure.titlesize": 9.5,
    })


def note(ax, text, loc="upper left", fontsize=6.8, **kw):
    """A small boxed text panel — the overlap-free way to carry numbers."""
    from matplotlib.offsetbox import AnchoredText
    at = AnchoredText(text, loc=loc, prop=dict(size=fontsize, family="DejaVu Sans"),
                      frameon=True, borderpad=0.3, pad=0.28, **kw)
    at.patch.set(boxstyle="round,pad=0.28", facecolor="white", edgecolor="0.75",
                 alpha=0.93, linewidth=0.6)
    at.zorder = 20
    ax.add_artist(at)
    return at


def save(fig, name: str) -> None:
    """Write PNG + PDF into `doc/paper/figures/` and report the pixel size."""
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"{name}.{ext}")
    w, h = fig.get_size_inches()
    print(f"wrote {FIGS / (name + '.png')}  ({round(w * DPI)}x{round(h * DPI)} px, "
          f"{w:.2f}x{h:.2f} in)")
