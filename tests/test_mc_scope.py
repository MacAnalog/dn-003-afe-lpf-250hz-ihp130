"""The Monte Carlo yield must name the spec lines it actually scored.

`lab.mc` drives ONE bench (`lab.deck.ac_noise`), so a draw carries evidence for
the ac/noise/power box only -- S1-S6 in `doc/target-spec.md`.  S7 (THD) needs an
independent long transient (`lab.thd`) and S8 (provenance) is not a measurement
at all.  A headline that says "passes every spec line" over those draws claims
evidence that was never collected, and the number is then quoted into sign-off
tables and the paper.

These tests pin the CLAIM, not the numbers, and they pin it to the DRAWS: the
covered ids come from the metric keys the samples actually produced, so a spec
row added to the acceptance box that no bench measures widens neither the
headline nor the ledger row.  Deriving the scope from `lab.metrics.SPEC` would
have exactly the opposite effect, which is what `SpecScopeComesFromTheDraws`
checks by mutating `SPEC` and requiring that nothing move.

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import corners, droop, mc  # noqa: E402
from lab import metrics as M  # noqa: E402
from lab.dut import Design, Dev  # noqa: E402

# A draw that passes every line of the ac/noise box, so the headline is the
# most flattering one the module can print -- which is where an overstated
# claim does its damage.
GOOD = {"ph_max_deg": 346.0, "a1000_db": -48.5, "fc_hz": 250.0, "dc_db": 0.0,
        "peak_db": 0.02, "ripple_db": 0.1, "irn_uv": 38.0, "p_core_nw": 12.0,
        "gd_dc_ms": 1.0, "gd_max_ms": 1.0}

# One more acceptance-box row, for a quantity NO draw of this bench measures --
# the S7 THD line, in the shape `lab.metrics.SPEC` holds.  Adding it is the
# realistic future edit that must NOT widen what a Monte Carlo campaign claims.
THD_ROW = {"thd_db": ("S7 THD at 175 mVpp, fin = 50 Hz", "<=", -40.0)}


def reference_design() -> Design:
    j = json.loads((REPO / "decks" / "reference" / "design.json").read_text())
    c = j["caps_pf"]
    return Design(topology=j["topology"],
                  devs={k: Dev(**v) for k, v in j["devs"].items()},
                  c1_a=c["c1_a"] * 1e-12, c2_a=c["c2_a"] * 1e-12,
                  c1_b=c["c1_b"] * 1e-12, c2_b=c["c2_b"] * 1e-12,
                  iref=j["iref"])


def result_of(values: dict, n: int = 4, *, violations=()) -> mc.McResult:
    """`n` draws that all produced `values`, scored as `violations`."""
    samples = [mc.Sample(seed=s,
                         score=M.Score(values=dict(values, seed=s),
                                       violations=list(violations)))
               for s in range(1, n + 1)]
    return mc.McResult(tag="scope_probe", design=reference_design(),
                       corner="mos_tt_mismatch", samples=samples)


def one_pass_result(n: int = 1) -> mc.McResult:
    return result_of(GOOD, n)


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

    def test_the_ac_noise_box_covers_s1_to_s6_today(self):
        """The status quo, so a silent change of scope shows up in a diff."""
        r = one_pass_result()
        self.assertEqual(r.spec_ids_covered, ["S1", "S2", "S3", "S4", "S5", "S6"])


class SpecScopeComesFromTheDraws(unittest.TestCase):
    """The scope is evidence, not intention: it follows the measured keys."""

    def test_a_spec_row_no_draw_measures_does_not_widen_the_scope(self):
        """Put THD in the acceptance box: the MC claim must not move.

        `mc.sample()` still runs one `lab.deck.ac_noise` deck and no
        transient, so no draw carries a `thd_db`.  A scope read off `SPEC`
        answers S1-S7 here -- a yield claiming a line nothing simulated.
        """
        with mock.patch.dict(M.SPEC, THD_ROW):
            r = one_pass_result(4)
            self.assertNotIn("S7", r.spec_ids_covered)
            self.assertEqual(r.spec_ids_covered,
                             ["S1", "S2", "S3", "S4", "S5", "S6"])
            self.assertIn("S7", r.spec_ids_excluded)
            self.assertNotIn("thd_db", r.scored_keys)

    def test_an_unmeasured_spec_row_is_not_a_convergence_failure(self):
        """A missing BENCH must not be reported as a broken simulation.

        Every draw here converged and met every line it measured.  Judging a
        draw against a line the bench never ran turns all four into
        'non-converged / non-finite' samples and the yield into 0 %.
        """
        with mock.patch.dict(M.SPEC, THD_ROW):
            r = one_pass_result(4)
            self.assertEqual(r.n_failed, 0)
            self.assertEqual(r.n_pass, 4)
            self.assertEqual(r.all_pass_yield, 1.0)

    def test_an_unmeasured_line_is_not_a_draw_failure(self):
        """`M.check`'s 'missing' line for an unrun bench is not a draw's fault."""
        with mock.patch.dict(M.SPEC, THD_ROW):
            r = result_of(GOOD, 4,
                          violations=["S7 THD at 175 mVpp, fin = 50 Hz: missing"])
            self.assertEqual(r.n_pass, 4)
            self.assertEqual(r.samples[0].scored_violations, [])

    def test_a_line_the_draws_stopped_measuring_leaves_the_scope(self):
        """Evidence lost is scope lost: drop irn_uv from the draws and S5 goes.

        The acceptance box is untouched here -- only the measurement is gone,
        which is the shape of a bench that silently stopped emitting a column.
        """
        no_noise = {k: v for k, v in GOOD.items() if k != "irn_uv"}
        r = result_of(no_noise, 4)
        self.assertNotIn("S5", r.spec_ids_covered)
        self.assertIn("S5", r.spec_ids_excluded)
        self.assertEqual(r.spec_ids_covered, ["S1", "S2", "S3", "S4", "S6"])

    def test_ids_are_read_off_the_spec_labels_not_hardcoded(self):
        """Take S5 out of the acceptance box and the covered span follows."""
        box = {k: v for k, v in M.SPEC.items() if k != "irn_uv"}
        with mock.patch.dict(M.SPEC, box, clear=True):
            r = one_pass_result(4)
            self.assertEqual(r.spec_ids_covered, ["S1", "S2", "S3", "S4", "S6"])
            self.assertIn("S5", r.spec_ids_excluded)

    def test_draws_that_all_failed_carry_evidence_for_nothing(self):
        """Zero results is zero scope -- never a full box quoted at 0 % yield."""
        samples = [mc.Sample(seed=s, error="doAnalyses: iteration limit reached")
                   for s in range(1, 5)]
        r = mc.McResult(tag="scope_probe", design=reference_design(),
                        corner="mos_tt_mismatch", samples=samples)
        self.assertEqual(r.spec_ids_covered, [])
        self.assertEqual(sorted(r.spec_ids_excluded), sorted(M.SPEC_IDS_ALL))
        t = mc.table(r)
        self.assertIn("No spec line was measured by every draw", t)
        self.assertNotIn("SCORED-BOX YIELD", t)


class ViolationMatching(unittest.TestCase):
    """A failed line must fail the draw whatever shape its sentence has."""

    def test_an_abs_bound_failure_fails_the_draw(self):
        """`abs<=` renders as `|S3 passband gain| <= 0.2 dB: got 0.5`.

        The sentence does not BEGIN with the label, so a prefix match drops it
        and a draw that misses S3 gain by 2.5x is counted as a pass.
        """
        bad = dict(GOOD, dc_db=0.5)
        self.assertEqual(M.check(bad), ["|S3 passband gain| <= 0.2 dB: got 0.5"])
        r = result_of(bad, 4, violations=M.check(bad))
        self.assertEqual(r.n_pass, 0)
        self.assertEqual(r.all_pass_yield, 0.0)

    def test_an_abs_bound_failure_fails_its_own_line_column(self):
        """The per-line column, too: `yield_dc_db` is not 100 % here.

        Pre-existing: `line_pass` matched the label as a prefix, so every
        `abs<=` line reported every usable draw as passing it, whatever the
        measurement was.
        """
        bad = dict(GOOD, dc_db=0.5)
        r = result_of(bad, 4, violations=M.check(bad))
        self.assertEqual(r.line_pass("dc_db"), 0)
        self.assertEqual(r.summary()["yield_dc_db"], 0.0)
        self.assertEqual(r.line_pass("fc_hz"), 4)      # only the failing line

    def test_the_sibling_benches_match_the_same_way(self):
        """`lab.corners` and `lab.droop` read the same sentences.

        A prefix match left `summary()['worst']['dc_db']['ok']` stuck at True
        for any gain whatever, and left `failing_keys` carrying the raw
        sentence -- so two supplies failing the SAME line looked like two
        different failure modes and the droop walk stopped at its anchor.
        """
        self.assertFalse(corners._line_ok("dc_db", 5.0))
        self.assertTrue(corners._line_ok("dc_db", 0.05))
        for key, v in (("dc_db", 5.0), ("ph_max_deg", 100.0)):
            bad = dict(GOOD, **{key: v})
            p = droop.DroopPoint(vdd=1.2, values=bad, violations=M.check(bad))
            self.assertEqual(p.failing_keys, frozenset({key}))


class Summary(unittest.TestCase):
    def test_summary_records_the_scope(self):
        """The ledger row / scorecard carries what the yield covered."""
        s = one_pass_result(4).summary()
        self.assertEqual(s["spec_ids_covered"], "S1,S2,S3,S4,S5,S6")
        self.assertEqual(s["spec_ids_excluded"], "S7,S8")

    def test_summary_scope_ignores_a_spec_row_nothing_measured(self):
        """The recorded scope is the draws' scope in the ledger too."""
        with mock.patch.dict(M.SPEC, THD_ROW):
            s = one_pass_result(4).summary()
            self.assertEqual(s["spec_ids_covered"], "S1,S2,S3,S4,S5,S6")
            self.assertEqual(s["spec_ids_excluded"], "S7,S8")
            self.assertEqual(s["all_pass_yield"], 1.0)
            self.assertNotIn("yield_thd_db", s)

    def test_summary_keeps_the_committed_key(self):
        """Regression guard, NOT a repro of the defect: `all_pass_yield` is the
        column name in the committed sign-off scorecards and paper data, so
        renaming it would orphan them.  Passes on the pre-fix code too."""
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

    def test_table_does_not_widen_when_the_box_gains_an_unrun_line(self):
        """The printed span and the per-line table stay on the evidence."""
        with mock.patch.dict(M.SPEC, THD_ROW):
            t = mc.table(one_pass_result(4)).replace("–", "-")
            self.assertIn("S1-S6", t)
            self.assertNotIn("S1-S7", t)
            self.assertIn("SCORED-BOX YIELD = 100.0 %", t)
            # no per-line row for a line no draw measured
            self.assertNotIn("| S7 THD at 175 mVpp", t)


if __name__ == "__main__":
    unittest.main()
