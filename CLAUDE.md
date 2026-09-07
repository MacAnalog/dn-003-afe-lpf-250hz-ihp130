# CLAUDE.md — 250 Hz LPF design challenge (IHP SG13G2)

**Map, not manual.** This file routes; the docs below hold the substance.
Sessions usually run from `spicexplorer-workspace/`; every path here is
relative to this repo (`external/agentic-design-250hz-lpf-ihp130/`).

## Mission

Redesign a fully differential **4th-order 250 Hz super-source-follower
low-pass filter** in the open **IHP SG13G2** 130 nm BiCMOS PDK, at VDD = 1.5 V,
so that **IRN(0.5–200 Hz) < 40 µVrms** — down from the **50.18 µVrms** of the
certified reference baseline in `decks/reference/` (−20.3 %) — by **combining
techniques from ≥ 2 papers in `pdf/`**, while holding two true biquads
(ph_max ≥ 330°, |H|@1 kHz ≤ −48 dB), fc = 250 Hz ±2 %, |dc| ≤ 0.2 dB, peaking
≤ 0.2 dB, THD ≤ −40 dB at 175 mVpp differential at fin = 50 Hz, and
filter-core power < 50 nW. Total capacitance is **reported, never specced**.

The reference baseline is the yardstick, not a target to beat on every axis:
it is on spec, measured in this repo, and frozen. A candidate wins by cutting
IRN without giving anything else back.

## Read this before that

| you are about to… | read first |
|---|---|
| anything | `doc/target-spec.md` — S1–S8, pass/fail definitions |
| measure something | `doc/benches.md` — **reference-first policy**; the frozen measurement definitions are sign-off |
| touch the DUT / model it | `doc/design-reference.md` — device map, validated biquad `H(s)`, the constraints that kill naive ideas |
| pick a device / a length / a bias | `doc/pdk-notes.md` — measured gm/ID, gm/gds, leakage and gate-referred noise per flavour |
| pick a paper/technique | `pdf/INDEX.md` — per-paper innovation + cross-corpus map |
| run simulations | `lab/` module docstrings (the API) + `doc/environment.md` (lanes, ngspice/IHP gotchas) |
| start an experiment | copy `experiments/_template/`; log one row in `doc/experiment-log.md` |
| learn from / add a lesson | `doc/journal.md` (index) — entries are one file each in `doc/journal/`, typed semantic/procedural; supersede, don't delete |
| understand what to read/write when | `doc/memory/README.md` — the memory model (working/episodic/semantic/procedural) + write-risk ordering |
| draw or deliver a schematic | `xschem/README.md` — the schematic lane, its package rules, and the two identity gates |

## Harness commands

The generic half — ledger, lints, context pack, spec-as-data — is the platform's
`spicexplorer-harness` package, configured by **`harness.yaml`** (spec rows,
frozen dirs, denylist, ledger columns, env-var names); `lab/` and `scripts/`
hold only what is specific to this design.

- `uv sync` — create `.venv` (each git worktree needs its own; the harness is
  a path dependency on the sibling platform checkout, see `pyproject.toml`).
- `make pack K="<keywords>"` — assemble **working memory** for a task (spec
  frame, constraints, matching papers/lessons/episodes). Run at task start;
  **re-run with `S="<symptom>"`** on any new failure signature before
  diagnosing from scratch.
- `make doctor` (`python -m lab.ngspice`) — is the simulator lane alive? Prints
  lane (docker|native), PDK, and the plots a one-transistor `op` produced. A
  stock ngspice cannot run this PDK at all: IHP MOS devices are PSP 103.6
  Verilog-A models loaded as **OSDI** objects, and a build without them reports
  `Unknown model type psp103va`.
- `make lint` — repo invariants (reference-deck `SHA256SUMS`, deck rebuild,
  experiment structure, paper index, journal typing, `harness.yaml`↔spec-doc
  sync, no proprietary-node references). **Failure messages carry their own
  remediation.** Run after any doc or structure edit. `make freeze` re-writes
  the manifest after a deliberate re-certification.
- `make check` — lint + the reference deck still reproduces the certified
  scorecard within tolerance. This is what re-certifies the yardstick.
- `make baseline` — run the reference deck, print the scorecard.
- `make runs ARGS="--fails | --best irn_uv | --exp NNN | --kind thd | --where topology=b"` —
  query the run ledger (`runs/ledger.ndjson`; every `lab.metrics.evaluate()`
  call is auto-recorded with metrics, deck hash, wall time, violations).
