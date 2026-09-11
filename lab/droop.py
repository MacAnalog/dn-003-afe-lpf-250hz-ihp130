"""Supply droop: the datasheet's V_DD,min, and the device that sets it.

Why this instrument exists
--------------------------
Every topology in this repo is a STACK.  The dc ladder descends

    VDD -> voutp -> net4 -> vout_1 -> net2 -> 0

through devices that each need a few kT/q of |Vds| to stay saturated.  There is
therefore a supply below which one specific device in that ladder runs out of
headroom, its gds starts coupling nodes the small-signal derivation assumes are
isolated, and the response does not degrade gracefully -- it collapses.  A
number like "fails below 1.2 V" is useless to whoever has to budget a regulator;
"fails below 1.2 V because `in_b` leaves saturation" is a design finding.

So every supply point here carries BOTH halves: the full cheap scorecard
(`lab.metrics.evaluate`) and the per-device bias sheet (`lab.oppoint.probe`),
measured at the same supply, from decks built at that supply.

Three outcomes are kept distinct, because they mean different things:

* **PASS**    -- solved, and every line of the SCORED box inside its bounds.
                 Scored = what one `lab.metrics.evaluate` measures, today
                 S1-S6; S7 (THD) needs its own long transient and S8 is not a
                 measurement, so neither is in this verdict.
* **FAIL**    -- solved, but out of spec (this is the graceful-degradation
                 region; the scorecard says which line went first).
* **NO-CONV** -- the simulator never found a dc solution.  NOT a spec failure
                 and never reported as one: it is a missing measurement, and
                 the row carries the simulator's own message.

Mechanics
---------
`lab.config.VDD` is a module constant read at deck-build time.  A parallel sweep
CANNOT vary it by mutating `C.VDD` -- that is a race between threads that
silently pairs one point's netlist with another point's rawfile.  The supply is
therefore threaded as an explicit `vdd=` argument through `lab.deck._core`,
`lab.metrics.evaluate`/`score_plots` (which needs it for S6, P = I_core * VDD)
and `lab.oppoint.probe`.  `vdd=None` everywhere reproduces the nominal deck
byte-for-byte, so no existing caller changes behaviour.

Usage
-----
    from lab import droop
    pts = droop.sweep(design, "droop_ref")
    print(droop.table(pts))
    print(droop.explain(droop.vdd_min(pts)))
    droop.plot(pts, "droop_ref.png")

or from the command line:

    python -m lab.droop reference
    python -m lab.droop experiments/020-novel-topologies/frozen/020B.json
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import config as C
from . import metrics as M
from . import oppoint as OP
from .dut import Design
from .parallel import batch

# Columns reported per supply, in the order the table prints them.
COLS = ("fc_hz", "dc_db", "ripple_db", "ph_max_deg", "irn_uv", "p_core_nw")

_FMT = {"fc_hz": "{:.2f}", "dc_db": "{:+.4f}", "ripple_db": "{:.4f}",
        "ph_max_deg": "{:.1f}", "irn_uv": "{:.2f}", "p_core_nw": "{:.3f}",
        "peak_db": "{:+.4f}", "a1000_db": "{:.2f}", "i_core_na": "{:.3f}"}


# --------------------------------------------------------------- one point --

@dataclass
class DroopPoint:
    """One supply: the whole scorecard AND the whole bias sheet, same rail."""

    vdd: float
    values: dict = field(default_factory=dict)      # scorecard (empty if none)
    violations: list[str] = field(default_factory=list)
    ops: dict = field(default_factory=dict)         # role -> lab.oppoint.DevOp
    volts: dict = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)
    ac_error: str = ""                              # simulator message, ac+noise
    op_error: str = ""                              # simulator message, op probe

    # -- convergence is reported separately from spec compliance --
    @property
    def converged(self) -> bool:
        """The ac+noise run produced a solution.  Says nothing about spec."""
        return not self.ac_error and bool(self.values)

    @property
    def op_converged(self) -> bool:
        return not self.op_error and bool(self.ops)

    @property
    def ok(self) -> bool:
        return self.converged and not self.violations

    @property
    def status(self) -> str:
        if not self.converged:
            return "NO-CONV"
        return "PASS" if self.ok else "FAIL"

    @property
    def failing_keys(self) -> frozenset[str]:
        """Which SPEC KEYS are violated -- the identity of a failure, not its text.

        `lab.metrics.check` renders each violation as "<label> <op> <bound>: got
        <measured>" (`abs<=` as "|<label>| <= <bound>: got <measured>"),
        so two supplies that fail the SAME line produce DIFFERENT strings.  Comparing
        the strings makes every supply look like a new failure mode; comparing the
        keys is what "no new spec violation" actually means.
        """
        return frozenset(_msg_keys(self))

    @property
    def unsat(self) -> tuple[str, ...]:
        """Roles NOT saturated at this supply, least |Vds| headroom first."""
        bad = [(o.vds, r) for r, o in self.ops.items() if not o.saturated]
        return tuple(r for _, r in sorted(bad))

    @property
    def first_dropout(self) -> str | None:
        """The device with the least headroom among those out of saturation."""
        u = self.unsat
        return u[0] if u else None

    @property
    def weak_inv_lost(self) -> tuple[str, ...]:
        """Roles still saturated but no longer in weak inversion (gm/ID < 18)."""
        return tuple(r for r, o in self.ops.items()
                     if o.saturated and o.gm_id < 18)

    def get(self, key: str, default=float("nan")):
        return self.values.get(key, default)

    def dropout_detail(self, role: str | None = None) -> str:
        role = role or self.first_dropout
        if role is None or role not in self.ops:
            return "-"
        o = self.ops[role]
        return (f"{role} ({o.inst}, {o.model[-4:]}): |Vds| {o.vds*1e3:.0f} mV "
                f"(floor {OP.VDS_FLOOR*1e3:.0f}), gm/gds {o.gm_gds:.0f}, "
                f"gm/ID {o.gm_id:.1f}, ID {o.id_na:.3f} nA")


def _key_of(msg: str) -> str:
    """The SPEC key a violation sentence came from ('' -> the sentence itself)."""
    for k, (label, *_rest) in M.SPEC.items():
        if label in msg:   # substring: op+bound precede the colon, `abs<=` leads with |
            return k
    return msg              # unrecognised -- keep it, never silently drop it


def _msg_keys(p: DroopPoint) -> list[str]:
    return [_key_of(m) for m in p.violations]


# ------------------------------------------------------------------ sweep ---

def _grid(lo: float, hi: float, step: float) -> list[float]:
    n = int(round((hi - lo) / step))
    return [round(lo + i * step, 6) for i in range(n + 1)]


def _slug(v: float) -> str:
    return f"v{round(v * 1000):04d}mv"


def measure(design: Design, tag: str, vdd: float, *,
            corner: str = C.CORNER_NOM, temp: float = C.TEMP_NOM) -> DroopPoint:
    """One supply point: op probe + cheap scorecard, both built at `vdd`.

    Never raises for a simulator failure -- a rail the circuit cannot start on
    is a RESULT of the sweep, not an error in it.  The message is carried on the
    point so the table can print NO-CONV instead of a fabricated spec failure.
    """
    p = DroopPoint(vdd=vdd)
    try:
        p.ops, p.volts = OP.probe(design, f"{tag}_{_slug(vdd)}_op",
                                  corner=corner, temp=temp, vdd=vdd)
        p.problems = OP.problems(p.ops)
    except Exception as exc:                                    # noqa: BLE001
        p.op_error = _short(exc)
    try:
        s = M.evaluate(design, f"{tag}_{_slug(vdd)}", corner=corner, temp=temp,
                       vdd=vdd)
        p.values, p.violations = s.values, s.violations
    except Exception as exc:                                    # noqa: BLE001
        p.ac_error = _short(exc)
    return p


def sweep(design: Design, tag: str, *, lo: float = 1.0, hi: float = 1.8,
          step: float = 0.05, workers: int = 6, corner: str = C.CORNER_NOM,
          temp: float = C.TEMP_NOM) -> list[DroopPoint]:
    """Characterise `design` from `lo` to `hi` volts; one DroopPoint per supply.

    Two simulations per point (op probe + ac/noise) run concurrently through
    `lab.parallel.batch`.  Keep `workers` at 6 or below: each job is its own
    container and the host contends past that.
    """
    vs = _grid(lo, hi, step)
    fn = lambda v: measure(design, tag, v, corner=corner, temp=temp)  # noqa: E731
    out = batch(vs, fn, workers=workers)
    pts: list[DroopPoint] = []
    for v, r in zip(vs, out):
        if isinstance(r, Exception):        # batch() should not reach here
            pts.append(DroopPoint(vdd=v, ac_error=_short(r), op_error=_short(r)))
        else:
            pts.append(r)
    return sorted(pts, key=lambda p: p.vdd)


# ----------------------------------------------------------- the verdict ----

def _walk_down(pts: list[DroopPoint], start: int, pred) -> tuple[int | None, int | None]:
    """Walk DOWN from `start` while `pred` holds; return (floor idx, first bad idx).

    A supply floor requires a CONTIGUOUS region: an isolated pass under a
    failing rail is a coincidence, not a floor.  Walking down from the nominal
    supply (rather than from the top of the sweep) is deliberate -- V_DD,min is
    a statement about droop below nominal, so a point at 1.8 V has no vote.
    """
    if not pred(pts[start]):
        return None, start
    i = start
    while i - 1 >= 0 and pred(pts[i - 1]):
        i -= 1
    return i, (i - 1 if i - 1 >= 0 else None)


def vdd_min(results: list[DroopPoint]) -> dict:
    """Lowest supply at which every SCORED spec line passes, and what broke below.

    Scored is the S1-S6 box `lab.metrics.evaluate` measures -- this sweep runs
    no THD transient, so no floor here speaks for S7 (or for S8).

    Two floors are reported, because they answer different questions:

    * `vdd_min` -- ABSOLUTE: the lowest supply at which the design meets that
      box.  Undefined (None) for a cell that already fails a line at the
      nominal supply, and reported as undefined rather than papered over.
    * `vdd_min_rel` -- DROOP-RELATIVE: the lowest supply at which the design is
      no worse than it is at nominal, i.e. the supply drop introduces no NEW
      spec violation.  This is the number that is meaningful while a cell is
      mid-refit, and it is the honest reading of "how far can the rail sag
      before the supply itself is the problem".

    Both are read as a contiguous region walking down from the nominal supply.
    `first_fail` / `first_new_fail` name both the spec line that went first and
    the device that left saturation to cause it: `new_unsat` is the set of
    devices saturated at the floor and no longer saturated one step below --
    the dropout the supply drop actually caused, not a device that was already
    marginal at nominal.
    """
    pts = sorted(results, key=lambda p: p.vdd)
    if not pts:
        return {"vdd_min": None, "vdd_min_rel": None,
                "reason": "no points measured"}

    # Anchor at the swept point nearest the nominal supply.
    start = min(range(len(pts)), key=lambda i: abs(pts[i].vdd - C.VDD))
    nom = pts[start]
    base = nom.failing_keys

    out: dict = {
        "vdd_nom": C.VDD,
        "anchor_vdd": nom.vdd,
        "nominal": nom,
        "nominal_violations": list(nom.violations),
        "nominal_keys": sorted(base),
        "tested": (pts[0].vdd, pts[-1].vdd, len(pts)),
        "n_pass": sum(1 for p in pts if p.ok),
        "n_fail": sum(1 for p in pts if p.status == "FAIL"),
        "n_noconv": sum(1 for p in pts if p.status == "NO-CONV"),
    }

    # --- absolute floor: every scored (S1-S6) spec line passes
    fi, bi = _walk_down(pts, start, lambda p: p.ok)
    if fi is None:
        out["vdd_min"] = None
        out["reason"] = (f"the design does not meet the scored box (S1-S6) "
                         f"even at the anchor supply ({nom.vdd:.3f} V): "
                         + "; ".join(nom.violations[:2]))
        out["first_fail"] = _fail_dict(pts[bi], None) if bi is not None else None
    else:
        out["vdd_min"] = pts[fi].vdd
        out["margin_v"] = round(C.VDD - pts[fi].vdd, 6)
        out["floor_point"] = pts[fi]
        out["reason"] = (f"every scored (S1-S6) spec line passes down to "
                         f"{pts[fi].vdd:.3f} V"
                         + (f"; {pts[bi].status} at {pts[bi].vdd:.3f} V"
                            if bi is not None else
                            " (the lowest supply tested)"))
        out["first_fail"] = (_fail_dict(pts[bi], pts[fi])
                             if bi is not None else None)

    # --- droop-relative floor: no NEW violation vs the anchor supply
    def no_worse(p: DroopPoint) -> bool:
        return p.converged and p.failing_keys <= base

    rfi, rbi = _walk_down(pts, start, no_worse)
    out["vdd_min_rel"] = pts[rfi].vdd if rfi is not None else None
    if rfi is not None:
        out["margin_rel_v"] = round(C.VDD - pts[rfi].vdd, 6)
        out["rel_floor_point"] = pts[rfi]
    out["reason_rel"] = (
        f"no new spec violation down to {pts[rfi].vdd:.3f} V"
        + (f"; {pts[rbi].status} at {pts[rbi].vdd:.3f} V"
           if rbi is not None else " (the lowest supply tested)")
        if rfi is not None else
        f"the anchor supply {nom.vdd:.3f} V did not converge")
    if rbi is not None:
        fd = _fail_dict(pts[rbi], pts[rfi] if rfi is not None else None)
        new_keys = pts[rbi].failing_keys - base
        fd["new_keys"] = sorted(new_keys)
        fd["new_lines"] = [m for m, k in zip(pts[rbi].violations,
                                             _msg_keys(pts[rbi]))
                           if k in new_keys]
        fd["first_new_line"] = fd["new_lines"][0] if fd["new_lines"] else None
        out["first_new_fail"] = fd
    else:
        out["first_new_fail"] = None
    return out


def _fail_dict(bad: DroopPoint, floor: DroopPoint | None) -> dict:
    was_ok = set(floor.ops) - set(floor.unsat) if floor else set(bad.ops)
    new_unsat = tuple(r for r in bad.unsat if r in was_ok)
    limiter = new_unsat[0] if new_unsat else bad.first_dropout
    return {
        "vdd": bad.vdd,
        "status": bad.status,
        "converged": bad.converged,
        "violations": list(bad.violations),
        "first_line": bad.violations[0] if bad.violations else None,
        "unsat": bad.unsat,
        "new_unsat": new_unsat,
        "limiter": limiter,
        "limiter_detail": bad.dropout_detail(limiter),
        "weak_inv_lost": bad.weak_inv_lost,
        "error": bad.ac_error or bad.op_error or "",
        "values": dict(bad.values),
    }


def explain(v: dict) -> str:
    """The verdict as prose -- for a scorecard's summary."""
    lines: list[str] = []
    if v.get("vdd_min") is None:
        lines.append(f"**V_DD,min (full spec): NOT ESTABLISHED** — "
                     f"{v.get('reason', '')}")
    else:
        lines.append(f"**V_DD,min (full spec) = {v['vdd_min']:.3f} V** "
                     f"(nominal {v['vdd_nom']:.2f} V, margin "
                     f"{v['margin_v']:.3f} V; {v['reason']}).")
    if v.get("vdd_min_rel") is not None:
        lines.append(f"**V_DD,min (droop-relative) = {v['vdd_min_rel']:.3f} V** "
                     f"— {v['reason_rel']}. Lines already failing at the anchor "
                     f"supply, therefore excluded from this floor: "
                     + (", ".join(x.split(":")[0]
                                  for x in v["nominal_violations"]) or "none"))
    ff = v.get("first_fail") or v.get("first_new_fail")
    if v.get("first_new_fail") is not None:
        ff = v["first_new_fail"]
    if not ff:
        return "\n".join(lines) + "\nNo failing supply inside the swept range."
    if ff.get("first_new_line"):
        lines.append(f"First NEW line to go, at {ff['vdd']:.3f} V: "
                     f"{ff['first_new_line']}"
                     + (f" (+{len(ff['new_lines']) - 1} more)"
                        if len(ff["new_lines"]) > 1 else ""))
    if not ff["converged"]:
        lines.append(f"At {ff['vdd']:.3f} V the dc solution NO LONGER CONVERGES "
                     f"(not a spec failure -- a missing measurement): "
                     f"{ff['error'][:200]}")
    elif not ff.get("first_new_line"):
        lines.append(f"First line to go, at {ff['vdd']:.3f} V: {ff['first_line']}"
                     + (f" (+{len(ff['violations']) - 1} more)"
                        if len(ff["violations"]) > 1 else ""))
    if ff["limiter"]:
        lines.append(f"Attributed to **{ff['limiter']}** leaving saturation: "
                     f"{ff['limiter_detail']}.")
        if len(ff["new_unsat"]) > 1:
            lines.append(f"Dropping out at the same step: "
                         f"{', '.join(ff['new_unsat'][1:])}.")
    elif ff["unsat"]:
        lines.append(f"Devices out of saturation (already so above this rail): "
                     f"{', '.join(ff['unsat'])}.")
    else:
        lines.append("No device left saturation at that supply -- the failure is "
                     "a gradual bias shift, not a ladder dropout.")
    if ff["weak_inv_lost"]:
        lines.append(f"Left weak inversion (gm/ID < 18): "
                     f"{', '.join(ff['weak_inv_lost'])}.")
    return "\n".join(lines)


