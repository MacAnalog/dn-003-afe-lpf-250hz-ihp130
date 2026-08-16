# Layout brief — `H12-pdk-cap`

**KIND: LAYOUT BRIEF (measured).** Every number below was produced by injecting a
perturbation into the certified `.subckt lpf_core` and re-running the frozen benches
(`lab.metrics.evaluate` for the ac+noise scorecard, `lab.thd.measure` for S7). Nothing
here is a rule of thumb. Commands are in §11.

| | |
|---|---|
| netlist of record | `signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp` |
| `netlist_sha` (sha256) | `ef78d6f8d4e28cfbf18dc7abf6bd4066070fdf9f63546d430f16c4d71ffaf3c7` |
| perturbation primitive | `spicexplorer_signoff.sensitivity` (`inject_caps`, `inject_resistor`, `scale_param`, `sweep`) spliced in through `Design.dut_override` |
| bench | `lab.metrics.evaluate` (op+ac+noise, `mos_tt`, 27 °C, 1.5 V) and `lab.thd.measure` (S7, 175 mVpp diff, 50 Hz) |
| `margin_fraction` | **0.25** — a budget is the perturbation that eats a quarter of the margin that line has left |
| evaluations | 273 ac+noise, 8 THD |

**The margin I am spending.** Two bases are given everywhere. `nom` is the 27 °C /
1.5 V / `mos_tt` scorecard (the yardstick in `PRELAYOUT.md` §1). `pvt` is the worst
**passing** corner in `PRELAYOUT.md` §2 and §5 — the margin that actually survives
process, ±10 % supply, 0–70 °C and the MIM cap corners after the iref trim. Where the
two differ by 2.4× (`ph_max`) or 1.7× (`a1000`), design to `pvt`.

| line | nominal | margin (nom) | worst PASS corner | margin (pvt) |
|---|---|---|---|---|
| S1 `ph_max` ≥ 330° | 332.382 | **2.382°** | 331.0 (cap_bcs, trimmed) | **1.00°** |
| S1 `a1000` ≤ −48 dB | −49.026 | **1.026 dB** | −48.6 (mos_ff) | **0.60 dB** |
| S2 `fc` 245–255 Hz | 249.775 | **4.775 / 5.225 Hz** | 247.4 / 252.5 | **2.4 / 2.5 Hz** |
| S3 `ripple` ≤ 0.2 dB | 0.0523 | 0.148 dB | 0.097 (mos_fs) | 0.103 dB |
| S3 `dc` \|·\| ≤ 0.2 dB | −0.0081 | 0.192 dB | −0.034 | 0.166 dB |
| S4 `peak` ≤ 0.2 dB | 0.0018 | 0.198 dB | — | 0.198 dB |
| S5 `IRN` < 40 µV | 29.199 | 10.80 µV | 30.6 | 9.4 µV |
| S6 `P` < 50 nW | 11.912 | 38.09 nW | 13.11 | 36.9 nW |
| S7 `THD` ≤ −40 dB | −50.401 | 10.40 dB | −47.28 | 7.28 dB |

**The one-paragraph version.** This cell has almost no capacitive sensitivity on its
output nodes (pF-class budgets) and a brutal one on a single mechanism: **any
capacitance from the biquad-A internal nodes `net2`/`net3` to any biquad-B node closes
a feedback path around the whole 4th-order filter and eats the S1 phase certificate at
2.15 °/fF — budget 0.28 fF.** Everything else — series R, IRN, THD, power, dc gain,
the input pair's matching — is a don't-care by one to three orders of magnitude. The
second real constraint is the six-unit nmos bias array (`xm9`, `xm10`, `xr3`×4), which
must match to **0.35 mV of V_T**. The third is the MIM plate orientation: as drawn,
`xc1`/`xc10` put their Metal5 bottom plates on `net4`/`net1`, which is a 2.5–17×
budget violation before a single wire is routed.

---

## 1. Net sensitivity and capacitance budgets

Slopes are linear coefficients, checked over 1 / 10 / 100 / 1000 fF (linear to
< 2 % up to 100 fF on every net except `net2`/`net3`, where the 1 pF point saturates).
`—` = below the numerical floor of the metric at 1 pF (fc 4.1e-5 Hz, ph 1.2e-6 °).

Three numbers per differential pair, because they are physically different faults:

* **balanced** — the same C to ground on *both* halves (what a symmetric routing adds);
* **asym** — C to ground on *one* half only (routing asymmetry, one-sided plate parasitics);
* **diff** — C *between* the two halves (a shield between them, a differential cap).

