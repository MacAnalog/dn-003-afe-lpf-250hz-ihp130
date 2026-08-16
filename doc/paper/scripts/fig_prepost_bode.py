#!/usr/bin/env python
"""Figure: pre- vs post-layout |H(f)| and phase for `H12-pdk-cap`.

Runs the cell's OWN frozen ac+noise bench (`lab.deck.ac_noise` -> `lab.ngspice.run`)
three times at `mos_tt`, 27 C, 1.5 V:

  * pre-layout  -- the certified sizing from `signoff/post-pvt/H12-pdk-cap/design.json`
  * post-layout it13 -- the same sizing with `Design.dut_override` set to the
    round-3 kpex CC subckt, read from git at
    `ee6b342:layout/H12-pdk-cap/asbuilt/core_pex.sp`
  * post-layout it14 -- ditto with the current layout of record,
    `layout/H12-pdk-cap/asbuilt/core_pex.sp` (owner-reversed dummy rows +
    campaign knobs)

and plots the differential transfer function of all three, plus the unwrapped phase
whose 4-pole certificate is S1 (`ph_max`). The scorecard of each run is scored
with the same `lab.metrics.score_plots` the sign-off uses, printed, and written
next to the curves so the figure and the tables cannot drift apart.

Run (native ngspice lane, LPF venv):

    cd <repo>/experiments/023-replica-bias
    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
        ../../.venv/bin/python ../../doc/paper/scripts/fig_prepost_bode.py

`--replot` re-draws from the stored curves without touching the simulator.

Outputs (under `doc/paper/figures/`):
    prepost_bode.png / .pdf          -- |H|, phase, and the post-pre delta
    data/prepost_bode.json           -- f, |H| dB, phase deg for all three DUTs + scorecards
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
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"      # the it14 layout of record
PEX_R3 = "ee6b342:layout/H12-pdk-cap/asbuilt/core_pex.sp"  # the round-3 (it13) layout
FIGS = REPO / "doc/paper/figures"


PRE = "pre-layout (schematic)"
POST13 = "post-layout it13 (kpex CC)"
POST = "post-layout it14 (kpex CC)"
ORDER = (PRE, POST13, POST)


def simulate() -> dict[str, dict]:
    os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
    os.environ.setdefault("PDK", "ihp-sg13g2")
    os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    os.chdir(EXP)                      # lab.* resolves decks/models relative to here

    import numpy as np
    from common import from_json                                    # noqa: E402
    from lab import deck as D, metrics as M, ngspice as ng, raw as R  # noqa: E402

    import subprocess
    pex13 = subprocess.run(["git", "-C", str(REPO), "show", PEX_R3],
                           capture_output=True, text=True, check=True).stdout

    base = from_json(json.loads(SIZING.read_text())["design"])
    duts = {PRE: base,
            POST13: base.with_(dut_override=pex13),
            POST: base.with_(dut_override=PEX.read_text())}

    out: dict[str, dict] = {}
    for label, d in duts.items():
        tag = "paper_bode_" + {PRE: "pre", POST13: "post13", POST: "post14"}[label]
        plots = ng.plots(ng.run(D.ac_noise(d), tag))
        ac = R.pick(plots, "ac")
        f, h = R.diff_tf(ac, "voutp", "voutn")
        mag = R.db_rel_dc(h)
        ph = np.unwrap(np.angle(h)) * 180.0 / np.pi
        ph = ph - ph[0]
        s = M.score_plots(plots, d)
        out[label] = {
            "f_hz": f.tolist(),
            "mag_db": mag.tolist(),
            "phase_deg": ph.tolist(),
            "scorecard": {k: (float(v) if isinstance(v, (int, float)) else v)
                          for k, v in s.values.items()},
            "violations": s.violations,
        }
        print(f"{label}: fc {s['fc_hz']:.4f} Hz  ph_max {s['ph_max_deg']:.4f} deg  "
              f"a1000 {s['a1000_db']:.4f} dB  IRN {s['irn_uv']:.4f} uV  "
              f"violations {s.violations}")

    FIGS.mkdir(parents=True, exist_ok=True)
    (FIGS / "data").mkdir(exist_ok=True)
    (FIGS / "data" / "prepost_bode.json").write_text(json.dumps(out, indent=1))
    return out


LABEL = {PRE: "pre-layout (schematic)",
         POST13: "post-layout, round 3 (it13)",
         POST: "post-layout, round 4 (it14)"}


def plot(out: dict[str, dict]) -> None:
    import numpy as np
    import _style as S

    S.use()
    import matplotlib.pyplot as plt

    f = np.asarray(out[PRE]["f_hz"])
    mag = {k: np.asarray(v["mag_db"]) for k, v in out.items()}
    ph = {k: np.asarray(v["phase_deg"]) for k, v in out.items()}
    sc = {k: v["scorecard"] for k, v in out.items()}
    style = {PRE: dict(color="#1f4e9c", lw=2.0, ls="-"),
             POST13: dict(color="#e08214", lw=1.3, ls=(0, (1, 1.6))),
             POST: dict(color="#c0392b", lw=1.3, ls=(0, (5, 2)))}

    # -- notch and floor, measured off the very curves being drawn -----------
    lf = np.log10(f)
    notch, depth = {}, {}
    for k in ORDER:
        i = int(np.argmin(mag[k]))
        c = np.polyfit(lf[i - 1:i + 2], mag[k][i - 1:i + 2], 2)
        notch[k] = 10.0 ** (-c[1] / (2 * c[0]))
        depth[k] = float(np.polyval(c, -c[1] / (2 * c[0])))
    floor = {k: float(np.interp(3e4, f, mag[k])) for k in ORDER}
    step = 100.0 * (f[1] / f[0] - 1.0)

    fig = plt.figure(figsize=(S.WIDE, 6.9))
    a1, a2, a3 = fig.subplots(3, 1, sharex=True,
                              gridspec_kw={"height_ratios": [1.5, 1.05, 0.8]})

    # ---- (a) magnitude, down to the feed-through floor ---------------------
    for k in ORDER:
        a1.semilogx(f, mag[k], label=f"{LABEL[k]} — phase max "
                    f"{sc[k]['ph_max_deg']:.2f}$^\\circ$", **style[k])
    a1.axhline(-48.0, color=S.GREY, lw=0.7, ls=(0, (4, 3)))
    a1.axvline(1e3, color=S.GREY, lw=0.7, ls=(0, (4, 3)))
    a1.set_ylim(-137, 12)
    a1.set_yticks([0, -25, -50, -75, -100, -125])
    a1.set_ylabel("$|H(f)|$   (dB, rel. dc)")
    a1.set_title("(a) differential magnitude — the stopband ends in a transmission "
                 "zero and a feed-through floor")
    a1.legend(loc="lower left")
    a1.annotate("stopband limit:\n$|H|$ at 1 kHz $\\leq-48$ dB", (1.25e3, -45),
                fontsize=6.8, color="0.3", va="bottom")
    # markers instead of leader lines: no text ever crosses a curve
    a1.plot([notch[PRE]], [depth[PRE]], marker="v", ms=5, mfc="none",
            mec="0.25", mew=0.9, ls="none", zorder=6)
    a1.plot([3e4], [floor[PRE]], marker=">", ms=5, mfc="none",
            mec="0.25", mew=0.9, ls="none", zorder=6)
    S.note(a1,
           f"\u25bc  transmission zero at {notch[PRE] / 1e3:.2f} kHz\n"
           f"     depth {depth[PRE]:.1f} dB pre \u2192 {depth[POST]:.1f} dB after layout\n"
           f"     unmoved to within the {step:.1f} % sweep step\n"
           f"\u25b6  feed-through floor at 30 kHz\n"
           f"     {floor[PRE]:.1f} dB pre \u2192 {floor[POST]:.1f} dB after layout "
           f"($+${floor[POST] - floor[PRE]:.2f} dB)",
           loc="upper right", fontsize=6.5)

    # ---- (b) unwrapped phase ----------------------------------------------
    for k in ORDER:
        a2.semilogx(f, ph[k], **style[k])
    a2.axhline(-330.0, color=S.GREY, lw=0.8, ls=(0, (4, 3)))
    a2.set_ylim(-356, 34)
    a2.set_yticks([0, -90, -180, -270, -330])
    a2.set_ylabel("phase   (deg)")
    a2.set_title("(b) unwrapped phase — the two-biquad certificate")
    a2.annotate("phase max $\\geq330^\\circ$ = two true biquads",
                (9.0e4, -310), fontsize=6.8, color="0.3", va="bottom", ha="right")
    S.note(a2, "the return to $0^\\circ$ above the notch is REAL: past the zero\n"
               "the direct feed-through path (follower $C_{gs}/C_{gd}$ plus\n"
               "capacitor feed-forward) dominates the biquads — and it is\n"
               "in phase, so the accumulated lag unwinds",
           loc="center left", fontsize=6.5)

    # ---- (c) post - pre ----------------------------------------------------
    a3.semilogx(f, mag[POST13] - mag[PRE], color="#1b7837", lw=0.9,
                ls=(0, (1, 1.6)), label="$\\Delta|H|$, round 3")
    a3.semilogx(f, mag[POST] - mag[PRE], color="#1b7837", lw=1.5, ls="-",
                label="$\\Delta|H|$, round 4")
    a3.axhline(0.0, color="0.75", lw=0.7)
    a3.set_ylabel("$\\Delta|H|$  (dB)", color="#1b7837")
    a3.tick_params(axis="y", labelcolor="#1b7837")
    a3b = a3.twinx()
    a3b.semilogx(f, ph[POST13] - ph[PRE], color="#6a3d9a", lw=0.9, ls=(0, (1, 2.6)),
                 label="$\\Delta$phase, round 3")
    a3b.semilogx(f, ph[POST] - ph[PRE], color="#6a3d9a", lw=1.5, ls=(0, (5, 1.6, 1, 1.6)),
                 label="$\\Delta$phase, round 4")
    a3b.set_ylabel("$\\Delta$phase  (deg)", color="#6a3d9a")
    a3b.tick_params(axis="y", labelcolor="#6a3d9a")
    a3b.grid(False)
    a3.set_xlabel("frequency (Hz)")
    a3.set_xlim(f[0], f[-1])
    a3.set_title("(c) after layout $-$ before: the 3–5 kHz spike is the notch region, "
                 "not a resonance")
    h1, l1 = a3.get_legend_handles_labels()
    h2, l2 = a3b.get_legend_handles_labels()
    a3.legend(h1 + h2, l1 + l2, loc="upper left", ncols=2)

    fig.suptitle("Pre- vs post-layout differential response, cell lpf_core\n"
                 "typical process, 27 $^\\circ$C, 1.5 V   ·   cutoff "
                 f"{sc[PRE]['fc_hz']:.2f} $\\rightarrow$ {sc[POST]['fc_hz']:.2f} Hz")
    S.save(fig, "prepost_bode")


def main() -> int:
    if "--replot" in sys.argv:
        out = json.loads((FIGS / "data" / "prepost_bode.json").read_text())
    else:
        out = simulate()
    plot(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
