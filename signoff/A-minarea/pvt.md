# PVT -- `A-minarea`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.86 | -0.0088 | 0.0545 | +0.0000 | -49.04 | 339.77 | 39.695 | 4.146 | PASS |
| mos_ss | -40 | 1.35 | 0.11 | -45.9768 | 54.0326 | +0.0000 | -53.59 | 17.78 | 121052.766 | 0.000 | FAIL (5) |
| mos_ss | -40 | 1.65 | 0.84 | -0.0675 | 100.7479 | +0.0000 | -102.49 | 240.21 | 137730.295 | 0.039 | FAIL (4) |
| mos_ss | +125 | 1.35 | 406.70 | -0.8221 | 0.0712 | +0.0000 | -17.37 | 337.26 | 51.774 | 24.701 | FAIL (4) |
| mos_ss | +125 | 1.65 | 586.29 | -6.7492 | 0.2392 | +0.0000 | -6.31 | 339.09 | 60.251 | 163.259 | FAIL (6) |
| mos_ff | -40 | 1.35 | 0.68 | -0.0998 | 100.0448 | +0.0000 | -101.37 | 237.29 | 131732.401 | 0.025 | FAIL (4) |
| mos_ff | -40 | 1.65 | 323.38 | -0.0059 | 0.0117 | +0.0000 | -40.35 | 340.15 | 30.815 | 4.336 | FAIL (2) |
| mos_ff | +125 | 1.35 | 600.13 | -6.1745 | 0.2267 | +0.0000 | -6.17 | 330.73 | 57.656 | 128.200 | FAIL (6) |
| mos_ff | +125 | 1.65 | 1243.90 | -19.2652 | 0.0557 | +0.0000 | -2.13 | 490.95 | 119.168 | 485.637 | FAIL (5) |
| mos_sf | -40 | 1.35 | 0.17 | -4.8178 | 94.6284 | +0.0000 | -94.88 | 183.85 | 152623.536 | 0.004 | FAIL (5) |
| mos_sf | -40 | 1.65 | 14.17 | -0.0071 | 34.9687 | +0.0000 | -95.23 | 290.05 | 435.668 | 0.642 | FAIL (4) |
| mos_sf | +125 | 1.35 | 651.10 | -7.3675 | 0.1600 | +0.0000 | -6.21 | 329.16 | 62.860 | 71.156 | FAIL (6) |
| mos_sf | +125 | 1.65 | 1611.59 | -20.8481 | 0.0308 | +0.0000 | -1.32 | 497.40 | 149.508 | 329.157 | FAIL (5) |
| mos_fs | -40 | 1.35 | 0.13 | -9.4794 | 90.6081 | +0.0000 | -90.25 | 129.65 | 165757.284 | 0.002 | FAIL (5) |
| mos_fs | -40 | 1.65 | 5.70 | -0.0077 | 59.0399 | +0.0000 | -94.55 | 260.35 | 5111.714 | 0.265 | FAIL (4) |
| mos_fs | +125 | 1.35 | 440.52 | -0.4761 | 0.3165 | +0.0000 | -11.43 | 336.45 | 50.674 | 51.524 | FAIL (6) |
| mos_fs | +125 | 1.65 | 514.25 | -5.8590 | 0.3221 | +0.0000 | -6.99 | 510.70 | 55.425 | 262.727 | FAIL (6) |
| mos_tt | +27 | 1.35 | 12.11 | -0.0111 | 39.0750 | +0.0000 | -96.64 | 294.54 | 766.170 | 0.595 | FAIL (4) |
| mos_ss | +27 | 1.35 | 2.07 | -0.0714 | 99.4900 | +0.0000 | -103.80 | 249.01 | 139050.754 | 0.105 | FAIL (4) |
| mos_ff | +27 | 1.35 | 241.19 | -0.0092 | 0.0786 | +0.0000 | -51.11 | 339.55 | 39.158 | 3.459 | FAIL (1) |
| mos_sf | +27 | 1.35 | 17.49 | -0.0131 | 31.0326 | +0.0000 | -109.12 | 314.27 | 352.667 | 0.831 | FAIL (4) |
| mos_fs | +27 | 1.35 | 8.70 | -0.0110 | 47.4354 | +0.0000 | -95.36 | 278.63 | 1766.457 | 0.434 | FAIL (4) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.11 | 1611.59 | 14364.934x | mos_ss / -40 C / 1.35 V | mos_sf / +125 C / 1.65 V |
| irn_uv | 30.815 | 165757.284 | 5379.196x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.000 | 485.637 | 1941524.312x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 17.78 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -1.32 | mos_sf / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 1611.59 | mos_sf / +125 C / 1.65 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -45.9768 | mos_ss / -40 C / 1.35 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +0.0000 | mos_tt / +27 C / 1.50 V | PASS |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 100.7479 | mos_ss / -40 C / 1.65 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 165757.284 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 485.637 | mos_ff / +125 C / 1.65 V | **FAIL** |
