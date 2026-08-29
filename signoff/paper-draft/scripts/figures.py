#!/usr/bin/env python
"""Every figure in the reviewer pack, drawn from the committed JSON in `../data/`.

No simulation, no symbolic algebra: this script only reads what `extract_bench.py`,
`tf_analysis.py`, `noise_analysis.py` and `linearity_analysis.py` produced, so a figure
can never disagree with the table beside it.

    spicexplorer-platform/.venv/bin/python signoff/paper-draft/scripts/figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))

import _style as S  # noqa: E402
from mc_stats import se_frac as MC_SE  # noqa: E402

S.use()
import matplotlib.pyplot as plt  # noqa: E402


def load(name):
    return json.loads((DATA / name).read_text())


# ----------------------------------------------------------------- F1: pole/zero map --
def fig_pz(tf):
    fig, axes = plt.subplots(1, 3, figsize=(S.WIDE * 1.45, 2.9))
    for ax, (label, title) in zip(axes[:2], (("pre_mim", "(a) pre-layout"),
                                             ("post_lumped", "(b) post-layout (extracted C)"))):
        pz = tf["cases"][label]["pz"]
        for r in (0.5, 1.0, 1.5):     # constant-Q rays: Q = 1/(2 cos(theta))
            th = np.arccos(1 / (2 * r))
            ax.plot([0, -3000 * np.cos(th)], [0, 3000 * np.sin(th)],
                    color="0.85", lw=0.6, zorder=0)
            ax.plot([0, -3000 * np.cos(th)], [0, -3000 * np.sin(th)],
                    color="0.85", lw=0.6, zorder=0)
            ax.annotate(f"Q={r:g}", (-2150 * np.cos(th), 2150 * np.sin(th)),
                        color="0.55", fontsize=5.8, ha="right", va="bottom")
        for w0 in (250.0,):           # the target cutoff, as a circle |s| = w0
            th = np.linspace(np.pi / 2, 3 * np.pi / 2, 200)
            ax.plot(2 * np.pi * w0 * np.cos(th), 2 * np.pi * w0 * np.sin(th),
                    color=S.GREY, ls=":", lw=0.8, zorder=0)
        # `pz["poles"]` lists one representative per conjugate pair; draw both members.
        for p in pz["poles"]:
            ims = [abs(p["im"]), -abs(p["im"])] if p["kind"] == "pair" else [p["im"]]
            for im in ims:
                ax.plot(p["re"], im, "x", color=S.CYCLE[1]["color"], ms=7, mew=1.6,
                        zorder=5)
            ax.annotate(f"$f_0$={p['f0_hz']:.1f} Hz\n$Q$={p['Q']:.3f}",
                        (p["re"], abs(p["im"])), textcoords="offset points",
                        xytext=(7, 3), fontsize=6.4)
        for z in pz["zeros"]:
            if abs(complex(z["re"], z["im"])) >= 4e4:
                continue
            ims = [abs(z["im"]), -abs(z["im"])] if z["kind"] == "pair" else [z["im"]]
            for im in ims:
                ax.plot(z["re"], im, "o", mfc="none", ms=6, mew=1.2,
                        color=S.CYCLE[0]["color"], zorder=4)
        ax.axhline(0, color="0.6", lw=0.6)
        ax.axvline(0, color="0.6", lw=0.6)
        ax.set_xlim(-4500, 900)
        ax.set_ylim(-2400, 2400)
        ax.set_xlabel(r"$\sigma$  (rad/s)")
        ax.set_ylabel(r"$j\omega$  (rad/s)")
        ax.set_title(title)
        S.note(ax, f"4 poles, 2 complex pairs\n{len(pz['cancelled'])} pole-zero "
                   f"cancellations removed\nno finite zero below 3.8 kHz",
               loc="lower left")

    # (c) the same map zoomed OUT far enough to contain the zeros, which is the panel that
    # answers "are the ZEROS real or imaginary" -- they are 15x out of band, so they cannot
    # share an axis with the poles at any useful scale.
    ax = axes[2]
    for label, mark, name in (("pre_mim", "x", "pre-layout"),
                              ("post_lumped", "+", "post-layout")):
        pz = tf["cases"][label]["pz"]
        for i, p in enumerate(pz["poles"]):
            ims = [abs(p["im"]), -abs(p["im"])] if p["kind"] == "pair" else [p["im"]]
            ax.plot([p["re"]] * len(ims), ims, mark, color=S.CYCLE[1]["color"], ms=7,
                    mew=1.6, zorder=5,
                    label=f"poles, {name}" if i == 0 else None)
        for i, z in enumerate(pz["zeros"]):
            ims = [abs(z["im"]), -abs(z["im"])] if z["kind"] == "pair" else [z["im"]]
            ax.plot([z["re"]] * len(ims), ims, "o" if mark == "x" else "s", mfc="none",
                    ms=6, mew=1.2, color=S.CYCLE[0]["color"], zorder=4,
                    label=f"zeros, {name}" if i == 0 else None)
    ax.axhline(0, color="0.6", lw=0.6)
    ax.axvline(0, color="0.6", lw=0.6)
    ax.set_xlim(-6500, 8500)          # the right half is empty; the annotations live there
    ax.set_ylim(-4.0e4, 4.0e4)
    ax.set_xlabel(r"$\sigma$  (rad/s)")
    ax.set_ylabel(r"$j\omega$  (rad/s)")
    ax.set_title("(c) full plane: poles and zeros")
    ax.legend(fontsize=5.8, loc="upper right", framealpha=0.9)
    zs = tf["cases"]["pre_mim"]["pz"]["zeros"]
    S.note(ax, "all 4 zeros are complex, in the LHP,\n"
               f"at {zs[0]['f0_hz'] / 1e3:.2f} and {zs[1]['f0_hz'] / 1e3:.2f} kHz\n"
               "(the poles are the cluster at the origin)", loc="lower right")
    S.save(fig, "pz_plane")
    plt.close(fig)


# ------------------------------------------- F1b: the half-circuit the algebra describes --
def fig_half_circuit():
    """The DM half-circuit as a node/branch diagram, labelled with the equation's symbols.

    Drawn rather than rendered: the point of this figure is the MAPPING from the schematic
    (`signoff/post-pvt/H12-pdk-cap/lpf_core_H12pc.png`, the committed drawing of record)
    onto the symbols of `theory.md` section 2, and onto the one branch -- the bridge -- that
    makes `kappa` non-zero.  A transistor-level render cannot show that; this can.
    """
    fig, ax = plt.subplots(figsize=(S.WIDE, 3.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 54)
    ax.axis("off")
    blue, red = S.CYCLE[0]["color"], S.CYCLE[1]["color"]

    def node(x, y, label, sub=""):
        ax.add_patch(plt.Circle((x, y), 2.0, fc="white", ec="0.25", lw=1.1, zorder=4))
        ax.annotate(label, (x, y + 3.0), ha="center", va="bottom", fontsize=7.4,
                    zorder=5)
        if sub:
            ax.annotate(sub, (x, y - 3.2), ha="center", va="top", fontsize=6.2,
                        color="0.4", zorder=5)

    def gm(x0, y0, x1, y1, label, at, color="0.25", rad=0.0, lw=1.3, fs=7.0):
        """One transconductance branch: an arrow from source node to the node it drives.

        `at` is the label position in data coordinates -- placed explicitly rather than at
        the arrow midpoint, because these arcs cross each other and a midpoint label lands
        on a neighbour's arrow every time.
        """
        ax.annotate("", (x1, y1), (x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                    shrinkA=8, shrinkB=8,
                                    connectionstyle=f"arc3,rad={rad}"), zorder=3)
        ax.annotate(label, at, ha="center", va="center", fontsize=fs, color=color,
                    zorder=6, bbox=dict(fc="white", ec="none", pad=0.8))

    def cap(x, y, label, vertical=True, size=2.4, to_gnd=False):
        if vertical:
            ax.plot([x - size, x + size], [y + 0.6] * 2, color="0.25", lw=1.4, zorder=3)
            ax.plot([x - size, x + size], [y - 0.6] * 2, color="0.25", lw=1.4, zorder=3)
            ax.annotate(label, (x + size + 0.8, y), ha="left", va="center", fontsize=7.0)
        else:
            ax.plot([x - 0.6] * 2, [y - size, y + size], color="0.25", lw=1.4, zorder=3)
            ax.plot([x + 0.6] * 2, [y - size, y + size], color="0.25", lw=1.4, zorder=3)
            ax.annotate(label, (x, y + size + 0.8), ha="center", va="bottom", fontsize=7.0)

    def gnd(x, y):
        for i, w in enumerate((2.4, 1.5, 0.7)):
            ax.plot([x - w, x + w], [y - 1.1 * i] * 2, color="0.35", lw=1.1)

    # ---- nodes -----------------------------------------------------------------------
    node(9, 37, "$v_{in}$", "vinp")
    node(30, 44, "$v_{xA}$", "net2")
    node(30, 22, "$v_{oA}$", "vout_1")
    node(72, 44, "$v_{xB}$", "net4")
    node(72, 22, "$v_{oB}$", "voutp")
    node(93, 22, "$v_{out}$", "")

    # ---- biquad A --------------------------------------------------------------------
    gm(9, 37, 30, 44, r"$gm_{ia}\,(v_{in}-v_{oA})$", at=(17, 42.5), rad=0.14, fs=6.6)
    gm(30, 44, 30, 22, r"$gm_{fa}\,v_{xA}$", at=(20.0, 33), rad=0.55, fs=6.6)
    cap(38, 33, "$C_{1a}$", vertical=False)
    ax.plot([30, 38, 38], [22, 22, 30.6], color="0.25", lw=1.0, zorder=2)
    ax.plot([38, 38, 30], [35.4, 44, 44], color="0.25", lw=1.0, zorder=2)
    ax.plot([30, 30], [20, 14], color="0.25", lw=1.0, zorder=2)
    cap(30, 13, r"$2\,C_{2a}$")
    gnd(30, 11.2)
    # ---- biquad B --------------------------------------------------------------------
    gm(30, 22, 72, 44, r"$gm_{ib}\,(v_{oA}-v_{oB})$", at=(53, 28.5), rad=0.10, fs=6.6)
    gm(72, 44, 72, 22, r"$gm_{fb}\,v_{xB}$", at=(62.0, 33), rad=0.55, fs=6.6)
    cap(80, 33, "$C_{1b}$", vertical=False)
    ax.plot([72, 80, 80], [22, 22, 30.6], color="0.25", lw=1.0, zorder=2)
    ax.plot([80, 80, 72], [35.4, 44, 44], color="0.25", lw=1.0, zorder=2)
    ax.plot([72, 72], [20, 14], color="0.25", lw=1.0, zorder=2)
    cap(72, 13, r"$2\,C_{2b}$")
    gnd(72, 11.2)
    ax.plot([74, 91], [22, 22], color="0.25", lw=1.0, zorder=2)

    # ---- the bridge: the one branch that makes kappa non-zero -------------------------
    gm(72, 44, 30, 22, r"$gm_{br}\,v_{xB}$   (the bridge, xmst)", at=(53, 39.5),
       color=red, rad=0.30, lw=1.8, fs=7.0)

    ax.annotate("biquad A  —  $D_A(s)$", (30, 50.5), ha="center", fontsize=8.4)
    ax.annotate("biquad B  —  $D_B(s)$", (72, 50.5), ha="center", fontsize=8.4)
    ax.annotate("differential-mode half-circuit: every axis net (vbn, vbr, vdd, the replica)\n"
                "is an ac ground, and each floating cross capacitor loads one half with $2C$.\n"
                "Instance names are the certified netlist's; symbols are theory.md section 2.",
                (1, 7.5), ha="left", va="top", fontsize=6.6, color="0.35")
    ax.annotate(r"$v_{oA}\!\rightarrow\! gm_{ib}\!\rightarrow\! v_{xB}"
                r"\!\rightarrow\! gm_{br}\!\rightarrow\! v_{oA}$"
                "\nis the only loop between the two biquads:\n"
                r"$\kappa = 2\,C_{1a}C_{2b}\,gm_{br}\,gm_{ib}$",
                (52, 15.0), ha="center", va="center", fontsize=7.0, color=red)
    S.save(fig, "half_circuit")
    plt.close(fig)


# ------------------------------------------------------- F2: model vs simulation Bode --
def fig_bode(tf):
    v = tf["cases"]["pre_mim"]["validation"]
    f = np.array(v["f"])
    fig, ax = plt.subplots(3, 1, figsize=(S.COL, 5.0), sharex=True)
    ax[0].semilogx(f, v["sim_db"], **S.CYCLE[0], markevery=12, label="ngspice (PSP103)")
    ax[0].semilogx(f, v["model_db"], **S.CYCLE[1], markevery=12,
                   label="netlist2tf small-signal")
    ax[0].set_ylabel(r"$|H|$  (dB)")
    ax[0].set_ylim(-120, 10)
    ax[0].legend(loc="lower left")
    ax[0].set_title("(a) magnitude")
    ax[1].semilogx(f, v["sim_deg"], **S.CYCLE[0], markevery=12)
    ax[1].semilogx(f, v["model_deg"], **S.CYCLE[1], markevery=12)
    ax[1].set_ylabel("phase  (deg)")
    ax[1].set_title("(b) unwrapped phase")
    err = np.array(v["model_db"]) - np.array(v["sim_db"])
    perr = np.array(v["model_deg"]) - np.array(v["sim_deg"])
    ax[2].semilogx(f, err, color=S.CYCLE[2]["color"], ls="-", label="magnitude (dB)")
    ax[2].semilogx(f, perr, color=S.CYCLE[3]["color"], ls="--", label="phase (deg)")
    ax[2].axvspan(0.1, 1000, color=S.OK, alpha=0.06)
    ax[2].set_ylabel("model $-$ sim")
    ax[2].set_xlabel("frequency (Hz)")
    ax[2].set_ylim(-3, 3)
    ax[2].legend(loc="lower left")
    ax[2].set_title("(c) residual")
    S.note(ax[2], f"scored band ($\\leq$1 kHz):\n"
                  f"{v['max_mag_err_db_scored']:.3f} dB, "
                  f"{v['max_phase_err_deg_scored']:.3f}$^\\circ$\n"
                  f"group delay {v['max_gd_err_pct']:.2f} %", loc="upper left")
    S.save(fig, "bode_model_vs_sim")
    plt.close(fig)


# ------------------------------------------------------------------------ F3: noise --
def fig_noise(nz):
    d = nz["pre_mim"]
    f = np.array(d["f"])
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))
    ax[0].loglog(f, np.array(d["inoise_sim"]) * 1e9, **S.CYCLE[0], markevery=14,
                 label="ngspice input-referred")
    ax[0].loglog(f, np.array(d["onoise_sum_of_generators"]) / np.array(d["h_mag"]) * 1e9,
                 **S.CYCLE[1], markevery=14, label=r"$\sum_k |Z_{T,k}|^2 S_{i,k}$ / $|H|^2$")
    ax[0].axvspan(0.5, 200, color=S.OK, alpha=0.07)
    ax[0].set_xlabel("frequency (Hz)")
    ax[0].set_ylabel(r"input-referred density (nV/$\sqrt{\rm Hz}$)")
    ax[0].set_title("(a) noise equation vs simulator")
    ax[0].legend(loc="lower left")
    S.note(ax[0], f"IRN 0.5-200 Hz\n  simulator {d['irn_uv_sim']:.4f} $\\mu$V\n"
                  f"  equation  {d['irn_uv_sum_of_generators']:.4f} $\\mu$V\n"
                  f"closure {d['onoise_closure_max_pct']:.1e} %", loc="upper right")

    by_role: dict[str, float] = {}
    for r in d["rows"]:
        key = f"{r['role']} / {r['gen']}"
        by_role[key] = by_role.get(key, 0.0) + r.get("irn_uv_rms", 0.0) ** 2
    tot = sum(by_role.values())
    items = sorted(by_role.items(), key=lambda kv: -kv[1])[:9]
    y = np.arange(len(items))
    ax[1].barh(y, [100 * v / tot for _k, v in items],
               color=[S.CYCLE[0]["color"] if "idid" in k else
                      S.CYCLE[1]["color"] if "igig" in k else
                      S.CYCLE[2]["color"] for k, _v in items])
    ax[1].set_yticks(y)
    ax[1].set_yticklabels([k for k, _v in items], fontsize=6.4)
    ax[1].invert_yaxis()
    ax[1].set_xlabel("share of input-referred noise POWER (%)")
    ax[1].set_title("(b) where the noise comes from")
    ax[1].grid(axis="y", alpha=0)
    S.save(fig, "noise_budget")
    plt.close(fig)


# -------------------------------------------------------------------- F4: distortion --
def fig_thd(la):
    al, fr = la["amplitude_law"], la["frequency_law"]
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))
    v = np.array([r["vpp_diff"] for r in al["all_points"]]) * 1e3
    ax[0].semilogx(v, [r["thd_db"] for r in al["all_points"]], **S.CYCLE[0],
                   label="THD (h2..h10)")
    ax[0].semilogx(v, [r["hd3_db"] for r in al["all_points"]], **S.CYCLE[1], label="HD3")
    lp = np.array([r["vpp_diff"] for r in al["points"]]) * 1e3
    ref = al["points"][-1]
    ax[0].semilogx(v, ref["hd3_db"] + 40 * np.log10(v / (ref["vpp_diff"] * 1e3)),
                   color=S.GREY, ls=":", lw=1.1, label=r"$A^2$ law (40 dB/decade)")
    ax[0].axhline(-40, color=S.BAD, lw=0.9, ls="--")
    ax[0].axvline(175, color=S.OK, lw=0.9, ls="--")
    ax[0].set_xlabel("differential input (mVpp)")
    ax[0].set_ylabel("dBc")
    ax[0].set_title("(a) distortion vs amplitude, $f_{in}$ = 50 Hz")
    ax[0].legend(loc="upper left")
    S.note(ax[0], f"fitted {al['fitted_slope_db_per_decade']:.1f} dB/decade\n"
                  f"residual {al['max_residual_db']:.2f} dB\n"
                  f"THD = $-$40 dB at {al['thd_minus40_vpp'] * 1e3:.0f} mVpp\n"
                  f"S7 point 175 mVpp", loc="lower right")

    fq = np.array([r["fin"] for r in fr["rows"]])
    ax[1].semilogx(fq, [r["hd3_measured_db"] for r in fr["rows"]], **S.CYCLE[0],
                   label="measured")
    ax[1].semilogx(fq, [r["hd3_model_db"] for r in fr["rows"]], **S.CYCLE[1],
                   label=r"model  $I_D\,2I_3(a)/I_0(a)$ through $Z_T(3\omega)$")
    # The shaded band is the model's stated validity window: the fins where |model -
    # measured| <= 2 dB.  Computed, not drawn by hand, so the figure cannot drift from
    # validation.md section 6.2.
    ok = [r["fin"] for r in fr["rows"] if abs(r["err_db"]) <= 2.0]
    ax[1].axvspan(min(ok), max(ok), color=S.OK, alpha=0.07)
    ax[1].set_xlabel("input frequency (Hz)")
    ax[1].set_ylabel("HD3 (dBc)")
    ax[1].set_title(f"(b) HD3 vs frequency at {fr['vpp_diff'] * 1e3:.2f} mVpp")
    ax[1].legend(loc="upper left")
    S.note(ax[1], f"HD3 moves "
                  f"{max(r['hd3_measured_db'] for r in fr['rows']) - min(r['hd3_measured_db'] for r in fr['rows']):.0f} dB "
                  f"across the passband\nat FIXED drive: the cell is\nnot memoryless\n"
                  f"model within 2 dB over {min(ok):.0f}-{max(ok):.0f} Hz (shaded)\n"
                  f"and within {max(abs(r['err_db']) for r in fr['rows']):.0f} dB over the "
                  f"whole sweep",
           loc="lower right")
    S.save(fig, "distortion")
    plt.close(fig)


# ------------------------------------------------------------------ F5: IMD3 / IIP3 --
def fig_iip3(la):
    ii = la["iip3"]["pre_mim"]
    mt = la["memoryless_test"]
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))
    a = np.array([r["ampl_per_tone_v"] for r in ii["points"]]) * 1e3
    im = np.array([r["imd3_db"] for r in ii["points"]])
    ax[0].semilogx(a, im, **S.CYCLE[0], label="IMD3 measured")
    ax[0].semilogx(a, [r["imd2_diff_db"] for r in ii["points"]], **S.CYCLE[2],
                   label=r"IMD2 ($f_2-f_1$)")
    ref_a, ref_i = a[0], im[0]
    ax[0].semilogx(a, ref_i + 40 * np.log10(a / ref_a), color=S.GREY, ls=":", lw=1.1,
                   label="2:1 in dBc (3:1 slope)")
    ax[0].set_xlabel("per-tone differential amplitude (mV)")
    ax[0].set_ylabel("dBc")
    ax[0].set_title("(a) two-tone, 45 / 55 Hz")
    ax[0].legend(loc="lower right")
    S.note(ax[0], f"IIP3 = {ii['iip3_dbv']:.2f} dBV\n"
                  f"({ii['iip3_v_peak_per_tone'] * 1e3:.0f} mV peak/tone)\n"
                  f"slope {ii['imd3_slope_db_per_decade']:.1f} dB/decade\n"
                  f"IIP3 spread "
                  f"{ii['consistency_of_iip3_over_linear_points_db']:.2f} dB",
           loc="upper left")

    sp = mt["spacing_sweep"]
    ax[1].semilogx([r["spacing"] for r in sp], [r["imd3_db"] for r in sp], **S.CYCLE[1],
                   label="IMD3 measured")
    ax[1].axhline(mt["imd3_memoryless_prediction_db"], color=S.BAD, ls="--", lw=1.0,
                  label=r"memoryless  HD3 + 9.54 dB")
    ax[1].set_xlabel(r"tone spacing $f_2-f_1$ (Hz), centred on 50 Hz")
    ax[1].set_ylabel("IMD3 (dBc)")
    ax[1].set_title("(b) is the excess an envelope-memory effect?")
    ax[1].legend(loc="center right")
    S.note(ax[1], f"IMD3 moves {mt['imd3_spread_over_spacing_db']:.2f} dB over a "
                  f"{mt['spacing_ratio']:.0f}$\\times$\nspacing change: NOT envelope "
                  f"memory.\nThe {mt['excess_db']:+.1f} dB excess over the\nmemoryless "
                  f"identity is the frequency\ndependence of HD3 itself.",
           loc="lower left")
    S.save(fig, "iip3")
    plt.close(fig)


def cy(i: int, **kw) -> dict:
    """One entry of the shared colour cycle with per-call overrides merged in.

    `S.CYCLE[i]` already carries `marker` and `ms`, so splatting it next to an explicit
    marker is a duplicate-keyword TypeError; this merges instead of colliding.
    """
    return {**S.CYCLE[i % len(S.CYCLE)], **kw}


# ------------------------------------------------- F6: the analytical results over PVT --
def fig_pvt(pv):
    """Scale moves, shape does not -- and the certified window does not superpose."""
    ax_rows = pv["cert-axes"]["rows"]
    post = {r["slug"]: r for r in pv["cert-axes:post_lumped"]["rows"]}
    n = len(ax_rows)
    x = np.arange(n)
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE * 1.15, 3.0))

    # (a) fc and Q on one axis, normalised to their nominal value, so "moves with T by
    # construction" and "should not move" can be compared on the same scale.
    def norm(vals):
        return np.asarray(vals, float) / vals[0]
    fc = norm([r["scorecard"]["fc_hz"] for r in ax_rows])
    qlo = norm([r["pairs"][0]["Q"] for r in ax_rows])
    qhi = norm([r["pairs"][1]["Q"] for r in ax_rows])
    # The x axis is a LIST of corners, not a continuous variable: markers only, because
    # a line between two corners would draw a trend that does not exist.
    ax[0].plot(x, fc, **cy(0, ls="none", ms=6), label=r"$f_c$  (scale: $g_m/C$)")
    ax[0].plot(x, qlo, **cy(1, ls="none", ms=6), label=r"$Q_{lo}$  (shape: ratio)")
    ax[0].plot(x, qhi, **cy(2, ls="none", ms=6), label=r"$Q_{hi}$  (shape: ratio)")
    ax[0].plot(x, norm([post[r["slug"]]["scorecard"]["fc_hz"] for r in ax_rows]),
               color=S.GREY, ls="none", marker="o", ms=9, mfc="none", mew=0.9,
               label=r"$f_c$, post-layout")
    for xi in x:
        ax[0].axvline(xi, color="0.92", lw=0.5, zorder=0)
    lo_y = min(fc.min(), qlo.min(), qhi.min())
    hi_y = max(fc.max(), qlo.max(), qhi.max())
    ax[0].set_ylim(lo_y - 0.35 * (hi_y - lo_y), hi_y + 0.08 * (hi_y - lo_y))
    ax[0].axhline(1.0, color="0.7", lw=0.6)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([r["slug"].replace("_", "\n") for r in ax_rows], fontsize=5.4)
    ax[0].set_ylabel("normalised to the nominal corner")
    ax[0].set_title("(a) the nine certified axis points")
    ax[0].legend(loc="upper left", fontsize=6)
    s, sp = pv["cert-axes"]["summary"], pv["cert-axes:post_lumped"]["summary"]
    S.note(ax[0], f"$f_c$ spans {s['fc_hz']['span_x']:.3f}$\\times$\n"
                  f"$Q_{{lo}}$ {s['Q_lo']['span_x']:.3f}$\\times$, "
                  f"$Q_{{hi}}$ {s['Q_hi']['span_x']:.3f}$\\times$\n"
                  f"two complex pairs {s['n_two_pair']}/{s['n_corners']}\n"
                  f"post-layout: {sp['fc_hz']['span_x']:.3f}$\\times$ / "
                  f"{sp['Q_lo']['span_x']:.3f}$\\times$ / "
                  f"{sp['Q_hi']['span_x']:.3f}$\\times$", loc="lower left")

    # (b) the 45-point cross product.  One marker per point, filled where both complex
    # pairs survive and hollow-red where one is lost -- the non-superposition finding.
    box = pv["cert-box"]["rows"]
    procs = sorted({r["corner"]["process"] for r in box})
    cols = sorted({(r["corner"]["temp"], r["corner"]["vdd"]) for r in box})
    for r in box:
        i = procs.index(r["corner"]["process"])
        j = cols.index((r["corner"]["temp"], r["corner"]["vdd"]))
        two = len(r["pairs"]) >= 2
        ax[1].plot(j, i, marker="o" if two else "X", ms=7 if two else 8,
                   color=S.OK if two else S.BAD, mfc=S.OK if two else "none",
                   mew=1.0 if two else 1.6, ls="none")
    ax[1].set_yticks(range(len(procs)))
    ax[1].set_yticklabels(procs, fontsize=6.5)
    ax[1].set_xticks(range(len(cols)))
    ax[1].set_xticklabels([f"{t:g}°C\n{v:.2f} V" for t, v in cols], fontsize=5.6)
    ax[1].set_xlim(-0.6, len(cols) - 0.4)
    # Leave an empty strip under the bottom row for the note, so it never sits on a point.
    ax[1].set_ylim(-1.9, len(procs) - 0.4)
    ax[1].set_title("(b) the certified window does not superpose")
    sb = pv["cert-box"]["summary"]
    S.note(ax[1], f"{sb['n_two_pair']}/{sb['n_corners']} keep two complex pairs;\n"
                  f"✕ = one pair lost.  Each axis is\ncertified ALONE -- the cross "
                  f"product\nis not, and 1.40 V at 0 °C shows it.", loc="lower center")
    S.save(fig, "pvt_axes")
    plt.close(fig)


# ------------------------------------------------------- F7: Monte Carlo over mismatch --
def fig_mc(pv):
    mc = pv["mismatch"]
    rows, s = mc["rows"], mc["summary"]
    fig, ax = plt.subplots(1, 3, figsize=(S.WIDE * 1.2, 2.7))
    for a, (vals, lab, unit) in zip(ax, (
            ([r["scorecard"]["fc_hz"] for r in rows], r"$f_c$", "Hz"),
            ([r["pairs"][1]["Q"] for r in rows], r"$Q_{hi}$", ""),
            ([r["offset_in_uv"] for r in rows], "input-referred offset", "µV"))):
        v = np.asarray(vals, float)
        a.hist(v, bins=max(14, int(np.sqrt(v.size))), color=S.CYCLE[0]["color"],
               alpha=0.8, edgecolor="white", linewidth=0.5)
        a.axvline(v.mean(), color=S.BAD, lw=1.1, ls="--")
        a.set_xlabel(f"{lab}  ({unit})" if unit else lab)
        a.set_ylabel("draws")
        S.note(a, f"mean {v.mean():.4g}\n$\\sigma$ {v.std(ddof=1):.4g}\n"
                  f"[{v.min():.4g}, {v.max():.4g}]", loc="upper right")
    # Relative sigma on both, because the PVT figure's headline is that shape is ~10x
    # stiffer than scale and under MISMATCH that separation does not hold: a random
    # per-device shift is not a global parameter shift, so it moves ratios too.
    ax[0].set_title(f"(a) scale: $\\sigma$ = {s['fc_hz']['sigma']:.3f} Hz "
                    f"({100 * s['fc_hz']['sigma'] / s['fc_hz']['mean']:.2f} %)")
    ax[1].set_title(f"(b) shape: $\\sigma$ = {s['Q_hi']['sigma']:.4f} "
                    f"({100 * s['Q_hi']['sigma'] / s['Q_hi']['mean']:.2f} %)")
    ax[2].set_title(f"(c) {s['n_two_pair']}/{s['n_draws']} keep two pairs")
    S.save(fig, "mc_mismatch")
    plt.close(fig)


# ------------------------------------- F8: supply rejection, CM rejection and offset --
def fig_rejection(rj):
    """The two rejection ratios, and the transfers they are built from.

    CMRR and PSRR are defined against the DIFFERENTIAL output -- CMRR = A_dm /
    A_(cm->dm), PSRR = A_dm / A_(vdd->dm) -- so panel (a) draws the numerator and the two
    denominators on one axis and the rejection is the vertical gap between them.  Panel
    (b) is the ratios themselves.  The common-mode-to-common-mode paths are a DIFFERENT
    quantity, finite at nominal where the differential ones are symmetry-cancelled, and
    they get their own panel (c) rather than sharing an axis with the rejection.
    """
    spots = rj["spots_hz"]
    keys = [f"{x:g}" for x in spots]
    cs = rj["corners"]
    nom = cs["tt_27c_1v500"]
    mc = rj["mismatch"]["curves"]
    fm = np.asarray(mc["f"], float)
    fig, ax = plt.subplots(1, 3, figsize=(S.WIDE * 1.2, 2.9))

    # (a) the definition, drawn.
    for i, (k, lab) in enumerate((("a_dm_db", r"$A_{dm}$  (signal)"),
                                  ("cm_to_dm_db", r"CM in $\rightarrow$ DM out"),
                                  ("supply_to_dm_db", r"supply $\rightarrow$ DM out"))):
        b = mc[k]
        ax[0].semilogx(fm, b["mean"], **cy(i, marker="", lw=1.2), label=lab)
        ax[0].fill_between(fm, b["min"], b["max"], color=S.CYCLE[i]["color"],
                           alpha=0.15, lw=0)
    ax[0].set_xlabel("frequency (Hz)")
    ax[0].set_ylabel("dB")
    ax[0].set_xlim(fm.min(), 1e4)
    ax[0].set_title("(a) the transfers the ratios are made of")
    # Headroom above the 0 dB signal path so the note sits in empty axes rather than on
    # top of the leakage curves it is describing.
    ax[0].set_ylim(-165, 55)
    ax[0].legend(loc="upper right", fontsize=6.0)
    S.note(ax[0], "rejection is the VERTICAL GAP:\n"
                  "CMRR = $A_{dm}$ $-$ (CM$\\rightarrow$DM),\n"
                  "PSRR = $A_{dm}$ $-$ (supply$\\rightarrow$DM).\n"
                  "Both leakage paths are measured\nto the DIFFERENTIAL output.",
           loc="lower left")

    # (b) the ratios.
    for i, (k, lab) in enumerate((("cmrr_db", "CMRR"), ("psrr_db", "PSRR"))):
        b = mc[k]
        ax[1].semilogx(fm, b["mean"], **cy(i, marker="", lw=1.2), label=f"{lab} mean")
        ax[1].fill_between(fm, b["min"], b["max"], color=S.CYCLE[i]["color"],
                           alpha=0.15, lw=0)
    ax[1].set_xlabel("frequency (Hz)")
    ax[1].set_ylabel("dB")
    ax[1].set_xlim(fm.min(), 1e4)
    ax[1].set_title(f"(b) mismatch-limited, {rj['mismatch']['n_draws']} draws")
    ax[1].set_ylim(-50, 150)
    ax[1].legend(loc="lower left", fontsize=6.5)
    mm = rj["mismatch"]
    S.note(ax[1], f"at dc: CMRR {mm['cmrr_db']['0.1']['mean']:.1f} dB mean,\n"
                  f"{mm['cmrr_db']['0.1']['min']:.1f} worst;  PSRR "
                  f"{mm['psrr_db']['0.1']['mean']:.1f} /\n"
                  f"{mm['psrr_db']['0.1']['min']:.1f}.  Input-referred offset\n"
                  f"$\\sigma$ = {mm['offset_in_uv']['sigma']:.0f} µV\n"
                  f"(line: mean of the dB values;\nshaded: min-max over draws)",
           loc="upper right")

    # (c) a different quantity: the common-mode paths, finite at nominal.
    f = np.asarray(nom["curves"]["f"], float)
    env = np.array([[c["curves"][k] for c in cs.values()]
                    for k in ("supply_to_cm_db", "cm_to_cm_db")])
    for i, (k, lab) in enumerate((("supply_to_cm_db", r"supply $\rightarrow$ CM"),
                                  ("cm_to_cm_db", r"CM $\rightarrow$ CM"))):
        ax[2].semilogx(f, nom["curves"][k], **cy(i, marker="", lw=1.2), label=lab)
        ax[2].fill_between(f, env[i].min(0), env[i].max(0),
                           color=S.CYCLE[i]["color"], alpha=0.15, lw=0)
        # The four spot frequencies the tables quote, marked on the measured sweep.
        ax[2].plot([float(x) for x in keys], [nom[k][s] for s in keys],
                   ls="none", marker="o", ms=4, color=S.CYCLE[i]["color"])
    ax[2].set_xlabel("frequency (Hz)")
    ax[2].set_ylabel("dB")
    ax[2].set_xlim(f.min(), 1e4)
    ax[2].set_title("(c) nominal common-mode paths")
    ax[2].legend(loc="lower right", fontsize=6.5)
    ax[2].set_ylim(-80, 6)
    S.note(ax[2], "NOT rejection: these end at the\noutput COMMON mode.  Shaded: the\n"
                  "envelope over the nine certified\naxis points.  Symmetry-exact, so\n"
                  "they are finite at nominal.", loc="center left")
    S.save(fig, "rejection")
    plt.close(fig)


# ------------------------------------------------- F9: the sub-35 Hz residual, explained --
def fig_residual(gr):
    rows = gr["rows"]
    f = np.array([r["fin"] for r in rows], float)
    flat = gr["flat_band_hz"]
    m = f <= flat
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))

    ax[0].loglog(f, [abs(r["v3_measured_uv"]) for r in rows], **cy(0, marker="o", ms=4), label="measured $V_3$")
    ax[0].loglog(f, [abs(r["v3_gate_model_uv"]) for r in rows], **cy(1, marker="s", ms=4), label=r"gate model  $2I_3(a)/I_0(a)$")
    ax[0].loglog(f, [abs(r["v3_unexplained_uv"]) for r in rows], **cy(2, marker="^", ms=4), label="unexplained (measured $-$ model)")
    ax[0].axvspan(f.min(), flat, color=S.GREY, alpha=0.10, lw=0)
    ax[0].set_xlabel("input frequency (Hz)")
    ax[0].set_ylabel(r"$V_3$  ($\mu$V)")
    ax[0].set_title("(a) what section 6.2 leaves unexplained")
    ax[0].legend(loc="upper left", fontsize=6.5)
    S.note(ax[0], f"shaded: the flat band, $f_{{in}} \\leq$ {flat:g} Hz.\nThe residual is "
                  f"flat in VOLTS there\nwhile the gate model moves 39$\\times$ --\nan "
                  f"additive mechanism, not a\nmis-scaled one.", loc="lower right")

    ax[1].plot(f[m], [r["v3_unexplained_uv"] for r in rows if r["fin"] <= flat],
               **cy(2, marker="^", ms=5), label="unexplained")
    ax[1].fill_between(f[m],
                       [min(r["v3_by_window_uv"].values()) for r in rows if r["fin"] <= flat],
                       [max(r["v3_by_window_uv"].values()) for r in rows if r["fin"] <= flat],
                       color=S.CYCLE[1]["color"], alpha=0.18, lw=0,
                       label=r"cubic $g_3A^3/24$, over the three fit windows")
    ax[1].plot(f[m], [r["v3_gds_pred_uv"] for r in rows if r["fin"] <= flat],
               **cy(1, marker="s", ms=4), label="cubic, mid window (pre-registered)")
    ax[1].plot(f[m], [r["v3_gds_exact_uv"] for r in rows if r["fin"] <= flat],
               **cy(3, marker="o", ms=4),
               label="window-free, over each device's own swing")
    ax[1].set_xlabel("input frequency (Hz)")
    ax[1].set_ylabel(r"$V_3$  ($\mu$V)")
    ax[1].set_ylim(0, None)
    ax[1].set_title(r"(b) drain-conductance curvature, $g_{ds}$")
    ax[1].legend(loc="upper left", fontsize=5.8)
    rf = gr["refinement"]
    S.note(ax[1], f"pre-registered point estimate:\nworst {gr['p1_worst_factor']:.2f}"
                  f"$\\times$ → {gr['verdict']}\nwindow-free: "
                  f"{rf['worst_factor']:.2f}$\\times$, i.e. "
                  f"{rf['coverage_pct']:.0f} % of the\nresidual, and the band overlap "
                  f"goes away.\nRight shape, about a fifth of the size.",
           loc="center right")
    S.save(fig, "gds_residual")
    plt.close(fig)


# ------------------------------------------------------------ F10: IIP3 over corners --
def fig_iip3_corners(ic):
    rows = list(ic["corners"].values())
    slugs = list(ic["corners"])
    x = np.arange(len(rows))
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))

    ok = [i for i, r in enumerate(rows) if r.get("trusted")]
    ax[0].plot(x[ok], [rows[i]["iip3_dbv"] for i in ok], **cy(0, marker="o", ms=5, ls="none"), label="IIP3")
    lo, hi = ic["iip3_dbv_span"]
    ax[0].axhspan(lo, hi, color=S.CYCLE[0]["color"], alpha=0.12, lw=0)
    ax[0].axhline(rows[0]["iip3_dbv"], color=S.GREY, ls=":", lw=1.0, label="nominal")
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([s.replace("_", "\n") for s in slugs], fontsize=5.4)
    ax[0].set_ylabel("IIP3 (dBVp)")
    # Headroom above the best corner so the note never covers a point.
    vals = [r["iip3_dbv"] for r in rows]
    ax[0].set_ylim(min(vals) - 0.25, max(vals) + 1.15)
    ax[0].set_title("(a) IIP3 over the certified axes")
    ax[0].legend(loc="lower left", fontsize=6.5)
    S.note(ax[0], f"{lo:+.3f} .. {hi:+.3f} dBVp\nspread {hi - lo:.2f} dB over "
                  f"{len(ok)}/{len(rows)} corners\ntones fixed at "
                  f"{ic['tones_hz'][0]:g}/{ic['tones_hz'][1]:g} Hz", loc="upper right")

    sl = [r["imd3_slope_db_per_decade"] for r in rows]
    ax[1].plot(x, sl, **cy(1, marker="s", ms=5, ls="none"))
    ax[1].axhline(ic["slope_ideal_db_per_decade"], color=S.OK, ls="--", lw=1.0,
                  label="cubic law, 40 dB/decade")
    ax[1].axhspan(ic["slope_ideal_db_per_decade"] - 10, ic["slope_ideal_db_per_decade"] + 10,
                  color=S.OK, alpha=0.08, lw=0)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([s.replace("_", "\n") for s in slugs], fontsize=5.4)
    ax[1].set_ylabel("measured IMD3 slope (dB/decade)")
    ax[1].set_title("(b) an intercept, or an extrapolation?")
    ax[1].legend(loc="lower left", fontsize=6.5)
    S.note(ax[1], "Two drive levels per corner, so\nevery row reports its OWN slope\n"
                  "instead of assuming 3:1.  A row\noutside the shaded band would\nnot be "
                  "an intercept.", loc="upper right")
    S.save(fig, "iip3_corners")
    plt.close(fig)


# ------------------------------------------------------------- F11: THD over corners --
def fig_thd_corners(tc):
    slugs = list(tc["corners"])
    fig, ax = plt.subplots(1, 2, figsize=(S.WIDE, 2.9))
    # Nine corners need nine distinguishable colours; the four-entry house cycle would
    # repeat and make two different corners look like one.
    shades = plt.cm.viridis(np.linspace(0.05, 0.9, len(slugs)))
    for i, s in enumerate(slugs):
        pts = tc["corners"][s]["points"]
        v = np.array([p["vpp_diff"] for p in pts]) * 1e3
        ax[0].semilogx(v, [p["thd_db"] for p in pts], color=shades[i],
                       lw=1.0, marker=".", ms=3.5, label=s)
    ax[0].axhline(-40, color=S.BAD, lw=0.9, ls="--")
    ax[0].axvline(tc["spec_vpp"] * 1e3, color=S.OK, lw=0.9, ls="--")
    ax[0].set_xlabel("differential input (mVpp)")
    ax[0].set_ylabel("THD (dBc)")
    ax[0].set_title(f"(a) the ladder at every corner, $f_{{in}}$ = {tc['fin_hz']:g} Hz")
    ax[0].legend(loc="upper left", fontsize=5.0, ncol=2, handlelength=1.4,
                 columnspacing=0.9, labelspacing=0.25)
    lo, hi = tc["thd_db_at_spec_span"]
    S.note(ax[0], f"dashed: the S7 lines\n({tc['spec_vpp'] * 1e3:g} mVpp, $-$40 dB).\n"
                  f"At that point the corners span\n{lo:.2f} .. {hi:.2f} dB.\n"
                  f"Report-only: S7 is scored at\nnominal by make check.", loc="lower right")

    x = np.arange(len(slugs))
    ax[1].plot(x, [tc["corners"][s]["thd_db_at_spec"] for s in slugs], **cy(0, marker="o", ms=5, ls="none"), label=f"THD at {tc['spec_vpp'] * 1e3:g} mVpp")
    ax[1].plot(x, [tc["corners"][s]["hd3_db_at_spec"] for s in slugs], **cy(1, marker="^", ms=5, ls="none"), label="HD3 at the same point")
    ax[1].axhline(-40, color=S.BAD, lw=0.9, ls="--", label="S7 limit")
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([s.replace("_", "\n") for s in slugs], fontsize=5.4)
    ax[1].set_ylabel("dBc")
    ax[1].set_title("(b) margin at the spec point")
    # Both lower corners hold data; the free space is top-left.
    ax[1].legend(loc="upper left", fontsize=6.5)
    # THD is negative dBc: the WORST corner is the least negative one.
    worst = max(tc["corners"][s]["thd_db_at_spec"] for s in slugs)
    S.note(ax[1], f"worst corner {worst:.2f} dB, i.e.\n{abs(worst) - 40:.2f} dB of margin on "
                  f"a limit\nthe spec defines at nominal only.\nBest {lo:.2f} dB; the nine "
                  f"span {hi - lo:.2f} dB.", loc="upper right")
    S.save(fig, "thd_corners")
    plt.close(fig)


# ------------------------------------------- F13: has the Monte Carlo converged? --
def fig_mc_convergence(pv, rj):
    """Running sigma against N, inside the band that (M1) allows it to wander in.

    Both populations use seeds `1..N` in order, so the left-hand part of every trace IS
    the smaller run that was reported before: a trace that passes through the old value
    and then flattens shows the larger set is a superset, not a different population.
    """
    fig, ax = plt.subplots(1, 3, figsize=(S.WIDE * 1.25, 2.8))
    band = dict(color=S.GREY, alpha=0.18, lw=0)
    nmax = pv["mismatch"]["summary"]["n_draws"]
    notes = {
        "(a) extraction MC":
            f"shaded: $\\pm 1/\\sqrt{{2(N-1)}}$, the standard\nerror of a sigma "
            f"estimated from N\ndraws (M1) -- $\\pm${100 * MC_SE(nmax):.1f} % at N = {nmax}.  All four\n"
            f"are inside it well before the end.",
        "(b) rejection MC":
            "rejection in dB is the log of a near-\ncancellation, so these tails are "
            "longer\nthan (a)'s and (M1)'s normal assumption\nis a guide, not a bound.  "
            "Here the trace,\nnot the formula, is the evidence.",
    }

    for a, (conv, title, keys) in zip(ax, (
            (pv["mismatch"]["summary"]["convergence"], "(a) extraction MC",
             (("fc_hz", r"$\sigma(f_c)$"), ("Q_lo", r"$\sigma(Q_{lo})$"),
              ("Q_hi", r"$\sigma(Q_{hi})$"), ("offset_in_uv", r"$\sigma$(offset)"))),
            (rj["mismatch"]["convergence"], "(b) rejection MC",
             (("cmrr_db_0.1hz", r"$\sigma$(CMRR@dc)"),
              ("psrr_db_0.1hz", r"$\sigma$(PSRR@dc)"),
              ("offset_in_uv", r"$\sigma$(offset)"))))):
        n = np.asarray(conv[keys[0][0]]["n"], float)
        se = np.asarray(conv[keys[0][0]]["se_frac"], float)
        a.fill_between(n, 1 - se, 1 + se, **band)
        for i, (k, lab) in enumerate(keys):
            v = np.asarray(conv[k]["sigma"], float)
            a.semilogx(conv[k]["n"], v / v[-1], **cy(i, marker="", lw=1.1), label=lab)
        a.axhline(1.0, color=S.GREY, lw=0.7, ls=":")
        a.set_xlabel("draws used, in seed order")
        a.set_ylabel(r"$\sigma(N)\ /\ \sigma(N_{max})$")
        a.set_title(title)
        a.set_ylim(0.4, 1.6)
        a.legend(loc="lower right", fontsize=6.0, ncol=1)
        S.note(a, notes[title], loc="upper right")

    # (c) why the worst case is not a convergent number.
    tr = pv["mismatch"]["summary"]["convergence"]["offset_in_uv"]
    n = tr["n"]
    for i, (k, lab, ls) in enumerate((("max", "max", "-"), ("p99", "p99", "--"),
                                      ("p01", "p01", "--"), ("min", "min", "-"))):
        ax[2].semilogx(n, tr[k], **cy(i % 2, marker="", lw=1.1, ls=ls), label=lab)
    ax[2].set_xlabel("draws used, in seed order")
    ax[2].set_ylabel("input-referred offset (µV)")
    ax[2].set_title("(c) order statistics do not converge")
    ax[2].legend(loc="center right", fontsize=6.0)
    ax[2].margins(y=0.28)
    S.note(ax[2], "min and max walk outward\nwith N by construction:\na longer run MUST "
                  "report a\nworse worst case.  p01/p99\nstay comparable across N.",
           loc="upper left")
    S.save(fig, "mc_convergence")
    plt.close(fig)


def main() -> None:
    tf, nz, la = load("tf.json"), load("noise.json"), load("linearity_analysis.json")
    fig_half_circuit()
    fig_pz(tf)
    fig_bode(tf)
    fig_noise(nz)
    fig_thd(la)
    fig_iip3(la)
    pv = load("pvt.json")
    fig_pvt(pv)
    fig_mc(pv)
    rj = load("psrr_cmrr.json")
    fig_rejection(rj)
    fig_mc_convergence(pv, rj)
    fig_residual(load("gds_residual.json"))
    fig_iip3_corners(load("iip3_corners.json"))
    fig_thd_corners(load("thd_corners.json"))


if __name__ == "__main__":
    main()
