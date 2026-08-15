"""Shared machinery for experiment 023: replica-biased ladder + headroom.

Everything here builds on 021's `common.py` (cap re-synthesis at equal shape)
and adds the two instruments this experiment needs:

* `replica(design, k)`  -- re-issue any merged (b/c) sizing as topology `d`
  with a matched replica sinking `k * iref`;
* `headroom(design, corners)` -- op-only probe of every device's saturation
  margin at a set of corners; the sizing instrument for the ladder budget
  `VDD - vicm = |V_SG|(in_a) + |V_SG|(in_b) + |V_SD|(gmf_b)`.

The one-axis corner sets (`PROCESS_ONLY`, `SUPPLY_ONLY`, `TEMP_ONLY`, `AXES`)
were born here and now live in `lab.corners`; `PROCESS_ONLY` is the set the
sign-off screen was missing (COMPARISON.md).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lab import config as C                      # noqa: E402
from lab import corners as K                     # noqa: E402
from lab import metrics as M                     # noqa: E402
from lab import oppoint as O                     # noqa: E402
from lab.dut import Design, Dev, replica_of      # noqa: E402
from lab.parallel import batch                   # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "c021", REPO / "experiments" / "021-publication-cell" / "common.py")
c021 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c021)
synth_from, full, gms, caps_for = c021.synth_from, c021.full, c021.gms, c021.caps_for

from build_signoff import design_of              # noqa: E402

SIGNOFF = REPO / "signoff" / "pre-pvt"      # the original nine cells (moved 2026-08-15)


def load_cell(name: str) -> Design:
    """A sign-off cell's sizing of record (topology b, as certified)."""
    return design_of(json.loads((SIGNOFF / name / "design.json").read_text())["design"])


def replica(d: Design, k: float) -> Design:
    return replica_of(d, k)


def to_json(d: Design) -> dict:
    return {"topology": d.topology, "iref": d.iref, "vicm": d.vicm, "vocm": d.vocm,
            "vmid": d.vmid, "lv_roles": sorted(d.lv_roles),
            "caps_pf": {k: getattr(d, k) * 1e12 for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
            "devs": {r: {"w": g.w, "l": g.l, "ng": g.ng, "m": g.m} for r, g in d.devs.items()}}


def from_json(g: dict) -> Design:
    return design_of(g)


# ------------------------------------------------------------ corner sets --
NOM = K.NOMINAL
#: one-axis-at-a-time sets -- graduated into `lab.corners` (PROCESS_ONLY,
#: SUPPLY_ONLY, TEMP_ONLY, AXES) once this experiment showed the 22-point
#: screen could not separate a process failure from a headroom one.
PROCESS_ONLY, SUPPLY_ONLY, TEMP_ONLY, AXES = K.PROCESS_ONLY, K.SUPPLY_ONLY, K.TEMP_ONLY, K.AXES
#: temperature envelope at the nominal rail (report-only sweep).
TSWEEP = tuple(K.Corner(C.CORNER_NOM, t, C.VDD) for t in (-40, -20, 0, 27, 55, 70, 85, 100, 125))
#: the vertices that decide headroom, for the op-only screen.
HEADROOM = (
    K.Corner("mos_tt", 27.0, K.VDDS[0]), K.Corner("mos_tt", 27.0, K.VDDS[-1]),
    K.Corner("mos_tt", -40.0, K.VDDS[0]), K.Corner("mos_tt", -40.0, K.VDDS[-1]),
    K.Corner("mos_tt", 125.0, K.VDDS[0]), K.Corner("mos_tt", 125.0, K.VDDS[-1]),
    K.Corner("mos_ss", 27.0, C.VDD), K.Corner("mos_ff", 27.0, C.VDD),
    K.Corner("mos_ss", -40.0, K.VDDS[0]), K.Corner("mos_ff", 125.0, K.VDDS[-1]),
)

SIGNAL_ROLES = ("in_a", "gmf_a", "bias_a_int", "bridge", "in_b", "gmf_b")


def headroom(d: Design, tag: str, corners=HEADROOM, workers: int | None = None) -> dict:
    """Per-corner saturation margin of every device (op only, no caps needed).

    Returns {corner.slug: {"margin_mv": min over signal devices of
    |Vds| - max(4kT/q, vdsat), "worst": role, "iL_na": bridge current,
    "ig_a_na": gmf_a current, "sat": all signal devices saturated}}.
    A collapsed ladder shows up as ig_a_na ~ 0 (gmf_a starved).
    """
    def one(c: K.Corner) -> dict:
        try:
            ops, volts = O.probe(d, f"{tag}_{c.slug}", corner=c.process,
                                 temp=c.temp, vdd=c.vdd)
        except Exception as exc:                        # noqa: BLE001
            return {"error": str(exc)[:120]}
        margins = {}
        for r in SIGNAL_ROLES:
            o = ops[r]
            floor = max(O.VDS_FLOOR, o.vdsat if o.vdsat == o.vdsat else 0.0)
            margins[r] = (o.vds - floor) * 1e3
        worst = min(margins, key=margins.get)
        return {"margin_mv": margins[worst], "worst": worst,
                "margins": {r: round(v, 1) for r, v in margins.items()},
                "iL_na": ops["bridge"].id_na, "ig_a_na": ops["gmf_a"].id_na,
                "sat": all(ops[r].saturated for r in SIGNAL_ROLES),
                "voutp": volts.get("v(voutp)"), "vout_1": volts.get("v(xdut.vout_1)")}
    res = batch(list(corners), one, workers=workers)
    return {c.slug: r for c, r in zip(corners, res)}


def worst_margin(hr: dict) -> float:
    vals = [r.get("margin_mv", -1e9) for r in hr.values()]
    return min(vals) if vals else -1e9
