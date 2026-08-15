# PVT -- `F-minnoise`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.95 | -0.0327 | 0.0546 | +0.0093 | -48.99 | 336.41 | 26.243 | 12.628 | PASS |
| mos_ss | -40 | 1.35 | 0.13 | -7.7582 | 103.7184 | +0.0000 | -104.41 | 144.63 | 327573.544 | 0.005 | FAIL (5) |
| mos_ss | -40 | 1.65 | 11.63 | -0.2487 | 40.0046 | +0.0000 | -102.34 | 288.84 | 637.994 | 1.264 | FAIL (5) |
| mos_ss | +125 | 1.35 | 213.84 | -0.8917 | 0.2859 | +0.0974 | -49.63 | 335.37 | 35.997 | 16.641 | FAIL (3) |
| mos_ss | +125 | 1.65 | 362.51 | -12.4094 | 0.4973 | +0.0000 | -16.48 | 322.34 | 74.133 | 74.912 | FAIL (7) |
| mos_ff | -40 | 1.35 | 11.08 | -10.5252 | 46.9905 | +0.0000 | -87.49 | 255.60 | 5734.133 | 0.567 | FAIL (5) |
| mos_ff | -40 | 1.65 | 472.66 | -0.0237 | 0.6594 | +1.5622 | -23.25 | 335.39 | 19.392 | 32.925 | FAIL (4) |
| mos_ff | +125 | 1.35 | 374.69 | -11.5550 | 0.4466 | +0.0000 | -16.22 | 322.69 | 66.348 | 61.640 | FAIL (7) |
| mos_ff | +125 | 1.65 | 588.59 | -31.8330 | 0.2391 | +0.0000 | -6.38 | 253.21 | 500.167 | 181.455 | FAIL (7) |
| mos_sf | -40 | 1.35 | 1.18 | -0.5765 | 103.4588 | +0.0000 | -111.94 | 245.03 | 197500.758 | 0.105 | FAIL (5) |
| mos_sf | -40 | 1.65 | 298.58 | -0.0176 | 0.1531 | +0.1926 | -44.70 | 336.56 | 20.679 | 11.939 | FAIL (2) |
| mos_sf | +125 | 1.35 | 268.43 | -11.0764 | 0.9323 | +0.0000 | -23.74 | 322.66 | 66.978 | 38.820 | FAIL (6) |
| mos_sf | +125 | 1.65 | 453.11 | -31.2876 | 0.4011 | +0.0000 | -8.79 | 246.73 | 562.951 | 132.013 | FAIL (7) |
| mos_fs | -40 | 1.35 | 0.51 | -3.4199 | 100.9484 | +0.0000 | -111.26 | 232.06 | 267978.756 | 0.036 | FAIL (5) |
| mos_fs | -40 | 1.65 | 203.60 | -0.9535 | 1.5727 | +0.0000 | -62.31 | 335.45 | 22.649 | 6.179 | FAIL (3) |
| mos_fs | +125 | 1.35 | 281.15 | -0.9590 | 0.4229 | +0.4229 | -36.89 | 334.68 | 34.863 | 29.787 | FAIL (5) |
| mos_fs | +125 | 1.65 | 468.41 | -12.7792 | 0.2658 | +0.0000 | -11.83 | 322.41 | 70.487 | 109.305 | FAIL (7) |
| mos_tt | +27 | 1.35 | 35.11 | -1.7391 | 33.7668 | +0.0000 | -110.88 | 323.77 | 583.557 | 2.577 | FAIL (5) |
| mos_ss | +27 | 1.35 | 3.91 | -0.2434 | 68.4396 | +0.0000 | -103.22 | 262.39 | 14502.581 | 0.469 | FAIL (5) |
| mos_ff | +27 | 1.35 | 245.50 | -0.3325 | 0.4795 | +0.0000 | -49.39 | 335.44 | 25.948 | 11.008 | FAIL (2) |
| mos_sf | +27 | 1.35 | 114.62 | -0.2531 | 13.0131 | +1.7425 | -84.98 | 336.51 | 61.181 | 3.671 | FAIL (5) |
| mos_fs | +27 | 1.35 | 19.57 | -3.5957 | 31.7435 | +0.0000 | -107.44 | 311.18 | 497.054 | 1.782 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.13 | 588.59 | 4396.931x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |
| irn_uv | 19.392 | 327573.544 | 16892.376x | mos_ff / -40 C / 1.65 V | mos_ss / -40 C / 1.35 V |
| p_core_nw | 0.005 | 181.455 | 37507.118x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 144.63 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -6.38 | mos_ff / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 588.59 | mos_ff / +125 C / 1.65 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -31.8330 | mos_ff / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +1.7425 | mos_sf / +27 C / 1.35 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 103.7184 | mos_ss / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 327573.544 | mos_ss / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 181.455 | mos_ff / +125 C / 1.65 V | **FAIL** |
