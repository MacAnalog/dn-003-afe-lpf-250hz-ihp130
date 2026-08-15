.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=1e-06 l=4.5e-05 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=1e-06 l=4.5e-05 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
  xmst vout_1 vbn net4 net4 sg13_hv_pmos w=4.8e-07 l=3.36e-05 ng=1 m=1
  xmstn vout_2 vbn net1 net1 sg13_hv_pmos w=4.8e-07 l=3.36e-05 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_lv_pmos w=1.28e-06 l=9.6e-05 ng=1 m=1
  xm15 voutn net1 vdd vdd sg13_lv_pmos w=1.28e-06 l=9.6e-05 ng=1 m=1
  c13 net2   vout_1 8.61884e-12
  c17 net3   vout_2 8.61884e-12
  c19 vout_2 vout_1 2.36443e-11
  c1  voutp  net4   8.10786e-11
  c10 voutn  net1   8.10786e-11
  c12 voutn  voutp  1.69787e-11
.ends lpf_core

