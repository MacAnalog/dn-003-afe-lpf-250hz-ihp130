# PVT -- `B-balanced`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 250.01 | -0.0118 | 0.0590 | +0.0000 | -49.86 | 332.23 | 29.376 | 6.010 | PASS |
| mos_ss | -40 | 1.35 | 0.11 | -48.8228 | 41.7909 | +0.0000 | -37.81 | 6.56 | 36508.103 | 0.000 | FAIL (6) |
| mos_ss | -40 | 1.65 | 0.91 | -0.0549 | 88.8808 | +0.0000 | -88.58 | 232.04 | 41532.629 | 0.053 | FAIL (4) |
| mos_ss | +125 | 1.35 | 137.53 | -2.9516 | 3.2492 | +0.0000 | -28.30 | 505.08 | 123.538 | 36.958 | FAIL (5) |
| mos_ss | +125 | 1.65 | 193.09 | -1.8955 | 1.9182 | +0.0000 | -15.30 | 511.00 | 78.194 | 243.005 | FAIL (6) |
| mos_ff | -40 | 1.35 | 0.71 | -0.0907 | 88.9353 | +0.0000 | -87.35 | 228.55 | 43452.606 | 0.035 | FAIL (4) |
| mos_ff | -40 | 1.65 | 313.00 | -0.0075 | 0.0075 | +0.0077 | -42.22 | 333.12 | 23.004 | 6.045 | FAIL (2) |
| mos_ff | +125 | 1.35 | 168.46 | -2.7290 | 2.3831 | +0.0000 | -16.51 | 505.41 | 95.202 | 190.727 | FAIL (6) |
| mos_ff | +125 | 1.65 | 219.28 | -2.3477 | 1.5594 | +0.0000 | -13.51 | 507.22 | 68.998 | 719.594 | FAIL (6) |
| mos_sf | -40 | 1.35 | 0.16 | -3.3550 | 85.8898 | +0.0000 | -83.22 | 169.65 | 52686.155 | 0.005 | FAIL (5) |
| mos_sf | -40 | 1.65 | 15.50 | -0.0057 | 34.3633 | +0.0000 | -87.22 | 276.41 | 339.445 | 0.887 | FAIL (4) |
| mos_sf | +125 | 1.35 | 189.07 | -2.3074 | 1.9728 | +0.0000 | -17.08 | 509.95 | 84.645 | 106.176 | FAIL (6) |
| mos_sf | +125 | 1.65 | 242.90 | -1.9079 | 1.3078 | +0.0000 | -12.77 | 509.07 | 61.956 | 488.433 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.13 | -9.7758 | 79.9208 | +0.0000 | -77.01 | 118.33 | 52916.871 | 0.002 | FAIL (5) |
| mos_fs | -40 | 1.65 | 6.27 | -0.0070 | 60.2169 | +0.0000 | -91.04 | 250.00 | 6310.747 | 0.366 | FAIL (4) |
| mos_fs | +125 | 1.35 | 124.28 | -3.4194 | 3.7217 | +0.0000 | -22.41 | 497.35 | 135.733 | 76.723 | FAIL (6) |
| mos_fs | +125 | 1.65 | 173.53 | -2.1884 | 2.2784 | +0.0000 | -15.73 | 509.66 | 87.184 | 390.243 | FAIL (6) |
| mos_tt | +27 | 1.35 | 13.91 | -0.4357 | 37.1518 | +0.0000 | -92.26 | 251.03 | 546.027 | 0.851 | FAIL (5) |
| mos_ss | +27 | 1.35 | 2.37 | -0.0566 | 84.7266 | +0.0000 | -89.57 | 236.89 | 34158.550 | 0.151 | FAIL (4) |
| mos_ff | +27 | 1.35 | 234.39 | -0.2462 | 0.1681 | +0.0000 | -52.17 | 311.26 | 29.644 | 4.976 | FAIL (3) |
| mos_sf | +27 | 1.35 | 20.28 | -0.0789 | 29.2756 | +0.0000 | -99.37 | 296.27 | 247.151 | 1.199 | FAIL (4) |
| mos_fs | +27 | 1.35 | 9.85 | -1.2152 | 44.0073 | +0.0000 | -90.55 | 210.14 | 1086.912 | 0.604 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.11 | 313.00 | 2819.807x | mos_ss / -40 C / 1.35 V | mos_ff / -40 C / 1.65 V |
| irn_uv | 23.004 | 52916.871 | 2300.373x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.000 | 719.594 | 2127423.535x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 6.56 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -12.77 | mos_sf / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 0.11 | mos_ss / -40 C / 1.35 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -48.8228 | mos_ss / -40 C / 1.35 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +0.0077 | mos_ff / -40 C / 1.65 V | PASS |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 88.9353 | mos_ff / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 52916.871 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 719.594 | mos_ff / +125 C / 1.65 V | **FAIL** |
