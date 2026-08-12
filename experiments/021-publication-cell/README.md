# 021 — the publication cell: a flat, monotone 4-pole that holds every line

**Status: CLOSED 2026-08-12 — `021-final` certified on all of S1–S8 at the nominal corner, with 78 % mismatch yield. NOT corner-robust and NOT droop-tolerant; see §5.**

| | |
|---|---|
| **Paper(s)** | branch stacking (`gmc-compact` §7T, with `tian2023`) + the floating differential capacitor (`fvf-2nd`) — each measured here by its own equal-shape A/B in [`s8.py`](s8.py). Cap/Q re-allocation (`ssf-33mhz`) is used throughout but claimed as the **control**, not as a technique, per the S8 row of [target-spec](../../doc/target-spec.md). |
| **Hypothesis** | The passband bump on every optimiser-fitted cell is a *fit artefact*, not a technology limit: scoring the whole passband against the 4-pole Butterworth **template** (rather than against scalar peak/ripple bounds) yields a monotone, maximally-flat response at no cost in cutoff or stopband. Where it does cost something, the currency is THD, and the cell with the largest S7 margin should therefore survive the flattening. |
| **Verdict** | **CONFIRMED.** The bump was a fit artefact: fitting against the Butterworth template instead of scalar bounds gives `mono_db` = 0.0000 dB and peaking +0.0000 dB at no cost in cutoff or stopband. Flatness *does* cost THD (5.8 dB on G-135, measured both ways), so the cell that survives it is the one with S7 margin — as predicted. Two things were found on the way that were not hypothesised: the S1 phase certificate was scoring a non-contiguous band and reporting an 18°-over-ideal FAIL as a PASS (§4.4), and the reference itself does not meet S3's flatness clause when measured densely. |

## 1. Why this experiment exists

Two defects in the previous round, both found by looking at the response rather
than at the scorecard.

**The bump.** `lab.shape.cost` scored a scalar ripple *bound*. A response that
sags 0.09 dB at 80 Hz and climbs 0.09 dB back at 130 Hz satisfies that bound —
`peak_db` reads 0.000 (it is one-sided) and `ripple_db` reads 0.084 against a
0.2 dB limit — while visibly not being a maximally-flat low-pass. The
originating campaign's merge cell measured **peaking 0.00 dB**, so this is a
fit artefact and not something the topology imposes.

The metric that catches it is now `lab.raw.monotone_db`, reported on every
scorecard as the soft column `mono_db`: the worst *rise* of |H| with frequency
below the corner, zero iff the response never climbs. Measured, before any
re-fit:

| cell | reference | n6-98 | gb12-175 | G-120 | G-135 | 020B |
|---|---|---|---|---|---|---|
| `mono_db` | **0.023** | 0.150 | 0.151 | 0.179 | 0.184 | 0.362 |

**The ported cap set does not transfer.** Loading the originating campaign's
merge-cell capacitors directly into SG13G2 gives **+8.18 dB** of peaking, and
uniform scaling does not help (peaking stays +8.2 dB at every scale factor) —
the Q's depend on gm_i/gm_f, and those moved with the technology. The shape has
to be re-derived here, which is what `lab.shape.fit_butter` does.

## 2. What "360° of phase" can actually mean here

S1 asks for two true biquads, certified as ≥ 330° of unwrapped phase lag. It is
worth being exact about the ceiling, because "4 poles ⇒ 360°" is true of the
transfer function and **not** of the measurement.

`lab.raw.ph_max_deg` scores phase only where |H| ≥ −100 dB relative to dc,
because below that the response has collapsed into a parasitic feed-through
plateau where the sampled phase aliases and manufactures fake lag. Pushed
through that same definition on the scoring grid, a **mathematically ideal**
4-pole Butterworth returns:

| | ideal 4-pole Butterworth | this repo's reference |
|---|---|---|
| `ph_max_deg`, −100 dB floor | **350.53°** | 346.43° |
| `ph_max_deg`, no floor | 359.57° | — |
| |H| reaches −100 dB at | 15.9 × fc (3981 Hz) | 3162 Hz |

So ~350° is the ceiling, not 360°: the magnitude falls through the floor while
the phase is still ~9° short of its asymptote. The reference sits 4° under the
ideal, i.e. it *is* a true 4-pole. A cell scoring materially **above** ~351° is
not "more fourth-order" — it is carrying parasitic lag the 4-pole model does
not contain, and should be treated as a warning rather than a win.

## 3. Method

Every candidate is fitted with **devices held fixed** — only the four
capacitors move — so any change in IRN is the capacitance moving and not the
transistors. That makes each fit its own re-allocation control (rule 3).

