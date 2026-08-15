.title lpf d -- thd fin=50 ampl=0.0875
.lib cornerMOShv.lib mos_tt
.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=1.6e-05 l=1e-05 ng=2 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=1.6e-05 l=1e-05 ng=2 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=2e-05 l=2.1e-05 ng=2 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=2e-05 l=2.1e-05 ng=2 m=1
  xmst vout_1 vbr net4 net4 sg13_hv_pmos w=3e-06 l=2.2e-05 ng=1 m=1
  xmstn vout_2 vbr net1 net1 sg13_hv_pmos w=3e-06 l=2.2e-05 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_hv_pmos w=8.5e-06 l=2.2e-05 ng=1 m=1
  xm15 voutn net1 vdd vdd sg13_hv_pmos w=8.5e-06 l=2.2e-05 ng=1 m=1
  xr1 rep_x rep_x vdd vdd sg13_hv_pmos w=8.5e-06 l=2.2e-05 ng=1 m=1
  xr2 vbr vbr rep_x rep_x sg13_hv_pmos w=3e-06 l=2.2e-05 ng=1 m=1
  xr3 vbr vbn 0 0 sg13_hv_nmos w=2e-05 l=2.1e-05 ng=2 m=3
  c13 net2   vout_1 4.81e-12
  c17 net3   vout_2 4.81e-12
  c19 vout_2 vout_1 2.135e-11
  c1  voutp  net4   4.615e-11
  c10 voutn  net1   4.615e-11
  c12 voutn  voutp  1.874e-11
.ends lpf_core

vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=0.6748 v(xdut.vout_2)=0.6748 v(voutp)=1.2463 v(voutn)=1.2463
iref vdd_top vbn 6.624e-10
xmbn vbn vbn 0 0 sg13_hv_nmos w=2e-05 l=2.1e-05 ng=2 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=2e-05 l=2.1e-05 ng=2 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=1.6e-05 l=1e-05 ng=2 m=1
vcm vcm 0 0.22
vsig sig vcm dc 0 sin(0 0.0875 50) ac 1
evp vinp vcm sig vcm 0.5
evn vinn vcm sig vcm -0.5
.temp 27.0
.options reltol=1e-5 abstol=1e-13 vntol=1e-9 chgtol=1e-16 method=gear maxord=2
.control
set filetype=binary
op
tran 3.90625e-05 0.56 0.16 3.90625e-05
write sim.raw
.endc
.end
