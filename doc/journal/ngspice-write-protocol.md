# 2026-08-11 — `write` saves only the current plot, and an explicit `save` starves `noise`: a multi-analysis deck must append per analysis and must not restrict its saves

KIND: journal entry | type: procedural | status: live

**Symptom.** The scorecard deck runs `op`, `ac` and `noise` in one `.control`
block and writes one rawfile. Two independent ways that rawfile came back wrong
— both **silently**, both scoring as a number rather than an error:

| defect | what the rawfile contained | what the scorecard read |
|---|---|---|
| single `write` at the end of the block | only the last analysis' plot | `S5` (or `S1-S4`) columns missing entirely |
| `write` after `noise` without `setplot noise1` | the **integrated** noise plot | no spectrum ⇒ IRN unusable |
| explicit `save v(...) ...` list in an ac+noise deck | the **ac plot twice** | **NaN** for S5 — not a failure, a hole |

**Mechanism.**

1. **`write` emits the CURRENT plot only.** ngspice keeps one plot per analysis
   (`op1`, `ac1`, `noise1`, `noise2`, …) and `write <file>` serializes whichever
   is current. A deck with three analyses and one `write` therefore ships one
   third of its results. The fix is `set appendwrite` plus **one `write` per
   analysis**.
2. **The `noise` command leaves the *integrated* plot current.** `noise` creates
   **two** plots: `noise1` = the spectral densities (`inoise_spectrum`,
   `onoise_spectrum`) and `noise2` = the integrated totals. It leaves `noise2`
   current, so a bare `write` after `noise` captures totals and no spectrum. The
   band-limited integral this repo specs is computed by the harness from the
   *spectrum* (see [`irn-band-definition.md`](irn-band-definition.md)), so the
   spectrum is the thing that must reach the file: `setplot noise1` first.
3. **Plot names are only deterministic when each analysis runs once.** The
   numbering is per-invocation. Any `while` / `repeat` loop that re-runs `op` or
   `ac` renumbers the plots, and `setplot noise1` then addresses **a different
   analysis' plot** without complaint. One deck = one pass through the analyses;
   sweeps are done by rebuilding the deck, never by looping inside `.control`.
4. **An explicit `save` list starves the noise analysis.** With a `save` line
   present, ngspice prints
   `Error: no data saved for Noise analysis; analysis not run`
   — and then **leaves the previous plot current**, so the appended write emits
   the ac plot a second time. The rawfile is well-formed, contains two plots,
   and the reader finds no noise data: S5 reads NaN instead of failing loudly.

**Rule.**

1. Every multi-analysis deck: `set appendwrite`, one `write` after **each**
   analysis, and `setplot noise1` before the noise write. This is what
   `lab.deck.ac_noise` emits — read it, do not re-invent it:

   ```
   .control
   set filetype=binary
   set appendwrite
   op
   write sim.raw
   ac dec 10 0.1 1e5
   write sim.raw
   noise v(voutp,voutn) vsig dec 10 0.1 1e3
   setplot noise1
   write sim.raw
   .endc
   ```
2. **The ac+noise deck carries no `save` line.** Restricting saves is a
   transient-deck optimisation only — a PSP103 device stores ~750 internal nodes
   per instance, which matters for a long strobed transient and not for an ac
   sweep. `lab.deck.SIGNAL_NETS` / `_save()` exist for that lane and must stay
   out of this one.
3. The noise analysis' input source **must** carry an `ac 1` spec, or ngspice
   aborts with `doAnalyses: ac input not found`. `lab.deck._stim_sine` therefore
   writes `... sin(0 ampl fin) ac 1` even for a transient deck.
4. **Readers assert on plot identity, not plot order.** `lab.raw.pick` selects a
   plot by its name (`ac analysis`, `noise spectral density curves`,
   `integrated noise`, `transient analysis`, `operating point`) so a mis-ordered
   or duplicated rawfile fails to resolve instead of resolving to the wrong
   trace.
5. Any new deck builder ships with the check that the rawfile contains **exactly
   the plots it claims**. A missing analysis must be an exception, never a NaN
   column — see [`silent-zero-rawfile.md`](silent-zero-rawfile.md).

Provenance: `lab/deck.py:74-145` (the `SIGNAL_NETS` note and `ac_noise`),
`lab/raw.py:pick`, `lab/ngspice.py:_FATAL`.
