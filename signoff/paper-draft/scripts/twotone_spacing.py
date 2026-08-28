#!/usr/bin/env python
"""Two-tone IMD3 vs TONE SPACING -- the experiment that decides whether the cell's
third-order behaviour is memoryless.

For a memoryless cubic, IMD3 (relative to the carriers) is `HD3 + 9.54 dB` at the same
per-tone amplitude, and it does not depend on the tone spacing at all.  Measured here at
one drive level, IMD3 sits well above that bound, so one of the two premises is false.
Sweeping the spacing separates them: a spacing-INDEPENDENT offset is a static
nonlinearity the memoryless algebra simply mis-models, while a spacing-DEPENDENT one is
memory -- second-order products at (f2 - f1) and (f1 + f2) circulating inside the
feedback loop and re-mixing to third order.  (The cell's even-order products cancel at
the differential OUTPUT -- measured IMD2 is at -119 dBc -- but each half's internal nodes
are single-ended and carry them at full strength, so the mechanism is available.)

Tone pairs are centred on 50 Hz, the S7 spec frequency, and every pair stays coherent on
the same 1 Hz grid so f1, f2, 2f1-f2 and 2f2-f1 all land exactly on DFT bins.

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_JOBS=24 \
        .venv/bin/python signoff/paper-draft/scripts/twotone_spacing.py
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

import linearity_runs as LR  # noqa: E402
from lab import config as C, ngspice as ng, parallel as P, raw as R  # noqa: E402

FC = 50.0                       # tone-pair centre = the S7 spec frequency
# Full spacing f2 - f1, Hz.  Every entry must be EVEN so that f1 = 50 - sp/2 and
# f2 = 50 + sp/2 are integers and therefore exact bins on the 1 Hz grid; an odd spacing
# puts the tones on half-bins and the result is leakage, not distortion (measured: a
# 5 Hz spacing reads IMD3 = -0.8 dBc, i.e. nonsense).
SPACINGS = (2.0, 4.0, 10.0, 20.0, 30.0)
AMPL = 21.875e-3                # per tone; the linear end of the ladder
FG = 1.0                        # 1 Hz grid: every tone and product is an integer bin
CYCLES, SETTLE, PPC = 4, 2, 2048   # 4 s of record at 2048 Sa/s


def score(plots, f1, f2, tag):
    tr = R.pick(plots, "tran")
    t = np.real(tr.x).astype(float)
    y = np.real(tr.get(C.OUT_P) - tr.get(C.OUT_N)).astype(float)
    n = CYCLES * PPC
    grid = t[0] + np.arange(n) / (FG * PPC)
    grid = grid[grid <= t[-1]]
    n = (len(grid) // PPC) * PPC
    ys = np.interp(grid[:n], t, y)
    cyc = n // PPC
    z = ys - ys.mean()
    rect = np.abs(np.fft.rfft(z)) * (2.0 / n)
    hann = np.abs(np.fft.rfft(z * np.hanning(n))) * (2.0 / n)
    for ftone in (f1, f2, 2 * f1 - f2, 2 * f2 - f1):
        if abs(abs(ftone) / FG - round(abs(ftone) / FG)) > 1e-9:
            raise ng.SimError(f"{tag}: {ftone} Hz is not a bin on the {FG} Hz grid")
    amp = lambda f: float(rect[int(round(abs(f) / FG)) * cyc])  # noqa: E731
    amph = lambda f: float(hann[int(round(abs(f) / FG)) * cyc])  # noqa: E731
    fund = 0.5 * (amp(f1) + amp(f2))
    im3 = 0.5 * (amp(2 * f1 - f2) + amp(2 * f2 - f1))
    # Coherence guard, same contract as lab.thd: rect and hann must agree on a coherent
    # record.  Without it a half-bin tone reads as a huge, entirely fictitious IMD3.
    r_db = 20 * np.log10(max(im3, 1e-300) / max(fund, 1e-300))
    h_db = 20 * np.log10(max(0.5 * (amph(2 * f1 - f2) + amph(2 * f2 - f1)), 1e-300)
                         / max(0.5 * (amph(f1) + amph(f2)), 1e-300))
    if abs(r_db - h_db) > 3.0:
        raise ng.SimError(f"{tag}: rect/hann IMD3 disagree by {abs(r_db - h_db):.1f} dB "
                          "-- the record is not coherent")
    db = lambda x: float(20 * np.log10(max(x, 1e-300) / max(fund, 1e-300)))  # noqa: E731
    return {"f1": f1, "f2": f2, "spacing": f2 - f1, "ampl_per_tone_v": AMPL,
            "fund_v": fund, "imd3_db": db(im3),
            "imd2_diff_db": db(amp(f2 - f1)), "imd2_sum_db": db(amp(f1 + f2)),
            "iip3_dbv": float(20 * np.log10(AMPL) - db(im3) / 2.0)}


def main() -> None:
    d = LR.design_of("H12-pdk-cap")

    def one(sp_hz):
        f1, f2 = FC - sp_hz / 2, FC + sp_hz / 2
        deck = LR.tran_twotone(d, AMPL, AMPL, f1=f1, f2=f2, fg=FG,
                               cycles=CYCLES, settle=SETTLE, ppc=PPC)
        plots = ng.simulate(deck, f"rev_ttsp_{sp_hz:g}hz", timeout=7200)
        return score(plots, f1, f2, f"sp{sp_hz:g}")

    rows = P.batch(list(SPACINGS), one)
    good = [r for r in rows if not isinstance(r, Exception)]
    for r in rows:
        if isinstance(r, Exception):
            print("FAILED:", r, flush=True)
    (OUT / "twotone_spacing.json").write_text(json.dumps(
        {"centre_hz": FC, "ampl_per_tone_v": AMPL, "fg": FG,
         "cycles": CYCLES, "settle": SETTLE, "ppc": PPC, "rows": good}, indent=1))
    for r in good:
        print(f"spacing {r['spacing']:5.1f} Hz  IMD3 {r['imd3_db']:8.3f} dBc  "
              f"IIP3 {r['iip3_dbv']:7.3f} dBV  IMD2diff {r['imd2_diff_db']:8.2f}", flush=True)


if __name__ == "__main__":
    main()
