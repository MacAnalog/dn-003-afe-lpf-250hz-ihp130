# CSV data for plotting

**[REFERENCE]** — every curve in this pack as a plain CSV, for Veusz or any other
plotting tool.  Same numbers as the figures and the tables in
[`../validation.md`](../validation.md); nothing here is a re-measurement.

## Opening one in Veusz

*Data → Import…*, pick the file, leave the CSV settings at their defaults (data in
columns, dataset names in the first row), *Import*.  Each column arrives as its own
dataset named after its header, so you then just choose an x and a y.

Nothing else is needed — there are no comment lines, no units row and no blank first
line, because any of those would stop the default import from working.

## Which file answers which request

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

Two extra files support those:

* `thd_vs_frequency_43p75mvpp.csv` — the same harmonic-vs-frequency sweep at the
  small-signal drive (43.75 mVpp instead of 175 mVpp), where the cell is well inside its
  cubic regime.  This is the sweep the distortion equation is checked against.
* `iip3_extrapolation.csv` — the two straight lines of the classic IIP3 picture, so you can
  draw them without fitting anything.  Two rows: the low-amplitude end, then the intercept.
  Plot `fund_line_dbvp_*` and `imd3_line_dbvp_*` against `x_dbvp_*` (the 1:1 and 3:1 lines)
  and they meet exactly at the published intercept.
* `ac_response_model.csv` — the closed-form model laid next to the simulation, the data
  behind `figures/bode_model_vs_sim.png`.  Columns come in `_sim_` / `_model_` pairs.

## Reading the column names

Every name ends in the DUT it was measured on:

| suffix | DUT |
|---|---|
| `_pre_ideal` | pre-layout, ideal capacitors |
| `_pre_mim` | **pre-layout DUT of record** — PDK MIM capacitors |
| `_post_pex` | **post-layout DUT of record** — the extracted layout |
| `_post_lumped` | post-layout parasitics as explicit capacitor cards (proven equivalent to `_post_pex`; it is what the symbolic model is evaluated on) |

The AC, noise and group-delay files carry all four.  The distortion and two-tone files
carry `_pre_mim` and `_post_pex` only — those are the two DUTs the transient benches were
run on, since the other two would answer the same question twice.

Units are in the name: `_hz`, `_db` (dB), `_dbc` (dB relative to the fundamental),
`_dbvp` (dB relative to 1 V peak), `_ms`, `_v`, `_vpp`, `_v_per_rthz` (V/√Hz).
Phase is in degrees and **negative means lag**, matching the pack's figures.

## Two things worth knowing before you plot

**Blank cells are deliberate.**  In `ac_response.csv` and `group_delay.csv` the phase and
group-delay columns stop at 3.0 kHz — the last 76 of 301 rows are empty.  Above the −100 dB
magnitude floor the swept phase aliases between points, so its unwrapping and its derivative
would be fiction; the pack does not score them there and does not plot them there.
Magnitude is valid over the whole sweep.  Veusz treats an empty cell as missing data and
simply skips it.

**The IIP3 fit is a subset, on purpose.**  `iip3_twotone.csv` has five amplitudes, but the
top two are already compressing — fitting a line through all five gives a different
intercept from the published one.  Two flag columns mark exactly what was used:
`in_fit_*` = 1 on the three rows still following the 3:1 law, and `in_ip3_avg_*` = 1 on the
two rows whose `iip3_dbvp_*` is averaged into the published number.  Averaging
`iip3_dbvp_*` over the `in_ip3_avg_*` rows gives **−3.281 dBVp** pre-layout and
**−3.348 dBVp** post-layout, which is what [`../validation.md` §6.3](../validation.md#63-two-tone-imd3-and-iip3) reports.

## Regenerating

From the repository root, after step 1 of
[the pack README §5](../README.md#5-regenerating-everything):

```bash
.venv/bin/python signoff/paper-draft/scripts/export_csv.py
```

It runs no simulation — it re-serialises `../data/*.json` — and prints the cross-checks that
tie these files back to the certified sign-off numbers (group delay at dc, integrated
input-referred noise, IIP3).  Re-running it produces byte-identical files.
