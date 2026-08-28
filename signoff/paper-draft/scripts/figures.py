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


def main() -> None:
    tf, nz, la = load("tf.json"), load("noise.json"), load("linearity_analysis.json")
    fig_half_circuit()
    fig_pz(tf)
    fig_bode(tf)
    fig_noise(nz)
    fig_thd(la)
    fig_iip3(la)


if __name__ == "__main__":
    main()
