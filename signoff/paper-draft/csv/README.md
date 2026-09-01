# CSV data for plotting

**[REFERENCE]** — every curve in this pack as a CSV, for Veusz or any other plotting
tool.  Same numbers as the figures and tables in [`../validation.md`](../validation.md);
nothing here is a re-measurement.

## Opening one in Veusz

*Data → Import…*, pick the file, leave the CSV settings at their defaults (data in
columns, dataset names in the first row), *Import*.  Each column becomes a dataset named
after its header; pick an x and a y — say x `f_hz`, y `mag_db_post_pex`.

There are no comment lines, no units row and no blank first line, so the defaults work.

## Which file answers which request

`*` in the table stands for a DUT suffix; *Reading the column names* below lists all four.

| you asked for | file | x | y |
|---|---|---|---|
| **AC response — Bode magnitude** | `ac_response.csv` | `f_hz` | `mag_db_*` |
| **AC response — Bode phase** | `ac_response.csv` | `f_hz` | `phase_deg_*` |
| **Input-referred noise vs frequency** | `input_referred_noise.csv` | `f_hz` | `inoise_v_per_rthz_*` |
| **Where the noise comes from — device by device** | `noise_by_device_and_type.csv` | `device` (text) | `irn_uv_rms`, `pct_of_power` |
| **Group delay** | `group_delay.csv` | `f_hz` | `group_delay_ms_*` |
| **THD / HD3 vs amplitude** | `thd_vs_amplitude.csv` | `vpp_diff_v` or `ampl_v` | `thd_db_*`, `hd3_db_*` |
| **the drive at a distortion limit, and the resulting DR** | `linearity_crossings.csv` | `target_db` | `vpp_diff_v`, `dr_db` |
| **HD2 vs amplitude** | `thd_vs_amplitude.csv` | `vpp_diff_v` or `ampl_v` | `hd2_db_*` |
| **THD / HD3 vs frequency** | `thd_vs_frequency_175mvpp.csv` | `fin_hz` | `thd_db_*`, `hd3_db_*` |
| **HD2 vs frequency** | `thd_vs_frequency_175mvpp.csv` | `fin_hz` | `hd2_db_*` |
| **IIP3 — output dBVp vs input dBVp** | `iip3_twotone.csv` | `pin_dbvp_*` | `pout_fund_dbvp_*`, `pout_imd3_dbvp_*` |

The files behind [`../validation.md`](../validation.md) §8–§10 — PVT, mismatch, rejection
and the corner sweeps:

| you asked for | file | x | y |
|---|---|---|---|
| **`fc` and `Q` over the certified window** | `pvt_certified_axes.csv` | `corner` (text) | `fc_hz_pre`, `q_lo_pre`, `q_hi_pre`, and the `_post` twins |
| **the 45-point cross product, and where a pole pair is lost** | `pvt_cert_box.csv` | `corner` (text) | `fc_hz`, `q_hi`, `n_complex_pairs` |
| **the mismatch distributions** | `mc_draws.csv` | `seed` | `fc_hz`, `q_lo`, `q_hi`, `offset_in_uv` |
| **PSRR and CMRR vs frequency** | `rejection_nominal.csv` | `freq_hz` | `psrr_db`, `cmrr_db` |
| **the transfers those ratios are made of** | `rejection_mismatch_curves.csv` | `freq_hz` | `a_dm_db_mean`, `cm_to_dm_db_mean`, `supply_to_dm_db_mean` |
| **supply → common-mode and CM → CM** | `rejection_nominal.csv` | `freq_hz` | `supply_to_cm_db`, `cm_to_cm_db` |
| **the mismatch-limited rejection band** | `rejection_mismatch_curves.csv` | `freq_hz` | `psrr_db_mean` with `_min` / `_max` |
| **offset, per draw** | `rejection_mismatch_draws.csv` | `seed` | `offset_in_uv` |
| **IIP3 over corners** | `iip3_corners.csv` | `corner` (text) | `iip3_dbv`, `imd3_slope_db_per_decade` |
| **the THD ladder over corners** | `thd_corners.csv` | `vpp_diff_v` | `thd_db_<corner>`, `hd3_db_<corner>` |
| **the low-frequency residual, and what explains it** | `gds_residual.csv` | `fin_hz` | `v3_unexplained_uv`, `v3_gds_cubic_uv`, `v3_gds_exact_uv` |
| **whether the Monte Carlo has converged** | `mc_convergence.csv` | `n_draws` | `sigma_fc_hz`, `sigma_q_hi`, `sigma_offset_in_uv_extraction`, `sigma_cmrr_db_dc`, … |