| net(s) | class | balanced fF (nom / pvt) | asym fF (nom / pvt) | diff fF (nom) | binds | fc Hz/fF | ph °/fF | a1000 dB/fF |
|---|---|---|---|---|---|---|---|---|
| **`net2`, `net3`** | biquad-A internal (hi-Z, 22.4 MΩ) | **22.8 / 9.6** | **45.7 / 19.2** | **11.4** | `ph_max` | −0.0145 | **−0.0261** | −0.00205 |
| **`net4`, `net1`** | biquad-B internal | **82.8 / 34.8** | 165.6 / 69.5 | 41.4 | `ph_max` | −0.00056 | −0.00719 | −0.00025 |
| `voutp`, `voutn` | biquad-B output (pins) | 904 / 455 | 1801 / 905 | 460 | `fc` | −0.00132 | +0.00019 | −0.00015 |
| `vout_1`, `vout_2` | biquad-A output | **3353** | 6705 | 1676 | `peak` | +9.9e-6 | +5.5e-5 | −0.00016 |
| `vinp`, `vinn` | inputs (pins) | ∞ | ∞ | ∞ | — | — | — | — |
| `vbr` | replica gate rail | ∞ | — | — | — | — | — | — |
| `rep_x` | replica internal | ∞ | — | — | — | — | — | — |
| `vbn` | nmos gate rail (pin) | ∞ | — | — | — | — | — | — |
| `vdd` | supply (pin) | ∞ | — | — | — | — | — | — |
| `vbp` | **unused port** | ∞ | — | — | — | — | — | — |

Notes that matter more than the table:

* **`vbr`, `rep_x`, `vbn` are ac-inert.** 1 fF and 100 pF give *bit-identical*
  scorecards. `vbr` carries no differential signal (the two bridge gates load it
  antisymmetrically) and `vbn`/`rep_x` are dc-only. Decoupling them is neither
  required nor harmful — but it buys nothing, so do not spend area on it.
* **`vinp`/`vinn`/`vdd`/`vbp` are blind *in this bench*,** because the balun sources
  and the supply are ideal. That is a bench property, not a cell property: C on
  `vinp`/`vinn` loads whatever drives them, and its budget belongs to that driver, not
  here. Report the extracted input C up to the block owner; do not treat it as free.
* **`vout_1`/`vout_2` are the dump.** 3.3 pF per half, and every slope that is not
  zero moves the *good* way (see §8). Park routing, plate parasitics and well
  junctions here.
* **`net2`/`net3` are hi-Z** (measured dc impedance 22.4 MΩ, from the leakage sweep)
  and carry only **0.663 nA**. They are the smallest-current, highest-impedance,
  tightest-budget nets in the cell.

### 1.1 Cross-net coupling — where the cell actually breaks

Same injection, but between two *internal* nets rather than to ground. This is the
table to floorplan from.

| coupling | kind | budget fF (nom / pvt) | binds | ph °/fF |
|---|---|---|---|---|
| **`net2`↔`voutp` *and* `net3`↔`voutn` (both halves)** | biquad-A internal → biquad-B, symmetric | **0.28 / 0.12** | `ph_max` | **−2.151** |
| **`net2`↔`net4` (one half)** | A-internal → B-internal | **0.43 / 0.18** | `ph_max` | −1.371 |
| **`net2`↔`voutp` (one half)** | A-internal → B-output | **0.44 / 0.19** | `ph_max` | −1.345 |
| `net3`↔`net1`, `net3`↔`voutn` | mirror images of the two above | 0.43 / 0.19 | `ph_max` | −1.371 / −1.345 |
| `net2`↔`vout_2` | A-internal → opposite-half A-output | 23.1 / 9.7 | `ph_max` | −0.0258 |
| `net2`↔`vbr` / `vbn` / `rep_x` | signal → bias rail (rail is ac ground) | 45.6 / 19.1 | `ph_max` | −0.0131 |
| `voutp`↔`net1` | B-output → opposite-half B-internal | 84.8 / 35.6 | `ph_max` | −0.0070 |
| `net2`↔`vout_1` | *this is just c1_a trim* | 89.6 / 45.0 | `fc` | −0.00014 |
| `net2`↔`voutn` | A-internal → opposite-half output | 103 / 52 | `fc` | +1.44 (safe dir.) |
| `net2`↔`net1` | A-internal → opposite-half B-internal | 110 / 56 | `fc` | +1.46 (safe dir.) |
| `net4`↔`vbr` / `vbn` / `rep_x` | signal → bias rail | 166 / 69.5 | `ph_max` | −0.0036 |
| `vout_1`↔`voutn` | A-output → opposite-half output | 205 / 120 | `a1000` | +0.0104 |
| `net4`↔`vout_2` | B-internal → opposite-half A-output | 213 / 125 | `a1000` | −0.0008 |
| `voutp`↔`vbr` | output → bias rail | 1828 / 919 | `fc` | +9.4e-5 |
| `vout_1`↔`vbr` / `rep_x` | A-output → bias rail | ≈6.5 pF | `peak` | +2.3e-5 |

**The mechanism, stated once.** `net2`/`net3` sit at 22 MΩ *inside* biquad A's local
loop. A capacitor from there to anything in biquad B (`net4`, `net1`, `voutp`, `voutn`)
is a feedback path that wraps the whole 4th-order filter, bypassing both source
followers. It costs phase lag — the direction S1 fails in — at 1.3–2.2 °/fF. Direct
sweep (`net2`↔`voutp` **and** `net3`↔`voutn`, i.e. what a symmetric layout produces):

