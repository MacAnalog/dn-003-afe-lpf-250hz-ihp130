# Paper pack — agentic schematic + layout design of a 250 Hz SSF LPF (IHP SG13G2)

[REFERENCE] · assembled 2026-08-16 on `feat/layout-h12-round2`.

This directory is the **evidence base** for two papers, not the papers. It exists
so that every claim either points at a committed artifact and the command that
produced it, or is named as a gap.

| file | contents |
|---|---|
| `README.md` (this) | storyline, claims, figure/table lists per paper, and the **gap list** |
| `results_schematic.md` | every schematic-level number, as tables, each citing its source path |
| `results_layout.md` | every layout-level number: area/iteration, DRC/LVS/PEX, pre→post, budgets, review findings, area campaigns |
| `results_group_delay.md` | group delay τ(f) = −dφ/dω: reference vs pre- vs post-layout at nominal, over the one-axis + MIM corners, and a paired 100-seed Monte Carlo — tables + `figures/group_delay.png` |
| [`../../signoff/paper-draft/`](../../signoff/paper-draft/) | **the reviewer response pack**: the derived equations (`theory.md`), every number that checks them (`validation.md`), and six figures — half-circuit, transfer function, poles/zeros, per-biquad Q, the noise equation, THD/IIP3, pre- and post-layout |
| `workflow.md` | the method: agent roles, gates, the review DSL, the iteration trail, the optimizer backend, co-optimization, **cost/effort with provenance**, and the human-decision log |
| `figures/` | the figures, PNG + PDF, with `figures/README.md` naming each one's script and inputs |
| `scripts/` | the generating scripts — ten `fig_*.py` plus `_style.py`, all reading committed artifacts |

**Provenance rule this repo enforces** (`make lint`): no proprietary node,
foundry, simulator or schematic-editor name appears anywhere. The PDK
(IHP SG13G2, Apache-2.0), ngspice, KLayout, kpex, Magic, netgen and gdsfactory
are open and named freely. Prior work on a closed node is cited only as *the
originating campaign*, with any inherited number marked **carried forward**.

---

## 1. The object

A fully differential **4th-order 250 Hz super-source-follower low-pass filter**
in **IHP SG13G2** at **VDD = 1.5 V**, two cascaded SSF biquads, replica-biased,
**all-hv devices (no lv anywhere)**, PDK MIM capacitors — taken from a spec to a
DRC-clean, LVS-matched, PEX-verified, independently reviewed and area-optimized
layout **entirely through agents**, with a human at exactly one gate (plan
approval + four recorded decisions).

Headline numbers, all measured in this repo:

| | reference baseline | **delivered cell** | note |
|---|---|---|---|
| IRN 0.5–200 Hz | 49.98 µVrms | **29.199 µVrms** | **−41.6 %**, against a −20 % ask |
| THD @ 175 mVpp, 50 Hz | −48.37 dB | **−50.401 dB** | S7 limit −40 dB |
| core power | 12.07 nW | **11.913 nW** | S6 limit 50 nW |
| `fc` / `ph_max` / \|H\|@1 kHz | 250.37 Hz / 346.74° / −48.43 dB | **249.775 Hz / 332.38° / −49.03 dB** | all in box |
| passband ripple | **0.2512 dB — fails S3** | **0.0523 dB** | the baseline fails its own flatness clause on a dense sweep |
| process corner span (fc) | 1.02× | **1.02×** | the merged ladder *without* the replica spanned 3–38× |
| mismatch scored-box (S1–S6) yield, n = 100 | — | **82 %** | every failure is S2 (`fc`), never shape |
| cell area | — | **228 093.6 µm²** (round 4) | −7.7 % vs round 3 |
| DRC / LVS / PEX | — | **0 violations / matched / 69 C (kpex CC)** | |
| post-layout S1 | — | **331.221°** nominal; **329.821°** at `cap_bcs ×0.9 / iref ×0.9` | one documented corner miss, owner-approved |

---

## 2. ISCAS paper (≈4 pages) — flow, cell, results

### 2.1 Storyline

1. **Problem.** Sub-nW, sub-kHz analog filters are noise- and area-bound, and the
   layout is not a detail: the S1 phase certificate is spent at **2.15 °/fF** on
   the biquad-A internal nodes, whose entire coupling budget to biquad B is
   **0.28 fF** — about **3–6 µm of parallel min-spacing metal**. A design flow
   that hands a layout designer a netlist and a vague "keep it symmetric" cannot
   close this.
