.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd vss
Mm2 net2 vinp vout_1 vout_1 sg13_hv_pmos w=16u l=10u
Mm5 net3 vinn vout_2 vout_2 sg13_hv_pmos w=16u l=10u
Mm4 vout_1 net2 vss vss sg13_hv_nmos w=1.5u l=45u
Mm8 vout_2 net3 vss vss sg13_hv_nmos w=1.5u l=45u
Mm9 net2 vbn vss vss sg13_hv_nmos w=24u l=25u
Mm10 net3 vbn vss vss sg13_hv_nmos w=24u l=25u
Mmst vout_1 vbr net4 net4 sg13_hv_pmos w=5u l=33u
Mmstn vout_2 vbr net1 net1 sg13_hv_pmos w=5u l=33u
Mm0 net4 vout_1 voutp voutp sg13_hv_pmos w=4u l=15u
Mm1 net1 vout_2 voutn voutn sg13_hv_pmos w=4u l=15u
Mm14 voutp net4 vdd vdd sg13_hv_pmos w=12u l=31u
Mm15 voutn net1 vdd vdd sg13_hv_pmos w=12u l=31u
Mr1 rep_x rep_x vdd vdd sg13_hv_pmos w=12u l=31u
Mr2 vbr vbr rep_x rep_x sg13_hv_pmos w=5u l=33u
Mr3 vbr vbn vss vss sg13_hv_nmos w=96u l=25u
Cc13 net2 vout_1 cap_cmim w=40.53u l=40.53u m=2
Cc17 net3 vout_2 cap_cmim w=40.53u l=40.53u m=2
Cc19a vout_2 vout_1 cap_cmim w=49.42u l=49.42u m=4
Cc19b vout_1 vout_2 cap_cmim w=49.42u l=49.42u m=4
Cc1 net4 voutp cap_cmim w=49.91u l=49.91u m=16
Cc10 net1 voutn cap_cmim w=49.91u l=49.91u m=16
Cc12a voutn voutp cap_cmim w=48.45u l=48.45u m=4
Cc12b voutp voutn cap_cmim w=48.45u l=48.45u m=3
Mdumn vss vss vss vss sg13_hv_nmos w=336u l=25u
Mdump vdd vdd vdd vdd sg13_hv_pmos w=24u l=31u
.ends lpf_core
