"""Op-only headroom screen: follower flavour x vicm x gmf_a width.

The ladder budget is  VDD - vicm = |V_SG|(in_a) + |V_SG|(in_b) + |V_SD|(gmf_b)
at the top and  vicm + |V_SG|(in_a) = V_GS(gmf_a) + |V_SD|(in_a)  at the bottom.
This sweeps the three knobs that move those terms and reports, per arm, the
worst saturation margin over the HEADROOM corner vertices.  No capacitors are
touched (op only), so an arm is a cheap ~10-sim probe.

    uv run python experiments/023-replica-bias/screen_headroom.py [cell] [k]
"""
from __future__ import annotations

import json
import sys

from common import HERE, Dev, headroom, load_cell, replica, worst_margin

cell = sys.argv[1] if len(sys.argv) > 1 else "E-combo"
k = float(sys.argv[2]) if len(sys.argv) > 2 else 2.90
base = replica(load_cell(cell), k)

LV_SETS = {
    "hv-all": (), "lvB": ("gmf_b",), "lvA": ("in_a",), "lvA+B": ("in_a", "gmf_b"),
    "lvIN": ("in_a", "in_b"), "lvIN+B": ("in_a", "in_b", "gmf_b"),
    "lvA2": ("in_a", "in_b", "gmf_b", "bridge"),
}
VICMS = [round(0.15 + 0.05 * i, 2) for i in range(13)]        # 0.15 .. 0.75
GMFA_W = (1e-6, 4e-6)

rows = []
for lname, lv in LV_SETS.items():
    lvset = set(lv)
    if "gmf_b" in lvset:
        lvset.add("rep_gmfb")
    if "bridge" in lvset:
        lvset.add("rep_bridge")
    for wa in GMFA_W:
        devs = dict(base.devs)
        devs["gmf_a"] = Dev(wa, base.devs["gmf_a"].l, 1, 1)
        for vicm in VICMS:
            d = base.with_(lv_roles=frozenset(lvset), devs=devs, vicm=vicm,
                           vocm=None if False else base.vocm)
            tag = f"hr_{cell}_{lname}_w{wa*1e6:g}_v{vicm:g}".replace(".", "p")
            hr = headroom(d, tag)
            wm = worst_margin(hr)
            bad = [c for c, r in hr.items() if r.get("ig_a_na", 0) < 0.2 * base.iref * 1e9]
            row = {"lv": lname, "gmfa_w_um": wa * 1e6, "vicm": vicm,
                   "worst_margin_mv": round(wm, 1),
                   "worst_at": min(hr, key=lambda c: hr[c].get("margin_mv", -1e9)),
                   "collapsed": bad, "detail": hr}
            rows.append(row)
            print(f"{lname:8s} wA={wa*1e6:g} vicm={vicm:.2f}  worst {wm:7.1f} mV "
                  f"@ {row['worst_at']} ({hr[row['worst_at']].get('worst')})"
                  f"  collapsed={len(bad)}", flush=True)

(HERE / f"headroom_{cell}.json").write_text(json.dumps(rows, indent=1))
