#!/usr/bin/env python
"""Figure: the layout designer's iteration trail for cell `lpf_core`.

A pure re-read of `layout/H12-pdk-cap/iterations/iterations.yaml` -- the machine
audit trail the `layout-designer` agent is required to write ("snapshot every
round -- no exceptions, failed builds included") and the `layout-reviewer` agent
re-hashes before it will review anything. Every entry carries the generator sha,
the GDS sha, the parameter delta, the area, the DRC/LVS/PEX verdicts and the full
post-layout scorecard, so the whole design history is one table -- and this figure
is that table drawn.

Panels:
  (a) cell area per iteration, with the review-round boundaries and the
      identical-GDS runs (assertion-/documentation-only rounds) marked;
  (b) the S1 phase certificate `ph_max` per iteration against its 330 deg floor
      and the optimizer campaign's own 331.10 deg working constraint;
  (c) the S2 cutoff `fc` per iteration inside its 245-255 Hz box;
  (d) the extracted-C element count and the DRC violation count per iteration --
      the physical-verification side of the same trail.

    python3 doc/paper/scripts/fig_iterations.py      # needs PyYAML: the system python3, not the LPF venv

Outputs: doc/paper/figures/iteration_trail.png / .pdf
         doc/paper/figures/data/iteration_trail.csv  (the drawn table, flat)
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml                          # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SRC = REPO / "layout/H12-pdk-cap/iterations/iterations.yaml"
FIGS = REPO / "doc/paper/figures"

PH_FLOOR = 330.0        # S1
PH_WORK = 331.10        # the area campaign's own working constraint
FC_LO, FC_HI = 245.0, 255.0

# Which review round each iteration belongs to. it01 is the round-1 layout of
# record rebuilt as the round-2 baseline; the rounds are named in the notes.
ROUNDS = [("fix round 2", 1, 8), ("fix round 3", 9, 13),
          ("campaign, round 4", 14, 14)]


def main() -> int:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib.pyplot as plt

    its = yaml.safe_load(SRC.read_text())["iterations"]
    n = len(its)
    x = np.arange(1, n + 1)
    ids = [e["id"] for e in its]
    area = np.array([e["area_um2"] for e in its], float)
    sc = [e.get("scorecard") or {} for e in its]

    def col(key):
        return np.array([s.get(key, np.nan) if s else np.nan for s in sc], float)

    ph, fc = col("ph_max_deg"), col("fc_hz")
    nc = np.array([(e.get("pex") or {}).get("n_c", np.nan) for e in its], float)
    ndrc = np.array([(e.get("drc") or {}).get("n", np.nan) for e in its], float)
    sha = [e["gds_sha256"][:12] for e in its]
    same = [k for k in range(1, n) if sha[k] == sha[k - 1]]

    fig = plt.figure(figsize=(S.WIDE, 6.6))
    a1, a2, a3, a4 = fig.subplots(4, 1, sharex=True,
                                  gridspec_kw={"height_ratios": [1.3, 1.0, 0.8, 0.85]})

    def bands(ax, name=False):
        for lab, lo, hi in ROUNDS:
            ax.axvspan(lo - 0.5, hi + 0.5, color="0.5",
                       alpha=0.05 if "campaign" not in lab else 0.13, lw=0)
            if name:
                ax.text((lo + hi) / 2, 0.965, lab, transform=ax.get_xaxis_transform(),
                        ha="center", va="top", fontsize=7, color="0.35")
        for _, lo, _ in ROUNDS[1:]:
            ax.axvline(lo - 0.5, color="0.55", lw=0.8, ls=(0, (4, 3)))

    # ---- (a) area ----------------------------------------------------------
    bands(a1, name=True)
    a1.plot(x, area / 1e3, color="#1f4e9c", lw=1.5, marker="o", ms=4.0)
    a1.scatter(x[same], area[same] / 1e3, s=105, facecolors="none", edgecolors="0.35",
               lw=1.2, zorder=5,
               label="rebuild produced a byte-identical layout\n(assertion- or "
                     "documentation-only round)")
    a1.axhline(area[0] / 1e3, color="0.45", lw=0.8, ls=(0, (1, 2)))
    a1.set_ylabel("cell area  (10$^3$ µm²)")
    a1.margins(y=0.22)
    a1.legend(loc="lower center", fontsize=6.4)
    a1.set_title("(a) area — the fix rounds cost area, the optimizer campaign gives it back")
    S.note(a1, f"first layout {area[0] / 1e3:.1f} k µm²\n"
               f"largest {area.max() / 1e3:.1f} k µm²\n"
               f"delivered {area[-1] / 1e3:.1f} k µm²  "
               f"({100 * (area[-1] - area[0]) / area[0]:+.1f} %)",
           loc="upper left", fontsize=6.4)

    # ---- (b) phase max -----------------------------------------------------
    bands(a2)
    a2.axhspan(PH_FLOOR, 333.0, color=S.OK, alpha=0.07, lw=0)
    a2.plot(x, ph, color="#6a3d9a", lw=1.5, marker="s", ms=3.6)
    a2.axhline(PH_FLOOR, color=S.BAD, lw=1.1, ls=(0, (4, 2)))
    a2.axhline(PH_WORK, color="0.45", lw=0.8, ls=(0, (1, 2)))
    a2.set_ylabel("phase max  (deg)")
    a2.annotate("spec floor 330° (two true biquads)", (0.62, PH_FLOOR + 0.06),
                fontsize=6.6, color=S.BAD, va="bottom")
    a2.annotate(f"optimizer working constraint {PH_WORK:.2f}°", (n + 0.45, PH_WORK - 0.05),
                fontsize=6.6, color="0.35", va="top", ha="right")
    a2.set_title("(b) phase max, measured on the extracted cell each round")

    # ---- (c) cutoff --------------------------------------------------------
    bands(a3)
    a3.axhspan(FC_LO, FC_HI, color=S.OK, alpha=0.08, lw=0)
    a3.plot(x, fc, color="#e08214", lw=1.5, marker="^", ms=3.8)
    a3.set_ylabel("cutoff  (Hz)")
    a3.set_ylim(min(np.nanmin(fc) - 0.35, 247.9), max(np.nanmax(fc) + 0.35, 249.2))
    a3.set_title("(c) cutoff — never left the 245–255 Hz box (shaded band is the box)")

    # ---- (d) physical verification ----------------------------------------
    bands(a4)
    a4.bar(x, nc, width=0.55, color="#1f4e9c", alpha=0.45, edgecolor="#1f4e9c", lw=0.8,
           label="extracted capacitance elements")
    for xi, v in zip(x, nc):
        if np.isfinite(v):
            a4.text(xi, v + 1.6, f"{v:.0f}", ha="center", fontsize=6.2)
    bad = int(np.nansum(ndrc))
    a4.plot(x, ndrc, color=S.BAD, lw=1.1, ls=(0, (4, 2)), marker="s", ms=3.6,
            label=f"design-rule violations ({bad} in the whole trail)")
    a4.set_ylabel("count")
    a4.set_xlabel("build round, in order")
    a4.set_ylim(0, np.nanmax(nc) * 1.62)
    a4.legend(loc="upper right", ncols=2, fontsize=6.5)
    a4.set_title("(d) design-rule, layout-vs-schematic and extraction checks ran "
                 "every round")
    k = int(np.nanargmax(ndrc))
    a4.annotate(f"{int(ndrc[k])} violations, no extraction:\n"
                "the round that failed, snapshotted anyway",
                xy=(x[k], ndrc[k]), xytext=(x[k] - 1.35, np.nanmax(nc) * 1.16),
                fontsize=6.4, color=S.BAD,
                arrowprops=dict(arrowstyle="->", color=S.BAD, lw=0.8))

    a4.set_xticks(x)
    a4.set_xticklabels(ids, fontsize=7)
    for ax in (a1, a2, a3, a4):
        ax.set_xlim(0.4, n + 0.6)

    fig.suptitle("The layout iteration trail, cell lpf_core — "
                 f"{n} snapshotted build rounds, written by the designer agent itself")
    S.save(fig, "iteration_trail")

    # ---- the drawn table, flat, so a reader can check the figure ------------
    (S.FIGS / "data").mkdir(parents=True, exist_ok=True)
    with (S.FIGS / "data" / "iteration_trail.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "area_um2", "ph_max_deg", "fc_hz", "a1000_db", "irn_uv",
                    "thd_db", "drc_n", "lvs_matched", "pex_n_c", "gds_sha256_12"])
        for e, s, h in zip(its, sc, sha):
            w.writerow([e["id"], e["area_um2"], s.get("ph_max_deg"), s.get("fc_hz"),
                        s.get("a1000_db"), s.get("irn_uv"), s.get("thd_db"),
                        (e.get("drc") or {}).get("n"), (e.get("lvs") or {}).get("matched"),
                        (e.get("pex") or {}).get("n_c"), h])
    print("wrote", S.FIGS / "data" / "iteration_trail.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
