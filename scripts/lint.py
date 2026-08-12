#!/usr/bin/env python3
"""Harness lints -- repo invariants promoted from docs to mechanical checks.

Principle: **a doc that fails to change behaviour gets promoted to a linter, and
the failure message itself teaches the remediation.**  Every check runs (no
short-circuit), every failure is collected, and the exit code is 1 if any hold.

    python scripts/lint.py        (or: make lint)

Stdlib only, on purpose: the lint must run before/without a working simulator
lane, so it reads lab/metrics.py through `ast` rather than importing numpy.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FAILS: list[str] = []


def fail(check: str, msg: str, fix: str) -> None:
    FAILS.append(f"[{check}] {msg}\n    FIX: {fix}")


# ---------------------------------------------------------------------------
# 1. the frozen reference deck is immutable
# ---------------------------------------------------------------------------
# sha256 of every file in the vendored reference bench, recorded 2026-08-11 --
# the day the SG13G2 reference baseline was certified (fc 250.00 Hz, dc
# -0.0047 dB, IRN 50.18 uVrms, core 12.07 nW).  A deliberate re-vendor updates
# this map AND re-runs `make check` so the certified scorecard is re-certified.
REFERENCE_SHA = {
    "decks/reference/build-sheet.md":
        "e88d2b37032a3a8d1e065da892b141a5daed38f9069f4f04264a6b979bdbbd26",
    "decks/reference/design.json":
        "c44b3e44068e9722f3ee87cc4e6cb6e7fd7f76415e588bb6f1be846fce5f5f86",
    "decks/reference/lpf_core.sp":
        "23ea089e854a598672a39dff17e1e94117b08d9fe7b0ded5b018ba3036a903c0",
    "decks/reference/lpf_tb.sp":
        "ffc3a6aba96756ea9e7af511a0d94395465c74b52cb813f64c3953f8559a6bfa",
    "decks/reference/scorecard.json":
        "8294dda28cf7e397848838634130876b4bf33de17b6a57d0462abfe7f2c26b2f",
}

RE_VENDOR = ("a deliberate re-vendor must update REFERENCE_SHA in scripts/lint.py "
             "AND re-run `make check`, which re-certifies "
             "decks/reference/scorecard.json against the new deck")


def check_reference_deck() -> None:
    """The reference bench is the yardstick; nothing may edit it in place."""
    d = REPO / "decks" / "reference"
    if not d.is_dir():
        fail("reference-deck", "decks/reference/ is missing",
             "restore with `git checkout -- decks/reference` (or re-vendor per "
             "doc/environment.md); experiments build their decks with lab.deck, "
             "never by editing the vendored files")
        return
    for rel, want in sorted(REFERENCE_SHA.items()):
        p = REPO / rel
        if not p.exists():
            fail("reference-deck", f"{rel} is missing",
                 "restore with `git checkout -- decks/reference` (or re-vendor per "
                 "doc/environment.md); experiments must mutate decks via lab.deck, "
                 "never the vendored files")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            fail("reference-deck", f"{rel} was modified (sha mismatch)",
                 "the vendored deck IS the certified reference; revert with "
                 f"`git checkout -- decks/reference`. If {RE_VENDOR}")
    extra = sorted(str(p.relative_to(REPO)) for p in d.rglob("*")
                   if p.is_file() and str(p.relative_to(REPO)) not in REFERENCE_SHA)
    for rel in extra:
        fail("reference-deck", f"{rel} is in decks/reference/ but not in REFERENCE_SHA",
             "the reference directory is hash-locked in full, so an unrecorded file "
             f"is either scratch (delete it) or a re-vendor -- and {RE_VENDOR}")


def check_deck_rebuild() -> None:
    """The frozen deck must still be reproducible from code + design.json.

    This is the tie between the two halves of the harness: `decks/reference/`
    is bytes, `lab.deck` + `lab.dut` is the generator.  If a topology builder or
    a testbench fragment drifts, every experiment silently starts measuring a
    different bench than the one the reference was certified on.
    """
    dj = REPO / "decks" / "reference" / "design.json"
    tb = REPO / "decks" / "reference" / "lpf_tb.sp"
    core = REPO / "decks" / "reference" / "lpf_core.sp"
    if not (dj.exists() and tb.exists()):
        return          # already reported by check_reference_deck
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
    except Exception as exc:                                   # noqa: BLE001
        fail("deck-rebuild", f"cannot rebuild the reference deck from design.json: {exc!r}",
             "decks/reference/design.json must round-trip through lab.dut.Design and "
             "lab.deck.ac_noise; fix the loader contract or re-export design.json from "
             "the Design that certified the baseline")
        return
    if built_tb != tb.read_text():
        fail("deck-rebuild", "lab.deck.ac_noise(design.json) no longer reproduces "
                             "decks/reference/lpf_tb.sp byte for byte",
             "either a deck fragment changed (revert it, or re-certify: re-run "
             "`python scripts/baseline.py --check`, re-freeze the deck and update "
             "REFERENCE_SHA) -- an un-reproducible reference means every A/B in the "
             "repo is measured against a bench nobody can rebuild")
    if core.exists() and built_core.strip() != core.read_text().strip():
        fail("deck-rebuild", "lab.dut.subckt(design.json) no longer reproduces "
                             "decks/reference/lpf_core.sp",
             "same remediation as the testbench: revert the topology-builder change "
             "or re-freeze and re-certify the reference")


# ---------------------------------------------------------------------------
# 2. hypotheses precede results
# ---------------------------------------------------------------------------

def check_experiments() -> None:
    exp_dir = REPO / "experiments"
    if not exp_dir.is_dir():
        return
    log_p = REPO / "doc" / "experiment-log.md"
    log = log_p.read_text() if log_p.exists() else None
    if log is None:
        fail("experiment-log", "doc/experiment-log.md is missing",
             "create it: `**KIND: TODO/log**` plus a table with one row per "
             "experiment directory (# | technique | paper(s) | verdict | IRN | power) "
             "-- the log is the index humans and agents trust")
    for d in sorted(exp_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        readme = d / "README.md"
        if not readme.exists():
            fail("experiment", f"{d.name} has no README.md",
                 "copy experiments/_template/README.md and fill "
                 "Paper(s)/Hypothesis/Verdict -- hypotheses precede results")
            continue
        txt = readme.read_text()
        for row in ("Paper", "Hypothesis", "Verdict"):
            if f"**{row}" not in txt:
                fail("experiment", f"{d.name}/README.md lacks a **{row}** row",
                     "every experiment states paper handle(s), a falsifiable "
                     "hypothesis, and (eventually) a verdict -- see "
                     "experiments/_template/README.md")
        if log is not None and d.name not in log:
            fail("experiment-log", f"{d.name} not listed in doc/experiment-log.md",
                 "add its one-line row (verdict or IN PROGRESS) -- the log is the "
                 "index humans and agents trust")


# ---------------------------------------------------------------------------
# 3. no untriaged paper is invisible
# ---------------------------------------------------------------------------

def check_paper_index() -> None:
    idx_p = REPO / "pdf" / "INDEX.md"
    pdfs = sorted((REPO / "pdf").glob("paper*.pdf"))
    if not idx_p.exists():
        if pdfs:
            fail("paper-index", "pdf/INDEX.md is missing",
                 "recreate the 5-column table `| `handle` | file | content / "
                 "innovation | usable here for | status |` -- it is the agent entry "
                 "point for paper retrieval and scripts/context_pack.py parses it")
        return
    idx = idx_p.read_text()
    for p in pdfs:
        if p.name not in idx:
            fail("paper-index", f"{p.name} missing from pdf/INDEX.md",
                 "add a row (handle, one-line innovation, usable-for, status) -- "
                 "INDEX.md is the agent entry point for paper retrieval; mark it "
                 "'untriaged' if not yet read")


# ---------------------------------------------------------------------------
# 4. journal folder discipline: indexed, typed, small enough for a context
# ---------------------------------------------------------------------------

MEMORY_DIRS = ("doc/journal", "doc/memory/semantic", "doc/memory/procedural")
SIZE_CAP = 20000


def check_journal() -> None:
    idx_p = REPO / "doc" / "journal.md"
    idx = idx_p.read_text() if idx_p.exists() else None
    entries = [p for rel in MEMORY_DIRS for p in sorted((REPO / rel).glob("*.md"))
               if p.name != "README.md"]
    if idx is None and entries:
        fail("journal", "doc/journal.md (the index) is missing",
             "create it: a table `| date | entry | type | status | hook |` with one "
             "row per file in doc/journal/ and doc/memory/* -- the index is what "
             "agents scan, and an unindexed entry is invisible")
    for p in entries:
        rel = p.relative_to(REPO)
        head = p.read_text()[:400]
        if idx is not None and p.name not in idx:
            fail("journal", f"{rel} missing from the index doc/journal.md",
                 "add its one-line row (date | entry | type | status | hook) -- the "
                 "index is what agents scan; unindexed entries are invisible")
        if not re.search(r"type: (semantic|procedural)", head):
            fail("journal", f"{rel} lacks a 'type: semantic|procedural' header line",
                 "add `KIND: journal entry | type: <t> | status: live` as the line "
                 "after the title -- the memory model (doc/memory/README.md) keys on "
                 "it, and scripts/context_pack.py drops the first three lines when it "
                 "builds an entry's summary")
        if not re.match(r"#\s+\d{4}-\d{2}-\d{2}", head):
            fail("journal", f"{rel} has no `# YYYY-MM-DD — title` H1 first line",
                 "entry files start with an H1 whose first token is the ISO date; "
                 "scripts/context_pack.py orders lessons newest-first by that date "
                 "and prints the rest of the line as the entry title")
    for p in entries + ([idx_p] if idx is not None else []):
        if p.stat().st_size > SIZE_CAP:
            fail("journal", f"{p.relative_to(REPO)} exceeds {SIZE_CAP // 1000} KB",
                 "split it: entries stay single-topic; move overflow to "
                 "doc/memory/semantic|procedural/ (owner rule: every memory surface "
                 "must fit an agent context)")


# ---------------------------------------------------------------------------
# 5. code and human spec cannot drift
# ---------------------------------------------------------------------------

def _spec_from_source() -> dict:
    """lab.metrics.SPEC read with `ast` -- no numpy, no import side effects."""
    tree = ast.parse((REPO / "lab" / "metrics.py").read_text())
    for node in tree.body:
        tgt = (node.target if isinstance(node, ast.AnnAssign) else
               (node.targets[0] if isinstance(node, ast.Assign) else None))
        if isinstance(tgt, ast.Name) and tgt.id == "SPEC":
            return ast.literal_eval(node.value)
    raise KeyError("SPEC not found in lab/metrics.py")


def _tokens(spec: dict) -> list[tuple[str, str]]:
    """Every load-bearing number of the acceptance box, as a literal token.

    Cheap substring tests on purpose ('40' also matches '340'); the point is that
    a bound cannot be changed in code without the human spec being touched too.
    """
    out, seen = [], set()
    for key, (label, op, bound) in spec.items():
        val = (bound[0] + bound[1]) / 2 if op == "in" else abs(bound)
        tok = f"{val:g}"
        if tok not in seen:
            seen.add(tok)
            out.append((tok, f"{key} ({label.split(':')[0]})"))
    return out


def check_spec_sync() -> None:
    """The numbers agents act on live in lab.metrics.SPEC; the human contract in
    doc/target-spec.md.  They must agree on every load-bearing constant."""
    spec_p = REPO / "doc" / "target-spec.md"
    if not spec_p.exists():
        fail("spec-sync", "doc/target-spec.md is missing",
             "recreate the `**KIND: SPEC**` S1-S8 table (# | requirement | target | "
             "reference baseline | checked by); lab.metrics.SPEC is its machine twin "
             "and this lint diffs the two")
        return
    spec = spec_p.read_text()
    try:
        code = _spec_from_source()
    except Exception as exc:                                   # noqa: BLE001
        fail("spec-sync", f"cannot read SPEC out of lab/metrics.py: {exc!r}",
             "lab.metrics.SPEC must stay a literal dict {key: (label, op, bound)} so "
             "the lint can read it without importing the simulator stack")
        return
    flat = spec.replace("**", "")
    for tok, where in _tokens(code):
        if tok not in flat:
            fail("spec-sync", f"{where} bound '{tok}' is in lab/metrics.py but not in "
                              f"doc/target-spec.md",
                 "keep lab.metrics.SPEC and the target-spec table in sync -- edit both "
                 "in the same change")
    goal = code.get("irn_uv", (None, None, None))[2]
    if goal is not None and f"< {goal:g} µV" not in flat:
        fail("spec-sync", f"S5 goal {goal:g} µVrms has no matching '< {goal:g} µV' in "
                          f"doc/target-spec.md",
             "update the target-spec S5 row (or revert the lab/metrics.py change) -- "
             "the goal is the headline of the challenge and must read identically in "
             "both places")
    ref = _reference_scorecard()
    if ref and f"{ref['irn_uv']:.2f}" not in flat:
        fail("spec-sync", f"the certified reference IRN {ref['irn_uv']:.2f} µVrms is "
                          f"absent from doc/target-spec.md",
             "the spec table's 'reference baseline' column quotes "
             "decks/reference/scorecard.json; re-run `python scripts/baseline.py "
             "--check` and copy the certified numbers across")


def _reference_scorecard() -> dict:
    try:
        return json.loads((REPO / "decks" / "reference" / "scorecard.json")
                          .read_text())["scorecard"]
    except Exception:                                          # noqa: BLE001
        return {}


# ---------------------------------------------------------------------------
# 6. no proprietary-node references anywhere in the tree
# ---------------------------------------------------------------------------
# This repo is the OPEN port of a campaign that ran on a proprietary foundry
# node with a commercial simulator and schematic editor.  Nothing here may name
# any of it: the prior work is referred to only as "the originating campaign" /
# "the originating design", with NO technology identified.  The list is a
# module-level constant so it is auditable in one place; scripts/lint.py is the
# only file exempt from the scan (it necessarily contains every pattern).
FORBIDDEN: tuple[tuple[str, int, str], ...] = (
    (r"tsmc",                  re.I, "originating foundry name"),
    (r"\b65\s*nm\b",           re.I, "originating node length"),
    (r"\bspectre\b",           re.I, "originating simulator"),
    (r"\bvirtuoso\b",          re.I, "originating schematic editor"),
    (r"\bcadence\b",           re.I, "originating EDA vendor"),
    (r"\bskill\b",             re.I, "originating scripting language"),
    (r"\bmaestro\b",           re.I, "originating ADE tool"),
    (r"\bpsf\b",               re.I, "originating result format"),
    (r"\b[np]ch_25\b",         0,    "originating device names"),
    (r"\brppolywo\b",          re.I, "originating resistor model"),
    (r"\bCMC\b",               0,    "originating kit vendor tag"),
    (r"/CMC/kits",             re.I, "originating PDK install path"),
    (r"Tapeout_1_Filter",      re.I, "originating library name"),
    (r"Filter_Test_Bench",     re.I, "originating cell name"),
    (r"Super_Source_Follower", re.I, "originating cell name"),
)

SCRUB_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "runs", "node_modules",
                   ".ruff_cache", ".mypy_cache", ".pytest_cache", ".idea"}
SCRUB_SKIP_SUFFIX = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".npz", ".npy",
                     ".raw", ".gz", ".zip", ".pyc", ".so", ".dylib", ".lock"}
SCRUB_SKIP_FILES = {"lint.py"}          # this file defines the patterns


def check_no_proprietary_node() -> None:
    pats = [(re.compile(p, f), why) for p, f, why in FORBIDDEN]
    hits: list[str] = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SCRUB_SKIP_DIRS]
        for name in sorted(files):
            p = Path(root) / name
            if name in SCRUB_SKIP_FILES or p.suffix.lower() in SCRUB_SKIP_SUFFIX:
                continue
            try:
                text = p.read_text()
            except (OSError, UnicodeDecodeError):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                for rx, why in pats:
                    m = rx.search(line)
                    if m:
                        hits.append(f"{p.relative_to(REPO)}:{n}: "
                                    f"{m.group(0)!r} ({why})")
    if hits:
        shown = "\n    ".join(hits[:20])
        more = f"\n    ... and {len(hits) - 20} more" if len(hits) > 20 else ""
        fail("node-scrub",
             f"{len(hits)} proprietary-node reference(s) in the tree:\n    {shown}{more}",
             "delete the reference. Refer to the prior work only as 'the originating "
             "campaign' / 'the originating design' / 'prior art carried forward', with "
             "NO technology identified, and mark any number that came from it as "
             "carried forward rather than as a measurement of this repo. The pattern "
             "list is FORBIDDEN in scripts/lint.py")


# ---------------------------------------------------------------------------
# 7. generated artefacts never enter git
# ---------------------------------------------------------------------------

GITIGNORE_MUST = (
    ("runs/", "the run ledger is local observability; keeper numbers graduate into "
              "experiment READMEs"),
    ("*.raw", "ngspice rawfiles are large binary artefacts, regenerated by any run"),
    ("__pycache__/", "bytecode is not a deliverable"),
    ("experiments/*/out/", "per-experiment scratch output"),
)


def check_gitignore() -> None:
    p = REPO / ".gitignore"
    if not p.exists():
        fail("gitignore", ".gitignore is missing",
             "recreate it with at least: " + ", ".join(x for x, _ in GITIGNORE_MUST))
        return
    lines = {ln.strip() for ln in p.read_text().splitlines()}
    for pat, why in GITIGNORE_MUST:
        if pat not in lines:
            fail("gitignore", f"'{pat}' is not ignored",
                 f"add `{pat}` to .gitignore -- {why}")


# ---------------------------------------------------------------------------
# 8. the reference deck is never edited in the working tree
# ---------------------------------------------------------------------------

def check_reference_clean() -> None:
    """Uncommitted edits under decks/reference/ are caught before they spread.

    Untracked ('??') paths are NOT a failure: a not-yet-committed reference is
    the normal state right after it is frozen, and an unrecorded file there is
    already caught by the hash manifest in check_reference_deck.  What this
    catches is a MODIFIED or DELETED certified file.
    """
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "decks/reference"],
                           cwd=REPO, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return                       # not a git checkout: nothing to assert
    dirty = [ln for ln in r.stdout.splitlines() if ln.strip()
             and not ln.startswith("??")]
    if r.returncode == 0 and dirty:
        fail("reference-clean",
             "the certified reference bench has local changes:\n    "
             + "\n    ".join(dirty),
             "decks/reference/ is a read-only certified artefact; revert with "
             "`git checkout -- decks/reference` and do design work in your own "
             "experiment (experiments/NNN-*/), building decks through lab.deck")


# ---------------------------------------------------------------------------
# 9. the working-memory pack must actually retrieve
# ---------------------------------------------------------------------------
# Run the real tool rather than re-implementing its parsers here: a doc whose
# structure the pack cannot parse is INVISIBLE to every agent, and it fails
# silently (an empty section, not an error).
PACK_SECTIONS = (
    ("Constraints", "doc/design-reference.md needs a `## ...constraints every "
                    "candidate must respect` (or `## Facts that constrain...`) "
                    "section whose items are either a `1.`-numbered list at column "
                    "0 or `**Cn — ...**` bold-labelled paragraphs -- see "
                    "CONSTRAINT_HEAD / CONSTRAINT_ITEMS in scripts/context_pack.py"),
    ("Papers", "pdf/INDEX.md data rows must start with '| `handle`' and carry at "
               "least 4 columns (handle | file | innovation | usable-for | status)"),
    ("Lessons", "doc/journal/ needs at least one live entry: `# YYYY-MM-DD — title`, "
                "blank line, `KIND: journal entry | type: <t> | status: live`, body"),
)


def check_context_pack() -> None:
    cmd = [sys.executable, str(REPO / "scripts" / "context_pack.py")]
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as exc:
        fail("context-pack", f"could not run scripts/context_pack.py: {exc!r}",
             "the context pack is the agent's working memory; it must run from a "
             "bare checkout with `python scripts/context_pack.py`")
        return
    if r.returncode != 0:
        tail = "\n    ".join((r.stderr or r.stdout).strip().splitlines()[-6:])
        fail("context-pack", f"scripts/context_pack.py exited {r.returncode}:\n    {tail}",
             "retrieval must never be the thing that fails a task -- a missing "
             "source degrades to an empty section, never to a traceback")
        return
    for name, fix in PACK_SECTIONS:
        # Section headers carry their item count and their provenance path, in
        # either order: "(doc/design-reference.md — 7)" / "(10 matching — pdf/…)".
        head = re.search(rf"^## {name} \(([^)]*)\)", r.stdout, re.M)
        m = re.search(r"\d+", head.group(1)) if head else None
        if not head:
            fail("context-pack", f"the pack printed no '## {name}' section",
                 "scripts/context_pack.py:render() emits a fixed section order "
                 "(Spec frame, Constraints, Papers, Lessons, Episodes); restore it")
        elif m is None or int(m.group(0)) == 0:
            fail("context-pack", f"the pack retrieved 0 {name.lower()}", fix)


# ---------------------------------------------------------------------------

CHECKS = (check_reference_deck, check_deck_rebuild, check_reference_clean,
          check_experiments, check_paper_index, check_journal, check_spec_sync,
          check_no_proprietary_node, check_gitignore, check_context_pack)


def main() -> int:
    for c in CHECKS:
        try:
            c()
        except Exception as exc:                               # noqa: BLE001
            # A lint that crashes teaches nothing.  Report the crash as a
            # failure of that check and keep the other checks running.
            fail(c.__name__, f"the check itself raised {exc!r}",
                 "this is a harness bug: fix scripts/lint.py (or the file it was "
                 "reading) so the invariant can be evaluated")
    if FAILS:
        print(f"LINT: {len(FAILS)} failure(s)\n")
        print("\n\n".join(FAILS))
        return 1
    print("LINT: all harness invariants hold (reference deck, deck rebuild, "
          "reference clean, experiments, paper index, journal, spec sync, "
          "node scrub, gitignore, context pack)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
