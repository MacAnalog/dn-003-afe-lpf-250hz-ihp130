.title lpf b -- mismatch MC sample (edit .option seed= per draw)
.lib cornerMOShv.lib mos_tt_mismatch
.lib cornerMOSlv.lib mos_tt_mismatch
.option seed=1
.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=1e-06 l=4.5e-05 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=1e-06 l=4.5e-05 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
  xmst vout_1 vbn net4 net4 sg13_hv_pmos w=7.5e-07 l=3.36e-05 ng=1 m=1
  xmstn vout_2 vbn net1 net1 sg13_hv_pmos w=7.5e-07 l=3.36e-05 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_lv_pmos w=2e-06 l=9.6e-05 ng=1 m=1
  xm15 voutn net1 vdd vdd sg13_lv_pmos w=2e-06 l=9.6e-05 ng=1 m=1
  c13 net2   vout_1 8.5027e-12
  c17 net3   vout_2 8.5027e-12
  c19 vout_2 vout_1 3.5035e-11
  c1  voutp  net4   1.13625e-10
  c10 voutn  net1   1.13625e-10
  c12 voutn  voutp  2.5732e-11
.ends lpf_core

vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=0.8095 v(xdut.vout_2)=0.8095 v(voutp)=1.3564 v(voutn)=1.3564
iref vdd_top vbn 1e-09
xmbn vbn vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=1e-05 l=1.6e-05 ng=1 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=8e-06 l=8e-06 ng=1 m=1
vcm vcm 0 0.32
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
