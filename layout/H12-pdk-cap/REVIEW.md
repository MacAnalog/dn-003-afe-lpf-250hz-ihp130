# Layout review — `H12-pdk-cap` (`lpf_core`), IHP SG13G2 — **round 3 (re-review)**

![annotated review](REVIEW.png)

**KIND: INDEPENDENT RE-REVIEW.** Nothing below is taken from `REPORT.md`. The GDS was rebuilt
twice from the committed generator, DRC / LVS / PEX (**CC and RC**, five kpex runs in total) were
re-run through the platform wrappers, every metric, every what-if and every corner was re-measured
on the block's own frozen benches, all **66** `BOUNDS` endpoints were re-swept with their own
builds and their own DRC runs, `--check-symmetry` was executed by the reviewer on five stored
iteration GDS files, and the 13-entry `iterations/` trail was re-hashed and partly re-built.
Round-1/2 ids are carried; **F22–F25 are new**. Per-finding zooms: [`review_crops/`](review_crops/);
machine-readable form: [`REVIEW.yaml`](REVIEW.yaml) (`layout-review/1`, `validate-review` → ok).

| | |
|---|---|
| reviewed GDS | rebuilt by the reviewer, sha256 `fc59cfd7ef38b5d91d0e78ab2a0cf56aa8c284578ac7ec29abe1be04cf0500ed` — **identical to the designer's claim, to `iterations/it13`, and identical on two independent builds** |
| generator | `layout/H12-pdk-cap/gen_H12_pdk_cap.py` sha `6ae114ad…fce65e`, default `LayoutParams` (33 knobs, none moved) |
| certified netlist of record | `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`, sha256 `ef78d6f8d4e28cfbf18dc7abf6bd4066070fdf9f63546d430f16c4d71ffaf3c7` |
| netlist LVS actually compared against | `layout/H12-pdk-cap/asbuilt/core_lvs.sp`, sha256 `57ee5906a02982a840f2c2db2aa5c6a4c797bd6ab355974b525abd6e833d46b1` (provenance re-derived below) |
| PEX modes run by the reviewer | kpex 2.5D **CC** (71 C / 0 R, three runs) **and RC** (71 C / 8 609 R, three runs) |
| symmetry axis | x = 0 |
| **verdict** | **PASS with notes** — the only remaining spec miss is the `cap_bcs ×0.9 + iref ×0.9` corner the block owner approved delivering with (PLAN R2.8 Q3), and it is on the report's front page with a correct, reproducible attribution |

## Findings

Severity is the **residual** severity now. `verdict` is scored by measurement, never from the
changelog. **19 of the 21 round-2 findings are fixed or approved-deferred; 2 remain open on
substance (F1, F2) and 4 are new (F22–F25).**

