"""Re-run the sign-off from the artefacts in this folder. One command, two gates.

This is the script a reviewer runs.  It does not trust anything in `signoff/`
except the sizing JSONs: it regenerates the schematics from them, netlists the
schematics with xschem, simulates those netlists, and compares the result with
what `lab.deck` builds from the same sizing.

**Gate 1 -- drawing == deck.**  Every scorecard metric from the xschem netlist
must match the deck's to 0.05 %.  This is the claim "the schematic IS the design"
and it is the only one worth making: netlist TEXT differs harmlessly (the deck
builder and the netlister order lines differently), so text comparison would fail
on nothing and pass on nothing.

**Gate 2 -- the certified numbers.**  Those same metrics must match the
scorecard recorded in `signoff/scorecard.json`, i.e. the design has not drifted
since sign-off.

    uv run python signoff/verify.py            # both gates
    uv run python signoff/verify.py --regen    # regenerate the .sch first
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from lab import metrics as M          # noqa: E402
from lab import ngspice as ng         # noqa: E402
from lab import thd as T              # noqa: E402
from lab.dut import Design, Dev       # noqa: E402

SCH = HERE / "schematic"
CELLS = {                      # cell -> (sizing json, tb stem, its drawer)
    "022-reuse-final": ("022-reuse-final.json", "lpf_tb_022",
                        "draw_lpf_core_022.py"),
    "021-lv-final":    ("021-lv-final.json",    "lpf_tb_021lv",
                        "draw_xschem.py"),
}
DELIVERABLE = "022-reuse-final"
CARD = HERE / "scorecard.json"
KEYS = ("fc_hz", "dc_db", "ripple_db", "peak_db", "mono_db", "a1000_db",
        "ph_max_deg", "irn_uv", "p_core_nw", "c_total_pf")


def design_of(path: Path) -> Design:
    d = json.loads(path.read_text())
    if isinstance(d, list):
        d = d[0]
    g = d.get("design", d)
    return Design(topology=g["topology"],
                  devs={r: Dev(**v) for r, v in g["devs"].items()},
                  iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
                  lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
                  **{k: v * 1e-12 for k, v in g["caps_pf"].items()})


def netlist(name: str) -> str:
    """xschem .sch -> ngspice deck (native if LPF_XSCHEM is set, else docker)."""
    from lab import xsch
    return xsch.netlist(SCH, name) + "\n.end\n"


def check(cell: str, regen: bool) -> bool:
    """Both gates for one cell. Returns True iff both pass."""
    js, tb, drawer = CELLS[cell]
    d = design_of(HERE / "design" / js)
    if regen:
        # Each drawing has its OWN drawer -- they lay out differently, so
        # regenerating with the wrong one silently replaces a reviewed schematic
        # with a different (still gate-passing) one.
        subprocess.run([sys.executable, str(REPO / "scripts" / drawer)], check=True)

    s_sch = M.score_plots(ng.simulate(netlist(tb), f"so_{cell[:6]}"), d)
    s_dck = M.evaluate(d, f"so_{cell[:6]}_ref", record=False)
    card = (json.loads(CARD.read_text())["scorecard"]
            if CARD.exists() and cell == DELIVERABLE else {})

    print(f"\n=== {cell} ===")
    print(f"{'metric':12s} {'schematic':>12s} {'lab.deck':>12s} {'certified':>12s}   gates")
    ok1 = ok2 = True
    for k in KEYS:
        a_, b_ = s_sch.values.get(k), s_dck.values.get(k)
        c_ = card.get(k)
        if a_ is None or b_ is None:
            continue
        tol = max(1e-6, abs(b_) * 5e-4)
        g1 = abs(a_ - b_) <= tol
        g2 = c_ is None or abs(a_ - c_) <= max(1e-3, abs(c_) * 5e-3)
        ok1 &= g1
        ok2 &= g2
        cs = "          --" if c_ is None else f"{c_:12.4f}"
        print(f"{k:12s} {a_:12.4f} {b_:12.4f} {cs}   "
              f"{'ok' if g1 else 'DIFFERS'}/{'ok' if g2 else 'DRIFTED'}")

    t_sch = T._score(ng.simulate(netlist(f"{tb}_thd"), f"so_{cell[:6]}_thd"),
                     50.0, 87.5e-3, 20, 512, "so")
    t_ref = T.measure(d, tag=f"so_{cell[:6]}_thdref", gate=False)
    g1t = abs(t_sch.thd_db - t_ref.thd_db) <= 0.05
    ok1 &= g1t
    ct = card.get("thd_db")
    print(f"{'thd_db':12s} {t_sch.thd_db:12.3f} {t_ref.thd_db:12.3f} "
          f"{'          --' if ct is None else f'{ct:12.3f}'}   "
          f"{'ok' if g1t else 'DIFFERS'}/-")
    print(f"GATE 1 drawing == deck: {'PASS' if ok1 else 'FAIL'}   "
          f"GATE 2 vs certified card: {'PASS' if ok2 else 'FAIL' if card else 'n/a'}   "
          f"violations: {s_sch.violations or 'none'}")
    return ok1 and (ok2 or not card)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regen", action="store_true",
                    help="regenerate each schematic with its own drawer first")
    ap.add_argument("--cell", choices=sorted(CELLS), default=None,
                    help="check one cell (default: all)")
    a = ap.parse_args()
    cells = [a.cell] if a.cell else list(CELLS)
    ok = all(check(c, a.regen) for c in cells)
    print(f"\nALL GATES: {'PASS' if ok else 'FAIL'}  ({len(cells)} cell(s))")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
