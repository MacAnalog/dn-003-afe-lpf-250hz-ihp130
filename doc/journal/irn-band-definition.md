# 2026-08-11 — IRN is band-limited AND input-referred: 0.5–200 Hz is part of the metric, and ngspice's own integrated total is over the wrong band

KIND: journal entry | type: procedural | status: live

**Symptom.** S5 — the number this whole campaign exists to move — is
`IRN(0.5–200 Hz) < 40 µVrms`, against a reference baseline of **50.18 µVrms**
(ledger `ref_fit`, deck `1ae5466ad00c`). Three different numbers can be computed
from the *same* noise run, and two of them are not S5:

| number | what it is | status |
|---|---|---|
| **50.18 µVrms** | `inoise_spectrum` integrated over **0.5–200 Hz** | **the spec metric** |
| whatever ngspice prints in `noise2` | ngspice's own integrated total, over **the whole sweep** — here 0.1 Hz to 1 kHz, because that is what the deck asked for | **not the metric.** Sitting in the same rawfile, one `setplot` away |
| `onoise_spectrum` integrated in band | output-referred noise | **not the metric** — the filter's gain is not 1 across the band |

The originating campaign measured the size of the first mistake directly: the
same trace read **55.59 µVrms** over 0.5–200 Hz and **1.76 mV** over
0.1 Hz–1 kHz — a factor of ~32 — *carried forward, not re-measured here.* The
arithmetic below says the same thing about this design.

**Mechanism.**

1. **Input-referred density diverges above the cutoff.** Input-referring divides
   the output noise by the transfer gain: `S_in(f) = S_out(f)/|H(f)|²`. Above fc
   a 4th-order response falls at 80 dB/decade while the device noise floor does
   not, so `S_in` *rises* steeply. This design measures **−48.43 dB at 1 kHz**,
   so referring the output floor to the input at that frequency multiplies the
   density by 10^(48.43/20) = **264×** in amplitude, **~7·10⁴×** in power. Any
   integral that reaches into the stopband is dominated by its own top end and
   reports the stopband's numerical floor, not the filter's noise.
2. **The band is therefore part of the definition, not a display option.** A
   noise number without its band is not a noise number. Comparing two candidates
   integrated over different bands compares their roll-off, not their noise.
3. **Output noise ≠ IRN even inside the band.** At the band edge the 4th-order
   Butterworth arithmetic gives |H(200 Hz)| = 1/√(1+(200/250)⁸) = **0.925**
   (−0.67 dB), so the last decade of the band is already de-weighted by ~8 % in
   amplitude. Referring is not a constant rescale.
4. **The lower edge matters too.** 0.5 Hz cuts the run before the 1/f tail and
   dc drift take over the integral; drop it to 0.1 Hz and you are scoring flicker
   and electrode-band content the filter was never specified against.

**Rule.**

1. **The harness computes the integral. Never quote a simulator's integrated
   total.** `lab.raw.integrate_noise(f, dens, f_lo, f_hi)` does a trapezoidal
   integral of density² over the band and **interpolates the density at the
   exact end points**, so the answer does not depend on where the sweep's grid
   points happen to land (`lab/raw.py:265-285`).
2. **The band is a constant in one place**: `lab.metrics.IRN_BAND = (0.5, 200.0)`,
   with its own comment saying why (`lab/metrics.py:37-41`). It is mirrored in
   `doc/target-spec.md` and the two are kept identical by the spec-sync lint.
   Change it in one place and `make check` fails — which is the intended
   behaviour, because changing the band changes the challenge.
3. **Refer at the source, not by post-hoc division.** The bench drives `vinp` /
   `vinn` from a single differential source `vsig` through a balun pair of
   controlled sources at ±0.5, so `vsig`'s amplitude *is* the differential input
   and a noise analysis referred to `vsig` is **directly** the differential
   input-referred noise (`lab/deck.py:11-20`). No gain trace to divide by, no
   place for a factor-of-2 to hide.
4. **The noise sweep may extend past the band; the integral may not.** The deck
   sweeps `noise … dec 10 0.1 1e3` deliberately — the shape above fc is
   diagnostic. That is exactly why the wrong number is always within reach, and
   why rule 1 is absolute.
5. **Any IRN quoted anywhere in this repo carries its band.** In a README, a
   plot title, a journal entry, a commit message: `IRN 0.5–200 Hz = xx.x µVrms`.
   A bare "IRN" is not reviewable.

**Corollary.** Per-device noise attribution obeys the same band: contributions
add **in power**, and `Σ IRN_k²` must reproduce the scorecard IRN *exactly* over
the same band. If it does not, the split is wrong — not the scorecard.

See also: [`phase-certificate-floor.md`](phase-certificate-floor.md) — the same
class of defect on the phase side, where a metric is computed on a band where
its own denominator has collapsed.

Provenance: `lab/metrics.py:37-41`, `lab/raw.py:265-285`, `lab/deck.py:11-20,
120-145`, ledger `ref_fit`.
