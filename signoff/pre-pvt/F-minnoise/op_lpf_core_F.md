# Operating point -- `lpf_core_F`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.001 | 25.10 | 25.1 | 2595 | 233 | 101 | +131 | sat/weak |
| `gmf_a` | m4 | nmos | 3.215 | 59.67 | 18.6 | 3490 | 810 | 120 | +690 | sat/mod |
| `bias_a_int` | m9 | nmos | 1.001 | 28.09 | 28.1 | 6818 | 577 | 101 | +475 | sat/weak |
| `bridge` | mst | pmos | 4.209 | 55.74 | 13.2 | 3443 | 312 | 133 | +179 | sat/mod |
| `in_b` | m0 | pmos | 4.171 | 102.29 | 24.5 | 2547 | 235 | 102 | +133 | sat/weak |
| `gmf_b` | m14 | pmos | 4.190 | 81.75 | 19.5 | 115 | 144 | 122 | +22 | sat/mod |

DC ladder (mV): VDD 1500 → voutp 1356 → net4 1122 → vout_1 810 → net2 577 → 0
Core current **8.419 nA** → **12.628 nW** @ 1.5 V
iref 1 nA · vicm 0.32 V · C_total 305.02 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 13.2
