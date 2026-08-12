# 2026-08-12 — Mismatch yield is a BIAS-device area problem; phase margin is a SIGNAL-path one. Grow them separately.

KIND: journal entry | type: semantic | status: live

**The symptom.** The unstacked VDD/2 cell passed all seven measurable spec lines
nominally and returned a **12 %** mismatch all-pass yield (σ(fc) 8.89 Hz on a
±2 % box). The obvious fix — make every device bigger, since
σ(V_th) ∝ 1/√(W·L) — works on the noise and then fails the design:

| all-device gate area | ph_max | MC all-pass |
|---|---|---|
| ×1 | 343.9° | 12 % |
| ×2.56 | 334.9° | 39 % |
| ×5.76 | **322.5° — S1 FAIL** | — |

**The separation.** The two effects have different owners:

* **fc spread comes from the BIAS devices.** In weak inversion
  `I ∝ exp(V_th/(n·U_T))`, so `σ(I)/I = σ(V_th)/(n·U_T)` with n·U_T ≈ 40 mV — a
  few mV of threshold mismatch is a **>10 % current spread**, and fc rides on it.
* **Phase loss comes from the SIGNAL path.** Longer/wider signal devices mean
  more gate–drain capacitance feeding the path that arrests the phase lag (the
  same mechanism that disqualified 020B-frozen at 320.7°).

Bias-device gates sit on `vbn`/`vbp` — quiet dc rails. Growing **only** them
therefore buys the whole yield and spends none of the phase:

| bias gate area | ph_max | IRN µV | THD | MC all-pass | σ(fc) |
|---|---|---|---|---|---|
| ×1 | 343.9° | 36.55 | −44.86 | 12 % | 8.89 Hz |
| ×4 | 343.4° | 35.22 | −44.88 | 50 % | 4.47 Hz |
| ×9 | 343.0° | 34.97 | −44.76 | 72 % | 3.24 Hz |
| ×16 | 342.6° | 34.91 | −44.70 | 78 % | 3.04 Hz |
| ×36 | 341.8° | 34.85 | −44.64 | **82 %** | 2.61 Hz |
| ×81 | 340.7° | 34.83 | −44.62 | 87 % | 2.40 Hz |

**3.2° of phase across an 81× area range** — i.e. none — while yield goes 12 % →
87 % and σ(fc) tracks 1/√area exactly.

**The lever is NOT monotone in yield, and that is the trap.** It buys σ(fc) but
it does slowly cost phase margin, so once the *nominal* phase margin is thin the
`ph_max` line becomes the binding one and the all-pass yield falls off a cliff.
Measured on the branch-stacked cell, whose nominal margin is only ~2.5°:

| bias area | ph_max | MC all-pass | binding line |
|---|---|---|---|
| ×1 | 332.2° | 68 % | ph_max 79 % |
| **×9** | **332.8°** | **84 %** | ph_max 87 % |
| ×36 | 330.8° | **50 %** | **ph_max 54 %** |

So the optimum depends on the cell's own phase margin: **×9 for the stacked cell
(2.5° of margin), ×36 for the unstacked one (13.9°)**. Do not carry a single
number across designs — measure the curve, and stop where `ph_max`'s per-line
yield starts falling faster than `fc_hz`'s rises.

**Sizing rule that follows.** Report the per-line yields, not just the all-pass
number. The all-pass figure hides which line is binding, and here that line
changes identity (fc → ph_max) partway along the very sweep meant to improve it.

**Cost to keep in view.** At ×81 the bias gate area reaches 103 680 µm², already
42 % of the capacitor area at 1 fF/µm². Bias area is cheap next to 245 pF of MIM,
but it is not free, and past ×36 it is buying ~5 points of yield per doubling.
