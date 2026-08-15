# PVT -- `E1-prev`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**2 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 250.00 | -0.0134 | 0.1119 | +0.0000 | -49.55 | 333.30 | 28.210 | 9.014 | PASS |
| mos_ss | -40 | 1.35 | 0.16 | -2.9301 | 88.3221 | +0.0000 | -85.48 | 173.56 | 80983.146 | 0.007 | FAIL (5) |
| mos_ss | -40 | 1.65 | 20.39 | -0.0336 | 30.1753 | +0.0000 | -94.45 | 304.97 | 306.535 | 1.427 | FAIL (4) |
| mos_ss | +125 | 1.35 | 70.66 | -8.6087 | 10.6710 | +0.0000 | -90.11 | 306.44 | 224.849 | 10.476 | FAIL (5) |
| mos_ss | +125 | 1.65 | 104.75 | -22.6721 | 4.7685 | +0.0000 | -31.61 | 434.16 | 255.498 | 41.211 | FAIL (5) |
| mos_ff | -40 | 1.35 | 17.26 | -6.5391 | 35.6622 | +0.0000 | -83.90 | 269.38 | 1315.501 | 0.775 | FAIL (5) |
| mos_ff | -40 | 1.65 | 483.64 | -0.0097 | 0.1589 | +0.2289 | -20.24 | 332.75 | 20.478 | 22.473 | FAIL (3) |
| mos_ff | +125 | 1.35 | 83.33 | -26.2216 | 6.2405 | +0.0000 | -33.90 | 232.00 | 405.220 | 34.119 | FAIL (6) |
| mos_ff | +125 | 1.65 | 103.69 | -39.0768 | 4.6961 | +0.0000 | -22.43 | 358.31 | 1554.704 | 93.885 | FAIL (6) |
| mos_sf | -40 | 1.35 | 2.33 | -0.5888 | 91.1283 | +0.0000 | -91.49 | 239.98 | 66217.001 | 0.143 | FAIL (5) |
| mos_sf | -40 | 1.65 | 320.06 | -0.0083 | 0.0425 | +0.0425 | -41.22 | 333.70 | 21.751 | 9.463 | FAIL (2) |
| mos_sf | +125 | 1.35 | 103.82 | -20.8786 | 5.0117 | +0.0000 | -38.33 | 263.69 | 226.091 | 22.458 | FAIL (6) |
| mos_sf | +125 | 1.65 | 127.65 | -36.2611 | 3.5895 | +0.0000 | -22.86 | 358.68 | 1058.006 | 69.833 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.98 | -4.2914 | 87.8199 | +0.0000 | -85.33 | 226.43 | 91532.197 | 0.048 | FAIL (5) |
| mos_fs | -40 | 1.65 | 238.24 | -0.0398 | 0.4040 | +0.0000 | -56.79 | 334.21 | 23.105 | 5.689 | FAIL (2) |
| mos_fs | +125 | 1.35 | 63.55 | -11.6111 | 9.2124 | +0.0000 | -59.26 | 293.59 | 273.937 | 17.608 | FAIL (5) |
| mos_fs | +125 | 1.65 | 84.76 | -27.3973 | 6.0236 | +0.0000 | -29.59 | 401.36 | 452.149 | 58.370 | FAIL (6) |
| mos_tt | +27 | 1.35 | 87.72 | -0.4994 | 22.8131 | +5.0323 | -125.83 | 329.40 | 201.861 | 2.313 | FAIL (6) |
| mos_ss | +27 | 1.35 | 6.09 | -0.5566 | 61.4558 | +0.0000 | -96.28 | 259.65 | 16473.562 | 0.482 | FAIL (5) |
| mos_ff | +27 | 1.35 | 246.55 | -0.0834 | 0.1790 | +0.0000 | -49.88 | 332.48 | 28.247 | 8.022 | PASS |
| mos_sf | +27 | 1.35 | 130.74 | -0.0975 | 7.1907 | +1.7636 | -89.33 | 332.66 | 47.498 | 3.106 | FAIL (4) |
| mos_fs | +27 | 1.35 | 30.95 | -3.0305 | 35.0785 | +0.0000 | -94.71 | 311.13 | 1049.523 | 1.627 | FAIL (5) |

**2 of 22 corners PASS** (20 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.16 | 483.64 | 2963.294x | mos_ss / -40 C / 1.35 V | mos_ff / -40 C / 1.65 V |
| irn_uv | 20.478 | 91532.197 | 4469.789x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.007 | 93.885 | 13761.299x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 173.56 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -20.24 | mos_ff / -40 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 0.16 | mos_ss / -40 C / 1.35 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -39.0768 | mos_ff / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +5.0323 | mos_tt / +27 C / 1.35 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 91.1283 | mos_sf / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 91532.197 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 93.885 | mos_ff / +125 C / 1.65 V | **FAIL** |
