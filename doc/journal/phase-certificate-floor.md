# 2026-08-11 — A phase certificate is only meaningful where the magnitude is: score `ph_max` above a −100 dB floor, or it aliases into fake lags

KIND: journal entry | type: procedural | status: live
[carried forward from the originating campaign — the fake-lag numbers below were measured there, not here. What is measured here is the reference's own certificate and its step margin.]

**Symptom.** The S1 certificate — "two true biquads", asserted as maximum
unwrapped phase **lag** ≥ 330° — could be *faked*. In the originating campaign,
computing `ph_max` over the whole ac sweep turned ±180° phase steps taken across
a ~−107 dB parasitic feed-through plateau into lags of **478°** and **494°** on
designs whose true lags were **321.4°** and **329.8°**. A fourth-order response
cannot lag more than 360°: the certificate was reporting a number that is
physically impossible, and reporting it as a **pass**.

| quantity | value | where from |
|---|---|---|
| feed-through plateau of the originating design | ~−107 dB, beyond ~4 kHz, at 10 pts/decade | carried forward |
| fake lags produced | 478°, 494° | carried forward |
| true lags of those same runs | 321.4°, 329.8° | carried forward |
| worst in-band step measured there after the fix | 178.8° — **1.2° from aliasing** | carried forward |
| runs whose answer the floor changed | 156 of 606 archived | carried forward |
| **this repo's reference certificate** | **`ph_max_deg` = 346.43°** | ledger `ref_fit`, deck `1ae5466ad00c` |
| **this repo's reference worst in-band step** | **`ph_step_deg` = 46.94°** (133° of margin) | ledger `ref_fit` |

**Mechanism.** `angle()` returns the phase modulo 360°, so the raw step between
two adjacent frequency points is only known as `d ∈ (−360°, +360°)`. The
unwrapper corrects it by `acc -= 360 · round(d / 360)`, i.e. it adds a full turn
**only when `|d| > 180°`**. Therefore:

* a raw step of, say, −204.7° is corrected to +155.3° — unambiguous, costs
  nothing;
* a raw step of −179° is **left alone** — and a *true* progression of **+181°**
  arrives in the data as exactly that same −179°. The two are indistinguishable
  from the samples. Recording +181° of advance as 179° of lag mis-states the
  accumulated lag by a whole **360°**.

**Only steps whose magnitude is below 180° can alias; larger ones cannot.**
Where the response is real, a dense sweep progresses far less than 180° per
point and every correction is unambiguous. Where the response has collapsed into
a parasitic feed-through plateau, |H| is at the numerical floor, consecutive
phase samples are effectively uncorrelated, raw steps pile up near ±180°, and
the accumulator walks off by whole turns. The lag is then a property of the
sweep grid, not of the circuit.

**Rule (two fail-closed guards, both in the harness, neither optional).**

1. **Magnitude floor.** `ph_max_deg` is scored **only** on points where
   `|H| ≥ PH_FLOOR_DB = −100 dB` relative to dc
   (`lab/metrics.py:53`, `lab/raw.py:230`). Empty band ⇒ **NaN**, never a
   number.
2. **Resolvability guard.** `lab.raw.max_phase_step_deg` reports the largest
   unwrap-corrected step inside that scored band, logged as the soft column
   `ph_step_deg` against `PH_STEP_GUARD_DEG = 150°`
   (`lab/metrics.py:57`). The floor **alone is not enough** — the originating
   campaign measured a legal-looking in-band step of 178.8°, 1.2° short of
   aliasing.
3. **A NaN or a guard trip means re-run the ac analysis denser. Never loosen
   the guard.** The scorecard deck sweeps `ac dec 10` because that matches the
   grid the certificate was defined on (`lab/deck.py:ac_noise`); density is the
   knob, the threshold is not. `lab.metrics.ph_max_hires` exists for the
   diagnostic re-run.
4. When a certificate is disputed, **dump the evidence, do not argue it**:
   f, |H| in dB, raw phase, unwrapped phase, and the step size per point. The
   failure is then visible instead of inferred.

**General lesson, the one worth carrying anywhere:** *a phase metric is only
meaningful where the magnitude is.* Any metric derived from a ratio must be
scored on the band where the numerator exists.

**Open procedural proposal.** Guard 2 is currently *reported*, not enforced:
`evaluate()` logs `ph_step_deg` but does not NaN the certificate when it exceeds
150°. Making it fail-closed (return NaN from `ph_max_deg`, as the originating
harness did) is the correct end state — a soft column is not a guard, it is a
column someone eventually stops reading.
Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10; queued
in `doc/proposed-lab-fixes.md`.

See also: [`irn-band-definition.md`](irn-band-definition.md) (the same
band-limits-are-load-bearing failure, on the noise side).
