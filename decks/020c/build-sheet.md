# 020C — build sheet

| role         | type          | W (um) | L (um) | m | area (um2) |
|---|---|---|---|---|---|
| in_a         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_a        | sg13_hv_nmos  | 4.000 | 4.000 | 1 | 16.0 |
| bias_a_int   | sg13_hv_nmos  | 5.000 | 8.000 | 1 | 40.0 |
| bridge       | sg13_hv_pmos  | 2.500 | 8.400 | 1 | 21.0 |
| in_b         | sg13_hv_pmos  | 4.000 | 4.000 | 1 | 16.0 |
| gmf_b        | sg13_hv_pmos  | 12.500 | 12.000 | 1 | 150.0 |

Total drawn capacitance: **260.94 pF** (c1_a 6.943 / c2_a 39.219 / c1_b 96.122 / c2_b 15.590 pF)

| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | \|Vds\| (mV) | region |
|---|---|---|---|---|---|---|---|---|
| `in_a` | m2 | pmos | 1.000 | 25.04 | 25.0 | 2176 | 282 | sat/weak |
| `gmf_a` | m4 | nmos | 1.706 | 48.19 | 28.2 | 1165 | 687 | sat/weak |
| `bias_a_int` | m9 | nmos | 1.000 | 28.14 | 28.1 | 2729 | 405 | sat/weak |
| `bridge` | mst | pmos | 2.706 | 63.86 | 23.6 | 3084 | 285 | sat/weak |
| `in_b` | m0 | pmos | 2.706 | 67.06 | 24.8 | 1847 | 242 | sat/weak |
| `gmf_b` | m14 | pmos | 2.706 | 67.20 | 24.8 | 3858 | 287 | sat/weak |

DC ladder (mV): VDD 1500 → voutp 1213 → net4 972 → vout_1 687 → net2 405 → 0
Core current **5.413 nA** → **8.119 nW** @ 1.5 V
iref 1 nA · vicm 0.2 V · C_total 260.94 pF
