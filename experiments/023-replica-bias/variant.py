"""One THD-aware variant of a built candidate: caps from a chosen Q assignment,
polished, then scorecard + THD + axes.  Run many in parallel (one process each).

    uv run python variant.py <src> <out> --qa <Q> --qb <Q> [--k K] [--dev role w l]... [--polish N]
"""
from __future__ import annotations
import argparse, json
from common import (HERE, AXES, Dev, K, M, O, from_json, to_json, caps_for, gms,
                    synth_from, load_cell, replica)
from lab import shape as S, thd as T
from lab.dut import replace

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--qa", type=float, default=None); ap.add_argument("--qb", type=float, default=None)
ap.add_argument("--k", type=float, default=None)
ap.add_argument("--vicm", type=float, default=None)
ap.add_argument("--dev", nargs=3, action="append", default=[], metavar=("ROLE", "W_UM", "L_UM"))
ap.add_argument("--polish", type=int, default=150)
ap.add_argument("--caps", nargs=4, type=float, default=None, metavar=("C1A","C2A","C1B","C2B"), help="pF start, then trims")
ap.add_argument("--pin", nargs=2, action="append", default=[], metavar=("CAP", "PF"))
a = ap.parse_args()

J = json.loads((HERE / f"{a.src}.json").read_text())
d = from_json(J["design"])
if a.dev:
    devs = dict(d.devs)
    for role, w, l in a.dev:
        devs[role] = Dev(float(w) * 1e-6, float(l) * 1e-6, 1, 1)
        if role == "gmf_b": devs["rep_gmfb"] = devs[role]
        if role == "bridge": devs["rep_bridge"] = devs[role]
    d = d.with_(devs=devs)
if a.k is not None:
    u = d.devs["bias_a_int"]
    d = d.with_(devs={**d.devs, "rep_sink": Dev(u.w, u.l, u.ng, int(a.k)) if float(a.k).is_integer()
                       else Dev(u.w * a.k, u.l, u.ng, 1)})
if a.vicm is not None:
    d = d.with_(vicm=a.vicm)
ops, volts = O.probe(d, f"v023_{a.out}_op")
d = d.with_(vocm=round(volts["v(voutp)"], 4), vmid=round(volts["v(xdut.vout_1)"], 4))
print(f"{a.out}: I_L {ops['bridge'].id_na:.3f} nA; margins",
      {r: round((o.vds - max(O.VDS_FLOOR, o.vdsat)) * 1e3) for r, o in ops.items()}, flush=True)
if a.caps is not None:
    d = d.with_(c1_a=a.caps[0]*1e-12, c2_a=a.caps[1]*1e-12, c1_b=a.caps[2]*1e-12, c2_b=a.caps[3]*1e-12)
    d = synth_from(d, f"v023_{a.out}", polish=0, trims=3)
if a.qa is not None:
    g = {"gm_i_a": ops["in_a"].gm_ns * 1e-9, "gm_f_a": ops["gmf_a"].gm_ns * 1e-9,
         "gm_i_b": ops["in_b"].gm_ns * 1e-9, "gm_f_b": ops["gmf_b"].gm_ns * 1e-9}
    d = d.with_(**caps_for(g, a.qa, a.qb))
    d = synth_from(d, f"v023_{a.out}", polish=0, trims=3)
if a.polish:
    fixed = {c: float(v) * 1e-12 for c, v in a.pin}
    d, _ = S.fit_butter(d, f"v023_{a.out}_pol", fc_target=250.0, maxiter=a.polish, verbose=False, fixed=fixed)
s = M.evaluate(d, f"v023_{a.out}_sc", record=False)
print(M.table({a.out: s}), flush=True)
t = T.measure(d, tag=f"v023_{a.out}_thd", gate=False)
print(f"THD {t.thd_db:.2f} dB  caps {[round(getattr(d,k)*1e12,2) for k in ('c1_a','c2_a','c1_b','c2_b')]}", flush=True)
r = K.run(d, f"v023_{a.out}_axes", corners=AXES, record=False)
print(K.table(r), flush=True)
out = {"name": a.out, "base": J.get("base"), "design": to_json(d), "nominal": dict(s.values),
       "violations": s.violations, "thd_db": t.thd_db,
       "axes": [{"corner": x.corner.as_dict(), "status": x.status,
                 "values": (dict(x.score.values) if x.score else {}), "violations": x.violations} for x in r]}
(HERE / f"{a.out}.json").write_text(json.dumps(out, indent=1, default=str))
