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
  * columns are numeric except the corner label in the PVT files, which Veusz
    imports as a text dataset and is what you label points with;
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
                       else x if isinstance(x, str) else FMT % x)
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


# ---- PVT, mismatch, rejection, corners --------------------------------------------

def _corner_cols(rows: list[dict]) -> list[tuple[str, list]]:
    """The axis columns every corner file repeats: what point of the window this is."""
    return [("corner", [r["slug"] for r in rows]),
            ("process", [r["corner"]["process"] for r in rows]),
            ("temp_c", [r["corner"]["temp"] for r in rows]),
            ("vdd_v", [r["corner"]["vdd"] for r in rows])]


def _pair_cols(rows: list[dict], sfx: str = "") -> list[tuple[str, list]]:
    """The two complex pole pairs, ordered low-Q first -- blank where a pair is absent.

    A corner that has lost a pair is the finding, so its row stays in the file with
    empty cells rather than being dropped: a reader plotting Q against temperature must
    be able to see the gap.
    """
    def at(r, i, k):
        return r["pairs"][i][k] if len(r["pairs"]) > i else None
    return [(f"f0_loq_hz{sfx}", [at(r, 0, "f0_hz") for r in rows]),
            (f"q_lo{sfx}", [at(r, 0, "Q") for r in rows]),
            (f"f0_hiq_hz{sfx}", [at(r, 1, "f0_hz") for r in rows]),
            (f"q_hi{sfx}", [at(r, 1, "Q") for r in rows]),
            (f"n_complex_pairs{sfx}", [len(r["pairs"]) for r in rows])]


def _sc_cols(rows: list[dict], sfx: str = "") -> list[tuple[str, list]]:
    return [(f"fc_hz{sfx}", [r["scorecard"].get("fc_hz") for r in rows]),
            (f"ph_max_deg{sfx}", [r["scorecard"].get("ph_max_deg") for r in rows]),
            (f"irn_uv{sfx}", [r["scorecard"].get("irn_uv") for r in rows])]


def pvt(pv: dict) -> list[Path]:
    """The certified axes (pre- and post-layout side by side) and the cross-product box."""
    ax = pv["cert-axes"]["rows"]
    post = {r["slug"]: r for r in pv["cert-axes:post_lumped"]["rows"]}
    order = [post[r["slug"]] for r in ax]
    assert [r["slug"] for r in order] == [r["slug"] for r in ax], "corner order differs"
    a = write_csv("pvt_certified_axes.csv",
                  _corner_cols(ax) + _sc_cols(ax, "_pre") + _pair_cols(ax, "_pre")
                  + _sc_cols(order, "_post") + _pair_cols(order, "_post"))

    box = pv["cert-box"]["rows"]
    b = write_csv("pvt_cert_box.csv",
                  _corner_cols(box) + _sc_cols(box) + _pair_cols(box))
    lost = sum(1 for r in box if len(r["pairs"]) < 2)
    assert lost == len(box) - pv["cert-box"]["summary"]["n_two_pair"], "box census differs"
    print(f"  pvt: {len(ax)} certified axes (pre + post), {len(box)} box points, "
          f"{lost} of them short of two complex pairs")
    return [a, b]


def monte_carlo(pv: dict) -> Path:
    """One row per mismatch draw -- the samples, not their moments."""
    rows = pv["mismatch"]["rows"]
    s = pv["mismatch"]["summary"]
    path = write_csv("mc_draws.csv",
                     [("seed", [r["seed"] for r in rows])]
                     + _sc_cols(rows) + _pair_cols(rows)
                     + [("offset_out_uv", [r["offset_out_uv"] for r in rows])])
    fc = np.asarray([r["scorecard"]["fc_hz"] for r in rows], float)
    assert abs(float(fc.std(ddof=1)) - s["fc_hz"]["sigma"]) < 1e-9, "sigma(fc) differs"
    print(f"  mc: {len(rows)} draws, sigma(fc) {s['fc_hz']['sigma']:.4f} Hz reproduced "
          f"from the exported column")
    return path


