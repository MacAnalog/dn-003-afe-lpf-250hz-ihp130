"""Fit the experiment-020 cells to the Butterworth template and re-score them.

020's certified cells were signed off before the passband SHAPE was scored, on
a sweep density that could step over a mid-band sag.  Re-measured densely, 020B
carries 1.46 dB of passband droop -- it sags and recovers, which `peak_db` reads
as 0.000 dB and `ripple_db` (added later) reads as a failure.

That matters because 020B is otherwise the strongest cell in the repo: THD
-49.83 dB and IRN 34.04 uV, i.e. ~10 dB of S7 margin and ~6 uV of S5 margin
where the 021 candidates have ~1 dB and ~0.5 uV.  If its shape can be repaired
without spending that margin, it is the publication cell.

Each entry is fitted with devices held fixed -- only the four capacitors move --
so any change in IRN is the capacitance moving, not the transistors.  That makes
the fit its own re-allocation control (CLAUDE.md rule 3).

    uv run python experiments/021-publication-cell/fitcells.py [name ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common as K                                      # noqa: E402
from lab.dut import Design, Dev                         # noqa: E402
from lab.parallel import batch                          # noqa: E402

OUT = HERE / "fitcells.json"
FROZEN = HERE.parent / "020-novel-topologies" / "frozen"


def from_json(path: Path) -> Design:
    d = json.loads(path.read_text())
    return Design(topology=d["topology"],
                  devs={r: Dev(**g) for r, g in d["devs"].items()},
                  iref=d.get("iref", 1e-9),
                  vicm=d.get("vicm", 0.25), vocm=d.get("vocm", 1.25),
                  **{k: v * 1e-12 for k, v in d["caps_pf"].items()})


def cells() -> dict:
    out = {"020B-frozen": from_json(FROZEN / "020B.json"),
           "020C-frozen": from_json(FROZEN / "020C.json")}
    # The 314.6 pF 020B the 020 README certifies, from the ledger's own row.
    from lab import ledger as L
    for r in L.read():
        if r.get("tag") == "cert_020B" and (r.get("design") or {}).get("devs"):
            d = r["design"]
            out["020B-cert"] = Design(
                topology=d["topology"],
                devs={k: Dev(**g) for k, g in d["devs"].items()},
                iref=d.get("iref", 1e-9),
                vicm=d.get("vicm") or 0.32, vocm=d.get("vocm") or 1.10,
                **{k: v * 1e-12 for k, v in d["caps_pf"].items()})
            break
    return out


def main() -> None:
    want = sys.argv[1:]
    todo = {k: v for k, v in cells().items() if not want or k in want}
    print(f"fitcells: {list(todo)}", flush=True)

    def one(item):
        name, d0 = item
        try:
            before = K.full(d0, f"fc_{name}_pre", thd=False)
            d1 = K.synth_from(d0, f"fc_{name}", polish=260)
            row = K.full(d1, f"fc_{name}_post")
            row["name"], row["before"] = name, before
            print("  BEFORE " + K.line(before), flush=True)
            print("  AFTER  " + K.line(row), flush=True)
            return row
        except Exception as exc:                          # noqa: BLE001
            return {"name": name, "error": repr(exc)}

    rows = [r for r in batch(list(todo.items()), one, workers=2)
            if not isinstance(r, Exception)]
    OUT.write_text(json.dumps(rows, indent=2))
    for r in rows:
        if "error" in r:
            print(f"{r['name']}: ERROR {r['error'][:120]}")


if __name__ == "__main__":
    main()
