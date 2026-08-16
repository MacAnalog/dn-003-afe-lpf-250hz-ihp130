# Schematic-level results — every number, with its source

[REFERENCE] · assembled 2026-08-16 from committed artifacts on `feat/layout-h12-round2`.

The cell of record is **`H12-pdk-cap`**: a fully differential 4th-order 250 Hz
super-source-follower low-pass filter in IHP SG13G2 at VDD = 1.5 V, two cascaded
SSF biquads, replica-biased, all-hv devices, PDK MIM capacitors.

Every table below is a transcription of a committed artifact — no number in this
file was computed here except where a row is explicitly marked *derived*. Each
table names its source path. Paths are relative to the repo root.

---

## 0. Which reference number to quote

The reference baseline has **two certified IRN values**, and a paper must not
conflate them:

| value | grid | when | status |
|---|---|---|---|
| **50.18 µVrms** | AC sweep at 10 points/decade | certified 2026-08-11 | the number quoted in `doc/experiment-log.md` row `000-reference-baseline` |
| **49.98 µVrms** | AC sweep at 50 points/decade | re-certified 2026-08-12 | **the current canonical baseline** — same `design.json`, same sizing, same lane; only the sweep density moved |

`decks/reference/scorecard.json`, verbatim: *"Certified 50.18 on the old 10
pts/decade grid; the −0.20 uV is the density change, not a design change."*

**Recommendation for both papers:** quote **49.98 µVrms** as the baseline and
state the challenge as **< 40 µVrms (−20.0 %)**. If the 50.18 figure is used
(e.g. because an earlier draft did), say which grid it is on.

Source: `decks/reference/scorecard.json`, `doc/target-spec.md`, `doc/experiment-log.md`

---

## 1. The spec box — S1…S8

| # | requirement | target | how measured |
|---|---|---|---|
| S1 | filter order / shape | 4th order, **two true biquads**: `ph_max_deg ≥ 330.0` **and** `a1000_db ≤ −48.0` | max unwrapped lag over samples with \|H\| ≥ −100 dB rel. dc, from `ac dec 10 0.1 100k` |
| S2 | cutoff | 250 Hz ± 2 % ⇒ `fc_hz` in **245.0 … 255.0** | −3 dB point of the differential TF |
| S3 | passband gain | `\|dc_db\| ≤ 0.2`, flat to 150 Hz (`ripple_db ≤ 0.2`) | \|H\| at 0.1 Hz; worst peak-to-peak over 0.1–150 Hz |
| S4 | peaking | `peak_db ≤ 0.2` | max rise of \|H\| above dc below fc |
| S5 | **input-referred noise 0.5–200 Hz** | `irn_uv < 40.0` | `.noise v(voutp,voutn) vsig dec 10 0.1 1k`, `inoise_spectrum` trapezoidally integrated 0.5–200 Hz, band edges interpolated in log-f |
| S6 | **filter-core power** (core only, excludes the bias reference) | `p_core_nw < 50.0` (= 33.3 nA at 1.5 V) | 0 V series source `vflt` in the DUT supply pin; `p_core_nw = \|i(vflt)\|·VDD·1e9` |
| S7 | THD at 175 mVpp differential, fin = 50 Hz | `thd_db ≤ −40.0`, harmonics 2–10 | coherent strobed transient + DFT (`lab.deck.tran_thd` → `lab.thd.measure`); `ppc=512`, `cycles=20`, `settle=8`, `reltol=1e-5 abstol=1e-15 vntol=1e-9 chgtol=1e-16 method=gear maxord=2` |
| S8 | technique provenance | ≥ 2 papers from `pdf/` combined | the experiment README's paper row + the netlist |

**Report-only, never a spec line** (`lab.metrics.SOFT`): `c_total_pf`,
`idd_total_na`, `i_core_na`, `onoise_uv`, `ph_step_deg`, `f_scored_hi`,
`mono_db`. Total capacitance is *reported, never specced*.

Bench conditions: `.lib cornerMOShv.lib mos_tt`, 27 °C, VDD 1.5 V, input CM
0.25 V, output CM ≈ 1.25 V, ngspice 45 with the PDK's PSP 103.6 Verilog-A models
loaded as OSDI objects. Devices `sg13_hv_nmos` / `sg13_hv_pmos` (3.3 V class);
MIM `cap_cmim`.