# ------------------------------------------------------------------ output --

def table(results: list[DroopPoint]) -> str:
    """One row per supply: the scorecard plus the device that dropped out."""
    head = ("| VDD (V) | fc (Hz) | dc (dB) | ripple (dB) | ph_max (deg) | "
            "IRN (uV) | P_core (nW) | verdict | first non-sat device |")
    rows = [head, "|" + "---|" * 9]
    for p in sorted(results, key=lambda q: q.vdd):
        cells = [f"{p.vdd:.3f}"]
        for c in COLS:
            val = p.values.get(c)
            cells.append("-" if val is None or (isinstance(val, float)
                                                and math.isnan(val))
                         else _FMT.get(c, "{:.4g}").format(val))
        if p.status == "PASS":
            verdict = "PASS"
        elif p.status == "NO-CONV":
            verdict = "**NO-CONV**"
        else:
            verdict = f"**FAIL** ({len(p.violations)})"
        if not p.op_converged:
            dev = "op did not converge"
        elif p.first_dropout:
            o = p.ops[p.first_dropout]
            dev = f"**{p.first_dropout}** ({o.vds*1e3:.0f} mV, gm/gds {o.gm_gds:.0f})"
        else:
            dev = "all saturated"
        rows.append("| " + " | ".join(cells + [verdict, dev]) + " |")
    return "\n".join(rows)


