#!/usr/bin/env python
"""Confirm the HD3 crossing of `validation.md` §6.1 by SIMULATING at it.

§6.1 solves the drive at which HD3 reaches its target by walking the fitted `A^2` law
from the highest uncompressed point of the ladder.  That is an interpolation -- the
target sits between two measured amplitudes -- but it is still a solved number, not a
measured one.  This script closes that gap: it re-runs the pack's own THD instrument
(`lab.thd.measure`, the same coherent strobed transient + DFT that produced the ladder)
at exactly the solved drive, on both DUTs, and reports the HD3 it actually gets.

The test is honest only if nothing is re-tuned to pass it, so the amplitude is read from
`data/linearity_analysis.json` and used verbatim -- no servo (`target_out_vpp=None`, the
ladder's own open-loop convention), no re-fit, no second guess.

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
        .venv/bin/python signoff/paper-draft/scripts/hd3_crossing_probe.py

Writes `data/hd3_crossing_probe.json`.  Needs ngspice + the PDK; two transients, ~1 min.
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

from lab import metrics as M, thd as T  # noqa: E402

from linearity_runs import design_of  # noqa: E402

#: How far the measurement may sit from the target before the crossing is not confirmed.
#: The ladder's own fit residual is ~0.5 dB, so a solved point cannot be expected to land
#: closer than that; 1 dB is that residual with room, and still an order below the 13.6 dB
#: the two bracketing measurements span.
TOL_DB = 1.0


def main() -> None:
    xc = json.loads((OUT / "linearity_analysis.json").read_text())["amplitude_law"]["hd3_crossing"]
    target = xc["target_db"]
    duts = {"pre_mim": design_of("H12-pdk-cap"),
            "post_pex": design_of("H12-pdk-cap", pex=True)}

    rows = []
    for label, d in duts.items():
        vpp = xc["per_dut"][label]["vpp_diff"]
        r = T.measure(d, fin=M.THD_FIN, ampl=vpp / 2.0, target_out_vpp=None, gate=False,
                      tag=f"rev_hd3x_{label}_{vpp * 1e3:.4g}mvpp")
        rows.append({"dut": label, "vpp_diff": vpp, "solved_hd3_db": target,
                     "measured_hd3_db": r.hd3_db, "measured_thd_db": r.thd_db,
                     "measured_hd2_db": r.hd2_db, "out_fund_vpp": r.out_fund_vpp,
                     "err_db": r.hd3_db - target})
        print(f"  {label:9s} drove {vpp * 1e3:6.2f} mVpp  ->  HD3 {r.hd3_db:7.3f} dB "
              f"(solved {target:+.0f}, err {r.hd3_db - target:+.3f} dB), "
              f"THD {r.thd_db:7.3f} dB", flush=True)

    worst = max(abs(r["err_db"]) for r in rows)
    ok = worst <= TOL_DB
    (OUT / "hd3_crossing_probe.json").write_text(json.dumps(
        {"target_db": target, "tol_db": TOL_DB, "worst_err_db": worst,
         "confirmed": ok, "rows": rows}))
    print(f"\nworst error {worst:.3f} dB against a {TOL_DB:.1f} dB tolerance -- "
          + ("CONFIRMED" if ok else "NOT CONFIRMED"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
