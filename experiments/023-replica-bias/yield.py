"""Yield lever: scale the AREA of named roles (W and L by sqrt(k), W/L kept),
re-trim caps uniformly onto fc, then mismatch MC.  Replica copies follow.

    uv run python yield.py <src> <out> --area bridge 4 [--area gmf_b 4] [--n 100]
"""
from __future__ import annotations
import argparse, json, math
from common import HERE, Dev, M, K, O, from_json, to_json, synth_from
from lab import mc as MC

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--area", nargs=2, action="append", default=[], metavar=("ROLE", "K"))
ap.add_argument("--n", type=int, default=100)
ap.add_argument("--polish", type=int, default=0)
a = ap.parse_args()
J = json.loads((HERE / f"{a.src}.json").read_text())
d = from_json(J["design"])
devs = dict(d.devs)
for role, k in a.area:
    k = float(k); g = devs[role]
    devs[role] = Dev(g.w * math.sqrt(k), g.l * math.sqrt(k), g.ng, g.m)
    twin = {"gmf_b": "rep_gmfb", "bridge": "rep_bridge", "bias_a_int": "rep_sink"}.get(role)
    if twin and twin in devs:
        t = devs[twin]; devs[twin] = Dev(t.w * math.sqrt(k), t.l * math.sqrt(k), t.ng, t.m)
d = d.with_(devs=devs)
d = synth_from(d, f"y023_{a.out}", polish=a.polish, trims=3)
s = M.evaluate(d, f"y023_{a.out}_sc", record=False)
print(M.table({a.out: s}), flush=True)
r = MC.run(d, f"y023_{a.out}_mc", n=a.n, record=False)
print(MC.table(r), flush=True)
out = {"name": a.out, "from": a.src, "area": a.area, "design": to_json(d),
       "nominal": dict(s.values), "violations": s.violations, "mc": r.summary()}
(HERE / f"{a.out}.json").write_text(json.dumps(out, indent=1, default=str))
