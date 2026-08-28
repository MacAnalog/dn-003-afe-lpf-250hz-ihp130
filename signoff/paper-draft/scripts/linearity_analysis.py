#!/usr/bin/env python
"""The linearity equations -- HD3, THD, IMD3, IIP3 -- and their check against simulation.

The model is the one the topology forces, and it reuses the SAME machinery as the noise
analysis, which is the point: a device's distortion current and its noise current are
injected at the same port and reach the output through the same transimpedance `Z_T`.

**Generation.**  Every device is in weak inversion, so `I_D = I_S * exp(v_gs / (n*U_T))`
exactly.  With `v_gs` a sinusoid of peak `V_e`, put `a = V_e / (n*U_T)`; then

    exp(a cos wt) = I0(a) + 2*SUM_k Ik(a) cos k*wt          (modified Bessel)
    third-harmonic drain current:  i3 = I_D * 2*I3(a) -> I_D * a^3 / 24   (a << 1)
    second-harmonic drain current: i2 = I_D * 2*I2(a) -> I_D * a^2 / 4

so each device injects a third-harmonic current at its own drain of `I_D * a^3 / 24`.
`a` is NOT a free parameter: `n` comes from the measured `gm/I_D` (`n = 1/(gm/I_D * U_T)`)
and `V_e = |v_gs(jw)|` is read straight out of the exact small-signal model at the drive
amplitude -- the follower's gate-minus-source excursion, which the shunt feedback makes
small and STRONGLY frequency dependent.

**Propagation.**  `i3` sits across drain-source, exactly where the channel noise generator
sits (`noise_analysis.py` establishes that port from the data), so the output third
harmonic is `Z_T(j*3w) * i3` and

    HD3(w) = | SUM_k Z_T,k(j3w) * I_D,k * a_k(w)^3 / 24 |  /  |V_out,fund(w)|

**Three predictions, all falsifiable and all tested here:**

 1. `HD3 ~ A^2` at fixed frequency (a^3 over a linear fundamental).  Tested on the
    amplitude ladder.
 2. `HD3` rises steeply with frequency, because shunt feedback makes `V_e` grow with w --
    at low frequency `|1 - H| -> w*C1/gm_i`, so `V_e ~ w` and `HD3 ~ w^2` (40 dB/decade).
    Tested on the 43.75 mVpp HD3-vs-fin sweep.
 3. Because of (2) the cell is emphatically NOT memoryless, so the textbook identity
    `IMD3 = HD3 + 9.54 dB` must fail.  Tested directly, and the failure is attributed:
    the spacing sweep shows IMD3 moves < 2 dB over a 15x change in tone spacing, so the
    excess is frequency dependence of the third-order response, not envelope memory.

    spicexplorer-platform/.venv/bin/python signoff/paper-draft/scripts/linearity_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.special import iv as _besseli

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))

import n2tf_model as M  # noqa: E402
import pencil as PZ  # noqa: E402
from spicexplorer_netlist2tf import Fidelity  # noqa: E402

U_T = 1.380649e-23 * 300.15 / 1.602176634e-19        # kT/q at 27 C, 25.86 mV
CORE_MIM = REPO / "signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp"
BENCH = PACK / "data/bench_pre_mim.json"
DRIVE = {"vinp": 0.5, "vinn": -0.5}
OUT = ("voutp", "voutn")
# Every device whose gate-source voltage carries signal, BOTH halves.  A bias device's
# gate sits on a quiet rail, so its `v_gs` is ~0 and it generates no distortion however
# noisy it is -- which is exactly the asymmetry between this cell's noise budget (led by
# `bias_a_int`) and its distortion budget (led by `in_b` and `gmf_a`).
#
# Both halves must be summed, and they add rather than cancel: under a differential drive
# the N half sees `v_gs_N = -v_gs_P`, so its third-harmonic current is `-i3_P` (an odd
# power), and its transimpedance to `voutp - voutn` is also negated -- the two minus signs
# multiply out.  The differential structure cancels the EVEN harmonics, not the odd ones.
SIGNAL_DEVS = ("m2", "m5", "m4", "m8", "mst", "mstn", "m0", "m1", "m14", "m15")


def node_response(system, drive, f_hz, nets):
    """Complex node voltages for a unit differential drive, at one frequency."""
    G, C, _ = PZ.split_gc(system)
    import scipy.linalg as la
    n = G.shape[0]
    idx_in = [system.row_of(k) for k in drive]
    u = np.array([drive[k] for k in drive], dtype=float)
    rest = [i for i in range(n) if i not in idx_in]
    Y = G + 2j * np.pi * f_hz * C
    v = la.solve(Y[np.ix_(rest, rest)], -Y[np.ix_(rest, idx_in)] @ u)
    out = {}
    for net in nets:
        r = system.row_of(net)
        if r is None:
            out[net] = 0j
        elif r in idx_in:
            out[net] = complex(drive[net])
        else:
            out[net] = complex(v[rest.index(r)])
    return out


def hd3_model(fins, ampl_diff) -> dict:
    """Predicted HD3 versus input frequency at a fixed differential drive amplitude.

    `ampl_diff` is the DIFFERENTIAL amplitude (the bench's `ampl`), so each half is driven
    by +-ampl_diff/2 -- the balun convention of `doc/benches.md`.
    """
    rec = json.loads(BENCH.read_text())
    op = M.bind_op(BENCH)
    _ir, _ss, sysf = M.build(CORE_MIM, op, level=Fidelity.FULL)

    ports = {}
    for m in __import__("re").finditer(
            r"(?im)^\s*x(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+sg13_\w+mos\b",
            CORE_MIM.read_text()):
        ports[m.group(1).lower()] = {"d": m.group(2), "g": m.group(3), "s": m.group(4)}

    nets = sorted({v for p in ports.values() for v in p.values()} | {"voutp", "voutn"})
    dev = {}
    for inst in SIGNAL_DEVS:
        o = rec["op"][inst]
        gm_id = abs(o["gm"]) / abs(o["ids"])
        dev[inst] = {"role": o["role"], "id": abs(o["ids"]),
                     "n": 1.0 / (gm_id * U_T), "gm_id": gm_id, "port": ports[inst]}

    rows = []
    for fin in fins:
        v1 = node_response(sysf, DRIVE, fin, nets)
        vout = v1["voutp"] - v1["voutn"]
        terms = []
        for inst, d in dev.items():
            p = d["port"]
            vgs = (v1[p["g"]] - v1[p["s"]]) * ampl_diff       # volts, complex
            a = abs(vgs) / (d["n"] * U_T)
            # Third-harmonic drain current.  The EXACT exponential result is used, not
            # its `a^3/24` small-signal truncation: `exp(a cos wt)` has harmonic content
            # `2*Ik(a)` against a dc term `I0(a)`, and the measured `I_D` already includes
            # that dc term, so `i3 = I_D * 2*I3(a)/I0(a)`.  The two agree to 1 % below
            # a = 0.3 and diverge above it, which is exactly where this sweep goes.
            i3 = (d["id"] * 2 * _besseli(3, a) / _besseli(0, a)
                  * np.exp(3j * np.angle(vgs)))
            z3 = PZ.z_transfer(sysf, OUT, (p["d"], p["s"]), ("vinp", "vinn"),
                               np.array([3 * fin]))[0]
            terms.append({"inst": inst, "role": d["role"], "a": a,
                          "i3_over_a3_24": float(2 * _besseli(3, a) / _besseli(0, a)
                                                 / max(a ** 3 / 24, 1e-30)),
                          "vgs_mv": abs(vgs) * 1e3, "n": d["n"],
                          "i3_a": abs(i3), "z3_gohm": abs(z3) / 1e9,
                          "v3": complex(z3 * i3)})
        v3_coh = sum(t["v3"] for t in terms)
        v3_max = sum(abs(t["v3"]) for t in terms)
        fund = abs(vout) * ampl_diff
        rows.append({
            "fin": fin,
            "hd3_db_coherent": float(20 * np.log10(abs(v3_coh) / fund)),
            "hd3_db_worstcase": float(20 * np.log10(v3_max / fund)),
            "fund_vpp": float(2 * fund),
            "v3_model_v": float(abs(v3_coh)),
            "a_max": float(max(t["a"] for t in terms)),
            "terms": [{k: (abs(v) if k == "v3" else v) for k, v in t.items()}
                      for t in terms],
            "dominant": max(terms, key=lambda t: abs(t["v3"]))["role"],
        })
    return {"ampl_diff": ampl_diff, "rows": rows,
            "devices": {k: {kk: vv for kk, vv in v.items() if kk != "port"}
                        for k, v in dev.items()}}


def fit_power_law(x, y_db) -> tuple[float, float]:
    """Slope in dB per decade, and the worst residual, of y_db against log10(x)."""
    lx = np.log10(np.asarray(x, dtype=float))
    yy = np.asarray(y_db, dtype=float)
    m, b = np.polyfit(lx, yy, 1)
    return float(m), float(np.max(np.abs(yy - (m * lx + b))))


def main() -> None:
    lin = json.loads((PACK / "data/linearity.json").read_text())
    hd3f = json.loads((PACK / "data/hd3_vs_fin.json").read_text())
    spac = json.loads((PACK / "data/twotone_spacing.json").read_text())

    out: dict = {}

    # ---- prediction 1: HD3 ~ A^2 -------------------------------------------------
    lad = lin["thd_ladder"]["pre_mim"]
    lin_pts = [r for r in lad if r["hd3_db"] < -45]          # the uncompressed end
    slope, dev = fit_power_law([r["vpp_diff"] for r in lin_pts],
                               [r["hd3_db"] for r in lin_pts])
    out["amplitude_law"] = {
        "fitted_slope_db_per_decade": slope, "expected_slope_db_per_decade": 40.0,
        "max_residual_db": dev,
        "points": [{"vpp_diff": r["vpp_diff"], "hd3_db": r["hd3_db"]} for r in lin_pts],
        "all_points": lad,
    }
    # The drive at which total THD reaches the -40 dB spec limit, from the A^2 law.
    ref = lin_pts[-1]
    out["amplitude_law"]["thd_minus40_vpp"] = float(
        ref["vpp_diff"] * 10 ** ((-40.0 - ref["thd_db"]) / slope))

    # ---- prediction 2: HD3 versus frequency, model vs measurement -----------------
    meas = hd3f["rows"]
    model = hd3_model([r["fin"] for r in meas], hd3f["ampl"])
    pairs = [(m["fin"], m["hd3_db"], p["hd3_db_coherent"], p["hd3_db_worstcase"],
              p["dominant"])
             for m, p in zip(meas, model["rows"])]
    err = [abs(a - b) for _f, a, b, _c, _d in pairs]
    lo = [(f, a, b) for f, a, b, _c, _d in pairs if f <= 65]
    out["frequency_law"] = {
        "ampl_diff": hd3f["ampl"], "vpp_diff": hd3f["vpp_diff"],
        "measured_slope_db_per_decade": fit_power_law(
            [f for f, _a, _b, _c, _d in pairs if f <= 50],
            [a for f, a, _b, _c, _d in pairs if f <= 50])[0],
        "rows": [{"fin": f, "hd3_measured_db": a, "hd3_model_db": b,
                  "hd3_model_worstcase_db": c, "dominant": d, "err_db": a - b}
                 for f, a, b, c, d in pairs],
        "max_err_db": float(max(err)),
        "max_err_db_below_65hz": float(max(abs(a - b) for _f, a, b in lo)),
        # Where the cubic-in-v_gs mechanism is BOTH the dominant one and still small
        # signal: 35-100 Hz, which brackets the S7 spec point.
        "max_err_db_35_to_100hz": float(max(
            abs(a - b) for f, a, b, _c, _d in pairs if 35 <= f <= 100)),
        # The residual third harmonic the model does not explain, as an absolute voltage.
        # It is nearly frequency-INDEPENDENT at the low end, where the modelled mechanism
        # (which scales with the feedback error, hence with w) has almost vanished --
        # consistent with a swing-driven mechanism such as the drain-conductance
        # nonlinearity, which this model does not contain.  Stated as an observation with
        # its numbers, not as a fitted claim.
        "residual_v3_uv": [
            {"fin": f,
             "v3_measured_uv": 1e6 * 10 ** (a / 20) * p["fund_vpp"] / 2,
             "v3_model_uv": 1e6 * p["v3_model_v"],
             "v3_unexplained_uv": 1e6 * (10 ** (a / 20) * p["fund_vpp"] / 2
                                         - p["v3_model_v"])}
            for (f, a, b, _c, _d), p in zip(pairs, model["rows"])],
        "model_detail": model,
    }

    # ---- prediction 3: the memoryless identity, and whether it is memory ----------
    tt = lin["twotone"]["pre_mim"]
    A_REF = 21.875e-3
    tt_ref = min(tt, key=lambda r: abs(r["ampl_per_tone_v"] - A_REF))
    hd3_ref = min(meas, key=lambda r: abs(r["fin"] - 50.0))
    out["memoryless_test"] = {
        "per_tone_ampl_v": tt_ref["ampl_per_tone_v"],
        "single_tone_ampl_v": hd3f["ampl"],
        "hd3_at_50hz_db": hd3_ref["hd3_db"],
        "imd3_measured_db": tt_ref["imd3_db"],
        "imd3_memoryless_prediction_db": hd3_ref["hd3_db"] + 9.542,
        "excess_db": tt_ref["imd3_db"] - (hd3_ref["hd3_db"] + 9.542),
        "spacing_sweep": spac["rows"],
        "imd3_spread_over_spacing_db": float(
            max(r["imd3_db"] for r in spac["rows"])
            - min(r["imd3_db"] for r in spac["rows"])),
        "spacing_ratio": float(max(r["spacing"] for r in spac["rows"])
                               / min(r["spacing"] for r in spac["rows"])),
    }

    # ---- IIP3 ---------------------------------------------------------------------
    for label in ("pre_mim", "post_pex"):
        rows = lin["twotone"][label]
        lin_rows = [r for r in rows if r["imd3_db"] < -40]
        sl, dv = fit_power_law([r["ampl_per_tone_v"] for r in lin_rows],
                               [r["imd3_db"] for r in lin_rows])
        out.setdefault("iip3", {})[label] = {
            "iip3_dbv": float(np.mean([r["iip3_dbv"] for r in lin_rows[:2]])),
            "iip3_v_peak_per_tone": float(10 ** (np.mean(
                [r["iip3_dbv"] for r in lin_rows[:2]]) / 20)),
            "oip3_dbv": float(np.mean([r["oip3_dbv"] for r in lin_rows[:2]])),
            "imd3_slope_db_per_decade": sl, "expected_slope_db_per_decade": 40.0,
            "slope_residual_db": dv,
            "consistency_of_iip3_over_linear_points_db": float(
                max(r["iip3_dbv"] for r in lin_rows) - min(r["iip3_dbv"] for r in lin_rows)),
            "points": rows,
        }

    (PACK / "data/linearity_analysis.json").write_text(json.dumps(out))
    a = out["amplitude_law"]
    print(f"HD3 vs amplitude : {a['fitted_slope_db_per_decade']:.2f} dB/decade "
          f"(A^2 law = 40), residual {a['max_residual_db']:.3f} dB; "
          f"THD hits -40 dB at {a['thd_minus40_vpp'] * 1e3:.1f} mVpp")
    fr = out["frequency_law"]
    print(f"HD3 vs frequency : measured slope {fr['measured_slope_db_per_decade']:.1f} "
          f"dB/decade; model error max {fr['max_err_db']:.2f} dB "
          f"({fr['max_err_db_below_65hz']:.2f} dB below 65 Hz)")
    for r in fr["rows"]:
        print(f"    fin {r['fin']:6.1f}  meas {r['hd3_measured_db']:8.2f}  "
              f"model {r['hd3_model_db']:8.2f}  err {r['err_db']:+7.2f}  "
              f"dominant {r['dominant']}")
    mt = out["memoryless_test"]
    print(f"memoryless test  : HD3 {mt['hd3_at_50hz_db']:.2f} -> predicts IMD3 "
          f"{mt['imd3_memoryless_prediction_db']:.2f}, measured "
          f"{mt['imd3_measured_db']:.2f} ({mt['excess_db']:+.2f} dB excess); "
          f"IMD3 moves {mt['imd3_spread_over_spacing_db']:.2f} dB over a "
          f"{mt['spacing_ratio']:.0f}x spacing change")
    for k, v in out["iip3"].items():
        print(f"IIP3 [{k}] {v['iip3_dbv']:.3f} dBV "
              f"({v['iip3_v_peak_per_tone'] * 1e3:.0f} mV peak/tone); IMD3 slope "
              f"{v['imd3_slope_db_per_decade']:.1f} dB/dec; IIP3 spread "
              f"{v['consistency_of_iip3_over_linear_points_db']:.3f} dB")
    print("wrote data/linearity_analysis.json")


if __name__ == "__main__":
    main()
