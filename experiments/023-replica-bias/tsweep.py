"""Temperature envelope at the nominal rail (report-only): TSWEEP corners for one cell.
    LPF_BIAS_ALPHA=<0|1> uv run python tsweep.py <cell> [--vdd V]"""
import json, sys, os, argparse
from common import HERE, K, C, from_json
ap = argparse.ArgumentParser(); ap.add_argument("cell"); ap.add_argument("--vdd", type=float, default=C.VDD)
ap.add_argument("--vicm", type=float, default=None)
a = ap.parse_args()
alpha = os.environ.get("LPF_BIAS_ALPHA", "0")
d = from_json(json.loads((HERE / f"{a.cell}.json").read_text())["design"])
if a.vicm is not None: d = d.with_(vicm=a.vicm)
temps = (-40, -20, 0, 27, 55, 70, 85, 100, 125)
corners = tuple(K.Corner(C.CORNER_NOM, float(t), a.vdd) for t in temps)
sfx = f"_v{a.vicm:g}" if a.vicm is not None else ""
tag = f"tsw_{a.cell}{sfx}_a{alpha}_{a.vdd:g}".replace(".", "p")
r = K.run(d, tag, corners=corners, record=False, workers=9)
print(f"# {a.cell} alpha={alpha} VDD={a.vdd} vicm={d.vicm}")
print(K.table(r))
out = {"cell": a.cell, "alpha": alpha, "vdd": a.vdd, "vicm": d.vicm,
       "rows": [{"corner": x.corner.as_dict(), "status": x.status,
                 "values": (dict(x.score.values) if x.score else {}), "violations": x.violations} for x in r]}
(HERE / f"{tag}.json").write_text(json.dumps(out, indent=1, default=str))
