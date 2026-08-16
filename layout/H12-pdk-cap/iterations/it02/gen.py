#!/usr/bin/env python3
"""Layout of record for **H12-pdk-cap** (`.subckt lpf_core`) — IHP SG13G2.

The layout is *this module*; the GDS is a build product.  It implements
`layout/H12-pdk-cap/PLAN.md` (approved 2026-08-15) line by line:

* two physically separate islands — biquad A (`net2`/`net3`) below the grounded
  shield band, biquad B above it — with the two MIM banks at the far ends, so
  the 0.28 fF A->B coupling budget (BRIEF §1.1) is met by construction;
* `xc1`/`xc10` drawn **flipped** (Metal5 bottom plate on `voutp`/`voutn`, the
  905 fF net, not on `net4`/`net1`, the 83 fF net — BRIEF §6);
* the six-unit nmos bias array (`xm9`, `xm10`, `xr3`x4) as a 2-D common centroid
  (rows 1,3 = `xr3`, row 2 = `xm9`|`xm10`) with a dummy column per side and
  identical routing on all six units (BRIEF §2.1);
* one shared `vdd` n-well for `xm14`/`xr1`/`xm15` + 2 dummies (1-D centroid);
  every other pmos gets its own minimum-enclosure n-well + `ntap1` (BRIEF §5).

Geometry (W/L/ng/m) is read from `design.json` at build time and never appears
as a knob.  `LayoutParams` carries only placement/routing constants (PLAN §5).

Layer discipline (PLAN §4): device straps on Metal1, vertical lanes on Metal2,
long horizontal hauls on Metal3, cap plates on Metal5 (bottom) / TopMetal1 (top,
also the `net2`/`net3` long haul).  **No Metal4 plane anywhere** — Metal4 exists
only as 2 um via-stack pads, never under a MIM bank.

CLI::

    python gen_H12_pdk_cap.py -o build/lpf_core.gds      # write the GDS
    python gen_H12_pdk_cap.py --lvs                      # write asbuilt/core_lvs.sp
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path

import gdsfactory as gf
from ihp import PDK
from ihp import cells as C
from ihp.cells.fet_transistors import _mos_core

PDK.activate()

CELL = "lpf_core"
GRID = 0.005

# --- fixed drawing constants (not knobs: they are DRC floors, not choices) ---
STRAP = 0.5   # S/D strap centre offset from the Activ edge
GATE = 1.5    # gate bar centre offset from the Activ edge (outside the strap)
GPAD = 0.5    # gate bar height / poly tab width
TAPOFF = 1.6  # n-well tap centre offset from the Activ edge (source side)
TAPH = 0.8    # n-well / p-substrate tap bar height
PTAPOFF = 2.9  # substrate tap bar centre offset below an nmos row
CONT = 0.16   # Cnt.a (exact)
VIA = 0.19    # V1.a / Vn.a (exact)
TVIA = 0.42   # TV1.a (exact)
VPAD = 0.38   # local via-stack pad (< Mn.e 0.39 "wide line" -> 0.21 space, not 0.24)
MIM_BIAS = 0.72  # gdsfactory grows the MIM box by 0.36/side vs the `cmim` arg
CAP_DENS = 1.5e-3  # pF/um2, for the design.json cross-check only

# --- capacitor table, transcribed from signoff/.../asbuilt/core.sp -----------
# (unit side, unit count, top-plate net (TopMetal1), bottom-plate net (Metal5))
# xc1/xc10 are the BRIEF §6 flip: bottom = voutp/voutn.
CAPS: dict[str, dict] = {
    "xc13": dict(unit=40.53, m=2, top="net2", bot="vout_1", key="c1_a"),
    "xc17": dict(unit=40.53, m=2, top="net3", bot="vout_2", key="c1_a"),
    "xc19": dict(unit=49.42, m=8, top="vout_2", bot="vout_1", key="c2_a"),
    "xc1": dict(unit=49.91, m=16, top="net4", bot="voutp", key="c1_b"),
    "xc10": dict(unit=49.91, m=16, top="net1", bot="voutn", key="c1_b"),
    "xc12": dict(unit=48.45, m=7, top="voutn", bot="voutp", key="c2_b"),
}

BOUNDS: dict[str, tuple[float, float]] = {
    "dev_gap_x": (1.0, 6.0),
    "axis_gap": (2.0, 30.0),
    "row_gap": (3.0, 20.0),
    "bias_row_gap": (2.0, 12.0),
    "bias_dummy_cols": (0, 2),
    "gmfb_dummy": (0, 2),
    "well_margin": (0.62, 3.0),
    "well_gap": (1.8, 6.0),
    "ring_w": (0.6, 3.0),
    "ring_gap": (2.0, 15.0),
    "shield_w": (2.0, 12.0),
    "cap_gap": (0.30, 3.0),
    "cap_bank_gap": (5.0, 40.0),
    "cap_axis_gap": (3.0, 20.0),
    "bank_gap": (8.0, 60.0),
    "w_m1": (0.16, 1.0),
    "w_m2": (0.20, 1.0),
    "w_m3": (0.20, 1.0),
    "w_tm1": (1.64, 4.0),
    "via_pad": (1.7, 3.0),
    "cc19_cols": (1, 4),
    "cc1_cols": (2, 8),
    "cc12_cols": (1, 7),
    "cc13_cols": (1, 2),
    "bankA_order": ("c19_axis", "c13_axis"),
    "cap_spine_side": ("left", "mirror"),
    "cap_anti_orient": (False, True),
    "cc12_split": ("none", "3|1|3"),
    "bias_dummy_rows": (0, 1),
    "xr1_split": (False, True),
    "net23_strap": ("lane_m1", "min_m1"),
    "net23_spine_layer": ("Metal2", "Metal5"),
    "vbn_bus_keepout": (0.0, 12.0),
}


@dataclasses.dataclass(frozen=True)
class LayoutParams:
    """The optimizer knobs (PLAN §5).  No W/L/ng/m ever appears here."""

    dev_gap_x: float = 2.0       # clearance between devices inside a row
    axis_gap: float = 6.0        # symmetry axis -> inner edge of each half
    row_gap: float = 6.0         # routing channel between device rows
    bias_row_gap: float = 4.0    # vertical pitch gap inside the bias array
    bias_dummy_cols: int = 1     # dummy columns per side of the bias array
    bias_dummy_rows: int = 0     # dummy rows above and below the bias array (F7)
    gmfb_dummy: int = 1          # dummy hv-pmos per end of the gmf_b row
    xr1_split: bool = False      # xr1 as two anti-oriented nf=1 halves (F14)
    well_margin: float = 0.62    # NWell enclosure of Activ (NW.c1 floor)
    well_gap: float = 2.0        # different-net NWell spacing (NW.b1 floor)
    ring_w: float = 1.0          # guard-ring Metal1 / tap width
    ring_gap: float = 4.0        # ring -> nearest device / cap plate
    shield_w: float = 4.0        # grounded A/B shield band width
    cap_gap: float = 0.4         # gap between adjacent MIM Metal5 plates
    cap_bank_gap: float = 10.0   # gap between two sub-arrays inside a bank
    cap_axis_gap: float = 5.0    # axis -> inner edge of the axis-adjacent sub-array (F5)
    bank_gap: float = 12.0       # cap bank -> device island
    w_m1: float = 0.20           # Metal1 wire width (M1.a = 0.16)
    w_m2: float = 0.20           # Metal2 wire width (Mn.a = 0.20)
    w_m3: float = 0.25           # Metal3 wire width
    w_tm1: float = 1.70          # TopMetal1 wire width (TM1.a = 1.64)
    via_pad: float = 2.0         # side of a via-stack landing pad
    cc19_cols: int = 4           # xc19 columns (per 4-unit half when split)
    cc1_cols: int = 4            # xc1/xc10 array columns (rows = 16/cols)
    cc12_cols: int = 7           # xc12 array columns
    cc13_cols: int = 1           # xc13/xc17 array columns
    # -- round-2 floorplan / routing modes (PLAN R2.1) ----------------------
    bankA_order: str = "c19_axis"    # which mirror pair sits on the axis (F5)
    cap_spine_side: str = "mirror"   # MIM top-plate spine column (F6)
    cap_anti_orient: bool = False    # xc19 drawn 4+4 with swapped plates (F8)
    cc12_split: str = "none"         # xc12 plate split (F8)
    net23_strap: str = "min_m1"      # net2/net3 device -> lane strap style (R2.6)
    net23_spine_layer: str = "Metal2"  # net2/net3 vertical spine layer (R2.6)
    vbn_bus_keepout: float = 0.0     # vbn M3 bus keep-out around the net2/net3 corridor


# --------------------------------------------------------------------------
# knob validation (PLAN R2.5) -- BOUNDS is the single source of truth
# --------------------------------------------------------------------------
def _fields() -> tuple[str, ...]:
    return tuple(f.name for f in dataclasses.fields(LayoutParams))


def clamp(params: "LayoutParams") -> "LayoutParams":
    """Resolve knob couplings and pull numeric knobs back inside ``BOUNDS``.

    Two couplings are structural, not preferences: the anti-oriented ``xc19``
    split only exists in the ``c13_axis`` bank-A order (in ``c19_axis`` the two
    halves would have to hand their bottom plates across the whole bank), and a
    ``c13_axis`` bank needs the split to keep the mirror symmetry.  ``clamp``
    makes the pair consistent instead of raising, so every ``BOUNDS`` endpoint
    is buildable.
    """
    d = dataclasses.asdict(params)
    for k, (lo, hi) in BOUNDS.items():
        if isinstance(lo, bool) or isinstance(lo, str):
            continue
        d[k] = type(d[k])(min(max(d[k], lo), hi))
    if d["bankA_order"] == "c19_axis":
        d["cap_anti_orient"] = False
    elif d["bankA_order"] == "c13_axis":
        d["cap_anti_orient"] = True
    if d["bankA_order"] == "c19_axis":
        d["cc19_cols"] = min(max(d["cc19_cols"], 1), 4)
        while 8 % d["cc19_cols"]:
            d["cc19_cols"] -= 1
    else:
        d["cc19_cols"] = 2 if d["cc19_cols"] > 1 else 1
    while 16 % d["cc1_cols"]:
        d["cc1_cols"] -= 1
    return LayoutParams(**d)


def validate(params: "LayoutParams", strict: bool = True) -> list[str]:
    """Return the list of knob problems; raise on any if ``strict``."""
    bad: list[str] = []
    assert set(BOUNDS) == set(_fields()), (
        f"BOUNDS/LayoutParams drift: {set(BOUNDS) ^ set(_fields())}")
    d = dataclasses.asdict(params)
    for k, (lo, hi) in BOUNDS.items():
        v = d[k]
        if isinstance(lo, str):
            if v not in (lo, hi):
                bad.append(f"{k}={v!r} not in {{{lo!r}, {hi!r}}}")
        elif isinstance(lo, bool):
            if v not in (False, True):
                bad.append(f"{k}={v!r} is not a bool")
        elif not (lo <= v <= hi):
            bad.append(f"{k}={v} outside [{lo}, {hi}]")
    if clamp(params) != params:
        bad.append("knob combination is inconsistent (see clamp(): "
                   f"{ {k: v for k, v in dataclasses.asdict(clamp(params)).items() if d[k] != v} })")
    if strict and bad:
        raise ValueError("; ".join(bad))
    return bad


# --------------------------------------------------------------------------
# small geometry helpers
# --------------------------------------------------------------------------
def _s(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


_STACK = ["Metal1", "Metal2", "Metal3", "Metal4", "Metal5", "TopMetal1"]
_VIA = {  # bottom layer -> (via layer, size, space, min enclosure)
    "Metal1": ("Via1drawing", VIA, 0.22, 0.06),
    "Metal2": ("Via2drawing", VIA, 0.22, 0.06),
    "Metal3": ("Via3drawing", VIA, 0.22, 0.06),
    "Metal4": ("Via4drawing", VIA, 0.22, 0.06),
    "Metal5": ("TopVia1drawing", TVIA, 0.42, 0.45),
}


@dataclasses.dataclass
class Mos:
    """Everything the router needs about one placed transistor."""

    x0: float
    x1: float          # Activ x range
    y0: float
    y1: float          # Activ y range
    cols_s: list[float]
    cols_d: list[float]
    gates: list[float]
    y_s: float         # source strap centre
    y_d: float         # drain strap centre
    y_g: float         # gate bar centre
    x_lo: float
    x_hi: float        # full extent (well / TGO)
    y_lo: float
    y_hi: float
    x_in_d: float      # innermost drain column
    x_in_s: float      # innermost source column


class _B:
    """Flat drawing helpers on one gdsfactory Component."""

    def __init__(self, c: gf.Component, p: LayoutParams):
        self.c, self.p = c, p

    def rect(self, layer: str, x0: float, y0: float, x1: float, y1: float) -> None:
        x0, x1 = sorted((_s(x0), _s(x1)))
        y0, y1 = sorted((_s(y0), _s(y1)))
        self.c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)

    def h(self, layer: str, y: float, x0: float, x1: float, w: float, cap: bool = True) -> None:
        """Horizontal wire; the ends are extended by w/2 so L-joints never leave
        a sub-min-width notch (M1.a / Mn.a on every corner otherwise)."""
        e = w / 2 if cap else 0.0
        lo, hi = min(x0, x1) - e, max(x0, x1) + e
        self.rect(layer, lo, y - w / 2, hi, y + w / 2)

    def v(self, layer: str, x: float, y0: float, y1: float, w: float, cap: bool = True) -> None:
        e = w / 2 if cap else 0.0
        lo, hi = min(y0, y1) - e, max(y0, y1) + e
        self.rect(layer, x - w / 2, lo, x + w / 2, hi)

    def m1h(self, y, x0, x1, w=None):
        self.h("Metal1drawing", y, x0, x1, w or self.p.w_m1)

    def m1v(self, x, y0, y1, w=None):
        self.v("Metal1drawing", x, y0, y1, w or self.p.w_m1)

    def m2h(self, y, x0, x1, w=None):
        self.h("Metal2drawing", y, x0, x1, w or self.p.w_m2)

    def m2v(self, x, y0, y1, w=None):
        self.v("Metal2drawing", x, y0, y1, w or self.p.w_m2)

    def m3h(self, y, x0, x1, w=None):
        self.h("Metal3drawing", y, x0, x1, w or self.p.w_m3)

    def m3v(self, x, y0, y1, w=None):
        self.v("Metal3drawing", x, y0, y1, w or self.p.w_m3)

    def label(self, net: str, x: float, y: float, layer: str = "Metal1text") -> None:
        self.c.add_label(text=net, position=(_s(x), _s(y)), layer=layer)

    # -- vias ---------------------------------------------------------------
    def vstack(self, x: float, y: float, bot: str, top: str, size: float | None = None) -> None:
        """Via stack with PDK-legal via sizes (via_stack() draws 0.26 -> V1.a fail)."""
        size = size or self.p.via_pad
        i0, i1 = _STACK.index(bot), _STACK.index(top)
        for i in range(i0, i1 + 1):
            lay = _STACK[i]
            s = max(size, 1.64) if lay == "TopMetal1" else size
            self.rect(lay + "drawing", x - s / 2, y - s / 2, x + s / 2, y + s / 2)
        for i in range(i0, i1):
            vl, vs, vsp, enc = _VIA[_STACK[i]]
            avail = size - 2 * enc
            # <=3 per direction: V1.b1/Vn.b1 demand 0.29 only for >3 rows AND >3 cols
            n = max(1, min(3, int((avail + vsp + 1e-9) // (vs + vsp))))
            span = n * vs + (n - 1) * vsp
            for a in range(n):
                for b in range(n):
                    xx = x - span / 2 + a * (vs + vsp)
                    yy = y - span / 2 + b * (vs + vsp)
                    self.rect(vl, xx, yy, xx + vs, yy + vs)

    def v12(self, x, y):
        self.vstack(x, y, "Metal1", "Metal2", VPAD)

    def v13(self, x, y):
        self.vstack(x, y, "Metal1", "Metal3", VPAD)

    def v23(self, x, y):
        self.vstack(x, y, "Metal2", "Metal3", VPAD)

    # -- taps ---------------------------------------------------------------
    def tap(self, x0: float, x1: float, yc: float, kind: str, h: float | None = None) -> None:
        """A substrate ('p') or n-well ('n') tap bar, drawn flat.

        `ptap1`/`ntap1` spread their contacts over ~2/3 of the Activ, which trips
        LU.d/LU.d1 ("max. extension of a tie Activ beyond Cont = 6 um") on bars
        longer than ~20 um; drawing the contact row ourselves fixes that and lets
        the bar be any length.
        """
        h = h or TAPH
        x0, x1 = min(x0, x1), max(x0, x1)
        ln = x1 - x0
        if ln < 0.5 or h < 0.3:
            return
        self.rect("Activdrawing", x0, yc - h / 2, x1, yc + h / 2)
        self.rect("pSDdrawing" if kind == "p" else "nSDdrawing",
                  x0 - 0.1, yc - h / 2 - 0.1, x1 + 0.1, yc + h / 2 + 0.1)
        n = max(1, int((ln - 0.3) / 0.40) + 1)
        pitch = (ln - 0.3 - CONT) / (n - 1) if n > 1 else 0.0
        for k in range(n):
            xx = x0 + 0.15 + k * pitch
            self.rect("Contdrawing", xx, yc - CONT / 2, xx + CONT, yc + CONT / 2)
        self.rect("Metal1drawing", x0, yc - h / 2, x1, yc + h / 2)

    def tapv(self, y0: float, y1: float, xc: float, kind: str, w: float) -> None:
        """Vertical twin of :meth:`tap` (ring sides)."""
        y0, y1 = min(y0, y1), max(y0, y1)
        ln = y1 - y0
        if ln < 0.5 or w < 0.3:
            return
        self.rect("Activdrawing", xc - w / 2, y0, xc + w / 2, y1)
        self.rect("pSDdrawing" if kind == "p" else "nSDdrawing",
                  xc - w / 2 - 0.1, y0 - 0.1, xc + w / 2 + 0.1, y1 + 0.1)
        n = max(1, int((ln - 0.3) / 0.40) + 1)
        pitch = (ln - 0.3 - CONT) / (n - 1) if n > 1 else 0.0
        for k in range(n):
            yy = y0 + 0.15 + k * pitch
            self.rect("Contdrawing", xc - CONT / 2, yy, xc + CONT / 2, yy + CONT)
        self.rect("Metal1drawing", xc - w / 2, y0, xc + w / 2, y1)

    # -- transistor ---------------------------------------------------------
    def mos(
        self,
        *,
        w: float,
        l: float,
        nf: int,
        pmos: bool,
        sign: int,
        x_in: float,
        y_act: float,
        d_top: bool,
        g_top: bool,
        tap: bool = True,
        tie: str | None = None,   # "all" (dummy) | "dg" (diode connect)
    ) -> Mos:
        core = _mos_core(width=w, length=l, nf=nf, is_pmos=pmos, is_hv=True)
        ref = self.c << core
        if sign > 0:
            ref.dmirror_x()
        sx, sy = ref.ports["S"].center
        dx = ref.ports["D"].center[0]
        gx = ref.ports["G"].center[0]
        pitch = dx - sx
        wf = w / nf
        cols = [sx + k * pitch for k in range(nf + 1)]
        gates = [gx + k * pitch for k in range(nf)]
        ax0, ax1 = min(cols) - 0.15, max(cols) + 0.15
        ay0 = sy - wf / 2
        ddx = sign * x_in - (ax1 if sign < 0 else ax0)
        ddy = y_act - ay0
        ref.dmovex(_s(ddx))
        ref.dmovey(_s(ddy))
        cols = [_s(v + ddx) for v in cols]
        gates = [_s(v + ddx) for v in gates]
        ax0, ax1 = _s(ax0 + ddx), _s(ax1 + ddx)
        ay0, ay1 = _s(y_act), _s(y_act + wf)

        cs, cd = cols[0::2], cols[1::2]
        y_d = ay1 + STRAP if d_top else ay0 - STRAP
        y_s = ay0 - STRAP if d_top else ay1 + STRAP
        y_g = (ay1 + GATE) if g_top else (ay0 - GATE)
        ws = max(0.2, self.p.w_m1)

        # S/D straps: vertical stubs off every column + a horizontal bar
        for grp, ys in ((cs, y_s), (cd, y_d)):
            for xx in grp:
                self.m1v(xx, min(ys, ay0) if ys < ay0 else ay1, max(ys, ay1) if ys > ay1 else ay0, ws)
            if len(grp) > 1:
                self.m1h(ys, min(grp), max(grp), ws)
        # gate: poly tabs -> poly bar -> contacts -> Metal1 bar
        py = ay1 + 0.18 if g_top else ay0 - 0.18
        for gxx in gates:
            self.rect("GatPolydrawing", gxx - GPAD / 2, py, gxx + GPAD / 2, y_g)
        gb0, gb1 = min(gates) - GPAD / 2, max(gates) + GPAD / 2
        self.h("GatPolydrawing", y_g, gb0, gb1, GPAD)
        self.h("Metal1drawing", y_g, gb0, gb1, GPAD)
        for gxx in gates:
            self.rect("Contdrawing", gxx - CONT / 2, y_g - CONT / 2, gxx + CONT / 2, y_g + CONT / 2)

        x_lo = min(ax0, ax1) - (self.p.well_margin if pmos else 0.3)
        x_hi = max(ax0, ax1) + (self.p.well_margin if pmos else 0.3)
        y_lo = min(y_g - GPAD / 2, y_d - 0.3, y_s - 0.3, ay0 - 0.55)
        y_hi = max(y_g + GPAD / 2, y_d + 0.3, y_s + 0.3, ay1 + 0.55)

        if pmos and tap:  # n-well tap on the source side + Metal1 body plate
            y_tap = (ay1 + TAPOFF) if not d_top else (ay0 - TAPOFF)
            self.tap(min(ax0, ax1), max(ax0, ax1), y_tap, "n")
            self.rect(
                "Metal1drawing",
                min(cs) - ws / 2,
                min(y_s, y_tap) - TAPH / 2 if y_tap < y_s else y_s - ws / 2,
                max(cs) + ws / 2,
                max(y_s, y_tap) + TAPH / 2 if y_tap > y_s else y_s + ws / 2,
            )
            y_lo = min(y_lo, y_tap - TAPH / 2 - self.p.well_margin)
            y_hi = max(y_hi, y_tap + TAPH / 2 + self.p.well_margin)
        if tie:  # "all": D+S+G (a dummy); "dg": drain to gate only (a diode)
            xt = cd[0] if len(cd) else cols[0]
            ys = (min(y_g, y_d, y_s), max(y_g, y_d, y_s)) if tie == "all" else \
                 (min(y_g, y_d), max(y_g, y_d))
            self.m1v(xt, ys[0], ys[1], ws)

        x_in_d = min(cd, key=lambda v: abs(v)) if cd else cols[-1]
        x_in_s = min(cs, key=lambda v: abs(v))
        return Mos(
            x0=min(ax0, ax1), x1=max(ax0, ax1), y0=ay0, y1=ay1,
            cols_s=cs, cols_d=cd, gates=gates, y_s=y_s, y_d=y_d, y_g=y_g,
            x_lo=min(x_lo, x_hi), x_hi=max(x_lo, x_hi), y_lo=y_lo, y_hi=y_hi,
            x_in_d=x_in_d, x_in_s=x_in_s,
        )

    def nwell(self, x0: float, y0: float, x1: float, y1: float) -> None:
        self.rect("NWelldrawing", x0, y0, x1, y1)

    # -- MIM array ----------------------------------------------------------
    def spine_cols(self, cols: int, xc: float) -> list[int]:
        """Which unit column(s) carry the TopMetal1 top-plate spine (PLAN R2.3).

        **Mirror rule**: an array whose centre is off the axis puts its spine on
        the column *nearest the axis* -- the inner column -- so the two members
        of a mirror pair are mirror images of each other and both hauls are
        short.  An array centred *on* the axis puts it on its centre column
        (odd) or on the two columns flanking the centre (even), which is the
        only placement that is its own mirror image.  ``cap_spine_side="left"``
        restores the v1 behaviour (always column 0) for comparison.
        """
        if self.p.cap_spine_side == "left":
            return [0]
        if abs(xc) < 1e-6:
            return [cols // 2] if cols % 2 else sorted({max(cols // 2 - 1, 0), cols // 2})
        return [cols - 1] if xc < 0 else [0]

    def cap_array(self, unit: float, cols: int, rows: int, xc: float, y0: float,
                  groups: list[int] | None = None) -> dict:
        """One MIM sub-array.  ``groups`` (a list of column counts summing to
        ``cols``) splits the bottom sheet / top comb into independently wired
        plate groups -- the F8 anti-orientation of ``xc12``; ``None`` = one
        group, the v1 behaviour."""
        p = self.p
        side = unit + 1.2                      # Metal5 plate side (MIM.c 0.6/side)
        pitch = side + p.cap_gap
        w = cols * side + (cols - 1) * p.cap_gap
        h = rows * side + (rows - 1) * p.cap_gap
        x0 = xc - w / 2
        cell = C.cmim(width=unit - MIM_BIAS, length=unit - MIM_BIAS)
        for i in range(cols):
            for j in range(rows):
                ref = self.c << cell
                ref.dcenter = (_s(x0 + side / 2 + i * pitch), _s(y0 + side / 2 + j * pitch))
        # bottom plate: one solid Metal5 sheet per plate group (merging the unit
        # plates; the sub-0.6 um inter-plate gaps would otherwise break Mn.f)
        c0 = 0
        for gc in (list(groups) if groups else [cols]):
            gx0 = x0 + c0 * pitch
            self.rect("Metal5drawing", gx0, y0, gx0 + gc * side + (gc - 1) * p.cap_gap, y0 + h)
            c0 += gc
        # top plate: TopMetal1 comb (one bar per unit row + a spine per group);
        # the spine sits *over* a unit column -- one centred in an inter-unit
        # gap would sit 0.31 um from both plates and fail TM1.b.
        gcols = list(groups) if groups else [cols]
        assert sum(gcols) == cols, (gcols, cols)
        c0, gsp, gx = 0, [], []
        for gc in gcols:
            gx0 = x0 + c0 * pitch
            gx1 = gx0 + gc * side + (gc - 1) * p.cap_gap
            for j in range(rows):
                self.h("TopMetal1drawing", y0 + side / 2 + j * pitch, gx0 + 0.9, gx1 - 0.9, p.w_tm1)
            sc = [c for c in self.spine_cols(cols, xc) if c0 <= c < c0 + gc] or [c0]
            for c in sc:
                xs = x0 + side / 2 + c * pitch
                self.v("TopMetal1drawing", xs, y0 + 0.9, y0 + h - 0.9, p.w_tm1)
            gsp.append(x0 + side / 2 + sc[0] * pitch)
            gx.append((gx0, gx1))
            c0 += gc
        return dict(x0=x0, x1=x0 + w, y0=y0, y1=y0 + h, xc=xc, side=side, pitch=pitch,
                    rows=rows, cols=cols, spine=gsp[0], spines=gsp, groups=gcols, gx=gx)


# --------------------------------------------------------------------------
# sizing record
# --------------------------------------------------------------------------
def _design(sizing: dict | None) -> dict:
    if sizing is None:
        f = Path(__file__).resolve().parents[2] / "signoff/post-pvt/H12-pdk-cap/design.json"
        sizing = json.loads(f.read_text())
    return sizing.get("design", sizing)


def _devs(sizing: dict | None) -> dict:
    d = _design(sizing)
    out = {}
    for role, v in d["devs"].items():
        out[role] = dict(w=v["w"] * 1e6, l=v["l"] * 1e6, nf=int(v["ng"]), m=int(v["m"]))
    caps = d["caps_pf"]
    for name, cp in CAPS.items():           # mechanical cross-check, no retyping
        want = caps[cp["key"]]
        got = cp["m"] * cp["unit"] ** 2 * CAP_DENS
        assert abs(got - want) / want < 0.02, f"{name}: {got:.3f} pF vs design.json {want} pF"
    return out


# --------------------------------------------------------------------------
# the layout
# --------------------------------------------------------------------------
def build(params: LayoutParams = LayoutParams(), sizing: dict | None = None) -> gf.Component:
    p = clamp(params)
    validate(p, strict=True)
    dv = _devs(sizing)
    c = gf.Component(CELL)
    b = _B(c, p)
    HALVES = (-1, 1)

    # side helpers: `inner` = the edge/gate facing the symmetry axis
    def inner(m: Mos, s: int) -> float:
        return m.x_hi if s < 0 else m.x_lo

    def outer(m: Mos, s: int) -> float:
        return m.x_lo if s < 0 else m.x_hi

    def gate_in(m: Mos, s: int) -> float:
        return min(m.gates, key=lambda v: abs(v))

    def gate_out(m: Mos, s: int) -> float:
        return max(m.gates, key=lambda v: abs(v))

    def gsz(role):
        d = dv[role]
        return dict(w=d["w"], l=d["l"], nf=d["nf"])

    def extent(role) -> tuple[float, float]:
        d = dv[role]
        return extent_of(d["w"], d["l"], d["nf"])

    def extent_of(w: float, l: float, nf: int) -> tuple[float, float]:
        core = _mos_core(width=w, length=l, nf=nf, is_pmos=False, is_hv=True)
        bb = core.bbox()
        return (bb.right - bb.left) - 0.54, w / nf          # Activ width, finger height

    w_bias, h_bias = extent("bias_a_int")
    w_gmfa, h_gmfa = extent("gmf_a")
    w_ina, h_ina = extent("in_a")
    w_brdg, h_brdg = extent("bridge")
    w_inb, h_inb = extent("in_b")
    w_gmfb, h_gmfb = extent("gmf_b")

    ext_p = p.well_margin                             # pmos well / TGO overhang
    gap_p = max(p.dev_gap_x, p.well_gap)              # different-net wells (NW.b1)
    gap_w = max(p.dev_gap_x, 2 * ext_p + 0.9)         # same-well pmos pitch (TGO.e)

    # =====================================================================
    # BANK A (bottom): xc13 | xc19 | xc17
    # =====================================================================
    a19 = b.cap_array(CAPS["xc19"]["unit"], p.cc19_cols,
                      CAPS["xc19"]["m"] // p.cc19_cols, 0.0, 0.0)
    w13 = p.cc13_cols * (CAPS["xc13"]["unit"] + 1.2) + (p.cc13_cols - 1) * p.cap_gap
    x13 = a19["x0"] - p.cap_bank_gap - w13 / 2
    a13 = b.cap_array(CAPS["xc13"]["unit"], p.cc13_cols,
                      CAPS["xc13"]["m"] // p.cc13_cols, x13, 0.0)
    a17 = b.cap_array(CAPS["xc17"]["unit"], p.cc13_cols,
                      CAPS["xc17"]["m"] // p.cc13_cols, -x13, 0.0)
    bankA = dict(x0=a13["x0"], x1=a17["x1"], y1=max(a19["y1"], a13["y1"]))
    # vout_1: xc13 bottom plate -> xc19 bottom plate (both Metal5, one polygon)
    b.rect("Metal5drawing", a13["x1"] - 1.0, a13["y1"] / 2 - 3, a19["x0"] + 1.0,
           a13["y1"] / 2 + 3)

    y_v1 = bankA["y1"] + 2.0     # M3 haul track: vout_1 / vout_2 out of bank A
    y_chA = bankA["y1"] + p.bank_gap

    # =====================================================================
    # ISLAND A: bias array (3 rows) | gmf_a | in_a
    # =====================================================================
    y = y_chA + PTAPOFF + TAPH / 2
    bias, biasd, y_bias_rows = [], [], []
    for r in range(3):
        row_u, row_d = {}, {}
        for s in HALVES:
            row_u[s] = b.mos(**gsz("bias_a_int"), pmos=False, sign=s, x_in=p.axis_gap / 2,
                             y_act=y, d_top=True, g_top=False)
            for k in range(p.bias_dummy_cols):
                row_d[(s, k)] = b.mos(
                    **gsz("bias_a_int"), pmos=False, sign=s,
                    x_in=p.axis_gap / 2 + (k + 1) * (w_bias + p.dev_gap_x),
                    y_act=y, d_top=True, g_top=False, tie="all")
        bias.append(row_u)
        biasd.append(row_d)
        y_bias_rows.append(y)
        y += h_bias + 0.6 + p.bias_row_gap + PTAPOFF + TAPH / 2
    x_biasmax = max([abs(m.x_lo) for row in bias for m in row.values()]
                    + [abs(m.x_lo) for row in biasd for m in row.values()]
                    + [abs(m.x_hi) for row in biasd for m in row.values()])

    # F4 root cause #1: a row substrate-tap bar sits PTAPOFF below the Activ and
    # the gate bar sits GATE below it, so its height is a *geometric* ceiling,
    # not the guard-ring metal width.  Tying it to `ring_w` is what made
    # ring_w = 3.0 produce 132 violations (Gat.c/Cnt.c/Cnt.j/pSD.i).
    h_ptap = min(p.ring_w, 2 * (PTAPOFF - GATE - GPAD / 2 - 0.5))

    def ptap_row(y_act: float, x_span: float) -> float:
        yc = y_act - PTAPOFF
        b.tap(-x_span + p.ring_w + 0.5, x_span - p.ring_w - 0.5, yc, "p", h_ptap)
        b.h("Metal1drawing", yc, -x_span, x_span, h_ptap)
        return yc

    # gmf_a row (nmos): D = vout_1 (top), S = vss (bottom), G = net2 (above D)
    y = y - p.bias_row_gap + p.row_gap
    gmfa = {s: b.mos(**gsz("gmf_a"), pmos=False, sign=s, x_in=p.axis_gap / 2, y_act=y,
                     d_top=True, g_top=True) for s in HALVES}
    y_gmfa = y
    y = max(m.y_hi for m in gmfa.values()) + p.row_gap

    # in_a row (pmos): D = net2 (bottom), S = vout_1 (top), G = vinp (below D)
    y_ina = y + 1.75
    ina = {}
    for s in HALVES:
        ina[s] = b.mos(**gsz("in_a"), pmos=True, sign=s, x_in=p.axis_gap / 2 + ext_p,
                       y_act=y_ina, d_top=False, g_top=False)
        b.nwell(ina[s].x_lo, ina[s].y_lo, ina[s].x_hi, ina[s].y_hi)
    y_islandA_top = max(m.y_hi for m in ina.values())

    y_shield = y_islandA_top + p.ring_gap + p.shield_w / 2
    y_islandA_bot = y_chA - p.ring_gap - p.ring_w / 2

    # =====================================================================
    # ISLAND B: bridge | in_b | gmf_b
    # =====================================================================
    y_brdg = y_shield + p.shield_w / 2 + p.ring_gap + 1.75
    xr2 = b.mos(**gsz("rep_bridge"), pmos=True, sign=-1, x_in=-w_brdg / 2, y_act=y_brdg,
                d_top=False, g_top=False)
    b.nwell(xr2.x_lo, xr2.y_lo, xr2.x_hi, xr2.y_hi)
    x_after_xr2 = w_brdg / 2 + ext_p + gap_p + ext_p
    brdg = {}
    for s in HALVES:
        brdg[s] = b.mos(**gsz("bridge"), pmos=True, sign=s, x_in=x_after_xr2, y_act=y_brdg,
                        d_top=False, g_top=False)
        b.nwell(brdg[s].x_lo, brdg[s].y_lo, brdg[s].x_hi, brdg[s].y_hi)
    y = max([m.y_hi for m in brdg.values()] + [xr2.y_hi]) + p.row_gap

    # in_b row: D = net4 (bottom), S = voutp (top), G = vout_1 (below D)
    y_inb = y + 1.75
    inb = {}
    for s in HALVES:
        inb[s] = b.mos(**gsz("in_b"), pmos=True, sign=s, x_in=p.axis_gap / 2 + ext_p,
                       y_act=y_inb, d_top=False, g_top=False)
        b.nwell(inb[s].x_lo, inb[s].y_lo, inb[s].x_hi, inb[s].y_hi)
    y = max(m.y_hi for m in inb.values()) + p.row_gap

    # gmf_b row: D | xm14 | xr1 | xm15 | D — one shared vdd n-well (1-D centroid)
    y_gmfb = y + 1.75
    if p.xr1_split:
        # F14: the replica is drawn as two anti-oriented nf=1 halves in the same
        # row and the same vdd well, so the rep_gmfb *ratio* carries no
        # orientation term (xm14/xm15 are already one mirrored + one not).
        # KLayout's MOS class sums the parallel W, so LVS still sees W = 12 um.
        d1 = dv["rep_gmfb"]
        w_h, _ = extent_of(d1["w"] / 2, d1["l"], 1)
        xr1s = tuple(
            b.mos(w=d1["w"] / 2, l=d1["l"], nf=1, pmos=True, sign=sg, x_in=gap_w / 2,
                  y_act=y_gmfb, d_top=False, g_top=False, tap=False, tie="dg")
            for sg in HALVES)
        xr1 = xr1s[0]
        w_xr1 = gap_w + 2 * w_h
    else:
        xr1 = b.mos(**gsz("rep_gmfb"), pmos=True, sign=-1, x_in=-w_gmfb / 2, y_act=y_gmfb,
                    d_top=False, g_top=False, tap=False, tie="dg")
        xr1s = (xr1,)
        w_xr1 = w_gmfb
    x_xr1_hi = max(m.x1 for m in xr1s)
    gmfb, gmfbd = {}, {}
    x_after_xr1 = w_xr1 / 2 + gap_w
    for s in HALVES:
        gmfb[s] = b.mos(**gsz("gmf_b"), pmos=True, sign=s, x_in=x_after_xr1, y_act=y_gmfb,
                        d_top=False, g_top=False, tap=False)
        for k in range(p.gmfb_dummy):
            gmfbd[(s, k)] = b.mos(**gsz("gmf_b"), pmos=True, sign=s,
                                  x_in=x_after_xr1 + (k + 1) * (w_gmfb + gap_w),
                                  y_act=y_gmfb, d_top=False, g_top=False,
                                  tap=False, tie="all")
    gmfb_all = list(xr1s) + list(gmfb.values()) + list(gmfbd.values())
    x_gmfb = max(m.x1 for m in gmfb_all)
    y_gmfb_tap = y_gmfb + h_gmfb + TAPOFF
    b.tap(-x_gmfb, x_gmfb, y_gmfb_tap, "n")
    b.rect("Metal1drawing", -x_gmfb, xr1.y_s - 0.1, x_gmfb, y_gmfb_tap + TAPH / 2)
    b.nwell(-x_gmfb - p.well_margin, min(m.y_lo for m in gmfb_all),
            x_gmfb + p.well_margin, y_gmfb_tap + TAPH / 2 + p.well_margin)
    y_islandB_top = y_gmfb_tap + TAPH / 2 + p.well_margin

    # =====================================================================
    # BANK B (top): xc1 | xc10, xc12 above them
    # =====================================================================
    y_n4 = y_islandB_top + 3.0          # M3 track: net4 / net1 out of bank B
    y_vo = y_islandB_top + 7.5          # M3 track: voutp / voutn out of bank B
    y_chB = y_islandB_top + p.bank_gap
    w1 = p.cc1_cols * (CAPS["xc1"]["unit"] + 1.2) + (p.cc1_cols - 1) * p.cap_gap
    b1 = b.cap_array(CAPS["xc1"]["unit"], p.cc1_cols, CAPS["xc1"]["m"] // p.cc1_cols,
                     -(w1 + p.cap_bank_gap) / 2, y_chB)
    b10 = b.cap_array(CAPS["xc10"]["unit"], p.cc1_cols, CAPS["xc10"]["m"] // p.cc1_cols,
                      (w1 + p.cap_bank_gap) / 2, y_chB)
    b12 = b.cap_array(CAPS["xc12"]["unit"], p.cc12_cols, CAPS["xc12"]["m"] // p.cc12_cols,
                      0.0, b1["y1"] + p.cap_bank_gap)
    bankB = dict(x0=b1["x0"], x1=b10["x1"], y0=b1["y0"], y1=b12["y1"])

    # =====================================================================
    # outline, guard rings, shield band, outer lanes
    # =====================================================================
    # F4 root cause #2: the outline used to be set by the cap banks alone, so a
    # knob that widened a *device* row (bias_dummy_cols = 2, gmfb_dummy = 2)
    # pushed transistors and n-wells into the guard ring (330 / 80 violations).
    # The core outline now contains whichever is wider, banks or islands.
    x_bank = max(abs(bankA["x0"]), bankA["x1"], abs(bankB["x0"]), bankB["x1"])
    _islB = [xr2] + list(xr1s) + list(brdg.values()) + list(inb.values()) \
        + list(gmfb.values()) + list(gmfbd.values())
    x_devB = max([abs(m.x_lo) for m in _islB] + [abs(m.x_hi) for m in _islB]
                 + [x_gmfb + p.well_margin + p.well_gap])
    x_ringA_need = max(x_biasmax, w_gmfa, w_ina) + p.ring_gap + p.ring_w / 2
    x_out = max(x_bank, x_ringA_need + 2.0, x_devB + p.ring_gap)
    x_lane0 = x_out + 1.2                    # M3 outer lane: vbn
    x_lane1 = x_out + 2.6                    # M3 outer lane: vdd
    x_ring = x_out + p.ring_gap + 1.0
    y_ring_lo = -p.ring_gap - p.ring_w
    y_ring_hi = bankB["y1"] + p.ring_gap + p.ring_w
    y_bot_pin = y_ring_lo - 4.0
    x_pin = x_ring - 2.0
    x_pin3 = x_out - 2.0         # Metal3 pins stay inside the vbn / vdd outer lanes

    LANE_IN = 0.7      # vout_1/vout_2, then voutp/voutn
    LANE_MID = 1.9     # net2/net3 (island A), net4/net1 (island B)
    x_drop = p.axis_gap / 2 + 3.0      # where a 2 um via stack may land in a channel

    for yy in (y_ring_lo, y_ring_hi):        # core guard ring (vss)
        b.tap(-x_ring, x_ring, yy, "p", p.ring_w)
    for xx in (-x_ring, x_ring):             # sides: Activ clear of the corners
        b.tapv(y_ring_lo + p.ring_w + 0.5, y_ring_hi - p.ring_w - 0.5, xx, "p", p.ring_w)
        b.v("Metal1drawing", xx, y_ring_lo, y_ring_hi, p.ring_w)
    b.label("vss", -x_ring, (y_ring_lo + y_ring_hi) / 2)

    x_ringA = min(x_ringA_need, x_ring - 2.0)
    b.tap(-x_ringA, x_ringA, y_islandA_bot, "p", p.ring_w)     # island A ring bottom
    b.tap(-x_ringA, x_ringA, y_shield, "p", p.shield_w)        # A/B shield band
    for xx in (-x_ringA, x_ringA):
        b.tapv(y_islandA_bot + p.ring_w + 0.7, y_shield - p.shield_w / 2 - 0.7, xx,
               "p", p.ring_w)
        b.v("Metal1drawing", xx, y_islandA_bot, y_shield, p.ring_w)
    for sgn in HALVES:                                          # tie the two rings
        b.m1h(y_islandA_bot, sgn * x_ringA, sgn * x_ring, p.ring_w)

    # =====================================================================
    # ROUTING
    # =====================================================================
    ws = max(0.2, p.w_m1)
    # TopMetal1 haul for net2/net3: between the island-A ring and the first
    # substrate tap bar, the only band where a 2 um via stack can reach Metal1
    y_tm = (y_islandA_bot + p.ring_w / 2 + y_bias_rows[0] - PTAPOFF - p.ring_w / 2) / 2

    # ---- vss: nmos sources + the substrate tap under every nmos row -------
    for r, row in enumerate(bias):
        yc = ptap_row(y_bias_rows[r], x_ringA)
        for m in list(row.values()) + list(biasd[r].values()):
            # only the OUTERMOST source column: the gate bar runs across all the
            # inner ones, and a stub there would short vbn to the tap bar
            b.m1v(m.cols_s[0], yc, m.y_s, ws)
    yc_gmfa = ptap_row(y_gmfa, x_ringA)
    for s in HALVES:
        b.m1v(gmfa[s].cols_s[0], yc_gmfa, gmfa[s].y_s, ws)

    # ---- vbn: the six bias gates -> M3 outer lanes -> bottom pin ----------
    for r, row in enumerate(bias):
        y_g = row[-1].y_g
        b.m1h(y_g, row[-1].gates[0] - GPAD / 2, row[1].gates[-1] + GPAD / 2, GPAD)
        for s in HALVES:
            # between the outer gate and the outer source column: that column
            # carries the vss link down to the tap bar, straight through y_g
            x_hop = (gate_out(row[s], s) + row[s].cols_s[0]) / 2
            b.m1h(y_g, gate_out(row[s], s), x_hop, GPAD)
            b.v13(x_hop, y_g)
            b.m3h(y_g, x_hop, s * x_lane0)
        b.m3v(-x_lane0, bias[0][-1].y_g, y_g)
        b.m3v(x_lane0, bias[0][1].y_g, y_g)
    for s in HALVES:
        b.m3v(s * x_lane0, y_bot_pin, bias[0][s].y_g)
    b.m3h(y_bot_pin, -x_lane0, x_lane0)
    b.rect("Metal3drawing", -2.0, y_bot_pin - 1.0, 2.0, y_bot_pin + 1.0)
    b.label("vbn", 0, y_bot_pin, "Metal3text")

    # ---- vbp: an isolated labelled Metal1 pad (dangling port, BRIEF §9) ---
    b.rect("Metal1drawing", 10.0, y_bot_pin - 1.0, 14.0, y_bot_pin + 1.0)
    b.label("vbp", 12.0, y_bot_pin)

    # ---- vbr: xr3 drains (bias rows 1 & 3) -> xr2 + the two bridge gates --
    for r in (0, 2):
        y_d = bias[r][-1].y_d
        b.m1h(y_d, bias[r][-1].x_in_d, bias[r][1].x_in_d, ws)
        b.v12(0, y_d)

    # ---- net2 / net3: xc13 top plate -> xm9.D -> xm4.G -> xm2.D ----------
    for s in HALVES:
        m9, m4, m2 = bias[1][s], gmfa[s], ina[s]
        b.m1h(m9.y_d, m9.x_in_d, s * LANE_MID, ws)
        b.v12(s * LANE_MID, m9.y_d)
        b.m1h(m4.y_g, s * LANE_MID, gate_in(m4, s), GPAD)
        b.v12(s * LANE_MID, m4.y_g)
        b.m1h(m2.y_d, m2.x_in_d, s * LANE_MID, ws)
        b.v12(s * LANE_MID, m2.y_d)
        b.m2v(s * LANE_MID, y_tm, m2.y_d)
        b.label("net2" if s < 0 else "net3", s * LANE_MID, (y_tm + m2.y_d) / 2, "Metal2text")
        b.m2h(y_tm, s * LANE_MID, s * x_drop)           # TopMetal1 drop, in-channel
        b.vstack(s * x_drop, y_tm, "Metal1", "TopMetal1")
    for s, arr in ((-1, a13), (1, a17)):
        b.v("TopMetal1drawing", arr["spine"], arr["y1"] - 1.0, y_tm, p.w_tm1)
        b.h("TopMetal1drawing", y_tm, arr["spine"], s * x_drop, p.w_tm1)

    # ---- vout_1 / vout_2 ---------------------------------------------------
    for s in HALVES:
        m4, m2, m0, mst = gmfa[s], ina[s], inb[s], brdg[s]
        b.m1h(m4.y_d, m4.x_in_d, s * LANE_IN, ws)
        b.v12(s * LANE_IN, m4.y_d)
        b.m1h(m2.y_s, m2.x_in_s, s * LANE_IN, ws)
        b.v12(s * LANE_IN, m2.y_s)
        b.m1h(m0.y_g, gate_in(m0, s), s * LANE_IN, GPAD)
        b.v12(s * LANE_IN, m0.y_g)
        b.m2v(s * LANE_IN, y_v1, m0.y_g)                # one continuous lane
        b.label("vout_1" if s < 0 else "vout_2", s * LANE_IN, (y_v1 + m0.y_g) / 2, "Metal2text")
        b.v23(s * LANE_IN, y_v1)
        # xmst.D hops to Metal2 at its own column (xr2 owns Metal1 near the axis)
        y_t = y_shield + p.shield_w / 2 + 1.5
        b.v12(mst.x_in_d, mst.y_d)
        b.m2v(mst.x_in_d, y_t, mst.y_d)
        b.m2h(y_t, mst.x_in_d, s * LANE_IN)
    # bank A exits
    xv1 = a19["x0"] + a19["side"] / 2
    b.rect("Metal5drawing", xv1 - 1.5, a19["y1"] - 1.0, xv1 + 1.5, y_v1)
    b.vstack(xv1, y_v1, "Metal1", "Metal5")
    b.m3h(y_v1, xv1, -LANE_IN)
    xv2 = a17["x0"] + a17["side"] / 2
    b.rect("Metal5drawing", xv2 - 1.5, a17["y1"] - 1.0, xv2 + 1.5, y_v1)
    b.vstack(xv2, y_v1, "Metal1", "Metal5")
    b.m3h(y_v1, xv2, LANE_IN)
    xv3 = a19["x1"] - a19["side"] / 2                    # xc19 top plate (vout_2)
    b.v("TopMetal1drawing", xv3, a19["y1"] - 1.0, y_v1, p.w_tm1)
    b.vstack(xv3, y_v1, "Metal1", "TopMetal1")

    # ---- island B: the shared vbr gate bar + xr2's diode tie -------------
    y_gb = brdg[-1].y_g
    b.m1h(y_gb, brdg[-1].gates[0] - GPAD / 2, brdg[1].gates[-1] + GPAD / 2, GPAD)
    b.m1v(xr2.x_in_d, xr2.y_g, xr2.y_d, ws)
    b.m1h(xr2.y_d, xr2.x_in_d, xr2.x_in_d, ws)
    b.v12(0, y_gb)
    b.m2v(0, bias[0][-1].y_d, y_gb)                      # the vbr spine
    b.label("vbr", 0, (bias[0][-1].y_d + y_gb) / 2, "Metal2text")

    # ---- rep_x: xr2.S -> xr1.D/G ------------------------------------------
    if len(xr1s) > 1:      # join the two anti-oriented halves' drains and gates
        b.m1h(xr1.y_d, xr1s[0].x_in_d, xr1s[1].x_in_d, ws)
        b.m1h(xr1.y_g, xr1s[0].gates[0], xr1s[1].gates[0], GPAD)
    b.m1h(xr2.y_s, xr2.x_in_s, 0, ws)
    b.v12(0, xr2.y_s)
    b.v12(0, xr1.y_d)
    b.m2v(0, xr2.y_s, xr1.y_d)
    b.label("rep_x", 0, (xr2.y_s + xr1.y_d) / 2, "Metal2text")

    # ---- net4 / net1: xmst.S -> xm0.D -> xm14.G -> xc1 top plate ---------
    for s in HALVES:
        mst, m0, m14 = brdg[s], inb[s], gmfb[s]
        x_hop = s * (abs(xr2.x_hi) + gap_p / 2)
        b.m1h(mst.y_s, mst.x_in_s, x_hop, ws)
        b.v12(x_hop, mst.y_s)
        b.m2h(mst.y_s, x_hop, s * LANE_MID)
        b.m1h(m0.y_d, m0.x_in_d, s * LANE_MID, ws)
        b.v12(s * LANE_MID, m0.y_d)
        x_hop2 = s * (x_xr1_hi + gap_w / 2)
        b.m1h(m14.y_g, gate_in(m14, s), x_hop2, GPAD)
        b.v12(x_hop2, m14.y_g)
        b.m2h(m14.y_g, x_hop2, s * LANE_MID)
        b.m2v(s * LANE_MID, mst.y_s, y_n4)
        b.label("net4" if s < 0 else "net1", s * LANE_MID, (mst.y_s + y_n4) / 2, "Metal2text")
        b.v23(s * LANE_MID, y_n4)
    for s, arr in ((-1, b1), (1, b10)):
        b.v("TopMetal1drawing", arr["spine"], arr["y0"] + 1.0, y_n4, p.w_tm1)
        b.vstack(arr["spine"], y_n4, "Metal1", "TopMetal1")
        b.m3h(y_n4, arr["spine"], s * LANE_MID)

    # ---- voutp / voutn: xm0.S -> xm14.D -> xc1 bottom plate (+ side pins) -
    for s in HALVES:
        m0, m14 = inb[s], gmfb[s]
        b.m1h(m0.y_s, m0.x_in_s, s * LANE_IN, ws)
        b.v12(s * LANE_IN, m0.y_s)
        x_hop2 = s * (x_xr1_hi + gap_w / 2)
        b.m1h(m14.y_d, m14.x_in_d, x_hop2, ws)
        b.v13(x_hop2, m14.y_d)
        b.m3h(m14.y_d, x_hop2, s * LANE_IN)              # Metal3: crosses net4
        b.v23(s * LANE_IN, m14.y_d)
        b.m2v(s * LANE_IN, m0.y_s, y_vo)
        b.v23(s * LANE_IN, y_vo)
        b.v23(s * LANE_IN, m0.y_s)
        b.m3h(m0.y_s, s * LANE_IN, s * x_pin3)           # side pin (Metal3: the
        b.rect("Metal3drawing", s * x_pin3 - 1.0, m0.y_s - 1.0,  # net4 lane is Metal2)
               s * x_pin3 + 1.0, m0.y_s + 1.0)
        b.label("voutp" if s < 0 else "voutn", s * x_pin3, m0.y_s, "Metal3text")
    for s, arr in ((-1, b1), (1, b10)):
        xm = arr["x1"] - arr["side"] / 2 if s < 0 else arr["x0"] + arr["side"] / 2
        b.rect("Metal5drawing", xm - 1.5, y_vo, xm + 1.5, arr["y0"] + 1.0)
        b.vstack(xm, y_vo, "Metal1", "Metal5")
        b.m3h(y_vo, xm, s * LANE_IN)
    # xc12: bottom plate (voutp) -> xc1 sheet; top plate (voutn) -> xc10 sheet
    b.rect("Metal5drawing", b1["x0"] + 2.0, b1["y1"] - 1.0, b1["x0"] + 8.0, b12["y0"] + 1.0)
    b.rect("Metal5drawing", b1["x0"] + 2.0, b12["y0"], b12["x0"] + 1.0, b12["y0"] + 4.0)
    xtc = b10["x1"] - b10["side"] / 2
    b.v("TopMetal1drawing", b12["x1"] - 2.0, b12["y0"] + 1.0, b12["y0"] - 4.0, p.w_tm1)
    b.h("TopMetal1drawing", b12["y0"] - 4.0, b12["x1"] - 2.0, xtc, p.w_tm1)
    b.vstack(xtc, b12["y0"] - 4.0, "Metal5", "TopMetal1")
    b.rect("Metal5drawing", xtc - 1.5, b12["y0"] - 4.0, xtc + 1.5, b10["y1"] - 1.0)

    # ---- vinp / vinn: xm2 gate -> side pins -------------------------------
    for s in HALVES:
        m2 = ina[s]
        x_hop = outer(m2, s) + s * 0.6
        b.m1h(m2.y_g, gate_out(m2, s), x_hop, GPAD)
        b.v12(x_hop, m2.y_g)
        b.m2h(m2.y_g, x_hop, s * x_pin)
        b.rect("Metal2drawing", s * x_pin - 1.0, m2.y_g - 1.0, s * x_pin + 1.0, m2.y_g + 1.0)
        b.label("vinp" if s < 0 else "vinn", s * x_pin, m2.y_g, "Metal2text")

    # ---- vdd: the gmf_b source plate -> M3 outer lanes -> top pin ---------
    for s in HALVES:
        b.v13(s * (x_gmfb - 2.0), y_gmfb_tap)
        b.m3h(y_gmfb_tap, s * (x_gmfb - 2.0), s * x_lane1)
        b.m3v(s * x_lane1, y_gmfb_tap, y_ring_hi - p.ring_w - 2.0)
    b.m3h(y_ring_hi - p.ring_w - 2.0, -x_lane1, x_lane1)
    b.rect("Metal3drawing", -2.0, y_ring_hi - p.ring_w - 3.0, 2.0, y_ring_hi - p.ring_w - 1.0)
    b.label("vdd", 0, y_ring_hi - p.ring_w - 2.0, "Metal3text")

    return c


# --------------------------------------------------------------------------
# LVS reference (PLAN §7) — always regenerated from the certified netlist
# --------------------------------------------------------------------------
def write_lvs_reference(params: LayoutParams = LayoutParams(),
                        out: str | os.PathLike | None = None,
                        core_sp: str | os.PathLike | None = None) -> str:
    """`core.sp` -> the flat M/C-card netlist the KLayout LVS deck compares against.

    Three mechanical edits on top of ``postlayout.to_lvs_reference`` (PLAN §7):
    ``0`` -> ``vss`` (+ the pin), the ``xc1``/``xc10`` terminal swap (the drawn
    Metal5 bottom plate is ``voutp``/``voutn``), and one card per dummy group.
    """
    from spicexplorer_signoff.postlayout import to_lvs_reference

    here = Path(__file__).resolve().parent
    core_sp = Path(core_sp) if core_sp else \
        here.parents[1] / "signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp"
    ref = to_lvs_reference(Path(core_sp).read_text(), "lpf_core")
    dv = _devs(None)
    lines = []
    for ln in ref.splitlines():
        t = ln.split()
        if ln.startswith(".subckt"):
            ln = ln + " vss"
        elif t and t[0].lower() in ("cc1", "cc10"):          # plate flip
            ln = " ".join([t[0], t[2], t[1]] + t[3:])
        if not ln.startswith("."):
            ln = " ".join(w if w != "0" else "vss" for w in ln.split())
        lines.append(ln)
    dum = []
    n_n = 2 * 3 * params.bias_dummy_cols
    if n_n:
        d = dv["bias_a_int"]
        dum.append(f"Mdumn vss vss vss vss sg13_hv_nmos w={n_n * d['w']:g}u l={d['l']:g}u")
    n_p = 2 * params.gmfb_dummy
    if n_p:
        d = dv["gmf_b"]
        dum.append(f"Mdump vdd vdd vdd vdd sg13_hv_pmos w={n_p * d['w']:g}u l={d['l']:g}u")
    i = lines.index(".ends lpf_core")
    text = "\n".join(lines[:i] + dum + lines[i:]) + "\n"
    out = Path(out) if out else here / "asbuilt/core_lvs.sp"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(text)
    return text


def write_pex_gds(gds_in: str | os.PathLike, gds_out: str | os.PathLike,
                  cell: str = CELL) -> str:
    """Strip the MIM devices from a copy of the GDS so **kpex 2.5D can run**.

    klayout-pex 0.3.12 ships an ihp-sg13g2 tech in which the MIM top layer
    (``cmim_top``, GDS 36/0) is called ``"<TODO>"``: the 2.5D engine dies with
    ``KeyError: '<TODO>'`` on any layout containing a ``cap_cmim``.  The PEX copy
    therefore drops MIM (36/0), Vmim (129/0) and the TopMetal1 *plates*
    (TopMetal1 minus MIM oversized by 0.2 um — the TopMetal1 hauls and via-stack
    pads survive), and the six ``cap_cmim`` cards are re-inserted into the PEX
    netlist verbatim from the certified schematic.

    Consequences, both recorded in REPORT.md: the Metal5 **bottom-plate**
    capacitance to substrate (the point of the BRIEF §6 plate flip) *is*
    extracted, the top-plate-to-neighbour capacitance is *not* (in silicon it is
    screened by the bottom plate directly underneath it).
    """
    import klayout.db as kdb

    ly = kdb.Layout()
    ly.read(str(gds_in))
    top = ly.cell(cell) or ly.top_cell()
    l_mim, l_vmim = ly.layer(36, 0), ly.layer(129, 0)
    l_tm1 = ly.layer(126, 0)
    mim = kdb.Region(top.begin_shapes_rec(l_mim)).merged()
    tm1 = kdb.Region(top.begin_shapes_rec(l_tm1)).merged()
    keep = tm1 - mim.sized(200)          # 0.2 um, in dbu
    for c in ly.each_cell():
        c.shapes(l_mim).clear()
        c.shapes(l_vmim).clear()
        c.shapes(l_tm1).clear()
    top.shapes(l_tm1).insert(keep)
    ly.write(str(gds_out))
    return str(gds_out)


def main() -> None:
    ap = argparse.ArgumentParser(description="generate the H12-pdk-cap layout")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--params", default=None, help='JSON overrides, e.g. {"row_gap": 8}')
    ap.add_argument("--lvs", action="store_true", help="write asbuilt/core_lvs.sp and exit")
    ap.add_argument("--pex-gds", default=None, metavar="OUT",
                    help="write the MIM-stripped copy of --out used for kpex (see write_pex_gds)")
    ap.add_argument("--pex-lvs", default=None, metavar="OUT",
                    help="write the matching kpex schematic (core_lvs.sp without the C cards)")
    a = ap.parse_args()
    p = LayoutParams(**json.loads(a.params)) if a.params else LayoutParams()
    if a.lvs:
        print(write_lvs_reference(p))
        return
    comp = build(p)
    out = a.out or os.path.join(os.path.dirname(__file__), "build", f"{CELL}.gds")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    comp.write_gds(out)
    if a.pex_gds:
        write_pex_gds(out, a.pex_gds)
        print(f"wrote {a.pex_gds} (MIM stripped, for kpex)")
    if a.pex_lvs:
        ref = (Path(__file__).resolve().parent / "asbuilt/core_lvs.sp").read_text()
        Path(a.pex_lvs).write_text(
            "\n".join(ln for ln in ref.splitlines() if not ln.startswith("Cc")) + "\n")
        print(f"wrote {a.pex_lvs} (kpex schematic, MIM devices removed)")
    bb = comp.bbox()
    print(f"wrote {out}: {bb}, area {(bb.right - bb.left) * (bb.top - bb.bottom) / 1e6:.4f} mm2")


if __name__ == "__main__":
    main()
