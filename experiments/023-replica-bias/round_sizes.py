"""Round every device to natural dimensions (integer um, 0.5 um where the device is
small), keep replica copies matched, split fingers <= 10 um, re-fit the caps from
the current values, trim caps to 0.1 pF, then scorecard + THD + AXES + MC.

    uv run python round_sizes.py <src> <out> ROLE=W/L[:ng] ...   e.g. in_a=16/10:2
"""
from __future__ import annotations
import json, sys, math
from common import HERE, AXES, Dev, K, M, O, from_json, to_json
from lab import shape as S, thd as T
from lab import mc as MC

src, out = sys.argv[1], sys.argv[2]
J = json.loads((HERE / f"{src}.json").read_text())
d = from_json(J["design"])
devs = dict(d.devs)
for spec in sys.argv[3:]:
    if spec == "--cmim":
        d = d.with_(cap_model="cmim"); continue
    role, wl = spec.split("=")
    ng = 1
    if ":" in wl:
        wl, ng = wl.split(":"); ng = int(ng)
    w, l = (float(x) for x in wl.split("/"))
    old = devs[role]
    devs[role] = Dev(w * 1e-6, l * 1e-6, ng, old.m)
    for twin in {"gmf_b": "rep_gmfb", "bridge": "rep_bridge", "bias_a_int": "rep_sink"}.get(role, ()) and [{"gmf_b": "rep_gmfb", "bridge": "rep_bridge", "bias_a_int": "rep_sink"}[role]]:
        t = devs[twin]; devs[twin] = Dev(w * 1e-6, l * 1e-6, ng, t.m)
d = d.with_(devs=devs)
print("cap_model", d.cap_model)
print({r: (round(g.w*1e6, 2), round(g.l*1e6, 2), g.ng, g.m) for r, g in d.devs.items()})
ops, volts = O.probe(d, f"rs_{out}_op")
d = d.with_(vocm=round(volts["v(voutp)"], 4), vmid=round(volts["v(xdut.vout_1)"], 4))
print(f"{out}: I_L {ops['bridge'].id_na:.3f} nA; margins",
      {r: round((o.vds - max(O.VDS_FLOOR, o.vdsat)) * 1e3) for r, o in ops.items()}, flush=True)
d, _ = S.fit_butter(d, f"rs_{out}_pol", fc_target=250.0, maxiter=120, verbose=False)
# trim caps to 0.01 pF
d = d.with_(**{k: round(getattr(d, k) * 1e14) / 1e14 for k in ("c1_a", "c2_a", "c1_b", "c2_b")})
s = M.evaluate(d, f"rs_{out}_sc", record=False)
print(M.table({out: s}), flush=True)
t = T.measure(d, tag=f"rs_{out}_thd", gate=False)
print(f"THD {t.thd_db:.2f} dB  caps {[round(getattr(d,k)*1e12,2) for k in ('c1_a','c2_a','c1_b','c2_b')]}", flush=True)
r = K.run(d, f"rs_{out}_axes", corners=AXES, record=False)
print(K.table(r), flush=True)
mc = MC.run(d, f"rs_{out}_mc", n=100, record=False)
print(MC.table(mc), flush=True)
res = {"name": out, "base": src, "design": to_json(d), "nominal": dict(s.values), "violations": s.violations,
       "thd_db": t.thd_db, "mc": mc.summary(),
       "axes": [{"corner": x.corner.as_dict(), "status": x.status, "values": (dict(x.score.values) if x.score else {}),
                 "violations": x.violations} for x in r]}
(HERE / f"{out}.json").write_text(json.dumps(res, indent=1, default=str))
