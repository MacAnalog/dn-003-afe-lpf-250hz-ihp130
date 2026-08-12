"""Figures.  A finding is a table or a plot; prose is interpretation only.

Every function here takes SIMULATED data and writes a png, so a figure in a
scorecard can always be regenerated from the ledger's deck hash.  Nothing is
drawn by hand and nothing is drawn from a number typed into a doc.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")           # headless: these run in CI and in containers
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

from . import config as C        # noqa: E402
from . import metrics as M       # noqa: E402
from . import ngspice as ng      # noqa: E402
from . import raw as R           # noqa: E402
from .deck import ac_noise       # noqa: E402
from .dut import Design          # noqa: E402

FIGS = C.REPO / "figs"
_COLORS = ("#444444", "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e")


def _style(ax, xlabel, ylabel, title=None):
    ax.grid(True, which="both", alpha=0.25, linewidth=0.6)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, fontsize=10)
    ax.tick_params(labelsize=9)


def _curves(designs: dict[str, Design], tag: str):
    """Simulate each design once; return {name: (f, H, fn, inz)}."""
    out = {}
    for i, (name, d) in enumerate(designs.items()):
        pl = ng.simulate(ac_noise(d), f"{tag}_fig{i}")
        ac = R.pick(pl, "ac")
        f, h = R.diff_tf(ac, C.OUT_P, C.OUT_N)
        try:
            no = R.pick(pl, "noise")
            fn = np.real(no.x).astype(float)
            inz = np.abs(no.get("inoise_spectrum"))
        except KeyError:
            fn, inz = None, None
        out[name] = (f, h, fn, inz)
    return out


def bode(designs: dict[str, Design], path="bode.png", *, tag="bode",
         title="Magnitude and phase, differential"):
    """Magnitude + unwrapped phase lag, with the spec boxes drawn on."""
    data = _curves(designs, tag)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
    for i, (name, (f, h, _, _)) in enumerate(data.items()):
        y = R.db_rel_dc(h)
        a1.semilogx(f, y, color=_COLORS[i % len(_COLORS)], lw=1.6, label=name)
        m = y >= M.PH_FLOOR_DB
        ph = np.unwrap(np.angle(h[m])) * 180 / np.pi
        a2.semilogx(f[m], -(ph - ph[0]), color=_COLORS[i % len(_COLORS)], lw=1.6)

    a1.axvline(250, color="0.6", ls=":", lw=1)
    a1.axhline(-3, color="0.6", ls=":", lw=1)
    a1.plot([1000], [-48], marker="_", ms=14, color="#d62728")
    a1.annotate("S1c: ≤ −48 dB @ 1 kHz", (1000, -48), textcoords="offset points",
                xytext=(-6, 10), ha="right", fontsize=8, color="#d62728")
    a1.set_ylim(-110, 8)
    _style(a1, "", "|H| rel. dc (dB)", title)
    a1.legend(fontsize=8, loc="lower left")

    a2.axhline(330, color="#d62728", ls="--", lw=1)
    a2.annotate("S1: ≥ 330° certificate", (0.2, 336), fontsize=8, color="#d62728")
    _style(a2, "frequency (Hz)", "unwrapped phase lag (deg)")
    fig.tight_layout()
    return _save(fig, path)


def noise(designs: dict[str, Design], path="noise.png", *, tag="noise",
          title="Input-referred noise density (differential)"):
    """Input-referred density with the S5 integration band shaded."""
    data = _curves(designs, tag)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    lo, hi = M.IRN_BAND
    ax.axvspan(lo, hi, color="#1f77b4", alpha=0.07)
    ax.annotate(f"S5 band {lo:g}–{hi:g} Hz", (lo * 1.3, 1.5e-6), fontsize=8,
                color="#1f77b4")
    for i, (name, (_, _, fn, inz)) in enumerate(data.items()):
        if fn is None:
            continue
        rms = R.integrate_noise(fn, inz, lo, hi) * 1e6
        ax.loglog(fn, inz * 1e9, color=_COLORS[i % len(_COLORS)], lw=1.6,
                  label=f"{name} — {rms:.2f} µVrms in band")
    _style(ax, "frequency (Hz)", "input-referred noise (nV/√Hz)", title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, path)


def bars(values: dict[str, float], path="bars.png", *, ylabel="", title="",
         limit: float | None = None, limit_label="spec"):
    """One bar per cell -- the comparison a reader should be able to read at a glance."""
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    names = list(values)
    vals = [values[n] for n in names]
    cols = [_COLORS[i % len(_COLORS)] for i in range(len(names))]
    ax.bar(names, vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax.annotate(f"{v:.2f}", (i, v), ha="center", va="bottom", fontsize=9)
    if limit is not None:
        ax.axhline(limit, color="#d62728", ls="--", lw=1.2)
        ax.annotate(limit_label, (len(names) - 0.5, limit), fontsize=8,
                    color="#d62728", va="bottom", ha="right")
    ax.set_ylim(0, max(vals + ([limit] if limit else [])) * 1.25)
    _style(ax, "", ylabel, title)
    fig.tight_layout()
    return _save(fig, path)


def tradeoff(points: list[dict], path="tradeoff.png", *, x="c_total_pf",
             y="irn_uv", label="wk", title="Noise / capacitance trade"):
    """Scatter of a sizing sweep -- what a design choice actually costs."""
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    xs = [p[x] for p in points]
    ys = [p[y] for p in points]
    ok = [p.get("thd") is not None and p["thd"] <= M.THD_LIMIT_DB for p in points]
    ax.scatter([v for v, k in zip(xs, ok) if k], [v for v, k in zip(ys, ok) if k],
               c="#2ca02c", s=54, label="S7 PASS", zorder=3)
    ax.scatter([v for v, k in zip(xs, ok) if not k],
               [v for v, k in zip(ys, ok) if not k],
               c="#d62728", s=54, marker="x", label="S7 FAIL", zorder=3)
    for p in points:
        ax.annotate(str(p.get(label, "")), (p[x], p[y]), fontsize=7,
                    textcoords="offset points", xytext=(5, 4))
    ax.axhline(40, color="#d62728", ls="--", lw=1.2)
    ax.annotate("S5: < 40 µVrms", (max(xs), 40), fontsize=8, color="#d62728",
                va="bottom", ha="right")
    _style(ax, "total drawn capacitance (pF)", "IRN 0.5–200 Hz (µVrms)", title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, path)


def thd_spectrum(fin: float, per_harmonic: dict, path="thd.png", *,
                 title="Harmonic spectrum at the S7 point"):
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    hs = sorted(per_harmonic)
    ax.bar([str(h) for h in hs], [per_harmonic[h] for h in hs], color="#1f77b4",
           width=0.6)
    ax.axhline(M.THD_LIMIT_DB, color="#d62728", ls="--", lw=1.2)
    ax.annotate("S7: ≤ −40 dB", (len(hs) - 0.5, M.THD_LIMIT_DB), fontsize=8,
                color="#d62728", va="bottom", ha="right")
    for h in hs:
        ax.annotate(f"{per_harmonic[h]:.0f}", (str(h), per_harmonic[h]),
                    ha="center", va="top", fontsize=7)
    _style(ax, f"harmonic of {fin:g} Hz", "dB rel. fundamental", title)
    fig.tight_layout()
    return _save(fig, path)


def _save(fig, path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        FIGS.mkdir(parents=True, exist_ok=True)
        p = FIGS / p
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=150, facecolor="white")
    plt.close(fig)
    return p
