# 2026-08-27 — Four things a hand-written small-signal model gets wrong at 1–3 nA, each measured on this cell

KIND: journal entry | type: semantic | status: live

Every device here runs 0.66–2.6 nA with `gm/I_D` = 22–28 V⁻¹ and `V_GS − V_TH`
from −25 to −227 mV. Four consequences, all measured, all of which a
strong-inversion reflex gets wrong by more than a rounding error. Numbers and
their provenance: `signoff/paper-draft/validation.md`.

**1. The gate charge sits on the BULK, not on a channel.** Measured on the
biquad-A input follower: `cgg` = 250.5 fF of which **`cgb` = 247.4 fF** and
`cgs` = **3.1 fF**. There is no inversion layer to terminate the gate field.
Bulk is tied to source in this cell, so all of it is gate-to-source capacitance
in every sense the circuit cares about — but a model that reads the `cgs` op-var
and leaves `cgb` on the bulk puts **81× too little** capacitance on the node.
That single capacitance is the whole 2 % gap between the `gm`-and-design-caps
closed form (254.8 Hz) and the full model (249.7 Hz), and it is also the origin
of both out-of-band zero pairs — proven by zeroing each capacitance family in
turn: killing `cgs` moves the poles back to 254.7 Hz and removes the zeros;
killing `cgd` changes nothing at all (it is **3.1 aF** — no channel, no Miller
path).

**2. Channel noise is shot noise, not `4kTγ·gm`.** The measured generator sits at
**0.87–1.04 × 2qI_D** across the signal devices — that is, at full shot noise.
Written against `gm` the same data reads 0.72–0.82 × `4kT·gm`, and the two
columns differ by exactly `n/2` as they must — a consistency check, not a second
measurement. *(Corrected 2026-08-31: this read 0.63–0.72 × until the channel was
put back together out of the two generators the model splits it into — see
[a-generator-name-is-not-its-physics](a-generator-name-is-not-its-physics.md).
The apparent shortfall was never shot-noise suppression.)*

**3. The channel arrives as TWO generators, and one of them is misleadingly
named.** The model reports `(1 − c²)·S_id` as `idid` and injects the remaining
`c²·S_id` drain-to-source under the name `igig`, with `c` = 0.55 here. Both are
the same generator at the same port; only their sum is `2qI_D`. Together they
are **89 % of the IRN power** against 11 % for flicker, and a model that takes
`idid` for the whole channel is **1.4 dB optimistic on IRN**. *(Corrected
2026-08-31: this entry previously read `igig` as gate-leakage shot noise. There
is no gate leakage in this cell — the gate current is exactly zero and the
model's actual gate-leakage generators `igs`/`igd` are identically zero on these
thick-oxide devices. See
[a-generator-name-is-not-its-physics](a-generator-name-is-not-its-physics.md).)*

**4. Distortion currents from the two halves add IN PHASE.** Under differential
drive the N-half device's gate excursion is opposite to its P-half twin's *and*
its transimpedance to the differential output is opposite; the two sign flips
cancel. Summing only one half under-predicted HD3 by **21 dB**. Use the exact
Bessel ratio `2·I₃(a)/I₀(a)` rather than its `a³/24` truncation — they part
company above `a ≈ 0.3`, which this cell reaches at 100 Hz and 43.75 mVpp.

**And one structural result that only the symbolic form shows.** Branch stacking
does not give `H(s) = H_A(s)·H_B(s)`. The exact denominator is
`D_A·D_B + κ·s²` with `κ = 2·C1a·C2b·gm_br·gm_ib` — the loop through the
current-reuse bridge — and κ is **11.78 %** of the quartic's own `s²`
coefficient. It is what maps the isolated-stage Q's (2.10, 0.46) onto the
filter's actual, near-Butterworth pole pairs (0.543, 1.307). Sizing the two
sections independently to the Q's you want does not give you those Q's.
