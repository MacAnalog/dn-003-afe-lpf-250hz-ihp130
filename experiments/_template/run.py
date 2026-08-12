"""Experiment NNN -- <technique>: the canonical run loop.

Copy this file with the directory.  It is deliberately short: the harness does
the work, and an experiment script's only job is to say WHICH designs are
compared and WHY.

The contract this file encodes (CLAUDE.md rules 2-4, 9):

    1. Decks are BUILT from a `Design`, never text-edited.  Mutating a Design
       and letting `lab.deck` regenerate every deck is what makes it impossible
       to score one sizing's netlist with another sizing's measurement.
    2. The untouched reference baseline is ALWAYS the first row -- measured in
       this session, on this PDK, with this simulator build.
    3. If any capacitor moves, the CONTROL is the same capacitance
       re-allocation without the technique.  Without it you have measured a cap
       re-shuffle, not a technique.
    4. The finding is the table.  Prose is interpretation.
    5. Expensive runs are gated: `lab.metrics.gate` refuses a transient on a
       design that fails the cheap hard box.  Do not work around it.

Run it:  python experiments/NNN-<technique>/run.py
Ledger:  export LPF_EXP=NNN first, then `python scripts/runs.py --exp NNN`.
"""
from __future__ import annotations

import json

from lab import config as C
from lab import metrics as M
from lab import parallel
from lab.dut import Dev, Design

# --------------------------------------------------------------- reference --


def reference() -> Design:
    """The frozen, certified reference baseline -- the yardstick, from disk.

    Loaded from `decks/reference/design.json` rather than retyped, so this
    experiment cannot silently drift from the thing it is compared against.
    Certified scorecard: fc 250.00 Hz, dc -0.0047 dB, peaking 0.023 dB,
    |H|@1 kHz -48.43 dB, ph_max 346.43 deg, IRN 50.18 uVrms, core 8.04 nA /
    12.07 nW, 98.01 pF total drawn C.
    """
    j = json.loads((C.DECK_DIR / "design.json").read_text())
    caps = j["caps_pf"]
    return Design(
        topology=j["topology"],
        devs={k: Dev(v["w"], v["l"], int(v.get("ng", 1)), int(v.get("m", 1)))
              for k, v in j["devs"].items()},
        c1_a=caps["c1_a"] * 1e-12, c2_a=caps["c2_a"] * 1e-12,
        c1_b=caps["c1_b"] * 1e-12, c2_b=caps["c2_b"] * 1e-12,
        iref=j["iref"],
        note="frozen reference baseline (decks/reference/design.json)",
    )


# ----------------------------------------------------------------- variants --

def variant(base: Design) -> Design:
    """The technique under test.

    Express it as a mutation of `base` -- `Design.with_(...)` and
    `Design.scaled_caps(k)` return copies, so nothing is edited in place.
    Everything not named here is held identical to the reference BY
    CONSTRUCTION, which is what makes the comparison honest.
    """
    devs = dict(base.devs)
    # e.g. the mechanism under test -- longer, wider input followers:
    # devs["in_a"] = Dev(8e-6, 8e-6)
    # devs["in_b"] = Dev(8e-6, 8e-6)
    return base.with_(devs=devs, note="variant: <what changed and why>")


def control(base: Design) -> Design:
    """The cap re-allocation with NO technique -- required whenever caps move.

    If the variant leaves every capacitor untouched, delete this function and
    say so in the README; otherwise it is not optional.
    """
    return base.with_(note="control: same caps as the variant, reference devices")


# --------------------------------------------------------------------- main --

def main() -> None:
    base = reference()
    cells = {
        "reference": base,          # rule: the baseline is always row 1
        "control": control(base),
        "variant": variant(base),
    }

    # One process per design; LPF_JOBS caps the width (default cpu_count()-2).
    names = list(cells)
    scores = parallel.batch(
        names, lambda n: M.evaluate(cells[n], f"NNN-{n}"), on_error="keep"
    )

    rows: dict[str, M.Score] = {}
    for name, s in zip(names, scores):
        if isinstance(s, Exception):
            # NEVER hide a failed run: report it as a row with its error.
            print(f"!! {name}: {type(s).__name__}: {s}")
            continue
        rows[name] = s

    print(M.table(rows))
    for name, s in rows.items():
        if not s.ok:
            print(f"\n{name}: {M.explain(s)}")

    # ---- expensive step, gated (rule 9) -----------------------------------
    # `gate` re-scores cheaply and refuses to spend a transient unless the hard
    # box passes; S5 is allowed to fail because S5 is the goal being worked on.
    try:
        M.gate(cells["variant"], "NNN-variant-gate")
    except M.Gated as exc:
        print(f"\nTHD skipped -- {exc}")
    else:
        print("\nvariant passes the hard box: THD run is justified "
              "(fin = 50 Hz, ampl = 87.5 mV differential = 175 mVpp).")


if __name__ == "__main__":
    main()
