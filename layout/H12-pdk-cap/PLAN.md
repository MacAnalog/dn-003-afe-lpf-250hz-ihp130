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
