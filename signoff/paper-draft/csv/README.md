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
| **Group delay** | `group_delay.csv` | `f_hz` | `group_delay_ms_*` |
| **THD / HD3 vs amplitude** | `thd_vs_amplitude.csv` | `vpp_diff_v` or `ampl_v` | `thd_db_*`, `hd3_db_*` |
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
| **the mismatch distributions** | `mc_draws.csv` | `seed` | `fc_hz`, `q_lo`, `q_hi`, `offset_out_uv` |
| **PSRR and CMRR vs frequency** | `rejection_nominal.csv` | `freq_hz` | `psrr_db`, `cmrr_db` |
| **supply → common-mode and CM → CM** | `rejection_nominal.csv` | `freq_hz` | `supply_to_cm_db`, `cm_to_cm_db` |
| **the mismatch-limited rejection band** | `rejection_mismatch_curves.csv` | `freq_hz` | `psrr_db_mean` with `_min` / `_max` |
| **offset, per draw** | `rejection_mismatch_draws.csv` | `seed` | `offset_in_uv` |
| **IIP3 over corners** | `iip3_corners.csv` | `corner` (text) | `iip3_dbv`, `imd3_slope_db_per_decade` |
| **the THD ladder over corners** | `thd_corners.csv` | `vpp_diff_v` | `thd_db_<corner>`, `hd3_db_<corner>` |
| **the low-frequency residual, and what explains it** | `gds_residual.csv` | `fin_hz` | `v3_unexplained_uv`, `v3_gds_cubic_uv`, `v3_gds_exact_uv` |

The remaining files support those:

* `thd_vs_frequency_43p75mvpp.csv` — the same harmonic-vs-frequency sweep at 43.75 mVpp
  instead of 175 mVpp, where distortion is still cubic in amplitude.  This is the sweep
  the distortion equation is checked against.
* `iip3_extrapolation.csv` — the two extrapolation lines, so you need not fit anything.
  Two rows: the low-amplitude end, then the intercept.  Plot `fund_line_dbvp_*` (slope 1)
  and `imd3_line_dbvp_*` (slope 3) against `x_dbvp_*`; they meet at the published intercept.
* `ac_response_model.csv` — the closed-form model next to the simulation, the data behind
  `figures/bode_model_vs_sim.png`.  Columns come in `_sim_` / `_model_` pairs.
* `rejection_mismatch_draws.csv` — each mismatch draw's CMRR and PSRR at the four spot
  frequencies the tables quote, next to its offset.  Use it for a histogram; use
  `rejection_mismatch_curves.csv` for the band against frequency.

## Reading the column names

Every name ends in the DUT it was measured on:

| suffix | DUT |
|---|---|
| `_pre_ideal` | pre-layout, ideal capacitors |
| `_pre_mim` | **pre-layout DUT of record** — PDK MIM capacitors |
| `_post_pex` | **post-layout DUT of record** — the extracted layout |
| `_post_lumped` | post-layout parasitics as explicit capacitor cards (proven equivalent to `_post_pex`; it is what the symbolic model is evaluated on) |

`ac_response.csv`, `input_referred_noise.csv` and `group_delay.csv` carry all four.  The
distortion and two-tone files carry `_pre_mim` and `_post_pex` only — the two DUTs the
transient benches ran on — except `thd_vs_frequency_43p75mvpp.csv`, which is `_pre_mim`
alone.

Units are in the name: `_hz`, `_db` (dB), `_dbc` (dB relative to the fundamental),
`_dbvp` (dB relative to 1 V peak), `_ms`, `_v`, `_vpp`, `_v_per_rthz` (V/√Hz).
Phase is in degrees and **negative means lag**, as in the pack's figures.

## Three things worth knowing before you plot

**The corner files have a text first column.**  `pvt_certified_axes.csv`,
`pvt_cert_box.csv` and `iip3_corners.csv` start with `corner`, `process` — corner names,
not numbers.  Veusz imports those as text datasets, which is what you want: use them as
point labels, and plot against the row index or against `temp_c` / `vdd_v`, which are
numeric.  `pvt_cert_box.csv` also carries blank `q_lo` / `q_hi` cells at the seven points
that have lost a complex pole pair — the gap is the finding, so those rows are kept rather
than dropped.

**Blank cells are deliberate.**  In `ac_response.csv` and `group_delay.csv` the phase and
group-delay columns stop at 3.0 kHz — the last 76 of 301 rows are empty.  Past that point
the magnitude is below the −100 dB floor and the swept phase aliases between points, so
its unwrapping and its derivative would be wrong; the pack neither scores nor plots them
there.  Magnitude is valid over the whole sweep.  Veusz skips empty cells as missing data.

**The IIP3 fit uses a subset of the rows.**  `iip3_twotone.csv` has five amplitudes, but
the top two are compressing — a line through all five gives a different intercept from the
published one.  Two flag columns mark what was used: `in_fit_*` = 1 on the three rows
still following the 3:1 law, and `in_ip3_avg_*` = 1 on the two rows whose `iip3_dbvp_*`
is averaged into the published number.  That average is **−3.281 dBVp** pre-layout and
**−3.348 dBVp** post-layout, which is what [`../validation.md` §6.3](../validation.md#63-two-tone-imd3-and-iip3) reports.

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
