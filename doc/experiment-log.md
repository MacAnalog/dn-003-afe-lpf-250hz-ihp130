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
| `000-reference-baseline` | expert topology ported and re-sized to spec; both input followers p-type; one ideal reference current into a real n/p mirror | — | **CLOSED — certified reference**; this is the yardstick every candidate is scored against | **50.18 µV** | **98.01 pF** |
| [`020-novel-topologies`](../experiments/020-novel-topologies/) | port the three signed-off candidate topologies: branch stacking, the gm_f merge, and the merge under a minimum-power ruling | carried forward: `gmc-compact`+`tian2023`, `ssf-33mhz` | **CLOSED — CONFIRMED. Three cells, 8/8 spec lines PASS on all three.** 020A (stacking alone) 32.83 µV / 28.95 nW / 747.8 pF / THD −43.51; **020B (+merge) 34.14 µV / 9.70 nW / 314.6 pF / THD −49.83**; 020C (min power) 34.45 µV / 8.12 nW / 260.9 pF / THD −41.42. Two implementation choices did NOT port and were re-realised on measurement: the n-type input follower (no isolated NMOS ⇒ dc gain exactly 1/n, −3.11 dB) and the rail-tied bridge gate (forced the bridge into triode at 46 mV, gm/gds 1). 020A vs 020B isolates the merge: −66 % power, −58 % capacitance and +6.3 dB THD for +1.31 µV of noise | **32.83 µV** (020A) | 260.9–747.8 pF |