| # | sev | verdict | where (net / device / rule) | evidence (number, file:line, XOR area) | effect (metric, how much, model) | fix → generator parameter | expected magnitude |
|---|---|---|---|---|---|---|---|
| **F1** | major *(blocker but for the approved Q3 decision)* | **open (accepted)** | corner `cap_bcs ×0.9` + `iref ×0.9`, whole cell (objective) | reviewer's own build → own extraction → own bench: **ph_max = 329.7509° < 330°, S1 FAIL**. REPORT's 329.751 reproduces to 4 decimals. Round 2: 329.7458; round 1: 329.299; **pre-layout 331.018 PASS**. 9-point `AXES` (pre *and* post) + 5 `cornerCAP` points re-run on the reviewer's PEX: **every corner that passed pre-layout still passes except this one**. Attribution re-measured at fixed `axis_gap = 12`: F16 = **+0.0722°**, F17 = **−0.0568°**, net **+0.005°** | ph_max **−0.2491°** short (what-if) | **design lane** — `iref` trim, small `C1`/`C2` re-allocation, shorter `L` on `xm4`, fewer `xm9` fingers. No layout lever remains: the 0.062° round 2's review called layout-reachable has been taken | 330.0° at that corner, or the formal re-scope already granted by PLAN R2.8 Q3 |
| **F2** | major | **worse (by design, disclosed)** | `net2` 32.328 fF, `net3` 32.329 fF (budget) | reviewer kpex CC, C to the bench ac grounds: **32.328 / 32.329 fF** vs `brief.json` `budget_c_ff` 22.8 (pvt 9.59) = **1.42× / 3.37×**. Round 2: 28.270 (1.24×); round 1: 50.04. The +4.06 fF is the F17 price, and the mechanism reproduces on the rebuilt GDS: `net2`'s Metal1 **4.971 → 29.542 µm²**, perimeter **44 → 232 µm**. One-sided Δ **−0.001 fF** (allowed 45.7) and between-halves C **0.0000 fF** (allowed 11.4) both pass, and **all 21 `cross_coupling` budgets in `brief.json` pass with ≥ 99 % margin** | ph_max **−0.741°** (what-if; deleting every `net2`/`net3` C gives 331.9003) | **`net23_strap` = `min_m1`** recovers 0.050° and 3.2 fF — but at the cost of BRIEF §2.1. The designer's choice is the right one; A4 now needs the design lane (F1) | ≤ 22.8 fF nominal, or an amended A4 that prices BRIEF §2.1 |
| **F3** | major | **deferred (approved)** | n-well islands of `net4`/`net1`/`rep_x`/`vout_*`/`vout*` (well) | reviewer re-measured on the rebuilt GDS: **8 islands, every one tapped** (tap 12.5–261 µm²), **NWell mirror-XOR exactly 0.0000 µm²**; areas 327.200 / 275.851 / 141.620 µm². Lumped-`Cj` what-if on a copy of the reviewer's PEX at 0.05 / 0.12 fF/µm²: ph_max **331.0515 / 330.9004** | ph_max **−0.108…−0.259°** (hand) | **new feature (platform)** — `Cj(area, perimeter, Vbias)` in `signoff.postlayout`. Deferred by the approved PLAN R2.7; `well_margin` is at the `NW.c` floor | a `Cj` term in the splice so the corner set is measured, not bounded |
| **F22** | minor | **new, open** | `XOR_BALANCE` / `budgets_for`, Metal3 (symmetry) | reviewer ran `--check-symmetry` on `iterations/it01/layout.gds` under each relaxing knob. **Default: Metal3 half-plane balance budget 4.814 µm², it01 measures 21.0888 → FAIL — that number *is* F6.** With `cap_spine_side="left"` the same budget becomes **100.000 µm²**; with `bankA_order="c19_axis"`, **48.145 µm²** — 4.7× and 2.3× F6's own signature, so **F6 would not fire**. `Metal5`'s XOR budget likewise goes 104.14 → **1301.73** in `c19_axis`, past it01's 948.78. it01 still FAILs *overall* everywhere (15 rules default → 10 / 6 / 13 singly relaxed → **4** with all three stacked), so these are **exceptions, not holes** — but the discrimination F18 was raised to restore is configuration-dependent, and that is not stated | guard-rail **−11 of 15 rules** on the known-bad artifact (what-if) | **`XOR_BALANCE` / `budgets_for`** — keep an absolute Metal3-balance floor (≈ 10 µm²) in every configuration; or the mirror-and-swap primitive REPORT §9 already names | the F6 signature rejected at every legal `BOUNDS` point, not only at the default |
| **F21** | minor | open | cell outline, `axis_gap`, PLAN §5 / R2.2 (other) | reviewer's rebuild: bbox (−216.84, −10.00)…(216.84, 559.86) = **247 136.8848 µm² — identical to round 2**, so REPORT §1's "round 3 costs no area" is verified. But PLAN R2.2's "within 1 %" is still wrong by 7× against round 1's 230 624 µm² and `PLAN.md` has not been touched since 2026-08-16 00:19; PLAN §5 still lists `axis_gap = 6.0` while the layout of record ships **12.0** (flagged in REPORT's *Assumptions*, as `bank_gap` and `cap_gap` were) | area Δ **0** vs round 2 (measured) | none — amend PLAN R2.2 and §5 | a plan whose area prediction and knob defaults match the layout of record |
| **F11** | note | open | `xc13`/`xc17` top plates (pex) | reviewer reproduced the MIM-stripped flow exactly — its CC netlist is **byte-identical to the committed `asbuilt/core_pex.sp`**. `xc13`/`xc17` top plates measure **3 285.36 µm² each** (2 units of 1 642.68) and are absent from the extraction; kpex's `cmim_top` is `"<TODO>"` | up to −0.39° (hand) | **new feature (platform)** — `tech_json=` on `run_pex`, or a MIM-aware kpex tech | an extraction that keeps the MIM top plates |
| **F12** | note | open | `net2`/`net3` TopMetal1 → `xm4` gate (leakage/antenna) | reviewer measured on the rebuilt GDS: `net2` TopMetal1 **3 242.344 µm²** / `xm4` gate 1.5 × 45 = 67.5 µm² = **48.03 : 1** (round 2: 48.11). The executed KLayout deck still contains no antenna rule table | antenna ratio 48 (hand) | **new feature** — chip-level antenna check or a lower-metal jumper; a diode is forbidden by BRIEF §3 (6.17 pA) | a documented antenna number before tape-out |
| **F13** | note | open | `vbp` pad at (10, −10)…(14, −8) (lvs) | reviewer's own LVS run: `lvs/lpf_core_extracted.cir` header is `.SUBCKT lpf_core vbn vss vout_1 vout_2 net3 vbr net2 vinp vinn vdd net4 voutp rep_x voutn net1`; **`grep vbp` returns 0 lines**, yet the deck reports *Netlists match* | 1 of 8 pins unchecked (hand) | **new feature (platform)** — pin-list assertion inside `signoff.lvs` | the extracted pin set asserted against the certified header |
| **F14** | note | **deferred (approved)** | `xr2` / `rep_x` bridge row (matching) | the regenerated LVS reference still carries `Mr1 … w=12u l=31u` (the `xr1` parallel-W fold works) and the `xr1_split` True/False builds differ in sha, so that half is real. `xr2` is still `sign=−1` only; its geometric residual is the 7.556 µm² of Metal1 XOR at y 234.76…242.21 (F19) | 0.8 Hz of `fc` per mV on the `rep_bridge` ratio (hand) | **new feature** — `xr2_split`. Approved deferral, PLAN R2.8 Q4 | both replica ratios orientation-balanced, or the residual measured |
| **F15** | note | open | all MIM banks (other) | reviewer measured merged MIM (36/0) = **122 253.49 µm²** in 51 units against a cell of 433.68 × 569.86 = 247 136.88 µm² → **49.47 %**, and **69.9 %** of the PDK's 174 800 µm²/chip guidance. `MIM.gR` is in the executed deck and does not fire. Rounds 2 and 3 changed MIM area by exactly **0** | area/architecture flag (hand) | block-level decision — total C is set by `design.json` | block owner acknowledges before a second instance is placed |
| **F19** | note | **fixed (attribution)** | `xr2` / `rep_x` Metal1, y 234.76…242.21 (symmetry) | reviewer measured the six Metal1 XOR polygons on the rebuilt GDS: **2 × 8.0000 µm² at (±10…±14, −10…−8)** = the `vbp` pad, and **2 × 3.5240 µm² at y 240.91…242.21** plus **2 × 0.2540 µm² at y 234.76…236.11** — all four inside the bridge row's n-well (y 234.26…243.63), **none** in the `gmf_b` row where `xr1` is. REPORT §8's coordinates are exact; round 2's `xr1` attribution is corrected in both the report and the generator comment | no ac effect (`rep_x` is an ac ground); the 23.556 µm² of geometry falls to 16.0 once `xr2_split` exists | **new feature** — `xr2_split` (= F14) | the declared Metal1 exception names `xr2` — **met** |
| **F23** | note | **new, open** | `scorecard_post.json` (other) | the file's `passes` / `violations: []` are the **nominal** bench (which the reviewer reproduces exactly); `corner_miss` carries `ph_max 329.751` against a `limit_deg 330.0`; the **last key is `"all_pass": true`**, unscoped. An optimizer or dashboard keying on it reads a clean pass on a cell whose S1 is broken at a certified corner | machine-readable honesty (hand) | none — rename to `all_pass_nominal`, or add `corner_pass: false` | a scorecard whose top-level boolean cannot contradict its own corner table |
| **F24** | note | **new, open** | kpex RC mesh (pex) | reviewer ran kpex **three times CC and three times RC** on the same MIM-stripped GDS. **CC is byte-deterministic across three runs** — the CC half of the designer's naming gotcha did *not* reproduce. **RC is not**: two RC runs differ in **17 221 lines** of `net.$n.m` sub-node naming while the 71 C cards and every device card are byte-identical. Measured on three RC meshes: `fc` = **248.6366 / 248.6763 / 248.6833 Hz**, a **0.047 Hz spread — larger than the 0.041 Hz CC↔RC delta REPORT §4 quotes as its evidence**. All three converged without a `.nodeset`; the pathological shorted-DC mesh was not reproduced in three draws | `fc` **±0.047 Hz** of mesh scatter (what-if) | **new feature (platform)** — a sorted-card-set comparator and an op-sanity gate next to `run_pex` | an RC cross-check reported to its own repeatability, and a mesh that cannot silently short the op |
| **F25** | note | **new, open** | `budget_c_diff_ff` column, REPORT §6 (budget) | the round added `brief.json`'s between-halves budget — the column whose absence let F16 sit uncounted — but prints `—` for `vout_1`/`vout_2` and `voutp`/`voutn`. `brief.json` defines it for both (**1 680 fF** and **460 fF**) and the reviewer measures **C(`vout_1`,`vout_2`) = 4.5576 fF** and **C(`voutp`,`voutn`) = 7.4474 fF** | both pass with 99.7 % / 98.4 % margin (measured) — completeness, not a breach | none — print the column for every pair the brief defines it for | a between-halves column with no blank cells where the brief has a number |
| **F16** | note | **FIXED** | `net2`↔`net3` Metal5 lanes (coupling) | reviewer's own kpex CC: **71 C elements (round 2: 78) and no `net2`–`net3` card at all**. The Metal5 spine labels now sit at x = **−4.900 / +4.900** (round 2: ±1.900) — **9.8 µm apart instead of 3.8**. `C(net4,net1)` likewise absent (round 2: 0.0257 fF). Isolated at fixed `axis_gap = 12` and fixed strap, the reviewer measures `lane_mid` 1.9 → 4.9 = ph_max **331.1465 → 331.2093** nominal and **329.7355 → 329.8077** at A7. Area **247 136.8848 µm² unchanged**, DRC 0 at both endpoints | ph_max **+0.072°** at corner A7 (what-if) | **`lane_mid` = 4.9** (new knob, `BOUNDS` (1.9, 4.9), clamped to `axis_gap/2 − 1.1`) | C(`net2`,`net3`) = 0 and the differential load counted in the budget — **met** |
| **F17** | note | **FIXED** | `xm9`/`xm10` vs the four `xr3` units, rows y 135.04 / 150.94 / 166.84 (matching) | reviewer measured per-device-window Metal1 on the rebuilt GDS and XOR'd the `xm9`/`xm10` units against the `xr3` units of *both* neighbouring rows after a pure row translation: **0.0324 µm² in 4 polygons** (four 0.09 × 0.09 µm corner slivers at the lane via pad) against **140.4637 µm²** of per-device Metal1 — **0.023 %**. Round 2's row delta was **21.17 µm²**. Activ / GatPoly / Cont are identical to 4 decimals on all three rows. The residual Metal2 +0.0342 and Metal5 +0.0342 µm² on the live row is the connection to the `net2`/`net3` lane itself, which only `xm9`/`xm10` have. **The disclosed cost verifies exactly**: at fixed `lane_mid = 4.9`, `min_m1 → lane_m1` = **331.2093 → 331.1595** nominal (**−0.0498**, REPORT says −0.050) and **329.8077 → 329.7509** at A7 (**−0.0568**, REPORT says −0.057); the `min_m1` build's sha `c0507860…` is byte-identical to `iterations/it09` | ph_max **−0.0568°** at A7 (what-if) | **`net23_strap` = `lane_m1`** (`min_m1` kept as a knob; both endpoints DRC-clean) | identical S/D/G routing on all six units (BRIEF §2.1) — **met to 0.03 µm²** |
| **F18** | note | **FIXED** | `--check-symmetry`, `XOR_BUDGET` / `XOR_BALANCE` (symmetry) | reviewer ran the CLI itself on five stored GDS files. **`it01` (round 1, the layout F6 was raised against): FAIL on 15 rules across 8 layers** — Metal1 XOR 47.556 > 40.91; Metal2 XOR 24.0 > 2.00 and balance −4.0 > 1.34; **Metal3 balance 21.0888 > 4.81**; Metal4 balance −4.0 > 1.00; Metal5 XOR 948.78 > 104.14; TopMetal1 XOR 847.048 > 71.85; Via1/Via2 XOR 1.9494 > 0.50 and balance −0.3249 > 0.20–0.22; Via3/Via4 balance −0.3249 > 0.20; TopVia1 XOR 1.4112 > 1.17 and balance −0.3528 > 0.20 — **character-for-character the output REPORT §9 quotes**. `it08`, `it09`, `it10` and `it13` all **PASS** | the guard-rail now fires on the defect it exists for (what-if) | **calibrated against two anchors** | the assertion FAILS on `it01` — **met** (see F22 for the configuration-dependent residual) |
| **F20** | note | **FIXED** | Metal4, `Via1`…`Via4`, `TopVia1` (symmetry) | reviewer's own mirror-XOR on the rebuilt GDS reproduces REPORT §8 to 4 decimals: Via1 0.0000/3.357, Via2 0.1444/2.960, Via3 3.8988/4.115, Via4 3.8988/4.115, TopVia1 1.4112/1.411, Metal4 48.0000/48.866 — and the **half-plane balance is exactly 0.0000 µm² on all eight balance layers**. The saturation explanation checks out: the Via3/Via4 XOR is **108 polygons of 0.0361 µm² each**, i.e. every via of the F8 swapped pair, at different y on the two halves | six previously unreported layers now measured (hand) | **`XOR_BUDGET` + `XOR_BALANCE`** | every drawn layer in the symmetry table with a measured number and a budget — **met** |
| **F4** | note | **FIXED** | `LayoutParams` / `BOUNDS` (knob) | reviewer independently built and DRC'd **all 33 knobs at both endpoints (66 builds, own build dirs, own `run_drc`)**: **66/66 build ok, 66/66 DRC PASS, 0 violations**, and **33/33 knobs change the GDS** (33 distinct min-vs-max sha pairs). `lane_mid` 1.9 → `dc25783d…`, 4.9 → `fc59cfd7…`; `net23_strap = min_m1` → `c0507860…` = `iterations/it09` — exactly REPORT §7's claims | claim "**66/66 BOUNDS endpoints DRC-clean**" **verified in full** | — | met |
| **F5** | note | **FIXED** | bank A order (routing) | reviewer measured on the rebuilt GDS: `net2` TopMetal1 bbox (−45.83, 17.83)…(−5.90, 122.74), 3 242.344 µm², perimeter 400.47, 1 polygon; `net3` is its exact mirror on all six numbers. `bankA_order` is a `LayoutParams` field, both endpoints DRC-clean | haul mismatch 0 (hand) | — | met |
| **F6** | note | **FIXED** | `net2`/`net3`, `net4`/`net1` (symmetry) | per-net geometry on the reviewer's rebuild: `net2` and `net3` have **identical area, perimeter and shape count on every layer** (Activ 8.800, GatPoly 84.735, Metal1 29.542, Metal2/3/4 0.433, Metal5 22.743, TopMetal1 3 242.344) with mirrored bboxes. Extracted Δ(`net2`,`net3`) = **−0.001 fF** (0.17 aF of kpex substrate rounding), Δ(`net4`,`net1`) = **0.089 fF** | Δ ≪ the 45.7 / 166 fF asymmetry budgets (what-if) | — | met |
| **F7** | note | **FIXED** | bias array dummy rows (matching) | Activ bands read back from the rebuilt GDS: **five identical nmos rows** at y 119.14 / 135.04 / 150.94 / 166.84 / 182.74, four devices each, 2 446.08 µm² per row, with the live `xr3` / `xm9`-`xm10` / `xr3` rows in the middle; the regenerated LVS reference carries `Mdumn w=336u` | every live unit has an identically drawn row above and below | — | met — and **F17 closes the routing half of the same rule** |
| **F8** | note | **FIXED** | `xc19` / `xc12` plate assignment; HD2 (symmetry) | Δ(`vout_1`,`vout_2`) = **−0.481 fF** (budget 6 710) and Δ(`voutp`,`voutn`) = **21.058 fF** (budget 1 800); `voutp` 460.060 fF = 1.01× its pvt budget. **On HD2 the reviewer did not need a second extraction**: a *pure reordering* of the parasitic C cards — electrically identical, same file otherwise — moves **round 2's own netlist from −104.2215 to −98.9640 / −99.2739 dB (5.3 dB)** while THD and HD3 reproduce to 0.002 dB. The same permutation on round 3's netlist gives −97.17…−97.37 dB; symmetrising the residual 11.2 aF cross-terms moves it 0.13 dB | **HD2 is this bench's numerical floor** — round 2's −104.22 was a draw, not a property, and round 3's −97.17 is the same floor. HD2 is not specced; S7 THD = **−49.7008 dB** against −40 | — | met; **do not spend a round chasing HD2 on this bench** |
| **F9** | note | **FIXED** | dead knobs (knob) | reviewer's own endpoint sweep: **33 knobs, 33 distinct min-vs-max GDS sha pairs, no exceptions** | one optimizer dimension per knob, none wasted | — | met |
| **F10** | note | **FIXED** | `BOUNDS` vs `LayoutParams` (knob) | reviewer parsed `BOUNDS` from the committed generator (33 entries) and swept it; `validate()` asserts `set(BOUNDS) == set(LayoutParams fields)` on every build and `clamp()` resolves the couplings so every endpoint is buildable. REPORT §7's table prints exactly the ranges the reviewer swept | contract drift 0 | — | met (**PLAN §5's `axis_gap` default is now stale — F21**) |

