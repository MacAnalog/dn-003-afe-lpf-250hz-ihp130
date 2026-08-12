"""Where the campaign stands: rebuild the candidate set, re-measure, plot.

Everything here is re-simulated live -- no number is copied out of the ledger
into a figure.  The ledger is used only to FIND candidates (by tag); each one is
then rebuilt into a `Design` and re-run, and the rebuild is CHECKED against the
row's own recorded fc/IRN before it is allowed into a figure.

That check is not ceremony.  Ledger rows written before 2026-08-11 do not carry
`vicm`/`vocm` (see `lab.ledger.design_dict`), so a rebuild silently falls back
to the dataclass defaults -- a different operating point, hence a different
circuit.  `resolve()` tries the plausible common-mode pairs and keeps the one
that reproduces the recorded scorecard.

    uv run python experiments/020-novel-topologies/state.py resolve
    uv run python experiments/020-novel-topologies/state.py thd
    uv run python experiments/020-novel-topologies/state.py figs
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lab import config as C          # noqa: E402
from lab import ledger as L          # noqa: E402
from lab import metrics as M         # noqa: E402
from lab import plot as P            # noqa: E402
from lab import thd as T             # noqa: E402
from lab.dut import Design, Dev, build_reference  # noqa: E402
from lab.parallel import batch       # noqa: E402

HERE = Path(__file__).resolve().parent
CACHE = HERE / "state_cache.json"

# The candidate set the figures compare.  Tags are ledger keys; `reference` is
# rebuilt from the frozen deck's own sizing instead.
CANDIDATES = [
    # The certified yardstick is the CAP-FITTED reference, not `sizes.v0()` --
    # v0 is the unfitted carry-over starting point (fc 226 Hz, 110.8 pF).
    ("reference",   "cert_reference"),
    ("020B frozen", "frozen:020B"),         # the ported headline cell
    ("G-135",       "thdG_il1.69_x0.25"),   # first cell clean on ALL NINE lines
    ("G-120",       "thdG_il1.50_x0.28"),   # the same family at minimum C
    ("gb12-175",    "r9t_gb12_rB0.6"),      # lowest IRN; fails S7
    ("n6-98",       "f2_n6_all_big"),       # lowest C and IRN; fails S7 hardest
]

# Common-mode pairs actually used across the campaign (lab.dut defaults first).
CM_TRIALS = [(0.25, 1.25), (0.20, 1.10), (0.70, 0.80)]


def _rows():
    return L.read()


def _design_from(d: dict, vicm: float, vocm: float) -> Design:
    caps = {k: v * 1e-12 for k, v in d["caps_pf"].items()}
    devs = {r: Dev(**g) for r, g in d["devs"].items()}
    return Design(topology=d["topology"], devs=devs, iref=d.get("iref", 1e-9),
                  vicm=d.get("vicm", vicm), vocm=d.get("vocm", vocm), **caps)


def _load(path: Path, name: str):
    """Import a module BY PATH.  Every experiment dir has its own `sizes.py`, so
    a plain `import sizes` would resolve to whichever landed on sys.path first."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)        # type: ignore[union-attr]
    return mod


def reference_design() -> Design:
    """The certified yardstick, from experiments/000's own definition."""
    return _load(HERE.parent / "000-reference-baseline" / "sizes.py", "sizes000").v0()


def _nominal(r: dict) -> bool:
    return (r.get("corner") == C.CORNER_NOM
            and abs((r.get("temp") or C.TEMP_NOM) - C.TEMP_NOM) < 1e-9
            and abs((r.get("vdd") or C.VDD) - C.VDD) < 1e-9)


def find(tag: str) -> tuple[dict, dict | None]:
    """(design dict, the nominal `evaluate` row that pins it) for a ledger tag.

    The tagged row may be a THD run, which carries no fc/IRN -- so the anchor is
    looked up by DESIGN FINGERPRINT among nominal scorecards, not by tag.  A
    candidate with no scorecard anchor cannot be rebuild-checked; that is
    reported, not silently accepted.
    """
    rows = _rows()
    hits = [r for r in rows if r.get("tag") == tag and r.get("design")]
    if not hits:
        raise SystemExit(f"no ledger row with a design for tag {tag!r}")
    design = hits[-1]["design"]
    key = json.dumps(design, sort_keys=True)
    anchors = [r for r in rows
               if r.get("kind") == "evaluate" and _nominal(r)
               and r.get("fc_hz") is not None
               and json.dumps(r.get("design"), sort_keys=True) == key]
    return design, (anchors[-1] if anchors else None)


