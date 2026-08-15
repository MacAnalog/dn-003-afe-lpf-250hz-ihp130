.title lpf d -- ac + noise
.lib cornerMOShv.lib mos_tt
.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=1.56e-05 l=1.04e-05 ng=2 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=1.56e-05 l=1.04e-05 ng=2 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=2.3885e-05 l=2.5475e-05 ng=17 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=2.3885e-05 l=2.5475e-05 ng=17 m=1
  xmst vout_1 vbr net4 net4 sg13_hv_pmos w=4.86e-06 l=3.276e-05 ng=1 m=1
  xmstn vout_2 vbr net1 net1 sg13_hv_pmos w=4.86e-06 l=3.276e-05 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_hv_pmos w=1.202e-05 l=3.1115e-05 ng=2 m=1
  xm15 voutn net1 vdd vdd sg13_hv_pmos w=1.202e-05 l=3.1115e-05 ng=2 m=1
  xr1 rep_x rep_x vdd vdd sg13_hv_pmos w=1.202e-05 l=3.1115e-05 ng=2 m=1
  xr2 vbr vbr rep_x rep_x sg13_hv_pmos w=4.86e-06 l=3.276e-05 ng=1 m=1
  xr3 vbr vbn 0 0 sg13_hv_nmos w=2.3885e-05 l=2.5475e-05 ng=17 m=4
  c13 net2   vout_1 5.00659e-12
  c17 net3   vout_2 5.00659e-12
  c19 vout_2 vout_1 2.89483e-11
  c1  voutp  net4   6.0258e-11
  c10 voutn  net1   6.0258e-11
  c12 voutn  voutp  2.39864e-11
.ends lpf_core

vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=0.6975 v(xdut.vout_2)=0.6975 v(voutp)=1.2811 v(voutn)=1.2811
iref vdd_top vbn 6.624e-10
xmbn vbn vbn 0 0 sg13_hv_nmos w=2.3885e-05 l=2.5475e-05 ng=17 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=2.3885e-05 l=2.5475e-05 ng=17 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=1.56e-05 l=1.04e-05 ng=2 m=1
vcm vcm 0 0.24
vsig sig vcm dc 0 ac 1
evp vinp vcm sig vcm 0.5
evn vinn vcm sig vcm -0.5
.temp 27.0
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec 50 0.1 100000
write sim.raw
noise v(voutp,voutn) vsig dec 50 0.1 1000
setplot noise1
write sim.raw
.endc
.end
