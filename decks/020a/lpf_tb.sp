.title lpf a -- ac + noise
.lib cornerMOShv.lib mos_tt
.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xmst vout_1 vbn net4 net4 sg13_hv_pmos w=1.2e-05 l=8.4e-06 ng=1 m=1
  xmstn vout_2 vbn net1 net1 sg13_hv_pmos w=1.2e-05 l=8.4e-06 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4e-06 l=4e-06 ng=1 m=1
  xm6 voutp net4 vdd vdd sg13_hv_pmos w=3e-05 l=1.2e-05 ng=1 m=1
  xm7 voutn net1 vdd vdd sg13_hv_pmos w=3e-05 l=1.2e-05 ng=1 m=1
  xm14 voutp vbp vdd vdd sg13_hv_pmos w=1.5e-05 l=1.2e-05 ng=1 m=1
  xm15 voutn vbp vdd vdd sg13_hv_pmos w=1.5e-05 l=1.2e-05 ng=1 m=1
  c13 net2   vout_1 7.38523e-12
  c17 net3   vout_2 7.38523e-12
  c19 vout_2 vout_1 1.65714e-10
  c1  voutp  net4   2.34051e-10
  c10 voutn  net1   2.34051e-10
  c12 voutn  voutp  9.92051e-11
.ends lpf_core

vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=1.1 v(xdut.vout_2)=1.1 v(voutp)=1.1 v(voutn)=1.1
iref vdd_top vbn 1e-09
xmbn vbn vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=1.5e-05 l=1.2e-05 ng=1 m=1
vcm vcm 0 0.2
vsig sig vcm dc 0 ac 1
evp vinp vcm sig vcm 0.5
evn vinn vcm sig vcm -0.5
.temp 27.0
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec 10 0.1 100000
write sim.raw
noise v(voutp,voutn) vsig dec 10 0.1 1000
setplot noise1
write sim.raw
.endc
.end
