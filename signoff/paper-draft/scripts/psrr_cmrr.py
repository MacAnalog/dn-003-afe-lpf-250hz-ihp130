#!/usr/bin/env python
"""PSRR, CMRR and input-referred offset -- the three quantities G12 records as missing.

Why the nominal number is not the answer.  This cell is geometrically symmetric, so
supply -> DIFFERENTIAL output and common-mode -> differential output both cancel by
construction: at nominal the simulator returns whatever its own solver residual is, which
reads as a spectacular rejection figure and means nothing about silicon.  What is finite
at nominal is the COMMON-MODE response (supply -> output CM, CM in -> CM out), and what
is real for the differential path is the MISMATCH-limited value.  Both are reported, and
the offset distribution is the same mismatch draw seen in the time domain.

    LPF_NGSPICE=... PDK_ROOT=... .venv/bin/python \\
        signoff/paper-draft/scripts/psrr_cmrr.py [--seeds 32]
"""
from __future__ import annotations

import argparse
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
from linearity_runs import CAMPAIGN_DUTS, campaign_design, dut_suffix  # noqa: E402
from lab import config as C, ngspice as ng, raw as R  # noqa: E402
from lab.deck import ac_cmrr, ac_noise, ac_psrr  # noqa: E402
from lab.mc import _seeded  # noqa: E402
from lab.parallel import batch  # noqa: E402

import mc_stats as MC  # noqa: E402

CELL = "H12-pdk-cap"
#: Spot frequencies the tables quote: dc, the THD spec tone, the cutoff, the stopband.
SPOTS = (0.1, 50.0, 250.0, 1000.0)


