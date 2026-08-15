"""Sixth screen: the S7/supply compromise -- gmf_a W (inversion level) x gmf_b W x in_b W x vicm,
scored by the worst saturation margin over both rails + 4 process corners at 27 C."""
from __future__ import annotations
import json, itertools
from common import HERE, Dev, K, headroom, from_json
CORNERS = (K.Corner("mos_tt", 27.0, 1.35), K.Corner("mos_tt", 27.0, 1.65), K.Corner("mos_tt", 27.0, 1.5),
           K.Corner("mos_ss", 27.0, 1.5), K.Corner("mos_ff", 27.0, 1.5), K.Corner("mos_sf", 27.0, 1.5), K.Corner("mos_fs", 27.0, 1.5))
base = from_json(json.loads((HERE / "B1.json").read_text())["design"])
rows = []
for wa, wg, wi, vicm in itertools.product((1.5, 2.0, 3.0), (4.0, 6.0, 8.0), (4.0, 8.0), (0.42, 0.46, 0.50, 0.54)):
    devs = dict(base.devs)
    devs["gmf_a"] = Dev(wa * 1e-6, 45e-6); devs["gmf_b"] = devs["rep_gmfb"] = Dev(wg * 1e-6, 31.2e-6); devs["in_b"] = Dev(wi * 1e-6, 30e-6)
    d = base.with_(devs=devs, vicm=vicm)
    hr = headroom(d, f"hr6_a{wa:g}_g{wg:g}_i{wi:g}_v{vicm:g}".replace(".", "p"), corners=CORNERS)
    wm = min(hr[c.slug].get("margin_mv", -999) for c in CORNERS)
    rows.append({"gmf_a_w": wa, "gmf_b_w": wg, "in_b_w": wi, "vicm": vicm, "worst_mv": round(wm, 1), "detail": hr})
    print(f"gmf_a {wa:3g}/45 gmf_b {wg:3g}/31 in_b {wi:3g}/30 vicm {vicm:.2f}  worst {wm:6.0f}  "
          + " ".join(f"{c.slug}:{hr[c.slug].get('margin_mv',-999):.0f}/{hr[c.slug].get('worst','?')}" for c in CORNERS), flush=True)
(HERE / "headroom6_B1.json").write_text(json.dumps(rows, indent=1))
