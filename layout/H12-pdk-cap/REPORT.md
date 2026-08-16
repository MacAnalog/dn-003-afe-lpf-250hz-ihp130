# Layout report — `H12-pdk-cap` (`lpf_core`), IHP SG13G2 — **round 4**

**KIND: LAYOUT OF RECORD (generated).** Everything below was produced by the
committed generator plus the platform signoff wrappers; nothing was hand-drawn
and no GDS was hand-edited. Round 4 is a **decision round, not a fix round**:
the block owner **reversed PLAN R2.8 Q2** (`bias_dummy_rows` 1 → **0**) and
adopted the area campaign's **A-best numeric knob point** as the new
`LayoutParams` defaults. It opens no new floorplan question, moves no device,
no size and no multiplicity, and changes no floorplan mode — it is a
**re-defaulting of existing knobs**, plus one generator bug fix the campaign
found. Hand off to `layout-reviewer`; this report does not self-certify
floorplan quality.

> ## Front page: 7.7 % smaller, 0.070° better at the failing corner, and the miss still stands
>
> **R2.10 A7 — `cap_bcs` ×0.9 with `iref ×0.9`: `ph_max` = 329.821° < 330°, S1
> still FAIL.** Round 3 was 329.751°, round 2 329.746°, round 1 329.299°,
> pre-layout 331.018° **PASS**. Round 4 nets **+0.070°** — the largest
> single-round move at that corner so far — and is **still 0.179° short**. The
> block owner approved delivering with this miss documented (PLAN R2.8 Q3); the
> residual remains design-lane, as §6 shows. **A1–A6 and A8–A11 pass.**
>
> The two things round 4 actually changed:
> 1. **The owner's reversal of R2.8 Q2 — `bias_dummy_rows = 0`.** Round 2 took
>    the dummy rows on a *hand bound* (F7, "1.2 Hz of `fc` against a 3.27 Hz
>    margin"); the area campaign then measured the other side of that trade:
>    **13 791 µm² — 5.6 % of the cell — plus 0.048° of `ph_max` and 2.09 fF on
>    `net2`/`net3`**, against a matching benefit that no bench in this campaign
>    can measure. The owner's call: not worth it. `bias_dummy_rows = 1` stays a
>    legal knob value (`BOUNDS` 0–1) and one build away; the matching debt is
>    re-opened **as a documented, unmeasured exposure** (PLAN R2.8 Q2 note,
>    dated 2026-08-16).
> 2. **The area campaign's A-best numeric knob point becomes the default.**
>    **17 numeric knobs** move (gaps, pitches, widths, via pad); **no
>    categorical or floorplan-mode knob moves**, so the topology the reviewer
>    signed off is untouched. Cross-check: the round-4 generator built at the
>    *round-3* default values reproduces round 3's GDS **byte-identically**
>    (sha `fc59cfd7ef…`). Together with (1): **247 136.9 → 228 093.6 µm²,
>    −7.71 %** — and *every* measured axis improves or holds: `ph_max` +0.061°
>    nominal, `net2`/`net3` −2.13 fF, DRC 0, LVS matched, `C(net2,net3)` still
>    exactly 0.0000 fF, symmetry assertion still PASS.
>
> **Generator fix landed in the same round:** `clamp()` now ties `cc12_cols` to
> `cc12_split`. `xc12` is an `m = 7` array placed as `m // cols` rows of `cols`,
> so a column count that does not divide 7 **silently dropped units** (`cols=2`
> → 6 plates) and LVS reported a device-count mismatch. The campaign found it
> because *its* loop runs LVS on every trial; **round 3's `BOUNDS` endpoint
> sweep was DRC-only and could not have** (§7).
>
> **What re-running that sweep *with* LVS then found (§7): it is no longer
> 66/66.** Three endpoints are not legal — `w_m1 = 1.0` and `ring_gap = 15.0`
> **short nets together at zero DRC violations**, and `w_tm1 = 4.0` trips the
> symmetry assertion by 0.6 %. `w_m1 = 1.0` **also fails at round-3 defaults**:
> it is a latent defect round 3 certified as clean because DRC cannot see a
> same-layer merge. The delivered cell is unaffected (all three knobs sit at
> their defaults, far from the offending endpoint); narrowing the three ranges
> is a round-5 generator change, listed in *Next Steps*.

| | |
|---|---|
| plan | `layout/H12-pdk-cap/PLAN.md` §Round 2 (**APPROVED 2026-08-16**), **R2.8 Q2 reversed by the block owner 2026-08-16** (note in `PLAN.md`); round 4 opens no new plan gate |
| brief | `layout/H12-pdk-cap/BRIEF.md` + `brief.json` |
| driver | `opt/results/README.md` — area campaign 2026-08-16 (A: 300 trials, B: 300 trials, 2 single evaluations) |
| generator | `layout/H12-pdk-cap/gen_H12_pdk_cap.py` sha256 `771468be65d24b2eb521e1aa9aa018e401774d31f61cadb6d999a252f37efb3c`, **33 knobs** (unchanged) — identical to `iterations/it14/gen.py`, the last entry of the trail |
| sizing record | `signoff/post-pvt/H12-pdk-cap/design.json` → `["design"]` (read at build time) |
| schematic of record | `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`, sha256 `ef78d6f8…faf3c7` |
| LVS reference | `layout/H12-pdk-cap/asbuilt/core_lvs.sp`, sha256 `060edcf9…3a5bb3b` — one line differs from round 3: `Mdumn` `w=336u` → **`w=144u`** (14 → 6 nmos dummies) |
| GDS (build product) | sha256 `1607b803d9dbb33620b7ba1609cf8edaa840358596abf1ede6625c06bc16e5d9` |
| post-layout netlist | `layout/H12-pdk-cap/asbuilt/core_pex.sp`, sha256 `d0e1d3d4…9e799f0` (kpex 2.5D **CC**, 69 C, + the six certified `cap_cmim` cards) |
| pre-layout yardstick | `signoff/post-pvt/H12-pdk-cap/scorecard.json` / `PRELAYOUT.md` §1 |
| round-3 yardstick | `iterations/it13/` (sha `fc59cfd7…0500ed`, the reviewed layout of record) |

## 0. What round 4 bought, in one table

| | pre-layout | round 1 | round 2 | round 3 | **round 4** | |
|---|---|---|---|---|---|---|
| **area** | — | 230 624 | 247 137 | 247 137 | **228 094 µm²** | **−7.71 %**, and 1.1 % below round 1 |
| `ph_max` nominal | 332.382 | 330.732 | 331.155 | 331.160 | **331.221** | +0.061 |
| `ph_max` @ `cap_bcs`, `iref ×0.9` | 331.018 PASS | 329.299 | 329.746 | 329.751 | **329.821 FAIL** | +0.070, still 0.179 short |
| C(`net2`) / C(`net3`) to ac gnd | — | 50.04 / 44.94 | 28.27 / 28.27 | 32.33 / 32.33 | **30.20 / 30.22** | −2.13 |
| **C(`net2`,`net3`)** (differential) | — | 0 | 1.3792 | 0.0000 | **0.0000** | held |
| **C(`net4`,`net1`)** | — | — | 0.0257 | 0.0000 | **0.0000** | held |
| Δ(`net2`,`net3`) | — | 5.10 | 0.000 | −0.001 | **−0.019** | 19 aF, still ≪ 0.5 fF |
| `bias_dummy_rows` | — | 0 | **1** | 1 | **0** | owner reversal |
| identical routing on all six `rep_sink` units | — | yes | no (F17) | yes | **yes** | BRIEF §2.1 held |
| `--check-symmetry` verdict | — | — | PASS | PASS | **PASS** (20 layers); **FAILS on it01** | guard-rail held |
| `BOUNDS` endpoints | — | 35/48 DRC | 64/64 DRC | 66/66 **DRC only** | **65/66 build, 65/65 DRC, 63/65 LVS** | LVS added to the gate; **3 bad endpoints found** (§7) |
| DRC / LVS | — | 0 / match | 0 / match | 0 / match | **0 / match** | no waivers |
| THD / IRN / P | −50.40 / 29.199 / 11.913 | −49.61 / 29.195 / 11.913 | −49.71 / 29.195 / 11.913 | −49.70 / 29.194 / 11.914 | **−49.73 / 29.194 / 11.914** | unmoved |

## 1. Outline and area

| | round 1 | round 3 | **round 4** |
|---|---|---|---|
| bbox | — | (−216.84, −10.00)…(216.84, 559.86) | **(−216.01, −8.83)…(216.01, 519.14)** |
| outline | 230 624 µm² | 433.68 × 569.86 = 247 136.88 µm² | **432.02 × 527.97 = 228 093.60 µm² = 0.2281 mm²** |
| aspect (h/w) | — | 1.314 | **1.222** |
| MIM area | 122 253 µm² | 122 253 µm² (49.5 %) | **122 253 µm² (53.6 %)** — unchanged in absolute terms (**F15 still flagged**, block-level) |
| devices | 15 certified | 16 instances for 15 certified + 14 nmos + 2 pmos dummies | **16 instances for 15 certified + 6 nmos + 2 pmos dummies** |
| n-well islands | 8 | 8, all tapped, mirror-XOR 0 | **8, all tapped, mirror-XOR 0** |

**−19 043.28 µm², −7.71 % vs round 3**, and **1.1 % below round 1's
230 624 µm²** — the first round that is smaller than the layout the review
process started from. It splits, measured, into:

| source | Δ area | how it was measured |
|---|---|---|
| `bias_dummy_rows` 1 → 0 | **−13 790.9 µm² (−5.58 %)** | single evaluation: round-3 defaults with only this knob changed → 233 345.97 µm² (`opt/results/summary.json` → `dummy0`) |
| the 17 moved numeric knobs (A-best) | **−5 252.4 µm² (−2.25 %)** | 228 093.60 − 233 345.97, i.e. the residue once the dummy rows are already out |

The height falls by 41.89 µm (the two dummy rows plus the tightened `row_gap`
/ `bias_row_gap`); the width falls by only 1.66 µm because it is still set by
bank B (±216.01 µm), which no device-row knob reaches. **The cell is now
53.6 % MIM by area** — the same absolute MIM, a smaller cell around it; the
F15 flag gets *stronger*, not weaker, and is still block-level.

**Determinism (A3):** the §7 endpoint sweep contains **eleven independent
builds whose knob value happens to equal the default** (`bias_dummy_rows` min,
`cc12_cols` max, `cc12_split` max, `cc19_cols` max, `cc13_cols` min,
`bankA_order` max, `cap_anti_orient` max, `cap_spine_side` max,
`net23_strap` min, `net23_spine_layer` max, `xr1_split` max) and **every one of
them produced sha `1607b803d9…`** — the sha stored in `iterations/it14/` and the
GDS `asbuilt/core_pex.sp` was extracted from.

## 2. DRC

| deck | run | result |
|---|---|---|
| `$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py` via `spicexplorer_signoff.run_drc` (`--no_density`) | full cell, top `lpf_core` | **0 violations** |

**Waivers: none.** Density/fill, sealring, pads and antenna diodes are out of
scope by PLAN §6. **A9 (partial): 65 of the 66 `BOUNDS` endpoints build, all 65
are DRC-clean, and 63 of them LVS-match** — the sweep now runs LVS, and that is
what found the three bad endpoints; §7 has the table and the diagnosis.

## 3. LVS

| | |
|---|---|
| deck | `sg13g2.lvs` via `spicexplorer_signoff.run_lvs` |
| reference | `asbuilt/core_lvs.sp` (emitted by `gen_H12_pdk_cap.py --lvs`) |
| result | **Netlists match**, 0 unmatched |

Round 4 moves **no device, no width, no length and no multiplicity of any
certified device**, so the reference regenerates identically to round 3 except
for the one line the reversal changes:

```
-Mdumn vss vss vss vss sg13_hv_nmos w=336u l=25u
+Mdumn vss vss vss vss sg13_hv_nmos w=144u l=25u
```

That is the merged dummy-nmos card: the generator emits
`n_n = 2·3·bias_dummy_cols + 2·(2·bias_dummy_rows)·(1 + bias_dummy_cols)`
dummy devices, i.e. **14 → 6** at `bias_dummy_rows` 1 → 0, and `14 × 24 µm =
336 µm` → `6 × 24 µm = 144 µm`. The reference is *derived from the knobs*, not
retyped — which is exactly why the campaign's `cc12_cols` bug surfaced as an
LVS mismatch rather than a silent layout defect. Provenance —
`postlayout.to_lvs_reference(core.sp)` plus four declared mechanical edits — is
unchanged and is set out in round 2's §3. `vbp` is still a dangling labelled pad
and therefore still unchecked by the deck (**F13 carried**, a platform fix).

## 4. PEX

| | CC (netlist of record) | RC (cross-check) |
|---|---|---|
| tool | kpex 0.3.12 (klayout-pex, 2.5D) via `spicexplorer_signoff.run_pex` | same, `--mode RC` |
| elements | **69 C, 0 R** (round 3: 71 C) | 69 C, **6 331 R** (round 3: 8 609 R) |
| `fc` / `ph_max` / `a1000` | 248.664 Hz / **331.2208°** / −49.218 dB | 248.710 Hz / **331.2205°** / −49.212 dB |
| `IRN` / `P` | 29.1944 µV / 11.9136 nW | 29.1920 µV / 11.9157 nW |

**RC converged without a `.nodeset`** — first extraction, no retry — and
reproduces CC to **0.047 Hz, 0.0003° and 0.006 dB**. BRIEF §1.2's "resistance is
a don't-care below ≈ 15 MΩ" re-measured on the smaller cell; the R mesh is 26 %
smaller than round 3's and still changes nothing.

**The two C elements round 3 had and round 4 does not are `C(vinn,vout_1)` and
`C(vinp,vout_2)`, 0.4 aF each.** Every other net pair present in round 3 is
present here — the C-card *set* is otherwise identical and only the values
moved. (Round 3's 78 → 71 was a *structural* change, F16; this one is noise
falling below kpex's halo.)

Extraction still runs on the **MIM-stripped** GDS and the six certified
`cap_cmim` cards are re-inserted verbatim (**F11 open**, ≤ 15 fF bound on
`net2`/`net3` carried). Round 3's gotcha — kpex node numbering is not
deterministic run-to-run, and one RC mesh once drove ngspice to a shorted
operating point — did **not** recur this round, which is consistent with it
being a per-extraction lottery rather than a property of the geometry. Compare
extractions by **sorted card set**, never by file sha.

## 5. Pre- vs post-layout scorecard (same benches, same definitions)

`lab.metrics.evaluate` (op+ac+noise, `mos_tt`, 27 °C, 1.5 V) and
`lab.thd.measure`, spliced through `Design.dut_override` — the block's own
frozen harness, unchanged. `scorecard_post.json` carries the machine-readable
version (round 4, with the full corner set and the budget table).

| line | spec | pre-layout | round 1 | round 2 | round 3 | **round 4** | Δ vs pre | Δ vs r3 | margin left |
|---|---|---|---|---|---|---|---|---|---|
| S1 `ph_max` | ≥ 330° | 332.382 | 330.732 | 331.155 | 331.160 | **331.221** | −1.162 | **+0.061** | 1.22° |
| S1 `a1000` | ≤ −48 dB | −49.026 | −49.263 | −49.220 | −49.222 | **−49.218** | −0.192 | +0.004 | 1.22 dB |
| S2 `fc` | 245–255 Hz | 249.775 | 248.275 | 248.651 | 248.639 | **248.664** | −1.111 | +0.025 | 3.66 / 6.34 Hz |
| S3 `dc` | \|·\| ≤ 0.2 dB | −0.0081 | −0.0081 | −0.0081 | −0.0081 | **−0.0081** | 0.000 | 0.000 | 0.192 dB |
| S3 `ripple` | ≤ 0.2 dB | 0.0523 | 0.0232 | 0.0355 | 0.0347 | **0.0363** | −0.016 | +0.002 | 0.164 dB |
| S4 `peak` | ≤ 0.2 dB | 0.0018 | 0.0206 | 0.0132 | 0.0136 | **0.0128** | +0.011 | −0.001 | 0.187 dB |
| S5 `IRN` | < 40 µV | 29.199 | 29.195 | 29.1945 | 29.1942 | **29.1944** | −0.005 | +0.000 | 10.8 µV |
| S6 `P` | < 50 nW | 11.9125 | 11.9130 | 11.9134 | 11.9136 | **11.9136** | +0.0011 | +0.000 | 38.1 nW |
| S7 `THD` | ≤ −40 dB | −50.401 | −49.614 | −49.714 | −49.701 | **−49.726** | +0.675 | −0.025 | 9.73 dB |
| — `HD3` | (not specced) | — | — | −49.912 | −49.898 | **−49.928** | — | −0.030 | — |
| — `HD2` | (not specced) | −100.19 | −88.06 | −104.22 | −97.17 | **−102.72** | −2.53 | −5.55 | bench floor, see below |
| — `C_total` | reported | 183.779 | 183.779 | 183.779 | 183.779 | **183.779 pF** | 0.000 | 0.000 | layout cannot move it |
| S8 | ≥ 2 papers | — | — | — | — | unchanged | — | — | documentation gate |

**All S1–S7 pass** (`s.violations == []`). A6 (`ph_max` ≥ 331.3°) is still
missed, now by **0.079°** (round 3: 0.140°).

**HD2's ±5 dB swing is this bench's numerical floor, established in round 3 and
unchanged here.** Round 3 measured **−98.99 and −97.17 dB from two PEX netlists
of the same GDS** with byte-identical `C` cards; round 4's −102.72 sits inside
that spread, and THD/HD3 — which are HD3-dominated and real — moved by 0.025 /
0.030 dB. Do not read −97.17 → −102.72 as a layout improvement.

### Every delta round 3 → round 4, explained

The round moved **one physical thing**: `net2`/`net3` (and, less, `net1`/`net4`,
`vout_1`/`vout_2`) got shorter spines because the cell lost **41.89 µm of
height** — the two dummy rows plus the tightened row/bias pitches, all of it
inside island A.
Everything in the table follows from that, and the what-ifs price it on round 4's
own extraction:

| what-if (on `core_pex.sp`) | `ph_max` | Δ | `fc` | round-3 Δ | reads as |
|---|---|---|---|---|---|
| as extracted | 331.221 | — | 248.664 | — | — |
| delete every `net2`/`net3` C | 331.901 | **+0.680** | 249.115 | +0.741 | the net costs 0.680° for 30.20 fF ⇒ **0.0225 °/fF** (round 3: 0.0229) |
| delete `net2`/`net3` → substrate only | 331.847 | +0.626 | 249.003 | +0.693 | 92 % of the net's cost is still its own substrate C |
| delete every `net4`/`net1` C | 331.710 | +0.489 | 248.709 | +0.483 | ~unchanged |
| delete `net2`/`net3` → `vbn` | 331.333 | +0.112 | 248.726 | +0.095 | `xm9`'s gate-to-drain; **grew** — the bias row is closer now |
| delete every `vout_1`/`vout_2` C | 331.266 | +0.045 | 248.681 | — | |
| delete `net2`/`net3` → `vinp`/`vinn` | 331.156 | **−0.064** | 248.693 | −0.058 | still *helps*; do not remove it |
| delete every `voutp`/`voutn` C | 331.157 | −0.064 | 249.269 | — | |
| delete **all** parasitic C | 332.332 | +1.111 | 249.772 | +1.172 | back to pre-layout within 0.05° |

**The arithmetic closes.** `net2`/`net3` lost **2.130 fF** per half at
**0.0225 °/fF** ⇒ **+0.048°** expected; measured **+0.061°**. The remaining
+0.013° is `net1`/`net4` (−0.16 fF) and `vout_1`/`vout_2` (−3.3 fF) shedding
their own share. No delta in the table needs a second mechanism — and none is
larger than the campaign's own noise floor except `ph_max`, `fc` and the HD2
draw.

`IRN`, `P`, `dc` and `C_total` did not move at all: noise and power are set by
the sizing record, and layout does not touch either.

### Corners on the PEX netlist (A7)

9-point `lab.corners.AXES` (both DUTs, `LPF_BIAS_ALPHA = 1.1`) **plus** the five
`cornerCAP.lib` points with the `iref` trim, all re-run on round 4's own
extraction.

| corner | pre `ph_max` | round-3 post | **round-4 post** | pre | **post** |
|---|---|---|---|---|---|
| `mos_tt` 27 °C 1.50 V | 332.38 | 331.16 | **331.22** | PASS | **PASS** |
| `mos_ss` 27 °C | 332.38 | 331.16 | **331.23** | PASS | **PASS** |
| `mos_ff` 27 °C | 332.17 | 330.96 | **331.03** | PASS | **PASS** |
| `mos_sf` 27 °C | 332.25 | 331.02 | **331.08** | PASS | **PASS** |
| `mos_fs` 27 °C | 332.44 | 331.23 | **331.29** | PASS | **PASS** |
| `mos_tt` 27 °C 1.65 V | 332.42 | 331.19 | **331.26** | PASS | **PASS** |
| `mos_tt` 1.35 V | 308.01 | 307.50 | 307.53 | FAIL | FAIL (headroom; fails pre-layout too) |
| `mos_tt` −40 °C | 237.04 | 235.04 | 235.17 | FAIL | FAIL (unchanged in kind) |
| `mos_tt` +125 °C | 222.31 | 221.75 | 221.76 | FAIL | FAIL (unchanged in kind) |
| `cap_typ` ×1.0 | 332.38 | 331.16 | **331.22** | PASS | **PASS** |
| `cap_bcs` ×1.0 | 330.95 | 329.69 | 329.76 | FAIL (`fc` 277 Hz) | FAIL (`fc` 276 Hz) — not an S1 corner either way |
| **`cap_bcs` ×0.9 + `iref ×0.9`** | **331.02** | **329.751** | **329.821** | **PASS** | **FAIL — S1 only (330.0 limit)** |
| `cap_wcs` ×1.0 | 333.61 | 332.43 | 332.49 | FAIL (`fc` 226 Hz) | FAIL (`fc` 226 Hz) |
| `cap_wcs` ×1.1 | 333.56 | 332.39 | **332.45** | PASS | **PASS** |

**Every corner that passed pre-layout still passes post-layout except one**, and
that one is the F1 blocker: **329.821 vs a 330.0 limit, 0.179° short** (round 3:
0.249°). At that corner S1's phase certificate is now the *only* violation —
`fc` 249.33 Hz, `a1000` −49.10 dB, `IRN` 30.6 µV all pass. The three
temperature/headroom failures fail **pre-layout too** and are a design-lane
property of the cell, not of this layout.

## 6. Parasitic budget — used vs allowed (kpex CC)

"to ac ground" sums C to `0`/substrate, `vdd`, `vbn`, `vbr`, `rep_x`,
`vinp`/`vinn` — the reviewer's definition, so the tables compare line for line
with rounds 1–3. Budgets are `brief.json`'s (`budget_c_ff` nominal /
`budget_c_ff_pvt`, `budget_c_asym_ff*` one-sided, `budget_c_diff_ff` between
halves).

| net | round 1 | round 2 | round 3 | **round 4** | allowed nom / pvt | ratio | one-sided Δ | allowed asym | **C between halves** | allowed diff |
|---|---|---|---|---|---|---|---|---|---|---|
| `net2` | 50.04 | 28.27 | 32.328 | **30.198** | 22.8 / 9.59 | **1.32× / 3.15×** | Δ = **−0.019** | 45.7 / 19.2 ✓ | **0.0000** | 11.4 ✓ |
| `net3` | 44.94 | 28.27 | 32.329 | **30.217** | 22.8 / 9.59 | 1.33× / 3.15× | " | " | " | " |
| `net4` | 77.30 | 67.578 | 67.338 | **67.180** | 82.8 / 34.8 | 0.81× / 1.93× | Δ = **0.102** | 166 / 69.5 ✓ | **0.0000** | 41.4 ✓ |
| `net1` | 67.27 | 67.471 | 67.249 | **67.078** | 82.8 / 34.8 | 0.81× / 1.93× | " | " | " | " |
| `vout_1` | 231.73 | 165.057 | 166.059 | **162.924** | 3350 | 0.05× | Δ = **−0.161** | 6710 ✓ | — | — |
| `vout_2` | 75.93 | 165.537 | 166.540 | **163.085** | 3350 | 0.05× | " | " | — | — |
| `voutp` | 505.50 | 459.418 | 460.060 | **463.401** | 905 / 455 | 0.51× / **1.02×** | Δ = **21.687** | 1800 / 905 ✓ | — | — |
| `voutn` | 352.55 | 438.359 | 439.002 | **441.714** | 905 / 455 | 0.49× / 0.97× | " | " | — | — |
| A ↔ B | 0.0000 | 0.0000 | 0.0000 | **0.0000** | 0.277 / 0.116 | — | — | — | **absent, not small** | — |

**`net2`/`net3` improve to 1.32× the balanced budget** (round 3: 1.42×, round 2:
1.24×) **with the brief's matching rule still honoured** — round 4 gets back
two-thirds of what F17 spent, and gets it from geometry rather than from
un-doing the matching fix. The differential term stays **exactly 0.0000 fF**,
the one-sided Δ is 19 aF against a 45.7 fF allowance, and `voutp` is the only
line anywhere near its budget (1.02× of the *pvt* number, 0.51× of nominal) —
unchanged in kind from round 3.

Every net in the extraction, for completeness:

| net | round 3 | **round 4** | Δ fF |
|---|---|---|---|
| `net1` / `net2` / `net3` / `net4` | 67.249 / 32.328 / 32.329 / 67.338 | **67.078 / 30.198 / 30.217 / 67.180** | −0.17 / **−2.13** / **−2.11** / −0.16 |
| `vout_1` / `vout_2` | 166.059 / 166.540 | **162.924 / 163.085** | −3.14 / −3.46 |
| `voutp` / `voutn` | 460.060 / 439.002 | **463.401 / 441.714** | +3.34 / +2.71 |
| `vbn` / `vbr` / `rep_x` | 609.904 / 95.698 / 54.445 | **608.281 / 95.304 / 54.254** | −1.62 / −0.39 / −0.19 |
| `vdd` | 206.922 | **209.600** | +2.68 |
| `vinp` / `vinn` | 34.027 / 34.027 | **33.869 / 33.869** | −0.16 / −0.16 |

The three nets that *grew* — `vdd`, `voutp`, `voutn` — are the wide supply and
output rails, and they grew because the tightened pitches (`row_gap` 6.0 → 3.11,
`bias_row_gap` 4.0 → 2.91, `ring_gap` 4.0 → 2.81) put them closer to their
neighbours and `w_m2`/`w_tm1` made them slightly wider. All three sit at
**≤ 0.51× of nominal budget**, and the pair asymmetry Δ(`voutp`,`voutn`) moves
21.058 → 21.687 fF against a 905 fF pvt allowance. Not a concern; recorded so
that the next round does not have to re-derive it.

### Where `net2`'s 30.20 fF sits, and where the 2.13 fF went

Measured pair by pair on the two extractions (same definition, same tool):

| `net2` couples to | round 3 | **round 4** | Δ | why |
|---|---|---|---|---|
| substrate (`0`) | 26.669 | **23.917** | **−2.752** | the cell (and island A with it) is 41.89 µm shorter ⇒ the Metal5 spine and TopMetal1 haul that carry `net2` are shorter. This is the whole story. |
| `vbn` | 3.930 | **4.372** | +0.442 | `bias_row_gap` 4.0 → 2.91 and `row_gap` 6.0 → 3.11 bring `xm9`'s gate bus closer; part of it is `xm9`'s own gate-to-drain, which no knob reaches |
| `vinp` | 1.639 | **1.821** | +0.182 | the `xm2` gate line is closer for the same reason — and the what-if says this term **helps** phase (−0.064°), so it is not a cost |
| `vbr` | 0.091 | **0.089** | −0.002 | |
| **to ac ground** | **32.329** | **30.198** | **−2.130** | |
| `vout_1` / `vout_2` (not ac gnd) | 0.632 / 0.127 | 0.683 / 0.170 | +0.05 / +0.04 | |
| **`net3`** | **absent** | **absent** | — | F16 held at the new `lane_mid` = 4.69 |

`net2` and `net3` remain each other's mirror image: the extraction's only
difference is **19 aF** on the substrate term, the same kpex substrate-C rounding
between geometrically identical shapes that round 3 saw at 1 aF. The generator's
own `--check-symmetry` assertion (§8) passes on all nine physical layers exactly.

### Why the last 0.179° is still not here

`net2`/`net3` cost **0.680° for 30.20 fF ⇒ 0.0225 °/fF**; closing 0.179° at
`cap_bcs`/`iref ×0.9` needs **≈ 8 fF off each half**. What is left on that net
is: `xm4`'s own gate poly (W 1.5, **L 45 µm** — layout-invariant), `xm9`'s
finger pitch, island-A height (now 41.89 µm shorter and still shrinkable only by
moving devices the plan fixes), and `xm9`'s gate-to-drain. Round 3 concluded the
0.062° the reviewer called layout-reachable had been spent; round 4 found
**another 0.070° in a knob nobody had priced** — which is the honest update to
that conclusion: *the layout-reachable budget was under-estimated, and the way
it was found was a measured search, not a hand argument.* The **remaining
0.179° is still a sizing question** (an `iref` trim, a small `C1`/`C2`
re-allocation, a shorter `L` on `xm4`, fewer `xm9` fingers), because the
remaining terms above are device geometry.

### Known-unmodelled and known-over-modelled terms (A11)

Unchanged in kind from rounds 2–3: **F3** n-well↔substrate junction C
(lumped-`Cj` what-if bound −0.108…−0.259°, deferred by R2.7 — note the NWell
*area* grew 5 213 → 5 400 µm² with `well_margin` 0.62 → 0.86, so this
unmodelled term is if anything slightly larger this round); **F11** MIM
top-plate environment C (≤ 15 fF on `net2`/`net3`, optimistic); the
**GatPoly-to-substrate over-count** (≈ 6 fF of `net2`, pessimistic, identical in
all four rounds so the comparison stays consistent); **F12** the ≈ 53 : 1
antenna ratio with no antenna rule in the deck — dominated by the MIM top plate,
which round 4 does not move; **F15** MIM is now **53.6 %** of the cell (was
49.5 %) because the cell shrank and the MIM did not.

## 7. Parameters, `BOUNDS`, and the endpoint sweep (A9)

`set(BOUNDS) == set(LayoutParams fields)` is asserted inside `validate()`, which
`build()` calls on every build; `clamp()` resolves the knob couplings. **Round 4
adds no knob and removes none — it moves 18 defaults**: `bias_dummy_rows` 1 → 0
(the owner's reversal) and 17 numeric knobs to the area campaign's A-best point
(`opt/results/summary.json` → `Abest_dummy0`). Every categorical / floorplan-mode
knob keeps its round-3 value, so the *topology* the reviewer signed off is
untouched.

**Cross-check that this is a re-defaulting and nothing else:** the round-4
generator built at the **round-3 default values** reproduces round 3's GDS
**byte-identically** — sha `fc59cfd7ef…`, area 247 136.9 µm². The only code
change in the geometry path is the `cc12_cols` clamp, which is inert at
`cc12_cols = 7`.

### The new `clamp()` tie: `cc12_cols` ↔ `cc12_split`

`xc12` is an `m = 7` MIM array and the array placer emits `m // cols` rows of
`cols` units. A `cols` that does not divide 7 therefore **silently drops
plates** — `cc12_cols = 2` gives 3 rows of 2 = 6 units, one short — and LVS
reports a device-count mismatch on a build that is otherwise clean. Only
`cols = 7` can carry the mirror-symmetric `3|1|3` plate split, so the two knobs
are one structural degree of freedom:

```python
if d["cc12_cols"] not in (1, 7):
    d["cc12_cols"] = 7 if d["cc12_cols"] > 4 else 1
if d["cc12_cols"] != 7:
    d["cc12_split"] = "none"
```

The area campaign found this because **its** loop runs LVS on every trial.
Round 3's endpoint sweep was **DRC-only** and structurally could not have.

### The endpoint sweep, now with LVS — and it is no longer 66/66

66 endpoints (33 knobs × 2), each: build → PDK DRC → generator-emitted
per-endpoint `core_lvs.sp` → `sg13g2.lvs`.

| | round 3 (DRC only) | **round 4 (DRC + LVS)** |
|---|---|---|
| build ok | 66 / 66 | **65 / 66** |
| DRC clean | 66 / 66 | **65 / 65** |
| LVS match | *not run* | **63 / 65** |
| dead knobs (identical GDS at both endpoints) | 0 | **0** |

| knob | round-3 default | **round-4 default** | range (`BOUNDS`) | min endpoint DRC / LVS | max endpoint DRC / LVS |
|---|---|---|---|---|---|
| `dev_gap_x` | 2.0 | **1.69** | 1.0 – 6.0 | 0 / match | 0 / match |
| `axis_gap` | 12.0 | **12.92** | 4.0 – 30.0 | 0 / match | 0 / match |
| `lane_mid` | 4.9 | **4.69** | 1.9 – 4.9 | 0 / match | 0 / match |
| `row_gap` | 6.0 | **3.11** | 3.0 – 20.0 | 0 / match | 0 / match |
| `bias_row_gap` | 4.0 | **2.91** | 2.0 – 12.0 | 0 / match | 0 / match |
| `bias_dummy_cols` | 1 | 1 | 0 – 2 | 0 / match | 0 / match |
| `bias_dummy_rows` | 1 | **0** | 0 – 1 | 0 / match | 0 / match |
| `gmfb_dummy` | 1 | 1 | 0 – 2 | 0 / match | 0 / match |
| `xr1_split` | True | True | False – True | 0 / match | 0 / match |
| `well_margin` | 0.62 | **0.86** | 0.62 – 3.0 | 0 / match | 0 / match |
| `well_gap` | 2.0 | **1.86** | 1.8 – 6.0 | 0 / match | 0 / match |
| `ring_w` | 1.0 | **1.02** | 0.6 – 3.0 | 0 / match | 0 / match |
| `ring_gap` | 4.0 | **2.81** | 2.0 – 15.0 | 0 / match | 0 / **MISMATCH** |
| `shield_w` | 4.0 | **6.52** | 2.0 – 12.0 | 0 / match | 0 / match |
| `cap_gap` | 0.6 | **0.74** | 0.6 – 3.0 | 0 / match | 0 / match |
| `cap_bank_gap` | 10.0 | **9.86** | 9.0 – 40.0 | 0 / match | 0 / match |
| `cap_axis_gap` | 5.0 | **4.39** | 3.0 – 20.0 | 0 / match | 0 / match |
| `bank_gap` | 14.0 | **16.23** | 14.0 – 60.0 | 0 / match | 0 / match |
| `w_m1` | 0.2 | 0.2 | 0.16 – 1.0 | 0 / match | 0 / **MISMATCH** |
| `w_m2` | 0.2 | **0.24** | 0.2 – 0.4 | 0 / match | 0 / match |
| `w_m3` | 0.25 | 0.25 | 0.2 – 1.0 | 0 / match | 0 / match |
| `w_tm1` | 1.7 | **1.94** | 1.64 – 4.0 | 0 / match | **build FAIL** |
| `via_pad` | 2.0 | **1.73** | 1.7 – 3.0 | 0 / match | 0 / match |
| `cc19_cols` | 2 | 2 | 1 – 2 | 0 / match | 0 / match |
| `cc1_cols` | 4 | 4 | 2 – 8 | 0 / match | 0 / match |
| `cc12_cols` | 7 | 7 | 1 – 7 | 0 / match | 0 / match |
| `cc13_cols` | 1 | 1 | 1 – 2 | 0 / match | 0 / match |
| `bankA_order` | c13_axis | c13_axis | c19_axis – c13_axis | 0 / match | 0 / match |
| `cap_spine_side` | mirror | mirror | left – mirror | 0 / match | 0 / match |
| `cap_anti_orient` | True | True | False – True | 0 / match | 0 / match |
| `cc12_split` | 3\|1\|3 | 3\|1\|3 | none – 3\|1\|3 | 0 / match | 0 / match |
| `net23_strap` | lane_m1 | lane_m1 | lane_m1 – min_m1 | 0 / match | 0 / match |
| `net23_spine_layer` | Metal5 | Metal5 | Metal2 – Metal5 | 0 / match | 0 / match |

**Three endpoints are not legal, and all three are worth reading carefully.**

| endpoint | verdict | at round-3 defaults | what it is |
|---|---|---|---|
| `w_m1 = 1.0` (max) | DRC **0**, LVS **mismatch** | **also mismatches** | A 1 µm Metal1 wire width merges the local hops into one another: the extracted netlist has a single net named `net1\|net2\|net3\|net4\|vbr\|vdd\|vout_1\|vout_2\|voutn\|voutp\|vss`. **A pre-existing latent defect** — it was there in round 3 and the DRC-only sweep could not see it. |
| `ring_gap = 15.0` (max) | DRC **0**, LVS **mismatch** | **matches** (area 279 723.7 µm²) | The extraction returns one merged net `vout_1\|vout_2\|vss`. **New at the A-best point** (area 263 219.6 µm²): the same knob value was legal around the round-3 defaults, so it is the *combination* with the tightened pitches that shorts, not the value. The exact colliding shape was **not** diagnosed — the measurement is the merged net, and that is enough to call the endpoint illegal. |
| `w_tm1 = 4.0` (max) | **build FAIL** | builds clean | `AssertionError: mirror symmetry broken -- TopMetal1: XOR 72.32 um2 > 71.86`. **New at the A-best point, and by 0.6 %**: the XOR budget is scale-relative (§9), the cell shrank, so the budget shrank with it while a 4 µm TopMetal1 makes the asymmetric `vbp`/`xr2` features bigger. The guard-rail is doing its job; the *range* is what is now wrong. |

**Why `w_m1 = 1.0` matters more than the other two.** It shorts eleven nets and
**DRC reports zero violations** — same-layer shapes that touch simply merge, and
no spacing rule can fire. Round 3 certified this endpoint as clean. It was not,
and no amount of DRC would have said so. **An endpoint sweep without LVS is not
a gate**; this is the round's most portable lesson and it is now written into
the sweep.

These three are **`BOUNDS` defects, not layout-of-record defects**: the
delivered cell sits at the defaults, all three knobs are far from the offending
endpoint, and every one of the 63 legal endpoints is DRC-clean and LVS-matched.
The fix (narrow `w_m1` to ~0.4, `ring_gap` to ~10, `w_tm1` to ~3.0, or make
`clamp()` resolve them the way it now resolves `cc12_cols`) is a **round-5
generator change** and is listed in *Next Steps*; it is deliberately not made
here, because it changes `clamp()` and would need its own build → DRC → LVS →
PEX round and its own re-review.

**Infrastructure gotcha, recorded:** the first pass of this sweep ran 8 KLayout
jobs concurrently and produced **7 spurious DRC failures and 7 spurious LVS
mismatches**, every one with an *empty* violation list and a truncated deck log.
Re-run at 2 workers, all 7+7 passed and the 2 real mismatches reproduced
exactly. Treat an empty failure as an infrastructure failure.

`W`, `L`, `ng`, `m` are read from `design.json` and are never knobs.
**Determinism (A3):** eleven builds in the sweep above land on the default
value of their own knob and **all eleven give sha `1607b803…c16e5d9`** (§1).


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

Measured on `iterations/it14/layout.gds` — **verdict PASS on all 20 layers**:

| layer | XOR µm² | budget | balance (L−R) µm² | balance budget | of total µm² | note |
|---|---|---|---|---|---|---|
| Activ / GatPoly / Cont / ThickGateOx / NWell / pSD / nSD / MIM / Vmim | **0.0000** | **0 (exact)** | 0.0000 | — | 16 635 / 11 081 / 332 / 12 168 / 5 400 / 9 985 / 505 / 122 253 / 23 266 | every device, well, tap, contact and MIM unit is exactly its own mirror image |
| Metal1 | 23.5560 | 46.45 | −4.7300 | — | 7 742 | **unchanged from round 3**: 16.0 = the `vbp` pad (BRIEF §9) + 7.556 = `xr2` — F19 below |
| Metal2 | 0.2128 | 2.00 | **0.0000** | 1.24 | 248 | |
| Metal3 | 268.3874 | 332.14 | **0.0000** | 5.54 | 1 107 | the four balanced top-plate crossing tracks (saturated XOR) |
| Metal4 | 35.9148 | 56.00 | **0.0000** | 1.00 | 36.8 | via pads only; XOR is 98 % of its own area **by construction** |
| Metal5 | 32.8232 | 105.02 | 4.4400 | — | 131 281 | |
| TopMetal1 | 35.0752 | 71.51 | 17.5376 | — | 119 177 | |
| Via1 | **0.0000** | 0.50 | **0.0000** | 0.20 | 3.36 | |
| Via2 | 0.1444 | 0.50 | **0.0000** | 0.20 | 2.96 | |
| Via3 | 3.8988 | 4.53 | **0.0000** | 0.21 | 4.12 | saturated (93 %) |
| Via4 | 3.8988 | 4.53 | **0.0000** | 0.21 | 4.12 | saturated (93 %) |
| TopVia1 | 1.4112 | 1.55 | **0.0000** | 0.20 | 1.41 | saturated (100 %); **9 % of margin — the tightest line in the table** |

The budgets are scale-relative (§9), so they move with the geometry: the cell
shrank, and Metal1's budget went 48.61 → 46.45 and Metal3's 338.01 → 332.14
while the measurements fell by more. `--check-symmetry iterations/it01/layout.gds`
still **FAILS on 15 rules across 8 layers**, so the guard-rail is still
calibrated against both anchors.

**F20 — why the via layers and Metal4 needed a second rule, not just a budget.**
The F8 anti-orientation makes the two `xc19` (and `xc12`) top-plate lines swap
sides, and the two members of each swapped pair sit at **different y**. Mirroring
one therefore does not land on the other, and the plain XOR saturates at ≈ 2× the
layer's own area — a number that cannot distinguish "balanced swap" from "the
whole thing is on one side". The discriminating statement is the **half-plane
area balance**, which a swap leaves at exactly 0 and a one-sided haul does not.
Round 4 measures **0.0000 µm² on all eight balance layers**; round 1's it01
breaks it on Metal2 (4.000), **Metal3 (21.089)**, Metal4 (4.000), Via1–Via4
(0.325) and TopVia1 (0.353). That Metal3 number *is* F6 — round 1's `net4`
Metal3 haul was 184.4 µm against `net1`'s 29.8 µm.

**F19 — the Metal1 exception is `xr2`, not `xr1`.** Measured on the round-3 GDS
and **numerically identical on round 4's** (23.5560 µm², the same six polygons),
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

**Round-4 postscript — the scale-relative budget bites a third time.** Because
the budgets are `max(floor, fraction × the layer's own area)`, shrinking the
cell shrinks them. TopMetal1's went **71.86 µm²** at the new defaults, and the
`w_tm1 = 4.0` endpoint — which built clean at round-3 defaults — now measures
**72.32** and fails the assertion **by 0.6 %** (§7). Nothing about that layout
got less symmetric; the *yardstick* moved. This is the third costume of the same
trap (round 2: a fixed budget calibrated for one geometry; round 3: a calibrated
budget that broke seven endpoints; round 4: a scale-relative budget that
re-scopes a knob range when the area objective moves). The lesson to carry: **a
budget that depends on the geometry must be re-swept whenever the geometry
moves, and the sweep is the only thing that will tell you** — which is exactly
what the endpoint sweep is for, and why it now runs LVS too.

## 10. Iterations

<!-- generated: `spicexplorer-layout iterations-md layout/H12-pdk-cap/iterations` -->

| it | what changed / what it fixed | DRC | LVS | PEX | area µm² | files |
|---|---|---|---|---|---|---|
| it01 | Baseline: round-1 layout of record rebuilt (sha e5cfa1da…) — DRC 0, LVS, 78 C; net2 50.0 fF, ph_max 330.73° | **0** | match | CC 78C/0R | 230624 | [gen](iterations/it01/gen.py) [png](iterations/it01/layout.png) |
| it02 | Cleanup: dead tap_len knob removed, cc13 1 column, cap spine on the axis-facing column → net2 50.0→42.5 fF, net4 asym 10.0→0.1 fF | **0** | match | CC 78C/0R | 230624 | [gen](iterations/it02/gen.py) [png](iterations/it02/layout.png) [diff_from_it01](iterations/diff_it01_it02.png) |
| it03 | xc13/xc17 moved onto the axis, xc19 split 4+4 outboard, xc12 anti-oriented 3|1|3 → LVS ok but 5× TM1.b: comb-bar ends 0.7 µm apart at the seam | 5 (TM1.b ×5) | match | — | 233346 | [gen](iterations/it03/gen.py) [png](iterations/it03/layout.png) [diff_from_it02](iterations/diff_it02_it03.png) |
| it04 | TM1.b fixed (comb bars inset w/2 before end caps) → DRC 0; re-order measured: net2 42.5→32.7 fF, Δ(net2,net3) 5.1→0.03, ph_max +0.23° | **0** | match | CC 78C/0R | 233346 | [gen](iterations/it04/gen.py) [png](iterations/it04/layout.png) [diff_from_it03](iterations/diff_it03_it04.png) |
| it05 | net2/net3 spine Metal2→Metal5, min-Metal1 straps, xc13/xc17 top-aligned → net2 32.7→26.5 fF, ph_max 331.14→331.21° | **0** | match | CC 78C/0R | 233346 | [gen](iterations/it05/gen.py) [png](iterations/it05/layout.png) [diff_from_it04](iterations/diff_it04_it05.png) |
| it06 | Bias array gets dummy rows, xr1 split anti-oriented → matching per brief; cost +31.8 µm height (+5.9 %), net2 +1.8 fF, ph_max −0.06° | **0** | match | CC 78C/0R | 247137 | [gen](iterations/it06/gen.py) [png](iterations/it06/layout.png) [diff_from_it05](iterations/diff_it05_it06.png) |
| it07 | Build-time mirror-XOR + A/B keep-apart asserts added; they caught a 5 nm contact-row asymmetry → contact centres snapped; GDS electrically same | **0** | match | CC 78C/0R | 247137 | [gen](iterations/it07/gen.py) [png](iterations/it07/layout.png) [diff_from_it06](iterations/diff_it06_it07.png) |
| it08 | All 64 knob endpoints made DRC-legal (scale-relative XOR budget, TGO.e floor on nmos pitch, w_m1 min 0.16), dead vbn keep-out knob deleted | **0** | match | CC 78C/0R | 247137 | [gen](iterations/it08/gen.py) [png](iterations/it08/layout.png) [diff_from_it07](iterations/diff_it07_it08.png) |
| it09 | 1.4 fF net2↔net3 lane coupling: lane offset made a knob, spines 3.8→9.8 µm apart → coupling 0.000 fF, ph_max +0.05° | **0** | match | CC 71C/0R | 247137 | [gen](iterations/it09/gen.py) [png](iterations/it09/layout.png) [diff_from_it08](iterations/diff_it08_it09.png) |
| it10 | Identical Metal1 drain bar restored on all six bias-sink units (matching rule) → net2 29.1→32.3 fF, ph_max −0.05° (disclosed trade) | **0** | match | CC 71C/0R | 247137 | [gen](iterations/it10/gen.py) [png](iterations/it10/layout.png) [diff_from_it09](iterations/diff_it09_it10.png) |
| it11 | Symmetry guard-rail recalibrated: round-1 layout now FAILS it (15 rules), round 3 passes; via layers + half-plane balance added; --check-symmetry CLI | **0** | match | CC 71C/0R | 247137 | [gen](iterations/it11/gen.py) [png](iterations/it11/layout.png) [diff_from_it10](iterations/diff_it10_it11.png) |
| it12 | Recalibration had made 7 legal knob endpoints unbuildable → per-topology declared budgets; 66/66 endpoints DRC-clean, GDS unchanged | **0** | match | CC 71C/0R | 247137 | [gen](iterations/it12/gen.py) [png](iterations/it12/layout.png) [diff_from_it11](iterations/diff_it11_it12.png) |
| it13 | Docs-only round (round-3 summary in module docstring); GDS byte-identical, re-verified DRC 0 / LVS / 71 C — the committed generator | **0** | match | CC 71C/0R | 247137 | [gen](iterations/it13/gen.py) [png](iterations/it13/layout.png) [diff_from_it12](iterations/diff_it12_it13.png) |
| it14 | Owner dropped the bias dummy rows + area-campaign knobs as defaults → area 247.1k→228.1k µm² (−7.7 %), ph_max 331.16→331.22°, net2 32.3→30.2 fF | **0** | match | CC 69C/0R | 228094 | [gen](iterations/it14/gen.py) [png](iterations/it14/layout.png) [diff_from_it13](iterations/diff_it13_it14.png) |

Fourteen rounds across four passes; round 4 is **it14 alone**. It is the only
round in this trail whose change is *not* a generator edit that draws something
differently: the geometry code is byte-identical to it13 apart from the
`cc12_cols` clamp — proven by rebuilding at round-3 defaults and getting
round 3's sha back — and what moved is the **default value of 18 knobs**. That is
the point of having had the knobs: a decision the owner made on measured
numbers cost one build, and the trail shows it next to the thirteen builds that
argued about the same 0.2°.

The dead ends and lessons worth remembering from this round:

* **A hand bound survived three rounds because nothing could measure it.** F7's
  dummy rows were taken in round 2 on "1.2 Hz of `fc` against a 3.27 Hz margin",
  priced at "+2.3 fF ⇒ −0.06°", and never revisited — because the *benefit* side
  still has no bench. What finally moved it was measuring the **cost** properly
  (5.6 % of the cell, in area, which nobody had put a number on until the
  campaign minimised for it) and handing the owner both sides. Lesson: when one
  side of a trade is unmeasurable, measure the other side *harder*, and re-open
  the decision when the number changes.
* **A search found 0.070° that four rounds of argument said was not there.**
  Round 3's §6 concluded the layout-reachable part of the corner miss had been
  spent. It had not: 21 numeric knobs moving together gave more than any of them
  gave alone, and no hand analysis in rounds 1–3 proposed that combination. The
  honest reading is not "the analysis was wrong" but "**hand analysis prices one
  knob at a time; the coupling between them is what the optimizer finds**".
* **A DRC-only endpoint sweep certifies almost nothing.** Round 3 reported
  "66/66 endpoints build and DRC clean". Round 4 ran the same sweep **with LVS**
  and found **two endpoints that short nets together** — `w_m1 = 1.0` merges
  eleven nets into one, `ring_gap = 15.0` merges `vout_1`/`vout_2`/`vss` — with
  **zero DRC violations**, because same-layer shapes that touch simply merge and
  no spacing rule fires. §7 has the table. A gate that cannot fail on the defect
  class you care about is decoration.
* **Parallel KLayout runs fake failures.** The first pass of this sweep ran 8
  DRC/LVS jobs concurrently and reported 7 spurious DRC failures and 7 spurious
  LVS mismatches, all with *empty* violation lists — truncated runs, not
  results. Re-run at 2 workers, every one of them passed, and the two real
  mismatches reproduced. **An empty failure is an infrastructure failure**;
  re-run before believing it.
* Carried from round 3 and still true: kpex naming is not run-to-run
  deterministic (compare by sorted card set); HD2 at ≈ −100 dB is bench noise
  (this round drew −102.72 against round 3's −97.17 with no physical change to
  the output nets, which is the same ±3 dB spread).

---
## Summary

**Round 4 (this round)** — a **decision round**: the block owner reversed
PLAN R2.8 Q2 (`bias_dummy_rows` 1 → **0**) and adopted the area campaign's
A-best numeric knob point as the new `LayoutParams` defaults. **18 defaults
move, no knob is added or removed, no categorical or floorplan-mode knob
changes, and no device, size or multiplicity moves** — proven by rebuilding the
round-4 generator at round-3 default values and getting round 3's GDS sha
`fc59cfd7ef…` back byte-identically. Result: **247 136.9 → 228 093.6 µm²
(−7.71 %, and 1.1 % below round 1)**, `ph_max` **331.155 → 331.221** nominal and
**329.751 → 329.821** at `cap_bcs` ×0.9 / `iref ×0.9`, `net2`/`net3`
**32.33 → 30.20 fF**, DRC 0, LVS matched, PEX CC **and** RC, full corner set,
symmetry assertion PASS. **The S1 corner miss stands at 0.179°** (was 0.249°),
delivered with the miss documented as the block owner approved.

**What was done**

* **PLAN R2.8 Q2 reversed** (dated note added to `PLAN.md`): `bias_dummy_rows`
  1 → 0. Measured cost of the round-2 decision, which is what re-opened it:
  **13 791 µm² (5.6 % of the cell), 0.048° of `ph_max`, 2.09 fF on
  `net2`/`net3`** — against a matching benefit no bench in this campaign can
  measure. `bias_dummy_rows = 1` remains a legal knob; the matching debt is
  re-opened as a **documented, unmeasured** exposure.
* **A-best numeric knobs adopted** (17 of them, `opt/results/summary.json` →
  `Abest_dummy0`): a further **−5 252 µm² (−2.25 %)** on top of the dummy rows,
  with `ph_max` and every budget line improving or holding.
* **Generator fix — `clamp()` ties `cc12_cols` to `cc12_split`.** `xc12` is an
  `m = 7` array placed as `m // cols` rows; a `cols` that does not divide 7
  silently dropped plates and broke LVS. Found by the campaign, whose loop runs
  LVS per trial.
* **`BOUNDS` endpoint sweep re-run with LVS** (66 endpoints): **65 build, 65/65
  DRC-clean, 63/65 LVS-match, 0 dead knobs**. Three endpoints are not legal —
  `w_m1 = 1.0` and `ring_gap = 15.0` **short nets at zero DRC violations**, and
  `w_tm1 = 4.0` trips the mirror-symmetry assertion by 0.6 %. §7.
* **Full re-measurement on round 4's own extraction**: nominal S1–S7 + THD,
  9-point `AXES` × 2 DUTs, 5 cap corners with the `iref` trim, per-net parasitic
  budget with the between-halves column, nine what-if attributions, RC
  cross-check (69 C / 6 331 R, agreeing with CC to 0.0003°), and
  `--check-symmetry` on the delivered GDS (PASS, 20 layers) and on it01 (FAIL,
  15 rules / 8 layers).
* it14 snapshotted with its `diff_it13_it14.png`; §10's table is generated, not
  typed.

**Assumptions**

* The block owner's reversal of R2.8 Q2 is taken as given for this round; the
  designer's recommendation in round 2 was the opposite, and both sides are now
  on the record with numbers (PLAN R2.8 Q2 note).
* **The matching benefit of the dummy rows is still unmeasured**, in either
  direction. Nothing in this campaign models edge/interior ΔV_T, so removing
  them is a *priced-cost, unpriced-benefit* decision — the same epistemic shape
  as taking them was, with the sign flipped.
* The block owner's approval to deliver with the `cap_bcs` corner miss
  documented (PLAN R2.8 Q3) still stands; round 4 does not re-scope it.
* The A-best point came from an optimizer minimising **area** subject to DRC 0,
  LVS match, S1–S7 pass, `ph_max ≥ 331.10°` and `net2`/`net3 ≤ 32.4 fF`. It is
  not claimed optimal for anything else — in particular no matching, EM or
  yield objective was in the loop.
* Round 3's other deviations (`axis_gap` vs PLAN §5, `bank_gap`, `cap_gap`)
  carry forward and are now joined by 17 more numeric defaults that differ from
  PLAN §5's table; the PLAN's *ranges* are unchanged, so this is a
  within-envelope re-defaulting.

**Errors / setbacks / gotchas**

* **A DRC-only endpoint sweep certified a short.** `w_m1 = 1.0` merges eleven
  nets into a single extracted net and produces **zero DRC violations** —
  same-layer shapes that touch just merge. It fails at round-3 defaults too, so
  round 3's "66/66 endpoints DRC-clean" was true and useless. The gate now runs
  LVS.
* **Two more endpoints went illegal because the cell shrank**: `ring_gap = 15.0`
  now shorts `vout_1`/`vout_2`/`vss`, and `w_tm1 = 4.0` trips the
  **scale-relative** XOR budget by 0.6 % (72.32 vs 71.86 µm²). A budget that
  scales with the geometry silently re-scopes what a knob range means — the
  same class of trap round 2 and round 3 each hit once.
* **Parallel KLayout fabricates failures.** Eight concurrent DRC/LVS jobs gave 7
  spurious DRC failures and 7 spurious LVS mismatches, all with **empty**
  violation lists and truncated deck logs. Re-running at 2 workers passed every
  one and reproduced the two real mismatches. An empty failure is an
  infrastructure failure.
* **The "layout-reachable budget is spent" conclusion of round 3 was wrong** —
  by 0.070°, which is 28 % of the miss it was written about. It was not wrong in
  its per-knob arithmetic; it was wrong because hand analysis prices one knob at
  a time and the win came from 17 of them moving together.
* `vdd`, `voutp` and `voutn` **grew** 2.7–3.3 fF as pitches tightened. Harmless
  here (≤ 0.51× of nominal budget, pair asymmetry 21.06 → 21.69 fF against a
  905 fF allowance) but it is the direction an area campaign pushes, and the
  next one should carry those nets as constraints rather than trust the margin.
* HD2 drew −102.72 dB against round 3's −97.17 with nothing physical changed on
  the output nets. Same ±3 dB bench floor round 3 characterised; **not** a
  layout property.

**Next Steps**

1. `layout-reviewer` re-review of round 4. Specifically: is trading the F7
   matching debt for 5.6 % of area the right call for this block, and does §7's
   endpoint failure change the confidence in the knob envelope?
2. **Fix the three `BOUNDS` ranges** (round-5 generator change, needs its own
   build → DRC → LVS → PEX round): narrow `w_m1` (~0.4 ceiling), `ring_gap`
   (~10) and `w_tm1` (~3.0), or teach `clamp()` to resolve them the way it now
   resolves `cc12_cols`. Then re-run the 66-endpoint sweep **with LVS** as the
   standing gate.
3. **The `cap_bcs`/`iref ×0.9` corner remains design-lane**, now 0.179° short.
   Candidates in the block owner's order: an `iref` trim, a small `C1`/`C2`
   re-allocation, a shorter `L` on `xm4` (45 µm), fewer `xm9` fingers.
4. **A second campaign with a different objective** — the first minimised area
   only. `ph_max` at the failing corner as the objective, with area as a
   constraint at 228 094 µm², is the obvious next question, and the harness for
   it already exists (`opt/project_setup.yaml`).
5. Platform gaps this cell has now exposed four times: `tech_json=` (or a
   MIM-aware tech) for `signoff.run_pex` (F11), a `Cj(area, perimeter, Vbias)`
   term in `signoff.postlayout` (F3), a pin-list assertion in `signoff.lvs`
   (F13), a **mirror-and-swap symmetry** primitive and a **sorted-card-set PEX
   comparator** in `spicexplorer-layout`. New this round: **`layout.gen` should
   ship the endpoint sweep as a runner** (build → DRC → LVS per endpoint, with a
   worker cap that does not fake failures), because every cell will need it and
   this one wrote it three times in scratch. Nit, unchanged:
   `iterations_table_md` does not escape `|` inside a note, so it03's `3|1|3`
   still breaks that one row of §10.
6. `xr2_split` (PLAN R2.8 Q4) would take the Metal1 exception from 23.556 to
   16.0 µm² and close F19 geometrically rather than by attribution.
7. Chip-level antenna check (F12) and the block owner's acknowledgement of the
   MIM area flag (**F15, now 53.6 % of a smaller cell**) before a second
   instance is placed.
