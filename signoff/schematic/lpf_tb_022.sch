v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {lpf_core_022.sym} 300 0 0 0 {name=xdut}
C {devices/lab_pin.sym} 240 -90 0 0 {name=t0 lab=vinp}
C {devices/lab_pin.sym} 240 -60 0 0 {name=t1 lab=vinn}
C {devices/lab_pin.sym} 240 -30 0 0 {name=t2 lab=voutp}
C {devices/lab_pin.sym} 240 0 0 0 {name=t3 lab=voutn}
C {devices/lab_pin.sym} 240 30 0 0 {name=t4 lab=vbn}
C {devices/lab_pin.sym} 240 60 0 0 {name=t5 lab=vbp}
C {devices/lab_pin.sym} 240 90 0 0 {name=t6 lab=vdd}
C {devices/code_shown.sym} 700 -200 0 0 {name=BENCH only_toplevel=false value=".lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
vdd_meas vdd_top 0 1.5
vflt vdd_top vdd 0
iref vdd_top vbn 6.624e-10
xmbn vbn vbn 0 0 sg13_hv_nmos w=2.925e-05 l=3.12e-05 ng=1 m=1
xmbp vbp vbn 0 0 sg13_hv_nmos w=2.925e-05 l=3.12e-05 ng=1 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=1.29324e-06 l=3.9e-05 ng=1 m=1
vcm vcm 0 0.65
vsig sig vcm dc 0 ac 1
evp vinp vcm sig vcm 0.5
evn vinn vcm sig vcm -0.5
.nodeset v(xdut.vout_1)=0.8181 v(xdut.vout_2)=0.8181 v(voutp)=1.3548 v(voutn)=1.3548
.temp 27.0"}
C {devices/code_shown.sym} 700 300 0 0 {name=CTRL only_toplevel=false value=".control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec 50 0.1 100000
write sim.raw
noise v(voutp,voutn) vsig dec 50 0.1 1000
setplot noise1
write sim.raw
.endc"}
C {devices/title.sym} 0 500 0 0 {name=l1 author="LPF sign-off testbench (acnoise) -- generated"}