Source: `doc/target-spec.md`, `lab/metrics.py`, `doc/benches.md`

---

## 2. Headline — baseline vs the cell of record

| line | spec box | reference baseline | **H12-pdk-cap** | H12-robust (ideal caps) |
|---|---|---|---|---|
| `fc_hz` | 245–255 | 250.37 | **249.7746** | 249.8316 |
| `dc_db` | \|·\| ≤ 0.2 | −0.0047 | **−0.0081** | −0.0081 |
| `ripple_db` | ≤ 0.2 | **0.2512 — FAILS S3** | **0.0523** | 0.0538 |
| `peak_db` | ≤ 0.2 | 0.0227 | **0.0018** | 0.0002 |
| `a1000_db` | ≤ −48 | −48.43 | **−49.026** | −48.9916 |
| `ph_max_deg` | ≥ 330 (ideal 4-pole ceiling 350.53) | 346.74 | **332.3823** | 332.3205 |
| **`irn_uv`** | **< 40** | **49.98** | **29.199** | 29.2014 |
| `p_core_nw` | < 50 | 12.07 | **11.9125** | 11.9124 |
| `thd_db` | ≤ −40 | −48.37 | **−50.401** | −50.676 |
| `c_total_pf` | reported only | 98.01 | **183.7792** | 183.73 |
| all S1–S8 | — | fails S3 flatness and S5 | **`all_pass: true`** | **`all_pass: true`** |

*Derived* (arithmetic on the rows above, not quoted from any file):
IRN **−41.6 %** vs the baseline (49.98 → 29.199 µVrms), against a −20.0 % ask;
THD **2.03 dB better**; core power **−1.3 %**; drawn capacitance **1.875×**.

Sources: `decks/reference/scorecard.json` · `signoff/post-pvt/H12-pdk-cap/scorecard.json` ·
`signoff/post-pvt/H12-robust/scorecard.json`

### Reference deck provenance (the frozen yardstick)

| field | value |
|---|---|
| deck | `decks/reference/lpf_tb.sp` |
| deck sha256 | `407e529809f01de38e500f67ef79c96a0756dcd51015869a336806ef12f007b5` (lint-pinned) |
| corner / temp / VDD | `mos_tt` / 27.0 °C / 1.5 V |
| caps (pF) | c1_a 29.468 · c2_a 6.221 · c1_b 11.453 · c2_b 9.946 |
| devices | 16 transistors + 6 capacitors, `i_core_na` 8.04 |

Source: `decks/reference/scorecard.json`, `decks/reference/build-sheet.md`

---

## 3. `H12-pdk-cap` nominal scorecard

27 °C, 1.5 V, `mos_tt`, `cap_typ` — **every S1–S8 line passes**.

| `fc_hz` | `dc_db` | `ripple_db` | `peak_db` | `a1000_db` | `ph_max_deg` | `irn_uv` | `p_core_nw` | `c_total_pf` | `thd_db` |
|---|---|---|---|---|---|---|---|---|---|
| 249.7746 | −0.0081 | 0.0523 | +0.0018 | −49.026 | 332.3823 | 29.199 | 11.9125 | 183.7792 | **−50.401** |

Report-only: `mono_db` 0.0018, `ph_step_deg` 9.697, `f_scored_hi` 3019.95 Hz,
`onoise_uv` 34.284, `i_core_na` 7.9416, `idd_total_na` 9.2674,
group delay τ(0) / τ_max / τ(fc) = 1.647 / 2.470 / 2.340 ms.

Both identity gates PASS: the drawn schematic ≡ `asbuilt/core.sp` ≡ this scorecard.

Sources: `signoff/post-pvt/H12-pdk-cap/scorecard.json`,
`signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`,
`doc/paper/figures/data/prepost_bode.json` (key `pre-layout (schematic)`, which
re-ran the same bench and reproduces every value)

### Sizing of record

topology `d` (replica-biased branch-stacked SSF) · `iref` 6.624e-10 A ·
vicm/vocm/vmid 0.24 / 1.2784 / 0.6948 V · `cap_model` `cmim` · `lv_roles` **`[]`
(all-hv — no lv devices anywhere)**

