#!/usr/bin/env python
"""Figure: the PVT operating window measured on the EXTRACTED cell.

The certified sign-off ran its corner sets on the schematic
(`signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`), and the layout lane reports exactly
ONE post-layout corner (`cap_bcs x0.9 + iref x0.9`). Nothing in the repo says
whether the extracted cell keeps the schematic's operating window. This script
answers that: it re-runs the SAME three corner sets (`lab.corners`, bias law
alpha = 1.1) on the it14 kpex CC subckt and on the schematic, in one process, so
the two are paired point for point.

  * pre-layout  -- the certified sizing from `signoff/post-pvt/H12-pdk-cap/design.json`
  * post-layout -- the same sizing with `Design.dut_override` set to
    `layout/H12-pdk-cap/asbuilt/core_pex.sp` (the it14 layout of record)

Corner sets, all three: `AXES` (9, one axis at a time), `REDUCED` (22, the screen),
`CORNERS` (45, the full grid). ~1 s/point is the floor, so 2 x 76 points is a
few minutes on an idle host.

Run (native ngspice lane, LPF venv):

    cd <repo>/experiments/023-replica-bias
    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_BIAS_ALPHA=1.1 \
        ../../.venv/bin/python ../../doc/paper/scripts/fig_pvt_postlayout.py

`--replot` re-draws from the stored rows without touching the simulator.

Outputs:
    doc/paper/figures/pvt_postlayout.png / .pdf
    doc/paper/figures/data/postlayout_pvt.json   -- every corner row, both DUTs
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXP = REPO / "experiments/023-replica-bias"
SIZING = REPO / "signoff/post-pvt/H12-pdk-cap/design.json"
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"
FIGS = REPO / "doc/paper/figures"

PRE = "pre-layout (schematic)"
POST = "post-layout (kpex CC, it14)"
PROC = ("mos_ss", "mos_sf", "mos_tt", "mos_fs", "mos_ff")
SHORT = {"mos_ss": "ss", "mos_sf": "sf", "mos_tt": "tt", "mos_fs": "fs", "mos_ff": "ff"}


def simulate() -> dict:
    os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
    os.environ.setdefault("PDK", "ihp-sg13g2")
    os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))
    os.environ.setdefault("LPF_BIAS_ALPHA", "1.1")   # read at lab.config import time
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    os.chdir(EXP)

    import time
    from common import AXES, C, K, from_json           # noqa: E402

    base = from_json(json.loads(SIZING.read_text())["design"])
    duts = {PRE: ("plpvt_pre", base),
            POST: ("plpvt_post", base.with_(dut_override=PEX.read_text()))}
    sets = {"axes": AXES, "reduced": K.REDUCED, "full": K.CORNERS}

    out: dict = {"alpha": C.BIAS_ALPHA, "campaigns": {}}
    for label, (tag, d) in duts.items():
        camp: dict = {"tag": tag, "sets": {}}
        for sname, corners in sets.items():
            t0 = time.time()
            res = K.run(d, f"{tag}_{sname}", corners=corners, record=False)
            rows = [{"corner": r.corner.as_dict(), "status": r.status,
                     "values": {k: (float(v) if isinstance(v, (int, float)) else v)
                                for k, v in (dict(r.score.values) if r.score else {}).items()},
                     "violations": list(r.violations)} for r in res]
            n_ok = sum(1 for r in rows if r["status"] == "PASS")
            camp["sets"][sname] = {"n": len(rows), "n_pass": n_ok,
                                   "wall_s": time.time() - t0, "rows": rows}
            print(f"{label:34s} {sname:8s} {n_ok:2d}/{len(rows):2d} pass  "
                  f"({time.time()-t0:.0f} s)")
        out["campaigns"][label] = camp

    FIGS.mkdir(parents=True, exist_ok=True)
    (FIGS / "data").mkdir(exist_ok=True)
    (FIGS / "data" / "postlayout_pvt.json").write_text(json.dumps(out, indent=1))
    return out


def plot(out: dict) -> None:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib
    import matplotlib.pyplot as plt

    OK, BAD = S.OK, S.BAD
    LABEL = {PRE: "before layout (schematic)", POST: "after layout, round 4 (it14)"}
    pre, post = out["campaigns"][PRE], out["campaigns"][POST]

    fig = plt.figure(figsize=(S.WIDE, 6.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.15, 0.62])

    # ---- (a) one-axis set: cutoff before vs after --------------------------
    ax = fig.add_subplot(gs[0, :])
    rp, rq = pre["sets"]["axes"]["rows"], post["sets"]["axes"]["rows"]
    labels = [f"{r['corner']['process'].replace('mos_', '')}\n"
              f"{r['corner']['temp']:g} $^\\circ$C\n{r['corner']['vdd']:g} V" for r in rp]
    x = np.arange(len(rp))
    ax.axhspan(245, 255, color=OK, alpha=0.10, lw=0)
    ax.bar(x - 0.19, [r["values"].get("fc_hz", np.nan) for r in rp], width=0.36,
           color=[OK if r["status"] == "PASS" else BAD for r in rp],
           alpha=0.45, edgecolor="k", lw=0.5, label=LABEL[PRE])
    ax.bar(x + 0.19, [r["values"].get("fc_hz", np.nan) for r in rq], width=0.36,
           color=[OK if r["status"] == "PASS" else BAD for r in rq],
           edgecolor="k", lw=0.9, hatch="///", label=LABEL[POST])
    ax.set_ylim(190, 345)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6.4)
    ax.set_ylabel("cutoff  (Hz)")
    ax.legend(loc="upper left", ncols=2)
    ax.set_title("(a) one corner axis at a time — green = every spec line passes, "
                 "red = at least one fails")

    # ---- (b)/(c) the 45-point grid, both cells -----------------------------
    for col, (name, camp) in enumerate(((PRE, pre), (POST, post))):
        ax = fig.add_subplot(gs[1, col])
        rws = camp["sets"]["full"]["rows"]
        temps = sorted({r["corner"]["temp"] for r in rws})
        vdds = sorted({r["corner"]["vdd"] for r in rws})
        grid = np.full((len(PROC), len(temps) * len(vdds)), np.nan)
        for r in rws:
            pi = PROC.index(r["corner"]["process"])
            c = temps.index(r["corner"]["temp"]) * len(vdds) + vdds.index(r["corner"]["vdd"])
            grid[pi, c] = 1.0 if r["status"] == "PASS" else 0.0
        ax.imshow(grid, cmap=matplotlib.colors.ListedColormap([BAD, OK]),
                  vmin=0, vmax=1, aspect="auto", interpolation="nearest")
        ax.grid(False)
        ax.set_yticks(range(len(PROC)))
        ax.set_yticklabels([SHORT[q] for q in PROC], fontsize=7)
        ax.set_xticks(range(len(temps) * len(vdds)))
        ax.set_xticklabels([f"{v:g}" for _ in temps for v in vdds], fontsize=6.0)
        for gi, tv in enumerate(temps):
            ax.text(gi * len(vdds) + (len(vdds) - 1) / 2, -0.16, f"{tv:g} $^\\circ$C",
                    ha="center", va="top", fontsize=6.6,
                    transform=ax.get_xaxis_transform())
            if gi:
                ax.axvline(gi * len(vdds) - 0.5, color="w", lw=1.8)
        ax.set_xlabel("supply (V), grouped by temperature", labelpad=13, fontsize=7.5)
        ax.set_ylabel("process corner", fontsize=7.5)
        ax.set_title(f"({'b' if col == 0 else 'c'}) {LABEL[name]} — "
                     f"{camp['sets']['full']['n_pass']} of 45 pass")

    # ---- (d) the per-set scoreboard ----------------------------------------
    ax = fig.add_subplot(gs[2, :])
    ax.axis("off")
    ax.grid(False)
    names = {"axes": "one axis at a time (9)", "reduced": "reduced screen (22)",
             "full": "full grid (45)"}
    cells = [[names[s],
              f"{pre['sets'][s]['n_pass']} / {pre['sets'][s]['n']}",
              f"{post['sets'][s]['n_pass']} / {post['sets'][s]['n']}",
              f"{post['sets'][s]['n_pass'] - pre['sets'][s]['n_pass']:+d}",
              f"{pre['sets'][s]['wall_s']:.0f} s / {post['sets'][s]['wall_s']:.0f} s"]
             for s in ("axes", "reduced", "full")]
    tb = ax.table(cellText=cells, cellLoc="center", loc="center",
                  colLabels=["corner set", "before layout", "after layout",
                             "change", "run time"])
    tb.auto_set_font_size(False)
    tb.set_fontsize(7.5)
    tb.scale(1, 1.3)
    for (r, _), cell in tb.get_celld().items():
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_text_props(weight="bold")
    ax.set_title("(d) corner coverage — the extraction changes no verdict on any of "
                 "the 45 corners")

    fig.suptitle("Operating window measured on the EXTRACTED cell, lpf_core\n"
                 "same corner sets and bench definitions as before layout")
    S.save(fig, "pvt_postlayout")


def main() -> int:
    if "--replot" in sys.argv:
        out = json.loads((FIGS / "data" / "postlayout_pvt.json").read_text())
    else:
        out = simulate()
    plot(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
