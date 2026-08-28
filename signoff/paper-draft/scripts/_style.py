"""Figure style for the reviewer pack -- the paper pack's `_style`, re-homed.

Identical rcParams and colour cycle as `doc/paper/scripts/_style.py`, so a figure can move
between the two packs unchanged; only the output directory differs.  Loaded by file path
rather than by name because both modules are called `_style` and importing by name from a
module of the same name is a circular import.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3] / "doc/paper/scripts/_style.py"
_spec = importlib.util.spec_from_file_location("_paper_style", _SRC)
_paper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_paper)

COL, WIDE, DPI = _paper.COL, _paper.WIDE, _paper.DPI
OK, BAD, GREY, CYCLE = _paper.OK, _paper.BAD, _paper.GREY, _paper.CYCLE
note, use = _paper.note, _paper.use

FIGS = Path(__file__).resolve().parents[1] / "figures"


def save(fig, name: str) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIGS / f"{name}.{ext}")
    w, h = fig.get_size_inches()
    print(f"wrote {FIGS / (name + '.png')}  ({round(w * DPI)}x{round(h * DPI)} px)")
