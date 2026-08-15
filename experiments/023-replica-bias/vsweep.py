"""Supply envelope at 27 C, tt (report-only): 1.35..1.65 V in 0.05 V steps (+ 1.425/1.575) for one cell.
    uv run python vsweep.py <cell>"""
import json, sys, os
from common import HERE, K, C, from_json
cell = sys.argv[1]
d = from_json(json.loads((HERE / f"{cell}.json").read_text())["design"])
vdds = (1.35, 1.40, 1.425, 1.45, 1.50, 1.55, 1.575, 1.60, 1.65)
corners = tuple(K.Corner(C.CORNER_NOM, C.TEMP_NOM, v) for v in vdds)
tag = f"vsw_{cell}"
r = K.run(d, tag, corners=corners, record=False, workers=9)
print(f"# {cell} supply sweep, 27 C, tt, vicm={d.vicm}")
print(K.table(r))
out = {"cell": cell, "rows": [{"corner": x.corner.as_dict(), "status": x.status,
        "values": (dict(x.score.values) if x.score else {}), "violations": x.violations} for x in r]}
(HERE / f"{tag}.json").write_text(json.dumps(out, indent=1, default=str))
