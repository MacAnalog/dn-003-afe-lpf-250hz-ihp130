# The method — agent roles, gates, artifacts, and what it cost

[REFERENCE] · assembled 2026-08-16. This is the TCAD-extension material: the
*how*, in enough detail that a reader could rebuild the loop.

Sources span three repos. Paths are marked:
`LPF:` = this repo · `META:` = `spicexplorer-workspace/` ·
`PF:` = `spicexplorer-platform/` (`git show <ref>:<path>` where a branch is named).

---

## 1. The shape of the flow

```
                 human: spec, floorplan constraints, plan approval, Q-decisions
                   │
   schematic lane  │                            layout lane
   ───────────────┼───────────────────────────────────────────────────────────
   sizing search   │
   sign-off cell ──┼──► layout-brief-author ──► BRIEF.md + brief.json
   (certified      │        (measured intent)      (per-net fF budgets, matching
    netlist +      │                                mV/%, hi-Z pA, wells, pins)
    scorecard)     │                                        │
                   │                                        ▼
                   │                        layout-designer ──► PLAN.md
                   │                                        │      │
                   │                        ┌───────────────┘   HUMAN GATE
                   │                        ▼                     (approve)
                   │              gen_<cell>.py  (parameterized generator)
                   │                        │
                   │        ┌── build ─► DRC ─► LVS ─► PEX ─► frozen benches ──┐
                   │        │        (every round, every optimizer trial)      │
                   │        └────────── iterations/ snapshot ◄─────────────────┘
                   │                        │
                   │                        ▼   REPORT.md + scorecard_post.json
                   │                        │
                   │        layout-reviewer ─► REVIEW.md + REVIEW.yaml + REVIEW.png
                   │           (rebuilds,        (layout-review/1 DSL, every
                   │            re-runs, and      finding with geometry anchors)
                   │            re-measures            │
                   │            everything)            ▼
                   │                            fix round → back to the designer
                   │
                   └──► optimizer over the generator's knobs
                        (nevergrad; each trial = the same build→DRC→LVS→PEX→bench)
```

Three rules govern the whole lane (`META: doc/layout-lane.md`, verbatim headings):

1. **Layout = code.** "The GDS is a build product of a gdsfactory module whose
   parameters are the knobs an optimizer may move… Same params → byte-identical
   GDS. Fixes go into the generator, never into the GDS."
2. **DRC, LVS and PEX always run**, through the platform wrappers, on every
   iteration — "never a one-off subprocess pipeline in the block repo."
3. **Runners live in the platform** so the same call serves an optimizer trial.

---

## 2. The three agents

All three are `model: opus`. Definitions live in `META: .claude/agents/`.

### 2.1 `layout-brief-author` — the schematic→layout hand-off

| | |
|---|---|
| tools | `Bash, Read, Write, Glob, Grep` (no `Edit`) |
| inputs | certified netlist of record, `design.json`, operating point, pre-layout scorecard; the block's **frozen bench harness**; the block's operating class (nA / µA / mA-RF) |
| outputs | `layout/<cell>/BRIEF.md` (human) + `brief.json` (machine) |

Its role, verbatim: *"the schematic-level expert handing the design over to
layout… Your job is to replace the designer's guesses with **measured**
numbers."*

Gates:
- *"All numbers below come from **that** harness — never a hand-rolled bench."*
- A budget is defined as **the parasitic that consumes 25 % of the margin that
  metric has left** (`margin_fraction`, default 0.25). Rank by budget, smallest
  first.
- *"Spend the pre-layout **margin**, not the spec… say the margin you started
  from."*
- *"One-sided (asymmetric) injection nearly always dominates in differential
  cells — report it separately from the balanced case."*
- Linearity check: *"Keep injections small enough to stay linear (check 1 fF vs
  10 fF scale); report the linear coefficient, not just one point."*
- *"You do not draw layout and you do not change the design."*
- Missing-tool rule: propose the platform wrapper as a diff — procedural writes
  are human-reviewed — rather than leaving a one-off script behind.

The perturbation primitive is `spicexplorer_signoff.sensitivity`
(`inject_caps`, `inject_resistor`, `scale_param`, `sweep`) spliced through
`Design.dut_override`.

### 2.2 `layout-designer` — generator, not geometry

| | |
|---|---|
| tools | `Bash, Read, Write, Edit, Glob, Grep` |
| inputs | cell of record; **the brief**; spec + bench harness; the PDK; *"floorplan constraints from the human: pin sides, aspect-ratio ceiling, what must be shared with a neighbour block"* |
| outputs | `PLAN.md`, `gen_<cell>.py`, `asbuilt/core_pex.sp`, `scorecard_post.json`, `iterations/`, `REPORT.md` |

