# Experiment log

**KIND: TODO/log.** One line per experiment, **newest last**. Details live in
each experiment's `README.md`; keep this table honest the moment a verdict
lands. Every `experiments/NNN-*` directory must appear here.

Goal: **IRN(0.5–200 Hz) < 40 µVrms** from the certified reference baseline's
**49.98 µVrms** (−20.0 %), combining techniques from **≥ 2 papers** in `pdf/`,
while holding two true biquads, 250 Hz ±2 %, |dc| ≤ 0.2 dB, peaking ≤ 0.2 dB,
THD ≤ −40 dB at 175 mVpp / 50 Hz, and filter-core power < 50 nW.

| # | technique | paper(s) | verdict | IRN 0.5–200 Hz | C total |
|---|---|---|---|---|---|
| `000-reference-baseline` | expert topology ported and re-sized to spec; both input followers p-type; one ideal reference current into a real n/p mirror | — | **CLOSED — certified reference**; the yardstick every candidate is scored against | **50.18 µV** (10 pts/dec; **49.98 µV** re-certified at 50 pts/dec) | **98.01 pF** |
| [`020-novel-topologies`](../experiments/020-novel-topologies/) | port the three signed-off candidate topologies: branch stacking, the gm_f merge, and the merge under a minimum-power ruling | carried forward: `gmc-compact`+`tian2023`, `ssf-33mhz` | **CLOSED — CONFIRMED.** Three cells, 8/8 spec lines PASS on all three (§020) | **32.83 µV** (020A) | 260.9–747.8 pF |
| [`021-publication-cell`](../experiments/021-publication-cell/) | repair the passband **shape** (monotone, maximally flat) without giving back the margins, then certify one cell on all of S1–S8 with corner + mismatch yield | `gmc-compact`+`tian2023` (branch stacking), `fvf-2nd` (floating differential cap) — each re-measured **here** by its own equal-shape A/B | **CLOSED — CONFIRMED.** `022-reuse-final` is the deliverable: all nine lines, best in the repo on every spec axis. Supply rejection proven impossible within the constraint (§021) | **28.07 µV** | 366.3 pF |
| [`023-replica-bias`](../experiments/023-replica-bias/) | make the branch-stacked cell PVT-tolerant and raise its yield: one shared 3-device **replica** of gmf_b + bridge generates the bridge-gate rail so the ladder current is mirror-referenced (topology `d`), then headroom re-centred and caps re-fitted; second pass: **all-hv** (no lv at 1.5 V) with every S1–S8 line at nominal | carried forward: `gmc-compact`+`tian2023` (stacking), `fvf-2nd` (floating cap); replica bias is textbook, not claimed as S8 | **CLOSED — CONFIRMED on process/supply, FALSIFIED on temperature.** Two all-hv cells delivered to `signoff/post-pvt/` (§023) | **29.2 µV** (H12-robust) | 183 pF |

---

## 000 — the certified reference baseline (CLOSED)

Frozen in `decks/reference/` (`lpf_core.sp`, `lpf_tb.sp`, `design.json`,
`build-sheet.md`). It plays the role the originating campaign's reference
design played: **every candidate is scored against it, in the same batch, with
the same deck builder.**

> **Grid caveat.** The table below is the **2026-08-11 certification at 10
> pts/decade**. The reference was re-certified on 2026-08-12 at 50 pts/decade
> (`lab.config.AC_DEC`), which moved three of its cells without the circuit
> moving — IRN 50.18 → **49.98 µVrms**, fc 250.00 → **250.37 Hz**, ph_max
> 346.43 → **346.74°** — and added one the coarse grid had straddled:
> `ripple_db` resolved at **0.2512 dB, an S3 flatness FAIL**, on a row this
> table never carried. The canonical numbers are
> `decks/reference/scorecard.json`; quote those, not these.

| metric | measured (10 pts/dec) | spec line |
|---|---|---|
| fc | **250.00 Hz** | S2: 250 Hz ±2 % (245–255) |
| passband gain (dc) | **−0.0047 dB** | S3: \|dc\| ≤ 0.2 dB |
| peaking | **0.023 dB** | S4: ≤ 0.2 dB |
| \|H\| at 1 kHz | **−48.43 dB** | S1 companion: ≤ −48 dB |
| ph_max (S1 order certificate) | **346.43°** | S1: ≥ 330° |
| **IRN 0.5–200 Hz** | **50.18 µVrms** | S5 goal: < 40 µV — **the number to beat** |
| core current | **8.04 nA** | — |
| core power | **12.07 nW** @ 1.5 V | S6: < 50 nW (4× headroom) |
| total drawn C | **98.01 pF** | reported, never specced |
| device count | 16 transistors + 6 capacitors | — |

