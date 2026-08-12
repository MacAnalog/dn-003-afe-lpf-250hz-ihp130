"""Rebuild `rounds.{json,md}` from the round JSONs the sizing runs wrote.

The history is DERIVED, never typed: every row is read back out of the JSON the
round itself produced, so it cannot drift from what was measured. Re-run after
adding a round; add the round to `ROUNDS` with a one-line reason it was tried.

    uv run python doc/sizing-history/build.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1] / "experiments"

ROUNDS = [
    ("reshape", "020-novel-topologies/reshaped.json",
     "Template re-fit of the 020 cells (capacitors only, devices frozen)"),
    ("qwalk", "021-publication-cell/qwalk.json",
     "Walk biquad B's Q allocation at fixed w0 — the THD hypothesis (FALSIFIED)"),
    ("fitcells", "021-publication-cell/fitcells.json",
     "Template re-fit of the frozen 020B/020C cells"),
    ("scale", "021-publication-cell/scaled.json",
     "Uniform I–C scaling of 020C (devices + iref + caps × k)"),
    ("area", "021-publication-cell/area_sweep.json",
     "Gate area at fixed W/L on the stacked hv cell"),
    ("lvcm", "021-publication-cell/lvcm.json",
     "lv input follower, common mode raised"),
    ("lv065_bias", "021-publication-cell/lv065_bias.json",
     "Bias-device area on the stacked lv cell"),
    ("unstacked75", "021-publication-cell/unstacked75.json",
     "Unstacked topology at vicm = VDD/2, k-scaled"),
    ("vdd2_area", "021-publication-cell/vdd2_area.json",
     "All-device area on the VDD/2 cell (costs phase)"),
    ("vdd2_bias", "021-publication-cell/vdd2_bias.json",
     "Bias-only area on the VDD/2 cell (does not cost phase)"),
    ("vdd2_bias2", "021-publication-cell/vdd2_bias2.json",
     "Bias-only area, pushed further"),
    ("reuse", "021-publication-cell/reuse.json",
     "lv gmf_b + ladder sizing — the current-reuse fix, and the deliverable"),
]

HEAD = """# Sizing history — every round attempted, and what it returned

**KIND: REFERENCE.** Built from the round JSONs by
[`build.py`](build.py), never typed; [`rounds.json`](rounds.json) is the
machine-readable twin. `PASS` means all nine lines met at the nominal corner;
`fail(n)` counts the spec lines missed (THD is scored separately and is not in
that count, so a `fail(0)` row is one that met the cheap box and missed S7).

The dead ends are kept deliberately. Two of them are the most useful rows here:
`qwalk` (Q allocation does **not** set THD — the fit pulls it straight back) and
`vdd2_area` (growing **all** device areas buys mismatch yield and then fails S1
on phase, where growing only the bias devices does not).
"""


def rows() -> list[dict]:
    out = []
    for name, rel, why in ROUNDS:
        p = EXP / rel
        if not p.exists():
            continue
        data = json.loads(p.read_text())
        if isinstance(data, dict):
            data = data.get("arms", [])
        for r in data if isinstance(data, list) else []:
            if not isinstance(r, dict) or "fc_hz" not in r:
                continue
            viol = r.get("violations", []) or []
            thd = r.get("thd_db")
            out.append({
                "round": name, "why": why, "cell": r.get("name", "?"),
                "fc": r.get("fc_hz"), "mono": r.get("mono", r.get("mono_db")),
                "a1k": r.get("a1000_db"), "ph": r.get("ph_max_deg"),
                "irn": r.get("irn_uv"), "p": r.get("p_core_nw"),
                "c": r.get("c_total_pf"), "thd": thd,
                "mc": (r.get("mc") or {}).get("all_pass_yield"),
                "ok": (not viol) and (thd is None or thd <= -40.0),
                "nviol": len(viol),
            })
    return out


def fmt(v, s="{:.2f}") -> str:
    return "—" if v is None else s.format(v)


def main() -> int:
    rs = rows()
    (HERE / "rounds.json").write_text(json.dumps(rs, indent=1))
    out = [HEAD]
    for name, _rel, why in ROUNDS:
        sel = [r for r in rs if r["round"] == name]
        if not sel:
            continue
        out += [f"## `{name}` — {why}", "",
                "| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in sel:
            mc = "—" if r["mc"] is None else f"{r['mc']*100:.0f} %"
            verdict = "**PASS**" if r["ok"] else f"fail({r['nviol']})"
            out.append(
                f"| `{r['cell']}` | {fmt(r['fc'])} | {fmt(r['mono'], '{:.4f}')} | "
                f"{fmt(r['a1k'])} | {fmt(r['ph'], '{:.1f}')} | {fmt(r['irn'])} | "
                f"{fmt(r['p'])} | {fmt(r['c'], '{:.1f}')} | {fmt(r['thd'])} | {mc} | "
                f"{verdict} |")
        out.append("")
    n_pass = sum(1 for r in rs if r["ok"])
    out += ["---", "",
            f"**{len(rs)} sizing points across {len(set(r['round'] for r in rs))} "
            f"rounds; {n_pass} met all nine lines.**"]
    (HERE / "rounds.md").write_text("\n".join(out))
    print(f"{len(rs)} points, {n_pass} passing -> rounds.md / rounds.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
