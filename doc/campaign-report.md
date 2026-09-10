# Campaign report — porting the 250 Hz SSF low-pass to IHP SG13G2

**KIND: REPORT.** What was delivered, how it was arrived at, and what is still
open. The deliverable and its evidence live in [`signoff/`](../signoff/pre-pvt/); every
sizing round attempted is in [`sizing-history/`](sizing-history/rounds.md).

## 1. The result

`022-reuse-final` — the originating **branch-stacked super-source-follower**
filter, bridge and current reuse intact, ported by **device type and size only**.
All 42 device connections identical to the drawn topology.

| | reference (yardstick) | **022-reuse-final** |
|---|---|---|
| IRN 0.5–200 Hz | 49.98 µVrms | **28.07 µVrms** (−43.8 %) |
| THD @ 175 mVpp, 50 Hz | −48.37 dB | **−56.46 dB** |
| core power | 12.07 nW | 14.45 nW |
| ph_max (S1) | 346.74° | 341.42° |
| passband ripple | **0.2512 dB — fails S3** | **0.0691 dB** |
| `mono_db` | 0.0227 | 0.0068 |
| drawn capacitance | 98.0 pF | 366.3 pF |
| mismatch yield | — | **95 %** (100 samples) |

> **Which `022-reuse-final` numbers these are.** The **`022-reuse-final`** column
> above is the sizing as fitted. The certified sign-off scorecard
> (`signoff/pre-pvt/scorecard.json`, cell `H-shipped`) is measured on the
> **layout-legalized** netlist (5 nm grid, PDK minimum widths, ≤ 10 µm gate
> fingers, `lab.grid.legalize` + the fc restoration it forces,
> `lab.retune.restore_fc`) and reads IRN **27.87 µVrms**, THD **−56.18 dB**,
> ph_max **341.30°**, core power **14.50 nW**, ripple **0.0929 dB**, fc
> **249.99 Hz**. The repo files the split as its own open item **G17**
> (`doc/paper/README.md` §5), whose ruling is: quote the packaged sign-off JSON
> everywhere. `signoff/pre-pvt/COMPARISON.md` ranks all nine sizings.

All of S1–S8 pass. The challenge asked for IRN < 40 µVrms combining ≥ 2 paper
techniques; both are met, and the cell also beats the reference on distortion and
on the flatness clause the reference itself misses.

## 2. How it was arrived at — four diagnoses

37 sizing points across 11 rounds ([full table](sizing-history/rounds.md)). The
path was not a search: each of four diagnoses changed what to search for.

### 2.1 The passband bump was a measurement gap, not a technology limit

Every optimiser-fitted cell had a visible bump and every one passed the flatness
box, because `peak_db` is one-sided and `ripple_db` is a peak-to-peak spread — a
response that sags 0.09 dB and recovers 0.09 dB scores 0.000 and 0.084 against a
0.2 dB bound. Fixed by scoring the *shape*: `lab.raw.monotone_db` (now on every
scorecard) and `lab.shape.fit_butter` against the 4-pole Butterworth template.
`mono_db` went 0.151 → 0.0005 on the first cell re-fitted.

Flatness turned out **not** to be free: it cost one candidate 5.8 dB of THD,
confirmed by re-measuring the pre-fit sizing. That set the selection rule for
everything after — the cell that survives flattening is the one with S7 margin.

### 2.2 The S1 phase certificate was inverting a verdict

`ph_max_deg` scored every point above the −100 dB floor rather than the
contiguous band below the first crossing. On a cell with a feed-through plateau
(|H| falls through at 3.2 kHz, returns at 14.5 kHz, sits at −98.5 dB to
100 kHz) `np.unwrap` ran across the gap and reported **368.6°** for a cell
whose lag saturates at **320.7°** — an S1 fail
reported as a pass by 38°, on what had been the strongest cell in the repo. The
150° step guard missed it (the spurious step was 75°). Fixed in `lab.raw`, and in
`lab.plot.bode`, which had the same mask.

The related fact worth keeping: **"4 poles ⇒ 360°" is false of the certificate.**
Pushed through the same −100 dB floor, a *mathematically ideal* 4-pole
Butterworth scores **350.53°**. The ceiling is ~350°, not 360°, and a score above
~351° is parasitic lag rather than extra order.

### 2.3 Mismatch and phase have different owners

The unstacked cell returned 12 % mismatch yield. Growing all device areas fixes
σ(fc) and then fails S1 on phase (343.9 → 322.5°) because the phase cost is
*signal-path* gate capacitance, while the fc spread is *bias-device* threshold
mismatch — σ(I)/I = σ(V_th)/(n·U_T), so
a few mV is a >10 % current spread. Growing **only** the bias devices, whose
gates sit on quiet rails, took yield 12 → 87 % for **3.2° of phase across an 81×
area range**. The lever is not monotone: once nominal phase margin is thin,
`ph_max` becomes the binding line and yield collapses — so the optimum depends on
the cell's own margin (×9 for the stacked cell, ×36 for the unstacked).

