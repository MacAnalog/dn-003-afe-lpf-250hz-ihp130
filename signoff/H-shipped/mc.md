# Monte-Carlo -- `H-shipped`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 249.99 Hz - dc -0.0206 dB - group delay tau(0) 1.659 ms, tau_max 2.462 ms (at-fc 2.355 ms)

### Mismatch Monte Carlo — `exp_H_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**95 of 100 samples pass every spec line — ALL-PASS YIELD = 95.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 4.0 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 100/100 | 100.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 95/100 | 95.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **95/100** | **95.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.02063 | +0.00066 | -0.02243 | -0.01887 | 100 |
| fc_hz | 249.810 | 2.350 | 243.629 | 256.090 | 100 |
| ripple_db | 0.0942 | 0.0209 | 0.0424 | 0.1344 | 100 |
| irn_uv | 27.868 | 0.152 | 27.433 | 28.391 | 100 |
| p_core_nw | 14.486 | 0.234 | 13.914 | 14.952 | 100 |
| gd_dc_ms | 1.6608 | 0.0190 | 1.6149 | 1.7136 | 100 |
| gd_max_ms | 2.4677 | 0.0335 | 2.3946 | 2.5595 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00066 dB** against the S3 box of 0.2 dB — 301.2 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 243.63 | -0.0195 | 0.0708 | 28.39 | 14.46 |
| 75 | S2 cutoff | 243.70 | -0.0189 | 0.1285 | 28.07 | 13.91 |
| 88 | S2 cutoff | 256.09 | -0.0221 | 0.0771 | 27.57 | 14.95 |
| 27 | S2 cutoff | 255.11 | -0.0210 | 0.1143 | 27.43 | 14.53 |
| 71 | S2 cutoff | 244.98 | -0.0200 | 0.1262 | 28.03 | 14.09 |