2. **Method, in one figure.** Three agents with disjoint duties — a *brief
   author* that converts pre-layout **margin** into measured per-net parasitic
   budgets, a *designer* that emits a **parameterized generator** (not geometry),
   and an independent *reviewer* that rebuilds and re-measures everything — with
   a human at one gate. Every round runs DRC + LVS + PEX and re-scores the cell
   on its **own frozen benches**.
3. **The cell.** Branch-stacked SSF biquads + floating differential capacitor
   (≥ 2 papers combined, S8) + a shared 3-device replica that generates the
   bridge-gate rail. The replica is what makes the merged ladder manufacturable:
   fc process span 3–38× → **1.02×**.
4. **The result.** −41.6 % IRN against a certified in-repo baseline; all of S1–S8
   at nominal, across four process corners, 1.40–1.65 V, 0…+70 °C; 82 % mismatch
   yield; and a layout whose post-layout scorecard moves the certificate by
   **1.16°** and `fc` by **1.11 Hz** — with every delta attributed to a named
   parasitic by a what-if.
5. **The claim.** Because the layout is code and the review is a schema, the last
   step is *optimizable*: 600 trials over 33 generator knobs, and a measurement
   that overturned a human decision taken on a hand bound.

### 2.2 Claims and where each is proved

| # | claim | proof | measured by |
|---|---|---|---|
| C1 | −41.6 % IRN vs a certified in-repo baseline, all S1–S8 passing | `results_schematic.md` §2, §3 | `lab.metrics.evaluate` on the frozen ac+noise bench; baseline `decks/reference/scorecard.json` (sha-pinned deck) |
| C2 | The replica bias converts an unmanufacturable ladder into a 1.02× fc-span one | `results_schematic.md` §4, §9.1 | 9-point one-axis corner set, `H12-pdk-cap.robust.a1p1.json` |
| C3 | 82 % mismatch scored-box (S1–S6) yield; every failure is S2, never shape | `results_schematic.md` §5; `figures/mc_hist.png` | `lab.mc.run`, n = 100, `mos_tt_mismatch`, seeds 1–100, PDK `agauss` model |
| C4 | The layout closes: DRC 0, LVS matched, PEX-verified, the post-layout scorecard still passes S1–S7 at nominal, **and the extraction does not change a single verdict across all 45 PVT corners** | `results_layout.md` §2, §3, §6.2 | KLayout DRC/LVS with the PDK's own decks; kpex 2.5D; the cell's own benches + `lab.corners` on the extracted subckt |
| C5 | Pre→post shift is small **and attributed** | `results_layout.md` §5; `figures/prepost_bode.png` | 3 × `lab.deck.ac_noise` runs, `Design.dut_override` with the PEX subckt |
| C6 | The layout is optimizable: −7.7 % area at *better* `ph_max` and *better* `net2` | `results_layout.md` §8; `figures/area_campaign.png` | 600 nevergrad trials, each a full build→DRC→LVS→PEX→bench |
| C7 | The flow is auditable end to end | `workflow.md` §4; `figures/iteration_trail.png` | 14 machine-written snapshots including one failed round; reviewer re-hashes the trail |

### 2.3 Figures (5, in order)

| # | file | caption thrust | source |
|---|---|---|---|
| F1 | *to draw — see gap G1* | the flow: three agents, their artifacts, the gates, the human gate | `workflow.md` §1 has the ASCII skeleton |
| F2 | `figures/static/schematic_lpf_core.png` | the cell of record; optionally inset `schematic_tb_acnoise.png` | `signoff/post-pvt/H12-pdk-cap/lpf_core_H12pc.png` |
| F3 | `figures/static/layout_lpf_core.png` | the layout of record, 228 093.6 µm², DRC 0 / LVS matched | `layout/H12-pdk-cap/lpf_core_layout.png` |
| F4 | `figures/prepost_bode.png` | pre- vs post-layout \|H\| and phase; panel (b) is the S1 certificate | 3 bench runs, `scripts/fig_prepost_bode.py` |
| F5 | `figures/area_campaign.png` | 600 optimizer trials: area is bounded by the gate-net capacitance, and the knobs do not reach the white space — the dummy-row *decision* does | `scripts/fig_area_campaign.py` |
| F6 | `figures/group_delay.png` | group delay: τ_dc·fc = 0.41 (Butterworth-like), layout adds +0.2 % at dc / +0.4 % at the peak — below one mismatch σ; corners scale τ as 1/fc except temperature | 25 bench runs + 200 MC draws, `scripts/fig_group_delay.py` |

