# Monte-Carlo -- `C-lownoise`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 248.14 Hz - dc -0.0127 dB - group delay tau(0) 1.658 ms, tau_max 2.500 ms (at-fc 2.366 ms)

### Mismatch Monte Carlo — `exp_C_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**75 of 100 samples pass every spec line — ALL-PASS YIELD = 75.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 4.4 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 88/100 | 88.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 85/100 | 85.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **75/100** | **75.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.01267 | +0.00028 | -0.01343 | -0.01209 | 100 |
| fc_hz | 247.975 | 2.707 | 241.222 | 253.357 | 100 |
| ripple_db | 0.0652 | 0.0131 | 0.0291 | 0.0937 | 100 |
| irn_uv | 28.558 | 0.144 | 28.153 | 29.070 | 100 |
| p_core_nw | 6.374 | 0.121 | 6.110 | 6.680 | 100 |
| gd_dc_ms | 1.6602 | 0.0245 | 1.6081 | 1.7204 | 100 |
| gd_max_ms | 2.5052 | 0.0506 | 2.3846 | 2.6110 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00028 dB** against the S3 box of 0.2 dB — 702.5 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 75 | S2 cutoff | 241.22 | -0.0123 | 0.0937 | 28.74 | 6.11 |
| 71 | S2 cutoff | 241.81 | -0.0123 | 0.0920 | 28.73 | 6.14 |
| 48 | S2 cutoff | 242.25 | -0.0125 | 0.0590 | 29.07 | 6.36 |
| 61 | S2 cutoff | 242.96 | -0.0127 | 0.0853 | 28.66 | 6.17 |
| 26 | S2 cutoff | 243.60 | -0.0121 | 0.0848 | 28.59 | 6.17 |
