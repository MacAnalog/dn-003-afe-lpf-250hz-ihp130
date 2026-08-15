# 2026-08-15 — Screen one axis at a time before the PVT box: `lab.corners.AXES` (9 points) tells bias from headroom, which the 22-point `REDUCED` set cannot; plus three harness fixes from the same session

KIND: journal entry | type: procedural | status: live

**The gap.** Every off-nominal row of `REDUCED` moves two or three axes at once
(process × temperature × rail vertices, plus process at the low rail). A cell
whose ladder current is threshold-referenced and a cell that merely runs out
of headroom at 1.35 V both read "1/22, fails S2". The sign-off set was filed
under "supply limitation" for a week on that reading; the process-only rows
(fc 13.6 → 524 Hz at nominal V/T on A-minarea) were never in the screen.

**The fix.** `lab.corners.PROCESS_ONLY` / `SUPPLY_ONLY` / `TEMP_ONLY` and
`AXES = (NOMINAL,) + …` (9 points). Run `AXES` first — it is one wave on the
native lane — and read the three axes separately: a process-only fc spread is
bias; a rail-only failure with dc gain moving is headroom; temperature-only fc
∝ 1/T at constant current is the reference's job (`LPF_BIAS_ALPHA=1`).
Experiment-side, `experiments/023-replica-bias/common.py::headroom()` is the
op-only companion (~10 sims per arm) that names the device that leaves
saturation at each corner.

**Three more, same session:**

* **Native-lane worker caps.** `lab.corners.MAX_WORKERS` and `lab.mc.WORKERS`
  were 6 (a Docker-startup limit) on every lane; on the native lane they now
  follow `lab.parallel.jobs()` (`LPF_JOBS`, default cpu−2). Keep `LPF_JOBS`
  ≈ 8–12 on a shared many-core host — ngspice is memory-bandwidth bound and a
  128-core box at load 280 does not get faster with 32 workers per sweep.
* **`lab.shape.fit_butter(fixed=…)`** pins named capacitors out of the
  Nelder-Mead. Added to walk the THD/flatness trade on purpose; NOTE the fit
  is a local search — from an analytic (`caps_for`) cold start on the 023
  cells it repeatedly walked `c2_b` to ~0 pF (peaking 2 dB, ph 270°) while
  from a warm start (a neighbouring flat cell's caps) it converged in ~150
  evaluations. Warm-start it, or scan (`scan.py`) and read the table.
* **`replica_of(design, m)`** with an integer `m` emits `rep_sink` as the bias
  unit at `m=` (unit-copy mirror, layout-friendly), a non-integer scales W.
  Sign-off cells carry `iref = 0.662 nA` (021 family) or `1 nA` (022 family) —
  read `design.iref` before choosing `m`; the first `B1` build used m = 2 on a
  0.662 nA unit and mis-biased the ladder at 1.32 nA.
