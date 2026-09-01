# 2026-08-31 — A noise generator's NAME is not its physics: `igig` is channel noise, not gate leakage

KIND: journal entry | type: semantic | status: live

Corrects traps 2 and 3 of
[weak-inversion-model-traps](weak-inversion-model-traps.md), which are also the
two numbers `signoff/paper-draft/` published in its §5.2 and §5.3 before
2026-08-31. Nothing measured was wrong; what was wrong was the name we read off
the simulator and believed.

**The claim that failed.** The compact model reports a noise generator called
`igig`, and the pack reported it as *gate-leakage shot noise* carrying 27 % of
the IRN power — with the note that a hand model omitting it is 1.4 dB
optimistic. The reviewer's question was the obvious one: **why is there gate
leakage at all when every device is thick oxide?**

**There is not.** Three measurements, in the order that settles it:

1. **The gate current is exactly zero** — not small, zero — on a device biased
   where this cell biases them (`i(gate)` = 0 at 6.39 nA of drain current).
   The PDK card sets every gate-current pre-factor to zero for both thick-oxide
   flavours (`iginvlw = igovw = igovdw = 0`), which is the right modelling call
   at `t_ox` = 7.43 nm n-channel / 6.95 nm p-channel: direct tunnelling there is
   twenty orders below the branch current.
2. **The model's real gate-leakage generators are `igs` and `igd`, and both are
   identically zero**, which follows from (1) — their PSDs are `2q·I_gs` and
   `2q·I_gd`. They are *not* named `igig`.
3. **`igig` is the channel.** The model splits the channel thermal noise by its
   correlation `c` with the induced gate noise: `idid` carries `(1 − c²)·S_id`,
   and the remaining `c²·S_id` is injected drain-to-source through an internal
   noise node under the name `igig`. Added back together they measure
   **1.0032 × 2qI_D** on a single device and 0.87–1.04 × across the cell — the
   full weak-inversion shot noise. `idid` alone is 0.70 of it, and `c` = 0.55.

Reproduce with `signoff/paper-draft/scripts/gate_leakage_probe.py`, which runs
one device with a resistive load and asserts all three. It is deliberately not
this cell: the result belongs to the device model and the PDK card, so neither
the topology nor the transimpedance solve can be blamed for it.

**What this changes, and what it does not.** No measured number moved. The IRN
total, the generator-sum closure and the per-role ranking are untouched, and so
is the design conclusion that capacitance belongs at biquad A. What changed is
the physics the numbers were said to show:

* channel thermal noise is **89 %** of the IRN power, not 62 %;
* `S_i/2qI_D` over the signal devices is **0.87–1.04**, not 0.63–0.72 — the
  channel *is* full shot noise, exactly as the weak-inversion derivation says,
  and the apparent shortfall was 30 % of the generator sitting under another
  name;
* the 1.4 dB penalty is real but has a different cause: it is what a hand model
  loses by taking `idid` for the whole channel. A hand model that writes
  `S_id = 2qI_D` needs no second term at all.

**The lesson, which is the reason this is a separate entry.** The port
identification in `scripts/noise_analysis.py::identify_port` had already
measured the truth and it was overruled by prose: `igig` selects a **drain**
port on 10 of the 12 signal devices, by 1.3–8.4 dB over the best gate port. A
generator named for the gate that measures at the drain is not a gate
generator. Two habits follow:

* **When a generator's contribution surprises you, read the model source before
  naming the mechanism.** The name is an author's label on a term, not a
  statement about physics; `igig` labels the source that *drives* the induced
  gate noise construct, and where its noise ends up is a different question
  from what it is called.
* **A measured port assignment outranks the label.** When the two disagree, the
  measurement is the finding — the disagreement was visible in the pack's own
  ranking table for a week before anyone read it as a contradiction.

Provenance: `signoff/paper-draft/scripts/gate_leakage_probe.py`,
`signoff/paper-draft/validation.md` §5.2 and §5.3,
`signoff/paper-draft/theory.md` §3.2.
