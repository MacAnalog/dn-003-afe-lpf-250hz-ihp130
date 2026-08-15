import json, sys
from common import HERE, K, headroom, from_json
src = sys.argv[1]
d = from_json(json.loads((HERE / f"{src}.json").read_text())["design"]).with_(lv_roles=frozenset())
CORNERS = (K.Corner("mos_tt",27.0,1.5), K.Corner("mos_tt",27.0,1.35), K.Corner("mos_tt",27.0,1.65),
           K.Corner("mos_ss",27.0,1.5), K.Corner("mos_ff",27.0,1.5), K.Corner("mos_sf",27.0,1.5), K.Corner("mos_fs",27.0,1.5),
           K.Corner("mos_tt",-40.0,1.5), K.Corner("mos_tt",85.0,1.5))
for v in (0.10, 0.15, 0.20, 0.25, 0.30):
    hr = headroom(d.with_(vicm=v), f"hvp_{src}_v{v:g}".replace(".","p"), corners=CORNERS, workers=9)
    print(f"{src} vicm {v:.2f} worst7 {min(hr[c.slug]['margin_mv'] for c in CORNERS[:7]):5.0f}  " + " ".join(f"{c.slug}:{hr[c.slug]['margin_mv']:.0f}/{hr[c.slug]['worst']}" for c in CORNERS), flush=True)
