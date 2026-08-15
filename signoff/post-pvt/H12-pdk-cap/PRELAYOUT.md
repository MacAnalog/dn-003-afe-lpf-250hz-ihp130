# H12-pdk-cap — pre-layout sign-off report

**KIND: SIGN-OFF (per-cell report).** Everything measured on the cell of record
(`design.json`, `asbuilt/core.sp`, PDK MIM capacitors), through the frozen
definitions in `lab.metrics` / `lab.thd` / `lab.corners` / `lab.mc`. Raw
results: `experiments/023-replica-bias/H12-pdk-cap{.json,.robust.a1p1.json,.prelayout.json}`,
`tsw_H12-pdk-cap_a1p1_1p5.json`, `vsw_H12-pdk-cap.json`. Bias law for every
temperature point: `LPF_BIAS_ALPHA=1.1` (constant-gm-class reference model);
27 °C rows are independent of it.

## 1. Nominal scorecard (27 °C, 1.5 V, mos_tt, cap_typ) — all S1–S8 PASS

| fc Hz | dc dB | ripple dB | peak dB | |H|@1 kHz dB | ph_max ° | IRN µV | P nW | C pF | THD dB (S7) |
|---|---|---|---|---|---|---|---|---|---|
| 249.77 | -0.0081 | 0.0523 | +0.0018 | -49.03 | 332.38 | 29.20 | 11.91 | 183.8 | **-50.40** |

Group delay τ(0) / τ_max = 1.647 / 2.470 ms (report-only). Both
identity gates PASS (`lpf_core_H12pc.sch` ≡ `asbuilt/core.sp` ≡ this scorecard).

## 2. One axis at a time (process | supply | temperature)

| corner | T | VDD | fc | dc | ripple | ph | a1000 | IRN | P nW | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.8 | -0.008 | 0.052 | 332.4 | -49.0 | 29.2 | 11.91 | PASS |
| mos_ss | +27 | 1.50 | 247.4 | -0.017 | 0.074 | 332.4 | -49.4 | 29.6 | 11.90 | PASS |
| mos_ff | +27 | 1.50 | 252.5 | -0.009 | 0.047 | 332.2 | -48.6 | 28.8 | 11.92 | PASS |
| mos_sf | +27 | 1.50 | 249.9 | -0.034 | 0.046 | 332.2 | -48.9 | 29.0 | 11.92 | PASS |
| mos_fs | +27 | 1.50 | 248.8 | -0.007 | 0.097 | 332.4 | -49.1 | 29.4 | 11.91 | PASS |
| mos_tt | +27 | 1.35 | 243.6 | -0.777 | 0.354 | 308.0 | -49.0 | 29.5 | 10.47 | FAIL |
| mos_tt | +27 | 1.65 | 249.9 | -0.009 | 0.050 | 332.4 | -49.0 | 29.2 | 13.11 | PASS |
| mos_tt | -40 | 1.50 | 211.1 | -5.054 | 0.470 | 251.7 | -44.9 | 28.6 | 7.40 | FAIL |
| mos_tt | +125 | 1.50 | 316.3 | -28.271 | 0.862 | 256.0 | -34.3 | 213.5 | 16.30 | FAIL |

Envelopes (nine-step sweeps): every line PASS over **1.40–1.65 V** at 27 °C and
**0…+70 °C** at 1.5 V; full 45-point grid 16/45, 22-point screen
6/22 — every failing corner contains 1.35 V, ≤ −20 °C or ≥ 85 °C and is a
headroom failure of the merged ladder (023 §5), never a bias failure.

## 3. THD (S7 definition: 175 mVpp differential, fin 50 Hz, harmonics 2–10)

**At corners** — spec drive, open loop:

| corner | T | VDD | THD dB | HD3 | HD2 |
|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | **-50.40** | -50.6 | -100.3 |
| mos_ss | +27 | 1.50 | **-47.68** | -47.9 | -102.6 |
| mos_ff | +27 | 1.50 | **-50.60** | -50.8 | -101.5 |
| mos_sf | +27 | 1.50 | **-51.90** | -52.2 | -106.3 |
| mos_fs | +27 | 1.50 | **-50.07** | -50.2 | -100.4 |
| mos_tt | +27 | 1.40 | **-47.28** | -47.5 | -106.4 |
| mos_tt | +27 | 1.65 | **-50.43** | -50.6 | -100.4 |
| mos_tt | +0 | 1.50 | **-47.29** | -47.6 | -104.8 |
| mos_tt | +70 | 1.50 | **-48.56** | -48.6 | -109.5 |

Worst -47.28 dB (1.40 V and 0 °C): **7.3 dB of S7 margin at every corner measured.**

**Mismatch MC** (n = 30, `mos_tt_mismatch` + `cap_typ_mismatch`, 27 °C):
mean **-50.21 dB**, σ 0.80 dB, worst -48.17, best -51.57 —
30/30 samples ≤ −40 dB.

**Profile over fin** (informative — only 50 Hz is spec; output amplitude follows
the filter roll-off, drive held at 175 mVpp):

| fin Hz | THD dB | HD3 dB |
|---|---|---|
| 20 | -72.07 | -72.10 |
| 50 | -50.40 | -50.60 |
| 100 | -21.78 | -22.05 |
| 150 | -20.19 | -20.37 |
| 200 | -21.34 | -21.44 |

The 100–200 Hz points show the family property recorded in 021 (`internal
node = bandpass tap`; the stacked ladder is ~20 dB worse than the un-stacked
reference at 100 Hz). This is a known limitation of the topology, not of this
sizing, and it is outside the S7 definition; state it, do not hide it.

## 4. Mismatch MC, all lines (n = 100, `mos_tt_mismatch` + `cap_typ_mismatch`)

**All-pass yield 82 %**, σ(fc) 3.76 Hz (mean 249.2), σ(dc) 0.00007 dB;
per line: S1 phase 100 %, S1 |H|@1k 96 %, S2 fc 82 %, S3–S6 100 %.
Every fail is S2 (fc outside ±2 %) — a bias/cap trim, not a shape failure.

## 5. MIM capacitor corners (`cornerCAP.lib`), 27 °C / 1.5 V / mos_tt

| cap corner | iref | fc | dc | ripple | ph | a1000 | IRN | verdict |
|---|---|---|---|---|---|---|---|---|
| cap_typ | ×1.0 | 249.8 | -0.008 | 0.052 | 332.4 | -49.0 | 29.2 | PASS |
| cap_bcs | ×1.0 | 277.1 | -0.008 | 0.013 | 331.0 | -45.3 | 29.2 | FAIL (S2 + S1 |H|@1k) |
| cap_bcs | ×0.9 | 250.6 | -0.008 | 0.070 | 331.0 | -48.9 | 30.6 | PASS |
| cap_wcs | ×1.0 | 227.3 | -0.008 | 0.121 | 333.6 | -52.4 | 29.2 | FAIL (S2) |
| cap_wcs | ×1.1 | 249.0 | -0.008 | 0.042 | 333.6 | -49.2 | 28.0 | PASS |

±10 % on `cap_carea` moves fc ∓10 % (fc ∝ gm/C), exactly as it must; a ±10 %
iref trim (fc ∝ I in weak inversion) restores every line — the same knob that
absorbs the S2 mismatch tail. The shape (dc, ripple, phase) is unaffected.

## What is NOT covered here (post-layout work)

Parasitic capacitance / resistance of the routing and of the MIM plates
(top/bottom-plate parasitics are "included by parasiticC extraction" per the
PDK model card, i.e. not in this schematic), well/substrate coupling of the
floating differential caps, and the real bias reference (α = 1.1 is a model).
