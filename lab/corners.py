"""PVT corners: the same scorecard, run everywhere the part has to work.

A nominal scorecard is a claim about ONE point in a three-dimensional operating
box.  Nothing in this design is trimmed, calibrated or servo'd -- the cutoff is
set by ``w0^2 = gm_i*gm_f/(C1*C2)`` and in weak inversion ``gm = I/(n*Vt)``, so
the pole frequency is proportional to ``1/T`` at constant current before the
process has said anything at all.

That is not a worry, it is a measurement.  On the reference cell, full 45-point
grid, this module:

    fc: 115.97 Hz (mos_ss / +27 C / 1.35 V) .. 333.14 Hz (mos_ff / -40 C /
    1.50 V) -- a 2.873x SPAN against an S2 box that is +-2 % wide.

The temperature axis alone, at ``mos_tt`` and 1.65 V, gives 329.73 / 250.23 /
176.92 Hz at -40 / +27 / +125 C = 1.864x, close to the ``Vt`` ratio
``398/233 = 1.71x`` that predicts it.  A 250.37 Hz nominal cutoff is therefore
not evidence that S2 is met; it is one sample of a distribution.  ZERO of 45
corners pass the reference cell today.

What the grid is, and why each axis is on it
--------------------------------------------
* **Process** -- the five MOS corner sections of ``cornerMOShv.lib``
  (`lab.config.CORNERS`).  ``tt`` is nominal; ``ss``/``ff`` move both flavours
  together; ``sf``/``fs`` skew them against each other.  Naming is
  ``<nmos><pmos>``: ``mos_sf`` is slow-N / fast-P.  (Confirmed against the
  library itself -- the same PSP ``dphibo`` multiplier that ``mos_ss`` lowers on
  BOTH flavours and ``mos_ff`` raises on both is lowered only on the nmos in
  ``mos_sf`` and only on the pmos in ``mos_fs``.)  The skews are not decoration
  here: every bias current in this circuit is set by an n-mirror driving a
  p-mirror, so an n-vs-p threshold skew is a direct multiplier on the branch
  current, and in the merged cells (020B/020C) the ladder current is the
  solution of ``V_SG(gmf_b) + V_SG(bridge) = VDD`` -- two p-thresholds against
  the supply, which a p-skew moves EXPONENTIALLY.
* **Temperature** -- -40 / 27 / 125 C, the industrial-plus range.  27 C is
  `config.TEMP_NOM`, so the nominal corner reproduces the bench exactly.
* **Supply** -- `config.VDD` +-10 %.  Derived from `config.VDD` rather than
  hard-coded so a re-based supply carries the tolerance with it.

Full cross product = 45 points; `REDUCED` = 22 (see its own note -- it is a
screen, and the vertex-only version of it provably misses this circuit's worst
cutoff corner).  Measured wall time, docker lane, 6 workers: 17 points in
10.7 s and 45 points in 51.4 s on an idle host -- but 22 points took 140 s while
another agent was simulating on the same machine, so treat ~1 s/point as the
floor and expect several times that under load.  Either way a full PVT sign-off
is a coffee-free operation, and there is no excuse for signing anything off on
`NOMINAL` alone.

The supply axis is a PARAMETER, never a global
----------------------------------------------
`config.VDD` is a module-level constant that `lab.deck._core` reads at deck
BUILD time and `lab.metrics.score_plots` multiplies into the S6 power number.
Sweeping supply by mutating `C.VDD` from inside a thread pool is a data race
with no error path: thread A builds its 1.35 V deck, thread B rebinds the global
to 1.65 V before thread A's power is computed, and the run finishes clean with a
21 % power error attributed to the wrong corner.  Every supply here is therefore
threaded through the explicit ``vdd=`` parameter on `deck.ac_noise` /
`metrics.evaluate` / `metrics.score_plots`.  This module never writes `C.VDD`.

Gotchas recorded while building this
------------------------------------
* **A non-converged corner is a RESULT, not a crash.**  `lab.ngspice` is
  deliberately loud (it raises `SimError` on ngspice's silent zero-filled dc
  failures), which means one unsolvable corner would otherwise abort a 45-point
  sweep and lose the 44 good answers.  Each point is wrapped, and a
  non-convergence is recorded as its own status -- distinct from FAIL, because
  "the solver could not find the operating point" and "the operating point is
  fine but IRN is 41 uV" are different engineering facts.  Both are still
  ledger-logged; a corner that produced no row would be indistinguishable from
  a corner nobody ran.
* **The bias reference is an ideal current source** (`deck._bias`: ``iref`` is a
  literal ``i`` element on ``vdd_top``).  So the supply axis measured here
  probes headroom and channel-length modulation ONLY -- it does not include the
  supply sensitivity of a real current reference, because there isn't one in
  this testbench.  Read a passing supply column as "the filter core tolerates
  the rail", not as "the product tolerates the rail".
* **The dc hint is supply-relative.**  `deck._core` clamps its output-CM nodeset
  to the rail; without that, the 1.25 V hint at a 1.35 V supply aims the solver
  at a node 0.1 V from the rail and manufactures non-convergences that the
  circuit does not actually have.  That clamp lives in `deck.py` (shared with
  the supply-droop work), not here.
* **A dead circuit is not a non-convergence, and the table must show which.**
  The reference cell at -40 C / 1.35 V solves perfectly well and reports
  ``dc_db = -40.46 dB`` (mos_tt) -- ngspice is not confused, the filter is
  simply gone.  Both a NON-CONV row and a "converged, dc gain -40 dB" row are
  failures, but only the second one is a design fact, so `status` distinguishes
  them and `table` renders NON-CONV as dashes rather than as zeros.
* **The low-supply column is a HEADROOM cliff, and it is the reference cell's
  dominant PVT weakness.**  Measured at -40 C, mos_tt: 1.35 V -> dc_db
  -40.46 dB, 1.50 V -> -0.0055 dB, 1.65 V -> -0.0035 dB.  The mechanism is the
  one `dut.build_reference` already names: every follower is p-type, so the
  common mode climbs one |Vgs| per stage instead of cancelling, and |Vgs| grows
  as the die gets cold.  At VDD-10 % the top bias device leaves saturation, gm
  collapses and the passband goes with it.  Any fix that buys S3 flatness by
  raising ``vocm`` spends this margin -- check the 1.35 V column before and
  after, not just the nominal row.
* **Temperature is the fc axis; supply is the headroom axis.**  Measured: the
  temperature sweep moves fc 1.864x while the supply sweep at +27 C / mos_tt
  moves it 250.16 -> 250.23 Hz (0.03 %) until headroom breaks, at which point
  supply stops being a small-signal axis at all (mos_ss / +27 C / 1.35 V:
  fc 115.97 Hz, ripple 4.87 dB, yet dc_db still -0.0163 dB).  That last row is
  the trap: a clean dc gain is NOT evidence the corner is healthy.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from . import config as C
from . import metrics as M
from . import ngspice as ng
from .dut import Design
from .parallel import batch, jobs

# ----------------------------------------------------------------- the grid --

PROCESSES: tuple[str, ...] = tuple(C.CORNERS)      # .lib cornerMOShv.lib <sec>
TEMPS: tuple[float, ...] = (-40.0, C.TEMP_NOM, 125.0)

# Supply tolerance.  +-10 % is the usual analog-IP contract for an unregulated
# rail and is what the datasheet section will quote; derived from config.VDD so
# the box follows a re-based supply instead of silently going asymmetric.
VDD_TOL = 0.10
VDDS: tuple[float, ...] = (round(C.VDD * (1 - VDD_TOL), 6), C.VDD,
                           round(C.VDD * (1 + VDD_TOL), 6))

# Never exceed this many concurrent containers: each ngspice is single-threaded
# but every point pays a Docker start-up, and past ~6 the contention makes the
# sweep slower AND the wall-time column meaningless.  The NATIVE lane pays no
# start-up, so there the cap is the core budget (`lab.parallel.jobs`, i.e.
# `LPF_JOBS` or cpu_count-2) -- a 45-point grid on a many-core host is one
# wave, not eight.
MAX_WORKERS = 6 if C.lane() == "docker" else max(6, jobs())


@dataclass(frozen=True, order=True)
class Corner:
    """One PVT point: a model-card section, a die temperature, and a rail."""

    process: str
    temp: float
    vdd: float

    @property
    def slug(self) -> str:
        """Filesystem-safe identity -- becomes the run tag and the ledger key."""
        p = self.process.replace("mos_", "")
        t = f"m{abs(self.temp):.0f}" if self.temp < 0 else f"{self.temp:.0f}"
        return f"{p}_{t}c_{self.vdd:.3f}".replace(".", "v")

    @property
    def label(self) -> str:
        return f"{self.process} / {self.temp:+.0f} C / {self.vdd:.2f} V"

    def as_dict(self) -> dict:
        return {"process": self.process, "temp": self.temp, "vdd": self.vdd,
                "slug": self.slug}


def grid(processes=PROCESSES, temps=TEMPS, vdds=VDDS) -> tuple[Corner, ...]:
    """Cross product, in a deterministic order (process, then temp, then vdd)."""
    return tuple(Corner(p, float(t), float(v))
                 for p in processes for t in temps for v in vdds)


NOMINAL = Corner(C.CORNER_NOM, C.TEMP_NOM, C.VDD)

#: The full cross product -- 5 x 3 x 3 = 45 points.  The sign-off set.
CORNERS: tuple[Corner, ...] = grid()

#: "Extremes + nominal" -- the in-loop SCREEN, not a sign-off set.  22 points:
#:
#:   1   the bench point (`NOMINAL`), so a screen always reproduces the
#:       standalone scorecard and a disagreement is caught immediately;
#:  16   every non-nominal process at both temperature AND both supply
#:       extremes -- the classic vertex box.  All four skews stay in, because
#:       `mos_sf`/`mos_fs` are NOT interior to `mos_ss`/`mos_ff`: they move the
#:       n-vs-p threshold ratio that every mirror in this circuit divides by;
#:   5   every process at NOMINAL temperature on the LOW rail.
#:
#: That last row is not symmetry, it is a measured correction.  The obvious
#: 17-point version (vertices + nominal) rests on the box interior being benign,
#: and on the reference cell it demonstrably is not: the worst cutoff in the
#: full 45-point grid is 115.97 Hz at `mos_ss / +27 C / 1.35 V`, an INTERIOR
#: point in temperature, which the vertex box steps straight over (its worst was
#: 173.56 Hz).  The low rail is where this topology's headroom cliff lives, so
#: it gets sampled at every temperature and not only at the ends.
#:
#: Verified: on the reference cell the 22-point screen returns the SAME worst
#: case as the 45-point grid on fc (115.97 Hz), ripple (4.869 dB), IRN
#: (20186 uV) and power (13.493 nW), and an fc span of 2.871x against the full
#: grid's 2.873x -- at half the simulations.
#:
#: A screen that passes still proves nothing on its own -- run `CORNERS`.
REDUCED: tuple[Corner, ...] = (
    (NOMINAL,)
    + grid(processes=tuple(p for p in PROCESSES if p != C.CORNER_NOM),
           temps=(TEMPS[0], TEMPS[-1]), vdds=(VDDS[0], VDDS[-1]))
    + grid(processes=PROCESSES, temps=(C.TEMP_NOM,), vdds=(VDDS[0],))
)

#: ONE AXIS AT A TIME -- the diagnostic set the 22-point screen cannot give.
#: Every off-nominal row of `REDUCED` moves two or three axes at once, so a
#: process failure and a headroom failure read the same.  Measured on the
#: sign-off cells (experiments/023-replica-bias): the family's ss/ff spread at
#: NOMINAL V and T was fc 13.6 -> 524 Hz, invisible in `REDUCED` because every
#: ss/ff row there is also at +-10 % rail or at a temperature extreme.
PROCESS_ONLY: tuple[Corner, ...] = tuple(
    Corner(p, C.TEMP_NOM, C.VDD) for p in PROCESSES if p != C.CORNER_NOM)
SUPPLY_ONLY: tuple[Corner, ...] = tuple(
    Corner(C.CORNER_NOM, C.TEMP_NOM, v) for v in VDDS if v != C.VDD)
TEMP_ONLY: tuple[Corner, ...] = tuple(
    Corner(C.CORNER_NOM, t, C.VDD) for t in TEMPS if t != C.TEMP_NOM)
#: nominal + process alone + supply alone + temperature alone = 9 points.
AXES: tuple[Corner, ...] = (NOMINAL,) + PROCESS_ONLY + SUPPLY_ONLY + TEMP_ONLY

# Every pass/fail column, in the reading order `metrics.table` uses, derived
# from SPEC so a new spec line shows up here without an edit.
SPEC_COLS: tuple[str, ...] = (tuple(c for c in M.COLS if c in M.SPEC)
                              + tuple(k for k in M.SPEC if k not in M.COLS))

# The quantities whose corner-to-corner SPREAD is the headline of a PVT report.
SPAN_KEYS: tuple[str, ...] = ("fc_hz", "irn_uv", "p_core_nw")


# ------------------------------------------------------------------ results --

PASS, FAIL, NONCONV, ERROR = "PASS", "FAIL", "NON-CONV", "ERROR"


@dataclass
class CornerResult:
    """One corner's verdict.  `score is None` iff the point produced no data."""

    corner: Corner
    score: M.Score | None = None
    status: str = PASS
    violations: list[str] = field(default_factory=list)
    error: str = ""
    wall_s: float = float("nan")

    @property
    def ok(self) -> bool:
        return self.status == PASS

    @property
    def measured(self) -> bool:
        """False for NON-CONV/ERROR -- i.e. 'this point has no numbers at all'."""
        return self.score is not None

    def get(self, key: str) -> float:
        if self.score is None:
            return float("nan")
        v = self.score.values.get(key)
        return float("nan") if v is None else float(v)


