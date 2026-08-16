*********************************************************
*** NGSPICE file created by KLayout-PEX 0.3.12
*** -----------------------------------------------------
*** Extraction Engine: KPEX/2.5D
*** Technology: ihp_sg13g2
*** Date: 2026-08-16 02:59:43
*********************************************************

.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
XM$1 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$2 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U PD=8.38U
+ rfmode=0
XM$3 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$4 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$5 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U PD=8.38U
+ rfmode=0
XM$6 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$7 net2 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$8 0 vbn net2 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$9 net2 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$10 0 vbn net3 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$11 net3 vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$12 0 vbn net3 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$13 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$14 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$15 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$16 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=2.72P AD=1.52P PS=16.68U
+ PD=8.38U rfmode=0
XM$17 vbr vbn 0 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=1.52P PS=8.38U
+ PD=8.38U rfmode=0
XM$18 0 vbn vbr 0 sg13_hv_nmos L=25U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$19 vout_1 net2 0 0 sg13_hv_nmos L=45U W=1.5U AS=0.51P AD=0.51P PS=3.68U
+ PD=3.68U rfmode=0
XM$20 0 net3 vout_2 0 sg13_hv_nmos L=45U W=1.5U AS=0.51P AD=0.51P PS=3.68U
+ PD=3.68U rfmode=0
XM$21 vbr vbr rep_x rep_x sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$22 net1 vbr vout_2 net1 sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$23 vdd rep_x rep_x vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=2.04P PS=12.68U
+ PD=12.68U rfmode=0
XM$24 net3 vinn vout_2 vout_2 sg13_hv_pmos L=10U W=8U AS=2.72P AD=1.52P
+ PS=16.68U PD=8.38U rfmode=0
XM$25 vout_2 vinn net3 vout_2 sg13_hv_pmos L=10U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$26 net2 vinp vout_1 vout_1 sg13_hv_pmos L=10U W=8U AS=2.72P AD=1.52P
+ PS=16.68U PD=8.38U rfmode=0
XM$27 vout_1 vinp net2 vout_1 sg13_hv_pmos L=10U W=8U AS=1.52P AD=2.72P PS=8.38U
+ PD=16.68U rfmode=0
XM$28 net4 vout_1 voutp voutp sg13_hv_pmos L=15U W=4U AS=1.36P AD=1.36P PS=8.68U
+ PD=8.68U rfmode=0
XM$29 vout_1 vbr net4 net4 sg13_hv_pmos L=33U W=5U AS=1.7P AD=1.7P PS=10.68U
+ PD=10.68U rfmode=0
XM$30 voutn vout_2 net1 voutn sg13_hv_pmos L=15U W=4U AS=1.36P AD=1.36P PS=8.68U
+ PD=8.68U rfmode=0
XM$31 voutn net1 vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=1.14P PS=12.68U
+ PD=6.38U rfmode=0
XM$32 vdd net1 voutn vdd sg13_hv_pmos L=31U W=6U AS=1.14P AD=2.04P PS=6.38U
+ PD=12.68U rfmode=0
XM$33 voutp net4 vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=1.14P PS=12.68U
+ PD=6.38U rfmode=0
XM$34 vdd net4 voutp vdd sg13_hv_pmos L=31U W=6U AS=1.14P AD=2.04P PS=6.38U
+ PD=12.68U rfmode=0
XM$35 rep_x rep_x vdd vdd sg13_hv_pmos L=31U W=6U AS=2.04P AD=2.04P PS=12.68U
+ PD=12.68U rfmode=0
Cext_1 net1 rep_x 2.05792f
Cext_2 net1 vbr 2.22327f
Cext_3 net1 vdd 4.28342f
Cext_4 net1 vout_2 546.944a
Cext_5 net1 voutn 5.90234f
Cext_6 net1 0 0.807588a
Cext_7 net2 vbn 3.92974f
Cext_8 net2 vbr 90.6441a
Cext_9 net2 vinp 1.63927f
Cext_10 net2 vout_1 632.283a
Cext_11 net2 vout_2 127.31a
Cext_12 net2 0 3.34881f
Cext_13 net3 vbn 3.92974f
Cext_14 net3 vbr 90.6441a
Cext_15 net3 vinn 1.63927f
Cext_16 net3 vout_1 116.142a
Cext_17 net3 vout_2 621.115a
Cext_18 net3 0 3.34898f
Cext_19 net4 rep_x 2.22072f
Cext_20 net4 vbr 2.20721f
Cext_21 net4 vdd 4.28342f
Cext_22 net4 vout_1 546.944a
Cext_23 net4 voutp 5.90234f
Cext_24 net4 0 0.807588a
Cext_25 rep_x vbr 1.4921f
Cext_26 rep_x vdd 3.96481f
Cext_27 rep_x vout_1 994.395a
Cext_28 rep_x vout_2 930.442a
Cext_29 rep_x voutn 2.26399f
Cext_30 rep_x voutp 2.26399f
Cext_31 vbn vbr 13.198f
Cext_32 vbn vout_1 233.291a
Cext_33 vbn vout_2 233.291a
Cext_34 vbn 0 86.2057f
Cext_35 vbr vinn 0.480394a
Cext_36 vbr vinp 0.480394a
Cext_37 vbr vout_1 8.97342f
Cext_38 vbr vout_2 9.02377f
Cext_39 vbr 0 3.25045f
Cext_40 vdd voutn 4.45262f
Cext_41 vdd voutp 5.17051f
Cext_42 vdd 0 6.40873f
Cext_43 vinn vout_1 0.401733a
Cext_44 vinn vout_2 1.84304f
Cext_45 vinn 0 195.51a
Cext_46 vinp vout_1 1.84304f
Cext_47 vinp vout_2 0.401733a
Cext_48 vinp 0 195.51a
Cext_49 vout_1 vout_2 4.55764f
Cext_50 vout_1 voutp 1.32039f
Cext_51 vout_1 0 2.45359f
Cext_52 vout_2 voutn 1.32039f
Cext_53 vout_2 0 3.12942f
Cext_54 voutn voutp 7.44735f
Cext_55 voutn 0 2.05945f
Cext_56 voutp 0 2.33986f
Cext_57 0 net1 58.6832f
Cext_58 0 net2 23.32f
Cext_59 0 net3 23.32f
Cext_60 0 net4 58.6259f
Cext_61 0 rep_x 48.9878f
Cext_62 0 vbn 510.5f
Cext_63 0 vbr 77.7569f
Cext_64 0 vdd 196.548f
Cext_65 0 vinn 33.8308f
Cext_66 0 vinp 33.8308f
Cext_67 0 vout_1 151.561f
Cext_68 0 vout_2 151.38f
Cext_69 0 voutn 430.226f
Cext_70 0 voutp 450.286f
xc13 net2 vout_1 cap_cmim w=40.53u l=40.53u m=2
xc17 net3 vout_2 cap_cmim w=40.53u l=40.53u m=2
xc19 vout_2 vout_1 cap_cmim w=49.42u l=49.42u m=8
xc1 voutp net4 cap_cmim w=49.91u l=49.91u m=16
xc10 voutn net1 cap_cmim w=49.91u l=49.91u m=16
xc12 voutn voutp cap_cmim w=48.45u l=48.45u m=7
.ENDS lpf_core
