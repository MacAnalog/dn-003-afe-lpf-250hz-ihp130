# Paper index — agent entry point

**KIND: REFERENCE (partially TBD).** Which paper to retrieve for what.
This is the first stop for any agent working the challenge: pick papers by
the *innovation* column, then read only what you need. The `lpf-paper-analyst`
agent fills a row's TBD cells when it triages that paper (one-line innovation
+ what's usable here); its full brief lands in the experiment directory that
uses the paper. Cite papers everywhere by **handle**.

Baseline context: 4th-order SSF LPF, 250 Hz, subthreshold, goal = IRN
0.5–200 Hz < 40 µVrms with ≥ 2 techniques combined
([../doc/target-spec.md](../doc/target-spec.md)).

**Provenance warning — read before trusting a verdict in this table.** The
triage verdicts below were reached in the **originating campaign**: a prior
design of this filter, in a different technology, at a **1 V** rail. Every
struck-through claim, every "measured" attribution, and every µV figure not
explicitly attributed to this repo is **carried forward, not re-measured
here** — the classified list (technology-independent vs technology-bound) is
[../doc/prior-findings.md](../doc/prior-findings.md). Two rows are
**re-opened** here because this PDK has **no isolated NMOS**, so an n-channel
bulk cannot follow its source: see `selfcomp-gain` and `bulk-neutral`.

