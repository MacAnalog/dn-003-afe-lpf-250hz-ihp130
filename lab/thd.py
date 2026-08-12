"""S7: total harmonic distortion, by coherent strobed transient + DFT.

The measurement contract (doc/benches.md), stated once so nobody re-derives it:

* the input is **175 mVpp DIFFERENTIAL**.  The balun makes `vsig`'s own
  amplitude the differential input, so that is `ampl = 87.5 m` -- not 175 m, and
  not 87.5 m per side.
* the spec point is **fin = 50 Hz**.  Higher input frequencies are an
  *informative profile*, not a pass/fail, because a nano-amp-biased follower
  becomes slew-limited well inside the passband and the profile collapses there
  by construction.
* harmonics **2 through 10** are summed for total THD; HD3 is reported
  separately because these differential cells are HD3-dominated (HD2 sits below
  the numerical floor while the differential balance holds -- if HD2 climbs,
  something is asymmetric and the number is telling you about a bug, not a
  distortion mechanism).

Coherence, not windowing, is what makes this trustworthy: the transient is
strobed at an exact integer number of points per input cycle over an exact
integer number of cycles, so the fundamental and every harmonic land exactly on
DFT bins and no window is needed.  A rectangular window on a coherent record has
no leakage; a Hann window on the same record is applied as a cross-check and the
two must agree to a small fraction of a dB.

Expensive by design, so it is GATED: `lab.metrics.gate` refuses to spend a
transient on a design whose cheap scorecard fails the shape box.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config as C
from . import metrics as M
from . import ngspice as ng
from . import raw as R
from .deck import tran_thd
from .dut import Design

HARMONICS = tuple(range(2, 11))


@dataclass
class Thd:
    fin: float
    ampl: float
    thd_db: float          # harmonics 2..10, power sum
    hd3_db: float
    hd2_db: float
    out_vpp: float
    per_harmonic: dict     # {n: dB relative to the fundamental}

    def row(self) -> str:
        return (f"| {self.fin:g} | {self.thd_db:.2f} | {self.hd3_db:.2f} | "
                f"{self.hd2_db:.2f} | {self.out_vpp*1e3:.1f} |")


def measure(design: Design, *, fin: float = M.THD_FIN, ampl: float = M.THD_AMPL,
            cycles: int = 20, settle: int = 8, ppc: int = 512,
            tag: str | None = None, gate: bool = True, **kw) -> Thd:
    """Simulate and score one THD point.

    `gate=False` only to debug the instrument itself -- it bypasses the
    sim-economy rule and will happily spend a long transient on a design whose
    shape is already wrong.
    """
    tag = tag or f"thd_{design.topology}_f{fin:g}_a{ampl*1e3:g}m"
    if gate:
        M.gate(design, f"{tag}_gate")

    deck = tran_thd(design, fin, ampl, cycles=cycles, settle=settle, ppc=ppc, **kw)
    plots = ng.simulate(deck, tag, timeout=3600)
    tr = R.pick(plots, "tran")
    t = np.real(tr.x).astype(float)
    y = np.real(tr.get(C.OUT_P) - tr.get(C.OUT_N)).astype(float)

    n = cycles * ppc
    grid = t[0] + np.arange(n) / (fin * ppc)
    grid = grid[grid <= t[-1]]
    n = (len(grid) // ppc) * ppc
    if n < 4 * ppc:
        raise ng.SimError(f"{tag}: transient too short for a coherent DFT "
                          f"({len(grid)} of {cycles * ppc} points)")
    grid = grid[:n]
    ys = np.interp(grid, t, y)
    cyc = n // ppc

    def mags(win: np.ndarray | None) -> np.ndarray:
        z = ys - ys.mean()
        if win is not None:
            z = z * win
        return np.abs(np.fft.rfft(z)) * (2.0 / n)

    rect = mags(None)
    hann = mags(np.hanning(n))

    f0 = rect[cyc]
    per = {h: 20 * np.log10(max(rect[h * cyc], 1e-300) / max(f0, 1e-300))
           for h in HARMONICS if h * cyc < len(rect)}
    pwr = sum((rect[h * cyc] / f0) ** 2 for h in HARMONICS if h * cyc < len(rect))
    thd_db = 10 * np.log10(max(pwr, 1e-300))

    # cross-check: the windowed estimate must agree, or the record is not coherent
    h3r = per.get(3, float("nan"))
    h3h = 20 * np.log10(max(hann[3 * cyc], 1e-300) / max(hann[cyc], 1e-300))
    if abs(h3r - h3h) > 3.0:
        raise ng.SimError(
            f"{tag}: rect and hann HD3 disagree by {abs(h3r-h3h):.1f} dB "
            f"({h3r:.2f} vs {h3h:.2f}) -- the record is not coherent, so the "
            f"number is leakage, not distortion")

    res = Thd(fin, ampl, float(thd_db), float(per.get(3, float("nan"))),
              float(per.get(2, float("nan"))), float(ys.max() - ys.min()), per)

    from .ledger import log_run
    log_run(tag, {"thd_db": res.thd_db, "hd3_db": res.hd3_db, "hd2_db": res.hd2_db,
                  "fin_hz": fin, "ampl_v": ampl, "out_vpp": res.out_vpp},
            deck=deck, design=design, kind="thd",
            violations=[] if res.thd_db <= M.THD_LIMIT_DB else
            [f"S7 THD @ {fin:g} Hz: {res.thd_db:.2f} dB > {M.THD_LIMIT_DB:g} dB"])
    return res


def profile(design: Design, fins=(20, 50, 100, 150, 200), **kw) -> list[Thd]:
    """The informative profile over input frequency.  Only `fin = 50` is spec."""
    out = []
    for i, f in enumerate(fins):
        out.append(measure(design, fin=f, gate=(i == 0), **kw))
    return out


def table(rows: list[Thd], limit: float = M.THD_LIMIT_DB) -> str:
    head = ("| fin (Hz) | THD h2..h10 (dB) | HD3 (dB) | HD2 (dB) | out (mVpp) |\n"
            "|---|---|---|---|---|")
    body = "\n".join(r.row() for r in rows)
    spec = [r for r in rows if abs(r.fin - M.THD_FIN) < 1e-9]
    note = ""
    if spec:
        s = spec[0]
        note = (f"\n\nS7 spec point (fin = {M.THD_FIN:g} Hz, "
                f"{M.THD_AMPL*2e3:g} mVpp differential): **{s.thd_db:.2f} dB** "
                f"vs {limit:g} dB -> **{'PASS' if s.thd_db <= limit else 'FAIL'}**"
                f" ({limit - s.thd_db:+.2f} dB margin)")
    return head + "\n" + body + note


if __name__ == "__main__":  # python -m lab.thd
    import json
    import sys
    from .dut import Design as _D  # noqa: F401
    print(json.dumps({"usage": "import lab.thd and call measure(design)"},
                     indent=2), file=sys.stderr)
