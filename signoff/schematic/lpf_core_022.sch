v {xschem version=3.4.4 file_version=1.2}
G {}
K {}
V {}
S {}
E {}

C {devices/iopin.sym} -200 0 0 0 {name=p0 lab=vinp}
C {devices/iopin.sym} -200 40 0 0 {name=p1 lab=vinn}
C {devices/iopin.sym} -200 80 0 0 {name=p2 lab=voutp}
C {devices/iopin.sym} -200 120 0 0 {name=p3 lab=voutn}
C {devices/iopin.sym} -200 160 0 0 {name=p4 lab=vbn}
C {devices/iopin.sym} -200 200 0 0 {name=p5 lab=vbp}
C {devices/iopin.sym} -200 240 0 0 {name=p6 lab=vdd}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 0 0 0 {name=m14 w=1.29324e-06 l=3.9e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 20 30 0 0 {name=l_m14_0 lab=voutp}
C {devices/lab_pin.sym} -20 0 0 0 {name=l_m14_1 lab=net4}
C {devices/lab_pin.sym} 20 -30 0 0 {name=l_m14_2 lab=vdd}
C {devices/lab_pin.sym} 20 0 0 0 {name=l_m14_3 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 120 0 0 {name=m0 w=1.56e-05 l=1.04e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 20 150 0 0 {name=l_m0_0 lab=net4}
C {devices/lab_pin.sym} -20 120 0 0 {name=l_m0_1 lab=vout_1}
C {devices/lab_pin.sym} 20 90 0 0 {name=l_m0_2 lab=voutp}
C {devices/lab_pin.sym} 20 120 0 0 {name=l_m0_3 lab=voutp}
C {sg13g2_pr/sg13_hv_pmos.sym} 0 240 0 0 {name=mst w=2.5896e-07 l=2.73e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 20 270 0 0 {name=l_mst_0 lab=vout_1}
C {devices/lab_pin.sym} -20 240 0 0 {name=l_mst_1 lab=vbn}
C {devices/lab_pin.sym} 20 210 0 0 {name=l_mst_2 lab=net4}
C {devices/lab_pin.sym} 20 240 0 0 {name=l_mst_3 lab=net4}
C {sg13g2_pr/sg13_lv_pmos.sym} 0 360 0 0 {name=m2 w=1.56e-05 l=1.04e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 20 390 0 0 {name=l_m2_0 lab=net2}
C {devices/lab_pin.sym} -20 360 0 0 {name=l_m2_1 lab=vinp}
C {devices/lab_pin.sym} 20 330 0 0 {name=l_m2_2 lab=vout_1}
C {devices/lab_pin.sym} 20 360 0 0 {name=l_m2_3 lab=vout_1}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 480 0 0 {name=m9 w=2.925e-05 l=3.12e-05 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 20 450 0 0 {name=l_m9_0 lab=net2}
C {devices/lab_pin.sym} -20 480 0 0 {name=l_m9_1 lab=vbn}
C {devices/lab_pin.sym} 20 510 0 0 {name=l_m9_2 lab=0}
C {devices/lab_pin.sym} 20 480 0 0 {name=l_m9_3 lab=0}
C {sg13g2_pr/sg13_hv_nmos.sym} 0 600 0 0 {name=m4 w=7.8e-06 l=5.2e-06 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 20 570 0 0 {name=l_m4_0 lab=vout_1}
C {devices/lab_pin.sym} -20 600 0 0 {name=l_m4_1 lab=net2}
C {devices/lab_pin.sym} 20 630 0 0 {name=l_m4_2 lab=0}
C {devices/lab_pin.sym} 20 600 0 0 {name=l_m4_3 lab=0}
C {sg13g2_pr/sg13_lv_pmos.sym} 780 0 0 0 {name=m15 w=1.29324e-06 l=3.9e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 800 30 0 0 {name=l_m15_0 lab=voutn}
C {devices/lab_pin.sym} 760 0 0 0 {name=l_m15_1 lab=net1}
C {devices/lab_pin.sym} 800 -30 0 0 {name=l_m15_2 lab=vdd}
C {devices/lab_pin.sym} 800 0 0 0 {name=l_m15_3 lab=vdd}
C {sg13g2_pr/sg13_hv_pmos.sym} 780 120 0 0 {name=m1 w=1.56e-05 l=1.04e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 800 150 0 0 {name=l_m1_0 lab=net1}
C {devices/lab_pin.sym} 760 120 0 0 {name=l_m1_1 lab=vout_2}
C {devices/lab_pin.sym} 800 90 0 0 {name=l_m1_2 lab=voutn}
C {devices/lab_pin.sym} 800 120 0 0 {name=l_m1_3 lab=voutn}
C {sg13g2_pr/sg13_hv_pmos.sym} 780 240 0 0 {name=mstn w=2.5896e-07 l=2.73e-05 ng=1 m=1 model=sg13_hv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 800 270 0 0 {name=l_mstn_0 lab=vout_2}
C {devices/lab_pin.sym} 760 240 0 0 {name=l_mstn_1 lab=vbn}
C {devices/lab_pin.sym} 800 210 0 0 {name=l_mstn_2 lab=net1}
C {devices/lab_pin.sym} 800 240 0 0 {name=l_mstn_3 lab=net1}
C {sg13g2_pr/sg13_lv_pmos.sym} 780 360 0 0 {name=m5 w=1.56e-05 l=1.04e-05 ng=1 m=1 model=sg13_lv_pmos spiceprefix=X}
C {devices/lab_pin.sym} 800 390 0 0 {name=l_m5_0 lab=net3}
C {devices/lab_pin.sym} 760 360 0 0 {name=l_m5_1 lab=vinn}
C {devices/lab_pin.sym} 800 330 0 0 {name=l_m5_2 lab=vout_2}
C {devices/lab_pin.sym} 800 360 0 0 {name=l_m5_3 lab=vout_2}
C {sg13g2_pr/sg13_hv_nmos.sym} 780 480 0 0 {name=m10 w=2.925e-05 l=3.12e-05 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 800 450 0 0 {name=l_m10_0 lab=net3}
C {devices/lab_pin.sym} 760 480 0 0 {name=l_m10_1 lab=vbn}
C {devices/lab_pin.sym} 800 510 0 0 {name=l_m10_2 lab=0}
C {devices/lab_pin.sym} 800 480 0 0 {name=l_m10_3 lab=0}
C {sg13g2_pr/sg13_hv_nmos.sym} 780 600 0 0 {name=m8 w=7.8e-06 l=5.2e-06 ng=1 m=1 model=sg13_hv_nmos spiceprefix=X}
C {devices/lab_pin.sym} 800 570 0 0 {name=l_m8_0 lab=vout_2}
C {devices/lab_pin.sym} 760 600 0 0 {name=l_m8_1 lab=net3}
C {devices/lab_pin.sym} 800 630 0 0 {name=l_m8_2 lab=0}
C {devices/lab_pin.sym} 800 600 0 0 {name=l_m8_3 lab=0}
C {devices/capa.sym} 260 0 0 0 {name=c13 m=1 value=8.46981e-12 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 -30 0 0 {name=l_c13_a lab=net2}
C {devices/lab_pin.sym} 260 30 0 0 {name=l_c13_b lab=vout_1}
C {devices/capa.sym} 260 120 0 0 {name=c17 m=1 value=8.46981e-12 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 90 0 0 {name=l_c17_a lab=net3}
C {devices/lab_pin.sym} 260 150 0 0 {name=l_c17_b lab=vout_2}
C {devices/capa.sym} 260 240 0 0 {name=c19 m=1 value=5.73811e-11 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 210 0 0 {name=l_c19_a lab=vout_2}
C {devices/lab_pin.sym} 260 270 0 0 {name=l_c19_b lab=vout_1}
C {devices/capa.sym} 260 360 0 0 {name=c1 m=1 value=1.31527e-10 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 330 0 0 {name=l_c1_a lab=voutp}
C {devices/lab_pin.sym} 260 390 0 0 {name=l_c1_b lab=net4}
C {devices/capa.sym} 260 480 0 0 {name=c10 m=1 value=1.31527e-10 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 450 0 0 {name=l_c10_a lab=voutn}
C {devices/lab_pin.sym} 260 510 0 0 {name=l_c10_b lab=net1}
C {devices/capa.sym} 260 600 0 0 {name=c12 m=1 value=2.88874e-11 footprint=1206 device="ceramic capacitor"}
C {devices/lab_pin.sym} 260 570 0 0 {name=l_c12_a lab=voutn}
C {devices/lab_pin.sym} 260 630 0 0 {name=l_c12_b lab=voutp}
C {devices/title.sym} -200 900 0 0 {name=l1 author="generated by scripts/gen_xschem.py -- topology b, lv_roles ['gmf_b', 'in_a']"}