| C per half | 0 | 1.0 fF | **1.5 fF** | 2.0 fF | 3.0 fF |
|---|---|---|---|---|---|
| `ph_max` (°) | 332.382 | 330.231 | **329.457 — S1 FAIL** | 328.777 | 327.614 |

Hard S1 limit ≈ **1.11 fF per half**; at the worst passing corner (`ph_max` 331.0) it is
**0.47 fF**. Minimum-spacing parallel metal couples ≈0.05–0.1 fF/µm, so **the entire
budget is 3–6 µm of parallel run.** Treat `net2`/`net3` as nets that must not run
alongside, above or below *any* biquad-B net, at any layer, for any distance. This is
the single hard floorplan constraint in the cell.

Note the asymmetry worth exploiting: the *cross-half* versions of the same coupling
(`net2`↔`net1`, `net2`↔`voutn`) move `ph_max` the **safe** way and are 250× looser.
If a crossing is unavoidable, cross into the *opposite* half.

### 1.2 Series resistance — measured, then dismissed

nA-class, 250 Hz. Injected 1 MΩ / 10 MΩ / 100 MΩ in series with `vbr`, `vdd`, `net2`
and `vout_1`:

| net | 1 MΩ effect | budget (nom) |
|---|---|---|
| `vbr` | below the numerical floor on every metric | ∞ |
| `net2` | below the numerical floor | ∞ |
| `vout_1` | fc +0.037 Hz | 35 MΩ |
| `vdd` | fc −0.008 Hz | 148 MΩ |

Maximum branch current is 2.65 nA, so 1 MΩ of routing is 2.6 mV of IR — and the loop
does not care. **Resistance is a don't-care for the whole cell.** Do not widen metal
for current, do not fret over via counts, do not add resistance-driven redundancy.
The only R worth a thought is the MIM top-plate `R1 = 55 mΩ` already in the model.

---

## 2. Matching

The PDK's `sg13_hv_*` wrapper hard-codes `delvto=0`, so a V_T mismatch cannot be passed
as a device parameter. It was injected as a **series dc source on the gate** (ΔV_GS,
which is −ΔV_T); the geometry column is the independent `scale_param` cross-check, and
the two agree to 10 % through the weak-inversion identity ΔI/I = ΔW/W = (g_m/I_D)·ΔV_T.

Two columns, because they are different faults with 20–400× different budgets:

* **common** — both halves shifted the same way *relative to the bias reference*: a
  systematic error (gradient across the array, different surroundings, wrong dummy
  count). This is what moves `fc`.
* **diff** — one half against the other: what random mismatch and linear gradients do.
  It moves essentially nothing linear; it produces dc offset and HD2 (§7).

| class | devices | tolerated ΔV_GS common, mV (nom / pvt) | tolerated ΔV_GS diff, mV | tolerated ΔW, % | binds | pattern required |
|---|---|---|---|---|---|---|
| **`rep_sink` ratio** | `xr3` (m=4) vs `xm9`,`xm10` | **0.35 / 0.18** | — | **0.89** | `a1000`/`fc` | **common-centroid + dummies**, one 6-unit array |
| **`bias_a`** | `xm9`, `xm10` | **0.41 / 0.20** | 152 | 2.02 | `fc` | same array as above |
| `rep_gmfb` ratio | `xr1` vs `xm14`,`xm15` | 0.84 / 0.40 | — | 1.91 | `fc` | common-centroid + dummies (shared `vdd` well) |
| `rep_bridge` ratio | `xr2` vs `xmst`,`xmstn` | 0.84 / 0.40 | — | 1.77 | `fc` | same row, same orientation, abutted |
| `gmf_b` | `xm14`, `xm15` (+`xr1`) | 0.79 / 0.40 | 8.0 / 3.4 | 4.02 | `fc` | common-centroid + dummies |
| `bridge` | `xmst`, `xmstn` | 0.79 / 0.40 | 8.1 / 3.4 | 3.79 | `a1000` | mirrored, **well-level** centroid |
| `in_b` | `xm0`, `xm1` | 34 / 16 | 33 / 16 | 37 | `fc` | mirrored about the axis; any |
| `gmf_a` | `xm4`, `xm8` | 97 / 46 | 64 / 41 | 14 | `ripple` | same row, same orientation |
| `in_a` | `xm2`, `xm5` | **48 / 23** | **108 / 54** | 89 | `ph_max` | **any** — orientation match only |

| cap class | devices | tolerated ΔC on one member, % (nom / pvt) | binds | fc Hz/% |
|---|---|---|---|---|
| `c1_b` | `xc1`, `xc10` (16 units, 59.9 pF) | **1.69 / 1.18** | `ripple` | −0.344 |
| `c1_a` | `xc13`, `xc17` (2 units, 4.94 pF) | 1.82 / 0.91 | `fc` | −0.657 |
| `c2_b` | `xc12` (7 units, 24.7 pF, on axis) | 1.83 / 0.92 | `fc` | −0.653 |
| `c2_a` | `xc19` (8 units, 29.3 pF, on axis) | 3.47 | `peak` | −0.0065 |

