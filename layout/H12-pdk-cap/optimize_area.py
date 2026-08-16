#!/usr/bin/env python3
"""Area optimization of the H12-pdk-cap layout over the generator's own knobs.

The layout of record is a parameterized generator (``gen_H12_pdk_cap.py``): its
``LayoutParams`` are the optimizer knobs and ``BOUNDS`` their legal ranges.  This
script is the first real consumer of that contract — Nevergrad searches the
*numeric* knobs (gaps, widths, array shapes) for the smallest cell that still
passes every gate the round-3 layout passed:

    build (ai_env, gdsfactory) -> KLayout DRC (0 violations) -> KLayout LVS (match)
    -> kpex 2.5D CC on the MIM-stripped GDS -> splice into the block's own frozen
    benches (lab.metrics.evaluate through Design.dut_override) -> constraints

Constraints (all measured, none inferred):
    S1..S7 pass at nominal, ph_max >= PH_FLOOR (no worse than the round-3 layout
    minus a small tolerance), net2/net3 C-to-ac-gnd <= their round-3 values,
    |C(net2)-C(net3)| <= 0.5 fF, C(A<->B) <= brief budget, DRC 0, LVS match.
    The generator's own build-time symmetry / keep-apart assertions run inside
    build(); a build that raises is a failed trial.

Objective: area / area_ref  (+ a large penalty per violated constraint, scaled by
how far it is violated, so the optimizer still gets a gradient out of the
infeasible region).

The categorical floorplan modes decided in the approved PLAN (bank order, spine
side, anti-orientation, cap split, strap style, spine layer, xr1 split,
bias_dummy_rows) are FIXED at their defaults — those are design decisions, not
tuning.  ``--free NAME,...`` frees any of them; ``--fix NAME=VALUE`` pins a knob.

Run from the platform workspace (it has nevergrad + spicexplorer_signoff/layout;
the LPF benches run in the block's own venv as a subprocess):

    cd spicexplorer-platform && uv run python \\
        ../external/agentic-design-250hz-lpf-ihp130/layout/H12-pdk-cap/optimize_area.py \\
        --budget 240 --workers 8 --out-dir /path/to/scratch/areaopt

Outputs: ``trials.jsonl`` (one row per trial: params, area, every gate, score),
``best.json``, ``baseline.json``; the best trial's build dir is kept.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GEN = HERE / "gen_H12_pdk_cap.py"
SIZING = REPO / "signoff/post-pvt/H12-pdk-cap/design.json"
CORE = REPO / "signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp"
EXP = REPO / "experiments/023-replica-bias"           # has common.from_json / M
LPF_PY = REPO / ".venv/bin/python"
AI_PY = Path(os.environ.get("GDS_PYTHON", os.path.expanduser("~/miniconda3/envs/ai_env/bin/python")))
CELL = "lpf_core"
PORTS = "vinp vinn voutp voutn vbn vbp vdd"

# --- constraints (round-3 layout of record = the reference) --------------------
PH_FLOOR = 331.10          # round 3: 331.1595 nominal; do not give phase back
NET23_MAX = 32.40          # round 3: 32.33 fF each (brief nominal budget is 22.8)
D_NET23_MAX = 0.50         # fF, |C(net2) - C(net3)|
AB_MAX = 0.277             # fF, brief's C(net2∪net3, net4∪net1∪voutp∪voutn) budget
AC_GND = {"0", "vdd", "vbn", "vbr", "rep_x", "vinp", "vinn"}
CATEGORICAL_FIXED = {"bankA_order", "cap_spine_side", "cap_anti_orient", "cc12_split",
                     "net23_strap", "net23_spine_layer", "xr1_split", "bias_dummy_rows"}

os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
os.environ.setdefault("PDK", "ihp-sg13g2")
os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))   # native lane, not docker


def _bounds_and_defaults() -> tuple[dict, dict]:
    src = GEN.read_text()
    tree = ast.parse(src)
    bounds = None
    for n in tree.body:
        if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "BOUNDS":
            bounds = ast.literal_eval(n.value)
    assert bounds, "BOUNDS not found in generator"
    # defaults: read the dataclass in a subprocess-free way (the module imports gdsfactory)
    defaults: dict = {}
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == "LayoutParams":
            for st in n.body:
                if isinstance(st, ast.AnnAssign) and st.value is not None:
                    defaults[st.target.id] = ast.literal_eval(st.value)
    return bounds, defaults


def _pex_budget(netlist_text: str) -> dict:
    """Per-net C to the bench ac grounds + pair table, from a kpex netlist (fF)."""
    import re

    unit = {"a": 1e-18, "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "": 1.0}
    txt = re.sub(r"\n\+", " ", netlist_text)
    pairs: dict[tuple, float] = {}
    for ln in txt.splitlines():
        t = ln.split()
        if not t or not t[0].lower().startswith("c") or t[0].lower().startswith("cap") or len(t) < 4:
            continue
        m = re.match(r"^([-+0-9.eE]+)([afpnu]?)", t[3])
        if not m:
            continue
        v = float(m.group(1)) * unit.get(m.group(2), 1.0) * 1e15
        a = "0" if t[1].upper() in ("VSS", "VSUBS", "0") else t[1]
        b = "0" if t[2].upper() in ("VSS", "VSUBS", "0") else t[2]
        k = tuple(sorted((a, b)))
        pairs[k] = pairs.get(k, 0.0) + v
    nets = sorted({n for k in pairs for n in k} - {"0"})
    to_gnd = {n: round(sum(v for k, v in pairs.items() if n in k and (k[0] if k[1] == n else k[1]) in AC_GND), 3)
              for n in nets}
    A = {"net2", "net3"}
    B = {"net4", "net1", "voutp", "voutn"}
    ab = round(sum(v for k, v in pairs.items() if (k[0] in A and k[1] in B) or (k[1] in A and k[0] in B)), 4)
    return {"to_acgnd": to_gnd, "AB": ab,
            "d_net23": round(to_gnd.get("net2", 0) - to_gnd.get("net3", 0), 3),
            "d_net41": round(to_gnd.get("net4", 0) - to_gnd.get("net1", 0), 3)}


def _pex_subckt(raw: str) -> str:
    """kpex netlist -> the verbatim `.subckt lpf_core <PORTS>` the benches splice in
    (same recipe as REPORT §4: prep, vss/VSUBS -> 0, drop 0-0 elements, re-add the
    schematic MIM cards)."""
    sys.path.insert(0, str(REPO.parents[1] / "spicexplorer-platform/packages/spicexplorer-signoff/src"))
    from spicexplorer_signoff.postlayout import prep_pex_subckt

    t = prep_pex_subckt(raw, CELL)
    lines: list[str] = []
    skip = False
    for ln in t.splitlines():
        if ln.lower().startswith(".subckt"):
            lines.append(f".subckt {CELL} {PORTS}")
            skip = True
            continue
        if skip and ln.startswith("+"):
            continue
        skip = False
        toks = [("0" if w.upper() in ("VSS", "VSUBS") else w) for w in ln.split()]
        if toks and toks[0][0].lower() in "cr" and len(toks) >= 4 and toks[1] == "0" and toks[2] == "0":
            continue
        lines.append(" ".join(toks))
    caps = [ln.strip() for ln in CORE.read_text().splitlines() if ln.strip().startswith("xc")]
    i = [k for k, ln in enumerate(lines) if ln.strip().lower().startswith(".ends")][0]
    return "\n".join(lines[:i] + caps + lines[i:]) + "\n"


def _bench(pex_sp: Path, tag: str, cap_corner: str | None = None, iref_scale: float = 1.0) -> dict:
    """Run the block's frozen scorecard on the PEX subckt (in the LPF venv)."""
    code = (
        "import json,sys; sys.path.insert(0, %r); from common import from_json, M\n"
        "d=from_json(json.loads(open(%r).read())['design'])\n"
        "d=d.with_(iref=d.iref*%r)\n"
        "d=d.with_(dut_override=open(%r).read())\n"
        "s=M.evaluate(d, %r, record=False)\n"
        "print('@@'+json.dumps({'values':dict(s.values),'violations':s.violations}))\n"
    ) % (str(EXP), str(SIZING), iref_scale, str(pex_sp), tag)
    env = {**os.environ}
    if cap_corner:
        env["LPF_CAP_CORNER"] = cap_corner
    r = subprocess.run([str(LPF_PY), "-c", code], cwd=str(EXP), env=env, capture_output=True, text=True,
                       timeout=1800)
    for ln in reversed(r.stdout.splitlines()):
        if ln.startswith("@@"):
            return json.loads(ln[2:])
    return {"error": (r.stderr or r.stdout)[-600:]}


