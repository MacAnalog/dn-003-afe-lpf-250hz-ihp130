# Operating point -- `lpf_core_G`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.001 | 25.09 | 25.1 | 3086 | 276 | 101 | +175 | sat/weak |
| `gmf_a` | m4 | nmos | 3.775 | 86.37 | 22.9 | 1986 | 809 | 109 | +700 | sat/weak |
| `bias_a_int` | m9 | nmos | 1.001 | 28.08 | 28.1 | 6705 | 533 | 101 | +432 | sat/weak |
| `bridge` | mst | pmos | 4.775 | 61.84 | 13.0 | 2802 | 310 | 134 | +176 | sat/mod |
| `in_b` | m0 | pmos | 4.759 | 116.16 | 24.4 | 2613 | 242 | 102 | +140 | sat/weak |
| `gmf_b` | m14 | pmos | 4.766 | 91.75 | 19.3 | 81 | 138 | 122 | +16 | sat/mod |

DC ladder (mV): VDD 1500 → voutp 1362 → net4 1120 → vout_1 809 → net2 533 → 0
Core current **9.549 nA** → **14.324 nW** @ 1.5 V
iref 1 nA · vicm 0.32 V · C_total 348.22 pF

## Problems

- bridge (mst) has left weak inversion: gm/ID 13.0
