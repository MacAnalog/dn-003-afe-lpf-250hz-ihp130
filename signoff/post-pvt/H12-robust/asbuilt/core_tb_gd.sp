.title lpf d -- group delay (single run)
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
save all @n.xdut.xm2.nsg13_hv_pmos[ids] @n.xdut.xm2.nsg13_hv_pmos[gm] @n.xdut.xm2.nsg13_hv_pmos[gds] @n.xdut.xm2.nsg13_hv_pmos[gmb] @n.xdut.xm2.nsg13_hv_pmos[vgs] @n.xdut.xm2.nsg13_hv_pmos[vds] @n.xdut.xm2.nsg13_hv_pmos[vth] @n.xdut.xm2.nsg13_hv_pmos[vdss] @n.xdut.xm2.nsg13_hv_pmos[cgg] @n.xdut.xm5.nsg13_hv_pmos[ids] @n.xdut.xm5.nsg13_hv_pmos[gm] @n.xdut.xm5.nsg13_hv_pmos[gds] @n.xdut.xm5.nsg13_hv_pmos[gmb] @n.xdut.xm5.nsg13_hv_pmos[vgs] @n.xdut.xm5.nsg13_hv_pmos[vds] @n.xdut.xm5.nsg13_hv_pmos[vth] @n.xdut.xm5.nsg13_hv_pmos[vdss] @n.xdut.xm5.nsg13_hv_pmos[cgg] @n.xdut.xm4.nsg13_hv_nmos[ids] @n.xdut.xm4.nsg13_hv_nmos[gm] @n.xdut.xm4.nsg13_hv_nmos[gds] @n.xdut.xm4.nsg13_hv_nmos[gmb] @n.xdut.xm4.nsg13_hv_nmos[vgs] @n.xdut.xm4.nsg13_hv_nmos[vds] @n.xdut.xm4.nsg13_hv_nmos[vth] @n.xdut.xm4.nsg13_hv_nmos[vdss] @n.xdut.xm4.nsg13_hv_nmos[cgg] @n.xdut.xm8.nsg13_hv_nmos[ids] @n.xdut.xm8.nsg13_hv_nmos[gm] @n.xdut.xm8.nsg13_hv_nmos[gds] @n.xdut.xm8.nsg13_hv_nmos[gmb] @n.xdut.xm8.nsg13_hv_nmos[vgs] @n.xdut.xm8.nsg13_hv_nmos[vds] @n.xdut.xm8.nsg13_hv_nmos[vth] @n.xdut.xm8.nsg13_hv_nmos[vdss] @n.xdut.xm8.nsg13_hv_nmos[cgg] @n.xdut.xm9.nsg13_hv_nmos[ids] @n.xdut.xm9.nsg13_hv_nmos[gm] @n.xdut.xm9.nsg13_hv_nmos[gds] @n.xdut.xm9.nsg13_hv_nmos[gmb] @n.xdut.xm9.nsg13_hv_nmos[vgs] @n.xdut.xm9.nsg13_hv_nmos[vds] @n.xdut.xm9.nsg13_hv_nmos[vth] @n.xdut.xm9.nsg13_hv_nmos[vdss] @n.xdut.xm9.nsg13_hv_nmos[cgg] @n.xdut.xm10.nsg13_hv_nmos[ids] @n.xdut.xm10.nsg13_hv_nmos[gm] @n.xdut.xm10.nsg13_hv_nmos[gds] @n.xdut.xm10.nsg13_hv_nmos[gmb] @n.xdut.xm10.nsg13_hv_nmos[vgs] @n.xdut.xm10.nsg13_hv_nmos[vds] @n.xdut.xm10.nsg13_hv_nmos[vth] @n.xdut.xm10.nsg13_hv_nmos[vdss] @n.xdut.xm10.nsg13_hv_nmos[cgg] @n.xdut.xmst.nsg13_hv_pmos[ids] @n.xdut.xmst.nsg13_hv_pmos[gm] @n.xdut.xmst.nsg13_hv_pmos[gds] @n.xdut.xmst.nsg13_hv_pmos[gmb] @n.xdut.xmst.nsg13_hv_pmos[vgs] @n.xdut.xmst.nsg13_hv_pmos[vds] @n.xdut.xmst.nsg13_hv_pmos[vth] @n.xdut.xmst.nsg13_hv_pmos[vdss] @n.xdut.xmst.nsg13_hv_pmos[cgg] @n.xdut.xmstn.nsg13_hv_pmos[ids] @n.xdut.xmstn.nsg13_hv_pmos[gm] @n.xdut.xmstn.nsg13_hv_pmos[gds] @n.xdut.xmstn.nsg13_hv_pmos[gmb] @n.xdut.xmstn.nsg13_hv_pmos[vgs] @n.xdut.xmstn.nsg13_hv_pmos[vds] @n.xdut.xmstn.nsg13_hv_pmos[vth] @n.xdut.xmstn.nsg13_hv_pmos[vdss] @n.xdut.xmstn.nsg13_hv_pmos[cgg] @n.xdut.xm0.nsg13_hv_pmos[ids] @n.xdut.xm0.nsg13_hv_pmos[gm] @n.xdut.xm0.nsg13_hv_pmos[gds] @n.xdut.xm0.nsg13_hv_pmos[gmb] @n.xdut.xm0.nsg13_hv_pmos[vgs] @n.xdut.xm0.nsg13_hv_pmos[vds] @n.xdut.xm0.nsg13_hv_pmos[vth] @n.xdut.xm0.nsg13_hv_pmos[vdss] @n.xdut.xm0.nsg13_hv_pmos[cgg] @n.xdut.xm1.nsg13_hv_pmos[ids] @n.xdut.xm1.nsg13_hv_pmos[gm] @n.xdut.xm1.nsg13_hv_pmos[gds] @n.xdut.xm1.nsg13_hv_pmos[gmb] @n.xdut.xm1.nsg13_hv_pmos[vgs] @n.xdut.xm1.nsg13_hv_pmos[vds] @n.xdut.xm1.nsg13_hv_pmos[vth] @n.xdut.xm1.nsg13_hv_pmos[vdss] @n.xdut.xm1.nsg13_hv_pmos[cgg] @n.xdut.xm14.nsg13_hv_pmos[ids] @n.xdut.xm14.nsg13_hv_pmos[gm] @n.xdut.xm14.nsg13_hv_pmos[gds] @n.xdut.xm14.nsg13_hv_pmos[gmb] @n.xdut.xm14.nsg13_hv_pmos[vgs] @n.xdut.xm14.nsg13_hv_pmos[vds] @n.xdut.xm14.nsg13_hv_pmos[vth] @n.xdut.xm14.nsg13_hv_pmos[vdss] @n.xdut.xm14.nsg13_hv_pmos[cgg] @n.xdut.xm15.nsg13_hv_pmos[ids] @n.xdut.xm15.nsg13_hv_pmos[gm] @n.xdut.xm15.nsg13_hv_pmos[gds] @n.xdut.xm15.nsg13_hv_pmos[gmb] @n.xdut.xm15.nsg13_hv_pmos[vgs] @n.xdut.xm15.nsg13_hv_pmos[vds] @n.xdut.xm15.nsg13_hv_pmos[vth] @n.xdut.xm15.nsg13_hv_pmos[vdss] @n.xdut.xm15.nsg13_hv_pmos[cgg] @n.xdut.xr1.nsg13_hv_pmos[ids] @n.xdut.xr1.nsg13_hv_pmos[gm] @n.xdut.xr1.nsg13_hv_pmos[gds] @n.xdut.xr1.nsg13_hv_pmos[gmb] @n.xdut.xr1.nsg13_hv_pmos[vgs] @n.xdut.xr1.nsg13_hv_pmos[vds] @n.xdut.xr1.nsg13_hv_pmos[vth] @n.xdut.xr1.nsg13_hv_pmos[vdss] @n.xdut.xr1.nsg13_hv_pmos[cgg] @n.xdut.xr1.nsg13_hv_pmos[ids] @n.xdut.xr1.nsg13_hv_pmos[gm] @n.xdut.xr1.nsg13_hv_pmos[gds] @n.xdut.xr1.nsg13_hv_pmos[gmb] @n.xdut.xr1.nsg13_hv_pmos[vgs] @n.xdut.xr1.nsg13_hv_pmos[vds] @n.xdut.xr1.nsg13_hv_pmos[vth] @n.xdut.xr1.nsg13_hv_pmos[vdss] @n.xdut.xr1.nsg13_hv_pmos[cgg] @n.xdut.xr2.nsg13_hv_pmos[ids] @n.xdut.xr2.nsg13_hv_pmos[gm] @n.xdut.xr2.nsg13_hv_pmos[gds] @n.xdut.xr2.nsg13_hv_pmos[gmb] @n.xdut.xr2.nsg13_hv_pmos[vgs] @n.xdut.xr2.nsg13_hv_pmos[vds] @n.xdut.xr2.nsg13_hv_pmos[vth] @n.xdut.xr2.nsg13_hv_pmos[vdss] @n.xdut.xr2.nsg13_hv_pmos[cgg] @n.xdut.xr2.nsg13_hv_pmos[ids] @n.xdut.xr2.nsg13_hv_pmos[gm] @n.xdut.xr2.nsg13_hv_pmos[gds] @n.xdut.xr2.nsg13_hv_pmos[gmb] @n.xdut.xr2.nsg13_hv_pmos[vgs] @n.xdut.xr2.nsg13_hv_pmos[vds] @n.xdut.xr2.nsg13_hv_pmos[vth] @n.xdut.xr2.nsg13_hv_pmos[vdss] @n.xdut.xr2.nsg13_hv_pmos[cgg] @n.xdut.xr3.nsg13_hv_nmos[ids] @n.xdut.xr3.nsg13_hv_nmos[gm] @n.xdut.xr3.nsg13_hv_nmos[gds] @n.xdut.xr3.nsg13_hv_nmos[gmb] @n.xdut.xr3.nsg13_hv_nmos[vgs] @n.xdut.xr3.nsg13_hv_nmos[vds] @n.xdut.xr3.nsg13_hv_nmos[vth] @n.xdut.xr3.nsg13_hv_nmos[vdss] @n.xdut.xr3.nsg13_hv_nmos[cgg] @n.xdut.xr3.nsg13_hv_nmos[ids] @n.xdut.xr3.nsg13_hv_nmos[gm] @n.xdut.xr3.nsg13_hv_nmos[gds] @n.xdut.xr3.nsg13_hv_nmos[gmb] @n.xdut.xr3.nsg13_hv_nmos[vgs] @n.xdut.xr3.nsg13_hv_nmos[vds] @n.xdut.xr3.nsg13_hv_nmos[vth] @n.xdut.xr3.nsg13_hv_nmos[vdss] @n.xdut.xr3.nsg13_hv_nmos[cgg]
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
