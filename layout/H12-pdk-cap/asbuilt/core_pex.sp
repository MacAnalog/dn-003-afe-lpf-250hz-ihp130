*********************************************************
*** NGSPICE file created by KLayout-PEX 0.3.12
*** -----------------------------------------------------
***     Extraction Engine: KPEX/2.5D
***     Technology: ihp_sg13g2
***     Date: 2026-08-15 22:54:44
*********************************************************

.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
XM$1 net2 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$2 0 vbn net2 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$3 net2 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$4 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$5 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U PD=8.38U
+ rfmode=0
XM$6 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$7 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$8 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U PD=8.38U
+ rfmode=0
XM$9 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$10 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$11 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$12 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$13 0 net3 vout_2 0 sg13_hv_nmos L=45U W=1.5U AS=0.51P AD=0.51P PS=3.68U
+ PD=3.68U rfmode=0
XM$14 0 vbn net3 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$15 net3 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$16 0 vbn net3 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$17 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$18 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$19 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$20 vout_1 net2 0 0 sg13_hv_nmos L=45U W=1.5U AS=0.51P AD=0.51P PS=3.68U
+ PD=3.68U rfmode=0
XM$21 voutn net1 vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=1.14P PS=12.68U
+ PD=6.38U rfmode=0
XM$22 vdd net1 voutn vdd sg13_hv_pmos L=31U W=6U AS=1.14P AD=2.04P PS=6.38U
+ PD=12.68U rfmode=0
XM$23 rep_x rep_x vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=1.14P PS=12.68U
+ PD=6.38U rfmode=0
XM$24 vdd rep_x rep_x vdd sg13_hv_pmos L=31U W=6U AS=1.14P AD=2.04P PS=6.38U
+ PD=12.68U rfmode=0
XM$25 net3 vinn vout_2 vout_2 sg13_hv_pmos L=10U W=8U AS=2.72P AD=1.52P
+ PS=16.68U PD=8.38U rfmode=0
XM$26 vout_2 vinn net3 vout_2 sg13_hv_pmos L=10U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$27 net2 vinp vout_1 vout_1 sg13_hv_pmos L=10U W=8U AS=2.72P AD=1.52P
+ PS=16.68U PD=8.38U rfmode=0
XM$28 vout_1 vinp net2 vout_1 sg13_hv_pmos L=10U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$29 net1 vbr vout_2 net1 sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$30 voutp net4 vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=1.14P PS=12.68U
+ PD=6.38U rfmode=0
XM$31 vdd net4 voutp vdd sg13_hv_pmos L=31U W=6U AS=1.14P AD=2.04P PS=6.38U
+ PD=12.68U rfmode=0
XM$32 vout_1 vbr net4 net4 sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$33 vbr vbr rep_x rep_x sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$34 net4 vout_1 voutp voutp sg13_hv_pmos L=15U W=4U AS=1.36P AD=1.36P PS=8.68U
+ PD=8.68U rfmode=0
XM$35 voutn vout_2 net1 voutn sg13_hv_pmos L=15U W=4U AS=1.36P AD=1.36P PS=8.68U
+ PD=8.68U rfmode=0
Cext_1 net1 net4 25.6634a
Cext_2 net1 rep_x 2.23371f
Cext_3 net1 vbr 2.32177f
Cext_4 net1 vdd 4.27987f
Cext_5 net1 vout_1 0.427493a
Cext_6 net1 vout_2 818.128a
Cext_7 net1 voutn 6.40131f
Cext_8 net1 voutp 0.196199a
Cext_9 net1 0 0.807588a
Cext_10 net2 net3 61.1355a
Cext_11 net2 vbn 5.93413f
Cext_12 net2 vbr 133.583a
Cext_13 net2 vinp 1.63763f
Cext_14 net2 vout_1 3.43368f
Cext_15 net2 vout_2 5.43289a
Cext_16 net2 0 5.81559f
Cext_17 net3 vbn 5.70751f
Cext_18 net3 vbr 133.583a
Cext_19 net3 vinn 1.63763f
Cext_20 net3 vout_1 5.43289a
Cext_21 net3 vout_2 11.3189f
Cext_22 net3 0 4.73276f
Cext_23 net4 rep_x 2.35938f
Cext_24 net4 vbr 2.30308f
Cext_25 net4 vdd 5.38023f
Cext_26 net4 vout_1 818.128a
Cext_27 net4 vout_2 0.427493a
Cext_28 net4 voutn 0.196199a
Cext_29 net4 voutp 5.43146f
Cext_30 net4 0 0.807588a
Cext_31 rep_x vbr 1.4921f
Cext_32 rep_x vdd 3.93763f
Cext_33 rep_x vout_1 965.872a
Cext_34 rep_x vout_2 904.973a
Cext_35 rep_x voutn 2.23639f
Cext_36 rep_x voutp 2.23639f
Cext_37 vbn vbr 13.2036f
Cext_38 vbn vout_1 142.273a
Cext_39 vbn vout_2 142.273a
Cext_40 vbn 0 84.3877f
Cext_41 vbr vinn 1.28709a
Cext_42 vbr vinp 1.28709a
Cext_43 vbr vout_1 7.57963f
Cext_44 vbr vout_2 7.62999f
Cext_45 vbr 0 2.49798f
Cext_46 vdd voutn 2.40094f
Cext_47 vdd voutp 7.09564f
Cext_48 vdd 0 6.36508f
Cext_49 vinn vinp 12.4093a
Cext_50 vinn vout_1 1.1911a
Cext_51 vinn vout_2 1.90255f
Cext_52 vinn 0 195.51a
Cext_53 vinp vout_1 1.90255f
Cext_54 vinp vout_2 1.1911a
Cext_55 vinp 0 195.51a
Cext_56 vout_1 vout_2 2.85557f
Cext_57 vout_1 voutp 1.30263f
Cext_58 vout_1 0 3.48146f
Cext_59 vout_2 voutn 1.30263f
Cext_60 vout_2 0 2.00841f
Cext_61 voutn voutp 899.173a
Cext_62 voutn 0 1.16696f
Cext_63 voutp 0 3.18447f
Cext_64 0 net1 58.4298f
Cext_65 0 net2 36.5217f
Cext_66 0 net3 32.7308f
Cext_67 0 net4 67.2614f
Cext_68 0 rep_x 50.5032f
Cext_69 0 vbn 508.048f
Cext_70 0 vbr 76.8724f
Cext_71 0 vdd 195.67f
Cext_72 0 vinn 34.0064f
Cext_73 0 vinp 34.0064f
Cext_74 0 vout_1 217.66f
Cext_75 0 vout_2 63.3418f
Cext_76 0 voutn 346.747f
Cext_77 0 voutp 492.984f
* dropped (substrate to substrate): Cext_78 0 0 936.647f
* --- kpex removes every capacitor device ("whiteboxed" in netlist_expander),
* --- so the six certified cap_cmim cards are re-inserted verbatim here;
* --- their plate/bottom-plate parasitics are the Cext_* elements above.
xc13 net2 vout_1 cap_cmim w=40.53u l=40.53u m=2
xc17 net3 vout_2 cap_cmim w=40.53u l=40.53u m=2
xc19 vout_2 vout_1 cap_cmim w=49.42u l=49.42u m=8
xc1 voutp net4 cap_cmim w=49.91u l=49.91u m=16
xc10 voutn net1 cap_cmim w=49.91u l=49.91u m=16
xc12 voutn voutp cap_cmim w=48.45u l=48.45u m=7
.ends lpf_core