Two mechanical identities it must prove: (i) **LVS** — extracted netlist ≡ the
certified schematic netlist (devices, sizes, multiplicities, connectivity, pin
names); (ii) **post-layout re-measurement** — the PEX netlist spliced into the
cell's *own frozen benches*, scorecard printed next to the pre-layout one,
*"every delta explained."*

Gates, verbatim:

| step | gate |
|---|---|
| 0 | *"If [the brief] is missing, ask for it (or ask that the author agent be run) before planning… Never replace it with your own guesses silently."* |
| 1 | **`PLAN.md` (gate: human approval)** — *"**Stop and get the plan approved before step 2.**"* |
| 2 | *"it builds"* — one `build(params: LayoutParams) -> gf.Component`; *"Deterministic: same params → byte-identical GDS. No randomness, no wall clock, no absolute paths."* |
| 3 | *"zero violations, or each waiver written down"*; *"Iterate on the **generator**, never on the GDS."* |
| 3 | **Snapshot rule:** *"**Snapshot every round — no exceptions, failed builds included.**"* — *"A build that throws is a snapshot too (`gds=None`, note = the error and the cause). The trail is what lets a reviewer or a future you audit the work instead of trusting a summary written from memory."* |
| 4 | *"clean compare vs the certified subckt"* — *"set the generator to the netlist's grid, never loosen the compare."* |
| 5 | scorecard next to pre-layout + per-net used/allowed budget vs the brief; *"Every delta pre→post > the campaign's noise floor gets a sentence naming the parasitic that caused it — verified by a what-if."* |
| 6 | the Iterations table is **generated** (`iterations_table_md`): *"Do not type the table by hand; if a round is missing from it, the round did not happen."* |
| — | **No self-certification:** *"Everything else (floorplan quality, matching, area) is judged by the independent `layout-reviewer`; do not self-certify it."* |
| — | *"**Do not fix the generator by editing the GDS**… the next build erases the fix and the reviewer's rebuild will not match."* |

Recorded dead end worth citing: *"Magic-native extraction is a recorded dead end
for our GDS (no FET recognition) — don't retry it."*

The agent also carries a **technique catalogue** mapping each analog-layout
technique to the generator knob that implements it — unit-device sizing
(`unit_w`), same-row/same-orientation (`row_of[class]`, `orient`),
interdigitation (`pattern[class]="interdigitate"`), common-centroid
(`pattern[class]="common_centroid"`), dummies (`n_dummy`), symmetric floorplan
(`axis`, `mirror`), equal proximity (`well_margin`, `ring_gap`), tap uniformity
(`tap_pitch`), guard rings; and for routing: matched routing, layer choice by
sensitivity (`layer[net]`), shielding (`shield[net]`), cross-coupled pair routing,
star supply, cap plate orientation (`plate_to[cap]`), via discipline,
antenna hygiene. Its rule of thumb: **"interdigitate what sets an offset,
common-centroid what sets a ratio."** This mapping is what makes the layout an
*optimizable* object rather than a drawing.

### 2.3 `layout-reviewer` — report-only, re-measures everything

| | |
|---|---|
| tools | `Bash, Read, Write, Glob, Grep` — **no `Edit`** |
| outputs | `REVIEW.md`, `REVIEW.yaml`, `REVIEW.png`, `review_crops/F<n>.png` |

Ground rules, verbatim:

- **Trust:** *"The designer's numbers are claims; you re-derive everything from
  the committed generator and the certified netlist."*
- **Rebuild, don't reuse:** *"If the built GDS differs from anything the designer
  checked in, that is finding #1."*
- *"No brief = finding #0: the layout was designed against guesses."*
- *"**Re-run DRC / LVS / PEX yourself** through the same platform wrappers — PEX
  in the mode(s) the report claims **and in `RC` if the report only has `CC`**"*;
  compare LVS *"against the certified schematic netlist of record, not against a
  netlist found in the layout dir."*
- *"**Re-measure** the PEX subckt through the campaign's own frozen benches… A
  number that didn't reproduce is a finding, not a footnote."*
- *"Work in a temp/build dir; **never** write into the layout dir or the
  generator."*
- **Separation of duty:** *"Designer ≠ reviewer: if you wrote this generator,
  refuse and say so."*
