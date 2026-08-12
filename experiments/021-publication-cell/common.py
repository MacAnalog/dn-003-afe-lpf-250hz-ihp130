"""Shared machinery for experiment 021: synthesise caps, polish, score, THD.

The one idea worth stating.  Every device change moves gm, which moves the
poles, which moves fc off the S2 box -- so a raw device sweep measures "this
sizing is mis-tuned", not "this sizing is worse".  Each point therefore gets its
capacitors RE-SYNTHESISED from its own measured gm before it is scored, which
makes the sweep a comparison of *devices at equal shape*.  That is the
re-allocation control (CLAUDE.md rule 3) built into the instrument rather than
bolted on afterwards.

Synthesis is analytic first (one op probe, closed form) and then polished by a
short template fit.  Analytic alone lands fc within a few percent; the polish is
what puts it inside +-2 % and flattens the passband.  A full `fit_butter` from a
cold start costs ~300 simulations, the polish costs ~50.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab import config as C            # noqa: E402
from lab import metrics as M           # noqa: E402
from lab import ngspice as ng          # noqa: E402
from lab import oppoint as O           # noqa: E402
from lab import raw as R               # noqa: E402
from lab import shape as S             # noqa: E402
from lab import thd as T               # noqa: E402
from lab.deck import ac_noise          # noqa: E402
from lab.dut import Design             # noqa: E402

WC = 2.0 * math.pi * 250.0
Q_LO, Q_HI = 0.541196, 1.306563


def gms(design: Design, tag: str) -> dict:
    """gm (siemens) of each biquad's input follower and shunt-feedback device."""
    ops, _ = O.probe(design, tag)
    g = {r: ops[r].gm_ns * 1e-9 for r in ops}
    return {"gm_i_a": g["in_a"], "gm_f_a": g["gmf_a"],
            "gm_i_b": g["in_b"], "gm_f_b": g["gmf_b"]}


def caps_for(g: dict, q_a: float, q_b: float) -> dict:
    """The four DRAWN capacitors for a Q assignment, from measured gm.

    C1 = gm_i/(w0*Q); C2_single = gm_f*Q/w0.  `c2_*` is ONE FLOATING capacitor
    across the differential pair, and a floating C between the halves loads each
    half with 2C -- so the drawn value is C2_single/2.  (That factor of two is
    `fvf-2nd`'s "2x effective C per farad drawn", and it is why this family
    reports the capacitance it does.)
    """
    return {"c1_a": g["gm_i_a"] / (WC * q_a),
            "c2_a": g["gm_f_a"] * q_a / WC / 2.0,
            "c1_b": g["gm_i_b"] / (WC * q_b),
            "c2_b": g["gm_f_b"] * q_b / WC / 2.0}


def dense(design: Design, tag: str) -> dict:
    """Shape numbers the scorecard does not carry, on a dense sweep."""
    pl = ng.simulate(ac_noise(design, dec=100, fstart=1.0, fstop=3e3, nstop=1.0),
                     tag)
    f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
    fc = R.f3db(f, h)
    rms, worst = S.template_error(f, h, fc)
    return {"rms": rms, "worst": worst, "mono": S.monotone_db(f, h, fc)}


def synth(base: Design, tag: str, q_a: float, q_b: float, *,
          polish: int = 0, trims: int = 2) -> Design:
    """Re-tune `base`'s capacitors to the Butterworth template for its own gm.

    Three stages, cheapest first:

    1.  **Analytic.**  `caps_for` from one op probe.  Gets the two Q's right and
        the cutoff wrong -- measured here, the closed form lands fc 21-50 % low,
        because every internal node carries parasitic capacitance the two-C
        model does not know about, so the drawn capacitors have to be smaller
        than the formula asks for.
    2.  **Uniform trim.**  Scaling all four capacitors by the same k leaves both
        Q's EXACTLY unchanged (Q depends only on ratios) and moves w0 by 1/k --
        so one measured fc buys the correct cutoff without disturbing the shape
        the analytic step just set.  Two passes converge because the parasitic
        share is small and roughly constant over a +-20 % capacitance move.
    3.  **Polish** (optional).  A short template fit for the residual, which is
        second-order once 1 and 2 have run.

    A screening sweep can stop after 2 for ~4 simulations an arm; a delivery
    candidate gets the polish.
    """
    g = gms(base, f"{tag}_op")
    return synth_from(base.with_(**caps_for(g, q_a, q_b)), tag,
                      polish=polish, trims=trims)


def synth_from(d: Design, tag: str, *, polish: int = 0, trims: int = 2) -> Design:
    """Stages 2-3 of `synth` on capacitors someone else chose.

    Split out because the analytic stage is only useful from a cold start.  Any
    warm start -- a cell already fitted, or one deliberately perturbed to move a
    Q -- wants the trim and the polish without having its capacitors thrown away
    and re-derived from a model that is known to be wrong here.
    """
    for i in range(max(0, trims)):
        s = M.evaluate(d, f"{tag}_trim{i}", record=False)
        fc = s["fc_hz"]
        if not (fc == fc):                       # NaN: no usable cutoff
            break
        k = fc / 250.0
        if abs(k - 1.0) < 0.002:
            break
        d = d.scaled_caps(k)
    if polish > 0:
        d, _ = S.fit_butter(d, f"{tag}_pol", fc_target=250.0,
                            maxiter=polish, verbose=False)
    return d


def full(design: Design, name: str, *, thd: bool = True) -> dict:
    """One row: scorecard + dense shape + (optionally) the S7 transient."""
    s = M.evaluate(design, f"{name}_sc", record=False)
    row = {"name": name, **{k: s[k] for k in
                            ("fc_hz", "dc_db", "ripple_db", "peak_db",
                             "a1000_db", "ph_max_deg", "irn_uv", "p_core_nw",
                             "c_total_pf")},
           **dense(design, f"{name}_dn"),
           "violations": s.violations,
           "caps_pf": {k: getattr(design, k) * 1e12
                       for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
           "devs": {r: {"w": d.w, "l": d.l, "ng": d.ng, "m": d.m}
                    for r, d in design.devs.items()},
           # `topology` is not decoration: it selects the BUILDER, so a row
           # without it cannot be rebuilt into the same netlist at all.
           "topology": design.topology,
           "iref": design.iref, "vicm": design.vicm, "vocm": design.vocm}
    if thd:
        add_thd(design, row)
    return row


def add_thd(design: Design, row: dict) -> dict:
    """Measure S7 and fold it into an existing row, in place.

    Split out from `full` so a sweep can score the cheap box first and spend the
    transient only on arms that landed in it (CLAUDE.md rule 9).
    """
    t = T.measure(design, tag=f"{row['name']}_thd", gate=False)
    row["thd_db"] = t.thd_db
    row["hd"] = {str(k): v for k, v in t.per_harmonic.items()}
    return row


def line(r: dict) -> str:
    return (f"{r['name']:>22s} | fc {r['fc_hz']:6.2f} | mono {r['mono']:.4f} | "
            f"a1k {r['a1000_db']:6.2f} | ph {r['ph_max_deg']:5.1f} | "
            f"IRN {r['irn_uv']:6.2f} | P {r['p_core_nw']:5.2f} | "
            f"C {r['c_total_pf']:6.1f} | THD "
            f"{r.get('thd_db', float('nan')):6.2f}")