def failures(results: list[DroopPoint]) -> str:
    """Per-supply detail for every non-passing point -- which line, which device."""
    out = []
    for p in sorted(results, key=lambda q: q.vdd):
        if p.ok:
            continue
        out.append(f"**{p.vdd:.3f} V — {p.status}**")
        if not p.converged:
            out.append(f"  - simulator: {(p.ac_error or p.op_error)[:300]}")
        for v in p.violations:
            out.append(f"  - {v}")
        for pr in p.problems:
            out.append(f"  - bias: {pr}")
    return "\n".join(out) if out else "no failing supply in the swept range"


def plot(results: list[DroopPoint], path="droop.png", *,
         title="Supply droop: response vs VDD"):
    """fc, passband and IRN/power against supply, with the spec boxes drawn on.

    Axis choices are forced by what the data does.  A stacked topology does not
    drift as the rail sags, it COLLAPSES: fc spans three decades and IRN five
    across an 0.8 V sweep, so both are log.  The passband axis is symlog with a
    linear threshold at the 0.2 dB spec box, which is the only way to show a
    +-0.2 dB budget and a -58 dB collapse on one pair of axes without hiding
    either.

    Shading marks the DROOP-DEGRADED region -- supplies where a spec line fails
    that does NOT fail at the anchor supply -- not simply every failing supply.
    On a cell that is already out of spec at nominal the latter shades the whole
    figure and says nothing about droop.

    Follows `lab.plot` conventions: matplotlib Agg, the shared palette, the
    shared axis styling, and `figs/` as the default destination.
    """
    from .plot import _COLORS, _save, _style
    import matplotlib.pyplot as plt
    import numpy as np

    pts = sorted(results, key=lambda p: p.vdd)
    solved = [p for p in pts if p.converged]
    xs = [p.vdd for p in solved]
    v = vdd_min(pts)
    base = set(v.get("nominal_keys") or ())

    fig, axes = plt.subplots(3, 1, figsize=(7.6, 8.4), sharex=True)
    a_fc, a_dc, a_n = axes

    # -- S2: cutoff
    a_fc.plot(xs, [p.get("fc_hz") for p in solved], "o-", color=_COLORS[1],
              lw=1.6, ms=4)
    a_fc.axhspan(245, 255, color="#2ca02c", alpha=0.18, zorder=0)
    a_fc.axhline(250, color="0.55", ls=":", lw=1)
    a_fc.set_yscale("log")
    a_fc.annotate("S2: 250 Hz ± 2 %", (0.015, 0.94), xycoords="axes fraction",
                  fontsize=8, color="#2ca02c", va="top")
    _style(a_fc, "", "cutoff fc (Hz)", title)

    # -- S3 / S3f: passband gain and flatness
    a_dc.plot(xs, [p.get("dc_db") for p in solved], "o-", color=_COLORS[2],
              lw=1.6, ms=4, label="dc gain (S3)")
    a_dc.plot(xs, [p.get("ripple_db") for p in solved], "s--", color=_COLORS[3],
              lw=1.4, ms=3.5, label="passband ripple to 150 Hz (S3f)")
    a_dc.set_yscale("symlog", linthresh=0.2)
    a_dc.axhspan(-0.2, 0.2, color="#2ca02c", alpha=0.18, zorder=0)
    a_dc.axhline(0.2, color="#d62728", ls="--", lw=1)
    a_dc.annotate("S3 / S3f box: ±0.2 dB", (0.985, 0.95), xycoords="axes fraction",
                  fontsize=8, color="#d62728", va="top", ha="right")
    _style(a_dc, "", "passband (dB, symlog)")
    a_dc.legend(fontsize=8, loc="lower right")

    # -- S5 / S6: noise and power
    a_n.plot(xs, [p.get("irn_uv") for p in solved], "o-", color=_COLORS[4],
             lw=1.6, ms=4, label="IRN 0.5–200 Hz (µVrms)")
    a_n.axhline(40, color="#d62728", ls="--", lw=1.2)
    a_n.set_yscale("log")
    a_n.annotate("S5: < 40 µVrms", (0.985, 0.06), xycoords="axes fraction",
                 fontsize=8, color="#d62728", va="bottom", ha="right")
    a_n2 = a_n.twinx()
    a_n2.plot(xs, [p.get("p_core_nw") for p in solved], "s--", color=_COLORS[5],
              lw=1.4, ms=3.5, label="filter-core power (nW)")
    a_n2.axhline(50, color=_COLORS[5], ls=":", lw=1.1)
    a_n2.set_yscale("log")
    a_n2.set_ylabel("filter-core power (nW) — S6 < 50", fontsize=9,
                    color=_COLORS[5])
    a_n2.tick_params(labelsize=9, colors=_COLORS[5])
    _style(a_n, "supply VDD (V)", "IRN 0.5–200 Hz (µVrms)")
    h1, l1 = a_n.get_legend_handles_labels()
    h2, l2 = a_n2.get_legend_handles_labels()
    a_n.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper center")

    # -- the verdict, drawn.  A cell that already fails a line at the anchor
    # supply has no absolute floor, so the droop-relative floor is drawn
    # instead and LABELLED "(rel)" -- never silently substituted.
    if v.get("vdd_min") is not None:
        floor_v, floor_kind = v["vdd_min"], ""
    else:
        floor_v, floor_kind = v.get("vdd_min_rel"), " (rel)"
    dx = _dx(pts)
    for ax in axes:
        for p in pts:
            if p.status == "NO-CONV":
                ax.axvspan(p.vdd - 0.5 * dx, p.vdd + 0.5 * dx, color="0.55",
                           alpha=0.35, lw=0, zorder=0)
            elif p.failing_keys - base:          # a NEW failure vs the anchor
                ax.axvspan(p.vdd - 0.5 * dx, p.vdd + 0.5 * dx, color="#d62728",
                           alpha=0.10, lw=0, zorder=0)
        if floor_v is not None:
            ax.axvline(floor_v, color="#d62728", ls="-", lw=1.4, zorder=1)
        ax.axvline(C.VDD, color="0.35", ls=":", lw=1.2, zorder=1)
    a_fc.annotate(f"nominal {C.VDD:g} V", (C.VDD, 0.98),
                  xycoords=("data", "axes fraction"), fontsize=8, color="0.35",
                  ha="right", va="top", rotation=90,
                  textcoords="offset points", xytext=(-3, 0))
    if floor_v is not None:
        ff = v.get("first_new_fail") or v.get("first_fail") or {}
        lim = (f"\n{ff['limiter']} leaves saturation below"
               if ff.get("limiter") else "")
        a_fc.annotate(f"V$_{{DD,min}}${floor_kind} = {floor_v:.2f} V{lim}",
                      (floor_v, 0.02), xycoords=("data", "axes fraction"),
                      fontsize=8, color="#d62728", va="bottom", ha="left",
                      textcoords="offset points", xytext=(5, 0))
    fig.tight_layout()
    return _save(fig, path)


