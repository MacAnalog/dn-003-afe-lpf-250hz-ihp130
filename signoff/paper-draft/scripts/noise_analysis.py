#!/usr/bin/env python
"""The noise equation, and its validation against the simulator's own per-generator data.

The claim under test is the textbook one, written for this cell:

    S_out(f) = SUM_k |Z_T,k(j2*pi*f)|^2 * S_i,k(f)          (output PSD, V^2/Hz)
    S_in(f)  = S_out(f) / |H(j2*pi*f)|^2                     (input-referred)
    IRN      = sqrt( INTEGRAL_0.5^200 S_in(f) df )           (S5)

where `Z_T,k` is the transimpedance from generator k's own port to the DIFFERENTIAL
output and `S_i,k` is that generator's current PSD.  Nothing here is asserted:

* `Z_T,k` is computed from the netlist2tf small-signal model -- `transimpedance` on the
  DM half-circuit (the package primitive, symbolic) and `pencil.z_transfer` on the full
  13-node cell (its numeric twin).  The two are compared, and agreeing is the licence to
  use the numeric one.
* `S_i,k` is NOT taken from a textbook.  `doc/design-reference.md` records, as a
  carried-forward hypothesis never re-measured here, that a MOS channel generator is
  `4*gamma*q*I_D` rather than `2*q*I_D`.  This script refuses to pick: it DIVIDES the
  simulator's own per-generator output density by the model's |Z_T| to recover S_i,k, and
  reports the measured ratio `S_i / (2*q*I_D)` per device.  That number is the finding.
* The whole sum is then checked against `onoise_spectrum`, and the integral against the
  certified `irn_uv`, using `lab.raw.integrate_noise`'s exact convention (trapezoid on the
  power over a log-spaced grid, with both band edges interpolated in log-frequency) --
  a different integration rule would manufacture a few-percent disagreement out of
  nothing.

Runs in the PLATFORM venv (needs `spicexplorer_netlist2tf`); reads only committed
netlists and `data/bench_*.json`.

    spicexplorer-platform/.venv/bin/python signoff/paper-draft/scripts/noise_analysis.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))

import n2tf_model as M  # noqa: E402
import pencil as PZ  # noqa: E402
from spicexplorer_netlist2tf import Fidelity, transimpedance  # noqa: E402

Q_E = 1.602176634e-19
K_B = 1.380649e-23
T_K = 300.15          # 27 degC, `lab.config.TEMP_NOM`

CORE = {
    "pre_ideal": REPO / "signoff/post-pvt/H12-robust/asbuilt/core.sp",
    "pre_mim": REPO / "signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp",
    # The post-layout model is the schematic devices + the extractor's Cext cards, not the
    # extracted device list -- see `extract_bench.post_lumped_netlist` for why, and for the
    # measured proof that the two are the same circuit (fc within 0.003 Hz, ph_max 0.05 deg).
    "post_lumped": None,
}
IRN_BAND = (0.5, 200.0)

# Candidate ports a generator's current source can sit across, as (terminal, terminal)
# of the device.  Which one each ngspice/PSP generator actually uses is NOT assumed here:
# `identify_port` below picks it from the data.  The physics only says the current has to
# flow between two of the device's own terminals.
CANDIDATE_PORTS = (("d", "s"), ("g", "s"), ("g", "d"), ("d", "b"), ("g", "b"), ("s", "b"))
# Generators that are series voltage sources (a terminal resistance), not shunt currents.
# All of them sit 5+ decades below the modelled generators in this cell, so they are
# reported and carried in the total but not attributed to a port.
GEN_UNMODELLED = ("rgate", "rdrain", "rsource", "rbulk", "rjund", "rjuns", "rwell")
# Expected log-log slope of the recovered current PSD: 0 for a white (shot) generator,
# about -1 for flicker.  Used only to LABEL the fit, never to constrain it.
GEN_EXPECTED_SLOPE = {"idid": 0.0, "igig": 0.0, "ibd": 0.0, "ididedge": 0.0,
                      "flicker": -1.0}


def identify_port(dens: np.ndarray, f: np.ndarray, ztab: dict, ports: dict[str, str],
                  ) -> tuple[tuple[str, str], float, float]:
    """Which terminal pair the generator sits across, decided by the data.

    A noise generator's own current PSD is a smooth power law in frequency -- flat for a
    shot generator, ~1/f for flicker.  The transimpedance `Z_T` to the differential output
    is emphatically NOT smooth: it carries the filter's two pole pairs.  So dividing the
    simulator's OUTPUT density by the |Z_T| of the WRONG port leaves the filter's own
    shape stamped all over the recovered `S_i`, and dividing by the right one does not.

    Returns (port, slope, worst deviation in dB, full ranking).  The deviation is the
    evidence that the port is right; the ranking's runner-up margin says how DECISIVE the
    choice is -- for a device whose gate sits on a quasi-ac-ground (a bias transistor), the
    (g,d) and (d,s) ports see almost the same Z_T and the test cannot separate them, which
    is a property of the circuit and is reported rather than hidden.
    """
    scored = []
    lf = np.log10(f)
    for port in CANDIDATE_PORTS:
        na, nb = ports[port[0]], ports[port[1]]
        if na == nb:
            continue
        z = np.abs(ztab[(na, nb)])
        if not np.all(z > 0):
            continue
        si = (dens / z) ** 2
        ls = np.log10(np.maximum(si, 1e-300))
        slope, intercept = np.polyfit(lf, ls, 1)
        dev_db = float(10 * np.max(np.abs(ls - (slope * lf + intercept))))
        scored.append((dev_db, port, float(slope)))
    scored.sort()
    dev_db, port, slope = scored[0]
    return port, slope, dev_db, [
        {"port": list(pp), "dev_db": dd, "slope": ss} for dd, pp, ss in scored]


# `onoise_n.<path>.<instance>.n<model>[_<generator>]`.  The model group must be anchored on
# the trailing `mos`: a lazy `sg13_\w+?` happily splits `nsg13_hv_pmos` into model
# `sg13_hv` + generator `pmos`, which turns every DEVICE TOTAL into a phantom generator and
# double-counts the whole sum by exactly 3 dB.
_KEY = re.compile(r"^onoise_n\.(?:xdut\.)?x?([\w$]+)\.n(sg13_\w+?mos)(?:_(\w+))?$")


def parse_contrib(noise: dict) -> tuple[dict, dict, np.ndarray]:
    """({(inst, gen): density}, {inst: device total}, f) from the raw noise vectors.

    ngspice emits an `onoise_...` vector per device AND one per generator inside it; the
    values are output-referred voltage DENSITIES (V/rtHz) that combine in power, which is
    asserted below: the device total must be the rss of its generators.
    """
    f = np.asarray(noise["f"], dtype=float)
    per_gen: dict[tuple[str, str], np.ndarray] = {}
    totals: dict[str, np.ndarray] = {}
    for key, vals in noise["contrib"].items():
        m = _KEY.match(key)
        if not m:
            continue
        inst, _model, gen = m.group(1), m.group(2), m.group(3)
        v = np.asarray(vals, dtype=float)
        if gen is None:
            totals[inst] = v
        else:
            per_gen[(inst, gen)] = v
    for inst, tot in totals.items():
        rss = np.sqrt(sum(v ** 2 for (i, _g), v in per_gen.items() if i == inst))
        bad = np.max(np.abs(rss - tot) / np.maximum(tot, 1e-30))
        if bad > 1e-6:
            raise ValueError(f"{inst}: generators do not rss to the device total "
                             f"(worst {bad:.3g}) -- the V/rtHz reading is wrong")
    return per_gen, totals, f


def integrate_noise(f: np.ndarray, dens: np.ndarray, lo: float, hi: float) -> float:
    """`lab.raw.integrate_noise`, re-implemented here so this script can run in the
    platform venv.  Kept byte-identical in behaviour: trapezoid on the POWER against a
    LINEAR frequency axis, with both band edges added by interpolating the density in
    log-frequency, so 0.5 Hz and 200 Hz are exact endpoints of the integral."""
    lf, ld = np.log10(f), np.log10(np.maximum(dens, 1e-300))
    edges = [lo, hi]
    fx = np.concatenate([f[(f > lo) & (f < hi)], edges])
    fx = np.unique(np.sort(fx))
    dx = 10 ** np.interp(np.log10(fx), lf, ld)
    return float(np.sqrt(np.trapezoid(dx ** 2, fx)))


def device_ports(core_sp: Path, pex: bool = False) -> dict[str, dict[str, str]]:
    """{instance: {d,g,s,b}} straight off the as-built netlist."""
    txt = Path(core_sp).read_text().replace("$", "_")
    out = {}
    for m in re.finditer(
            r"(?im)^\s*x(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(sg13_\w+mos)\b", txt):
        out[m.group(1).lower()] = {"d": m.group(2), "g": m.group(3),
                                   "s": m.group(4), "b": m.group(5)}
    return out


def cross_check_transimpedance(core_sp: Path, op) -> dict:
    """Run the package primitive and the numeric pencil on the SAME half-circuit port.

    `spicexplorer_netlist2tf.transimpedance` solves it symbolically by Cramer's rule;
    `pencil.z_transfer` solves the identical system by dense LU per frequency.  They must
    agree to round-off, and that is what licenses using the pencil on the full cell where
    the symbolic solve does not finish.
    """
    _ir, _ss, sysh, _dbl = M.build_half(core_sp, op, level=Fidelity.FULL)
    f = np.array([0.5, 5.0, 50.0, 250.0, 1000.0])
    # gmf_a's channel generator: drain vout_1, source 0.  Both the input node vinp and the
    # axis nets are already ac grounds in the half-circuit build.
    raw = transimpedance(sysh, ("voutp", "0"), ("vout_1", "0"))
    lam = __import__("sympy").lambdify(__import__("sympy").Symbol("s"), raw.expr, "numpy")
    zsym = np.array([complex(lam(2j * np.pi * x)) for x in f])
    # No source-zeroing here: the two solvers must see the IDENTICAL system, and the
    # package primitive has no way to ground a node after the fact.
    znum = PZ.z_transfer(sysh, ("voutp", "0"), ("vout_1", "0"), (), f)
    rel = np.max(np.abs(zsym - znum) / np.abs(zsym))
    return {"f_hz": f.tolist(), "z_symbolic_ohm": np.abs(zsym).tolist(),
            "z_pencil_ohm": np.abs(znum).tolist(), "max_rel_diff": float(rel)}


def core_netlist(label: str) -> Path:
    """The netlist the small-signal model is built from, materialised on disk."""
    if CORE[label] is not None:
        return CORE[label]
    sys.path.insert(0, str(HERE))
    import extract_bench as EB
    out = PACK / "data/post_lumped_core.sp"
    out.write_text(EB.post_lumped_netlist())
    return out


def analyse(label: str) -> dict:
    rec = json.loads((PACK / f"data/bench_{label}.json").read_text())
    core = core_netlist(label)
    op = M.bind_op(PACK / f"data/bench_{label}.json")
    mirror = None
    _ir, _ss, sysf = M.build(core, op, level=Fidelity.FULL, mirror_from=mirror)

    per_gen, totals, f = parse_contrib(rec["noise"])
    ports = device_ports(core)
    ports["mbn"] = {"d": "vbn", "g": "vbn", "s": "0", "b": "0"}

    # Source-zeroing: with the signal source off the balun holds both inputs at their dc
    # level, so vinp and vinn are ac grounds for every noise solve.
    grounded = ("vinp", "vinn")
    hs = np.asarray(rec["ac"]["re"]) + 1j * np.asarray(rec["ac"]["im"])
    fac = np.asarray(rec["ac"]["f"], dtype=float)
    h_noise = np.interp(f, fac, np.abs(hs))

    # Pre-compute every transimpedance any candidate port could need, once.
    ztab: dict[tuple[str, str], np.ndarray] = {}
    for inst, p in ports.items():
        for a, b in CANDIDATE_PORTS:
            key = (p[a], p[b])
            if key[0] != key[1] and key not in ztab:
                ztab[key] = PZ.z_transfer(sysf, ("voutp", "voutn"), key, grounded, f)

    rows, model_power = [], np.zeros_like(f)
    for (inst, gen), dens in sorted(per_gen.items()):
        p = ports.get(inst)
        model_power += dens ** 2
        if p is None or gen in GEN_UNMODELLED or not np.any(dens > 0):
            rows.append({"inst": inst, "role": op.roles.get(inst), "gen": gen,
                         "modelled": False,
                         "onoise_uv_rms": integrate_noise(f, dens, *IRN_BAND) * 1e6,
                         "irn_uv_rms": integrate_noise(f, dens / h_noise, *IRN_BAND) * 1e6})
            continue
        port, slope, dev_db, ranking = identify_port(dens, f, ztab, p)
        z = np.abs(ztab[(p[port[0]], p[port[1]])])
        si = (dens / np.maximum(z, 1e-300)) ** 2
        idd = abs(rec["op"].get(inst, {}).get("ids", float("nan")))
        gm = abs(rec["op"].get(inst, {}).get("gm", float("nan")))
        si10 = float(np.interp(10.0, f, si))
        rows.append({
            "inst": inst, "role": op.roles.get(inst), "gen": gen, "modelled": True,
            "port": list(port), "port_nets": [p[port[0]], p[port[1]]],
            "fit_slope": slope, "fit_dev_db": dev_db,
            "port_ranking": ranking,
            "port_margin_db": (ranking[1]["dev_db"] - dev_db) if len(ranking) > 1 else None,
            "expected_slope": GEN_EXPECTED_SLOPE.get(gen),
            "id_na": idd * 1e9, "gm_ns": gm * 1e9,
            "z_dc_gohm": float(z[0] / 1e9),
            "z_at_fc_gohm": float(np.interp(250.0, f, z) / 1e9),
            "si_at_10hz_a2_hz": si10,
            # The two normalisations the literature argues about, both reported, neither
            # assumed: shot (2*q*I_D) and thermal (4*k*T*gm).
            "si_over_2qid": si10 / (2 * Q_E * idd) if idd > 0 else None,
            "si_over_4ktgm": si10 / (4 * K_B * T_K * gm) if gm > 0 else None,
            # If this generator IS shot noise, the dc current it implies.
            "implied_dc_current_na": si10 / (2 * Q_E) * 1e9,
            "onoise_uv_rms": integrate_noise(f, dens, *IRN_BAND) * 1e6,
            "irn_uv_rms": integrate_noise(f, dens / h_noise, *IRN_BAND) * 1e6,
        })

    onoise = np.asarray(rec["noise"]["onoise"], dtype=float)
    inoise = np.asarray(rec["noise"]["inoise"], dtype=float)
    sum_dens = np.sqrt(model_power)
    irn_sim = integrate_noise(f, inoise, *IRN_BAND) * 1e6
    irn_sum = integrate_noise(f, sum_dens / h_noise, *IRN_BAND) * 1e6

    return {
        "label": label,
        "f": f.tolist(),
        "onoise_sim": onoise.tolist(),
        "onoise_sum_of_generators": sum_dens.tolist(),
        "inoise_sim": inoise.tolist(),
        "h_mag": h_noise.tolist(),
        "rows": rows,
        "irn_uv_sim": irn_sim,
        "irn_uv_sum_of_generators": irn_sum,
        "irn_uv_certified": rec["scorecard"].get("irn_uv"),
        "onoise_closure_max_pct": float(
            100 * np.max(np.abs(sum_dens - onoise) / np.maximum(onoise, 1e-30))),
        "inoise_vs_onoise_over_h_max_pct": float(
            100 * np.max(np.abs(onoise / h_noise - inoise) / np.maximum(inoise, 1e-30))),
        "transimpedance_cross_check": cross_check_transimpedance(core, op),
    }


# ----------------------------------------------- the raw extraction, model-free --

def roles_by_nets(rec: dict, ref: str = "pre_mim") -> dict:
    """Instance -> design role for a DUT whose instance NAMES carry no role.

    kpex renames every device and splits each drawn transistor into its layout fingers,
    so `xm_1 ... xm_35` cannot be matched to `in_a`/`gmf_b`/... by name.  The WIRING still
    can be: each finger keeps the schematic's own net names, and in this cell every role
    has a unique (gate, {drain, source}, bulk) net signature -- drain and source as an
    unordered pair because the extractor labels a finger's two diffusions by geometry and
    freely swaps them.  Both halves of that claim are asserted, so a topology change that
    broke the uniqueness would stop the script rather than mislabel a device.
    """
    sch = json.loads((PACK / f"data/bench_{ref}.json").read_text())["op"]

    def sig(n):
        return (frozenset((n["d"], n["s"])), n["g"], n["b"])

    table: dict = {}
    for inst, o in sch.items():
        if not o.get("nets"):
            continue
        k = sig(o["nets"])
        if k in table and table[k] != (o.get("role") or inst):
            raise ValueError(f"net signature {k} is not unique in {ref}: "
                             f"{table[k]} and {o.get('role')}")
        table[k] = o.get("role") or inst
    # Keyed lower-case: the op probe reads the instance name off the netlist card while
    # the noise vectors come back from ngspice, which lower-cases everything.
    out = {}
    for inst, o in rec["op"].items():
        if not o.get("nets"):
            continue
        k = sig(o["nets"])
        if k not in table:
            raise ValueError(f"{inst}: net signature {k} has no counterpart in {ref}")
        out[inst.lower()] = table[k]
    missing = {i.lower() for i in rec["op"]} - set(out)
    if missing:
        raise ValueError(f"unresolved instances: {sorted(missing)}")
    return out


def analyse_measured(label: str, ref: str = "pre_mim") -> dict:
    """The noise budget of a DUT the small-signal model cannot be built on.

    `analyse` needs `n2tf_model.bind_op`, which folds `gmb`/`cgb` on the `bulk == source`
    identity and therefore refuses the raw extraction (kpex leaves an n-channel finger
    whose source is not its bulk).  Everything in this function comes out of the
    SIMULATOR instead: the per-generator output densities ngspice emits, referred to the
    input through `onoise/inoise` -- which is the simulator's own |H|, so no model enters
    -- and the per-instance `id`/`gm` from the same operating point.  What is therefore
    absent, and only this, is the model-derived half of `analyse`'s row: the port
    identification and the `Z_T`-normalised current PSD (`si_over_2qid`, `si_over_4ktgm`).
    Those stay on `post_lumped`, which is the same layout's parasitics on a device list
    the model does accept.
    """
    rec = json.loads((PACK / f"data/bench_{label}.json").read_text())
    per_gen, _totals, f = parse_contrib(rec["noise"])
    onoise = np.asarray(rec["noise"]["onoise"], float)
    inoise = np.asarray(rec["noise"]["inoise"], float)
    h_noise = np.where(inoise > 0, onoise / np.maximum(inoise, 1e-300), 1.0)
    roles = roles_by_nets(rec, ref)

    op_lc = {k.lower(): v for k, v in rec["op"].items()}
    rows = []
    for (inst, gen), dens in sorted(per_gen.items()):
        o = op_lc.get(inst.lower(), {})
        rows.append({
            "inst": inst, "role": roles.get(inst), "gen": gen, "modelled": None,
            "id_na": None if o.get("ids") is None else 1e9 * abs(o["ids"]),
            "gm_ns": None if o.get("gm") is None else 1e9 * o["gm"],
            "onoise_uv_rms": 1e6 * integrate_noise(f, dens, *IRN_BAND),
            "irn_uv_rms": 1e6 * integrate_noise(f, dens / h_noise, *IRN_BAND),
        })
    rows.sort(key=lambda r: -r["irn_uv_rms"])

    sum_dens = np.sqrt(sum(v ** 2 for v in per_gen.values()))
    irn_sim = 1e6 * integrate_noise(f, inoise, *IRN_BAND)
    irn_sum = float(np.sqrt(sum(r["irn_uv_rms"] ** 2 for r in rows)))   # already uV
    return {
        "label": label,
        "measured_only": True,
        "role_source": ref,
        "f": f.tolist(),
        "onoise_sim": onoise.tolist(),
        "onoise_sum_of_generators": sum_dens.tolist(),
        "inoise_sim": inoise.tolist(),
        "h_mag": h_noise.tolist(),
        "rows": rows,
        "irn_uv_sim": irn_sim,
        "irn_uv_sum_of_generators": irn_sum,
        "irn_uv_certified": rec["scorecard"].get("irn_uv"),
        "onoise_closure_max_pct": float(
            100 * np.max(np.abs(sum_dens - onoise) / np.maximum(onoise, 1e-30))),
        "inoise_vs_onoise_over_h_max_pct": 0.0,
        "transimpedance_cross_check": None,
    }


def main() -> None:
    out = {}
    for label in ("pre_ideal", "pre_mim", "post_lumped", "post_pex"):
        # `post_pex` is the raw extraction: measured lane only, for the reason in
        # `analyse_measured`'s docstring.
        r = analyse_measured(label) if label == "post_pex" else analyse(label)
        out[label] = r
        print(f"[{label}] IRN sim {r['irn_uv_sim']:.4f} uV | certified "
              f"{r['irn_uv_certified']:.4f} | sum-of-generators "
              f"{r['irn_uv_sum_of_generators']:.4f} uV | onoise closure "
              f"{r['onoise_closure_max_pct']:.4g} %"
              + ("  [measured only]" if r.get("measured_only") else ""))
        cc = r["transimpedance_cross_check"]
        if cc:
            print(f"          netlist2tf.transimpedance vs pencil: "
                  f"max rel diff {cc['max_rel_diff']:.3g}")
    (PACK / "data/noise.json").write_text(json.dumps(out))
    print("wrote data/noise.json")


if __name__ == "__main__":
    main()