`common.synth` builds a sizing point's capacitors in three stages, cheapest
first: analytic (closed form from one op probe), uniform trim (scaling all four
caps by k leaves both Q's exactly unchanged and moves ω₀ by 1/k), then a
template polish. Stage 1 alone is **not** trustworthy in this PDK — measured, it
lands fc 21–50 % low and, once trimmed back to 250 Hz, gives |H|@1 kHz of
−26 dB where Butterworth demands −48. Every internal node carries parasitic
capacitance the two-capacitor model does not know about, so the closed form is
a starting point and the fit is the instrument.

## 4. Result

### 4.1 The certified cell — `021-final`

020C-frozen, scaled ×1.5 in size (§4.3) and ×1.30 in *gate area at fixed W/L*
(§4.6), template-fitted, then **independently re-measured** by
[`certify.py`](certify.py) from its stored sizing. Nothing below is read back
out of a run the fitter made.

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ≥ 330° (ideal-4-pole ceiling 350.5°) | **333.29°** | PASS |
| S1 stopband | ≤ −48 dB @ 1 kHz | **−49.60 dB** | PASS |
| S2 cutoff | 245–255 Hz | **249.87 Hz** | PASS |
| S3 dc gain | \|dc\| ≤ 0.2 dB | **−0.0078 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB to 150 Hz | **0.0557 dB** | PASS |
| S4 peaking | ≤ 0.2 dB | **+0.0000 dB** | PASS |
| S5 IRN 0.5–200 Hz | < 40 µVrms | **30.71 µV** | PASS |
| S6 core power | < 50 nW | **6.01 nW** | PASS |
| S7 THD @ 175 mVpp, 50 Hz | ≤ −40 dB | **−42.22 dB** | PASS |
| S8 provenance | ≥ 2 papers combined | §4.2 | PASS |

`mono_db` = **0.0000 dB** — the response never climbs anywhere below the corner.
Template rms 0.0045 dB, worst 0.0196 dB. Total drawn capacitance **150.6 pF**
(reported, never specced). Against the reference: **IRN −38.6 %**, **core power
−50.2 %**, capacitance +54 %, and it meets the S3 flatness clause the reference
itself misses (0.0557 dB vs 0.2512).

Phase certificate audit: worst step 2.5° against a 150° alarm, scored band ends
at ≈ 12 × fc against the ideal's 15.9 ×, floored and unfloored values agree.
Harmonics are HD3-limited with HD2/HD4 at ≈ −157 dB, i.e. the differential
balance is intact.

**Disclosed:** the cell has a high-frequency **feed-through plateau at ≈ −98 dB**
from ~15 kHz out to 100 kHz (visible in `figs/cert021_bode.png`). Harmless for a
250 Hz biopotential filter, but it is why the phase certificate must be scored
on a contiguous prefix — see §4.4.

### 4.2 S8 — two techniques, each measured here

**Branch stacking** (`gmc-compact` §7T, with `tian2023`). Both input followers
share one dc branch through a p-type bridge, and the merge re-gates biquad B's
output bias device to its own internal node, deleting the separate gm_f pair.
A/B at **equal drawn capacitance and equal cutoff** — the confound that would
otherwise carry the claim:

| arm | C pF | fc | IRN µV | P nW | devices | bias devices |
|---|---|---|---|---|---|---|
| unstacked (reference topology) | 98.0 | 250.37 | 49.98 | 12.07 | 16 | 8 |
| **stacked + merged** | 98.4 | 249.91 | **40.96** | **3.92** | 12 | **2** |

**−18.1 % IRN and −67.5 % core power**, six fewer bias devices per pair.

**Floating differential capacitor** (`fvf-2nd`). Each `c2` is one capacitor
across the pair rather than two to ground. A/B by toggling
`Design.c2_grounded`, which changes nothing else:

| realisation | fc | a1k | mono | IRN | **drawn C** |
|---|---|---|---|---|---|
| floating (as built) | 249.86 | −48.77 | 0.0005 | 27.24 | **167.0 pF** |
| grounded (control) | 249.86 | −48.77 | 0.0005 | 27.24 | 304.2 pF |

Worst \|H\| difference across the whole sweep: **0.00002 dB** — the same filter
to five decimals, for **45.1 % fewer drawn farads**.

Cap/Q re-allocation (`ssf-33mhz`) is used throughout and is claimed as the
**control**, not as a technique, per the S8 row of the spec.

### 4.3 Why uniform scaling, and where it stops

Multiplying every device width, `iref` and all four capacitors by the same k
leaves every current *density* unchanged, so the operating points, the poles,
the shape, the phase and the linearity should all be invariant while IRN falls
as 1/√k and power rises as k. Measured on 020C-frozen:

| k | fc | mono | a1k | ph_max | IRN µV | P nW | C pF | THD | all 9? |
|---|---|---|---|---|---|---|---|---|---|
| 1.0 | 249.86 | 0.0000 | −49.04 | 339.77 | 39.70 | 4.15 | 104.4 | −41.69 | PASS |
| **1.5** | **250.14** | **0.0000** | **−49.40** | **339.59** | **32.46** | **5.99** | **153.2** | **−40.50** | **PASS** |
| 2.0 | 250.06 | 0.0000 | −49.56 | 339.54 | 28.12 | 7.88 | 202.7 | −39.97 | fail |
| 2.5 | 250.00 | 0.0000 | −49.64 | 339.52 | 25.16 | 9.78 | 252.5 | −39.71 | fail |
| 3.0 | 249.97 | 0.0000 | −49.68 | 339.52 | 22.97 | 11.70 | 302.4 | −39.56 | fail |

fc, `mono_db`, a1k and ph_max are flat to within noise, and IRN tracks 1/√k to
0.2 % — the law holds. **THD does not**: it drifts 2.1 dB over 3×, which the law
does not predict and which is what closes the passing window at k ≈ 1.6. The
drift is monotone in k, so it is a real effect (the drawn capacitance grows
while the parasitics that shape the internal-node swing do not), not noise.

**The passing window is k ∈ [1.0, ~1.6]**, and it is bounded by S5 at the bottom
(k = 1.0 leaves 0.30 µV of margin) and S7 at the top. k = 1.5 is chosen as the
midpoint of what the box allows, not as an optimum.

### 4.6 Gate area buys mismatch yield, and phase pays for it

σ(V_th) ∝ 1/√(W·L), so scaling W **and** L by the same factor multiplies gate
area while leaving W/L — and therefore gm, current, fc, THD, phase and power —
nominally untouched. It is aimed straight at the candidate's binding mismatch
line, which is fc (only 75 % of samples inside the ±2 % box). Measured, each
point re-fitted and then given its own 64-sample mismatch run:

| gate area | fc | mono | a1k | **ph_max** | IRN µV | P nW | C pF | **THD** | **MC all-pass** | σ(fc) |
|---|---|---|---|---|---|---|---|---|---|---|
| ×1.00 | 250.19 | 0.0291 | −49.42 | 340.0 | 32.44 | 5.99 | 151.5 | −39.83 | 73.4 % | 4.08 Hz |
| ×1.32 | 249.93 | 0.0154 | −49.80 | 337.3 | 31.39 | 6.00 | 151.8 | −40.03 | 75.0 % | 3.60 Hz |
| **×1.69** | **249.87** | **0.0000** | **−49.60** | **333.3** | **30.71** | **6.01** | **150.6** | **−42.22** | **78.1 %** | **3.25 Hz** |
| ×2.10 | 249.98 | 0.0226 | −50.36 | 331.3 | 30.15 | 6.03 | 150.7 | −40.96 | 67.2 % | 2.95 Hz |
| ×2.56 | 249.88 | 0.0000 | −50.43 | **327.3** | 29.81 | 6.04 | 150.1 | −42.78 | **0 % (S1 fails)** | 2.73 Hz |

σ(fc) falls monotonically with area, exactly as σ(V_th) ∝ 1/√area predicts, and
IRN and THD improve too. **Phase does not survive it**: ph_max falls 340.0° →
327.3° and drops out of the S1 box at ×2.56. Longer gates mean more gate–drain
capacitance, which strengthens the feed-through path that arrests the lag —
the same mechanism that disqualified 020B-frozen in §4.4, arrived at from the
other direction.

All-pass yield is therefore **not** monotone in area: it peaks at ×1.69 and
collapses once the nominal phase margin is too thin for mismatch to survive.
×1.69 is the chosen operating point.

### 4.4 A harness defect this experiment found, and why it matters

`ph_max_deg` scored **every point above the −100 dB floor**, not the contiguous
band below the first crossing. On a cell with a feed-through plateau that is not
the same thing: |H| falls through the floor at 3.2 kHz, comes back at 14.5 kHz,
`np.unwrap` runs across the 11 kHz gap, and the certificate reads **368.6°** for
a cell whose lag genuinely saturates at **320.7°**.

That is an S1 **FAIL reported as a PASS, by 38°** — and the existing step guard
did not catch it, because the spurious step measured 75°, half the 150° alarm.
Fixed in `lab.raw._floor_prefix` (and in `lab.plot.bode`, which had the same
mask and drew phase climbing to ~358°). The ideal 4-pole still scores 350.53°,
so the fix is conservative. Re-scored:

| cell | ph_max before | ph_max corrected | S1 |
|---|---|---|---|
| 020B-frozen | 368.56 | **320.66** | **FAIL** |
| 020C-frozen | 359.8 | 339.77 | PASS |
| 020B-cert | 342.4 | 346.13 | PASS |
| reference | 346.74 | 346.74 | PASS (unchanged) |

020B-frozen had otherwise been the strongest cell in the repo — IRN 28.05 µV,
THD −44.78 dB, 5.39 nW, perfectly monotone — and it is disqualified by this. It
is not a marginal loss either: 320.7° is 9° outside the box, and the deficit is
structural (a feed-through zero arrests the lag by 2 kHz).

### 4.5 Falsified along the way

**Q allocation does not set THD here.** A 4th-order Butterworth needs
{0.5412, 1.3066} and which stage carries which is free in the magnitude
response, so the assignment looked like a free THD lever — and THD across four
cells correlated cleanly with biquad B's capacitor ratio (3.33 → −41.6 dB,
2.47 → −35.8, 1.59 → −35.7, 0.27 → −28.6). Walking that ratio at fixed ω₀ and
re-fitting each point: only **2 of 6** points reached the template at all, and
the fit pulled the survivor straight back to the same allocation
(c1_b/c2_b 2.53 vs 2.47) for **0.54 dB** of THD. The allocation is not free in
this topology — the two stages have different gm ratios, so the template has
essentially one solution, and the correlation was a proxy for the device sizing
that produced it.