### 2.4 The common mode is a threshold problem, and it forced the flavour work

The all-p cascade shifts CM up one |V_SG| per stage, pinning vicm near 0.20 V.
Width buys only ~92 mV per *decade*, and the ~30× needed for 0.5 V converts
47 pF of MIM into non-linear **gate** capacitance — drawn C fell
150.6 → 104.0 pF at the same cutoff, THD collapsed to −30.3 dB, and the response
stopped being 4-pole. `sg13_lv_pmos` attacks V_th instead: measured 0.168 V
against hv's 0.457 V at this cell's own currents, i.e. **588 mV** of headroom,
and it *improved* noise (gm/ID 32 vs 25).

## 3. What device type and size could not fix — supply rejection

The reuse ladder sets its current by
`|V_SG|(gmf_b) + |V_SG|(bridge) = VDD − vbn`, so it is threshold-referenced:
`dI/I = dVDD/(2·n·U_T)`. Measured, fc goes
250.0 → 206.5 Hz at VDD 1.45 V and
**S2 is what breaks**. Moving `gmf_b` to lv roughly halved the sensitivity
(supply-current ratio 6.4 → 2.7) and got nowhere near enough.

The arithmetic closes it. **No choice of device type or size can make a
current-reuse ladder hold a ±2 % cutoff over a drooping supply**; it needs a
supply-independent bias, i.e. added components. The 1/22 corner count has the
same root cause.

| quantity | value |
|---|---|
| fc tolerance required (S2) | ±2 % |
| branch-current tolerance that implies | ±4 % |
| over a rail of | ±10 % |
| device slope that would need | **~1.9 V per e-fold** |
| slope real MOS delivers | 0.04 V (weak inversion) … ~0.2 V (strong) |

A second structural fact came out of the same analysis: the ladder pins the
current *density*, so widening both devices raised the current 2.15 → 55.9 nA
over 100× while **gm/ID stayed at 24.5 throughout**. Sizing cannot move the
inversion level at all; only V_th can — and only a *mixed* flavour pair works,
because lv on both needs |V_ds| ≈ V_ov = 0.39 V that a five-device ladder cannot
give (measured gm/gds of 0–2, i.e. triode).

Neither supply droop nor corner yield is an S1–S8 line, and the frozen reference
does not survive the ±10 % box either. The cell is fully spec-compliant; what it
is not is supply-tolerant.

## 4. Corrections made to the repo's own record

* The frozen reference **does not meet its own S3 flatness clause** when measured
  densely: `ripple_db` 0.2512 dB against a 0.2 dB bound. It passed at 10
  pts/decade only because the samples straddled the feature. The reference was
  re-certified at 50 pts/decade (IRN 50.18 → 49.98 µVrms; the ask is −20.0 %,
  not −20.3 %) and the failure is recorded rather than smoothed over.
* `pdf/INDEX.md` said the floating differential capacitor is worth 2×. Measured
  here it is worth **4× on that element** — a floating C between the halves of a
  balanced pair loads each half with 2C, so the grounded realisation needs 2C per
  side. Corrected in the row.
* **Q allocation does not set THD** in this topology (the `qwalk` round). THD
  correlated cleanly with biquad B's capacitor ratio across four cells, but
  walking that ratio and re-fitting showed only 2 of 6 points could reach the
  template and the fit pulled the survivor back to the same allocation for
  0.54 dB. The correlation was a proxy for device sizing.
* **S7's single 50 Hz point hides a 23 dB spread.** Profiled across the passband,
  two cells 2 dB apart at 50 Hz were 23 dB apart at 100 Hz. Degradation toward
  the corner is a family property (the internal node is a bandpass tap and peaks
  there); the extra gap is stacking's, because one shared ladder current cannot
  serve both taps. Profiling is now a pre-sign-off step.

## 5. Open

1. **Supply-independent bias** — the only route to droop tolerance, and it needs
   components the current constraint forbids. This is the single largest gap
   between this cell and a manufacturable one.
2. **In-band THD above 100 Hz** remains ~15 dB behind the reference. More current
   narrows it (7.6 dB from 2.2× the power) without closing it.
3. **Level shifter** for the input common mode (0.65 V today). Budget:
   √(40² − 28.07²) = 28.5 µVrms of input-referred noise before S5 breaks.
4. **Layout** — explicitly out of scope here. The capacitors are drawn as ideal
   elements (366.3 pF of `cap_cmim` is an area decision), and the 95 % mismatch
   yield assumes the PDK's statistical model with no layout gradient;
   common-centroid placement of the bias devices is what protects it.
5. `021-vdd2-final` is a technique short of S8. Its 365 mV of spare |V_ds| would
   accommodate `gmc-4p6nw`'s self-cascode composite on the bias devices — a
   bias-device change, not a signal-topology one.
