# NNN — <technique name>

**KIND: experiment.** Copy this directory to `experiments/NNN-<technique>/`,
fill it in top to bottom, and add one row to `doc/experiment-log.md`.
`make lint` requires the `**Paper`, `**Hypothesis` and `**Verdict` rows below
to exist, and requires this directory to appear in the experiment log.

**Paper(s):** `<handle>` (+ `<handle>`) — cite by the handle in `pdf/INDEX.md`,
never by filename. S8 needs **≥ 2 papers combined**, and the mechanism of each
must be visible in the netlist, not just in this README.

**Hypothesis:** one falsifiable sentence with a number in it, written *before*
the first simulation. It must be possible for the measurement to say "no".

> Template: *"Applying \<mechanism\> to \<the specific devices/nodes\> cuts
> IRN(0.5–200 Hz) from 50.18 µVrms to below X µVrms at unchanged fc, dc gain,
> peaking, stopband and core current, at a cost of ≤ Y pF of total
> capacitance."*

Bad hypotheses to avoid: "improves noise" (unfalsifiable), "should be better
than the reference" (no number), "reduces the output conductance of the
internal node" (in weak inversion the driving-point conductance is pinned at
`gms = gm + gmb = I_D/V_T` exactly — the mechanism does not exist; see
`doc/design-reference.md`).

**Control:** name it explicitly. **If any capacitor value moves, the control is
the same capacitance re-allocation without the technique** — otherwise the
experiment has measured a cap re-shuffle. If bias current moves, the control is
the same current at the reference topology. Every batch also carries the
untouched reference baseline as its first row, so the yardstick is measured in
the same session, on the same PDK, with the same simulator build.

**Prediction (before running):** fill in the cells you expect, so the table
below can contradict you.

| metric | reference | predicted | why |
|---|---|---|---|
| irn_uv | 50.18 | | |
| fc_hz | 250.00 | | |
| ph_max_deg | 346.43 | | |
| p_core_nw | 12.07 | | |
| c_total_pf | 98.01 | | |

## Findings

Tables or plots. Prose is interpretation only. Paste the `lab.metrics.table`
output verbatim — keeper numbers **graduate** from `runs/ledger.ndjson` into
this README (that promotion is the semantic write; the ledger is git-ignored
local observability).

| cell | fc_hz | dc_db | peak_db | a1000_db | ph_max_deg | irn_uv | p_core_nw | c_total_pf | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reference | 250.00 | −0.0047 | +0.0230 | −48.43 | 346.43 | 50.180 | 12.070 | 98.01 | PASS |
| control | | | | | | | | | |
| variant | | | | | | | | | |

Report the soft columns too when they moved (`c_total_pf`, `idd_total_na`,
`i_core_na`, `onoise_uv`, `ph_step_deg`) — total capacitance is **reported,
never specced**, and `ph_step_deg` is what says whether the S1 certificate is
resolvable rather than one sample from aliasing.

**Stopband check:** state `a1000_db` explicitly for every row. Stopband is never
traded silently; a candidate that buys noise with order is not a candidate.

**THD (S7):** only if the cheap scorecard already passes the hard box —
`lab.metrics.gate` refuses otherwise, and that refusal is the rule, not an
obstacle. Iterate with the coherent-FFT path; any number called final comes
from the sign-off method in `doc/benches.md`, at fin = 50 Hz and 175 mVpp
differential (`THD_AMPL = 87.5 mV` on the differential source).

**Run evidence:** ledger tags used here — `<tag>`, `<tag>`, … (query with
`python scripts/runs.py --exp NNN`). Every number above must be re-derivable
from one of them.

## Verdict

**Verdict:** PASS / FAIL / PARTIAL — one line, naming the hypothesis and
whether the measurement confirmed or refuted it, with the deciding number.

A refuted hypothesis is a result. Record *why* it failed in enough detail that
nobody re-runs it: which term dominated, which constraint bit, what the
measurement said that the derivation did not.

**Next:** what this sets up — the follow-up experiment, the combination
candidate, or the closed door and its reason.

**Journal:** if the lesson transfers beyond this experiment, add
`doc/journal/<slug>.md` with a `type: semantic|procedural | status: live`
header and an index row in `doc/journal.md`. If it contradicts an earlier
entry, mark that entry `[superseded <date> — …]`; do not delete it.