**Read this before choosing patterns.**

1. **One nmos array rules the cell.** `xm9`, `xm10` and `xr3` are the *same* 0.663 nA
   unit device — 1 + 1 + 4 = **six identical units**. Their ratio sets `vbr`, hence
   every branch current, hence `fc`. Tolerated 0.35 mV. At W/L = 24/25 µm × ng 3
   (600 µm² per unit) the random σ(V_T) is already ≈0.2 mV, which is exactly the
   `PRELAYOUT.md` §4 Monte-Carlo result (σ(fc) = 3.76 Hz, 82 % all-pass, **every**
   failure S2). **The layout has no mismatch budget to spend here — it may only avoid
   adding gradient.** Common-centroid, ≥2 rings of dummies, identical local
   surroundings, identical routing on all six.
2. **The off-cell mirror unit is part of the array.** `xmbn` in the bench (and the real
   reference block) is built from the same `bias_*` geometry at m = 1. If it is drawn
   differently or sits far away, that is a ratio error against the same 0.35 mV
   budget. Export the unit cell, its pitch and its orientation to whoever draws the
   reference; do not let them re-derive it.
3. **Bulk-to-source ties forbid classical interdigitation for four of the pairs.**
   `xm2`/`xm5`, `xmst`/`xmstn`, `xm0`/`xm1` and `xr2` each have their body on their own
   signal net (§5), so the two members of each pair **cannot share an n-well**.
   Common-centroid for them means *well-level* centroid: two wells placed
   symmetrically about the axis with matching surroundings, not interleaved fingers.
   Only `xm14`/`xm15`/`xr1` (all bulk = `vdd`) and the nmos (all bulk = substrate) can
   be interdigitated in the textbook way — and those are exactly the two arrays where
   it matters.
4. **`in_a` is free.** 48 mV common / 108 mV differential of tolerated ΔV_GS on the
   *input pair*. This is counter-intuitive and worth stating loudly: do not spend a
   big common-centroid structure on `xm2`/`xm5`. They are source followers; their V_T
   mismatch shows up as output offset, not as a spec line. Same for `gmf_a`.

---

## 3. Hi-Z nodes and leakage

Injected a dc current source on each node and re-ran the bench. Budget = the leakage
that costs 25 % of the tightest margin.

| node | branch current | dc impedance | budget pA (nom / pvt) | one-sided pA | binds | rule for layout |
|---|---|---|---|---|---|---|
| **`net2`, `net3`** | **0.663 nA** | 22.4 MΩ | **6.2 / 3.0** | 11.0 | `fc` | **no ESD or antenna diode, no pad, no extra diffusion or well area.** Minimum drain areas only; route on metal, never on diffusion or poly straps |
| `vbr` | 2.649 nA | — | 25.9 / 12.5 | — | `a1000` | gate rail + `xr2` diode + `xr3` drain; keep short, no diode-like structures |
| `rep_x` | 2.649 nA | — | 53 / 25.7 | — | `a1000` | carries the `xr2` n-well |
| `net4`, `net1` | 2.646 nA | 8.2 MΩ | 60.6 / 29.0 | 122 | `fc` | carries the `xmst`/`xmstn` n-well — keep that well minimal |
| `vout_1`, `vout_2` | 1.984 nA | — | 145 / 72.7 | — | `fc` | carries the `xm2`/`xm5` n-well; generous |
| `voutp`, `voutn` | 2.646 nA | — | 211 / 106 | — | `fc` | carries the `xm0`/`xm1` n-well; the only analog nets that may leave the cell |

**How much headroom is that, really.** `doc/pdk-notes.md` §2.4: an hv nmos leaks
≈5e-14 A and an hv pmos ≈1e-13 A at W = 10 µm with V_GS = 0 — four to five orders below
the branch. The `net2` junctions are tiny (the PDK wrapper computes A_D = 3.0 µm² for
`xm2`, 5.8 µm² for `xm9`), so the real dc leak at 27 °C is sub-femtoamp against a
6.2 pA budget: **~10⁴ of margin, unless the layout creates a new leakage path.** The
budget exists to forbid exactly that — a protection diode, a probe pad, a large
n-well, a poly/diffusion routing strap. Note also that leakage on `net2` propagates
straight to the output dc: 10 pA one-sided moves `voutp` by 0.6 mV.

---

## 4. Devices — currents, voltages, saturation margin

All hv (thick-oxide) flavour, all in weak inversion, all bodies tied to their sources.

