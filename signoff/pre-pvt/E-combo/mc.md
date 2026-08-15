# Monte-Carlo -- `E-combo`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 249.88 Hz - dc -0.0207 dB - group delay tau(0) 1.652 ms, tau_max 2.475 ms (at-fc 2.346 ms)

### Mismatch Monte Carlo — `exp_E_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**92 of 100 samples pass every spec line — ALL-PASS YIELD = 92.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 3.9 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 100/100 | 100.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 92/100 | 92.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **92/100** | **92.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.02065 | +0.00087 | -0.02337 | -0.01884 | 100 |
| fc_hz | 249.697 | 2.761 | 241.022 | 256.769 | 100 |
| ripple_db | 0.0557 | 0.0165 | 0.0247 | 0.0966 | 100 |
| irn_uv | 27.274 | 0.212 | 26.764 | 27.998 | 100 |
| p_core_nw | 8.875 | 0.130 | 8.605 | 9.186 | 100 |
| gd_dc_ms | 1.6530 | 0.0166 | 1.6146 | 1.6963 | 100 |
| gd_max_ms | 2.4793 | 0.0340 | 2.4036 | 2.5536 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00087 dB** against the S3 box of 0.2 dB — 230.9 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 241.02 | -0.0192 | 0.0446 | 28.00 | 8.94 |
| 88 | S2 cutoff | 256.77 | -0.0234 | 0.0555 | 26.87 | 9.06 |
| 9 | S2 cutoff | 243.63 | -0.0197 | 0.0698 | 27.71 | 8.84 |
| 27 | S2 cutoff | 256.30 | -0.0221 | 0.0667 | 26.76 | 8.86 |
| 76 | S2 cutoff | 243.85 | -0.0200 | 0.0506 | 27.74 | 8.91 |