- `make thd` — THD profile at 175 mVpp across passband fins (slow).
- `make clean` — remove this checkout's simulation work dirs.

## Simulation lanes and reuse (contract for every agent in this repo)

- **Open-source PDK (IHP SG13G2, sky130, gf180 …) → the open lane.** ngspice (with OSDI/openvaf models) through this repo's lane
  module (`design/sim.py` or its equivalent here), KLayout / magic / netgen / kpex for layout and sign-off, xschem for schematics — natively
  on the workstation; `make doctor` proves the lane. An open-PDK bench is never routed through the commercial tools.
- **Commercial PDK under NDA → the bridge lane only.** Those simulations run on the EDA server through the lab's
  remote-simulator bridge (the bridge submodule of the lab's shared agent library and its two simulator method definitions): decks are built here, uploaded by basename with *relative* `include`s,
  simulated there, and only results come back. Kit bytes never reach the workstation or the model (`pdk_guard`
  blocks it); every server-side artifact is design-named, never tool-named (`naming_guard`).
- **SpiceXplorer first.** Before writing a script, use what exists and compose it: the platform packages
  (`spicexplorer_core` — `spice_engine.run_deck`, measurements; `spicexplorer_harness` — ledger, pack, lint,
  spec; `spicexplorer-optimize`; `spicexplorer_gmid`; `spicexplorer_layout` + `spicexplorer_signoff`;
  `spicexplorer_waveview`; `spicexplorer_circuitgraph`; `spicexplorer_netlist2xschem`), the orchestration
  workflows and MCP tools (`spicexplorer_orchestration.workflows`: layout, sizing, campaign, sign-off,
  literature), and the reusable agents and method definitions in the lab's shared agent library (this repo's `.sx` submodule once its template migration lands). A missing function is added to the platform or the
  library by PR (gap-as-signal), never reimplemented privately in this repo.

## Rules (mechanically enforced where possible; the rest is contract)

1. **Reference first** — fast metrics iterate; the frozen definitions in
   `lab/metrics.py` (+ the long-window DFT THD path) certify. A number that has
   not passed through them is a claim, not a measurement.
2. **Decks are built, never text-edited.** A sizing point is a `lab.dut.Design`;
   every deck (ac+noise, op, THD, corner) is regenerated from it by `lab.deck`,
   so a scorecard can never mix one sizing's netlist with another's
   measurement. Never hand-edit `decks/reference/` — its sha is lint-pinned,
   and an edit invalidates every prior comparison.
3. Every experiment: **falsifiable hypothesis first**; the **re-allocation
   control** whenever caps move (otherwise you have measured a cap re-shuffle,
   not a technique); **stopband never traded silently**.
4. Findings are **tables or plots** (`lab.metrics.table`); prose is
   interpretation only. Keeper numbers graduate from the ledger into the
   experiment README — the repo is the memory.
5. **Parallelize netlist-lane batches** (`lab.parallel`, `LPF_JOBS`, default
   `cpu_count()-2`). ngspice is free and single-threaded per process, so the
   bound is cores and memory, not licences. The **xschem lane is
   version-controlled text** — one worktree per experiment; there is no daemon,
   no lock and no single-session rule to obey.
6. **Open PDK, clean provenance.** IHP-Open-PDK is Apache-2.0 and ngspice is
   GPL: read model cards, corner files and symbols freely, and commit decks,
   models-by-reference and logs verbatim — nothing here is under NDA. Two
   obligations replace the secrecy that used to sit here:
   (a) **reproducibility** — reference the PDK by `$PDK_ROOT` or bare library
   name (`cornerMOShv.lib`), pin its git SHA in `doc/environment.md`, record
   the exact corner sections used (`mos_tt|ss|ff|sf|fs`), and never vendor
   model bytes into the repo;
   (b) **provenance hygiene** — this repo names **no proprietary node, foundry,
   simulator or schematic editor**. Prior work is cited only as *the
   originating campaign* / *prior art carried forward*, with no technology
   identified, and any number inherited from it is marked **carried forward**,
   never presented as a measurement of this repo. `make lint` enforces the
   denylist; a hit is a build failure, not a style note.
7. **Designer ≠ verifier**: delivery claims are re-measured by
   `lpf-signoff-verifier` from raw artifacts, never accepted as reported.
8. **Gap-as-signal**: if you struggle (missing tool/doc/check, repeated trap),
   don't just push through — fix the harness (add the lint, the `lab` helper,
   the doc line) and record it as a `doc/journal/` entry (+ index line).
