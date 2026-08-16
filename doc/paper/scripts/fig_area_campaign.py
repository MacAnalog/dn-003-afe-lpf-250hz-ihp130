#!/usr/bin/env python
"""Figure: the area-optimization campaigns over the layout generator's knobs.

Reads `layout/H12-pdk-cap/opt/results/campaign_{A,B}_trials.jsonl` (600 trials, one
JSON object per trial, written by `layout/H12-pdk-cap/optimize_area.py`) and
`opt/results/summary.json`, and draws:

  (a) cell area vs the binding constraint C(`net2`) for every trial that got far
      enough to be extracted, coloured by outcome, with the constraint lines and
      the three reference points (round-3 layout of record, A-best, and
      `A-best + bias_dummy_rows=0` -- the point adopted as `it14` / round 4) marked;
  (b) the outcome histogram per campaign -- what the 600 trials actually spent
      themselves on (build / DRC / LVS / constraint failures vs feasible);
  (c) best-feasible-area vs trial index (the convergence trace of each campaign).

No simulation: this is a pure re-read of committed campaign artifacts.

    python3 doc/paper/scripts/fig_area_campaign.py

Outputs: doc/paper/figures/area_campaign.png / .pdf
"""
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RES = REPO / "layout/H12-pdk-cap/opt/results"
FIGS = REPO / "doc/paper/figures"

R3_AREA = 247136.8848          # the round-3 layout of record (it13)
NET2_LIMIT = 32.4              # the campaign's own C(net2) constraint, fF
PH_LIMIT = 331.10              # the campaign's own ph_max constraint, deg

COLOR = {"ok": "#1b7837", "constraint_fail": "#e08214", "lvs_fail": "#c0392b",
         "drc_fail": "#6a3d9a", "build_fail": "#7f7f7f"}
MARK = {"ok": "o", "constraint_fail": "^", "lvs_fail": "s", "drc_fail": "v",
        "build_fail": "x"}
NICE = {"ok": "feasible", "constraint_fail": "missed a budget",
        "lvs_fail": "layout \u2260 schematic", "drc_fail": "design-rule violation",
        "build_fail": "generator refused"}
ORDER = ("ok", "constraint_fail", "drc_fail", "lvs_fail", "build_fail")


def load(camp: str) -> list[dict]:
    return [json.loads(ln) for ln in (RES / f"campaign_{camp}_trials.jsonl").read_text().splitlines() if ln.strip()]


