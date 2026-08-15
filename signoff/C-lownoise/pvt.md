# PVT -- `C-lownoise`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 248.14 | -0.0127 | 0.0667 | +0.0000 | -50.17 | 333.04 | 28.558 | 6.379 | PASS |
| mos_ss | -40 | 1.35 | 0.11 | -48.7293 | 43.5162 | +0.0000 | -39.40 | 7.22 | 40132.097 | 0.000 | FAIL (6) |
| mos_ss | -40 | 1.65 | 0.90 | -0.0558 | 89.7547 | +0.0000 | -90.16 | 233.25 | 44988.072 | 0.057 | FAIL (4) |
| mos_ss | +125 | 1.35 | 138.09 | -2.9367 | 3.2307 | +0.0000 | -28.68 | 504.12 | 118.278 | 38.491 | FAIL (5) |
| mos_ss | +125 | 1.65 | 192.78 | -1.8876 | 1.9228 | +0.0000 | -15.40 | 512.14 | 75.718 | 249.424 | FAIL (6) |
| mos_ff | -40 | 1.35 | 0.71 | -0.0910 | 90.1796 | +0.0000 | -88.92 | 229.83 | 46923.034 | 0.038 | FAIL (4) |
| mos_ff | -40 | 1.65 | 312.88 | -0.0075 | 0.0020 | +0.0002 | -42.21 | 334.00 | 22.252 | 6.485 | FAIL (2) |
| mos_ff | +125 | 1.35 | 168.76 | -2.7152 | 2.3762 | +0.0000 | -16.58 | 505.19 | 91.882 | 196.169 | FAIL (6) |
| mos_ff | +125 | 1.65 | 218.98 | -2.2747 | 1.5630 | +0.0000 | -13.53 | 508.62 | 67.019 | 733.133 | FAIL (6) |
| mos_sf | -40 | 1.35 | 0.16 | -3.3903 | 87.7919 | +0.0000 | -84.70 | 170.50 | 57441.578 | 0.005 | FAIL (5) |
| mos_sf | -40 | 1.65 | 15.41 | -0.0057 | 34.5302 | +0.0000 | -88.78 | 280.45 | 332.112 | 0.951 | FAIL (4) |
| mos_sf | +125 | 1.35 | 189.30 | -2.2958 | 1.9671 | +0.0000 | -17.27 | 510.53 | 81.782 | 109.743 | FAIL (6) |
| mos_sf | +125 | 1.65 | 242.15 | -1.8656 | 1.3146 | +0.0000 | -12.83 | 510.39 | 60.230 | 498.835 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.13 | -9.6384 | 81.4628 | +0.0000 | -78.65 | 120.28 | 57687.598 | 0.002 | FAIL (5) |
| mos_fs | -40 | 1.65 | 6.24 | -0.0071 | 59.9880 | +0.0000 | -92.13 | 252.09 | 5541.935 | 0.394 | FAIL (4) |
| mos_fs | +125 | 1.35 | 124.34 | -3.4244 | 3.7209 | +0.0000 | -22.67 | 495.73 | 130.599 | 79.477 | FAIL (6) |
| mos_fs | +125 | 1.65 | 173.08 | -2.1790 | 2.2874 | +0.0000 | -15.79 | 510.73 | 84.548 | 399.327 | FAIL (6) |
| mos_tt | +27 | 1.35 | 13.70 | -0.5352 | 37.4954 | +0.0000 | -93.50 | 249.62 | 548.187 | 0.903 | FAIL (5) |
| mos_ss | +27 | 1.35 | 2.33 | -0.0786 | 84.6537 | +0.0000 | -91.24 | 236.54 | 33903.883 | 0.161 | FAIL (4) |
| mos_ff | +27 | 1.35 | 232.66 | -0.2797 | 0.1965 | +0.0000 | -52.30 | 309.75 | 28.869 | 5.288 | FAIL (3) |
| mos_sf | +27 | 1.35 | 20.14 | -0.1162 | 29.9394 | +0.0000 | -102.72 | 297.62 | 259.774 | 1.275 | FAIL (4) |
| mos_fs | +27 | 1.35 | 9.68 | -1.4526 | 43.7589 | +0.0000 | -91.03 | 206.81 | 1022.894 | 0.638 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.11 | 312.88 | 2815.600x | mos_ss / -40 C / 1.35 V | mos_ff / -40 C / 1.65 V |
| irn_uv | 22.252 | 57687.598 | 2592.459x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.000 | 733.133 | 2023573.462x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 7.22 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -12.83 | mos_sf / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 0.11 | mos_ss / -40 C / 1.35 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -48.7293 | mos_ss / -40 C / 1.35 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +0.0002 | mos_ff / -40 C / 1.65 V | PASS |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 90.1796 | mos_ff / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 57687.598 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 733.133 | mos_ff / +125 C / 1.65 V | **FAIL** |
