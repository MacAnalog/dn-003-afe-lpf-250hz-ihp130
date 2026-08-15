# Operating point -- `lpf_core_E`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.001 | 25.09 | 25.1 | 2877 | 258 | 101 | +156 | sat/weak |
| `gmf_a` | m4 | nmos | 1.963 | 40.84 | 20.8 | 4313 | 809 | 114 | +696 | sat/weak |
| `bias_a_int` | m9 | nmos | 1.001 | 28.09 | 28.1 | 6755 | 552 | 101 | +450 | sat/weak |
| `bridge` | mst | pmos | 2.960 | 38.40 | 13.0 | 3510 | 310 | 134 | +176 | sat/mod |
| `in_b` | m0 | pmos | 2.935 | 72.67 | 24.8 | 2440 | 223 | 102 | +121 | sat/weak |
| `gmf_b` | m14 | pmos | 2.947 | 56.72 | 19.2 | 211 | 158 | 123 | +35 | sat/mod |

DC ladder (mV): VDD 1500 → voutp 1342 → net4 1120 → vout_1 809 → net2 552 → 0
Core current **5.921 nA** → **8.881 nW** @ 1.5 V
iref 1 nA · vicm 0.32 V · C_total 220.02 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 13.0
