#!/usr/bin/env python3
"""Query the run ledger (runs/ledger.ndjson) -- observability as querying.

Every `lab.metrics.evaluate` call appends one row automatically, so the ledger
is the episodic memory of the whole campaign.  This script is how an agent asks
it questions instead of re-running simulations it already ran.

    python scripts/runs.py                    # last 15 evaluate rows
    python scripts/runs.py --last 40          # more
    python scripts/runs.py --fails            # only rows with spec violations
    python scripts/runs.py --best irn_uv      # top 10 by a metric (ascending)
    python scripts/runs.py --best ph_max_deg --desc
    python scripts/runs.py --exp 006          # rows stamped with LPF_EXP=006
    python scripts/runs.py --topology b       # one topology
    python scripts/runs.py --since 2026-08-11 # timestamp prefix, ISO order
    python scripts/runs.py --tag caps         # tag substring
    python scripts/runs.py --kind thd         # THD rows instead of scorecards
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import ledger                      # noqa: E402

DEFAULT_LAST = 15
BEST_N = 10


def _f(row: dict, key: str, default: float = 0.0) -> float:
    v = row.get(key)
    if isinstance(v, (int, float)) and v == v:      # not None, not NaN
        return float(v)
    return default


def _fit(v: float, w: int, p: int = 1) -> str:
    """Fixed-point in `w` columns, falling back to %g so a runaway value (a
    diverged sizing point reads 7.8e5 uVrms) cannot shift the whole table."""
    for s in (f"{v:.{p}f}", f"{v:.4g}", f"{v:.3g}", f"{v:.2g}", f"{v:.1g}"):
        if len(s) <= w:
            break
    return f"{s:>{w}}"


def show_eval(rows: list[dict]) -> None:
    hdr = (f"{'t':<20}{'tag':<24}{'topo':<10}{'dc':>7}{'fc':>8}{'peak':>6}"
           f"{'IRN':>7}{'P nW':>7}{'C pF':>8}{'s':>6}  violations")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        v = "; ".join(r.get("violations") or [])
        goal = "*" if r.get("goal_met") else " "        # * == inside the whole box
        print(f"{str(r.get('t', '?')):<20}{str(r.get('tag', '?'))[:23]:<24}"
              f"{str(r.get('topology', '') or '-')[:9]:<10}"
              f"{_fit(_f(r, 'dc_db'), 7, 2)}{_fit(_f(r, 'fc_hz'), 8)}"
              f"{_fit(_f(r, 'peak_db'), 6, 2)}{_fit(_f(r, 'irn_uv'), 6)}{goal}"
              f"{_fit(_f(r, 'p_core_nw'), 7, 2)}{_fit(_f(r, 'c_total_pf'), 8, 2)}"
              f"{_fit(_f(r, 'wall_s'), 6)}  {v}")


def show_thd(rows: list[dict]) -> None:
    """THD rows.  Field names are the frozen ledger contract for kind='thd':
    method ('fast' | 'signoff'), fin, ampl_pp_mv, thd_db | hd3_db, pass_spec."""
    hdr = (f"{'t':<20}{'tag':<24}{'method':<9}{'fin':>6}{'mVpp':>7}"
           f"{'THD/HD3':>9}  pass")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        db = r.get("thd_db", r.get("hd3_db", 0)) or 0
        print(f"{str(r.get('t', '?')):<20}{str(r.get('tag', '?'))[:23]:<24}"
              f"{str(r.get('method', '?')):<9}{_f(r, 'fin'):>6g}"
              f"{_f(r, 'ampl_pp_mv'):>7.1f}{float(db):>9.1f}  "
              f"{'PASS' if r.get('pass_spec') else 'FAIL'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--last", type=int, default=DEFAULT_LAST,
                    help=f"how many rows to show (default {DEFAULT_LAST})")
    ap.add_argument("--fails", action="store_true",
                    help="only rows that violate a spec line")
    ap.add_argument("--best", metavar="METRIC",
                    help=f"top {BEST_N} by a metric, ascending; overrides --last")
    ap.add_argument("--desc", action="store_true",
                    help="--best sorts descending (for metrics that are maximised, "
                         "e.g. ph_max_deg)")
    ap.add_argument("--tag", help="tag substring filter")
    ap.add_argument("--exp", help="experiment id (the LPF_EXP stamp), exact match")
    ap.add_argument("--topology", help="topology name, exact match")
    ap.add_argument("--since", help="timestamp prefix, e.g. 2026-08-11 (ISO order)")
    ap.add_argument("--kind", default="evaluate",
                    help="ledger row kind: evaluate (default), thd, or 'all'")
    a = ap.parse_args()

    rows = ledger.read()                                   # oldest first
    if a.kind != "all":
        rows = [r for r in rows if r.get("kind", "evaluate") == a.kind]
    if a.tag:
        rows = [r for r in rows if a.tag in str(r.get("tag", ""))]
    if a.exp:
        rows = [r for r in rows if str(r.get("exp", "")) == a.exp]
    if a.topology:
        rows = [r for r in rows if str(r.get("topology", "")) == a.topology]
    if a.since:
        rows = [r for r in rows if str(r.get("t", "")) >= a.since]
    if a.fails:
        rows = [r for r in rows
                if r.get("violations")
                or (a.kind == "thd" and not r.get("pass_spec"))]
    if a.best:
        rows = sorted((r for r in rows
                       if isinstance(r.get(a.best), (int, float))
                       and r[a.best] == r[a.best]),
                      key=lambda r: r[a.best], reverse=a.desc)[:BEST_N]
    else:
        rows = rows[-a.last:]

    if not rows:
        print("no matching ledger rows (runs/ledger.ndjson)")
        return 0
    if a.kind == "thd":
        show_thd(rows)
    else:
        show_eval(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