# --------------------------------------------------------------------- run --

def run(design: Design, tag: str, *, corners: tuple[Corner, ...] | None = None,
        workers: int = MAX_WORKERS, record: bool = True) -> list[CornerResult]:
    """Score `design` at every corner, in parallel, and never abort on one point.

    `corners` defaults to `REDUCED`.  Each point runs the ordinary cheap
    scorecard deck (`metrics.evaluate` -> op + ac + noise, one rawfile) at that
    corner's model section, temperature and supply, and is auto-logged to the
    ledger under ``<tag>_<corner.slug>`` with its corner/temp/vdd fields set --
    so any number in a corner table can be traced back to a deck hash.

    Failures are converted, not propagated: `ngspice.SimError` (which covers
    ngspice's zero-exit dc failures as well as a genuine non-zero exit) becomes
    a NON-CONV row, anything else an ERROR row, and both are still written to
    the ledger.  The return list is in `corners` order regardless of completion
    order.
    """
    cs = tuple(corners) if corners is not None else REDUCED
    n = max(1, min(int(workers), MAX_WORKERS))

    def one(c: Corner) -> CornerResult:
        t0 = time.time()
        try:
            s = M.evaluate(design, f"{tag}_{c.slug}", corner=c.process,
                           temp=c.temp, vdd=c.vdd, record=record)
        except ng.SimError as exc:
            return _failed(design, tag, c, NONCONV, exc, time.time() - t0, record)
        except Exception as exc:                              # noqa: BLE001
            return _failed(design, tag, c, ERROR, exc, time.time() - t0, record)
        return CornerResult(c, score=s, status=PASS if s.ok else FAIL,
                            violations=list(s.violations), wall_s=time.time() - t0)

    out = batch(cs, one, workers=n)          # on_error='keep' by default
    # `one` already swallows everything, but batch's slot could still hold an
    # exception if the wrapper itself died (e.g. a KeyboardInterrupt path).
    # Never hand a caller a list that mixes results and exceptions.
    return [r if isinstance(r, CornerResult)
            else CornerResult(c, status=ERROR, error=repr(r),
                              violations=[f"{ERROR}: {r!r}"])
            for c, r in zip(cs, out)]


