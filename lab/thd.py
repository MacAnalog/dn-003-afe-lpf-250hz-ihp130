"""S7: total harmonic distortion, by coherent strobed transient + DFT.

The measurement contract (doc/benches.md), stated once so nobody re-derives it:

* the level is **175 mVpp differential at the INPUT** -- the originating
  campaign's definition verbatim.  The balun makes `vsig`'s own amplitude the
  differential input, so that is `ampl = 87.5 m`: not 175 m, and not 87.5 m per
  side.  This is the default and it is what S7 means.
* a reporting option, NOT the spec: `measure(target_out_vpp=...)` servoes the
  drive until the OUTPUT fundamental hits a common level.  It exists because
  these cells do not have unity large-signal gain -- measured -0.63 dB to
  +0.86 dB at the spec level, and one variant put out 213 mVpp for a 175 mVpp
  drive -- so a fixed input tests different cells at different output swings.
  Quoting both numbers separates "this cell distorts more" from "this cell was
  driven harder".
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
two must agree, or the record is not coherent and the number is leakage.

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
    ampl: float            # the differential drive AMPLITUDE that was needed
    thd_db: float          # harmonics 2..10, power sum
    hd3_db: float
    hd2_db: float
    out_vpp: float         # peak-to-peak of the actual waveform
    out_fund_vpp: float    # peak-to-peak of the FUNDAMENTAL -- what is servoed
    per_harmonic: dict     # {n: dB relative to the fundamental}

    def row(self) -> str:
        return (f"| {self.fin:g} | {self.thd_db:.2f} | {self.hd3_db:.2f} | "
                f"{self.hd2_db:.2f} | {self.out_fund_vpp * 1e3:.1f} | "
                f"{self.ampl * 2e3:.1f} |")


def _score(plots, fin, ampl, cycles, ppc, tag) -> Thd:
    """Coherent DFT of one transient record."""
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
    ys = np.interp(grid[:n], t, y)
    cyc = n // ppc

    z = ys - ys.mean()
    rect = np.abs(np.fft.rfft(z)) * (2.0 / n)
    hann = np.abs(np.fft.rfft(z * np.hanning(n))) * (2.0 / n)

    f0 = rect[cyc]
    per = {h: 20 * np.log10(max(rect[h * cyc], 1e-300) / max(f0, 1e-300))
           for h in HARMONICS if h * cyc < len(rect)}
    pwr = sum((rect[h * cyc] / f0) ** 2 for h in HARMONICS if h * cyc < len(rect))

    h3r = per.get(3, float("nan"))
    h3h = 20 * np.log10(max(hann[3 * cyc], 1e-300) / max(hann[cyc], 1e-300))
    if abs(h3r - h3h) > 3.0:
        raise ng.SimError(
            f"{tag}: rect and hann HD3 disagree by {abs(h3r - h3h):.1f} dB "
            f"({h3r:.2f} vs {h3h:.2f}) -- the record is not coherent, so the "
            f"number is leakage, not distortion")

    return Thd(fin, ampl, float(10 * np.log10(max(pwr, 1e-300))),
               float(per.get(3, float("nan"))), float(per.get(2, float("nan"))),
               float(ys.max() - ys.min()), float(f0 * 2.0), per)


def _run_point(design: Design, fin, ampl, cycles, settle, ppc, tag, **kw) -> Thd:
    """One transient at a fixed drive -- the inner step of the amplitude servo."""
    deck = tran_thd(design, fin, ampl, cycles=cycles, settle=settle, ppc=ppc, **kw)
    plots = ng.simulate(deck, tag, timeout=3600)
    return _score(plots, fin, ampl, cycles, ppc, tag)


def measure(design: Design, *, fin: float = M.THD_FIN, ampl: float | None = None,
            target_out_vpp: float | None = None, tol: float = 0.01,
            max_iter: int = 5, cycles: int = 20, settle: int = 8, ppc: int = 512,
            tag: str | None = None, gate: bool = True, **kw) -> Thd:
    """Simulate and score one THD point, servoed to the OUTPUT level.

    `target_out_vpp` defaults to the spec level (`lab.metrics.THD_OUT_VPP`).
    Pass an explicit `ampl` with `target_out_vpp=None` to drive open loop, which
    is only meaningful when comparing a cell against itself.

    `gate=False` only to debug the instrument itself -- it bypasses the
    sim-economy rule and will spend a long transient on a broken shape.
    """
    if ampl is None:
        ampl = M.THD_AMPL
    tag = tag or f"thd_{design.topology}_f{fin:g}"
    if gate:
        M.gate(design, f"{tag}_gate")

    hist: list[tuple[float, float]] = []
    res: Thd | None = None
    if target_out_vpp:
        for it in range(max_iter):
            got = _run_point(design, fin, ampl, cycles, settle, ppc,
                             f"{tag}_amp{it}", **kw)
            hist.append((ampl, got.out_fund_vpp))
            err = got.out_fund_vpp / target_out_vpp - 1.0
            if abs(err) <= tol:
                res = got
                break
            # near-linear at these levels, so one proportional step lands within
            # a percent; the loop still iterates in case it does not.
            ampl = ampl / (1.0 + err)
        if res is None:
            res = _run_point(design, fin, ampl, cycles, settle, ppc,
                             f"{tag}_final", **kw)
    else:
        res = _run_point(design, fin, ampl, cycles, settle, ppc, tag, **kw)

    from .ledger import log_run
    log_run(tag, {"thd_db": res.thd_db, "hd3_db": res.hd3_db,
                  "hd2_db": res.hd2_db, "fin_hz": fin, "ampl_v": res.ampl,
                  "out_vpp": res.out_vpp, "out_fund_vpp": res.out_fund_vpp,
                  "servo_iters": len(hist)},
            design=design, kind="thd",
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
    head = ("| fin (Hz) | THD h2..h10 (dB) | HD3 (dB) | HD2 (dB) | "
            "out fund (mVpp) | drive (mVpp) |\n|---|---|---|---|---|---|")
    body = "\n".join(r.row() for r in rows)
    spec = [r for r in rows if abs(r.fin - M.THD_FIN) < 1e-9]
    note = ""
    if spec:
        s = spec[0]
        note = (f"\n\nS7 spec point (fin = {M.THD_FIN:g} Hz, "
                f"{M.THD_OUT_VPP * 1e3:g} mVpp differential AT THE OUTPUT): "
                f"**{s.thd_db:.2f} dB** vs {limit:g} dB -> "
                f"**{'PASS' if s.thd_db <= limit else 'FAIL'}**"
                f" ({limit - s.thd_db:+.2f} dB margin)")
    return head + "\n" + body + note
