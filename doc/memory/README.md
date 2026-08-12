# The memory model

KIND: REFERENCE

Theory anchor: **CoALA** (*Cognitive Architectures for Language Agents*,
arXiv:2309.02427), as distilled in the workspace plan
`spicexplorer-workspace/doc/plan_harness_engineering.md` §4e. This repo is the
working prototype of that plan: four memory tiers, each with a physical home in
the repo, a declared writer, and a declared write risk.

The governing constraint, which everything else on this page is a consequence
of:

> **No memory surface may grow past what fits comfortably in an agent context.**

One-file-per-entry, small lint-enforced indexes, 20 KB caps, and the
`doc/memory/**` overflow tiers all exist to satisfy that one rule. A memory you
cannot load is not a memory.

---

## 1. Storage layout

| surface | path | what lives there |
|---|---|---|
| journal entries | `doc/journal/` | dated lessons, **one file each**; header line carries `type: semantic \| procedural` and `status: live \| superseded` |
| journal index | `doc/journal.md` | one line per entry, **lint-enforced complete**; the hook column carries the numbers |
| semantic overflow | `doc/memory/semantic/` | *undated* distilled knowledge that outgrows a journal entry or a `doc/design-reference.md` bullet (a device-behaviour study, a topology trade map). **Provenance required.** |
| procedural overflow | `doc/memory/procedural/` | *undated* recipes/checklists (multi-step flows: a corner/Monte-Carlo run recipe, the xschem→netlist→verify loop) that outgrow `doc/environment.md` |
| episodic log | `runs/ledger.ndjson` | one NDJSON row per simulation. **Gitignored**, append-only, machine-written |
| curated authoritative docs | `doc/design-reference.md` (core semantic facts), `doc/environment.md` (core procedural gotchas), `doc/benches.md` (what certifies what), `doc/target-spec.md` (the spec), `doc/pdk-notes.md` (measured device data), `pdf/INDEX.md` (paper knowledge) | these **stay authoritative** |

`doc/memory/semantic/` and `doc/memory/procedural/` are the **overflow tier, not
a replacement** for the curated docs. A fact's first home is the curated doc or
a journal entry; it moves into an overflow file only when it needs more room
than either can give without breaking the size rule.

### Filenames: slug, not date-prefix (deviation from the originating campaign)

The originating campaign named entries `YYYY-MM-DD-<slug>.md` and got recency
ordering for free from a reverse-lexicographic sort. **Here entries are named
`<slug>.md`** — because `lab/` cites them from code:

| citation | file |
|---|---|
| `doc/journal/phase-certificate-floor.md` | `lab/metrics.py:53`, `lab/raw.py:241` |
| `doc/journal/nmos-bulk-tie.md` | `lab/dut.py:39` |
| `doc/journal/all-p-followers.md` | `lab/config.py:89`, `lab/dut.py:171` |
| `doc/journal/mirror-unit-must-match.md` | `lab/deck.py:44` |
| `doc/journal/nodeset-not-ic.md` | `lab/deck.py:67` |

A date in the filename would rot every one of those cross-references the moment
an entry is re-dated or superseded. The date therefore lives **in the title
line and in the index's date column**, and recency ordering is taken from the
title-line date, not the filename. Everything else about the entry format is
unchanged.

---

## 2. The four tiers, as instantiated here

| tier | what it is here | written by | retrieval |
|---|---|---|---|
| **working** | typed variables for the current task; each prompt serializes a subset | assembled fresh by retrieval; updated by every sim verdict | `python scripts/context_pack.py <keywords>` (`make pack K="..."`) → spec frame, constraints, matching papers, lessons, episodes |
| **episodic** | raw experience, append-only: `runs/ledger.ndjson` (every `evaluate()` / THD / corner / Monte-Carlo run — metrics, deck hash, corner, temp, lane, host, wall time, violations, `goal_met`, `LPF_EXP`) + the experiment dirs | **mechanical, automatic** — `lab/ledger.py:log_run`. A gated procedure, not free-form prose | `scripts/runs.py` (`make runs`), or the context pack's episodes section |
| **semantic** | distilled knowledge, provenance-linked: `doc/journal.md` + `doc/journal/` (lessons), `doc/design-reference.md` (constraints), `doc/pdk-notes.md` (measured device data), `pdf/INDEX.md` (paper knowledge), experiment READMEs (verdicts) | **distillation at close-out** (or immediately on a surprising failure) | the context pack's lessons/constraints/papers slots; direct read of the curated docs |
| **procedural** | the code that implements actions and decisions; **human-initialized**: `lab/`, `scripts/`, `xschem/`, `Makefile`, the lints, the agent definitions in `.claude/agents/`, and `CLAUDE.md` | **trap→gate promotion, human-reviewed only** | the harness-commands section of `CLAUDE.md` |

