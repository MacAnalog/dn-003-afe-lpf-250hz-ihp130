"""A committed scorecard's verdict must not contradict its own tables.

`layout/H12-pdk-cap/scorecard_post.json` is hand-assembled (no script writes
it), and it is a RECORD: the numbers in it were measured once and are not
re-derivable without re-simulating.  What IS mechanically checkable is that the
file agrees with itself and with the acceptance box in `harness.yaml`.

The defect these tests were written for (reviewer's F23 / gap G18): the file
ended on an unscoped `"all_pass": true` while its own `corners` table carried
five S1 misses and `corner_miss` recorded 329.821 deg against a 330.0 limit.
`all_pass` was not WRONG -- it is `all(passes.values())`, the nominal bench
only -- it was unlabelled, and `lab.corners` uses the same name for the
opposite scope.  The fix was additive (`all_pass_scope`, `corner_pass`,
`corner_pass_detail`); these tests stop the scope from going missing again and
stop a hand edit from moving a number out of agreement with its verdict.

Nothing here re-measures anything: every assertion is a cross-check between two
places the same fact is written down.

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab.metrics import SPEC  # noqa: E402

CARD = REPO / "layout" / "H12-pdk-cap" / "scorecard_post.json"

# The S1 line, read from the acceptance box rather than hardcoded, so that
# re-pointing the spec surfaces here instead of silently re-labelling the
# recorded misses.
S1_LABEL, S1_OP, S1_BOUND = SPEC["ph_max_deg"]


def card() -> dict:
    return json.loads(CARD.read_text())


def corner_rows(d: dict) -> list[tuple[str, dict]]:
    out = []
    for group in ("axes", "cap"):
        for r in d["corners"][group]:
            slug = r.get("slug") or f"{r['cap_corner']} iref x{r['iref_scale']}"
            out.append((f"corners.{group}[{r['dut']} / {slug}]", r))
    return out


class SpecBoxIsStillAMinimum(unittest.TestCase):
    """The 330 deg S1 threshold is a FLOOR, so 329.821 is a miss.

    Every reading of this scorecard turns on that.  If the operator ever became
    `<=`, the recorded `corner_miss` and its `short_by_deg` would mean the
    opposite of what they say, and this file would have to be re-derived rather
    than re-labelled.
    """

    def test_ph_max_is_scored_as_a_lower_bound(self):
        self.assertEqual(S1_OP, ">=", f"{S1_LABEL}: ph_max_deg is no longer a minimum")
        self.assertEqual(S1_BOUND, 330.0)


class VerdictsAreScoped(unittest.TestCase):
    def test_all_pass_is_exactly_the_nominal_passes_dict(self):
        d = card()
        self.assertEqual(d["all_pass"], all(d["passes"].values()))

    def test_all_pass_carries_its_scope_in_the_file(self):
        """A bare boolean is what an optimizer or a dashboard keys on."""
        d = card()
        scope = d.get("all_pass_scope", "")
        self.assertTrue(scope.strip(), "all_pass has no all_pass_scope beside it (F23/G18)")
        self.assertIn("corner_pass", scope,
                      "all_pass_scope must point the reader at the corner verdict")

    def test_corner_pass_matches_the_corner_table(self):
        d = card()
        self.assertIn("corner_pass", d, "the file records corner rows but no corner verdict")
        self.assertEqual(d["corner_pass"], all(r["pass"] for _, r in corner_rows(d)))

    def test_a_failing_corner_forces_corner_pass_false(self):
        """The contradiction F23 found, stated directly."""
        d = card()
        if any(not r["pass"] for _, r in corner_rows(d)):
            self.assertFalse(d["corner_pass"])


class TablesAgreeWithThemselves(unittest.TestCase):
    def test_every_corner_row_pass_flag_matches_its_violation_list(self):
        d = card()
        for where, r in corner_rows(d):
            self.assertEqual(r["pass"], not r["violations"], f"{where}: pass flag vs violations")

    def test_every_ph_max_below_the_bound_is_recorded_as_an_S1_violation(self):
        """Re-scores only S1, from the acceptance box, on every corner row."""
        d = card()
        for where, r in corner_rows(d):
            short = r["ph_max_deg"] < S1_BOUND
            flagged = any(v.startswith("S1 biquad-order certificate") for v in r["violations"])
            self.assertEqual(short, flagged,
                             f"{where}: ph_max {r['ph_max_deg']} vs bound {S1_BOUND}, "
                             f"violations {r['violations']}")

    def test_corner_miss_is_arithmetically_consistent(self):
        d = card()
        m = d["corner_miss"]
        self.assertEqual(m["limit_deg"], S1_BOUND)
        self.assertLess(m["ph_max_deg"], m["limit_deg"])
        self.assertAlmostEqual(m["short_by_deg"], m["limit_deg"] - m["ph_max_deg"], places=3)

    def test_corner_miss_names_a_row_that_is_in_the_corner_table(self):
        """The headline miss must be the same measurement as the table's."""
        d = card()
        m = d["corner_miss"]
        hits = [r for r in d["corners"]["cap"]
                if r["dut"] == "post" and r["ph_max_deg"] == m["ph_max_deg"]]
        self.assertTrue(hits, f"corner_miss ph_max {m['ph_max_deg']} is in no corners.cap post row")
        for r in hits:
            self.assertFalse(r["pass"], "the corner_miss row is recorded as a pass")

    def test_the_nominal_scorecard_is_the_cap_typ_post_row(self):
        """`scorecard` and `corners.cap[post/cap_typ]` are the same bench."""
        d = card()
        typ = [r for r in d["corners"]["cap"]
               if r["dut"] == "post" and r["cap_corner"] == "cap_typ" and r["iref_scale"] == 1.0]
        self.assertEqual(len(typ), 1)
        self.assertAlmostEqual(d["scorecard"]["ph_max_deg"], typ[0]["ph_max_deg"], places=2)
        self.assertAlmostEqual(d["scorecard"]["fc_hz"], typ[0]["fc_hz"], places=2)


if __name__ == "__main__":
    unittest.main()
