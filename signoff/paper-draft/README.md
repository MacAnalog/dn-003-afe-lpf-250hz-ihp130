# Reviewer response pack — equations, poles/zeros, noise, linearity

**[REFERENCE]** — the answer to [`request.md`](request.md), for the delivered
4th-order 250 Hz SSF low-pass filter (IHP SG13G2, VDD = 1.5 V), **pre-layout and
post-layout**.

Everything here is derived from committed netlists and can be regenerated with the commands
in §5.  Every number is quoted with the script and the artifact that produced it.

## Start here

You do not need to read all of this, or to run anything.

1. **§1 below** is your `request.md`, one row per request, linked to where it is answered.
2. **[`validation.md`](validation.md)** holds the numbers and the checks; **[`theory.md`](theory.md)**
   holds the derivations behind them.  Follow the links in §1 rather than reading either
   file in order.
3. **[`csv/`](csv/README.md)** is every curve as a plain CSV for Veusz — magnitude, phase,
   noise, group delay, THD/HD2/HD3, IIP3, and everything in §8–§10 below.  Open
   [`csv/README.md`](csv/README.md) for one line per plot; §4 below summarises it.
4. `figures/` holds the same curves plotted, as PNG and PDF.
5. **[validation §8–§10](validation.md#8-the-analytical-results-over-pvt-and-mismatch)**
   answer questions you did not ask: how the poles, `Q`, the noise budget, IIP3 and THD
   move over PVT and mismatch, pre- and post-layout; PSRR, CMRR and offset; and a test of
   the mechanism behind the low-frequency residual §6.2 reports.

§5–§7 are for reproducing the pack and are not needed to review it.

| file | what it is |
|---|---|
| [`theory.md`](theory.md) | **the derivations** — `H(s)`, the noise equation, the distortion equation, IMD3/IIP3, and the list of assumptions.  Hand-written; symbolic; not regenerated. |
| [`validation.md`](validation.md) | **every number, and what checks it** — DC operating point, poles/zeros, model-vs-simulation, the noise budget, the linearity tables.  **Generated** by `scripts/report.py`; do not hand-edit. |
| `figures/` | the thirteen figures, PNG + PDF |
| `scripts/` | the generating scripts (§5) |
| [`csv/`](csv/README.md) | **every curve as a plain CSV for plotting** (§4) |
| `data/` | the extracted and analysed JSON (§6) |

---

## 1. The request, answered

| # | reviewer's request | answer | where |
|---|---|---|---|
| 1 | **transfer function** | exact symbolic 4th-order `H(s)`, and the identity `D(s) = D_A·D_B + κ·s²` proved by symbolic expansion (residual exactly 0) | [theory §2.2](theory.md#22-the-result), numbers in [validation §2.1](validation.md#21-the-closed-form-at-the-measured-operating-point) |
| 2 | **noise equation** | `S_out = Σ_k \|Z_T,k\|²·S_i,k`, `IRN² = ∫S_out/\|H\|²`, with each generator's port established from the data | [theory §3](theory.md#3-the-noise-equation), [validation §5](validation.md#5-the-noise-equation-checked-generator-by-generator) |
| 3 | **THD / linearity equation** | `HD3(ω) = \|Σ_k Z_T,k(j3ω)·I_D,k·2I₃(a_k)/I₀(a_k)\| / \|V_out,fund\|` from the weak-inversion exponential, with a stated validity window | [theory §4](theory.md#4-the-distortion-equation), [validation §6.1–6.2](validation.md#61-hd3-versus-amplitude--the-a²-law) |
| 4 | **pole / zero locations** | 4 poles (2 complex pairs), 4 zeros (2 complex pairs), 7 pole–zero cancellations reported with their residuals; pre- and post-layout | [validation §4](validation.md#4-poles-and-zeros--the-map) |
| 5 | **Q of each biquad** | given **twice**: isolated-stage Q (2.10 / 0.46) and the filter's pole-pair Q (**0.543 / 1.307**, close to Butterworth).  The two differ because the current-reuse bridge contributes `κ` = 11.78 % of the quartic's `s²` coefficient; the closed form gives the relation. | [theory §2.3](theory.md#23-per-biquad-f₀-and-q--and-which-q-the-reviewer-should-be-given), [validation §2.1](validation.md#21-the-closed-form-at-the-measured-operating-point) |
| 6 | **IIP3, IMD3** | IIP3 = **−3.28 dBV** pre-layout, **−3.35 dBV** post-layout, from a 5-point two-tone ladder with a verified 3:1 slope; IMD3 tabulated, plus a spacing sweep | [theory §5](theory.md#5-imd3-and-iip3), [validation §6.3](validation.md#63-two-tone-imd3-and-iip3) |
| 7 | **proof of the equations, checked against sim** | see the table in §2 below — every equation is checked numerically against the simulator | [validation §3, §5.1, §6](validation.md#3-model-versus-simulation) |
| 8 | **pole/zero plane plot; real or imaginary; verified by DC ops and sim data** | `figures/pz_plane.png`, plus **three independent checks** — see §3 below | [validation §3.2, §4](validation.md#32-what-the-simulation-says-about-the-poles-on-its-own) |

The topology identification in `request.md` needed no action; the device-level reading is
restated in [theory §1.1](theory.md#11-the-cell) so the equations can be read against it.

---

## 2. "The proof of the equations" — the closures, in one table

Each equation is checked against the simulator.  These are the numbers to look at first.

| equation | check | pre-layout | post-layout |
|---|---|---|---|
| `H(s)` | max Δ\|H\| vs the ac sweep, dc–1 kHz | **0.0267 dB** | 0.0265 dB |
| `H(s)` | max Δφ vs the ac sweep, dc–1 kHz | **0.3448°** | 0.3427° |
| `H(s)` | max Δ group delay, dc–1 kHz | 0.997 % | 1.023 % |
| `D = D_A·D_B + κs²` | symbolic residual after expansion | **exactly 0** | — |
| `H(0) = 1` | closed form vs full model / simulator | 1 vs −0.008148 dB (finite `ro`) | same |
| noise `Σ_k` | max Δ`S_out` vs the simulator's own total, per frequency | **2.0·10⁻⁷ %** | 2.0·10⁻⁷ % |
| noise | integrated IRN vs the certified sign-off number | **exact** (29.1990 µV) | exact (29.1959 µV) |
| `Z_T` | `netlist2tf.transimpedance` vs the independent pencil solve | 1.7·10⁻⁸ | 2.6·10⁻⁹ |
| `HD3 ∝ A²` | fitted slope vs 40 dB/decade | **42.63** (resid 0.51 dB) | — |
| `HD3(ω)` | model vs measured, 35–65 Hz | **±2 dB** | — |
| IMD3 slope | fitted vs 40 dB/decade | **41.71** (resid 0.26 dB) | 42.29 (resid 0.20 dB) |
| IIP3 | spread over the three amplitudes inside the validity window | 0.52 dB | 0.69 dB |

---

## 3. "Real or imaginary — verified by the DC ops and the sim data"

The reviewer asked for the pole/zero plane **and** for it to be verified two ways.  Three
independent checks are given:

1. **From the DC operating point.**  One `.op` on the as-built netlist gives every device's
   `gm`, `ro` and capacitances ([validation §1](validation.md#1-the-dc-operating-point--the-root-of-every-number-below));
   those fill the MNA pencil, and the poles are its generalised eigenvalues.  Every symbol
   in every equation comes from that one table.
2. **From the simulation data, as a falsification test.**  A 4-pole rational is fitted to
   the measured complex response — no model, no netlist, no operating point.  It fits to
   0.215 dB.  Refitting with both Q's forced ≤ 0.5, i.e. **all four poles real**, the best
   residual is **4.85 dB / 52°**, with both Q's at the bound.  So **the measured response
   cannot be produced by any all-real-pole 4th-order model**: the poles are complex, from
   the simulation data alone
   ([validation §3.2](validation.md#32-what-the-simulation-says-about-the-poles-on-its-own)).
3. **From the model overlay.**  The operating-point model is evaluated at every ac point and
   compared with the sweep: 0.027 dB, 0.34°, 1 % on group delay.

`ngspice`'s own `.pz` cannot be used here: it aborts with *"the input signal is shorted
on the way to the output"* for any input port carrying its dc bias, which a subthreshold
gate must; confirmed on a one-transistor deck, so it is the analysis and not the netlist.
The three checks above replace it.

**The answer:** four poles, **two complex-conjugate pairs**, at
(249.72 Hz, Q 0.543) and (251.08 Hz, Q 1.307) pre-layout — a Butterworth-like quartic
realised by frequency-coincident, differently damped sections.  Four zeros, **two complex
pairs**, at 3.85 kHz and 5.05 kHz, both far out of band, both traced by ablation to the
followers' gate–source capacitance.  Post-layout the poles move to (248.18 Hz, Q 0.546) and
(249.97 Hz, Q 1.304); the description above is otherwise unchanged.

### Figures

| figure | what it shows | script |
|---|---|---|
| `figures/half_circuit.png` | the DM half-circuit the algebra describes, each branch labelled with its equation symbol, the `κ` loop in red | `scripts/figures.py::fig_half_circuit` |
| `figures/pz_plane.png` | the pole/zero plane, both conjugate members, pre- vs post-layout, cancellations hollow | `scripts/figures.py::fig_pz` |
| `figures/bode_model_vs_sim.png` | \|H\| and phase, model over simulation, plus the residual | `scripts/figures.py::fig_bode` |
| `figures/noise_budget.png` | `S_out(f)`, the sum of generators, and the top contributors — one colour per mechanism, so `idid` and `igig` share one | `scripts/figures.py::fig_noise` |
| `figures/distortion.png` | HD3 vs amplitude and vs frequency, measured against the equation | `scripts/figures.py::fig_thd` |
| `figures/iip3.png` | the two-tone ladder and the IIP3 extrapolation | `scripts/figures.py::fig_iip3` |
| `figures/pvt_axes.png` | `fc` and both `Q` over the nine certified points, pre- and post-layout; and the 45-point box with the lost pairs marked | `scripts/figures.py::fig_pvt` |
| `figures/mc_mismatch.png` | the mismatch distributions of `fc`, `Q` and input-referred offset | `scripts/figures.py::fig_mc` |
| `figures/rejection.png` | the transfers CMRR and PSRR are built from, the mismatch-limited band itself, and the nominal common-mode paths | `scripts/figures.py::fig_rejection` |
| `figures/gds_residual.png` | what §6.2 leaves unexplained, and the two `g_ds` predictions against it | `scripts/figures.py::fig_residual` |
| `figures/iip3_corners.png` | IIP3 and the measured IMD3 slope at every certified corner | `scripts/figures.py::fig_iip3_corners` |
| `figures/thd_corners.png` | the THD amplitude ladder at every certified corner, and the margin at the spec point | `scripts/figures.py::fig_thd_corners` |
| `figures/mc_convergence.png` | running σ against draw count for both Monte Carlo populations, inside the band a σ estimated from N draws is allowed to wander in | `scripts/figures.py::fig_mc_convergence` |

---

## 4. The data as CSV

Every requested curve is in [`csv/`](csv/README.md) as a plain CSV — one header row, then
numbers, so Veusz imports it with no options changed.  Column names include the unit and
end with the DUT (`_pre_mim`, `_post_pex`, …).

| plot | file | x | y |
|---|---|---|---|
| AC response, magnitude and phase | `csv/ac_response.csv` | `f_hz` | `mag_db_*`, `phase_deg_*` |
| Input-referred noise vs frequency | `csv/input_referred_noise.csv` | `f_hz` | `inoise_v_per_rthz_*` |
| the noise budget: which device, which mechanism | `csv/noise_by_device_and_type.csv` | `device` (text) | `irn_uv_rms`, `pct_of_power` |
| Group delay | `csv/group_delay.csv` | `f_hz` | `group_delay_ms_*` |
| THD / HD3 / HD2 vs amplitude | `csv/thd_vs_amplitude.csv` | `vpp_diff_v` | `thd_db_*`, `hd3_db_*`, `hd2_db_*` |
| the distortion-limited drive and the dynamic range it sets | `csv/linearity_crossings.csv` | `target_db` | `vpp_diff_v`, `dr_db` |
| THD / HD3 / HD2 vs frequency | `csv/thd_vs_frequency_175mvpp.csv` | `fin_hz` | `thd_db_*`, `hd3_db_*`, `hd2_db_*` |
| IIP3, output dBVp vs input dBVp | `csv/iip3_twotone.csv` | `pin_dbvp_*` | `pout_fund_dbvp_*`, `pout_imd3_dbvp_*` |
| `fc` and `Q` over the certified axes, pre- and post-layout | `csv/pvt_certified_axes.csv` | `corner` | `fc_hz_*`, `q_lo_*`, `q_hi_*` |
| the same over the 45-point box | `csv/pvt_cert_box.csv` | `corner` | `fc_hz`, `q_hi`, `n_complex_pairs` |
| the mismatch draws | `csv/mc_draws.csv` | `seed` | `fc_hz`, `q_hi`, `offset_in_uv` |
| PSRR / CMRR / common-mode transfers vs frequency | `csv/rejection_nominal.csv` | `freq_hz` | `psrr_db`, `cmrr_db`, `supply_to_cm_db`, … |
| the mismatch-limited rejection band | `csv/rejection_mismatch_curves.csv` | `freq_hz` | `psrr_db_mean`, `psrr_db_min`, `psrr_db_max`, … |
| IIP3 over corners | `csv/iip3_corners.csv` | `corner` | `iip3_dbv`, `imd3_slope_db_per_decade` |
| the THD ladder over corners | `csv/thd_corners.csv` | `vpp_diff_v` | `thd_db_<corner>`, `hd3_db_<corner>` |
| the low-frequency residual and both `g_ds` predictions | `csv/gds_residual.csv` | `fin_hz` | `v3_unexplained_uv`, `v3_gds_cubic_uv`, `v3_gds_exact_uv` |
| running σ against draw count, both MC populations | `csv/mc_convergence.csv` | `n_draws` | `sigma_fc_hz`, `sigma_q_hi`, `sigma_cmrr_db_dc`, … |

Four more files support those: the modelled Bode curves that overlay the simulated
ones, the harmonic-vs-frequency sweep repeated at the small-signal drive, the 1:1 / 3:1
IIP3 extrapolation lines, and the per-draw rejection samples.
[`csv/README.md`](csv/README.md) covers all twenty-one, plus five points to note before
plotting: why the corner files carry a text column, that CMRR and PSRR are ratios whose
two halves are exported beside them, why the phase and group-delay columns are blank above
3 kHz, which two-tone points the published IIP3 is fitted on, and why a worst case is not
a converged number.

`export_csv.py` writes them.  It runs no simulation and re-defines no metric: it
re-serialises the same JSON the figures and tables are built from, and asserts that the
CSVs reproduce the certified group delay, integrated noise and IIP3.

---

## 5. Regenerating everything

The symbolic lane needs `spicexplorer_netlist2tf`, so it runs in the **platform** venv; the
simulation lane runs in this repo's venv.  **Set the ngspice lane first** — the default is
the Docker lane, and on a host without a usable Docker socket every simulation step fails
with `rc=126` (see [`doc/environment.md`](../../doc/environment.md)):

```bash
export LPF_NGSPICE=/path/to/ngspice PDK_ROOT=/path/to/pdks   # native lane; omit for Docker
```

Then, from the repo root:

```bash
# 1. simulation lane -- op + ac + per-generator noise for all four DUTs   (~2 min)
.venv/bin/python signoff/paper-draft/scripts/extract_bench.py
# 2. simulation lane -- THD ladder, THD profile, two-tone, spacing sweep  (~25 min)
.venv/bin/python signoff/paper-draft/scripts/linearity_runs.py
.venv/bin/python signoff/paper-draft/scripts/twotone_spacing.py
.venv/bin/python signoff/paper-draft/scripts/hd3_vs_fin.py
# 3. symbolic lane -- transfer function, poles/zeros, noise, distortion   (~8 min)
PF=../../spicexplorer-platform/.venv/bin/python
$PF signoff/paper-draft/scripts/tf_analysis.py
$PF signoff/paper-draft/scripts/noise_analysis.py
$PF signoff/paper-draft/scripts/linearity_analysis.py
# 4. the pack
#    report.py is stdlib-only but needs Python >= 3.12 (it uses backslash escapes inside
#    f-string expressions), so it runs in the REPO venv, not the platform's 3.11 one.
.venv/bin/python signoff/paper-draft/scripts/report.py   # rewrites validation.md
$PF signoff/paper-draft/scripts/figures.py               # rewrites figures/
# 5. the CSVs (needs step 1; no simulation, seconds)
.venv/bin/python signoff/paper-draft/scripts/export_csv.py   # rewrites csv/
# 6. PVT / mismatch / rejection / distortion mechanism -- the §8-§10 material.
#    LPF_BIAS_ALPHA=1.1 is the constant-gm bias the cells were certified with; without it
#    the temperature rows measure an UNCOMPENSATED cell.
#    OMP_NUM_THREADS=1 is not optional for the Monte Carlo: ngspice takes ~11 threads per
#    process by default, so LPF_JOBS workers ask for 11x LPF_JOBS threads and the host
#    thrashes -- 5 draws/min instead of ~110.  One thread per worker and ~32 workers is
#    the fast setting here.  ~15 min for the two 1024-draw runs.
E="signoff/paper-draft/scripts"
export OMP_NUM_THREADS=1 LPF_JOBS=32
for s in cert-axes cert-box both; do
  LPF_BIAS_ALPHA=1.1 .venv/bin/python $E/extract_bench.py --pvt $s --dut pre_mim
done
.venv/bin/python $E/extract_bench.py --mc 1024 --dut pre_mim   # ~10 min
LPF_BIAS_ALPHA=1.1 .venv/bin/python $E/extract_bench.py --pvt cert-axes --dut post_lumped
.venv/bin/python $E/psrr_cmrr.py --seeds 1024
.venv/bin/python $E/gds_probe.py
LPF_BIAS_ALPHA=1.1 .venv/bin/python $E/iip3_corners.py
LPF_BIAS_ALPHA=1.1 .venv/bin/python $E/thd_corners.py    # 54 transients, ~20 min
$PF $E/pvt_analysis.py --mc --set cert-axes --set cert-box --set both
$PF $E/pvt_analysis.py --set cert-axes --dut post_lumped
$PF $E/gds_residual.py
```

Steps 4 and 5 come last: `report.py`, `figures.py` and `export_csv.py` all read the JSON
step 6 writes.

| script | role |
|---|---|
| `extract_bench.py` | one `op` deck and one `ac`+`noise` deck per DUT; per-instance operating point, per-generator noise vectors, and the `post_lumped` netlist |
| `n2tf_model.py` | the only place that converts an as-built subckt into an MNA system at the measured operating point; the DM half-circuit; the symbol renaming |
| `pencil.py` | poles, zeros, `H(jω)` and `Z_T` from the matrix pencil `G + sC` |
| `tf_analysis.py` | the symbolic `H(s)`, the factorisation proof, the pole/zero locations, the capacitance ablation, the validation and the sim-only fit |
| `noise_analysis.py` | per-generator port identification, the noise equation, the closure and the transimpedance cross-check |
| `linearity_runs.py`, `twotone_spacing.py`, `hd3_vs_fin.py` | the transient benches |
| `linearity_analysis.py` | the HD3 model, the amplitude/frequency laws, the memoryless test, IIP3 |
| `report.py` | renders `validation.md` |
| `figures.py` | renders `figures/` |
| `export_csv.py` | renders `csv/` — every curve as a plain CSV, with the cross-checks that tie them to the certified numbers |
| `pvt_analysis.py` | the poles, per-biquad `Q` and noise budget at every corner and every mismatch draw (§8) |
| `psrr_cmrr.py` | PSRR, CMRR and input-referred offset, nominal and mismatch-limited (§9) |
| `gds_probe.py`, `gds_residual.py` | the drain-conductance distortion test: per-device `I_D(V_DS)` curves, then the third harmonic they generate, propagated (§10.1) |
| `iip3_corners.py` | IIP3 over the certified axes, two amplitudes per corner (§10.2) |
| `thd_corners.py` | the THD amplitude ladder over the certified axes (§10.3) |
| `mc_stats.py` | how much a σ estimated from N draws is allowed to move, and the running traces that show whether it did |
| `gate_leakage_probe.py` | one device, one load: the gate current is exactly zero, the model's gate-leakage generators `igs`/`igd` are exactly zero, and `idid` + `igig` is the full shot noise `2qI_D` (§5.2) |

---

## 6. What is committed, and what is regenerated

Committed: the scripts, the figures, the CSVs, `validation.md`, `theory.md`, and the small
analysis JSON (`tf.json`, `noise.json`, `linearity*.json`, `twotone_spacing.json`, `hd3_vs_fin.json`,
`post_lumped_core.sp`, and for §8–§10 `pvt.json`, `psrr_cmrr.json`, `gds_taylor.json`,
`gds_residual.json`, `iip3_corners.json`, `thd_corners.json`, `pvt_index_*.json`, `mc_index_*.json`).  **Not committed**: `data/bench_*.json` — the raw op + ac + noise
vectors, 2.7 MB for the four nominal DUTs and ~90 MB more for the 156 per-corner and
per-draw extractions, regenerated by steps 1 and 6 above, and simulator output under the
repo's never-commit rule.  If they are absent, every downstream script names the missing
path: `tf_analysis.py` prints `[<case>] SKIPPED` and continues, and the `report.py` render
then raises on the missing case, so a stale `validation.md` cannot be produced silently.

The four DUTs — two pre-layout, two post-layout — and why each exists are in
[validation §7](validation.md#7-the-four-duts-side-by-side).

---

## 7. Open items

* **The low-frequency third-harmonic residual — narrowed, not closed.**  Below ~35 Hz the
  measured third harmonic exceeds the distortion equation by **0.18–0.28 µV, constant in
  volts**, while the equation's own prediction moves by a factor of 39 over the same span.
  §10.1 tests the mechanism named for it.  Drain-conductance curvature reproduces the flat
  frequency signature — the prediction varies 1.39× where the residual varies 1.59× — but
  not the size.  The `g₃` the pre-registered test used moves 5.4× with the interval it is
  fitted over, so §10.1 also evaluates the third harmonic **without a fit window**, over
  each device's own drain swing.  That resolves the ambiguity and makes the answer smaller:
  the mechanism accounts for about **a fifth** of the residual, so it is established as *a*
  contributor and excluded as the whole of it.  The probe pins the gate by construction, so
  the untested candidate for the rest is the gate–drain cross-term.  The residual still sits
  **61.7 dB below** the 256 µV third harmonic this cell produces at the S7 operating point,
  so it remains a modelling gap and not a performance one.
* **Corners and Monte Carlo — measured for the analytical quantities.**  §8 gives the
  poles, per-biquad `Q`, the pair-coincidence ratio and the noise budget over the certified
  window and 64 mismatch draws; §10.2 gives IIP3 and §10.3 the THD amplitude ladder over
  the certified axes.  The post-layout DUT is no longer an assumption: §8.4 re-runs the
  nine certified axes on `post_lumped` and the sensitivity spans agree with the pre-layout
  ones to the third decimal.  What §8 does report as a narrowing of the earlier claim is
  that only the LOW-Q pair's damping is stiff — the high-Q pair's `Q` moves about as much
  as `fc` does, and almost all of it over the temperature axis.
* **The certified window is one axis at a time, and the axes do not superpose.**  §8.1:
  7 of the 45 cross-product points lose a complex pole pair, including `tt / 0 °C /
  1.40 V`, whose three coordinates are each individually inside the certified window.
  Reading the sign-off numbers as a BOX is not supported by the evidence that exists.
* **PSRR / CMRR / offset — measured** (§9): both ratios are taken to the DIFFERENTIAL
  output — `CMRR = A_dm / A_(cm→dm)`, `PSRR = A_dm / A_(vdd→dm)` — and the transfers they
  are built from are tabulated and plotted beside them; the common-mode-to-common-mode
  paths are reported separately, as a different quantity.  Two results worth carrying:
  the output common mode tracks the supply almost one-for-one at 1 kHz (−0.14 dB), and
  the input-referred offset has σ ≈ 2.1 mV, 1.2 % of the S7 drive.  Neither is a specified quantity, so neither
  carries a pass/fail.
