"""Remaining pre-layout sims for one cell (run with LPF_BIAS_ALPHA=1.1):
THD at process / supply / temperature corners, THD mismatch MC (n seeds),
THD-vs-fin profile, and (via LPF_CAP_CORNER sub-runs) the MIM cap corners
with the iref trim that recovers fc.  Writes <cell>.prelayout.json.

    uv run python prelayout.py <cell> [--nmc 30]
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from common import HERE, K, C, M, from_json
from lab import thd as T, ngspice as ng
from lab.deck import tran_thd
from lab.parallel import batch

ap = argparse.ArgumentParser(); ap.add_argument("cell"); ap.add_argument("--nmc", type=int, default=30)
a = ap.parse_args()
d = from_json(json.loads((HERE / f"{a.cell}.json").read_text())["design"])
out = {"cell": a.cell, "alpha": C.BIAS_ALPHA}

# ---- 1. THD at corners (open-loop spec drive, as the sign-off S7 point)
CORN = [K.Corner("mos_tt", 27, 1.5), K.Corner("mos_ss", 27, 1.5), K.Corner("mos_ff", 27, 1.5),
        K.Corner("mos_sf", 27, 1.5), K.Corner("mos_fs", 27, 1.5),
        K.Corner("mos_tt", 27, 1.40), K.Corner("mos_tt", 27, 1.65),
        K.Corner("mos_tt", 0, 1.5), K.Corner("mos_tt", 70, 1.5)]
def one_c(c):
    try:
        t = T.measure(d, tag=f"pl_{a.cell}_thd_{c.slug}", gate=False, corner=c.process, temp=c.temp, vdd=c.vdd)
        return {"corner": c.as_dict(), "thd_db": t.thd_db, "hd3_db": t.hd3_db, "hd2_db": t.hd2_db}
    except Exception as e:  # noqa
        return {"corner": c.as_dict(), "error": str(e)[:200]}
rows = batch(CORN, one_c, workers=9)
out["thd_corners"] = rows
print("## THD at corners (175 mVpp diff, fin 50 Hz)\n\n| corner | T | VDD | THD dB | HD3 | HD2 |\n|---|---|---|---|---|---|")
for r in rows:
    c = r["corner"]; print(f"| {c['process']} | {c['temp']:+.0f} | {c['vdd']:.2f} | {r.get('thd_db', float('nan')):.2f} | {r.get('hd3_db', float('nan')):.1f} | {r.get('hd2_db', float('nan')):.1f} |" if "thd_db" in r else f"| {c['process']} | {c['temp']} | {c['vdd']} | ERROR {r['error']} |")
sys.stdout.flush()

# ---- 2. THD mismatch MC
def one_mc(seed):
    deck = tran_thd(d, 50.0, 87.5e-3, corner=C.mismatch_corner("mos_tt"))
    lines = deck.splitlines()
    i = max(i for i, ln in enumerate(lines) if ln.lower().startswith(".lib"))
    lines.insert(i + 1, C.seed_directive(seed))
    try:
        plots = ng.simulate("\n".join(lines), f"pl_{a.cell}_thdmc_{seed}", timeout=3600)
        t = T._score(plots, 50.0, 87.5e-3, 20, 512, f"pl_{a.cell}_thdmc_{seed}")
        return {"seed": seed, "thd_db": t.thd_db, "hd3_db": t.hd3_db}
    except Exception as e:  # noqa
        return {"seed": seed, "error": str(e)[:200]}
mc = batch(list(range(1, a.nmc + 1)), one_mc, workers=10)
vals = [r["thd_db"] for r in mc if "thd_db" in r]
import statistics as st
out["thd_mc"] = {"n": a.nmc, "rows": mc, "mean": st.mean(vals), "sigma": st.pstdev(vals), "min": min(vals), "max": max(vals),
                 "n_pass": sum(v <= M.THD_LIMIT_DB for v in vals), "n_ok": len(vals)}
print(f"\n## THD mismatch MC (n = {a.nmc}, mos_tt_mismatch + cap_typ_mismatch, 27 C)\n\n"
      f"mean {st.mean(vals):.2f} dB, sigma {st.pstdev(vals):.2f}, worst {max(vals):.2f}, best {min(vals):.2f}; "
      f"{sum(v <= M.THD_LIMIT_DB for v in vals)}/{len(vals)} <= {M.THD_LIMIT_DB:g} dB ({a.nmc - len(vals)} failed sims)")
sys.stdout.flush()

# ---- 3. THD profile over fin
prof = T.profile(d, fins=(20, 50, 100, 150, 200), tag=f"pl_{a.cell}_prof")
out["thd_profile"] = [{"fin": r.fin, "thd_db": r.thd_db, "hd3_db": r.hd3_db} for r in prof]
print("\n## THD profile (informative; only 50 Hz is spec)\n")
print(T.table(prof))
sys.stdout.flush()

# ---- 4. MIM cap corners: scorecard at cap_bcs / cap_wcs, untrimmed and with an iref trim
def sub(capc, iref_scale):
    env = {**os.environ, "LPF_CAP_CORNER": capc}
    code = (f"import json,sys; sys.path.insert(0,'.'); from common import from_json, M, HERE\n"
            f"d=from_json(json.loads((HERE/'{a.cell}.json').read_text())['design'])\n"
            f"d=d.with_(iref=d.iref*{iref_scale})\n"
            f"s=M.evaluate(d,'pl_{a.cell}_{capc}_k{iref_scale}',record=False)\n"
            f"print(json.dumps({{'values':dict(s.values),'violations':s.violations}}))")
    r = subprocess.run([sys.executable, "-c", code], cwd=HERE, env=env, capture_output=True, text=True)
    return json.loads(r.stdout.strip().splitlines()[-1])
capc = []
for cc, ks in (("cap_typ", (1.0,)), ("cap_bcs", (1.0, 0.9)), ("cap_wcs", (1.0, 1.1))):
    for k in ks:
        r = sub(cc, k); capc.append({"cap_corner": cc, "iref_scale": k, **r})
out["cap_corners"] = capc
print("\n## MIM cap corners (cornerCAP.lib), 27 C / 1.5 V / mos_tt\n\n| cap corner | iref x | fc | dc | ripple | ph | a1000 | IRN | verdict |\n|---|---|---|---|---|---|---|---|---|")
for r in capc:
    v = r["values"]; print(f"| {r['cap_corner']} | {r['iref_scale']:.1f} | {v['fc_hz']:.1f} | {v['dc_db']:+.3f} | {v['ripple_db']:.3f} | {v['ph_max_deg']:.1f} | {v['a1000_db']:.1f} | {v['irn_uv']:.1f} | {'PASS' if not r['violations'] else 'FAIL: ' + '; '.join(x[:22] for x in r['violations'])} |")
(HERE / f"{a.cell}.prelayout.json").write_text(json.dumps(out, indent=1, default=str))