def main() -> int:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib.pyplot as plt

    A, B = load("A"), load("B")
    summ = json.loads((RES / "summary.json").read_text())

    fig = plt.figure(figsize=(S.WIDE, 7.0))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.30, 0.92, 0.98])

    # ---- (a) area vs the binding constraint --------------------------------
    ax = fig.add_subplot(gs[0, :])
    for st in ORDER:
        xs, ys = [], []
        for r in A + B:
            b = r.get("budget")
            if not b or r["status"] != st:
                continue
            xs.append(b["net2"]); ys.append(r["area_um2"] / 1e3)
        if xs:
            ax.scatter(xs, ys, s=13, alpha=0.6, c=COLOR[st], marker=MARK[st],
                       edgecolors="none", label=f"{NICE[st]} ({len(xs)})")
    ax.axvline(NET2_LIMIT, color="0.35", lw=1.0, ls=(0, (4, 2)))
    ax.axhline(R3_AREA / 1e3, color="0.35", lw=1.0, ls=(0, (1, 2)))
    ax.set_ylim(220, 425)
    ax.annotate("budget limit on net2, 32.4 fF", (NET2_LIMIT + 0.1, 224),
                ha="left", va="bottom", fontsize=6.6, color="0.3")
    ax.annotate("round-3 layout of record, 247.1 k µm²", (36.9, R3_AREA / 1e3 + 3),
                fontsize=6.6, color="0.3", ha="right")
    for key, marker, lab in (("A", "*", "best of campaign A"),
                             ("Abest_dummy0", "D", "adopted as round 4 (it14)")):
        rec = summ[key]["best"] if "best" in summ[key] else summ[key]
        ax.scatter([rec["budget"]["net2"]], [rec["area_um2"] / 1e3], marker=marker,
                   s=180 if marker == "*" else 55, c="k", zorder=6, label=lab)
    d0 = summ["dummy0"]
    ax.scatter([d0["budget"]["net2"]], [d0["area_um2"] / 1e3], marker="s", s=45,
               facecolors="none", edgecolors="k", zorder=6,
               label="defaults, bias dummy rows removed")
    ax.set_xlabel("capacitance of net2 to ac ground (fF) — the binding constraint")
    ax.set_ylabel("cell area  (10$^3$ µm²)")
    ax.legend(loc="upper left", ncols=2, fontsize=6.4, markerscale=0.55)
    ax.set_title("(a) 600 optimizer trials — area is bounded by the internal-node "
                 "capacitance")

    # ---- (b) outcome histogram ---------------------------------------------
    ax2 = fig.add_subplot(gs[1, 0])
    w = 0.38
    for k, (name, trials) in enumerate((("A", A), ("B", B))):
        counts = [sum(1 for r in trials if r["status"] == st) for st in ORDER]
        ax2.bar(np.arange(len(ORDER)) + (k - 0.5) * w, counts, width=w,
                color=[COLOR[s] for s in ORDER], alpha=1.0 - 0.42 * k,
                edgecolor="k", lw=0.5, hatch=None if k == 0 else "///")
        for xx, c in zip(np.arange(len(ORDER)) + (k - 0.5) * w, counts):
            ax2.text(xx, c + 5, str(c), ha="center", fontsize=6.0)
    ax2.set_xticks(range(len(ORDER)))
    ax2.set_xticklabels([NICE[s] for s in ORDER], rotation=28, ha="right", fontsize=6.6)
    ax2.set_ylabel("trials")
    ax2.set_ylim(0, 235)
    ax2.set_title("(b) where the trials went")
    S.note(ax2, "left bar campaign A\nright bar campaign B (hatched)",
           loc="upper left", fontsize=6.2)

    # ---- (c) convergence ----------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 1])
    for name, trials, sty in (("A", A, dict(color="#1f4e9c", ls="-")),
                              ("B", B, dict(color="#c0392b", ls=(0, (5, 2))))):
        best, trace = np.inf, []
        for r in sorted(trials, key=lambda r: r["trial"]):
            if r["status"] == "ok":
                best = min(best, r["area_um2"])
            trace.append(best / 1e3 if np.isfinite(best) else np.nan)
        ax3.plot(range(len(trace)), trace, lw=1.5, label=f"campaign {name}", **sty)
    ax3.axhline(R3_AREA / 1e3, color="0.4", lw=0.9, ls=(0, (1, 2)))
    ax3.axhline(summ["Abest_dummy0"]["area_um2"] / 1e3, color="k", lw=0.9, ls=(0, (4, 2)))
    ax3.set_ylim(226.5, 249.5)
    ax3.annotate("adopted as round 4", (8, summ["Abest_dummy0"]["area_um2"] / 1e3 + 0.4),
                 fontsize=6.6, ha="left", va="bottom")
    ax3.set_xlabel("trial")
    ax3.set_ylabel("best feasible area (10$^3$ µm²)")
    ax3.set_title("(c) convergence")
    ax3.legend(loc="center right")

    # ---- (d) the cost of the dummy-row decision -----------------------------
    ax4 = fig.add_subplot(gs[2, :])
    rows = [
        ("round-3 layout of record\n(bias dummy rows kept, stock knobs)",
         R3_AREA, 331.1595, "0.55"),
        ("best of campaign A\n(25 numeric knobs, dummy rows kept)",
         summ["A"]["best"]["area_um2"], summ["A"]["best"]["ph_max"], "#1f4e9c"),
        ("best of campaign B\n(dummy rows also searchable)",
         summ["B"]["best"]["area_um2"], summ["B"]["best"]["ph_max"], "#c0392b"),
        ("stock knobs, dummy rows removed",
         summ["dummy0"]["area_um2"], summ["dummy0"]["ph_max"], "#e08214"),
        ("campaign-A knobs + dummy rows removed\n(adopted as round 4)",
         summ["Abest_dummy0"]["area_um2"], summ["Abest_dummy0"]["ph_max"], "#1b7837"),
    ]
    y = np.arange(len(rows))[::-1]
    ax4.barh(y, [r[1] / 1e3 for r in rows], color=[r[3] for r in rows], height=0.55,
             edgecolor="k", lw=0.5)
    for yy, r in zip(y, rows):
        ax4.text(r[1] / 1e3 + 2.5, yy,
                 f"{r[1] / 1e3:.1f} k µm²   ({100 * (r[1] - R3_AREA) / R3_AREA:+.1f} %)"
                 f"   phase max {r[2]:.3f}$^\\circ$", va="center", fontsize=6.5)
    ax4.set_yticks(y)
    ax4.set_yticklabels([r[0] for r in rows], fontsize=6.6)
    ax4.set_xlim(0, 420)
    ax4.set_xlabel("cell area  (10$^3$ µm²)")
    ax4.set_title("(d) the knobs alone do not reach the white space")

    fig.suptitle("Area optimization over the layout generator's 33 knobs, cell lpf_core")
    S.save(fig, "area_campaign")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