9. **Sim economy**: expensive runs (THD transients, corner sets, Monte Carlo)
   only after the cheap scorecard passes the hard box — `lab.metrics.gate`
   enforces it; don't bypass with a hand-rolled `evaluate` call except to debug
   the harness itself. This is an attention-economy rule, not a licence one: a
   multi-second subthreshold transient is still the most expensive thing you
   can ask for, and a reader's attention on a mis-shaped design is wasted.
10. **Write-risk ordering** (`doc/memory/README.md`): episodic writes are
    automatic (the ledger); semantic writes (journal, READMEs, `pdf/INDEX.md`)
    need provenance and use supersede-don't-delete; **procedural writes**
    (`lab/`, `scripts/`, `xschem/`, agent definitions, this file) are
    human-reviewed — subagents **propose diffs, never self-apply them**.

## Agents

In `.claude/agents/`:

- `lpf-paper-analyst` — one paper → a falsifiable technique brief; fills
  `pdf/INDEX.md` rows. Analysis only, never simulates.
- `lpf-variant-runner` — parallel netlist-lane A/B batches; scorecard tables
  only. Netlist lane only — never touches `xschem/`.
- `lpf-signoff-verifier` — independent re-measurement of delivery claims from
  raw artifacts (rule 7). Reports; never fixes.
- `lpf-schematic-builder` — turns a certified netlist into the reviewable
  `.sch`/`.sym` of record, then proves drawing ≡ netlist ≡ simulation.
- `lpf-gardener` — report-only doc/consistency sweep. Has no write tools, by
  design; do not "improve" it by adding them.

Concurrency: analyst briefs and variant batches parallelize freely. Sign-off
stays serialized behind the thing it is signing off. The schematic lane needs
no serialization at all — only "two generators must never write the same
`.sch`".

## Parallel sessions & blast radius

**One experiment = one session = one git worktree on its own branch — never two
sessions in the same checkout (shared index/branch = clobbering).**

```bash
git -C external/agentic-design-250hz-lpf-ihp130 \
    worktree add ../lpf-wt/001-<technique> -b feat/001-<technique>
cd external/lpf-wt/001-<technique> && uv sync && export LPF_EXP=001
```

**Isolated automatically per checkout** — `lab.config` namespaces the work dir
by repo name + path hash (`WORK = /tmp/lpf_work-{repo.name}-{sha1(path)[:6]}`),
so two worktrees can never land runs in the same directory or read each other's
rawfiles. `LPF_EXP` stamps every ledger row (`make runs ARGS="--exp NNN"`).

**What IS shared, and therefore needs discipline:**

| shared surface | who it collides with | the rule |
|---|---|---|
| `runs/ledger.ndjson` | every session in the *same* checkout | repo-relative, append-only, one line per run; never hand-edit, never delete rows. Two worktrees get two ledgers — that is intended; keeper numbers graduate into the experiment README, which is what merges. |
| `decks/reference/` | everyone, always | **frozen.** sha-pinned by `make lint`. Read it, splice against it, never edit it. A re-vendor is a deliberate act: update the pin *and* re-run `make check` so the certified scorecard is re-certified. |
| `doc/journal.md`, `doc/experiment-log.md`, `pdf/INDEX.md` | every session at merge time | write into **your own** `experiments/NNN-*/README.md` during the work; graduate lessons to the shared docs at merge/close-out. That is what keeps the shared files conflict-free. |
| `xschem/<cell>.sch` | whoever draws | cells are namespaced by experiment (`lpf_core_001.sch`). Never modify the reference cell or another experiment's cell; new sizing gets a new cell name and git holds the history. Delivery is still a close-out step, so the netlist can be independently re-verified. |

Edit only your own `experiments/NNN-*/` dir during parallel work.

**Merge:** PR `feat/NNN-*` → `main`, squash into one descriptive commit;
**re-pin the meta repo's submodule SHA afterwards**; `git worktree remove` when
done (never `rm -rf`).

## Git

Work on `feat/<name>` off `main`; PR and squash. This repo is a **submodule** of
`spicexplorer-workspace` — after a merge, re-pin the meta repo. PR bodies follow
the workspace's four-part shape (What was done / Assumptions / Errors, setbacks,
gotchas / Next Steps).

**Ask before pushing.** Never commit `runs/`, `/tmp` work-dir output, rawfiles,
simulator logs, or PDK content.
