# Operating point -- `lpf_core_D`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.661 | 21.14 | 32.0 | 2625 | 429 | 101 | +328 | sat/weak |
| `gmf_a` | m4 | nmos | 1.828 | 51.55 | 28.2 | 1698 | 817 | 101 | +716 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.59 | 28.1 | 12897 | 388 | 101 | +286 | sat/weak |
| `bridge` | mst | pmos | 2.490 | 25.66 | 10.3 | 3422 | 314 | 154 | +159 | sat/mod |
| `in_b` | m0 | pmos | 2.481 | 62.00 | 25.0 | 2465 | 196 | 102 | +95 | sat/weak |
| `gmf_b` | m14 | pmos | 2.485 | 50.88 | 20.5 | 437 | 173 | 119 | +54 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1327 → net4 1131 → vout_1 817 → net2 388 → 0
Core current **4.980 nA** → **7.470 nW** @ 1.5 V
iref 0.662 nA · vicm 0.65 V · C_total 187.86 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 10.3
