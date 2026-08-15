# Operating point -- `lpf_core_022`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.661 | 21.14 | 32.0 | 2619 | 400 | 101 | +299 | sat/weak |
| `gmf_a` | m4 | nmos | 4.175 | 117.30 | 28.1 | 1641 | 817 | 102 | +715 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.59 | 28.1 | 13435 | 417 | 101 | +316 | sat/weak |
| `bridge` | mst | pmos | 4.834 | 47.85 | 9.9 | 2587 | 324 | 158 | +166 | sat/mod |
| `in_b` | m0 | pmos | 4.827 | 119.25 | 24.7 | 2646 | 213 | 102 | +111 | sat/weak |
| `gmf_b` | m14 | pmos | 4.830 | 105.04 | 21.7 | 184 | 146 | 116 | +30 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1354 → net4 1141 → vout_1 817 → net2 417 → 0
Core current **9.668 nA** → **14.502 nW** @ 1.5 V
iref 0.662 nA · vicm 0.65 V · C_total 366.26 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 9.9
