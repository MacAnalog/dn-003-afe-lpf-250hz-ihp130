# Layout report — `H12-pdk-cap` (`lpf_core`), IHP SG13G2 — **round 3**

**KIND: LAYOUT OF RECORD (generated).** Everything below was produced by the
committed generator plus the platform signoff wrappers; nothing was hand-drawn
and no GDS was hand-edited. Round 3 is a **narrow fix pass** against the round-2
re-review ([`REVIEW.md`](REVIEW.md) / [`REVIEW.yaml`](REVIEW.yaml), verdict
**FAIL**): **F16, F17, F18, F19, F20** and the `BOUNDS` endpoint table. It opens
no new floorplan question — the approved `PLAN.md` §Round 2 still governs — and
it deliberately changes nothing else. Hand off to `layout-reviewer`; this report
does not self-certify floorplan quality.

> ## Front page: the same acceptance target is still missed, and now for a smaller reason
>
> **R2.10 A7 — `cap_bcs` ×0.9 with `iref ×0.9`: `ph_max` = 329.751° < 330°, S1
> still FAIL.** Round 2 was 329.746°, round 1 329.299°, pre-layout 331.018°
> **PASS**. Round 3 nets **+0.005°**: **+0.062°** from F16 (the lane offset is a
> knob now and the 1.379 fF `net2`↔`net3` coupling is *gone*) **−0.057°** spent
> honouring the brief's tightest matching rule (F17). The block owner approved
> delivering with this miss documented (PLAN R2.8 Q3); the residual is
> design-lane, as §6 shows. **A1–A6 and A8–A11 pass.**
>
> The three things round 3 actually changed:
> 1. **F16 — `lane_mid` is a knob** (was the module constant `LANE_MID = 1.9`).
>    Default 4.9 µm with `axis_gap` 6 → 12: the two `net2`/`net3` spines now run
>    **9.8 µm apart instead of 3.8**. Extracted **C(`net2`,`net3`) 1.3792 →
>    0.0000 fF** and **C(`net4`,`net1`) 0.0257 → 0.0000 fF** — the elements are
>    absent from the netlist (78 C → 71 C). Zero area, zero DRC cost.
> 2. **F17 — `net23_strap` default `min_m1` → `lane_m1`.** All six members of
>    the 0.35 mV `rep_sink` class are drawn *and routed* identically again
>    (BRIEF §2.1). **Disclosed cost: −0.050° nominal, −0.057° at the corner,
>    `net2` 29.106 → 32.328 fF.** The brief's matching rule outranks 0.05° of an
>    optional corner; `min_m1` stays as a knob.
> 3. **F18/F19/F20 — the symmetry guard-rail now fires on the defect it exists
>    for.** `gen_H12_pdk_cap.py --check-symmetry iterations/it01/layout.gds`
>    (round 1, the layout F6 was raised against) **FAILS on 15 rules across 8
>    layers**; it08 (round 2), it11 and it12 **PASS**. Via layers and Metal4 are
>    in the table, and the Metal1 exception is re-attributed to `xr2` (F19).

| | |
|---|---|
| plan | `layout/H12-pdk-cap/PLAN.md` §Round 2 (**APPROVED 2026-08-16**); round 3 opens no new plan gate |
| brief | `layout/H12-pdk-cap/BRIEF.md` + `brief.json` |
| review answered | `REVIEW.md` round 2 (2026-08-16, FAIL) — **F16, F17, F18, F19, F20** + the `BOUNDS` table |
| generator | `layout/H12-pdk-cap/gen_H12_pdk_cap.py` sha256 `6ae114ad2690935155d07a2b9fbb984e574445f72a4382770e02d99498fce65e`, **33 knobs** (was 32; `lane_mid` is new) — identical to `iterations/it13/gen.py`, the last entry of the trail |
| sizing record | `signoff/post-pvt/H12-pdk-cap/design.json` → `["design"]` (read at build time) |
| schematic of record | `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`, sha256 `ef78d6f8…faf3c7` |
| LVS reference | `layout/H12-pdk-cap/asbuilt/core_lvs.sp`, sha256 `57ee5906…3d46b1` — **regenerates byte-identically to round 2** (round 3 moves no device and no size) |
| GDS (build product) | sha256 `fc59cfd7ef38b5d91d0e78ab2a0cf56aa8c284578ac7ec29abe1be04cf0500ed` |
| post-layout netlist | `layout/H12-pdk-cap/asbuilt/core_pex.sp`, sha256 `cdd5cd83…0e15f` (kpex 2.5D **CC**, 71 C, + the six certified `cap_cmim` cards) |
| pre-layout yardstick | `signoff/post-pvt/H12-pdk-cap/scorecard.json` / `PRELAYOUT.md` §1 |
| round-2 yardstick | `iterations/it08/` (sha `240fb440…1ce4cb`, the reviewed layout of record) |

## 0. What round 3 bought, in one table

| | pre-layout | round 1 | round 2 | **round 3** | |
|---|---|---|---|---|---|
| `ph_max` nominal | 332.382 | 330.732 | 331.155 | **331.160** | +0.005 |
| `ph_max` @ `cap_bcs`, `iref ×0.9` | 331.018 PASS | 329.299 | 329.746 | **329.751 FAIL** | +0.005, still 0.249 short |
| **C(`net2`,`net3`)** (differential) | — | 0 | **1.3792** | **0.0000** | **F16 closed** |
| **C(`net4`,`net1`)** | — | — | 0.0257 | **0.0000** | F16 closed |
| C(`net2`) / C(`net3`) to ac gnd | — | 50.04 / 44.94 | 28.27 / 28.27 | **32.33 / 32.33** | +4.06, the F17 disclosure |
| Δ(`net2`,`net3`) | — | 5.10 | 0.000 | **−0.001** | 0.17 aF of kpex rounding |
| identical routing on all six `rep_sink` units | — | yes | **no (F17)** | **yes** | BRIEF §2.1 |
| `--check-symmetry` on it01 (round 1) | — | — | **PASS** (F18) | **FAIL, 15 rules / 8 layers** | guard-rail fixed |
| via layers in the symmetry table | — | no | no (F20) | **Metal4 + Via1…4 + TopVia1** | |
| `BOUNDS` endpoints DRC-clean | — | 35/48 | 64/64 | **66/66** (33 knobs) | 2N/2N held |
| area | — | 230 624 | 247 137 | **247 137 µm²** | **unchanged** |
| DRC / LVS | — | 0 / match | 0 / match | **0 / match** | no waivers |

## 1. Outline and area

| | round 2 | **round 3** |
|---|---|---|
| bbox | (−216.84, −10.00)…(216.84, 559.86) | **identical** |
| outline | 433.68 × 569.86 = 247 136.88 µm² = 0.2471 mm² | **identical — round 3 costs no area** |
| aspect | 1.31 | 1.31 |
| MIM area | 122 253 µm² (49.5 %) | unchanged (**F15 still flagged**, block-level) |
| devices | 16 instances for 15 certified + 14 nmos + 2 pmos dummies | unchanged |
| n-well islands | 8, all tapped, mirror-XOR 0 | unchanged |

`axis_gap` 6 → 12 µm widens the *device* gap at the symmetry axis by 6 µm, and
the cell outline does not move: it is set by bank B (±216.84 µm), which is
36 µm wider than island A's widest row even after the change. That is why F16
is free.

## 2. DRC

| deck | run | result |
|---|---|---|
| `$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py` via `spicexplorer_signoff.run_drc` (`--no_density`) | full cell, top `lpf_core` | **0 violations** |

