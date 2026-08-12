# 2026-08-11 — The bias mirror's diodes must be built from the design's own unit geometry at m = 1, or every branch current is scaled by a W/L ratio and the filter still looks like a filter

KIND: journal entry | type: procedural | status: live

**Symptom.** The reference bench biases the core from **one ideal reference
current** into a real n/p mirror pair, and every bias device in the core is an
integer multiple `m` of that unit (per side: 2 units at each biquad output ⇒
8 nA total, 8.04 nA measured, `ref_fit`). Building the mirror's **diode-connected
devices with a convenient geometry instead of the design's own unit geometry**
gave a run that:

* converged;
* produced a monotone low-pass ac response;
* returned a finite `fc`, a finite `dc_db`, a finite `ph_max_deg` and a finite
  IRN — i.e. **a full scorecard**;
* and was wrong in every one of them, because each branch carried
  `iref × (W/L)_diode / (W/L)_unit` instead of `iref × m`.

The tell, when you finally look at the operating point rather than the
scorecard: **biquad A's internal node rails**, and its shunt-feedback device is
**switched off**. The stage degenerates to a single-pole follower; the cascade
still rolls off, so the ac plot reads as a plausible, merely *mis-tuned*
low-pass. Nothing in a magnitude-only scorecard distinguishes "mis-tuned filter"
from "one stage is dead".

**Mechanism.** A current mirror copies `I_D` in proportion to `(W/L)·m` at equal
`V_GS`. Weak inversion makes this worse in both directions: the copy ratio is
still geometric, but `I_D ∝ exp(V_GS/(n·U_T))`, so a geometry mismatch that would
be a 20 % error in strong inversion becomes a large multiplicative error in the
branch current, and the resulting `V_GS` shift is spent by the *whole* mirror
tree, not just one branch. Starve or flood one node and the device that is
supposed to hold it in saturation leaves saturation; with no CMFB, nothing pulls
it back.

**Rule.**

1. **The mirror is built from the design, not alongside it.** `lab.deck._bias`
   takes the diode geometries from the `Design`'s **own** bias unit devices
   (`bias_a_int` / `bias_b_int` for the n-type unit, `bias_a_out` / `bias_b_out`
   for the p-type) and instantiates them at **`m = 1`**:

   ```
   iref  vdd_top vbn <iref>
   xmbn  vbn vbn 0 0        <NCH> w=<unit.w> l=<unit.l> ng=<unit.ng> m=1
   xmbp  vbp vbn 0 0        <NCH> w=<unit.w> l=<unit.l> ng=<unit.ng> m=1
   xmbpd vbp vbp vdd_top vdd_top <PCH> w=<unit.w> l=<unit.l> ng=<unit.ng> m=1
   ```
   A bias device drawn at `m = k` then carries exactly `k · iref`, by
   construction. **Bias current becomes a multiplicity, not a hand calculation.**
2. **`m` is the only bias knob.** Changing a bias device's `w`, `l` or `ng`
   without changing the mirror unit breaks the copy ratio. If a candidate needs a
   different bias-device geometry, it needs a different *unit*, and the mirror
   moves with it.
3. **The mirror sits on `vdd_top`, ahead of the core probe `vflt`** — it is a
   *reference*, excluded from S6 by definition. Keeping the reference ideal stops
   a reference design choice from contaminating a filter comparison
   (`lab/deck.py:_core`, `_bias`).
4. **Never certify a bias change from the ac response.** Read the operating
   point: per-branch currents against `m · iref`, and every core device's `V_DS`
   against its `vdsat`. `lab.deck.op_only` + `lab.metrics.op_table` exist for
   exactly this and cost one cheap run.
5. **A railed internal node must be a loud failure.** A plausible-looking
   low-pass with a dead stage is the most expensive kind of wrong answer in this
   harness, because it survives every magnitude check
   (cf. [`silent-zero-rawfile.md`](silent-zero-rawfile.md)).

**Open procedural proposal.** Add an op-point invariant to `evaluate()`: every
core device `|V_DS| ≥ 3·|vdsat|` and every branch current within a few percent
of `m · iref`, raised as a violation rather than reported as a column.
Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10; queued
in `doc/proposed-lab-fixes.md`.

Provenance: `lab/deck.py:34-56` (`_bias`, with this trap recorded in its
docstring), `decks/reference/build-sheet.md`, ledger `ref_fit` (8.04 nA core).