| inst | role | type | I_D nA | \|V_DS\| mV | \|V_GS\| mV | V_dsat mV | sat margin mV | g_m/I_D | body / well |
|---|---|---|---|---|---|---|---|---|---|
| `xm2` / `xm5` | in_a | hv pmos | 0.663 | 166 | 455 | 101 | **+64** | 25.1 | n-well = `vout_1` / `vout_2` (695 mV) |
| `xm4` / `xm8` | gmf_a | hv nmos | 1.984 | 695 | 529 | 110 | +585 | 22.6 | p-substrate |
| `xm9` / `xm10` | bias_a_int | hv nmos | 0.663 | 529 | 356 | 101 | +428 | 28.1 | p-substrate |
| `xmst` / `xmstn` | bridge | hv pmos | 2.646 | 236 | 609 | 105 | +131 | 22.2 | n-well = `net4` / `net1` (931 mV) |
| `xm0` / `xm1` | in_b | hv pmos | 2.646 | 347 | 584 | 104 | +244 | 23.4 | n-well = `voutp` / `voutn` (1278 mV) |
| `xm14` / `xm15` | gmf_b | hv pmos | 2.646 | 222 | 569 | 103 | **+119** | 24.0 | n-well = `vdd` (1500 mV) |
| `xr1` | rep_gmfb | hv pmos | 2.649 | 569 | 569 | 103 | +466 | 24.0 | n-well = `vdd` |
| `xr2` | rep_bridge | hv pmos | 2.649 | 609 | 609 | 105 | +504 | 22.2 | n-well = `rep_x` (931 mV) |
| `xr3` (m=4) | rep_sink | hv nmos | 2.649 | 322 | 356 | 101 | +221 | 28.1 | p-substrate |

* dc ladder: VDD 1500 → `voutp` 1278 → `net4` 931 → `vout_1` 695 → `net2` 529 → 0.
* Smallest saturation margins: **`xm2`/`xm5` +64 mV**, then `xm14`/`xm15` +119 mV.
  These two set the cell's headroom, and headroom is the axis every failing PVT corner
  fails on (`PRELAYOUT.md` §2). A differential offset of X mV splits ±X/2 across the
  ladder, so keep total dc offset well under 2×0.25×64 ≈ **32 mV** — 32× more than any
  realistic mismatch produces (§7), i.e. not a real constraint, but the number to check
  against if the layout ever introduces a systematic ΔV_GS.
* Core current 7.94 nA / 11.91 nW at 1.5 V; largest single-net current **2.65 nA**.

---

## 5. Wells — the island plan

Every pmos has its body tied to its own source, so **eight distinct n-wells**, seven of
them at a *signal* potential. There is no freedom here: two devices may share a well
only if their sources are the same net.

| well net | V | devices | shareable? |
|---|---|---|---|
| `vdd` | 1500 mV | `xm14`, `xm15`, `xr1` | **yes — the only shared well.** Put all three in one common-centroid array |
| `voutp` | 1278 | `xm0` | no |
| `voutn` | 1278 | `xm1` | no |
| `net4` | 931 | `xmst` | no — **and see below** |
| `net1` | 931 | `xmstn` | no |
| `rep_x` | 931 | `xr2` | no |
| `vout_1` | 695 | `xm2` | no |
| `vout_2` | 695 | `xm5` | no |
| p-substrate | 0 | `xm4`, `xm8`, `xm9`, `xm10`, `xr3` | yes (all nmos) |

Consequences the designer must plan around:

1. **The `net4`/`net1` wells sit on the second-tightest nets in the cell.** Their
   n-well/p-substrate junction capacitance and leakage land directly on `net4`/`net1`,
   whose *balanced* budget is 82.8 fF (34.8 fF at corner). `xmst` is W 5 µm × L 33 µm,
   so the minimum enclosing well is ≈220 µm²; at a typical 0.1 fF/µm² junction density
   that is ≈22 fF — **a quarter of the budget, before any routing.** Draw these two
   wells at minimum enclosure, and give them identical shapes. Confirm the junction
   density from PEX rather than trusting the 0.1 fF/µm² estimate.
2. **`rep_x` is at the same 931 mV as `net4`/`net1` but is a different net** — three
   separate wells at the same potential, which is exactly the kind of thing a layout
   tool will try to merge. It must not.
3. The three 931 mV wells and the two 695 mV wells are close in potential and adjacent
   in the floorplan; **well-to-well spacing here is a matching and coupling question,
   not a DRC one.** Any well-to-well capacitance between a `net4`-well and a
   `net2`-adjacent structure falls under the 0.28 fF rule of §1.1.
4. Guard rings: the cell tolerates 6.2 pA of leakage and 0.28 fF of A→B coupling. Ring
   the whole core with a substrate tap ring, and ring `net2`/`net3`'s devices
   separately. Do **not** tie a guard ring to any of the seven signal wells.

---

## 6. MIM capacitors — plate orientation is a hard finding

`cap_cmim` is 1.5 fF/µm². The PDK DRC (`MIM.c`: "Min. **Metal5** enclosure of MIM";
`MIM.d`: "Min. MIM enclosure of TopVia1") puts the **bottom plate on Metal5** and takes
the top plate up through TopVia1; the SPICE model card says *"top corresponds to PLUS
pin"* and *"top/bottom plate parasitic capacitance is included by parasiticC
extraction"* — i.e. **the second terminal in each card is the bottom plate, and its
parasitic is not in the schematic at all.**

