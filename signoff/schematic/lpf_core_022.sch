v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}

N -40 60 60 60 {lab=0}
N 60 60 220 60 {lab=0}
N 220 60 400 60 {lab=0}
N 400 60 560 60 {lab=0}
N 560 60 1660 60 {lab=0}
N 60 -80 60 60 {lab=0}
N 60 -110 60 -80 {lab=0}
N 220 -80 220 60 {lab=0}
N 220 -110 220 -80 {lab=0}
N 400 -80 400 60 {lab=0}
N 400 -110 400 -80 {lab=0}
N 560 -80 560 60 {lab=0}
N 560 -110 560 -80 {lab=0}
N 1640 -140 1570 -140 {lab=net1}
N 1570 -140 1480 -140 {lab=net1}
N 1480 -140 1410 -140 {lab=net1}
N 1480 -230 1480 -140 {lab=net1}
N 1480 -100 1480 -140 {lab=net1}
N 1480 -70 1480 -100 {lab=net1}
N 1410 -170 1410 -140 {lab=net1}
N 1520 -450 1640 -450 {lab=net1}
N 1640 -450 1640 -140 {lab=net1}
N 60 -180 120 -180 {lab=net2}
N 120 -180 150 -180 {lab=net2}
N 150 -180 180 -180 {lab=net2}
N 60 -290 60 -180 {lab=net2}
N 60 -140 60 -180 {lab=net2}
N 150 -200 150 -180 {lab=net2}
N 180 -180 180 -110 {lab=net2}
N 560 -180 500 -180 {lab=net3}
N 500 -180 470 -180 {lab=net3}
N 470 -180 440 -180 {lab=net3}
N 560 -290 560 -180 {lab=net3}
N 560 -140 560 -180 {lab=net3}
N 470 -200 470 -180 {lab=net3}
N 440 -180 440 -110 {lab=net3}
N 820 -140 890 -140 {lab=net4}
N 890 -140 980 -140 {lab=net4}
N 980 -140 1050 -140 {lab=net4}
N 980 -230 980 -140 {lab=net4}
N 980 -100 980 -140 {lab=net4}
N 980 -70 980 -100 {lab=net4}
N 1050 -170 1050 -140 {lab=net4}
N 940 -450 820 -450 {lab=net4}
N 820 -450 820 -140 {lab=net4}
N 20 -110 0 -110 {lab=vbn}
N 600 -110 620 -110 {lab=vbn}
N 940 -70 920 -70 {lab=vbn}
N 1520 -70 1540 -70 {lab=vbn}
N -40 -630 20 -630 {lab=vbn}
N -40 -670 20 -670 {lab=vbp}
N -40 -560 980 -560 {lab=vdd}
N 980 -560 1480 -560 {lab=vdd}
N 1480 -560 1660 -560 {lab=vdd}
N 980 -560 980 -480 {lab=vdd}
N 980 -480 980 -450 {lab=vdd}
N 1480 -560 1480 -480 {lab=vdd}
N 1480 -480 1480 -450 {lab=vdd}
N 600 -320 640 -320 {lab=vinn}
N 20 -320 -20 -320 {lab=vinp}
N 60 -380 100 -380 {lab=vout_1}
N 100 -380 150 -380 {lab=vout_1}
N 150 -380 220 -380 {lab=vout_1}
N 220 -380 280 -380 {lab=vout_1}
N 60 -350 60 -380 {lab=vout_1}
N 60 -350 60 -320 {lab=vout_1}
N 150 -260 150 -380 {lab=vout_1}
N 220 -140 220 -380 {lab=vout_1}
N 940 -260 920 -260 {lab=vout_1}
N 980 -40 980 10 {lab=vout_1}
N 560 -380 520 -380 {lab=vout_2}
N 520 -380 470 -380 {lab=vout_2}
N 470 -380 400 -380 {lab=vout_2}
N 400 -380 340 -380 {lab=vout_2}
N 560 -350 560 -380 {lab=vout_2}
N 560 -350 560 -320 {lab=vout_2}
N 470 -260 470 -380 {lab=vout_2}
N 400 -140 400 -380 {lab=vout_2}
N 1520 -260 1540 -260 {lab=vout_2}
N 1480 -40 1480 10 {lab=vout_2}
N 1480 -320 1410 -320 {lab=voutn}
N 1410 -320 1370 -320 {lab=voutn}
N 1370 -320 1260 -320 {lab=voutn}
N 1480 -420 1480 -320 {lab=voutn}
N 1480 -290 1480 -320 {lab=voutn}
N 1480 -260 1480 -290 {lab=voutn}
N 1410 -230 1410 -320 {lab=voutn}
N 1370 -360 1370 -320 {lab=voutn}
N 1370 -360 1330 -360 {lab=voutn}
N 980 -320 1050 -320 {lab=voutp}
N 1050 -320 1090 -320 {lab=voutp}
N 1090 -320 1200 -320 {lab=voutp}
N 980 -420 980 -320 {lab=voutp}
N 980 -290 980 -320 {lab=voutp}
N 980 -260 980 -290 {lab=voutp}
N 1050 -230 1050 -320 {lab=voutp}
N 1090 -360 1090 -320 {lab=voutp}
N 1090 -360 1130 -360 {lab=voutp}
C {sg13g2_pr/sg13_lv_pmos.sym} 40 -320 0 0 {name=m2 w=1.56e-05 l=1.04e-05 ng=2 m=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 40 -110 0 0 {name=m9 w=2.925e-05 l=3.12e-05 ng=3 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 200 -110 0 0 {name=m4 w=7.8e-06 l=5.2e-06 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 580 -320 0 1 {name=m5 w=1.56e-05 l=1.04e-05 ng=2 m=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 580 -110 0 1 {name=m10 w=2.925e-05 l=3.12e-05 ng=3 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_nmos.sym} 420 -110 0 1 {name=m8 w=7.8e-06 l=5.2e-06 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 960 -450 0 0 {name=m14 w=1.295e-06 l=3.9e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 960 -260 0 0 {name=m0 w=1.56e-05 l=1.04e-05 ng=2 m=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 960 -70 0 0 {name=mst w=3e-07 l=2.874e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_lv_pmos.sym} 1500 -450 0 1 {name=m15 w=1.295e-06 l=3.9e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1500 -260 0 1 {name=m1 w=1.56e-05 l=1.04e-05 ng=2 m=1 model=sg13_hv_pmos spiceprefix=X}
C {sg13g2_pr/sg13_hv_pmos.sym} 1500 -70 0 1 {name=mstn w=3e-07 l=2.874e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/capa.sym} 150 -230 2 0 {name=c13 m=1 value=8.46981e-12 footprint=1206 device="ceramic capacitor"}
C {devices/capa.sym} 470 -230 2 0 {name=c17 m=1 value=8.46981e-12 footprint=1206 device="ceramic capacitor"}
C {devices/capa.sym} 310 -380 1 0 {name=c19 m=1 value=5.73811e-11 footprint=1206 device="ceramic capacitor"}
C {devices/capa.sym} 1050 -200 0 0 {name=c1 m=1 value=1.31527e-10 footprint=1206 device="ceramic capacitor"}
C {devices/capa.sym} 1410 -200 0 0 {name=c10 m=1 value=1.31527e-10 footprint=1206 device="ceramic capacitor"}
C {devices/capa.sym} 1230 -320 1 0 {name=c12 m=1 value=2.88874e-11 footprint=1206 device="ceramic capacitor"}
C {devices/ipin.sym} -20 -320 0 0 {name=p_vinp lab=vinp}
C {devices/ipin.sym} 640 -320 0 1 {name=p_vinn lab=vinn}
C {devices/opin.sym} 1130 -360 0 0 {name=p_voutp lab=voutp}
C {devices/opin.sym} 1330 -360 0 1 {name=p_voutn lab=voutn}
C {devices/ipin.sym} -40 -560 0 0 {name=p_vdd lab=vdd}
C {devices/ipin.sym} -40 -670 0 0 {name=p_vbp lab=vbp}
C {devices/ipin.sym} -40 -630 0 0 {name=p_vbn lab=vbn}
C {devices/title.sym} 0 260 0 0 {name=l1 author="lpf_core_022 -- drawn from signoff/asbuilt"}
C {devices/lab_pin.sym} 100 -380 0 0 {name=l6_100_-380 lab=vout_1}
C {devices/lab_pin.sym} 120 -180 0 0 {name=l4_120_-180 lab=net2}
C {devices/lab_pin.sym} 520 -380 0 1 {name=l6_520_-380 lab=vout_2}
C {devices/lab_pin.sym} 500 -180 0 1 {name=l4_500_-180 lab=net3}
C {devices/lab_pin.sym} 0 -110 0 0 {name=l3_0_-110 lab=vbn}
C {devices/lab_pin.sym} 620 -110 0 1 {name=l3_620_-110 lab=vbn}
C {devices/lab_pin.sym} 890 -140 0 1 {name=l4_890_-140 lab=net4}
C {devices/lab_pin.sym} 920 -260 0 0 {name=l6_920_-260 lab=vout_1}
C {devices/lab_pin.sym} 980 10 0 0 {name=l6_980_10 lab=vout_1}
C {devices/lab_pin.sym} 920 -70 0 0 {name=l3_920_-70 lab=vbn}
C {devices/lab_pin.sym} 1570 -140 0 0 {name=l4_1570_-140 lab=net1}
C {devices/lab_pin.sym} 1540 -260 0 1 {name=l6_1540_-260 lab=vout_2}
C {devices/lab_pin.sym} 1480 10 0 1 {name=l6_1480_10 lab=vout_2}
C {devices/lab_pin.sym} 1540 -70 0 1 {name=l3_1540_-70 lab=vbn}
C {devices/lab_pin.sym} 1660 -560 0 1 {name=l3_1660_-560 lab=vdd}
C {devices/gnd.sym} -40 60 0 0 {name=l1_-40_60 lab=0}
C {devices/gnd.sym} 1660 60 0 0 {name=l1_1660_60 lab=0}
C {devices/lab_pin.sym} 20 -670 0 1 {name=l3_20_-670 lab=vbp}
C {devices/lab_pin.sym} 20 -630 0 1 {name=l3_20_-630 lab=vbn}
T {lpf_core_022 -- 4th-order 250 Hz super-source-follower low-pass, fully differential, IHP SG13G2, VDD 1.5 V} 0 -760 0 0 0.5 0.5 {}
T {Schematic of record. Placement and routing carried forward from the originating campaign's drawing; stage A is re-routed because this cell's input follower is p-type.} 0 -725 0 0 0.25 0.25 {}
T {The gm_f of stage B is MERGED into the branch-top device: m14/m15 gates are driven by net4/net1, so the follower loop closes through the branch top. vbp is a port only -- unused by the core.} 0 -700 0 0 0.25 0.25 {}
T {STAGE A -- biquad 1  (pmos input followers m2/m5, nmos gm_f m4/m8, nmos bias sink m9/m10)} 60 -600 0 0 0.3 0.3 {}
T {STAGE B -- biquad 2  (pmos input followers m0/m1, merged gm_f m14/m15)} 900 -600 0 0 0.3 0.3 {}
T {SSF loop: net4 -> gate of m14} 700 -530 0 0 0.25 0.25 {}
T {SSF loop: net1 -> gate of m15} 1560 -530 0 0 0.25 0.25 {}
T {bridge: net4 -> vout_1} 830 -20 0 0 0.25 0.25 {}
T {bridge: net1 -> vout_2} 1250 -20 0 0 0.25 0.25 {}
T {in_a} -30 -370 0 0 0.25 0.25 {}
T {in_a} 610 -370 0 0 0.25 0.25 {}
T {bias_a_int} -60 -160 0 0 0.25 0.25 {}
T {bias_a_int} 620 -160 0 0 0.25 0.25 {}
T {gm_f,a} 130 -30 0 0 0.25 0.25 {}
T {gm_f,a} 470 -30 0 0 0.25 0.25 {}
T {gm_f,b (merged)} 800 -480 0 0 0.25 0.25 {}
T {gm_f,b (merged)} 1540 -480 0 0 0.25 0.25 {}
T {in_b} 830 -300 0 0 0.25 0.25 {}
T {in_b} 1560 -300 0 0 0.25 0.25 {}
T {stage A per half: m2/m5 pmos input follower (bulk tied to source), m4/m8 shunt gm_f to gnd (gate on net2/net3), m9/m10 vbn bias sink, c13/c17 the Miller cap, c19 the differential load.} 0 130 0 0 0.25 0.25 {}
T {stage B per half: m14/m15 branch-top pmos acting as bias source AND gm_f loop device, m0/m1 pmos input follower, c1/c10 the Miller cap, c12 the differential load.} 0 160 0 0 0.25 0.25 {}
T {dc ladder per half, top to bottom: vdd - m14 - voutp - m0 - net4 - mst - vout_1 - m2 - net2 - m9 - gnd, with m4 shunting vout_1 to gnd. No CMFB: c12/c19 set the differential poles.} 0 190 0 0 0.25 0.25 {}
T {generated 2026-08-14 23:28 UTC by scripts/draw_lpf_core_022.py} 0 220 0 0 0.2 0.2 {}
T {Vds=400m Vdsat=101m
Id=0.66nA Vgs=167m
gm/ID=32.0 gm/gds=2619 [sat/weak]} 70 -276 0 0 0.12 0.12 {name=opannot_m2 layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 40 -680 0 0 {name=opannot_live_m2 ref=m2}
T {Vds=400m Vdsat=101m
Id=0.66nA Vgs=167m
gm/ID=32.0 gm/gds=2619 [sat/weak]} 610 -276 0 0 0.12 0.12 {name=opannot_m5 layer=11}
T {Vds=817m Vdsat=102m
Id=4.17nA Vgs=417m
gm/ID=28.1 gm/gds=1641 [sat/weak]} 230 -66 0 0 0.12 0.12 {name=opannot_m4 layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 290 -680 0 0 {name=opannot_live_m4 ref=m4}
T {Vds=817m Vdsat=102m
Id=4.17nA Vgs=417m
gm/ID=28.1 gm/gds=1641 [sat/weak]} 450 -66 0 0 0.12 0.12 {name=opannot_m8 layer=11}
T {Vds=417m Vdsat=101m
Id=0.66nA Vgs=356m
gm/ID=28.1 gm/gds=13435 [sat/weak]} 70 -66 0 0 0.12 0.12 {name=opannot_m9 layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 540 -680 0 0 {name=opannot_live_m9 ref=m9}
T {Vds=417m Vdsat=101m
Id=0.66nA Vgs=356m
gm/ID=28.1 gm/gds=13435 [sat/weak]} 610 -66 0 0 0.12 0.12 {name=opannot_m10 layer=11}
T {Vds=324m Vdsat=158m
Id=4.83nA Vgs=785m
gm/ID=9.9 gm/gds=2587 [sat/mod]} 990 -26 0 0 0.12 0.12 {name=opannot_mst layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 790 -680 0 0 {name=opannot_live_mst ref=mst}
T {Vds=324m Vdsat=158m
Id=4.83nA Vgs=785m
gm/ID=9.9 gm/gds=2587 [sat/mod]} 1530 -26 0 0 0.12 0.12 {name=opannot_mstn layer=11}
T {Vds=213m Vdsat=102m
Id=4.83nA Vgs=537m
gm/ID=24.7 gm/gds=2646 [sat/weak]} 990 -216 0 0 0.12 0.12 {name=opannot_m0 layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 1040 -680 0 0 {name=opannot_live_m0 ref=m0}
T {Vds=213m Vdsat=102m
Id=4.83nA Vgs=537m
gm/ID=24.7 gm/gds=2646 [sat/weak]} 1530 -216 0 0 0.12 0.12 {name=opannot_m1 layer=11}
T {Vds=146m Vdsat=116m
Id=4.83nA Vgs=359m
gm/ID=21.7 gm/gds=184 [sat/weak]} 990 -406 0 0 0.12 0.12 {name=opannot_m14 layer=11}
C {sg13g2_pr/annotate_fet_params.sym} 1290 -680 0 0 {name=opannot_live_m14 ref=m14}
T {Vds=146m Vdsat=116m
Id=4.83nA Vgs=359m
gm/ID=21.7 gm/gds=184 [sat/weak]} 1530 -406 0 0 0.12 0.12 {name=opannot_m15 layer=11}
T {OP ANNOTATION (generated 2026-08-14 23:28 UTC) -- corner mos_tt, 27 C, VDD 1.5 V, measured by lab.oppoint (PSP vdss = Vdsat). P half shown on both halves (differential symmetry). The empty L-brackets are the IHP PDK live annotator (annotate_fet_params): run the *_gd bench, load its sim.raw in xschem, descend into the DUT, and they fill with the same numbers plus ft.} 40 96 0 0 0.16 0.16 {name=opannot_banner layer=11}
