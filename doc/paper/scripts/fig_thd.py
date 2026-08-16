#!/usr/bin/env python
"""Figure: the S7 distortion evidence for `H12-pdk-cap` (pre-layout, schematic).

A pure re-read of `experiments/023-replica-bias/H12-pdk-cap.prelayout.json`, the
machine twin of the tables in `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`. No
simulation: every number here came out of the frozen coherent-strobed-transient +
DFT path (`lab.deck.tran_thd` -> `lab.thd.measure`) at 175 mVpp differential.

Panels:
  (a) THD and HD3 at nine PVT corners, against the S7 -40 dB line;
  (b) the n=30 mismatch Monte Carlo of THD (`mos_tt_mismatch` + `cap_typ_mismatch`);
  (c) THD vs input frequency at a held 175 mVpp drive -- only the 50 Hz point is
      S7; the 100-200 Hz points are the family property (internal node is a
      bandpass tap) and are informative only.

    python3 doc/paper/scripts/fig_thd.py

Outputs: doc/paper/figures/thd.png / .pdf
"""
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SRC = REPO / "experiments/023-replica-bias/H12-pdk-cap.prelayout.json"
FIGS = REPO / "doc/paper/figures"

LIMIT = -40.0



def label(c: dict) -> str:
    return (f"{c['process'].replace('mos_', '')}\n{c['temp']:g} $^\\circ$C\n"
            f"{c['vdd']:g} V")


def main() -> int:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib.pyplot as plt

    d = json.loads(SRC.read_text())
    corners, mc, prof = d["thd_corners"], d["thd_mc"], d["thd_profile"]

    fig = plt.figure(figsize=(S.WIDE, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.12, 1.0])

    # ---- (a) distortion over the nine corners ------------------------------
    ax = fig.add_subplot(gs[0, :])
    x = np.arange(len(corners))
    thd = [c["thd_db"] for c in corners]
    hd3 = [c["hd3_db"] for c in corners]
    ax.bar(x - 0.19, thd, width=0.36, edgecolor="k", lw=0.5,
           color=[S.OK if v <= LIMIT else S.BAD for v in thd],
           label="total harmonic distortion")
    ax.bar(x + 0.19, hd3, width=0.36, color="#1f4e9c", alpha=0.45, hatch="///",
           edgecolor="#1f4e9c", lw=0.8, label="3rd harmonic")
    ax.axhline(LIMIT, color="k", ls=(0, (4, 2)), lw=1.2)
    ax.annotate("spec limit $-40$ dB", (len(corners) - 0.55, LIMIT + 0.5),
                fontsize=7, ha="right", va="bottom")
    for xi, v in zip(x, thd):
        ax.text(xi - 0.19, v - 0.5, f"{v:.1f}", ha="center", va="top", fontsize=6.2)
    ax.set_xticks(x)
    ax.set_xticklabels([label(c["corner"]) for c in corners], fontsize=6.4)
    ax.set_ylabel("distortion  (dB)")
    ax.set_ylim(min(thd + hd3) - 4.5, LIMIT + 5)
    ax.legend(loc="lower left", ncols=2)
    ax.set_title("(a) distortion at nine corners, 175 mVpp differential at 50 Hz — "
                 f"worst {max(thd):.2f} dB ({abs(max(thd) - LIMIT):.2f} dB of margin)")

    # ---- (b) mismatch Monte Carlo of the distortion -------------------------
    ax = fig.add_subplot(gs[1, 0])
    v = np.array([r["thd_db"] for r in mc["rows"]])
    ax.hist(v, bins=12, color="#1f4e9c", alpha=0.55, edgecolor="#1f4e9c", lw=0.9)
    ax.axvline(v.mean(), color="0.25", lw=1.2)
    for k in (-1, 1):
        ax.axvline(v.mean() + k * v.std(ddof=1), color="0.25", ls=(0, (1, 2)), lw=1.0)
    ax.set_xlabel("total harmonic distortion  (dB)")
    ax.set_ylabel("samples")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.35)
    ax.set_title(f"(b) mismatch Monte Carlo, {mc['n']} draws")
    S.note(ax, f"mean {mc['mean']:.2f} dB, $\\sigma$ {mc['sigma']:.2f} dB\n"
               f"worst {max(v):.2f} dB\n"
               f"{mc['n_pass']} of {mc['n']} meet the $-40$ dB limit",
           loc="upper left", fontsize=6.4)

    # ---- (c) distortion vs input frequency ---------------------------------
    ax = fig.add_subplot(gs[1, 1])
    fin = [q["fin"] for q in prof]
    ax.plot(fin, [q["thd_db"] for q in prof], color="#c0392b", lw=1.5, ls="-",
            marker="o", ms=4.2, label="total harmonic distortion")
    ax.plot(fin, [q["hd3_db"] for q in prof], color="#1f4e9c", lw=1.1,
            ls=(0, (5, 2)), marker="^", ms=4.0, label="3rd harmonic")
    ax.axhline(LIMIT, color="k", ls=(0, (4, 2)), lw=1.1)
    ax.axvline(50.0, color="0.5", lw=0.9, ls=(0, (1, 2)))
    ax.annotate("only 50 Hz is the\nspecified operating point", (56, -32),
                fontsize=6.4, color="0.3", va="center")
    ax.set_xlabel("input frequency (Hz), drive held at 175 mVpp")
    ax.set_ylabel("distortion  (dB)")
    ax.set_ylim(-80, -8)
    ax.legend(loc="lower left", fontsize=6.4)
    ax.set_title("(c) sweep over input frequency")

    fig.suptitle("Distortion evidence before layout, cell lpf_core   ·   "
                 "2nd harmonic sits at $\\approx\\!-100$ dB (bench floor, off scale)")
    S.save(fig, "thd")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