- **Audit-trail gate:** one `iterations.yaml` entry per claimed round (*"a
  hand-typed table is a finding"*); the last entry's `gds_sha256` must equal the
  sha of the rebuilt GDS; each diff PNG must show the fix its note claims. *"A
  missing trail on a cell laid out after 2026-08-15 is a **major**."*
- Verdicts: `PASS` / `PASS with majors` / `FAIL`; severities blocker / major /
  minor / note. *"Never soften a FAIL because 'it is close'."*
- Coordinates: *"Get coordinates from the GDS itself… **never eyeball them**."*
- *"You do not fix, push, or open PRs."*

Two traps it is told to look for, both of which fired in this campaign:
*"LVS 'clean' with a wrong netlist file is the most common false pass — print the
path and hash of the netlist you compared against"* and *"A PEX run with the
wrong layer map / mode yields near-zero parasitics… **a perfect reproduction is
suspicious**."*

Eight-step flow: reproduce (+ trail audit) → identity beyond LVS (pin
names/order, device flavour, model mapping, m/finger split) → extraction-driven
per-net budget vs the brief → matching & symmetry audit (mirror-XOR about the
declared axis; routing symmetry by layer, length Δ, via count, shielding) →
wells/ties/rings → **optimizer-knob sanity** (probe min/max of every knob with
build + DRC; *"build twice, hash"*; *"anything the optimizer would need to move
that is hard-coded is a finding"*) → objective audit → re-review mode
(confirmed-fixed / still-open / made-worse **by measurement, not by reading the
designer's changelog**).

---

## 3. The `layout-review/1` DSL

A review is three co-ordinated artifacts with **the same finding ids**:
`REVIEW.md` (narrative), `REVIEW.yaml` (the DSL), `REVIEW.png` + `review_crops/`
(the findings drawn on the PDK render, numbered and colour-coded by severity).

Normative implementation: `PF: packages/spicexplorer-layout/src/spicexplorer_layout/review.py`
(`SCHEMA = "layout-review/1"`), public API `Review`/`Finding`,
`load_review`/`dump_review`/`validate`, `annotate()`, `annotate_crops()`; CLI
`spicexplorer-layout validate-review REVIEW` and
`spicexplorer-layout annotate GDS REVIEW.yaml PNG [--crops DIR]`.
Documented in `PF: packages/spicexplorer-layout/README.md` and
`META: doc/layout-lane.md`.

**Top level:** `schema, cell, gds, gds_sha256, generator{path,params,sha256},
verdict, round, kind, reproduced{...}, units, axis, findings[], not_checked[],
reviewer, date`.

**`reproduced`** is the gate-by-gate reproduction record:
`build`, `drc{passed,n,deck,waivers}`,
`lvs{passed,matched,unmatched,netlist_sha,netlist_path,certified_netlist,provenance,unchecked_pins[]}`,
`pex{mode,n_c,n_r,rc_n_c,rc_n_r,note}`, `scorecard` (per metric
`{designer, reviewer}`), `corners`,
`bounds{knobs,endpoints,built,drc_clean,violations,dead_knobs}`, `symmetry`,
`trail{entries,gds_sha_match,last_entry,rebuilt,table,diffs}`.

**Per finding:** `id, severity(blocker|major|minor|note),
category(reproduce|drc|lvs|pex|budget|coupling|matching|symmetry|routing|well|leakage|knob|objective|other),
title, where[], evidence, effect{metric,delta,unit,model: hand|what-if},
fix{knob,to,note}, expected, verdict(open|fixed|worse)`.

**Anchors (`where`)** carry GDS coordinates in µm — `box{layer,x0,y0,x1,y1}`,
`point{x,y}`, `pair{a,b}`, `line`, `device{name,x0,y0,x1,y1}`, `rule`, `net`
(legend-only). Rendering: box → outline + tint, point → crosshair, pair →
arrow-line, line → polyline, rule → squares at each hit; every marker tagged with
the finding number in the severity colour.

**Two structural properties make the DSL useful, and both are visible in the real
instance** (`LPF: layout/H12-pdk-cap/REVIEW.yaml`, 25 findings):

1. `effect.model` is either `hand` (14 findings) or `what-if` (11) — the review
   distinguishes an *argued* magnitude from a *simulated* one, per finding.
2. `fix.knob` names a **generator parameter** (or `none (design lane)` /
   `new feature (platform)`), so a finding is machine-routable to whoever can act
   on it. That is what turns a review into a work queue.

Anchor coverage is itself informative: 23/25 findings carry `where`; the five
findings with no drawable crop (F4, F9, F10, F23, F24) are exactly the ones whose
subject is a `BOUNDS` sweep, a JSON key or an extraction mesh — not a place in
the layout.

---

## 4. The iteration trail

`iterations/iterations.yaml` — one entry per build round, written by
`spicexplorer_layout.iterations.snapshot(...)`. Each entry:
`id, note, gen_sha256, gds_sha256, params, area_um2,
drc{passed,n,rules}, drc_hits, lvs{passed,matched,unmatched,netlist_sha},
pex{ok,mode,n_c,n_r}, scorecard{9 metrics}, files{gen,gds,png}`, plus
`diff_it<N-1>_it<N>.png` between consecutive rounds.

For this cell: **14 entries** (it01…it14), 13 diff renders. What it shows —
drawn in `figures/iteration_trail.png`, flat table in
`figures/data/iteration_trail.csv`:

- **it03 is a failed round**: 5 DRC violations, no LVS/PEX, no scorecard —
  snapshotted anyway, exactly as the rule demands. It is the single most
  convincing artifact for the "the trail is honest" claim.
- **it07/it08 and it10–it13 build byte-identical GDS** (`240fb440614b`,
  `fc59cfd7ef38`): assertion- and documentation-only rounds. As `REPORT.md` §10
  puts it, *"a guard-rail is part of the layout of record and gets the same
  build → DRC → LVS → PEX treatment as a geometry change."*
- **LVS matched on 14/14**; total DRC violations across the whole trail: **5**,
  all in it03.
- The extracted-C element count is itself a trail: 78 → 71 (the `lane_mid` knob
  removing the `net2`–`net3` coupling card entirely) → 69 (round 4).

---

## 5. The optimizer backend (PR #101, `PF: feat/layout-optimizer-backend`)

23 files, +3064/−139; the core is
`packages/spicexplorer/src/spicexplorer/backends/layout.py` (1338 lines) with
831 lines of offline tests and 71 of live tests.

**How a layout becomes an optimizable design space.** A parameterized layout is
a `spicexplorer_layout` generator: the frozen `LayoutParams` dataclass *is* the
knob list, `BOUNDS = {knob: (lo, hi)}` is the search space, and `build(params,
sizing)` is the map from a candidate to geometry. The optimizer reads the knob
types by an `ast` parse of `LayoutParams` — *never importing the generator* — and
casts candidates to ints / bools / grid-snapped floats. The "netlist" of the
testbench is a `layout-flow/1` YAML spec rather than a SPICE deck
(`sim_engine: layout`).

**One trial = one `run()`:**
build (`GdsBuilder`, in the gdsfactory interpreter) → `run_drc` → `run_lvs`
(fixed reference **or** a `lvs.writer` callable re-run per candidate, because the
reference netlist itself depends on the knobs) → `run_pex`
(`mode CC|RC|R`, `strip_mim`, `schematic_cards_from`, `ports`, `ac_gnd_nets`) →
post-layout measurement.

**Two measurement paths**, and this campaign used both — a clean contrast:

| path | mechanism | used by |
|---|---|---|
| `postlayout:` | the platform's own ngspice testbenches on `dut_postlayout.spice` — the extracted subckt rewritten to the schematic DUT's exact `.subckt` header and pin order (kpex reorders pins) — with Tier-1 registry recipes (`{meas: ugf\|pm\|dcgain}`) | the 5T-OTA example |
| `measure:` | a block-specific hook run in **any** interpreter (the block's own harness venv) speaking `spicexplorer_layout.measure_protocol`: `{"pex_subckt","work_dir","params","corner","extra"}` in → `{"scalars":{…},"status":"ok"}` out. Every key of `scalars` becomes an optimizer metric | **this cell** — its scorecard is the LPF harness in the LPF venv |

**Objective and constraint model.** Ordinary target specs over flow scalars:
`area_um2`, `width_um`, `height_um`, `drc_violations`/`drc_pass`, `lvs_match`,
`pex_ok`/`pex_n_c`/`pex_n_r`, per-net C (`c_<net>_ff`, `ctot_<net>_ff`,
`c_<a>__<b>_ff`), `postlayout_ok`, `build_secs`/`total_secs`, plus every
`measure` key. DSL spellings: `m ≥ T` → `goal: exceed`; `m ≤ T` →
`goal: minimize`; `m == T` → `goal: exact, tolerance: 0`.

**Failure is the constraint mechanism, not an exception:** *"a failed stage never
raises out of `run()`"*; `gates` (DRC fail skips LVS/PEX/measure, LVS mismatch
skips PEX/measure, PEX fail skips measure) leave the skipped stages' scalars NaN
→ `MAX_PENALTY` on those specs, while `area_um2` — which came from the build —
still scores. So an infeasible point still ranks, by area plus failures.

**A real methodological finding, worth a paragraph in the paper:** the area
objective must use `reward_type: log` (`|log10(area/target)|`, monotonic below
the target), not `relative-log`, which rewards *proximity* to the target and
mis-ranks a minimize objective. This was found and fixed in the co-optimization
example (`PF: aed4b82`).

**Co-optimization seam:** `sizing_params: {dut_param: sizing key}` routes a
candidate into `build(params, sizing)` (per-run `sizing.json` overlay), **and**
into the LVS writer, **and** into the post-layout decks' `.param`s — so a single
search moves transistor widths and floorplan clearances together and the LVS
identity still holds. A name that is both a sizing key and a `LayoutParams` field
is rejected at load.

**Parallelism — state it honestly.** `spicexplorer-optimize --workers K` sets
`optimizer_kwargs.num_workers`, which is *Nevergrad's ask-batching hint*; the
platform's trial loop is **sequential today**. The concurrency that exists is
*within* a trial (testbenches × PVT corners, and the flow spec's own
`max_workers`). Trial-level fan-out is named as the obvious next step. The
stand-alone driver used for this cell's campaigns *does* fan out — it runs its
own `ThreadPoolExecutor` ask/tell pool.

**`seed_from_init` is a hint, not "trial 0".** From `_suggest_init_point`:
*"`suggest()` is a HINT to Nevergrad, not a queue: with `num_workers == 1` and
most algorithms it is the first `ask()`, but with parallel workers / TwoPointsDE
it has been observed as trial 4 — read the init trial back from the log by its
params, do not assume index 0."* In the co-optimization run the seeded point
landed at **trial 8**. (The notebook's own prose in cell 17 says "trial 0" and is
wrong; cite the docstring.)

---

## 6. Layout↔schematic co-optimization (PR #102, `PF: feat/layout-coopt-notebook`)

Notebook `packages/spicexplorer/notebooks/layout_schematic_cooptimization.ipynb`
— 33 cells (17 code, 16 markdown), outputs stored, 3 stored images. Replay
artifact `examples/layout/ihp-sg13g2/5t_ota_gf/coopt/coopt_replay.json` lets
every table and the scatter figure regenerate without the physical stack.

**Setup:** the gdsfactory-lane 5T OTA (`ota_5t_gf`) in IHP SG13G2. Bench
`tb_ac.spice`: VDD 1.5 V, VCM 0.8 V, IBIAS 20 µA, **CL 50 fF**, corner `mos_tt`,
`.op` + `.ac`. Optimizer `OnePlusOne`, budget 16, `seed_from_init: true`.

**Search space — 9 dimensions, 3 sizing + 6 layout:**

| param | kind | min | init | max |
|---|---|---|---|---|
| `in_w` | sizing | 0.45 | 0.62 | 0.85 |
| `pld_w` | sizing | 1.40 | 2.00 | 2.40 |
| `tail_w` | sizing | 1.60 | 2.00 | 2.60 |
| `gap_x` | layout | 1.00 | 1.46 | 1.80 |
| `ch_y` | layout | 0.90 | 0.92 | 1.60 |
| `edge_x` | layout | 1.30 | 1.57 | 2.00 |
| `ib_off` | layout | 0.80 | 1.10 | 1.40 |
| `vdd_off` | layout | 0.90 | 1.35 | 1.60 |
| `vss_off` | layout | 1.00 | 1.44 | 1.80 |

**Target specs:** `area_um2` minimize 205.9 (weight 10, `reward_type: log`);
`ugf` exceed 32 MHz (8); `dcgain` exceed 30 dB (8); `pm` exceed 55° (5);
`drc_pass` / `lvs_match` / `pex_ok` / `postlayout_ok` exact 1 (weight 100 each).
The notebook is explicit that these are **soft**: *"they are weighted terms in
one score, so a slightly infeasible point can still out-score a feasible one."*

**Extraction cost on the layout of record** (the pre→post the co-optimization is
compensating):

| metric | pre-layout | post-layout | Δ |
|---|---|---|---|
| UGF (MHz) | 30.146 | 29.447 | **−0.699** |
| PM (deg) | 61.479 | 61.926 | +0.447 |
| DC gain (dB) | 29.769 | 29.779 | +0.009 |

**Result — the headline three-way:**

| | area (µm²) | UGF (MHz) | PM (°) | gain (dB) | meets spec? |
|---|---|---|---|---|---|
| baseline — layout of record, default sizing | **205.9** | 29.45 | 61.9 | 29.78 | ✗ UGF, ✗ gain |
| **sizing alone** — trial 8 (the seeded `init` point) | **217.0** | 32.52 | 61.4 | 30.51 | ✓ |
| **co-optimized** — trial 14 | **208.3** | 32.61 | 61.4 | 30.23 | ✓ |

*Derived, and stated in the notebook:* sizing alone costs **+11.0 µm² (+5.4 %)**;
co-optimization costs **+2.3 µm² (+1.1 %)** — it gives back **8.7 µm², 79 % of
what the sizing cost**. Knob/sizing deltas baseline → best: `in_w` +22.0 %,
`pld_w` +25.3 %, `tail_w` +2.5 %, `gap_x` +6.2 %, `ch_y` 0 %, `edge_x` −7.6 %,
`ib_off` −11.8 %, `vdd_off` −3.7 %, `vss_off` −9.0 %.

**Campaign cost:** 16 trials in **559.4 s = 9.3 min** (34.96 s/trial mean,
34.60–36.89 s range). **6/16 feasible**; **0 trials failed a physical gate** —
all 16 candidates were DRC-clean and LVS-matched, so the 10 infeasible points
failed on *performance*, not physics.

**Its own stated caveat, verbatim:** *"16 trials in a 9-dimensional space is a
demonstration, not a campaign, and the run leans on `seed_from_init` for a
feasible starting point. Trial 1 and trial 15 both found ~202.6 µm² — genuinely
smaller than anything above — and were rejected only because they land 1.7 and
2.1 MHz short on UGF."* Quote this caveat in the paper; a TCAD reviewer will find
it otherwise.

---

## 7. Cost and effort — with provenance

**Read the provenance column.** Anything marked *estimate* is **not** recorded in
any repo: a grep of `META: doc/`, `META: .claude/agents/`, this repo's `doc/`,
`CLAUDE.md` and `layout/` for `token`, `k tokens`, `wall clock`, `api cost`,
`hours` returns **zero** agent-cost hits. The only "token" hits anywhere are
circuit-*representation* prompt sizes in an unrelated annotation experiment.

### 7.1 Tool stage cost — measured

| stage | 5T OTA | **this cell (`lpf_core`)** | provenance |
|---|---|---|---|
| build (gdsfactory) | 3.2 s | 7 s | notebook cell 12 / `LPF: layout/H12-pdk-cap/opt/README.md` |
| KLayout DRC | 21.7 s (≈25 s quoted) | **85 s** | as above / `PF: packages/spicexplorer-signoff/README.md` |
| KLayout LVS | 7.4 s (≈4 s quoted) | 28 s | as above |
| kpex CC | 4.1 s (≈7 s quoted) | 19 s | as above |
| post-layout benches | 0.2 s | 9 s | as above |
| **one full trial** | **36.8 s** ("35–70 s, KLayout DRC dominates") | **≈150 s** | as above |
| measured trial wall time, this cell | — | median **130.35 s** (A) / **129.8 s** (B); min 6.0 s (early `build_fail`), max 194.7 s | `secs` field of `LPF: layout/H12-pdk-cap/opt/results/campaign_{A,B}_trials.jsonl` |

Tool versions: KLayout 0.30.5, kpex 0.3.12, ngspice 45 (+ OSDI). The PDK's own
DRC/LVS decks are used, not re-implemented.

### 7.2 Campaign cost — measured

| campaign | trials | workers | wall clock | provenance |
|---|---|---|---|---|
| area campaign A | 300 | 12 (`--workers`, stand-alone driver's own thread pool) | **≈40 min** — *estimate*, from 300 × 130.35 s median ÷ 12 ≈ 54 min if perfectly packed; no wall-clock total is recorded | `opt/results/campaign_A_trials.jsonl` has per-trial `secs`; **the campaign total is not recorded** |
| area campaign B | 300 | 12 | as above | as above |
| co-optimization (5T OTA) | 16 | 1 (sequential) | **559.4 s = 9.3 min** — measured | notebook cell 21, `coopt_replay.json` `run_secs` |

> **Correction to carry forward.** The stated "≈40 min each, 12 workers" for the
> two area campaigns is **not supported by a recorded total**. What *is* recorded
> is 300 trials × 130 s median each. Either recompute from the trial timestamps
> before publishing, or state it as "600 trials at a 130 s median, run in
> parallel on a 128-core host."

### 7.3 Iteration and verification volume — measured

| quantity | value | provenance |
|---|---|---|
| designer iteration rounds, snapshotted | **14** (it01–it14) across 4 passes; 1 failed round (it03) preserved; 4 byte-identical rebuilds (assertion/documentation rounds) | `iterations/iterations.yaml` |
| review rounds | **3** — round 4 (the decision round) is delivered but **not yet reviewed** | `REVIEW.yaml` `round: 3` |
| findings, round 3 | **25** — 3 major, 2 minor, 20 note; 12 fixed, 10 open, 2 approved-deferred, 1 worse | `REVIEW.yaml` |
| round-2 → round-3 disposition | 21 round-2 findings → **19 fixed or approved-deferred, 2 open on substance, 4 new** | `REVIEW.md` |
| reviewer's independent work, round 3 | **66 endpoint builds + 66 own DRC runs** (33 knobs × 2), 2 full GDS rebuilds, **3× CC + 3× RC** kpex runs, `--check-symmetry` on 5 stored iteration GDS, 13-entry trail re-hashed | `REVIEW.md` |
| brief sensitivity evaluations | **273 ac+noise + 8 THD** | `BRIEF.md` |
| optimizer trials | **600** (300 + 300) + 2 single evaluations | `opt/results/summary.json` |
| schematic-side sizing points | **37 across 11 rounds** | `doc/sizing-history/rounds.md` |

### 7.4 Agent effort — ALL ESTIMATES, none recorded

The following figures were reported at hand-off but have **no artifact backing
them anywhere in any of the three repos**. They must be labelled *estimate* in
the paper, or dropped, or (best) re-derived from the session transcripts before
submission:

| agent episode | token / wall figure | status |
|---|---|---|
| layout-designer, round 2 | ≈ 413 k tokens / 84 min | **estimate — no provenance** |
| layout-designer, round 3 | ≈ 294 k / 65 min | **estimate — no provenance** |
| PLAN-v2 author | ≈ 113 k / 13 min | **estimate — no provenance** |
| layout-reviewer, round 1 | ≈ 324 k / 38 min | **estimate — no provenance** |
| layout-reviewer, round 2 | ≈ 261 k / 25 min | **estimate — no provenance** |
| layout-reviewer, round 3 | ≈ 273 k / 37 min | **estimate — no provenance** |
| optimizer backend implementation | ≈ 155 k tokens | **estimate — no provenance** |
| co-optimization notebook | ≈ 338 k / 107 min | **estimate — no provenance** |

*Total, if the estimates are accepted:* ≈ 2.17 M tokens across 8 episodes,
≈ 6.2 h of agent wall clock — for one cell taken from certified netlist to
reviewed, optimized layout. What *is* documented and can be stated without
caveat: all three agents run on the same frontier model, and the loop's
*machine* cost is 14 layout rounds + 600 optimizer trials + ~200 DRC/LVS/PEX
invocations by the reviewer alone.

**Recommended fix before submission** (also in the gap list): add a
`cost.jsonl` the agents append to at episode end (model, tokens in/out, wall
seconds, artifacts written). That is a ~20-line harness change and it converts
the single weakest table in the paper into a measured one.

---

## 8. The human-decision log

The plan gate is where a human enters the loop, and every decision is written
down in `LPF: layout/H12-pdk-cap/PLAN.md`.

| # | decision | date | outcome |
|---|---|---|---|
| — | **v1 plan approved** | 2026-08-15 | *"APPROVED 2026-08-15 (human sign-off) — built as planned."* Honest footnote in the file itself: *"the human approver was not live when this plan was first written, so the flow proceeded past the gate on the launching agent's instruction; the sign-off arrived on 2026-08-15 and approved the plan unchanged."* — the one gate violation in the campaign, self-reported |
| — | **Round-2 delta approved** | 2026-08-16 | *"APPROVED 2026-08-16 (human sign-off), as written."* (commit `aac192f`) |
| **Q1** | take the anti-oriented MIM split (`cap_anti_orient=True`, `cc12` 3\|1\|3)? | 2026-08-16 | **yes.** Reasoning recorded: v1 rejected it on a one-sided-C argument; the reviewer's what-if contradicted that *with a measurement* (14.2 dB of HD2), and single-orientation `xc12` plates had put `voutp` at 505.5 fF = 1.11× its pvt budget while `voutn` sat at 352.5. *"Balancing them is a budget fix, not only a linearity fix."* |
| **Q2** | `bias_dummy_rows = 1`, costing ≈0.06° of the S1 margin? | 2026-08-16 | **yes**, explicitly *"the human's call"* on a **hand bound** (1.2 Hz of fc against a 3.27 Hz margin) |
| **Q2** | — **REVERSED** | **2026-08-17** (as dated in `PLAN.md`) | **`bias_dummy_rows = 0`.** The area campaign *measured* the other side: the dummy rows cost **13 791 µm² (5.6 % of the cell) + 0.05° of `ph_max` + 2.1 fF on `net2`/`net3`**, against a matching benefit that *"is still a hand bound and still unmeasured (no bench in this campaign models edge/interior ΔV_T)."* Round 4 defaults then give **228 093.6 µm² (−7.7 %), `ph_max` 331.221 nominal (+0.061) and 329.821 at the failing corner (+0.070)**, DRC 0, LVS matched — *"the reversal is free on every measured axis."* F7's exposure is re-opened as a **documented, unmeasured matching debt**; `bias_dummy_rows = 1` stays a legal knob value, one build away |
| **Q3** | deliver with the `cap_bcs ×0.9 / iref ×0.9` corner miss? | 2026-08-16 | **yes — report, never hide.** *"The block owner has said corners are nice-to-have, not must — so the proposed default is deliver with the miss documented"*; the follow-ups (an `iref` trim, a small C1/C2 re-allocation, the well-junction model) are **design-lane** work, not layout. The reviewer's counter-note: *"without that approved decision this row is a blocker"* |
| **Q4** | defer the `xr2` (bridge replica) orientation split? | 2026-08-16 | **defer.** Splitting it would double its n-well count and add well junction area on exactly the nets F3 says are already unmodelled |
| **R2.7** | defer the n-well / p-substrate junction-C model (F3) | 2026-08-16 | **defer** — *"the layout has no lever: `well_margin` is at the `NW.c` floor"*; the fix is a platform feature, `Cj(area, perimeter, Vbias)` |

**The Q2 reversal is the paper's best single illustration of the method's value**:
a decision was taken on a hand bound at the plan gate, an automated campaign then
*measured* both sides of it, and the human reversed themselves against their own
earlier call — with the cost of the reversal (an unmeasured matching debt) written
down rather than buried. That is a closed loop between human judgement and
machine measurement, not an approval rubber-stamp.

> **Date to reconcile before submission:** `PLAN.md` dates the Q2 reversal
> 2026-08-17, while the round-4 git activity is 2026-08-16. Fix one or the other.

---

## 9. The T0…T5 roadmap this sits on

`META: doc/plan_layout_automation.md` §6. Useful for the paper's "future work"
and for positioning what is *done* vs *planned*:

| tier | content | status |
|---|---|---|
| **T0** | package skeletons — `spicexplorer-layout` + `spicexplorer-signoff` behind typed APIs; `layout.gen` exposes `build(params) → GDS`; `signoff.sensitivity` feeds the brief | **landed** (PR #99, 2026-08-16) |
| T1 | placement engine v1 — row/mirror-pair placer in `layout.place`, grouping spec as input | planned |
| T2 | matching patterns (interdigitation + dummies, common-centroid) + live-PCell spike | planned |
| T3 | graph integration — `detect_blocks`: deterministic circuit-graph motifs → grouping spec, LLM annotation agent as fallback, net weights for the router | planned |
| **T4** | agent pair + knowledge base | **agent definitions landed 2026-08-15**; acceptance criterion was *"a designer → reviewer episode on a real cell (first: LPF `H12-pdk-cap`)"* — **this campaign is that acceptance test** |
| **T5** | closing the design loop — post-layout metrics as an optimizer scoring hook | **prototyped 2026-07-10** (`optimize_layout.py`: nevergrad over placement clearances, full-toolchain evaluator, **−11.3 % area**, 232 → 206 µm²); PR #101/#102 productionize it. Remaining: joint multi-corner PEX, FasterCap, density/fill |

Two design principles from the same doc that belong in the paper's discussion:
*"**Agentic, not fully deterministic.** The agent chooses floorplan and per-block
patterns, calls the tools, reads structured feedback, iterates. Verification is
the calibration signal."* And on scope: *"**complexity is added only when a named
need arrives**, never ahead of it"* — which is why the delivery staging is
agents-and-CLIs first, a lean plain-Python episode runner second, and a protocol
server *"deferred, maybe never"*.

An earlier prototype comparison also belongs in the results: the generator lane
had **6× lower PEX UGF penalty** than a hand-drawn strip layout of the same cell.