Capacitors (pF): `c1_a 29.468` · `c2_a 6.221` · `c1_b 11.453` · `c2_b 9.946`.

Three properties of the measurement worth keeping in mind before quoting it:

- **The stopband is not slack.** −48.43 dB at 1 kHz against a 4th-order
  Butterworth arithmetic of −48.16 dB — the shape is Butterworth to within
  0.27 dB, leaving 0.43 dB between the reference and the box. Any technique that
  trades stopband away hits this line first.
- **ph_max has 16.4° of margin** (346.43° against a 330° box). A single
  forward-path LHP zero caps the achievable lag well below 330°, so `ph_max` is
  the metric that catches an order defect a magnitude-only scorecard would pass.
- **The bias reference is excluded by construction, not by subtraction.** One
  ideal reference current into a *real* n/p mirror; every bias device is an
  integer multiple of that unit (per side, 2 units at each biquad output ⇒ 8 nA
  total). The reference sits ahead of the core supply probe.

## 020 — topology port: all-p input followers (IN PROGRESS)

The one structural change against the originating design, and it is forced by
the process, not chosen.

SG13G2 has **no deep-n-well / isolated NMOS**, so an n-channel device's bulk is
the shared p-substrate and cannot follow its source. In weak inversion a
gate-driven source follower with its bulk at the rail has dc gain exactly `1/n`
(`gmb = (n−1)·gm`), and n = 1.38 for these devices (`doc/pdk-notes.md` §2.1).

Measured here on the alternating n/p structure the originating design used:

| stage | input follower | bulk | measured dc gain |
|---|---|---|---|
| A | n-type | shared p-substrate (forced) | **−2.328 dB** |
| B | p-type | its own source | **−0.003 dB** |

The n-stage alone overruns S3 (|dc| ≤ 0.2 dB) by **more than 10×**, and **no
re-sizing recovers it** — `1/n` is set by the process. Making both stages
p-type restores exact unity gain and preserves the **self-referenced gain** the
follower family's mismatch yield depends on (`doc/prior-findings.md` §4). Cost:
the common mode climbs one |Vgs| per stage instead of cancelling, absorbed by
placing the input CM at 0.25 V so the output lands at ~1.25 V mid-supply.

### The three ported cells (CLOSED 2026-08-11 — CONFIRMED, 8/8 spec lines each)

| cell | technique | IRN (µV) | power (nW) | C total (pF) | THD (dB) |
|---|---|---|---|---|---|
| 020A | stacking alone | **32.83** | 28.95 | 747.8 | −43.51 |
| **020B** | **+ gm_f merge** | 34.14 | **9.70** | **314.6** | **−49.83** |
| 020C | merge, minimum power | 34.45 | 8.12 | 260.9 | −41.42 |

- **020A vs 020B isolates the merge:** −66 % power, −58 % capacitance and
  +6.3 dB THD for +1.31 µV of noise.
- **Two implementation choices did NOT port** and were re-realised on
  measurement: the n-type input follower (no isolated NMOS ⇒ dc gain exactly
  1/n, **−3.11 dB**) and the rail-tied bridge gate (forced the bridge into
  triode at **46 mV**, gm/gds 1).

**Open in 020:** the transferable-learning write-up
(`doc/journal/nmos-bulk-tie.md`, `doc/journal/all-p-followers.md`), and a full
4th-order scorecard of the alternating structure as the negative control (so
the decision is on the record as a measurement, not as an argument).

## 021 — publication cell (CLOSED — CONFIRMED)

`022-reuse-final` is the deliverable. Six findings, in the order they changed
what to search for.

