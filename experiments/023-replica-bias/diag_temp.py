"""Diagnose the temperature failure of B1-y2: op-only device margins vs T at 1.5 V,
with vicm swept, so we can tell headroom drift from anything else."""
import json, sys, os
from common import HERE, K, C, headroom, from_json
d = from_json(json.loads((HERE / "B1-y2.json").read_text())["design"])
alpha = os.environ.get("LPF_BIAS_ALPHA", "0")
temps = (-40, 27, 85, 125)
vicms = (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)
for T in temps:
    corners = tuple(K.Corner("mos_tt", float(T), 1.5) for _ in vicms)
    # one design per vicm; run each separately (headroom takes one design)
    rows = []
    for v in vicms:
        hr = headroom(d.with_(vicm=v), f"dt_a{alpha}_T{T}_v{v:g}".replace(".", "p").replace("-", "m"),
                      corners=(K.Corner("mos_tt", float(T), 1.5),), workers=1)
        r = list(hr.values())[0]
        rows.append((v, r))
    print(f"T={T:+4d} C  alpha={alpha}")
    for v, r in rows:
        if "error" in r: print(f"  vicm {v:.2f}  ERROR {r['error']}"); continue
        print(f"  vicm {v:.2f}  worst {r['margin_mv']:6.0f} mV @ {r['worst']:10s}  iL {r['iL_na']:.2f} nA  ig_a {r['ig_a_na']:.2f} nA  "
              f"vout_1 {r['vout_1']:.3f} voutp {r['voutp']:.3f}  " + " ".join(f"{k}:{m:.0f}" for k, m in r["margins"].items()), flush=True)