Capacitors (pF): `c1_a` 4.94 · `c2_a` 29.37 · `c1_b` 59.90 · `c2_b` 24.70

| device | W (µm) | L (µm) | ng | m |
|---|---|---|---|---|
| `in_a` | 16.0 | 10.0 | 2 | 1 |
| `gmf_a` | 1.5 | 45.0 | 1 | 1 |
| `bias_a_int` | 24.0 | 25.0 | 3 | 1 |
| `bridge` | 5.0 | 33.0 | 1 | 1 |
| `in_b` | 4.0 | 15.0 | 1 | 1 |
| `gmf_b` | 12.0 | 31.0 | 2 | 1 |
| `rep_gmfb` | 12.0 | 31.0 | 2 | 1 |
| `rep_bridge` | 5.0 | 33.0 | 1 | 1 |
| `rep_sink` | 24.0 | 25.0 | 3 | 4 |

Source: `signoff/post-pvt/H12-pdk-cap/design.json`

### Measured operating point (P half; N half identical by symmetry)

| role | inst | type | I_D (nA) | g_m (nS) | g_m/I_D | g_m/g_ds | \|V_ds\| (mV) | \|V_dsat\| (mV) | margin (mV) |
|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.663 | 16.63 | 25.1 | 1935 | 166 | 101 | +64 |
| `gmf_a` | m4 | nmos | 1.984 | 44.75 | 22.6 | 5262 | 695 | 110 | +585 |
| `bias_a_int` | m9 | nmos | 0.663 | 18.60 | 28.1 | 11793 | 529 | 101 | +428 |
| `bridge` | mst | pmos | 2.646 | 58.78 | 22.2 | 4512 | 236 | 105 | +131 |
| `in_b` | m0 | pmos | 2.646 | 62.03 | 23.4 | 4934 | 347 | 104 | +244 |
| `gmf_b` | m14 | pmos | 2.646 | 63.51 | 24.0 | 4493 | 222 | 103 | +119 |
| `rep_gmfb` | r1 | pmos | 2.649 | 63.58 | 24.0 | 11791 | 569 | 103 | +466 |
| `rep_bridge` | r2 | pmos | 2.649 | 58.85 | 22.2 | 12004 | 609 | 105 | +504 |
| `rep_sink` | r3 | nmos | 2.649 | 74.37 | 28.1 | 9446 | 322 | 101 | +221 |

Every device saturated and in weak inversion. DC ladder (mV):
VDD 1500 → `voutp` 1278 → `net4` 931 → `vout_1` 695 → `net2` 529 → 0.
Core current **7.942 nA** → **11.912 nW**.

Source: `signoff/post-pvt/H12-pdk-cap/op_lpf_core_H12pc.md` (JSON twin `op_lpf_core_H12pc.json`)

---

## 4. PVT — one axis at a time

Bias law `LPF_BIAS_ALPHA = 1.1` for every temperature point; the 27 °C rows are
independent of it.

| corner | T (°C) | VDD (V) | `fc` | `dc` | `ripple` | `ph_max` | `a1000` | `irn` | `P` (nW) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `mos_tt` | +27 | 1.50 | 249.8 | −0.008 | 0.052 | 332.4 | −49.0 | 29.2 | 11.91 | **PASS** |
| `mos_ss` | +27 | 1.50 | 247.4 | −0.017 | 0.074 | 332.4 | −49.4 | 29.6 | 11.90 | **PASS** |
| `mos_ff` | +27 | 1.50 | 252.5 | −0.009 | 0.047 | 332.2 | −48.6 | 28.8 | 11.92 | **PASS** |
| `mos_sf` | +27 | 1.50 | 249.9 | −0.034 | 0.046 | 332.2 | −48.9 | 29.0 | 11.92 | **PASS** |
| `mos_fs` | +27 | 1.50 | 248.8 | −0.007 | 0.097 | 332.4 | −49.1 | 29.4 | 11.91 | **PASS** |
| `mos_tt` | +27 | 1.35 | 243.6 | −0.777 | 0.354 | 308.0 | −49.0 | 29.5 | 10.47 | FAIL |
| `mos_tt` | +27 | 1.65 | 249.9 | −0.009 | 0.050 | 332.4 | −49.0 | 29.2 | 13.11 | **PASS** |
| `mos_tt` | −40 | 1.50 | 211.1 | −5.054 | 0.470 | 251.7 | −44.9 | 28.6 | 7.40 | FAIL |
| `mos_tt` | +125 | 1.50 | 316.3 | −28.271 | 0.862 | 256.0 | −34.3 | 213.5 | 16.30 | FAIL |