def _failed(design: Design, tag: str, c: Corner, status: str, exc: BaseException,
            wall: float, record: bool) -> CornerResult:
    """Record a point that produced no data -- in the ledger too, deliberately.

    A corner with no ledger row is indistinguishable from a corner nobody ran,
    which is exactly the ambiguity a PVT report must not have.
    """
    first = next((ln for ln in str(exc).splitlines() if ln.strip()),
                 type(exc).__name__)
    msg = f"{status}: {first.strip()[:200]}"
    if record:
        from .ledger import log_run
        log_run(f"{tag}_{c.slug}", {}, design=design, corner=c.process,
                temp=c.temp, wall=wall, violations=[msg], kind="corner",
                extra={"vdd": c.vdd, "status": status,
                       "error": str(exc)[:1000]})
    return CornerResult(c, score=None, status=status, violations=[msg],
                        error=str(exc)[:1000], wall_s=wall)


# ----------------------------------------------------------------- summary ---

def _worse(op, bound):
    """Sort key: bigger = further into violation, for this spec line's operator.

    The direction is per-operator, not per-quantity -- ``ph_max_deg`` is a
    floor, ``irn_uv`` a ceiling, ``fc_hz`` a window -- so 'the worst corner' is
    meaningless without it.  For the ``in`` window the metric is distance from
    the window CENTRE, which makes 245.1 Hz and 254.9 Hz equally bad, as they
    are.
    """
    if op == ">=":
        return lambda v: -v
    if op in ("<=", "<"):
        return lambda v: v
    if op == "abs<=":
        return lambda v: abs(v)
    if op == "in":
        mid = 0.5 * (bound[0] + bound[1])
        return lambda v: abs(v - mid)
    raise ValueError(op)


