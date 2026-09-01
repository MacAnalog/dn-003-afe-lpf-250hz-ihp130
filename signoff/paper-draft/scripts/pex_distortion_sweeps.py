#!/usr/bin/env python
"""Distortion of the EXTRACTED cell: THD/HD2/HD3 versus frequency, then versus amplitude
at the frequency that comes out worst.

Everything here runs on `post_pex` -- the kpex-extracted layout netlist spliced in whole,
36 instances of parasitic R and C -- and on nothing else.  The existing profiles in the
pack are useful but neither answers this question: `linearity_runs.py`'s profile stops at
200 Hz and runs both DUTs at the 175 mVpp spec drive, and `hd3_vs_fin.py` runs the small
43.75 mVpp drive on the PRE-layout cell.  This sweep is the extracted cell alone, over the
full 20-300 Hz band, at one small drive, and then an amplitude ladder at the worst point.

Two things the numbers mean, and do not mean.  The corner is 250 Hz and the filter is 4th
order, so above ~83 Hz the third harmonic is already past the corner and by 300 Hz the
FUNDAMENTAL itself is in the rolloff: what the DFT sees at the output is the harmonic the
cell generated MINUS the filter's own attenuation of it, referenced to a fundamental that
is itself shrinking.  Both effects are recorded here -- `out_fund_vpp` per point makes the
second visible -- so the profile is read as "distortion at the output", which is what a
downstream stage sees, and not as "the nonlinearity of the cell".  Second: HD2 on a
balanced differential cell sits at the numerical floor by construction; it is reported at
every point because the reviewer asked for it and because an HD2 that climbs is evidence
of asymmetry, not of a distortion mechanism.

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice OMP_NUM_THREADS=1 LPF_JOBS=16 \
        .venv/bin/python signoff/paper-draft/scripts/pex_distortion_sweeps.py

Writes `data/pex_distortion_sweeps.json`.  Needs ngspice + the PDK.
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

from lab import parallel as P, thd as T  # noqa: E402

import linearity_runs as LR  # noqa: E402

#: The frequency axis the reviewer asked for: 20 Hz to 300 Hz, closing up around the
#: 250 Hz corner where the response is moving fastest.
FINS = (20.0, 35.0, 50.0, 65.0, 80.0, 100.0, 125.0, 150.0, 175.0, 200.0, 250.0, 300.0)

#: The drive for the frequency profile.  The request said "50 Vpp", which cannot be meant
#: literally -- the rail is 1.5 V -- so it is read as 50 mVpp DIFFERENTIAL at the input.
#: That sits inside the cubic region (the A^2 law holds to ~175 mVpp) and between the
#: pack's two existing profile drives, 43.75 and 175 mVpp.
PROFILE_VPP = 50e-3

#: The amplitude axis at the worst frequency: the ladder `linearity_runs.py` already uses,
#: so the two are directly comparable, plus the profile's own drive to tie them together.
LADDER_VPP = tuple(sorted(set(LR.THD_VPP) | {PROFILE_VPP}))


def _row(fin: float, vpp: float, r) -> dict:
    return {"fin": fin, "vpp_diff": vpp, "thd_db": r.thd_db, "hd3_db": r.hd3_db,
            "hd2_db": r.hd2_db, "out_fund_vpp": r.out_fund_vpp, "out_vpp": r.out_vpp,
            "per_harmonic": {str(k): v for k, v in r.per_harmonic.items()}}


def main() -> None:
    d = LR.design_of("H12-pdk-cap", pex=True)

    print(f"THD/HD2/HD3 vs frequency on post_pex at {PROFILE_VPP * 1e3:g} mVpp", flush=True)
    res = P.batch(list(FINS), lambda f: T.measure(
        d, fin=f, ampl=PROFILE_VPP / 2.0, target_out_vpp=None, gate=False,
        tag=f"rev_pexprof_{f:g}hz"))
    prof = [_row(f, PROFILE_VPP, r) for f, r in zip(FINS, res) if not isinstance(r, Exception)]
    if len(prof) != len(FINS):
        bad = [f for f, r in zip(FINS, res) if isinstance(r, Exception)]
        raise SystemExit(f"frequency profile failed at {bad}")
    for r in prof:
        print(f"  fin {r['fin']:6.1f} Hz   THD {r['thd_db']:8.3f}   HD3 {r['hd3_db']:8.3f}   "
              f"HD2 {r['hd2_db']:8.3f}   out {r['out_fund_vpp'] * 1e3:7.3f} mVpp", flush=True)

    worst = max(prof, key=lambda r: r["thd_db"])
    fin_w = worst["fin"]
    print(f"\nworst THD at {fin_w:g} Hz ({worst['thd_db']:.3f} dB); "
          f"amplitude ladder there", flush=True)

    res = P.batch(list(LADDER_VPP), lambda v: T.measure(
        d, fin=fin_w, ampl=v / 2.0, target_out_vpp=None, gate=False,
        tag=f"rev_pexlad_{fin_w:g}hz_{v * 1e3:.4g}mvpp"))
    lad = [_row(fin_w, v, r) for v, r in zip(LADDER_VPP, res) if not isinstance(r, Exception)]
    if len(lad) != len(LADDER_VPP):
        bad = [v for v, r in zip(LADDER_VPP, res) if isinstance(r, Exception)]
        raise SystemExit(f"amplitude ladder failed at {bad}")
    for r in lad:
        print(f"  {r['vpp_diff'] * 1e3:8.3f} mVpp   THD {r['thd_db']:8.3f}   "
              f"HD3 {r['hd3_db']:8.3f}   HD2 {r['hd2_db']:8.3f}   "
              f"out {r['out_fund_vpp'] * 1e3:8.3f} mVpp", flush=True)

    (OUT / "pex_distortion_sweeps.json").write_text(json.dumps(
        {"dut": "post_pex", "profile_vpp_diff": PROFILE_VPP,
         "profile_note": "request said 50 Vpp; read as 50 mVpp differential (VDD is 1.5 V)",
         "worst_fin_hz": fin_w, "worst_thd_db": worst["thd_db"],
         "profile": prof, "ladder": lad}, indent=1))


if __name__ == "__main__":
    main()
