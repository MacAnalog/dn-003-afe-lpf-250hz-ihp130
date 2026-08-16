# Layout plan — `H12-pdk-cap` (`lpf_core`)

This file holds **two versions**. The **Round 2** section below is the approved
delta (human sign-off 2026-08-16); the **v1** plan that follows it was approved
on 2026-08-15 and is reproduced **unchanged** — where the two disagree, the
round-2 section says so explicitly and names the finding that forced it.

---

# Round 2 (2026-08-16) — changes vs the approved v1

> **STATUS: APPROVED 2026-08-16 (human sign-off), as written.** R2.8 decisions:
> **Q1 yes** (take the anti-oriented split, `cap_anti_orient=True`, `cc12` 3|1|3);
> **Q2 yes** (`bias_dummy_rows=1`, the ~0.06° is accepted) — **REVERSED to `0` by
> the block owner on 2026-08-16 for round 4, see the note under R2.8 Q2**; **Q3 yes** (if
> `cap_bcs`/`iref×0.9` still misses S1 after every lever, deliver with the corner
> row reported, not hidden — corners are nice-to-have for this block); **Q4 yes**
> (`xr2` split deferred). Build proceeds under R2.9's iteration protocol.
> The v1 plan (everything from *"Layout plan — `H12-pdk-cap`"* onward) **stands
> as approved**; this section is the *delta* only. It exists because the
> independent review of the round-1 layout
> ([`REVIEW.md`](REVIEW.md) / [`REVIEW.yaml`](REVIEW.yaml), 2026-08-15) returned
> **FAIL** on one measured fact — S1 `ph_max` = **329.299° < 330°** at
> `cap_bcs` with `iref ×0.9`, a corner the pre-layout sign-off certified as
> **PASS** (331.021°) — plus two structural findings (F2/F5, F3) and eleven
> smaller ones. Every number quoted below is the reviewer's measurement, not a
> re-derivation. **No generator line is written until this section is approved.**
>
> What does **not** change: the two-island floorplan (biquad A / biquad B
> separated by a grounded band, `net2`/`net3` never leaving island A — the
> A↔B coupling measured **0.0000 fF** against a 0.28 fF budget and that
> property is preserved by construction in every change below), the `xc1`/`xc10`
> plate flip, the pin sides, the device/matching table of v1 §2, v1 §6
> ("what this layout will NOT do"), and the rule that W/L/ng/m come from
> `design.json` and are never knobs.

## R2.0 — what round 2 is trying to buy

| | pre-layout | round 1 (measured) | round-2 target |
|---|---|---|---|
| `ph_max` nominal | 332.382° | 330.732° | **≥ 331.3°** |
| `ph_max` @ `cap_bcs`, `iref ×0.9` | 331.021° **PASS** | **329.299° FAIL** | **≥ 330.0° PASS** (reported either way) |
| C(`net2`) / C(`net3`) to ac gnd | — | 50.04 / 44.94 fF | **≤ 22.8 fF each** (nominal budget); stretch ≤ 19.6 fF (bare corner pass), goal ≤ 9.6 fF (pvt budget) |
| Δ(`net2`,`net3`) | — | 5.10 fF | **< 0.5 fF** |
| C(`net4`) / C(`net1`) | — | 77.30 / 67.27 fF | ≤ 82.8 fF each, Δ < 1 fF |
| Δ(`voutp`,`voutn`) | — | 152.95 fF | **< 25 fF** (both under the 455 fF pvt budget) |

The whole round is a **capacitance-reduction round on two nets**. The
reviewer's validated slope is **−0.0261 °/fF on `net2`+`net3`** and
**−0.00719 °/fF on `net4`+`net1`** (good to ~10 %, F1/F2 evidence), so
`ph_max` is a linear function of two numbers and every change below is priced
in fF first, degrees second.

## R2.1 — findings addressed → generator change → knob → expected magnitude