def _dx(pts: list[DroopPoint]) -> float:
    return (pts[1].vdd - pts[0].vdd) if len(pts) > 1 else 0.05


def _short(exc: Exception) -> str:
    s = str(exc).strip().replace("\n", " | ")
    return s[:400] if s else exc.__class__.__name__


# -------------------------------------------------------------------- cli ---

def _load(name: str) -> tuple[str, Design]:
    """`reference`, a frozen cell name (020B), or a path to a design JSON."""
    import importlib.util
    import sys
    from pathlib import Path
    sys.path.insert(0, str(C.REPO))
    # Reuse certify.load rather than re-implementing the JSON -> Design mapping:
    # a second reader is a second chance to disagree about what a frozen cell is.
    spec = importlib.util.spec_from_file_location(
        "certify", C.REPO / "experiments" / "020-novel-topologies" / "certify.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if name in ("reference", "ref"):
        return "reference", mod.load(C.REPO / "decks" / "reference" / "design.json")
    p = Path(name)
    if not p.exists():
        p = C.REPO / "experiments" / "020-novel-topologies" / "frozen" / f"{name}.json"
    return p.stem, mod.load(p)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="supply-droop characterisation")
    ap.add_argument("design", nargs="?", default="reference")
    ap.add_argument("--lo", type=float, default=1.0)
    ap.add_argument("--hi", type=float, default=1.8)
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tag", default="")
    ap.add_argument("--png", default="")
    a = ap.parse_args(argv)

    name, d = _load(a.design)
    tag = a.tag or f"droop_{name}"
    pts = sweep(d, tag, lo=a.lo, hi=a.hi, step=a.step, workers=a.workers)
    print(f"\n## {name} — supply droop ({d.topology})\n")
    print(table(pts))
    v = vdd_min(pts)
    print("\n" + explain(v) + "\n")
    print("### failing supplies\n")
    print(failures(pts))
    png = plot(pts, a.png or f"droop_{name}.png",
               title=f"Supply droop — {name} ({d.topology})")
    print(f"\nfigure -> {png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
