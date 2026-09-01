#!/usr/bin/env python
"""HD3 versus input frequency at a SMALL, fixed drive -- the frequency dependence of the
cell's third-order behaviour, measured away from compression.

`linearity_runs.py`'s THD profile is taken at the 175 mVpp spec drive, where the cell is
already partly slew limited above ~50 Hz, so it mixes two effects.  This sweep runs at
43.75 mVpp (a quarter of the spec drive, the clean end of the amplitude ladder), where
HD3 still obeys the A^2 law, so whatever frequency dependence remains is the *mechanism*
and not the onset of compression.  It is the evidence for or against treating the cell as
memoryless when relating HD3 to IMD3.

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_JOBS=16 \
        .venv/bin/python signoff/paper-draft/scripts/hd3_vs_fin.py
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

import linearity_runs as LR  # noqa: E402
from lab import parallel as P, thd as T  # noqa: E402

AMPL = 21.875e-3          # 43.75 mVpp differential -- a quarter of the S7 drive
FINS = (10.0, 20.0, 35.0, 50.0, 65.0, 100.0, 150.0, 200.0)


def main() -> None:
    dut = LR.dut_argv()
    sfx = LR.dut_suffix(dut)
    d = LR.campaign_design(dut)
    rows = P.batch(list(FINS), lambda f: T.measure(
        d, fin=f, ampl=AMPL, target_out_vpp=None, gate=False,
        tag=f"rev_hd3fin{sfx}_{f:g}hz"))
    good = [{"fin": f, "thd_db": r.thd_db, "hd3_db": r.hd3_db, "hd2_db": r.hd2_db,
             "out_fund_vpp": r.out_fund_vpp}
            for f, r in zip(FINS, rows) if not isinstance(r, Exception)]
    (OUT / f"hd3_vs_fin{sfx}.json").write_text(json.dumps(
        {"dut": dut, "ampl": AMPL, "vpp_diff": 2 * AMPL, "rows": good}, indent=1))
    for r in good:
        print(f"fin {r['fin']:6.1f} Hz  HD3 {r['hd3_db']:8.3f} dBc  "
              f"out {r['out_fund_vpp'] * 1e3:7.2f} mVpp", flush=True)


if __name__ == "__main__":
    main()
