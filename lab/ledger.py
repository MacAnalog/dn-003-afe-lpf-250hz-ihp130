"""The run ledger (append-only episodic memory), via the platform package.

This shim adds what is specific to this repo: the `topology` / `vdd` / `lane` row fields and
the `Design` serialization.  `runs/ledger.ndjson` stays repo-relative and git-ignored; keeper
numbers graduate into experiment READMEs (doc/memory/README.md).
"""
from __future__ import annotations

import hashlib as _hashlib
from pathlib import Path

from spicexplorer_harness import ledger as _L

from . import config as C

LEDGER = C.REPO / C.H.ledger


def log_run(tag: str, values: dict, *, deck: str = "", design=None,
            corner: str = C.CORNER_NOM, temp: float = C.TEMP_NOM,
            wall: float = float("nan"), violations: list[str] | None = None,
            kind: str = "evaluate", extra: dict | None = None) -> dict:
    fields = {"topology": getattr(design, "topology", ""), "vdd": C.VDD, "lane": C.lane(),
              **(extra or {})}
    return _L.log_run(C.H, tag, values, kind=kind, corner=corner, temp=temp, deck=deck,
                      wall=wall, violations=violations,
                      design=None if design is None else design_dict(design), extra=fields)


def design_dict(design) -> dict:
    """A `Design` as plain JSON -- enough to rebuild the exact netlist later.

    `vicm`/`vocm` are in here because they move every operating point and therefore fc, IRN
    and THD.  Rows written before 2026-08-11 omit them, so a rebuilder must CHECK its
    reconstruction against the row's recorded metrics (experiments/.../state.py).
    """
    ov = getattr(design, "dut_override", None)
    return {
        "topology": design.topology,
        "iref": design.iref,
        # sha of a verbatim DUT override (post-layout PEX / injected variant); absent = built
        **({"dut_override_sha": _hashlib.sha256(ov.encode()).hexdigest()[:16]} if ov else {}),
        "vicm": design.vicm,
        "vocm": design.vocm,
        "caps_pf": {k: round(getattr(design, k) * 1e12, 6)
                    for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
        "devs": {role: {"w": d.w, "l": d.l, "ng": d.ng, "m": d.m}
                 for role, d in design.devs.items()},
    }


def read(path: Path | None = None) -> list[dict]:
    return _L.read(Path(path) if path else C.H)
