#!/usr/bin/env python3
"""Context pack -- the agent's WORKING MEMORY, assembled by retrieval.

CoALA-informed: a typed, per-task variable store serialized fresh for each task,
built by deterministic grep-based retrieval over the repo's memory tiers:

  * episodic   runs/ledger.ndjson                    (raw trial records)
  * semantic   doc/journal/, doc/memory/{semantic,procedural}/,
               doc/design-reference.md, pdf/INDEX.md (distilled)
  * spec       lab.metrics constants + decks/reference/scorecard.json
               (the acceptance box and the number to beat)

Retrieval is an ACTION with a policy, not a one-shot preamble: run this at task
start with topic keywords, and RE-RUN it keyed on new symptoms mid-task
(`--symptom 'peaking after cap swap'`) BEFORE diagnosing from scratch.  The same
policy is restated in doc/memory/README.md and in CLAUDE.md; the redundancy is
deliberate harness design.

    python scripts/context_pack.py noise irn            # topic keywords
    python scripts/context_pack.py --symptom "fc drifted after cap fit"
    python scripts/context_pack.py thd --json           # typed dict output

Matching is raw case-insensitive SUBSTRING matching over whole file text -- not
tokenized, not stemmed, no embeddings.  Determinism and greppability are the
design: the same keywords always return the same pack, and any agent can predict
what a keyword will hit.  No keywords => everything matches.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import ledger, metrics          # noqa: E402  -- the ONLY two lab deps

SUPERSEDED = re.compile(r"\[superseded", re.I)

# The certified reference scorecard: measured in THIS repo on the frozen deck
# (decks/reference/), not carried forward from the originating campaign.
REFERENCE_JSON = REPO / "decks" / "reference" / "scorecard.json"

# Memory tiers the `lessons` builder walks, newest file first within each.
LESSON_DIRS = ("doc/journal", "doc/memory/semantic", "doc/memory/procedural")

EPISODE_KEYS = ("tag", "kind", "irn_uv", "fc_hz", "thd_db", "violations")


def _match(text: str, words) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def _read(rel: str) -> str:
    """Text of a repo-relative file, or '' if it is not in this checkout.

    Missing sources degrade to an empty section rather than a traceback -- the
    pack is a retrieval tool and must never be the thing that fails a task.
    """
    p = REPO / rel
    try:
        return p.read_text()
    except OSError:
        return ""


def reference() -> dict:
    """The measured reference scorecard, or {} before it is certified."""
    try:
        return json.loads(REFERENCE_JSON.read_text()).get("scorecard", {})
    except (OSError, ValueError):
        return {}


# ------------------------------------------------------------------- sections

def _spec_line(label: str, op: str, bound) -> str:
    if op == "in":
        return f"{label} in [{bound[0]:g}, {bound[1]:g}]"
    if op == "abs<=":
        return f"|{label}| <= {bound:g}"
    return f"{label} {op} {bound:g}"


def spec_frame() -> dict:
    """The acceptance box, straight out of lab.metrics -- no file I/O."""
    ref = reference()
    goal = metrics.SPEC.get("irn_uv", (None, None, float("nan")))[2]
    lo, hi = metrics.IRN_BAND
    return {
        "goal": f"IRN({lo:g}-{hi:g} Hz) < {goal:g} uVrms "
                f"(reference {ref.get('irn_uv', float('nan')):g} uVrms, measured here), "
                f">=2 papers combined",
        "hard_spec": [_spec_line(*v) for v in metrics.SPEC.values()],
        "soft_spec": list(metrics.SOFT),
        "thd_spec": f"<= {metrics.THD_LIMIT_DB:g} dB @ {metrics.THD_AMPL * 2e3:g} mVpp "
                    f"differential @ fin = {metrics.THD_FIN:g} Hz; sign-off = an "
                    f"independent long-transient DFT re-measure from the raw artefacts, "
                    f"NOT the fast strobed FFT used for iteration; expensive sims are "
                    f"gated on the cheap box (lab.metrics.gate)",
        "reference": ref,
    }


# Structural contract on doc/design-reference.md, enforced by scripts/lint.py
# (check_context_pack): a `## ` heading naming the constraints, whose body is
# EITHER a `1.`/`2.`/... ordered list at column 0 OR `**Cn — ...**` bold-labelled
# paragraphs.  The trailing `\Z` alternative matters: without it a constraints
# section that is the LAST section of the file silently yields nothing.
CONSTRAINT_HEAD = re.compile(
    r"## [^\n]*(?:Facts that constrain|constraints every candidate)[^\n]*"
    r".*?(?=\n## |\Z)", re.S | re.I)
CONSTRAINT_ITEMS = (r"^\d+\.\s+(.*?)(?=^\d+\.|\Z)",          # 1. 2. 3.
                    r"^(\*\*C\d+.*?)(?=^\*\*C\d+|\Z)")       # **C0 — ...**


def constraints() -> list[str]:
    """The hard-won constraints from doc/design-reference.md.

    NOT keyword-filtered: these are always carried in full (truncated only at
    render), because every one of them has already cost someone a round of
    simulations.  Items are whitespace-collapsed into one line each, so put the
    load-bearing claim FIRST in each item -- the render cuts at 220 chars.
    """
    m = CONSTRAINT_HEAD.search(_read("doc/design-reference.md"))
    if not m:
        return []
    for pat in CONSTRAINT_ITEMS:
        found = re.findall(pat, m.group(0), re.S | re.M)
        if found:
            return [" ".join(c.split()) for c in found]
    return []


def papers(words) -> list[dict]:
    """Matching rows of pdf/INDEX.md.

    Contract: data rows begin with '| `' (a backticked handle) and have >= 4
    columns, ordered handle | file | innovation | usable-here-for | status.
    The whole line is matched, so file names and status text are searchable too.
    """
    out = []
    for line in _read("pdf/INDEX.md").splitlines():
        if line.startswith("| `") and (not words or _match(line, words)):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 4:
                out.append({"handle": cols[0].strip("`` "),
                            "innovation": cols[2], "usable_for": cols[3]})
    return out


def _entry_date(p: Path, txt: str) -> str:
    """The entry's date, for newest-first ordering.

    The originating repo encoded the date in the FILENAME (`YYYY-MM-DD-slug.md`)
    and got newest-first from a reverse lexicographic sort.  Here entries are
    named by slug (`nmos-bulk-tie.md`) because lab/ source comments point at them
    by name, so the date is read from the H1 title line instead -- same ordering
    guarantee, one less thing that breaks when an entry is renamed.
    """
    m = re.search(r"\d{4}-\d{2}-\d{2}", (txt.splitlines() or [""])[0]) \
        or re.match(r"\d{4}-\d{2}-\d{2}", p.name)
    return m.group(0) if m else "0000-00-00"


def lessons(words) -> list[dict]:
    """The semantic tier: one entry = one file, newest first, live entries only.

    One entry = one file so that any single entry fits an agent context (the
    reason for the split; see doc/memory/README.md).  An entry is dropped if its
    first 400 characters carry `status: superseded` or a `[superseded ...]`
    marker -- supersede, never delete.  Matching is against the WHOLE file text,
    so retrieval hits body content, not just titles.
    """
    out = []
    for rel in LESSON_DIRS:
        found = []
        for p in sorted((REPO / rel).glob("*.md")):
            if p.name == "README.md":
                continue
            txt = p.read_text()
            found.append((_entry_date(p, txt), p.name, p, txt))
        for _, _, p, txt in sorted(found, key=lambda e: (e[0], e[1]), reverse=True):
            head = txt.splitlines()[0].lstrip("# ").strip()
            if "status: superseded" in txt[:400] or SUPERSEDED.search(txt[:400]):
                continue
            if not words or _match(txt, words):
                out.append({"entry": head,
                            "file": str(p.relative_to(REPO)),
                            "summary": " ".join(txt.split("\n", 3)[-1].split())[:300]})
    return out


def episodes(words, n: int = 10) -> list[dict]:
    """The episodic tier: the last `n` matching ledger rows, oldest first.

    All kinds are searched (evaluate AND thd AND corner batches) -- a symptom
    query about distortion must be able to reach a THD row -- so `kind` is
    printed alongside the tag rather than filtered out.
    """
    rows = ledger.read()
    if words:
        rows = [r for r in rows
                if _match(" ".join([r.get("tag", ""), r.get("kind", ""),
                                    r.get("topology", ""), r.get("exp", ""),
                                    *(r.get("violations") or [])]), words)]
    return rows[-n:]


def build(words) -> dict:
    """The typed working-memory record.  Key order is the render order."""
    return {"keywords": words, "spec": spec_frame(), "constraints": constraints(),
            "papers": papers(words), "lessons": lessons(words),
            "episodes": episodes(words)}


# -------------------------------------------------------------------- render

def render(pack: dict) -> None:
    p = pack
    print(f"# Context pack  (keywords: {', '.join(p['keywords']) or 'none'})\n")

    print("## Spec frame")
    print(f"- GOAL: {p['spec']['goal']}")
    for s in p["spec"]["hard_spec"]:
        print(f"- hard: {s}")
    for s in p["spec"]["soft_spec"]:
        print(f"- soft: {s}")
    print(f"- THD: {p['spec']['thd_spec']}")
    ref = p["spec"]["reference"]
    print("- reference: " + "  ".join(f"{k}={v}" for k, v in ref.items()))

    print(f"\n## Constraints (doc/design-reference.md — {len(p['constraints'])})")
    for c in p["constraints"]:
        print(f"- {c[:220]}")

    print(f"\n## Papers ({len(p['papers'])} matching — pdf/INDEX.md)")
    for r in p["papers"]:
        print(f"- `{r['handle']}`: {r['innovation'][:120]} || USE: {r['usable_for'][:140]}")

    print(f"\n## Lessons ({len(p['lessons'])} matching — doc/journal/ + doc/memory/)")
    for r in p["lessons"]:
        print(f"- {r['entry']}  [{r['file']}]: {r['summary'][:200]}")

    print(f"\n## Episodes ({len(p['episodes'])} matching — runs/ledger.ndjson)")
    for r in p["episodes"]:
        print("- " + "  ".join(f"{k}={r[k]}" for k in EPISODE_KEYS
                               if r.get(k) is not None))


STOP = ("the", "and", "after", "with", "for")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Assemble the working-memory context pack for a task.")
    ap.add_argument("keywords", nargs="*",
                    help="topic keywords; none => the whole pack")
    ap.add_argument("--symptom",
                    help="mid-task re-retrieval: symptom text is tokenized into "
                         "extra keywords")
    ap.add_argument("--json", action="store_true", help="typed dict output")
    a = ap.parse_args()

    words = [w.lower() for w in a.keywords]
    if a.symptom:
        words += [w for w in re.findall(r"[a-z]{3,}", a.symptom.lower())
                  if w not in STOP]
    pack = build(words)
    print(json.dumps(pack, indent=1, default=str)) if a.json else render(pack)


if __name__ == "__main__":
    main()
