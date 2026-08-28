# validation.md — every number, and what checks it

**[GENERATED]** by `scripts/report.py` from `data/*.json`.  Do not hand-edit: re-run

```
.venv/bin/python signoff/paper-draft/scripts/report.py
```

The derivations these numbers check live in [theory.md](theory.md); the map from the
reviewer's request to the answers is in [README.md](README.md).

## 1. The DC operating point — the root of every number below

Every symbol in every equation in [theory.md](theory.md) is bound to **one measured
operating point**, so this table is the root of the whole chain: the poles, the noise
transimpedances and the distortion currents are all functions of these `gm`, `I_D` and
`C` values and of nothing else.  It is the "verified by the DC ops" check the reviewer
asked for.

Extracted with `.op` on the as-built subckt, one saved op-var per device per parameter
(`scripts/extract_bench.py` → `data/bench_pre_mim.json`, `data/bench_post_lumped.json`).
`n` is *derived* from the measured `gm/I_D` as `n = 1/((gm/I_D)·U_T)` with
`U_T = 25.865` mV at 27 °C — it is a restatement of column 5, not an independent
measurement, and it is tabulated because `n` is the symbol the distortion equation of §6
uses.  The independent evidence that the exponential law applies is column 7.

| dev | role | I_D (nA) | gm (nS) | gm/I_D (1/V) | n implied | V_GS−V_TH (mV) | \|V_DS\| (V) | \|V_DSAT\| (V) | sat. margin (V) | Δgm post (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| `m2` | biquad-A input follower (`gm_ia`) | 0.663 | 16.631 | 25.10 | 1.540 | -227.4 | 0.1657 | 0.1013 | +0.0645 | +1.20e-04 |
| `m5` | biquad-A input follower (`gm_ia`) | 0.663 | 16.631 | 25.10 | 1.540 | -227.4 | 0.1657 | 0.1013 | +0.0645 | -3.01e-04 |
| `m4` | biquad-A shunt-feedback device (`gm_fa`) | 1.984 | 44.748 | 22.56 | 1.714 | -24.7 | 0.6948 | 0.1098 | +0.5851 | -8.94e-05 |
| `m8` | biquad-A shunt-feedback device (`gm_fa`) | 1.984 | 44.748 | 22.56 | 1.714 | -24.7 | 0.6948 | 0.1098 | +0.5851 | -4.02e-04 |
| `m10` | biquad-A internal bias sink | 0.663 | 18.604 | 28.08 | 1.377 | -195.5 | 0.5291 | 0.1013 | +0.4278 | +0.00e+00 |
| `m9` | biquad-A internal bias sink | 0.663 | 18.604 | 28.08 | 1.377 | -195.5 | 0.5291 | 0.1013 | +0.4278 | +0.00e+00 |
| `mst` | current-reuse bridge (`gm_br`) | 2.646 | 58.784 | 22.21 | 1.740 | -76.0 | 0.2364 | 0.1054 | +0.1310 | +8.51e-05 |
| `mstn` | current-reuse bridge (`gm_br`) | 2.646 | 58.784 | 22.21 | 1.740 | -76.0 | 0.2364 | 0.1054 | +0.1310 | +3.06e-04 |
| `m0` | biquad-B input follower (`gm_ib`) | 2.646 | 62.034 | 23.44 | 1.649 | -101.1 | 0.3472 | 0.1036 | +0.2435 | +9.67e-05 |
| `m1` | biquad-B input follower (`gm_ib`) | 2.646 | 62.034 | 23.44 | 1.649 | -101.1 | 0.3472 | 0.1036 | +0.2435 | +3.22e-04 |
| `m14` | biquad-B shunt-feedback device (`gm_fb`) | 2.646 | 63.513 | 24.00 | 1.611 | -115.7 | 0.2216 | 0.1029 | +0.1187 | -1.26e-04 |
| `m15` | biquad-B shunt-feedback device (`gm_fb`) | 2.646 | 63.514 | 24.00 | 1.611 | -115.7 | 0.2216 | 0.1029 | +0.1187 | -3.46e-04 |
| `r1` | replica branch, `gm_fb` copy | 2.649 | 63.583 | 24.00 | 1.611 | -115.7 | 0.5687 | 0.1029 | +0.4658 | +0.00e+00 |
| `r2` | replica branch, bridge copy | 2.649 | 58.850 | 22.21 | 1.740 | -76.0 | 0.6091 | 0.1054 | +0.5037 | +0.00e+00 |
| `r3` | replica branch, sink | 2.649 | 74.375 | 28.08 | 1.377 | -195.5 | 0.3221 | 0.1013 | +0.2208 | +0.00e+00 |
| `mbn` | testbench bias-mirror diode | 0.662 | 18.596 | 28.08 | 1.377 | -195.5 | 0.3558 | 0.1013 | +0.2546 | +0.00e+00 |

**Design checks on this table**

* **Every device is below threshold**, measured rather than assumed: `V_GS − V_TH` runs
  from -227 mV to -25 mV, i.e.
  1.0–8.8 thermal voltages below threshold.
  The tightest device, `m4`, is 24.7 mV
  (0.95·U_T) below `V_TH`, which is the moderate-inversion edge
  rather than deep weak inversion.  This is why the §6 distortion model is stated with a
  validity window and then *tested* — §6.1 measures 42.63 dB/decade of HD3-vs-amplitude
  against the 40 dB/decade the exponential law predicts, which is the empirical
  confirmation that the law holds where it is used.
* **The implied slope factors are physical.**  `n` spans 1.377–1.740, inside
  the 1 < n < 2 band a subthreshold MOS must obey.  `n` is algebraically tied to `gm/I_D`,
  so this is a consistency test, not an independent one — but it is a test the data could
  have failed (moderate/strong inversion would have pushed `n` past 2) and does not.
* **Every device is saturated with margin.** The tightest `V_DS − V_DSAT` is `m2`
  at +64.5 mV.  In weak inversion the saturation condition is
  `V_DS ≳ 4·U_T ≈ 103` mV, and the smallest `V_DS` in the cell is
  `m2` at 165.7 mV = 6.4·U_T — clear by
  1.60×.  A follower dropping out of saturation would break both
  the `gm`-only transfer function and the `Z_T`-propagated distortion model.
* **Bulk is tied to source on every device** (asserted in `n2tf_model.bind_op`, which
  refuses the netlist otherwise).  That is what makes `gmb` inert and lets the PSP `cgb`
  op-var — which carries ~99 % of `cgg` in weak inversion — fold into `cgs`.
* **The layout barely moves the operating point**: the largest `gm` shift
  between pre- and post-layout is 4.0e-04 %.  The pre→post differences reported
  everywhere below are therefore *capacitive*, not bias shifts.

## 2. The transfer function, evaluated

### 2.1 The closed form at the measured operating point

[theory.md §2](theory.md#2-the-transfer-function) derives, as an exact symbolic identity
on the differential-mode half-circuit,

```
                     gm_fa · gm_ia · gm_ib · (gm_br + gm_fb)
    H(s) = ------------------------------------------------------------
                        D_A(s) · D_B(s)  +  κ · s²
```

with `D_A`, `D_B`, `κ` as given there.  Substituting the §1 `gm` values and the design's
own capacitors gives the numbers below.  This evaluation is at **`Fidelity.IDEAL`** —
transconductances and the four design capacitors, nothing else — so it is the *design
equation*, not the full model; §2.2 quantifies exactly what the rest of the model adds.

#### pre-layout (`pre_mim`)

| symbol | measured | symbol | value |
|---|---|---|---|
| `gm_ia` | 16.6312 nS | `C1a` | 4.9410 pF |
| `gm_fa` | 44.7478 nS | `C2a` | 29.3713 pF |
| `gm_br` | 58.7844 nS | `C1b` | 59.9120 pF |
| `gm_ib` | 62.0341 nS | `C2b` | 24.7020 pF |
| `gm_fb` | 63.5135 nS | `gm_br + gm_fb` | 122.2979 nS |

The cross capacitors are drawn floating between the halves, so the half-circuit sees
**2·C2a = 58.743 pF** and **2·C2b = 49.404 pF** — the factor
of two from the differential realisation, and the reason the drawn farads are half what a
single-ended filter would need.

Roots of the closed-form quartic:

| pole pair | s (rad/s) | f₀ (Hz) | Q |
|---|---|---|---|
| 1 | -1496.03 ± j569.91 | 254.793 | 0.5351 |
| 2 | -613.17 ± j1479.29 | 254.861 | 1.3058 |

Isolated-stage ("decoupled", κ = 0) contrast: biquad A **f₀ = 254.849 Hz,
Q = 2.1021**; biquad B **f₀ = 254.805 Hz,
Q = 0.4632**.  The coupling term is
**κ = 8.9017e-37**, i.e. **11.78 %** of the quartic's own
`s²` coefficient.

#### post-layout (`post_lumped`)

| symbol | measured | symbol | value |
|---|---|---|---|
| `gm_ia` | 16.6312 nS | `C1a` | 4.9410 pF |
| `gm_fa` | 44.7478 nS | `C2a` | 29.3713 pF |
| `gm_br` | 58.7844 nS | `C1b` | 59.9120 pF |
| `gm_ib` | 62.0342 nS | `C2b` | 24.7020 pF |
| `gm_fb` | 63.5134 nS | `gm_br + gm_fb` | 122.2978 nS |

The cross capacitors are drawn floating between the halves, so the half-circuit sees
**2·C2a = 58.743 pF** and **2·C2b = 49.404 pF** — the factor
of two from the differential realisation, and the reason the drawn farads are half what a
single-ended filter would need.

Roots of the closed-form quartic:

| pole pair | s (rad/s) | f₀ (Hz) | Q |
|---|---|---|---|
| 1 | -1496.03 ± j569.92 | 254.793 | 0.5351 |
| 2 | -613.17 ± j1479.29 | 254.861 | 1.3058 |

Isolated-stage ("decoupled", κ = 0) contrast: biquad A **f₀ = 254.849 Hz,
Q = 2.1021**; biquad B **f₀ = 254.805 Hz,
Q = 0.4632**.  The coupling term is
**κ = 8.9017e-37**, i.e. **11.78 %** of the quartic's own
`s²` coefficient.

### 2.2 Reconciling the three pole estimates — closed form, full model, simulation

The closed form above is deliberately minimal, and it is **+5.07 Hz**
away from the full model.  That gap is not an error: it is what the device capacitances
add, and naming it is the point of reporting both.

|  | biquad-A pair f₀ / Q | biquad-B pair f₀ / Q | `fc` (−3 dB, Hz) | what it includes |
|---|---|---|---|---|
| closed form, `Fidelity.IDEAL` | 254.79 / 0.5351 | 254.86 / 1.3058 | 254.83 (geometric) | `gm` + the 4 design caps |
| full model, `Fidelity.FULL` | 249.72 / 0.5430 | 251.08 / 1.3074 | — | + every `ro`, `cgs`, `cgd`, `cdb` and the replica branch |
| 4-pole fit to the ac sweep | 258.96 / 0.5211 | 247.22 / 1.3272 | 249.775 (measured) | the simulator, no model at all |

**Which capacitance closes the gap is measured, not asserted.**  Each family of device
capacitance symbols is zeroed in turn and the pencil re-solved on the same matrices
(`scripts/tf_analysis.py::cap_ablation`):

| capacitance zeroed | symbols zeroed | pole f₀ (Hz) | kept zero f₀ (Hz) |
|---|---|---|---|
| (none: the full model) | 0 | 249.72, 251.08 | 3854, 5045 |
| `cgs` | 16 | 254.65, 254.66 | 13253, 1107233 |
| `cgd` | 16 | 249.72, 251.08 | 3854, 5045 |
| `cdb` | 16 | 249.84, 251.40 | 3858, 5457 |

**`cgs` is the whole gap.**  Zero it and the poles return to
254.65 Hz — the closed form's
254.83 Hz to within
0.18 Hz —
and the two out-of-band zero pairs disappear with them.  (The kept-zero column can still
show a root in the 10 kHz–1 MHz range: with `cgs` gone the model has almost no state left
up there, and what survives is near-cancelling pole/zero residue three to four orders of
magnitude above the band — it is listed for completeness, not read as a filter feature.)  `cgd` moves nothing at all
(it is 3.1 aF on the input device:
in weak inversion the channel is not formed, so there is no Miller path), and `cdb`
moves `fc` by 0.12 Hz.

The mechanism is specific: PSP reports
**cgg = 250.5 fF** on the biquad-A
input follower, of which
**247.4 fF is `cgb`** — because in
weak inversion the gate charge terminates on the bulk, not on a channel.  Bulk is tied to
source here, so all of it lands gate-to-source and adds
5.1 %
to `C1a` = 4.941 pF, the smallest
capacitor in the filter.  Reading the op-vars by strong-inversion convention — `cgs` as the
gate-to-source capacitance, `cgb` left on the bulk — would have put
81×
too little capacitance on that node and hidden this shift entirely.

Two consequences:

* **The closed form is the design equation, and it is accurate to ~2 % in `fc`** — the
  width of the S2 window — with the error sign and mechanism both known.  Sizing from it
  and then trimming on the full model is exactly how this cell was built.
* **Everything quoted as a *result* — poles, Q, `fc`, group delay — comes from the full
  model or from the simulator, never from the closed form.**  §3 shows the full model and
  the simulator agree to 0.0267 dB.

The same accounting applies to the dc gain: the closed form gives **H(0) = 1 exactly**
(the numerator is literally the constant term of `D_A·D_B`), while the full model and the
simulator both give **-0.008148 dB** — the finite `ro`
of the followers, and nothing else.

## 3. Model versus simulation

### 3.1 The model, evaluated against the ac sweep point by point

The exact same operating-point-bound system that produced the poles is evaluated at every
frequency of the certified ac sweep and compared against it point by point
(`scripts/tf_analysis.py::validate`).  No fitting, no scaling: one `.op`, one solve.

|  | max Δ\|H\| ≤1 kHz (dB) | max Δφ ≤1 kHz (°) | max Δτ_g (%) | τ_g(dc) sim / model (ms) | max Δ\|H\| all f (dB) | max Δφ all f (°) |
|---|---|---|---|---|---|---|
| pre-layout | 0.0267 | 0.3448 | 0.997 | 1.6470 / 1.6471 | 2.582 | 26.01 |
| post-layout | 0.0265 | 0.3427 | 1.023 | 1.6508 / 1.6510 | 2.301 | 23.95 |

* **In the scored band the model matches the simulator to a few hundredths of a dB** — 0.027 dB and
  0.34° over dc–1 kHz, on a response that falls 49 dB across that band.
* **Above the scored band it degrades to ~2.6 dB / 26°.**  That is the stopband, below
  −49 dB, where the device-capacitance feed-through zeros of §4 take over; the
  discrepancy there is the linearisation itself, and it is reported rather than hidden by
  trimming the plot.
* **Group delay closes to ~1 %**, and τ_g(dc) — the most pole-sensitive scalar the filter
  has — matches to 4 significant figures.  A group-delay match this tight requires *all
  four* poles to be right, which is why it is quoted as the strongest aggregate check on
  the pole locations.

### 3.2 What the simulation says about the poles **on its own**

A 4-pole / 0-zero rational is fitted directly to the measured complex response over
0.1–500 Hz, in log-magnitude and unwrapped phase together.  It never sees the
small-signal model, the netlist or the operating point — it is the reviewer's
"verified by the sim data" check, standing alone.

|  | pair A f₀ / Q | pair B f₀ / Q | fit residual (dB / °) | monic-quartic coefficient error vs model (%) | worst single-root distance (%) | **all-real refit** residual (dB / °) |
|---|---|---|---|---|---|---|
| pre-layout | 258.96 / 0.5211 | 247.22 / 1.3272 | 0.2151 / 0.8607 | 4.80, 3.29, 4.63, 4.25 | 12.3 | 4.846 / 52.5 |
| post-layout | 258.13 / 0.5220 | 245.89 / 1.3253 | 0.2292 / 0.9179 | 5.19, 3.59, 5.06, 4.68 | 12.9 | 4.860 / 52.3 |

Read this table in the right order, because the conditioning differs by column:

* **The fit is good**: 0.215 dB and
  0.861° over 185 points and 60 dB of dynamic range.  The
  measured response *is* 4-pole/0-zero to that accuracy in the passband — the order is
  confirmed from data.
* **The pole set agrees with the model to 3–5 %** in the coefficients of the monic
  quartic, which is the well-posed comparison.
* **The individual (f₀, Q) split is only good to ~12 %
  per root, and that is expected, not a discrepancy.**  The two pairs are nearly
  co-located in frequency (§2), so the response has a shallow valley in the direction that
  trades one pair against the other; the fit slides along it.  The number is printed
  rather than suppressed so the limit of what an ac sweep alone can resolve is visible.
* **The last column is the decisive one for the reviewer's actual question.**  Refitting
  with both Q's constrained to ≤ 0.5 — which is exactly "all four poles are real" — the
  best achievable residual is **4.85 dB
  and 52°**,
  23×
  and 61×
  worse, with both Q's pinned against the 0.5 bound (the fit is driven toward complex
  poles and the constraint prevents it).  **The measured response cannot be
  reproduced by any all-real-pole 4th-order model.**  So "are the poles real or
  imaginary?" is answered by the simulation data alone: **complex, both pairs**, and the
  model then says where.

**Why not `ngspice .pz`?**  It is not usable on this cell: it aborts with *"the input
signal is shorted on the way to the output"* for any input port that carries its own dc
bias, which a subthreshold gate must.  Confirmed on a one-transistor deck as well, so it
is the analysis and not the netlist.  The three checks above — an operating-point-bound
eigenvalue solve, a simulator-only fit with a falsification test, and a point-by-point
overlay — replace it: between them they report what a `.pz` listing would have, plus
checks it does not make.

## 4. Poles and zeros — the map

From the matrix pencil of the **full 13-node differential system** at `Fidelity.FULL`
(`scripts/pencil.py`): poles are the finite generalised eigenvalues of `(−G, C)`, zeros
come from the bordered pencil with the output port as the border, both computed on the
same matrices the ac solve uses.  Everything is `Fidelity.FULL` here — every `ro`, every
device capacitance, the replica branch and the bias diode included.

### pre-layout (`pre_mim`)

`11` poles and `11` zeros are returned; **7 of
them cancel** — 1 conjugate pair (counted as
2 roots) plus 5 real — leaving the
4-pole,
4-zero response
below.  A cancelling pole/zero pair is a mode the differential input cannot excite or the
differential output cannot observe — the replica branch and the bias diode account for all of
them — and they are *reported*, not silently dropped.  Cancellation is declared at 10⁻⁴
relative separation because the two sets come from two separately conditioned
eigenproblems; the worst residual separation actually observed here is
**1.4e-11** relative, i.e. 0.00 % of the declaration threshold.

**Poles** (dc gain -0.008148 dB)

| # | s (rad/s) | f₀ (Hz) | Q | kind |
|---|---|---|---|---|
| 1 | -1444.68 ± j612.20 | 249.720 | 0.5430 | complex pair |
| 2 | -603.33 ± j1457.63 | 251.076 | 1.3074 | complex pair |

**Zeros**

| # | s (rad/s) | f₀ (Hz) | Q | kind |
|---|---|---|---|---|
| 1 | -799.4 ± j2.42e+04 | 3854 | 15.1476 | complex pair |
| 2 | -4353 ± j3.14e+04 | 5045 | 3.6411 | complex pair |


### post-layout (`post_lumped`)

`11` poles and `11` zeros are returned; **7 of
them cancel** — 1 conjugate pair (counted as
2 roots) plus 5 real — leaving the
4-pole,
4-zero response
below.  A cancelling pole/zero pair is a mode the differential input cannot excite or the
differential output cannot observe — the replica branch and the bias diode account for all of
them — and they are *reported*, not silently dropped.  Cancellation is declared at 10⁻⁴
relative separation because the two sets come from two separately conditioned
eigenproblems; the worst residual separation actually observed here is
**5.0e-06** relative, i.e. 0.05 % of the declaration threshold.

**Poles** (dc gain -0.008148 dB)

| # | s (rad/s) | f₀ (Hz) | Q | kind |
|---|---|---|---|---|
| 1 | -1428.86 ± j624.47 | 248.179 | 0.5457 | complex pair |
| 2 | -602.20 ± j1450.55 | 249.967 | 1.3041 | complex pair |

**Zeros**

| # | s (rad/s) | f₀ (Hz) | Q | kind |
|---|---|---|---|---|
| 1 | -947.6 ± j2.395e+04 | 3815 | 12.6489 | complex pair |
| 2 | -4559 ± j3.111e+04 | 5004 | 3.4485 | complex pair |

### What the map says

* **All four filter poles are complex** — two conjugate pairs, Q =
  0.543 and 1.307.  There is no real pole in the
  passband, so the answer to *"real or imaginary?"* is: **two under-damped pairs, at
  249.72 Hz and 251.08 Hz, essentially
  co-located in frequency (0.54 %
  apart) and split only in damping**.  A 4th-order Butterworth has
  Q = 0.5412 and 1.3066 at a single ω₀; this cell measures
  **0.5430 and 1.3074** — within
  0.3 % and
  0.1 % of Butterworth — which is what gives
  the 0.008 dB dc flatness and the 0.05 dB passband ripple of §7.
  The shape is *not* designed by placing two textbook stages: §2.1 shows the isolated
  stages would be Q = 2.10 and 0.46, and it is the κ·s² coupling term that maps them onto
  the Butterworth pair.
* **The zeros are all far out of band and all complex**: the lowest is at
  3.85 kHz, 15.4×
  above the pole frequency, so neither the passband shape nor the 1 kHz stopband number
  depends on them.  **Their origin is measured** (§2.2 ablation table): zeroing `cgs`
  removes both pairs, zeroing `cgd` changes nothing.  They are the followers' own
  **gate-to-source feed-forward** — a source follower's input capacitance is a direct path
  to its output — and they are why the modelled stopband stops falling at 80 dB/decade,
  which is the same physics as the \|H\|-vs-model divergence above 1 kHz in §3.1, seen
  from the other side.
* **`figures/pz_plane.png`** plots exactly these tables — both members of each conjugate
  pair, poles and zeros, pre- and post-layout on the same axes, with the cancelled pairs
  shown hollow.

## 5. The noise equation, checked generator by generator

[theory.md §3](theory.md#3-the-noise-equation) states the equation

```
    S_out(f) = Σ_k |Z_T,k(jω)|² · S_i,k(f) ,     IRN² = ∫ S_out(f)/|H(jω)|² df
```

— every device's every noise generator, each propagated to the differential output by the
transimpedance of its own port.  The check below is not a fit: `S_i,k(f)` is the
simulator's own per-generator noise vector, `Z_T,k` is solved from the operating-point
model, and the two are multiplied and summed.

### 5.1 Closure

|  | IRN sim (µV) | IRN Σ generators (µV) | IRN certified (µV) | max Δ S_out (%) | max Δ inoise vs onoise/\|H\| (%) | `netlist2tf.transimpedance` vs pencil |
|---|---|---|---|---|---|---|
| pre-layout | 29.1990 | 29.1990 | 29.1990 | 1.98e-07 | 4.19e-14 | 1.67e-08 |
| post-layout | 29.1959 | 29.1959 | 29.1959 | 1.98e-07 | 4.16e-14 | 2.62e-09 |

Three independent closures:

1. **The sum over generators reproduces the simulator's own total** to
   2.0e-07 % at every frequency —
   so no generator is missing and none is double-counted.  This is what justifies writing
   `Σ_k` at all.
2. **The integrated IRN equals the certified sign-off number** to all quoted digits — the
   frozen `lab.metrics` definition, not a re-derivation.
3. **`spicexplorer_netlist2tf.transimpedance` and the independent matrix-pencil solve
   agree to ~10⁻⁸ relative.**  The package primitive and the checking code are separate
   implementations of `Z_T`, which is the point of running both.

### 5.2 Where the noise comes from

Integrated 0.5–200 Hz, input-referred.  Percentages are of total IRN **power**.  First by
generator kind:

| generator | what it is | pre-layout (µV / % power) | post-layout (µV / % power) |
|---|---|---|---|
| `idid` | channel (weak-inversion shot) noise | 22.9082 / 61.55 % | 22.9057 / 61.55 % |
| `igig` | gate-leakage shot noise | 15.2010 / 27.10 % | 15.1994 / 27.10 % |
| `flicker` | 1/f gate noise | 9.8346 / 11.34 % | 9.8339 / 11.35 % |
| `ibd` | bulk-drain junction | 0.0560 / 0.00 % | 0.0560 / 0.00 % |
| `rgate` | gate resistance | 0.0002 / 0.00 % | 0.0002 / 0.00 % |

**The gate-leakage generator is a quarter of the noise power.**  In any normal bias regime
`igig` is discarded; at 0.66–2.6 nA per branch, with 10–60 MΩ of transimpedance in front of
it, it is second only to the channel.  A hand-written noise model that omits it is 1.4 dB
optimistic on IRN before it does anything else (10·log₁₀(1/(1−0.271))).

Then by device role — the answer to "which device should I make bigger":

| role | pre-layout (µV / % power) | post-layout (µV / % power) |
|---|---|---|
| biquad-A input follower (`gm_ia`) | 18.4306 / 39.84 % | 18.4309 / 39.85 % |
| biquad-A internal bias sink | 18.2210 / 38.94 % | 18.2214 / 38.95 % |
| biquad-B input follower (`gm_ib`) | 10.7789 / 13.63 % | 10.7687 / 13.60 % |
| biquad-B shunt-feedback device (`gm_fb`) | 5.7379 / 3.86 % | 5.7364 / 3.86 % |
| current-reuse bridge (`gm_br`) | 5.0345 / 2.97 % | 5.0297 / 2.97 % |
| biquad-A shunt-feedback device (`gm_fa`) | 2.5363 / 0.75 % | 2.5519 / 0.76 % |
| testbench bias-mirror diode | 0.0000 / 0.00 % | 0.0033 / 0.00 % |
| replica branch, sink | 0.0000 / 0.00 % | 0.0010 / 0.00 % |
| replica branch, bridge copy | 0.0000 / 0.00 % | 0.0005 / 0.00 % |
| replica branch, `gm_fb` copy | 0.0000 / 0.00 % | 0.0005 / 0.00 % |
| testbench bias devices | 0.0000 / 0.00 % | 0.0000 / 0.00 % |

**The two biquad-A branch devices carry 79 % of the noise between them**, and the
biquad-A bias sink — a device that appears nowhere in `H(s)`, because an ideal current
source is an open circuit to small signals — contributes almost as much as the input
follower.
The reason is not the cascade order — both biquads are unity-gain followers, so neither
attenuates the other's noise — it is **node impedance**: the transimpedance from biquad
A's internal node `net2` to the differential output is
60 MΩ against 16 MΩ
at biquad B's `net4`, because `C1a` is the smallest capacitor in the filter.  The same
injected current therefore makes
3.7× more output noise in A than
in B — which is also why the design spends its capacitance there.  The replica branch and
the testbench bias diode sit on the differential axis and contribute nothing measurable.

And by role × generator:

#### pre-layout (`pre_mim`) — total 29.1990 µV

| role | generator | IRN contribution (µV) | % of power |
|---|---|---|---|
| biquad-A internal bias sink | `idid` | 14.8996 | 26.04 |
| biquad-A input follower (`gm_ia`) | `idid` | 14.8549 | 25.88 |
| biquad-A internal bias sink | `igig` | 9.9240 | 11.55 |
| biquad-A input follower (`gm_ia`) | `igig` | 9.8935 | 11.48 |
| biquad-B input follower (`gm_ib`) | `flicker` | 7.4427 | 6.50 |
| biquad-B input follower (`gm_ib`) | `idid` | 6.5304 | 5.00 |
| biquad-B shunt-feedback device (`gm_fb`) | `idid` | 4.6154 | 2.50 |
| biquad-A input follower (`gm_ia`) | `flicker` | 4.5974 | 2.48 |
| biquad-B input follower (`gm_ib`) | `igig` | 4.2597 | 2.13 |
| current-reuse bridge (`gm_br`) | `idid` | 3.7770 | 1.67 |
| *(all other role × generator terms)* | — | 6.3764 | 4.77 |

#### post-layout (`post_lumped`) — total 29.1959 µV

| role | generator | IRN contribution (µV) | % of power |
|---|---|---|---|
| biquad-A internal bias sink | `idid` | 14.8999 | 26.04 |
| biquad-A input follower (`gm_ia`) | `idid` | 14.8552 | 25.89 |
| biquad-A internal bias sink | `igig` | 9.9242 | 11.55 |
| biquad-A input follower (`gm_ia`) | `igig` | 9.8937 | 11.48 |
| biquad-B input follower (`gm_ib`) | `flicker` | 7.4410 | 6.50 |
| biquad-B input follower (`gm_ib`) | `idid` | 6.5199 | 4.99 |
| biquad-B shunt-feedback device (`gm_fb`) | `idid` | 4.6141 | 2.50 |
| biquad-A input follower (`gm_ia`) | `flicker` | 4.5974 | 2.48 |
| biquad-B input follower (`gm_ib`) | `igig` | 4.2529 | 2.12 |
| current-reuse bridge (`gm_br`) | `idid` | 3.7727 | 1.67 |
| *(all other role × generator terms)* | — | 6.3810 | 4.78 |
### 5.3 Are the generators what they claim to be?

Two per-generator sanity checks, applied to the 12 devices
whose differential transimpedance is non-degenerate.  (The other
4 — the replica branch and the testbench's bias diode —
sit **on the differential axis**, where `|Z_T|` comes out at
38.4 Ω against
14.3 kΩ for the weakest signal-path device
and 60 MΩ for the strongest; their `S_i`
extraction is a division by ~0 and is therefore meaningless, while their *actual*
contribution is **4.5e-11 %** of the IRN power.  A further
2.39e-04 µV — **6.7e-09 %** of the power, the gate-resistance
generators and the testbench's own bias devices — has no resolved port at all and is
carried at its measured value.)

| check | expected | observed over the signal devices |
|---|---|---|
| channel noise against full shot noise, `S_i / 2qI_D` | ≤ 1, approaching 1 deep in saturation | 0.628 – 0.719 |
| the same, written against `gm`: `S_i / 4kT·gm` | = (n/2)·(previous column) | 0.495 – 0.580 |
| flicker slope, `d log S_i / d log f` | ≈ −1 (1/f) | -1.152 – -0.999 |
| power-law fit residual over 1–200 Hz | small | ≤ 0.035 dB |

The first row is the physical statement: the channel generator is
**0.63–0.72× full
shot noise `2qI_D`**.  That is a weak-inversion channel generator; the strong-inversion
form `4kTγ·gm` with γ = 2/3 is a different law with a different bias dependence, and the
data picks the shot-noise one.  The second row is the same measurement rewritten against `gm`, and it is a *consistency* check
rather than a new one: the two columns must differ by exactly `n/2`, and their measured
ratio is
1.249 = 2/n
with n = 1.601,
which matches the §1 slope factors.  The flicker slope being slightly steeper than −1 is
the PSP flicker model's own `f^-(1+δ)` behaviour, not a fitting artifact.

**The port of every generator is identified from the data, not assumed**
(`scripts/noise_analysis.py::identify_port`): for each generator the candidate device
ports are ranked by how well `S_out/|Z_T,port|²` comes out frequency-flat (or `1/f`, for
flicker), and the winner is taken.  Every channel-noise generator selects drain–source and
every gate generator selects gate–source, which is what the physics predicts.  Doing it
this way makes the port assignment a measured result rather than an assumption, and that
is what justifies re-using the same `Z_T` for the distortion currents in §6.

`figures/noise_budget.png` plots `S_out(f)`, the sum of generators, and the top
contributors' individual curves on one axis.

## 6. Linearity — HD3, THD, IMD3, IIP3

[theory.md §4](theory.md#4-the-distortion-equation) derives the distortion equation from
the same two ingredients as the noise: an exponential device injects a third-harmonic
drain current, and that current reaches the output through the **same** `Z_T` the noise
uses.

```
    a_k(ω) = |v_gs,k(jω)| / (n_k U_T)
    i₃,k   = I_D,k · 2·I₃(a_k)/I₀(a_k)          →  I_D,k · a_k³/24   for a ≪ 1
    HD3(ω) = | Σ_k Z_T,k(j3ω) · i₃,k(ω) |  /  |V_out,fund(ω)|
```

**Validity window, defined by the check below:** the equation is a
*weak-inversion, small-`a`, quasi-static* model.  It is confirmed to **±2 dB over
35–65 Hz** at 43.75 mVpp; outside that window it under-predicts, and
§6.2 says by how much and why.  Every claim made from it is made inside that window.

### 6.1 HD3 versus amplitude — the `A²` law

At f_in = 50 Hz, differential drive, coherent strobed transient + DFT with a
rect/Hann agreement guard (`scripts/linearity_runs.py`).

| V_in (Vpp diff) | THD (dB) | HD3 (dB) | HD2 (dB) | V_out fund (Vpp) | THD post-layout (dB) | HD3 post-layout (dB) |
|---|---|---|---|---|---|---|
| 0.04375 | -76.254 | -76.271 | -100.969 | 0.04370 | -76.395 | -76.413 |
| 0.0875 | -64.198 | -64.208 | -105.858 | 0.08731 | -63.607 | -63.616 |
| 0.175 | -50.401 | -50.605 | -100.187 | 0.17386 | -49.726 | -49.928 |
| 0.35 | -23.855 | -24.575 | -72.411 | 0.32614 | -23.525 | -24.191 |
| 0.525 | -18.738 | -19.278 | -77.248 | 0.36157 | -18.598 | -19.141 |
| 0.7 | -16.570 | -17.141 | -78.042 | 0.34117 | -16.473 | -17.058 |

Fitted over the three points that are inside the model's own validity window
(43.75, 87.50, 175.00 mVpp):
**42.63 dB/decade** against the predicted
**40 dB/decade** (HD3 ∝ A², i.e. `a³` over a linear
fundamental), worst residual **0.513 dB**.  The prediction is
confirmed.

Beyond ~0.3 Vpp the ladder leaves the small-signal regime entirely — the fundamental stops
growing (0.326 → 0.362 → 0.341 Vpp for 0.35 → 0.525 → 0.70 Vpp in) and THD saturates near
−17 dB.  That is slew/compression, correctly *outside* the equation's window.
**The −40 dB THD crossing is at 306.9 mVpp** — the compression
point a reviewer asks for, 1.75× the S7 drive of 175 mVpp.

### 6.2 HD3 versus frequency — the `ω²` law, and where the model stops

At 43.75 mVpp differential, one decade and a half of f_in.  `a` is the modulation index
the follower's own gate–source excursion produces; it is *computed*, not fitted.

**This check runs pre-layout only, and that is sufficient.**  The equation's inputs are
the `gm`, `I_D` and `n` of §1 — and the layout moves every one of those by at most
4.0e-04 % (§1.3), so the *modelled* HD3 is identical to the digits printed
here for either DUT.  What the layout can move is the *measured* HD3, and that is reported
independently, on the extracted netlist, in §6.1 and §6.3.

| f_in (Hz) | HD3 measured (dB) | HD3 model, coherent (dB) | HD3 model, worst-case (dB) | model − measured (dB) | dominant device | max `a` |
|---|---|---|---|---|---|---|
| 10 | -100.272 | -115.535 | -114.262 | -15.263 | biquad-B input follower (`gm_ib`) | 0.0286 |
| 20 | -92.907 | -97.747 | -95.460 | -4.840 | biquad-B input follower (`gm_ib`) | 0.0573 |
| 35 | -82.148 | -83.692 | -80.091 | -1.545 | biquad-B input follower (`gm_ib`) | 0.1009 |
| 50 | -76.271 | -74.386 | -70.310 | +1.885 | biquad-A shunt-feedback device (`gm_fa`) | 0.1454 |
| 65 | -65.897 | -66.432 | -63.387 | -0.535 | biquad-A shunt-feedback device (`gm_fa`) | 0.1914 |
| 100 | -50.411 | -55.268 | -54.660 | -4.857 | biquad-A shunt-feedback device (`gm_fa`) | 0.3070 |
| 150 | -42.889 | -50.575 | -49.653 | -7.685 | biquad-A shunt-feedback device (`gm_fa`) | 0.5004 |
| 200 | -38.203 | -49.131 | -47.070 | -10.928 | biquad-A shunt-feedback device (`gm_fa`) | 0.7061 |

* **Inside 35–65 Hz the model is within ±2 dB** on the absolute
  level, and it tracks the slope there: measured
  **60 dB/decade** against the model's **64 dB/decade**.
* **The `HD3 ∝ ω²` (40 dB/decade) rule is the ω → 0 *asymptote*, not the model.**  The
  mechanism it comes from is explicit — shunt feedback makes `|1 − H| → ω·C₁/gm_i`, so the
  follower's own `v_gs` grows linearly with ω, `a³` gives ω³, and the falling `Z_T(j3ω)`
  gives one power back — but that argument needs `3ω ≪ ω₀`, and at f_in = 50 Hz the third
  harmonic is already at 150 Hz, 0.6·f_c.  The full expression keeps `|1 − H(jω)|` and
  `Z_T(j3ω)` as they are and is correspondingly steeper near the corner, which is what
  both columns above show.  (The whole-sweep fit of
  34.9 dB/decade in `data/linearity_analysis.json` is
  *not* a test of the law: it averages a floored low end with a compressed high end.)
* **Below ~35 Hz the model under-predicts by up to
  15.3 dB — but in *volts* the shortfall is a
  constant.**  The same three points, written as absolute output third-harmonic amplitude:

| f_in (Hz) | measured V₃ (µV) | model V₃ (µV) | measured − model (µV) |
|---|---|---|---|
| 10 | 0.2118 | 0.0365 | +0.1753 |
| 20 | 0.4945 | 0.2833 | +0.2113 |
| 35 | 1.7066 | 1.4286 | +0.2780 |

  The model's own prediction moves by a factor of 39 across those
  three points while the shortfall stays at
  **0.18–0.28 µV**.
  An additive, frequency-independent residual is a *different mechanism*, not a mis-scaled
  version of the modelled one.  Drain-conductance nonlinearity (`g_ds(V_DS)`) is the
  natural candidate — the small-signal `Z_T` linearises it away by construction — but that
  is a hypothesis: it is stated as a bounded observation with numbers attached, **not** as
  a fitted claim, and closing it needs a `g_ds`-expansion term the present model does not
  have ([README.md](README.md#7-open-items)).  For scale, the entire residual sits
  61.7 dB below the third harmonic this same
  cell produces at the S7 operating point — a modelling gap, not a performance one.
* **Above ~100 Hz `a` passes 0.3** (last column) and the *propagation* stops being linear.
  The harmonic generation itself is still exact — the code uses the Bessel ratio
  `2·I₃(a)/I₀(a)`, not its `a³/24` truncation — but with `a` this large the cell is
  compressing (V_out falls from 43.7 to 36.6 mVpp between 10 and 200 Hz), so both the
  small-signal `Z_T` and the "fundamental unaffected" assumption behind the ratio break
  down.  The model's 10.9 dB miss at
  200 Hz is therefore expected, and is the reason the window is stated up front.

THD versus f_in at the **S7 drive** of 175 mVpp, both DUTs:

| f_in (Hz) | THD pre-layout (dB) | THD post-layout (dB) | HD3 pre (dB) | HD3 post (dB) | V_out fund (Vpp) |
|---|---|---|---|---|---|
| 20 | -72.082 | -71.647 | -72.105 | -71.664 | 0.17478 |
| 50 | -50.401 | -49.726 | -50.605 | -49.928 | 0.17386 |
| 100 | -21.778 | -21.594 | -22.052 | -21.872 | 0.15465 |
| 150 | -20.189 | -20.255 | -20.370 | -20.434 | 0.08381 |
| 200 | -21.338 | -21.427 | -21.438 | -21.527 | 0.05197 |

### 6.3 Two-tone: IMD3 and IIP3

Two equal tones at 45 / 55 Hz (10 Hz
spacing, both on the DFT grid), coherent transient + DFT, `IMD3` referred to the
fundamental (`scripts/linearity_runs.py::tran_twotone`).

| A per tone (V) | fund (V) | IMD3 lo (dBc) | IMD3 hi (dBc) | IMD3 (dBc) | IIP3 (dBV) | IMD3 post-layout (dBc) | IIP3 post-layout (dBV) |
|---|---|---|---|---|---|---|---|
| 0.0109375 | 0.010922 | -72.537 | -71.386 | -71.943 | -3.250 | -71.946 | -3.249 |
| 0.021875 | 0.021829 | -60.229 | -59.348 | -59.777 | -3.312 | -59.509 | -3.447 |
| 0.04375 | 0.043514 | -47.254 | -46.425 | -46.829 | -3.766 | -46.486 | -3.938 |
| 0.0875 | 0.083668 | -27.144 | -26.803 | -26.972 | -7.674 | -26.711 | -7.805 |
| 0.13125 | 0.103299 | -13.708 | -13.174 | -13.437 | -10.920 | -13.120 | -11.078 |

|  | IIP3 (dBV) | IIP3 (V_peak per tone) | OIP3 (dBV) | IMD3 slope (dB/decade) | slope residual (dB) | IIP3 spread over the linear points (dB) |
|---|---|---|---|---|---|---|
| pre-layout | -3.281 | 0.6854 | -3.297 | 41.71 | 0.261 | 0.515 |
| post-layout | -3.348 | 0.6802 | -3.359 | 42.29 | 0.196 | 0.689 |

* **IIP3 = -3.28 dBV pre-layout,
  -3.35 dBV post-layout** — a
  -0.066 dB shift,
  i.e. the layout is linearity-neutral to within the measurement's own repeatability.
* **The 3:1 slope is confirmed**: 41.7
  dB/decade of IMD3 against the theoretical 40, residual
  0.26 dB, and the extrapolated IIP3 is
  consistent to 0.52 dB
  across the three amplitudes that are actually in the cubic regime.  The top two
  amplitudes are excluded from the extrapolation and shown anyway — they are compressing
  (fund 0.084 → 0.103 V for a 1.5× drive increase), and an IIP3 extrapolated from them
  would not be valid.
* **IIP3 is quoted in dBV, not dBm, deliberately.**  This is a voltage-mode filter driven
  by a balun-style differential source into a capacitive gate; there is no 50 Ω anywhere
  in the cell, so a dBm number would require inventing a reference impedance.  The dBV
  figure is referred to the **peak** amplitude of one
  tone at the differential input, which is
  0.6854 V — 3.9× the S7 drive amplitude, and
  well past where §6.1 shows the cell compressing, so IIP3 here is an extrapolated
  figure of merit rather than a reachable operating point.  That is the normal reading of
  an intercept, and it is stated because a filter this deep in weak inversion has no
  large-signal headroom to spend.

### 6.4 Is the cell memoryless?  (The `IMD3 = HD3 + 9.54 dB` test)

For a memoryless cubic nonlinearity, IMD3 and HD3 at the same per-tone amplitude differ by
exactly 20·log₁₀(3) = 9.54 dB.  Measured at A = 21.875 mV per tone:

| quantity | value |
|---|---|
| HD3 at 50 Hz, same amplitude | -76.271 dBc |
| memoryless prediction, HD3 + 9.54 dB | -66.729 dBc |
| IMD3 measured | -59.777 dBc |
| **excess** | **+6.952 dB** |

**The identity fails by 6.95 dB, and it is supposed to.**  §6.2 established
that HD3 rises at ~60 dB/decade through this band, so the third-order response
is strongly frequency dependent and the cell is by construction *not* memoryless.  The
question is which kind of memory, and the spacing sweep answers it:

| f₁ / f₂ (Hz) | spacing (Hz) | IMD3 (dBc) | IIP3 (dBV) |
|---|---|---|---|
| 49 / 51 | 2 | -59.529 | -3.436 |
| 48 / 52 | 4 | -59.556 | -3.423 |
| 45 / 55 | 10 | -59.720 | -3.341 |
| 40 / 60 | 20 | -60.269 | -3.067 |
| 35 / 65 | 30 | -61.289 | -2.556 |

Over a **15× change in tone spacing** — which is a 15× change in the
envelope frequency the cell must follow — IMD3 moves only
**1.76 dB**.  Envelope (baseband) memory would show up
here as a strong spacing dependence and does not.  The 6.95 dB excess is
therefore attributable to the *carrier*-frequency dependence of the third-order response —
the same mechanism §6.2 measured — and not to envelope memory.  That is the useful engineering
statement: **HD3 at one frequency does not predict IMD3 for this cell; measure IMD3.**

All spacings are constrained to even values so both tones and all four intermodulation
products land exactly on DFT bins; an odd spacing puts the tones on half-bins and the
resulting IMD3 is scalloping, not distortion (observed once at −0.79 dBc, which is how the
constraint was found).

`figures/distortion.png` and `figures/iip3.png` plot §6.1–6.3.

## 7. The four DUTs, side by side

Every table above is measured on one of four netlists.  They are all the *same cell*; they
differ only in what is modelled.

| DUT | what it is | instances | noise vectors |
|---|---|---|---|
| `pre_ideal` | as-built schematic, ideal linear capacitors (`signoff/post-pvt/H12-robust/asbuilt/core.sp`) | 16 | 97 |
| `pre_mim` | **the pre-layout DUT of record** — as-built schematic with PDK MIM capacitors (`signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`) | 16 | 109 |
| `post_pex` | **the post-layout DUT of record** — the kpex-extracted subckt of the it14 layout | 36 | 224 |
| `post_lumped` | the schematic devices carrying the extracted parasitics as 68 explicit `Cext_*` cards (`data/post_lumped_core.sp`) | 16 | 109 |

**Why `post_lumped` exists.**  kpex splits some devices across the extracted netlist, so a
handful of extracted halves no longer have bulk tied to source — which `bind_op` refuses,
correctly, because it is the assumption that makes `gmb` inert and folds `cgb` into `cgs`.
`post_lumped` restores that structure by putting the schematic devices back and attaching
the extraction's parasitic capacitances as explicit cards.  It is not an approximation of
`post_pex` — it is **proven equivalent to it**: `fc` within
0.0031 Hz
and `ph_max` within
0.0477°
of the certified post-layout scorecard.  Symbolic post-layout results are therefore quoted
on `post_lumped`; measured post-layout results (THD, IIP3, the certified scorecard) are
quoted on `post_pex`.

| metric | `pre_ideal` | `pre_mim` | `post_pex` | `post_lumped` |
|---|---|---|---|---|
| \|dc gain\| (dB) | -0.0081 | -0.0081 | -0.0081 | -0.0082 |
| fc (Hz) | 249.8316 | 249.7746 | 248.6636 | 248.6605 |
| peaking (dB) | 0.0002 | 0.0018 | 0.0128 | 0.0121 |
| passband ripple (dB) | 0.0538 | 0.0523 | 0.0363 | 0.0377 |
| \|H\| @ 1 kHz (dB) | -48.9916 | -49.0260 | -49.2183 | -49.2184 |
| ph_max (°) | 332.3205 | 332.3823 | 331.2208 | 331.2685 |
| τ_g(dc) (ms) | 1.6464 | 1.6470 | 1.6506 | 1.6508 |
| τ_g max (ms) | 2.4696 | 2.4703 | 2.4818 | 2.4814 |
| IRN 0.5–200 Hz (µVrms) | 29.2014 | 29.1990 | 29.1944 | 29.1959 |
| output noise (µVrms) | 34.2949 | 34.2843 | 34.2413 | 34.2402 |
| core power (nW) | 11.9124 | 11.9125 | 11.9136 | 11.9124 |
| total C (pF) | 183.7300 | 183.7792 | 183.7792 | 183.7792 |

Pre → post (`pre_mim` → `post_pex`, both signed post minus pre): `fc`
**-1.111 Hz**
(-0.44 %),
`ph_max` **-1.161°**,
IRN -0.0045 µV
(-0.015 %),
stopband -0.192 dB,
core power +0.0011 nW.
**The layout costs this filter 1.1 Hz of `fc` and 1.2° of `ph_max`; noise and power are
unchanged at the fourth digit, and the stopband improves by 0.19 dB.**  Every equation
above makes the same pre→post statement in its own quantity.

## 8. The analytical results over PVT and mismatch

Everything in Sections 1–7 is derived at ONE operating point.  This section re-derives the
poles, the per-biquad `Q` and the noise budget at every corner of the window the cell is
certified over, and over 64 mismatch draws.  No new modelling is involved: each of those
quantities is a function of the operating point, and `extract_bench.py --pvt/--mc` produces
one operating point per point.  Generated by `scripts/pvt_analysis.py`.

**Read `fc` and `Q` as different questions.**  `fc` is a SCALE set by `gm/C`, and in weak
inversion `gm = I/(n·U_T)`, so a reference current that does not track temperature makes
`fc` move by construction — that is old news and `lab/corners.py` documents it.  `Q` and the
pair-coincidence ratio are `gm` RATIOS.  Whether the filter's SHAPE survives when its scale
drifts is the question the nominal analysis could not answer, and it is the one below.

**The bias law matters and is recorded.**  The temperature rows use `LPF_BIAS_ALPHA=1.1`,
the constant-`gm` shaping the delivered cells were certified with.  At 27 °C it is the same
current as the default `alpha = 0`, so the nominal numbers above are unaffected; at every
other temperature it is a different measurement, and a sweep that silently took the default
would report an uncompensated cell as if it were this one.

### 8.1 Scale versus shape

| quantity | what it is | certified axes (9) | certified box (45) | harness box (29) |
|---|---|---|---|---|
| `fc` | **scale** — set by `gm/C` | 1.022× | 1.675× | 6.408× |
| `Q` low pair | **shape** — a `gm` ratio | 1.002× | 3.968× | 3.447× |
| `Q` high pair | **shape** — a `gm` ratio | 1.027× | 1.550× | 1.385× |
| `f₀` ratio | **shape** — pair coincidence | 1.023× | 1.976× | 1.442× |
| two complex pairs | the S1 property itself | **9/9** | 38/45 | 15/29 |
| Σ generators vs IRN | the noise equation, per corner | 1.1e-06 % | 2.3e-05 % | 3.1e-05 % |

The certified window is **one axis at a time** — process at 27 °C/1.5 V, supply 1.40–1.65 V
at 27 °C, temperature 0–70 °C at 1.5 V — which is how `signoff/post-pvt/README.md` states
it.  On those nine points the scale moves 1.022×, and **both complex pairs survive every
one of them** — the S1 property itself never comes close to failing.

The two pairs then behave differently, and the table says so.  The LOW-Q pair is the pure
ratio the framing predicts: its `Q` holds to 0.16 %, 1× stiffer than the scale beside it.
The HIGH-Q pair is not: its `Q` moves 2.7 %, which is as much as `fc` moves and slightly
more.  Splitting that by axis shows where it comes from — 0.8 % over process,
0.2 % over supply, 2.7 % over temperature — so it is a temperature effect, and it
persists under the constant-`gm` bias that is supposed to remove temperature from `gm`.
The honest summary is therefore narrower than "shape is invariant": the filter stays two
biquads and the low-Q damping is fixed, while the high-Q damping carries a residual
temperature dependence of the same order as the cutoff's (1.1 % over the same axis).

**The axes do not superpose, and that is a result.**  The middle column is the CROSS
PRODUCT of the same endpoints — 45 points, none of them ever certified.  7 of them have
lost a complex pair, i.e. the filter is no longer two biquads, and `tt / 0 °C / 1.40 V` is
among the failures even though nominal process, 0 °C and 1.40 V are each individually
inside the certified window.  A one-axis-at-a-time claim is therefore not a box, and the
distinction is invisible in the scorecard alone.

### 8.2 The certified axes, point by point

| corner | `fc` (Hz) | `ph_max` (°) | low-Q pair `f₀` / `Q` | high-Q pair `f₀` / `Q` | IRN (µV) |
|---|---|---|---|---|---|
| `tt_27c_1v500` | 249.775 | 332.38 | 249.72 / 0.5430 | 251.08 / 1.3074 | 29.199 |
| `ss_27c_1v500` | 247.365 | 332.38 | 246.63 / 0.5430 | 249.32 / 1.3087 | 29.578 |
| `ff_27c_1v500` | 252.502 | 332.17 | 252.88 / 0.5432 | 253.90 / 1.3045 | 28.821 |
| `sf_27c_1v500` | 249.890 | 332.25 | 251.33 / 0.5432 | 251.25 / 1.2989 | 29.043 |
| `fs_27c_1v500` | 248.836 | 332.44 | 247.75 / 0.5425 | 251.65 / 1.3070 | 29.378 |
| `tt_27c_1v400` | 249.613 | 332.07 | 249.53 / 0.5423 | 250.95 / 1.3091 | 29.203 |
| `tt_27c_1v650` | 249.920 | 332.42 | 249.98 / 0.5431 | 251.19 / 1.3067 | 29.198 |
| `tt_0c_1v500` | 249.449 | 332.43 | 249.77 / 0.5432 | 249.23 / 1.3129 | 27.681 |
| `tt_70c_1v500` | 247.056 | 332.02 | 248.43 / 0.5424 | 253.65 / 1.2782 | 31.708 |

### 8.3 Mismatch

64 draws at `mos_tt_mismatch`, 27 °C, each one a full extraction and the same pencil
solve — not a rational fit to the response, because `fit_poles_from_sim` (Section 3.2)
records that the `f₀`/`Q` split of two nearly co-located pairs is weakly determined by the
response, so a `Q` distribution built that way would mostly measure the fit's conditioning.

| quantity | mean | σ | min … max |
|---|---|---|---|
| `fc` (Hz) | 249.427 | 3.367 | 242.198 … 256.233 |
| `ph_max` (°) | 332.286 | 0.165 | 331.599 … 332.468 |
| low-pair `Q` | 0.5429 | 0.0013 | 0.5400 … 0.5461 |
| high-pair `Q` | 1.3081 | 0.0165 | 1.2678 … 1.3512 |
| IRN (µV) | 29.211 | 0.193 | 28.853 … 29.678 |
| output offset (µV) | +95.0 | 1974.9 | -3986.2 … +4478.7 |

Both complex pairs survive **64/64** draws.  The low-Q pair is again the stiff one — `Q`
scatters by 0.24 % against 1.35 % for `fc` — but the high-Q pair scatters 1.27 %, i.e. as
much as the scale does.  That is the expected shape of the difference: a PVT corner shifts
every device the same way, so ratios can hold while scale moves, whereas a mismatch draw
shifts each device independently and a ratio has no reason to survive it.  σ(`fc`) = 3.37 Hz here
against the 3.7 Hz the certified 100-sample scorecard MC reports, which is the agreement
that says these draws are the same population.

`figures/pvt_axes.png` plots the nine points and the 45-point box; `figures/mc_mismatch.png`
plots the three distributions.

One caveat on the pole COUNT.  At nominal the cell is symmetric and seven pole/zero pairs
cancel exactly; under mismatch those become near-cancellations, so the raw solve returns
the doublets separately plus a parasitic pair near 10 kHz from the device capacitances.
The filter's poles are the two nearest the origin and are selected that way
(`pvt_analysis._pairs`); the doublets are reported in `n_complex_pairs_all`.

### 8.4 Does any of this transfer to the post-layout cell?

Everything above is measured on the pre-layout DUT.  Section 7 argues the sensitivity
carries over to the extracted cells because layout adds capacitance and the capacitance
ratios are what set `Q`.  That argument is now measured rather than asserted: the same nine
certified axes, re-extracted on `post_lumped`.

| quantity | pre-layout (`pre_mim`) | post-layout (`post_lumped`) |
|---|---|---|
| `fc` span | 1.0220× | 1.0224× |
| `Q` low pair span | 1.0016× | 1.0016× |
| `Q` high pair span | 1.0271× | 1.0271× |
| `f₀` ratio span | 1.0232× | 1.0232× |
| two complex pairs | 9/9 | 9/9 |
| IRN over the axes (µV) | 27.681 … 31.708 | 27.675 … 31.705 |
| Σ generators vs IRN | 1.1e-06 % | 1.1e-06 % |

The two columns agree to the third decimal on every span, and the post-layout cell keeps
two complex pairs at all 9/9 points.  `fc` sits about 0.45 % lower everywhere — the
layout capacitance the extraction adds — but the SENSITIVITY, which is what this section is
about, is the same measurement.  The post-layout `fc` is drawn as hollow circles in
`figures/pvt_axes.png`.

## 9. Supply rejection, common-mode rejection, and offset

`doc/paper/README.md` G12 records these three as unmeasured.  Generated by
`scripts/psrr_cmrr.py`, from two new benches in `lab/deck.py` (`ac_psrr`, `ac_cmrr`).

**Why the nominal differential number is not the answer.**  This cell is geometrically
symmetric, so supply → differential output and common-mode → differential output both
cancel by construction.  At nominal the simulator returns its own solver residual, which
reads as a spectacular rejection figure and says nothing about silicon.  What is finite at
nominal is the COMMON-MODE response; what is real for the differential path is the
MISMATCH-limited value.  Both are given, and neither alone would be honest.

### 9.1 Nominal, common-mode paths

| transfer | 0.1 Hz | 50 Hz | 250 Hz | 1000 Hz |
|---|---|---|---|---|
| supply → output CM (dB) | -61.72 | -10.70 | -1.54 | -0.14 |
| CM in → CM out (dB) | -0.01 | -0.43 | -6.07 | -23.08 |

Two things to read here.  The cell **passes** its input common mode to the output at dc
(-0.01 dB) and low-passes it — expected of a follower chain, and not a defect, because
every spec in `doc/target-spec.md` is differential.  Supply → output common mode is
-61.72 dB at dc but only -0.14 dB at 1 kHz: **in the stopband the output common mode
tracks the rail essentially one-for-one.**  That does not touch the differential signal,
but it bounds what may sit downstream of this filter on the same supply.

### 9.2 Mismatch-limited, differential paths

32 draws, `mos_tt_mismatch`, 27 °C.

| quantity | 0.1 Hz | 50 Hz | 250 Hz | 1000 Hz |
|---|---|---|---|---|
| CMRR mean (dB) | 98.99 | 52.73 | 44.04 | 24.60 |
| CMRR worst (dB) | 88.74 | 42.52 | 33.80 | 13.59 |
| PSRR mean (dB) | 108.18 | 55.66 | 52.66 | 19.93 |
| PSRR worst (dB) | 95.78 | 42.55 | 39.58 | 6.63 |

Rejection falls with frequency in both paths, as the loop gain that produces it falls.

`figures/rejection.png` plots both: panel (a) the nominal common-mode transfers with
their envelope over the nine certified axis points, panel (b) the mismatch band.

### 9.3 Input-referred offset

Zero by symmetry at nominal, so it is a mismatch quantity and only a distribution.  Over
the same 32 draws: mean **-163.5 µV**, σ **1924.9 µV**, worst |offset| **4054.8 µV**.  The dc
gain is within 0.01 dB of unity, so the input-referred and output values coincide.  For
scale, σ is 1.10 % of the 175 mVpp S7 drive.

Section 8.3 measures the same quantity a second way — 64 draws, from the operating point
of a full extraction rather than from this bench's `op` — and gets mean +95.0 µV,
σ **1974.9 µV**.  The two σ agree to 2.6 %, and both means sit inside one
standard error of zero, which is what a symmetric cell should give.

## 10. The sub-35 Hz residual, and linearity over corners

### 10.1 A named mechanism for the residual

Section 6.2 reports a third harmonic below 35 Hz that the gate-referred model does not
explain: 0.18–0.28 µV, and nearly CONSTANT IN VOLTS while the modelled mechanism moves by
39× over the same span.  That additive signature says a different mechanism, not a
mis-scaled one.  This is the test of the candidate named there.

**The hypothesis, its predictions and its refutation threshold were written down before
the measurement** (`scripts/gds_probe.py`, repo rule 3):

* **H** — the residual is generated by drain-conductance nonlinearity, the curvature of
  `I_D` in `V_DS`.  The gate-referred model does not contain it and the small-signal `Z_T`
  linearises it away.
* **P1**, magnitude within a factor of 3 of the residual.  **P2**, flat in volts below 35 Hz.
* **Refuted** by a prediction more than 10× off, or a frequency slope of the wrong sign.

A device whose drain swings by `v_ds` sources `I(v) = I₀ + g₁v + g₂v²/2 + g₃v³/6`; the
small-signal model keeps `g₁` and drops the rest.  For `v = A·cos(ωt)` the cubic term makes
a third harmonic of amplitude `g₃A³/24`, injected at the SAME port the noise analysis
already characterised, so it propagates through the same `Z_T` and needs no new machinery.
`g₃` is measured per device by a probe pinned to that device's own in-circuit bias
(`gds_probe.py`, which reproduces the DUT's PSP `gds` to 1.09 %); `A` and its phase come
from the MNA node solve, not from an estimated swing.

| f_in (Hz) | measured V₃ (µV) | gate model (µV) | unexplained (µV) | `g_ds` prediction (µV) | ratio |
|---|---|---|---|---|---|
| 10 | 0.2118 | 0.0365 | 0.1753 | 0.0506 | 0.289 |
| 20 | 0.4945 | 0.2833 | 0.2113 | 0.0556 | 0.263 |
| 35 | 1.7066 | 1.4286 | 0.2780 | 0.0702 | 0.253 |
| 50 | 3.3567 | 4.1704 | -0.8137 | 0.0952 | -0.117 |
| 65 | 11.0808 | 10.4191 | 0.6617 | 0.1284 | 0.194 |
| 100 | 65.8510 | 37.6442 | 28.2068 | 0.1405 | 0.005 |
| 150 | 155.1183 | 64.0310 | 91.0873 | 0.0926 | 0.001 |
| 200 | 248.1947 | 70.5301 | 177.6646 | 0.0664 | 0.000 |

**P2 is satisfied.**  The prediction varies 1.39× below 35 Hz where the residual it
explains varies 1.59× — flat in volts, which is the signature that made this residual
look like a separate mechanism in the first place, and which the gate-referred model misses
by 39×.

**P1 is not settled.**  On the pre-registered point estimate the worst factor is
3.96×, so H is **INCONCLUSIVE** — outside the accept band, well inside the refute
threshold.  The threshold is not moved after the fact.  What the point estimate hides is
that the sum is dominated by `in_a`, whose `I_D(V_DS)` is not locally cubic over its own
drain swing: its `g₃` moves 5.4× across the three fit windows, against ≤ 1.3× for every
other device.  Carrying that through, the predicted band is **0.0365 … 0.2697 µV** against a
measured residual of **0.1753 … 0.2780 µV** — the bands overlap.

**The window dependence is now removed, and it does not rescue the magnitude.**  `g₃A³/24`
is the first term of a series and `g₃` is a fit, so the number it produces depends on the
interval it was fitted over.  Replacing it: expand the MEASURED `I_D(V_DS)` in Chebyshev
polynomials over exactly the swing the device sees, `[-A, +A]`.  Substituting
`x = A·cos θ` turns `T_n(x/A)` into `cos nθ`, so the Chebyshev coefficients ARE the Fourier
coefficients of the current waveform and `c₃` is the third harmonic exactly — no window is
chosen and no series is truncated.  The extractor is checked against synthetic curves whose
answer is known in closed form, including one carrying a fifth-order term that a cubic
truncation would drop; worst error 1.6e-13.  (5 of the 15 devices swing too little
across the stored curve to condition the fit; they keep the cubic term, which is the
correct expansion in exactly that limit, and together they are 0.0043 % of the total.)

| | prediction below 35 Hz | worst factor vs the residual | flatness |
|---|---|---|---|
| cubic, mid window (pre-registered) | 0.0506 … 0.0702 µV | 3.96× | 1.39× |
| cubic, across the three windows | 0.0365 … 0.2697 µV | — | — |
| **window-free, over each device's own swing** | **0.0350 … 0.0491 µV** | **5.66×** | 1.40× |

The window-free number is SMALLER, not larger.  It covers 18 % of the residual, keeps the
flat frequency signature, and removes the band overlap that the cubic's window ambiguity had
produced.  So the ambiguity is resolved in the direction that sharpens the conclusion rather
than the one that would have rescued it.

**So:** drain-conductance curvature is established as *a* contributor — the right frequency
dependence and about a fifth of the magnitude — and is excluded as the whole of it.  The
probe pins the gate and sweeps only the drain, so the one mechanism it cannot see by
construction is the cross-term, gate and drain swinging together, which in a source follower
they do.  That is where the remaining 82 % is expected to sit; testing it needs a
two-dimensional device probe this pack does not have, and it is left open rather than fitted.

`figures/gds_residual.png` plots both panels of this argument.

### 10.2 IIP3 over the certified axes

Tones stay at 45/55 Hz — the frozen definition every other IIP3 here uses — so each
row also carries its corner's `fc`: the tones sit at a different fraction of the passband
when the cutoff moves.  Two amplitudes per corner, so each corner reports its own IMD3
slope instead of assuming the 3:1 law that a corner might break.

| corner | `fc` (Hz) | IMD3 slope (dB/decade) | IIP3 (dBVp) | OIP3 (dBVp) |
|---|---|---|---|---|
| `tt_27c_1v500` | 249.775 | 40.47 | -3.248 | -3.260 |
| `ss_27c_1v500` | 247.365 | 41.94 | -3.600 | -3.623 |
| `ff_27c_1v500` | 252.502 | 40.42 | -3.159 | -3.171 |
| `sf_27c_1v500` | 249.890 | 41.53 | -5.726 | -5.768 |
| `fs_27c_1v500` | 248.836 | 41.10 | -3.169 | -3.186 |
| `tt_27c_1v400` | 249.613 | 41.92 | -3.802 | -3.829 |
| `tt_27c_1v650` | 249.920 | 39.83 | -3.336 | -3.348 |
| `tt_0c_1v500` | 249.449 | 40.67 | -4.079 | -4.085 |
| `tt_70c_1v500` | 247.056 | 38.50 | -7.044 | -7.185 |

IIP3 spans **-7.044 … -3.159 dBVp** over the 9 certified points, a 3.88 dB spread, with
every corner's measured slope within 2 dB/decade of 40 — so every row is an intercept and
not an extrapolation from an unverified law.  The worst is the hot corner.  The nominal row
differs from Section 6.3's -3.250 dBVp at the same amplitude in the third decimal because the `alpha = 1.1`
bias makes the reference a behavioural source even at 27 °C, where it carries the same
current.

`figures/iip3_corners.png` plots the intercepts and the measured slopes.

### 10.3 THD over the certified axes

Section 6.1 measures the THD amplitude ladder at nominal.  The same ladder, re-run at every
certified axis point: 6 amplitudes × 9 corners at `fin` = 50 Hz, open loop — an explicit
drive with no servo, because servoing the output to a constant level would remove the
amplitude dependence the ladder exists to measure.

**This table is characterisation, not a spec line.**  S7 is defined at one point —
175 mVpp, 50 Hz, nominal — and it is scored there by `lab.metrics` in `make check`.
What a corner row says is how much margin the delivered cell carries away from nominal.

| corner | `fc` (Hz) | 43.75 mVpp | 87.5 mVpp | 175 mVpp | 350 mVpp | 525 mVpp | 700 mVpp | HD3 slope (dB/dB) |
|---|---|---|---|---|---|---|---|---|
| `tt_27c_1v500` | 249.775 | -76.19 | -64.19 | -50.40 | -23.86 | -18.74 | -16.57 | 1.99 |
| `ss_27c_1v500` | 247.365 | -75.61 | -62.45 | -47.68 | -29.40 | -23.13 | -20.28 | 2.18 |
| `ff_27c_1v500` | 252.502 | -76.57 | -64.25 | -50.60 | -23.93 | -19.12 | -16.70 | 2.05 |
| `sf_27c_1v500` | 249.890 | -74.45 | -61.56 | -51.90 | -27.46 | -17.47 | -15.43 | 2.14 |
| `fs_27c_1v500` | 248.836 | -76.60 | -64.07 | -50.07 | -23.85 | -21.06 | -18.59 | 2.08 |
| `tt_27c_1v400` | 249.613 | -74.72 | -61.47 | -47.28 | -30.10 | -24.00 | -20.86 | 2.20 |
| `tt_27c_1v650` | 249.920 | -76.07 | -64.17 | -50.43 | -23.91 | -18.69 | -16.45 | 1.98 |
| `tt_0c_1v500` | 249.449 | -74.80 | -62.18 | -47.29 | -22.87 | -20.40 | -18.06 | 2.10 |
| `tt_70c_1v500` | 247.056 | -68.46 | -57.58 | -48.56 | -38.35 | -21.05 | -17.64 | 1.81 |

At the spec amplitude the nine corners span **-51.901 … -47.280 dB**, so the WORST of them
(-47.28 dB, at `tt_27c_1v400`) still clears the -40 dB limit by 7.28 dB.  HD2 is 24 dB below HD3 in every
row, so each of these numbers is third-order distortion and not an even-order artefact.

The corners do not simply translate the nominal ladder.  `tt_70c_1v500` sits +7.73 dB
relative to nominal at the lowest drive but only +1.84 dB at the spec amplitude, and its
HD3 slope over the two lowest points, 1.81 dB/dB, is the furthest of the nine from
the cubic law's 2.  A low-drive point lifted above a cubic extrapolation is the signature of
an additive third-harmonic term that does NOT scale with `A³` — which is what Section 10.1
measures at nominal.  Whether that mechanism also carries this temperature dependence is not
tested here; the ladder measures it, it does not explain it.

`figures/thd_corners.png` plots the ladder at every corner and the margin at the spec point.
