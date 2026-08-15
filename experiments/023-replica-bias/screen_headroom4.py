"""Fourth screen: in_b x gmf_b geometry (both |V_SG| set the top window) x vicm."""
from __future__ import annotations
import json, sys, itertools
from common import HERE, Dev, K, O, headroom, load_cell, worst_margin
from lab.dut import replica_of

cell = sys.argv[1] if len(sys.argv) > 1 else "B-balanced"
b0 = load_cell(cell)
ops, _ = O.probe(b0, f"hr4_{cell}_k")
k = ops["bridge"].id_na / (b0.iref * 1e9)
CORNERS = (K.Corner("mos_tt", 27.0, 1.35), K.Corner("mos_tt", 27.0, 1.65),
           K.Corner("mos_ss", 27.0, 1.5), K.Corner("mos_ff", 27.0, 1.5),
           K.Corner("mos_tt", 0.0, 1.5), K.Corner("mos_tt", 70.0, 1.5),
           K.Corner("mos_tt", -40.0, 1.5), K.Corner("mos_tt", 125.0, 1.5))
IB = {"15.6/10.4": (15.6e-6, 10.4e-6), "8/20": (8e-6, 20e-6), "4/20": (4e-6, 20e-6), "2/30": (2e-6, 30e-6)}
GB = {"4/31": (4e-6, 31.2e-6), "2/31": (2e-6, 31.2e-6), "1/40": (1e-6, 40e-6)}
VICMS = (0.40, 0.45, 0.50, 0.55, 0.60)
rows = []
for (ibn, (wi, li)), (gbn, (wg, lg)) in itertools.product(IB.items(), GB.items()):
    d0 = b0.with_(devs={**b0.devs, "in_b": Dev(wi, li, 1, 1), "gmf_b": Dev(wg, lg, 1, 1)})
    base = replica_of(d0, k)
    for vicm in VICMS:
        d = base.with_(vicm=vicm)
        hr = headroom(d, f"hr4_{cell}_{ibn}_{gbn}_v{vicm:g}".replace(".", "p").replace("/", "_"), corners=CORNERS)
        w4 = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS[:4])
        w6 = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS[:6])
        rows.append({"in_b": ibn, "gmf_b": gbn, "vicm": vicm, "w27_mv": round(w4, 1), "w0_70_mv": round(w6, 1), "detail": hr})
        print(f"in_b {ibn:9s} gmf_b {gbn:5s} vicm={vicm:.2f}  27C-box {w4:6.0f}  0-70C {w6:6.0f}  "
              + " ".join(f"{c.slug}:{hr[c.slug].get('margin_mv',-999):.0f}/{hr[c.slug].get('worst','?')}" for c in CORNERS), flush=True)
(HERE / f"headroom4_{cell}.json").write_text(json.dumps({"k": k, "rows": rows}, indent=1))