**Waivers: none.** Density/fill, sealring, pads and antenna diodes are out of
scope by PLAN §6. **A9: all 66 `BOUNDS` endpoints (33 knobs × 2) build and DRC
clean** — §7.

## 3. LVS

| | |
|---|---|
| deck | `sg13g2.lvs` via `spicexplorer_signoff.run_lvs` |
| reference | `asbuilt/core_lvs.sp` (emitted by `gen_H12_pdk_cap.py --lvs`) |
| result | **Netlists match**, 0 unmatched |

Round 3 moves **no device, no width, no length and no multiplicity**, so the
reference regenerates **byte-identically** to round 2 (sha `57ee5906…3d46b1`,
re-derived from the round-3 generator and diffed: no change). Its provenance —
`postlayout.to_lvs_reference(core.sp)` plus exactly four declared mechanical
edits — is unchanged and is set out in round 2's §3. `vbp` is still a dangling
labelled pad and therefore still unchecked by the deck (**F13 carried**, a
platform fix).

## 4. PEX

| | CC (netlist of record) | RC (cross-check) |
|---|---|---|
| tool | kpex 0.3.12 (klayout-pex, 2.5D) via `spicexplorer_signoff.run_pex` | same, `--mode RC` |
| elements | **71 C, 0 R** (round 2: 78 C) | 71 C, **8 609 R** |
| `fc` / `ph_max` / `a1000` | 248.639 Hz / **331.1595°** / −49.222 dB | 248.679 Hz / **331.1592°** / −49.217 dB |

RC converged **without a `.nodeset`** and reproduces CC to **0.041 Hz and
0.0003°** — BRIEF §1.2's "resistance is a don't-care below ≈15 MΩ" re-measured
on the round-3 routing.

**The seven C elements round 2 had and round 3 does not are the F16 couplings**:
`net2`↔`net3` (1.3792 fF), `net4`↔`net1` (0.0257 fF) and five smaller lane
terms. They are not "small" now, they are **absent** — kpex's halo no longer
reaches across the 9.8 µm gap.

Extraction still runs on the **MIM-stripped** GDS and the six certified
`cap_cmim` cards are re-inserted verbatim (**F11 open**, ≤ 15 fF bound on
`net2`/`net3` carried).

**Gotcha, new in round 3:** kpex's *node numbering* is not deterministic across
runs of the same GDS. Two CC extractions of `fc59cfd7…` give byte-identical `C`
cards but different `XM$n` device numbering; two RC extractions give the same
71 C / 8 609 R but different `net.$n.m` sub-node names — and **the first RC run's
mesh made ngspice solve the operating point to a wrong, shorted DC state**
(`fc` 0.11 Hz, 768 mW). Re-extracting produced the converging mesh reported
above. This is the runbook's `.nodeset` trap arriving through a door nobody
was watching; the reported RC is the second extraction.

## 5. Pre- vs post-layout scorecard (same benches, same definitions)

`lab.metrics.evaluate` (op+ac+noise, `mos_tt`, 27 °C, 1.5 V) and
`lab.thd.measure`, spliced through `Design.dut_override` — the block's own
frozen harness. `scorecard_post.json` carries the machine-readable version.

| line | spec | pre-layout | round 1 | round 2 | **round 3** | Δ vs pre | Δ vs r2 | margin left |
|---|---|---|---|---|---|---|---|---|
| S1 `ph_max` | ≥ 330° | 332.382 | 330.732 | 331.155 | **331.160** | −1.223 | **+0.005** | 1.16° |
| S1 `a1000` | ≤ −48 dB | −49.026 | −49.263 | −49.220 | **−49.222** | −0.196 | −0.002 | 1.22 dB |
| S2 `fc` | 245–255 Hz | 249.775 | 248.275 | 248.651 | **248.639** | −1.136 | −0.012 | 3.64 / 6.36 Hz |
| S3 `dc` | \|·\| ≤ 0.2 dB | −0.0081 | −0.0081 | −0.0081 | **−0.0081** | 0.000 | 0.000 | 0.192 dB |
| S3 `ripple` | ≤ 0.2 dB | 0.0523 | 0.0232 | 0.0355 | **0.0347** | −0.018 | −0.001 | 0.165 dB |
| S4 `peak` | ≤ 0.2 dB | 0.0018 | 0.0206 | 0.0132 | **0.0136** | +0.012 | +0.000 | 0.186 dB |
| S5 `IRN` | < 40 µV | 29.199 | 29.195 | 29.1945 | **29.1942** | −0.005 | 0.000 | 10.8 µV |
| S6 `P` | < 50 nW | 11.9125 | 11.9130 | 11.9134 | **11.9136** | +0.0011 | +0.000 | 38.1 nW |
| S7 `THD` | ≤ −40 dB | −50.401 | −49.614 | −49.714 | **−49.701** | +0.700 | +0.013 | 9.7 dB |
| — `HD3` | (not specced) | — | — | −49.912 | **−49.898** | — | +0.014 | — |
| — `HD2` | (not specced) | −100.19 | −88.06 | −104.22 | **−97.17** | +3.02 | +7.05 | see below |
| S8 | ≥ 2 papers | — | — | — | unchanged | — | — | documentation gate |

**All S1–S7 pass** (`s.violations == []`). A6 (`ph_max` ≥ 331.3°) is still
missed, by 0.140°.

**HD2 is at this bench's numerical floor and round 3 proves it.** Two PEX
netlists of the **same GDS** with **byte-identical `C` cards and identical
device cards** (only kpex's `XM$n` instance numbering differs — see §4) measure
**−98.99 dB and −97.17 dB**. THD and HD3 reproduce across that same pair to
0.002 dB. Round 2's −104.22 dB is the same floor seen from a different draw, not
a property the layout holds; round 1's −88.06 dB *was* real (it had a 155.8 fF
`vout_1`/`vout_2` imbalance, and round 3 still measures 0.48 fF). Two direct
what-ifs confirm nothing physical moved: symmetrising the residual 11.2 aF
`net2`↔`vout_1` / `net3`↔`vout_2` cross-term difference gives **−99.18 dB**
(+0.19), and re-adding the removed 1.379 fF `net2`↔`net3` element gives
**−98.59 dB** (−0.40). Neither is 5 dB.

### Every delta round 2 → round 3, explained

| what-if (on `core_pex.sp`) | `ph_max` | Δ | `fc` | reads as |
|---|---|---|---|---|
| as extracted | 331.160 | — | 248.639 | — |
| delete every `net2`/`net3` C | 331.900 | +0.741 | 249.118 | `net2`/`net3` cost 0.741° (round 2: 0.740°) |
| delete every `net4`/`net1` C | 331.643 | +0.483 | 248.683 | (round 2: 0.470°) |
| delete `net2`/`net3` → substrate only | 331.852 | +0.693 | 249.017 | 94 % of the net's cost is its own substrate C |
| delete `net2`/`net3` → `vbn` | 331.254 | +0.095 | 248.695 | `xm9`'s gate-to-drain, intrinsic |
| delete `net2`/`net3` → `vinp`/`vinn` | 331.102 | **−0.058** | 248.666 | this one *helps*; do not remove it |
| delete **all** parasitic C | 332.332 | +1.172 | 249.776 | back to pre-layout within 0.05° |

The isolated 2×2 that prices F16 and F17 — four builds, four extractions, same
bench:

