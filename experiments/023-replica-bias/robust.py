"""The expensive box for one 023 candidate: axes + reduced PVT + full PVT + MC.

    LPF_BIAS_ALPHA=<a> uv run python experiments/023-replica-bias/robust.py <name> [--n 100] [--full]

Reads `<name>.json` (a `common.to_json` dict) from this directory, writes
`<name>.robust.a<alpha>.json` and prints the tables.  `alpha` is taken from
`lab.config.BIAS_ALPHA` (env, before import), so a constant-current bench
(alpha 0) and a PTAT reference (alpha 1) are two invocations, never a flag.
"""
from __future__ import annotations

import argparse
import json
import time

from common import AXES, HERE, C, K, M, from_json
from lab import mc as MC

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--n", type=int, default=100)
ap.add_argument("--full", action="store_true", help="also the 45-point grid")
ap.add_argument("--no-mc", action="store_true")
a = ap.parse_args()

d = from_json(json.loads((HERE / f"{a.name}.json").read_text())["design"])
al = f"a{C.BIAS_ALPHA:g}".replace(".", "p")
tag = f"r023_{a.name}_{al}"
out: dict = {"name": a.name, "alpha": C.BIAS_ALPHA}

s = M.evaluate(d, f"{tag}_nom", record=False)
print(M.table({a.name: s}))
out["nominal"] = dict(s.values)

t0 = time.time()
res = K.run(d, f"{tag}_axes", corners=AXES, record=False)
print("\n## one axis at a time (nominal + process | supply | temperature)\n")
print(K.table(res))
out["axes"] = [{"corner": r.corner.as_dict(), "status": r.status,
                "values": (dict(r.score.values) if r.score else {}),
                "violations": r.violations} for r in res]

res = K.run(d, f"{tag}_red", record=False)
print("\n## reduced 22-point screen\n")
print(K.table(res))
out["reduced"] = {"summary": K.summary(res),
                  "rows": [{"corner": r.corner.as_dict(), "status": r.status,
                            "values": (dict(r.score.values) if r.score else {}),
                            "violations": r.violations} for r in res]}
if a.full:
    res = K.run(d, f"{tag}_full", corners=K.CORNERS, record=False)
    print("\n## full 45-point grid\n")
    print(K.table(res))
    out["full"] = {"summary": K.summary(res),
                   "rows": [{"corner": r.corner.as_dict(), "status": r.status,
                             "values": (dict(r.score.values) if r.score else {}),
                             "violations": r.violations} for r in res]}
print(f"corners: {time.time()-t0:.0f} s")

if not a.no_mc:
    r = MC.run(d, f"{tag}_mc", n=a.n, record=False)
    print("\n## mismatch MC\n")
    print(MC.table(r))
    out["mc"] = r.summary()

(HERE / f"{a.name}.robust.{al}.json").write_text(json.dumps(out, indent=1, default=str))