## What reproduced

Everything the designer claimed reproduced, essentially all of it exactly. Round 3 is the most
completely reproducible round in this lane so far — the reviewer's own CC netlist came out
**byte-identical** to the committed one.

| gate | designer | reviewer | |
|---|---|---|---|
| GDS sha256 | `fc59cfd7…0500ed` | `fc59cfd7…0500ed`, **two independent builds** | **match**, deterministic |
| outline / area | 433.68 × 569.86 µm, unchanged from round 2 | (−216.84, −10.00)…(216.84, 559.86) = **247 136.8848 µm²**, byte-for-byte the round-2 area | match — round 3 really is free |
| DRC | 0, **no waivers** | **0 violations**, PDK KLayout deck via `signoff.run_drc`, `--no_density` | match. No waiver claimed, none needed |
| LVS | match | **matched** against `core_lvs.sp` sha `57ee5906…3d46b1` | match |
| LVS reference *provenance* | "regenerates byte-identically to round 2" | regenerated from the **round-3** generator → **byte-identical** to the committed file; diff against `to_lvs_reference(core.sp)` (certified sha `ef78d6f8…af3c7`) shows **exactly** the four declared edits (`0`→`vss` + pin; `xc1`/`xc10` terminal swap; `Cc19` 8 → 4+4 and `Cc12` 7 → 4+3 anti-oriented; `Mdumn w=336u` + `Mdump w=24u`) **and nothing else** | match |
| PEX CC | 71 C, 0 R | 71 C, 0 R; the reviewer's own subckt is **byte-identical to `asbuilt/core_pex.sp`**; three CC runs byte-deterministic | match |
| PEX RC | 71 C, 8 609 R | 71 C, 8 609 R; three meshes, all converged without a `.nodeset`, `fc` 248.6366 / 248.6763 / 248.6833 | match (but see **F24**) |
| **C(`net2`,`net3`) 1.379 → 0.000 fF** | claimed | **the element does not exist in the reviewer's netlist**; 78 C → 71 C; lane labels at x = ±4.900 (was ±1.900) | **verified** |
| **F17 disclosure −0.050° / −0.057°** | claimed | at fixed `lane_mid = 4.9`: **331.2093 → 331.1595** (−0.0498) and **329.8077 → 329.7509** (−0.0568) | **verified to 0.0002°** |
| **F18 calibration** | it01 FAIL / it08, it11, it12 PASS | reviewer ran `--check-symmetry` itself: **it01 FAIL, 15 rules / 8 layers, character-identical to §9's quoted output**; it08 / it09 / it10 / it13 **PASS** | **verified** |
| scorecard (CC) | fc 248.639 · ph 331.1595 · a1000 −49.222 · ripple 0.0347 · peak 0.0136 · dc −0.0081 · IRN 29.1942 · P 11.9136 · THD −49.701 · HD3 −49.898 · HD2 −97.17 | fc 248.6388 · ph **331.1595** · a1000 −49.2221 · ripple 0.0347 · peak 0.0136 · dc −0.0081 · IRN 29.1942 · P 11.9136 · THD −49.7008 · HD3 −49.8985 · HD2 −97.1706 | match, **all S1–S7 pass at nominal** |
| **corner A7** | 329.751 **FAIL** | **329.7509 FAIL** (`S1 biquad-order certificate`), on the reviewer's own extraction | match |
| all other corners | REPORT §5 | 9-point `AXES` (pre **and** post) + 5 `cornerCAP` points re-run on the reviewer's PEX: tt 331.16 / ss 331.16 / ff 330.96 / sf 331.02 / fs 331.23 / 1.65 V 331.19 / `cap_typ` 331.16 / `cap_wcs`×1.1 332.39 — **all PASS**; 1.35 V, −40 °C, +125 °C fail pre-layout too | match |
| what-if attribution | 0.741 / 0.483 / 0.693 / 0.095 / −0.058 / 1.172° | **331.9003 (+0.7408), 331.6430 (+0.4835), 331.8523 (+0.6928), 331.2542 (+0.0947), 331.1017 (−0.0578), 332.3318 (+1.1723)** | match, every row |
| F3 lumped-`Cj` | −0.108…−0.259° | **331.0515 / 330.9004** | match |
| symmetry (A10) | nine physical layers 0; Metal1 23.556, Metal2 0.274, Metal3 280.338, Metal4 48.000, Metal5 39.200, TopMetal1 35.060, Via1 0, Via2 0.1444, Via3/Via4 3.8988, TopVia1 1.4112; balance 0.0000 on eight layers | **identical to 4 decimals**, and Activ / GatPoly / Cont / ThickGateOx / NWell / pSD / nSD / MIM / Vmim **exactly 0.0000** | match |
| BOUNDS endpoints (A9) | 66/66 DRC-clean, 0 dead knobs | **66/66 build + DRC clean, 0 violations; 33/33 knobs change the GDS** | match, **verified in full** |
| the two recorded gotchas | kpex naming non-determinism; HD2 −104.2 → −97.2 is bench floor | **RC confirmed (17 221 differing lines, same C and device cards); CC *not* confirmed (3 byte-identical runs)**. **HD2 confirmed, and more strongly than the designer's own proof**: a pure C-card permutation of round 2's netlist alone spans 5.3 dB | 1 of 2 halves of gotcha 1; gotcha 2 fully |