If a sixth fits: `figures/mc_hist.png` (yield) or `figures/static/review_annotated.png`
(all 25 findings drawn on the layout — the strongest single image in the pack).

### 2.4 Tables (3)

| # | content | source in this pack |
|---|---|---|
| T1 | Spec box S1–S8 vs baseline vs delivered cell (one row per line, with the pass/fail definition) | `results_schematic.md` §1 + §2 |
| T2 | PVT + Monte Carlo summary: 5 process corners, supply and temperature windows, grid coverage, MC yield and σ | `results_schematic.md` §4, §5 |
| T3 | Layout closure: area, DRC, LVS, PEX element counts, and the pre→post scorecard delta with attribution | `results_layout.md` §2, §5 |
| T4 | Group delay: τ(dc), peak, τ(fc), passband delay ripple, τ_dc·fc — reference vs pre vs post, corners, MC | `results_group_delay.md` §2 |

---

## 3. TCAD extension — methodology in depth

### 3.1 Storyline

1. **Thesis.** An analog design agent becomes trustworthy when its *outputs are
   artifacts a machine can re-check*, not prose: a measured brief, a
   parameterized generator, a machine-written iteration trail, and a review
   expressed in a schema with geometry anchors. Every one of those turns a
   subjective step into a gate.
2. **Roles and gates.** Why designer ≠ reviewer; why the reviewer rebuilds rather
   than reads; why the plan gate is the *only* human gate and what happens when
   it is bypassed (it was, once, and the file says so).
3. **The review DSL.** `layout-review/1`: findings with geometry anchors,
   `effect.model ∈ {hand, what-if}` separating an argued magnitude from a
   simulated one, and `fix.knob` routing each finding to a generator parameter, a
   design-lane task, or a platform feature. This is what makes a review a work
   queue instead of an essay.
4. **The iteration trail as evidence.** 14 rounds, one failed round preserved,
   four byte-identical rebuilds that were assertion-only rounds — and a reviewer
   that re-hashes all of it before reviewing anything.
5. **Closing the loop.** The layout optimizer backend: how `LayoutParams` +
   `BOUNDS` becomes a search space, how failed stages become NaN → penalty rather
   than exceptions, and the `reward_type: log` subtlety that silently mis-ranks a
   minimize objective. Then **co-optimization**: moving sizing and floorplan
   together recovers 79 % of the area that sizing alone costs.
6. **Cost.** What the loop costs in machine time (measured) and agent time
   (estimated, and honestly labelled).
7. **The human in the loop.** Four recorded decisions — and one **reversed by
   measurement**, which is the paper's cleanest evidence that the loop is closed
   in both directions.

### 3.2 Claims and proof

| # | claim | proof |
|---|---|---|
| D1 | Measured intent beats guessed intent: the brief turns pre-layout margin into 25 %-of-margin budgets per net, per matching class, per hi-Z node | `results_layout.md` §1; 273 ac+noise + 8 THD evaluations recorded in `BRIEF.md` |
| D2 | Layout-as-code gives byte-reproducibility and an optimizable surface: 33 knobs, 33/33 of which change the GDS; 11 independent builds at default values all give the same sha | `results_layout.md` §7; reviewer's independent re-sweep |
| D2b | **A gate that cannot fail on the defect class you care about is decoration.** Round 3's "66/66 endpoints DRC-clean" became 63/65 LVS-matching in round 4: two endpoints **short nets together at zero DRC violations** | `results_layout.md` §3, §7 |
| D3 | An independent reviewer that rebuilds finds things a self-report cannot: 25 findings, 4 of them new in round 3, including a **non-determinism in the extractor itself** | `results_layout.md` §6 (F24: two RC runs differ in 17 221 lines; fc spread 0.047 Hz > the 0.041 Hz CC↔RC delta the report quoted as evidence) |
| D4 | A schema'd review is machine-routable: every finding names a generator knob, a design-lane task, or a platform feature | `workflow.md` §3 |
| D5 | The trail is honest: failed rounds are in it | `workflow.md` §4; it03 = 5 DRC violations, no LVS/PEX, snapshotted |
| D6 | Physical closure can be an optimizer constraint, not a post-check: 600 trials, and the binding constraint is a *parasitic budget from the brief* | `results_layout.md` §8; 195/300 campaign-A trials die on C(`net2`) alone |
| D7 | Layout↔schematic co-optimization recovers most of the area that sizing alone costs (79 %) | `workflow.md` §6; 16 trials, 9.3 min, replayable from `coopt_replay.json` |
| D8 | The loop changes human decisions: Q2 was taken on a hand bound and reversed against a measurement | `workflow.md` §8 |

