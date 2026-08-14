v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {lpf_core_H.sym} 600 0 0 0 {name=xdut}
N 480 -40 360 -40 {lab=vinp}
C {devices/lab_pin.sym} 360 -40 0 0 {name=t0 lab=vinp}
N 480 40 360 40 {lab=vinn}
C {devices/lab_pin.sym} 360 40 0 0 {name=t1 lab=vinn}
N 720 -40 840 -40 {lab=voutp}
C {devices/lab_pin.sym} 840 -40 0 1 {name=t2 lab=voutp}
N 720 40 840 40 {lab=voutn}
C {devices/lab_pin.sym} 840 40 0 1 {name=t3 lab=voutn}
N 600 -100 600 -200 {lab=vdd}
C {devices/lab_pin.sym} 600 -200 0 0 {name=t4 lab=vdd}
N 560 100 560 200 {lab=vbn}
C {devices/lab_pin.sym} 560 200 0 0 {name=t5 lab=vbn}
N 640 100 640 200 {lab=vbp}
C {devices/lab_pin.sym} 640 200 0 0 {name=t6 lab=vbp}
C {devices/code_shown.sym} -260 320 0 0 {name=BENCH only_toplevel=false value=".lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
.nodeset v(xdut.vout_1)=0.8181 v(xdut.vout_2)=0.8181 v(voutp)=1.3548 v(voutn)=1.3548
iref vdd_top vbn 6.624e-10
xmbn vbn vbn 0 0 sg13_hv_nmos w=2.925e-05 l=3.12e-05 ng=3 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=2.925e-05 l=3.12e-05 ng=3 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=1.56e-05 l=1.04e-05 ng=2 m=1
vcm vcm 0 0.65
vsig sig vcm dc 0 ac 1
evp vinp vcm sig vcm 0.5
evn vinn vcm sig vcm -0.5
.temp 27.0"}
C {devices/code_shown.sym} -260 800 0 0 {name=CTRL only_toplevel=false value=".control
set filetype=binary
set appendwrite
save all @n.xdut.xm2.nsg13_lv_pmos[ids] @n.xdut.xm2.nsg13_lv_pmos[gm] @n.xdut.xm2.nsg13_lv_pmos[gds] @n.xdut.xm2.nsg13_lv_pmos[gmb] @n.xdut.xm2.nsg13_lv_pmos[vgs] @n.xdut.xm2.nsg13_lv_pmos[vds] @n.xdut.xm2.nsg13_lv_pmos[vth] @n.xdut.xm2.nsg13_lv_pmos[vdss] @n.xdut.xm2.nsg13_lv_pmos[cgg] @n.xdut.xm5.nsg13_lv_pmos[ids] @n.xdut.xm5.nsg13_lv_pmos[gm] @n.xdut.xm5.nsg13_lv_pmos[gds] @n.xdut.xm5.nsg13_lv_pmos[gmb] @n.xdut.xm5.nsg13_lv_pmos[vgs] @n.xdut.xm5.nsg13_lv_pmos[vds] @n.xdut.xm5.nsg13_lv_pmos[vth] @n.xdut.xm5.nsg13_lv_pmos[vdss] @n.xdut.xm5.nsg13_lv_pmos[cgg] @n.xdut.xm4.nsg13_hv_nmos[ids] @n.xdut.xm4.nsg13_hv_nmos[gm] @n.xdut.xm4.nsg13_hv_nmos[gds] @n.xdut.xm4.nsg13_hv_nmos[gmb] @n.xdut.xm4.nsg13_hv_nmos[vgs] @n.xdut.xm4.nsg13_hv_nmos[vds] @n.xdut.xm4.nsg13_hv_nmos[vth] @n.xdut.xm4.nsg13_hv_nmos[vdss] @n.xdut.xm4.nsg13_hv_nmos[cgg] @n.xdut.xm8.nsg13_hv_nmos[ids] @n.xdut.xm8.nsg13_hv_nmos[gm] @n.xdut.xm8.nsg13_hv_nmos[gds] @n.xdut.xm8.nsg13_hv_nmos[gmb] @n.xdut.xm8.nsg13_hv_nmos[vgs] @n.xdut.xm8.nsg13_hv_nmos[vds] @n.xdut.xm8.nsg13_hv_nmos[vth] @n.xdut.xm8.nsg13_hv_nmos[vdss] @n.xdut.xm8.nsg13_hv_nmos[cgg] @n.xdut.xm9.nsg13_hv_nmos[ids] @n.xdut.xm9.nsg13_hv_nmos[gm] @n.xdut.xm9.nsg13_hv_nmos[gds] @n.xdut.xm9.nsg13_hv_nmos[gmb] @n.xdut.xm9.nsg13_hv_nmos[vgs] @n.xdut.xm9.nsg13_hv_nmos[vds] @n.xdut.xm9.nsg13_hv_nmos[vth] @n.xdut.xm9.nsg13_hv_nmos[vdss] @n.xdut.xm9.nsg13_hv_nmos[cgg] @n.xdut.xm10.nsg13_hv_nmos[ids] @n.xdut.xm10.nsg13_hv_nmos[gm] @n.xdut.xm10.nsg13_hv_nmos[gds] @n.xdut.xm10.nsg13_hv_nmos[gmb] @n.xdut.xm10.nsg13_hv_nmos[vgs] @n.xdut.xm10.nsg13_hv_nmos[vds] @n.xdut.xm10.nsg13_hv_nmos[vth] @n.xdut.xm10.nsg13_hv_nmos[vdss] @n.xdut.xm10.nsg13_hv_nmos[cgg] @n.xdut.xmst.nsg13_hv_pmos[ids] @n.xdut.xmst.nsg13_hv_pmos[gm] @n.xdut.xmst.nsg13_hv_pmos[gds] @n.xdut.xmst.nsg13_hv_pmos[gmb] @n.xdut.xmst.nsg13_hv_pmos[vgs] @n.xdut.xmst.nsg13_hv_pmos[vds] @n.xdut.xmst.nsg13_hv_pmos[vth] @n.xdut.xmst.nsg13_hv_pmos[vdss] @n.xdut.xmst.nsg13_hv_pmos[cgg] @n.xdut.xmstn.nsg13_hv_pmos[ids] @n.xdut.xmstn.nsg13_hv_pmos[gm] @n.xdut.xmstn.nsg13_hv_pmos[gds] @n.xdut.xmstn.nsg13_hv_pmos[gmb] @n.xdut.xmstn.nsg13_hv_pmos[vgs] @n.xdut.xmstn.nsg13_hv_pmos[vds] @n.xdut.xmstn.nsg13_hv_pmos[vth] @n.xdut.xmstn.nsg13_hv_pmos[vdss] @n.xdut.xmstn.nsg13_hv_pmos[cgg] @n.xdut.xm0.nsg13_hv_pmos[ids] @n.xdut.xm0.nsg13_hv_pmos[gm] @n.xdut.xm0.nsg13_hv_pmos[gds] @n.xdut.xm0.nsg13_hv_pmos[gmb] @n.xdut.xm0.nsg13_hv_pmos[vgs] @n.xdut.xm0.nsg13_hv_pmos[vds] @n.xdut.xm0.nsg13_hv_pmos[vth] @n.xdut.xm0.nsg13_hv_pmos[vdss] @n.xdut.xm0.nsg13_hv_pmos[cgg] @n.xdut.xm1.nsg13_hv_pmos[ids] @n.xdut.xm1.nsg13_hv_pmos[gm] @n.xdut.xm1.nsg13_hv_pmos[gds] @n.xdut.xm1.nsg13_hv_pmos[gmb] @n.xdut.xm1.nsg13_hv_pmos[vgs] @n.xdut.xm1.nsg13_hv_pmos[vds] @n.xdut.xm1.nsg13_hv_pmos[vth] @n.xdut.xm1.nsg13_hv_pmos[vdss] @n.xdut.xm1.nsg13_hv_pmos[cgg] @n.xdut.xm14.nsg13_lv_pmos[ids] @n.xdut.xm14.nsg13_lv_pmos[gm] @n.xdut.xm14.nsg13_lv_pmos[gds] @n.xdut.xm14.nsg13_lv_pmos[gmb] @n.xdut.xm14.nsg13_lv_pmos[vgs] @n.xdut.xm14.nsg13_lv_pmos[vds] @n.xdut.xm14.nsg13_lv_pmos[vth] @n.xdut.xm14.nsg13_lv_pmos[vdss] @n.xdut.xm14.nsg13_lv_pmos[cgg] @n.xdut.xm15.nsg13_lv_pmos[ids] @n.xdut.xm15.nsg13_lv_pmos[gm] @n.xdut.xm15.nsg13_lv_pmos[gds] @n.xdut.xm15.nsg13_lv_pmos[gmb] @n.xdut.xm15.nsg13_lv_pmos[vgs] @n.xdut.xm15.nsg13_lv_pmos[vds] @n.xdut.xm15.nsg13_lv_pmos[vth] @n.xdut.xm15.nsg13_lv_pmos[vdss] @n.xdut.xm15.nsg13_lv_pmos[cgg]
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
.endc"}
T {lpf_core_H sign-off testbench -- group delay, tau computed in-deck} -260 -360 0 0 0.5 0.5 {}
T {generated 2026-08-14 23:28 UTC by scripts/draw_xschem.py} -260 -270 0 0 0.18 0.18 {}
T {The bench text below is copied verbatim from signoff/asbuilt/ - balun evp/evn at +-0.5 so vsig IS the differential input, series vflt carrying the filter-core current only, bias reference ahead of that probe so S6 excludes it by construction.} -260 -320 0 0 0.25 0.25 {}
C {devices/title.sym} -260 1220 0 0 {name=l1 author="lpf_core_H testbench"}
