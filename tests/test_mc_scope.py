"""The Monte Carlo yield must name the spec lines it actually scored.

`lab.mc` drives ONE bench (`lab.deck.ac_noise`), so a draw carries evidence for
the ac/noise/power box only -- S1-S6 in `doc/target-spec.md`.  S7 (THD) needs an
independent long transient (`lab.thd`) and S8 (provenance) is not a measurement
at all.  A headline that says "passes every spec line" over those draws claims
evidence that was never collected, and the number is then quoted into sign-off
tables and the paper.

These tests pin the CLAIM, not the numbers: the covered and excluded spec ids
are derived from `lab.metrics.SPEC`, so the day S7 enters the acceptance box the
scope widens by itself instead of going quietly stale.

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import mc  # noqa: E402
from lab import metrics as M  # noqa: E402
from lab.dut import Design, Dev  # noqa: E402

# A draw that passes every line of the ac/noise box, so the headline is the
# most flattering one the module can print -- which is where an overstated
# claim does its damage.
GOOD = {"ph_max_deg": 346.0, "a1000_db": -48.5, "fc_hz": 250.0, "dc_db": 0.0,
        "peak_db": 0.02, "ripple_db": 0.1, "irn_uv": 38.0, "p_core_nw": 12.0,
        "gd_dc_ms": 1.0, "gd_max_ms": 1.0}


def reference_design() -> Design:
    j = json.loads((REPO / "decks" / "reference" / "design.json").read_text())
    c = j["caps_pf"]
    return Design(topology=j["topology"],
                  devs={k: Dev(**v) for k, v in j["devs"].items()},
                  c1_a=c["c1_a"] * 1e-12, c2_a=c["c2_a"] * 1e-12,
                  c1_b=c["c1_b"] * 1e-12, c2_b=c["c2_b"] * 1e-12,
                  iref=j["iref"])


def one_pass_result(n: int = 1) -> mc.McResult:
    d = reference_design()
    samples = [mc.Sample(seed=s, score=M.Score(values=dict(GOOD, seed=s),
                                               violations=[]))
               for s in range(1, n + 1)]
    return mc.McResult(tag="scope_probe", design=d,
                       corner="mos_tt_mismatch", samples=samples)


class SpecIds(unittest.TestCase):
    def test_all_ids_are_partitioned(self):
        """Covered + excluded is exactly the S1-S8 universe, with no overlap."""
        r = one_pass_result()
        cov, exc = r.spec_ids_covered, r.spec_ids_excluded
        self.assertEqual(sorted(set(cov) | set(exc)), sorted(M.SPEC_IDS_ALL))
        self.assertEqual(set(cov) & set(exc), set())

    def test_thd_is_not_covered_by_an_ac_noise_draw(self):
        """S7 is scored by lab.thd, never by the deck lab.mc runs."""
        r = one_pass_result()
        self.assertNotIn("S7", r.spec_ids_covered)
        self.assertIn("S7", r.spec_ids_excluded)

    def test_covered_ids_come_from_the_spec_box(self):
        """Derived from harness.yaml, not hardcoded: today that is S1-S6."""
        r = one_pass_result()
        self.assertEqual(r.spec_ids_covered, ["S1", "S2", "S3", "S4", "S5", "S6"])


class Summary(unittest.TestCase):
    def test_summary_records_the_scope(self):
        """The ledger row / scorecard carries what the yield covered."""
        s = one_pass_result(4).summary()
        self.assertEqual(s["spec_ids_covered"], "S1,S2,S3,S4,S5,S6")
        self.assertEqual(s["spec_ids_excluded"], "S7,S8")

    def test_summary_keeps_the_committed_key(self):
        """`all_pass_yield` is in committed records; renaming it would orphan them."""
        s = one_pass_result(4).summary()
        self.assertIn("all_pass_yield", s)
        self.assertEqual(s["all_pass_yield"], 1.0)


class Table(unittest.TestCase):
    def test_headline_does_not_claim_every_spec_line(self):
        """The unqualified claim is the defect: S7 was never simulated."""
        t = mc.table(one_pass_result(4))
        self.assertNotIn("pass every spec line", t)
        self.assertNotIn("ALL-PASS YIELD", t)

    def test_headline_names_the_covered_ids(self):
        t = mc.table(one_pass_result(4))
        self.assertIn("S1-S6", t.replace("–", "-"))

    def test_table_states_what_was_not_scored(self):
        """A reader must see S7/S8 named as out of scope, on the same page."""
        t = mc.table(one_pass_result(4))
        self.assertIn("S7", t)
        self.assertIn("S8", t)
        self.assertIn("lab.thd", t)


if __name__ == "__main__":
    unittest.main()
