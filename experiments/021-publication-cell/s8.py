"""S8: the two paper techniques the delivered cell rests on, each measured here.

S8 asks for >= 2 techniques from `pdf/` COMBINED.  The spec also rules that a
pure capacitance/Q re-allocation is not a technique -- it is the control that
has to be subtracted first (doc/target-spec.md, S8 row).  So the two claims
below are structural, and each gets its own A/B in this repo rather than being
inherited from the originating campaign's write-up.

TECHNIQUE 1 -- branch stacking (`gmc-compact` §7T biquad, with `tian2023`).
    Both input followers share ONE dc branch through a p-type bridge, so the
    two internal-node bias pairs are deleted and the same ampere does the gm
    work of both followers.  A/B: the reference topology (eight bias devices,
    independent branches) against the stacked topology, both fitted to the same
    250 Hz Butterworth template.  Claim under test: stacking cuts core power and
    removes the bias devices that dominate the noise budget.

TECHNIQUE 2 -- the floating differential capacitor (`fvf-2nd`).
    Each `c2` is one capacitor across the pair rather than two to ground.  A/B:
    the SAME design with `c2_grounded` toggled.  Claim under test: identical
    differential response, materially fewer drawn farads.  This one is exact
    rather than statistical -- if the two responses are not on top of each
    other, the claim is simply wrong.

Neither A/B is a sizing search; both are equal-shape comparisons, which is the
only way a "technique" can be separated from "we spent more capacitance".

    uv run python experiments/021-publication-cell/s8.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np                                      # noqa: E402

import common as K                                      # noqa: E402
from qsplit import load                                 # noqa: E402
from lab import config as C                             # noqa: E402
from lab import metrics as M                            # noqa: E402
from lab import ngspice as ng                           # noqa: E402
from lab import raw as R                                # noqa: E402
from lab.deck import ac_noise                           # noqa: E402

OUT = HERE / "s8.json"


def reference():
    """The certified yardstick, from experiment 000's own definition."""
    import importlib.util
    p = HERE.parent / "000-reference-baseline" / "sizes.py"
    spec = importlib.util.spec_from_file_location("sizes000", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                        # type: ignore[union-attr]
    return mod.v0()


def stacking() -> dict:
    """A/B 1: independent bias branches vs one shared, stacked branch."""
    out = {}
    for name, d in (("unstacked (reference topology)", reference()),
                    ("stacked (bridge + merge)", load())):
        fitted = K.synth_from(d, f"s8_stack_{name[:5]}", polish=160)
        row = K.full(fitted, f"s8_{name[:5]}", thd=False)
        row["n_bias_devices"] = sum(1 for r in fitted.devs if r.startswith("bias"))
        row["n_devices"] = len(fitted.devs)
        out[name] = row
        print(K.line(row) + f" | bias devs {row['n_bias_devices']}", flush=True)
    return out


def floating_cap() -> dict:
    """A/B 2: one floating differential cap vs two grounded ones.

    Scored on the differential transfer only.  The grounded arm also loads the
    COMMON mode, which this cell has no CMFB to care about -- so a difference
    there would be a finding about the testbench, not about the technique.
    """
    base = load()
    out = {}
    curves = {}
    for name, d in (("floating (as built)", base),
                    ("grounded (area control)", base.with_(c2_grounded=True))):
        pl = ng.simulate(ac_noise(d, dec=50, fstart=1.0, fstop=3e3, nstop=1.0),
                         f"s8_cap_{'g' if d.c2_grounded else 'f'}")
        f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
        curves[name] = (np.asarray(np.real(f), float), R.db_rel_dc(h))
        s = M.evaluate(d, f"s8_cap_{'g' if d.c2_grounded else 'f'}_sc", record=False)
        out[name] = {"fc_hz": s["fc_hz"], "a1000_db": s["a1000_db"],
                     "mono_db": s["mono_db"], "irn_uv": s["irn_uv"],
                     "c_total_pf": d.total_cap() * 1e12}
        print(f"  {name:26s} fc {s['fc_hz']:7.2f} | a1k {s['a1000_db']:6.2f} | "
              f"C {d.total_cap()*1e12:6.1f} pF | IRN {s['irn_uv']:.2f}", flush=True)
    (f0, y0), (f1, y1) = curves["floating (as built)"], curves["grounded (area control)"]
    n = min(len(y0), len(y1))
    out["max_curve_diff_db"] = float(np.max(np.abs(y0[:n] - y1[:n])))
    out["drawn_saving_pct"] = 100.0 * (1.0 - out["floating (as built)"]["c_total_pf"]
                                       / out["grounded (area control)"]["c_total_pf"])
    print(f"  worst |H| difference across the sweep: "
          f"{out['max_curve_diff_db']:.4f} dB   "
          f"=> drawn-capacitance saving {out['drawn_saving_pct']:.1f} %")
    return out


def main() -> None:
    print("=== S8 technique 1: branch stacking ===", flush=True)
    a = stacking()
    print("\n=== S8 technique 2: floating differential capacitor ===", flush=True)
    b = floating_cap()
    OUT.write_text(json.dumps({"stacking": a, "floating_cap": b}, indent=2))


if __name__ == "__main__":
    main()
