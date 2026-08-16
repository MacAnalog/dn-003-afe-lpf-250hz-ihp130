#!/usr/bin/env python
"""Figure: mismatch Monte Carlo, pre- vs post-layout, for `H12-pdk-cap`.

The certified sign-off (`signoff/post-pvt/H12-pdk-cap/PRELAYOUT.md`, produced by
`experiments/023-replica-bias/prelayout.py`) reports the MC n=100 campaign only as
summary statistics -- `experiments/023-replica-bias/H12-pdk-cap.json["mc"]` keeps
mean/sigma/min/max and the per-line yields, not the samples. A histogram needs the
samples, so this script RE-RUNS the same campaign (`lab.mc.run`, corner
`mos_tt_mismatch`, seeds 1..100, 27 C, 1.5 V) and keeps every draw:

  * pre-layout  -- the certified sizing from `signoff/post-pvt/H12-pdk-cap/design.json`
  * post-layout -- the same sizing with `Design.dut_override` set to the kpex CC
    subckt `layout/H12-pdk-cap/asbuilt/core_pex.sp` (the it14 layout of record)

Seeds are shared, so the two campaigns see the SAME draws of the random stream and
the comparison is paired, not noisy. The re-run reproduces the certified summary
(that agreement is printed, and is itself the check that the figure is honest).

Run (native ngspice lane, LPF venv; ~2 x 100 ac+noise processes):

    cd <repo>/experiments/023-replica-bias
    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
        ../../.venv/bin/python ../../doc/paper/scripts/fig_mc.py

`--replot` re-draws from the stored samples without touching the simulator.

Outputs (under `doc/paper/figures/`):
    mc_hist.png / .pdf        -- fc, |H|@1 kHz, IRN, dc distributions, pre vs post
    data/mc_samples.json      -- every sample of both campaigns + the yields
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXP = REPO / "experiments/023-replica-bias"
SIZING = REPO / "signoff/post-pvt/H12-pdk-cap/design.json"
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"
CERT = EXP / "H12-pdk-cap.json"          # the certified MC summary, for the cross-check
FIGS = REPO / "doc/paper/figures"

N = 100
PRE = "pre-layout (schematic)"
POST = "post-layout (kpex CC, it14)"
KEYS = ("fc_hz", "a1000_db", "irn_uv", "dc_db", "ph_max_deg", "p_core_nw")


def simulate() -> dict:
    os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
    os.environ.setdefault("PDK", "ihp-sg13g2")
    os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    os.chdir(EXP)

    from common import from_json                       # noqa: E402
    from lab import mc as MC, metrics as M             # noqa: E402

    base = from_json(json.loads(SIZING.read_text())["design"])
    duts = {PRE: ("mcpaper_pre", base),
            POST: ("mcpaper_post", base.with_(dut_override=PEX.read_text()))}

    out: dict = {"n": N, "seed0": 1, "corner": "mos_tt_mismatch", "campaigns": {}}
    for label, (tag, d) in duts.items():
        r = MC.run(d, tag, n=N, seed0=1, record=False)
        rows = [{"seed": s.seed, "usable": s.usable, "ok": s.ok,
                 "violations": s.violations,
                 **{k: (float(s.values[k]) if k in s.values else None) for k in KEYS}}
                for s in r.samples]
        out["campaigns"][label] = {
            "tag": tag,
            "wall_s": r.wall_s,
            "n": r.n, "n_pass": r.n_pass, "n_failed": r.n_failed,
            "all_pass_yield": r.all_pass_yield,
            "line_yield": {k: r.line_yield(k) for k in M.SPEC},
            "stats": {k: {kk: float(vv) for kk, vv in r.stats(k).items()
                          if isinstance(vv, (int, float))} for k in KEYS
                      if k in ("fc_hz", "irn_uv", "dc_db", "p_core_nw")},
            "rows": rows,
        }
        print(f"{label}: {r.n_pass}/{r.n} all-pass ({100*r.all_pass_yield:.1f} %), "
              f"{r.n_failed} non-usable, wall {r.wall_s:.0f} s")

    # -- cross-check the pre-layout re-run against the CERTIFIED summary ------
    cert = json.loads(CERT.read_text())["mc"]
    got = out["campaigns"][PRE]
    print("\ncross-check vs certified summary (experiments/023-replica-bias/H12-pdk-cap.json):")
    print(f"  all-pass yield  certified {cert['all_pass_yield']:.2f}   re-run {got['all_pass_yield']:.2f}")
    for k in ("fc_hz", "irn_uv", "p_core_nw", "dc_db"):
        print(f"  {k:11s} mean  certified {cert[k+'_mean']:.5f}   re-run {got['stats'][k]['mean']:.5f}"
              f"   sigma {cert[k+'_sigma']:.5f} / {got['stats'][k]['sigma']:.5f}")
    out["certified_summary"] = cert

    FIGS.mkdir(parents=True, exist_ok=True)
    (FIGS / "data").mkdir(exist_ok=True)
    (FIGS / "data" / "mc_samples.json").write_text(json.dumps(out, indent=1))
    return out


def plot(out: dict) -> None:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib.pyplot as plt

    LABEL = {PRE: "pre-layout (schematic)", POST: "post-layout, round 4 (it14)"}
    panels = (
        ("fc_hz", "cutoff  (Hz)", (245.0, 255.0), "in band 245–255 Hz"),
        ("a1000_db", "$|H|$ at 1 kHz  (dB)", (None, -48.0), "stopband $\\leq-48$ dB"),
        ("irn_uv", "input-referred noise, 0.5–200 Hz  (µVrms)", (None, 40.0),
         "noise $<40$ µVrms"),
        ("dc_db", "passband gain  (dB)", (-0.2, 0.2), "$|$gain$|\\leq0.2$ dB"),
    )
    face = {PRE: "#1f4e9c", POST: "#c0392b"}
    hatch = {PRE: None, POST: "///"}

    fig = plt.figure(figsize=(S.WIDE, 4.9))
    axes = fig.subplots(2, 2)

    for ax, (key, xlabel, lim, limlab) in zip(axes.ravel(), panels):
        data = {lab: np.array([r[key] for r in out["campaigns"][lab]["rows"]
                               if r["usable"] and r[key] is not None])
                for lab in (PRE, POST)}
        allx = np.concatenate(list(data.values()))
        bins = np.linspace(allx.min(), allx.max(), 20)
        miss = {}
        for lab in (PRE, POST):
            miss[lab] = int(sum(1 for v in data[lab]
                                if (lim[0] is not None and v < lim[0])
                                or (lim[1] is not None and v > lim[1])))
            ax.hist(data[lab], bins=bins, histtype="stepfilled", alpha=0.42,
                    color=face[lab], edgecolor=face[lab], lw=1.0, hatch=hatch[lab],
                    label=f"{LABEL[lab]}: mean {data[lab].mean():.4g}, "
                          f"{miss[lab]} out of box")
        for v in lim:
            if v is not None and allx.min() <= v <= allx.max():
                ax.axvline(v, color="k", ls=(0, (4, 2)), lw=1.1)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.42)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("samples")
        ax.locator_params(axis="x", nbins=5)
        ax.set_title(f"spec: {limlab}")
        ax.legend(loc="upper left", fontsize=6.2)

    pre, post = out["campaigns"][PRE], out["campaigns"][POST]
    fig.suptitle("Mismatch Monte Carlo, 100 paired draws (same seeds), typical process "
                 "+ mismatch, 27 $^\\circ$C, 1.5 V\n"
                 f"every-spec-passing yield {100 * pre['all_pass_yield']:.0f} % before "
                 f"layout, {100 * post['all_pass_yield']:.0f} % after — "
                 "cutoff is the only binding line")
    S.save(fig, "mc_hist")


def main() -> int:
    if "--replot" in sys.argv:
        out = json.loads((FIGS / "data" / "mc_samples.json").read_text())
    else:
        out = simulate()
    plot(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
