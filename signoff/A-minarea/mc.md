# Monte-Carlo -- `A-minarea`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 249.86 Hz - dc -0.0088 dB - group delay tau(0) 1.653 ms, tau_max 2.477 ms (at-fc 2.345 ms)

### Mismatch Monte Carlo — `exp_A_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**45 of 100 samples pass every spec line — ALL-PASS YIELD = 45.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 3.8 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 97/100 | 97.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 86/100 | 86.0 % |
| S2 cutoff | 245..255 | 67/100 | 67.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 68/100 | 68.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **45/100** | **45.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.00885 | +0.00006 | -0.00903 | -0.00873 | 100 |
| fc_hz | 249.153 | 5.070 | 235.562 | 260.104 | 100 |
| ripple_db | 0.0605 | 0.0177 | 0.0262 | 0.1050 | 100 |
| irn_uv | 39.731 | 0.615 | 38.409 | 41.704 | 100 |
| p_core_nw | 4.142 | 0.142 | 3.859 | 4.559 | 100 |
| gd_dc_ms | 1.6575 | 0.0398 | 1.5717 | 1.7377 | 100 |
| gd_max_ms | 2.4904 | 0.0910 | 2.2665 | 2.7278 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00006 dB** against the S3 box of 0.2 dB — 3582.0 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 235.56 | -0.0090 | 0.0746 | 41.70 | 4.24 |
| 9 | S2 cutoff | 237.76 | -0.0090 | 0.0504 | 41.09 | 4.13 |
| 71 | S2 cutoff | 238.67 | -0.0090 | 0.0826 | 40.35 | 3.96 |
| 36 | S2 cutoff | 260.10 | -0.0088 | 0.0717 | 38.41 | 4.11 |
| 75 | S2 cutoff | 240.31 | -0.0088 | 0.0848 | 40.02 | 3.92 |