**`021-final` passes all of S1–S8 at nominal:** fc 249.87, dc −0.0078, ripple
0.0557, peak +0.0000, **mono 0.0000**, @1 kHz −49.60, ph_max 333.29,
**IRN 30.71 µV**, **6.01 nW**, **THD −42.22**, C 150.6 pF; mismatch scored-box
(S1–S6) yield **78 %** (100 samples), σ(fc) 3.32 Hz against the reference's 13.99. S8 measured
here: stacking −18.1 % IRN / −67.5 % power at **equal capacitance**; the
floating differential cap −45.1 % drawn farads for a 0.00002 dB response
difference. It is **NOT corner-robust (1/22)** and has **NO droop margin**
(VDD_min 1.50 V against the reference's 1.35) — the branch-stacked ladder is
threshold-referenced, so its current moves exponentially with process and
supply.

**Two harness defects found.** `ph_max_deg` scored a **non-contiguous** band and
turned a 320.7° S1 FAIL into a 368.6° PASS (fixed; an ideal 4-pole still scores
350.53°). And the frozen reference does **not** meet S3 flatness when measured
densely (ripple 0.2512).

**The common-mode constraint, resolved by a second certified cell.** The all-p
cascade shifts CM up 2×|V_SG|, pinning vicm at 0.20 V. Width buys only
~92 mV/decade, and the ~30× needed converted 47 pF of MIM into non-linear
**gate** capacitance (THD −42 → −30 dB). `sg13_lv_pmos` attacks V_th instead:
289/299 mV less shift per stage = **588 mV** of CM headroom (lv_nmos stays
closed — it carries 1.6–5.1 nA at Vgs = 0). Stacked + lv reaches vicm 0.65 V
(the bridge then binds); dropping to the unstacked topology reaches
**vicm = 0.75 V = VDD/2** with 365 mV of |Vds| to spare.

**Mismatch is a bias-device problem.** Growing ONLY the bias devices (gates on
quiet rails) took yield 12 → 82 % for 3.2° of phase, where growing all devices
cost 21° and failed S1.

| cell | all nine lines | IRN (µV) | power (nW) | C (pF) | THD (dB) | ph_max (°) | mismatch | droop / corners |
|---|---|---|---|---|---|---|---|---|
| `021-final` | yes | 30.71 | 6.01 | 150.6 | −42.22 | 333.29 | 78 % | VDD_min 1.50 V, 1/22 |
| `021-vdd2-final` (unstacked, VDD/2) | yes | 34.85 | 24.01 | 245.0 | −44.64 | 341.83 | **82 %** | **VDD_min 1.25 V (0.25 V margin)**, 6/22 — it FIXES the droop failure |
| `021-lv-final` (stacked + lv follower, vicm 0.65 V, bias-area ×9) | yes | **28.54** | 6.46 | 164.0 | −42.39 | 332.83 | 84 % | VDD_min 1.50 V, 1/22 — supersedes `021-final` outright |
| **`022-reuse-final`** | yes | **28.07** | 14.45 | 366.3 | **−56.46** (beats the reference's −48.37) | 341.42 | **95 %**, σ(fc) 2.42 Hz | VDD_min 1.50 V, 1/22 — the limitation it does **not** fix (`signoff/pre-pvt/scorecard.json` `yield`, on the layout-legalized twin) |

`021-lv-final` posts mono 0.0000.

**The THD profile changed the recommendation.** S7's single 50 Hz point hides a
23 dB spread. At 175 mVpp across the passband the reference runs
−48.4/−43.96/−29.8 dB at 50/100/200 Hz; `021-vdd2-final` tracks it
(−44.6/−40.1/−28.1) while `021-lv-final` collapses (−42.4/**−20.9**/−21.2).
Degradation toward fc is a family property (the internal node is a bandpass tap)
but the stacked cell's extra 19 dB is a defect of stacking — one shared ladder
current cannot serve both taps. That made `021-vdd2-final` the recommended cell
(its S8 gap is closable; a 23 dB in-band linearity gap is structural) until
`022-reuse-final` landed.

**`022-reuse-final` — the original topology made to work.** Bridge and current
reuse intact, device type + size only, 42 connections byte-identical; best in
the repo on every spec axis, and it keeps S8. Two structural findings came out
of it:

- **Sizing cannot move the inversion level.** The ladder pins
  |V_SG|(gmf_b) + |V_SG|(bridge) = VDD − vbn, so gm/ID stayed **24.5** while the
  current went 2.15 → 55.9 nA over 100× width. Only V_th can move it, and only
  a MIXED flavour pair works — lv alone needs |Vds| ≈ V_ov 0.39 V that the
  5-device ladder cannot give (triode).
- **Supply rejection is proven impossible within the constraint.** fc within
  ±2 % over a ±10 % rail needs the branch current within ±4 %, but
  `dI/I = dVDD/(2·n·U_T)` would need a ~1.9 V/e-fold device slope against
  0.04–0.2 V for real MOS. It needs added components.

## 023 — replica bias (CLOSED — CONFIRMED on process/supply, FALSIFIED on temperature)

Two all-hv cells delivered to `signoff/post-pvt/`.

- **Process was the bigger half of the "supply limitation".** Process alone at
  nominal V/T moved the sign-off cells' fc **13.6 → 524 Hz** against the
  reference's 247.8–252.8. The replica cut the fc span from **14×** to
  **1.01–1.02×** on every cell built.
- **The headroom identity.** Top window = `min(V_SG(gmf_b), V_SG(in_b)) −
  2·Vds_min`; budget `VDD ≥ V_GS(gmf_a) + max V_SG + 2m`. The window drifts
  ~1.5 mV/K against a fixed vicm, and with an lv `in_a` that device has 29 mV of
  |V_SG| left at 125 °C ⇒ **−40…+125 °C is unreachable by any sizing at 1.5 V**.
  α ≈ 1.1 (constant-gm class) flattens fc to 248–250 Hz over 110 K.
- **THD follows gmf_a's inversion level and nothing else** — bridge inversion is
  worth −1 dB, and a wider gmf_b costs the S1 phase.

| cell | sizing | all nine lines | IRN (µV) | power (nW) | C (pF) | THD (dB) | ph_max (°) | MC | PVT held |
|---|---|---|---|---|---|---|---|---|---|
| **`H12-robust`** | all-hv, gmf_a 1.5/45, gmf_b 12/31, in_b 4/15, m = 4, vicm 0.24, bias area ×9/×6 | yes | **29.2** | **11.9** | 183 | −50.8 | 332.1 | **83 %** | all 4 process corners, 1.40–1.65 V, 0…+70 °C (α 1.1) |
| `H5-lean` | — | yes | 30.1 | 8.9 | 140 | −49.0 | 330.8 | 55 % | 1.40–1.65 V, −20…+55 °C |
| `B1-y2` (lv `in_a`) | — | **S7 fail** | — | — | — | — | — | — | −40…+70 °C, 1.35–1.65 V |
| `E3-y0` (lv `in_a`) | — | — | — | — | — | −40.7 | — | — | −20…+70 °C |

The two lv-`in_a` cells are kept in the experiment as the trade record.
**Open:** the schematic gate for topology `d`.

---

## Queue — what is open

Ordered by expected value per simulation, not by number.

1. **Where is the noise?** A per-device noise breakdown of the reference
   baseline, integrated over 0.5–200 Hz, plus the thermal/flicker split. The
   originating campaign found 61.7 % of noise *power* in the eight bias
   sources and only 5.3 % in flicker — **both numbers are technology-bound and
   must be re-measured here before any technique is chosen**
   (`doc/prior-findings.md` §2). Until this exists, every candidate technique
   is aimed blind.
2. **DONE (021 §4.3).** The technique-free control curve. The I–C homothety (scale every device
   multiplier *and* every capacitor by k) predicts `IRN ∝ 1/√k` exactly, at
   invariant fc/Q/dc/THD, with power ∝ k. At 12.07 nW against a 50 nW box
   there is **k ≈ 4 of headroom**, which alone would put IRN at ~25 µV. This
   must be measured and published as the control **before** any technique is
   credited — a technique's result is its distance from this curve, not its
   distance from the baseline.
   **Measured in 021 §4.3:** fc, `mono_db`, a1k and ph_max are
   flat in k and IRN tracks 1/√k to within 0.2 %, so the law holds — but **THD
   does not**, drifting 2.1 dB over 3× and closing the passing window at
   k ≈ 1.6. Any k-scaling claim must carry its own THD measurement.
3. **Cap/Q re-allocation control.** Silicon cost per biquad is `2·C1 + C2`, so
   the high-Q pole pair belongs on the biquad with the larger `gm_i`. Pure
   re-allocation, no circuit change. Must be run as a control for every
   experiment, and — open ruling — **does re-allocation ∘ homothety count
   toward the "≥ 2 papers" requirement?** Settle this before a candidate is
   delivered, not after.
4. **Bias-source degeneration with a real resistor** (`rhigh`). Only a genuine
   resistor removes a subthreshold source's shot noise; `R > 2·V_T/I` at 1 nA
   is tens of MΩ, so this is an area question as much as a noise one.
5. **HD2 on this reference.** S7 is measured (−48.37 dB at the spec point,
   HD3-dominated) but "THD ≈ HD3" is a carried-forward property of a different
   differential layout, not a law (`doc/prior-findings.md` §6). Re-measure HD2
   here, and re-run S7 after anything that touches swing, caps or bias.
6. **Corners and mismatch.** Five MOS corner sections exist (`mos_tt/ss/ff/sf/fs`).
   The mismatch lane's **first** action is to prove the samples actually differ —
   a dead mismatch lane returns bit-identical samples and every yield number it
   prints is a lie (`doc/prior-findings.md` §5).

**Ruled out, deliberately not queued:** see `doc/prior-findings.md` §3 — but
note that list is carried forward from a different technology and a 1 V rail.
Anything whose stated blocker was headroom is **re-opened here at 1.5 V**, and
anything whose blocker was bulk-tied-to-source is re-opened because this
process cannot tie an n-channel bulk to its source at all.