## 5. Yield

Reported on three axes, because they fail differently — see
[`robust.py`](robust.py). Corner yield is **not** an S1–S8 line, and the frozen
reference does not survive the ±10 % supply box either, so corner counts are a
comparison against the reference and never a pass/fail.

### 5.1 Mismatch Monte Carlo — the yield question as a fab would ask it

100 samples, PDK mismatch models (`<corner>_mismatch`, per-instance `delvto`,
`factuo`, `dw`, `dl`), seeded by `.option seed=<n>` at netlist-parse time.
Denominator is samples **attempted**, so a non-converged sample can only lower
the number.

| | 021-final | reference |
|---|---|---|
| **all-pass yield** | **78.0 %** (78/100) | 0 % (0/64) |
| non-converged | 0 | 0 |
| σ(dc_db) | 0.00003 dB | 0.00004 dB |
| σ(fc) | **3.32 Hz** (1.3 %) | 13.99 Hz (5.6 %) |
| σ(IRN) | 0.338 µV | 1.856 µV |
| lines below 100 % | fc 86.0 %, ph_max 90.0 % | irn 0 %, ripple 18.8 %, fc 32.8 %, a1000 48.4 %, peak 82.8 % |

σ(dc_db) of 30 µdB against a 200 mdB box confirms the property the whole family
rests on: a source follower's passband gain is **self-referenced**, so a
threshold shift moves the operating point and barely moves the gain. σ(fc) is
**4.2× tighter** than the reference's.