| handle | file | content / innovation | usable here for | status |
|---|---|---|---|---|
| `tian2023` | paper01-A_Low-Noise_and_Low-Power_Multi-Channel_ECG_AFE_Based_on_Orthogonal_Current-Reuse_Amplifier.pdf | §II.C cross-coupled current-cancellation CS-LPF (eqs (19)–(21) **wrong** — corrected form carried forward in [prior findings](../doc/prior-findings.md) §1, §3) | drain-cross gm scaling at constant bias; the only power-neutral gm1 multiplier. **Carried-forward verdict:** input-side cancellation at any useful strength is dead (the forward-path zero must clear ~13 kHz to keep the order certificate ⇒ k ≳ 0.98); feedback-side is zero-free but a pure −2.4 % C per +3.2 % IRN trade — [prior findings](../doc/prior-findings.md) §3 | **triaged; ruled out (carried forward)** |
| `fvf-2nd` | paper02-0.6-V_Sub-nW_second-order_lowpass_filters_using_flipped_voltage_followers.pdf | FVF's internal two-pole feedback loop used *as* a complete biquad (0.18 nW/pole @ 0.6 V); the DUT's SSF is this + a level shift | skip as primary (own IRN 52 µV, linear range only 30 mVp); harvest the **floating differential cap** and the orthogonal sizing rule (I_B↔fc, cap-ratio↔Q). **MEASURED HERE (021 §4.2), and it is worth 4× on that element, not 2×:** a floating C between the halves of a balanced pair loads each half with 2C, so the grounded realisation needs 2C per side — four drawn farads where the floating version draws one. A/B by toggling `Design.c2_grounded`, which changes nothing else: **167.0 pF vs 304.2 pF (−45.1 %) for a worst |H| difference of 0.00002 dB across the whole sweep**. This is one of the two techniques S8 rests on | **triaged; technique MEASURED HERE** |
| `selfcomp-gain` | paper03-A_1.5_V_5.2_nW_60_dB-DR_Lowpass_Filter_With_Self-Compansated_Gain_in_0.35_m_CMOS_Suitable_for_Biomedical_Applications.pdf | complementary bulk-effect gains cancel across the cascade: n-input stage K=1/n × p-input stage K=n ⇒ exact 0 dB, zero extra power (eqs 5–6) | ~~**IRN lever**: put the gain-n (p-input) stage FIRST → downstream noise ÷n²~~ ~~**VOID:** shunt feedback pins each SSF stage at 0 dB (bq A −0.0487 dB, bq B −0.0250 dB), so there is no gain-*n* stage and downstream noise divides by 1.000, not n²~~ — that verdict is **carried forward from the originating campaign** ([prior findings](../doc/prior-findings.md) §3, §8.2), where every device could tie bulk to its own source. **RE-OPENED HERE.** SG13G2 has **no isolated NMOS**, so a bulk-at-rail n-follower divides by 1/n whether anyone wants it or not: measured in this repo, an n-input stage gives **−2.328 dB** against **−0.003 dB** for a p-input stage ([experiment-log](../doc/experiment-log.md) 020). The complementary cancellation is therefore a live option, not a moot one — but it cannot be exact: measured here **n_n = 1.38** vs **n_p = 1.54** for the hv pair ([pdk-notes](../doc/pdk-notes.md) §2.1, **11 % apart**), so an n/p cascade leaves a residual against a ±0.2 dB S3 box. The reference baseline sidesteps the family entirely by making **both** followers p-type | **triaged; RE-OPENED (no isolated NMOS)** |
| `ssf-33mhz` | paper04-A_33_MHz_70_dB-SNR_Super-Source-Follower-Based_Low-Pass_Analog_Filter 1.pdf | canonical SSF-biquad theory (JSSC'15): local loop G0=gm2·R2 collapses output noise to **M1 alone** (ORN²≈(32/3)kT/gm1, eq 10); Q set purely by cap ratio | ~~the noise-budget certificate: the baseline IRN is an M1-kT/gm floor — attack gm1 (reuse/chop) or nothing~~ **CORRECTED — carried forward, measured in the originating campaign and NOT re-measured here** ([prior findings](../doc/prior-findings.md) §2): eq (10) assumes IDEAL current-source loads, so the M1-floor claim does not survive real loads — there the input followers were only 27.8 % of IRN power and the eight non-ideal bias sources **61.7 %**. Both shares are technology-bound: re-measure them on this reference before aiming a technique ([experiment-log](../doc/experiment-log.md) queue 1). What survives and is load-bearing: the **cap-ratio/Q rules** — re-allocating the high-Q pair was a free −21.4 % IRN / −8.0 % C. The gm/ID→moderate-inversion lever is an *area* lever that **raises** IRN | **triaged; noise claim corrected (carried forward)** |
| `follower-63nw` | paper05-A_63_nW_250_Hz_70_dB-DR_Subthreshold_CMOS_Follower-Based_LPF_for_ECG_Detection.pdf | CSCP n+p composite input: signal splits across two series gate junctions ⇒ 2× linear range, gm halved ⇒ C halved at same fc (eq 1) | **THD lever** (2× swing + half the slew burden) at a stated **2× IRN density cost** — must be bought back elsewhere. Proof the corner is reachable: 30.3 µVrms @ 250 Hz follower LPF (63 nW). Gives the slew feasibility check `I/C > 2πfc·Vp` (golden fails ~15×) | triaged |
| `bulk-neutral` | paper07-A_Nanopower_Biopotential_Lowpass_Filter_Using_Subthreshold_Current-Reuse_Biquads_With_Bulk_Effect_Self-Neutralization.pdf | all bulks to rails ⇒ every gms = I_B/U_T, passband gain = pure n_p/n_n ratio; N/P cascade cancels to 0 dB (TCAS-I'19) | ~~neutralization itself **moot** (the originating design already tied bulk→source — the better option)~~ **RE-OPENED HERE:** this PDK has **no isolated NMOS**, so "all bulks to rails" is not a design choice, it is the only thing an n-channel device can do — the paper's premise is the process's default. The n-input stage measures **−2.328 dB** here ([experiment-log](../doc/experiment-log.md) 020), i.e. exactly the 1/n the paper cancels. Its N/P cascade is a live 0 dB candidate, subject to n_n = 1.38 vs n_p = 1.54 leaving a residual ([pdk-notes](../doc/pdk-notes.md) §2.1, §3). Keep the **noise bookkeeping** regardless: noise ∝ kT/C2·S(Q), *independent of I_B* (eqs 11–13); K>1-stage-first ordering; HD3∝(1+LG)³; confirms the gms-pinning constraint from the literature | **triaged; RE-OPENED (no isolated NMOS)** |
| `buffer-biquad` | paper08-A_Subthreshold_Buffer-Based_Biquadratic_Cell_and_its_Application_to_Biopotential_Filter_Design.pdf | 3T current-reuse buffer biquad: gate-driven diff pair + shared-branch CS device in global unity feedback; gm = I_B/(2n_pU_T) ≈ gms/3 ⇒ ~3× less C at same fc (TCAS-I'18) | **slew/THD lever**: swap the worst SSF stage for this cell → I/C improves ~3× at same power; eq (13) predicts HD3 ≈ −42 dB at our 43.75 mVp/side (marginal PASS). As-published IRN 80.5 µV (small caps) — resize. Current sources dominate its noise → degenerate them (portable to SSF too) | triaged |
| `gmc-compact` | paper06-A_compact_subthreshold_CMOS_2nd-order_gm-C_lowpass_filter.pdf | 7T biquad: global unity feedback linearizes the passband; two gm's stacked in ONE bias branch (3·I_B total Butterworth) | not a noise donor (own IRN 89 µV); harvest **branch-stacking** (2× gm at zero added current) and the node-partition insight (internal node = bandpass tap that barely swings in-band). **MEASURED HERE (021 §4.2) at EQUAL drawn capacitance and equal cutoff**, which is the confound that would otherwise carry the claim: unstacked 98.0 pF / 49.98 µV / 12.07 nW / 16 devices vs stacked+merged 98.4 pF / **40.96 µV** / **3.92 nW** / 12 devices ⇒ **−18.1 % IRN and −67.5 % core power**. The second technique S8 rests on. **Caveat found here:** the stacked ladder is threshold-referenced (V_SG(gmf_b)+V_SG(bridge)=VDD), so it has NO supply-droop margin (VDD_min 1.50 V vs the reference's 1.35) and it caps the input common mode at 0.65 V | **triaged; technique MEASURED HERE** |
| `gmc-4p6nw` | paper10-Electronics Letters - 2025 - Huang - A 4 6‐nW  100‐Hz  63 88‐dB DR  Second‐Order Subthreshold Gm‐C Filter for Portable.pdf | SCP replaces the follower + **self-cascode composites** (bottom device in subthreshold triode = free local degeneration); HD3 → λ²Vm²/8 (eq 8) | skip the SCP half (2× current, 2× noise, IRN 104 µV). **SC composite is NOT a noise lever — refuted, carried forward and NOT re-measured here** ([prior findings](../doc/prior-findings.md) §2, §3): used to degenerate the bias sources it recovered only −4.6 % (vs −21 % for an ideal resistor), because a subthreshold device in triode itself carries S_id = 2qI·coth(V_DS/2V_T) ≥ 2qI and became the top contributor. The mechanism is technology-independent, so it stays closed as a noise lever. Its **HD3** claim is untested and may still stand; sizing rule: maximize L | **triaged; noise claim refuted (carried forward)** |
| `biodevices` | paper09-biodevices.pdf | Sawigun/Hiseni/Serdijn, BIODEVICES 2012: 6× identical 5T follower-integrators (gate-driven diff pair, unity feedback) — feedback beats linearization; 0.45 nW | **strongest slew/THD fix in the corpus**: gate-drive slew margin A/(2nU_T) vs follower's A/V_T ⇒ ~3–4× more headroom per nA, symmetric ±I_B drive; −40 dB THD @ 0.23 Vpp from 0.15 nA/stage. Costs thermal noise per nA + soft (real-pole) roll-off → use selectively (output stage), keep complex-pole stages for the corner. Flicker rule: big WL, small I_B | triaged |

Triage rules: fill "content / innovation" with ONE line (the mechanism, not
the abstract); "usable here for" says what it could buy on *this* filter
toward IRN/THD/power — or "nothing, because …" (a ruled-out paper is a
result too). Keep [../doc/target-spec.md](../doc/target-spec.md)'s handle
table in sync if files are added.

## Cross-corpus map (2026-08-09 triage)

The corpus separates cleanly by which spec each mechanism moves:

| lever | papers | mechanism |
|---|---|---|
| **IRN** | `selfcomp-gain` (gain-n first, ÷n²), `tian2023` (drain-cross gm1 reuse), `ssf-33mhz` (proof: only M1 matters), `bulk-neutral` (kT/C2·S(Q) budget, I_B-independent) | attack M1's kT/gm or the noise referral order |
| **THD/slew** (the failing spec) | `biodevices` (gate-driven integrator, 3–4× slew/nA), `buffer-biquad` (gm/3 ⇒ C/3), `follower-63nw` (CSCP 2× swing, C/2), `gmc-compact` (branch-stacked 2× gm), `fvf-2nd`+`selfcomp-gain` (floating diff caps), `gmc-4p6nw` (SC composite residual-HD3 cleanup) | add slew margin per nA: reduce required C, or switch swing-critical nodes from gms-drive to gate-drive |
| **0 dB / flatness insurance** | `selfcomp-gain` ↔ `bulk-neutral` (competing, pick one), `buffer-biquad` (K=1 by feedback) | N/P alternation or global unity feedback |

Anti-rules from the triage: SCP (paper10 main idea) hurts both budgets; FVF
as primary is dominated; ~~bulk-neutralization is moot on this DUT~~
**bulk-neutralization is LIVE here** — SG13G2 has no isolated NMOS, so
"all bulks to rails" is the process default rather than a choice
([../doc/pdk-notes.md](../doc/pdk-notes.md) §3); nothing in
the corpus fixes slew by loop gain alone. All nine agents independently
confirmed the weak-inversion pinning constraint holds in their paper's math.

### Re-shelving — carried forward, then re-classified for this PDK

**Everything in this subsection except the two "in this repo" notes is carried
forward from the originating campaign and was NOT re-measured here**
([../doc/prior-findings.md](../doc/prior-findings.md)).

The map above was drawn when THD was believed to be the failing spec. It was
not: the originating baseline **passed S7 with 11 dB of margin**, and **every**
lever in the THD/slew row buys its margin by shrinking C via a smaller gm —
which costs IRN by exactly √(C₀/C) (gm/2 & C/2 measured 78.68 µV, +41.5 %, vs
a √2 prediction of 78.62; the √ law is technology-independent). So:

- The **THD/slew row is spent** — six of ten papers had no value against the
  binding spec. Re-open it only if the high-fin profile becomes a spec line.
  *In this repo:* **S7 has not been measured at all yet**
  ([../doc/experiment-log.md](../doc/experiment-log.md) queue 5), so this is a
  carried-forward expectation, not a local result.
- The **IRN row was aimed at the wrong 28 %**: `tian2023`'s drain-cross makes
  IRN *worse* (+8 to +29 %) while failing the S1 phase certificate, and
  `ssf-33mhz`'s M1 floor is not where the noise is. The surviving IRN content
  is `bulk-neutral`'s kT/C²·S(Q) bookkeeping and `ssf-33mhz`'s cap-ratio/Q
  rules. **Correction for this PDK:** `selfcomp-gain` was struck as "void
  (0 dB stages)" — that reasoning does not transfer, because here an n-input
  follower is **not** a 0 dB stage (−2.328 dB measured). It is re-opened.
- The corpus's one correct pointer at the real problem is buried in the
  `buffer-biquad` row: *"current sources dominate its noise → degenerate
  them (portable to SSF too)"*. It was filed under THD/slew. It was the whole
  game there — and it is queue item 4 here
  ([../doc/experiment-log.md](../doc/experiment-log.md)); note that only a
  **genuine resistor** does it, never a MOS in triode
  ([../doc/prior-findings.md](../doc/prior-findings.md) §2).
- Still-unharvested and the highest-value entries to aim at this repo's own
  noise breakdown once it exists: `gmc-compact` branch-stacking and
  `tian2023` current reuse (delete bias sources rather than degenerate them);
  `biodevices` / `buffer-biquad` gate-driven pairs (make bias noise
  common-mode — but they convert self-referenced gain into a device ratio, so
  they owe a mismatch measurement,
  [../doc/prior-findings.md](../doc/prior-findings.md) §4); `fvf-2nd` floating
  caps (area density).
