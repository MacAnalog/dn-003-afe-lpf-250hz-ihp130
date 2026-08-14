"""Restore fc after the layout-legal projection moved it.

`lab.grid.legalize` preserves DRAWN W/L when it bumps a sub-minimum width, but
PSP's effective-geometry corrections (dW, dL) do not scale with the drawing, so
a large bump shifts the device's effective W/L and with it the reuse ladder's
branch current.  Measured on the deliverable: the bridge's 0.259 -> 0.30 um
projection moved fc by -2.9 % -- past the +-2 % S2 box -- while every other
metric stayed inside its line.

The remedy stays inside the projection's own footprint: the ONE device the
min-width bump reshaped gets its length retuned, on-grid, until fc is back on
target.  Nothing else moves -- no cap, no other device, no bias -- so this is
the projection completing itself, not a new sizing technique.  The secant runs
on log fc vs log L (the relation is a near-perfect power law over this range;
measured convergence: 2 probes + 1 refinement to land within 6 mHz of 250 Hz).

    from lab.retune import restore_fc
    d, moves = legalize(d)
    d, tunes = restore_fc(d, tag="pkg_X")     # no-op when S2 already holds
"""
from __future__ import annotations

import math
from dataclasses import replace

from . import metrics as M
from .dut import Design, Dev
from .grid import snap

FC_TARGET = 250.0
FC_BOX = (245.0, 255.0)          # the S2 pass window
MAX_PROBES = 5


def restore_fc(d: Design, *, role: str = "bridge", tag: str = "retune",
               target: float = FC_TARGET) -> tuple[Design, list[str]]:
    """Retune `role`'s length until fc is back inside the S2 box.

    Returns (design, report).  No-op (and no report) when fc already passes.
    Raises RuntimeError if MAX_PROBES probes cannot land inside the box --
    a projection that cannot be completed must fail loudly, not ship.
    """
    s = M.evaluate(d, f"{tag}_fc0", record=False)
    if FC_BOX[0] <= s["fc_hz"] <= FC_BOX[1]:
        return d, []
    if role not in d.devs:
        raise RuntimeError(f"fc {s['fc_hz']:.1f} Hz outside S2 and no {role!r} "
                           f"device to retune")

    dev = d.devs[role]
    probes: list[tuple[float, float]] = [(dev.l, s["fc_hz"])]

    def at(l: float) -> tuple[Design, float]:
        l = snap(l)
        di = replace(d, devs={**d.devs, role: Dev(w=dev.w, l=l, ng=dev.ng, m=dev.m)})
        return di, M.evaluate(di, f"{tag}_fc{len(probes)}", record=False)["fc_hz"]

    # First guess: fc ~ (1/L)^k with k ~ 1 in the ladder -> L1 = L0 * fc0/target.
    best_d, best = d, s["fc_hz"]
    l_next = dev.l * probes[0][1] / target
    for _ in range(MAX_PROBES):
        di, fc = at(l_next)
        probes.append((snap(l_next), fc))
        if abs(fc - target) < abs(best - target):
            best_d, best = di, fc
        if abs(fc - target) <= 0.05:
            break
        (l1, f1), (l2, f2) = probes[-2], probes[-1]
        if abs(math.log(f2) - math.log(f1)) < 1e-9:
            break
        k = (math.log(f2) - math.log(f1)) / (math.log(l2) - math.log(l1))
        l_next = math.exp(math.log(l2) + (math.log(target) - math.log(f2)) / k)

    if not (FC_BOX[0] <= best <= FC_BOX[1]):
        raise RuntimeError(f"{tag}: bridge-L retune failed, best fc {best:.2f} Hz "
                           f"after {len(probes) - 1} probes: {probes}")
    rep = [f"{role}: l {dev.l * 1e6:.6g} -> {best_d.devs[role].l * 1e6:.6g} um "
           f"(fc {probes[0][1]:.2f} -> {best:.2f} Hz; S2 restored after the "
           f"min-width projection)"]
    return best_d, rep