**Envelopes** (nine-step sweeps, every S-line): **1.40–1.65 V** at 27 °C, and
**0 … +70 °C** at 1.5 V. Grid coverage: one-axis set **6/9**, reduced screen
**6/22**, full grid **16/45**. Every failing corner contains 1.35 V, ≤ −20 °C or
≥ 85 °C, and is a headroom failure of the merged ladder — never a bias failure.

The process span is the campaign's key robustness result: **fc span 1.02×
(247.4–252.5 Hz)**, the same as the un-stacked, fully mirrored reference; the
merged ladder *without* the replica spanned **3–38×** (`A-minarea` 13.6→524 Hz).

Sources: `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md` ·
machine twins `experiments/023-replica-bias/H12-pdk-cap.robust.a1p1.json`
(`axes` = 9, `reduced.rows` = 22, `full.rows` = 45),
`vsw_H12-pdk-cap.json` (9-step supply), `tsw_H12-pdk-cap_a1p1_1p5.json` (9-step temperature)
· drawn in `figures/pvt_window.png`

---

## 5. Mismatch Monte Carlo, n = 100

`mos_tt_mismatch` + `cap_typ_mismatch`, 27 °C, 1.5 V, seeds 1–100. The PDK's own
`agauss` expressions supply every sigma; `lab.mc` only drives them, and the seed
is a **netlist directive** (`.option seed=`), not a `.control` `set rndseed`.
The denominator is **samples attempted**, so a dropped sample can only lower the
reported yield.

| quantity | value |
|---|---|
| **all-pass yield** | **82 % (82/100)** |
| non-converged / non-finite | 0 |
| `fc_hz` | mean 249.2104, σ **3.7578**, min 238.0053, max 258.3262 |
| `dc_db` | mean −0.0081533, σ **7.04e-05**, min −0.0083459, max −0.0079616 |
| `ripple_db` | mean 0.057675, σ 0.025244, min 0.019164, max 0.134062 |
| `irn_uv` | mean 29.2181, σ 0.19690, min 28.7869, max 29.7275 |
| `p_core_nw` | mean 11.8869, σ 0.20763, min 11.3687, max 12.3960 |
| `gd_dc_ms` | mean 1.65137, σ 0.028261 |
| `gd_max_ms` | mean 2.47785, σ 0.042020 |

Per-line yields: `ph_max` **100 %** · `a1000` 96 % · **`fc` 82 %** · `dc` 100 % ·
`peak` 100 % · `ripple` 100 % · `irn` 100 % · `p_core` 100 %.

**Every failure is S2** (fc outside ±2 %) — a bias/cap trim, not a shape failure.
σ(`dc_db`) at 7e-5 dB against a 0.2 dB box is the follower family's signature:
passband gain is self-referenced, so a threshold shift moves the operating point
and barely moves the gain.

Sources: `experiments/023-replica-bias/H12-pdk-cap.json` → `mc` (summary only —
the per-sample rows are **not** in the committed artifact),
`signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`

**Per-sample data**: re-generated for this pack by
`doc/paper/scripts/fig_mc.py`, which re-runs the identical campaign and stores
every draw in `doc/paper/figures/data/mc_samples.json`. The re-run reproduces
the certified summary to every printed digit (yield 0.82; `fc` mean 249.21037 /
σ 3.75782; `irn` mean 29.21810 / σ 0.19690; `p_core` mean 11.88686 / σ 0.20763;
`dc` mean −0.00815 / σ 0.00007) — see `figures/mc_hist.png`. The same script also
runs the paired post-layout campaign; see `results_layout.md` §7.

---

## 6. THD (S7)

### 6.1 Nine PVT corners, 175 mVpp differential at 50 Hz

