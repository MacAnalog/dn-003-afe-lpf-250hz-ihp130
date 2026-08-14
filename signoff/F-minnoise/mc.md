# Monte-Carlo -- `F-minnoise`

Mismatch MC over the PDK's own statistical model (`mos_tt_mismatch`, parse-time draws, netlist-directive seeds; see `lab.mc`). Reproduce one sample with `asbuilt/core_tb_mc.sp` (edit `.option seed=`); this table is n = 100 seeds 1-100.

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 249.95 Hz - dc -0.0327 dB - group delay tau(0) 1.659 ms, tau_max 2.483 ms (at-fc 2.363 ms)

### Mismatch Monte Carlo — `exp_F_mc` (b), corner `mos_tt_mismatch`, T = 27 °C

**93 of 100 samples pass every spec line — ALL-PASS YIELD = 93.0 % (denominator: 100 samples attempted, seeds 1–100).**

Non-converged / non-finite samples: **0** (0.0 % of attempted) — counted as failures, never as passes. Statistics below are over the 100 usable samples; yields are over all 100 attempted.
Wall time 3.9 s.

| spec line | bound | pass | yield |
|---|---|---|---|
| S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 100/100 | 100.0 % |
| S1 companion: |H| at 1 kHz | <= -48 | 100/100 | 100.0 % |
| S2 cutoff | 245..255 | 93/100 | 93.0 % |
| S3 passband gain | |·| <= 0.2 | 100/100 | 100.0 % |
| S4 peaking | <= 0.2 | 100/100 | 100.0 % |
| S3 passband flatness to 150 Hz | <= 0.2 | 100/100 | 100.0 % |
| S5 input-referred noise, 0.5-200 Hz | < 40 | 100/100 | 100.0 % |
| S6 filter-core power | < 50 | 100/100 | 100.0 % |
| **ALL LINES** | — | **93/100** | **93.0 %** |

| quantity | mean | sigma | min | max | n |
|---|---|---|---|---|---|
| dc_db | -0.03259 | +0.00180 | -0.03807 | -0.02861 | 100 |
| fc_hz | 249.786 | 2.753 | 240.915 | 256.604 | 100 |
| ripple_db | 0.0625 | 0.0255 | 0.0233 | 0.1339 | 100 |
| irn_uv | 26.247 | 0.217 | 25.733 | 26.976 | 100 |
| p_core_nw | 12.624 | 0.162 | 12.291 | 13.014 | 100 |
| gd_dc_ms | 1.6600 | 0.0141 | 1.6282 | 1.6969 | 100 |
| gd_max_ms | 2.4895 | 0.0221 | 2.4469 | 2.5385 | 100 |

Mismatch figure of merit: **sigma(dc_db) = 0.00180 dB** against the S3 box of 0.2 dB — 111.2 sigma of headroom.

**Worst 5 samples**

| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |
|---|---|---|---|---|---|---|
| 48 | S2 cutoff | 240.91 | -0.0293 | 0.0916 | 26.98 | 12.73 |
| 27 | S2 cutoff | 256.60 | -0.0358 | 0.1093 | 25.73 | 12.59 |
| 9 | S2 cutoff | 243.63 | -0.0307 | 0.0414 | 26.67 | 12.59 |
| 88 | S2 cutoff | 256.30 | -0.0381 | 0.0706 | 25.88 | 12.82 |
| 76 | S2 cutoff | 243.73 | -0.0312 | 0.0577 | 26.71 | 12.67 |