def _line_ok(key: str, v: float) -> bool:
    """Does ONE spec line pass, given one value?

    `metrics.check` scores the whole dict and reports every key it did not find
    as "NOT MEASURED", so calling it with a single-key dict returns seven
    spurious violations.  Filtering by the line's own label reuses the real
    comparison operators instead of re-implementing them here (the SPEC table
    must stay the single source of truth) without inheriting that behaviour.
    """
    label = M.SPEC[key][0]
    return not any(m.startswith(label) for m in M.check({key: v}))


def summary(results: list[CornerResult]) -> dict:
    """Worst case per spec line, the fc span, and who failed on what.

    Everything here is computed only over corners that actually produced data.
    `n_nonconv` is reported separately and loudly: a span computed across 15 of
    17 corners is not a span, and the two missing points are the interesting
    ones.
    """
    got = [r for r in results if r.measured]
    out: dict = {
        "n_corners": len(results),
        "n_pass": sum(1 for r in results if r.ok),
        "n_fail": sum(1 for r in results if r.status == FAIL),
        "n_nonconv": sum(1 for r in results if r.status == NONCONV),
        "n_error": sum(1 for r in results if r.status == ERROR),
        "n_measured": len(got),
        "all_pass": bool(results) and all(r.ok for r in results),
        "worst": {},
        "span": {},
        "failing": [],
    }

    for key, (label, op, bound) in M.SPEC.items():
        cand = [r for r in got if not math.isnan(r.get(key))]
        if not cand:
            out["worst"][key] = {"label": label, "value": None,
                                 "corner": None, "ok": None,
                                 "note": "NOT MEASURED at any corner"}
            continue
        keyfn = _worse(op, bound)
        r = max(cand, key=lambda x: keyfn(x.get(key)))
        v = r.get(key)
        out["worst"][key] = {
            "label": label, "value": v, "corner": r.corner.label,
            "corner_slug": r.corner.slug, "bound": bound, "op": op,
            "ok": _line_ok(key, v),
        }

    for key in SPAN_KEYS:
        cand = [r for r in got if not math.isnan(r.get(key))]
        if not cand:
            out["span"][key] = None
            continue
        lo = min(cand, key=lambda x: x.get(key))
        hi = max(cand, key=lambda x: x.get(key))
        vlo, vhi = lo.get(key), hi.get(key)
        out["span"][key] = {
            "min": vlo, "min_corner": lo.corner.label,
            "max": vhi, "max_corner": hi.corner.label,
            "span": (vhi / vlo) if vlo else float("inf"),
            "delta": vhi - vlo,
        }

    for r in results:
        if not r.ok:
            out["failing"].append({
                "corner": r.corner.label, "slug": r.corner.slug,
                "status": r.status, "violations": list(r.violations),
            })
    return out


