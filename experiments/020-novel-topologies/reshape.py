"""Re-fit each candidate's four capacitors against the Butterworth TEMPLATE.

Why this exists: the first fit scored a scalar ripple BOUND, and a response that
sags then recovers satisfies a bound while visibly not being a maximally-flat
low-pass.  The originating campaign's merge cell measured peak = 0.00 dB, so a
monotone passband is achievable in this topology and the bump is a fit artefact,
not a technology limit.

Device sizing is NOT touched here -- gm, current, noise and power are held, and
only the four capacitors move.  That makes this a clean re-allocation control:
any change in IRN is the cap total moving, not the devices.

    uv run python experiments/020-novel-topologies/reshape.py G-135 gb12-175
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from lab import config as C          # noqa: E402
from lab import metrics as M         # noqa: E402
from lab import ngspice as ng        # noqa: E402
from lab import raw as R             # noqa: E402
from lab import shape as S           # noqa: E402
from lab import thd as T             # noqa: E402
from lab.deck import ac_noise        # noqa: E402

OUT = HERE / "reshaped.json"


def _state():
    spec = importlib.util.spec_from_file_location("s020", HERE / "state.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def probe(design, tag: str) -> dict:
    """Shape numbers that the scorecard does not carry, on a dense sweep."""
    pl = ng.simulate(ac_noise(design, dec=100, fstart=1.0, fstop=3e3, nstop=1.0),
                     tag)
    f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
    fc = R.f3db(f, h)
    rms, worst = S.template_error(f, h, fc)
    return {"fc": fc, "rms": rms, "worst": worst,
            "mono": S.monotone_db(f, h, fc)}


def run(names: list[str]) -> list[dict]:
    st = _state()
    cells = st.load()
    rows = []
    for name in names:
        d0 = cells[name]
        slug = name.replace("-", "").replace(" ", "")
        before = probe(d0, f"rs_before_{slug}")
        s0 = M.evaluate(d0, f"rs_sc_before_{slug}", record=False)
        print(f"\n=== {name}: fitting to the template "
              f"(was mono {before['mono']:.3f} dB) ===", flush=True)
        d1, res = S.fit_butter(d0, f"rs_fit_{slug}", fc_target=250.0, maxiter=340)
        after = probe(d1, f"rs_after_{slug}")
        s1 = M.evaluate(d1, f"rs_sc_after_{slug}", record=False)
        t1 = T.measure(d1, tag=f"rs_thd_{slug}", gate=False)
        rows.append({
            "cell": name,
            "before": {**before, **{k: s0.values[k] for k in
                                    ("ripple_db", "peak_db", "a1000_db",
                                     "irn_uv", "p_core_nw", "c_total_pf",
                                     "ph_max_deg", "dc_db")}},
            "after": {**after, **{k: s1.values[k] for k in
                                  ("ripple_db", "peak_db", "a1000_db", "irn_uv",
                                   "p_core_nw", "c_total_pf", "ph_max_deg",
                                   "dc_db")},
                      "thd_db": t1.thd_db},
            "design": {"topology": d1.topology, "iref": d1.iref,
                       "vicm": d1.vicm, "vocm": d1.vocm,
                       "caps_pf": {k: getattr(d1, k) * 1e12
                                   for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
                       "devs": {r: vars(g) for r, g in d1.devs.items()}},
            "violations_after": s1.violations,
        })
        print(f"  {name}: mono {before['mono']:.3f} -> {after['mono']:.3f} dB | "
              f"ripple {s0['ripple_db']:.3f} -> {s1['ripple_db']:.3f} | "
              f"fc {after['fc']:.1f} | C {s0['c_total_pf']:.1f} -> "
              f"{s1['c_total_pf']:.1f} pF | IRN {s0['irn_uv']:.2f} -> "
              f"{s1['irn_uv']:.2f} | THD {t1.thd_db:.2f}", flush=True)
    prev = json.loads(OUT.read_text()) if OUT.exists() else []
    keep = [r for r in prev if r["cell"] not in names]
    OUT.write_text(json.dumps(keep + rows, indent=2))
    return rows


if __name__ == "__main__":
    run(sys.argv[1:] or ["G-135"])