| `lane_mid` | `net23_strap` | C(`net2`) to ac gnd | **C(`net2`,`net3`)** | `ph_max` nom | `ph_max` @ A7 | |
|---|---|---|---|---|---|---|
| 1.9 | `min_m1` | 28.270 | **1.3792** | 331.155 | 329.746 | round 2 |
| 1.9 | `lane_m1` | 31.444 | 1.4113 | 331.105 | 329.688 | F17 alone |
| **4.9** | `min_m1` | 29.106 | **0.0000** | 331.209 | 329.808 | F16 alone (it09) |
| **4.9** | **`lane_m1`** | 32.328 | **0.0000** | 331.160 | 329.751 | **round 3** |

The two effects are additive to within 0.002°. F16 buys +0.054° nominal /
+0.062° at A7 for **no area and no DRC**; F17 spends 0.050° / 0.057° to put the
six `rep_sink` units back on identical routing. Both numbers reproduce the
reviewer's what-ifs (331.209 / 329.808 and 331.105 / 329.688) exactly.

### Corners on the PEX netlist (A7)

9-point `lab.corners.AXES` (both DUTs, `LPF_BIAS_ALPHA = 1.1`) **plus** the five
`cornerCAP.lib` points with the `iref` trim, all re-run on round 3's own
extraction.

| corner | pre `ph_max` | **post `ph_max`** | pre | post |
|---|---|---|---|---|
| `mos_tt` 27 °C 1.50 V | 332.38 | **331.16** | PASS | **PASS** |
| `mos_ss` / `ff` / `sf` / `fs` 27 °C | 332.38 / 332.17 / 332.25 / 332.44 | **331.16 / 330.96 / 331.02 / 331.23** | PASS | **PASS** |
| `mos_tt` 27 °C 1.65 V | 332.42 | **331.19** | PASS | **PASS** |
| `mos_tt` 1.35 V | 308.01 | 307.50 | FAIL | FAIL (headroom; fails pre-layout too) |
| `mos_tt` −40 °C | 237.04 | 235.04 | FAIL | FAIL (unchanged) |
| `mos_tt` +125 °C | 222.31 | 221.75 | FAIL | FAIL (unchanged) |
| `cap_typ` ×1.0 | 332.38 | **331.16** | PASS | **PASS** |
| `cap_bcs` ×1.0 | 330.95 | 329.69 | FAIL (`fc` 277 Hz) | FAIL (`fc` 276 Hz) — not an S1 corner either way |
| **`cap_bcs` ×0.9 + `iref ×0.9`** | **331.02** | **329.751** | **PASS** | **FAIL — S1 (330.0 limit)** |
| `cap_wcs` ×1.0 | 333.61 | 332.43 | FAIL (`fc` 227 Hz) | FAIL (`fc` 226 Hz) |
| `cap_wcs` ×1.1 | 333.56 | **332.39** | PASS | **PASS** |

**Every corner that passed pre-layout still passes post-layout except one**, and
that one is the F1 blocker: **329.751 vs a 330.0 limit, 0.249° short.**

## 6. Parasitic budget — used vs allowed (kpex CC)

"to ac ground" sums C to `0`/substrate, `vdd`, `vbn`, `vbr`, `rep_x`,
`vinp`/`vinn` — the reviewer's definition, so the tables compare line for line.
**New in round 3: the last column.** `brief.json` carries a
`budget_c_diff_ff` — capacitance *between* the two halves — that neither round-1
nor round-2's table printed. That omission is exactly what let F16's 1.379 fF
sit uncounted, so the budget definition itself is fixed here.

| net | round 1 | round 2 | **round 3** | allowed nom / pvt | ratio | one-sided Δ | allowed asym | **C between halves** | allowed diff |
|---|---|---|---|---|---|---|---|---|---|
| `net2` | 50.04 | 28.27 | **32.328** | 22.8 / 9.59 | **1.42× / 3.37×** | Δ = **−0.001** | 45.7 / 19.2 ✓ | **0.0000** (r2: 1.3792) | 11.4 ✓ |
| `net3` | 44.94 | 28.27 | **32.329** | 22.8 / 9.59 | 1.42× / 3.37× | " | " | " | " |
| `net4` | 77.30 | 67.578 | **67.338** | 82.8 / 34.8 | 0.81× / 1.93× | Δ = **0.089** | 166 / 69.5 ✓ | **0.0000** (r2: 0.0257) | 41.4 ✓ |
| `net1` | 67.27 | 67.471 | **67.249** | 82.8 / 34.8 | 0.81× / 1.93× | " | " | " | " |
| `vout_1` | 231.73 | 165.057 | **166.059** | 3350 | 0.05× | Δ = **−0.481** | 6710 ✓ | — | — |
| `vout_2` | 75.93 | 165.537 | **166.540** | 3350 | 0.05× | " | " | — | — |
| `voutp` | 505.50 | 459.418 | **460.060** | 905 / 455 | 0.51× / **1.01×** | Δ = **21.058** | 1800 / 905 ✓ | — | — |
| `voutn` | 352.55 | 438.359 | **439.002** | 905 / 455 | 0.49× / 0.96× | " | " | — | — |
| A ↔ B | 0.0000 | 0.0000 | **0.0000** | 0.277 / 0.116 | — | — | — | **absent, not small** | — |

`net2`'s pairs, measured: `0` 26.669, `vbn` 3.930, `vinp` 1.639, `vout_1` 0.632,
`vout_2` 0.127, `vbr` 0.091. **`net3` no longer appears in that list at all.**

**`net2`/`net3` are further over the balanced budget than in round 2 (1.42× vs
1.24×) and that is a disclosure, not an accident.** The +4.06 fF is the price of
BRIEF §2.1 (F17): restoring the Metal1 drain bar on the `xm9`/`xm10` row puts
`net2`'s Metal1 back from 4.97 to **29.54 µm²** (and its perimeter from 44 to
232 µm), which the extraction charges as **+3.05 fF of substrate C** and
**+0.60 fF to `vbn`**. Split by the 2×2 above: F16 (the wider lane, which runs
over its own device row) costs **+0.836 fF** and removes the 1.379 fF
differential term; F17 costs **+3.222 fF**. Netted through the bench, the trade is
**+0.005°** — and the *differential* load, which is what the biquad's pole
actually sees, is now `C_g` alone (32.33 fF) instead of round 2's
`C_g + 2·C_c` = 31.03 fF, i.e. within 1.3 fF of round 2 with the coupling
counted honestly.

### Where `net2`'s 32.33 fF sits (per-layer geometry, measured on the GDS)

| layer | round 2 area µm² | **round 3** | what changed |
|---|---|---|---|
| Activ | 8.800 | 8.800 | device |
| GatPoly | 84.735 | 84.735 | `xm4`'s own gate (W 1.5, **L 45 µm**) — layout-invariant |
| Metal1 | 4.971 | **29.542** | **F17**: the 52 µm `xm9` drain bar is back on all six units |
| Metal2/3/4 pads | 0.578 each | 0.433 each | fewer via-stack pads |
| Metal5 (spine) | 40.488 | **22.743** | the drain bar left the spine when it returned to Metal1 |
| TopMetal1 (haul) | 3 247.444 | 3 242.344 | unchanged in kind |

`net2` and `net3` still have **identical area, perimeter and shape count on
every layer**, with mirrored bounding boxes — F6 stays fixed.

### Why the last 0.249° is still not here

