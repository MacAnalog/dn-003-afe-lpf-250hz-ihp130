.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  xm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=1.6e-05 l=1e-05 ng=2 m=1
  xm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=1.6e-05 l=1e-05 ng=2 m=1
  xm4 vout_1 net2 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm8 vout_2 net3 0 0 sg13_hv_nmos w=1.5e-06 l=4.5e-05 ng=1 m=1
  xm9 net2 vbn 0 0 sg13_hv_nmos w=2.4e-05 l=2.5e-05 ng=3 m=1
  xm10 net3 vbn 0 0 sg13_hv_nmos w=2.4e-05 l=2.5e-05 ng=3 m=1
  xmst vout_1 vbr net4 net4 sg13_hv_pmos w=5e-06 l=3.3e-05 ng=1 m=1
  xmstn vout_2 vbr net1 net1 sg13_hv_pmos w=5e-06 l=3.3e-05 ng=1 m=1
  xm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4e-06 l=1.5e-05 ng=1 m=1
  xm14 voutp net4 vdd vdd sg13_hv_pmos w=1.2e-05 l=3.1e-05 ng=2 m=1
  xm15 voutn net1 vdd vdd sg13_hv_pmos w=1.2e-05 l=3.1e-05 ng=2 m=1
  xr1 rep_x rep_x vdd vdd sg13_hv_pmos w=1.2e-05 l=3.1e-05 ng=2 m=1
  xr2 vbr vbr rep_x rep_x sg13_hv_pmos w=5e-06 l=3.3e-05 ng=1 m=1
  xr3 vbr vbn 0 0 sg13_hv_nmos w=2.4e-05 l=2.5e-05 ng=3 m=4
  xc13 net2 vout_1 cap_cmim w=40.53u l=40.53u m=2
  xc17 net3 vout_2 cap_cmim w=40.53u l=40.53u m=2
  xc19 vout_2 vout_1 cap_cmim w=49.42u l=49.42u m=8
  xc1 voutp net4 cap_cmim w=49.91u l=49.91u m=16
  xc10 voutn net1 cap_cmim w=49.91u l=49.91u m=16
  xc12 voutn voutp cap_cmim w=48.45u l=48.45u m=7
  Cext_1 net1 rep_x 2.08296f
  Cext_2 net1 vbr 2.237f
  Cext_3 net1 vdd 4.26002f
  Cext_4 net1 vout_2 601.767a
  Cext_5 net1 voutn 6.3783f
  Cext_6 net1 0 1.02101a
  Cext_7 net2 vbn 4.3717f
  Cext_8 net2 vbr 88.6808a
  Cext_9 net2 vinp 1.82108f
  Cext_10 net2 vout_1 683.085a
  Cext_11 net2 vout_2 170.428a
  Cext_12 net2 0 1.78979f
  Cext_13 net3 vbn 4.3717f
  Cext_14 net3 vbr 88.6808a
  Cext_15 net3 vinn 1.82108f
  Cext_16 net3 vout_1 115.742a
  Cext_17 net3 vout_2 670.341a
  Cext_18 net3 0 1.78996f
  Cext_19 net4 rep_x 2.26018f
  Cext_20 net4 vbr 2.22016f
  Cext_21 net4 vdd 4.26002f
  Cext_22 net4 vout_1 601.103a
  Cext_23 net4 voutp 6.3783f
  Cext_24 net4 0 1.02101a
  Cext_25 rep_x vbr 1.49176f
  Cext_26 rep_x vdd 3.96707f
  Cext_27 rep_x vout_1 930.419a
  Cext_28 rep_x vout_2 827.584a
  Cext_29 rep_x voutn 2.16393f
  Cext_30 rep_x voutp 2.16393f
  Cext_31 vbn vbr 13.2046f
  Cext_32 vbn vout_1 267.252a
  Cext_33 vbn vout_2 267.252a
  Cext_34 vbn 0 88.3123f
  Cext_35 vbr vinn 0.482111a
  Cext_36 vbr vinp 0.482111a
  Cext_37 vbr vout_1 7.65961f
  Cext_38 vbr vout_2 7.7068f
  Cext_39 vbr 0 3.95534f
  Cext_40 vdd voutn 5.9328f
  Cext_41 vdd voutp 7.13456f
  Cext_42 vdd 0 9.24438f
  Cext_43 vinn vout_2 1.83619f
  Cext_44 vinn 0 209.864a
  Cext_45 vinp vout_1 1.83619f
  Cext_46 vinp 0 209.864a
  Cext_47 vout_1 vout_2 4.14963f
  Cext_48 vout_1 voutp 1.32099f
  Cext_49 vout_1 0 2.47055f
  Cext_50 vout_2 voutn 1.32099f
  Cext_51 vout_2 0 2.64275f
  Cext_52 voutn voutp 6.7408f
  Cext_53 voutn 0 2.90132f
  Cext_54 voutp 0 3.29259f
  Cext_55 0 net1 58.4965f
  Cext_56 0 net2 22.1268f
  Cext_57 0 net3 22.1452f
  Cext_58 0 net4 58.439f
  Cext_59 0 rep_x 48.7947f
  Cext_60 0 vbn 506.764f
  Cext_61 0 vbr 76.6516f
  Cext_62 0 vdd 196.389f
  Cext_63 0 vinn 33.6582f
  Cext_64 0 vinp 33.6582f
  Cext_65 0 vout_1 149.76f
  Cext_66 0 vout_2 149.804f
  Cext_67 0 voutn 430.716f
  Cext_68 0 voutp 450.81f
.ends lpf_core

