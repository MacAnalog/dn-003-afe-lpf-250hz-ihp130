# PVT -- `H-shipped`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.99 | -0.0206 | 0.0929 | +0.0003 | -49.38 | 341.30 | 27.866 | 14.502 | PASS |
| mos_ss | -40 | 1.35 | 0.16 | -3.4689 | 96.7103 | +0.0000 | -94.77 | 180.54 | 143590.564 | 0.011 | FAIL (5) |
| mos_ss | -40 | 1.65 | 37.08 | -0.1112 | 47.3805 | +12.2722 | -111.96 | 323.47 | 2018.422 | 2.285 | FAIL (5) |
| mos_ss | +125 | 1.35 | 79.51 | -5.5529 | 9.8558 | +0.0000 | -68.31 | 329.81 | 170.527 | 16.825 | FAIL (5) |
| mos_ss | +125 | 1.65 | 121.55 | -17.6528 | 3.9164 | +0.0000 | -31.12 | 477.84 | 158.649 | 66.239 | FAIL (6) |
| mos_ff | -40 | 1.35 | 14.92 | -13.3224 | 40.0865 | +0.0000 | -86.11 | 270.21 | 3921.288 | 0.910 | FAIL (5) |
| mos_ff | -40 | 1.65 | 482.33 | -0.0109 | 0.2171 | +0.3504 | -21.09 | 341.62 | 20.533 | 36.196 | FAIL (4) |
| mos_ff | +125 | 1.35 | 98.65 | -20.3201 | 5.1569 | +0.0000 | -32.51 | 472.24 | 221.185 | 54.854 | FAIL (6) |
| mos_ff | +125 | 1.65 | 119.68 | -33.9746 | 3.9171 | +0.0000 | -22.96 | 362.61 | 954.817 | 150.924 | FAIL (6) |
| mos_sf | -40 | 1.35 | 2.38 | -1.9924 | 100.1354 | +0.0000 | -101.58 | 249.49 | 131997.985 | 0.218 | FAIL (5) |
| mos_sf | -40 | 1.65 | 319.86 | -0.0096 | 0.0421 | +0.0421 | -41.21 | 341.68 | 21.548 | 15.242 | FAIL (2) |
| mos_sf | +125 | 1.35 | 121.69 | -15.5907 | 4.0369 | +0.0000 | -37.84 | 493.67 | 141.373 | 36.107 | FAIL (5) |
| mos_sf | +125 | 1.65 | 145.82 | -31.3817 | 2.9593 | +0.0000 | -23.42 | 369.59 | 665.392 | 112.272 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.94 | -9.7833 | 92.6951 | +0.0000 | -89.88 | 227.66 | 224320.220 | 0.060 | FAIL (5) |
| mos_fs | -40 | 1.65 | 241.65 | -0.1037 | 0.9139 | +0.0000 | -55.22 | 341.54 | 22.730 | 9.123 | FAIL (2) |
| mos_fs | +125 | 1.35 | 74.98 | -7.5088 | 8.1557 | +0.0000 | -54.40 | 516.98 | 205.512 | 28.297 | FAIL (4) |
| mos_fs | +125 | 1.65 | 98.95 | -22.0060 | 5.0505 | +0.0000 | -28.64 | 453.19 | 258.755 | 93.831 | FAIL (6) |
| mos_tt | +27 | 1.35 | 112.19 | -1.0429 | 14.6714 | +0.5758 | -98.04 | 338.57 | 79.738 | 3.585 | FAIL (5) |
| mos_ss | +27 | 1.35 | 6.14 | -1.9615 | 61.0570 | +0.0000 | -105.63 | 278.29 | 10364.440 | 0.732 | FAIL (5) |
| mos_ff | +27 | 1.35 | 244.74 | -0.1924 | 0.3182 | +0.0000 | -49.71 | 340.41 | 27.876 | 12.837 | FAIL (2) |
| mos_sf | +27 | 1.35 | 143.81 | -0.2354 | 3.1419 | +0.0000 | -79.83 | 340.33 | 34.668 | 4.963 | FAIL (3) |
| mos_fs | +27 | 1.35 | 61.56 | -4.3063 | 36.1665 | +5.3349 | -114.34 | 329.05 | 1109.311 | 2.244 | FAIL (6) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.16 | 482.33 | 2975.548x | mos_ss / -40 C / 1.35 V | mos_ff / -40 C / 1.65 V |
| irn_uv | 20.533 | 224320.220 | 10924.605x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.011 | 150.924 | 14023.035x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 180.54 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -21.09 | mos_ff / -40 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 0.16 | mos_ss / -40 C / 1.35 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -33.9746 | mos_ff / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +12.2722 | mos_ss / -40 C / 1.65 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 100.1354 | mos_sf / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 224320.220 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 150.924 | mos_ff / +125 C / 1.65 V | **FAIL** |