Bottom-plate estimate from the ITF stack (`libs.tech/parasitics/itf/sg13g2_typ.itf`):
Metal5 to substrate is ≈6.98 µm of ε_r 4.1 dielectric → **5.2 aF/µm²** with nothing
underneath, rising to **35 aF/µm²** if a Metal4 plane sits directly below.

| MIM | nets (PLUS = top) | units | area µm² | C | bottom plate on | C_bot est. | budget of that net | verdict |
|---|---|---|---|---|---|---|---|---|
| `xc13` | `net2` / `vout_1` | 2 × 40.53 µm | 3 285 | 4.94 pF | `vout_1` | 17–115 fF | 3353 fF | **OK as drawn** |
| `xc17` | `net3` / `vout_2` | 2 × 40.53 | 3 285 | 4.94 pF | `vout_2` | 17–115 fF | 3353 fF | **OK as drawn** |
| `xc19` | `vout_2` / `vout_1` | 8 × 49.42 | 19 539 | 29.3 pF | `vout_1` only | 102–684 fF | 6705 fF (asym) | OK but **asymmetric** — split 4+4 anti-oriented |
| **`xc1`** | `voutp` / **`net4`** | 16 × 49.91 | 39 856 | 59.8 pF | **`net4`** | **207–1395 fF** | **83 fF** | **FLIP — 2.5–17× over budget** |
| **`xc10`** | `voutn` / **`net1`** | 16 × 49.91 | 39 856 | 59.8 pF | **`net1`** | **207–1395 fF** | **83 fF** | **FLIP** |
| `xc12` | `voutn` / `voutp` | 7 × 48.45 | 16 432 | 24.7 pF | `voutp` only | 85–575 fF | 1801 fF (asym) | OK but **asymmetric** — split 4+3 anti-oriented |

**Action.** Draw `xc1`/`xc10` with the Metal5 bottom plate on `voutp`/`voutn` (the
900 fF-budget net), not on `net4`/`net1`. Electrically a capacitor is symmetric, so
this costs nothing; if LVS enforces PLUS = top, swap the terminal order on those two
cards in the layout-equivalent netlist and re-run the identity gate. As drawn, the
extracted cell fails S1 before a single wire is routed.

Two more MIM rules that follow from §1.1:

* **`xc13`/`xc17`'s plates carry `net2`/`net3`.** They must be physically separated
  from the `xc1`/`xc10`/`xc12` plates — no stacking, no abutment, a grounded gap
  between the arrays. Plate-to-plate coupling between those two cap banks is exactly
  the `net2`↔`voutp`/`net4` path with a 0.28 fF budget.
* Total MIM area 0.122 mm² against the PDK's recommended 174 800 µm² per chip — this
  one cell uses 70 % of that recommendation. Flag it to the block owner.

---

## 7. What the linear bench cannot see — S7 and offset

Differential mismatch barely moves the ac scorecard, so S7 (expensive, 8 runs) and the
dc operating point were measured separately to prove it is not hiding there.

| perturbation | THD dB | HD3 dB | HD2 dB | Δ dc offset |
|---|---|---|---|---|
| baseline | **−50.401** | −50.605 | −100.19 | 0 |
| `in_a` ΔV_GS diff 1 mV | −50.401 | −50.605 | −91.43 | +1.00 mV |
| `in_a` ΔV_GS diff 5 mV | −50.412 | −50.621 | −80.63 | — |
| `in_b` ΔV_GS diff 5 mV | −50.406 | −50.609 | −101.78 | +1.00 mV (at 1 mV) |
| `bias_a` ΔV_GS diff 5 mV | −50.098 | −50.525 | −63.30 | +1.12 mV (at 1 mV) |
| `c1_a` +1 % on one side | −50.277 | −50.480 | −81.94 | — |
| `net2` one-sided C 100 fF | −50.158 | −50.368 | −75.73 | — |
| `net2`+`net3` balanced C 100 fF | *gated: S1 FAIL (`ph_max` 329.9)* | | | |

* S7 is **HD3-dominated and mismatch-blind.** HD2 rises 20 dB per decade of mismatch,
  but from −100 dB — it would take ≈19 mV of `bias_a` ΔV_GS or 31 % of cap mismatch to
  make HD2 reach HD3 and cost a quarter of the 10.4 dB margin. **THD is a don't-care
  for layout.** Spend nothing on it.
* dc offset is ≈1 mV of differential output per 1 mV of `in_a`/`in_b`/`bias_a`
  mismatch, −0.49 mV per mV for `gmf_b`/`bridge`, and essentially zero for `gmf_a`.
  Against the ≈32 mV headroom limit of §4 this is not a constraint either.
* The last row is the useful one: **100 fF of balanced parasitic on `net2`/`net3` fails
  S1 outright** — the harness refused to spend a transient on it. That is the budget of
  §1 confirmed at the pass/fail boundary rather than by extrapolation.