### 3.3 Figures (TCAD adds to the ISCAS five)

| # | file | thrust |
|---|---|---|
| F6 | `figures/static/review_annotated.png` (+ crops `F1`, `F2`, `F16`, `F17`, `F18`) | the review DSL rendered: 25 findings, numbered, severity-coloured, anchored in GDS coordinates |
| F7 | `figures/iteration_trail.png` | 14 rounds: area, `ph_max`, `fc`, and the DRC/PEX counts — with the failed round and the byte-identical rebuilds marked |
| F8 | `figures/static/diff_it05_it06.png` + `diff_it13_it14.png` | the dummy rows going in (Q2 yes, +13.8 k µm²) and coming out (Q2 reversal, −19.0 k µm²) — the human decision, drawn |
| F9 | `figures/mc_hist.png` | paired pre/post mismatch MC, n = 100 — the layout's effect on *yield*, not just on the nominal point |
| F10 | `figures/pvt_window.png` + `figures/pvt_postlayout.png` | the PVT operating window pre-layout, and the same three corner sets re-measured **on the extraction** — identical verdict on all 45 corners |
| F11 | `figures/thd.png` | S7 across corners, mismatch and input frequency — including the honest 100–200 Hz topology limit |
| F12 | `figures/static/coopt_area_vs_ugf.png` (+ `coopt_baseline_vs_best.png`) | co-optimization: area vs UGF over 16 trials, and the two geometries side by side |
| F13 | `figures/static/diff_it02_it03.png` | the failed round, drawn — 5 DRC violations, preserved |

### 3.4 Tables (TCAD)

| # | content | source |
|---|---|---|
| U1 | Agent roster: role, tools, inputs, outputs, gates | `workflow.md` §2 |
| U2 | `layout-review/1` schema: top-level keys, per-finding fields, anchor kinds with occurrence counts | `workflow.md` §3 |
| U3 | The full F1–F25 findings table: id, severity, category, verdict per round | `results_layout.md` §6 |
| U4 | Per-net budget: brief budget (nominal / pvt / asym / diff) vs measured, per review round | `results_layout.md` §1.2, §4 |
| U5 | Iteration trail: 14 rows — area, DRC, LVS, PEX n_c, scorecard, GDS sha | `figures/data/iteration_trail.csv` |
| U6 | Optimizer setup: 33 knobs (25 searched), objective, constraints, penalties, worker config, per-trial cost | `results_layout.md` §7, §8 |
| U7 | Campaign outcomes: A/B trial taxonomy, best feasible, the two single evaluations | `results_layout.md` §8 |
| U8 | Cost: stage wall-clock (measured), campaign wall-clock, iteration/verification volume, agent effort (**estimates, labelled**) | `workflow.md` §7 |
| U9 | Human-decision log: Q1–Q4, the two plan approvals, and the Q2 reversal | `workflow.md` §8 |
| U10 | Co-optimization: search space, target specs, the three-way result, trial cost | `workflow.md` §6 |

---

## 4. What was simulated for this pack

Only two scripts touch the simulator; everything else re-reads committed
artifacts.