**Trail audit (`iterations/`) — passes.** **13 entries for the 13 rounds the REPORT claims**
(it09–it13 are round 3). **13/13 stored `layout.gds` files hash to the sha recorded in
`iterations.yaml`.** The **last entry's `gds_sha256` is `fc59cfd7…0500ed` — the GDS the reviewer
rebuilt — and its `gen_sha256` is `6ae114ad…fce65e`, the committed generator.** `it09`…`it13`
**rebuilt from their own stored `gen.py` reproduce `c0507860…` / `fc59cfd7…` (×4) exactly**;
`it09`'s sha is also what `net23_strap = min_m1` produces from the committed generator, so the
2×2 is internally consistent. REPORT §10's table, regenerated with
`spicexplorer-layout iterations-md`, is **identical to the committed one** — generated, not typed.
The diffs show what their notes claim: `diff_it08_it09` boxes **33** changed regions in island A
(the lane move); `diff_it09_it10` boxes **6** Metal1/Metal2/Via1 regions on the middle bias row
(12.1, 12.1, 10.7, 10.7, 2.7, 2.7 µm² — the drain bar returning); `diff_it10_it11`,
`diff_it11_it12` and `diff_it12_it13` **draw nothing at all**, consistent with their byte-identical
GDS and their "assertion-only / documentation-only" notes.

