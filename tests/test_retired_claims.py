"""A claim retired from the code must not survive in the live prose.

`lab.mc`'s headline stopped being an "all-pass yield" because one draw is one
`lab.deck.ac_noise` run and therefore evidence for S1-S6 only.  A rename inside
the module is worth nothing if the paper, the spec document and the experiment
log go on printing the retired name beside the same number -- that is what a
reader actually quotes.

Two guards, both regression guards: they pin wording, so they say nothing about
whether a NEW overstatement is phrased differently.  They exist because these
exact sentences were shipped once and were still in the tree after the first
fix.

**Live vs frozen.**  Only files that speak in the present tense are checked.
Round records -- `signoff/**`, the per-experiment READMEs, `doc/journal/**`,
`doc/sizing-history/**`, `layout/**` -- are the output of a campaign as it ran
and are deliberately left alone; rewriting them would falsify a record.

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

CERTIFY = REPO / "experiments" / "021-publication-cell" / "certify.py"

# Present-tense documents and the code that prints into them.
LIVE = [
    "README.md",
    "CLAUDE.md",
    "doc/target-spec.md",
    "doc/experiment-log.md",
    "doc/paper/README.md",
    "doc/paper/results_schematic.md",
    "doc/paper/results_layout.md",
    "doc/paper/results_group_delay.md",
    "lab/mc.py",
    "lab/droop.py",
    "lab/corners.py",
    "doc/paper/scripts/fig_mc.py",
    "doc/paper/scripts/fig_pvt.py",
    "doc/paper/scripts/fig_pvt_postlayout.py",
    "experiments/021-publication-cell/robust.py",
]

# The retired names for the mismatch yield.  `all_pass_yield` (the dict key and
# JSON column) is deliberately NOT matched: it is the name of a column in
# committed records, and keeping it is the point.
RETIRED = (
    re.compile(r"all[- ]pass yield", re.I),
    re.compile(r"MC all[- ]pass", re.I),
    re.compile(r"mismatch all[- ]pass", re.I),
    re.compile(r"\d+\s*/\s*\d+[*\s]+all[- ]pass", re.I),   # "**82/100** all-pass"
    re.compile(r"ALL-PASS YIELD"),
)


def live_files() -> list[Path]:
    return [REPO / rel for rel in LIVE if (REPO / rel).exists()]


class RetiredYieldName(unittest.TestCase):
    def test_no_live_document_calls_it_an_all_pass_yield(self):
        """S7 and S8 are not in those draws; only the scored box is."""
        hits = []
        for f in live_files():
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if any(p.search(line) for p in RETIRED):
                    hits.append(f"{f.relative_to(REPO)}:{n}: {line.strip()}")
        self.assertEqual(hits, [], "retired 'all-pass yield' wording is live in:\n"
                                  + "\n".join(hits))


class NoPerDrawS1toS8Gate(unittest.TestCase):
    """Nothing ANDs a Monte Carlo draw with a THD measurement of that draw.

    `certify.py` ANDs S1-S6 with S7 on ONE NOMINAL cell (`M.evaluate` +
    `T.measure`), which is a per-cell verdict and not a rate over a population.
    The first fix wrote the opposite into `doc/target-spec.md` and into
    `robust.py`; this guard fails if that sentence comes back while the code
    still has no per-draw gate.
    """

    def test_certify_does_not_import_the_monte_carlo(self):
        src = CERTIFY.read_text()
        self.assertNotIn("lab import mc", src)
        self.assertNotIn("lab.mc", src)

    def test_no_live_document_claims_certify_ands_a_draw(self):
        if "lab.mc" in CERTIFY.read_text():        # a per-draw gate would be news
            self.skipTest("certify.py now touches lab.mc -- re-read the docs by hand")
        pat = re.compile(r"`?lab\.mc`? draw with an `?lab\.thd`?")
        hits = [str(f.relative_to(REPO)) for f in live_files()
                if pat.search(f.read_text())]
        self.assertEqual(hits, [],
                         "these say certify.py ANDs an lab.mc draw with an "
                         "lab.thd measurement of that draw; it does not: "
                         + ", ".join(hits))


if __name__ == "__main__":
    unittest.main()
