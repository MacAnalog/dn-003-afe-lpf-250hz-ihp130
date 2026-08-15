"""Q-split scan around a flat solution: c1_b*s, c2_b/s (lower Q_b), c1_a/t, c2_a*t
(higher Q_a), uniform re-trim onto 250 Hz, then ripple/mono/THD per point."""
from __future__ import annotations
import json, sys, itertools
from common import HERE, M, from_json, to_json, synth_from
from lab import thd as T
from lab.parallel import batch

src = sys.argv[1]; out = sys.argv[2]
SS = [float(x) for x in sys.argv[3].split(",")]
TT = [float(x) for x in sys.argv[4].split(",")]
J = json.loads((HERE / f"{src}.json").read_text())
base = from_json(J["design"])

def one(st):
    s, t = st
    d = base.with_(c1_b=base.c1_b * s, c2_b=base.c2_b / s, c1_a=base.c1_a / t, c2_a=base.c2_a * t)
    tag = f"scan023_{out}_s{s:g}_t{t:g}".replace(".", "p")
    d = synth_from(d, tag, polish=0, trims=3)
    sc = M.evaluate(d, tag + "_sc", record=False)
    row = {"s": s, "t": t, **{k: sc[k] for k in ("fc_hz", "ripple_db", "peak_db", "mono_db", "a1000_db", "ph_max_deg", "irn_uv", "c_total_pf")},
           "ok_shape": not [v for v in sc.violations], "design": to_json(d)}
    try:
        th = T.measure(d, tag=tag + "_thd", gate=False); row["thd_db"] = th.thd_db
    except Exception as e:  # noqa
        row["thd_db"] = float("nan"); row["thd_err"] = str(e)[:100]
    print(f"s={s:4.2f} t={t:4.2f} fc {row['fc_hz']:6.2f} ripple {row['ripple_db']:.3f} mono {row['mono_db']:.3f} "
          f"a1k {row['a1000_db']:6.2f} ph {row['ph_max_deg']:5.1f} IRN {row['irn_uv']:.2f} C {row['c_total_pf']:.1f} THD {row['thd_db']:.2f} "
          f"caps {[round(getattr(d,k)*1e12,1) for k in ('c1_a','c2_a','c1_b','c2_b')]}", flush=True)
    return row
rows = batch(list(itertools.product(SS, TT)), one, workers=12)
(HERE / f"scan_{out}.json").write_text(json.dumps([r for r in rows if isinstance(r, dict)], indent=1, default=str))