| # (sev) | finding | generator change | knob (new / changed) — default, range | expected magnitude (reviewer-measured unless marked) |
|---|---|---|---|---|
| **F1** (blocker) | S1 fails at `cap_bcs`/`iref ×0.9` (329.299°) | the sum of F2 + F5 + F6 + the residual levers R2.6 | — (composite) | **+0.55…+0.70°** from F2/F5/F6 alone ⇒ 329.85…330.00 (knife-edge); + **0.18…0.31°** from the R2.6 residual levers (hand, priced in fF) ⇒ **330.0…330.3 PASS** |
| **F5** (major) | `xc13`/`xc17` outboard, `xc19` on the axis — hard-coded, no knob reaches it | bank A re-ordered: `xc13`/`xc17` **adjacent to the axis**, `xc19` **split into two mirror-symmetric 4-unit halves** outboard; the split is what keeps the MIM mirror-XOR at 0 | **`bankA_order`** — `"c13_axis"` (new default), `{"c19_axis"` = v1 `, "c13_axis"}`; **`cap_axis_gap`** — 5.0 µm, 3.0–20.0 (axis → inner edge of the axis-adjacent sub-array) | `net2` TopMetal1 haul **170.5 µm → ≈20 µm** ⇒ **−13 fF ⇒ +0.34°** (reviewer's number for a ~60 µm haul; the inner-edge spine of F6 makes it ~20 µm, so this is a floor, not a ceiling) |
| **F2** (major) | `net2`/`net3` 2.19×/1.97× over the balanced budget, 5.22×/4.69× over pvt | `xc13`/`xc17` drawn 1 column × 2 rows | **`cc13_cols`** — **2 → 1**, range 1–2 | `net2` 50.04 → **42.52 fF**, `net3` → 42.11, `ph_max` 330.732 → **330.872** ⇒ **+0.14°** (free: identical area, DRC 0) |
| **F6** (major) | MIM top-plate spine always on the array's **left** column ⇒ mirrored arrays are not mirror images (Metal3 XOR 126.35 µm², TopMetal1 847.05 µm²) | `cap_array()` takes the half sign: spine at `x0+side/2` on the left half, `x1−side/2` on the right — i.e. always the **inner** column, which also shortens both hauls | **`cap_spine_side`** — `"mirror"` (new default), `{"left"` = v1 `, "mirror", "inner", "outer"}` | Δ(`net2`,`net3`) **5.10 → < 0.5 fF**, `net2` **−5 fF ⇒ +0.13°**; `net4` Metal3 haul 184.4 → ~30 µm, Δ(`net4`,`net1`) 10.04 → **< 1 fF**, `net4` −10 fF ⇒ **+0.07°** |
| **F8** (minor) | single-orientation `xc19`/`xc12` plates cost **14.2 dB of HD2** and put `voutp` 1.11× over its pvt budget | anti-oriented plate assignment: `xc19` = 4+4 (one half bottom = `vout_1`, the other bottom = `vout_2`), `xc12` = **3 \| 1 \| 3** (geometry stays mirror-symmetric, only the on-axis unit picks a side) | **`cap_anti_orient`** — `True` (new default), `{True, False}`; **`cc12_split`** — `"3|1|3"` (new default), `{"none", "3|1|3"}` | HD2 −88.06 → **≈ −102 dB**; Δ(`vout_1`,`vout_2`) 155.80 → ≈ 0; Δ(`voutp`,`voutn`) 152.95 → **≈ 22 fF** (one residual unit), both halves ≈ 430 fF, **under the 455 fF pvt budget** (today `voutp` = 505.5 is over it) |
| **F7** (major) | bias common-centroid array has dummy **columns** but no dummy **rows**; `xr3` owns both edge rows, `xm9`/`xm10` the interior row | one dummy row above and below the 3-row array (5 rows drawn, 3 live), same S/G routing, tied to `vss` | **`bias_dummy_rows`** — **1** (new), 0–1 (0–2 once the F4 dummy DRC root cause is fixed) | every array member gets a dummy on four sides; removes the 1.2 Hz-of-`fc` edge/interior exposure (hand bound) against a 3.27 Hz margin. **Cost:** island A grows ~20 µm ⇒ `net2` spine +20 µm ⇒ **+2.3 fF ⇒ −0.06°** — priced and accepted (see R2.8 Q2) |
| **F14** (note) | `xr1` is a single un-mirrored instance while `xm14`/`xm15` are 1+1 — the replica ratio carries an orientation term | `xr1` drawn as **two anti-oriented half-instances** (`nf=1` each, same row, same well); KLayout's MOS class sums parallel W, so LVS still sees `W=12u` (the `xr3`→`W=96u` fold proves the mechanism) | **`xr1_split`** — `True` (new), `{True, False}` | orientation term of the `rep_gmfb` ratio cancelled (0.8 Hz/mV exposure, hand). **`xr2` is deferred** — see R2.7 |
| **F9** (minor) | `tap_len` is referenced 0 times; both endpoints build byte-identical | field deleted from `LayoutParams` **and** `BOUNDS` | **`tap_len`** — **removed** | every `LayoutParams` field changes the GDS (asserted by the R2.5 sweep) |
| **F10** (minor) | `BOUNDS` silently narrows `w_m1`/`w_m2` vs approved PLAN §5 | none — the **generator is right** (`M1.a = 0.16`, `Mn.a = 0.20`); **PLAN §5 is amended here** and `BOUNDS` becomes the single source of truth, re-printed in REPORT §7 with a PLAN-vs-BOUNDS equality assertion in the generator's self-test | `w_m1` — 0.20, **0.16**–1.0; `w_m2` — 0.20, **0.20**–1.0 (PLAN §5 corrected) | PLAN §5 and `BOUNDS` agree field by field, mechanically |
| **F4** (major) | 13 of 48 `BOUNDS` endpoints are DRC-dirty (REPORT §7 claimed none could be) | see R2.5 — measured ranges + a `clamp()`/`validate()` in `build()` + an endpoint sweep in the generator's own test | **`BOUNDS`** (all rows) | **2N/2N endpoints DRC-clean**, re-measured by the same sweep the reviewer ran (35/48 today) |
| **F3** (major) | n-well↔substrate junction C is in neither kpex nor the PSP model (16–39 fF/half on `net4`/`net1`) | **not modelled in the netlist this round** (deferred, R2.7) — but the round-2 REPORT carries an explicit *known-unmodelled* row: the well areas from the built GDS × 0.05–0.12 fF/µm², plus a **what-if** run with those lumped `Cj` values added to a copy of the PEX netlist | — | the estimate lands on the scorecard as a line item (−0.12…−0.28° of `ph_max`), never absent from it |

**Where the fixes overlap.** F5 (short haul) subsumes part of F2 and F6 — the
three cannot simply be added. The honest composite, in fF on `net2`: haul
19.8 → 2.3 (−17.5), `vbn`-bus overlap under the haul 5.9 → ~2 (−4), spine/comb
re-shape (−1…−3), `vinp` proximity (−0.5). Net: **50.0 → ≈27 fF**, i.e.
**+0.60°**, landing `cap_bcs` at **≈ 329.9°** — *still short*. That is why
R2.6 exists and why the acceptance target is measured, not assumed.

## R2.2 — bank A floorplan (updated sketch)

`bankA_order = "c13_axis"`, `cc13_cols = 1`, `cc19_cols = 2` **per half**,
`cap_anti_orient = True`, `cap_spine_side = "mirror"`. Everything above bank A
(island A, the shield band, island B, bank B) keeps its v1 arrangement and
`y`-order; only bank A's internal order and the two spine sides change.

```
                                   x = 0  (symmetry axis)
                                     |
  <---------------------------- bank A (bottom) ---------------------------->
  +----------------+  +--------+     |     +--------+  +----------------+
  |   xc19-L 2x2   |  | xc13   |     |     |  xc17  |  |   xc19-R 2x2   |
  |   4 units      |  | 1 x 2  |     |     |  1 x 2 |  |   4 units      |
  |  M5(bot)=vout_1|  | TM1(top)     |     | TM1(top)  |  M5(bot)=vout_2 |   <-- anti-
  |  TM1(top)=vout_2| |   = net2|    |     | = net3 |  |  TM1(top)=vout_1|       oriented
  |                |  | M5=vout_1    |     | M5=vout_2 |                |       (F8)
  +----------------+  +--------+     |     +--------+  +----------------+
        ^                     ^ spine|spine ^                    ^
        |                     |  (inner edge, F6)                |
   spine on the inner edge    |     |     |                 spine inner
   (F6 mirror rule)           |     |     |
                              |<-5->|<-5->|   cap_axis_gap = 5.0 um / half
                     x=-25.9 -+     |     +- x=+25.9   (TM1 spine centre)

  net2 haul:  spine x=-25.9  ->  island-A drop x=-6      =  ~20 um   (was 170.5)
  net3 haul:  mirror image                               =  ~20 um   (was 128.4)
```

* **`xc13`/`xc17` on the axis** is the F5 fix: their top plates are the
  `net2`/`net3` terminals and the island-A drop points are at x = ∓6, so the
  axis is where they belong. `xc19` (both plates on the `vout_1`/`vout_2`
  don't-cares, 3350 fF budget) absorbs the length instead.
* **`xc19` must split to keep symmetry**: one 8-unit array cannot sit on both
  sides of the axis, and putting it wholly on one side would break the
  MIM mirror-XOR = 0 property the reviewer verified. 4+4 mirrored halves keep
  it *and* deliver the F8 anti-orientation for free.
* **Bank A gets narrower** (≈ 317 µm vs 396 µm): the cell outline stays set by
  bank B (`xc1`/`xc10`), so the expected outline is ≈ **432 × 535 µm**
  (+20 µm of height from `bias_dummy_rows`), area ≈ 0.231 mm² — within 1 % of
  round 1. **No area is bought or spent by this round.**
* The `vout_1`/`vout_2` bottom-plate straps now cross the axis region under the
  `net2`/`net3` spines on Metal5/Metal3. Both are don't-cares; the crossing is
  orthogonal, on a different layer, and is *intra*-biquad-A — the A↔B
  keep-apart assertion (`_assert_keep_apart`) is unchanged and still runs at
  build time.

## R2.3 — the spine-per-half mirror rule (F6)

Today `cap_array()` computes `x_spine = x0 + side/2` for **every** array, so on
the right half the spine sits on the *far* side of the array and the haul is
drawn back across it. The rule for round 2, stated so the reviewer can check it
mechanically:

> **Every MIM sub-array's TopMetal1 top-plate spine is placed on the column
> nearest the symmetry axis** — `x1 − side/2` for an array whose centre is at
> x < 0, `x0 + side/2` for one at x > 0, and (for an on-axis array) on the side
> its net's drop point is on, chosen by the half sign, never by array-local
> coordinates. The same rule governs the Metal3/Metal5 bottom-plate exit of
> every array.

Consequences the reviewer already measured and can re-measure: the mirror-XOR
of **Metal3, TopMetal1 and Metal5** about x = 0 must fall to ≈ 0 (from 126.35 /
847.05 / 948.78 µm²); the nine physical layers that already XOR to exactly 0
must stay at 0. The generator gains a **build-time assertion**: for every
routing layer, `XOR(shapes, mirror_x(shapes)) ≤ 5 µm²`, failing the build
otherwise — so this class of defect cannot come back silently. (The `vbp` pad,
8.0 µm² of Metal1, is the one declared exception, brief §9.)

## R2.4 — bias dummy rows (F7) and the replica orientation (F14) — both in this round

* **`bias_dummy_rows = 1` — yes, this round.** The `rep_sink` ratio is the
  tightest matching class in the cell (0.346 mV nominal / 0.178 mV pvt) and it
  is the only class whose failure moves `fc`, where the post-layout margin is
  3.27 Hz. It costs ~20 µm of island-A height ⇒ ~2.3 fF on `net2` ⇒ −0.06° of
  the very margin this round is fighting for, which is why it is called out as
  a decision (R2.8 Q2) rather than done silently. **Blocked on F4**: the same
  dummy-placement code produces 330 DRC violations at `bias_dummy_cols = 2`
  (Cnt.j 278, pSD.i 24, Cnt.f 12, Cnt.d 10, Gat.f 6), so the root cause is
  fixed *first*, then the row dummies are added on the fixed code. `BOUNDS` for
  `bias_dummy_rows` stays 0–1 until that DRC root cause is understood.
* **`xr1_split = True` — yes, this round.** Two anti-oriented `nf=1` halves in
  the same row and the same `vdd` well; LVS unchanged (parallel-W fold), no
  area, no new well.
* **`xr2` (bridge replica) — deferred**, see R2.7.

## R2.5 — `BOUNDS` reconciliation (F4), dead knob (F9), PLAN drift (F10)

The reviewer built and DRC'd all 24 knobs at both endpoints; **13 endpoints are
dirty**. Round 2 does three things, in this order:

1. **Fix the root causes that are real bugs** rather than tightening around
   them: the dummy-device generator (`bias_dummy_cols = 2` → 330 violations;
   `gmfb_dummy = 2` → 80) and the guard-ring generator (`ring_w = 3.0` → 132)
   are producing illegal contact/pSD geometry, not "the knob is too big".
2. **Declare the measured legal range** for the knobs whose endpoint is a
   genuine geometric floor/ceiling. Provisional values below — *each is
   re-measured by the sweep in step 3 and the table in REPORT §7 carries the
   measured value, not this guess*:

| knob | v1 range | round-2 proposal | why |
|---|---|---|---|
| `dev_gap_x` | 1.0 – 6.0 | **1.6** – 6.0 (or keep 1.0 with the pmos-pitch clamp extended to every row) | TGO.e at ±79.71, 148.22 (6 hits) |
| `axis_gap` | 2.0 – 30.0 | **3.0** – 30.0 | M1.b (2 hits) |
| `row_gap` | 3.0 – 20.0 | **4.0** – 20.0 | 12 hits |
| `bank_gap` | 6.0 – 60.0 | **8.0** – 60.0 | 13 hits |
| `cap_bank_gap` | 4.0 – 40.0 | **5.0** – 40.0 | TM1.b (2 hits) |
| `ring_gap` | 2.0 – 15.0 | 2.0 – **12.0** | TM1.b (1 hit) |
| `ring_w` | 0.6 – 3.0 | 0.6 – **1.5** *after* the generator fix; 0.6 – 3.0 if the fix holds | Gat.c 48, Cnt.c 36, Cnt.j 36, pSD.i 12 |
| `bias_dummy_cols` | 0 – 2 | **0 – 1** until the dummy generator is fixed | 330 hits |
| `gmfb_dummy` | 0 – 2 | **0 – 1** until the dummy generator is fixed | 80 hits |
| `w_m2` | 0.20 – 1.0 | 0.20 – **0.60** | M2.b (12 hits) |
| `via_pad` | 1.7 – 4.0 | 1.7 – **3.0** | TM1.b (2 hits) |
| `cc1_cols` | 1 – 16 | **2 – 8** | CntB.a1, and the cell grows to x = ±834 µm at 16 |
| `cc19_cols` | 1 – 8 | **1 – 2** (now *per 4-unit half*: 1×4 or 2×2) | V2.b at 1 col; the semantics change with the split |
| `cc13_cols` | 1 – 2 | 1 – 2 (default **1**) | clean at both ends |
| `w_m1` | PLAN 0.14 / gen 0.16 | **0.16** – 1.0 (PLAN §5 corrected, F10) | M1.a = 0.16 |
| `tap_len` | 1.0 – 20.0 | **removed** (F9) | referenced 0 times |

3. **Make it mechanical, not a promise.** `build()` gains
   `validate(params, strict=True)` which raises on an out-of-`BOUNDS` or
   known-illegal combination (the pmos-pitch clamp generalised), the generator
   ships a test that asserts `set(BOUNDS) == set(LayoutParams fields)` and that
   the PLAN's table equals `BOUNDS`, and the **2N-endpoint build+DRC sweep is
   run as part of the round-2 gate** (it is ~1 min/build; the reviewer's 48
   builds are the precedent). REPORT §7 prints the sweep result, not a claim.

## R2.6 — the residual `net2`/`net3` levers (why F2/F5/F6 alone are not enough)

The three structural fixes land `cap_bcs` at ≈ 329.9°, ~0.1° short, and the
unmodelled F3 well term would eat more. Round 1's own PEX netlist says where
the rest of `net2`'s 50 fF is (kpex `ihp` substrate table: Metal1 35.0 aF/µm² +
39.6 aF/µm, Metal2 18.2 + 34.8, Metal5 7.1 + 27.5, TopMetal1 5.6 + 37.4 — the
**perimeter** term dominates every layer, so *length and layer count*, not
width, are the levers):

| residual term | round 1 | lever (knob) | expected |
|---|---|---|---|
| `net2` Metal1 straps — 33.5 µm², **perimeter 240 µm** | ≈ 10 fF | **`net23_strap = "min_m1"`** (new; default on): drop from the drain contact to the spine layer at the device, no Metal1 run longer than the contact row | **−3…−5 fF** (hand, from the aF/µm table) |
| `net2` Metal2 vertical spine, 67 µm | ≈ 5 fF | **`net23_spine_layer`** — `"Metal5"` (new default), `{"Metal2"` = v1 `, "Metal3", "Metal5", "TopMetal1"}`; Metal5 min-width is 56.5 aF/µm vs Metal2's 73.2 | **−1…−2 fF** |
| C(`net2`,`vbn`) = 5.93 fF — the `vbn` Metal3 bus runs the full cell width (x −212…+212) under the `net2` corridor | ≈ 5.9 fF | **`vbn_bus_keepout`** (new, 0 = off / µm value): route the `vbn` M3 bus around the `net2`/`net3` corridor instead of under it | **−2…−4 fF** (the short haul removes most of it already) |
| C(`net2`,`vinp`) = 1.64 fF — `vinp` runs beside the `net2` spine into `xm2`'s gate | ≈ 1.6 fF | placement: `vinp` enters on the far side of the in_a row (no new knob) | **−0.5…−1 fF** |

Total residual **−7…−12 fF per half ⇒ +0.18…+0.31°**. Levers are applied
**in the order above, measuring after each** (that is what the iteration trail
in R2.9 is for); the round stops as soon as the acceptance targets in R2.10 are
met, so the cheapest sufficient set is what ships.

## R2.7 — findings deliberately deferred, and why

| # | finding | why it is not fixed in round 2 | what would fix it |
|---|---|---|---|
| **F3** | n-well↔substrate junction C absent from both kpex and the PSP cards (16–39 fF/half on `net4`/`net1`) | it is a **measurement-model gap, not a layout defect**: the wells are already at the NW.c minimum enclosure (`well_margin = 0.62`) and identical shapes, so the layout has no lever left. Fixing it properly means adding a `Cj` model to the post-layout splice — that is `spicexplorer-signoff` work, and doing it mid-round would change the yardstick under the comparison | a `Cj(area, perimeter, Vbias)` term in `signoff.postlayout` (platform PR), or a smaller `xmst`/`xmstn`. **Round 2 still reports it**: measured well areas × 0.05–0.12 fF/µm² as a line item, plus a lumped-`Cj` what-if on a copy of the PEX netlist so the exposure is a number on the scorecard |
| **F11** | kpex cannot extract MIM top plates (`cmim_top` = `"<TODO>"` in its IHP tech) — up to +15 fF on `net2`/`net3` unbounded | patching the kpex tech is platform/tool work with its own validation (the omission must be *closed*, not re-estimated); round 2's comparison stays consistent because pre- and post-layout both use the stripped flow | a MIM-aware kpex tech or `tech_json=` on `run_pex` (platform). Round-2 REPORT repeats the ≤15 fF bound and marks it open |
| **F12** | antenna ratio ≈ 53:1 on the `net2`/`net3` gate lines; the IHP KLayout deck ships no antenna table | the ratio is dominated by the **MIM top plate itself** (3 285 µm² of the 3 588 µm²), which the re-order does not shrink; the brief forbids a diode (6.17 pA leakage); a lower-metal break in the gate line costs `net2` capacitance — exactly what this round is buying back | a chip-level antenna check, or a jumper once the phase margin is banked. Round-2 REPORT re-states the number for the new geometry |
| **F13** | `run_lvs` does not assert the extracted pin set against the certified header (`vbp` is unchecked) | one-line assertion in `spicexplorer-signoff`, not in this cell's generator; it changes a shared verdict object and belongs in its own platform PR | `signoff.lvs` pin-list assertion (platform). Opportunistic — landed if the round has slack, otherwise carried |
| **F15** | MIM occupies 53 % of the cell / 70 % of the PDK's per-chip recommendation | **block-level**: total C is set by `design.json`; the layout cannot shrink it | the block owner's call before a second instance is placed. Round 2 changes total MIM area by **0** |

## R2.8 — decisions the human must make

1. **Q1 — the F8 anti-oriented split: take it (recommended).** v1 §8.3 rejected
   it on a one-sided-C argument ("benefit ≈ 0"); the reviewer's what-if
   contradicts that with a measurement — **14.2 dB of HD2** — and, more
   importantly for this round, the single-orientation `xc12` plates are what
   put `voutp` at 505.5 fF, **1.11× over its 455 fF pvt budget** while `voutn`
   sits at 352.5. Balancing them is a *budget* fix, not only a linearity fix.
   THD is unchanged (−49.614, HD3-dominated, S7 keeps 9.6 dB), so this buys
   robustness and budget headroom, not a spec line. Cost: `xc19`/`xc12` each
   become two LVS cards (the generator already emits swapped-terminal cards for
   `xc1`/`xc10`), one residual un-paired `xc12` unit (Δ ≈ 22 fF). It does not
   shrink total capacitance — the owner's "reduce cap sizes" ask cannot be met
   by layout — but it stops ~150 fF of avoidable one-sided load, which is the
   layout-side reading of "do not waste parasitic budget".
2. **Q2 — `bias_dummy_rows = 1` costs ~0.06° of the S1 margin this round is
   fighting for.** Recommended **yes** (matching debt is harder to pay later
   than 2.3 fF), but it is the human's call: `bias_dummy_rows = 0` is a legal
   knob value and the exposure (1.2 Hz of `fc` against a 3.27 Hz margin) is a
   hand bound, not a measurement.

   > **REVERSED 2026-08-16 (block owner), round 4: `bias_dummy_rows = 0`.**
   > The Q2 decision was taken on a *hand bound*; the area campaign
   > (`opt/results/README.md`, 300+300 trials + two single evaluations) then
   > measured the other side of it: the dummy rows cost **13 791 µm² — 5.6 % of
   > the cell — plus 0.05° of `ph_max` and 2.1 fF on `net2`/`net3`**, against a
   > matching benefit that is still a hand bound and still unmeasured (no bench
   > in this campaign models edge/interior ΔV_T). The owner's call is that 5.6 %
   > of area and 0.07° at the failing corner is the wrong price for it. Taken
   > together with the campaign's A-best numeric knob point, round 4's defaults
   > give **228 093.6 µm² (−7.7 % vs round 3), `ph_max` 331.221 nominal
   > (+0.061) and 329.821 at `cap_bcs` ×0.9 / `iref ×0.9` (+0.070)**, DRC 0,
   > LVS matched — i.e. the reversal is free on every measured axis. F7's
   > exposure is re-opened as a **documented, unmeasured** matching debt on the
   > bias common-centroid array's outer rows; `bias_dummy_rows = 1` remains a
   > legal knob value (BOUNDS 0–1) and one build away. R2.8 Q1, Q3 and Q4 are
   > unchanged.
3. **Q3 — what if `cap_bcs`/`iref ×0.9` still misses after all levers?** The
   plan's rule is **report, never hide**: the corner row goes in REPORT §5 with
   its measured value and the attribution. The block owner has said corners are
   nice-to-have, not must — so the proposed default is *deliver with the miss
   documented*, and the follow-ups (an `iref` trim, a small `C1`/`C2`
   re-allocation, or the F3 model) are **design-lane** work, not layout. Confirm.
4. **Q4 — `xr2` orientation (F14) deferred**: splitting the bridge replica into
   two anti-oriented halves would double its n-well count and add well junction
   area on `net4`/`rep_x`/`net1` — the exact term F3 says is already
   unaccounted. Recommended defer; say so if you disagree.

## R2.9 — iteration protocol for step 3 (mechanical, no exceptions)

Every build → DRC (→ LVS → PEX) round, **including builds that throw**, is
recorded before the generator is touched again:

* `spicexplorer_layout.iterations.snapshot(layout/H12-pdk-cap/iterations, note=…,
  gen_path=…, gds=…, params=…, drc=…, lvs=…, pex=…, scorecard=…,
  keep_gds=False)` — `keep_gds=False` because this repo does not ignore GDS and
  PLAN §6 keeps build products out of git; the build-dir GDS is retained for
  the diff. The `note` is one line: *what changed and what it fixed / broke*.
* `diff_png(iter_dir, "it<N-1>", "it<N>")` after every snapshot — before | after,
  changed regions boxed, previous DRC hits marked fixed / still / new.
* **`it01` = the round-1 layout of record**, rebuilt from the committed
  `gen_H12_pdk_cap.py` at default `LayoutParams` **before any edit**, with its
  DRC/LVS/PEX verdicts and the round-1 scorecard attached. Its GDS sha256 must
  be `e5cfa1daad8818248f2695ac22b18d633d7723edd71cd2f4f0d76bc888786a9c`; if the
  rebuild does not reproduce that sha, the round stops and the discrepancy is
  reported before anything else is changed.
* REPORT §*Iterations* is generated by
  `iterations_table_md(layout/H12-pdk-cap/iterations)` — never typed by hand.
  A round missing from the table did not happen.
* Committed from `iterations/`: `iterations.yaml`, `it*/gen.py`, `it*/layout.png`,
  `diff_it*_it*.png`. Not committed: any GDS, PEX netlist copies, run dirs.

Scratch for this round lives outside the repo
(`/home/noorizad/.claude/jobs/fca5caa6/tmp/round2/`); `runs/` and build products
are never committed.

## R2.10 — round-2 acceptance targets (the gate for step 5)

| # | target | how it is measured |
|---|---|---|
| A1 | **DRC 0**, no waivers | PDK KLayout deck via `signoff.drc` (35 tables + `sg13g2_maximal`, `--no_density`) |
| A2 | **LVS matched** against `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp` (sha `ef78d6f8…af3c7`) via the generator-emitted `core_lvs.sp`, whose diff vs `to_lvs_reference(core.sp)` is **only** the declared mechanical edits (now: `0`→`vss`+pin, `xc1`/`xc10` swap, **`xc19`/`xc12` anti-oriented splits**, dummy cards incl. the new dummy rows) | `signoff.lvs` + a regenerate-and-diff step in REPORT |
| A3 | **deterministic**: same params → identical sha256, two independent builds | REPORT §1 |
| A4 | **C(`net2`), C(`net3`) ≤ 22.8 fF** each (nominal balanced budget); **Δ < 0.5 fF**. Stretch: ≤ 19.6 fF (the reviewer's bare-corner-pass number); goal ≤ 9.6 fF (pvt budget) | kpex CC, C to the bench ac grounds (`0`, `vdd`, `vbn`, `vbr`, `rep_x`, `vinp`, `vinn`) — the reviewer's exact definition |
| A5 | **C(`net4`), C(`net1`) ≤ 82.8 fF**, Δ < 1 fF; **C(`voutp`), C(`voutn`) ≤ 455 fF** (pvt), Δ < 25 fF; **C(A↔B) = 0.000 fF** (unchanged) | same |
| A6 | **nominal `ph_max` ≥ 331.3°** (round 1: 330.732), with every other S-line no worse than round 1 beyond the campaign noise floor: `fc` 248.275 Hz, `a1000` −49.263 dB, ripple 0.0232, peak 0.0206, dc −0.0081, IRN 29.195 µVrms, P 11.913 nW, THD −49.614 dB, HD2 → **≈ −102 dB** (F8) | `lab.metrics.evaluate` on `asbuilt/core_pex.sp`, frozen benches, same definitions as `scorecard.json` |
| A7 | **corners on the PEX netlist**: the 9-point `lab.corners.AXES` set (both DUTs, `LPF_BIAS_ALPHA=1.1`; *as run in round 4: α = 0, see REPORT §5*) **plus the five `cornerCAP.lib` points**, including **`cap_bcs` (×0.9) with `iref ×0.9`** — the corner that failed. Target **≥ 330.0°**; a miss is a reported row with its attribution, never omitted or re-defined | `LPF_CAP_CORNER=…` + `Design.iref` scaling, `lab.corners` |
| A8 | **PEX CC for every iteration; CC *and* RC side by side for the final report** | `signoff.pex` (policy: `doc/layout-lane.md`) |
| A9 | **every `BOUNDS` endpoint DRC-clean** (2N/2N) and every `LayoutParams` field provably changes the GDS | the endpoint sweep of R2.5, printed in REPORT §7 |
| A10 | **mirror-XOR ≈ 0 on the routing layers** (Metal1/2/3/5, TopMetal1 ≤ 5 µm² each, `vbp` pad excepted) and still exactly 0 on the nine physical layers | build-time assertion + REPORT table |
| A11 | **known-unmodelled terms stated**: F3 well-junction estimate + lumped-`Cj` what-if, F11 ≤ 15 fF MIM bound, F12 antenna ratio | REPORT §*known-unmodelled* |

A round-2 layout that meets A1–A6 and A8–A11 but misses A7 is **delivered with
the miss on the front page** (R2.8 Q3), not quietly re-scoped.

---
---

# v1 — approved 2026-08-15, reproduced unchanged

# Layout plan — `H12-pdk-cap` (`lpf_core`)

> **STATUS: APPROVED 2026-08-15 (human sign-off) — built as planned.** All §8
> decisions and the §3 pin sides stand as written; the generator, DRC/LVS/PEX and
> the post-layout scorecard implement exactly this plan. (Historical note: the
> human approver was not live when this plan was first written, so the flow
> proceeded past the gate on the launching agent's instruction; the sign-off
> arrived on 2026-08-15 and approved the plan unchanged.) Everything downstream (generator, DRC/LVS/PEX, post-layout
> scorecard) is built on the decisions below; **if this plan is rejected, the
> generator must be re-run with the changed knobs / re-written for the changed
> floorplan and the whole signoff chain repeated** — nothing here is hand-drawn,
> so a rejection costs a rebuild, not a redraw. The three decisions most likely
> to be contested, and what a rejection changes, are listed in §8.

| | |
|---|---|
| cell of record | `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp` (`.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd`) |
| `netlist_sha` | `ef78d6f8d4e28cfbf18dc7abf6bd4066070fdf9f63546d430f16c4d71ffaf3c7` |
| sizing record | `signoff/post-pvt/H12-pdk-cap/design.json` → `["design"]` (read at build time; **no W/L/m is ever a knob**) |
| brief | `layout/H12-pdk-cap/BRIEF.md` + `brief.json` (measured hand-off) |
| pre-layout yardstick | `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md` §1 + `scorecard.json` |
| PDK | IHP SG13G2, `$PDK_ROOT=/home/noorizad/local/pdks`, gdsfactory + `ihp-gdsfactory` 0.2.7 |
| generator | `layout/H12-pdk-cap/gen_H12_pdk_cap.py`, `CELL = "lpf_core"` |

---

## 1. The one constraint that shapes the floorplan

The brief's §1.1 finding: **any capacitance from a biquad-A internal node
(`net2`/`net3`) to any biquad-B node (`net4`/`net1`/`voutp`/`voutn`) closes a
feedback path around the whole 4th-order filter and costs 1.3–2.2 °/fF of the
S1 phase certificate. Budget 0.28 fF per half** (0.12 fF at the worst passing
corner). Minimum-spacing parallel metal is 0.05–0.1 fF/µm, so the entire budget
is **3–6 µm of parallel run**.

The floorplan answer is topological, not incremental: **biquad A and biquad B
are two physically separate islands, stacked, with a grounded band between
them, and `net2`/`net3` never leave island A.** They do not have to: their only
connections are `xm2`.D, `xm9`.D, `xm4`.G and the `xc13`/`xc17` MIM top plates,
all of which are placed in island A. Only six nets cross the A/B boundary and
every one of them is a don't-care or a rail: `vout_1`, `vout_2` (3353 fF
budget), `vbr` (ac-inert), `vbn` (dc-only), `vdd`, `vss`.

Second hard finding (brief §6): `xc1`/`xc10` as drawn put their Metal5 **bottom**
plates on `net4`/`net1` (83 fF budget) — 207–1395 fF of bottom-plate parasitic,
a 2.5–17× violation before a wire exists. **Both are flipped** (bottom plate on
`voutp`/`voutn`, 905 fF budget) and the terminal order is swapped on those two
cards in the LVS reference. Electrically free; the MIM is a symmetric device.

Third (brief §2.1): the six-unit nmos bias array (`xm9`, `xm10`, `xr3`×4) has a
0.35 mV V_T ratio budget against a random σ of ≈0.2 mV. The layout cannot buy
margin there, only lose it — so the array is a true 2-D common centroid with
dummy columns and identical routing on all six units.

---

## 2. Device table by matching class

Geometry is read from `design.json`; the "drawn as" column is the generator's
finger/instance split, which must reproduce what the netlist declares.

| class (brief §2) | devices | tolerated ΔV_GS common (nom/pvt) | pattern the brief implies | pattern drawn | drawn as |
|---|---|---|---|---|---|
| **`rep_sink` ratio + `bias_a`** | `xr3` (m=4) vs `xm9`, `xm10` | **0.35 / 0.18 mV** | common-centroid + dummies, one 6-unit array | **2-D common centroid, 3 rows × 2 cols + 1 dummy column per side**, identical S/D/G routing on all six, shared vss bar | 6 × hv nmos W=24 L=25 nf=3 (unit); `xr3` = 4 units in parallel (that is what `m=4` means) |
| `rep_gmfb` ratio + `gmf_b` | `xr1` vs `xm14`, `xm15` | 0.84 / 0.79 mV | common-centroid + dummies, shared `vdd` well | **1-D common centroid `D · xm14 · xr1 · xm15 · D`** in ONE `vdd` n-well, 1 hv-pmos dummy per end | 3 × hv pmos W=12 L=31 nf=2 + 2 dummies |
| `rep_bridge` ratio + `bridge` | `xr2` vs `xmst`, `xmstn` | 0.84 / 0.79 mV | same row, same orientation, abutted | **row `xmst · xr2 · xmstn`, same orientation, minimum legal pitch**; three separate n-wells (bodies are `net4`/`net1`/`rep_x`) — *well-level* centroid, no dummies | 3 × hv pmos W=5 L=33 nf=1 |
| `in_b` | `xm0`, `xm1` | 34 / 16 mV | mirrored about the axis; any | mirror pair about x = 0, own wells (`voutp`/`voutn`) | 2 × hv pmos W=4 L=15 nf=1 |
| `gmf_a` | `xm4`, `xm8` | 97 / 46 mV | same row, same orientation | mirror pair, same row | 2 × hv nmos W=1.5 L=45 nf=1 |
| `in_a` | `xm2`, `xm5` | 48 / 23 mV | **any** — orientation match only | mirror pair, same row, own wells (`vout_1`/`vout_2`) | 2 × hv pmos W=16 L=10 nf=2 |

**Why no interdigitation anywhere.** Brief §2.3: `xm2`/`xm5`, `xmst`/`xmstn`,
`xm0`/`xm1` and `xr2` each have their body on their own *signal* net, so the
two members of a pair cannot share an n-well and classical finger
interdigitation is physically illegal. For them "common centroid" means
**well-level** centroid: two wells placed symmetrically about the axis with
matching surroundings. Only the nmos (all bodies = substrate) and
`xm14`/`xm15`/`xr1` (all bodies = `vdd`) may be interleaved — and those are
exactly the two arrays where the budget is tight, which is where the effort
goes.

**Why dummies only on two classes.** Dummy transistors are *not* purged by the
KLayout LVS deck (verified — see §7), so every dummy has to be declared in the
LVS reference. They are spent where the brief says the budget is tight
(`bias` 0.35 mV, `gmf_b` 0.79/0.84 mV) and skipped where it explicitly says not
to gold-plate (`in_a` 48 mV, `gmf_a` 97 mV, `in_b` 34 mV).

### Cap classes (brief §2, §6)

| cap | nets (schematic order = PLUS/top first) | units × MIM side | drawn plate assignment | array |
|---|---|---|---|---|
| `xc13` | `net2` / `vout_1` | 2 × 40.53 µm | top(TM1) = `net2`, bottom(M5) = `vout_1` — **as drawn** | 2 × 1 |
| `xc17` | `net3` / `vout_2` | 2 × 40.53 | mirror of `xc13` | 2 × 1 |
| `xc19` | `vout_2` / `vout_1` | 8 × 49.42 | bottom = `vout_1` (3353 fF budget) | 4 × 2, on axis |
| **`xc1`** | `voutp` / `net4` | 16 × 49.91 | **FLIPPED**: bottom = `voutp`, top = `net4` | 4 × 4 |
| **`xc10`** | `voutn` / `net1` | 16 × 49.91 | **FLIPPED**: bottom = `voutn`, top = `net1` | 4 × 4 |
| `xc12` | `voutn` / `voutp` | 7 × 48.45 | bottom = `voutp` — as drawn | 7 × 1, on axis |

All units of one capacitor keep **one orientation** so the extractor's MIM
combiner folds them into a single `cap_cmim … m=N` device (the deck's
`MIMCAPNDeviceCombiner` sums `m` for units sharing `mim_top`/`mim_btm` and
matching `w`/`l`). The brief's "split 4+3 / 4+4 anti-oriented" suggestion for
`xc12`/`xc19` is **deliberately not taken**: with no metal plane under the
banks the bottom-plate density is 5.2 aF/µm², so the one-sided load is 85–102 fF
against 1800–6710 fF one-sided budgets — 20–70× of margin — and an
anti-oriented split would break the single-device LVS fold for a benefit the
measurement says is worth nothing. Recorded as a deviation from the brief.

---

## 3. Floorplan

Vertical symmetry axis **x = 0**; half-P (`vinp`,`net2`,`vout_1`,`net4`,`voutp`)
on the left, half-N mirrored on the right. Every row is a mirror pair about the
axis, with the replica device (when the class has one) centred on the axis.

```
        <------------------------ ~440 um ------------------------>
  +==========================  vss core guard ring  =================+  ^
  |                                    vdd  (top pin)                |  |
  |  +----------------+ +----------+ +----------------+              |  |
  |  |  xc12  7 x 1   (voutn top / voutp bottom, on axis)            |  |
  |  +---------------------------------------------------+          |  |
  |  |  xc1   4 x 4   |            |  xc10  4 x 4        |   BANK B  |  |
  |  |  M5(bot)=voutp |            |  M5(bot)=voutn      |  (biquad  |  |
  |  |  TM1(top)=net4 |            |  TM1(top)=net1      |   B caps) |  |
  |  +----------------+            +---------------------+          |  |
  |                                                                  |  |
  |   ---- island B (biquad B devices) --------------------------    |  |
  |   D  xm14   xr1   xm15  D      <- gmf_b row, ONE vdd n-well      |  |
  |        xm0        xm1          <- in_b row, wells voutp | voutn  | ~520
  |     xmst   xr2   xmstn         <- bridge row, wells net4|rep_x|net1| um
  |   ----------------------------------------------------------     |  |
  |  ####################  vss shield band + p-tap row  ###########   |  |  <-- A/B boundary
  |   ---- island A (biquad A devices), own vss guard ring -------    |  |
  |        xm2        xm5          <- in_a row, wells vout_1|vout_2  |  |
  |        xm4        xm8          <- gmf_a row (nmos)               |  |
  |   D  [ xr3   xr3 ]  D          <- bias array row 3               |  |
  |   D  [ xm9   xm10]  D          <- bias array row 2  (centre)     |  |
  |   D  [ xr3   xr3 ]  D          <- bias array row 1               |  |
  |   ----------------------------------------------------------     |  |
  |  +----------+ +-------------------+ +----------+                 |  |
  |  | xc13 2x1 | |   xc19   4 x 2    | | xc17 2x1 |      BANK A     |  |
  |  | TM1=net2 | |  M5(bot)=vout_1   | | TM1=net3 |     (biquad     |  |
  |  | M5=vout_1| |  TM1(top)=vout_2  | | M5=vout_2|      A caps)    |  |
  |  +----------+ +-------------------+ +----------+                 |  v
  |            vbn        vbp(isolated)        vss                   |
  +==================================================================+
   vinp/voutp on the left edge          vinn/voutn on the right edge
```

* **`net2`/`net3` live only between bank A and the in_a row** — a vertical
  TopMetal1 spine per half, from the `xc13`/`xc17` top plate up through
  `xm9`.D, `xm4`.G, `xm2`.D. Nothing of biquad B is within ~120 µm of it, at
  any layer.
* **`net4`/`net1`, `voutp`/`voutn` live only between the bridge row and bank B.**
* The two cap banks are on opposite ends of the cell: the `net2`/`net3` plate
  bank (`xc13`/`xc17`) and the `net4`/`net1` plate bank (`xc1`/`xc10`) are
  ~300 µm and one grounded shield apart — the plate-to-plate path the brief
  warns about in §10 is broken by construction.
* **Bias array centroids.** rows/cols: `xr3` occupies (±1 col, row 1) and
  (±1 col, row 3); `xm9`/`xm10` occupy (∓1 col, row 2). Centroid of the four
  `xr3` units = centroid of {`xm9`,`xm10`} = the array centre, in **both**
  axes, and the arrangement is still mirror-symmetric about x = 0 (so `net2`
  and `net3` see identical routing).
* **Wells.** Eight islands, seven at signal potential (brief §5): `vdd`
  (shared by `xm14`/`xm15`/`xr1`/2 dummies — the only shared well), `voutp`,
  `voutn`, `net4`, `net1`, `rep_x`, `vout_1`, `vout_2`. Every island gets its
  own explicit NWell rectangle at **minimum enclosure** (`well_margin`, default
  0.62 µm = NW.c) and its own `ntap1` tied to that well's net; different-net
  wells are kept ≥ `well_gap` (default 2.0 µm ≥ NW.b1 = 1.8). `net4`/`net1`
  wells are drawn at minimum enclosure and to **identical shapes** (brief §5.1:
  their junction cap lands on an 83 fF net).
* **Guard rings.** A `vss` p-tap ring around the whole core, a second `vss`
  p-tap ring around island A (the `net2`/`net3` devices), and the shield band
  between the islands. **No guard ring is tied to any of the seven signal
  wells** (brief §5.4).
* Pins: `vinp` / `voutp` left edge, `vinn` / `voutn` right edge (mirror-
  symmetric), `vdd` top edge, `vbn` bottom edge under the bias array, `vss` on
  the ring, `vbp` an isolated labelled Metal1 pad on the bottom edge (dangling
  port — brief §9; nothing routes to it).

Expected outline ≈ **440 × 520 µm ≈ 0.23 mm²**, aspect ≈ 1.2. MIM area
0.122 mm² (53 % fill) — **flagged**: this one cell uses 70 % of the PDK's
recommended 174 800 µm² total MIM area per chip (brief §6).

---

## 4. Sensitivity → concrete generator constraints

Each row is a brief number turned into something the generator does and the
reviewer can check.

| brief finding | budget | generator constraint |
|---|---|---|
| `net2`↔`voutp` / `net4` / `net1` / `voutn` | **0.28 / 0.12 fF** | island separation: `net2`/`net3` nets exist only below the shield band; **no biquad-B net is routed into island A or bank A on any layer**; asserted at build time by a net-extent check (`_assert_keep_apart`) and re-checked from PEX at step 5 |
| `net2`/`net3` balanced C to gnd | 22.8 / 9.6 fF | long haul on **TopMetal1** (`net_layer["net2"]`), the layer with the smallest C to substrate; minimum via count; no Metal1 run longer than the device pitch; no diffusion or poly routing straps |
| `net2`/`net3` one-sided C | 45.7 / 19.2 fF | half-P and half-N routing are exact mirror images (same layer, same length, same via count) — enforced by generating both halves from one placement function with `mirror=True` |
| `net4`/`net1` balanced C | 82.8 / 34.8 fF | `xc1`/`xc10` **flipped** so the M5 bottom plate is on `voutp`/`voutn`; `xmst`/`xmstn` wells at minimum enclosure, identical shape; `net4`/`net1` routed on TopMetal1 inside island B |
| MIM bottom-plate density 5.2 aF/µm² *only if nothing is underneath* (35 aF/µm² with a Metal4 plane below) | 207 vs 1395 fF | **hard rule: no Metal2/3/4 anywhere under a cap bank**, and Metal1 only for the guard ring outside the bank footprint. Metal4 is not used in the cell at all. |
| `voutp`/`voutn` balanced C | 905 / 455 fF | the flipped M5 plates land 217 fF here (measured at PEX); routing kept off Metal1-over-active |
| leakage `net2`/`net3` | **6.2 / 3.0 pA** | **no antenna diode, no ESD diode, no pad, no extra diffusion or n-well on `net2`/`net3`**; drain areas are the device's own minimum; gate lines jumper to TopMetal1, not to a diode |
| leakage `net4`/`net1` | 60.6 pA | `xmst`/`xmstn` n-wells minimum |
| series R everywhere | ∞ (≥ 15 MΩ before anything moves) | **minimum-width metal on every net including `vdd`**; no EM widening, no redundant-via ceremony, single vias are fine (brief §1.2, §9) |
| current density | max 2.65 nA | ditto |
| `vbr`, `rep_x`, `vbn` ac-inert to 100 pF | ∞ | **no decoupling capacitors** — the brief says they buy nothing; area not spent |
| S5 IRN, S6 power, S7 THD, S3 dc | layout-insensitive | nothing spent |
| `vout_1`/`vout_2` loading *improves* ripple/`a1000`/IRN | 3353 fF | used as the parasitic dump: `xc19`+`xc13` bottom plates, the vertical spines and any shield return land here |
| cross-half coupling raises `ph_max` (safe direction) | — | if a crossing is ever unavoidable it crosses into the **opposite** half; none is needed in this floorplan |

---

## 5. `LayoutParams` — the optimizer knobs

Every field is a placement/routing constant. **No W, L, ng or m appears here**;
those are read from `design.json` at build time. `BOUNDS` in the generator
carries the same ranges.

| knob | default | range | what it moves |
|---|---|---|---|
| `dev_gap_x` | 2.0 µm | 1.0 – 6.0 | horizontal clearance between devices inside a row |
| `axis_gap` | 6.0 µm | 2.0 – 30.0 | clearance from the symmetry axis to the inner edge of each half |
| `row_gap` | 6.0 µm | 3.0 – 20.0 | routing channel between device rows |
| `bias_row_gap` | 4.0 µm | 2.0 – 12.0 | vertical pitch gap inside the bias common-centroid array |
| `bias_dummy_cols` | 1 | 0 – 2 | dummy columns per side of the bias array |
| `gmfb_dummy` | 1 | 0 – 2 | dummy hv-pmos per end of the `gmf_b` centroid row |
| `well_margin` | 0.62 µm | 0.62 – 3.0 | NWell enclosure of Activ (NW.c floor) |
| `well_gap` | 2.0 µm | 1.8 – 6.0 | spacing between different-net n-wells (NW.b1 floor) |
| `ring_w` | 1.0 µm | 0.6 – 3.0 | guard-ring Metal1 width |
| `ring_gap` | 4.0 µm | 2.0 – 15.0 | clearance from the ring to the nearest device / cap plate |
| `shield_w` | 4.0 µm | 2.0 – 12.0 | width of the grounded A/B shield band |
| `cap_gap` | 0.4 µm | 0.30 – 3.0 | gap between adjacent MIM Metal5 plates inside a bank (M5 space ≥ 0.2, MIM space ≥ 0.6) |
| `cap_bank_gap` | 10.0 µm | 4.0 – 40.0 | gap between two sub-arrays inside a bank |
| `bank_gap` | 12.0 µm | 6.0 – 60.0 | gap between a cap bank and the device island next to it |
| `w_m1` | 0.20 µm | 0.14 – 1.0 | Metal1 wire width (M1.a = 0.14) |
| `w_m2` | 0.20 µm | 0.16 – 1.0 | Metal2 wire width |
| `w_m3` | 0.25 µm | 0.20 – 1.0 | Metal3 wire width |
| `w_tm1` | 1.70 µm | 1.64 – 4.0 | TopMetal1 wire width (TM1.a = 1.64) |
| `via_pad` | 2.0 µm | 1.7 – 4.0 | side of a `via_stack` landing pad (must clear TM1.a) |
| `tap_len` | 4.0 µm | 1.0 – 20.0 | length of one tap segment in a ring/row |
| `cc19_cols` | 4 | 1 – 8 | `xc19` array columns (rows derived: 8/cols) |
| `cc1_cols` | 4 | 1 – 16 | `xc1`/`xc10` array columns (rows derived) |
| `cc12_cols` | 7 | 1 – 7 | `xc12` array columns |
| `cc13_cols` | 2 | 1 – 2 | `xc13`/`xc17` array columns |

Cap array shape knobs (`cc*_cols`) change *placement only* — the unit count and
unit size come from `design.json` / `core.sp`, so `m` is invariant under the
knob and LVS cannot break on it. `bias_dummy_cols` and `gmfb_dummy` **do**
change the extracted netlist (dummies are real devices), so the generator also
emits the matching LVS reference — see §7.

Determinism: no randomness, no wall clock, no absolute paths; the same params
and the same `design.json` give a byte-identical GDS (checked by sha256 in the
report).

---

## 6. What this layout will NOT do

* **No density fill, no metal fill, no slotting.** Chip-level; it would distort
  the PEX of a bare cell. DRC is run with `--no_density`.
* **No sealring, no pads, no bumps, no ESD.** `net2`/`net3` tolerate 6.2 pA —
  an ESD or antenna diode on them is explicitly forbidden by the brief.
* **No antenna jumpers beyond the TopMetal1 spine that already exists.** If the
  antenna deck flags a long gate line, the fix is a higher-metal jumper, never
  a diode.
* **No Metal4 anywhere** (it would raise the MIM bottom-plate density 7×).
* **No decoupling on `vbr`/`vbn`/`rep_x`** (measured ac-inert to 100 pF).
* **No EM/IR-driven widening or via redundancy** (2.65 nA).
* **No off-cell mirror unit.** Brief §2.2: `xmbn` in the reference block is the
  same `bias` unit at m = 1 and belongs to the same 0.35 mV ratio. The unit
  cell, its pitch and its orientation are exported in the REPORT for whoever
  draws the reference block; drawing it here is out of scope.
* **The certified GDS is not committed** — the generator is the layout of
  record; build products go to a scratch build dir.

---

## 7. LVS reference — what is generated and why

`layout/H12-pdk-cap/asbuilt/core_lvs.sp` is produced by
`spicexplorer_signoff.postlayout.to_lvs_reference(core.sp, "lpf_core")` (X-cards
→ flat `M`/`C` cards the KLayout deck reads) plus three mechanical edits, all
emitted by `gen_H12_pdk_cap.py --lvs` so they can never drift from the drawn
layout:

1. node `0` → `vss`, and `vss` appended to the `.subckt` pin list (the layout's
   p-substrate tap ring is a named net);
2. **`xc1` and `xc10` terminal order swapped** (`Cc1 net4 voutp …`,
   `Cc10 net1 voutn …`): the deck's MIM device has non-equivalent
   `mim_top`/`mim_btm` terminals, and the brief's §6 flip puts `voutp`/`voutn`
   on the Metal5 bottom plate. Electrically identical for `cap_cmim`;
3. **dummy device cards** for the drawn dummies, one card per (type, L) group
   with the widths summed — verified behaviour: the deck runs `netlist.simplify`
   but does **not** purge a MOS with all four terminals shorted, and KLayout's
   MOS class combines parallel devices by summing W. With the default knobs:
   `Mdumn vss vss vss vss sg13_hv_nmos w=144u l=25u` (6 nmos dummies × 24 µm)
   and `Mdump vdd vdd vdd vdd sg13_hv_pmos w=24u l=31u` (2 pmos dummies × 12 µm).

Everything else is untouched — in particular `Mr3 … w=96u l=25u`, which is what
four drawn `W=24 µm` units in parallel extract to.

---

## 8. Decisions a human might reject, and what changes

1. **Stacked A-over-B islands with the caps at the two ends** (§3). Rejecting it
   in favour of, say, a left/right island split changes only the placement
   functions; the knob list and the LVS reference survive. Cost: one rebuild +
   full DRC/LVS/PEX/scorecard chain.
2. **Dummies on two classes only** (§2). If the reviewer wants dummies on the
   `bridge` or `in_*` rows, `gmfb_dummy`-style knobs get added per class and the
   LVS reference grows another card. Cost: one rebuild.
3. **`xc12`/`xc19` kept single-orientation instead of the brief's anti-oriented
   split** (§2). If rejected, each becomes two devices with swapped terminals
   and the LVS reference splits those two cards. Cost: one rebuild; the measured
   benefit is ≈ 0 (85–102 fF one-sided against 1800–6710 fF budgets).

Pin sides (§3) and the aspect-ratio target (≈ 1.2) were **not** specified by a
human; they are proposals under the same gate.
