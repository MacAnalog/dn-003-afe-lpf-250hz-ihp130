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
         peak_max: float = 0.05, dc_max: float = 0.05) -> float:
    """Squared, weighted distance from the spec shape.  Lower is better."""
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
                      f"a1k={v['a1000_db']:7.2f} peak={v['peak_db']:6.3f} "
                      f"irn={v['irn_uv']:6.2f} C={v['c_total_pf']:6.2f}")
        except Exception:
            c = 1e6
        seen[key] = c
        return c

    res = minimize(f, x0, method="Nelder-Mead",
                   options={"maxiter": maxiter, "xatol": 1e-4, "fatol": 1e-4})
    return design_at(res.x), res


def q_report(v: dict) -> str:
    """How far the achieved shape is from Butterworth, in the spec's own terms."""
    return (f"fc {v['fc_hz']:.2f} Hz | @1 kHz {v['a1000_db']:.2f} dB "
            f"(Butterworth {A1000_BUTTER_DB:.2f}) | peaking {v['peak_db']:.3f} dB "
            f"| dc {v['dc_db']:+.4f} dB | ph_max {v['ph_max_deg']:.2f} deg")