**Working-memory retrieval policy** (load-bearing, and stated twice on purpose —
here and in the `scripts/context_pack.py` docstring): run the pack **at task
start, and re-run it keyed on every new symptom** (`--symptom "…"`).

> Retrieval is an ACTION with a policy, not a one-shot preamble.

**Episodic discipline.** `runs/` is gitignored. The ledger is *local
observability*, not a deliverable: numbers that matter **graduate** into an
experiment README or `doc/experiment-log.md`, and that promotion is the semantic
write. **The repo is the memory; the ledger is the flight recorder.** Never
hand-edit the ledger — a hand-edited flight recorder is not evidence. A later
contradicting row **revokes** an earlier sign-off; nothing is deleted to make
that happen.

*Known gap, standing:* `lab/ledger.py:log_run` writes its row without an
exception guard, so an unwritable `runs/` would fail the measurement it is only
supposed to observe. Wrapping it (`except Exception: pass` —
"observability must not break the run it observes") is a **procedural** write
and therefore belongs in `doc/proposed-lab-fixes.md` for owner review, not in an
agent's edit.

---

## 3. Learning actions — what writes what

1. **experience → episodic.** Automatic. Every simulation appends one schema'd
   row. Nobody has to remember to log. **Never hand-edit the ledger.**
2. **distillation → semantic.** Deliberate, at experiment close-out *or the
   moment a failure surprises you*: read the episodes, then write the journal
   entry / curated-doc bullet **with provenance** — ledger tags, experiment
   dir, deck hash, paper equation or figure numbers. A claim with no pointer
   back to an episode is an opinion.
3. **new code → procedural.** Gap-as-signal promotion: a trap that recurs
   becomes a lint, a `lab/` helper, or a deck-builder invariant. This is the
   **highest-risk tier** — it lands only as a human-reviewed change. An agent
   proposes the diff; it never self-applies edits to `lab/`, `scripts/`,
   `xschem/`, agent definitions, or `CLAUDE.md` — **and no agent ever edits its
   own decision procedures.**

---

## 4. Write-risk ordering

