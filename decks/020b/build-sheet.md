# 020B — build sheet

| role         | type          | W (um) | L (um) | m | area (um2) |
|---|---|---|---|---|---|
| in_a         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_a        | sg13_hv_nmos  | 4.000 | 4.000 | 1 | 16.0 |
| bias_a_int   | sg13_hv_nmos  | 5.000 | 8.000 | 1 | 40.0 |
| bridge       | sg13_hv_pmos  | 3.000 | 8.400 | 1 | 25.2 |
| in_b         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_b        | sg13_hv_pmos  | 15.000 | 12.000 | 1 | 180.0 |

Total drawn capacitance: **314.58 pF** (c1_a 7.093 / c2_a 47.353 / c1_b 117.349 / c2_b 18.345 pF)

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | region |
|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.000 | 25.04 | 25.0 | 2104 | 272 | sat/weak |
| `gmf_a` | m4 | nmos | 2.234 | 63.02 | 28.2 | 1151 | 687 | sat/weak |
| `bias_a_int` | m9 | nmos | 1.000 | 28.14 | 28.1 | 2739 | 415 | sat/weak |
| `bridge` | mst | pmos | 3.234 | 76.34 | 23.6 | 3075 | 285 | sat/weak |
| `in_b` | m0 | pmos | 3.234 | 79.83 | 24.7 | 1893 | 249 | sat/weak |
| `gmf_b` | m14 | pmos | 3.234 | 80.32 | 24.8 | 3758 | 280 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1220 → net4 972 → vout_1 687 → net2 415 → 0
Core current **6.468 nA** → **9.702 nW** @ 1.5 V
iref 1 nA · vicm 0.2 V · C_total 314.58 pF
