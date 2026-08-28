#!/usr/bin/env python
"""The ANALYTICAL quantities over PVT: poles, per-biquad Q, and the noise budget.

`doc/paper/README.md` G25 records the gap this closes: the symbolic results in this pack
-- `H(s)`, the pole/zero map, the per-biquad Q, the per-generator noise budget -- were all
derived at ONE operating point, so nothing was on record about their sensitivity.  Closing
it needs no new modelling: every one of them is a function of the operating point, and
`extract_bench.py --pvt` produces one operating point per corner.  This script re-runs the
same pencil solve and the same noise decomposition on each.

Read the tables with the SCALE/SHAPE split in mind.  That `fc` moves with temperature is
old news -- it is set by `gm/C` and `gm = I/(n*U_T)`, so a constant-current reference makes
it CTAT by construction (`lab.corners`, `lab.config.BIAS_ALPHA`).  The question this script
answers is whether the pole SHAPE survives: `Q` and the pole-pair ratio are gm-RATIO
quantities, so they should be far more stable than `fc`, and a filter whose shape holds
while its scale drifts is a different (and better) engineering position than one that
loses both.

    PF=../../spicexplorer-platform/.venv/bin/python
    $PF signoff/paper-draft/scripts/pvt_analysis.py --set cert-axes --set cert-box
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
REPO = HERE.parents[2]
DATA = PACK / "data"
sys.path.insert(0, str(HERE))

import n2tf_model as M  # noqa: E402
import pencil as PZ  # noqa: E402
from noise_analysis import integrate_noise, parse_contrib  # noqa: E402
from tf_analysis import CORE_MIM, DRIVE, OUT, pz_map  # noqa: E402

IRN_BAND = (0.5, 200.0)
#: The generator kinds ngspice emits, grouped as `validation.md` Section 5 groups them.
KINDS = {"idid": "channel thermal", "ididedge": "channel thermal",
         "flicker": "flicker", "igig": "gate shot", "ibd": "bulk shot"}


def budget(rec: dict) -> dict:
    """Each noise generator's share of the INPUT-REFERRED noise power in 0.5-200 Hz.

    ngspice reports output-referred densities; `onoise/inoise` is the simulator's own
    |H(f)|, so dividing by it refers every contribution through exactly the transfer the
    certified IRN was integrated against -- no model enters here.
    """
    per_gen, _totals, f = parse_contrib(rec["noise"])
    onz = np.asarray(rec["noise"]["onoise"], float)
    inz = np.asarray(rec["noise"]["inoise"], float)
    hmag = np.where(inz > 0, onz / np.maximum(inz, 1e-300), 1.0)

    roles = {inst: (o.get("role") or inst) for inst, o in rec["op"].items()}
    by_kind: dict[str, float] = {}
    by_role: dict[str, float] = {}
    total = 0.0
    for (inst, gen), dens in per_gen.items():
        v = integrate_noise(f, dens / hmag, *IRN_BAND)
        p = v * v
        total += p
        by_kind[KINDS.get(gen, gen)] = by_kind.get(KINDS.get(gen, gen), 0.0) + p
        by_role[roles.get(inst, inst)] = by_role.get(roles.get(inst, inst), 0.0) + p
    if total <= 0:
        return {"irn_uv_from_generators": 0.0, "by_kind": {}, "by_role": {}}
    return {
        "irn_uv_from_generators": 1e6 * float(np.sqrt(total)),
        "by_kind": {k: 100.0 * v / total for k, v in
                    sorted(by_kind.items(), key=lambda kv: -kv[1])},
        "by_role": {k: 100.0 * v / total for k, v in
                    sorted(by_role.items(), key=lambda kv: -kv[1])[:6]},
    }


def _offset_uv(rec: dict) -> float | None:
    """Differential output offset at the operating point, or None on an older record.

    Zero by symmetry at nominal; under mismatch it is the quantity G12 asks for.  The dc
    gain is within 0.01 dB of unity, so the output value is the input-referred one too.
    """
    n = rec.get("nodes")
    return None if not n else 1e6 * (n["voutp"] - n["voutn"])


def _pairs(pz: dict) -> tuple[list[dict], int]:
    """(the filter's two dominant complex pole pairs, total complex pairs found).

    Two selections, and both are load-bearing.

    WHICH PAIRS.  At nominal the cell is symmetric and seven pole/zero pairs cancel
    exactly, leaving the two that make the filter.  Under mismatch -- and at corners
    where the halves diverge -- those cancellations become near-cancellations, so the
    solve returns the doublets as separate poles plus a parasitic pair near 10 kHz from
    the device capacitances.  The FILTER poles are the two nearest the origin, so the
    pairs are ranked by f0 and the lowest two are kept.  Ranking all of them by Q would
    let the 10 kHz pair (Q ~ 0.538) impersonate the low-Q filter pair.

    WHICH IS WHICH.  The two kept pairs are then ordered by Q, not by f0: they are
    frequency-coincident by construction (249.72 and 251.08 Hz at nominal, 0.5 % apart)
    and differently damped, so an f0 ordering swaps the labels whenever a corner moves
    them past each other -- which turned a Q stable to 2.4 % into an apparent 2.42x
    span, an artefact of the sort key and nothing else.
    """
    allp = sorted((p for p in pz["poles"] if p["kind"] == "pair"),
                  key=lambda p: p["f0_hz"])
    return sorted(allp[:2], key=lambda p: p["Q"]), len(allp)


def analyse_corner(entry: dict) -> dict:
    bench = DATA / entry["file"]
    rec = json.loads(bench.read_text())
    pz = pz_map(CORE_MIM, bench)
    pp, n_all = _pairs(pz)
    row = {
        "slug": entry.get("slug") or f"s{entry['seed']:05d}",
        "corner": entry["corner"],
        "seed": entry.get("seed"),
        # Differential output offset at the operating point.  Zero by symmetry at
        # nominal; under mismatch it is the quantity G12 asks for, and the dc gain is
        # within 0.01 dB of unity so the output value is also the input-referred one.
        "offset_out_uv": _offset_uv(rec),
        "scorecard": entry["scorecard"],
        "dc_gain_db": pz["dc_gain_db"],
        "n_poles": pz["n_poles"], "n_zeros": pz["n_zeros"],
        "n_cancelled": len(pz["cancelled"]),
        "n_complex_pairs_all": n_all,
        "pairs": [{"f0_hz": p["f0_hz"], "Q": p["Q"]} for p in pp],
        "noise": budget(rec),
    }
    if len(pp) >= 2:
        # f0 of the high-Q pair over f0 of the low-Q pair: 1.0 would be exactly
        # coincident sections.  Both this and q_ratio are gm RATIOS -- the shape.
        row["pair_ratio"] = pp[1]["f0_hz"] / pp[0]["f0_hz"]
        row["q_ratio"] = pp[1]["Q"] / pp[0]["Q"]
    return row


def _span(rows: list[dict], get) -> dict | None:
    vals = [(get(r), r["slug"]) for r in rows if get(r) is not None]
    if not vals:
        return None
    lo, hi = min(vals), max(vals)
    return {"min": lo[0], "min_at": lo[1], "max": hi[0], "max_at": hi[1],
            "span_x": (hi[0] / lo[0]) if lo[0] else None}


def summarise(rows: list[dict]) -> dict:
    def pair(i, key):
        return lambda r: (r["pairs"][i][key] if len(r["pairs"]) > i else None)
    # Report the pole-pair CENSUS before any Q span, because a Q span is only
    # meaningful across corners that still have the pair to measure.  "Two true
    # biquads" is what S1 buys; where a pair splits into two real poles the filter
    # has changed order-shape, and averaging a Q over that is a category error.
    census = {}
    for r in rows:
        census[len(r["pairs"])] = census.get(len(r["pairs"]), 0) + 1
    out = {
        "n_corners": len(rows),
        "pole_pair_census": {f"{k}_pairs": v for k, v in sorted(census.items())},
        "n_two_pair": census.get(2, 0),
        "two_pair_corners": [r["slug"] for r in rows if len(r["pairs"]) == 2],
        "degenerate_corners": [r["slug"] for r in rows if len(r["pairs"]) != 2],
        # SCALE -- expected to move; set by gm/C.
        "fc_hz": _span(rows, lambda r: r["scorecard"].get("fc_hz")),
        "f0_loQ_hz": _span(rows, pair(0, "f0_hz")),
        "f0_hiQ_hz": _span(rows, pair(1, "f0_hz")),
        # SHAPE -- gm RATIOS; this is the question the nominal analysis could not answer.
        "Q_lo": _span(rows, pair(0, "Q")),
        "Q_hi": _span(rows, pair(1, "Q")),
        "pair_ratio": _span(rows, lambda r: r.get("pair_ratio")),
        "q_ratio": _span(rows, lambda r: r.get("q_ratio")),
        "irn_uv": _span(rows, lambda r: r["scorecard"].get("irn_uv")),
        "dc_gain_db": _span(rows, lambda r: r["dc_gain_db"]),
    }
    # Does the noise budget keep the same shape, or does a different mechanism take over?
    kinds = sorted({k for r in rows for k in r["noise"]["by_kind"]})
    out["noise_by_kind_pct"] = {
        k: _span(rows, lambda r, k=k: r["noise"]["by_kind"].get(k, 0.0)) for k in kinds}
    out["dominant_kind"] = sorted(
        {(max(r["noise"]["by_kind"], key=r["noise"]["by_kind"].get)
          if r["noise"]["by_kind"] else "?") for r in rows})
    # Every corner must reproduce its own certified IRN from the generators alone.
    err = [abs(r["noise"]["irn_uv_from_generators"] - r["scorecard"]["irn_uv"])
           / max(r["scorecard"]["irn_uv"], 1e-12) for r in rows
           if r["scorecard"].get("irn_uv")]
    out["noise_closure_max_pct"] = 100.0 * max(err) if err else None
    return out


def _stat(vals: list[float]) -> dict:
    v = np.asarray([x for x in vals if x is not None], float)
    if not v.size:
        return {}
    return {"n": int(v.size), "mean": float(v.mean()),
            "sigma": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "min": float(v.min()), "max": float(v.max()),
            "p50": float(np.median(v)), "p01": float(np.percentile(v, 1)),
            "p99": float(np.percentile(v, 99))}


def run_mc(dut: str = "pre_mim") -> dict:
    """The same analytical pipeline, one mismatch draw at a time."""
    idx_p = DATA / f"mc_index_{dut}.json"
    if not idx_p.exists():
        sys.exit(f"missing {idx_p.relative_to(REPO)} -- run\n"
                 f"  .venv/bin/python signoff/paper-draft/scripts/extract_bench.py "
                 f"--mc 64 --dut {dut}")
    idx = json.loads(idx_p.read_text())
    rows = [analyse_corner(e) for e in idx["draws"]]
    two = [r for r in rows if len(r["pairs"]) == 2]

    def pick(i, key):
        return [r["pairs"][i][key] for r in two]

    summary = {
        "n_draws": len(rows), "n_two_pair": len(two),
        "pole_pair_census": {f"{k}_pairs": sum(1 for r in rows if len(r["pairs"]) == k)
                             for k in sorted({len(r["pairs"]) for r in rows})},
        "fc_hz": _stat([r["scorecard"].get("fc_hz") for r in rows]),
        "ph_max_deg": _stat([r["scorecard"].get("ph_max_deg") for r in rows]),
        "irn_uv": _stat([r["scorecard"].get("irn_uv") for r in rows]),
        "offset_out_uv": _stat([r["offset_out_uv"] for r in rows]),
        "offset_abs_uv": _stat([abs(r["offset_out_uv"]) for r in rows]),
        "f0_loQ_hz": _stat(pick(0, "f0_hz")), "Q_lo": _stat(pick(0, "Q")),
        "f0_hiQ_hz": _stat(pick(1, "f0_hz")), "Q_hi": _stat(pick(1, "Q")),
        "pair_ratio": _stat([r["pair_ratio"] for r in two]),
        "noise_closure_max_pct": 100.0 * max(
            abs(r["noise"]["irn_uv_from_generators"] - r["scorecard"]["irn_uv"])
            / max(r["scorecard"]["irn_uv"], 1e-12) for r in rows),
    }
    return {"set": "mismatch", "dut": dut, "corner": idx["corner"],
            "rows": rows, "summary": summary}


def run(which: str, dut: str = "pre_mim", alpha: str = "_a1p1") -> dict:
    idx_p = DATA / f"pvt_index_{dut}{alpha}_{which}.json"
    if not idx_p.exists():
        sys.exit(f"missing {idx_p.relative_to(REPO)} -- run\n"
                 f"  LPF_BIAS_ALPHA=1.1 .venv/bin/python "
                 f"signoff/paper-draft/scripts/extract_bench.py --pvt {which} --dut {dut}")
    idx = json.loads(idx_p.read_text())
    rows = []
    for e in idx["corners"]:
        rows.append(analyse_corner(e))
        r = rows[-1]
        pp = r["pairs"]
        print(f"  [{r['slug']:16s}] "
              + (f"loQ {pp[0]['f0_hz']:7.2f} Hz Q {pp[0]['Q']:6.3f} | "
                 f"hiQ {pp[1]['f0_hz']:7.2f} Hz Q {pp[1]['Q']:6.3f}"
                 if len(pp) >= 2 else f"{len(pp)} pairs")
              + f" | IRN {r['scorecard'].get('irn_uv', float('nan')):8.2f} uV")
    return {"set": which, "dut": dut, "bias_alpha": idx.get("bias_alpha"),
            "rows": rows, "summary": summarise(rows)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", dest="sets", action="append", default=None,
                    help="corner set to analyse (repeatable); default: cert-axes cert-box")
    ap.add_argument("--dut", default="pre_mim")
    ap.add_argument("--alpha", default="_a1p1", help="alpha tag of the extraction")
    ap.add_argument("--mc", action="store_true", help="also analyse the mismatch draws")
    a = ap.parse_args()
    out = {}
    if a.mc:
        print("=== mismatch ===")
        out["mismatch"] = run_mc(a.dut)
        s = out["mismatch"]["summary"]
        for k in ("fc_hz", "ph_max_deg", "irn_uv", "Q_lo", "Q_hi", "offset_abs_uv"):
            v = s[k]
            print(f"  {k:14s} mean {v['mean']:10.4f}  sigma {v['sigma']:9.4f}  "
                  f"[{v['min']:10.4f} .. {v['max']:10.4f}]")
        print(f"  two complex pairs at {s['n_two_pair']}/{s['n_draws']} draws")
    for which in (a.sets or []):
        print(f"=== {which} ===")
        out[which] = run(which, a.dut, a.alpha)
        s = out[which]["summary"]
        print(f"  -> fc {s['fc_hz']['span_x']:.3f}x, "
              f"Q_lo {s['Q_lo']['span_x']:.3f}x, Q_hi {s['Q_hi']['span_x']:.3f}x, "
              f"noise closure {s['noise_closure_max_pct']:.2e} %\n"
              f"     two complex pairs at {s['n_two_pair']}/{s['n_corners']} corners")
    if (DATA / "pvt.json").exists():
        out = {**json.loads((DATA / "pvt.json").read_text()), **out}
    (DATA / "pvt.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {(DATA / 'pvt.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
