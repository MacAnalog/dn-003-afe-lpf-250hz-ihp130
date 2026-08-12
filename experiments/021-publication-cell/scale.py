"""Buy noise margin with area and the unspent power budget, at fixed shape.

Multiply every device width, the reference current, and all four capacitors by
the same k.  Every current DENSITY is then unchanged, so every operating point,
every gm/ID, the pole positions, the passband shape, the phase certificate and
the large-signal linearity are unchanged too -- the cell is literally k copies
of itself in parallel.  What does move:

    fc          unchanged (gm and C both scale by k)
    THD         unchanged (same densities, same swings)
    ph_max      unchanged (same poles)
    IRN         ~ 1/sqrt(k)   (thermal noise is kT/C at fixed fc)
    power       ~ k
    capacitance ~ k

That is the cleanest trade in the box: S6 has ~12x of unspent headroom (4.15 nW
of 50) and S5 is the line with no margin left (39.70 uV of 40).  Capacitance is
reported, never specced, so area is the currency being spent.

It is also the sharpest possible re-allocation control: nothing about the
circuit changes except its size, so any deviation of fc/THD/phase from "flat in
k" is a real effect (short-channel, parasitic, or numerical), not a design
choice -- and is worth reading as a warning.

    uv run python experiments/021-publication-cell/scale.py [k ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import common as K                                      # noqa: E402
from certify import design_from                         # noqa: E402
from lab.parallel import batch                          # noqa: E402

OUT = HERE / "scaled.json"
KS = (1.0, 1.5, 2.0, 2.5, 3.0)
BASE = "020C-frozen"


def scaled(d, k: float):
    """k parallel copies: widths, reference current and capacitors all x k."""
    devs = {r: g.__class__(**{**vars(g), "w": g.w * k}) for r, g in d.devs.items()}
    return d.with_(devs=devs, iref=d.iref * k,
                   c1_a=d.c1_a * k, c2_a=d.c2_a * k,
                   c1_b=d.c1_b * k, c2_b=d.c2_b * k)


def main() -> None:
    ks = [float(x) for x in sys.argv[1:]] or list(KS)
    rows = json.loads((HERE / "fitcells.json").read_text())
    base = design_from(next(r for r in rows if r["name"] == BASE))
    print(f"scale: {BASE} x {ks}", flush=True)

    def one(k: float) -> dict:
        name = f"k{k:g}".replace(".", "p")
        try:
            # No re-fit: if the scaling law holds, the shape needs no repair.
            # Trims are allowed only to absorb second-order drift in fc.
            d = K.synth_from(scaled(base, k), f"sc_{name}", polish=0, trims=2)
            r = K.full(d, f"{BASE}_x{k:g}")
            r["k"] = k
            print(K.line(r), flush=True)
            return r
        except Exception as exc:                          # noqa: BLE001
            return {"name": name, "k": k, "error": repr(exc)}

    out = [r for r in batch(ks, one, workers=4) if not isinstance(r, Exception)]
    OUT.write_text(json.dumps(out, indent=2))
    print("\n| k | fc | mono | a1k | ph_max | IRN | P nW | C pF | THD | all 9? |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted((x for x in out if "error" not in x), key=lambda x: x["k"]):
        ok = (not r["violations"]) and r.get("thd_db", 0) <= -40.0
        print(f"| {r['k']:.1f} | {r['fc_hz']:.2f} | {r['mono']:.4f} | "
              f"{r['a1000_db']:.2f} | {r['ph_max_deg']:.2f} | {r['irn_uv']:.2f} | "
              f"{r['p_core_nw']:.2f} | {r['c_total_pf']:.1f} | "
              f"{r.get('thd_db', float('nan')):.2f} | "
              f"{'**PASS**' if ok else 'fail'} |")


if __name__ == "__main__":
    main()
