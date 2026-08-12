# 2026-08-11 — ngspice exits 0 after a failed operating point and leaves a rawfile full of zeros: the runner must read stdout, because the return code is not a verdict

KIND: journal entry | type: procedural | status: live

**Symptom.** A deck whose dc operating point failed to converge returned
**exit code 0**. The rawfile existed, was well-formed, had the expected plots and
the expected vector names — and was **filled with zeros**. Downstream that is not
an error; it is a measurement. A zero-filled ac plot yields a finite `dc_db`, a
finite `fc`, a phase array, a noise density: a complete scorecard, produced by a
circuit that was never solved.

**This is the single most expensive failure mode in this harness**: a silent
zero-filled result that scores as a PASS. Everything downstream — the ledger row,
the experiment README that graduates from it, the ranking a candidate wins on —
inherits it, and nothing about it looks wrong.

**Mechanism.** ngspice reports analysis failures on stdout and keeps going: the
`.control` block continues, `write` still runs, and the process ends normally.
The batch return code reflects "did the interpreter finish", not "did the
analysis succeed". The failure text is the only signal, and it is one line among
the PDK's own model-loading chatter.

**Rule.**

1. **The runner scans stdout for fatal strings and raises `SimError`.** Return
   code and rawfile existence are necessary, not sufficient
   (`lab/ngspice.py:_check_convergence`, `_FATAL`):

   ```
   "doAnalyses: iteration limit reached"
   "Transient solution failed"
   "singular matrix"
   "no such vector"
   "Unknown model type"
   "could not find a valid modelname"
   ```
2. **Fail loudly, never NaN-quietly.** Three checks, in order, all raising:
   non-zero return code → `SimError`; no rawfile → `SimError`; fatal string in
   stdout → `SimError`. A run that cannot be trusted must not reach the ledger,
   because a ledger row is evidence.
3. **`Unknown model type psp103va` is in that list for a reason.** The IHP MOS
   models are PSP 103.6 Verilog-A compact models loaded as **OSDI** objects; a
   stock ngspice cannot simulate this PDK at all and says so with exactly that
   line. Without the scan, the lane being wrong would present as a design being
   bad (`lab/ngspice.py:9-12`, `lab.ngspice.preflight`, `make doctor`).
4. **Every new fatal string found in the wild is appended to `_FATAL` in the
   same session it is found**, with a ledger tag in the commit message. The list
   is memory, and it only grows by someone getting burned.
5. **Sanity-check the physics, not just the plumbing.** A converged run whose
   core current, node CM or device saturation is impossible is the same class of
   defect arriving by a different door — see
   [`mirror-unit-must-match.md`](mirror-unit-must-match.md) and
   [`nodeset-not-ic.md`](nodeset-not-ic.md).

**Corollary for anything that parses simulator output.** A parser's job is to
*refuse*, not to cope. `lab.raw.pick` resolves a plot by name and raises when it
is absent, rather than falling back to "the first plot"; a missing analysis then
surfaces as an exception instead of a NaN column
([`ngspice-write-protocol.md`](ngspice-write-protocol.md)).

Provenance: `lab/ngspice.py:29-31, 55-70, 107-128, 135-155`.