# ------------------------------------------------------------------ output --

def table(results: list[CornerResult], cols: tuple[str, ...] = SPEC_COLS) -> str:
    """The finding: one row per corner, every spec column, then the spans.

    Non-converged corners keep their row with dashes in it.  Dropping them would
    turn 'this design has no operating point at -40 C' into a table that simply
    looks two rows shorter.
    """
    head = ("| corner | T (C) | VDD (V) | " + " | ".join(cols) + " | verdict |")
    sep = "|" + "---|" * (len(cols) + 4)
    out = [head, sep]
    for r in results:
        cells = []
        for c in cols:
            v = r.get(c)
            cells.append("-" if math.isnan(v) else M._FMT.get(c, "{:.4g}").format(v))
        verdict = r.status if r.ok or not r.measured else f"FAIL ({len(r.violations)})"
        out.append(f"| {r.corner.process} | {r.corner.temp:+.0f} | "
                   f"{r.corner.vdd:.2f} | " + " | ".join(cells) +
                   f" | {verdict} |")

    s = summary(results)
    out += ["", f"**{s['n_pass']} of {s['n_corners']} corners PASS** "
                f"({s['n_fail']} fail, {s['n_nonconv']} non-converged, "
                f"{s['n_error']} error).", "",
            "| quantity | min | max | span (max/min) | min at | max at |",
            "|---|---|---|---|---|---|"]
    for key in SPAN_KEYS:
        sp = s["span"].get(key)
        if not sp:
            out.append(f"| {key} | - | - | - | - | - |")
            continue
        fmt = M._FMT.get(key, "{:.4g}")
        out.append(f"| {key} | {fmt.format(sp['min'])} | {fmt.format(sp['max'])} "
                   f"| {sp['span']:.3f}x | {sp['min_corner']} | {sp['max_corner']} |")

    out += ["", "| # | spec line | bound | worst measured | at corner | verdict |",
            "|---|---|---|---|---|---|"]
    for key, w in s["worst"].items():
        label, op, bound = M.SPEC[key]
        b = (f"{bound[0]:g}..{bound[1]:g}" if op == "in" else f"{op} {bound:g}")
        if w["value"] is None:
            out.append(f"| {key} | {label} | {b} | - | - | NOT MEASURED |")
            continue
        fmt = M._FMT.get(key, "{:.4g}")
        out.append(f"| {key} | {label} | {b} | {fmt.format(w['value'])} | "
                   f"{w['corner']} | {'PASS' if w['ok'] else '**FAIL**'} |")
    return "\n".join(out)