| run | cost | result |
|---|---|---|
| `fig_prepost_bode.py` — 3 × ac+noise (pre, it13 PEX, it14 PEX) at `mos_tt`/27 °C/1.5 V | seconds | pre 332.3823° / 249.7746 Hz; it13 331.1595° / 248.6388 Hz; it14 331.2208° / 248.6636 Hz — no violations in any. Reproduces the designer's numbers to four decimals |
| `fig_mc.py` — 2 × 100 mismatch draws, paired seeds 1–100 | 17 s + 51 s wall at 14 workers | pre-layout **82/100** pass the scored box S1–S6 (reproduces the certified summary to every printed digit); post-layout **87/100** |
| `fig_pvt_postlayout.py` — 2 DUTs × (9 + 22 + 45) corners, bias law α = 1.1 | **12 s total** | pre-layout 6/9, 6/22, 16/45 (reproduces the certified sign-off exactly); post-layout **6/9, 6/22, 16/45 — zero of the 45 corners changes verdict**. Mean shift `fc` −1.27 Hz, `ph_max` −1.16° |

The post-layout MC yield (**87 %**) is a **new measurement** made for this pack:
the extracted capacitance pulls the `fc` distribution's mean down by ≈0.6 Hz,
which happens to re-centre it in the 245–255 Hz box (out-of-box drops 18 → 13
samples). It is a real, reproducible number — but it is one seed set on one
corner, so state it as *measured, n = 100, paired seeds*, not as a yield
improvement claim.

---

## 5. Gap list — what a reviewer will ask for that we do not have

Ordered by how likely it is to be asked, with the concrete way to produce it.

### Blocking-ish (a reviewer will notice their absence)

| # | gap | how to close it | effort |
|---|---|---|---|
| **G1** | **No flow diagram.** Both papers need one figure showing the three agents, their artifacts and the gates. `workflow.md` §1 has the skeleton, but there is no drawn figure. | Draw it — TikZ/Inkscape by hand, or a `scripts/fig_flow.py` with matplotlib boxes. Do not generate it from the agent files; it is an editorial figure. | 1–2 h, human |
| **G2** | **No silicon, no measurement.** Everything is simulation + extraction. | Cannot be closed in this campaign. State it plainly in the abstract; ISCAS accepts simulated results, TCAD reviewers will still ask. | — |
| **G3** | **No comparison table against published sub-nW filters.** The three S8 papers are technique sources, not benchmarked competitors, and there is no FoM table. | Build a comparison table (fc, order, IRN, power, area, supply, technology, FoM) from `pdf/INDEX.md` plus a literature pass. The `lpf-paper-analyst` agent already produces per-paper technique briefs; extend it to extract the results table of each paper. | 3–5 h, 1 agent pass + human curation |
| **G4** | **Agent cost is unmeasured.** Every token/wall-clock figure in `workflow.md` §7.4 is an estimate with no artifact behind it. | Add a `cost.jsonl` that each agent appends to at episode end (model, tokens in/out, wall seconds, artifacts written); back-fill the eight episodes from the session transcripts if they are still available. | ~20 lines of harness + 1–2 h of back-fill |
| **G5** | **The area-campaign wall clock is not recorded.** Only per-trial `secs` exist. | `python3 -c` over `campaign_{A,B}_trials.jsonl`: sum `secs`, and if the rows carry timestamps take max−min for the true wall clock. If they do not, state "600 trials at a 130 s median". | 15 min |

### Strengthening (would make the results harder to dismiss)

