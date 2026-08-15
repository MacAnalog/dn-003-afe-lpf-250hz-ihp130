# Monte-Carlo -- `E1-prev`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 250.00 Hz - dc -0.0134 dB - group delay tau(0) 1.641 ms, tau_max 2.431 ms (at-fc 2.319 ms)

### Mismatch Monte Carlo — `exp_E1_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**96 of 100 samples pass every spec line — ALL-PASS YIELD = 96.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 3.8 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 99/100 | 99.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 97/100 | 97.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **96/100** | **96.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.01345 | +0.00019 | -0.01395 | -0.01296 | 100 |
| fc_hz | 249.765 | 2.199 | 243.600 | 255.658 | 100 |
| ripple_db | 0.0854 | 0.0133 | 0.0567 | 0.1245 | 100 |
| irn_uv | 28.207 | 0.152 | 27.766 | 28.734 | 100 |
| p_core_nw | 9.007 | 0.126 | 8.695 | 9.266 | 100 |
| gd_dc_ms | 1.6423 | 0.0164 | 1.6003 | 1.6888 | 100 |
| gd_max_ms | 2.4518 | 0.0352 | 2.3776 | 2.5423 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00019 dB** against the S3 box of 0.2 dB — 1046.0 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 243.60 | -0.0132 | 0.0773 | 28.73 | 8.99 |
| 75 | S2 cutoff | 244.14 | -0.0130 | 0.0954 | 28.41 | 8.70 |
| 88 | S2 cutoff | 255.66 | -0.0138 | 0.0714 | 27.90 | 9.27 |
| 41 | S1 biquad-order certificate (max unwrapped phase lag) | 251.24 | -0.0133 | 0.0814 | 28.06 | 8.96 |
| 1 | (passes) | 251.78 | -0.0135 | 0.0619 | 28.20 | 9.16 |
