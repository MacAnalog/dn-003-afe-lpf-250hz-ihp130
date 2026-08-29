#!/usr/bin/env python
"""Has the Monte Carlo converged?  -- answered with a number instead of a feeling.

A sigma estimated from N draws is itself an estimate, and it carries its own error bar.
For a normal population the sample standard deviation has relative standard error

    SE(sigma) / sigma = 1 / sqrt(2 (N - 1))                                        (M1)

-- 8.9 % at N = 64, 4.4 % at N = 256, 2.2 % at N = 1024.  (M1) is what "converged"
means operationally: it is the width a running-sigma trace is allowed to wander in, and
quoting it next to every sigma turns "looks converged" into a claim a reader can check.
The trace and the band are computed here; `figures.py` plots them and `report.py`
quotes the final value.

TWO WARNINGS about what does NOT converge.

*   **min and max are order statistics.**  They move monotonically outward as N grows,
    by construction -- a longer run MUST report a worse worst case, and a worst case
    that got worse is therefore not evidence of anything.  Fixed quantiles (p01, p99)
    are the extremes that stay comparable across N, and at N = 1024 the 1 % tail
    finally has ~10 samples under it.
*   **(M1) assumes normality.**  It is a good guide for `fc` and `Q`, which are smooth
    functions of many small independent device shifts, and a rough one for rejection in
    dB, which is a log of a near-cancellation and has a long tail.  Where it matters the
    trace itself is the evidence: a sigma that still drifts outside its band at large N
    has not converged whatever (M1) says.
"""
from __future__ import annotations

import math

import numpy as np

def ladder(n: int, n_min: int = 8, per_octave: int = 8) -> list[int]:
    """Where the running trace is sampled: geometric, so early N (where the estimate
    moves) is resolved and late N (where it should not) is not oversampled."""
    if n < n_min:
        return [n]
    k = max(1, int(round(per_octave * math.log2(n / n_min))))
    xs = set(np.round(np.geomspace(n_min, n, k + 1)).astype(int).tolist())
    # Every power of two is a rung, so a run that extends an earlier one lands exactly
    # on the earlier N: the trace then reads through the published value rather than
    # near it, which is what makes "the old run is the first rows of this one" checkable.
    xs |= {1 << i for i in range(3, n.bit_length()) if n_min <= (1 << i) <= n}
    xs.add(int(n))
    return sorted(int(x) for x in xs)


def se_frac(n: int) -> float:
    """(M1): the relative standard error of a sigma estimated from `n` draws."""
    return float("inf") if n < 2 else 1.0 / math.sqrt(2.0 * (n - 1))


def trace(v, n_min: int = 8, per_octave: int = 8) -> dict:
    """Running mean and sigma over the first n draws, for n on a geometric ladder.

    The draws are used in seed order, never shuffled: seeds are `1..N`, so the first 64
    rows of a 1024-draw run ARE the 64-draw run, and the trace passing through the old
    value at n = 64 is the proof that the larger set is a superset rather than a
    different population.
    """
    v = np.asarray(v, float)
    ns = ladder(int(v.size), n_min, per_octave)
    out = {
        "n": ns,
        "mean": [float(v[:n].mean()) for n in ns],
        "sigma": [float(v[:n].std(ddof=1)) for n in ns],
        "se_frac": [se_frac(n) for n in ns],
        "min": [float(v[:n].min()) for n in ns],
        "max": [float(v[:n].max()) for n in ns],
        "p01": [float(np.percentile(v[:n], 1)) for n in ns],
        "p99": [float(np.percentile(v[:n], 99)) for n in ns],
    }
    # Carried in the record so a stdlib-only reader (`report.py`) can quote it.
    out["drift_pct"] = drift_pct(out)
    return out


def drift_pct(tr: dict, since: int = 4) -> float:
    """|sigma(N) / sigma(N/2^k) - 1| over the last `since` rungs, in per cent.

    The empirical companion to (M1): how much the estimate actually moved over the last
    part of the run, against how much (M1) says it is allowed to move.
    """
    s = tr["sigma"]
    if len(s) <= since or s[-1] == 0:
        return float("nan")
    return 100.0 * abs(s[-1] / s[-1 - since] - 1.0)


def annotate(stat: dict) -> dict:
    """Add (M1) to a stat dict in place, as a fraction and as an absolute sigma."""
    n = int(stat.get("n", 0))
    stat["se_sigma_frac"] = se_frac(n)
    stat["se_sigma"] = stat["sigma"] * se_frac(n) if n >= 2 else float("nan")
    return stat
