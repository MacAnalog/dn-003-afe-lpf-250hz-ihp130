#!/usr/bin/env python3
"""`make lint`: the platform harness checks (driven by harness.yaml) plus this repo's own.

Every failure message carries its remediation.  The generic half -- frozen reference dir,
experiments, paper index, journal, spec<->doc sync, denylist, gitignore, context pack -- is
`spicexplorer_harness.lint`; below are the checks only this repo can state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from spicexplorer_harness import lint, load  # noqa: E402
from spicexplorer_harness.lint import Lint  # noqa: E402


def deck_rebuild(L: Lint) -> None:
    """The frozen deck must still be reproducible from lab code + design.json.

    `decks/reference/` is bytes, `lab.deck` + `lab.dut` is the generator; if a builder drifts,
    every experiment silently measures a different bench than the certified one.
    """
    ref = REPO / "decks" / "reference"
    dj, tb, core = ref / "design.json", ref / "lpf_tb.sp", ref / "lpf_core.sp"
    if not (dj.exists() and tb.exists()):
        return  # the frozen check already reported it
    try:
        from lab import deck as L_deck
        from lab.dut import Design, Dev
        j = json.loads(dj.read_text())
        d = Design(topology=j["topology"],
                   devs={k: Dev(**v) for k, v in j["devs"].items()},
                   c1_a=j["caps_pf"]["c1_a"] * 1e-12, c2_a=j["caps_pf"]["c2_a"] * 1e-12,
                   c1_b=j["caps_pf"]["c1_b"] * 1e-12, c2_b=j["caps_pf"]["c2_b"] * 1e-12,
                   iref=j["iref"])
        built_tb, built_core = L_deck.ac_noise(d), L_deck.subckt(d)
    except Exception as exc:  # noqa: BLE001
        L.fail("deck-rebuild", f"cannot rebuild the reference deck from design.json: {exc!r}",
               "decks/reference/design.json must round-trip through lab.dut.Design and "
               "lab.deck.ac_noise; fix the loader contract or re-export design.json")
        return
    fix = ("either a deck fragment changed (revert it) or re-certify: `python scripts/baseline.py "
           "--check`, re-freeze with `make freeze`, commit SHA256SUMS -- an un-reproducible "
           "reference means every A/B is measured against a bench nobody can rebuild")
    if built_tb != tb.read_text():
        L.fail("deck-rebuild", "lab.deck.ac_noise(design.json) no longer reproduces "
                               "decks/reference/lpf_tb.sp byte for byte", fix)
    if core.exists() and built_core.strip() != core.read_text().strip():
        L.fail("deck-rebuild", "lab.dut.subckt(design.json) no longer reproduces "
                               "decks/reference/lpf_core.sp", fix)


def spec_headline(L: Lint) -> None:
    """The S5 goal and the certified reference IRN read identically in doc/target-spec.md."""
    h = L.h
    flat = h.text(h.spec_doc).replace("**", "")
    goal = next((r.bound for r in h.spec if r.key == "irn_uv"), None)
    if goal is not None and f"< {goal:g} µV" not in flat:
        L.fail("spec-sync", f"S5 goal {goal:g} µVrms has no '< {goal:g} µV' in {h.spec_doc}",
               "update the target-spec S5 row (or revert harness.yaml); the goal is the headline "
               "of the challenge and must read identically in both places")
    try:
        ref = json.loads(h.text(h.reference_scorecard))["scorecard"]["irn_uv"]
    except (ValueError, KeyError, TypeError):
        return
    if f"{ref:.2f}" not in flat:
        L.fail("spec-sync", f"the certified reference IRN {ref:.2f} µVrms is absent from "
                            f"{h.spec_doc}",
               "the spec table's 'reference baseline' column quotes decks/reference/scorecard.json;"
               " re-run `python scripts/baseline.py --check` and copy the certified numbers across")


if __name__ == "__main__":
    sys.exit(lint.main(load(REPO), extra=(deck_rebuild, spec_headline)))