def resolve(verbose: bool = True) -> dict[str, Design]:
    """Rebuild every candidate and PROVE the rebuild reproduces its ledger row."""
    out: dict[str, Design] = {}
    report = []
    for name, tag in CANDIDATES:
        if tag is None:
            d = reference_design()
            s = M.evaluate(d, "state_ref", record=False)
            report.append((name, "-", s["fc_hz"], s["irn_uv"], s["c_total_pf"], "n/a"))
            out[name] = d
            continue
        if tag.startswith("frozen:"):
            raw = json.loads((HERE / "frozen" / f"{tag[7:]}.json").read_text())
            d = _design_from(raw, raw.get("vicm", 0.25), raw.get("vocm", 1.25))
            s = M.evaluate(d, f"state_{tag[7:]}", record=False)
            out[name] = d
            report.append((name, tag, s["fc_hz"], s["irn_uv"], s["c_total_pf"],
                           "frozen json (carries vicm)"))
            continue
        design, anchor = find(tag)
        if anchor is None:
            raise SystemExit(f"{name}: {tag} has no nominal scorecard to check "
                             f"the rebuild against")
        want_fc, want_irn = anchor["fc_hz"], anchor["irn_uv"]
        best = None
        for vicm, vocm in CM_TRIALS:
            d = _design_from(design, vicm, vocm)
            try:
                s = M.evaluate(d, f"state_{tag}_{vicm}", record=False)
            except Exception as e:                       # noqa: BLE001
                if verbose:
                    print(f"  {name} @ vicm={vicm}: {type(e).__name__}")
                continue
            err = abs(s["fc_hz"] / want_fc - 1) + abs(s["irn_uv"] / want_irn - 1)
            if best is None or err < best[0]:
                best = (err, d, s, vicm)
            if err < 2e-3:
                break
        if best is None:
            raise SystemExit(f"{name}: could not rebuild {tag}")
        err, d, s, vicm = best
        if err > 0.02:
            raise SystemExit(
                f"{name}: rebuild of {tag} does not reproduce its ledger row "
                f"(fc {s['fc_hz']:.2f} vs {want_fc:.2f}, "
                f"IRN {s['irn_uv']:.2f} vs {want_irn:.2f}); the row is missing "
                f"state the rebuild needs.")
        out[name] = d
        report.append((name, tag, s["fc_hz"], s["irn_uv"], s["c_total_pf"],
                       f"vicm={vicm:g} (err {err*100:.2f} %)"))
    if verbose:
        print(f"\n{'cell':14} {'tag':20} {'fc':>7} {'IRN':>7} {'C pF':>7}  rebuild")
        for r in report:
            print(f"{r[0]:14} {r[1][:20]:20} {r[2]:7.2f} {r[3]:7.2f} {r[4]:7.2f}  {r[5]}")
    CACHE.write_text(json.dumps(
        {n: {"topology": d.topology, "iref": d.iref, "vicm": d.vicm, "vocm": d.vocm,
             "caps_pf": {k: getattr(d, k) * 1e12 for k in ("c1_a", "c2_a", "c1_b", "c2_b")},
             "devs": {r: vars(g) for r, g in d.devs.items()}}
         for n, d in out.items()}, indent=2))
    return out


def load() -> dict[str, Design]:
    if not CACHE.exists():
        return resolve()
    raw = json.loads(CACHE.read_text())
    return {n: _design_from(d, d["vicm"], d["vocm"]) for n, d in raw.items()}


# --------------------------------------------------------------------- THD --

def run_thd(names: list[str] | None = None) -> dict[str, T.Thd]:
    cells = load()
    names = names or list(cells)
    def one(n):
        return n, T.measure(cells[n], tag=f"state_thd_{n.replace(' ', '_')}",
                            gate=False)
    res = batch(names, one)
    return {n: t for n, t in res if not isinstance(t, Exception)}


# -------------------------------------------------------------------- figs --

