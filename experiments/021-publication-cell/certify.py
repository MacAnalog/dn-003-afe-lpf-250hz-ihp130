"""Sign-off: re-measure a candidate from its stored sizing, and plot it.

Deliberately independent of whatever produced the candidate.  It takes a
`Design` out of JSON, rebuilds every deck from it, and re-runs the frozen
measurement definitions in `lab.metrics` (+ the long-window DFT for THD) --
nothing is carried over from the fit, and no number here is read back out of a
run that the fitter made.  That is rule 1: a number that has not passed through
these definitions is a claim, not a measurement.

Emits the scorecard table, the S1-S8 verdict, and three figures: the Bode plot
with the ideal 4-pole template overlaid, the passband detail against the S3/S4
boxes, and the input-referred noise density with the S5 band shaded.

    uv run python experiments/021-publication-cell/certify.py <cells.json> [name]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import numpy as np                                      # noqa: E402

from lab import config as C                             # noqa: E402
from lab import metrics as M                            # noqa: E402
from lab import ngspice as ng                           # noqa: E402
from lab import plot as P                               # noqa: E402
from lab import raw as R                                # noqa: E402
from lab import shape as S                              # noqa: E402
from lab import thd as T                                # noqa: E402
from lab.deck import ac_noise                           # noqa: E402
from lab.dut import Design, Dev                         # noqa: E402

OUT = HERE / "certified.json"
FIGS = HERE.parents[1] / "figs"


def design_from(d: dict) -> Design:
    return Design(topology=d["topology"],
                  devs={r: Dev(**g) for r, g in d["devs"].items()},
                  iref=d["iref"], vicm=d["vicm"], vocm=d["vocm"],
                  # lv_roles selects the device FLAVOUR and vmid is the
                  # inter-stage dc hint; a rebuild that drops either is a
                  # different circuit or a non-converging one, not a detail.
                  lv_roles=frozenset(d.get("lv_roles") or ()),
                  vmid=d.get("vmid"),
                  **{k: v * 1e-12 for k, v in d["caps_pf"].items()})


def certify(d: Design, name: str) -> dict:
    s = M.evaluate(d, f"cert021_{name}")                # recorded in the ledger
    t = T.measure(d, tag=f"cert021_{name}_thd")         # gated on the cheap box
    pl = ng.simulate(ac_noise(d, dec=200, fstart=1.0, fstop=3e3, nstop=1.0),
                     f"cert021_{name}_dense")
    f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
    rms, worst = S.template_error(f, h, s["fc_hz"])
    row = {"name": name, "thd_db": t.thd_db,
           "hd": {str(k): v for k, v in t.per_harmonic.items()},
           "template_rms_db": rms, "template_worst_db": worst,
           **{k: s[k] for k in M.COLS if k in s.values},
           "violations": list(s.violations),
           "design": {"topology": d.topology, "iref": d.iref, "vicm": d.vicm,
                      "vocm": d.vocm, "vmid": d.vmid,
                      "lv_roles": sorted(d.lv_roles),
                      "caps_pf": {k: getattr(d, k) * 1e12
                                  for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
                      "devs": {r: {"w": g.w, "l": g.l, "ng": g.ng, "m": g.m}
                               for r, g in d.devs.items()}}}
    row["s7_pass"] = t.thd_db <= M.THD_LIMIT_DB
    row["all_pass"] = not s.violations and row["s7_pass"]
    row["phase"] = phase_detail(d, name)
    return row


def phase_detail(d: Design, name: str) -> dict:
    """Is the S1 certificate a real 4-pole, or is it being inflated?

    An ideal 4-pole scores 350.53 deg through the -100 dB floor and 359.57 deg
    without it (doc/journal/phase-ceiling-is-350-not-360.md).  A cell that
    scores MORE than ~351 is carrying lag the 4-pole model does not contain, and
    there are two very different reasons it might:

    *   real parasitic poles above the band -- benign here, since the passband
        and the 1 kHz stopband point are unaffected; or
    *   an aliased unwrap on a sparse grid, which is a measurement artefact and
        invalidates the certificate.

    Telling them apart needs the step margin (`ph_step_deg`, aliasing is a risk
    as it approaches 180 deg) measured on a DENSE sweep, and the frequency at
    which the response actually falls through the floor.  A cell whose |H| stays
    above -100 dB well past 15.9*fc is rolling off more slowly than 4 poles out
    there, which is exactly where the extra lag comes from.
    """
    pl = ng.simulate(ac_noise(d, dec=200, fstart=0.1, fstop=1e5, nstop=1.0),
                     f"cert021_{name}_ph")
    f, h = R.diff_tf(R.pick(pl, "ac"), C.OUT_P, C.OUT_N)
    y = R.db_rel_dc(h)
    scored = np.asarray(np.real(f), float)[y >= M.PH_FLOOR_DB]
    fc = R.f3db(f, h)
    return {
        "ph_max_floored_deg": R.ph_max_deg(f, h, M.PH_FLOOR_DB),
        "ph_max_unfloored_deg": R.ph_max_deg(f, h, -1e9),
        "ph_step_deg": R.max_phase_step_deg(f, h, M.PH_FLOOR_DB),
        "f_scored_hi_hz": float(scored[-1]) if len(scored) else float("nan"),
        "f_scored_hi_over_fc": float(scored[-1] / fc) if len(scored) else float("nan"),
        "ideal_4pole_floored_deg": 350.53,
        "ideal_4pole_floor_at_x_fc": 15.9,
    }


def verdict(r: dict) -> str:
    lines = [f"### {r['name']} — {'ALL LINES PASS' if r['all_pass'] else 'FAIL'}",
             "",
             "| line | requirement | measured | verdict |",
             "|---|---|---|---|"]
    box = [("S1 phase", "≥ 330° (ideal 4-pole ceiling 350.5°)",
            f"{r['ph_max_deg']:.2f}°", r["ph_max_deg"] >= 330.0),
           ("S1 stopband", "≤ −48 dB @ 1 kHz", f"{r['a1000_db']:.2f} dB",
            r["a1000_db"] <= -48.0),
           ("S2 cutoff", "245–255 Hz", f"{r['fc_hz']:.2f} Hz",
            245.0 <= r["fc_hz"] <= 255.0),
           ("S3 dc gain", "|dc| ≤ 0.2 dB", f"{r['dc_db']:+.4f} dB",
            abs(r["dc_db"]) <= 0.2),
           ("S3 flatness", "ripple ≤ 0.2 dB to 150 Hz", f"{r['ripple_db']:.4f} dB",
            r["ripple_db"] <= 0.2),
           ("S4 peaking", "≤ 0.2 dB", f"{r['peak_db']:+.4f} dB",
            r["peak_db"] <= 0.2),
           ("S5 IRN", "< 40 µVrms (0.5–200 Hz)", f"{r['irn_uv']:.2f} µV",
            r["irn_uv"] < 40.0),
           ("S6 power", "< 50 nW (core only)", f"{r['p_core_nw']:.2f} nW",
            r["p_core_nw"] < 50.0),
           ("S7 THD", "≤ −40 dB @ 175 mVpp, 50 Hz", f"{r['thd_db']:.2f} dB",
            r["s7_pass"])]
    for label, req, got, ok in box:
        lines.append(f"| {label} | {req} | **{got}** | {'PASS' if ok else 'FAIL'} |")
    lines += [
        "",
        f"*monotonicity* `mono_db` = **{r.get('mono_db', float('nan')):.4f} dB**"
        " (0 = never climbs); template rms "
        f"{r['template_rms_db']:.4f} dB / worst {r['template_worst_db']:.4f} dB;"
        f" total drawn capacitance **{r['c_total_pf']:.1f} pF**"
        " (reported, never specced)",
    ]
    return "\n".join(lines)


def figures(cells: dict, tag: str = "pub") -> None:
    FIGS.mkdir(exist_ok=True)
    P.bode(cells, "cert021_bode.png", tag=f"{tag}b", dec=100,
           title="Certified cell vs reference — differential AC response")
    P.passband(cells, "cert021_passband.png", tag=f"{tag}p", fmax=300)
    P.noise(cells, "cert021_noise.png", tag=f"{tag}n", dec=100,
            title="Input-referred noise density — S5 band (0.5–200 Hz) shaded")
    print(f"wrote {FIGS}/cert021_{{bode,passband,noise}}.png")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    payload = json.loads(Path(sys.argv[1]).read_text())
    rows = payload if isinstance(payload, list) else [payload]
    if len(sys.argv) > 2:
        rows = [r for r in rows if r.get("name") == sys.argv[2]]
    out, cells = [], {}
    for r in rows:
        d = design_from(r["design"] if "design" in r else r)
        name = r.get("name", "cell")
        res = certify(d, name)
        cells[name] = d
        out.append(res)
        print("\n" + verdict(res), flush=True)
        if res["violations"]:
            print("\nviolations: " + "; ".join(res["violations"]))
    OUT.write_text(json.dumps(out, indent=2))
    if cells:
        figures(cells)


if __name__ == "__main__":
    main()
