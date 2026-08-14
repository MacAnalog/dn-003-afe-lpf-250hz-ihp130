# Monte-Carlo -- `G-maxthd`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 249.88 Hz - dc -0.0417 dB - group delay tau(0) 1.661 ms, tau_max 2.483 ms (at-fc 2.355 ms)

### Mismatch Monte Carlo — `exp_G_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**90 of 100 samples pass every spec line — ALL-PASS YIELD = 90.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 4.0 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 100/100 | 100.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 98/100 | 98.0 % |
| S2 cutoff | 245..255 | 91/100 | 91.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **90/100** | **90.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.04156 | +0.00278 | -0.05032 | -0.03598 | 100 |
| fc_hz | 249.660 | 2.997 | 240.496 | 257.216 | 100 |
| ripple_db | 0.0640 | 0.0257 | 0.0264 | 0.1336 | 100 |
| irn_uv | 26.815 | 0.216 | 26.300 | 27.546 | 100 |
| p_core_nw | 14.311 | 0.242 | 13.800 | 14.860 | 100 |
| gd_dc_ms | 1.6624 | 0.0188 | 1.6206 | 1.7114 | 100 |
| gd_max_ms | 2.4874 | 0.0316 | 2.4283 | 2.5624 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00278 dB** against the S3 box of 0.2 dB — 72.0 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 240.50 | -0.0368 | 0.0687 | 27.55 | 14.42 |
| 88 | S2 cutoff | 257.22 | -0.0503 | 0.0658 | 26.42 | 14.65 |
| 9 | S2 cutoff | 243.11 | -0.0385 | 0.0380 | 27.25 | 14.23 |
| 27 | S2 cutoff | 256.82 | -0.0462 | 0.1049 | 26.30 | 14.29 |
| 76 | S2 cutoff | 243.46 | -0.0396 | 0.0417 | 27.28 | 14.36 |