The remaining files support those:

* `thd_vs_frequency_43p75mvpp.csv` — the same harmonic-vs-frequency sweep at 43.75 mVpp
  instead of 175 mVpp, where distortion is still cubic in amplitude.  This is the sweep
  the distortion equation is checked against.
* `linearity_crossings.csv` — the drive at which distortion reaches a stated limit, and
  the dynamic range that follows.  Three rows: HD3 = −60 dB on both DUTs, and the
  THD = −40 dB compression point.  Each carries the fit it was solved from —
  `vpp_diff_v = anchor_vpp_diff_v · 10^((target_db − anchor_db)/slope_db_per_decade)` — so
  the number can be checked without refitting.  The HD3 target sits **between** two
  measured amplitudes, and `bracket_vpp_diff_v` is an independent log-linear interpolation
  between them; the THD one is past the compression knee and has no bracket, which is why
  that cell is blank.  `dr_db` is `20·log10(vrms_v / irn_uv_rms)` against the same DUT's
  certified 0.5–200 Hz noise.  **A dynamic range is only comparable against another design
  measured to the same criterion** — this one is HD3 = −60 dB at f_in = 50 Hz, differential
  peak-to-peak converted to rms as `V_pp/(2√2)`.  `fom_fj` is `P/(N·f_c·DR)` in fJ and
  inherits that criterion.  `measured_hd3_db` is the crossing **re-simulated at exactly
  the solved drive** (`scripts/hd3_crossing_probe.py`), so `measured_err_db` says how far
  the solved number is from a measured one rather than leaving you to trust the fit.
* `iip3_extrapolation.csv` — the two extrapolation lines, so you need not fit anything.
  Two rows: the low-amplitude end, then the intercept.  Plot `fund_line_dbvp_*` (slope 1)
  and `imd3_line_dbvp_*` (slope 3) against `x_dbvp_*`; they meet at the published intercept.
* `ac_response_model.csv` — the closed-form model next to the simulation, the data behind
  `figures/bode_model_vs_sim.png`.  Columns come in `_sim_` / `_model_` pairs.
