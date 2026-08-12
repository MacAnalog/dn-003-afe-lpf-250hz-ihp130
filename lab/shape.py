"""Shape fitting: put the four capacitors where the spec says the poles go.

A 4th-order all-pole low-pass at 250 Hz with no peaking and >= 48 dB of stopband
at 1 kHz is, arithmetically, a **Butterworth**: at 4x the cutoff a maximally
flat 4-pole response is exactly 4^-4 = -48.16 dB.  So `a1000 <= -48 dB` is not
an independent requirement -- it is the numeric statement that the pole Q's are
Butterworth's (0.5412 and 1.3066) and not something flatter-but-slower.

This module turns that into a search over the only free knobs the topology
gives: the four capacitor values.  Device sizing sets the transconductances;
capacitors set where the poles land for a given set of transconductances.

The cost is deliberately a CONSTRAINT function, not a figure of merit: the
reference baseline is not supposed to be optimal, it is supposed to be *on
spec*, so that a candidate's win is measured against a fair yardstick.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

from . import metrics as M
from .dut import Design

# 4th-order Butterworth, both stages at w0 = 2*pi*fc
BUTTER_Q = (0.541196, 1.306563)
A1000_BUTTER_DB = -48.16     # 20*log10(4**-4)


def cost(v: dict, *, fc_target: float = 250.0, a1000_max: float = -48.2,
         peak_max: float = 0.05, dc_max: float = 0.05,
         ripple_max: float = 0.12) -> float:
    """Squared, weighted distance from the spec shape.  Lower is better.

    RIPPLE is in here for a reason worth remembering: without it the optimiser
    is free to stagger the two biquads' poles so the magnitude sags mid-band and
    recovers before the corner.  A one-sided peaking check reads 0.000 dB
    through that, and on a 10 pt/decade grid the samples straddle the dip
    entirely -- so the fit converges happily onto a response with 1.5 dB of
    passband droop.  Score it, on a dense sweep, or it will come back.
    """
    if v.get("fc_hz") is None or math.isnan(v.get("fc_hz", float("nan"))):
        return 1e6
    c = 0.0
    c += 400.0 * ((v["fc_hz"] - fc_target) / fc_target) ** 2
    over = v["a1000_db"] - a1000_max
    if over > 0:
        c += 4.0 * over ** 2
    if v["peak_db"] > peak_max:
        c += 40.0 * (v["peak_db"] - peak_max) ** 2
    if abs(v["dc_db"]) > dc_max:
        c += 40.0 * (abs(v["dc_db"]) - dc_max) ** 2
    rip = v.get("ripple_db")
    if rip is not None and not math.isnan(rip) and rip > ripple_max:
        c += 400.0 * (rip - ripple_max) ** 2
    return c


def fit_caps(base: Design, tag: str, *, fc_target: float = 250.0,
             maxiter: int = 220, verbose: bool = True, **spec) -> tuple[Design, object]:
    """Nelder-Mead over log-capacitance until the shape is on spec.

    Optimising in LOG space keeps every trial capacitor positive and makes the
    search scale-invariant, which matters because the four values span an order
    of magnitude.
    """
    keys = ("c1_a", "c2_a", "c1_b", "c2_b")
    x0 = np.log(np.array([getattr(base, k) for k in keys]))
    n = {"i": 0}
    seen: dict = {}

    def design_at(x) -> Design:
        vals = {k: float(np.exp(xi)) for k, xi in zip(keys, x)}
        return base.with_(**vals)

    def f(x) -> float:
        key = tuple(round(float(xi), 6) for xi in x)
        if key in seen:
            return seen[key]
        n["i"] += 1
        d = design_at(x)
        try:
            s = M.evaluate(d, f"{tag}_{n['i']:04d}")
            c = cost(s.values, fc_target=fc_target, **spec)
            if verbose and n["i"] % 20 == 0:
                v = s.values
                print(f"  [{n['i']:3d}] cost={c:9.4f} fc={v['fc_hz']:7.2f} "
                      f"a1k={v['a1000_db']:7.2f} rip={v['ripple_db']:6.3f} "
                      f"irn={v['irn_uv']:6.2f} C={v['c_total_pf']:6.2f}")
        except Exception:
            c = 1e6
        seen[key] = c
        return c

    res = minimize(f, x0, method="Nelder-Mead",
                   options={"maxiter": maxiter, "xatol": 1e-4, "fatol": 1e-4})
    return design_at(res.x), res


# ---------------------------------------------------------------------------
# Fitting to the TEMPLATE rather than to a bound
# ---------------------------------------------------------------------------
# `cost()` above is a constraint function: it scores |peak| and |ripple| against
# bounds and is indifferent to the SHAPE that produces them.  A staggered pair
# that sags 0.09 dB at 80 Hz and lifts 0.09 dB at 130 Hz scores ripple 0.084 and
# passes -- while being visibly not a maximally-flat filter, and not what the
# originating campaign built (its merge cell measured **peak = 0.00 dB**).
#
# The fix is to score the whole passband against the Butterworth template.  A
# 4th-order maximally-flat response is monotone by construction, so "no bump"
# stops being a side condition and becomes the objective.

def butter_db(f: np.ndarray, fc: float, n: int = 4) -> np.ndarray:
    """|H| of an n-pole maximally-flat low-pass, in dB relative to dc."""
    return -10.0 * np.log10(1.0 + (np.asarray(f, float) / fc) ** (2 * n))


def template_error(f, h, fc: float, fmax: float | None = None, n: int = 4) -> tuple:
    """(rms, worst) dB deviation of a measured response from the template.

    Scored over the PASSBAND AND CORNER only (`fmax` defaults to 1.25*fc).
    Deliberately not further: past the corner a real cell rolls off FASTER than
    the template (finite gm/gds, parasitic poles), and that surplus is a good
    thing the spec already rewards -- scoring it as "deviation" would push the
    fit to make the skirt worse.  The stopband is a separate, one-sided
    constraint (`a1000_db <= -48`), not a shape target.
    """
    from . import raw as R
    y = R.db_rel_dc(np.asarray(h))
    f = np.asarray(np.real(f), float)
    m = f <= (1.25 * fc if fmax is None else fmax)
    d = y[m] - butter_db(f[m], fc, n)
    return float(np.sqrt(np.mean(d ** 2))), float(np.max(np.abs(d)))


def monotone_db(f, h, fmax: float) -> float:
    """Worst RISE of |H| below `fmax`, in dB.  0 => monotone.

    Lives in `lab.raw` beside the other shape primitives (and is reported on
    every scorecard as the soft column `mono_db`); re-exported here because the
    template fit is its main consumer.
    """
    from . import raw as R
    return R.monotone_db(f, h, fmax)


def fit_butter(base: Design, tag: str, *, fc_target: float = 250.0,
               fmax: float | None = None, a1000_max: float = -48.2,
               maxiter: int = 300, verbose: bool = True):
    """Nelder-Mead over log-capacitance against the Butterworth TEMPLATE.

    Device sizing is untouched, so gm, current, noise and power do not move --
    only where the four capacitors put the two pole pairs.  Returns
    `(design, result)` like `fit_caps`.
    """
    from . import config as C
    from . import ngspice as ng
    from . import raw as R
    from .deck import ac_noise

    keys = ("c1_a", "c2_a", "c1_b", "c2_b")
    x0 = np.log(np.array([getattr(base, k) for k in keys]))
    n = {"i": 0}
    seen: dict = {}

    def f_obj(x) -> float:
        key = tuple(round(float(xi), 6) for xi in x)
        if key in seen:
            return seen[key]
        n["i"] += 1
        d = base.with_(**{k: float(np.exp(xi)) for k, xi in zip(keys, x)})
        try:
            pl = ng.simulate(ac_noise(d, dec=50, fstart=1.0, fstop=3e3,
                                      nstop=1.0), f"{tag}_{n['i']:04d}")
            ac = R.pick(pl, "ac")
            fr, h = R.diff_tf(ac, C.OUT_P, C.OUT_N)
            y = R.db_rel_dc(h)
            rms, worst = template_error(fr, h, fc_target, fmax)
            # the shape objective ...
            c = rms ** 2 + 0.25 * worst ** 2
            # ... plus the two things the template cannot express: the cutoff
            # must land in the S2 box, and the stopband is one-sided (steeper
            # than Butterworth is a bonus, shallower is a violation).
            fc = R.f3db(fr, h)
            if fc == fc:
                c += 40.0 * ((fc - fc_target) / fc_target) ** 2
            else:
                c += 10.0
            over = R.value_at(fr, y, 1000.0) - a1000_max
            if over > 0:
                c += 4.0 * over ** 2
            if verbose and n["i"] % 25 == 0:
                print(f"  [{n['i']:3d}] rms={rms:6.3f} worst={worst:6.3f} "
                      f"mono={monotone_db(fr, h, fc_target):6.3f} "
                      f"fc={fc:7.2f} C={d.total_cap()*1e12:7.2f} pF")
        except Exception:                                   # noqa: BLE001
            c = 1e6
        seen[key] = c
        return c

    res = minimize(f_obj, x0, method="Nelder-Mead",
                   options={"maxiter": maxiter, "xatol": 1e-4, "fatol": 1e-6})
    best = base.with_(**{k: float(np.exp(xi)) for k, xi in zip(keys, res.x)})
    return best, res


def q_report(v: dict) -> str:
    """How far the achieved shape is from Butterworth, in the spec's own terms."""
    return (f"fc {v['fc_hz']:.2f} Hz | @1 kHz {v['a1000_db']:.2f} dB "
            f"(Butterworth {A1000_BUTTER_DB:.2f}) | peaking {v['peak_db']:.3f} dB "
            f"| ripple {v['ripple_db']:.3f} dB | dc {v['dc_db']:+.4f} dB "
            f"| ph_max {v['ph_max_deg']:.2f} deg")