| [`021-publication-cell`](../experiments/021-publication-cell/) | repair the passband **shape** (monotone, maximally flat) without giving back the margins, then certify one cell on all of S1–S8 with corner + mismatch yield | `gmc-compact`+`tian2023` (branch stacking), `fvf-2nd` (floating differential cap) — each re-measured **here** by its own equal-shape A/B | **CLOSED — CONFIRMED. `021-final` passes all of S1–S8 at nominal**: fc 249.87, dc −0.0078, ripple 0.0557, peak +0.0000, **mono 0.0000**, @1 kHz −49.60, ph_max 333.29, **IRN 30.71 µV**, **6.01 nW**, **THD −42.22**, C 150.6 pF; mismatch all-pass **78 %** (100 samples), σ(fc) 3.32 Hz vs the reference's 13.99. S8 measured here: stacking −18.1 % IRN / −67.5 % power at **equal capacitance**; floating diff cap −45.1 % drawn farads for a 0.00002 dB response difference. **NOT corner-robust (1/22) and NO droop margin (VDD_min 1.50 V vs the reference's 1.35)** — the branch-stacked ladder is threshold-referenced, so its current moves exponentially with process and supply. Two harness defects found: `ph_max_deg` scored a **non-contiguous** band and turned a 320.7° S1 FAIL into a 368.6° PASS (fixed, ideal 4-pole still 350.53°); and the frozen reference does **not** meet S3 flatness when measured densely (ripple 0.2512) **A SECOND certified cell resolves the common-mode constraint**: the all-p cascade shifts CM up 2×|V_SG|, so vicm was stuck at 0.20 V; width buys only ~92 mV/decade and the ~30× needed converted 47 pF of MIM into non-linear GATE capacitance (THD −42→−30 dB). `sg13_lv_pmos` attacks V_th instead: 289/299 mV less shift per stage = **588 mV** of CM headroom (lv_nmos stays closed — it carries 1.6–5.1 nA at Vgs = 0). Stacked + lv reaches vicm 0.65 V (the bridge then binds); dropping to the unstacked topology reaches **vicm = 0.75 V = VDD/2** with 365 mV of |Vds| to spare. `021-vdd2-final`: all nine lines, IRN 34.85 µV, 24.01 nW, C 245.0 pF, THD −44.64, ph 341.83, **MC 82 %**, **VDD_min 1.25 V (0.25 V margin)**, 6/22 corners — i.e. it FIXES the droop failure. Mismatch there is a bias-device problem: growing ONLY the bias devices (gates on quiet rails) took yield 12 → 82 % for 3.2° of phase, where growing all devices cost 21° and failed S1 **Best cell `021-lv-final`** (stacked + lv follower, vicm 0.65 V, bias-area x9): all nine lines, **IRN 28.54 µV**, 6.46 nW, C 164.0 pF, THD −42.39, ph 332.83, mono 0.0000, **MC 84 %** — supersedes 021-final outright. Still **no droop margin** (VDD_min 1.50 V, 1/22 corners) **THD PROFILE CHANGES THE RECOMMENDATION**: S7's single 50 Hz point hides a 23 dB spread. At 175 mVpp across the passband the reference runs −48.4/−43.96/−29.8 dB at 50/100/200 Hz; `021-vdd2-final` tracks it (−44.6/−40.1/−28.1) while `021-lv-final` collapses (−42.4/**−20.9**/−21.2). Degradation toward fc is a family property (internal node = bandpass tap) but the stacked cell's extra 19 dB is a defect of stacking — one shared ladder current cannot serve both taps. **`021-vdd2-final` is therefore the recommended cell**: its S8 gap is closable, a 23 dB in-band linearity gap is structural **`022-reuse-final` — the original topology made to work.** Bridge and current reuse intact, device type + size only, 42 connections byte-identical: all nine lines, **IRN 28.07 µV**, **THD −56.46 dB** (beats the reference's −48.37), ph 341.42, 14.45 nW, 366.3 pF, **MC 95 %**, σ(fc) 2.42 Hz — best in the repo on every spec axis, and it keeps S8. Key structural finding: the ladder pins |V_SG|(gmf_b)+|V_SG|(bridge) = VDD−vbn, so **sizing cannot move the inversion level** (gm/ID stayed 24.5 while current went 2.15→55.9 nA over 100× width); only V_th can, and only a MIXED pair works — lv alone needs |Vds| ≈ V_ov 0.39 V that the 5-device ladder cannot give (triode). **Proven impossible within the constraint:** ±2 % fc over a ±10 % rail needs the branch current within ±4 %, but dI/I = dVDD/(2·n·U_T) would need a ~1.9 V/e-fold device slope vs 0.04–0.2 V real. Supply rejection needs added components | **28.07 µV** | 366.3 pF |
| [`023-replica-bias`](../experiments/023-replica-bias/) | make the branch-stacked cell PVT-tolerant and raise its yield: one shared 3-device **replica** of gmf_b + bridge generates the bridge-gate rail so the ladder current is mirror-referenced (topology `d`), then headroom re-centred (lv in_a, narrow hv in_b/gmf_b, vicm 0.40) and caps re-fitted | carried forward: `gmc-compact`+`tian2023` (stacking), `fvf-2nd` (floating cap); replica bias is textbook, not claimed as S8 | **IN PROGRESS.** Process alone at nominal V/T moved the sign-off cells' fc 13.6→524 Hz (A) / 28→398 (E) vs the reference's 247.8–252.8 — the "supply limitation" was process too. Replica: E fc span 14×→1.13× (I_L 3.03 vs sink 3.04 nA). `B1` (B-balanced + replica m=3 + headroom): **every spec line at all 4 process corners and both rails** (fc 248.0–250.6 / 249.1–250.1), 45-grid 1/22 → **12/45**, **20/45 with a PTAT reference** (reference 0/45); THD −35.8 (S7 fail: the flat cap family sits at −36…−38 — S7 follows the inversion level of gmf_a: 1/45 µm gives −48 but its +70 mV V_GS spends the 1.35 V rail); MC 49 % (σ 7.5 Hz) → 61 % with bias/replica area. Headroom identity found: top window = min(V_SG(gmf_b), V_SG(in_b)) − 2·Vds_min, drifts 3δ with T ⇒ merged ladder holds ~0–70 °C at 1.5 V, not the industrial range | 30.8 µV (B1) | 126 pF |

---

## 000 — the certified reference baseline (CLOSED)

Frozen in `decks/reference/` (`lpf_core.sp`, `lpf_tb.sp`, `design.json`,
`build-sheet.md`). It plays the role the originating campaign's reference
design played: **every candidate is scored against it, in the same batch, with
the same deck builder.**

| metric | measured | spec line |
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

Two properties of the measurement worth keeping in mind before quoting it:

- **−48.43 dB at 1 kHz against a 4th-order Butterworth arithmetic of −48.16 dB**
  — the shape is Butterworth to within 0.27 dB, so the S1 companion is not
  slack: there is 0.43 dB between the reference and the box, and any technique
  that trades stopband away will hit it first.
- **ph_max 346.43° against a 330° box** — 16.4° of margin. A single forward-path
  LHP zero caps the achievable lag well below 330°, so `ph_max` is the metric
  that catches an order defect a magnitude-only scorecard would pass.
- **Bias:** one ideal reference current into a *real* n/p mirror; every bias
  device is an integer multiple of that unit (per side, 2 units at each biquad
  output ⇒ 8 nA total). The reference sits ahead of the core supply probe, so
  it is excluded from S6 by construction, not by subtraction.

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

**Open in 020:** the transferable-learning write-up
(`doc/journal/nmos-bulk-tie.md`, `doc/journal/all-p-followers.md`), and a full
4th-order scorecard of the alternating structure as the negative control (so
the decision is on the record as a measurement, not as an argument).

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
5. **S7 (THD) has never been measured on this reference.** The scorecard rows
   above are ac + noise only. Run it before any technique that touches swing,
   caps or bias — and re-measure **HD2** while there, because "THD ≈ HD3" is a
   carried-forward property of a different differential layout, not a law
   (`doc/prior-findings.md` §6).
6. **Corners and mismatch.** Five MOS corner sections exist (`mos_tt/ss/ff/sf/fs`).
   The mismatch lane does not exist yet; when it is built, the **first** action
   is to prove the samples actually differ — a dead mismatch lane returns
   bit-identical samples and every yield number it prints is a lie
   (`doc/prior-findings.md` §5).

**Ruled out, deliberately not queued:** see `doc/prior-findings.md` §3 — but
note that list is carried forward from a different technology and a 1 V rail.
Anything whose stated blocker was headroom is **re-opened here at 1.5 V**, and
anything whose blocker was bulk-tied-to-source is re-opened because this
process cannot tie an n-channel bulk to its source at all.