* `noise_by_device_and_type.csv` — the noise budget of
  [`../validation.md` §5.2](../validation.md#52-where-the-noise-comes-from) with nothing
  folded away: one row per DUT per device per *named* generator, 79 generators on 18
  devices, for `pre_ideal`, `pre_mim` and `post_lumped`.  `mechanism` is the physical
  grouping — note that `idid` and `igig` are two halves of ONE channel thermal generator
  and both carry `mechanism = channel_thermal`; `igig` is **not** gate leakage, and this
  cell has none.  `pct_of_power` sums to 100 within each DUT.  `port` is the noise port
  the data identified for that generator, and `z_dc_ohm` is that port's transimpedance to
  the differential output, which is what turns a device current into output noise.
  `post_pex` has no per-generator decomposition and is absent, exactly as in §5.2.
* `rejection_mismatch_draws.csv` — each mismatch draw's CMRR and PSRR at the four spot
  frequencies the tables quote, next to its offset.  Use it for a histogram; use
  `rejection_mismatch_curves.csv` for the band against frequency.
* **Offset is input-referred.**  `mc_draws.csv` ships `offset_in_uv` (what the tables
  quote), `offset_out_uv` (the raw differential output measurement) and the `dc_gain_db`
  that relates them, so the referral can be checked rather than assumed.

## Reading the column names

Every name ends in the DUT it was measured on:

| suffix | DUT |
|---|---|
| `_pre_ideal` | pre-layout, ideal capacitors |
| `_pre_mim` | **pre-layout DUT of record** — PDK MIM capacitors |
| `_post_pex` | **post-layout DUT of record** — the extracted layout |
| `_post_lumped` | post-layout parasitics as explicit capacitor cards (proven equivalent to `_post_pex`; it is what the symbolic model is evaluated on) |

`ac_response.csv`, `input_referred_noise.csv` and `group_delay.csv` carry all four.
`noise_by_device_and_type.csv` names the DUT in a `dut` column instead of a suffix,
because every one of its rows is a separate measurement rather than a separate curve.  The
distortion and two-tone files carry `_pre_mim` and `_post_pex` only — the two DUTs the
transient benches ran on — except `thd_vs_frequency_43p75mvpp.csv`, which is `_pre_mim`
alone.

Units are in the name: `_hz`, `_db` (dB), `_dbc` (dB relative to the fundamental),
`_dbvp` (dB relative to 1 V peak), `_ms`, `_v`, `_vpp`, `_v_per_rthz` (V/√Hz).
Phase is in degrees and **negative means lag**, as in the pack's figures.

## Five things worth knowing before you plot

**Some files have text columns.**  `pvt_certified_axes.csv`,
`pvt_cert_box.csv` and `iip3_corners.csv` start with `corner`, `process` — corner names,
not numbers.  `noise_by_device_and_type.csv` is more so: it is a categorical table rather
than a curve, with six text columns, meant to be sorted or pivoted rather than plotted.  Veusz imports those as text datasets, which is what you want: use them as
point labels, and plot against the row index or against `temp_c` / `vdd_v`, which are
numeric.  `pvt_cert_box.csv` also carries blank `q_lo` / `q_hi` cells at the seven points
that have lost a complex pole pair — the gap is the finding, so those rows are kept rather
than dropped.

**CMRR and PSRR are ratios, and the columns carry both halves.**  Both are taken to the
DIFFERENTIAL output: in dB, `cmrr_db = a_dm_db − cm_to_dm_db` and `psrr_db = a_dm_db −
supply_to_dm_db`.  `rejection_mismatch_curves.csv` ships the signal gain and both leakage
transfers next to the quotients, so a plot can show the gap the ratio measures.  The
`cm_to_cm_db` and `supply_to_cm_db` columns are **not** rejection — they end at the output
COMMON mode, which is a different quantity, finite at nominal where the differential paths
are symmetry-cancelled.

**Blank cells are deliberate.**  In `ac_response.csv` and `group_delay.csv` the phase and
group-delay columns stop at 3.0 kHz — the last 76 of 301 rows are empty.  Past that point
the magnitude is below the −100 dB floor and the swept phase aliases between points, so
its unwrapping and its derivative would be wrong; the pack neither scores nor plots them
there.  Magnitude is valid over the whole sweep.  Veusz skips empty cells as missing data.

**The distortion fits use a subset of the rows.**  This applies to two files.
`thd_vs_amplitude.csv` has six amplitudes, but the top three are compressing — the
fundamental has stopped growing — and a line through all six gives a different slope and a
different crossing from the published one.  `in_fit_*` = 1 marks the three rows the `A²`
fit uses.  Likewise for IIP3: `iip3_twotone.csv` has five amplitudes, but
the top two are compressing — a line through all five gives a different intercept from the
published one.  Two flag columns mark what was used: `in_fit_*` = 1 on the three rows
still following the 3:1 law, and `in_ip3_avg_*` = 1 on the two rows whose `iip3_dbvp_*`
is averaged into the published number.  That average is **−3.281 dBVp** pre-layout and
**−3.348 dBVp** post-layout, which is what [`../validation.md` §6.3](../validation.md#63-two-tone-imd3-and-iip3) reports.

**A worst case is not a converged number.**  Both Monte Carlo populations are 1024
draws, and the tables quote `min`/`max` next to `p01`/`p99` on purpose: the minimum and
maximum of a sample are order statistics, so they walk outward as draws are added and a
longer run must report a worse worst case.  Only the quantiles are comparable between runs
of different length.  `mc_convergence.csv` is the evidence for the σ values: plot
`sigma_*` against `n_draws` and compare the movement with `se_sigma_frac`, the standard
error 1/√(2(N−1)) that a σ estimated from N draws carries.  Both axes are useful on a log
x-scale.

## Regenerating

From the repository root, after steps 1 and 6 of
[the pack README §5](../README.md#5-regenerating-everything) — step 1 for the AC, noise and
group-delay files, step 6 for the PVT, rejection and corner ones:

```bash
.venv/bin/python signoff/paper-draft/scripts/export_csv.py
```

It runs no simulation; it re-serialises `../data/*.json` and prints the cross-checks tying
these files to the certified sign-off numbers (group delay at dc, integrated input-referred
noise, IIP3).  Re-running it produces byte-identical files.
