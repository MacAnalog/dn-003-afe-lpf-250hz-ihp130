"""Build one 023 candidate: sizing -> replica -> caps re-synthesised -> scorecard + axes.

    uv run python build.py <name> [--polish N]

Candidates are declared in CANDS below (sizing deltas against a sign-off cell);
the result is `<name>.json` (a `to_json` dict) + `<name>.build.md`.
"""
from __future__ import annotations
import argparse, json, sys
from common import (AXES, HERE, Dev, K, M, O, C, load_cell, replica, synth_from,
                    to_json, headroom, PROCESS_ONLY, SUPPLY_ONLY, TEMP_ONLY, NOM)
from lab import thd as T

CANDS = {
    # name: (base cell, k units, vicm, device overrides)
    "E-rep":   ("E-combo", 3, None, {}),                       # replica only, E as-is
    "B-rep":   ("B-balanced", 3, None, {}),                    # replica only, B as-is
    "B1":      ("B-balanced", 3, 0.40, {"in_b": Dev(2e-6, 30e-6), "gmf_b": Dev(2e-6, 31.2e-6)}),
    "B1-v35":  ("B-balanced", 3, 0.35, {"in_b": Dev(2e-6, 30e-6), "gmf_b": Dev(2e-6, 31.2e-6)}),
    "B1-v38":  ("B-balanced", 3, 0.38, {"in_b": Dev(2e-6, 30e-6), "gmf_b": Dev(2e-6, 31.2e-6)}),
    "B2":      ("B-balanced", 3, 0.40, {"in_b": Dev(1e-6, 40e-6), "gmf_b": Dev(1e-6, 50e-6)}),
    "B2-v35":  ("B-balanced", 3, 0.35, {"in_b": Dev(1e-6, 40e-6), "gmf_b": Dev(1e-6, 50e-6)}),
}

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--polish", type=int, default=25)
ap.add_argument("--thd", action="store_true")
a = ap.parse_args()

cell, k, vicm, over = CANDS[a.name]
b = load_cell(cell)
d = b.with_(devs={**b.devs, **over}, vicm=b.vicm if vicm is None else vicm)
d = replica(d, k)
# dc hints: measure them rather than inherit the base cell's
ops, volts = O.probe(d, f"b023_{a.name}_op0")
d = d.with_(vocm=round(volts["v(voutp)"], 4), vmid=round(volts["v(xdut.vout_1)"], 4))
print(f"{a.name}: I_L {ops['bridge'].id_na:.3f} nA, sink {ops['rep_sink'].id_na:.3f} nA, "
      f"vocm {d.vocm} vmid {d.vmid}", flush=True)
print("  op margins:", {r: round((o.vds - max(O.VDS_FLOOR, o.vdsat)) * 1e3) for r, o in ops.items()})

d = synth_from(d, f"b023_{a.name}", polish=a.polish, trims=3)
s = M.evaluate(d, f"b023_{a.name}_sc", record=False)
print(M.table({a.name: s}), flush=True)
out = {"name": a.name, "base": cell, "k": k, "design": to_json(d), "nominal": dict(s.values),
       "violations": s.violations}
if a.thd:
    t = T.measure(d, tag=f"b023_{a.name}_thd", gate=False)
    out["thd_db"] = t.thd_db
    print(f"  THD @50 Hz 175 mVpp: {t.thd_db:.2f} dB", flush=True)
res = K.run(d, f"b023_{a.name}_axes", corners=AXES, record=False)
print(K.table(res), flush=True)
out["axes"] = [{"corner": r.corner.as_dict(), "status": r.status,
                "values": (dict(r.score.values) if r.score else {}), "violations": r.violations}
               for r in res]
(HERE / f"{a.name}.json").write_text(json.dumps(out, indent=1, default=str))
