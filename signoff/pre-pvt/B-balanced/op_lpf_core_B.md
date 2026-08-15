# Operating point -- `lpf_core_B`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.661 | 21.13 | 32.0 | 2620 | 440 | 101 | +339 | sat/weak |
| `gmf_a` | m4 | nmos | 1.341 | 37.82 | 28.2 | 1711 | 817 | 101 | +716 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.662 | 18.62 | 28.1 | 3931 | 377 | 101 | +275 | sat/weak |
| `bridge` | mst | pmos | 2.003 | 45.79 | 22.9 | 808 | 138 | 104 | +34 | sat/weak |
| `in_b` | m0 | pmos | 2.003 | 50.16 | 25.0 | 4616 | 363 | 102 | +262 | sat/weak |
| `gmf_b` | m14 | pmos | 2.003 | 49.24 | 24.6 | 2683 | 182 | 102 | +79 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1318 → net4 955 → vout_1 817 → net2 377 → 0
Core current **4.007 nA** → **6.010 nW** @ 1.5 V
iref 0.662 nA · vicm 0.65 V · C_total 152.85 pF

All devices saturated and in weak inversion.
