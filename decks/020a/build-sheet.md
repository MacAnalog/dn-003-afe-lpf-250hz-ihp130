# 020A — build sheet

| role         | type          | W (um) | L (um) | m | area (um2) |
|---|---|---|---|---|---|
| in_a         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_a        | sg13_hv_nmos  | 4.000 | 4.000 | 1 | 16.0 |
| bias_a_int   | sg13_hv_nmos  | 5.000 | 8.000 | 1 | 40.0 |
| bridge       | sg13_hv_pmos  | 12.000 | 8.400 | 1 | 100.8 |
| in_b         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_b        | sg13_hv_pmos  | 30.000 | 12.000 | 1 | 360.0 |
| bias_b_out   | sg13_hv_pmos  | 15.000 | 12.000 | 1 | 180.0 |

Total drawn capacitance: **747.79 pF** (c1_a 7.385 / c2_a 165.714 / c1_b 234.051 / c2_b 99.205 pF)

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | region |
|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.001 | 25.06 | 25.0 | 1726 | 224 | sat/weak |
| `gmf_a` | m4 | nmos | 8.648 | 238.47 | 27.6 | 1011 | 687 | sat/weak |
| `bias_a_int` | m9 | nmos | 1.001 | 28.16 | 28.1 | 2783 | 463 | sat/weak |
| `bridge` | mst | pmos | 9.649 | 231.89 | 24.0 | 2967 | 273 | sat/weak |
| `in_b` | m0 | pmos | 9.649 | 227.03 | 23.5 | 2193 | 305 | sat/weak |
| `gmf_b` | m6 | pmos | 8.644 | 213.29 | 24.7 | 3111 | 234 | sat/weak |
| `bias_b_out` | m14 | pmos | 1.005 | 25.23 | 25.1 | 3187 | 234 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1266 → net4 960 → vout_1 687 → net2 463 → 0
Core current **19.298 nA** → **28.947 nW** @ 1.5 V
iref 1 nA · vicm 0.2 V · C_total 747.79 pF
