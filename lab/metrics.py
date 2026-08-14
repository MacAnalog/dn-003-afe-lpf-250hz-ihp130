"""The scorecard: one simulation in, one spec verdict out.

`SPEC` here is the machine-readable twin of doc/target-spec.md.  If you change
one, change the other -- `scripts/lint.py` fails the build when they disagree.

Design note on what is technology-independent.  S1-S5 and S7-S8 are properties
of the FILTER (order, cutoff, flatness, noise, distortion, provenance) and carry
across any process unchanged; they are the challenge.  Only S6 has a supply term
in it, and it is stated in WATTS, so it survives the supply change on its own.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import config as C
from . import ngspice as ng
from . import raw as R
from .dut import Design
from .deck import ac_noise

# ---------------------------------------------------------------- the spec --
# (key, human label, comparison, bound)
SPEC: dict[str, tuple] = {
    "ph_max_deg": ("S1 biquad-order certificate (max unwrapped phase lag)", ">=", 330.0),
    "a1000_db":   ("S1 companion: |H| at 1 kHz", "<=", -48.0),
    "fc_hz":      ("S2 cutoff", "in", (245.0, 255.0)),      # 250 Hz +-2 %
    "dc_db":      ("S3 passband gain", "abs<=", 0.2),
    "peak_db":    ("S4 peaking", "<=", 0.2),
    "ripple_db":  ("S3 passband flatness to 150 Hz", "<=", 0.2),
    "irn_uv":     ("S5 input-referred noise, 0.5-200 Hz", "<", 40.0),
    "p_core_nw":  ("S6 filter-core power", "<", 50.0),
}

# Soft/report-only columns: measured and logged, never a pass/fail.
SOFT = ("c_total_pf", "idd_total_na", "i_core_na", "onoise_uv", "ph_step_deg",
        "f_scored_hi", "mono_db")

# S3's flatness clause is judged over dc .. FLAT_FMAX.
FLAT_FMAX = 150.0

# AC sweep density for SCORING.  10 pts/decade -- the density the originating
# bench used -- puts the samples ~26 % apart near the corner, which is coarse
# enough to step straight over a passband dip and to alias the phase.  Scoring
# uses 50; a diagnostic can go denser still.
AC_DEC = 50

# The band S5 is defined over.  Band limits are load-bearing: an input-referred
# density DIVERGES above the cutoff (the gain goes to zero), so integrating the
# same trace to 1 kHz on a 250 Hz filter reads milli-volts and means nothing.
IRN_BAND = (0.5, 200.0)

# THD spec point (see lab.thd): differential 175 mVpp at fin = 50 Hz.
# S7 is specified at the INPUT: 175 mVpp DIFFERENTIAL drive.  The balun makes
# the source's own amplitude the differential input, so 175 mVpp is ampl=87.5m.
# This is the originating campaign's definition verbatim (its `AMPL_SPEC`), kept
# so the two campaigns' THD numbers mean the same thing.
THD_AMPL = 87.5e-3
# Reporting aid only, NOT the spec: these cells do not have unity large-signal
# gain (measured -0.63 dB to +0.86 dB at the spec level), so a fixed input tests
# different cells at different output swings.  `lab.thd.measure(target_out_vpp=
# THD_OUT_VPP)` servoes the drive to a common OUTPUT level, which separates
# "distorts more" from "is driven harder".
THD_OUT_VPP = 175e-3
THD_FIN = 50.0
THD_LIMIT_DB = -40.0

# The phase certificate's magnitude floor, relative to dc.  Above the floor the
# response has collapsed into a parasitic feed-through plateau where the sampled
# phase steps ~180 deg between points and ALIASES into fake lags far beyond what
# a 4-pole response can produce.  See doc/journal/phase-certificate-floor.md.
PH_FLOOR_DB = -100.0
# Resolvability guard: a band whose worst unwrap-corrected step approaches
# 180 deg is one sample away from aliasing, so its certificate is not
# trustworthy however comfortably it passes.
PH_STEP_GUARD_DEG = 150.0


@dataclass
class Score:
    values: dict
    violations: list[str]

    @property
    def ok(self) -> bool:
        return not self.violations

    def __getitem__(self, k):
        return self.values[k]

    def get(self, k, default=None):
        return self.values.get(k, default)


def check(values: dict) -> list[str]:
    """Every spec line this measurement violates, as human sentences."""
    out = []
    for key, (label, op, bound) in SPEC.items():
        v = values.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(f"{label}: NOT MEASURED")
            continue
        if op == ">=" and not v >= bound:
            out.append(f"{label}: {v:.4g} < {bound:g}")
        elif op == "<=" and not v <= bound:
            out.append(f"{label}: {v:.4g} > {bound:g}")
        elif op == "<" and not v < bound:
            out.append(f"{label}: {v:.4g} >= {bound:g}")
        elif op == "abs<=" and not abs(v) <= bound:
            out.append(f"{label}: |{v:.4g}| > {bound:g}")
        elif op == "in" and not (bound[0] <= v <= bound[1]):
            out.append(f"{label}: {v:.4g} outside [{bound[0]:g}, {bound[1]:g}]")
    return out


def goal_met(values: dict) -> bool:
    """The challenge headline: S5 met AND the hard box intact."""
    return not check(values)


# ------------------------------------------------------------- measurement --

def score_plots(plots: list[R.Plot], design: Design | None = None,
                vdd: float | None = None) -> Score:
    """Turn one ac+noise rawfile into the full scorecard.

    `vdd` names the supply the rawfile was SIMULATED at, for the S6 power term
    only (P = I_core * VDD).  It must be passed by anything that built its deck
    with a non-nominal supply -- `lab.config.VDD` is a module constant and a
    parallel sweep cannot vary it by mutation.  `None` = the nominal supply.
    """
    v: dict = {}

    ac = R.pick(plots, "ac")
    f, h = R.diff_tf(ac, C.OUT_P, C.OUT_N)
    y = R.db_rel_dc(h)
    v["dc_db"] = float(R.db(h)[0])                 # absolute, vs the 1 V drive
    v["fc_hz"] = R.f3db(f, h)
    v["peak_db"] = R.peaking_db(f, h, fmax=1e3)
    v["ripple_db"] = R.ripple_db(f, h, FLAT_FMAX)
    # Report-only, but reported ALWAYS: `ripple_db` and `peak_db` both read
    # small through a sag-then-recover passband, and that shape is how a fit
    # that scores bounds instead of shape gets away with not being maximally
    # flat.  Scored to the corner, not to FLAT_FMAX -- the climb can sit either
    # side of 150 Hz and it is equally wrong in both places.
    v["mono_db"] = R.monotone_db(f, h, v["fc_hz"])
    v["a1000_db"] = R.value_at(f, y, 1000.0)
    v["ph_max_deg"] = R.ph_max_deg(f, h, PH_FLOOR_DB)
    v["ph_step_deg"] = R.max_phase_step_deg(f, h, PH_FLOOR_DB)
    # The same contiguous prefix `ph_max_deg` uses -- NOT "every point above the
    # floor".  A cell that falls through the floor and recovers onto a
    # feed-through plateau would otherwise report a scored band running to the
    # end of the sweep, which is the tell that the certificate is unwrapping
    # across a gap.  See `lab.raw._floor_prefix`.
    v["f_scored_hi"] = R.f_scored_hi(f, h, PH_FLOOR_DB)

    # Group delay -- report-only soft columns (nothing in S1-S8 scores them,
    # same contract as `mono_db`).  tau(f) = -dphi/domega over the certificate's
    # own contiguous band; a 4th-order low-pass peaks near fc.
    fg, gd = R.group_delay_s(f, h, PH_FLOOR_DB)
    if fg.size:
        v["gd_dc_ms"] = float(gd[0]) * 1e3
        band = fg <= max(v["fc_hz"] * 1.2, 1.0)
        v["gd_max_ms"] = float(np.max(gd[band])) * 1e3 if band.any() else float("nan")
        v["gd_fc_ms"] = float(np.interp(v["fc_hz"], fg, gd)) * 1e3 \
            if fg[-1] >= v["fc_hz"] else float("nan")

    try:
        no = R.pick(plots, "noise")
        fn = np.real(no.x).astype(float)
        inz = _noise_vec(no, "inoise_spectrum")
        onz = _noise_vec(no, "onoise_spectrum")
        v["irn_uv"] = R.integrate_noise(fn, inz, *IRN_BAND) * 1e6
        v["onoise_uv"] = R.integrate_noise(fn, onz, 0.1, 1e3) * 1e6
    except KeyError:
        v["irn_uv"] = float("nan")
        v["onoise_uv"] = float("nan")

    try:
        op = R.pick(plots, "op")
        i_core = abs(float(np.real(op.get(f"i({C.CORE_PROBE})"))[0]))
        i_tot = abs(float(np.real(op.get(f"i({C.SUPPLY_PROBE})"))[0]))
        v["i_core_na"] = i_core * 1e9
        v["idd_total_na"] = i_tot * 1e9
        v["p_core_nw"] = i_core * (C.VDD if vdd is None else vdd) * 1e9
    except KeyError:
        v["i_core_na"] = v["idd_total_na"] = v["p_core_nw"] = float("nan")

    if design is not None:
        v["c_total_pf"] = design.total_cap() * 1e12

    return Score(v, check(v))


def _noise_vec(plot: R.Plot, name: str) -> np.ndarray:
    for cand in (name, name.replace("_spectrum", ""), f"{name}_spectrum"):
        try:
            return np.abs(plot.get(cand))
        except KeyError:
            continue
    raise KeyError(name)


def evaluate(design: Design, tag: str, *, corner: str = C.CORNER_NOM,
             temp: float = C.TEMP_NOM, record: bool = True,
             vdd: float | None = None, **kw) -> Score:
    """Simulate `design` and score it.  Every call is auto-recorded in the ledger.

    This is the CHEAP scorecard.  Expensive runs (THD transients, corner sets,
    Monte Carlo) are gated behind `gate()` -- the sim-economy rule.
    """
    deck = ac_noise(design, corner=corner, temp=temp, vdd=vdd, **kw)
    rundir = ng.run(deck, tag)
    s = score_plots(ng.plots(rundir), design, vdd=vdd)
    if record:
        from .ledger import log_run
        log_run(tag, s.values, deck=deck, design=design, corner=corner,
                temp=temp, wall=ng.wall_time(rundir), violations=s.violations,
                extra=None if vdd is None else {"vdd": vdd})
    return s


class Gated(RuntimeError):
    """An expensive run was requested on a design that fails the cheap box."""


def gate(design: Design, tag: str, *, allow: tuple[str, ...] = ("irn_uv",),
         **kw) -> Score:
    """Sim economy: refuse an expensive measurement unless the cheap box passes.

    `allow` names spec keys whose failure is tolerated -- by default S5, because
    S5 is the goal being *worked on*, so a THD or corner run on a design that is
    still above the noise target is legitimate.  A design that fails the SHAPE
    (order, cutoff, flatness, power) is not worth an expensive run at all.
    """
    s = evaluate(design, tag, **kw)
    hard = [msg for msg in s.violations
            if not any(SPEC[a][0] in msg for a in allow if a in SPEC)]
    if hard:
        raise Gated(f"{tag}: cheap scorecard fails the hard box; "
                    f"not spending an expensive run.\n  " + "\n  ".join(hard))
    return s


# ------------------------------------------------------------------ output --

_FMT = {
    "fc_hz": "{:.2f}", "dc_db": "{:+.4f}", "peak_db": "{:+.4f}",
    "ripple_db": "{:.4f}",
    "a1000_db": "{:.2f}", "ph_max_deg": "{:.2f}", "ph_step_deg": "{:.1f}",
    "irn_uv": "{:.3f}", "onoise_uv": "{:.2f}", "p_core_nw": "{:.3f}",
    "i_core_na": "{:.3f}", "idd_total_na": "{:.2f}", "c_total_pf": "{:.2f}",
    "f_scored_hi": "{:.0f}", "mono_db": "{:.4f}",
    "gd_dc_ms": "{:.4f}", "gd_max_ms": "{:.4f}", "gd_fc_ms": "{:.4f}",
}
COLS = ("fc_hz", "dc_db", "ripple_db", "peak_db", "mono_db", "a1000_db", "ph_max_deg",
        "irn_uv", "p_core_nw", "c_total_pf")


def table(rows: dict[str, Score], cols: tuple[str, ...] = COLS) -> str:
    """A markdown findings table.  Prose is interpretation; THIS is the finding."""
    head = "| cell | " + " | ".join(cols) + " | verdict |"
    sep = "|" + "---|" * (len(cols) + 2)
    out = [head, sep]
    for name, s in rows.items():
        cells = []
        for c in cols:
            val = s.values.get(c)
            cells.append("-" if val is None or (isinstance(val, float) and math.isnan(val))
                         else _FMT.get(c, "{:.4g}").format(val))
        verdict = "PASS" if s.ok else f"FAIL ({len(s.violations)})"
        out.append(f"| {name} | " + " | ".join(cells) + f" | {verdict} |")
    return "\n".join(out)


def explain(s: Score) -> str:
    if s.ok:
        return "all measured spec lines PASS"
    return "FAIL:\n  - " + "\n  - ".join(s.violations)