| corner | T | VDD | THD (dB) | HD3 | HD2 |
|---|---|---|---|---|---|
| `mos_tt` | +27 | 1.50 | **−50.40** | −50.6 | −100.3 |
| `mos_ss` | +27 | 1.50 | **−47.68** | −47.9 | −102.6 |
| `mos_ff` | +27 | 1.50 | **−50.60** | −50.8 | −101.5 |
| `mos_sf` | +27 | 1.50 | **−51.90** | −52.2 | −106.3 |
| `mos_fs` | +27 | 1.50 | **−50.07** | −50.2 | −100.4 |
| `mos_tt` | +27 | 1.40 | **−47.28** | −47.5 | −106.4 |
| `mos_tt` | +27 | 1.65 | **−50.43** | −50.6 | −100.4 |
| `mos_tt` | 0 | 1.50 | **−47.29** | −47.6 | −104.8 |
| `mos_tt` | +70 | 1.50 | **−48.56** | −48.6 | −109.5 |

Worst **−47.28 dB** ⇒ **7.28 dB of S7 margin at every corner measured**. HD2 sits
at the bench numerical floor (≈ −100 dB), not at a device property — the layout
reviewer later proved this independently by showing a *pure reordering of the
extracted C cards* moves HD2 by 5.3 dB with THD/HD3 unchanged to 0.002 dB.

### 6.2 THD mismatch Monte Carlo, n = 30

| statistic | value |
|---|---|
| corner | `mos_tt_mismatch` + `cap_typ_mismatch`, 27 °C |
| mean | **−50.21 dB** |
| σ | 0.80 dB |
| worst | −48.17 dB |
| best | −51.57 dB |
| pass S7 | **30/30** |

### 6.3 Profile over fin (drive held at 175 mVpp — informative, only 50 Hz is S7)

| fin (Hz) | 20 | **50** | 100 | 150 | 200 |
|---|---|---|---|---|---|
| THD (dB) | −72.07 | **−50.40** | −21.78 | −20.19 | −21.34 |
| HD3 (dB) | −72.10 | −50.60 | −22.05 | −20.37 | −21.44 |

The 100–200 Hz points are a family property established in experiment 021: the
internal node of a stacked SSF biquad is a bandpass tap, so the stacked ladder is
≈ 20 dB worse than the un-stacked reference at 100 Hz. It is a topology
limitation, outside the S7 definition, and it must be stated in the paper rather
than omitted.

Sources: `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`; machine twin
`experiments/023-replica-bias/H12-pdk-cap.prelayout.json`
(`thd_corners` 9 rows, `thd_mc` 30 rows, `thd_profile` 5 rows) · drawn in
`figures/thd.png`

---

## 7. MIM capacitor corners

`cornerCAP.lib`, 27 °C / 1.5 V / `mos_tt`.

| cap corner | `iref` | `fc` | `dc` | `ripple` | `ph_max` | `a1000` | `irn` | verdict |
|---|---|---|---|---|---|---|---|---|
| `cap_typ` | ×1.0 | 249.8 | −0.008 | 0.052 | 332.4 | −49.0 | 29.2 | **PASS** |
| `cap_bcs` | ×1.0 | 277.1 | −0.008 | 0.013 | 331.0 | −45.3 | 29.2 | FAIL (S2 + S1 \|H\|@1k) |
| `cap_bcs` | ×0.9 | 250.6 | −0.008 | 0.070 | 331.0 | −48.9 | 30.6 | **PASS** |
| `cap_wcs` | ×1.0 | 227.3 | −0.008 | 0.121 | 333.6 | −52.4 | 29.2 | FAIL (S2) |
| `cap_wcs` | ×1.1 | 249.0 | −0.008 | 0.042 | 333.6 | −49.2 | 28.0 | **PASS** |

±10 % on `cap_carea` moves fc ∓10 % (fc ∝ g_m/C); a ±10 % `iref` trim (fc ∝ I in
weak inversion) restores every line. Shape (dc, ripple, phase) is unaffected.

**This is the corner that matters downstream:** the `cap_bcs ×0.9 + iref ×0.9`
point leaves only **1.00° of S1 margin** (331.0 vs 330.0), and it is exactly the
corner where the post-layout cell later misses S1 at 329.751° — see
`results_layout.md` §3.

