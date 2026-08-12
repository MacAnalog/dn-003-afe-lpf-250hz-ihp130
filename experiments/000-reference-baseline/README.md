# 000 — reference baseline: the expert SSF topology in SG13G2

**Status: CLOSED 2026-08-11. Certified and frozen in `decks/reference/`.**

| | |
|---|---|
| **Paper(s)** | none — this is the carried-forward expert topology, not a technique |
| **Hypothesis** | The expert two-biquad super-source-follower low-pass ports to SG13G2 at nano-amp bias and can be re-sized to the full shape box (250 Hz, two true biquads, 0 dB flat, no peaking) without changing the circuit idea. Falsified if any shape line is unreachable at any sizing. |
| **Verdict** | **CONFIRMED, with one forced structural change.** Every shape line passes. The change: both input followers must be **p-type**, because this PDK has no isolated NMOS (§2). |

This experiment exists because the challenge is defined *relative to a
baseline*, and the originating campaign's baseline cannot come with it — it was
a vendored deck of a proprietary technology. Something has to play that role
here, and it has to be earned rather than asserted: same topology, same
measurement contract, re-sized until it sits on the same shape box.

## 1. Result — the numbers every candidate is scored against

Measured on the frozen deck (`decks/reference/lpf_tb.sp`), nominal corner, 27 °C,
VDD = 1.5 V. Ledger tag `ref_fit`.

| # | spec | target | **measured** | verdict |
|---|---|---|---|---|
| S1 | max unwrapped phase lag | ≥ 330° | **346.43°** | PASS |
| S1c | \|H\| at 1 kHz | ≤ −48 dB | **−48.43 dB** | PASS |
| S2 | cutoff | 250 Hz ± 2 % | **250.00 Hz** | PASS |
| S3 | passband gain | \|dc\| ≤ 0.2 dB | **−0.0047 dB** | PASS |
| S4 | peaking | ≤ 0.2 dB | **0.023 dB** | PASS |
| S5 | IRN 0.5–200 Hz | < 40 µVrms | **50.18 µVrms** | **FAIL — by design** |
| S6 | filter-core power | < 50 nW | **12.07 nW** (8.04 nA) | PASS |
| S8 | ≥ 2 papers combined | ≥ 2 | 0 | n/a — not a technique |

Report-only: total drawn capacitance **98.01 pF**; 16 transistors + 6 capacitors.

S5 failing is the point. **50.18 µVrms is the number the challenge exists to
beat**, and the −20.3 % it demands (50.18 → < 40) is the same order as the
−28 % the originating campaign faced from its own baseline. That the two
baselines land within 10 % of each other (50.18 here, 55.59 there) on completely
different silicon is the strongest evidence available that the port is faithful:
nothing about the noise mechanism was lost in translation.

## 2. The forced structural change — and how it was found, not assumed

The originating design **alternated** an n-input biquad with a p-input biquad.
That is not decoration: the two |Vgs| level shifts have opposite sign, so the
output common mode returns to the input's and stages cascade identically.

It only works if both followers have **bulk tied to their own source**. SG13G2
has no deep-n-well NMOS, so an n-channel device's bulk *is* the shared
p-substrate. A gate-driven source follower whose bulk sits at the rail has, in
weak inversion, dc gain of exactly **1/n** — because gmb = (n−1)·gm, so
gm/(gm+gmb) = 1/n. For these devices n ≈ 1.38.

Measured directly, stage by stage, on the faithful alternating redraw:

| stage | follower | bulk | dc gain |
|---|---|---|---|
| A | n-type | substrate (forced) | **−2.328 dB** |
| B | p-type | its own source | **−0.003 dB** |

−2.328 dB against an S3 box of ±0.2 dB is an order of magnitude over, and **no
re-sizing recovers it**: 1/n is a process constant, not a geometry. Making both
stages p-type restores exact unity gain — re-measured at −0.0047 dB for the
whole 4th-order filter — and with it the *self-referenced gain* that the
candidate family's mismatch yield depends on.

The cost is real and is paid in headroom: the common mode now climbs one |Vgs|
per stage instead of cancelling. It is absorbed by placing the input common mode
low (0.25 V) so the output lands at ~1.25 V with headroom on both rails, which
is what sets VDD = 1.5 V for this cell.

Recorded as [doc/journal/nmos-bulk-tie.md](../../doc/journal/nmos-bulk-tie.md)
and [doc/journal/all-p-followers.md](../../doc/journal/all-p-followers.md).

## 3. Method

1. **Device flavour first.** `sg13_hv_*` (thick oxide) over `sg13_lv_*`, decided
   on measurement, not on analogy — see [doc/pdk-notes.md](../../doc/pdk-notes.md).
   The decisive number: an lv n-channel device at W = 17 µm / L = 8 µm already
   carries **2.5 nA at Vgs = 0**, so it cannot be biased at 1 nA at all, and its
   gm/gds is ~70 against ~2900 for the hv device at the same geometry.
2. **Bias by construction.** One ideal reference current into a real mirror whose
   diodes are built from the design's *own* unit geometry at m = 1, so a bias
   device drawn at m = k carries exactly k·iref and the core current is exact
   rather than fitted. At iref = 1 nA the core draws 8.04 nA — the intended 8
   units, to 0.5 %.
3. **Shape by search, not by hand.** `lab.shape.fit_caps` runs Nelder–Mead over
   log-capacitance against a constraint cost (fc, stopband, peaking, dc). 91
   iterations, 77 s. The cost is deliberately a *constraint*, not a figure of
   merit: a baseline should be **on spec**, not optimal, or the yardstick
   flatters whatever it is compared against.

## 4. Why `a1000 ≤ −48 dB` is not an extra requirement

It is the same requirement as "no peaking, 4th order", written numerically. A
maximally flat 4-pole response at 4× its cutoff is exactly 4⁻⁴ = **−48.16 dB**.
So the stopband line is what stops the optimiser from buying flatness with a
slower roll-off. The fit lands at −48.43 dB: Butterworth, with 0.27 dB to spare.

## 5. Build sheet

`decks/reference/build-sheet.md` (generated). Capacitors, in pF:
c1_a 29.468 · c2_a 6.221 · c1_b 11.453 · c2_b 9.946 → **98.01 pF** total.

## 6. What this hands forward

- The baseline number: **IRN 50.18 µVrms**. Every candidate's win is what it
  subtracts from that, at equal shape.
- The all-p follower constraint, which is **not** free for the candidate family:
  the branch-stacking mechanism needs an n-type follower to close its dc ladder.
  That collision is experiment [020](../020-novel-topologies/)'s central problem.
- The observation that the bias devices, not the followers, are where the noise
  lives — carried forward from the originating campaign and consistent with the
  baseline measured here.