Unchanged from round 2 in kind, and now with the layout-reachable part spent:
`net2`/`net3` cost 0.741° for 32.33 fF ⇒ 0.0229 °/fF; reaching 330.0° at
`cap_bcs`/`iref ×0.9` needs ≈ 11 fF per half off a net whose remaining terms are
`xm4`'s gate poly, `xm9`'s finger pitch, island-A height and `xm9`'s own
gate-to-drain. The reviewer's own arithmetic — "≈ 0.062° of the 0.254° miss is
layout-reachable, the rest is design lane" — is now **spent**: 0.062° was taken
(F16) and 0.057° was given back on purpose (F17). **The remaining ≈ 0.25° is a
sizing question**: an `iref` trim, a small `C1`/`C2` re-allocation, a shorter `L`
on `xm4`, or fewer `xm9` fingers.

### Known-unmodelled and known-over-modelled terms (A11)

Unchanged from round 2 and re-stated for completeness: **F3** n-well↔substrate
junction C (lumped-`Cj` what-if bound −0.108…−0.259°, deferred by R2.7, no
layout lever — `well_margin` is at the `NW.c` floor and the wells mirror-XOR to
0); **F11** MIM top-plate environment C (≤ 15 fF on `net2`/`net3`, optimistic);
the **GatPoly-to-substrate over-count** (≈ 6 fF of `net2`, pessimistic,
identical in all three rounds so the comparison is consistent); **F12** the
48 : 1 antenna ratio with no antenna rule in the deck; **F15** MIM = 49.5 % of
the cell.

## 7. Parameters, `BOUNDS`, and the endpoint sweep (A9)

