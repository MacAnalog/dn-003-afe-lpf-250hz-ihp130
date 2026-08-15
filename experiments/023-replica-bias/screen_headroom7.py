"""Seventh screen: extend headroom6 to wider gmf_b / in_b (lower |V_SG| relaxes the budget wall
VDD >= V_GS(gmf_a)+max(V_SG)+2m) and add the -40/85 C vertices; gmf_a in moderate inversion (S7)."""
from __future__ import annotations
import json, itertools
from common import HERE, Dev, K, headroom, from_json
CORNERS = (K.Corner("mos_tt", 27.0, 1.35), K.Corner("mos_tt", 27.0, 1.65), K.Corner("mos_tt", 27.0, 1.5),
           K.Corner("mos_ss", 27.0, 1.5), K.Corner("mos_ff", 27.0, 1.5), K.Corner("mos_sf", 27.0, 1.5), K.Corner("mos_fs", 27.0, 1.5),
           K.Corner("mos_tt", -40.0, 1.5), K.Corner("mos_tt", 85.0, 1.5))
base = from_json(json.loads((HERE / "B1.json").read_text())["design"])
rows = []
for wa, wg, wi, vicm in itertools.product((2.0, 3.0), (8.0, 12.0, 16.0), (8.0, 12.0), (0.46, 0.50, 0.54)):
    devs = dict(base.devs)
    devs["gmf_a"] = Dev(wa * 1e-6, 45e-6); devs["gmf_b"] = devs["rep_gmfb"] = Dev(wg * 1e-6, 31.2e-6); devs["in_b"] = Dev(wi * 1e-6, 30e-6)
    d = base.with_(devs=devs, vicm=vicm)
    hr = headroom(d, f"hr7_a{wa:g}_g{wg:g}_i{wi:g}_v{vicm:g}".replace(".", "p"), corners=CORNERS, workers=9)
    core = CORNERS[:7]
    wm = min(hr[c.slug].get("margin_mv", -999) for c in core)
    wmT = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS)
    rows.append({"gmf_a_w": wa, "gmf_b_w": wg, "in_b_w": wi, "vicm": vicm, "worst_mv": round(wm, 1), "worst_withT_mv": round(wmT, 1), "detail": hr})
    print(f"gmf_a {wa:3g}/45 gmf_b {wg:3g}/31 in_b {wi:3g}/30 vicm {vicm:.2f}  worst {wm:5.0f} (withT {wmT:5.0f})  "
          + " ".join(f"{c.slug}:{hr[c.slug].get('margin_mv',-999):.0f}/{hr[c.slug].get('worst','?')}" for c in CORNERS), flush=True)
(HERE / "headroom7_B1.json").write_text(json.dumps(rows, indent=1))
