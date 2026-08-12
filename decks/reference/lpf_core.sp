.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm3 net2 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm13 net3 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm9 vout_1 vbp vdd vdd sg13_hv_pmos w=5e-06 l=1.2e-05 ng=1 m=2
  xm10 vout_2 vbp vdd vdd sg13_hv_pmos w=5e-06 l=1.2e-05 ng=1 m=2
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm11 net4 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm12 net1 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm6 voutp net4 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm7 voutn net1 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm14 voutp vbp vdd vdd sg13_hv_pmos w=5e-06 l=1.2e-05 ng=1 m=2
  xm15 voutn vbp vdd vdd sg13_hv_pmos w=5e-06 l=1.2e-05 ng=1 m=2
  c13 net2   vout_1 2.94678e-11
  c17 net3   vout_2 2.94678e-11
  c19 vout_2 vout_1 6.2205e-12
  c1  voutp  net4   1.14525e-11
  c10 voutn  net1   1.14525e-11
  c12 voutn  voutp  9.9455e-12
.ends lpf_core
