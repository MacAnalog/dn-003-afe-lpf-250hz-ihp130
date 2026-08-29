#!/usr/bin/env python
"""Every transient this pack needs: the THD amplitude ladder, the THD frequency
profile, and the two-tone IMD3/IIP3 ladder -- pre- and post-layout.

Three measurements, one file because they share one instrument (`lab.thd`'s coherent
strobed transient + DFT) and one economy problem (transients are the most expensive run
in the repo, so they are batched across cores rather than serialised).

**THD ladder** (closes `doc/paper/README.md` gap G13).  Open loop -- an explicit `ampl`
with `target_out_vpp=None` -- because servoing the output level to a constant would
destroy exactly the amplitude dependence being measured.  `ampl` is the DIFFERENTIAL
amplitude, i.e. half the differential Vpp (`lab.metrics.THD_AMPL` = 87.5 mV = the
175 mVpp spec point).

**THD profile** over fin: informative only, never a pass/fail (spec is 50 Hz).  The
post-layout column closes gap G7.

**Two-tone IMD3** is a NEW bench and is deliberately **report-only**: IMD3/IIP3 are not
S1-S8 lines and nothing here re-defines a spec metric.  Its one design constraint is
coherence, imposed the same way `lab.deck.tran_thd` imposes it: both tones and every
intermodulation product of interest must land exactly on a DFT bin, so the tones are
integer multiples of a grid frequency `fg` and the record is an integer number of
`fg` cycles.  With fg = 5 Hz, f1 = 45 Hz (9 fg) and f2 = 55 Hz (11 fg):

    IMD3 lower  2f1 - f2 = 35 Hz  (7 fg)      IMD2 diff  f2 - f1 =  10 Hz (2 fg)
    IMD3 upper  2f2 - f1 = 65 Hz  (13 fg)     IMD2 sum   f1 + f2 = 100 Hz (20 fg)

all integer bins, all inside or just above the passband.  The tolerance set is the
frozen THD one (`.options reltol=1e-5 abstol=1e-13 ... method=gear maxord=2`).

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_JOBS=24 \
        .venv/bin/python signoff/paper-draft/scripts/linearity_runs.py
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

os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
os.environ.setdefault("PDK", "ihp-sg13g2")
os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))

import numpy as np  # noqa: E402

from lab import config as C, metrics as M, ngspice as ng, parallel as P, raw as R, thd as T  # noqa: E402
from lab.deck import _bias, _core, _libs  # noqa: E402
from lab.dut import Design, Dev, subckt  # noqa: E402

SIGNOFF = REPO / "signoff/post-pvt"
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"

# THD amplitude ladder, as DIFFERENTIAL Vpp.  175 mVpp is the S7 spec point.
THD_VPP = (43.75e-3, 87.5e-3, 175e-3, 350e-3, 525e-3, 700e-3)
THD_FINS = (20.0, 50.0, 100.0, 150.0, 200.0)

# Two-tone bench.
FG = 5.0
F1, F2 = 45.0, 55.0
TT_CYCLES, TT_SETTLE, TT_PPC = 16, 6, 512
# Per-tone differential amplitude.  A = 43.75 mV puts the two-tone PEAK envelope
# (2A = 87.5 mV) at the same place as the single-tone S7 point.
TT_AMPL = (10.9375e-3, 21.875e-3, 43.75e-3, 87.5e-3, 131.25e-3)


def design_of(cell: str, *, pex: bool = False) -> Design:
    g = json.loads((SIGNOFF / cell / "design.json").read_text())["design"]
    d = Design(topology=g["topology"],
               devs={r: Dev(**v) for r, v in g["devs"].items()},
               iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
               lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
               cap_model=g.get("cap_model", "ideal"),
               **{k: v * 1e-12 for k, v in g["caps_pf"].items()})
    return d.with_(dut_override=PEX.read_text().replace("$", "_")) if pex else d


# --------------------------------------------------------------- two-tone bench --
def tran_twotone(d: Design, a1: float, a2: float, *, f1: float = F1, f2: float = F2,
                 fg: float = FG, cycles: int = TT_CYCLES, settle: int = TT_SETTLE,
                 ppc: int = TT_PPC, corner: str = C.CORNER_NOM,
                 temp: float = C.TEMP_NOM, vdd: float | None = None) -> str:
    """Coherent strobed two-tone transient.  `ppc` is points per GRID cycle."""
    tper = 1.0 / fg
    tstop = (settle + cycles) * tper
    tstep = tper / ppc
    stim = "\n".join([
        f"vcm vcm 0 {d.vicm}",
        # `vsig` keeps its `ac 1` so the deck still has a well-formed ac source
        # (`lab.deck` documents that ngspice aborts the noise/ac path without one).
        f"{C.IN_SRC} sig2 vcm dc 0 sin(0 {a1:.10g} {f1:.10g}) ac 1",
        f"vsig2 sig sig2 dc 0 sin(0 {a2:.10g} {f2:.10g})",
        "evp vinp vcm sig vcm 0.5",
        "evn vinn vcm sig vcm -0.5",
    ])
    return f""".title lpf {d.topology} -- two-tone f1={f1:g} f2={f2:g} a={a1:g}
{_libs(corner, d)}
{subckt(d)}
{_core(d, vdd=vdd)}
{_bias(d)}
{stim}
.temp {temp}
.options reltol=1e-5 abstol=1e-13 vntol=1e-9 chgtol=1e-16 method=gear maxord=2
.control
set filetype=binary
op
tran {tstep:.10g} {tstop:.10g} {settle * tper:.10g} {tstep:.10g}
write sim.raw
.endc
.end
"""


def score_twotone(plots, a: float, tag: str) -> dict:
    """Coherent DFT of a two-tone record; every product read straight off its bin."""
    tr = R.pick(plots, "tran")
    t = np.real(tr.x).astype(float)
    y = np.real(tr.get(C.OUT_P) - tr.get(C.OUT_N)).astype(float)
    n = TT_CYCLES * TT_PPC
    grid = t[0] + np.arange(n) / (FG * TT_PPC)
    grid = grid[grid <= t[-1]]
    n = (len(grid) // TT_PPC) * TT_PPC
    if n < 4 * TT_PPC:
        raise ng.SimError(f"{tag}: two-tone record too short ({len(grid)} pts)")
    ys = np.interp(grid[:n], t, y)
    cyc = n // TT_PPC                      # DFT bins per grid cycle
    z = ys - ys.mean()
    rect = np.abs(np.fft.rfft(z)) * (2.0 / n)
    hann = np.abs(np.fft.rfft(z * np.hanning(n))) * (2.0 / n)

    def bin_of(f: float) -> int:
        return int(round(f / FG)) * cyc

    def amp(f: float) -> float:
        return float(rect[bin_of(f)])

    fund = 0.5 * (amp(F1) + amp(F2))
    im3 = {"lo": amp(2 * F1 - F2), "hi": amp(2 * F2 - F1)}
    im2 = {"diff": amp(F2 - F1), "sum": amp(F1 + F2)}
    db = lambda x: float(20 * np.log10(max(x, 1e-300) / max(fund, 1e-300)))  # noqa: E731
    # Coherence check, same contract as lab.thd: a rectangular and a Hann window on a
    # truly coherent record must agree; if they do not, the number is leakage.
    h_im3 = 20 * np.log10(max(hann[bin_of(2 * F1 - F2)], 1e-300)
                          / max(0.5 * (hann[bin_of(F1)] + hann[bin_of(F2)]), 1e-300))
    if abs(db(im3["lo"]) - h_im3) > 3.0:
        raise ng.SimError(f"{tag}: rect/hann IMD3 disagree by "
                          f"{abs(db(im3['lo']) - h_im3):.1f} dB -- record not coherent")
    imd3_db = db(0.5 * (im3["lo"] + im3["hi"]))
    return {
        "ampl_per_tone_v": a, "fund_v": fund,
        "imd3_lo_db": db(im3["lo"]), "imd3_hi_db": db(im3["hi"]),
        "imd3_db": imd3_db,
        "imd2_diff_db": db(im2["diff"]), "imd2_sum_db": db(im2["sum"]),
        # Input-referred IP3 in dBV (amplitude convention): the per-tone input level
        # plus half the IMD3 suppression.  Report-only, extrapolated from one point --
        # the ladder's 3:1 slope is what makes the extrapolation legitimate.
        "iip3_dbv": float(20 * np.log10(a) - imd3_db / 2.0),
        "oip3_dbv": float(20 * np.log10(fund) - imd3_db / 2.0),
    }


# ------------------------------------------------------------------------- runs --
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    duts = {"pre_mim": design_of("H12-pdk-cap"),
            "post_pex": design_of("H12-pdk-cap", pex=True)}
    res: dict = {"thd_ladder": {}, "thd_profile": {}, "twotone": {},
                 "bench": {"fg": FG, "f1": F1, "f2": F2, "cycles": TT_CYCLES,
                           "settle": TT_SETTLE, "ppc": TT_PPC,
                           "thd_vpp": list(THD_VPP), "thd_fins": list(THD_FINS),
                           "tt_ampl": list(TT_AMPL)}}

    for label, d in duts.items():
        lad = P.batch(list(THD_VPP), lambda v, d=d, label=label: T.measure(
            d, fin=M.THD_FIN, ampl=v / 2.0, target_out_vpp=None, gate=False,
            tag=f"rev_thdlad_{label}_{v * 1e3:.4g}mvpp"))
        res["thd_ladder"][label] = [
            {"vpp_diff": v, "ampl": v / 2.0, "thd_db": r.thd_db, "hd3_db": r.hd3_db,
             "hd2_db": r.hd2_db, "out_fund_vpp": r.out_fund_vpp}
            for v, r in zip(THD_VPP, lad) if not isinstance(r, Exception)]
        print(f"[thd-ladder {label}] {len(res['thd_ladder'][label])}/{len(THD_VPP)} ok",
              flush=True)

        prof = P.batch(list(THD_FINS), lambda f, d=d, label=label: T.measure(
            d, fin=f, ampl=M.THD_AMPL, target_out_vpp=None, gate=False,
            tag=f"rev_thdprof_{label}_{f:g}hz"))
        res["thd_profile"][label] = [
            {"fin": f, "thd_db": r.thd_db, "hd3_db": r.hd3_db, "hd2_db": r.hd2_db,
             "out_fund_vpp": r.out_fund_vpp}
            for f, r in zip(THD_FINS, prof) if not isinstance(r, Exception)]
        print(f"[thd-profile {label}] {len(res['thd_profile'][label])}/{len(THD_FINS)} ok",
              flush=True)

        def one_tt(a, d=d, label=label):
            plots = ng.simulate(tran_twotone(d, a, a),
                                f"rev_tt_{label}_{a * 1e3:.5g}mv", timeout=7200)
            return score_twotone(plots, a, f"tt_{label}_{a:g}")

        tt = P.batch(list(TT_AMPL), one_tt)
        res["twotone"][label] = [r for r in tt if not isinstance(r, Exception)]
        for r in tt:
            if isinstance(r, Exception):
                print(f"[twotone {label}] FAILED: {r}", flush=True)
        print(f"[twotone {label}] {len(res['twotone'][label])}/{len(TT_AMPL)} ok",
              flush=True)
        (OUT / "linearity.json").write_text(json.dumps(res, indent=1))

    (OUT / "linearity.json").write_text(json.dumps(res, indent=1))
    print("done")


if __name__ == "__main__":
    main()
