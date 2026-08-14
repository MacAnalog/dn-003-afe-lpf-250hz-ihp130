# Monte-Carlo -- `D-thdjump`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 250.00 Hz - dc -0.0131 dB - group delay tau(0) 1.623 ms, tau_max 2.372 ms (at-fc 2.267 ms)

### Mismatch Monte Carlo — `exp_D_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**75 of 100 samples pass every spec line — ALL-PASS YIELD = 75.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 3.9 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 77/100 | 77.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 97/100 | 97.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **75/100** | **75.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.01309 | +0.00017 | -0.01354 | -0.01266 | 100 |
| fc_hz | 249.884 | 2.140 | 243.545 | 255.585 | 100 |
| ripple_db | 0.1604 | 0.0064 | 0.1462 | 0.1758 | 100 |
| irn_uv | 28.814 | 0.152 | 28.378 | 29.347 | 100 |
| p_core_nw | 7.464 | 0.101 | 7.219 | 7.680 | 100 |
| gd_dc_ms | 1.6240 | 0.0156 | 1.5843 | 1.6678 | 100 |
| gd_max_ms | 2.3762 | 0.0331 | 2.3091 | 2.4595 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00017 dB** against the S3 box of 0.2 dB — 1177.7 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 243.55 | -0.0128 | 0.1715 | 29.35 | 7.44 |
| 88 | S2 cutoff | 255.58 | -0.0134 | 0.1513 | 28.50 | 7.67 |
| 75 | S2 cutoff | 244.54 | -0.0127 | 0.1722 | 29.03 | 7.22 |
| 41 | S1 biquad-order certificate (max unwrapped phase lag) | 251.53 | -0.0129 | 0.1543 | 28.67 | 7.43 |
| 59 | S1 biquad-order certificate (max unwrapped phase lag) | 248.21 | -0.0133 | 0.1641 | 29.03 | 7.56 |
