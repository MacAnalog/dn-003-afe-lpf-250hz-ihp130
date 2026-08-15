# Operating point -- `lpf_core_A`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.442 | 11.08 | 25.1 | 3050 | 273 | 101 | +172 | sat/weak |
| `gmf_a` | m4 | nmos | 0.940 | 26.58 | 28.3 | 1185 | 657 | 101 | +556 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.442 | 12.44 | 28.2 | 2842 | 384 | 101 | +283 | sat/weak |
| `bridge` | mst | pmos | 1.382 | 31.51 | 22.8 | 3252 | 298 | 104 | +193 | sat/weak |
| `in_b` | m0 | pmos | 1.382 | 34.58 | 25.0 | 2267 | 205 | 102 | +103 | sat/weak |
| `gmf_b` | m14 | pmos | 1.382 | 33.91 | 24.5 | 4572 | 341 | 102 | +239 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1159 → net4 954 → vout_1 657 → net2 384 → 0
Core current **2.764 nA** → **4.146 nW** @ 1.5 V
iref 0.442 nA · vicm 0.2 V · C_total 104.41 pF

All devices saturated and in weak inversion.