def _ac(plots) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(f, differential response, common-mode response) of one ac plot.

    Every stimulus in this file is a 1 V ac source, so the vectors ARE the transfers.
    """
    ac = R.pick(plots, "ac")
    f = np.asarray(np.real(ac.x), float)
    vp = np.asarray(ac["v(voutp)"], complex)
    vn = np.asarray(ac["v(voutn)"], complex)
    return f, vp - vn, 0.5 * (vp + vn)


def _db(y: np.ndarray) -> np.ndarray:
    return 20 * np.log10(np.maximum(np.abs(y), 1e-300))


def _at(f: np.ndarray, y: np.ndarray, spots=SPOTS) -> dict:
    """|y| in dB at each spot frequency, interpolated in log-frequency."""
    mag = _db(y)
    return {f"{s:g}": float(np.interp(np.log10(s), np.log10(f), mag)) for s in spots}


def _offset_v(plots) -> float:
    """Differential output offset at the operating point, in volts."""
    op = R.pick(plots, "op")
    return float(np.real(np.asarray(op["v(voutp)"])).ravel()[0]
                 - np.real(np.asarray(op["v(voutn)"])).ravel()[0])


def measure(d, *, corner: str, temp: float, vdd: float | None, tag: str,
            seed: int | None = None) -> dict:
    """A_dm, and the four rejection transfers, at one PVT point / one mismatch draw."""
    def run(deck, sfx):
        return ng.plots(ng.run(_seeded(deck, seed) if seed is not None else deck,
                               f"{tag}_{sfx}"))

    kw = {"corner": corner, "temp": temp, "vdd": vdd}
    p_dm = run(ac_noise(d, **kw), "dm")
    f, dm, _cm = _ac(p_dm)

    p_cm = run(ac_cmrr(d, **kw), "cm")
    fc_, cm2dm, cm2cm = _ac(p_cm)
    p_ps = run(ac_psrr(d, **kw), "ps")
    fp_, ps2dm, ps2cm = _ac(p_ps)
    assert np.allclose(f, fc_) and np.allclose(f, fp_), "ac grids differ"

    # Rejection is referred to the differential gain the cell actually has, so a
    # passband droop cannot flatter the number.
    cmrr = dm / np.where(np.abs(cm2dm) > 0, cm2dm, 1e-300)
    psrr = dm / np.where(np.abs(ps2dm) > 0, ps2dm, 1e-300)
    off = _offset_v(p_dm)
    gdc = float(np.abs(dm[0]))
    return {
        "a_dm_db": _at(f, dm),
        "cmrr_db": _at(f, cmrr), "psrr_db": _at(f, psrr),
        # The two transfers the rejection ratios are BUILT from, kept beside them: a
        # ratio hides which of its halves moved, and only the leakage paths --
        # common-mode input and supply, each to the DIFFERENTIAL output -- say how much
        # unwanted signal actually arrives.  CMRR = A_dm / (CM -> DM),
        # PSRR = A_dm / (supply -> DM); in dB, the ratio is the vertical gap.
        "cm_to_dm_db": _at(f, cm2dm), "supply_to_dm_db": _at(f, ps2dm),
        "cm_to_cm_db": _at(f, cm2cm), "supply_to_cm_db": _at(f, ps2cm),
        # The spot values above are what the tables quote; the full sweep is what a
        # rejection plot needs.  Four interpolated points drawn as a line would imply a
        # shape between them that was never measured.
        "curves": {"f": f.tolist(),
                   **{k: _db(v).tolist() for k, v in
                      (("a_dm_db", dm), ("cmrr_db", cmrr), ("psrr_db", psrr),
                       ("cm_to_dm_db", cm2dm), ("supply_to_dm_db", ps2dm),
                       ("cm_to_cm_db", cm2cm), ("supply_to_cm_db", ps2cm))}},
        "offset_out_v": off,
        "offset_in_v": off / gdc if gdc else None,
        "dc_gain": gdc,
        "seed": seed,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=32,
                    help="mismatch draws for the differential-path numbers")
    ap.add_argument("--dut", default="pre_mim", choices=CAMPAIGN_DUTS,
                    help="which DUT to run the campaign on (default: %(default)s)")
    a = ap.parse_args()
    sfx = dut_suffix(a.dut)
    d = campaign_design(a.dut, CELL)
    OUT.mkdir(parents=True, exist_ok=True)

    print("nominal + certified axes (common-mode transfers are the meaningful ones):")
    def one_corner(c):
        return measure(d, corner=c.process, temp=c.temp, vdd=c.vdd,
                       tag=f"rej{sfx}_{c.slug}")
    corner_rows = batch(list(CERT_AXES), one_corner)
    corners = {}
    for c, r in zip(CERT_AXES, corner_rows):
        if isinstance(r, BaseException):
            print(f"  [{c.slug}] FAILED {r!r}")
            continue
        corners[c.slug] = {"corner": c.as_dict(), **r}
        print(f"  [{c.slug:16s}] supply->CM {r['supply_to_cm_db']['0.1']:8.2f} dB, "
              f"CM->CM {r['cm_to_cm_db']['0.1']:8.2f} dB @dc")

    print(f"\nmismatch, {a.seeds} draws at {C.CORNER_MM_NOM} / {C.TEMP_NOM:g} C "
          f"(the differential path is mismatch-limited):")
    def one_seed(s):
        return measure(d, corner=C.CORNER_MM_NOM, temp=C.TEMP_NOM, vdd=None,
                       tag=f"rej{sfx}_mm_s{s:05d}", seed=s)
    seed_rows = batch(list(range(1, a.seeds + 1)), one_seed)
    draws = [r for r in seed_rows if not isinstance(r, BaseException)]
    nfail = len(seed_rows) - len(draws)

    def stat(get):
        v = np.asarray([get(r) for r in draws], float)
        # p01/p99 alongside min/max because only the quantiles are comparable across N:
        # see `mc_stats` -- min and max are order statistics and must drift outward as
        # draws are added.  `se_sigma_frac` is (M1), the error bar on sigma itself.
        return MC.annotate({
            "n": int(v.size), "mean": float(v.mean()), "sigma": float(v.std(ddof=1)),
            "min": float(v.min()), "max": float(v.max()),
            "p50": float(np.median(v)), "p10": float(np.percentile(v, 10)),
            "p01": float(np.percentile(v, 1)), "p99": float(np.percentile(v, 99))})

    mm = {"n_draws": len(draws), "n_failed": nfail,
          "offset_in_uv": stat(lambda r: 1e6 * r["offset_in_v"]),
          "offset_in_abs_uv": stat(lambda r: abs(1e6 * r["offset_in_v"]))}
    # The draws themselves, not only their moments: a rejection distribution set by
    # mismatch is not Gaussian in dB, so a mean and a sigma do not reconstruct it and a
    # reader plotting the spread needs the samples.
    mm["draws"] = [{"seed": r["seed"], "offset_in_uv": 1e6 * r["offset_in_v"],
                    **{f"{k}_{s}hz": r[k][s] for k in ("cmrr_db", "psrr_db")
                       for s in map(lambda x: f"{x:g}", SPOTS)}}
                   for r in draws]
    # The BAND, not one sweep per draw.  The figure and the CSV both consume only the
    # mean and the min-max envelope at each frequency, and keeping every draw's 301
    # points would put tens of MB of derived JSON in the repo to plot three curves.
    mm["curves"] = {"f": draws[0]["curves"]["f"]}
    for k in ("a_dm_db", "cm_to_dm_db", "supply_to_dm_db", "cmrr_db", "psrr_db"):
        v = np.asarray([r["curves"][k] for r in draws], float)
        mm["curves"][k] = {"mean": v.mean(0).tolist(), "min": v.min(0).tolist(),
                           "max": v.max(0).tolist()}
    for k in ("cmrr_db", "psrr_db", "cm_to_dm_db", "supply_to_dm_db"):
        mm[k] = {s: stat(lambda r, s=s, k=k: r[k][s]) for s in map(lambda x: f"{x:g}", SPOTS)}
    # Convergence of the three headline distributions, in seed order (see `mc_stats`).
    mm["convergence"] = {
        "offset_in_uv": MC.trace([1e6 * r["offset_in_v"] for r in draws]),
        **{f"{k}_0.1hz": MC.trace([r[k]["0.1"] for r in draws])
           for k in ("cmrr_db", "psrr_db")}}
    for k, s in (("cmrr_db", "0.1"), ("psrr_db", "0.1")):
        v = mm[k][s]
        print(f"  {k:9s} @dc  mean {v['mean']:7.2f} dB  "
              f"sigma {v['sigma']:6.2f} +/-{100 * v['se_sigma_frac']:.1f} %  "
              f"p01 {v['p01']:7.2f}  worst {v['min']:7.2f}")
    o = mm["offset_in_abs_uv"]
    print(f"  |offset|      mean {o['mean']:7.2f} uV  sigma {o['sigma']:6.2f} "
          f"+/-{100 * o['se_sigma_frac']:.1f} %  p99 {o['p99']:7.2f}  "
          f"worst {o['max']:7.2f} uV")
    for k, tr in mm["convergence"].items():
        print(f"  converge {k:16s} sigma drifted {MC.drift_pct(tr):5.2f} % over the last "
              f"4 rungs; (M1) allows {100 * MC.se_frac(len(draws)):.2f} %")

    out = OUT / f"psrr_cmrr{sfx}.json"
    out.write_text(json.dumps(
        {"cell": CELL, "dut": a.dut, "spots_hz": list(SPOTS), "corners": corners,
         "mismatch": mm}, indent=1))
    print(f"\nwrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
