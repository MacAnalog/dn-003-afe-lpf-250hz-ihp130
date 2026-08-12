"""THD versus where the high-Q pole pair sits -- measured, not modelled.

Two facts set this experiment up.

*   The magnitude response does not care which cascade stage carries which Q: a
    4th-order Butterworth needs {0.5412, 1.3066} and the assignment is free.
    The shape fit has been choosing it by accident, from its starting point.
*   Distortion does care.  Across four cells re-fitted to the template, THD
    tracked biquad B's capacitor ratio and nothing else: c1_b/c2_b of 3.33,
    2.47, 1.59, 0.27 gave -41.6, -35.8, -35.7, -28.6 dB.

The closed form cannot referee this.  Synthesising caps from measured gm through
the ideal biquad lands fc 21-50 % low and, once uniformly trimmed back to
250 Hz, gives |H|@1 kHz of -26 dB where Butterworth demands -48 -- i.e. the
two-capacitor model gets the Q's materially wrong in this PDK, because every
internal node carries parasitic capacitance it does not know about.  So the
allocation is walked EMPIRICALLY.

The walk parameter is exact where the model is not.  Within one stage, at fixed
w0, Q is proportional to sqrt(C2/C1) and w0 to 1/sqrt(C1*C2).  Multiplying C1 by
r and dividing C2 by r therefore leaves the PRODUCT -- hence that stage's cutoff
contribution -- untouched, and moves only its Q, by 1/r.  Stage A is shifted the
opposite way so the pair stays complementary.

HYPOTHESIS: THD improves monotonically as biquad B's Q is reduced (r > 1), and
at least one r reaches the template (rms < 0.02 dB) with THD <= -40 dB.

FALSIFIED IF THD is flat in r to within 1 dB, or if every r that reaches the
template is worse than -40 dB.

Each point is re-polished against the same template, so all surviving points are
the same filter to the eye and differ only in where the capacitance sits: the
re-allocation control is the sweep itself.

    uv run python experiments/021-publication-cell/qwalk.py [r ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common as K                                      # noqa: E402
from qsplit import load                                 # noqa: E402
from lab.parallel import batch                          # noqa: E402

OUT = HERE / "qwalk.json"
RS = (0.40, 0.60, 1.00, 1.60, 2.50, 4.00)


def shifted(base, r: float):
    """Move biquad B's Q by 1/r and biquad A's by r, both at fixed w0."""
    return base.with_(c1_b=base.c1_b * r, c2_b=base.c2_b / r,
                      c1_a=base.c1_a / r, c2_a=base.c2_a * r)


def main() -> None:
    rs = [float(x) for x in sys.argv[1:]] or list(RS)
    base = load()
    print(f"qwalk: {len(rs)} points, base C = {base.total_cap()*1e12:.1f} pF",
          flush=True)

    def one(r: float) -> dict:
        name = f"qw_r{r:g}".replace(".", "p")
        try:
            d = shifted(base, r)
            # trims fix the cutoff the shift did not move but the polish will;
            # the polish is what decides whether this r can BE a Butterworth.
            d = K.synth_from(d, name, polish=140)
            row = K.full(d, name)
            row["r"] = r
            print(K.line(row) + f" | rms {row['rms']:.4f}", flush=True)
            return row
        except Exception as exc:                          # noqa: BLE001
            return {"name": name, "r": r, "error": repr(exc)}

    rows = [r for r in batch(rs, one, workers=3) if not isinstance(r, Exception)]
    OUT.write_text(json.dumps(rows, indent=2))
    good = [r for r in rows if r.get("rms", 9) < 0.02 and "thd_db" in r]
    print(f"\n{len(good)}/{len(rows)} points reached the template (rms < 0.02 dB)")
    for r in sorted(good, key=lambda r: r["thd_db"]):
        print(f"  r={r['r']:.2f}  THD {r['thd_db']:6.2f} dB  "
              f"c1_b/c2_b {r['caps_pf']['c1_b']/r['caps_pf']['c2_b']:5.2f}  "
              f"IRN {r['irn_uv']:.2f}  C {r['c_total_pf']:.1f} pF")


if __name__ == "__main__":
    main()