def _lvs_ref(params: dict, out: Path) -> Path:
    """The LVS reference depends on the knobs (dummy groups, split arrays) — regenerate it
    per trial with the generator's own writer, in the gdsfactory interpreter."""
    pf = REPO.parents[1] / "spicexplorer-platform/packages"
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(
        str(pf / d / "src") for d in ("spicexplorer-signoff", "spicexplorer-layout", "spicexplorer-core"))}
    code = ("import json,sys; sys.path.insert(0,%r); import gen_H12_pdk_cap as g\n"
            "print(g.write_lvs_reference(g.LayoutParams(**json.loads(%r)), out=%r))") % (
        str(HERE), json.dumps(params), str(out))
    r = subprocess.run([str(AI_PY), "-c", code], env=env, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not out.is_file():
        raise RuntimeError("lvs reference: " + (r.stderr or r.stdout)[-400:])
    return out


def evaluate(params: dict, work: Path, area_ref: float, tag: str) -> dict:
    """One build -> DRC -> LVS -> PEX -> bench pass. Never raises; returns a row."""
    from spicexplorer_layout import GdsBuilder
    from spicexplorer_signoff import run_drc, run_lvs, run_pex
    from spicexplorer_signoff.pex import strip_cards, strip_mim_for_pex

    row: dict = {"params": params, "tag": tag}
    t0 = time.time()
    work.mkdir(parents=True, exist_ok=True)
    try:
        b = GdsBuilder(GEN, work, cell=CELL, sizing_json=SIZING, python=AI_PY)
        gds = b(params)
        area = float(b.last.area_um2)
        row.update(area_um2=round(area, 1), sha=b.last.sha256[:12], bbox=b.last.bbox_um)
    except Exception as e:  # build-time assertions (symmetry / keep-apart / validate) land here
        row.update(status="build_fail", error=str(e)[-400:], score=50.0, secs=round(time.time() - t0, 1))
        return row
    pen = 0.0
    try:
        drc = run_drc(gds, CELL, work / "drc")
        row["drc_n"] = drc.n_violations
        row["drc_rules"] = sorted({v.rule for v in drc.violations})[:6]
        if not drc.passed:
            pen += 5.0 + min(drc.n_violations, 200) / 20
    except Exception as e:
        row.update(status="drc_error", error=str(e)[-300:], score=40.0, secs=round(time.time() - t0, 1))
        return row
    if pen:
        row.update(status="drc_fail", score=round(area / area_ref + pen, 4), secs=round(time.time() - t0, 1))
        return row
    try:
        lvs_ref = _lvs_ref(params, work / "core_lvs.sp")
    except Exception as e:
        row.update(status="lvsref_error", error=str(e)[-300:], score=round(area / area_ref + 5.0, 4),
                   secs=round(time.time() - t0, 1))
        return row
    lvs = run_lvs(gds, lvs_ref, CELL, work / "lvs")
    row["lvs"] = bool(lvs.matched)
    if not lvs.matched:
        row.update(status="lvs_fail", score=round(area / area_ref + 5.0, 4), secs=round(time.time() - t0, 1))
        return row
    # PEX CC on the MIM-stripped GDS
    nomim = work / f"{CELL}_nomim.gds"
    strip_mim_for_pex(gds, nomim)
    (work / "core_lvs_nomim.sp").write_text(strip_cards(lvs_ref.read_text()))
    px = run_pex(nomim, CELL, work / "core_lvs_nomim.sp", work / "pex_cc", mode="CC")
    if not px.ok:
        row.update(status="pex_fail", score=round(area / area_ref + 5.0, 4), secs=round(time.time() - t0, 1))
        return row
    raw = Path(px.netlist_path).read_text()
    bud = _pex_budget(raw)
    row["budget"] = {"net2": bud["to_acgnd"].get("net2"), "net3": bud["to_acgnd"].get("net3"),
                     "net4": bud["to_acgnd"].get("net4"), "net1": bud["to_acgnd"].get("net1"),
                     "voutp": bud["to_acgnd"].get("voutp"), "voutn": bud["to_acgnd"].get("voutn"),
                     "AB": bud["AB"], "d_net23": bud["d_net23"], "d_net41": bud["d_net41"]}
    pex_sp = work / "core_pex_cc.sp"
    pex_sp.write_text(_pex_subckt(raw))
    m = _bench(pex_sp, f"areaopt_{tag}")
    if "error" in m:
        row.update(status="bench_error", error=m["error"][-300:], score=round(area / area_ref + 5.0, 4),
                   secs=round(time.time() - t0, 1))
        return row
    v = m["values"]
    row["ph_max"] = round(v["ph_max_deg"], 4)
    row["fc"] = round(v["fc_hz"], 3)
    row["violations"] = m["violations"]
    # constraints -> penalties (scaled, so infeasible points still rank)
    n2, n3 = bud["to_acgnd"].get("net2", 0.0), bud["to_acgnd"].get("net3", 0.0)
    viol = {}
    if m["violations"]:
        viol["spec"] = len(m["violations"])
        pen += 3.0 * len(m["violations"])
    if v["ph_max_deg"] < PH_FLOOR:
        viol["ph_max"] = round(PH_FLOOR - v["ph_max_deg"], 4)
        pen += 2.0 + 4.0 * (PH_FLOOR - v["ph_max_deg"])
    if max(n2, n3) > NET23_MAX:
        viol["net23"] = round(max(n2, n3) - NET23_MAX, 3)
        pen += 1.0 + 0.2 * (max(n2, n3) - NET23_MAX)
    if abs(bud["d_net23"]) > D_NET23_MAX:
        viol["d_net23"] = bud["d_net23"]
        pen += 1.0 + abs(bud["d_net23"])
    if bud["AB"] > AB_MAX:
        viol["AB"] = bud["AB"]
        pen += 1.0 + 4.0 * bud["AB"]
    row["viol"] = viol
    row.update(status="ok" if not viol else "constraint_fail",
               score=round(area / area_ref + pen, 4), secs=round(time.time() - t0, 1))
    return row


def main() -> None:
    import nevergrad as ng

    ap = argparse.ArgumentParser(description="area-optimize the H12-pdk-cap layout over its knobs")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--free", default="", help="comma list of normally-fixed categorical knobs to free")
    ap.add_argument("--fix", action="append", default=[], help="NAME=VALUE pin (repeatable)")
    ap.add_argument("--keep-all", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = os.path.expanduser("~/miniconda3/envs/pex/bin") + os.pathsep + os.environ["PATH"]

    bounds, defaults = _bounds_and_defaults()
    free_cat = {s for s in a.free.split(",") if s}
    pins = {}
    for s in a.fix:
        k, v = s.split("=", 1)
        pins[k] = ast.literal_eval(v) if v[0] in "-0123456789TF([" else v
    space_kw = {}
    fixed = {}
    for k, (lo, hi) in bounds.items():
        d = defaults[k]
        if k in pins:
            fixed[k] = pins[k]
            continue
        if isinstance(lo, str) or isinstance(lo, bool):
            if k in free_cat:
                space_kw[k] = ng.p.Choice([lo, hi])
            else:
                fixed[k] = d
            continue
        if k in CATEGORICAL_FIXED and k not in free_cat:
            fixed[k] = d
            continue
        if isinstance(lo, int) and isinstance(hi, int) and isinstance(d, int):
            space_kw[k] = ng.p.Scalar(init=d, lower=lo, upper=hi).set_integer_casting()
        else:
            space_kw[k] = ng.p.Scalar(init=float(d), lower=float(lo), upper=float(hi))
    print(f"free knobs ({len(space_kw)}): {sorted(space_kw)}")
    print(f"fixed ({len(fixed)}): {fixed}")

    def snap(kw: dict) -> dict:
        p = {}
        for k, v in kw.items():
            if isinstance(v, bool) or isinstance(v, str):
                p[k] = v
            elif isinstance(v, int):
                p[k] = int(v)
            else:
                p[k] = round(float(v), 2)   # 0.01 µm grid (ports need an even DBU count)
        p.update(fixed)
        return p

    # baseline = the layout of record (defaults)
    base_params = snap({k: defaults[k] for k in space_kw})
    print("baseline …", flush=True)
    base = evaluate(base_params, out / "baseline", 1.0, "base")
    (out / "baseline.json").write_text(json.dumps(base, indent=1))
    if base.get("status") != "ok":
        print("BASELINE DOES NOT PASS ITS OWN GATES:", json.dumps(base, indent=1))
        sys.exit(2)
    area_ref = float(base["area_um2"])
    base["score"] = 1.0
    print(f"baseline area {area_ref:.0f} um2  ph_max {base['ph_max']}  net2/3 {base['budget']['net2']}/{base['budget']['net3']}",
          flush=True)

    space = ng.p.Instrumentation(**space_kw)
    space.random_state.seed(a.seed)
    opt = ng.optimizers.TwoPointsDE(parametrization=space, budget=a.budget, num_workers=a.workers)
    opt.suggest(**{k: defaults[k] for k in space_kw})
    log = open(out / "trials.jsonl", "a")
    lock = threading.Lock()
    best = {"score": 1.0, "params": base_params, "area_um2": area_ref, "trial": -1, "status": "ok"}
    done = 0

    def run_one(i: int, cand):
        p = snap(cand.kwargs)
        row = evaluate(p, out / f"t{i:04d}", area_ref, f"t{i:04d}")
        row["trial"] = i
        return cand, row

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {}
        i = 0
        while i < a.budget or futs:
            while i < a.budget and len(futs) < a.workers:
                cand = opt.ask()
                futs[ex.submit(run_one, i, cand)] = i
                i += 1
            for f in as_completed(list(futs)):
                idx = futs.pop(f)
                cand, row = f.result()
                opt.tell(cand, float(row["score"]))
                with lock:
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    done += 1
                    mark = ""
                    if row["status"] == "ok" and row["score"] < best["score"]:
                        # drop the previous best's build dir
                        if best.get("trial", -1) >= 0 and not a.keep_all:
                            shutil.rmtree(out / f"t{best['trial']:04d}", ignore_errors=True)
                        best = row
                        mark = "  <-- best"
                        (out / "best.json").write_text(json.dumps(best, indent=1))
                    elif not a.keep_all:
                        shutil.rmtree(out / f"t{idx:04d}", ignore_errors=True)
                    b_ = row.get("budget", {})
                    print(f"[{idx:04d}] {row['status']:<15} area={row.get('area_um2', '-'):>9} "
                          f"({(row.get('area_um2', area_ref) / area_ref - 1) * 100:+5.1f}%) "
                          f"ph={row.get('ph_max', '-'):>8} net2/3={b_.get('net2', '-')}/{b_.get('net3', '-')} "
                          f"score={row['score']:<8} {row.get('secs', '')}s{mark}", flush=True)
                break  # re-fill the pool after each completion
    (out / "best.json").write_text(json.dumps(best, indent=1))
    print(f"\nbaseline area {area_ref:.0f}; best area {best.get('area_um2')} "
          f"({(best.get('area_um2', area_ref) / area_ref - 1) * 100:+.1f}%) trial {best.get('trial')}")
    print(json.dumps(best, indent=1))


if __name__ == "__main__":
    main()
