# PVT -- `D-thdjump`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 250.00 | -0.0131 | 0.1604 | +0.0000 | -49.27 | 330.66 | 28.812 | 7.470 | PASS |
| mos_ss | -40 | 1.35 | 0.16 | -3.0260 | 84.9819 | +0.0000 | -80.50 | 167.90 | 68555.012 | 0.005 | FAIL (5) |
| mos_ss | -40 | 1.65 | 20.03 | -0.0189 | 29.5747 | +0.0000 | -87.01 | 291.13 | 323.366 | 1.151 | FAIL (4) |
| mos_ss | +125 | 1.35 | 65.34 | -9.0323 | 11.3293 | +0.0000 | -70.75 | 293.40 | 259.227 | 8.622 | FAIL (5) |
| mos_ss | +125 | 1.65 | 97.98 | -21.6096 | 5.1609 | +0.0000 | -31.83 | 433.45 | 263.784 | 34.279 | FAIL (5) |
| mos_ff | -40 | 1.35 | 18.27 | -4.8122 | 33.6425 | +0.0000 | -81.33 | 266.08 | 958.032 | 0.701 | FAIL (5) |
| mos_ff | -40 | 1.65 | 484.79 | -0.0096 | 0.1020 | +0.1252 | -19.13 | 330.49 | 20.604 | 18.969 | FAIL (2) |
| mos_ff | +125 | 1.35 | 77.77 | -25.8030 | 6.6886 | +0.0000 | -34.49 | 217.69 | 449.616 | 28.659 | FAIL (6) |
| mos_ff | +125 | 1.65 | 97.82 | -38.8187 | 5.0290 | +0.0000 | -22.14 | 358.18 | 1744.702 | 79.009 | FAIL (6) |
| mos_sf | -40 | 1.35 | 2.37 | -0.3226 | 88.4707 | +0.0000 | -86.20 | 235.63 | 56218.114 | 0.119 | FAIL (5) |
| mos_sf | -40 | 1.65 | 322.34 | -0.0083 | 0.0059 | +0.0059 | -40.39 | 331.29 | 22.144 | 7.928 | FAIL (2) |
| mos_sf | +125 | 1.35 | 96.67 | -20.4776 | 5.4388 | +0.0000 | -39.01 | 251.48 | 248.916 | 18.768 | FAIL (6) |
| mos_sf | +125 | 1.65 | 120.51 | -35.7794 | 3.8799 | +0.0000 | -22.52 | 358.57 | 1150.243 | 58.592 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.95 | -2.6597 | 86.4001 | +0.0000 | -81.93 | 224.00 | 70688.482 | 0.041 | FAIL (5) |
| mos_fs | -40 | 1.65 | 234.65 | -0.0331 | 0.2576 | +0.2992 | -57.63 | 331.63 | 23.776 | 4.688 | FAIL (3) |
| mos_fs | +125 | 1.35 | 58.74 | -11.8760 | 9.7817 | +0.0000 | -78.92 | 276.70 | 312.278 | 14.602 | FAIL (5) |
| mos_fs | +125 | 1.65 | 79.43 | -26.4009 | 6.4491 | +0.0000 | -29.91 | 399.30 | 471.260 | 48.741 | FAIL (5) |
| mos_tt | +27 | 1.35 | 53.13 | -0.3933 | 35.1812 | +9.6597 | -96.23 | 306.39 | 913.414 | 1.909 | FAIL (6) |
| mos_ss | +27 | 1.35 | 5.97 | -0.2695 | 62.9866 | +0.0000 | -90.25 | 251.94 | 45945.415 | 0.387 | FAIL (5) |
| mos_ff | +27 | 1.35 | 248.57 | -0.0746 | 0.2323 | +0.0000 | -49.11 | 329.73 | 28.813 | 6.739 | FAIL (2) |
| mos_sf | +27 | 1.35 | 120.04 | -0.0754 | 10.6364 | +3.2672 | -100.23 | 328.23 | 65.818 | 2.578 | FAIL (5) |
| mos_fs | +27 | 1.35 | 26.43 | -1.9497 | 28.2607 | +0.0000 | -97.53 | 306.71 | 450.426 | 1.383 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.16 | 484.79 | 3018.285x | mos_ss / -40 C / 1.35 V | mos_ff / -40 C / 1.65 V |
| irn_uv | 20.604 | 70688.482 | 3430.819x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.005 | 79.009 | 14746.620x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 167.90 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -19.13 | mos_ff / -40 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 0.16 | mos_ss / -40 C / 1.35 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -38.8187 | mos_ff / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +9.6597 | mos_tt / +27 C / 1.35 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 88.4707 | mos_sf / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 70688.482 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 79.009 | mos_ff / +125 C / 1.65 V | **FAIL** |
