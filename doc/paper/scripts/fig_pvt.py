#!/usr/bin/env python
"""Figure: the PVT operating window of `H12-pdk-cap` (pre-layout, schematic).

A pure re-read of the committed sign-off artifacts under
`experiments/023-replica-bias/` -- no simulation:

  * `vsw_H12-pdk-cap.json`          -- 9-step supply sweep, 27 C, mos_tt
  * `tsw_H12-pdk-cap_a1p1_1p5.json` -- 9-step temperature sweep, 1.5 V, bias law alpha=1.1
  * `H12-pdk-cap.robust.a1p1.json`  -- one-axis set (9), reduced screen (22), full grid (45)

Panels:
  (a) fc and ph_max vs VDD, with the S2 band and the S1 floor drawn, points
      coloured by whether EVERY spec line passed at that corner;
  (b) the same vs temperature -- the axis on which experiment 023's hypothesis
      was falsified;
  (c) the five process corners at 27 C / 1.5 V: fc span and IRN;
  (d) the full 45-point grid as a pass/fail map (5 process x 3 temperature x
      3 supply), which is what "16/45" in the sign-off actually looks like.

    .venv/bin/python doc/paper/scripts/fig_pvt.py

Outputs: doc/paper/figures/pvt_window.png / .pdf
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib                      # noqa: E402

import _style as S                       # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXP = REPO / "experiments/023-replica-bias"
FIGS = REPO / "doc/paper/figures"

OK, BAD = S.OK, S.BAD
PROC = ("mos_ss", "mos_sf", "mos_tt", "mos_fs", "mos_ff")
SHORT = {"mos_ss": "ss", "mos_sf": "sf", "mos_tt": "tt", "mos_fs": "fs", "mos_ff": "ff"}


def rows(path: Path, key: str | None = None) -> list[dict]:
    d = json.loads(path.read_text())
    return d[key]["rows"] if key else d["rows"]


def _axis(ax, xs, rs, xlabel, title):
    """Cutoff (left) + phase max (right) vs one swept quantity, verdict-coloured."""
    import numpy as np
    fc = [r["values"]["fc_hz"] for r in rs]
    ph = [r["values"]["ph_max_deg"] for r in rs]
    good = [r["status"] == "PASS" for r in rs]

    ax.axhspan(245.0, 255.0, color=OK, alpha=0.10, lw=0)
    ax.plot(xs, fc, color="0.45", lw=1.1, zorder=1)
    ax.scatter(xs, fc, c=[OK if g else BAD for g in good],
               marker="o", s=30, zorder=3, edgecolors="k", linewidths=0.4)
    ax.margins(y=0.16)
    ax.set_ylabel("cutoff  (Hz)")
    ax.set_xlabel(xlabel)
    ax.set_title(title)

    axb = ax.twinx()
    axb.plot(xs, ph, color="#6a3d9a", lw=1.1, ls=(0, (5, 2)), marker="^", ms=3.4)
    axb.axhline(330.0, color="#6a3d9a", lw=0.8, ls=(0, (1, 2)))
    axb.set_ylabel("phase max  (deg)", color="#6a3d9a")
    axb.tick_params(axis="y", labelcolor="#6a3d9a")
    axb.grid(False)
    axb.margins(y=0.16)

    span = [x for x, g in zip(xs, good) if g]
    if span:
        S.note(ax, f"every spec line passes\nfrom {min(span):g} to {max(span):g}\n"
                   "green band = the 245–255 Hz\ncutoff box",
               loc="lower right", fontsize=6.2)
    return axb


def main() -> int:
    import numpy as np
    S.use()
    import matplotlib.pyplot as plt

    vs = rows(EXP / "vsw_H12-pdk-cap.json")
    ts = rows(EXP / "tsw_H12-pdk-cap_a1p1_1p5.json")
    rb = json.loads((EXP / "H12-pdk-cap.robust.a1p1.json").read_text())
    axes9, full = rb["axes"], rb["full"]["rows"]

    fig = plt.figure(figsize=(S.WIDE, 5.4))
    gs = fig.add_gridspec(2, 2)

    _axis(fig.add_subplot(gs[0, 0]), [r["corner"]["vdd"] for r in vs], vs,
          "supply  (V)", "(a) supply sweep at 27 $^\\circ$C, typical process")
    _axis(fig.add_subplot(gs[0, 1]), [r["corner"]["temp"] for r in ts], ts,
          "temperature  ($^\\circ$C)", "(b) temperature sweep at 1.5 V")

    # ---- (c) the five process corners --------------------------------------
    ax = fig.add_subplot(gs[1, 0])
    by = {r["corner"]["process"]: r for r in axes9
          if r["corner"]["temp"] == 27.0 and r["corner"]["vdd"] == 1.5}
    fc = [by[p]["values"]["fc_hz"] for p in PROC]
    irn = [by[p]["values"]["irn_uv"] for p in PROC]
    x = np.arange(len(PROC))
    ax.axhspan(245.0, 255.0, color=OK, alpha=0.10, lw=0)
    ax.bar(x, fc, width=0.55, edgecolor="k", lw=0.5,
           color=[OK if by[p]["status"] == "PASS" else BAD for p in PROC])
    for xi, f_ in enumerate(fc):
        ax.text(xi, f_ + 0.30, f"{f_:.1f}", ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{SHORT[q]}\n{i_:.1f} \u00b5V" for q, i_ in zip(PROC, irn)])
    ax.set_xlim(-0.7, len(PROC) - 0.3)
    ax.set_ylim(243.0, 255.4)
    ax.set_ylabel("cutoff  (Hz)")
    ax.set_xlabel("process corner (n / p skew) and its input-referred noise")
    ax.set_title("(c) process at 27 $^\\circ$C, 1.5 V — 5 of 5 pass, spread 1.02×")

    # ---- (d) the full 45-point grid as a map -------------------------------
    ax = fig.add_subplot(gs[1, 1])
    temps = sorted({r["corner"]["temp"] for r in full})
    vdds = sorted({r["corner"]["vdd"] for r in full})
    grid = np.full((len(PROC), len(temps) * len(vdds)), np.nan)
    for r in full:
        pi = PROC.index(r["corner"]["process"])
        c = temps.index(r["corner"]["temp"]) * len(vdds) + vdds.index(r["corner"]["vdd"])
        grid[pi, c] = 1.0 if r["status"] == "PASS" else 0.0
    ax.imshow(grid, cmap=matplotlib.colors.ListedColormap([BAD, OK]), vmin=0, vmax=1,
              aspect="auto", interpolation="nearest")
    ax.grid(False)
    ax.set_yticks(range(len(PROC)))
    ax.set_yticklabels([SHORT[p] for p in PROC])
    ax.set_xticks(range(len(temps) * len(vdds)))
    ax.set_xticklabels([f"{v:g}" for _ in temps for v in vdds], fontsize=6.2)
    for gi, tv in enumerate(temps):
        ax.text(gi * len(vdds) + (len(vdds) - 1) / 2, -0.15, f"{tv:g} $^\\circ$C",
                ha="center", va="top", fontsize=7,
                transform=ax.get_xaxis_transform())
        if gi:
            ax.axvline(gi * len(vdds) - 0.5, color="w", lw=1.8)
    ax.set_xlabel("supply (V), grouped by temperature\nevery miss contains 1.35 V, $\\leq\\!-20\\,^\\circ$C or $\\geq\\!85\\,^\\circ$C", labelpad=17)
    ax.set_ylabel("process corner")
    n_ok = int(np.nansum(grid))
    ax.set_title(f"(d) full grid — {n_ok} of {grid.size} corners pass every line")

    fig.suptitle("Operating window before layout, cell lpf_core   ·   "
                 "green = every spec line passes, red = at least one fails")
    S.save(fig, "pvt_window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
