# Operating point -- `lpf_core_H12pc`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.663 | 16.63 | 25.1 | 1935 | 166 | 101 | +64 | sat/weak |
| `gmf_a` | m4 | nmos | 1.984 | 44.75 | 22.6 | 5262 | 695 | 110 | +585 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.60 | 28.1 | 11793 | 529 | 101 | +428 | sat/weak |
| `bridge` | mst | pmos | 2.646 | 58.78 | 22.2 | 4512 | 236 | 105 | +131 | sat/weak |
| `in_b` | m0 | pmos | 2.646 | 62.03 | 23.4 | 4934 | 347 | 104 | +244 | sat/weak |
| `gmf_b` | m14 | pmos | 2.646 | 63.51 | 24.0 | 4493 | 222 | 103 | +119 | sat/weak |
| `rep_gmfb` | r1 | pmos | 2.649 | 63.58 | 24.0 | 11791 | 569 | 103 | +466 | sat/weak |
| `rep_bridge` | r2 | pmos | 2.649 | 58.85 | 22.2 | 12004 | 609 | 105 | +504 | sat/weak |
| `rep_sink` | r3 | nmos | 2.649 | 74.37 | 28.1 | 9446 | 322 | 101 | +221 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1278 → net4 931 → vout_1 695 → net2 529 → 0
Core current **7.942 nA** → **11.912 nW** @ 1.5 V
iref 0.662 nA · vicm 0.24 V · C_total 183.78 pF

All devices saturated and in weak inversion.