Sources: `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`,
`experiments/023-replica-bias/H12-pdk-cap.prelayout.json` → `cap_corners`

---

## 8. Explicitly not covered at schematic level

Stated in the sign-off itself, and the reason the layout lane exists:

- Parasitic C/R of routing and of the MIM plates (the PDK model card says
  top/bottom-plate parasitics are *"included by parasiticC extraction"* — i.e.
  they are **not** in the schematic model).
- Well/substrate coupling of the floating differential capacitors.
- The real bias reference (α = 1.1 is a model, not a circuit).

Source: `signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`

---

## 9. The campaign that produced the cell

### 9.1 Experiments

Four numbered experiments exist — `000`, `020`, `021`, `023` (plus `_template/`).
There is **no** 001–019 or 022 directory; `022-reuse-final` is a *cell* delivered
inside experiment 021.

| # | technique | verdict | IRN | C total |
|---|---|---|---|---|
| `000-reference-baseline` | expert topology ported and re-sized to spec | CLOSED — certified reference | 50.18 µV (10 pts/dec) → 49.98 (50 pts/dec) | 98.01 pF |
| `020-novel-topologies` | branch stacking; the g_mf merge; the merge under a minimum-power ruling | CLOSED — CONFIRMED, 3 cells, 8/8 lines each. 020A 32.83 µV / 28.95 nW / 747.8 pF; **020B 34.14 µV / 9.70 nW / 314.6 pF / THD −49.83**; 020C 34.45 µV / 8.12 nW / 260.9 pF. 020A vs 020B isolates the merge: −66 % power, −58 % C, +6.3 dB THD for +1.31 µV noise | 32.83 µV (020A) | 260.9–747.8 pF |
| `021-publication-cell` | repair passband shape, then certify one cell on S1–S8 with corners + mismatch yield | CLOSED — CONFIRMED. `021-final` 30.71 µV / 6.01 nW / THD −42.22 / MC 78 %. Two harness defects found (non-contiguous `ph_max` band; the reference fails S3 densely). `022-reuse-final`: **28.07 µV, THD −56.46 dB, ph 341.42, 14.45 nW, 366.3 pF, MC 95 %** | 28.07 µV | 366.3 pF |
| `023-replica-bias` | PVT tolerance + yield: one shared 3-device replica of `gmf_b` + `bridge` generates the bridge-gate rail (topology `d`); headroom re-centred; caps re-fitted; second pass all-hv | CLOSED — **CONFIRMED on process and supply, FALSIFIED on temperature.** Replica takes the fc span from 14× (`E-combo`) / 3–38 × (family) to **1.01–1.02×**. −40…+125 °C is unreachable by any sizing at 1.5 V; α ≈ 1.1 flattens fc to 248–250 Hz over 110 K. Delivered `H12-robust` and `H5-lean` | 29.2 µV | 183 pF |

Measured replica tracking on `E-combo`: I_L **3.03 nA** vs sink **3.04 nA (0.4 %)**.

Sources: `doc/experiment-log.md`, `experiments/023-replica-bias/README.md`, `doc/campaign-report.md`

> **Number conflicts inside the repo, both real.** (a) `022-reuse-final` reads
> 28.07 µV / −56.46 dB / 14.45 nW in `doc/campaign-report.md` (pre-legalization
> sizing-history row) and 27.8663 µV / −56.183 dB / 14.5025 nW in the packaged
> `signoff/pre-pvt/scorecard.json` (after grid legalization + fc restore).
> (b) `doc/experiment-log.md` says H12 MC 83 % and `H5-lean` MC 55 % / THD −49.0
> / 140 pF; the sign-off measures 82 % and 67 % / −46.74 / 142.0 pF.
> **Quote the packaged sign-off JSON in a paper.**

### 9.2 S8 — the techniques combined

Three paper techniques from three papers (≥ 2 required). The replica bias is
textbook and is **not** claimed as an S8 technique.

| handle | paper | mechanism as used here |
|---|---|---|
| `gmc-compact` | *A compact subthreshold CMOS 2nd-order g_m-C lowpass filter* | two g_m's stacked in ONE bias branch (2× g_m at zero added current) → branch stacking |
| `tian2023` | *A Low-Noise and Low-Power Multi-Channel ECG AFE Based on Orthogonal Current-Reuse Amplifier* | cross-coupled current cancellation / drain-cross g_m scaling at constant bias → branch stacking |
| `fvf-2nd` | *0.6-V Sub-nW second-order lowpass filters using flipped voltage followers* | floating differential capacitor — measured worth **4×** on that element here, not the 2× the corpus index claimed |

