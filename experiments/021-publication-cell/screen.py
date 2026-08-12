"""Which device actually sets THD?  One-at-a-time, at equal shape.

S7 is the only line the flat cell misses (THD -35.8 dB against -40), and it has
12.8 uV of S5 margin and 43 nW of S6 margin to spend buying it back.  Spending
them intelligently needs to know WHICH device the distortion lives in, and the
existing evidence does not say: the four cells measured so far differ in several
devices at once, so their 13 dB THD spread is unattributable.

This is the attribution.  Each arm perturbs ONE role by one factor and leaves
everything else alone -- then RE-SYNTHESISES the four capacitors from that arm's
own measured gm, so every arm is scored at the same 250 Hz Butterworth shape.
Without that step the sweep would measure detuning, not linearity.

Read the result as a sensitivity, not a design: the winning direction is the
one to walk in `walk.py`, and a single arm is one point on a curve.

    uv run python experiments/021-publication-cell/screen.py [q_b]

`q_b` selects biquad B's Q (default: whichever assignment `qsplit.py` found
better).  Everything else follows from it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common as K                                      # noqa: E402
from qsplit import load                                 # noqa: E402
from lab.parallel import batch, jobs                    # noqa: E402

OUT = HERE / "screen.json"

# The four roles the distortion could plausibly live in, plus the two that set
# biquad A.  `bridge` and `gmf_b` are in here because in the merged topology
# they jointly fix the whole B-branch current (V_SG(gmf_b) + V_SG(bridge) = VDD),
# so they are the only handles on that branch's inversion level.
ARMS = [
    ("in_b",       "w", 2.0), ("in_b",       "w", 0.5),
    ("in_b",       "l", 2.0), ("in_b",       "l", 0.5),
    ("gmf_b",      "w", 2.0), ("gmf_b",      "w", 0.5),
    ("gmf_b",      "l", 2.0), ("gmf_b",      "l", 0.5),
    ("bridge",     "w", 2.0), ("bridge",     "w", 0.5),
    ("bridge",     "l", 2.0), ("bridge",     "l", 0.5),
    ("in_a",       "w", 2.0), ("in_a",       "l", 2.0),
    ("gmf_a",      "w", 2.0), ("gmf_a",      "l", 2.0),
    ("bias_a_int", "w", 2.0), ("bias_a_int", "l", 2.0),
]


def perturb(base, role: str, knob: str, factor: float):
    dev = base.devs[role]
    return base.with_(devs={**base.devs,
                            role: dev.__class__(**{**vars(dev),
                                                   knob: getattr(dev, knob) * factor})})


def main() -> None:
    q_b = float(sys.argv[1]) if len(sys.argv) > 1 else K.Q_LO
    q_a = K.Q_HI if abs(q_b - K.Q_LO) < 1e-6 else K.Q_LO
    base = load()
    print(f"screen: Q_A={q_a:.4f} Q_B={q_b:.4f}, {len(ARMS)} arms "
          f"on {jobs()} workers", flush=True)

    def one(arm):
        role, knob, factor = arm
        name = f"{role}.{knob}x{factor:g}"
        try:
            d = base if factor == 1.0 else perturb(base, role, knob, factor)
            d = K.synth(d, f"sc_{role}_{knob}{factor:g}".replace(".", "p"),
                        q_a, q_b, polish=60)
            r = K.full(d, name, thd=False)
            r["arm"] = list(arm)
            # Sim economy: no transient on an arm that missed the shape box.
            if 240.0 <= r["fc_hz"] <= 260.0:
                K.add_thd(d, r)
            return r
        except Exception as exc:                        # noqa: BLE001
            return {"name": name, "arm": list(arm), "error": repr(exc)}

    rows = [r for r in batch([("base", "w", 1.0)] + ARMS, one)
            if not isinstance(r, Exception)]
    OUT.write_text(json.dumps(rows, indent=2))
    good = [r for r in rows if "thd_db" in r]
    for r in sorted(good, key=lambda r: r["thd_db"]):
        print(K.line(r), flush=True)
    for r in rows:
        if "error" in r:
            print(f"{r['name']:>22s} | ERROR {r['error'][:70]}")


if __name__ == "__main__":
    main()
