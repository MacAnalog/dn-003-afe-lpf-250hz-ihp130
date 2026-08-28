#!/usr/bin/env python
"""Export every reviewer-requested curve as a plain CSV for Veusz.

This script re-serialises data that already exists -- it runs no simulation and
re-defines no metric.  Every number comes from the same JSON the tables and
figures in `validation.md` are built from, so a CSV and a figure can never
disagree.

Written to `signoff/paper-draft/csv/`.  The format is deliberately dumb so that
Veusz's default `Data > Import > CSV` works with no options changed:

  * one header row, then numbers -- no comment lines, no units row, no blank
    leading line (Veusz reads row 1 as the dataset names);
  * column names are lowercase `[a-z0-9_]` with the unit in the name;
  * an empty field means "not valid here", which Veusz reads as missing and
    simply does not plot.  Phase and group delay are blank above each DUT's
    -100 dB magnitude floor, because past that point the swept phase aliases
    and its derivative is fiction (`lab.raw.group_delay_s`).

Phase and group delay are computed by `lab.raw` -- the same functions that
score sign-off -- so `group_delay.csv` reproduces the certified `gd_dc_ms` to
every printed digit.  The script asserts that before it writes anything.

    .venv/bin/python signoff/paper-draft/scripts/export_csv.py

The AC / noise / group-delay files derive from `data/bench_*.json`, which are
gitignored (2.7 MB); run `extract_bench.py` first in a fresh clone.  The
linearity files derive from committed JSON and always regenerate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = HERE.parent / "data"
OUT = HERE.parent / "csv"
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402

from lab import metrics as M, raw as R  # noqa: E402

AC_DUTS = ("pre_ideal", "pre_mim", "post_lumped", "post_pex")
MODEL_DUTS = ("pre_ideal", "pre_mim", "post_lumped")
LIN_DUTS = ("pre_mim", "post_pex")
FMT = "%.10g"


# ---- csv writing ------------------------------------------------------------------

def write_csv(name: str, columns: list[tuple[str, list]]) -> Path:
    """One header row + fixed-format numbers.  `None` in a column -> empty field."""
    n = max(len(v) for _, v in columns)
    lines = [",".join(k for k, _ in columns)]
    for i in range(n):
        row = []
        for _, v in columns:
            x = v[i] if i < len(v) else None
            row.append("" if x is None or (isinstance(x, float) and not np.isfinite(x))
                       else FMT % x)
        lines.append(",".join(row))
    path = OUT / name
    path.write_text("\n".join(lines) + "\n")
    return path


def padded(values, n: int) -> list:
    """A short column (a scored-band prefix) padded to the full sweep with blanks."""
    return list(values) + [None] * (n - len(values))


def load(name: str) -> dict:
    path = DATA / name
    if not path.exists():
        sys.exit(f"missing {path.relative_to(REPO)} -- run extract_bench.py first "
                 f"(see signoff/paper-draft/README.md step 1)")
    return json.loads(path.read_text())


# ---- the exports ------------------------------------------------------------------

def ac_and_group_delay(bench: dict) -> list[Path]:
    """Bode magnitude + phase, and group delay, for all four DUTs."""
    f = np.asarray(bench["pre_mim"]["ac"]["f"], float)
    mag, pha, gd = [], [], []
    checks = []
    for d in AC_DUTS:
        a = bench[d]["ac"]
        assert np.allclose(a["f"], f), f"{d}: AC frequency grid differs"
        h = np.asarray(a["re"], float) + 1j * np.asarray(a["im"], float)
        n = R._floor_prefix(h, M.PH_FLOOR_DB)
        ph = np.unwrap(np.angle(h[:n])) * 180.0 / np.pi
        fg, tau = R.group_delay_s(f, h, M.PH_FLOOR_DB)

        mag.append((f"mag_db_{d}", list(20.0 * np.log10(np.abs(h)))))
        pha.append((f"phase_deg_{d}", padded(ph, len(f))))
        gd.append((f"group_delay_ms_{d}", padded(tau * 1e3, len(f))))
        checks.append((d, float(tau[0]) * 1e3, bench[d]["scorecard"]["gd_dc_ms"]))

    for d, got, want in checks:
        assert abs(got - want) < 1e-12, f"{d}: gd_dc {got} != certified {want}"
    print("  group delay at dc reproduces the certified scorecard:")
    for d, got, _ in checks:
        print(f"    {d:12s} {got:.4f} ms")

    return [write_csv("ac_response.csv", [("f_hz", list(f))] + mag + pha),
            write_csv("group_delay.csv", [("f_hz", list(f))] + gd)]


def ac_model(tf: dict) -> Path:
    """The symbolic model laid next to the simulation, as plotted in figure 1."""
    f = np.asarray(tf["cases"]["pre_mim"]["validation"]["f"], float)
    cols: list[tuple[str, list]] = [("f_hz", list(f))]
    for d in MODEL_DUTS:
        v = tf["cases"][d]["validation"]
        assert np.allclose(v["f"], f), f"{d}: model frequency grid differs"
        cols += [(f"mag_db_sim_{d}", list(v["sim_db"])),
                 (f"mag_db_model_{d}", list(v["model_db"])),
                 (f"phase_deg_sim_{d}", list(v["sim_deg"])),
                 (f"phase_deg_model_{d}", list(v["model_deg"]))]
    return write_csv("ac_response_model.csv", cols)


def noise(bench: dict) -> Path:
    """Input-referred noise density.  Integrating it must give the certified IRN."""
    f = np.asarray(bench["pre_mim"]["noise"]["f"], float)
    cols: list[tuple[str, list]] = [("f_hz", list(f))]
    print("  input-referred noise integrated over "
          f"{M.IRN_BAND[0]}-{M.IRN_BAND[1]} Hz reproduces the certified IRN:")
    for d in AC_DUTS:
        nz = bench[d]["noise"]
        assert np.allclose(nz["f"], f), f"{d}: noise frequency grid differs"
        dens = np.asarray(nz["inoise"], float)
        got = R.integrate_noise(f, dens, *M.IRN_BAND) * 1e6
        want = bench[d]["scorecard"]["irn_uv"]
        assert abs(got - want) < 1e-9, f"{d}: IRN {got} != certified {want}"
        print(f"    {d:12s} {got:.3f} uV")
        cols.append((f"inoise_v_per_rthz_{d}", list(dens)))
    return write_csv("input_referred_noise.csv", cols)


def _harmonic_cols(rows_by_dut: dict, x_key: str) -> list[tuple[str, list]]:
    duts = list(rows_by_dut)
    grid = [r[x_key] for r in rows_by_dut[duts[0]]]
    for d in duts[1:]:
        assert [r[x_key] for r in rows_by_dut[d]] == grid, f"{d}: {x_key} grid differs"
    cols: list[tuple[str, list]] = []
    for key in ("thd_db", "hd3_db", "hd2_db", "out_fund_vpp"):
        for d in duts:
            cols.append((f"{key}_{d}", [r[key] for r in rows_by_dut[d]]))
    return cols


def harmonics(lin: dict, hd3f: dict) -> list[Path]:
    """THD / HD3 / HD2 against amplitude at 50 Hz, and against frequency at two drives."""
    ladder = {d: lin["thd_ladder"][d] for d in LIN_DUTS}
    amp = [("vpp_diff_v", [r["vpp_diff"] for r in ladder["pre_mim"]]),
           ("ampl_v", [r["ampl"] for r in ladder["pre_mim"]])]
    out = [write_csv("thd_vs_amplitude.csv", amp + _harmonic_cols(ladder, "vpp_diff"))]

    prof = {d: lin["thd_profile"][d] for d in LIN_DUTS}
    out.append(write_csv("thd_vs_frequency_175mvpp.csv",
                         [("fin_hz", [r["fin"] for r in prof["pre_mim"]])]
                         + _harmonic_cols(prof, "fin")))

    small = {"pre_mim": hd3f["rows"]}
    mv = f"{hd3f['vpp_diff'] * 1e3:g}".replace(".", "p")
    out.append(write_csv(f"thd_vs_frequency_{mv}mvpp.csv",
                         [("fin_hz", [r["fin"] for r in hd3f["rows"]])]
                         + _harmonic_cols(small, "fin")))
    return out


def iip3(lin: dict, ana: dict) -> list[Path]:
    """Two-tone points as output dBVp vs input dBVp, and the 1:1 / 3:1 extrapolation.

    `in_fit` marks the rows the published slope fit used (IMD3 below -40 dBc, i.e.
    still cubic); `in_ip3_avg` marks the two rows whose IIP3 is averaged into the
    published intercept.  Both are `linearity_analysis.py`'s own selection, so the
    reviewer can reproduce the number from this file alone instead of refitting all
    the points -- the top amplitudes are compressing and would pull the fit.
    """
    pts: list[tuple[str, list]] = []
    lines: list[tuple[str, list]] = []
    print("  IIP3 rebuilt from the exported columns matches linearity_analysis.json:")
    for d in LIN_DUTS:
        rows = lin["twotone"][d]
        fit = [r for r in rows if r["imd3_db"] < -40]
        avg = fit[:2]
        a = np.asarray([r["ampl_per_tone_v"] for r in rows], float)
        fund = np.asarray([r["fund_v"] for r in rows], float)
        imd3 = np.asarray([r["imd3_db"] for r in rows], float)

        pin = 20.0 * np.log10(a)
        pts += [(f"pin_dbvp_{d}", list(pin)),
                (f"pout_fund_dbvp_{d}", list(20.0 * np.log10(fund))),
                (f"pout_imd3_dbvp_{d}", list(20.0 * np.log10(fund) + imd3)),
                (f"imd3_dbc_{d}", list(imd3)),
                (f"iip3_dbvp_{d}", [r["iip3_dbv"] for r in rows]),
                (f"oip3_dbvp_{d}", [r["oip3_dbv"] for r in rows]),
                (f"in_fit_{d}", [1 if r in fit else 0 for r in rows]),
                (f"in_ip3_avg_{d}", [1 if r in avg else 0 for r in rows])]

        iip3_db = float(np.mean([r["iip3_dbv"] for r in avg]))
        oip3_db = float(np.mean([r["oip3_dbv"] for r in avg]))
        want = ana["iip3"][d]
        assert abs(iip3_db - want["iip3_dbv"]) < 1e-12, f"{d}: IIP3 mismatch"
        assert abs(oip3_db - want["oip3_dbv"]) < 1e-12, f"{d}: OIP3 mismatch"
        print(f"    {d:12s} IIP3 {iip3_db:+.3f} dBVp   OIP3 {oip3_db:+.3f} dBVp")

        # Two straight lines that meet exactly at the intercept: 1:1 through the
        # fundamental, 3:1 through the third-order product.
        x_lo = float(pin.min())
        gain = oip3_db - iip3_db
        lines += [(f"x_dbvp_{d}", [x_lo, iip3_db]),
                  (f"fund_line_dbvp_{d}", [x_lo + gain, oip3_db]),
                  (f"imd3_line_dbvp_{d}", [3.0 * (x_lo - iip3_db) + oip3_db, oip3_db])]

    return [write_csv("iip3_twotone.csv", pts),
            write_csv("iip3_extrapolation.csv", lines)]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    bench = {d: load(f"bench_{d}.json") for d in AC_DUTS}
    lin, hd3f = load("linearity.json"), load("hd3_vs_fin.json")
    ana, tf = load("linearity_analysis.json"), load("tf.json")

    print("cross-checks against the certified data:")
    written = ac_and_group_delay(bench)
    written.append(noise(bench))
    written.append(ac_model(tf))
    written += harmonics(lin, hd3f)
    written += iip3(lin, ana)

    print(f"\nwrote {len(written)} files to {OUT.relative_to(REPO)}/")
    for p in sorted(written):
        print(f"  {p.name:34s} {p.stat().st_size / 1024:6.1f} kB")


if __name__ == "__main__":
    main()
