"""The run ledger: append-only episodic memory of every simulation.

Every `evaluate()` / THD / corner / Monte-Carlo run writes one NDJSON row here
automatically.  Nobody has to remember to log; the point is that a claim made in
a README can always be traced back to a row, and a later contradicting row
REVOKES an earlier sign-off.

The ledger is `runs/ledger.ndjson`, repo-relative and git-ignored: it is local
observability, not a deliverable.  Numbers *graduate* from the ledger into an
experiment README when they become keepers -- that promotion is the semantic
write, and it is deliberate (doc/memory/README.md).
"""
from __future__ import annotations

import hashlib as _hashlib
import json
import os
import platform
import time
from pathlib import Path

from . import config as C

LEDGER = C.REPO / "runs" / "ledger.ndjson"


def log_run(tag: str, values: dict, *, deck: str = "", design=None,
            corner: str = C.CORNER_NOM, temp: float = C.TEMP_NOM,
            wall: float = float("nan"), violations: list[str] | None = None,
            kind: str = "evaluate", extra: dict | None = None) -> dict:
    from .ngspice import deck_hash

    row = {
        "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tag": tag,
        "kind": kind,
        "exp": os.environ.get("LPF_EXP", ""),
        "topology": getattr(design, "topology", ""),
        "corner": corner,
        "temp": temp,
        "vdd": C.VDD,
        "deck": deck_hash(deck) if deck else "",
        "wall_s": round(wall, 3) if wall == wall else None,
        "host": platform.node(),
        "lane": C.lane(),
        "violations": violations or [],
        "goal_met": not (violations or []),
    }
    row.update({k: _clean(v) for k, v in values.items()})
    if design is not None:
        row["design"] = design_dict(design)
    if extra:
        row.update(extra)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row


def design_dict(design) -> dict:
    """A `Design` as plain JSON -- enough to rebuild the exact netlist later.

    `vicm`/`vocm` are in here because they are NOT bench trivia: `vicm` sets the
    input common mode, so it moves every device's operating point and therefore
    fc, IRN and THD.  Rows written before 2026-08-11 omit them, and a design
    rebuilt from one of those rows silently falls back to the dataclass defaults
    (0.25 / 1.25) -- which is a different circuit from a cell sized at 0.20 /
    1.10.  Rebuilders must therefore CHECK a reconstruction against the row's
    own recorded metrics rather than trust it (see experiments/.../state.py).
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


def _clean(v):
    if isinstance(v, float):
        return None if v != v else round(v, 9)
    return v


def read(path: Path | None = None) -> list[dict]:
    p = Path(path or LEDGER)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows
