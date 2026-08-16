# Layout-level results — every number, with its source

[REFERENCE] · assembled 2026-08-16 from committed artifacts on `feat/layout-h12-round2`.

Cell `lpf_core`, layout of record `layout/H12-pdk-cap/`, IHP SG13G2.
Four design passes ("rounds"), 14 snapshotted iterations, three independent
reviews, two 300-trial area campaigns. Paths are relative to the repo root.

**Round numbering.** Round 1 = the first generated layout (it01). Round 2 =
it02–it08 (the fix round after review 1). Round 3 = it09–it13 (the fix round
after review 2). Round 4 = **it14 alone** — a *decision* round: the block owner
reversed a plan decision and the area campaign's knob point became the default.
The independent review of record is **round 3** (`REVIEW.md`, `REVIEW.yaml`);
round 4 has not been reviewed yet.

---

## 1. The brief — measured design intent

The brief is what makes a generic layout agent circuit-specific. It was produced
from **273 ac+noise and 8 THD evaluations** of the certified netlist
(`signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`, sha256 `ef78d6f8…af3c7`) with
parasitics and mismatch injected through `Design.dut_override`
(`spicexplorer_signoff.sensitivity`). A budget is **the perturbation that eats
25 % of the margin that spec line has left** (`margin_fraction: 0.25`).

### 1.1 The margin being spent

| line | nominal | margin (nominal) | worst PASSING corner | margin (pvt) |
|---|---|---|---|---|
| S1 `ph_max ≥ 330°` | 332.382 | **2.382°** | 331.0 (`cap_bcs` trimmed) | **1.00°** |
| S1 `a1000 ≤ −48 dB` | −49.026 | **1.026 dB** | −48.6 (`mos_ff`) | **0.60 dB** |
| S2 `fc` 245–255 Hz | 249.775 | 4.775 / 5.225 Hz | 247.4 / 252.5 | 2.4 / 2.5 Hz |
| S3 `ripple ≤ 0.2 dB` | 0.0523 | 0.148 dB | 0.097 (`mos_fs`) | 0.103 dB |
| S3 `\|dc\| ≤ 0.2 dB` | −0.0081 | 0.192 dB | −0.034 | 0.166 dB |
| S4 `peak ≤ 0.2 dB` | 0.0018 | 0.198 dB | — | 0.198 dB |
| S5 `IRN < 40 µV` | 29.199 | 10.80 µV | 30.6 | 9.4 µV |
| S6 `P < 50 nW` | 11.912 | 38.09 nW | 13.11 | 36.9 nW |
| S7 `THD ≤ −40 dB` | −50.401 | 10.40 dB | −47.28 | 7.28 dB |

Source: `layout/H12-pdk-cap/BRIEF.md` §0

### 1.2 Per-net capacitance budget

Three numbers per differential pair: **balanced** (equal C on both halves),
**asym** (C on one half only), **diff** (C between the halves).

| net(s) | class | balanced fF (nom / pvt) | asym fF | diff fF | binds | fc Hz/fF | ph °/fF |
|---|---|---|---|---|---|---|---|
| **`net2`, `net3`** | **biquad-A internal, hi-Z (22.4 MΩ)** | **22.8 / 9.59** | 45.7 / 19.2 | 11.4 | `ph_max` | −0.0145 | **−0.0261** |
| `net4`, `net1` | biquad-B internal | 82.8 / 34.8 | 166 / 69.5 | 41.4 | `ph_max` | −0.00056 | −0.00719 |
| `voutp`, `voutn` | biquad-B output (pins) | 905 / 455 | 1800 / 905 | 460 | `fc` | −0.00132 | +0.00019 |
| `vout_1`, `vout_2` | biquad-A output | 3350 | 6710 | 1680 | `peak` | +9.9e-6 | +5.5e-5 |
| `vinp`/`vinn`/`vbr`/`rep_x`/`vbn`/`vdd`/`vbp` | rails, pins, ac-inert | ∞ | — | — | — | — | — |

`vbr`, `rep_x`, `vbn` are **ac-inert**: 1 fF and 100 pF give bit-identical
scorecards. `vinp`/`vinn`/`vdd`/`vbp` are blind *in this bench only* (ideal
sources) — a bench property, not a cell property, and the brief says so.
`vout_1`/`vout_2` are "the dump" — 3.3 pF per half, and every non-zero slope
moves the good way.

### 1.3 Cross-net coupling — the floorplan constraint

| coupling | budget fF (nom / pvt) | binds | ph °/fF |
|---|---|---|---|
| **`net2`↔`voutp` *and* `net3`↔`voutn` (symmetric, both halves)** | **0.28 / 0.12** | `ph_max` | **−2.151** |
| `net2`↔`net4` (one half) | 0.43 / 0.18 | `ph_max` | −1.371 |
| `net2`↔`voutp` (one half) | 0.44 / 0.19 | `ph_max` | −1.345 |
| `net2`↔`vout_2` | 23.1 / 9.7 | `ph_max` | −0.0258 |
| `net2`↔ any bias rail | 45.6 / 19.1 | `ph_max` | −0.0131 |
| `voutp`↔`net1` | 84.8 / 35.6 | `ph_max` | −0.0070 |
| `net2`↔`voutn`, `net2`↔`net1` | 103 / 52, 110 / 56 | `fc` | +1.44, +1.46 (safe direction) |
| `vout_1`↔`voutn` | 205 / 120 | `a1000` | +0.0104 |

Direct pass/fail sweep of the binding mechanism (C injected on **both** halves):

| C per half | 0 | 1.0 fF | **1.5 fF** | 2.0 fF | 3.0 fF |
|---|---|---|---|---|---|
| `ph_max` (°) | 332.382 | 330.231 | **329.457 — S1 FAIL** | 328.777 | 327.614 |

**Hard S1 limit ≈ 1.11 fF per half; 0.47 fF at the worst passing corner.** At
≈0.05–0.1 fF/µm for min-spacing parallel metal, the entire budget is **3–6 µm of
parallel run**. This single number is the paper's best justification for why the
layout of a 250 Hz filter is not a formality.

Source: `layout/H12-pdk-cap/BRIEF.md` §1, §1.1; `brief.json` → `nets[]`, `cross_coupling[]` (18 entries)

### 1.4 Matching, hi-Z and wells

**Matching** (ΔV_T injected as a series dc gate source; the PDK `sg13_hv_*`
wrapper hard-codes `delvto=0`):

| class | devices | ΔV_GS common (nom / pvt), mV | ΔV_GS diff, mV | ΔW, % | binds | pattern required |
|---|---|---|---|---|---|---|
| **`rep_sink` ratio** | `xr3` (m=4) vs `xm9`,`xm10` | **0.35 / 0.18** | — | 0.89 | `a1000`/`fc` | **common-centroid + dummies**, one 6-unit array |
| **`bias_a`** | `xm9`, `xm10` | **0.41 / 0.20** | 152 | 2.02 | `fc` | same array |
| `rep_gmfb` ratio | `xr1` vs `xm14`,`xm15` | 0.84 / 0.40 | — | 1.91 | `fc` | common-centroid + dummies |
| `rep_bridge` ratio | `xr2` vs `xmst`,`xmstn` | 0.84 / 0.40 | — | 1.77 | `fc` | same row, same orientation, abutted |
| `gmf_b` | `xm14`, `xm15` | 0.79 / 0.40 | 8.0 / 3.4 | 4.02 | `fc` | common-centroid + dummies |
| `bridge` | `xmst`, `xmstn` | 0.79 / 0.40 | 8.1 / 3.4 | 3.79 | `a1000` | mirrored, **well-level** centroid |
| `in_b` / `gmf_a` / `in_a` | — | 34 / 97 / 48 | 33 / 64 / 108 | 37 / 14 / 89 | `fc` / `ripple` / `ph_max` | orientation match only |

Caps: `c1_b` 1.69 / 1.18 % · `c1_a` 1.82 / 0.91 % · `c2_b` 1.83 / 0.92 % ·
`c2_a` 3.47 % tolerated ΔC on one member.

The rule that dominates the floorplan: **one 6-unit nmos array**
(`xm9` + `xm10` + `xr3`×4, same 0.663 nA unit) governs the cell, and σ(V_T) at
600 µm²/unit is already ≈0.2 mV against a 0.35 mV budget — *"the layout has no
mismatch budget to spend, only gradient to avoid."* Bulk-to-source ties forbid
classical interdigitation for `xm2`/`xm5`, `xmst`/`xmstn`, `xm0`/`xm1`, `xr2`;
**well-level centroid only**.

**Hi-Z / leakage** — `net2`/`net3` carry **0.663 nA at 22.4 MΩ**, budget
**6.2 / 3.0 pA** (11.0 pA one-sided): *"no ESD or antenna diode, no pad, no extra
diffusion or well area. Minimum drain areas only; route on metal, never on
diffusion or poly straps."* Real leakage at 27 °C is sub-femtoamp (≈10⁴ of
margin) — the budget exists to forbid a **new** path, not to bound the existing
one.

**Wells** — eight distinct n-wells, **seven at signal potential**; only the `vdd`
well (`xm14`, `xm15`, `xr1`) is shareable. `xmst`'s minimum enclosing well
≈220 µm² ⇒ ≈22 fF at 0.1 fF/µm², *a quarter of `net4`'s 82.8 fF budget before any
routing*.

**MIM plate orientation — the hard pre-layout finding.** `cap_cmim` is
1.5 fF/µm²; bottom-plate density 5.2 aF/µm² bare, 35 aF/µm² over a Metal4 plane.

