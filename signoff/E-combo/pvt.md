# PVT -- `E-combo`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.88 | -0.0207 | 0.0546 | +0.0015 | -48.92 | 334.63 | 27.268 | 8.881 | PASS |
| mos_ss | -40 | 1.35 | 0.14 | -6.6770 | 98.6516 | +0.0000 | -98.61 | 149.70 | 255223.264 | 0.004 | FAIL (5) |
| mos_ss | -40 | 1.65 | 12.70 | -0.0825 | 37.7348 | +0.0000 | -94.74 | 280.95 | 618.370 | 0.982 | FAIL (4) |
| mos_ss | +125 | 1.35 | 219.15 | -0.8831 | 0.2657 | +0.2657 | -50.31 | 333.64 | 36.751 | 11.175 | FAIL (4) |
| mos_ss | +125 | 1.65 | 430.64 | -11.2404 | 0.0810 | +0.0000 | -17.55 | 321.22 | 50.312 | 49.889 | FAIL (5) |
| mos_ff | -40 | 1.35 | 12.62 | -7.4642 | 42.9345 | +0.0000 | -85.01 | 257.64 | 3025.069 | 0.514 | FAIL (5) |
| mos_ff | -40 | 1.65 | 488.76 | -0.0174 | 0.5317 | +1.2486 | -21.60 | 333.69 | 19.689 | 23.655 | FAIL (4) |
| mos_ff | +125 | 1.35 | 437.39 | -10.3597 | 0.0713 | +0.0000 | -17.18 | 321.54 | 46.376 | 41.269 | FAIL (5) |
| mos_ff | +125 | 1.65 | 724.98 | -31.0220 | 0.1383 | +0.0000 | -5.15 | 273.56 | 387.132 | 120.868 | FAIL (6) |
| mos_sf | -40 | 1.35 | 1.33 | -0.2681 | 100.3467 | +0.0000 | -107.09 | 243.38 | 164995.905 | 0.085 | FAIL (5) |
| mos_sf | -40 | 1.65 | 305.75 | -0.0137 | 0.2386 | +0.3141 | -43.44 | 334.77 | 21.382 | 8.807 | FAIL (4) |
| mos_sf | +125 | 1.35 | 351.06 | -10.1353 | 0.1916 | +0.0000 | -24.14 | 322.66 | 48.856 | 26.038 | FAIL (5) |
| mos_sf | +125 | 1.65 | 577.91 | -30.3158 | 0.2282 | +0.0000 | -7.04 | 272.78 | 344.574 | 87.971 | FAIL (7) |
| mos_fs | -40 | 1.35 | 0.55 | -1.9976 | 98.7248 | +0.0000 | -105.54 | 231.82 | 206902.856 | 0.031 | FAIL (5) |
| mos_fs | -40 | 1.65 | 191.97 | -0.6449 | 1.2175 | +1.3100 | -63.55 | 333.45 | 23.858 | 4.704 | FAIL (4) |
| mos_fs | +125 | 1.35 | 284.43 | -0.8057 | 0.4955 | +0.4955 | -37.03 | 332.91 | 34.905 | 19.951 | FAIL (5) |
| mos_fs | +125 | 1.65 | 491.92 | -11.8158 | 0.0649 | +0.0000 | -13.66 | 318.85 | 49.858 | 72.737 | FAIL (6) |
| mos_tt | +27 | 1.35 | 25.86 | -0.6860 | 24.1518 | +0.0000 | -92.08 | 318.06 | 184.983 | 1.931 | FAIL (5) |
| mos_ss | +27 | 1.35 | 4.01 | -0.0608 | 68.2797 | +0.0000 | -99.53 | 257.38 | 19898.559 | 0.343 | FAIL (4) |
| mos_ff | +27 | 1.35 | 247.96 | -0.1888 | 0.3175 | +0.0000 | -49.03 | 333.90 | 26.919 | 7.856 | FAIL (1) |
| mos_sf | +27 | 1.35 | 41.08 | -0.2501 | 36.2712 | +2.7070 | -101.79 | 303.17 | 821.453 | 2.662 | FAIL (6) |
| mos_fs | +27 | 1.35 | 18.96 | -1.6162 | 30.4510 | +0.0000 | -104.32 | 302.07 | 402.931 | 1.391 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.14 | 724.98 | 5291.342x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |
| irn_uv | 19.689 | 255223.264 | 12962.670x | mos_ff / -40 C / 1.65 V | mos_ss / -40 C / 1.35 V |
| p_core_nw | 0.004 | 120.868 | 31384.921x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 149.70 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -5.15 | mos_ff / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 724.98 | mos_ff / +125 C / 1.65 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -31.0220 | mos_ff / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +2.7070 | mos_sf / +27 C / 1.35 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 100.3467 | mos_sf / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 255223.264 | mos_ss / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 120.868 | mos_ff / +125 C / 1.65 V | **FAIL** |
