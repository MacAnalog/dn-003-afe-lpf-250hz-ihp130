"""Third headroom screen: gmf_b geometry (its |V_SG| is the in_b/gmf_b window) x vicm.

Merged ladder identity: |V_SD|(in_b) + |V_SD|(gmf_b) = |V_SG|(gmf_b).  So the
supply/temperature window of the top pair IS |V_SG|(gmf_b) - 2*Vds_min, and a
narrower, longer gmf_b widens it.  Replica keeps I_L fixed while gmf_b moves.
"""
from __future__ import annotations
import json, sys
from common import HERE, Dev, K, O, C, headroom, load_cell, replica, worst_margin
from lab.dut import replica_of

cell = sys.argv[1] if len(sys.argv) > 1 else "B-balanced"
b0 = load_cell(cell)
ops, _ = O.probe(b0, f"hr3_{cell}_k")
k = ops["bridge"].id_na / (b0.iref * 1e9)
CORNERS = (K.Corner("mos_tt", 27.0, 1.35), K.Corner("mos_tt", 27.0, 1.65),
           K.Corner("mos_tt", -40.0, 1.5), K.Corner("mos_tt", 125.0, 1.5),
           K.Corner("mos_ss", 27.0, 1.5), K.Corner("mos_ff", 27.0, 1.5),
           K.Corner("mos_tt", -40.0, 1.35), K.Corner("mos_tt", 125.0, 1.65),
           K.Corner("mos_ss", -40.0, 1.35), K.Corner("mos_ff", 125.0, 1.65))
GB = {"8/15.6": (8.08e-6, 15.6e-6), "4/31": (4e-6, 31.2e-6), "2/31": (2e-6, 31.2e-6),
      "1/40": (1e-6, 40e-6), "0.5/60": (0.5e-6, 60e-6), "0.3/80": (0.3e-6, 80e-6)}
VICMS = (0.35, 0.4, 0.45, 0.5, 0.55, 0.6)
rows = []
for gn, (w, l) in GB.items():
    d0 = b0.with_(devs={**b0.devs, "gmf_b": Dev(w, l, 1, 1)})
    base = replica_of(d0, k)
    for vicm in VICMS:
        d = base.with_(vicm=vicm)
        hr = headroom(d, f"hr3_{cell}_{gn}_v{vicm:g}".replace(".", "p").replace("/", "_"), corners=CORNERS)
        wm6 = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS[:6])
        wm = worst_margin(hr)
        rows.append({"gmf_b": gn, "vicm": vicm, "worst6_mv": round(wm6, 1), "worst_mv": round(wm, 1), "detail": hr})
        print(f"gmf_b {gn:7s} vicm={vicm:.2f}  worst(axes) {wm6:7.1f}  worst(all) {wm:7.1f}  "
              + " ".join(f"{c.slug}:{hr[c.slug].get('margin_mv',-999):.0f}/{hr[c.slug].get('worst','?')}" for c in CORNERS), flush=True)
(HERE / f"headroom3_{cell}.json").write_text(json.dumps({"k": k, "rows": rows}, indent=1))
