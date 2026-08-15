# Monte-Carlo -- `B-balanced`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 250.01 Hz - dc -0.0118 dB - group delay tau(0) 1.639 ms, tau_max 2.463 ms (at-fc 2.334 ms)

### Mismatch Monte Carlo — `exp_B_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**70 of 100 samples pass every spec line — ALL-PASS YIELD = 70.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 4.9 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 80/100 | 80.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 88/100 | 88.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **70/100** | **70.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.01182 | +0.00023 | -0.01240 | -0.01137 | 100 |
| fc_hz | 249.682 | 3.319 | 240.463 | 256.199 | 100 |
| ripple_db | 0.0601 | 0.0117 | 0.0336 | 0.0867 | 100 |
| irn_uv | 29.387 | 0.313 | 28.691 | 30.432 | 100 |
| p_core_nw | 6.007 | 0.134 | 5.749 | 6.406 | 100 |
| gd_dc_ms | 1.6410 | 0.0257 | 1.5829 | 1.6961 | 100 |
| gd_max_ms | 2.4692 | 0.0600 | 2.3100 | 2.6070 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00023 dB** against the S3 box of 0.2 dB — 876.3 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 240.46 | -0.0116 | 0.0486 | 30.43 | 6.09 |
| 9 | S2 cutoff | 242.52 | -0.0114 | 0.0596 | 30.04 | 5.99 |
| 71 | S2 cutoff | 242.86 | -0.0115 | 0.0754 | 29.71 | 5.84 |
| 75 | S2 cutoff | 242.95 | -0.0115 | 0.0768 | 29.59 | 5.78 |
| 88 | S2 cutoff | 256.20 | -0.0124 | 0.0610 | 28.87 | 6.05 |
