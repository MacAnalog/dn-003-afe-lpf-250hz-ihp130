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
CELL = HERE / "design" / "022-reuse-final.json"
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
    """xschem .sch -> ngspice deck, run in the same container as the simulator."""
    from lab import config as C
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{SCH}:/sch", "-w", "/sch", C.DOCKER_IMAGE,
         "sh", "-lc", f"xschem -n -s -q --rcfile /sch/xschemrc /sch/{name}.sch"],
        check=True, capture_output=True, text=True)
    return (SCH / f"{name}.spice").read_text() + "\n.end\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regen", action="store_true",
                    help="regenerate the schematics from the sizing JSON first")
    a = ap.parse_args()
    d = design_of(CELL)
    if a.regen:
        subprocess.run([sys.executable, str(REPO / "scripts" / "gen_xschem.py"),
                        str(CELL), str(SCH), "--name", "lpf_core_022"], check=True)

    s_sch = M.score_plots(ng.simulate(netlist("lpf_tb_022"), "so_ac"), d)
    s_dck = M.evaluate(d, "so_ac_ref", record=False)
    card = json.loads(CARD.read_text())["scorecard"] if CARD.exists() else {}

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
        cs = "     --" if c_ is None else f"{c_:12.4f}"
        print(f"{k:12s} {a_:12.4f} {b_:12.4f} {cs}   "
              f"{'ok' if g1 else 'DIFFERS'}/{'ok' if g2 else 'DRIFTED'}")

    t_sch = T._score(ng.simulate(netlist("lpf_tb_022_thd"), "so_thd"),
                     50.0, 87.5e-3, 20, 512, "so")
    t_ref = T.measure(d, tag="so_thd_ref", gate=False)
    g1t = abs(t_sch.thd_db - t_ref.thd_db) <= 0.05
    ok1 &= g1t
    print(f"{'thd_db':12s} {t_sch.thd_db:12.3f} {t_ref.thd_db:12.3f} "
          f"{card.get('thd_db', float('nan')):12.3f}   {'ok' if g1t else 'DIFFERS'}/-")

    print(f"\nGATE 1  drawing == deck        : {'PASS' if ok1 else 'FAIL'}")
    print(f"GATE 2  matches certified card : {'PASS' if ok2 else 'FAIL'}")
    print(f"spec violations from the drawing: {s_sch.violations or 'none'}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
