# 2026-08-11 — dc hints are `.nodeset`, never `.ic`, and a hint on a subckt node must be instance-qualified or it is a silent no-op

KIND: journal entry | type: procedural | status: live

**Symptom.** Two different ways of giving the dc solver a hint, two different
silent failures, both of which produce a rawfile that scores:

| what was written | what ngspice did | how it looked |
|---|---|---|
| `.nodeset v(vout_1)=1.25` (unqualified, node lives inside `xdut`) | printed `Warning : Nodeset on non-existent node` and continued | the hint had no effect; the op point landed wherever it landed, and nothing in the scorecard said so |
| `.ic v(xdut.vout_1)=1.25` | held the node **clamped through the operating point** | a clean, converged, **latched** dc solution that produced a plausible ac response and a **PASS** |

**Mechanism.**

* A **`.nodeset` is a hint**: ngspice uses it as the initial guess for the dc
  solve and the solver is free to leave it. If the guess was wrong, the solver
  walks away and the answer is still the circuit's answer.
* An **`.ic` is a clamp**: the node is *held* at the value while the operating
  point is computed. For a circuit with more than one dc basin — which any
  follower chain with a shunt-feedback loop and no CMFB is — that is not a hint,
  it is an instruction to report the basin you asked for. This circuit has a
  latched basin. Clamp into it and you get a converged op point, a low-pass-
  looking ac response, and a scorecard that says PASS about a state the circuit
  will not enter on its own.
* **Node names inside a subckt must be instance-qualified**: `v(xdut.vout_1)`,
  not `v(vout_1)`. The unqualified form does not error and does not stop the
  run; it emits one warning line among the PDK's own output and is a no-op.
  A no-op hint is indistinguishable from a hint that worked, unless you check
  the resulting node voltages.

**Rule.**

1. **`.nodeset` only. `.ic` is banned in this repo's dc-solve path.** If a
   design needs a clamp to converge, that is a finding about the design, not a
   deck setting. `lab.deck._core` writes:

   ```
   .nodeset v(xdut.vout_1)=1.25 v(xdut.vout_2)=1.25 v(voutp)=1.25 v(voutn)=1.25
   ```
   with the value taken from `lab.config.VOCM`, i.e. from the design's own
   common-mode plan ([`all-p-followers.md`](all-p-followers.md)), not from a
   number someone liked.
2. **Every hint on an internal node carries its instance prefix.** Decks are
   built, never hand-edited (`lab/deck.py`), so the prefix is applied once in
   the builder and cannot rot per-experiment.
3. **A hint is not evidence.** Read back the op point and confirm the node
   actually sits where the hint suggested; a design that only lands mid-rail
   when hinted has a dc problem that the ac response will not show you.
4. Grep the stdout for `Nodeset on non-existent node` and treat it as a
   **failure**, not a warning: it means a hint the deck believed it was giving
   was never given.

Provenance: `lab/deck.py:60-75`, `lab/config.py:VOCM`. Related:
[`mirror-unit-must-match.md`](mirror-unit-must-match.md) (the other way this
circuit lands in a wrong-but-plausible dc state) and
[`silent-zero-rawfile.md`](silent-zero-rawfile.md).
