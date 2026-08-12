"""Run a batch of designs concurrently.

The netlist lane parallelises freely: every run has its own work directory and
its own container, and the ledger append is atomic per line.  Use it for sweeps,
corner sets and Monte-Carlo batches.

`LPF_JOBS` caps concurrency (default: CPU count - 2, min 2).  Keep a couple of
cores free -- each ngspice is single-threaded but the container start-up is not.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, Sequence


def jobs() -> int:
    env = os.environ.get("LPF_JOBS")
    if env:
        return max(1, int(env))
    return max(2, (os.cpu_count() or 4) - 2)


def batch(items: Sequence, fn: Callable, *, workers: int | None = None,
          on_error: str = "keep") -> list:
    """Map `fn` over `items` concurrently, preserving input order.

    `on_error='keep'` stores the exception in the result slot (so one broken
    sizing point cannot abort a 200-point sweep); `'raise'` re-raises the first.
    """
    n = workers or jobs()
    out: list = [None] * len(items)
    with ThreadPoolExecutor(max_workers=n) as pool:
        futs = {pool.submit(fn, it): i for i, it in enumerate(items)}
        for f in as_completed(futs):
            i = futs[f]
            try:
                out[i] = f.result()
            except Exception as exc:  # noqa: BLE001
                if on_error == "raise":
                    raise
                out[i] = exc
    return out


def ok(results: Iterable) -> list:
    """Drop the slots that raised."""
    return [r for r in results if not isinstance(r, Exception)]
