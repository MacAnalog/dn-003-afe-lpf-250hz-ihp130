"""A reader of the headline post-layout row must meet its limitations there.

The four things the extraction does not model -- nondeterministic RC meshing,
stripped MIM top plates, missing well/substrate junction C, and an LVS gate that
cannot see the pin list -- were recorded only in the paper pack's gap list
(`doc/paper/README.md` gaps G8-G11) and in the reviewer's findings.  `README.md`
quoted the post-layout scorecard with none of them beside it, so the honest
qualifications sat two documents away from the number they qualify.

**What these tests can and cannot do.**  They pin PRESENCE and CITATION
INTEGRITY: that the limitation block still exists inside the layout-of-record
section, still names all four subjects, and still cites gap and finding ids that
actually exist in the documents it points at.  They say nothing about whether
the bounds in it are right -- those are measurements in `REVIEW.md` and
`scorecard_post.json` and are not re-derivable without re-simulating.  A test
that claimed otherwise would be the hollow kind.

Run:  .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

README = REPO / "README.md"
PAPER = REPO / "doc" / "paper" / "README.md"
REVIEW = REPO / "layout" / "H12-pdk-cap" / "REVIEW.md"

# One (subject, pattern) per thing the extraction does not model.  Patterns are
# deliberately loose -- the block may be re-worded; it may not lose a subject.
SUBJECTS = (
    ("nondeterministic RC extraction", re.compile(r"RC (extraction|run|mesh)", re.I)),
    ("stripped MIM top plates", re.compile(r"MIM top plate", re.I)),
    ("well/substrate junction capacitance", re.compile(r"junction capacitance", re.I)),
    ("the unchecked `vbp` pin", re.compile(r"\bvbp\b")),
)


def layout_section() -> str:
    """`README.md` from the layout-of-record heading to the next top-level one."""
    text = README.read_text()
    start = text.index("### Layout of record")
    rest = text[start:]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


class HeadlineCarriesItsLimitations(unittest.TestCase):
    def test_the_layout_section_has_a_limitation_block(self):
        sec = layout_section()
        self.assertRegex(sec, r"###\s+Known limitation",
                         "the layout-of-record section quotes a post-layout scorecard with no "
                         "limitation subsection beside it")

    def test_all_four_unmodelled_effects_are_named(self):
        sec = layout_section()
        missing = [name for name, pat in SUBJECTS if not pat.search(sec)]
        self.assertEqual(missing, [], f"not surfaced beside the headline row: {missing}")


class CitationsResolve(unittest.TestCase):
    """A limitation that points at a gap or finding id which no longer exists is
    worse than no pointer: the reader concludes the qualification was retired."""

    def test_every_gap_id_cited_exists_in_the_paper_gap_list(self):
        sec = layout_section()
        cited = sorted(set(re.findall(r"\bG\d+\b", sec)))
        cited += [f"G{n}" for m in re.findall(r"\bG(\d+)\s*[-–]\s*G(\d+)\b", sec)
                  for n in range(int(m[0]), int(m[1]) + 1)]
        self.assertTrue(cited, "the limitation block cites no gap id")
        paper = PAPER.read_text()
        for gid in sorted(set(cited)):
            self.assertRegex(paper, rf"\|\s*\*\*{gid}\*\*\s*\|",
                             f"{gid} is cited by README.md but is not a row in doc/paper/README.md")

    def test_every_reviewer_finding_cited_exists_in_the_review(self):
        sec = layout_section()
        cited = sorted(set(re.findall(r"\bF\d+\b", sec)))
        self.assertTrue(cited, "the limitation block cites no reviewer finding")
        review = REVIEW.read_text()
        for fid in cited:
            self.assertRegex(review, rf"\|\s*\*\*{fid}\*\*\s*\|",
                             f"{fid} is cited by README.md but is not a row in "
                             f"layout/H12-pdk-cap/REVIEW.md")


ASBUILT = REPO / "layout" / "H12-pdk-cap" / "asbuilt"
LIVE_DOCS = (README, PAPER, REPO / "doc" / "paper" / "results_layout.md")


def subckt_pins(path) -> list[str]:
    """The `.subckt lpf_core ...` header of a committed netlist, as a pin list."""
    for line in path.read_text().splitlines():
        if line.lower().startswith(".subckt"):
            return line.split()[2:]
    raise AssertionError(f"{path} has no .subckt header")


def vbp_lines(path) -> list[str]:
    return [ln for ln in path.read_text().splitlines() if re.search(r"\bvbp\b", ln, re.I)]


class VbpIsWhereTheProseSaysItIs(unittest.TestCase):
    """The `vbp` limitation is prose ABOUT two committed netlists, so it is checkable.

    Three live documents (`README.md`'s limitation block, gap **G11**, the **F13**
    mirror) say the same three things: `vbp` is on the `.subckt` header of both
    as-built netlists, on no device card in either, and the two headers disagree on
    pin count.  An earlier wording said instead that `vbp` was "absent from the
    extracted netlist" -- true only of the reviewer's own uncommitted run, and
    false of `asbuilt/core_pex.sp`, which is the extracted netlist of record.
    These tests read the netlists, so the prose cannot drift back.
    """

    def test_vbp_is_declared_by_both_asbuilt_netlists(self):
        for name in ("core_lvs.sp", "core_pex.sp"):
            self.assertIn("vbp", subckt_pins(ASBUILT / name),
                          f"{name} no longer declares vbp; the vbp limitation is now wrong")

    def test_vbp_is_on_no_device_card_in_either_netlist(self):
        """"Dangling port" (BRIEF section 9) means the header line and nothing else."""
        for name in ("core_lvs.sp", "core_pex.sp"):
            hits = vbp_lines(ASBUILT / name)
            self.assertEqual(len(hits), 1, f"{name}: vbp appears on {len(hits)} lines, not just "
                                           f"the .subckt header: {hits}")
            self.assertTrue(hits[0].lower().startswith(".subckt"))

    def test_the_two_headers_disagree_exactly_as_documented(self):
        """8 pins vs 7: `core_pex.sp` omits `vss`, which kpex ties to node 0."""
        lvs, pex = subckt_pins(ASBUILT / "core_lvs.sp"), subckt_pins(ASBUILT / "core_pex.sp")
        self.assertEqual(len(lvs), 8)
        self.assertEqual(len(pex), 7)
        self.assertEqual(sorted(set(lvs) - set(pex)), ["vss"])

    def test_no_live_doc_still_calls_vbp_absent_from_the_extracted_netlist(self):
        """The stale wording, pinned against the artifact that refutes it."""
        for doc in LIVE_DOCS:
            for line in doc.read_text().splitlines():
                if re.search(r"\bvbp\b", line, re.I):
                    self.assertNotRegex(
                        line, r"absent from the extracted netlist",
                        f"{doc.relative_to(REPO)}: vbp IS on the .subckt header of "
                        f"asbuilt/core_pex.sp, the extracted netlist of record")


if __name__ == "__main__":
    unittest.main()
