"""Layout-legal device geometry: 5 nm grid, PDK minima, finger split.

The optimizer explores a CONTINUOUS (w, l) space, so a winning sizing lands on
values like w = 1.29324 um that no mask can hold: SG13G2's manufacturing grid
is 5 nm (`sg13g2_tech_mod.json: "grid": 0.005`, enforced by the OffGrid.* DRC
checks), the hv-MOS minimum drawn width is 0.30 um (`pmosHV_minW`/`nmosHV_minW`)
against 0.15 um for the lv flavour, and the PDK PCells refuse a single gate
finger wider than 10 um (`*_maxW`).  `legalize()` maps a `Design` onto that
lattice so the sizing of record IS the drawable sizing:

*   **w and l snap to the nearest 5 nm.**  Worst case this perturbs a device by
    half a grid step -- <= 0.4 % on the narrowest device here, noise against the
    +-2 % S2 window -- and the re-certification that follows measures the
    snapped sizing, never assumes it.
*   **A sub-minimum width is bumped to the minimum at constant W/L**: l scales
    by the same factor before snapping.  In weak inversion the branch current
    rides on W/L, so this preserves the operating point to first order and the
    scorecard re-run judges the second order.
*   **w > 10 um becomes ng equal fingers** (smallest ng that keeps a finger
    <= 10 um AND on-grid), which is exactly how the PCell will draw it.  If no
    finger count divides the snapped width exactly, the width moves to the
    nearest ng-divisible grid multiple -- reported, like every other change.

What this module deliberately does NOT touch: channel LENGTHS above the 10 um
PCell bound (l is a series-stack question for the layout lane -- splitting it
here would change the device count and break netlist identity with the drawn
topology), capacitor values (ideal elements until the MIM area decision), and
`m` (reserved for the layout lane's own use).

    from lab.grid import legalize
    d2, changes = legalize(d)      # changes: one human-readable line per edit
"""
from __future__ import annotations

from dataclasses import replace

from .dut import Design, Dev

GRID = 5e-9                 # SG13G2 manufacturing grid, metres
WMAX_FINGER = 10e-6         # PCell *_maxW: widest single gate finger
NG_MAX = 64                 # sanity bound for the finger search

# Minimum drawn W/L per flavour (sg13g2_tech_mod.json).  The hv minima are the
# binding ones; the conservative n-channel minL is used for both polarities
# (every length in this family is >= 5 um, so minL never actually binds).
MIN_W = {"lv": 0.15e-6, "hv": 0.30e-6}
MIN_L = {"lv": 0.13e-6, "hv": 0.45e-6}

_EPS = 1e-12                # float-noise guard (0.2 % of one grid step)


def _units(x: float) -> int:
    """x in whole grid steps, nearest."""
    return int(round(x / GRID))


def snap(x: float) -> float:
    """x moved to the nearest 5 nm grid point."""
    return _units(x) * GRID


def on_grid(x: float) -> bool:
    return abs(x - snap(x)) <= _EPS


def legalize_dev(role: str, dev: Dev, *, lv: bool) -> tuple[Dev, list[str]]:
    """One device -> layout-legal device + the list of edits made."""
    fl = "lv" if lv else "hv"
    w, l, ng, changes = dev.w, dev.l, dev.ng, []

    # 1. sub-minimum width: bump to the flavour minimum at constant W/L.
    if w < MIN_W[fl] - _EPS:
        f = MIN_W[fl] / w
        changes.append(f"{role}: w {w * 1e6:.5g} um < {fl} min "
                       f"{MIN_W[fl] * 1e6:.2g} um -> w x{f:.4f}, l x{f:.4f} "
                       f"(W/L preserved)")
        w, l = MIN_W[fl], l * f
    if l < MIN_L[fl] - _EPS:      # defensive; never binds in this family
        changes.append(f"{role}: l {l * 1e6:.5g} um below {fl} min -> bumped")
        l = MIN_L[fl]

    # 2. snap to the manufacturing grid.
    for name, old, new in (("w", w, snap(w)), ("l", l, snap(l))):
        if abs(new - old) > _EPS:
            changes.append(f"{role}: {name} {old * 1e6:.6g} -> {new * 1e6:.6g} um "
                           f"(5 nm grid, {(new - old) / old * 100:+.3f} %)")
    w, l = snap(w), snap(l)

    # 3. fingers: keep every finger <= 10 um, on-grid and >= the minimum width.
    if w > WMAX_FINGER + _EPS:
        wu, need = _units(w), -(-_units(w) // _units(WMAX_FINGER))  # ceil
        pick = next((n for n in range(max(need, ng), NG_MAX + 1)
                     if wu % n == 0 and (wu // n) * GRID >= MIN_W[fl] - _EPS),
                    None)
        if pick is None:                       # no exact split: nudge the width
            pick = max(need, ng)
            wu2 = max(pick * round(wu / pick),
                      pick * _units(MIN_W[fl]))
            changes.append(f"{role}: w {wu * GRID * 1e6:.6g} -> "
                           f"{wu2 * GRID * 1e6:.6g} um (nearest {pick}-finger "
                           f"grid multiple)")
            wu = wu2
            w = wu * GRID
        if pick != ng:
            changes.append(f"{role}: ng {ng} -> {pick} "
                           f"({wu // pick * GRID * 1e6:.6g} um/finger)")
            ng = pick

    out = Dev(w=w, l=l, ng=ng, m=dev.m)
    return (dev, []) if (out == dev) else (out, changes)


def legalize(d: Design) -> tuple[Design, list[str]]:
    """Design -> layout-legal Design + report.  Idempotent."""
    devs, changes = {}, []
    for role, dev in d.devs.items():
        nd, ch = legalize_dev(role, dev, lv=role in d.lv_roles)
        devs[role] = nd
        changes += ch
    return replace(d, devs=devs), changes
