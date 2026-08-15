# Operating point -- `lpf_core_H5`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.663 | 16.63 | 25.1 | 1978 | 166 | 101 | +64 | sat/weak |
| `gmf_a` | m4 | nmos | 1.323 | 31.76 | 24.0 | 6362 | 677 | 107 | +570 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.61 | 28.1 | 9497 | 512 | 101 | +410 | sat/weak |
| `bridge` | mst | pmos | 1.985 | 45.37 | 22.9 | 4376 | 266 | 104 | +161 | sat/weak |
| `in_b` | m0 | pmos | 1.985 | 47.41 | 23.9 | 4430 | 306 | 103 | +203 | sat/weak |
| `gmf_b` | m14 | pmos | 1.985 | 48.30 | 24.3 | 4410 | 251 | 102 | +149 | sat/weak |
| `rep_gmfb` | r1 | pmos | 1.987 | 48.35 | 24.3 | 9903 | 557 | 102 | +454 | sat/weak |
| `rep_bridge` | r2 | pmos | 1.987 | 45.42 | 22.9 | 10009 | 597 | 104 | +492 | sat/weak |
| `rep_sink` | r3 | nmos | 1.987 | 55.79 | 28.1 | 8259 | 347 | 101 | +245 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1249 → net4 943 → vout_1 677 → net2 512 → 0
Core current **5.957 nA** → **8.935 nW** @ 1.5 V
iref 0.662 nA · vicm 0.22 V · C_total 140.41 pF

All devices saturated and in weak inversion.
