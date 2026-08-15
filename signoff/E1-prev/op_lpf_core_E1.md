# Operating point -- `lpf_core_E1`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.661 | 21.14 | 32.0 | 2627 | 420 | 101 | +319 | sat/weak |
| `gmf_a` | m4 | nmos | 2.367 | 66.71 | 28.2 | 1685 | 817 | 101 | +716 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.59 | 28.1 | 13073 | 397 | 101 | +296 | sat/weak |
| `bridge` | mst | pmos | 3.005 | 29.77 | 9.9 | 3237 | 324 | 158 | +166 | sat/mod |
| `in_b` | m0 | pmos | 2.993 | 74.62 | 24.9 | 2418 | 194 | 102 | +92 | sat/weak |
| `gmf_b` | m14 | pmos | 2.999 | 65.14 | 21.7 | 418 | 165 | 116 | +49 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1335 → net4 1141 → vout_1 817 → net2 397 → 0
Core current **6.009 nA** → **9.014 nW** @ 1.5 V
iref 0.662 nA · vicm 0.65 V · C_total 229.35 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 9.9