| # | gap | how to close it | effort |
|---|---|---|---|
| **G6** | ~~No post-layout PVT.~~ **CLOSED by this pack.** All three corner sets were re-run on the it14 PEX subckt, paired against the schematic: **6/9, 6/22, 16/45 — identical verdict on all 45 corners**, 12 s of simulation (`scripts/fig_pvt_postlayout.py`, `figures/pvt_postlayout.png`). What is still open is crossing the **cap** corners into the process/temperature/supply grid post-layout. | `LPF_CAP_CORNER` + `iref_scale` hooks already exist in `opt/flow.yaml`; extend `fig_pvt_postlayout.py` with the 5 cap points × the 45 grid. | 225 extra points ≈ 10 min |
| **G7** | ~~No post-layout THD.~~ **NARROWED by `signoff/paper-draft/`**: post-layout THD now has a 6-point amplitude ladder at 50 Hz and a 5-point THD-vs-`fin` profile at 175 mVpp on the PEX subckt, plus a 5-point two-tone IIP3 ladder (`signoff/paper-draft/validation.md` §6). **IIP3 now has corners** — `validation.md` §10.2, nine certified axes, two amplitudes each, 18 transients in 27 s on a 128-core host, so the "over budget" estimate below was wrong by two orders of magnitude. What is still open is the **THD ladder and profile** over corners and MC. | `iip3_corners.py` is the template: it already sweeps `CERT_AXES` with `tran_twotone(..., vdd=)`. The same loop over `tran_thd` closes it. | ~1 min of simulation |
| **G8** | **The RC extraction is not deterministic** and the report's CC↔RC agreement claim (0.041 Hz) is finer than the extractor's own repeatability (0.047 Hz over three meshes) — the reviewer's F24. | Run kpex RC n ≥ 5 times, report mean ± spread, and re-word the agreement claim as "within the extractor's mesh repeatability". | 1 h (5 × RC at ~1 min each + write-up) |
| **G9** | **MIM top plates are stripped before extraction** (kpex has no `cap_cmim` support; its IHP tech marks the MIM layer `<TODO>` and crashes). The ≤ 15 fF bound on `net2`/`net3` is *carried*, not closed — reviewer's F11. | Either a hand/FasterCap calculation of the stripped top-plate capacitance, or a kpex tech-file patch. State the bound and its basis either way. | hand bound 2 h; FasterCap 1 day |
| **G10** | **n-well / p-substrate junction C is outside every model in the flow** — reviewer's F3, deferred by approved plan. Bound: −0.108…−0.259° on `ph_max`. | Platform feature: `Cj(area, perimeter, Vbias)` in `spicexplorer_signoff`. Until then, quote the bound and say it is a bound. | 1–2 days (platform) |
| **G11** | **`vbp` is a dangling labelled pad**: absent from the extracted netlist, and LVS still reports a match — 1 of 8 declared pins unchecked (reviewer's F13). | Platform feature: pin-list assertion inside `signoff.lvs` comparing the extracted `.SUBCKT` header against the certified one. | half a day (platform) |
| **G12** | ~~No PSRR / CMRR / offset, and no noise *spectrum* per corner.~~ **CLOSED.** Nominal spectrum: `signoff/paper-draft/validation.md` §5, `S_out(f)` over all 109 per-generator vectors, pre- and post-layout, closing to 2·10⁻⁷ %. **Per-corner spectrum**: §8 re-runs the same decomposition at every certified corner and 64 mismatch draws — closure ≤ 3·10⁻⁵ % everywhere, and channel thermal stays the dominant kind at every point. **PSRR/CMRR/offset**: §9, from two new benches (`lab.deck.ac_psrr`, `ac_cmrr`). Nominal differential rejection is symmetry-cancelled and meaningless, so the honest numbers are the mismatch-limited ones — CMRR 99.0 dB mean / 88.7 worst at dc, PSRR 108.2 / 95.8 — plus the finite common-mode transfers. Two carried findings: supply → output CM is −0.14 dB at 1 kHz (the output CM tracks the rail in the stopband), and input-referred offset is σ ≈ 1.9 mV, 1.1 % of the S7 drive. | — | — |
| **G13** | ~~No THD-vs-amplitude sweep at 50 Hz.~~ **CLOSED by `signoff/paper-draft/`**: 6-point ladder from 43.75 to 700 mVpp, both DUTs; **the −40 dB THD crossing is 306.9 mVpp**, 1.75× the S7 drive. `validation.md` §6.1, `figures/distortion.png`. | — | — |
| **G14** | **No second cell.** The layout lane's T4 acceptance criterion names two (this cell and the 5T OTA); the 5T OTA exists only in the platform examples/notebook, not as a full designer→reviewer episode. | Run the three agents on the 5T OTA end to end. This is the strongest generality claim available. | 1 full agent episode set, ~1 day |
| **G25** | ~~The analytical results are nominal-only.~~ **CLOSED** by `signoff/paper-draft/validation.md` §8 and §10.2 (`scripts/pvt_analysis.py`, `iip3_corners.py`; `extract_bench.py --pvt/--mc`). On the nine certified axes: `fc` span **1.022×** but `Q` span **1.002× / 1.027×** and pair coincidence **1.023×** — the SCALE moves and the SHAPE does not, because `Q` is a `gm` ratio. 64 mismatch draws: σ(`fc`) 3.37 Hz (vs 3.7 Hz from the certified 100-sample scorecard MC), σ(`Q`) 0.24 % / 1.26 %, two complex pairs in 64/64. IIP3 over the certified axes **−7.04 … −3.16 dBVp**, every corner's own IMD3 slope within 2 dB/decade of 40. **New finding**: the certified window is one-axis-at-a-time and the axes do NOT superpose — 7 of the 45 cross-product points lose a complex pole pair, including `tt / 0 °C / 1.40 V` whose three coordinates are each individually certified (`doc/journal/one-axis-certification-does-not-superpose.md`). Post-layout sensitivity is still open: the sweep runs on `pre_mim`. | Post-layout: re-run `--pvt` with `--dut post_lumped`. | ~5 min of simulation |
| **G15** | **Layout-lane history is not in `doc/`.** No journal entry, no experiment-log row, no campaign-report section covers the layout lane or the review rounds; the record lives in `layout/H12-pdk-cap/` and in commit messages. | Add a `doc/journal/` entry per durable lesson + an experiment-log row; the `lpf-gardener` agent will otherwise flag it. | 1–2 h |

### Housekeeping (fix before submission)

| # | gap | fix |
|---|---|---|
| **G16** | **Two IRN baselines in the repo** (50.18 on the 10 pts/dec grid, 49.98 on the re-certified 50 pts/dec grid). | Quote 49.98 and state the challenge as −20.0 %. See `results_schematic.md` §0. |
| **G17** | **Two `022-reuse-final` number sets** (prose docs vs the packaged JSON, differing by grid legalization) and **two 023 MC numbers** (log row 83 % / 55 % vs sign-off 82 % / 67 %). | Quote the packaged sign-off JSON everywhere. |
| **G18** | **`scorecard_post.json` reports `all_pass: true` while recording an S1 corner violation eight keys above** (reviewer's F23). | Rename to `all_pass_nominal`, or add `corner_pass: false`. Do not quote the bare `all_pass` in a paper. |
| **G19** | **The Q2 reversal is dated 2026-08-16 in `PLAN.md`** while the round-4 git activity is 2026-08-16. | Reconcile the date. |
| **G20** | **PLAN §5 and PLAN R2.2 are stale** — `axis_gap` listed as 6.0 while the layout ships 12.0, and an area prediction "within 1 %" that is wrong by 7× (reviewer's F21, still open). | Amend `PLAN.md`, or state in the paper that the plan is a *record of the decision at the time*, not a live spec — which is defensible, and arguably the more honest methodological position. |
| **G21** | **The run ledger is gitignored and partial** (253 rows, 3 days) — it cannot support a "total simulations" claim. | Use the defensible substitutes in `results_schematic.md` §10. |
| **G22** | ~~A pre-layout corner column disagrees with the certified sign-off~~ — **resolved 2026-08-16**: `REPORT.md` §5 (A7) ran both DUTs with the constant-current bias law (`LPF_BIAS_ALPHA` unset = 0 → 237.04° / 222.31° pre-layout, reproduced exactly on re-run); `PRELAYOUT.md` uses α = 1.1 (251.7° / 256.0°). REPORT §5's caption corrected. | Quote α = 1.1 rows for schematic PVT; REPORT rows only for the pre→post shift. |
| **G23** | **Round 4 has not been independently reviewed.** The review of record is round 3; round 4 changed 18 knob defaults and found three illegal `BOUNDS` endpoints. | Run `layout-reviewer` on round 4 — 1 agent episode (~30–40 min of machine time, see `workflow.md` §7.3). |
| **G24** | ~~No group-delay characterisation~~ — **closed 2026-08-16**: `results_group_delay.md` + `figures/group_delay.png` (nominal ×3 DUTs, 12 corners pre/post, 100-seed paired MC). | — |

---

## 6. Reproducing the pack

```bash
cd <repo>
make lint                                   # repo invariants incl. the provenance denylist
.venv/bin/python doc/paper/scripts/fig_pvt.py
.venv/bin/python doc/paper/scripts/fig_thd.py
.venv/bin/python doc/paper/scripts/fig_area_campaign.py
python3            doc/paper/scripts/fig_iterations.py    # needs PyYAML
cd experiments/023-replica-bias
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_prepost_bode.py
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_JOBS=14 \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_mc.py
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_BIAS_ALPHA=1.1 LPF_JOBS=14 \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_pvt_postlayout.py
```

See `figures/README.md` for what each script produces and where its inputs live.
