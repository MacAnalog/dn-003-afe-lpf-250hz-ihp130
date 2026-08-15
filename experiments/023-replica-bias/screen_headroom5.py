"""Fifth screen: lv gmf_b in moderate inversion (D-thdjump's route) x in_b x vicm."""
from __future__ import annotations
import json, itertools
from common import HERE, Dev, K, O, headroom, load_cell
from lab.dut import replica_of

b0 = load_cell("B-balanced")
CORNERS = (K.Corner("mos_tt", 27.0, 1.35), K.Corner("mos_tt", 27.0, 1.65),
           K.Corner("mos_ss", 27.0, 1.5), K.Corner("mos_ff", 27.0, 1.5),
           K.Corner("mos_tt", 0.0, 1.5), K.Corner("mos_tt", 70.0, 1.5),
           K.Corner("mos_tt", -40.0, 1.5), K.Corner("mos_tt", 125.0, 1.5),
           K.Corner("mos_ss", 27.0, 1.35), K.Corner("mos_ff", 27.0, 1.65))
GB = {"lv0.81/62": (0.81e-6, 62.4e-6), "lv0.5/62": (0.5e-6, 62.4e-6), "lv1.3/62": (1.3e-6, 62.4e-6), "lv0.5/96": (0.5e-6, 96e-6)}
IB = {"2/30": (2e-6, 30e-6), "4/30": (4e-6, 30e-6), "8/30": (8e-6, 30e-6)}
VICMS = (0.35, 0.40, 0.45, 0.50)
rows = []
for (gn, (wg, lg)), (ibn, (wi, li)) in itertools.product(GB.items(), IB.items()):
    d0 = b0.with_(devs={**b0.devs, "gmf_b": Dev(wg, lg, 1, 1), "in_b": Dev(wi, li, 1, 1)},
                  lv_roles=frozenset(b0.lv_roles | {"gmf_b"}))
    base = replica_of(d0, 3)
    for vicm in VICMS:
        d = base.with_(vicm=vicm)
        hr = headroom(d, f"hr5_{gn}_{ibn}_v{vicm:g}".replace(".", "p").replace("/", "_"), corners=CORNERS)
        w4 = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS[:4] + CORNERS[8:])
        w6 = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS[:6] + CORNERS[8:])
        rows.append({"gmf_b": gn, "in_b": ibn, "vicm": vicm, "w27_mv": round(w4, 1), "w0_70_mv": round(w6, 1), "detail": hr})
        print(f"gmf_b {gn:10s} in_b {ibn:5s} vicm={vicm:.2f}  27C-box {w4:6.0f}  0-70C {w6:6.0f}  "
              + " ".join(f"{c.slug}:{hr[c.slug].get('margin_mv',-999):.0f}/{hr[c.slug].get('worst','?')}" for c in CORNERS), flush=True)
(HERE / "headroom5_B.json").write_text(json.dumps(rows, indent=1))