`set(BOUNDS) == set(LayoutParams fields)` is asserted inside `validate()`, which
`build()` calls on every build; `clamp()` resolves the knob couplings so that
**every** `BOUNDS` endpoint is buildable. Round 3 adds **one** knob, `lane_mid`
(F16), and moves **three** defaults: `axis_gap` 6.0 → 12.0 and `lane_mid` 1.9 →
4.9 (F16, the reviewer's what-if geometry, reproduced byte-identically),
`net23_strap` `min_m1` → `lane_m1` (F17).

`lane_mid` is coupled in `clamp()`: `lane_mid = max(1.9, min(lane_mid,
axis_gap/2 − 1.1))`. The lane lives *inside* the axis gap, 1.1 µm clear of the
device inner edge, so its ceiling is geometric, not a preference; at the default
`axis_gap = 12` that ceiling is exactly 4.9 µm, which is why `BOUNDS` stops
there. A wider `axis_gap` raises it, but the term `lane_mid` exists to kill —
C(`net2`,`net3`) — is already **0.0000 fF** at 4.9.

| knob | default | range (`BOUNDS`) | min-endpoint DRC | max-endpoint DRC |
|---|---|---|---|---|
| `dev_gap_x` | 2.0 | 1.0 – 6.0 | 0 | 0 |
| **`axis_gap`** | **12.0** | 4.0 – 30.0 | 0 | 0 |
| **`lane_mid`** | **4.9** | 1.9 – 4.9 | 0 | 0 |
| `row_gap` | 6.0 | 3.0 – 20.0 | 0 | 0 |
| `bias_row_gap` | 4.0 | 2.0 – 12.0 | 0 | 0 |
| `bias_dummy_cols` | 1 | 0 – 2 | 0 | 0 |
| `bias_dummy_rows` | 1 | 0 – 1 | 0 | 0 |
| `gmfb_dummy` | 1 | 0 – 2 | 0 | 0 |
| `xr1_split` | True | False – True | 0 | 0 |
| `well_margin` | 0.62 | 0.62 – 3.0 | 0 | 0 |
| `well_gap` | 2.0 | 1.8 – 6.0 | 0 | 0 |
| `ring_w` | 1.0 | 0.6 – 3.0 | 0 | 0 |
| `ring_gap` | 4.0 | 2.0 – 15.0 | 0 | 0 |
| `shield_w` | 4.0 | 2.0 – 12.0 | 0 | 0 |
| `cap_gap` | 0.6 | 0.6 – 3.0 | 0 | 0 |
| `cap_bank_gap` | 10.0 | 9.0 – 40.0 | 0 | 0 |
| `cap_axis_gap` | 5.0 | 3.0 – 20.0 | 0 | 0 |
| `bank_gap` | 14.0 | 14.0 – 60.0 | 0 | 0 |
| `w_m1` | 0.2 | 0.16 – 1.0 | 0 | 0 |
| `w_m2` | 0.2 | 0.2 – 0.4 | 0 | 0 |
| `w_m3` | 0.25 | 0.2 – 1.0 | 0 | 0 |
| `w_tm1` | 1.7 | 1.64 – 4.0 | 0 | 0 |
| `via_pad` | 2.0 | 1.7 – 3.0 | 0 | 0 |
| `cc19_cols` | 2 | 1 – 2 | 0 | 0 |
| `cc1_cols` | 4 | 2 – 8 | 0 | 0 |
| `cc12_cols` | 7 | 1 – 7 | 0 | 0 |
| `cc13_cols` | 1 | 1 – 2 | 0 | 0 |
| `bankA_order` | c13_axis | c19_axis – c13_axis | 0 | 0 |
| `cap_spine_side` | mirror | left – mirror | 0 | 0 |
| `cap_anti_orient` | True | False – True | 0 | 0 |
| `cc12_split` | 3\|1\|3 | none – 3\|1\|3 | 0 | 0 |
| **`net23_strap`** | **lane_m1** | lane_m1 – min_m1 | 0 | 0 |
| `net23_spine_layer` | Metal5 | Metal2 – Metal5 | 0 | 0 |

**66/66 endpoints build and DRC clean** (round 2: 64/64 on 32 knobs) and **no
knob is dead** — no `LayoutParams` field leaves the GDS byte-identical at both
endpoints, `lane_mid` included (1.9 → `dc25783d…`, 4.9 → `fc59cfd7…`). Only the
two changed knobs and the new one needed re-measuring for their *ranges*; the
full 66 were re-swept anyway because the round's other change — the symmetry
assertion — runs inside `build()` and therefore touches every endpoint. That was
the right call: see §9.

`W`, `L`, `ng`, `m` are read from `design.json` and are never knobs.
**Determinism:** two builds of the round-3 generator give sha `fc59cfd7…0500ed`;
it09's build reproduces the reviewer's patched-generator what-if sha
`c0507860…` exactly.

## 8. Mirror symmetry (A10) — asserted at build time, and now calibrated

`_assert_symmetry(c, p)` runs inside `build()` and fails the build. Nine
physical layers must be **exactly** 0. The routing and via layers carry two
rules: a **mirror-XOR budget** and — new in round 3 — a **half-plane area
balance**, because on five layers the XOR is *structurally saturated* and
carries almost no information (see below). The same rules are re-runnable
against any stored GDS:

```
python gen_H12_pdk_cap.py --check-symmetry iterations/it01/layout.gds
```

| layer | XOR µm² | budget | balance (L−R) µm² | balance budget | of total µm² | note |
|---|---|---|---|---|---|---|
| Activ / GatPoly / Cont / ThickGateOx / NWell / pSD / nSD / MIM / Vmim | **0.0000** | **0 (exact)** | 0.0000 | — | 21 469 / 16 316 / 405 / 17 735 / 5 213 / 10 097 / 502 / 122 253 / 23 266 | every device, well, tap, contact and MIM unit is exactly its own mirror image |
| Metal1 | 23.5560 | 48.61 | −4.7300 | — | 8 101 | **16.0 = the `vbp` pad** (BRIEF §9) + **7.556 = `xr2`** — see F19 below |
| Metal2 | 0.2736 | 2.00 | **0.0000** | 1.22 | 243 | |
| Metal3 | 280.3376 | 338.01 | **0.0000** | 5.63 | 1 127 | the four balanced top-plate crossing tracks (saturated XOR) |
| Metal4 | 48.0000 | 56.00 | **0.0000** | 1.00 | 48.9 | via pads only; XOR is 98 % of its own area **by construction** |
| Metal5 | 39.2000 | 104.68 | 3.6000 | — | 130 845 | |
| TopMetal1 | 35.0600 | 71.47 | 15.1300 | — | 119 123 | |
| Via1 | **0.0000** | 0.50 | **0.0000** | 0.20 | 3.36 | |
| Via2 | 0.1444 | 0.50 | **0.0000** | 0.20 | 2.96 | |
| Via3 | 3.8988 | 4.53 | **0.0000** | 0.21 | 4.12 | saturated (93 %) |
| Via4 | 3.8988 | 4.53 | **0.0000** | 0.21 | 4.12 | saturated (93 %) |
| TopVia1 | 1.4112 | 1.55 | **0.0000** | 0.20 | 1.41 | saturated (100 %) |

**F20 — why the via layers and Metal4 needed a second rule, not just a budget.**
The F8 anti-orientation makes the two `xc19` (and `xc12`) top-plate lines swap
sides, and the two members of each swapped pair sit at **different y**. Mirroring
one therefore does not land on the other, and the plain XOR saturates at ≈ 2× the
layer's own area — a number that cannot distinguish "balanced swap" from "the
whole thing is on one side". The discriminating statement is the **half-plane
area balance**, which a swap leaves at exactly 0 and a one-sided haul does not.
Round 3 measures **0.0000 µm² on all eight balance layers**; round 1's it01
breaks it on Metal2 (4.000), **Metal3 (21.089)**, Metal4 (4.000), Via1–Via4
(0.325) and TopVia1 (0.353). That Metal3 number *is* F6 — round 1's `net4`
Metal3 haul was 184.4 µm against `net1`'s 29.8 µm.

**F19 — the Metal1 exception is `xr2`, not `xr1`.** Measured on the round-3 GDS,
the six Metal1 XOR polygons are: 2 × 8.000 µm² at (±10…±14, −10…−8) — the `vbp`
pad — and 2 × 3.524 + 2 × 0.254 µm² at **y 234.76…242.21**, which is the
**bridge row (`rep_x` / `xr2`)**, not the `gmf_b` row where `xr1` is. `xr1`'s two
anti-oriented halves mirror exactly; the reviewer's `xr1_split=False` build
measures the identical 23.556 µm², which settles it. The residual falls to
16.0 µm² (the pad alone) once `xr2_split` exists — the fix deferred by PLAN
R2.8 Q4. Round 2's §8 and the generator comment both said `xr1`; both are
corrected.

## 9. The XOR-budget calibration (F18) — what the numbers are and how they were set

**The finding.** Round 2 installed a mirror-XOR assertion to stop the F6 class
from recurring, and the reviewer showed it did not: applied to
`iterations/it01/layout.gds` — the round-1 layout **F6 was raised against** — it
passed on every routing layer. Round 2's REPORT §9 claimed the opposite. It is
also worth saying plainly: round 2's budget was tuned to *survive the endpoint
sweep*, and nobody ever ran it against a layout known to be broken.

**The calibration rule.** Each budget stays scale-relative,
`max(floor, fraction × the layer's own drawn area)` — an absolute number is
calibrated for one geometry, which is round 2's other recorded lesson — and is
now set to **≈ 1.2–2× the round-3 measurement, and below the it01 measurement
wherever the two can be separated at all**. The XOR of `it01` and of `it12` was
measured first, then the numbers were chosen; they are in the generator with the
two measurements in the comment.

| layer | it01 (round 1) | **it12 (round 3)** | fraction | budget @ it12 | budget @ it01 | it01 verdict |
|---|---|---|---|---|---|---|
| Metal1 | 47.556 | **23.556** | max(26.0, 0.006·A) | 48.61 | 40.91 | **FAIL** |
| Metal2 | 24.000 | **0.274** | max(2.0, 0.005·A) | 2.00 | 2.00 | **FAIL** |
| Metal3 | 126.353 | 280.338 | max(16.0, 0.30·A) | 338.01 | 288.87 | pass (saturated — the balance rule catches it) |
| Metal4 | 24.000 | 48.000 | max(56.0, 1.10·A) | 56.00 | 56.00 | pass (balance rule: **FAIL**) |
| Metal5 | 948.780 | **39.200** | max(60.0, 0.0008·A) | 104.68 | 104.14 | **FAIL** |
| TopMetal1 | 847.048 | **35.060** | max(60.0, 0.0006·A) | 71.47 | 71.85 | **FAIL** |
| Via1 | 1.949 | **0.000** | max(0.5, 0.05·A) | 0.50 | 0.50 | **FAIL** |
| Via2 | 1.949 | **0.144** | max(0.5, 0.10·A) | 0.50 | 0.50 | **FAIL** |
| Via3 / Via4 | 1.949 | 3.899 | max(0.5, 1.10·A) | 4.53 | 3.21 | pass (balance rule: **FAIL**) |
| TopVia1 | 1.411 | 1.411 | max(0.5, 1.10·A) | 1.55 | 1.17 | **FAIL** |

Balance budgets (`|area(x<0) − area(x>0)|`, the eight layers whose XOR
saturates): Metal2 max(1.0, 0.005·A), Metal3 max(1.0, 0.005·A), Metal4
max(1.0, 0.005·A), Via1…Via4 and TopVia1 max(0.2, 0.05·A). Metal1, Metal5 and
TopMetal1 are deliberately **not** balance-asserted (the `vbp` pad and the bank
spines make their balance legitimately non-zero); their XOR budget guards them
and their measured balance is printed in §8 anyway.

**The calibration result — the deliverable of F18:**

| GDS | what it is | verdict |
|---|---|---|
| `iterations/it01/layout.gds` | round 1, the layout F6 was raised against | **FAIL — 15 rules across 8 layers** (Metal1, Metal2, Metal3, Metal4, Metal5, TopMetal1, Via1, Via2, Via3, Via4, TopVia1) |
| `iterations/it08/layout.gds` | round 2, the reviewed layout of record | **PASS** |
| `iterations/it11/layout.gds`, `it12` | round 3 | **PASS** |

```
$ python gen_H12_pdk_cap.py --check-symmetry iterations/it01/layout.gds
verdict: FAIL -- Metal1: XOR 47.556 > 40.91; Metal2: XOR 24.0 > 2.00;
  Metal2: balance -4.0 > 1.34; Metal3: balance 21.0888 > 4.81;
  Metal4: balance -4.0 > 1.00; Metal5: XOR 948.78 > 104.14;
  TopMetal1: XOR 847.048 > 71.85; Via1: XOR 1.9494 > 0.50;
  Via1: balance -0.3249 > 0.22; Via2: XOR 1.9494 > 0.50;
  Via2: balance -0.3249 > 0.20; Via3: balance -0.3249 > 0.20;
  Via4: balance -0.3249 > 0.20; TopVia1: XOR 1.4112 > 1.17;
  TopVia1: balance -0.3528 > 0.20
```

**And the trap it walked into on the way (it11 → it12).** The first calibrated
table — set purely from `it01` vs `it12` at the *default* knobs — made **seven of
the 66 `BOUNDS` endpoints unbuildable**. Two were plain mis-scaling
(`w_m1 = 1.0`: Metal1 55.02 > 41.14 — the `vbp` pad and the `xr2` shapes scale
with `w_m1`; `via_pad = 3.0`: Metal5 79.2 > 78.54) and were fixed by raising the
*fractions* (0.004 → 0.006, 0.0006 → 0.0008) in a way that still fails it01.
The other five are different in kind: **three knob settings select a cap-bank
topology that is deliberately not its own mirror image** —

| knob setting | what it does | measured | relaxed layers |
|---|---|---|---|
| `cap_spine_side = "left"` | both halves put the MIM top-plate spine on their **left** column: the spine, its via stack and the Metal3 tracks it feeds are *translated*, not mirrored | TopMetal1 290.352, Metal4 64.0, Metal2 16.274, Via3/Via4 5.198, TopVia1 2.117, Metal3 balance 76.71 | TopMetal1, Metal4, Metal2, Via1–4, TopVia1, Metal3 balance |
| `bankA_order = "c19_axis"` (≡ `cap_anti_orient = False`) | the v1 bank A: **one** `xc19` array on the axis, so its bottom-plate riser has to pick a half | Metal5 888.52, Metal2 8.0, Via1/Via2 0.650, Metal2 balance 4.0, Metal3 balance 17.54, Metal4 balance 4.0 | Metal5, Metal2, Via1/Via2 + those balances |
| `cc12_split = "none"` | **seven** units in one unsplit array have no mirror-symmetric arrangement — one unit always sits off-centre | Metal5 445.3 (`cc12_cols=7`) / 1 651.3 (`cc12_cols=1`), TopMetal1 75.2 / 587.8 | Metal5, TopMetal1 |

so `budgets_for(params)` applies a **declared, measured relaxation to exactly
the layers each of those settings touches**. The default configuration — the
layout of record, and what an older GDS is judged by — keeps the tight table.
This is the honest shape of the rule: *the mirror rule applies to
configurations that claim mirror symmetry*. Its limitation is equally plain and
is a next step: in those three configurations the check degrades to
gross-breakage only, because the right statement there is a mirror-**and-swap**
symmetry that nothing in this flow computes yet.

## 10. Iterations

<!-- generated: `spicexplorer-layout iterations-md layout/H12-pdk-cap/iterations` -->

| it | what changed / what it fixed | DRC | LVS | PEX | area µm² | files |
|---|---|---|---|---|---|---|
| it01 | it01 = round-1 layout of record rebuilt from the committed generator at default LayoutParams, before any round-2 edit; GDS sha reproduces e5cfa1da... exactly; DRC 0 / LVS matched / kpex CC 78C 0R, round-1 scorecard attached (baseline for the round) | **0** | match | CC 78C/0R | 230624 | [gen](it01/gen.py) [png](it01/layout.png) |
| it02 | F9 tap_len deleted, F10 BOUNDS/PLAN reconciled + clamp()/validate(), F2 cc13_cols 2->1, F6 spine on the axis-facing column, F4 root causes fixed (outline now contains the device islands; row tap height decoupled from ring_w), xr1_split code added (off) — net2 50.04->42.52, net4 77.30->67.37, d(net4,net1) 10.04->0.11, ph_max 330.732->330.905; DRC 0, LVS matched | **0** | match | CC 78C/0R | 230624 | [gen](it02/gen.py) [png](it02/layout.png) [diff_from_it01](diff_it01_it02.png) |
| it03 | F5 bank-A re-order (xc13/xc17 on the axis, xc19 split 4+4 outboard) + F8 anti-orientation (xc19 L/R plates swapped, xc12 3|1|3) + cap_gap 0.4->0.6 (Mn.f for the split Metal5 sheets) + LVS reference now emits the two split MIM card pairs — LVS matched first try, but DRC 5x TM1.b: the h() helper caps every wire end by w/2, so the two xc12 comb bars across a 0.6 um group seam end 0.7 um apart | 5 (TM1.b ×5) | match | — | 233346 | [gen](it03/gen.py) [png](it03/layout.png) [diff_from_it02](diff_it02_it03.png) |
| it04 | TM1.b fixed by insetting the comb bars by w_tm1/2 before h() caps them — DRC back to 0, LVS matched. F5+F8 measured: net2 42.52->32.71, net3 42.11->32.74 (delta 5.10->0.03), vout_1/vout_2 delta 155.80->0.48, voutp/voutn delta 152.95->21.06, ph_max 330.905->331.139 | **0** | match | CC 78C/0R | 233346 | [gen](it04/gen.py) [png](it04/layout.png) [diff_from_it03](diff_it03_it04.png) |
| it05 | R2.6 residual levers on net2/net3: spine layer Metal2->Metal5 (27.5 vs 34.8 aF/um sidewall), net23_strap=min_m1 (the 52 um xm9 drain bar and the xm4 gate hop leave Metal1 entirely; only contact-row stubs + 0.38 um via pads remain), xc13/xc17 top-aligned with the bank (-18 um of TopMetal1 spine) — net2 32.71->26.46, Metal1 10.7->2.4 fF, C(net2,vbn) 4.47->3.77, ph_max 331.139->331.214; DRC 0, LVS matched | **0** | match | CC 78C/0R | 233346 | [gen](it05/gen.py) [png](it05/layout.png) [diff_from_it04](diff_it04_it05.png) |
| it06 | F7 bias_dummy_rows=1 (5 drawn rows, 3 live: every array member now has a dummy on four sides; 14 nmos dummies, Mdumn w=336u) + F14 xr1_split=True (two anti-oriented nf=1 W=6u halves, LVS still folds them to W=12u) — cost as priced: island A +31.8 um of height, net2/net3 26.46->28.27, ph_max 331.214->331.155; delta(net2,net3) now exactly 0.000 fF; DRC 0, LVS matched | **0** | match | CC 78C/0R | 247137 | [gen](it06/gen.py) [png](it06/layout.png) [diff_from_it05](diff_it05_it06.png) |
| it07 | R2.3/PLAN-4 build-time assertions added: per-layer mirror-XOR (nine physical layers must be exactly 0; routing layers against a declared, itemised budget) and the A/B keep-apart check (no Metal5 or TopMetal1 shape may cross the grounded shield band). The XOR assertion immediately found a real defect: the tap contact rows were not their own mirror image (Cont XOR 0.0128 um2 from 5 nm banker's-rounding slivers) — fixed by snapping the contact CENTRE. Electrically identical to it06 (same PEX, same scorecard) | **0** | match | CC 78C/0R | 247137 | [gen](it07/gen.py) [png](it07/layout.png) [diff_from_it06](diff_it06_it07.png) |
| it08 | F4 closed: XOR budget made scale-relative (a fixed one is calibrated for one geometry only), TGO.e floor added to the nmos in-row pitch (dev_gap_x=1.0 root cause), ws now reaches w_m1's own 0.16 minimum, dead knob vbn_bus_keepout DELETED (measured: after the F5 re-order the vbn M3 bus no longer runs under the net2/net3 corridor and the residual 3.8 fF C(net2,vbn) is xm9's own gate-to-drain geometry, which no routing knob reaches), bankA_order/cap_anti_orient coupling made symmetric so neither knob is dead, axis_gap/cap_bank_gap/w_m2 ranges re-measured — 64/64 BOUNDS endpoints build DRC-clean, 0 dead knobs; GDS unchanged from it07; PEX CC+RC; THD -49.714, HD2 -104.22 (round 1: -88.06) | **0** | match | CC 78C/0R | 247137 | [gen](it08/gen.py) [png](it08/layout.png) [diff_from_it07](diff_it07_it08.png) |
| it09 | F16: the net2/net3 (and net4/net1) lane offset is now the knob `lane_mid` (BOUNDS 1.9-4.9, clamped to axis_gap/2-1.1) and axis_gap's default moves 6->12, so the two spines sit 9.8 um apart instead of 3.8 -- the reviewer's what-if geometry, reproduced byte-identically (sha c0507860...). C(net2,net3) 1.379 -> 0.000 fF (the element is gone from the extraction: 78 -> 71 C), C(net4,net1) also gone; net2/net3 to ac gnd 28.270 -> 29.106 fF (the lane now runs over its own device row), delta(net2,net3) still exactly 0.000. ph_max 331.155 -> 331.209 nominal, 329.746 -> 329.808 at cap_bcs x0.9 + iref x0.9. DRC 0, LVS matched, area unchanged at 247136.88 um2 | **0** | match | CC 71C/0R | 247137 | [gen](it09/gen.py) [png](it09/layout.png) [diff_from_it08](diff_it08_it09.png) |
| it10 | F17: net23_strap default min_m1 -> lane_m1, so the Metal1 drain bar is drawn on ALL SIX members of the rep_sink matching class again (BRIEF 2.1 'identical S/D/G routing on all six'); min_m1 stays as a knob but is no longer the default. Measured cost, disclosed: net2/net3 29.106 -> 32.328 fF (the 52 um xm9 drain bar plus the longer Metal1 hops at lane_mid=4.9; C(net2,vinp) 1.175 -> 1.639 partly offsets it), ph_max 331.209 -> 331.160 nominal (-0.050, exactly the reviewer's number) and 329.808 -> 329.751 at cap_bcs. Net of it09+it10 vs round 2: +0.005 deg with the brief's matching rule honoured and the 1.379 fF differential coupling gone. DRC 0, LVS matched | **0** | match | CC 71C/0R | 247137 | [gen](it10/gen.py) [png](it10/layout.png) [diff_from_it09](diff_it09_it10.png) |
| it11 | F18/F19/F20 guard-rail calibration; GDS byte-identical to it10 (fc59cfd7...), so this round changes only what the build ASSERTS. F18: the round-2 XOR budget passed on it01 -- the very layout F6 was raised against -- so it is re-derived by calibration (max(floor, fraction x the layer's own area), set to ~1.2-2x the round-3 measurement and below it01's) and it01 now FAILS on Metal1 47.556>27.27, Metal2 24.0>2.0, Metal5 948.78>78.10, TopMetal1 847.05>71.85, Via1 1.949>0.5, Via2 1.949>0.5, TopVia1 1.411>1.17. F20: Metal4 + Via1/2/3/4 + TopVia1 added to the table; on Metal3/Metal4/Via3/Via4/TopVia1 the plain XOR is saturated by the F8 balanced swaps (the two members sit at different y), so a second rule XOR_BALANCE asserts the left/right drawn-area balance -- 0.0000 um2 on all eight balance layers in round 3, and it01 breaks it on Metal2/Metal3/Metal4/Via1-4/TopVia1 (that is the rule that actually catches F6's one-sided Metal3 haul, 21.089 um2). F19: the 7.556 um2 Metal1 XOR is re-attributed to the single-orientation xr2 (rep_x bridge, y 234.76-242.21), not xr1. New CLI 'gen_H12_pdk_cap.py --check-symmetry <gds>' re-runs the whole rule on any stored iteration. DRC 0, LVS matched, PEX CC 71C/0R + RC 71C/8609R | **0** | match | CC 71C/0R | 247137 | [gen](it11/gen.py) [png](it11/layout.png) [diff_from_it10](diff_it10_it11.png) |
| it12 | F18 follow-up -- the calibrated budget of it11 made SEVEN legal BOUNDS endpoints unbuildable (w_m1=1.0 Metal1 55.02>41.14, via_pad=3.0 Metal5 79.2>78.54, and five cap-topology endpoints), i.e. round 2's own recorded trap in a new costume. Fixed WITHOUT loosening the default rule: Metal1 fraction 0.004->0.006 and Metal5 0.0006->0.0008 (both still fail it01), plus a new budgets_for(params) that applies a DECLARED, measured relaxation to exactly the layers a non-mirrored cap topology touches -- cap_spine_side='left' (both halves put the top-plate spine on their left column), bankA_order='c19_axis'/cap_anti_orient=False (one on-axis xc19 array whose riser must pick a half) and cc12_split='none' (seven units cannot be arranged mirror-symmetrically). The default configuration -- the layout of record, and what an older GDS is judged by -- keeps the tight table. Result: 66/66 endpoints build DRC-clean, 0 dead knobs, and 'gen_H12_pdk_cap.py --check-symmetry iterations/it01/layout.gds' still FAILS on 15 rules across 8 layers while it08/it11/it12 PASS. GDS byte-identical to it10/it11 (fc59cfd7...); PEX C-card set byte-identical to it11's; DRC 0, LVS matched, PEX CC 71C/0R + RC 71C/8609R | **0** | match | CC 71C/0R | 247137 | [gen](it12/gen.py) [png](it12/layout.png) [diff_from_it11](diff_it11_it12.png) |
| it13 | Documentation round, no geometry and no rule change: the module docstring gains the round-3 summary and the new --check-symmetry CLI line. GDS byte-identical to it10/it11/it12 (fc59cfd7...) and re-verified end to end anyway -- DRC 0, LVS matched, kpex CC 71C/0R -- so the LAST entry of this trail is the committed generator (sha 6ae114ad...), which is the property a reviewer rebuilds against. Round 3 delivers here: ph_max 331.1595 nominal / 329.751 at cap_bcs x0.9 + iref x0.9 (S1 still short by 0.249 deg, delivered with the miss documented), C(net2,net3) 0.000 fF, identical routing on all six rep_sink units, symmetry guard-rail FAILING on it01 as it must, 66/66 BOUNDS endpoints DRC-clean | **0** | match | CC 71C/0R | 247137 | [gen](it13/gen.py) [png](it13/layout.png) [diff_from_it12](diff_it12_it13.png) |


Thirteen rounds across three passes; round 3 is it09–it13. Three of the five
are **assertion- or documentation-only** (it11, it12 and it13 build the
byte-identical GDS `fc59cfd7…`), which
is the point: a guard-rail is part of the layout of record and gets the same
build → DRC → LVS → PEX treatment as a geometry change.

The dead ends worth remembering from this round:

* **A guard-rail calibrated only against the thing it must pass is not
  calibrated.** Round 2's XOR budget survived the endpoint sweep and was never
  run against a layout known to be broken; it therefore passed the very GDS it
  was installed to reject. Calibration needs **both** anchors — a known-good and
  a known-bad artifact — and the `iterations/` trail is what makes the known-bad
  one still available three rounds later.
* **…and calibrating against the known-bad one alone breaks the sweep.** The
  first tightened table made seven legal `BOUNDS` endpoints unbuildable. The fix
  that is *not* available is "loosen until everything passes"; the fix that is,
  is to notice that three knob settings **declare** a non-mirrored topology and
  to relax only what they touch (§9).
* **A saturated metric reads like a clean one.** Via3/Via4/TopVia1/Metal4 XOR at
  93–100 % of their own area looks alarming and means almost nothing; the
  half-plane balance at exactly 0.000 means a lot. Round 2 reported the first
  number for Metal4 and none at all for the vias.
* **kpex is not run-to-run deterministic in its naming, and once it mattered.**
  Same GDS, same mode: identical `C` cards, different instance and sub-node
  numbering — and one RC mesh drove ngspice's operating point to a shorted
  solution (`fc` 0.11 Hz). The GDS is byte-reproducible; the *netlist* is only
  value-reproducible. Compare extractions by sorted card set, not by sha.
* **HD2 at ≈ −100 dB is bench noise, and the same non-determinism proves it**:
  two netlists with byte-identical `C` cards measure −98.99 and −97.17 dB while
  THD and HD3 agree to 0.002 dB. Round 2's −104.22 dB was never a layout
  property. Do not spend a round chasing it.

---

## Summary

**Round 3 (this round)** — a narrow fix pass on the round-2 re-review: F16
(`lane_mid` is a knob; C(`net2`,`net3`) 1.379 → **0.000 fF**, +0.062° at the
failing corner, zero area), F17 (`net23_strap = lane_m1`; identical routing
restored on all six `rep_sink` units per BRIEF §2.1, disclosed cost −0.057°),
F18 (the symmetry guard-rail re-calibrated so it **FAILS on round 1's own GDS**,
15 rules / 8 layers, while round 2 and round 3 pass), F19 (the 7.556 µm² Metal1
exception re-attributed to `xr2`) and F20 (Metal4 + five via layers added, with a
new half-plane balance rule for the layers whose XOR saturates). `BOUNDS` is
33 knobs, **66/66 endpoints DRC-clean, 0 dead**. DRC 0, LVS matched, PEX CC + RC,
full corner set. **`ph_max` 331.155 → 331.160 nominal and 329.746 → 329.751 at
`cap_bcs` ×0.9 / `iref ×0.9` — the S1 corner miss stands at 0.249°**, delivered
with the miss documented as the block owner approved.

**What was done**

* **F16** — `LANE_MID = 1.9` (a module constant) → the knob `lane_mid`, default
  **4.9 µm**, `BOUNDS` (1.9, 4.9), coupled in `clamp()` to
  `axis_gap/2 − 1.1`; `axis_gap` default 6 → 12. The two `net2`/`net3` spines run
  **9.8 µm apart instead of 3.8**. Extracted **C(`net2`,`net3`) 1.3792 → 0.0000
  fF** and **C(`net4`,`net1`) 0.0257 → 0.0000** (78 C → 71 C). **No area, no DRC
  cost.** The build reproduces the reviewer's patched-generator what-if
  byte-identically (sha `c0507860…`).
* **F17** — `net23_strap` default → `lane_m1`, so the Metal1 drain bar is drawn
  on **all six** members of the 0.35 mV `rep_sink` class again (BRIEF §2.1).
  Disclosed: `net2` 29.106 → 32.328 fF, **−0.050° nominal / −0.057° at A7**.
  `min_m1` remains a knob.
* **F18** — the routing-layer XOR budget re-derived by calibration against two
  anchors (it01 known-bad, it12 known-good), plus a `--check-symmetry <gds>` CLI
  so any stored iteration can be re-judged. **it01 FAILS on 15 rules across
  8 layers; it08, it11, it12 PASS.** Numbers in §9.
* **F19 / F20** — the Metal1 exception re-attributed to `xr2` with the measured
  polygon coordinates; Metal4, Via1–Via4 and TopVia1 added to the table, and a
  **half-plane area balance** rule added for the layers whose XOR is
  structurally saturated (0.0000 µm² in round 3; it01 breaks it on seven layers,
  including the Metal3 21.089 µm² that *is* F6).
* **`BOUNDS`** — re-swept in full (not just the changed knobs, because the
  assertion runs inside `build()`): **66/66 build + DRC clean, 0 dead knobs.**
* Per-net budget table extended with the brief's **`budget_c_diff_ff`** column —
  the between-halves budget whose absence is what let F16 go uncounted.
* DRC 0 (no waivers), LVS matched against a byte-identical LVS reference,
  PEX **CC and RC**, full 9-point `AXES` + 5 cap-corner set, what-if
  attribution, four iterations snapshotted with diffs.

**Assumptions**

* The block owner's approval to deliver with the `cap_bcs` corner miss
  documented (PLAN R2.8 Q3) still stands; round 3 does not re-scope it.
* **The brief's matching rule outranks 0.05° of an optional corner.** That is the
  judgement behind F17 and it is the reviewer's own framing; it is the reason
  `net2` moves *further* over its balanced budget (1.24× → 1.42×) in a round
  whose headline number improved.
* `axis_gap`'s default change 6 → 12 is a **plan deviation** (PLAN §5 lists 6.0),
  taken because F16's fix is worthless without it and it costs no area. Flagged
  here for the same reason round 2 flagged `bank_gap` and `cap_gap`.
* `lane_mid`'s `BOUNDS` max is 4.9 = the geometric ceiling at the *default*
  `axis_gap`. A wider `axis_gap` would allow more, but the term it targets is
  already 0.0000 fF, so the range was not extended.
* No post-layout Monte Carlo; F17's matching benefit is therefore **structural,
  not measured** — no bench in this campaign models routing-induced ΔV_T.

**Errors / setbacks / gotchas**

* The first calibrated XOR table broke **7 of 66** `BOUNDS` endpoints — round 2's
  own recorded trap, in a new costume (§9). Fixed by two fraction changes plus
  configuration-declared relaxations, not by loosening the default rule.
* **kpex naming is not run-to-run deterministic**, and one RC extraction of the
  final GDS produced a mesh whose operating point ngspice solved to a shorted
  state (`fc` 0.11 Hz, 768 mW). Re-extracting fixed it; the reported RC is the
  second run. Compare extractions by **sorted card set**, never by file sha.
* **HD2 −104.22 → −97.17 dB is not a regression**, it is the bench's floor: two
  netlists with byte-identical `C` cards differ by 1.8 dB, and the two obvious
  physical candidates move it by ≤ 0.4 dB (§5).
* Δ(`net2`,`net3`) is **−0.001 fF** rather than round 2's exact 0.000. It is
  0.17 aF of kpex substrate-C rounding between two shapes that are geometrically
  identical (same area, perimeter and shape count on every layer).
* `net2` is 1.42× its nominal balanced budget, up from 1.24×. Priced, disclosed
  and deliberate (F17); the *differential* load the pole sees is 32.33 fF against
  round 2's honestly-counted 31.03 fF.

**Next Steps**

1. `layout-reviewer` re-review. Specifically: audit the §9 configuration-declared
   relaxations (are they exceptions or holes?) and the §5 F17 trade.
2. **The `cap_bcs`/`iref ×0.9` corner is now entirely a design-lane fix.** The
   0.062° the reviewer identified as layout-reachable has been taken; 0.249°
   remains and every remaining `net2` term is device geometry or island height.
   Candidates in the block owner's order: an `iref` trim, a small `C1`/`C2`
   re-allocation, a shorter `L` on `xm4` (45 µm), fewer `xm9` fingers.
3. Platform gaps this cell has now exposed three times: `tech_json=` (or a
   MIM-aware tech) for `signoff.run_pex` (F11), a `Cj(area, perimeter, Vbias)`
   term in `signoff.postlayout` (F3), a pin-list assertion in `signoff.lvs`
   (F13). New: a **mirror-and-swap symmetry** primitive in `spicexplorer-layout`
   would let §9's three declared relaxations become real assertions, and a
   **sorted-card-set comparator** for PEX netlists belongs next to `run_pex`.
   Nit, same package: `iterations_table_md` does not escape `|` inside a note,
   so it03's `3|1|3` breaks that one row of §10's table. The table is printed as
   generated — it is not hand-typed and must stay that way — so the fix belongs
   in `spicexplorer-layout`, not here.
4. `xr2_split` (PLAN R2.8 Q4) would take the Metal1 exception from 23.556 to
   16.0 µm² and close F19 geometrically rather than by attribution.
5. Chip-level antenna check (F12) and the block owner's acknowledgement of the
   MIM area flag (F15) before a second instance is placed.
