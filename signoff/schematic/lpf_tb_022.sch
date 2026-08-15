v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}

N 300 530 300 580 {lab=0}
N 1570 380 1570 410 {lab=0}
N 1570 410 1570 470 {lab=0}
N 1920 380 1920 410 {lab=0}
N 1920 410 1920 470 {lab=0}
N 1570 470 1750 470 {lab=0}
N 1750 470 1920 470 {lab=0}
N 2050 170 2050 230 {lab=0}
N 300 270 300 180 {lab=sig}
N 300 180 380 180 {lab=sig}
N 380 180 460 180 {lab=sig}
N 460 180 560 180 {lab=sig}
N 560 180 560 220 {lab=sig}
N 460 180 460 540 {lab=sig}
N 460 540 560 540 {lab=sig}
N 1600 170 1600 300 {lab=vbn}
N 1400 300 1500 300 {lab=vbn}
N 1500 300 1570 300 {lab=vbn}
N 1570 300 1600 300 {lab=vbn}
N 1600 300 1750 300 {lab=vbn}
N 1570 300 1570 350 {lab=vbn}
N 1500 300 1500 380 {lab=vbn}
N 1500 380 1530 380 {lab=vbn}
N 1750 300 1750 380 {lab=vbn}
N 1750 380 1880 380 {lab=vbn}
N 1240 520 1240 620 {lab=vbn}
N 1240 620 1320 620 {lab=vbn}
N 1320 620 1320 560 {lab=vbn}
N 1320 560 1320 300 {lab=vbn}
N 1320 300 1400 300 {lab=vbn}
N 1850 250 1920 250 {lab=vbp}
N 1920 210 1920 250 {lab=vbp}
N 1920 250 1920 350 {lab=vbp}
N 1880 180 1850 180 {lab=vbp}
N 1850 180 1850 250 {lab=vbp}
N 1160 520 1160 700 {lab=vbp}
N 1160 700 1600 700 {lab=vbp}
N 1600 700 2120 700 {lab=vbp}
N 2120 700 2120 250 {lab=vbp}
N 2120 250 1920 250 {lab=vbp}
N 300 330 300 400 {lab=vcm}
N 300 400 300 470 {lab=vcm}
N 300 400 400 400 {lab=vcm}
N 400 400 500 400 {lab=vcm}
N 500 260 500 290 {lab=vcm}
N 500 290 500 400 {lab=vcm}
N 500 400 500 580 {lab=vcm}
N 500 580 500 610 {lab=vcm}
N 500 260 560 260 {lab=vcm}
N 500 290 600 290 {lab=vcm}
N 600 290 600 270 {lab=vcm}
N 500 580 560 580 {lab=vcm}
N 500 610 600 610 {lab=vcm}
N 600 610 600 590 {lab=vcm}
N 1450 170 1450 220 {lab=vdd}
N 1450 220 1320 220 {lab=vdd}
N 1320 220 1200 220 {lab=vdd}
N 1200 220 1200 280 {lab=vdd}
N 1450 60 1600 60 {lab=vdd_top}
N 1600 60 1750 60 {lab=vdd_top}
N 1750 60 1920 60 {lab=vdd_top}
N 1920 60 2050 60 {lab=vdd_top}
N 1450 60 1450 110 {lab=vdd_top}
N 1600 60 1600 110 {lab=vdd_top}
N 1920 60 1920 150 {lab=vdd_top}
N 1920 150 1920 180 {lab=vdd_top}
N 2050 60 2050 110 {lab=vdd_top}
N 600 530 860 530 {lab=vinn}
N 860 530 1000 530 {lab=vinn}
N 1000 530 1000 440 {lab=vinn}
N 1000 440 1060 440 {lab=vinn}
N 600 210 900 210 {lab=vinp}
N 900 210 1060 210 {lab=vinp}
N 1060 210 1060 360 {lab=vinp}
N 1340 440 1420 440 {lab=voutn}
N 1340 360 1420 360 {lab=voutp}
C {devices/vsource.sym} 300 300 0 0 {name=vsig value="dc 0 ac 1" savecurrent=false}
C {devices/vsource.sym} 300 500 0 0 {name=vcm value=0.65 savecurrent=false}
C {devices/vcvs.sym} 600 240 0 0 {name=evp value=0.5}
C {devices/vcvs.sym} 600 560 0 0 {name=evn value=-0.5}
C {lpf_core_022.sym} 1200 400 0 0 {name=xdut}
C {devices/vsource.sym} 1450 140 0 0 {name=vflt value=0 savecurrent=false}
C {devices/vsource.sym} 2050 140 0 0 {name=vdd_meas value=1.5 savecurrent=false}
C {devices/isource.sym} 1600 140 0 0 {name=iref value=6.624e-10}
C {sg13g2_pr/sg13_hv_nmos.sym} 1550 380 0 0 {name=mbn w=2.925e-05 l=3.12e-05 ng=3 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 1900 380 0 0 {name=mbp w=2.925e-05 l=3.12e-05 ng=3 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1900 180 0 0 {name=mbpd w=1.56e-05 l=1.04e-05 ng=2 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/code_shown.sym} 200 820 0 0 {name=BENCH only_toplevel=false value=".title lpf b -- ac + noise
.lib cornerMOShv.lib mos_tt
.lib cornerMOSlv.lib mos_tt
.nodeset v(xdut.vout_1)=0.8181 v(xdut.vout_2)=0.8181 v(voutp)=1.3548 v(voutn)=1.3548
.temp 27.0"}
C {devices/code_shown.sym} 200 1000 0 0 {name=CTRL only_toplevel=false value=".control
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
C {devices/title.sym} 200 1490 0 0 {name=l1 author="lpf_core_022 testbench -- acnoise"}
C {devices/gnd.sym} 300 580 0 0 {name=l1_300_580 lab=0}
C {devices/gnd.sym} 1750 470 0 0 {name=l1_1750_470 lab=0}
C {devices/gnd.sym} 2050 230 0 0 {name=l1_2050_230 lab=0}
C {devices/lab_pin.sym} 380 180 0 0 {name=l3_380_180 lab=sig}
C {devices/lab_pin.sym} 400 400 0 0 {name=l3_400_400 lab=vcm}
C {devices/lab_pin.sym} 1750 60 0 0 {name=l7_1750_60 lab=vdd_top}
C {devices/lab_pin.sym} 1320 220 0 0 {name=l3_1320_220 lab=vdd}
C {devices/lab_pin.sym} 900 210 0 0 {name=l4_900_210 lab=vinp}
C {devices/lab_pin.sym} 860 530 0 0 {name=l4_860_530 lab=vinn}
C {devices/lab_pin.sym} 1600 700 0 0 {name=l3_1600_700 lab=vbp}
C {devices/lab_pin.sym} 1320 560 0 1 {name=l3_1320_560 lab=vbn}
C {devices/lab_pin.sym} 1420 360 0 1 {name=l5_1420_360 lab=voutp}
C {devices/lab_pin.sym} 1420 440 0 1 {name=l5_1420_440 lab=voutn}
T {lpf_core_022 sign-off testbench -- op + ac + noise} 200 40 0 0 0.5 0.5 {}
T {balun gains +-0.5 so the vsig amplitude IS the differential input.} 200 75 0 0 0.3 0.3 {}
T {vflt is a 0 V series probe carrying the CORE current only. The bias reference sits AHEAD of it, so S6 excludes the reference by construction rather than by subtraction.} 200 760 0 0 0.3 0.3 {}
T {generated 2026-08-15 02:48 UTC by scripts/draw_lpf_core_022.py} 200 1450 0 0 0.2 0.2 {}
