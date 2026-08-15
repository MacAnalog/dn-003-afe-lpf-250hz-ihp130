"""Mismatch Monte Carlo: how much of the spec box survives local variation.

The PDK carries the mismatch model; this module only *drives* it.  Selecting
``<corner>_mismatch`` instead of ``<corner>`` (see `lab.config.mismatch_corner`)
makes every device instance draw its own `delvto`, `factuo`, `dw` and `dl` from
the PDK's own agauss expressions.  Nothing here invents a sigma.

Three facts about ngspice shape the whole design of this module.

1.  **The draws happen at netlist-parse time.**  `set rndseed=<n>` inside a
    `.control` block runs *after* the devices already exist, so it changes
    nothing: measured, seeds 1/2/3 on a two-device probe all returned the
    identical pair 1.340305 nA / 1.515478 nA.  The seed has to be a netlist
    directive -- `.option seed=<n>` (`lab.config.seed_directive`), which does
    move the sample (1.360461/1.433172, 1.391129/1.371615, 1.478674/1.498904 nA
    for seeds 1/2/3) and is reproducible for a repeated seed.
2.  **One process per sample.**  An in-ngspice `repeat`/`while` loop with
    `reset` renumbers the analysis plots, so the `setplot noise1` that the
    ac+noise deck depends on silently addresses the wrong plot and S5 comes back
    as another copy of the ac sweep.  See doc/journal/ngspice-write-protocol.md.
3.  **A sample that did not converge is not a sample.**  ngspice returns 0 after
    a failed operating point, and a scorecard built on that rawfile is a number,
    not an error.  Every non-converged or non-finite sample is counted, named,
    reported on its own line, and is NEVER in the pass numerator.  The yield
    denominator is the number of samples ATTEMPTED, so dropping a bad sample can
    only ever lower the reported yield, not raise it.

The headline number is the **all-pass yield**: the fraction of attempted samples
that pass *every* spec line at once.  The per-line yields are diagnostics that
explain it; they do not multiply into it (the lines are strongly correlated).

For this follower family the mismatch figure of merit is **sigma(dc_db)**.  A
source follower's passband gain is self-referenced -- it is set by one device's
gm against its own load -- so a threshold shift moves the operating point and
barely moves the gain.  A topology that loses that property shows it here first,
as a sigma(dc_db) that is no longer a small fraction of the 0.2 dB S3 box, long
before anything visible happens to fc.

    from lab.mc import run, table, histogram
    r = run(design, "mc_ref", n=64)
    print(table(r)); histogram(r, "mc_ref.png")
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import config as C
from . import metrics as M
from . import ngspice as ng
from .deck import ac_noise
from .dut import Design
from .parallel import batch, jobs

# Docker contention: each sample is its own container, and past ~6 concurrent
# containers the wall time per sample grows faster than the batch shrinks.
WORKERS = 6 if C.lane() == "docker" else max(6, jobs())

# The columns whose distribution is reported.  sigma(dc_db) first -- see the
# module docstring.
STAT_KEYS = ("dc_db", "fc_hz", "ripple_db", "irn_uv", "p_core_nw",
             "gd_dc_ms", "gd_max_ms")

_STAT_FMT = {"dc_db": "{:+.5f}", "fc_hz": "{:.3f}", "ripple_db": "{:.4f}",
             "irn_uv": "{:.3f}", "p_core_nw": "{:.3f}",
             "gd_dc_ms": "{:.4f}", "gd_max_ms": "{:.4f}"}


# --------------------------------------------------------------- one sample --

@dataclass
class Sample:
    """One seed's worth of result -- or the reason there isn't one."""

    seed: int
    score: M.Score | None = None
    error: str = ""          # non-empty => the simulation itself failed

    @property
    def usable(self) -> bool:
        """A real measurement: it ran, and every spec line has a finite value.

        A NaN spec column is treated exactly like a failed run.  `M.check`
        would call it 'NOT MEASURED' and count it as a violation, which is
        honest for a scorecard but wrong for a yield: it would put a hole in the
        statistics and pretend the sample was measured and lost.
        """
        if self.score is None:
            return False
        for key in M.SPEC:
            v = self.score.values.get(key)
            if v is None or (isinstance(v, float) and not math.isfinite(v)):
                return False
        return True

    @property
    def ok(self) -> bool:
        """Passes every spec line.  A non-usable sample is never ok."""
        return self.usable and self.score.ok

    @property
    def values(self) -> dict:
        return self.score.values if self.score is not None else {}

    @property
    def violations(self) -> list[str]:
        return list(self.score.violations) if self.score is not None else []

    @property
    def why(self) -> str:
        """Why this sample is not usable ('' if it is)."""
        if self.error:
            return f"sim error: {self.error.splitlines()[0][:120]}"
        if self.score is None:
            return "no result"
        if not self.usable:
            bad = [k for k in M.SPEC
                   if not isinstance(self.score.values.get(k), (int, float))
                   or not math.isfinite(float(self.score.values.get(k, float("nan"))))]
            return "non-finite metric: " + ", ".join(bad)
        return ""


def sample(design: Design, seed: int, *, corner: str = C.CORNER_MM_NOM,
           temp: float = C.TEMP_NOM, tag: str | None = None,
           record: bool = False, **kw) -> M.Score:
    """Simulate ONE mismatch draw and score it.

    `corner` defaults to the nominal mismatch section; any `<corner>_mismatch`
    works, and a plain corner is upgraded to its mismatch twin rather than
    silently producing n identical copies of the nominal point.

    Raises `lab.ngspice.SimError` if the draw does not converge -- the caller
    (`run`) counts those; nothing here swallows one.
    """
    corner = C.mismatch_corner(corner)
    tag = tag or f"mc_{design.topology}_s{int(seed):05d}"
    deck = _seeded(ac_noise(design, corner=corner, temp=temp, **kw), seed)
    rundir = ng.run(deck, tag)
    s = M.score_plots(ng.plots(rundir), design)
    s.values["seed"] = int(seed)
    if record:
        from .ledger import log_run
        log_run(tag, s.values, deck=deck, design=design, corner=corner,
                temp=temp, wall=ng.wall_time(rundir), violations=s.violations,
                kind="mc_sample")
    return s


def _seeded(deck: str, seed: int) -> str:
    """Put `.option seed=<n>` in the netlist, ahead of every device line.

    Second line of the deck, straight after `.title`: the agauss draws are made
    as the instances are parsed, so a seed that arrives later (a `.control`
    `set rndseed`, or a directive below the devices) is a no-op that looks like
    it worked.
    """
    lines = deck.splitlines()
    head = 1 if lines and lines[0].lstrip().lower().startswith(".title") else 0
    return "\n".join(lines[:head] + [C.seed_directive(seed)] + lines[head:]) + "\n"


# ------------------------------------------------------------- the campaign --

@dataclass
class McResult:
    tag: str
    design: Design
    corner: str
    samples: list[Sample]
    temp: float = C.TEMP_NOM
    seed0: int = 1
    wall_s: float = float("nan")
    meta: dict = field(default_factory=dict)

    # -- denominators ------------------------------------------------------
    @property
    def n(self) -> int:
        """Samples ATTEMPTED.  This is the yield denominator, always."""
        return len(self.samples)

    @property
    def usable(self) -> list[Sample]:
        return [s for s in self.samples if s.usable]

    @property
    def failed(self) -> list[Sample]:
        """Non-converged / non-finite samples -- reported, never passes."""
        return [s for s in self.samples if not s.usable]

    @property
    def n_failed(self) -> int:
        return len(self.failed)

    # -- yields -------------------------------------------------------------
    @property
    def passes(self) -> list[Sample]:
        return [s for s in self.samples if s.ok]

    @property
    def n_pass(self) -> int:
        return len(self.passes)

    @property
    def all_pass_yield(self) -> float:
        """THE headline: every spec line met at once, over samples attempted."""
        return self.n_pass / self.n if self.n else float("nan")

    def line_pass(self, key: str) -> int:
        """How many attempted samples meet ONE spec line."""
        label = M.SPEC[key][0]
        return sum(1 for s in self.samples
                   if s.usable and not any(v.startswith(label) for v in s.violations))

    def line_yield(self, key: str) -> float:
        return self.line_pass(key) / self.n if self.n else float("nan")

    # -- statistics ---------------------------------------------------------
    def column(self, key: str) -> np.ndarray:
        """One metric across the USABLE samples (never padded with zeros)."""
        return np.array([float(s.values[key]) for s in self.usable
                         if isinstance(s.values.get(key), (int, float))], dtype=float)

    def stats(self, key: str) -> dict:
        x = self.column(key)
        if x.size == 0:
            return {"n": 0, "mean": float("nan"), "sigma": float("nan"),
                    "min": float("nan"), "max": float("nan")}
        return {"n": int(x.size), "mean": float(x.mean()),
                "sigma": float(x.std(ddof=1)) if x.size > 1 else 0.0,
                "min": float(x.min()), "max": float(x.max())}

    @property
    def sigma_dc_db(self) -> float:
        """The mismatch figure of merit for the follower family."""
        return self.stats("dc_db")["sigma"]

    def worst(self, k: int = 5) -> list[Sample]:
        """The k samples furthest outside the box, non-converged ones first."""
        return sorted(self.samples, key=lambda s: -_excess(s)[0])[:k]

    def summary(self) -> dict:
        """Flat dict -- what goes in the ledger and in a scorecard."""
        out = {"n": self.n, "n_pass": self.n_pass, "n_failed": self.n_failed,
               "all_pass_yield": round(self.all_pass_yield, 6),
               "corner": self.corner, "seed0": self.seed0}
        for k in M.SPEC:
            out[f"yield_{k}"] = round(self.line_yield(k), 6)
        for k in STAT_KEYS:
            st = self.stats(k)
            out[f"{k}_mean"] = st["mean"]
            out[f"{k}_sigma"] = st["sigma"]
            out[f"{k}_min"] = st["min"]
            out[f"{k}_max"] = st["max"]
        return out


def _excess(s: Sample) -> tuple[float, str]:
    """(how far outside the box, which line) -- the worst-sample ordering.

    Normalised so lines with different units compare: the violation divided by
    the size of the bound (half-width for an interval).  A non-converged sample
    sorts above every converged one.
    """
    if not s.usable:
        return (float("inf"), s.why)
    worst, who = 0.0, ""
    for key, (label, op, bound) in M.SPEC.items():
        v = float(s.values[key])
        if op == ">=":
            e = (bound - v) / abs(bound)
        elif op in ("<=", "<"):
            e = (v - bound) / abs(bound)
        elif op == "abs<=":
            e = (abs(v) - bound) / bound
        elif op == "in":
            lo, hi = bound
            e = max(lo - v, v - hi) / ((hi - lo) / 2)
        else:                                   # pragma: no cover - guard
            continue
        if e > worst:
            worst, who = e, label
    return (worst, who)


def run(design: Design, tag: str, *, n: int = 64, workers: int = WORKERS,
        seed0: int = 1, corner: str = C.CORNER_MM_NOM, temp: float = C.TEMP_NOM,
        record: bool = True, **kw) -> McResult:
    """`n` independent mismatch draws of `design`, one ngspice process each.

    Seeds are `seed0 .. seed0+n-1`, so a campaign is reproducible and two
    campaigns on different designs see the SAME draws of the random stream --
    which makes a design-to-design yield comparison paired rather than noisy.

    A draw that fails to converge lands in the result as a failed `Sample`; it is
    reported and it never counts as a pass.
    """
    import time

    corner = C.mismatch_corner(corner)
    seeds = list(range(seed0, seed0 + int(n)))
    t0 = time.time()

    def one(seed: int):
        return sample(design, seed, corner=corner, temp=temp,
                      tag=f"{tag}_s{seed:05d}", record=False, **kw)

    raw = batch(seeds, one, workers=workers, on_error="keep")
    samples = [Sample(seed=sd, score=r) if isinstance(r, M.Score)
               else Sample(seed=sd, error=str(r))
               for sd, r in zip(seeds, raw)]
    res = McResult(tag=tag, design=design, corner=corner, samples=samples,
                   temp=temp, seed0=seed0, wall_s=time.time() - t0)
    if record:
        from .ledger import log_run
        log_run(tag, res.summary(), deck=_seeded(ac_noise(design, corner=corner,
                                                          temp=temp, **kw), seed0),
                design=design, corner=corner, temp=temp, wall=res.wall_s,
                violations=[] if res.n_pass == res.n else
                [f"mismatch yield {res.n_pass}/{res.n}"],
                kind="mc", extra={"seeds": [seeds[0], seeds[-1]] if seeds else [],
                                  "n_failed": res.n_failed,
                                  "deck_note": "hash is the seed0 sample's deck; "
                                               "the other samples differ only in "
                                               ".option seed"})
    return res


# ------------------------------------------------------------------ output ---

def table(r: McResult) -> str:
    """Yield table + statistics table + the five worst samples."""
    out = [f"### Mismatch Monte Carlo — `{r.tag}` ({r.design.topology}), "
           f"corner `{r.corner}`, T = {r.temp:g} °C",
           "",
           f"**{r.n_pass} of {r.n} samples pass every spec line — "
           f"ALL-PASS YIELD = {100 * r.all_pass_yield:.1f} % "
           f"(denominator: {r.n} samples attempted, seeds "
           f"{r.seed0}–{r.seed0 + r.n - 1}).**",
           "",
           f"Non-converged / non-finite samples: **{r.n_failed}** "
           f"({100 * r.n_failed / r.n if r.n else float('nan'):.1f} % of "
           f"attempted) — counted as failures, never as passes. "
           f"Statistics below are over the {len(r.usable)} usable samples; "
           f"yields are over all {r.n} attempted.",
           f"Wall time {r.wall_s:.1f} s.", "",
           "| spec line | bound | pass | yield |", "|---|---|---|---|"]
    for key, (label, op, bound) in M.SPEC.items():
        b = (f"{bound[0]:g}..{bound[1]:g}" if op == "in"
             else f"{op} {bound:g}" if op != "abs<=" else f"|·| <= {bound:g}")
        out.append(f"| {label} | {b} | {r.line_pass(key)}/{r.n} | "
                   f"{100 * r.line_yield(key):.1f} % |")
    out.append(f"| **ALL LINES** | — | **{r.n_pass}/{r.n}** | "
               f"**{100 * r.all_pass_yield:.1f} %** |")

    out += ["", "| quantity | mean | sigma | min | max | n |", "|---|---|---|---|---|---|"]
    for key in STAT_KEYS:
        st = r.stats(key)
        f = _STAT_FMT.get(key, "{:.4g}").format
        out.append(f"| {key} | {f(st['mean'])} | {f(st['sigma'])} | "
                   f"{f(st['min'])} | {f(st['max'])} | {st['n']} |")
    out.append("")
    sd, box = r.sigma_dc_db, M.SPEC["dc_db"][2]
    if math.isfinite(sd) and sd > 0:
        out.append(f"Mismatch figure of merit: **sigma(dc_db) = {sd:.5f} dB** "
                   f"against the S3 box of {box:g} dB — {box / sd:.1f} sigma of "
                   f"headroom.")
    else:
        out.append("Mismatch figure of merit: sigma(dc_db) NOT MEASURED.")

    out += ["", "**Worst 5 samples**", "",
            "| seed | worst line | fc_hz | dc_db | ripple_db | irn_uv | p_core_nw |",
            "|---|---|---|---|---|---|---|"]
    for s in r.worst(5):
        e, who = _excess(s)
        if not s.usable:
            out.append(f"| {s.seed} | NON-CONVERGED — {s.why} | – | – | – | – | – |")
            continue
        v = s.values
        line = who if who else "(passes)"
        out.append(f"| {s.seed} | {line} | {v['fc_hz']:.2f} | {v['dc_db']:+.4f} | "
                   f"{v['ripple_db']:.4f} | {v['irn_uv']:.2f} | "
                   f"{v['p_core_nw']:.2f} |")
    return "\n".join(out)


def histogram(r: McResult, path="mc_hist.png", *, title: str | None = None):
    """Distributions of dc_db, fc_hz and irn_uv with the spec limits drawn."""
    from . import plot as P     # matplotlib Agg + FIGS live there
    import matplotlib.pyplot as plt

    panels = (
        ("dc_db", "passband gain (dB)", (-M.SPEC["dc_db"][2], M.SPEC["dc_db"][2]),
         "S3: |dc| ≤ 0.2 dB"),
        ("fc_hz", "cutoff (Hz)", M.SPEC["fc_hz"][2], "S2: 245–255 Hz"),
        ("irn_uv", "IRN 0.5–200 Hz (µVrms)", (None, M.SPEC["irn_uv"][2]),
         "S5: < 40 µVrms"),
    )
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.6))
    for ax, (key, xlabel, limits, lab) in zip(axes, panels):
        x = r.column(key)
        st = r.stats(key)
        if x.size:
            ax.hist(x, bins=max(8, min(24, x.size // 3)), color="#1f77b4",
                    alpha=0.8, edgecolor="white", linewidth=0.5)
            ax.axvline(st["mean"], color="#444444", ls="-", lw=1.2)
            for k in (-1, 1):
                ax.axvline(st["mean"] + k * st["sigma"], color="#444444",
                           ls=":", lw=1.0)
        for lim in limits:
            if lim is not None:
                ax.axvline(lim, color="#d62728", ls="--", lw=1.4)
        ax.annotate(lab, (0.5, 0.97), xycoords="axes fraction", ha="center",
                    va="top", fontsize=8, color="#d62728")
        P._style(ax, xlabel, "samples",
                 f"μ = {st['mean']:.4g}, σ = {st['sigma']:.4g}  (n = {st['n']})")
    fig.suptitle(title or
                 f"Mismatch Monte Carlo — {r.tag} ({r.design.topology}), "
                 f"{r.n_pass}/{r.n} all-pass, {r.n_failed} non-converged",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return P._save(fig, path)


# --------------------------------------------------------------------- cli ---

def _load(path: str) -> Design:
    """Reuse experiments/020-novel-topologies/certify.py's frozen-JSON loader."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_certify", C.REPO / "experiments" / "020-novel-topologies" / "certify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load(Path(path))


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="mismatch Monte Carlo")
    ap.add_argument("design", help="path to a frozen design JSON")
    ap.add_argument("--tag", default=None)
    ap.add_argument("-n", type=int, default=32)
    ap.add_argument("--seed0", type=int, default=1)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--corner", default=C.CORNER_MM_NOM)
    ap.add_argument("--fig", default=None, help="write a histogram png")
    a = ap.parse_args(argv)

    d = _load(a.design)
    tag = a.tag or f"mc_{Path(a.design).stem}"
    r = run(d, tag, n=a.n, workers=a.workers, seed0=a.seed0, corner=a.corner)
    print(table(r))
    if a.fig:
        print("\nfigure ->", histogram(r, a.fig))
    return 0


if __name__ == "__main__":       # `python -m lab.mc decks/reference/design.json`
    raise SystemExit(main())
