# PVT -- `G-maxthd`

Process x temperature x supply screen: corners ss/ff/sf/fs (+ tt anchors), T = -40/27/125 C, VDD = 1.35/1.5/1.65 V -- the repo's 22-point reduced set (`lab.corners.REDUCED`). Group-delay columns are soft (reported, not spec lines).

**1 of 22 corners pass every spec line.** The family is threshold-referenced (see signoff/README.md limitation 1): off-nominal supply moves the reuse-ladder current, and that is the documented, unfixable-by-sizing mechanism behind the failures.

| corner | T (C) | VDD (V) | fc_hz | dc_db | ripple_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mos_tt | +27 | 1.50 | 249.88 | -0.0417 | 0.0542 | +0.0029 | -48.69 | 343.53 | 26.807 | 14.324 | PASS |
| mos_ss | -40 | 1.35 | 0.14 | -7.0074 | 107.3086 | +0.0000 | -108.80 | 153.70 | 502594.406 | 0.006 | FAIL (5) |
| mos_ss | -40 | 1.65 | 12.59 | -0.5786 | 38.8315 | +0.0000 | -117.76 | 308.02 | 584.549 | 1.563 | FAIL (5) |
| mos_ss | +125 | 1.35 | 213.44 | -0.3443 | 0.2583 | +0.2583 | -51.05 | 343.04 | 36.207 | 18.001 | FAIL (4) |
| mos_ss | +125 | 1.65 | 388.77 | -6.8278 | 0.1207 | +0.1211 | -21.58 | 337.41 | 38.556 | 80.443 | FAIL (4) |
| mos_ff | -40 | 1.35 | 11.08 | -14.3381 | 47.3214 | +0.0000 | -87.27 | 260.32 | 9616.463 | 0.595 | FAIL (5) |
| mos_ff | -40 | 1.65 | 483.26 | -0.0319 | 0.4852 | +1.0856 | -22.00 | 343.23 | 19.781 | 38.192 | FAIL (4) |
| mos_ff | +125 | 1.35 | 395.66 | -6.1641 | 0.1050 | +0.1050 | -21.03 | 337.47 | 36.468 | 66.486 | FAIL (4) |
| mos_ff | +125 | 1.65 | 621.16 | -23.3344 | 0.1245 | +0.0000 | -7.88 | 308.12 | 204.614 | 194.716 | FAIL (6) |
| mos_sf | -40 | 1.35 | 1.35 | -1.2375 | 111.5622 | +0.0000 | -113.28 | 251.60 | 368561.011 | 0.133 | FAIL (5) |
| mos_sf | -40 | 1.65 | 308.51 | -0.0239 | 0.1348 | +0.1617 | -42.89 | 343.79 | 21.061 | 14.228 | FAIL (2) |
| mos_sf | +125 | 1.35 | 341.06 | -6.1146 | 0.2231 | +0.2243 | -28.17 | 338.31 | 38.001 | 41.965 | FAIL (5) |
| mos_sf | +125 | 1.65 | 577.05 | -23.5737 | 0.1580 | +0.0000 | -8.84 | 312.65 | 194.805 | 141.804 | FAIL (6) |
| mos_fs | -40 | 1.35 | 0.59 | -5.8117 | 107.2004 | +0.0000 | -112.88 | 237.08 | 513129.723 | 0.043 | FAIL (5) |
| mos_fs | -40 | 1.65 | 209.41 | -1.2611 | 1.6742 | +0.0000 | -60.63 | 342.32 | 22.992 | 7.248 | FAIL (3) |
| mos_fs | +125 | 1.35 | 276.23 | -0.2713 | 0.4800 | +0.4800 | -38.09 | 342.63 | 34.777 | 32.153 | FAIL (5) |
| mos_fs | +125 | 1.65 | 418.25 | -7.2259 | 0.0368 | +0.0023 | -17.32 | 335.91 | 38.240 | 117.284 | FAIL (4) |
| mos_tt | +27 | 1.35 | 53.81 | -1.2692 | 36.4540 | +7.2444 | -113.93 | 337.84 | 745.150 | 2.927 | FAIL (5) |
| mos_ss | +27 | 1.35 | 3.96 | -0.4661 | 68.0700 | +0.0000 | -105.97 | 273.18 | 13531.555 | 0.549 | FAIL (5) |
| mos_ff | +27 | 1.35 | 245.14 | -0.4140 | 0.4794 | +0.0000 | -49.06 | 342.62 | 26.425 | 12.498 | FAIL (2) |
| mos_sf | +27 | 1.35 | 121.58 | -0.3296 | 10.5690 | +1.4936 | -82.23 | 343.68 | 50.602 | 4.250 | FAIL (5) |
| mos_fs | +27 | 1.35 | 19.97 | -5.0033 | 33.3359 | +0.0000 | -112.13 | 323.27 | 709.559 | 1.953 | FAIL (5) |

**1 of 22 corners PASS** (21 fail, 0 non-converged, 0 error).

| quantity | min | max | span (max/min) | min at | max at |
|---|---|---|---|---|---|
| fc_hz | 0.14 | 621.16 | 4582.360x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |
| irn_uv | 19.781 | 513129.723 | 25940.094x | mos_ff / -40 C / 1.65 V | mos_fs / -40 C / 1.35 V |
| p_core_nw | 0.006 | 194.716 | 31397.150x | mos_ss / -40 C / 1.35 V | mos_ff / +125 C / 1.65 V |

| # | spec line | bound | worst measured | at corner | verdict |
|---|---|---|---|---|---|
| ph_max_deg | S1 biquad-order certificate (max unwrapped phase lag) | >= 330 | 153.70 | mos_ss / -40 C / 1.35 V | **FAIL** |
| a1000_db | S1 companion: |H| at 1 kHz | <= -48 | -7.88 | mos_ff / +125 C / 1.65 V | **FAIL** |
| fc_hz | S2 cutoff | 245..255 | 621.16 | mos_ff / +125 C / 1.65 V | **FAIL** |
| dc_db | S3 passband gain | abs<= 0.2 | -23.5737 | mos_sf / +125 C / 1.65 V | **FAIL** |
| peak_db | S4 peaking | <= 0.2 | +7.2444 | mos_tt / +27 C / 1.35 V | **FAIL** |
| ripple_db | S3 passband flatness to 150 Hz | <= 0.2 | 111.5622 | mos_sf / -40 C / 1.35 V | **FAIL** |
| irn_uv | S5 input-referred noise, 0.5-200 Hz | < 40 | 513129.723 | mos_fs / -40 C / 1.35 V | **FAIL** |
| p_core_nw | S6 filter-core power | < 50 | 194.716 | mos_ff / +125 C / 1.65 V | **FAIL** |
