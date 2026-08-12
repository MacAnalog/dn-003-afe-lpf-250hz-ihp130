"""Which biquad carries the high-Q pole pair -- and what it costs in THD.

A 4th-order Butterworth needs Q = 0.5412 and Q = 1.3066, both at w0 = wc.  The
MAGNITUDE response does not care which cascade stage carries which: swap them
and |H(jw)| is identical to the last digit.  So the assignment is a free
variable that the shape fit has been picking by accident, from wherever its
starting point happened to sit.

It is not free for distortion.  In an SSF biquad the pole Q is set by
Q = sqrt(gm_i*C2/(gm_f*C1)), and C1 is the capacitor between the OUTPUT and the
INTERNAL node.  Raising Q at fixed w0 shrinks C1 and grows C2, which lets the
internal node swing further relative to the output -- and the internal node's
excursion is exactly the follower's Vgs modulation, i.e. the distortion term.
A high-Q stage should therefore distort more than a low-Q one, and putting the
high-Q pair in the stage that is already the more nonlinear of the two should
show up as several dB of THD.

The evidence that provoked this: across four cells re-fitted to the template,
THD tracks biquad B's C1/C2 ratio and nothing else --

    c1_b/c2_b  3.33 -> THD -41.56    (G-135, before the template re-fit)
    c1_b/c2_b  2.47 -> THD -35.76    (gb12-175, after)
    c1_b/c2_b  1.59 -> THD -35.74    (G-135, after)
    c1_b/c2_b  0.27 -> THD -28.61    (n6-98, after)

HYPOTHESIS.  With devices held fixed, assigning Q = 0.5412 to biquad B (and
1.3066 to A) gives a Butterworth response indistinguishable in magnitude from
the opposite assignment, and at least 3 dB better THD.

FALSIFIED IF the two assignments land within 1 dB of each other, or if the
low-Q-B assignment cannot reach the template at all.

Both arms are re-fitted with the SAME fitter to the SAME template, so this is
also its own re-allocation control: the only thing that differs between the two
final cells is where the capacitance sits, not how much or what it is made of.

    uv run python experiments/021-publication-cell/qsplit.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from lab import metrics as M            # noqa: E402
from lab import oppoint as O            # noqa: E402
from lab import shape as S              # noqa: E402
from lab import thd as T                # noqa: E402
from lab.dut import Design, Dev         # noqa: E402

RESHAPED = HERE.parent / "020-novel-topologies" / "reshaped.json"
OUT = HERE / "qsplit.json"

WC = 2.0 * math.pi * 250.0
Q_LO, Q_HI = 0.541196, 1.306563


def load(cell: str = "gb12-175") -> Design:
    """The template-re-fitted cell, rebuilt from experiment 020's own record."""
    rows = json.loads(RESHAPED.read_text())
    row = next(r for r in rows if r["cell"] == cell)
    d = row["design"]
    return Design(topology=d["topology"],
                  devs={r: Dev(**g) for r, g in d["devs"].items()},
                  iref=d["iref"], vicm=d["vicm"], vocm=d["vocm"],
                  **{k: v * 1e-12 for k, v in d["caps_pf"].items()})


def gms(design: Design, tag: str) -> dict:
    """gm of each biquad's input follower and shunt-feedback device, in S."""
    ops, _ = O.probe(design, tag)
    g = {r: ops[r].gm_ns * 1e-9 for r in ops}
    # Biquad B's feedback device IS its bias device in the merged topology --
    # `gmf_b` is the merged p-device; there is no separate role to read.
    return {"gm_i_a": g["in_a"], "gm_f_a": g["gmf_a"],
            "gm_i_b": g["in_b"], "gm_f_b": g["gmf_b"]}


def caps_for(g: dict, q_a: float, q_b: float) -> dict:
    """Synthesise the four DRAWN capacitors for a given Q assignment.

    Per-stage, from the validated all-pole biquad (doc/design-reference.md):
        w0^2 = gm_i*gm_f/(C1*C2_single),  Q = sqrt(gm_i*C2_single/(gm_f*C1))
    =>  C1 = gm_i/(w0*Q)  and  C2_single = gm_f*Q/w0.

    `c1_*` is drawn once PER SIDE, so it is C1 directly.  `c2_*` is one FLOATING
    differential capacitor across the two outputs, and a floating C between the
    halves of a balanced pair loads each half with 2C -- so the drawn value is
    C2_single/2, not C2_single.  Getting that factor wrong puts the pole pair a
    factor sqrt(2) off in Q and looks like a device problem.
    """
    return {
        "c1_a": g["gm_i_a"] / (WC * q_a),
        "c2_a": g["gm_f_a"] * q_a / WC / 2.0,
        "c1_b": g["gm_i_b"] / (WC * q_b),
        "c2_b": g["gm_f_b"] * q_b / WC / 2.0,
    }


def arm(base: Design, name: str, q_a: float, q_b: float, g: dict) -> dict:
    """Synthesise -> fit to the template -> score -> THD, for one assignment."""
    start = base.with_(**caps_for(g, q_a, q_b))
    print(f"\n=== {name}: Q_A={q_a:.4f} Q_B={q_b:.4f} "
          f"(synthesised C = {start.total_cap()*1e12:.1f} pF) ===", flush=True)
    fitted, _ = S.fit_butter(start, f"q_{name}", fc_target=250.0, maxiter=320)
    s = M.evaluate(fitted, f"q_{name}_sc", record=False)
    from lab import config as C
    from lab import ngspice as ng
    from lab import raw as R
    from lab.deck import ac_noise
    pl = ng.simulate(ac_noise(fitted, dec=100, fstart=1.0, fstop=3e3, nstop=1.0),
                     f"q_{name}_dense")
    f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
    rms, worst = S.template_error(f, h, s["fc_hz"])
    mono = S.monotone_db(f, h, s["fc_hz"])
    t = T.measure(fitted, tag=f"q_{name}_thd", gate=False)
    row = {"name": name, "q_a": q_a, "q_b": q_b,
           "mono": mono, "rms": rms, "worst": worst, "thd_db": t.thd_db,
           **{k: s[k] for k in ("fc_hz", "dc_db", "ripple_db", "peak_db",
                                "a1000_db", "ph_max_deg", "irn_uv",
                                "p_core_nw", "c_total_pf")},
           "caps_pf": {k: getattr(fitted, k) * 1e12
                       for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
           "violations": s.violations}
    print(f"  {name}: mono {mono:.4f} | fc {s['fc_hz']:.2f} | a1k "
          f"{s['a1000_db']:.2f} | ph {s['ph_max_deg']:.1f} | IRN {s['irn_uv']:.2f}"
          f" | C {s['c_total_pf']:.1f} pF | THD {t.thd_db:.2f} dB", flush=True)
    return row


def main() -> None:
    base = load()
    g = gms(base, "q_op")
    print("measured gm (nS): " + "  ".join(f"{k}={v*1e9:.3f}" for k, v in g.items()))
    rows = [arm(base, "loQ_B", Q_HI, Q_LO, g),   # high Q in biquad A
            arm(base, "hiQ_B", Q_LO, Q_HI, g)]   # high Q in biquad B (today)
    OUT.write_text(json.dumps({"gm": g, "arms": rows}, indent=2))
    d = rows[0]["thd_db"] - rows[1]["thd_db"]
    print(f"\nTHD(low-Q in B) - THD(high-Q in B) = {d:+.2f} dB "
          f"({'hypothesis SUPPORTED' if d < -1 else 'NOT supported'})")


if __name__ == "__main__":
    main()
