#!/usr/bin/env python3
"""Run the frozen reference deck and print its scorecard.

    python scripts/baseline.py            # simulate + print
    python scripts/baseline.py --check    # exit 1 if it drifted from certified

This is the repo's "is the world still the world?" command, and the second half
of `make check` (scripts/lint.py is the first).  It simulates
`decks/reference/lpf_tb.sp` EXACTLY AS FROZEN -- the same bytes the reference
baseline was certified on -- and compares the result against the certified
numbers in `decks/reference/scorecard.json`.

A drift here means one of: the simulator moved (ngspice build / OSDI objects),
the PDK model cards moved, the lane changed (docker vs native), or someone
edited the deck.  All four are legitimate re-certification events and all four
invalidate every A/B measured before them -- which is why this is a hard failure
and not a warning.  `scripts/lint.py` covers the fourth case mechanically
(REFERENCE_SHA) and additionally asserts that `lab.deck.ac_noise` still
regenerates these bytes from `decks/reference/design.json`.

Nothing here is carried forward from the originating campaign: every certified
number was measured in this repo, on this deck, in this lane.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import config as C                      # noqa: E402
from lab import ledger, metrics                  # noqa: E402
from lab import ngspice as ng                    # noqa: E402
from lab.dut import Design, Dev                  # noqa: E402

REF_DIR = REPO / "decks" / "reference"
SCORECARD = REF_DIR / "scorecard.json"
DESIGN = REF_DIR / "design.json"
DECK = REF_DIR / "lpf_tb.sp"

# Drift tolerances.  ngspice is deterministic for a fixed binary + options, so
# these are set by the spec's own resolution, not by run-to-run spread:
#   ("rel", 0.005)  0.5 % on cutoff, noise, current, power, capacitance
#   ("abs", 0.02)   0.02 dB on every gain -- a tenth of the S3/S4 budget (0.2 dB)
# The phase tolerance is the one number CARRIED FORWARD from the originating
# campaign's tolerance table (2 deg); it has not been re-derived from repeated
# runs here, and it is loose only because ph_max is read off a dec-10 grid.
TOL: dict[str, tuple[str, float]] = {
    "fc_hz":      ("rel", 0.005),
    "irn_uv":     ("rel", 0.005),
    "i_core_na":  ("rel", 0.005),
    "p_core_nw":  ("rel", 0.005),
    "c_total_pf": ("rel", 0.005),
    "dc_db":      ("abs", 0.02),
    "peak_db":    ("abs", 0.02),
    "a1000_db":   ("abs", 0.02),
    "ph_max_deg": ("abs", 2.0),
}


def load_design(path: Path = DESIGN) -> Design:
    """decks/reference/design.json -> the Design that generated the frozen deck."""
    j = json.loads(path.read_text())
    caps = j["caps_pf"]
    return Design(
        topology=j["topology"],
        devs={k: Dev(**v) for k, v in j["devs"].items()},
        c1_a=caps["c1_a"] * 1e-12, c2_a=caps["c2_a"] * 1e-12,
        c1_b=caps["c1_b"] * 1e-12, c2_b=caps["c2_b"] * 1e-12,
        iref=j["iref"],
        note="frozen reference baseline (decks/reference/)",
    )


def certified() -> dict:
    return json.loads(SCORECARD.read_text())["scorecard"]


def run_reference(tag: str = "reference_check", record: bool = True) -> metrics.Score:
    """Simulate the frozen deck text -- not a rebuild of it."""
    design = load_design()
    deck = DECK.read_text()
    rundir = ng.run(deck, tag)
    s = metrics.score_plots(ng.plots(rundir), design)
    if record:
        ledger.log_run(tag, s.values, deck=deck, design=design,
                       wall=ng.wall_time(rundir), violations=s.violations)
    return s


def drift(measured: metrics.Score) -> list[tuple[str, float, float, str]]:
    """Every certified key whose measurement moved beyond its tolerance."""
    out = []
    ref = certified()
    for k, (mode, tol) in TOL.items():
        want = ref.get(k)
        got = measured.get(k)
        if want is None:
            out.append((k, float("nan"), float("nan"),
                        "not in decks/reference/scorecard.json"))
            continue
        if got is None or (isinstance(got, float) and math.isnan(got)):
            out.append((k, float("nan"), float(want), "NOT MEASURED"))
            continue
        d = abs(got - want)
        limit = tol * abs(want) if mode == "rel" else tol
        if d > limit:
            unit = f"{tol * 100:g} %" if mode == "rel" else f"{tol:g} abs"
            out.append((k, float(got), float(want), f"|delta| {d:.4g} > {unit}"))
    return out


def report(s: metrics.Score) -> None:
    ref = certified()
    print(metrics.table({"reference (frozen deck)": s}))
    print()
    print(f"{'metric':<12}{'certified':>12}{'measured':>12}{'delta':>12}")
    print("-" * 48)
    for k in TOL:
        want, got = ref.get(k), s.get(k)
        if want is None or got is None or (isinstance(got, float) and math.isnan(got)):
            print(f"{k:<12}{'-' if want is None else f'{want:>12.4f}'}"
                  f"{'NOT MEASURED':>12}{'':>12}")
            continue
        print(f"{k:<12}{want:>12.4f}{got:>12.4f}{got - want:>12.4f}")
    print(f"\nlane: {C.lane()}   corner: {C.CORNER_NOM}   vdd: {C.VDD} V   "
          f"deck: {DECK.relative_to(REPO)}")
    print(f"\nspec verdict -- the reference is the YARDSTICK, not a solution: it is "
          f"expected to\nfail S5 (its {ref['irn_uv']:g} uVrms is the number to beat, "
          f"goal < {metrics.SPEC['irn_uv'][2]:g} uVrms).")
    print(metrics.explain(s))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the deck no longer reproduces the certified "
                         "scorecard")
    ap.add_argument("--tag", default="reference_check",
                    help="ledger tag for this run (default: reference_check)")
    ap.add_argument("--no-record", action="store_true",
                    help="do not append a ledger row")
    a = ap.parse_args()

    for p in (DECK, DESIGN, SCORECARD):
        if not p.exists():
            print(f"MISSING: {p.relative_to(REPO)}\n"
                  f"  The certified reference is the yardstick every candidate is "
                  f"scored against.\n"
                  f"  Restore it with `git checkout -- decks/reference`.")
            return 2

    try:
        s = run_reference(a.tag, record=not a.no_record)
    except ng.SimError as exc:
        print(f"SIMULATION FAILED on the frozen reference deck:\n{exc}\n\n"
              f"  Check the lane first: `make doctor` (python -m lab.ngspice).\n"
              f"  docker lane needs {C.DOCKER_IMAGE}; native lane needs LPF_NGSPICE\n"
              f"  pointing at an ngspice whose ~/.spiceinit loads the PDK .osdi "
              f"objects.")
        return 2

    report(s)

    if not a.check:
        return 0
    d = drift(s)
    if d:
        print("\nDRIFT vs the certified reference "
              "(decks/reference/scorecard.json):")
        for k, got, want, why in d:
            print(f"  {k}: got {got:.4f}, certified {want:.4f}   [{why}]")
        print("\n  Every A/B measured against the old numbers is now suspect.\n"
              "  If the change is deliberate (new ngspice build, new PDK, new lane),\n"
              "  re-certify: re-run this without --check, write the new numbers into\n"
              "  decks/reference/scorecard.json, and update REFERENCE_SHA in\n"
              "  scripts/lint.py in the same commit.")
        return 1
    print("\nOK: the frozen reference deck reproduces the certified scorecard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
