.title lpf b -- group delay (single run)
.lib cornerMOShv.lib mos_tt
.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=4e-06 l=4e-06 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
  xmst vout_1 vbn net4 net4 sg13_hv_pmos w=8.3e-07 l=8.4e-06 ng=1 m=1
  xmstn vout_2 vbn net1 net1 sg13_hv_pmos w=8.3e-07 l=8.4e-06 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_hv_pmos w=4.145e-06 l=1.2e-05 ng=1 m=1
  xm15 voutn net1 vdd vdd sg13_hv_pmos w=4.145e-06 l=1.2e-05 ng=1 m=1
  c13 net2   vout_1 3.42107e-12
  c17 net3   vout_2 3.42107e-12
  c19 vout_2 vout_1 1.71624e-11
  c1  voutp  net4   3.34819e-11
  c10 voutn  net1   3.34819e-11
  c12 voutn  voutp  1.34455e-11
.ends lpf_core

vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=1.1 v(xdut.vout_2)=1.1 v(voutp)=1.1 v(voutn)=1.1
iref vdd_top vbn 4.416e-10
xmbn vbn vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=5e-06 l=8e-06 ng=1 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
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
ac dec 50 0.1 1000
let hdiff = v(voutp) - v(voutn)
let hdb = db(mag(hdiff))
let dc_db = hdb[0]
let ph = cph(hdiff)
let gd = -deriv(ph) / (2 * pi)
let gd_dc_ms = gd[0] * 1e3
let gd_max_ms = vecmax(gd) * 1e3
let hrel = hdb - dc_db
meas ac fc_hz when hrel = -3 fall = 1
print dc_db gd_dc_ms gd_max_ms
write sim.raw hdiff ph gd frequency
.endc
.end