**Extraction-driven budget (kpex CC, reviewer's own run) — used vs `brief.json`:**

| net | round 1 | round 2 | **round 3** | allowed nom / pvt | ratio | one-sided Δ | allowed asym | **C between halves** | allowed diff | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `net2` | 50.04 | 28.270 | **32.328** | 22.8 / 9.59 | **1.42× / 3.37×** | **−0.001** | 45.7 ✓ | **0.0000** (r2: 1.3792) | 11.4 ✓ | over budget (**F2**) |
| `net3` | 44.94 | 28.270 | **32.329** | 22.8 / 9.59 | 1.42× / 3.37× | " | " | " | " | over budget |
| `net4` | 77.30 | 67.578 | **67.338** | 82.8 / 34.8 | 0.81× / 1.93× | **0.089** | 166 ✓ | **0.0000** (r2: 0.0257) | 41.4 ✓ | ✓ |
| `net1` | 67.27 | 67.471 | **67.249** | 82.8 / 34.8 | 0.81× / 1.93× | " | " | " | " | ✓ |
| `vout_1` | 231.73 | 165.057 | **166.059** | 3350 | 0.05× | **−0.481** | 6710 ✓ | **4.5576** | 1680 ✓ | ✓ (**F25**: not printed) |
| `vout_2` | 75.93 | 165.537 | **166.540** | 3350 | 0.05× | " | " | " | " | ✓ |
| `voutp` | 505.50 | 459.418 | **460.060** | 905 / 455 | 0.51× / **1.01×** | **21.058** | 1800 ✓ | **7.4474** | 460 ✓ | ✓ nominal (**F25**) |
| `voutn` | 352.55 | 438.359 | **439.002** | 905 / 455 | 0.49× / 0.96× | " | " | " | " | ✓ |
| A ↔ B | 0.0000 | 0.0000 | **0.0000** | 0.277 / 0.116 | — | — | — | — | — | **absent, not small** |

`net2`'s pairs, measured: `0` 26.6688, `vbn` 3.9297, `vinp` 1.6393, `vout_1` 0.6323,
`vout_2` 0.1273, `vbr` 0.0906 — **`net3` no longer appears in the list at all**. All **21**
`cross_coupling` budgets in `brief.json` are met with ≥ 99 % margin. No `Metal1` of any signal net
runs over *foreign* diffusion (measured: 0.000 µm² for all ten signal nets).

**The three things the designer asked to be audited.**

1. **The §9 configuration-declared relaxations — exceptions, not holes, but with a named cost.**
   Stacking all three relaxations still leaves `it01` FAILing (4 rules), so no legal knob setting
   turns the guard-rail off. What *is* lost is the specific discrimination F18 restored: the Metal3
   half-plane balance rule — the one that catches F6 — is relaxed from 4.814 to **100.0 / 48.1 µm²**
   against F6's own 21.089 µm² signature in two of them (**F22**). The honest fix is an absolute
   floor, not a fraction.
2. **The §5 F17 trade — correct, and the disclosure is exact.** −0.0498° nominal / −0.0568° at A7,
   against the report's −0.050 / −0.057; the matching benefit is real and now measurable
   (0.0324 µm² of Metal1 XOR across the six-unit class, from 21.17 µm²). Trading 0.05° of an
   already-accepted corner for the brief's tightest matching rule is the right call, and the round
   said so out loud rather than banking the number.
3. **The two gotchas — one confirmed, one confirmed and strengthened, one half not reproduced.**
   RC mesh non-determinism is real (17 221 differing lines). CC naming non-determinism did **not**
   reproduce in three runs — the claim should be scoped to RC. HD2-as-bench-floor is right, and the
   reviewer's cleaner proof (a pure card permutation, no re-extraction) spans 5.3 dB on round 2's
   own netlist.

## What I could not check

* **MIM top-plate environment capacitance** — kpex's `cmim_top` is `"<TODO>"`; extraction runs on
  the stripped GDS (F11). The ≤ 15 fF bound is carried, not closed.
* **N-well/p-substrate junction capacitance as a model** — only the lumped-`Cj` what-if bound (F3).
* **Antenna ratios** — the IHP KLayout deck ships no antenna rule table (F12).
* **Post-layout mismatch Monte Carlo** — which is what would *price* F7, F14 and F17's benefit.
  F17 is now verified **geometrically** (0.0324 µm²), not statistically.
* **The full 45-point PVT grid post-layout** — I ran the 9-point `AXES` set (pre *and* post) + the
  five `cornerCAP.lib` points, on my own PEX netlist.
* **Magic DRC / netgen LVS second opinion.**
* **The pathological RC mesh the designer reported** (`fc` 0.11 Hz, 768 mW) — three reviewer RC
  draws all converged, so I can neither reproduce nor bound its frequency (F24).
* Fill/density and sealring are absent by PLAN §6, so pre- and post-layout are equally fill-free
  and the comparison is consistent; a chip-level fill will move the budget.

## Verdict — **PASS with notes**

**One sentence: every gate reproduces exactly on the reviewer's own build, extraction and benches,
all five round-3 fixes (F16, F17, F18, F19, F20) are confirmed by measurement, and the single
remaining spec miss is the `cap_bcs ×0.9 + iref ×0.9` corner the block owner approved delivering
with — reported on the front page with an attribution that reproduces to 0.0002°.**

This is a narrow round that did exactly what it said and nothing else: 5 findings closed, the GDS
byte-reproducible and byte-identical to the last trail entry, DRC 0 with no waivers, LVS matched
against a byte-identical four-edit derivation of the certified netlist, a CC netlist byte-identical
to the committed one, 66/66 endpoints clean, and a 13-entry trail whose every hash, table and
picture checks out. Two of the round's harder claims — that HD2 is bench floor and that the
symmetry guard-rail now rejects round 1 — I re-derived independently and by a different route, and
both hold.

Top three:

1. **F1 — `S1` is still 0.2491° short at a certified corner (329.7509° vs 330.0°).** This is the
   only spec miss, it is design-lane, and PLAN R2.8 Q3 pre-authorised delivering with it
   documented — which the designer did, on the front page, with the numbers. A reviewer records
   the spec state: without that approved decision this row is a blocker.
2. **F2 — `net2`/`net3` moved *further* over the brief's balanced budget (1.24× → 1.42×).** Bought
   deliberately to honour BRIEF §2.1, priced (+4.06 fF), disclosed, and its whole effect is already
   inside F1's number. No new failure — but A4 is now unreachable from the layout lane.
3. **F22 (new) — the recalibrated guard-rail's F6-catching rule is switched off by two legal knob
   settings.** `cap_spine_side="left"` and `bankA_order="c19_axis"` relax the Metal3 half-plane
   balance budget to 100.0 / 48.1 µm² against F6's own 21.089 µm². `it01` still fails overall, so
   this is an exception rather than a hole — but it is the exact failure mode F18 was raised to end,
   and an absolute floor closes it in one line.

— `layout-reviewer`, 2026-08-16. Findings, anchors and reproduction data: `REVIEW.yaml`; zooms:
`review_crops/` (20 of the 25 findings have drawable geometry; **F4, F9, F10, F23 and F24** are
legend-only by the DSL's `net` anchor — a `BOUNDS` sweep, a JSON key and an extraction mesh have
no place in the layout).