Sources: `experiments/023-replica-bias/README.md` (paper row), `doc/target-spec.md`, `doc/campaign-report.md`

### 9.3 The sizing search — 37 points across 11 rounds, 24 met all nine lines

Round names: `qwalk`, `fitcells`, `scale`, `area`, `lvcm`, `lv065_bias`,
`unstacked75`, `vdd2_area`, `vdd2_bias`, `vdd2_bias2`, `reuse`. The full
37-row table (fc / mono / a1000 / ph / IRN / P / C / THD / MC / verdict per
point) is in `doc/sizing-history/rounds.md`, machine twin
`doc/sizing-history/rounds.json`.

Selected rows showing the noise-power-capacitance frontier:

| round | cell | `fc` | `a1000` | `ph` | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| fitcells | `020C-frozen` | 249.86 | −49.04 | 339.8 | 39.70 | 4.15 | 104.4 | −41.69 | — | PASS |
| area | `area_x1.69` | 249.87 | −49.60 | 333.3 | 30.71 | 6.01 | 150.6 | −42.22 | 78 % | PASS |
| lv065_bias | `sb3` | 249.85 | −49.78 | 332.8 | 28.54 | 6.46 | 164.0 | −42.39 | 84 % | PASS |
| reuse | `cr_0p1_4` | 249.86 | −50.35 | 331.6 | 29.34 | 7.31 | 187.9 | −52.29 | — | PASS |
| reuse | `cp_0p25_4` | 249.91 | −49.62 | 336.0 | 27.44 | 11.96 | 303.7 | −53.85 | — | PASS |
| reuse | `cp_0p16_2p5` | 249.99 | −49.55 | 341.4 | **28.07** | 14.45 | 366.3 | **−56.46** | — | PASS |

Source: `doc/sizing-history/rounds.md`

### 9.4 The pre-PVT variant ladder (nine sign-off cells, all pass all nine lines)

| cell | IRN µV | P nW | C pF | THD dB | `ph` ° | `fc` Hz | MC all-pass | σ(fc) Hz |
|---|---|---|---|---|---|---|---|---|
| `A-minarea` | **39.695** | **4.146** | **104.41** | −41.684 | 339.77 | 249.856 | 45 % | 5.070 |
| `B-balanced` | 29.376 | 6.010 | 152.85 | −41.944 | 332.23 | 250.010 | 70 % | 3.319 |
| `C-lownoise` | 28.558 | 6.379 | 164.00 | −41.691 | 333.04 | 248.141 | 75 % | 2.707 |
| `D-thdjump` | 28.813 | 7.470 | 187.86 | −52.485 | 330.66 | 250.003 | 75 % | 2.140 |
| `E-combo` | 27.268 | 8.881 | 220.02 | −54.878 | 334.63 | 249.876 | 92 % | 2.761 |
| `E1-prev` | 28.210 | 9.014 | 229.35 | −52.604 | 333.30 | 250.002 | **96 %** | 2.199 |
| `F-minnoise` | **26.243** | 12.628 | 305.02 | −58.515 | 336.41 | 249.947 | 93 % | 2.753 |
| `G-maxthd` | 26.807 | 14.324 | 348.22 | **−70.984** | 343.53 | 249.879 | 90 % | 2.997 |
| `H-shipped` | 27.866 | 14.503 | 366.26 | −56.183 | 341.30 | 249.994 | 95 % | 2.350 |

None of these nine is corner-robust: every one is 1–2/22 on the PVT screen and
VDD_min 1.5 V. That is what experiment 023 fixed.

Source: `signoff/pre-pvt/COMPARISON.md` and `signoff/pre-pvt/<cell>/scorecard.json`

### 9.5 The post-PVT four (the cells that survived 023)