---

## 8. Things that move the *good* way — free trims

* **`iref` ±10 % moves `fc` ∓10 % with the shape unchanged** (`PRELAYOUT.md` §5, the
  same knob that absorbs the S2 Monte-Carlo tail). Every *symmetric* parasitic `fc`
  shift the layout adds is therefore recoverable at test. Asymmetric shifts and phase
  loss are not. **Spend the `fc` budget freely on symmetric parasitics; guard the
  `ph_max` budget absolutely.**
* **Loading `vout_1`/`vout_2` (balanced) improves three lines at once**: ripple
  −5.9e-5 dB/fF, `a1000` −1.6e-4 dB/fF, IRN −1.35e-5 µV/fF, with `fc` +9.9e-6 Hz/fF.
  100 fF per half buys 0.016 dB of stopband for nothing. If a shield plate or a MIM
  bottom plate has to go somewhere, this is where.
* Cross-half coupling (`net2`↔`net1`, `net2`↔`voutn`) *raises* `ph_max`. Do not use it
  as a trim — it also costs `fc` at 0.011 Hz/fF and it makes the S1 certificate
  meaningless (see the caveat in §10) — but it means an unavoidable crossing should be
  routed into the **opposite** half, not the same one.

---

## 9. Don't-cares — what not to over-constrain

Listed so the layout is not gold-plated where the measurement says it need not be:

* **Series resistance, everywhere.** Nothing below ≈15 MΩ is measurable (§1.2).
* **Current density / EM.** Max net current 2.65 nA, supply pin 7.94 nA. Minimum-width
  metal is electrically adequate on every net including `vdd`.
* **Self-heating, dV/dt aggressors inside the cell.** 11.9 nW, 250 Hz. There is no
  aggressor here; the threat is entirely external (see §10).
* **`vbn`, `vdd`, `vbp`, `vinp`, `vinn`** — no measurable capacitive sensitivity.
  `vbp` is a **dangling port**: it appears in the `.subckt` header and connects to no
  device. Keep the pin for LVS, route nothing to it.
* **`vbr`, `rep_x`** — ac-inert to 100 pF; only their leakage (26 / 53 pA) and the
  matching of the devices on them matter.
* **`in_a` (`xm2`/`xm5`) and `gmf_a` (`xm4`/`xm8`) matching** — 48–97 mV of tolerated
  ΔV_GS. Same orientation, same row; no centroid, no dummy ceremony.
* **S5 / IRN.** No perturbation in 273 runs moved IRN by more than 0.3 % of its
  10.8 µV margin. The cell's headline number is layout-insensitive.
* **S6 / power** (38 nW of margin) and **S3 / dc gain** (every slope ≤ 1e-5 dB).
* **S7 / THD** (§7).
* **C on `vout_1`/`vout_2` below 3.3 pF per half** (§8).

---

## 10. What I would watch

Three things, in order.

