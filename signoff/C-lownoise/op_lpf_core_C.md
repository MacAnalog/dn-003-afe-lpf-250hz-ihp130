# Operating point -- `lpf_core_C`

Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` (PSP103 `vdss` is Vdsat); P half shown, N half identical by symmetry.

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | \|Vdsat\| (mV) | margin (mV) | region |
|---|---|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 0.661 | 21.14 | 32.0 | 2622 | 437 | 101 | +336 | sat/weak |
| `gmf_a` | m4 | nmos | 1.465 | 41.32 | 28.2 | 1708 | 817 | 101 | +716 | sat/weak |
| `bias_a_int` | m9 | nmos | 0.663 | 18.59 | 28.1 | 12742 | 380 | 101 | +279 | sat/weak |
| `bridge` | mst | pmos | 2.126 | 48.32 | 22.7 | 689 | 136 | 105 | +31 | sat/weak |
| `in_b` | m0 | pmos | 2.126 | 53.21 | 25.0 | 4674 | 368 | 102 | +267 | sat/weak |
| `gmf_b` | m14 | pmos | 2.126 | 52.17 | 24.5 | 2632 | 179 | 102 | +77 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1321 → net4 953 → vout_1 817 → net2 380 → 0
Core current **4.252 nA** → **6.379 nW** @ 1.5 V
iref 0.662 nA · vicm 0.65 V · C_total 164.00 pF

All devices saturated and in weak inversion.
