#!/usr/bin/env python
"""IIP3 over the certified PVT window -- the last quantity G25 lists as nominal-only.

Two decisions worth stating, because both change what the number means.

TONES ARE FIXED at 45/55 Hz, the frozen definition every other IIP3 in this pack uses
(`lab` rule 1: a number that has not passed through the frozen bench is a claim, not a
measurement).  They are NOT re-centred on each corner's own cutoff.  That is the right
choice for comparability and the wrong one for interpretation, so each row also carries
its corner's `fc`: the tones sit at a different fraction of the passband when the cutoff
moves, and a reader needs to see that next to the intercept.

TWO AMPLITUDES PER CORNER, not one.  A single point gives an IIP3 only by ASSUMING the
3:1 law, which is exactly what a corner might break; two points let each corner report
its own measured IMD3 slope, and a slope far from 40 dB/decade marks a row whose
intercept should not be trusted.

    LPF_BIAS_ALPHA=1.1 LPF_NGSPICE=... PDK_ROOT=... .venv/bin/python \\
        signoff/paper-draft/scripts/iip3_corners.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "data"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
os.environ.setdefault("PDK", "ihp-sg13g2")
os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))

import numpy as np  # noqa: E402

from extract_bench import CERT_AXES  # noqa: E402
from lab import ngspice as ng  # noqa: E402
from lab.parallel import batch  # noqa: E402
from linearity_runs import F1, F2, design_of, score_twotone, tran_twotone  # noqa: E402

CELL = "H12-pdk-cap"
#: Both inside the cubic regime at nominal (IMD3 -71.9 and -59.8 dBc), one decade of
#: amplitude apart in the 40 dB/decade sense, so their slope is well determined.
AMPLS = (10.9375e-3, 21.875e-3)
SLOPE_IDEAL = 40.0


def main() -> None:
    d = design_of(CELL)
    fcs = {}
    idx = OUT / "pvt_index_pre_mim_a1p1_cert-axes.json"
    if idx.exists():
        fcs = {c["slug"]: c["scorecard"].get("fc_hz")
               for c in json.loads(idx.read_text())["corners"]}

    jobs = [(c, a) for c in CERT_AXES for a in AMPLS]
    print(f"two-tone at {F1:g}/{F2:g} Hz, {len(CERT_AXES)} corners x {len(AMPLS)} "
          f"amplitudes = {len(jobs)} transients")

    def one(job):
        c, a = job
        deck = tran_twotone(d, a, a, corner=c.process, temp=c.temp, vdd=c.vdd)
        plots = ng.plots(ng.run(deck, f"iip3_{c.slug}_a{a * 1e3:.4f}".replace(".", "p")))
        return c, a, score_twotone(plots, a, f"iip3_{c.slug}")

    rows: dict[str, dict] = {}
    for r in batch(jobs, one):
        if isinstance(r, BaseException):
            print(f"  FAILED: {r!r}")
            continue
        c, a, s = r
        rows.setdefault(c.slug, {"corner": c.as_dict(), "fc_hz": fcs.get(c.slug),
                                 "points": []})["points"].append(s)

    print(f"\n{'corner':16s} {'fc (Hz)':>9s} {'IMD3 slope':>11s} {'IIP3 (dBVp)':>12s} "
          f"{'OIP3 (dBVp)':>12s} {'slope dev':>10s}")
    for slug, rec in rows.items():
        pts = sorted(rec["points"], key=lambda p: p["ampl_per_tone_v"])
        if len(pts) < 2:
            rec["trusted"] = False
            continue
        (a0, i0), (a1, i1) = ((p["ampl_per_tone_v"], p["imd3_db"]) for p in pts)
        slope = (i1 - i0) / np.log10(a1 / a0)
        # The intercept from the LOWEST amplitude, which is deepest in the cubic regime.
        rec["imd3_slope_db_per_decade"] = float(slope)
        rec["slope_dev_db_per_decade"] = float(slope - SLOPE_IDEAL)
        rec["iip3_dbv"] = float(pts[0]["iip3_dbv"])
        rec["oip3_dbv"] = float(pts[0]["oip3_dbv"])
        rec["trusted"] = bool(abs(slope - SLOPE_IDEAL) <= 10.0)
        print(f"{slug:16s} {rec['fc_hz'] or float('nan'):9.3f} {slope:11.2f} "
              f"{rec['iip3_dbv']:12.3f} {rec['oip3_dbv']:12.3f} "
              f"{slope - SLOPE_IDEAL:+10.2f}" + ("" if rec["trusted"] else "   UNTRUSTED"))

    good = [r for r in rows.values() if r.get("trusted")]
    if good:
        v = [r["iip3_dbv"] for r in good]
        print(f"\nIIP3 over {len(good)}/{len(rows)} trusted corners: "
              f"{min(v):+.3f} .. {max(v):+.3f} dBVp (spread {max(v) - min(v):.3f} dB)")
    (OUT / "iip3_corners.json").write_text(json.dumps(
        {"cell": CELL, "tones_hz": [F1, F2], "ampls_v": list(AMPLS),
         "bias_alpha": os.environ.get("LPF_BIAS_ALPHA", "0"),
         "slope_ideal_db_per_decade": SLOPE_IDEAL, "corners": rows,
         "iip3_dbv_span": [min(v), max(v)] if good else None}, indent=1))
    print(f"wrote {(OUT / 'iip3_corners.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
