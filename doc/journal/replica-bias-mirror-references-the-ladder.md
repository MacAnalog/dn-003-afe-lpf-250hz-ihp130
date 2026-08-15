# 2026-08-15 — The branch-stacked ladder's PVT failure is PROCESS as much as supply; a three-device replica of gmf_b + bridge makes the ladder current mirror-referenced (fc span 14× → 1.13× across ss/ff at nominal V/T)

KIND: journal entry | type: semantic | status: live

**Symptom.** Every sign-off cell reported 1/22 (E1 2/22) PVT corners and
`signoff/COMPARISON.md` called it "the threshold-referenced supply
limitation". Run process ALONE at the bench's 1.5 V / 27 °C — a set the
22-point screen does not contain — and the cells give fc (ss/ff/sf/fs):
A 13.6/524/299/205 Hz, E 28.3/398/281/221, H 125/377/277/224; the un-stacked
reference gives **247.8/252.8/251.8/248.8**. The reference mirrors every
current from `iref`; the merged ladder's current is the solution of
`|V_SG|(gmf_b) + |V_SG|(bridge) = VDD − vbn` — three thresholds against the
supply — so a Vth skew moves it exponentially. Topology property, not sizing.

**The fix (topology `d`, `lab.dut.build_d`, `replica_of`).** One shared branch,
`vdd → xr1 (p, diode, = gmf_b) → xr2 (p, diode, = bridge) → xr3 (n, gate vbn, m·unit) → gnd`,
whose bottom node `vbr` becomes the bridge gate rail. Then
`vbr = VDD − |V_SG|(xr1) − |V_SG|(xr2)` at I_t = m·iref and the ladder solves to
I_L = I_t: measured E-combo 3.03 nA vs 3.04 (0.4 %). Signal path unchanged
(S8 provenance intact); cost one branch of I_t (3–4.5 nW inside S6) and a
replica-vs-ladder mismatch term.

**Measured (experiments/023-replica-bias):**

| cell | fc @ ss / ff (27 °C, 1.5 V) | fc @ 1.35 / 1.65 V |
|---|---|---|
| E-combo (sign-off) | 28 / 398 | 96 / 258 |
| E-rep (replica only) | 231 / 261 | 95 / 258 |
| B1 (replica + headroom re-centred) | **248.0 / 250.6** | **249.1 / 250.1** |

Replica alone fixes the *bias*; what remains at `ss` and the low rail is
headroom (`merged-ladder-headroom-identity`). With both, `B1` passes every spec
line at all four process corners and both rails; the full 45-point grid goes
1/22 → 12/45 at constant current and **20/45 with a PTAT reference**
(`LPF_BIAS_ALPHA=1`; the reference cell is 0/45 either way).

**What the replica costs in yield.** MC all-pass 49 % on `B1` (σ(fc) 7.5 Hz)
against 70 % on B-balanced: the current-setting loop now has five matched
devices (gmf_b/xr1, bridge/xr2, xr3/xmbn) and the smallest of them (bridge
1.62/10.9 µm, 18 µm²) dominates. Area on the replica pair is the yield lever
(bias-area-buys-yield-phase-pays applies: their gates sit on quiet rails).

**How to apply.** Any merged/stacked cell: build it as topology `d`
(`replica_of(design, m)` with an integer m so the sink is a unit-copy mirror),
then size headroom, then caps. Run `lab.corners.AXES` before `REDUCED`.