| MIM | nets (PLUS = top) | units | C | bottom plate on | C_bot est. | that net's budget | verdict |
|---|---|---|---|---|---|---|---|
| `xc13`/`xc17` | `net2`/`vout_1`, `net3`/`vout_2` | 2 × 40.53 µm | 4.94 pF | `vout_1`/`vout_2` | 17–115 fF | 3353 fF | OK as drawn |
| `xc19` | `vout_2`/`vout_1` | 8 × 49.42 | 29.3 pF | `vout_1` only | 102–684 fF | 6705 fF | OK but **asymmetric** — split 4+4 anti-oriented |
| **`xc1`/`xc10`** | `voutp`/**`net4`**, `voutn`/**`net1`** | 16 × 49.91 | 59.8 pF | **`net4`/`net1`** | **207–1395 fF** | **83 fF** | **FLIP — 2.5–17× over budget** |
| `xc12` | `voutn`/`voutp` | 7 × 48.45 | 24.7 pF | `voutp` only | 85–575 fF | 1801 fF | OK but **asymmetric** — split 4+3 anti-oriented |

Total MIM area 0.122 mm² = 70 % of the PDK's 174 800 µm²/chip recommendation.

**Series resistance is a don't-care for the whole cell**: max branch current
2.65 nA, so 1 MΩ of routing is 2.6 mV of IR; `vbr` and `net2` are below the
numerical floor at 1 MΩ, `vout_1`'s budget is 35 MΩ and `vdd`'s 148 MΩ.

**Symmetry / pin intent:** vertical axis at x = 0; mirror pairs
(`vinp`,`vinn`) (`net2`,`net3`) (`vout_1`,`vout_2`) (`net4`,`net1`)
(`voutp`,`voutn`) and (`xm2`,`xm5`) (`xm4`,`xm8`) (`xm9`,`xm10`)
(`xmst`,`xmstn`) (`xm0`,`xm1`) (`xm14`,`xm15`) (`xc13`,`xc17`) (`xc1`,`xc10`);
on-axis `xc19`, `xc12`, `xr1`, `xr2`, `xr3`. Pins: `vinp`/`vinn` left,
`voutp`/`voutn` right, `vbn`+`vss` bottom, `vdd` top, `vbp` unused (dangling,
kept for LVS). Keep-apart pairs: (`net2`,`net4`) (`net2`,`voutp`) (`net3`,`net1`)
(`net3`,`voutn`) (`net2`,`voutn`) (`net3`,`voutp`). No self-heating (11.9 nW
total), no EM or IR constraint anywhere.

Sources: `layout/H12-pdk-cap/BRIEF.md` §2, §3, §5, §6, §8–9; `brief.json` →
`matching[]` (13), `leakage[]` (6), `wells[]` (9), `mim_caps[]` (6),
`structure`, `dont_care`, `free_trims`

---

## 2. Outline and area, per round

| | round 1 (it01) | round 2 (it06–it08) | round 3 (it09–it13) | **round 4 (it14)** |
|---|---|---|---|---|
| outline | 230 624.28 µm² | 247 136.88 | 247 136.88 | **228 093.60 µm² = 0.2281 mm²** |
| bbox | — | (−216.84, −10.00)…(216.84, 559.86) | same | **(−216.01, −8.83)…(216.01, 519.14)** |
| dimensions | — | 433.68 × 569.86 µm | same | **432.02 × 527.97 µm** |
| aspect (h/w) | — | 1.314 | 1.314 | **1.222** |
| MIM area | 122 253 µm² | 122 253 (49.5 %) | 122 253 (49.5 %) | **122 253 (53.6 %)** |
| devices | 15 certified | 15 certified + 14 nmos + 2 pmos dummies | same | **15 certified + 6 nmos + 2 pmos dummies** |
| n-well islands | 8 | 8, all tapped, mirror-XOR 0 | 8 | **8** |

Round 4 is **−19 043.28 µm², −7.71 % vs round 3**, and **1.1 % below round 1** —
the first round smaller than the layout the review process started from. It
splits, measured:

| source | Δ area | how measured |
|---|---|---|
| `bias_dummy_rows` 1 → 0 (the owner's Q2 reversal) | **−13 790.9 µm² (−5.58 %)** | single evaluation, round-3 defaults with only this knob changed → 233 345.97 µm² (`opt/results/summary.json` → `dummy0`) |
| the 17 moved numeric knobs (campaign A-best) | **−5 252.4 µm² (−2.25 %)** | 228 093.60 − 233 345.97, the residue once the dummy rows are out |

Height falls 41.89 µm; width falls only 1.66 µm because the width is set by cap
bank B (±216.01 µm), which no device-row knob reaches. **The cell is now 53.6 %
MIM by area** — same absolute MIM, smaller cell — so the "MIM dominates" flag
(F15) gets *stronger*, not weaker, and is block-level: total capacitance is a
`design.json` decision the layout cannot touch.

Source: `layout/H12-pdk-cap/REPORT.md` §1; iteration areas in `figures/data/iteration_trail.csv`

---

## 3. Physical verification, per round

| | round 1 | round 2 | round 3 | **round 4** |
|---|---|---|---|---|
| DRC | 0 violations | 0 | 0 | **0**, no waivers |
| LVS | match | match | match | **match, 0 unmatched** |
| PEX CC | 78 C / 0 R | 78 C / 0 R | 71 C / 0 R | **69 C / 0 R** |
| PEX RC | — | — | 71 C / 8 609 R | **69 C / 6 331 R** |
| CC↔RC agreement | — | — | 0.041 Hz / 0.0003° | **0.047 Hz / 0.0003° / 0.006 dB** |
| `BOUNDS` endpoints | 35/48 DRC | 64/64 DRC | 66/66 **DRC only** | **65/66 build, 65/65 DRC, 63/65 LVS** |
| `--check-symmetry` | — | PASS | PASS | **PASS (20 layers); FAILS on it01, as it must** |

Toolchain: KLayout with **the PDK's own decks**
(`$PDK_ROOT/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py`, `sg13g2.lvs`) via
`spicexplorer_signoff.run_drc` / `run_lvs`; **kpex 0.3.12** (klayout-pex, 2.5D)
via `run_pex`. Density/fill, sealring, pads and antenna diodes are out of scope
by the approved plan.

**The three CC→RC and 78→71→69 element counts are each a story, not noise:**

- 78 → 71 was **structural**: the `lane_mid` knob moved the two internal-node
  spines from 3.8 µm apart to 9.8 µm, and the `C(net2,net3)` card **disappeared
  from the extraction entirely** (reviewer's F16: *"absent, not small"*).
- 71 → 69 is noise: the two lost cards are `C(vinn,vout_1)` and `C(vinp,vout_2)`
  at **0.4 aF each**, below kpex's halo on the smaller cell. Every other net pair
  present in round 3 is present in round 4.

**LVS reference is derived from the knobs, not retyped.** The only line that
changed round 3 → round 4:

```
-Mdumn vss vss vss vss sg13_hv_nmos w=336u l=25u
+Mdumn vss vss vss vss sg13_hv_nmos w=144u l=25u
```

— the merged dummy-nmos card, `n_n = 2·3·bias_dummy_cols +
2·(2·bias_dummy_rows)·(1 + bias_dummy_cols)` = 14 → 6 devices. That derivation is
exactly why a generator bug (a `cc12_cols` value that does not divide the m = 7
`xc12` array, silently dropping plates) surfaced as an **LVS device-count
mismatch** rather than a silent layout defect.

**A methodological finding worth its own paragraph in the paper.** Round 3
reported *"66/66 endpoints build and DRC clean"*. Round 4 re-ran the same sweep
**with LVS added** and found **two endpoints that short nets together at zero DRC
violations** — `w_m1 = 1.0` merges eleven nets into one, `ring_gap = 15.0` merges
`vout_1`/`vout_2`/`vss` — because same-layer shapes that touch simply merge and
no spacing rule fires. `w_m1 = 1.0` **also fails at round-3 defaults**: a latent
defect round 3 certified as clean. The delivered cell is unaffected (all three
knobs sit at their defaults). The designer's own conclusion: *"A gate that cannot
fail on the defect class you care about is decoration."*

A second, purely operational trap, also recorded: *"Parallel KLayout runs fake
failures."* The first pass of that sweep ran 8 DRC/LVS jobs concurrently and
reported 7 spurious DRC failures and 7 spurious LVS mismatches, **all with empty
violation lists** — truncated runs, not results. Re-run at 2 workers, all passed
and the two real mismatches reproduced. *"An empty failure is an infrastructure
failure; re-run before believing it."*

Source: `layout/H12-pdk-cap/REPORT.md` §2, §3, §4, §7, §10

---

## 4. Parasitic budget — used vs allowed (kpex CC)

"To ac ground" sums C to `0`/substrate, `vdd`, `vbn`, `vbr`, `rep_x`,
`vinp`/`vinn` — the reviewer's definition, so all four rounds compare line for
line. Budgets are `brief.json`'s.

| net | round 1 | round 2 | round 3 | **round 4** | allowed nom / pvt | ratio | one-sided Δ | allowed asym | **C between halves** | allowed diff |
|---|---|---|---|---|---|---|---|---|---|---|
| `net2` | 50.04 | 28.270 | 32.328 | **30.198** | 22.8 / 9.59 | **1.32× / 3.15×** | **−0.019** | 45.7 / 19.2 ✓ | **0.0000** | 11.4 ✓ |
| `net3` | 44.94 | 28.270 | 32.329 | **30.217** | 22.8 / 9.59 | 1.33× / 3.15× | " | " | " | " |
| `net4` | 77.30 | 67.578 | 67.338 | **67.180** | 82.8 / 34.8 | 0.81× / 1.93× | **0.102** | 166 / 69.5 ✓ | **0.0000** | 41.4 ✓ |
| `net1` | 67.27 | 67.471 | 67.249 | **67.078** | 82.8 / 34.8 | 0.81× / 1.93× | " | " | " | " |
| `vout_1` | 231.73 | 165.057 | 166.059 | **162.924** | 3350 | 0.05× | **−0.161** | 6710 ✓ | 4.5576 (r3) | 1680 ✓ |
| `vout_2` | 75.93 | 165.537 | 166.540 | **163.085** | 3350 | 0.05× | " | " | " | " |
| `voutp` | 505.50 | 459.418 | 460.060 | **463.401** | 905 / 455 | 0.51× / **1.02×** | **21.687** | 1800 / 905 ✓ | 7.4474 (r3) | 460 ✓ |
| `voutn` | 352.55 | 438.359 | 439.002 | **441.714** | 905 / 455 | 0.49× / 0.97× | " | " | " | " |
| **A ↔ B** | 0.0000 | 0.0000 | 0.0000 | **0.0000** | 0.277 / 0.116 | — | — | — | **absent, not small** | — |

Every other net: `vbn` 608.281 · `vdd` 209.600 · `vbr` 95.304 · `rep_x` 54.254 ·
`vinp`/`vinn` 33.869 fF (round 4).

**The one line still over budget is `net2`/`net3`**, at 1.32× the balanced
budget (round 3: 1.42×, round 2: 1.24×) and 3.15× the pvt budget. It is a
**disclosed, priced** over-run, not a slip: the reviewer logs it as F2
*"worse (by design, disclosed)"*, and round 4 gets back two-thirds of what the
matching fix (F17) spent, from geometry rather than by un-doing the fix.

**Where `net2`'s 30.20 fF sits, and where the 2.13 fF went** (pair by pair, same
tool, same definition):

| `net2` couples to | round 3 | **round 4** | Δ | why |
|---|---|---|---|---|
| substrate (`0`) | 26.669 | **23.917** | **−2.752** | the cell is 41.89 µm shorter ⇒ shorter Metal5 spine and TopMetal1 haul. **This is the whole story.** |
| `vbn` | 3.930 | 4.372 | +0.442 | tighter row pitches bring `xm9`'s gate bus closer; part of it is `xm9`'s own gate-to-drain, which no routing knob reaches |
| `vinp` | 1.639 | 1.821 | +0.182 | the `xm2` gate line is closer — and the what-if says this term **helps** phase (−0.064°), so it is not a cost |
| `vbr` | 0.091 | 0.089 | −0.002 | |
| **to ac ground** | **32.329** | **30.198** | **−2.130** | |
| **`net3`** | **absent** | **absent** | — | F16 held at the new `lane_mid` = 4.69 |

`net2` and `net3` differ by **19 aF** on the substrate term — kpex's own
substrate-C rounding between geometrically identical shapes — against a 45.7 fF
one-sided allowance. All 21 cross-coupling budgets pass with ≥ 99 % margin, and
no Metal1 of any signal net runs over foreign diffusion (0.000 µm² for all ten
signal nets).

Source: `layout/H12-pdk-cap/REPORT.md` §6; round-3 figures cross-checked in `REVIEW.md`

---

## 5. Pre- vs post-layout scorecard

`lab.metrics.evaluate` (op+ac+noise, `mos_tt`, 27 °C, 1.5 V) and
`lab.thd.measure`, spliced through `Design.dut_override` — **the block's own
frozen harness, unchanged**. This is the identity that makes the comparison
meaningful: the same bench definitions score the schematic and the extracted
cell.

| line | spec | pre-layout | round 1 | round 2 | round 3 | **round 4** | Δ vs pre | margin left |
|---|---|---|---|---|---|---|---|---|
| S1 `ph_max` | ≥ 330° | 332.382 | 330.732 | 331.155 | 331.160 | **331.221** | **−1.162** | 1.22° |
| S1 `a1000` | ≤ −48 dB | −49.026 | −49.263 | −49.220 | −49.222 | **−49.218** | −0.192 | 1.22 dB |
| S2 `fc` | 245–255 Hz | 249.775 | 248.275 | 248.651 | 248.639 | **248.664** | **−1.111** | 3.66 / 6.34 Hz |
| S3 `dc` | \|·\| ≤ 0.2 dB | −0.0081 | −0.0081 | −0.0081 | −0.0081 | **−0.0081** | 0.000 | 0.192 dB |
| S3 `ripple` | ≤ 0.2 dB | 0.0523 | 0.0232 | 0.0355 | 0.0347 | **0.0363** | −0.016 | 0.164 dB |
| S4 `peak` | ≤ 0.2 dB | 0.0018 | 0.0206 | 0.0132 | 0.0136 | **0.0128** | +0.011 | 0.187 dB |
| S5 `IRN` | < 40 µV | 29.199 | 29.195 | 29.1945 | 29.1942 | **29.1944** | −0.005 | 10.8 µV |
| S6 `P` | < 50 nW | 11.9125 | 11.9130 | 11.9134 | 11.9136 | **11.9136** | +0.0011 | 38.1 nW |
| S7 `THD` | ≤ −40 dB | −50.401 | −49.614 | −49.714 | −49.701 | **−49.726** | **+0.675** | 9.73 dB |
| — `HD3` | not specced | −50.605 | — | −49.912 | −49.898 | **−49.928** | +0.68 | — |
| — `HD2` | not specced | −100.19 | −88.06 | −104.22 | −97.17 | **−102.72** | — | **bench floor** |
| — `C_total` | reported | 183.779 | 183.779 | 183.779 | 183.779 | **183.779 pF** | 0.000 | layout cannot move it |

**All S1–S7 pass at nominal** (`s.violations == []`) in every round.

Group delay and the other report-only columns (from the paper pack's own
independent bench run, `figures/data/prepost_bode.json`): `gd_dc` 1.6470 →
1.6506 ms, `gd_max` 2.4703 → 2.4825 ms, `gd_fc` 2.3397 → 2.3471 ms,
`onoise` 34.2843 → 34.2425 µV, `i_core` 7.9416 → 7.9424 nA.

### 5.1 Every delta, explained

Round 4 moved **one physical thing**: the cell lost **41.89 µm of height** inside
island A, so `net2`/`net3` (and less, `net1`/`net4`, `vout_1`/`vout_2`) got
shorter spines. What-ifs on round 4's own extraction price it:

| what-if on `core_pex.sp` | `ph_max` | Δ | `fc` | reads as |
|---|---|---|---|---|
| as extracted | 331.221 | — | 248.664 | — |
| delete every `net2`/`net3` C | 331.901 | **+0.680** | 249.115 | 0.680° for 30.20 fF ⇒ **0.0225 °/fF** (round 3: 0.0229) |
| delete `net2`/`net3` → substrate only | 331.847 | +0.626 | 249.003 | **92 % of the net's cost is its own substrate C** |
| delete every `net4`/`net1` C | 331.710 | +0.489 | 248.709 | ~unchanged from round 3 |
| delete `net2`/`net3` → `vbn` | 331.333 | +0.112 | 248.726 | `xm9`'s gate-to-drain; *grew* — the bias row is closer now |
| delete every `vout_1`/`vout_2` C | 331.266 | +0.045 | 248.681 | |
| delete `net2`/`net3` → `vinp`/`vinn` | 331.156 | **−0.064** | 248.693 | still *helps*; do not remove it |
| delete every `voutp`/`voutn` C | 331.157 | −0.064 | 249.269 | |
| **delete all parasitic C** | **332.332** | **+1.111** | **249.772** | back to the pre-layout point within 0.05° — the extraction is accounted for |

**The arithmetic closes.** `net2`/`net3` lost 2.130 fF per half at 0.0225 °/fF ⇒
**+0.048° expected, +0.061° measured**; the remaining +0.013° is `net1`/`net4`
(−0.16 fF) and `vout_1`/`vout_2` (−3.3 fF) shedding their share. No delta needs a
second mechanism.

`IRN`, `P`, `dc` and `C_total` **did not move at all**: noise and power are set
by the sizing record, and layout does not touch either. That is a substantive
result for a sub-nW filter, not a null.

**Do not read HD2 as a layout property.** Its ±5 dB swing is this bench's
numerical floor: round 3 measured **−98.99 and −97.17 dB from two PEX netlists of
the same GDS** with byte-identical C cards, and the reviewer independently showed
that a **pure reordering of the parasitic C cards** moves it 5.3 dB with THD/HD3
unchanged to 0.002 dB. Round 4's −102.72 sits inside that spread.

### 5.2 The pre→post shift, drawn

`figures/prepost_bode.png` (this pack's own independent bench run, three DUTs):
pre 332.3823° / 249.7746 Hz, post-round-3 331.1595° / 248.6388 Hz, **post-round-4
331.2208° / 248.6636 Hz** — reproducing the designer's numbers to four decimals.
`figures/data/prepost_bode.json` carries the curves and the full scorecards.

**The stopband does not roll off forever, and the phase returning to 0° is real.**
Extending the plotted range to −137 dB shows the mechanism: a **transmission zero
at 3.82 kHz** (−124.6 dB pre-layout, −122.6 dB post) followed by a **direct
feed-through floor of ≈ −101 dB** (pre −101.0, post −100.8 at 30 kHz; −100.5 dB
and −0.5° of phase at 100 kHz). Past the zero the signal no longer travels
through the two biquads — it arrives through the direct high-frequency path (the
followers' own C_gs/C_gd plus capacitor feed-forward), which is **in phase**, so
the 332° of accumulated lag unwinds. Two results follow, both measured:

* **the layout moves the floor by only +0.16 dB and does not move the notch**
  (the zero holds to within the 4.7 % sweep step) — the extracted parasitics
  perturb the feed-through path far less than they perturb the poles; and
* the 3–5 kHz spike in the post−pre delta panel is **the notch region**, not a
  resonance: a fraction of a dB of movement in a −120 dB null is a large
  *relative* delta. A caption must say so, or a reviewer will read a parasitic
  resonance into it.

Source: `layout/H12-pdk-cap/REPORT.md` §5; `doc/paper/figures/data/prepost_bode.json`

---

## 6. Corners on the extracted cell

### 6.1 Cap corners with the `iref` trim (the designer's set)

| corner | pre `ph_max` | round 3 post | **round 4 post** | pre | **post** |
|---|---|---|---|---|---|
| `mos_tt` 27 °C 1.50 V | 332.38 | 331.16 | **331.22** | PASS | **PASS** |
| `mos_ss` 27 °C | 332.38 | 331.16 | **331.23** | PASS | **PASS** |
| `mos_ff` 27 °C | 332.17 | 330.96 | **331.03** | PASS | **PASS** |
| `mos_sf` 27 °C | 332.25 | 331.02 | **331.08** | PASS | **PASS** |
| `mos_fs` 27 °C | 332.44 | 331.23 | **331.29** | PASS | **PASS** |
| `mos_tt` 27 °C 1.65 V | 332.42 | 331.19 | **331.26** | PASS | **PASS** |
| `cap_typ` ×1.0 | 332.38 | 331.16 | **331.22** | PASS | **PASS** |
| `cap_bcs` ×1.0 | 330.95 | 329.69 | 329.76 | FAIL (`fc` 277 Hz) | FAIL (`fc` 276 Hz) — not an S1 corner either way |
| **`cap_bcs` ×0.9 + `iref` ×0.9** | **331.02** | **329.751** | **329.821** | **PASS** | **FAIL — S1 only** |
| `cap_wcs` ×1.0 | 333.61 | 332.43 | 332.49 | FAIL (`fc` 226 Hz) | FAIL (`fc` 226 Hz) |
| `cap_wcs` ×1.1 | 333.56 | 332.39 | **332.45** | PASS | **PASS** |

**Every corner that passed pre-layout still passes post-layout except one**, and
that one is the campaign's single open spec item: `ph_max` **329.821° vs a 330.0°
limit — 0.179° short** (round 3: 0.249°; round 2: 0.254°; round 1: 0.701°). At
that corner S1's phase certificate is the *only* violation: `fc` 249.33 Hz,
`a1000` −49.10 dB, `IRN` 30.6 µV all pass. The block owner pre-authorised
delivering with the miss documented (plan decision Q3); the reviewer's counter-note
is that *"without that approved decision this row is a blocker."*

**Why the last 0.179° is not a layout problem.** `net2`/`net3` cost 0.0225 °/fF,
so closing 0.179° needs **≈8 fF off each half**. What is left on that net is
`xm4`'s own gate poly (W 1.5 µm, **L 45 µm** — layout-invariant), `xm9`'s finger
pitch, island-A height, and `xm9`'s gate-to-drain. The residual is a **sizing**
question (an `iref` trim, a small C1/C2 re-allocation, a shorter `L` on `xm4`,
fewer `xm9` fingers). The honest update the report itself records: round 3
concluded the layout-reachable budget was spent; round 4 found **another 0.070°
in a knob nobody had priced** — *"hand analysis prices one knob at a time; the
coupling between them is what the optimizer finds."*

Source: `layout/H12-pdk-cap/REPORT.md` §5 (A7)

### 6.2 Full PVT on the extraction — measured for this pack

The repo's post-layout corner evidence stops at the set above. This pack ran the
**full schematic-side corner machinery on the it14 extraction**, paired point for
point against the schematic (`doc/paper/scripts/fig_pvt_postlayout.py`,
`lab.corners`, bias law α = 1.1, ~12 s of simulation total):

| corner set | pre-layout | **post-layout (it14 PEX)** | Δ corners |
|---|---|---|---|
| one-axis set (9) | 6/9 | **6/9** | **+0** |
| reduced screen (22) | 6/22 | **6/22** | **+0** |
| full grid (45) | 16/45 | **16/45** | **+0** |

**Zero of the 45 corners changes verdict.** The extraction shifts every corner
in the same direction — `fc` by **−1.27 Hz mean** (range −4.12 … +1.61) and
`ph_max` by **−1.16° mean** (range −3.82 … +0.10) — without moving a single
pass/fail boundary. The pre-layout column reproduces the certified sign-off
exactly (6/9, 6/22, 16/45), which is the check that the re-run is honest.

Worth stating in the paper: the tightest post-layout corner is `mos_ss` at
27 °C / 1.5 V, `fc` = **246.24 Hz** — **1.24 Hz** above the 245 Hz floor, down
from 2.36 Hz pre-layout. The operating window did not shrink in *count*, but it
did get thinner.

Data: `doc/paper/figures/data/postlayout_pvt.json`; drawn in
`figures/pvt_postlayout.png`

---

## 7. The generator — knobs and endpoint sweep

The layout of record is `gen_H12_pdk_cap.py` (sha256 `771468be…7efb3c` at round
4), **33 knobs**, `set(BOUNDS) == set(LayoutParams fields)` asserted inside every
build. `BOUNDS` is the single source of truth; `clamp()` resolves the couplings
so every endpoint is buildable.

| round | endpoint sweep result |
|---|---|
| 1 | 35/48 DRC-clean |
| 2 | 64/64 DRC-clean, 0 dead knobs |
| 3 | 66/66 build + DRC-clean, **33/33 knobs change the GDS** (independently re-verified by the reviewer with its own builds and its own DRC runs) |
| **4** | **65/66 build, 65/65 DRC-clean, 63/65 LVS-match, 0 dead knobs** — LVS added to the gate, and it found three illegal endpoints (see §3) |

**Determinism.** Round 4's sweep contains **eleven independent builds whose knob
value happens to equal the default**, and every one produced GDS sha
`1607b803d9…` — the sha stored in `iterations/it14/` and the one
`asbuilt/core_pex.sp` was extracted from. The reviewer's round-3 equivalent:
two independent rebuilds, identical sha, identical to `iterations/it13`.

**Round-4 cross-check of the "no floorplan change" claim:** the round-4 generator
built *at round-3 default values* reproduces round 3's GDS **byte-identically**
(sha `fc59cfd7ef…`). 18 defaults moved; **no knob was added or removed, no
categorical or floorplan-mode knob changed, and no device, size or multiplicity
moved.**

Source: `layout/H12-pdk-cap/REPORT.md` §0, §1, §7, §10

---

## 8. The area campaigns

Two 300-trial nevergrad campaigns (`TwoPointsDE`, seed 0, 12 workers via the
stand-alone driver's own thread pool), plus two single evaluations. Each trial is
a **full** build → KLayout DRC → LVS (reference regenerated per trial) → kpex CC →
the block's own frozen benches, then constraints → penalties → score.

### 8.1 Setup

| item | value |
|---|---|
| knobs total | 33 |
| **numeric knobs searched** | **25** — `dev_gap_x`, `axis_gap`, `lane_mid`, `row_gap`, `bias_row_gap`, `bias_dummy_cols`, `gmfb_dummy`, `well_margin`, `well_gap`, `ring_w`, `ring_gap`, `shield_w`, `cap_gap`, `cap_bank_gap`, `cap_axis_gap`, `bank_gap`, `w_m1`, `w_m2`, `w_m3`, `w_tm1`, `via_pad`, `cc19_cols`, `cc1_cols`, `cc12_cols`, `cc13_cols` |
| categorical / floorplan-mode knobs **pinned** | **8** — `bankA_order`, `cap_spine_side`, `cap_anti_orient`, `cc12_split`, `bias_dummy_rows`, `xr1_split`, `net23_strap`, `net23_spine_layer` — *"design decisions, not tuning"* (the approved plan). `--free NAME` / `--fix NAME=VALUE` move the line |
| grid | floats snap to 0.01 µm (`param_grid`) |
| objective | `area / area_ref` **+ a scaled penalty per violated constraint**, so infeasible points still rank |
| seeding | `opt.suggest(**defaults)` — the layout of record is evaluated as the baseline first; the driver **exits 2** if the baseline fails its own gates |

Constraints and their penalties:

| constraint | limit | penalty |
|---|---|---|
| S1–S7 nominal violations | 0 | `3.0 × n_violations` |
| `ph_max` | ≥ **331.10°** | `2.0 + 4.0 × (331.10 − ph_max)` |
| `max(C(net2), C(net3))` to ac gnd | ≤ **32.40 fF** | `1.0 + 0.2 × excess` |
| \|C(net2) − C(net3)\| | ≤ 0.50 fF | `1.0 + \|Δ\|` |
| C(A↔B) | ≤ **0.277 fF** (the brief's budget) | `1.0 + 4.0 × AB` |
| DRC | 0 violations | `5.0 + min(n,200)/20`, short-circuits |
| LVS | matched | `+5.0`, short-circuits |
| PEX | ok | `+5.0`, short-circuits |
| build (the generator's own symmetry / keep-apart assertions) | must not raise | fixed score 50.0 |

Note that **three of the eight constraints are budgets lifted directly from the
brief** — `ph_max`, C(`net2`), C(A↔B). The schematic-side sensitivity analysis
is literally the optimizer's feasible region.

### 8.2 Results

| campaign | search space | trials | ok | best area | Δ vs round 3 | `ph_max` | `net2` |
|---|---|---|---|---|---|---|---|
| **A** | 25 numeric knobs, modes + `bias_dummy_rows=1` fixed | 300 | 17 | 240 890.0 µm² | **−2.5 %** | 331.175 | 32.14 fF |
| **B** | A + `bias_dummy_rows` free | 300 | 39 | 243 180.9 | −1.6 % | 331.128 | 32.08 |
| single eval | round-3 defaults, `bias_dummy_rows=0` | 1 | ok | 233 345.9 | **−5.6 %** | 331.207 | 30.24 |
| **single eval** | **A-best knobs + `bias_dummy_rows=0`** | 1 | ok | **228 093.6** | **−7.7 %** | **331.221** | **30.20** |

The last row **became it14**.

### 8.3 Where 600 trials went

| status | campaign A | campaign B |
|---|---|---|
| `ok` | 17 | 39 |
| `constraint_fail` | **199** | 144 |
| `lvs_fail` | 55 | 58 |
| `drc_fail` | 17 | 24 |
| `build_fail` | 12 | 35 |
| reached a build (have an area) | 288 | 265 |

Among feasible trials: area min / median / max = 240 890 / 254 738 / 291 269 µm²
(A) and 243 181 / 249 404 / 368 536 (B); C(`net2`) range 31.920–32.388 fF (A),
31.287–32.396 (B); `ph_max` range 331.107–331.175° (A), 331.101–331.176 (B).
Trial wall time median 130.35 s (A) / 129.8 s (B), min 6.0 s (early
`build_fail`), max 194.7 s.

**The binding constraint is a parasitic budget, and it is binding hard.**
C(`net2`) is violated in **195 of A's 199 constraint failures** — **65 % of all
campaign-A trials die on the `net2` budget alone** — and 132 of B's 144. Even
relaxed to 35 fF, no explored point sits below −3.6 %: with the floorplan modes
fixed, **the knobs do not reach the white space**. Campaign A's global minimum
*built* area (238 142 µm²) is *below* its best feasible (240 890) — the sub-240 k
region exists and is infeasible.

### 8.4 What the loop found that argument had not

- **The dummy-row price.** `bias_dummy_rows = 1` costs **13 791 µm² (5.6 % of the
  cell), 0.048° of `ph_max` and 2.09 fF on `net2`/`net3`** — measured, against a
  matching benefit that is still a hand bound (*"no bench in this campaign models
  edge/interior ΔV_T"*). This is what re-opened the human decision. Campaign B
  never explored `bias_dummy_rows = 0` successfully — its four `=0` trials hit the
  symmetry assertion or LVS on other knobs — which is why B's best is worse than
  A's despite the larger space.
- **A generator bug**: `cc12_cols ≠ 7` with `cc12_split = "3|1|3"` → LVS
  mismatch, because `xc12` is an m = 7 array placed as `m // cols` rows and a
  column count that does not divide 7 silently drops units. *The campaign found
  it because its loop runs LVS on every trial; round 3's endpoint sweep was
  DRC-only and could not have.*
- **47 builds rejected by the generator's own mirror-XOR / TopVia1 half-plane
  assertion** at otherwise legal knob combinations — the guard-rail doing its
  job, though the report notes the via-layer budget may be over-tight.
- **0.070° of `ph_max` at the failing corner** that four rounds of hand analysis
  had concluded was not there. *"21 numeric knobs moving together gave more than
  any of them gave alone, and no hand analysis in rounds 1–3 proposed that
  combination."*

Sources: `layout/H12-pdk-cap/opt/results/{summary.json, README.md}`,
`opt/{flow.yaml, project_setup.yaml}`, `optimize_area.py`;
trial statistics computed from `campaign_{A,B}_trials.jsonl`; drawn in
`figures/area_campaign.png`

---

## 9. Review findings — F1…F25 and how they moved

Round 3 verdict: **PASS with notes**. Of the 21 round-2 findings, **19 are fixed
or approved-deferred; 2 remain open on substance (F1, F2); 4 are new (F22–F25)**.

Counts — severity: 3 major, 2 minor, 20 note. Verdict: **12 fixed, 10 open,
2 deferred (approved), 1 worse**. Category: symmetry 6; matching / knob / other 3
each; budget / pex 2 each; objective, well, leakage, lvs, coupling, routing 1
each. `effect.model`: 14 `hand`, 11 `what-if`.

| id | sev | category | verdict | what it is, and what measured it |
|---|---|---|---|---|
| **F1** | major | objective | **open (owner-accepted)** | S1 missed at `cap_bcs ×0.9 + iref ×0.9`: reviewer's own build→extract→bench gives **329.7509°** (round 2: 329.7458, round 1: 329.299, pre-layout 331.018 PASS). Round 4: **329.821**. Fix is design-lane |
| **F2** | major | budget | **worse (by design, disclosed)** | `net2`/`net3` at 1.42× the balanced budget (round 2: 1.24×). +4.06 fF is the F17 price (`net2` Metal1 4.971 → 29.542 µm², perimeter 44 → 232 µm). Round 4 improves it to 1.32× |
| **F3** | major | well | **deferred (approved)** | n-well/p-substrate junction C is outside every model in the flow; lumped-`Cj` what-if bound **−0.108…−0.259°**. 8 well islands, all tapped, NWell mirror-XOR exactly 0.0000 µm². Fix = platform feature `Cj(area, perimeter, Vbias)` |
| **F4** | note | knob | **FIXED** | 66/66 `BOUNDS` endpoints build DRC-clean — reviewer built and DRC'd **all 66 itself**, 33 distinct min-vs-max sha pairs. *(Round 4 overturns the "clean" part: see §3)* |
| **F5** | note | routing | **FIXED** | bank-A order keeps the `net2`/`net3` TopMetal1 haul short and exactly mirrored: bbox (−45.83, 17.83)…(−5.90, 122.74), 3 242.344 µm², perimeter 400.47, 1 polygon; `net3` is its exact mirror on all six numbers |
| **F6** | note | symmetry | **FIXED** | `net2`/`net3` and `net4`/`net1` layer-for-layer mirror images: identical area/perimeter/shape count on Activ 8.800, GatPoly 84.735, Metal1 29.542, Metal2/3/4 0.433, Metal5 22.743, TopMetal1 3 242.344. Extracted Δ(`net2`,`net3`) = −0.001 fF |
| **F7** | note | matching | **FIXED** | five identical nmos rows — every live bias unit has an identically drawn row above and below (Activ bands at y 119.14/135.04/150.94/166.84/182.74, 2 446.08 µm² each). **Re-opened as a documented, unmeasured debt by the round-4 owner reversal** |
| **F8** | note | symmetry | **FIXED** | output-pair imbalance inside budget; and the reviewer's own proof that **HD2 is bench floor**: a pure reordering of parasitic C cards moves −104.2215 → −98.9640/−99.2739 dB (5.3 dB) with THD/HD3 unchanged to 0.002 dB |
| **F9** | note | knob | **FIXED** | no dead knob: 33/33 `LayoutParams` fields change the GDS at their endpoints (reviewer's own sweep) |
| **F10** | note | knob | **FIXED** | `BOUNDS` is the single source of truth, asserted against `LayoutParams` in every build |
| **F11** | note | pex | **open** | MIM top plates are stripped before extraction (kpex marks the MIM layer `<TODO>` and crashes); `xc13`/`xc17` top plates 3 285.36 µm² each are absent. The ≤ 15 fF bound on `net2`/`net3` is **carried, not closed**; bound up to −0.39° |
| **F12** | note | leakage | **open** | `net2`/`net3` TopMetal1 → `xm4` gate antenna ratio **48 : 1** (3 242.344 µm² / 67.5 µm²), and the executed deck has no antenna rule. A diode is forbidden by the brief (6.17 pA budget) |
| **F13** | note | lvs | **open** | `vbp` is a dangling labelled pad: absent from the extracted netlist, and the deck still reports *Netlists match* — **1 of 8 declared pins unchecked**. Fix = pin-list assertion inside `signoff.lvs` |
| **F14** | note | matching | **deferred (approved)** | `xr2` drawn in one orientation only; residual 7.556 µm² of Metal1 XOR at y 234.76…242.21. 0.8 Hz of `fc` per mV |
| **F15** | note | other | **open** | MIM is 49.47 % of the cell and 69.9 % of the PDK's per-chip guidance (122 253.49 µm² in 51 units). Block-level — total C is a `design.json` decision. **Round 4 makes it 53.6 %** |
| **F16** | note | coupling | **FIXED** | `lane_mid` is a knob and **C(`net2`,`net3`) = 0.0000 fF — the element is gone from the extraction** (71 C, was 78). Metal5 spine labels at x = ±4.900 (was ±1.900). Isolated: +0.072° at the failing corner |
| **F17** | note | matching | **FIXED** | all six `rep_sink` members routed identically again: per-device Metal1 XOR **0.0324 µm² in 4 polygons** against 140.4637 µm² per device = **0.023 %** (round 2: 21.17 µm²). Cost verifies exactly: −0.0498° nominal, −0.0568° at the corner |
| **F18** | note | symmetry | **FIXED** | the symmetry guard-rail now **FAILS on the round-1 GDS it was installed to reject** — it01 fails 15 rules across 8 layers (Metal1 XOR 47.556 > 40.91; Metal5 948.78 > 104.14; TopMetal1 847.048 > 71.85; Metal3 balance 21.0888 > 4.81; …), while it08/it09/it10/it13 PASS |
| **F19** | note | symmetry | **FIXED (attribution)** | the Metal1 mirror exception correctly re-attributed to `xr2`: six XOR polygons — 2 × 8.0000 µm² (the `vbp` pad), 2 × 3.5240, 2 × 0.2540 — all inside the bridge row's n-well, none in the `gmf_b` row |
| **F20** | note | symmetry | **FIXED** | Metal4 and all five via layers now in the symmetry table with a half-plane balance rule; reviewer's mirror-XOR reproduces to 4 decimals, balance exactly 0.0000 µm² on all eight balance layers |
| **F21** | minor | other | **open** | `PLAN.md` is stale: R2.2's "within 1 %" area prediction is wrong by 7× vs round 1's 230 624 µm², and PLAN §5 lists `axis_gap = 6.0` while the layout ships 12.0 |
| **F22** | minor | symmetry | **new, open** | the F18 configuration relaxations drop the very rule that catches F6 below F6's own magnitude in two knob settings (Metal3 balance budget 4.814 → 100.000 µm² at `cap_spine_side="left"`). it01 still FAILs overall everywhere (15 rules default → 10/6/13 singly relaxed → 4 all stacked): **exceptions, not holes** |
| **F23** | note | other | **new, open** | `scorecard_post.json` says `all_pass: true` while recording an S1 corner violation eight keys above. Fix: rename to `all_pass_nominal`, or add `corner_pass: false` |
| **F24** | note | pex | **new, open** | **the RC cross-check quotes a precision finer than kpex's own mesh repeatability.** Three CC runs are byte-deterministic; two RC runs differ in **17 221 lines** of sub-node naming with identical C and device cards, and three RC meshes give `fc` = 248.6366 / 248.6763 / 248.6833 Hz — a **0.047 Hz spread, larger than the 0.041 Hz CC↔RC delta the report quoted as its evidence** |
| **F25** | note | budget | **new, open** | the between-halves budget column is populated for two of four differential pairs. Measured C(`vout_1`,`vout_2`) = 4.5576 fF and C(`voutp`,`voutn`) = 7.4474 fF — pass with 99.7 % / 98.4 % margin, but printed as `—` |

**Reviewer↔designer scorecard agreement, round 3:** every one of 14 metrics
matched to the last printed digit (`fc` 248.6388, `ph_max` 331.1595,
`a1000` −49.2221, `ripple` 0.0347, `peak` 0.0136, `dc` −0.0081, `irn` 29.1942,
`p_core` 11.9136, `thd` −49.7008, `hd3` −49.8985, `hd2` −97.1706, corner
329.7509, `rc_ph_max` 331.1592) — **except `rc_fc_hz`, 248.6793 vs 248.6833**,
which is precisely the non-determinism F24 identifies.

Round-3 what-if attribution: the reviewer reproduced **all seven** of the
designer's what-ifs to four decimals.

Sources: `layout/H12-pdk-cap/REVIEW.md`, `REVIEW.yaml`; crops in `review_crops/`
(20 of 25 findings; F4/F9/F10/F23/F24 have no drawable anchor by design)

---

## 10. Round-by-round headline

| | pre-layout | round 1 | round 2 | round 3 | **round 4** |
|---|---|---|---|---|---|
| area (µm²) | — | 230 624 | 247 137 | 247 137 | **228 094** |
| `ph_max` nominal | 332.382 | 330.732 | 331.155 | 331.160 | **331.221** |
| `ph_max` @ `cap_bcs` ×0.9 / `iref` ×0.9 | 331.018 **PASS** | 329.299 | 329.746 | 329.751 | **329.821 FAIL** (0.179 short) |
| C(`net2`) / C(`net3`) (fF) | — | 50.04 / 44.94 | 28.27 / 28.27 | 32.33 / 32.33 | **30.20 / 30.22** |
| C(`net2`,`net3`) differential | — | 0 | 1.3792 | **0.0000** | **0.0000** |
| `bias_dummy_rows` | — | 0 | **1** | 1 | **0** (owner reversal) |
| DRC / LVS | — | 0 / match | 0 / match | 0 / match | **0 / match** |
| PEX CC | — | 78 C | 78 C | 71 C | **69 C** |
| THD / IRN / P | −50.40 / 29.199 / 11.913 | −49.61 / 29.195 / 11.913 | −49.71 / 29.195 / 11.913 | −49.70 / 29.194 / 11.914 | **−49.73 / 29.194 / 11.914** |
| review verdict | — | **FAIL** (`cap_bcs` corner) | 21 findings | **PASS with notes**, 25 findings | not yet reviewed |

Source: `layout/H12-pdk-cap/REPORT.md` §0

---

## 11. Layout-side gaps

Full list with commands and effort in `README.md` §5. The layout-specific ones:

1. **G6 is closed by this pack** — full PVT on the extraction is now measured
   (§6.2). What remains open is post-layout PVT with the **cap** corners crossed
   into the process/temperature/supply grid.
2. **No post-layout THD corners or THD MC** (G7). Post-layout S7 is one number
   per round.
3. **RC is not run-to-run deterministic** and the report's agreement claim is
   finer than the extractor's repeatability (G8, F24).
4. **MIM top plates are stripped before extraction**; the ≤ 15 fF bound is
   carried (G9, F11).
5. **n-well/substrate junction C is unmodelled** everywhere in the flow
   (G10, F3), bound −0.108…−0.259°.
6. **One declared pin (`vbp`) is not LVS-checked** (G11, F13).
7. **Round 4 has not been independently reviewed.** The review of record is
   round 3. A paper should say which round each layout number comes from — this
   file does.
8. **A pre-layout corner discrepancy to reconcile** (new, found while assembling
   this pack): `REPORT.md` §5's A7 table gives pre-layout `ph_max` = **237.04°**
   at `mos_tt`/−40 °C and **222.31°** at +125 °C, while the certified
   `PRELAYOUT.md` and this pack's independent re-run both give **251.7°** and
   **256.0°** at the same two corners. The post-layout columns are
   self-consistent; it is the *pre-layout reference column* that disagrees. Both
   are in the repo — reconcile before quoting either.