**First, the A→B feedback path.** Everything else in this brief is a budget; this one
is a topology hazard with a 0.28 fF allowance, and it is invisible to the usual layout
instincts because the two nets involved (`net2` and `voutp`) look like they belong to
different, unrelated stages. They do — that is precisely why coupling them closes a
loop the design never had. I would floorplan biquad A and biquad B as two separated
islands with the replica between them, keep `net2`/`net3` entirely inside biquad A's
island (they never need to leave it: their only connections are `xm2`/`xm9` drains,
`xm4`'s gate and the `xc13` top plate), and put a grounded shield on the island
boundary. Then I would ask the PEX reviewer for one specific number — C(`net2`,
`net4`) + C(`net2`, `voutp`) + C(`net2`, `net1`) + C(`net2`, `voutn`) — and treat
anything above 0.3 fF as a redesign, not a tune.

**Second, the MIM plate assignment and the cap-bank adjacency.** `xc1`/`xc10` as drawn
put 0.2–1.4 pF of bottom-plate parasitic on an 83 fF net; that is a fail on paper
before any routing exists, and it is fixed by a free choice of which plate is which.
While fixing it, keep the `xc13`/`xc17` bank (whose top plates are `net2`/`net3`)
physically away from the other three banks — the plate-to-plate path is the 0.28 fF
mechanism again, with 0.12 mm² of plate area to build it from.

**Third, the six-unit nmos bias array.** 0.35 mV of tolerated V_T mismatch against a
random σ of ≈0.2 mV means the design is already at the mismatch limit; the Monte-Carlo
yield of 82 % — with *every* failure on S2 `fc` — is that statement measured. The
layout cannot improve this and can easily halve it. Common-centroid the six units,
dummy them generously, keep the routing to all six identical, and make sure the
reference block's mirror unit is the same drawn device in the same orientation.

Two caveats on the instrument itself. (a) `ph_max` is the max unwrapped phase lag over
the whole 0.1 Hz–100 kHz sweep, so a cross-half coupling that adds a *high-frequency*
pole pushes it **up** by up to 116° regardless of the coupling's size — the number
still passes but stops certifying "two true biquads". If PEX shows `ph_max` above ~340°,
that is a corrupted certificate, not extra margin; re-read the phase curve. (b) `vinp`,
`vinn` and `vdd` are driven by ideal sources in the bench, so their capacitance
measures as exactly zero. That is a bench boundary, not a result — report the extracted
input and supply capacitance upward rather than declaring it free.

---

## 11. Reproducing every table

Environment, from the repo root:

```bash
export LPF_NGSPICE=/home/noorizad/local/bin/ngspice \
       PDK_ROOT=/home/noorizad/local/pdks LPF_JOBS=12
cd experiments/023-replica-bias
```

Common preamble for every script (the perturbation primitive is the platform's; the
measurement is this repo's frozen harness — the module never depends on the bench):

```python
import json, sys
sys.path.insert(0, ".../spicexplorer-platform/packages/spicexplorer-signoff/src")
import common as X                                  # experiments/023-replica-bias/common.py
from lab.metrics import evaluate                    # the frozen ac+noise scorecard
from lab import thd as T                            # S7
from lab.oppoint import probe                       # dc node voltages
from spicexplorer_signoff.sensitivity import inject_caps, inject_resistor, scale_param, sweep

d    = X.from_json(json.load(open("../../signoff/post-pvt/H12-pdk-cap/design.json"))["design"])
core = open("../../signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp").read()

def measure(text):
    s = evaluate(d.with_(dut_override=text), "brief", record=False)
    return {k: float(s.values[k]) for k in
            ("fc_hz","dc_db","ripple_db","peak_db","ph_max_deg","a1000_db","irn_uv","p_core_nw")}
```

| table | script | what it runs |
|---|---|---|
| §1 (net budgets), §1.2 (R), §2 (geometry) | `run_sens.py` | `sweep(core, "lpf_core", measure, nets=[15 nets], pairs=[5 pairs], c_ff=(1,10,100,1000), r_nets=[(vbr,1M),(vdd,1M),(net2,1M),(vout_1,1M),(vbr,100M),(vdd,10M)], params=[16 scale_param cases])` — 123 evaluations, 51 s |
| §1 (balanced), §1.1 (cross-coupling), §2 (ΔV_GS) | `run_sens2.py` | balanced `inject_caps([(a,"0",C),(b,"0",C)])`; 17 cross pairs × 10/100 fF; 1 pF–100 pF decaps on `vbn`/`vbr`/`rep_x`; gate-series ΔV_GS on 9 devices — 65 evaluations, 28 s |
| §2 (common vs diff), §7 (offset) | `run_sens3.py` | ±0.5 mV (pure differential) and +1 mV (pure common) per pair; replica-only ΔV_GS; `probe()` for `v(voutp)−v(voutn)` — 23 evaluations, 13 s |
| §7 (THD) | `run_thd.py` | `T.measure(d.with_(dut_override=text), tag=...)` over 8 cases via `lab.parallel.batch(workers=8)` — 16 s |
| §3 (leakage) | `run_leak.py` | dc `Ilk <net> 0 dc I` at ±1/10/100 pA on 6 nodes, balanced and one-sided, with `probe()` node voltages — 31 evaluations, 21 s |
| §1.1 (sub-fF confirmation) | inline | `inject_caps(core,"lpf_core",[("net2","voutp",C),("net3","voutn",C)])` for C = 1.0/1.5/1.7/2.0/3.0 fF, reading `s.violations` |
| all budgets | `compute.py` | budget = 0.25 × remaining margin ÷ linear slope, min over the metrics that move the wrong way; slope taken at the smallest injection clearing 10× the metric's numerical floor |

Scripts live in the scratch dir of the session that produced this brief
(`/home/noorizad/.claude/jobs/fca5caa6/tmp/brief/`) together with the raw rows
(`sens_rows{,2,3,6}.json`, `thd_rows.json`, `leak_rows.json`, `budgets.json`).

### Proposed platform diffs (procedural — not self-applied, per rule 10)

`spicexplorer_signoff.sensitivity` covers C, series R and device parameters. Two
perturbations this brief needed are missing and were written inline; both are
general-purpose and belong in the module:

1. **`inject_vsource(subckt, name, device, dv, *, pin="g")`** — a dc source in series
   with a device pin. Needed because the IHP `sg13_hv_*` wrapper hard-codes
   `delvto=0`, so a V_T mismatch **cannot** be expressed through `scale_param`. Without
   it every mismatch campaign on this PDK has to go through ΔW and an analytic
   conversion.
2. **`inject_isource(subckt, name, nets: dict[str, float])`** — dc current injection
   per node, i.e. the leakage / ESD-diode / antenna-diode budget primitive. `sweep()`
   should grow an `i_nets=` argument alongside `r_nets=`.

A third, smaller one: `sweep()` currently offers `c_pair` (between the halves) and
`c_onesided` (one half to ground) but not `c_balanced` (both halves to ground), which
is the case a symmetric layout actually produces and the one that turned out to bind
here. Adding it would have saved a hand-written loop.
