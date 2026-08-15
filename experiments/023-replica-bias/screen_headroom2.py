"""Second headroom screen, on the lv-in_a / hv-in_b / hv-gmf_b pattern (cells B/C).

    uv run python screen_headroom2.py B-balanced
"""
from __future__ import annotations
import json, sys
from common import HERE, Dev, O, headroom, load_cell, replica, worst_margin

cell = sys.argv[1] if len(sys.argv) > 1 else "B-balanced"
b0 = load_cell(cell)
ops, _ = O.probe(b0, f"hr2_{cell}_k")
k = ops["bridge"].id_na / (b0.iref * 1e9)
print(f"{cell}: ladder {ops['bridge'].id_na:.3f} nA -> k = {k:.3f}", flush=True)
base = replica(b0, k)
VICMS = [round(0.30 + 0.05 * i, 2) for i in range(9)]           # 0.30 .. 0.70
GA = base.devs["gmf_a"]
ARMS = {"gA-x1": GA, "gA-x2": Dev(GA.w * 2, GA.l, GA.ng, GA.m),
        "gA-x0.5": Dev(GA.w, GA.l * 2, GA.ng, GA.m)}
rows = []
for an, ga in ARMS.items():
    devs = dict(base.devs); devs["gmf_a"] = ga
    for vicm in VICMS:
        d = base.with_(devs=devs, vicm=vicm)
        hr = headroom(d, f"hr2_{cell}_{an}_v{vicm:g}".replace(".", "p"))
        wm = worst_margin(hr)
        bad = [c for c, r in hr.items() if r.get("ig_a_na", 0) < 0.2 * base.iref * 1e9]
        rows.append({"arm": an, "vicm": vicm, "worst_margin_mv": round(wm, 1), "collapsed": bad, "detail": hr})
        print(f"{an:8s} vicm={vicm:.2f} worst {wm:7.1f} @ {min(hr, key=lambda c: hr[c].get('margin_mv', -1e9))} collapsed={len(bad)}", flush=True)
(HERE / f"headroom2_{cell}.json").write_text(json.dumps({"k": k, "rows": rows}, indent=1))
