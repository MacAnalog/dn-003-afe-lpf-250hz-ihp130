"""Every sign-off candidate gets its own plots, plus the overlays that compare them.

Per cell, into `signoff/<cell>/`:
    <cell>_bode.png      magnitude + phase, with the S1 boxes drawn
    <cell>_passband.png  the flat band against the +-0.2 dB S3 window
    <cell>_noise.png     input-referred density, S5 band shaded

Across the set, into `signoff/`:
    all_passband.png     every candidate on one flatness axis
    all_noise.png        every candidate's noise density
    tradeoff.png         the three scatter panels a layout choice is actually
                         made on: IRN vs power, IRN vs capacitance, THD vs
                         capacitance, each point labelled

The overlays are the point: a table says `mono_db` is 0.0016, a plot shows that
none of the nine has a bump, which is the claim a reviewer actually wants to
check by eye.

    uv run python scripts/plot_signoff.py [cell ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import matplotlib                                      # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                        # noqa: E402

from lab import plot as P                              # noqa: E402
from lab.dut import Design, Dev                        # noqa: E402

SIGNOFF = REPO / "signoff"
ORDER = ["A-minarea", "B-balanced", "C-lownoise", "D-thdjump", "E-combo",
         "F-minnoise", "G-maxthd", "E1-prev", "H-shipped"]


def design_of(cell: str) -> Design:
    g = json.loads((SIGNOFF / cell / "design.json").read_text())["design"]
    return Design(topology=g["topology"],
                  devs={r: Dev(**v) for r, v in g["devs"].items()},
                  iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
                  lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
                  **{k: v * 1e-12 for k, v in g["caps_pf"].items()})


def card(cell: str) -> dict:
    return json.loads((SIGNOFF / cell / "scorecard.json").read_text())


def per_cell(cell: str) -> None:
    d, c = design_of(cell), card(cell)
    s = c["scorecard"]
    lbl = (f"{cell} — {s['irn_uv']:.2f} µV, {s['p_core_nw']:.2f} nW, "
           f"{s['c_total_pf']:.1f} pF, THD {c['thd_db']:.2f} dB")
    out = SIGNOFF / cell
    P.bode({lbl: d}, out / f"{cell}_bode.png", tag=f"pb_{cell}", dec=100,
           title=f"{cell} — differential AC response")
    P.passband({lbl: d}, out / f"{cell}_passband.png", tag=f"pp_{cell}", fmax=400)
    P.noise({lbl: d}, out / f"{cell}_noise.png", tag=f"pn_{cell}", dec=100,
            title=f"{cell} — input-referred noise, S5 band shaded")
    print(f"  {cell}: 3 plots")


def overlays(cells: list[str]) -> None:
    ds, cs = {}, {}
    for cell in cells:
        c = card(cell)
        s = c["scorecard"]
        ds[f"{cell} ({s['irn_uv']:.1f} µV, {s['p_core_nw']:.1f} nW, "
           f"{s['c_total_pf']:.0f} pF)"] = design_of(cell)
        cs[cell] = c
    P.passband(ds, SIGNOFF / "all_passband.png", tag="allpb", fmax=400,
               title="All sign-off candidates — passband flatness (S3 window drawn)")
    P.noise(ds, SIGNOFF / "all_noise.png", tag="alln", dec=100,
            title="All sign-off candidates — input-referred noise, S5 band shaded")

    # Pareto scatter across every axis pair a layout choice turns on.
    # On each pair the non-dominated set is recomputed for THAT pair -- a cell
    # can be on the front for noise-vs-power and off it for linearity-vs-area,
    # and that is exactly the information a picker needs.
    def val(cell, k):
        c = cs[cell]
        return c["thd_db"] if k == "thd_db" else c["scorecard"][k]

    PAIRS = [("p_core_nw", "irn_uv", "core power (nW)", "IRN (µVrms)",
              "noise vs power", 40.0),
             ("c_total_pf", "irn_uv", "drawn capacitance (pF)", "IRN (µVrms)",
              "noise vs area", 40.0),
             ("p_core_nw", "thd_db", "core power (nW)", "THD (dB)",
              "linearity vs power", -40.0),
             ("c_total_pf", "thd_db", "drawn capacitance (pF)", "THD (dB)",
              "linearity vs area", -40.0),
             ("c_total_pf", "p_core_nw", "drawn capacitance (pF)",
              "core power (nW)", "power vs area", 50.0),
             ("irn_uv", "thd_db", "IRN (µVrms)", "THD (dB)",
              "linearity vs noise", -40.0)]

    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2))
    for ax, (xk, yk, xl, yl, ttl, bound) in zip(axes.ravel(), PAIRS):
        pts = [(val(c, xk), val(c, yk), c) for c in cells]
        # lower is better on every axis used here (THD is negative dB)
        front = [p for p in pts if not any(
            q is not p and q[0] <= p[0] and q[1] <= p[1]
            and (q[0] < p[0] or q[1] < p[1]) for q in pts)]
        fx = [p[0] for p in sorted(front)]
        fy = [p[1] for p in sorted(front)]
        ax.step(fx, fy, where="post", color="#2ca02c", lw=1.4, alpha=0.65,
                zorder=1, label="Pareto front")
        on = {p[2] for p in front}
        for x, y, cell in pts:
            best = cell == "E-combo"
            ax.scatter([x], [y], s=130 if best else (70 if cell in on else 42),
                       color="#d62728" if best else ("#2ca02c" if cell in on else "0.62"),
                       marker="*" if best else ("o" if cell in on else "x"),
                       zorder=3, edgecolor="white" if cell in on or best else None,
                       linewidth=0.8)
            ax.annotate(cell, (x, y), textcoords="offset points", xytext=(6, 4),
                        fontsize=7, fontweight="bold" if best else "normal",
                        color="#d62728" if best else ("0.2" if cell in on else "0.55"))
        ax.axhline(bound, color="#d62728", ls="--", lw=1.0, alpha=0.7)
        P._style(ax, xl, yl)
        ax.set_title(ttl, fontsize=10)
    axes[0][0].legend(fontsize=7.5, loc="upper right")
    fig.suptitle("Sign-off candidates — Pareto fronts (green = non-dominated on "
                 "that pair, grey x = dominated, red star = E-combo, "
                 "dashed = spec bound)", fontsize=11)
    fig.tight_layout()
    P._save(fig, SIGNOFF / "pareto.png")

    # keep the compact 3-panel view too
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
    for ax, (xk, yk, xl, yl, ttl, bound) in zip(axes, PAIRS[:2] + [PAIRS[3]]):
        for cell in cells:
            x, y = val(cell, xk), val(cell, yk)
            best = cell == "E-combo"
            ax.scatter([x], [y], s=110 if best else 55,
                       color="#d62728" if best else "#1f77b4", zorder=3,
                       edgecolor="white", linewidth=0.8)
            ax.annotate(cell, (x, y), textcoords="offset points", xytext=(6, 4),
                        fontsize=7.5, color="#d62728" if best else "0.25",
                        fontweight="bold" if best else "normal")
        ax.axhline(bound, color="#d62728", ls="--", lw=1.1)
        P._style(ax, xl, yl); ax.set_title(ttl, fontsize=10)
    fig.suptitle("Sign-off candidates — the trade a layout pick is made on "
                 "(red = E-combo, recommended)", fontsize=11)
    fig.tight_layout()
    P._save(fig, SIGNOFF / "tradeoff.png")
    print("  overlays: all_passband, all_noise, tradeoff, pareto")


def main() -> int:
    cells = sys.argv[1:] or [c for c in ORDER if (SIGNOFF / c).is_dir()]
    print(f"plotting {len(cells)} candidates")
    for c in cells:
        per_cell(c)
    overlays(cells)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