The reference's 0 % is not a fair comparison — it fails S5 *nominally*, so no
sample can pass. Its *shape* yields (fc 32.8 %, ripple 18.8 %) are the
meaningful column, and 021-final beats them on both.

### 5.2 PVT corners — and the honest verdict

| | 021-final | reference |
|---|---|---|
| corners clean (`REDUCED`, 22 points) | **1/22** | 0/22 |

Both are poor. The reference's binding corner is a **headroom collapse at the
1.35 V rail**, documented in `lab/corners.py`: all-p followers push the common
mode up one \|Vgs\| per stage, \|Vgs\| grows cold, and at VDD −10 % the top bias
device leaves saturation. 021-final inherits that and adds its own: the
branch-stacked ladder fixes its current through
V_SG(gmf_b) + V_SG(bridge) = VDD, which is **threshold-referenced, not
mirror-referenced**, so a process or supply shift moves the branch current
*exponentially*. That is why its fc span across the box is far wider than the
reference's.

### 5.3 Supply droop — the real weakness, stated plainly

| | 021-final | reference |
|---|---|---|
| VDD_min (no new spec violation) | **1.50 V — zero margin** | 1.35 V (0.15 V margin) |
| first new failure at | 1.45 V | 1.30 V (limiter `bias_b_out`, \|Vds\| 77 mV) |

**021-final has no supply-droop margin at all.** It meets every spec line at
1.5 V and loses one at 1.45 V — a 3.3 % droop. The reference tolerates 10 %.
This is the single largest thing standing between this cell and a
manufacturable design, and it follows directly from §5.2: the self-biased
ladder has no headroom to give.

**What this means for the claim.** 021-final is certified on **all of S1–S8 at
the nominal corner**, with two paper techniques measured here and 78 % mismatch
yield. It is **not** a corner-robust or droop-tolerant design, and it must not
be presented as one. The next round's job is to make the B-branch current
mirror-referenced rather than threshold-referenced, which is the same fix the
originating campaign identified for this family and which §5.2 now has a
measured mechanism for.