> **episodic (automatic, zero review) → semantic (agent-written; provenance +
> supersede-don't-delete) → procedural (human-reviewed only).**

This is restated verbatim as `CLAUDE.md` rule 10, and every agent contract in
`.claude/agents/` repeats the same three sentences: episodic writes are
automatic; semantic writes require provenance and use supersede-don't-delete;
procedural writes are proposed as diffs and never self-applied.

Related enforcing rules in `CLAUDE.md`:

* **gap-as-signal** — if you struggle (missing tool, missing doc, missing check,
  a trap hit twice), do not push through: fix the harness *and* record it as a
  `doc/journal/` entry plus its index line.
* **designer ≠ verifier** — delivery claims are re-measured independently from
  raw artifacts by the sign-off verifier, never quoted from the designer's run.
* **sim economy** — expensive runs (THD, corners, Monte Carlo) only after the
  cheap ac+noise scorecard passes (`lab.metrics.gate`).

### How the human-review rule shows up in practice

Three mechanisms, all three in use:

1. **A flag line ends the entry.** Any procedural journal entry that proposes a
   `lab/` or `scripts/` change ends with:
   `Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10.`
2. **A standing review queue exists.** `doc/proposed-lab-fixes.md`
   (`KIND: TODO (owner review)`) is the destination for every agent-proposed
   procedural diff: the defect, the ledger evidence that exposed it, the diff,
   what it changes about what "sign-off" means, and a `PENDING` /
   `APPLIED (owner-authorized <date>)` marker.
3. **Applied writes are stamped.** When a procedural change *is* applied, the
   row in `doc/experiment-log.md` (and the entry) says
   **APPLIED (owner-authorized)** — so the audit trail shows who authorized the
   harness to change its own behaviour.

"Proposed for graduation" is itself a legitimate state: an analysis script that
lives in `experiments/NNN-*/` and is *proposed* for promotion into `lab/` stays
where it is until an owner moves it.

---

## 5. Unlearning — supersede, don't delete

Semantic entries are **retired by supersession, never silently deleted.**
Retiring an entry is a **three-place edit**, and all three are required:

1. Entry file **line 3** flips to `… | type: <t> | status: superseded`.
2. The bracket note lands **immediately after that line**, i.e. as the first
   line of the body: `[superseded <date> — see <entry/section>]`. It must fall
   inside the **first 400 characters** of the file, because that is the window
   the retrieval filter reads.
3. The **index row's status cell** in `doc/journal.md` flips to
   `**superseded**`.

The context pack serves only non-superseded entries. The gardener sweep flags
contradictions that lack a supersession marker, and flags any entry that has
`[superseded` in its body but is missing either of the other two edits (the
three-place edit is manual and easy to half-do).

**Partial supersession is supported and expected.** Retire the *claim that
died*, not the whole entry, and say exactly which claim it was: an entry whose
verdict is overtaken but whose *mechanism* still holds should re-home the
mechanism into `doc/design-reference.md` and mark only the verdict superseded.

Supersession also runs **across surfaces**: when a measurement here corrects a
paper's premise, the `pdf/INDEX.md` row is struck through in place
(`~~old claim~~ **CORRECTED by <exp> (measured)** …`) and its status cell says
so. `pdf/INDEX.md` already carries one such row (`ssf-33mhz`).

> **If you disprove an entry, marking it is part of the fix — a stale lesson is
> worse than none.**

---

## 6. The decision cycle

> propose (reason + retrieve via the context pack) → **evaluate by ngspice**
> (`.control` deck → rawfile → scorecard) → select → **the ledger row is the
> observation that closes the loop.**

Fast lab metrics iterate the cycle; the frozen reference bench and the
long-transient sign-off methods certify the exit (`doc/benches.md`). This is why
the repo needs no formal agent machinery: **SPICE is the environment and the
ledger row is the observation.** A proposal that has not produced a ledger row
has not been evaluated, whatever the reasoning around it looked like.

---

## 7. Blast radius — keeping parallel work from clobbering shared memory

* **One experiment = one session = one git worktree**, on `feat/NNN-*`.
* Simulation space is namespaced automatically:
  `WORK = /tmp/lpf_work-{repo.name}-{sha1(repo path)[:6]}` (`lab/config.py`), and
  `runs/ledger.ndjson` is repo-relative, so the ledger is per-worktree too.
* `LPF_EXP` stamps every ledger row (`lab/ledger.py`), queryable with
  `scripts/runs.py --exp NNN`.
* **Shared docs stay conflict-free by staging:** lessons live in the
  experiment's own README first and **graduate** to `doc/journal.md` /
  `doc/experiment-log.md` / `pdf/INDEX.md` at close-out. That is the anti-clobber
  rule for shared memory surfaces.
* Delivered schematics are plain files under `experiments/NNN-*/`, so no
  shared-tool lock is needed; namespace cells by experiment id.

---

## 8. Enforcement

`scripts/lint.py check_journal`, over every `doc/journal/*.md`:

1. **indexed** — the filename must appear in `doc/journal.md`.
   FIX: *add its one-line row (date | entry | type | status | hook) — the index
   is what agents scan; unindexed entries are invisible.*
2. **typed** — `re.search(r"type: (semantic|procedural)", head)` over the first
   400 bytes. FIX: *add `type: <t> | status: live` on the line after the title —
   the memory model (doc/memory/README.md) keys on it.*
3. **size** — every entry **and** `doc/journal.md` ≤ 20 000 bytes. FIX: *split
   it: entries stay single-topic; move overflow to
   `doc/memory/semantic|procedural/` — every memory surface must fit an agent
   context.*
4. **sorted** — index rows newest-first.
5. **supersession complete** — an entry containing `[superseded` must also carry
   `status: superseded` on line 3 **and** a `**superseded**` status cell in the
   index.

Design principle for every lint in this repo: *a doc that fails to change
behaviour gets promoted to a linter, and the failure message itself teaches the
remediation.* Exit 1 on any failure.