def rejection(rj: dict) -> list[Path]:
    """The measured rejection sweeps, not just the four spot frequencies.

    Four interpolated points joined by a line would draw a shape between them that was
    never measured, so the sweep the simulator produced is what gets exported and what
    the figure plots.  The spot values the tables quote are asserted against it.
    """
    spots = [f"{x:g}" for x in rj["spots_hz"]]
    cs = rj["corners"]
    nom = cs["tt_27c_1v500"]
    f = np.asarray(nom["curves"]["f"], float)
    cols: list[tuple[str, list]] = [("freq_hz", f.tolist())]
    for k in ("a_dm_db", "cmrr_db", "psrr_db", "cm_to_cm_db", "supply_to_cm_db"):
        env = np.array([c["curves"][k] for c in cs.values()], float)
        cols.append((k, nom["curves"][k]))
        # The envelope over the nine certified points, so a reader can draw the band
        # without importing nine more columns.
        cols.append((f"{k}_min", env.min(0).tolist()))
        cols.append((f"{k}_max", env.max(0).tolist()))
        for sp in spots:
            got = float(np.interp(np.log10(float(sp)), np.log10(f), nom["curves"][k]))
            assert abs(got - nom[k][sp]) < 1e-9, f"{k} at {sp} Hz differs from the table"
    a = write_csv("rejection_nominal.csv", cols)

    mc = rj["mismatch"]["curves"]
    fm = np.asarray(mc["f"], float)
    cols = [("freq_hz", fm.tolist())]
    for k in ("cmrr_db", "psrr_db"):
        v = np.asarray(mc[k], float)
        cols += [(f"{k}_mean", v.mean(0).tolist()), (f"{k}_min", v.min(0).tolist()),
                 (f"{k}_max", v.max(0).tolist())]
    b = write_csv("rejection_mismatch_curves.csv", cols)

    draws = rj["mismatch"]["draws"]
    keys = [k for k in draws[0] if k != "seed"]
    c = write_csv("rejection_mismatch_draws.csv",
                  [("seed", [d["seed"] for d in draws])]
                  + [(k.replace(".", "p"), [d[k] for d in draws]) for k in keys])
    got = float(np.std([d["offset_in_uv"] for d in draws], ddof=1))
    assert abs(got - rj["mismatch"]["offset_in_uv"]["sigma"]) < 1e-9, "sigma(offset) differs"
    print(f"  rejection: {len(f)}-point sweep, nominal + 9-corner envelope; "
          f"{len(draws)} mismatch draws and their {len(fm)}-point band")
    return [a, b, c]


def iip3_corners(ic: dict) -> Path:
    """One row per corner, with both drive levels, the measured slope and the trust flag."""
    rows = list(ic["corners"].values())
    slugs = list(ic["corners"])
    amps = ic["ampls_v"]

    def at(r, a, k):
        return next((p[k] for p in r["points"]
                     if abs(p["ampl_per_tone_v"] - a) < 1e-12), None)
    cols = [("corner", slugs),
            ("process", [r["corner"]["process"] for r in rows]),
            ("temp_c", [r["corner"]["temp"] for r in rows]),
            ("vdd_v", [r["corner"]["vdd"] for r in rows]),
            ("fc_hz", [r["fc_hz"] for r in rows])]
    for a in amps:
        tag = f"{a * 1e3:.4f}".rstrip("0").rstrip(".").replace(".", "p")
        cols.append((f"imd3_db_a{tag}mv", [at(r, a, "imd3_db") for r in rows]))
        cols.append((f"iip3_dbv_a{tag}mv", [at(r, a, "iip3_dbv") for r in rows]))
    cols += [("imd3_slope_db_per_decade",
              [r.get("imd3_slope_db_per_decade") for r in rows]),
             ("iip3_dbv", [r.get("iip3_dbv") for r in rows]),
             ("oip3_dbv", [r.get("oip3_dbv") for r in rows]),
             # Carried with the data for the same reason the two-tone file carries its
             # fit flags: the published span is over TRUSTED rows only, and a bare
             # column invites a span that disagrees with the pack.
             ("trusted", [1 if r.get("trusted") else 0 for r in rows])]
    path = write_csv("iip3_corners.csv", cols)
    v = [r["iip3_dbv"] for r in rows if r.get("trusted")]
    assert [min(v), max(v)] == ic["iip3_dbv_span"], "IIP3 span differs"
    print(f"  iip3 corners: {len(rows)} rows, span {min(v):+.3f} .. {max(v):+.3f} dBVp "
          f"over {len(v)} trusted")
    return path


