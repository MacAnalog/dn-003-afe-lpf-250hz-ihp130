# Operating point -- `lpf_core_H12`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.663 | 16.63 | 25.1 | 2032 | 168 | 101 | +67 | sat/weak |
| `gmf_a` | m4 | nmos | 1.984 | 44.75 | 22.6 | 5278 | 697 | 110 | +588 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.70 | 28.2 | 11633 | 529 | 101 | +428 | sat/weak |
| `bridge` | mst | pmos | 2.646 | 58.64 | 22.2 | 4430 | 234 | 106 | +128 | sat/weak |
| `in_b` | m0 | pmos | 2.646 | 62.03 | 23.4 | 4973 | 350 | 104 | +246 | sat/weak |
| `gmf_b` | m14 | pmos | 2.646 | 63.50 | 24.0 | 4444 | 219 | 103 | +116 | sat/weak |
| `rep_gmfb` | r1 | pmos | 2.649 | 63.58 | 24.0 | 11812 | 569 | 103 | +466 | sat/weak |
| `rep_bridge` | r2 | pmos | 2.649 | 58.71 | 22.2 | 11954 | 610 | 106 | +505 | sat/weak |
| `rep_sink` | r3 | nmos | 2.649 | 74.76 | 28.2 | 9399 | 321 | 101 | +220 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1281 → net4 931 → vout_1 697 → net2 529 → 0
Core current **7.941 nA** → **11.912 nW** @ 1.5 V
iref 0.662 nA · vicm 0.24 V · C_total 183.46 pF

All devices saturated and in weak inversion.