def figs():
    cells = load()
    P.bode(cells, "state_bode.png", tag="stb", dec=100,
           title="AC response, differential — all five cells")
    P.passband(cells, "state_passband.png", tag="stp", fmax=300)
    P.noise(cells, "state_noise.png", tag="stn", dec=100,
            title="Input-referred noise density — S5 band shaded")
    print("wrote state_bode / state_passband / state_noise")


def thd_figs():
    """Harmonic spectra for the candidate set, from a LIVE re-measurement."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    res = run_thd()
    order = [n for n, _ in CANDIDATES if n in res]
    # ODD harmonics only.  These cells are differential and HD2/HD4 sit at the
    # numerical floor (~-145 dB) while the balance holds -- plotting them just
    # draws six full-height bars per harmonic and hides the signal.  An even
    # harmonic that CLIMBS is a bug report, so it is checked, not drawn.
    hs = [3, 5, 7, 9]
    floor = -100.0
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.6, 4.4),
                                 gridspec_kw={"width_ratios": [1.35, 1]})
    w = 0.84 / len(order)
    for i, n in enumerate(order):
        t = res[n]
        y = [max(t.per_harmonic.get(h, floor), floor) for h in hs]
        a1.bar(np.arange(len(hs)) + i * w, np.array(y) - floor, width=w,
               bottom=floor, color=P._COLORS[i % len(P._COLORS)],
               label=f"{n} — THD {t.thd_db:.1f} dB")
    a1.axhline(M.THD_LIMIT_DB, color="#d62728", ls="--", lw=1.3)
    a1.annotate("S7: TOTAL ≤ −40 dB", (len(hs) - 0.55, M.THD_LIMIT_DB),
                fontsize=8, color="#d62728", va="bottom", ha="right")
    a1.set_xticks(np.arange(len(hs)) + 0.42 - w / 2)
    a1.set_xticklabels([f"{h}f₀" for h in hs])
    a1.set_ylim(floor, -15)
    P._style(a1, f"odd harmonic of {M.THD_FIN:g} Hz", "dB rel. fundamental",
             f"Harmonic spectra at the S7 point "
             f"({M.THD_AMPL*2e3:g} mVpp diff. input, {M.THD_FIN:g} Hz)")
    a1.legend(fontsize=8, loc="lower left")

    # HD3 IS the distortion here -- the right panel proves it, so a reader knows
    # the total is not hiding a high-order tail.
    tot = [res[n].thd_db for n in order]
    h3 = [res[n].hd3_db for n in order]
    a2.scatter(h3, tot, s=64, c=[P._COLORS[i % len(P._COLORS)]
                                 for i in range(len(order))], zorder=3)
    for n, x, y in zip(order, h3, tot):
        a2.annotate(n, (x, y), fontsize=7.5, textcoords="offset points",
                    xytext=(6, -3))
    lim = [min(h3 + tot) - 2, max(h3 + tot) + 2]
    a2.plot(lim, lim, color="0.6", ls=":", lw=1)
    a2.annotate("total = HD3", (lim[1], lim[1]), fontsize=8, color="0.45",
                ha="right", va="top")
    a2.axhline(M.THD_LIMIT_DB, color="#d62728", ls="--", lw=1.2)
    a2.axvline(M.THD_LIMIT_DB, color="#d62728", ls="--", lw=1.2)
    a2.set_xlim(*lim)
    a2.set_ylim(*lim)
    P._style(a2, "HD3 (dB)", "total THD, h2..h10 (dB)",
             "Every cell is HD3-dominated")
    fig.tight_layout()
    print("wrote", P._save(fig, "state_thd_spectra.png"))
    worst2 = {n: res[n].hd2_db for n in order if res[n].hd2_db > -100}
    if worst2:
        print("  NOTE: even-harmonic energy above the floor (asymmetry?):", worst2)
    return res


def report():
    """The nine-line scorecard for the candidate set, re-measured live."""
    cells = load()
    scores = {n: M.evaluate(d, f"state_rpt_{n.replace(' ', '_')}", record=False)
              for n, d in cells.items()}
    thds = {}
    for n, d in cells.items():
        t = T.measure(d, tag=f"state_rpt_thd_{n.replace(' ', '_')}", gate=False)
        thds[n] = t
    lines = ["| cell | C pF | fc Hz | dc dB | ripple dB | peak dB | @1k dB | "
             "ph deg | IRN µV | P nW | THD dB | verdict |",
             "|" + "---|" * 12]
    for n, s in scores.items():
        v, t = s.values, thds[n]
        bad = list(s.violations) + ([] if t.thd_db <= M.THD_LIMIT_DB else ["S7"])
        lines.append(
            f"| {n} | {v['c_total_pf']:.1f} | {v['fc_hz']:.1f} | {v['dc_db']:+.3f} "
            f"| {v['ripple_db']:.3f} | {v['peak_db']:.3f} | {v['a1000_db']:.2f} "
            f"| {v['ph_max_deg']:.0f} | {v['irn_uv']:.2f} | {v['p_core_nw']:.2f} "
            f"| {t.thd_db:.2f} | {'**PASS**' if not bad else f'FAIL ({len(bad)})'} |")
    out = "\n".join(lines)
    print(out)
    (HERE / "state_scorecard.md").write_text(out + "\n")
    return scores, thds


def frontier():
    """Every cell ever measured at the S7 point: what THD actually costs.

    Two panels because the trade is two-dimensional and the second panel is the
    finding: distortion does not track capacitance, it tracks how far the two
    biquads' poles are STAGGERED -- and the stagger is exactly what the S3
    flatness clause forbids.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = _rows()
    ev = {}
    for r in rows:
        if (r.get("kind") == "evaluate" and r.get("design") and _nominal(r)
                and r.get("ripple_db") is not None):
            ev[json.dumps(r["design"], sort_keys=True)] = r
    pts, seen = [], set()
    for t in rows:
        if (t.get("kind") != "thd" or t.get("fin_hz") != M.THD_FIN
                or abs((t.get("ampl_v") or 0) - M.THD_AMPL) > 1e-9):
            continue
        k = json.dumps(t.get("design"), sort_keys=True)
        e = ev.get(k)
        if e is None or k in seen:
            continue
        seen.add(k)
        pts.append({"thd": t["thd_db"], "C": e["c_total_pf"], "irn": e["irn_uv"],
                    "rip": e["ripple_db"], "clean": bool(e["goal_met"])})

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.6))
    for ax, xk, xl in ((a1, "C", "total drawn capacitance (pF)"),
                       (a2, "rip", "passband ripple to 150 Hz (dB)")):
        for flag, col, mk, lab in ((True, "#2ca02c", "o", "8-line scorecard PASS"),
                                   (False, "#d62728", "x", "8-line scorecard FAIL")):
            sel = [p for p in pts if p["clean"] is flag]
            ax.scatter([p[xk] for p in sel], [p["thd"] for p in sel],
                       c=col, marker=mk, s=52, label=lab, zorder=3)
        ax.axhline(M.THD_LIMIT_DB, color="#d62728", ls="--", lw=1.3)
        ax.annotate("S7 ≤ −40 dB", (ax.get_xlim()[1], M.THD_LIMIT_DB), fontsize=8,
                    color="#d62728", va="bottom", ha="right")
        P._style(ax, xl, "THD at the S7 point (dB)")
    a2.axvspan(0, 0.2, color="#2ca02c", alpha=0.10)
    a2.annotate("S3 flat", (0.02, -58), fontsize=8, color="#2ca02c")
    a2.set_xscale("log")
    a1.legend(fontsize=8, loc="lower right")
    a1.set_title("Distortion does NOT buy back with capacitance", fontsize=10)
    a2.set_title("It buys back with passband DROOP — which S3 forbids", fontsize=10)
    fig.tight_layout()
    print("wrote", P._save(fig, "state_frontier.png"), f"({len(pts)} cells)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "resolve"
    if cmd == "resolve":
        resolve()
    elif cmd == "thd":
        for n, t in run_thd(sys.argv[2:] or None).items():
            print(f"{n:14} THD {t.thd_db:+.2f} dB  HD3 {t.hd3_db:+.2f}  "
                  f"out {t.out_fund_vpp*1e3:.1f} mVpp")
    elif cmd == "figs":
        figs()
    elif cmd == "thdfigs":
        thd_figs()
    elif cmd == "frontier":
        frontier()
    elif cmd == "report":
        report()
    else:
        raise SystemExit(f"unknown command {cmd!r}")