def explain(results: list[CornerResult]) -> str:
    """One-screen prose verdict -- what a reviewer reads before the table."""
    s = summary(results)
    if s["all_pass"]:
        fc = s["span"].get("fc_hz")
        extra = (f"; fc span {fc['span']:.3f}x "
                 f"({fc['min']:.2f}..{fc['max']:.2f} Hz)" if fc else "")
        return f"all {s['n_corners']} corners PASS{extra}"
    lines = [f"{s['n_pass']}/{s['n_corners']} corners pass. Failing:"]
    for f in s["failing"]:
        lines.append(f"  - {f['corner']} [{f['status']}]")
        for v in f["violations"]:
            lines.append(f"      {v}")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI --

def _load_design(path):
    """Reuse the frozen-design loader that certify.py already owns.

    Imported by PATH and only from `__main__`, on purpose: `lab/` is the
    library and `experiments/` is the caller, so a module-level import here
    would invert the dependency and make every `import lab.corners` drag an
    experiment script in with it.
    """
    import importlib.util
    p = C.REPO / "experiments" / "020-novel-topologies" / "certify.py"
    spec = importlib.util.spec_from_file_location("_certify", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load(path)


def main(argv: list[str] | None = None) -> int:
    """`python -m lab.corners <design.json> [--full] [--tag NAME]`"""
    import argparse
    ap = argparse.ArgumentParser(description="PVT corner sweep")
    ap.add_argument("design", help="path to a frozen design JSON")
    ap.add_argument("--full", action="store_true",
                    help=f"all {len(CORNERS)} corners (default: the "
                         f"{len(REDUCED)}-point reduced set)")
    ap.add_argument("--tag", default="corners")
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    a = ap.parse_args(argv)

    d = _load_design(a.design)
    cs = CORNERS if a.full else REDUCED
    t0 = time.time()
    res = run(d, a.tag, corners=cs, workers=a.workers)
    print(table(res))
    print()
    print(explain(res))
    print(f"\n{len(cs)} corners in {time.time() - t0:.1f} s "
          f"({C.lane()} lane, {min(a.workers, MAX_WORKERS)} workers)")
    return 0 if summary(res)["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
