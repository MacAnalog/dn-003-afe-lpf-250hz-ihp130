# Operating point -- `lpf_core_H5pc`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.663 | 16.63 | 25.1 | 1878 | 163 | 101 | +62 | sat/weak |
| `gmf_a` | m4 | nmos | 1.322 | 31.76 | 24.0 | 6343 | 675 | 107 | +568 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.60 | 28.1 | 9609 | 512 | 101 | +410 | sat/weak |
| `bridge` | mst | pmos | 1.985 | 45.00 | 22.7 | 4400 | 268 | 105 | +164 | sat/weak |
| `in_b` | m0 | pmos | 1.985 | 47.41 | 23.9 | 4391 | 303 | 103 | +200 | sat/weak |
| `gmf_b` | m14 | pmos | 1.985 | 48.30 | 24.3 | 4457 | 254 | 102 | +151 | sat/weak |
| `rep_gmfb` | r1 | pmos | 1.987 | 48.35 | 24.3 | 9903 | 557 | 102 | +454 | sat/weak |
| `rep_bridge` | r2 | pmos | 1.987 | 45.05 | 22.7 | 10032 | 600 | 105 | +496 | sat/weak |
| `rep_sink` | r3 | nmos | 1.987 | 55.78 | 28.1 | 8304 | 343 | 101 | +242 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1246 → net4 943 → vout_1 675 → net2 512 → 0
Core current **5.956 nA** → **8.935 nW** @ 1.5 V
iref 0.662 nA · vicm 0.22 V · C_total 141.94 pF

All devices saturated and in weak inversion.