| | `H5-lean` | `H5-pdk-cap` | `H12-robust` | **`H12-pdk-cap`** |
|---|---|---|---|---|
| capacitors | ideal | PDK MIM | ideal | **PDK MIM** |
| ladder current I_L (replica m) | 1.98 nA (m=3) | 1.98 nA | 2.65 nA (m=4) | 2.65 nA |
| vicm / vocm (V) | 0.22 / 1.25 | 0.22 / 1.25 | 0.24 / 1.28 | 0.24 / 1.28 |
| **IRN (µVrms)** | 30.084 | 30.085 | 29.201 | **29.199** |
| **P core (nW)** | 8.935 | 8.935 | 11.912 | **11.913** |
| C total (pF) | 142.01 | 141.94 | 183.73 | **183.78** |
| **THD (dB)** | −46.743 | −46.723 | −50.676 | **−50.401** |
| `ph_max` / `a1000` | 332.56 / −49.26 | 332.53 / −49.26 | 332.32 / −48.99 | **332.38 / −49.03** |
| process corners | 4/4 PASS, fc 247.2–252.6 | " | 4/4 PASS, fc 247.4–252.6 | **4/4 PASS** |
| supply window | **1.35–1.65 V** | " | 1.40–1.65 V | **1.40–1.65 V** |
| temperature window | **−20 … +55 °C** | " | 0 … +70 °C | **0 … +70 °C** |
| one-axis / reduced / full | 7/9 · 8/22 · 18/45 | " | 6/9 · 6/22 · 16/45 | **6/9 · 6/22 · 16/45** |
| **MC all-pass** | 67 % | 64 % | 82 % | **82 %** |
| all S1–S8 | PASS | PASS | PASS | **PASS** |

`H12-pdk-cap` was taken to layout because it has the best mismatch yield and the
best THD; `H5-lean` is the low-power alternative (−25 % core power for +0.9 µV
IRN and +3.7 dB THD). Its `why` field, verbatim: *"H12-robust with the PDK MIM
capacitors (cap_cmim): re-fitted through the real model. THD −50.4, all process
corners, MC 82 %. The cell to take to layout."*

Sources: `signoff/post-pvt/README.md`, the four `scorecard.json` files

---

## 10. Campaign scale — what is defensible

The run ledger `runs/ledger.ndjson` is **gitignored** (local observability only)
and on disk holds **253 rows over three days** — overwhelmingly THD re-runs of the
final cell. It cannot support a "total simulations in the campaign" claim. Use
these instead, all from committed evidence:

| measure | value | source |
|---|---|---|
| sizing points attempted (pre-PVT arc) | **37 across 11 rounds; 24 met all nine lines** | `doc/sizing-history/rounds.md` |
| candidate sizing JSONs in experiment 023 alone | **131** | `experiments/023-replica-bias/` |
| sign-off cells packaged | **13** (9 pre-PVT + 4 post-PVT), each with scorecard, as-built decks and two identity gates | `signoff/` |
| PVT grids per post-PVT cell | 9-point one-axis, 22-point reduced, 45-point full, plus 9-step supply and 9-step temperature envelopes | `signoff/post-pvt/README.md` |
| Monte Carlo | n = 100 per cell (13 cells) + n = 30 THD MC on the cell of record | `signoff/*/COMPARISON.md`, `PRELAYOUT.md` |
| layout-brief sensitivity evaluations | **273 ac+noise + 8 THD** on one cell | `layout/H12-pdk-cap/BRIEF.md` |
| layout optimizer trials | **600** (2 × 300) | `layout/H12-pdk-cap/opt/results/` |

---

## 11. Gaps at schematic level

See `README.md` §5 for the full gap list with commands and effort. The
schematic-side ones:

1. No `PRELAYOUT.md` for `H12-robust` — only `H12-pdk-cap` has the full report.
2. No per-sample MC data was committed; this pack regenerates it
   (`figures/data/mc_samples.json`) but the artifact is not in the repo's own
   sign-off.
3. No THD-vs-amplitude sweep at 50 Hz (only THD at one drive level over corners /
   MC / fin) — a reviewer will ask for the 1 % / −40 dB compression point.
4. No PSRR, no CMRR, no input-referred offset, no noise-vs-corner *spectrum*
   (only the integrated IRN per corner).
5. No comparison table against published sub-nW filters — the papers cited for S8
   are technique sources, not benchmarked competitors.
