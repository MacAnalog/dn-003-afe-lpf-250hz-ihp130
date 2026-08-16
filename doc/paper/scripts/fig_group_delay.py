#!/usr/bin/env python
"""Figure + tables: group delay tau(f) = -d(phase)/d(omega) of the 250 Hz LPF.

Group delay is report-only in this repo (no S-line scores it; `lab.metrics`
carries `gd_dc_ms` / `gd_max_ms` / `gd_fc_ms` as soft columns). This script
runs the cell's OWN frozen ac bench (`lab.deck.ac_noise` -> `lab.ngspice.run`)
at 100 points/decade so the derivative is smooth, and reports tau(f) for

  * the certified reference baseline (`decks/reference/design.json`),
  * pre-layout `H12-pdk-cap` (`signoff/post-pvt/H12-pdk-cap/design.json`),
  * post-layout it14 (`Design.dut_override` = `layout/H12-pdk-cap/asbuilt/core_pex.sp`),

at nominal (`mos_tt`, 27 C, 1.5 V), then pre vs post over the one-axis corner
set (`lab.corners.AXES`, temperature rows with `LPF_BIAS_ALPHA = 1.1` like
`PRELAYOUT.md`), the MIM corners (`cap_bcs` x0.9 / `cap_wcs` x1.1) and the
accepted-miss corner (`cap_bcs` + `iref` x0.9), and a paired 100-seed mismatch
Monte Carlo (`lab.mc.run`, `mos_tt_mismatch`, seeds 1..100) for tau statistics.

tau is computed on the same contiguous scored band as the phase certificate
(`lab.raw.group_delay_s`: stops where |H| falls below -100 dB) — beyond that
the sampled phase aliases and its derivative is fiction. Reported numbers:

    tau_dc        tau at the first sweep point (0.1 Hz)
    tau_pk, f_pk  peak tau in the passband (f <= 1.2 fc) and where it sits
    tau_fc        tau at the measured -3 dB frequency
    tau_100/200   tau at 100 Hz and 200 Hz (upper passband)
    dtau_pb       passband delay ripple: max - min over 0.5 .. 200 Hz (the IRN band)
    tau_dc*fc     dimensionless dc delay; a 4th-order Butterworth has tau(0)*omega_c = 2.613,
                  i.e. tau_dc*fc = 0.416 -- the sanity anchor for every row below

Run (native ngspice lane, LPF venv):

    cd <repo>/experiments/023-replica-bias
    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
        ../../.venv/bin/python ../../doc/paper/scripts/fig_group_delay.py [--no-mc]

`--replot` re-draws + re-tabulates from the stored curves without simulating.

Outputs (under `doc/paper/figures/`):
    group_delay.png / .pdf            -- (a) tau(f) nominal x3, (b) post-pre delta,
                                         (c) tau(f) over corners, (d) MC spread
    data/group_delay.json             -- every curve + scorecard + MC rows
    ../results_group_delay.md tables  -- printed to stdout as markdown
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXP = REPO / "experiments/023-replica-bias"
SIZING = REPO / "signoff/post-pvt/H12-pdk-cap/design.json"
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"
FIGS = REPO / "doc/paper/figures"
DATA = FIGS / "data" / "group_delay.json"

REF = "reference baseline"
PRE = "pre-layout (schematic)"
POST = "post-layout it14 (kpex CC)"
ORDER = (REF, PRE, POST)
DEC = 100                    # points per decade for the tau curves
IRN_BAND = (0.5, 200.0)      # the noise band == the passband we quote ripple over


# ---------------------------------------------------------------- simulate --
def _env() -> None:
    os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
    os.environ.setdefault("PDK", "ihp-sg13g2")
    os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))
    os.environ.setdefault("LPF_BIAS_ALPHA", "1.1")   # read at lab.config import time
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    os.chdir(EXP)


def _curve(plots, d):
    """(f, mag_db, phase_deg, f_gd, tau_s, scorecard) from one ac+noise run."""
    import numpy as np
    from lab import metrics as M, raw as R

    ac = R.pick(plots, "ac")
    f, h = R.diff_tf(ac, "voutp", "voutn")
    mag = R.db_rel_dc(h)
    ph = np.unwrap(np.angle(h)) * 180.0 / np.pi
    ph -= ph[0]
    fg, gd = R.group_delay_s(f, h, M.PH_FLOOR_DB)
    s = M.score_plots(plots, d)
    sc = {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in s.values.items()}
    return {"f_hz": f.tolist(), "mag_db": mag.tolist(), "phase_deg": ph.tolist(),
            "f_gd_hz": fg.tolist(), "tau_s": gd.tolist(),
            "scorecard": sc, "violations": list(s.violations)}


def simulate(mc: bool = True) -> dict:
    _env()
    from common import from_json                                       # noqa: E402
    from lab import config as C, corners as K, deck as D, mc as MC, ngspice as ng  # noqa: E402
    from lab.parallel import batch                                     # noqa: E402
    from scripts.baseline import load_design                           # noqa: E402

    ref = load_design()
    pre = from_json(json.loads(SIZING.read_text())["design"])
    post = pre.with_(dut_override=PEX.read_text())
    duts = {REF: ref, PRE: pre, POST: post}
    short = {REF: "ref", PRE: "pre", POST: "post14"}

    # -- job list: (key, dut label, corner label, deck) — decks built serially,
    #    because the MIM corner is a module attribute read at deck-build time.
    jobs: list[tuple[str, str, str, str]] = []
    for lab_, d in duts.items():
        jobs.append(("nominal", lab_, "mos_tt 27C 1.50V",
                     D.ac_noise(d, dec=DEC)))
    for lab_ in (PRE, POST):
        d = duts[lab_]
        for c in K.AXES[1:]:
            jobs.append(("axes", lab_, f"{c.process} {c.temp:+.0f}C {c.vdd:.2f}V",
                         D.ac_noise(d, corner=c.process, temp=c.temp, vdd=c.vdd, dec=DEC)))
        for cap in ("cap_bcs", "cap_wcs"):
            C.CAP_CORNER = cap
            jobs.append(("cap", lab_, f"{cap} x{0.9 if cap == 'cap_bcs' else 1.1}",
                         D.ac_noise(d, dec=DEC)))
        C.CAP_CORNER = "cap_bcs"
        jobs.append(("cap", lab_, "cap_bcs x0.9 + iref x0.9",
                     D.ac_noise(d.with_(iref=d.iref * 0.9), dec=DEC)))
        C.CAP_CORNER = "cap_typ"

    def one(job):
        key, lab_, cname, deck = job
        tag = "paper_gd_" + short[lab_] + "_" + "".join(
            ch if ch.isalnum() else "_" for ch in (key + "_" + cname))
        d = duts[lab_]
        return _curve(ng.plots(ng.run(deck, tag)), d)

    print(f"running {len(jobs)} ac decks ...", flush=True)
    res = batch(jobs, one, workers=max(2, min(8, os.cpu_count() or 2)), on_error="keep")

    out: dict = {"dec": DEC, "irn_band_hz": IRN_BAND, "nominal": {}, "corners": {PRE: {}, POST: {}}}
    for (key, lab_, cname, _), r in zip(jobs, res):
        if isinstance(r, Exception):
            print(f"  FAILED {lab_} / {cname}: {r!r}")
            continue
        if key == "nominal":
            out["nominal"][lab_] = r
        else:
            out["corners"][lab_][cname] = r
        sc = r["scorecard"]
        print(f"  {lab_:<26} {cname:<26} fc {sc['fc_hz']:8.3f}  ph_max {sc['ph_max_deg']:8.3f}  "
              f"tau_dc {sc.get('gd_dc_ms', float('nan')):.4f} ms  tau_max {sc.get('gd_max_ms', float('nan')):.4f} ms")

    if mc:
        out["mc"] = {}
        for lab_ in (PRE, POST):
            r = MC.run(duts[lab_], f"paper_gd_mc_{short[lab_]}", n=100, seed0=1, record=False)
            rows = []
            for s in r.samples:
                v = s.score.values if s.score is not None else {}
                rows.append({"seed": int(v.get("seed", -1)), "usable": bool(s.usable),
                             **{k: float(v[k]) for k in ("fc_hz", "gd_dc_ms", "gd_max_ms", "gd_fc_ms")
                                if k in v}})
            out["mc"][lab_] = {"n": r.n, "rows": rows}
            print(f"  MC {lab_}: {r.n} draws, {sum(x['usable'] for x in rows)} usable")

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(out, indent=1))
    return out


# ------------------------------------------------------------------ stats --
def stats(c: dict) -> dict:
    """The tau numbers quoted in the tables, from one stored curve."""
    import numpy as np

    f = np.asarray(c["f_gd_hz"]); tau = np.asarray(c["tau_s"]) * 1e3   # ms
    fc = float(c["scorecard"]["fc_hz"])
    pb = f <= 1.2 * fc
    ipk = int(np.argmax(np.where(pb, tau, -np.inf)))
    band = (f >= IRN_BAND[0]) & (f <= IRN_BAND[1])
    at = lambda x: float(np.interp(x, f, tau))                          # noqa: E731
    return {"fc_hz": fc,
            "tau_dc_ms": float(tau[0]),
            "tau_pk_ms": float(tau[ipk]), "f_pk_hz": float(f[ipk]),
            "tau_fc_ms": at(fc), "tau_100_ms": at(100.0), "tau_200_ms": at(200.0),
            "dtau_pb_ms": float(tau[band].max() - tau[band].min()) if band.any() else float("nan"),
            "tau_dc_x_fc": float(tau[0] * 1e-3 * fc),
            "ph_max_deg": float(c["scorecard"]["ph_max_deg"])}


def _fmt(x, nd=3):
    return "—" if x != x else f"{x:.{nd}f}"


def tables(out: dict) -> str:
    import numpy as np
    L: list[str] = []
    L.append("### Nominal group delay (`mos_tt`, 27 °C, 1.5 V; 100 pts/decade)\n")
    L.append("| DUT | `fc` (Hz) | τ(0.1 Hz) (ms) | τ peak (ms) @ f (Hz) | τ(fc) (ms) | τ(100 Hz) | τ(200 Hz) | Δτ 0.5–200 Hz (ms) | τ_dc·fc | `ph_max` (°) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    S = {k: stats(v) for k, v in out["nominal"].items()}
    for k in ORDER:
        if k not in S:
            continue
        s = S[k]
        L.append(f"| {k} | {s['fc_hz']:.2f} | {s['tau_dc_ms']:.3f} | {s['tau_pk_ms']:.3f} @ {s['f_pk_hz']:.0f} | "
                 f"{s['tau_fc_ms']:.3f} | {s['tau_100_ms']:.3f} | {s['tau_200_ms']:.3f} | {s['dtau_pb_ms']:.3f} | "
                 f"{s['tau_dc_x_fc']:.3f} | {s['ph_max_deg']:.2f} |")
    if PRE in S and POST in S:
        a, b = S[PRE], S[POST]
        L.append(f"| **post − pre (it14)** | {b['fc_hz']-a['fc_hz']:+.2f} | {b['tau_dc_ms']-a['tau_dc_ms']:+.4f} | "
                 f"{b['tau_pk_ms']-a['tau_pk_ms']:+.4f} | {b['tau_fc_ms']-a['tau_fc_ms']:+.4f} | "
                 f"{b['tau_100_ms']-a['tau_100_ms']:+.4f} | {b['tau_200_ms']-a['tau_200_ms']:+.4f} | "
                 f"{b['dtau_pb_ms']-a['dtau_pb_ms']:+.4f} | {b['tau_dc_x_fc']-a['tau_dc_x_fc']:+.4f} | "
                 f"{b['ph_max_deg']-a['ph_max_deg']:+.3f} |")
    L.append("")
    L.append("### Group delay over corners — pre-layout vs post-layout it14\n")
    L.append("Temperature rows use the α = 1.1 bias law (as `PRELAYOUT.md`); MIM rows use `cornerCAP.lib` sections.\n")
    L.append("| corner | `fc` pre → post (Hz) | τ(0.1 Hz) pre → post (ms) | τ peak pre → post (ms) | τ(fc) pre → post (ms) | Δτ 0.5–200 Hz pre → post (ms) | S1 pre / post |")
    L.append("|---|---|---|---|---|---|---|")
    names = list(out["corners"][PRE])
    nomS = {k: stats(out["nominal"][k]) for k in (PRE, POST) if k in out["nominal"]}
    rows = [("mos_tt 27C 1.50V (nominal)", nomS.get(PRE), nomS.get(POST))]
    for n in names:
        rows.append((n, stats(out["corners"][PRE][n]) if n in out["corners"][PRE] else None,
                     stats(out["corners"][POST][n]) if n in out["corners"][POST] else None))
    for n, a, b in rows:
        if a is None or b is None:
            L.append(f"| {n} | — | — | — | — | — | — |"); continue
        ok = lambda s: "PASS" if s["ph_max_deg"] >= 330.0 else "FAIL"          # noqa: E731
        L.append(f"| {n} | {a['fc_hz']:.1f} → {b['fc_hz']:.1f} | {a['tau_dc_ms']:.3f} → {b['tau_dc_ms']:.3f} | "
                 f"{a['tau_pk_ms']:.3f} → {b['tau_pk_ms']:.3f} | {a['tau_fc_ms']:.3f} → {b['tau_fc_ms']:.3f} | "
                 f"{a['dtau_pb_ms']:.3f} → {b['dtau_pb_ms']:.3f} | {ok(a)} / {ok(b)} |")
    L.append("")
    if out.get("mc"):
        L.append("### Mismatch Monte Carlo, n = 100 paired seeds (`mos_tt_mismatch`, 27 °C, 1.5 V; 50 pts/decade scorecard columns)\n")
        L.append("| DUT | usable | τ(0.1 Hz) mean ± σ (ms) | min / max | τ peak mean ± σ (ms) | min / max | τ(fc) mean ± σ (ms) | `fc` mean ± σ (Hz) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for k in (PRE, POST):
            m = out["mc"].get(k)
            if not m:
                continue
            rows_ = [r for r in m["rows"] if r.get("usable") and "gd_dc_ms" in r]
            g = lambda key: np.array([r[key] for r in rows_])                     # noqa: E731
            dc, pk, fcv, fcz = g("gd_dc_ms"), g("gd_max_ms"), g("gd_fc_ms"), g("fc_hz")
            L.append(f"| {k} | {len(rows_)}/{m['n']} | {dc.mean():.3f} ± {dc.std(ddof=1):.3f} | {dc.min():.3f} / {dc.max():.3f} | "
                     f"{pk.mean():.3f} ± {pk.std(ddof=1):.3f} | {pk.min():.3f} / {pk.max():.3f} | "
                     f"{fcv.mean():.3f} ± {fcv.std(ddof=1):.3f} | {fcz.mean():.2f} ± {fcz.std(ddof=1):.2f} |")
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------- plot --
def plot(out: dict) -> None:
    import numpy as np
    import _style as S
    S.use()
    import matplotlib.pyplot as plt

    nom = out["nominal"]
    style = {REF: dict(color=S.GREY, lw=1.3, ls=(0, (2, 1.5))),
             PRE: dict(color="#1f4e9c", lw=2.0, ls="-"),
             POST: dict(color="#c0392b", lw=1.4, ls=(0, (5, 2)))}
    label = {REF: "reference baseline (certified, 50.18 µV IRN)",
             PRE: "H12-pdk-cap pre-layout (schematic)",
             POST: "H12-pdk-cap post-layout, round 4 (it14)"}
    S_ = {k: stats(v) for k, v in nom.items()}
    has_mc = bool(out.get("mc"))

    rows = 4 if has_mc else 3
    fig = plt.figure(figsize=(S.WIDE, 9.6 if has_mc else 7.4))
    gs = fig.add_gridspec(rows, 1, height_ratios=[1.45, 0.7, 1.05, 0.9][:rows])
    a1 = fig.add_subplot(gs[0]); a2 = fig.add_subplot(gs[1], sharex=a1)
    a3 = fig.add_subplot(gs[2]); a4 = fig.add_subplot(gs[3]) if has_mc else None
    fig.suptitle("Group delay τ(f) = −dφ/dω of the 250 Hz low-pass filter (cell lpf_core, "
                 "differential output)")

    # (a) nominal tau(f)
    for k in ORDER:
        if k not in nom:
            continue
        f = np.asarray(nom[k]["f_gd_hz"]); t = np.asarray(nom[k]["tau_s"]) * 1e3
        s = S_[k]
        a1.semilogx(f, t, label=f"{label[k]} — τ(0.1 Hz) {s['tau_dc_ms']:.2f} ms, "
                    f"peak {s['tau_pk_ms']:.2f} ms at {s['f_pk_hz']:.0f} Hz", **style[k])
        a1.plot([s['f_pk_hz']], [s['tau_pk_ms']], marker="v", ms=5, color=style[k]["color"], zorder=6)
    for k in (PRE,):
        if k in S_:
            a1.axvline(S_[k]["fc_hz"], color=S.GREY, lw=0.7, ls=(0, (4, 3)))
            a1.annotate(f"−3 dB cutoff {S_[k]['fc_hz']:.1f} Hz", (S_[k]["fc_hz"] * 1.08, 1.25),
                        fontsize=6.8, color=S.GREY)
    a1.axvspan(*IRN_BAND, color="#1b7837", alpha=0.06, lw=0)
    a1.annotate("passband 0.5–200 Hz (the noise band)", (0.55, 0.06), fontsize=6.8, color=S.OK)
    a1.set_xlim(0.1, 3e3); a1.set_ylim(0, 2.9)
    a1.set_ylabel("group delay τ (ms)")
    a1.set_title("(a) typical process, 27 °C, 1.5 V — flat below ≈ 30 Hz, peaks just below the cutoff,\n"
                 "     then falls through the stopband (curves stop where |H| reaches the −100 dB floor)")
    a1.legend(loc="lower left", bbox_to_anchor=(0.005, 0.07))
    if REF in S_ and PRE in S_:
        S.note(a1, f"passband delay ripple, 0.5–200 Hz:\n"
                   f"  reference {S_[REF]['dtau_pb_ms']:.2f} ms · pre-layout {S_[PRE]['dtau_pb_ms']:.2f} ms · "
                   f"post-layout {S_[POST]['dtau_pb_ms']:.2f} ms\n"
                   f"τ(0.1 Hz)·fc: reference {S_[REF]['tau_dc_x_fc']:.3f} · "
                   f"pre {S_[PRE]['tau_dc_x_fc']:.3f} · post {S_[POST]['tau_dc_x_fc']:.3f}\n"
                   f"(a 4th-order Butterworth gives 0.416)",
               loc="upper left")

    # (b) post - pre
    if PRE in nom and POST in nom:
        fa = np.asarray(nom[PRE]["f_gd_hz"]); ta = np.asarray(nom[PRE]["tau_s"]) * 1e6
        fb = np.asarray(nom[POST]["f_gd_hz"]); tb = np.asarray(nom[POST]["tau_s"]) * 1e6
        n = min(len(fa), len(fb))
        a2.semilogx(fa[:n], tb[:n] - ta[:n], color="#c0392b", lw=1.5)
        a2.axhline(0, color=S.GREY, lw=0.7)
        a2.set_ylabel("Δτ post − pre (µs)")
        d = S_[POST]["tau_dc_ms"] - S_[PRE]["tau_dc_ms"]
        dp = S_[POST]["tau_pk_ms"] - S_[PRE]["tau_pk_ms"]
        a2.set_title(f"(b) post − pre-layout: parasitics add {d*1e3:+.1f} µs at 0.1 Hz "
                     f"({d/S_[PRE]['tau_dc_ms']*100:+.2f} %) and {dp*1e3:+.1f} µs at the peak "
                     f"({dp/S_[PRE]['tau_pk_ms']*100:+.2f} %);\n     the S-shape around the cutoff is the "
                     f"delay signature of the {S_[PRE]['fc_hz']-S_[POST]['fc_hz']:.2f} Hz cutoff shift"
                     )
        a2.set_xlabel("frequency (Hz)")

    # (c) corners
    corner_style = [dict(color="#1f4e9c"), dict(color="#e08214"), dict(color="#6a3d9a"),
                    dict(color="#1b7837"), dict(color="#c0392b"), dict(color="#8c564b"),
                    dict(color="#17becf"), dict(color="#7f7f7f"), dict(color="#bcbd22"),
                    dict(color="#e377c2"), dict(color="#000000")]
    names = list(out["corners"][PRE])
    for i, n_ in enumerate(names):
        st = corner_style[i % len(corner_style)]
        pa = out["corners"][PRE].get(n_); pb = out["corners"][POST].get(n_)
        if pa:
            a3.semilogx(np.asarray(pa["f_gd_hz"]), np.asarray(pa["tau_s"]) * 1e3, lw=1.1, ls="-",
                        label=_corner_label(n_), **st)
        if pb:
            a3.semilogx(np.asarray(pb["f_gd_hz"]), np.asarray(pb["tau_s"]) * 1e3, lw=1.1, ls=(0, (2, 1.5)), **st)
    if PRE in nom:
        a3.semilogx(np.asarray(nom[PRE]["f_gd_hz"]), np.asarray(nom[PRE]["tau_s"]) * 1e3,
                    color="k", lw=1.6, label="nominal (typical, 27 °C, 1.5 V)")
    a3.set_xlim(0.1, 3e3); a3.set_ylim(0, 3.2)
    a3.set_xlabel("frequency (Hz)"); a3.set_ylabel("group delay τ (ms)")
    a3.set_title("(c) one-axis corners — solid: pre-layout, dashed: post-layout it14 (same colour);\n"
                 "     temperature corners use the α = 1.1 bias law")
    a3.legend(loc="upper left", fontsize=6.3, ncol=3, columnspacing=1.0)

    # (d) MC
    if a4 is not None:
        for k, st in ((PRE, style[PRE]), (POST, style[POST])):
            m = out["mc"].get(k)
            if not m:
                continue
            dc = np.array([r["gd_dc_ms"] for r in m["rows"] if r.get("usable") and "gd_dc_ms" in r])
            pk = np.array([r["gd_max_ms"] for r in m["rows"] if r.get("usable") and "gd_max_ms" in r])
            a4.hist(dc, bins=20, histtype="step", lw=1.4, color=st["color"], ls="-",
                    label=f"{'pre' if k == PRE else 'post'}-layout τ(0.1 Hz): {dc.mean():.3f} ± {dc.std(ddof=1):.3f} ms")
            a4.hist(pk, bins=20, histtype="step", lw=1.4, color=st["color"], ls=(0, (2, 1.5)),
                    label=f"{'pre' if k == PRE else 'post'}-layout τ peak: {pk.mean():.3f} ± {pk.std(ddof=1):.3f} ms")
        a4.set_xlabel("group delay τ (ms)"); a4.set_ylabel("draws")
        a4.set_title("(d) mismatch Monte Carlo, 100 paired seeds, typical process, 27 °C, 1.5 V —\n"
                     "     τ at 0.1 Hz (solid) and at the passband peak (dashed)")
        a4.legend(loc="upper center", fontsize=6.4, ncol=2)

    S.save(fig, "group_delay")


def _corner_label(n: str) -> str:
    n = n.replace("mos_", "").replace("cap_bcs", "MIM −10 %").replace("cap_wcs", "MIM +10 %")
    n = n.replace(" x0.9", "").replace(" x1.1", "").replace("iref x0.9", "bias current −10 %")
    return (n.replace("tt", "typical").replace("ss", "slow-slow").replace("ff", "fast-fast")
             .replace("sf", "slow-n fast-p").replace("fs", "fast-n slow-p")
             .replace("+27C 1.50V", "").replace("+27C", "").replace(" 1.50V", "").strip()) or "typical"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replot", action="store_true")
    ap.add_argument("--no-mc", action="store_true")
    a = ap.parse_args()
    if a.replot:
        out = json.loads(DATA.read_text())
    else:
        out = simulate(mc=not a.no_mc)
    sys.path.insert(0, str(HERE))
    plot(out)
    print()
    print(tables(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
