#!/usr/bin/env python
"""The THD amplitude ladder over the certified PVT window.

Section 6.1 measures HD3 against amplitude at nominal, and `doc/paper/README.md` G25
asks for the analytical results over corners.  This is the distortion half of that: the
same open-loop ladder, re-run at every certified corner.

Three decisions, all of which change what a row means.

FIXED fin = 50 Hz, the S7 spec frequency, and FIXED drive amplitudes -- not servoed to a
constant output level.  Servoing would hide the amplitude dependence this ladder exists
to measure, and re-centring the tone per corner would make the columns incomparable.
Each row therefore carries its corner's `fc`, because a corner whose cutoff has moved is
being driven at a different fraction of its own passband.

REPORT-ONLY.  S7 is defined at 175 mVpp, 50 Hz, nominal -- one point, and it is scored by
`lab.metrics` in `make check`, not here.  A corner row is characterisation: it says how
much margin the delivered cell carries away from nominal, and it never re-defines the
spec line.  The 175 mVpp column is flagged so a reader can find the spec amplitude, and
its nominal row must reproduce the frozen number.

THE BIAS LAW IS SET EXPLICITLY.  This sweep has a temperature axis, so it runs at
`LPF_BIAS_ALPHA=1.1` -- the law the delivered cells were certified under -- and records
it.  The default (0, constant current) is a DIFFERENT circuit everywhere except 27 C.
See `doc/journal/bias-alpha-is-part-of-a-temperature-measurement.md`.

    LPF_BIAS_ALPHA=1.1 LPF_NGSPICE=... PDK_ROOT=... .venv/bin/python \
        signoff/paper-draft/scripts/thd_corners.py
"""
from __future__ import annotations

import json
import math
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

from extract_bench import CERT_AXES  # noqa: E402
from lab import config as C, metrics as M, parallel as P, thd as T  # noqa: E402
from linearity_runs import THD_VPP, campaign_design, dut_argv, dut_suffix  # noqa: E402

CELL = "H12-pdk-cap"
FIN = M.THD_FIN                     #: the S7 frequency, 50 Hz
SPEC_VPP = 175e-3                   #: the S7 amplitude, flagged in every row


def main() -> None:
    dut = dut_argv()
    sfx = dut_suffix(dut)
    d = campaign_design(dut, CELL)
    fcs = {}
    # The fc column beside each corner comes from that corner's own extraction, so it
    # has to be the SAME DUT and the same bias-alpha convention as the transients.
    idx = OUT / f"pvt_index_{dut}_a1p1_cert-axes.json"
    if idx.exists():
        fcs = {c["slug"]: c["scorecard"].get("fc_hz")
               for c in json.loads(idx.read_text())["corners"]}

    jobs = [(c, v) for c in CERT_AXES for v in THD_VPP]
    print(f"THD ladder at {FIN:g} Hz, {len(CERT_AXES)} corners x {len(THD_VPP)} "
          f"amplitudes = {len(jobs)} transients, bias alpha={C.BIAS_ALPHA:g}")

    def one(job):
        c, v = job
        tag = f"thdc{sfx}_{c.slug}_{v * 1e3:.4g}mvpp".replace(".", "p")
        # Open loop (explicit ampl, no servo) and gate=False, the ladder convention of
        # `linearity_runs.py`: the sim-economy gate scores the NOMINAL hard box, which a
        # corner point is not required to pass.
        r = T.measure(d, fin=FIN, ampl=v / 2.0, target_out_vpp=None, gate=False, tag=tag,
                      corner=c.process, temp=c.temp, vdd=c.vdd)
        return c, v, {"vpp_diff": v, "ampl": v / 2.0, "thd_db": r.thd_db,
                      "hd3_db": r.hd3_db, "hd2_db": r.hd2_db,
                      "out_fund_vpp": r.out_fund_vpp,
                      "is_spec_amplitude": bool(abs(v - SPEC_VPP) < 1e-9)}

    rows: dict[str, dict] = {}
    for r in P.batch(jobs, one):
        if isinstance(r, BaseException):
            print(f"  FAILED: {r!r}")
            continue
        c, v, rec = r
        rows.setdefault(c.slug, {"corner": c.as_dict(), "fc_hz": fcs.get(c.slug),
                                 "points": []})["points"].append(rec)

    print(f"\n{'corner':16s} {'fc (Hz)':>9s} {'THD@175m':>10s} {'HD3@175m':>10s} "
          f"{'THD@43.75m':>11s} {'ladder slope':>13s}")
    for slug, rec in rows.items():
        pts = sorted(rec["points"], key=lambda p: p["vpp_diff"])
        rec["points"] = pts
        spec = next((p for p in pts if p["is_spec_amplitude"]), None)
        rec["thd_db_at_spec"] = spec["thd_db"] if spec else None
        rec["hd3_db_at_spec"] = spec["hd3_db"] if spec else None
        # HD3 in dBc rises 2 dB per dB of drive in the cubic regime; the slope measured
        # over the two smallest amplitudes says whether a corner is still in it.
        (v0, h0), (v1, h1) = ((p["vpp_diff"], p["hd3_db"]) for p in pts[:2])
        rec["hd3_slope_db_per_db"] = float((h1 - h0) / (20.0 * math.log10(v1 / v0)))
        print(f"{slug:16s} {rec['fc_hz'] or float('nan'):9.3f} "
              f"{rec['thd_db_at_spec']:10.3f} {rec['hd3_db_at_spec']:10.3f} "
              f"{pts[0]['thd_db']:11.3f} {rec['hd3_slope_db_per_db']:13.3f}")

    spec_vals = [r["thd_db_at_spec"] for r in rows.values() if r["thd_db_at_spec"]]
    print(f"\nTHD at the S7 point ({SPEC_VPP * 1e3:g} mVpp, {FIN:g} Hz) over "
          f"{len(spec_vals)} corners: {min(spec_vals):.3f} .. {max(spec_vals):.3f} dB "
          f"(spread {max(spec_vals) - min(spec_vals):.3f} dB)")
    out = OUT / f"thd_corners{sfx}.json"
    out.write_text(json.dumps(
        {"cell": CELL, "dut": dut, "fin_hz": FIN, "vpp_diff": list(THD_VPP),
         "spec_vpp": SPEC_VPP, "bias_alpha": C.BIAS_ALPHA,
         "report_only": True, "corners": rows,
         "thd_db_at_spec_span": [min(spec_vals), max(spec_vals)] if spec_vals else None},
        indent=1))
    print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