def thd_corners(tc: dict) -> Path:
    """The amplitude ladder, one column per corner -- the shape a THD-vs-drive plot wants."""
    slugs = list(tc["corners"])
    vpp = tc["vpp_diff"]
    cols: list[tuple[str, list]] = [("vpp_diff_v", list(vpp))]

    def series(slug, k):
        pts = {p["vpp_diff"]: p[k] for p in tc["corners"][slug]["points"]}
        return [pts.get(v) for v in vpp]
    for k, short in (("thd_db", "thd_db"), ("hd3_db", "hd3_db"), ("hd2_db", "hd2_db")):
        for slug in slugs:
            cols.append((f"{short}_{slug}", series(slug, k)))
    path = write_csv("thd_corners.csv", cols)
    spec = [tc["corners"][s]["thd_db_at_spec"] for s in slugs]
    assert [min(spec), max(spec)] == tc["thd_db_at_spec_span"], "THD span differs"
    print(f"  thd corners: {len(vpp)} amplitudes x {len(slugs)} corners, at the "
          f"{tc['spec_vpp'] * 1e3:g} mVpp point {min(spec):.3f} .. {max(spec):.3f} dB")
    return path


def gds_residual(gr: dict) -> Path:
    """The residual, both g_ds predictions, and the fit-window band the cubic implies."""
    rows = gr["rows"]
    wins = sorted(rows[0]["v3_by_window_uv"], key=float)
    path = write_csv("gds_residual.csv", [
        ("fin_hz", [r["fin"] for r in rows]),
        ("v3_measured_uv", [r["v3_measured_uv"] for r in rows]),
        ("v3_gate_model_uv", [r["v3_gate_model_uv"] for r in rows]),
        ("v3_unexplained_uv", [r["v3_unexplained_uv"] for r in rows]),
        ("v3_gds_cubic_uv", [r["v3_gds_pred_uv"] for r in rows]),
        # The cubic's window band travels WITH the cubic column, because the point of
        # section 10.1 is that the single number was never the whole statement.
        ("v3_gds_cubic_win_lo_uv",
         [min(r["v3_by_window_uv"][w] for w in wins) for r in rows]),
        ("v3_gds_cubic_win_hi_uv",
         [max(r["v3_by_window_uv"][w] for w in wins) for r in rows]),
        ("v3_gds_exact_uv", [r["v3_gds_exact_uv"] for r in rows]),
    ])
    lo = [r for r in rows if r["fin"] <= gr["flat_band_hz"]]
    ex = [r["v3_gds_exact_uv"] for r in lo]
    assert [min(ex), max(ex)] == gr["refinement"]["pred_band_uv"], "exact band differs"
    print(f"  gds residual: {len(rows)} frequencies, window-free prediction "
          f"{min(ex):.4f} .. {max(ex):.4f} uV below {gr['flat_band_hz']:g} Hz")
    return path


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
    written += pvt(load("pvt.json"))
    written.append(monte_carlo(load("pvt.json")))
    written += rejection(load("psrr_cmrr.json"))
    written.append(iip3_corners(load("iip3_corners.json")))
    written.append(thd_corners(load("thd_corners.json")))
    written.append(gds_residual(load("gds_residual.json")))

    print(f"\nwrote {len(written)} files to {OUT.relative_to(REPO)}/")
    for p in sorted(written):
        print(f"  {p.name:34s} {p.stat().st_size / 1024:6.1f} kB")


if __name__ == "__main__":
    main()
