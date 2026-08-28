#!/usr/bin/env python
"""The transfer function: exact symbolic form, its factorisation into two biquads, the
pole/zero map, and every check of all three against simulation.

Five things are produced, in order, each one checking the one before:

1. **The exact H(s)**, fully symbolic, from `spicexplorer_netlist2tf` on the DM
   half-circuit at `Fidelity.IDEAL` -- gm's and the four design capacitors, nothing else.
   This is the equation the paper quotes.
2. **The factorisation.**  The quartic denominator is shown, by exact symbolic identity,
   to be `D_A(s) * D_B(s) + kappa * s^2` -- two textbook SSF biquads plus ONE residual
   coupling term that the branch stacking creates.  `kappa` is printed, and the pole pair
   it moves is measured, so "is this really two biquads?" gets a number instead of a shrug.
3. **The pole/zero map** of the full 13-node differential cell at `Fidelity.FULL`
   (`pencil.solve`), pre- and post-layout: every pole and zero, per-pair f0 and Q, and the
   pole-zero cancellations flagged rather than quietly dropped.
4. **Validation against the simulator**: |H| in dB, phase in degrees and group delay,
   model vs the ac sweep, over the scored band and over the whole sweep.
5. **An independent pole estimate FROM THE SIMULATION DATA ALONE** -- a 4-pole rational
   fit of the measured complex response, which never sees the small-signal model.  Poles
   that agree between (3) and (5) are verified by sim data in the strict sense the
   reviewer asked for; `ngspice`'s own `.pz` cannot do this job here (it aborts with "the
   input signal is shorted on the way to the output" for any input port that carries its
   dc bias, which a subthreshold gate must -- checked on a one-transistor deck too).

    spicexplorer-platform/.venv/bin/python signoff/paper-draft/scripts/tf_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import sympy as sp
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))

import n2tf_model as M  # noqa: E402
import pencil as PZ  # noqa: E402
from spicexplorer_netlist2tf import Fidelity  # noqa: E402

CORE_IDEAL = REPO / "signoff/post-pvt/H12-robust/asbuilt/core.sp"
CORE_MIM = REPO / "signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp"
DRIVE = {"vinp": 0.5, "vinn": -0.5}
OUT = ("voutp", "voutn")
# The sim-only fit is a 4-pole/0-zero model, so it is fitted only where the measured
# response IS 4-pole/0-zero: above ~500 Hz the cell's device-capacitance feed-through
# zeros lift the stopband and a zero-free model cannot follow them.  Widening this band
# does not "improve" the fit, it just fits a different function.
FIT_BAND = (0.1, 500.0)


# ------------------------------------------------------------------ 1 + 2: the algebra --
def symbolic_form() -> dict:
    """Exact H(s) on the DM half-circuit, and the two-biquad factorisation of D(s)."""
    _ir, _ss, sysm, doubled = M.build_half(CORE_IDEAL, None, level=Fidelity.IDEAL,
                                           numeric=False, symbolic_caps=True)
    raw = M.h_half(sysm)
    h = M.rename_symbols(sp.cancel(sp.together(raw.expr)))
    num, den = sp.fraction(h)

    # Bind every symbol BY NAME out of the expression itself.  sympy treats
    # Symbol('c1a') and Symbol('c1a', positive=True) as different symbols, and the
    # netlist-derived capacitor symbols carry no assumptions while the minted device
    # symbols do -- so re-declaring them here would silently compare two disjoint
    # alphabets and every cancellation would fail to happen.
    by_name = {str(x): x for x in h.free_symbols}
    missing = [n for n in ("c1a", "c2a", "c1b", "c2b",
                           "gm_ia", "gm_fa", "gm_br", "gm_ib", "gm_fb")
               if n not in by_name]
    if missing:
        raise AssertionError(f"H(s) does not contain {missing}; free: {sorted(by_name)}")
    C1a, C2a, C1b, C2b = (by_name[n] for n in ("c1a", "c2a", "c1b", "c2b"))
    gia, gfa, gbr, gib, gfb = (by_name[f"gm_{x}"]
                               for x in ("ia", "fa", "br", "ib", "fb"))
    s = M.S
    # Biquad A, exactly the SSF form of doc/design-reference.md section 3, with the
    # single-ended load 2*C2a that the floating differential capacitor presents.
    D_A = gia * gfa + C1a * gfa * s + 2 * C1a * C2a * s ** 2
    # Biquad B, with the two things branch stacking does to it: the bridge's gm ADDS to
    # the shunt-feedback gm (the two devices share the node), and the bridge puts an extra
    # 2*C2b*gm_br damping term on the s coefficient.
    D_B = (gib * (gfb + gbr) + (C1b * (gfb + gbr) + 2 * C2b * gbr) * s
           + 2 * C1b * C2b * s ** 2)
    kappa = 2 * C1a * C2b * gbr * gib
    # `expand` is the zero test here, not `simplify`: the difference is a sum of exactly
    # cancelling monomials, and `simplify` is free to hand it back factored as s*(...)
    # without ever expanding the bracket -- which looks like a non-zero residual.
    residual = sp.expand(sp.expand(den) - sp.expand(D_A * D_B + kappa * s ** 2))
    if residual != 0:
        raise AssertionError(f"the factorisation is not an identity; residual {residual}")
    num_expected = gfa * gia * gib * (gbr + gfb)
    if sp.expand(sp.expand(num) - sp.expand(num_expected)) != 0:
        raise AssertionError(f"unexpected numerator {sp.factor(num)}")

    # The exact quartic, coefficient by coefficient -- this, not the decoupled product, is
    # the closed form the poles come from.  `coeffs` is what `closed_form_numbers`
    # evaluates at the measured operating point.
    poly = sp.Poly(sp.expand(den), s)
    coeffs = [sp.factor(c) for c in poly.all_coeffs()]

    w0a2 = gia * gfa / (2 * C1a * C2a)
    Qa = sp.sqrt(2 * C2a * gia / (C1a * gfa))
    w0b2 = gib * (gfb + gbr) / (2 * C1b * C2b)
    Qb = sp.sqrt(2 * C1b * C2b * gib * (gfb + gbr)) / (C1b * (gfb + gbr) + 2 * C2b * gbr)
    return {
        "_coeff_exprs": coeffs,      # sympy, in-process only; stripped before JSON
        "_symbols": {"C1a": C1a, "C2a": C2a, "C1b": C1b, "C2b": C2b,
                     "gm_ia": gia, "gm_fa": gfa, "gm_br": gbr,
                     "gm_ib": gib, "gm_fb": gfb},
        "quartic_coeffs": [str(c) for c in coeffs],
        "h_latex": sp.latex(h),
        "h_text": str(h),
        "numerator": str(sp.factor(num)),
        "denominator_factored": f"({sp.expand(D_A)}) * ({sp.expand(D_B)}) + ({kappa})*s**2",
        "D_A": str(sp.expand(D_A)), "D_B": str(sp.expand(D_B)), "kappa": str(kappa),
        "factorisation_residual": str(residual),
        "dc_gain": str(sp.simplify(h.subs(s, 0))),
        "w0a_sq": str(w0a2), "Q_a": str(Qa), "w0b_sq": str(w0b2), "Q_b": str(Qb),
        "cross_caps_doubled_f": doubled,
    }


def closed_form_numbers(bench: dict, roles_to_inst: dict, sym: dict) -> dict:
    """The poles from the CLOSED FORM, at the measured operating point.

    The quartic's coefficients are the symbolic ones, evaluated with the measured gm's and
    the design's own capacitors; its roots are the closed-form poles.  Reported alongside
    them, for contrast, is what the DECOUPLED two-biquad model would predict -- because
    the gap between the two is the whole point: the residual coupling term `kappa*s^2` is
    not a rounding error in this cell, it is what turns a (2.10, 0.46) pair of isolated
    stage Q's into the (0.54, 1.31) Butterworth pair the filter actually has.
    """
    op = bench["op"]
    gm = {r: abs(op[i]["gm"]) for r, i in roles_to_inst.items()}
    c = bench["caps_f"]
    subs = {sym["_symbols"]["C1a"]: c["c1_a"], sym["_symbols"]["C2a"]: c["c2_a"],
            sym["_symbols"]["C1b"]: c["c1_b"], sym["_symbols"]["C2b"]: c["c2_b"],
            sym["_symbols"]["gm_ia"]: gm["in_a"], sym["_symbols"]["gm_fa"]: gm["gmf_a"],
            sym["_symbols"]["gm_br"]: gm["bridge"], sym["_symbols"]["gm_ib"]: gm["in_b"],
            sym["_symbols"]["gm_fb"]: gm["gmf_b"]}
    coeffs = [float(cc.subs(subs)) for cc in sym["_coeff_exprs"]]
    roots = np.roots(coeffs)

    def pairs(rs):
        out = []
        for x, y in PZ.pair_up(np.array(sorted(rs, key=abs))):
            f0, q = PZ.biquad(x)
            out.append({"re": x.real, "im": x.imag, "f0_hz": f0, "Q": q,
                        "kind": "pair" if y is not None else "real"})
        return out

    # The decoupled model, for contrast only.
    gfb_eff = gm["gmf_b"] + gm["bridge"]
    w0a = np.sqrt(gm["in_a"] * gm["gmf_a"] / (2 * c["c1_a"] * c["c2_a"]))
    Qa = np.sqrt(2 * c["c2_a"] * gm["in_a"] / (c["c1_a"] * gm["gmf_a"]))
    w0b = np.sqrt(gm["in_b"] * gfb_eff / (2 * c["c1_b"] * c["c2_b"]))
    Qb = (np.sqrt(2 * c["c1_b"] * c["c2_b"] * gm["in_b"] * gfb_eff)
          / (c["c1_b"] * gfb_eff + 2 * c["c2_b"] * gm["bridge"]))
    kappa = 2 * c["c1_a"] * c["c2_b"] * gm["bridge"] * gm["in_b"]
    a2_full = coeffs[2]
    return {
        "gm_ns": {k: v * 1e9 for k, v in gm.items()},
        "caps_pf": {k: v * 1e12 for k, v in c.items()},
        "gmf_b_effective_ns": gfb_eff * 1e9,
        "quartic_coeffs": coeffs,
        "poles": pairs(roots),
        "f_c_geometric_hz": float(np.sqrt(abs(roots[0]) * abs(roots[-1])) / (2 * np.pi)),
        "decoupled": {"f0_a_hz": float(w0a / (2 * np.pi)), "Q_a": float(Qa),
                      "f0_b_hz": float(w0b / (2 * np.pi)), "Q_b": float(Qb)},
        "kappa": float(kappa),
        "coupling_ratio_s2": float(kappa / a2_full),
    }


# ------------------------------------------------------------ 3: the pole/zero map --
def pz_map(core: Path, bench_path: Path, level=Fidelity.FULL) -> dict:
    op = M.bind_op(bench_path)
    _ir, _ss, sysf = M.build(core, op, level=level)
    r = PZ.solve(sysf, OUT, DRIVE)
    poles = sorted(r.poles, key=lambda p: abs(p))
    zeros = sorted(r.zeros, key=lambda z: abs(z))

    # A pole and a zero at the same place is a mode the input cannot excite or the output
    # cannot see; report the cancellation instead of pretending the order is higher.
    # 1e-4 relative, not 1e-6: an exact cancellation comes back from two separate QZ
    # problems, so it is only exact to their conditioning.  The residual separation of
    # each cancelled pair is recorded, so "cancelled" stays a measurement.
    cancelled, kept_p, kept_z = [], list(poles), list(zeros)
    for p in poles:
        for z in list(kept_z):
            if abs(p - z) <= 1e-4 * max(abs(p), 1.0):
                cancelled.append({"s": [p.real, p.imag], "f_hz": abs(p) / (2 * np.pi),
                                  "residual_rel": float(abs(p - z) / max(abs(p), 1.0))})
                kept_z.remove(z)
                kept_p.remove(p)
                break

    def described(rs):
        out = []
        for a, b in PZ.pair_up(np.array(rs)) if len(rs) else []:
            f0, q = PZ.biquad(a)
            out.append({"re": a.real, "im": a.imag, "f0_hz": f0, "Q": q,
                        "kind": "pair" if b is not None else "real"})
        return out

    return {"n_poles": len(poles), "n_zeros": len(zeros),
            "dc_gain": [r.gain_dc.real, r.gain_dc.imag],
            "dc_gain_db": float(20 * np.log10(abs(r.gain_dc))),
            "poles": described(kept_p), "zeros": described(kept_z),
            "cancelled": cancelled,
            "poles_all": [[p.real, p.imag] for p in poles],
            "zeros_all": [[z.real, z.imag] for z in zeros]}


# ------------------------------------------------------ 4 + 5: validation and the fit --
def validate(core: Path, bench_path: Path) -> dict:
    rec = json.loads(Path(bench_path).read_text())
    op = M.bind_op(bench_path)
    _ir, _ss, sysf = M.build(core, op, level=Fidelity.FULL)
    f = np.asarray(rec["ac"]["f"], dtype=float)
    hs = np.asarray(rec["ac"]["re"]) + 1j * np.asarray(rec["ac"]["im"])
    hm = PZ.h_over(sysf, OUT, DRIVE, f)
    band = f <= 1000.0

    def gd(fx, h):
        ph = np.unwrap(np.angle(h))
        return -np.gradient(ph, 2 * np.pi * fx)

    mag = 20 * np.log10(np.abs(hm) / np.abs(hs))
    phs = np.degrees(np.angle(hm / hs))
    g_s, g_m = gd(f[band], hs[band]), gd(f[band], hm[band])
    return {
        "f": f.tolist(),
        "sim_db": (20 * np.log10(np.abs(hs))).tolist(),
        "model_db": (20 * np.log10(np.abs(hm))).tolist(),
        "sim_deg": np.degrees(np.unwrap(np.angle(hs))).tolist(),
        "model_deg": np.degrees(np.unwrap(np.angle(hm))).tolist(),
        "max_mag_err_db_scored": float(np.max(np.abs(mag[band]))),
        "max_phase_err_deg_scored": float(np.max(np.abs(phs[band]))),
        "max_mag_err_db_all": float(np.max(np.abs(mag))),
        "max_phase_err_deg_all": float(np.max(np.abs(phs))),
        "max_gd_err_pct": float(100 * np.max(np.abs((g_m - g_s) / np.maximum(np.abs(g_s), 1e-12)))),
        "gd_dc_ms_sim": float(g_s[0] * 1e3), "gd_dc_ms_model": float(g_m[0] * 1e3),
    }


def cap_ablation(core: Path, bench_path: Path) -> list[dict]:
    """Which device capacitance moves the poles, and which one makes the zeros?

    The closed form of (1) has no device capacitance in it and lands ~2 % high in `fc`;
    the full model has all of them and lands on the simulator.  Rather than assert which
    one closes the gap, zero one FAMILY of capacitance symbols at a time and re-solve.
    The answer is a measurement on the same matrices everything else uses.
    """
    base = M.bind_op(bench_path)
    rows = []
    for kill in (None, "cgs", "cgd", "cdb"):
        subs = dict(base.subs)
        n = 0
        for k in list(subs):
            if kill and k.startswith(kill + "_"):
                subs[k] = 0.0
                n += 1
        _ir, _ss, sysf = M.build(core, M.OpBinding(subs, base.per_instance, base.roles),
                                 level=Fidelity.FULL)
        r = PZ.solve(sysf, OUT, DRIVE)
        zs, ps = sorted(r.zeros, key=abs), sorted(r.poles, key=abs)
        kz = [z for z in zs if all(abs(z - q) > 1e-4 * max(abs(z), 1.0) for q in ps)]
        kp = [q for q in ps if all(abs(q - z) > 1e-4 * max(abs(q), 1.0) for z in zs)]
        rows.append({"zeroed": kill or "(none: the full model)", "n_symbols": n,
                     "pole_f_hz": sorted({round(abs(q) / (2 * np.pi), 2) for q in kp}),
                     "zero_f_hz": sorted({round(abs(z) / (2 * np.pi), 1) for z in kz})[:4],
                     "n_zeros_kept": len(kz)})
    return rows


def fit_poles_from_sim(bench_path: Path, model_poles: list[dict] | None = None) -> dict:
    """Fit a 4-pole/0-zero rational to the MEASURED response -- no small-signal model.

    Two conjugate pairs, parameterised as (f0, Q) each plus a dc gain, fitted to the
    complex response over 0.1 Hz-1 kHz in log-magnitude and unwrapped phase together.  It
    is the sim-only pole estimate the pole/zero plot is checked against.

    Two things are reported beyond the fitted parameters, because the (f0, Q) split of two
    NEARLY CO-LOCATED pairs is weakly conditioned -- the response pins the pole SET down
    far better than it pins either pair individually:

    * `quartic_coeffs_fit` / `quartic_coeffs_model` and their per-coefficient agreement:
      the MONIC quartic denominator, which the response determines well even when the
      (f0, Q) split between the two pairs does not.  This is the well-posed comparison.
    * `max_pole_distance_rel`: the fitted roots matched to the model roots individually.
      It is the LOOSE comparison and is reported so the conditioning is visible, not
      hidden.
    * `real_pole_refit`: the same fit with both Q's forced to <= 0.5, i.e. FOUR REAL POLES.
      If that refit cannot follow the data, the measured response by itself proves the
      poles are complex -- which is the reviewer's question, answered without the model.
    """
    rec = json.loads(Path(bench_path).read_text())
    f = np.asarray(rec["ac"]["f"], dtype=float)
    h = np.asarray(rec["ac"]["re"]) + 1j * np.asarray(rec["ac"]["im"])
    m = (f >= FIT_BAND[0]) & (f <= FIT_BAND[1])
    fb, hb = f[m], h[m]
    w = 2j * np.pi * fb

    def model(p):
        k, f0a, qa, f0b, qb = p
        wa, wb = 2 * np.pi * f0a, 2 * np.pi * f0b
        da = w ** 2 + (wa / qa) * w + wa ** 2
        db = w ** 2 + (wb / qb) * w + wb ** 2
        return k * (wa ** 2 * wb ** 2) / (da * db)

    def resid(p):
        hm = model(p)
        return np.concatenate([
            20 * np.log10(np.abs(hm)) - 20 * np.log10(np.abs(hb)),
            np.degrees(np.unwrap(np.angle(hm)) - np.unwrap(np.angle(hb))) / 10.0])

    def score(p):
        hm = model(p)
        return (float(np.max(np.abs(20 * np.log10(np.abs(hm)) - 20 * np.log10(np.abs(hb))))),
                float(np.max(np.abs(np.degrees(
                    np.unwrap(np.angle(hm)) - np.unwrap(np.angle(hb)))))))

    def roots_of(p):
        _k, f0a, qa, f0b, qb = p
        out = []
        for f0, q in ((f0a, qa), (f0b, qb)):
            w0 = 2 * np.pi * f0
            out += list(np.roots([1.0, w0 / q, w0 ** 2]))
        return out

    r = least_squares(resid, [1.0, 250.0, 0.54, 250.0, 1.31],
                      bounds=([0.5, 50, 0.3, 50, 0.3], [2.0, 2000, 5.0, 2000, 5.0]))
    k, f0a, qa, f0b, qb = r.x
    mag_db, ph_deg = score(r.x)

    # Falsification refit: Q <= 0.5 on both pairs is exactly "all four poles are real".
    rr = least_squares(resid, [1.0, 250.0, 0.5, 250.0, 0.5],
                       bounds=([0.5, 50, 0.05, 50, 0.05], [2.0, 5000, 0.5, 5000, 0.5]))
    rmag_db, rph_deg = score(rr.x)

    out = {"k": float(k), "f0_a_hz": float(f0a), "Q_a": float(qa),
           "f0_b_hz": float(f0b), "Q_b": float(qb),
           "max_mag_resid_db": mag_db, "max_phase_resid_deg": ph_deg,
           "band_hz": list(FIT_BAND), "n_points": int(m.sum()),
           "real_pole_refit": {"Q_a": float(rr.x[2]), "Q_b": float(rr.x[4]),
                               "f0_a_hz": float(rr.x[1]), "f0_b_hz": float(rr.x[3]),
                               "max_mag_resid_db": rmag_db,
                               "max_phase_resid_deg": rph_deg}}
    if model_poles:
        mp = []
        for d in model_poles:
            mp.append(complex(d["re"], d["im"]))
            if d["kind"] == "pair":
                mp.append(complex(d["re"], -d["im"]))
        fitted, used, worst = roots_of(r.x), set(), 0.0
        for z in fitted:
            j = min((i for i in range(len(mp)) if i not in used),
                    key=lambda i: abs(mp[i] - z), default=None)
            if j is None:
                break
            used.add(j)
            worst = max(worst, abs(mp[j] - z) / abs(mp[j]))
        out["max_pole_distance_rel"] = float(worst)
        out["fitted_poles"] = [[z.real, z.imag] for z in fitted]
        cf = np.real(np.poly(np.array(fitted)))
        cm = np.real(np.poly(np.array(mp)))
        out["quartic_coeffs_fit"] = cf.tolist()
        out["quartic_coeffs_model"] = cm.tolist()
        out["quartic_coeff_err_pct"] = [float(100 * (a - b) / b)
                                        for a, b in zip(cf[1:], cm[1:])]
    return out


ROLE_INST = {"in_a": "m2", "gmf_a": "m4", "bias_a_int": "m9", "bridge": "mst",
             "in_b": "m0", "gmf_b": "m14"}

CASES = {
    "pre_ideal": CORE_IDEAL,
    "pre_mim": CORE_MIM,
    "post_lumped": PACK / "data/post_lumped_core.sp",
}


def main() -> None:
    out = {"symbolic": symbolic_form(), "cases": {}}
    print("symbolic H(s) numerator:", out["symbolic"]["numerator"])
    print("factorisation residual :", out["symbolic"]["factorisation_residual"])
    for label, core in CASES.items():
        bench = PACK / f"data/bench_{label}.json"
        if not core.exists() or not bench.exists():
            print(f"[{label}] SKIPPED (missing {core if not core.exists() else bench})")
            continue
        rec = json.loads(bench.read_text())
        pz = pz_map(core, bench)
        case = {
            "core": str(core.relative_to(REPO)) if core.is_relative_to(REPO) else str(core),
            "closed_form": closed_form_numbers(rec, ROLE_INST, out["symbolic"]),
            "pz": pz,
            "validation": validate(core, bench),
            "sim_fit": fit_poles_from_sim(bench, pz["poles"]),
            "cap_ablation": cap_ablation(core, bench),
            "scorecard": rec["scorecard"],
        }
        out["cases"][label] = case
        cf, fit = case["closed_form"], case["sim_fit"]
        cfp = [p for p in cf["poles"] if p["kind"] == "pair"][:2]
        pairs = [p for p in case["pz"]["poles"] if p["kind"] == "pair"][:2]
        print(f"[{label}]")
        for i, p in enumerate(cfp):
            print(f"   closed form {i}: f0 {p['f0_hz']:8.3f} Q {p['Q']:.4f}")
        dd = cf["decoupled"]
        print(f"   decoupled   : A f0 {dd['f0_a_hz']:8.3f} Q {dd['Q_a']:.4f} | "
              f"B f0 {dd['f0_b_hz']:8.3f} Q {dd['Q_b']:.4f} | "
              f"coupling term {cf['coupling_ratio_s2'] * 100:.2f} % of a2")
        for i, p in enumerate(pairs):
            print(f"   exact pole {i}: f0 {p['f0_hz']:8.3f} Q {p['Q']:.4f}")
        print(f"   sim-only fit: A f0 {fit['f0_a_hz']:8.3f} Q {fit['Q_a']:.4f} | "
              f"B f0 {fit['f0_b_hz']:8.3f} Q {fit['Q_b']:.4f} | "
              f"resid {fit['max_mag_resid_db']:.4f} dB / {fit['max_phase_resid_deg']:.3f} deg")
        v = case["validation"]
        print(f"   model vs sim: {v['max_mag_err_db_scored']:.4f} dB, "
              f"{v['max_phase_err_deg_scored']:.4f} deg (<=1 kHz); "
              f"group delay {v['max_gd_err_pct']:.3f} %")
    out["symbolic"] = {k: v for k, v in out["symbolic"].items()
                       if not k.startswith("_")}
    (PACK / "data/tf.json").write_text(json.dumps(out))
    print("wrote data/tf.json")


if __name__ == "__main__":
    main()
