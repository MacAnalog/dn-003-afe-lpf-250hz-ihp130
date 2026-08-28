"""Symbolic small-signal model of the LPF core, built with `spicexplorer_netlist2tf`.

The one place that knows how to turn an as-built SPICE subckt of this cell into an MNA
system whose symbols are bound to the MEASURED operating point.  Everything downstream --
transfer function, poles/zeros, per-biquad Q, noise transimpedances -- is a solve over
the system this module returns.

Four facts about this cell make the mapping exact, and all four are asserted here:

* **Every device has bulk tied to source.**  Each PMOS sits in its own n-well whose
  contact is the source; every NMOS source is at 0, which is also its bulk.  So `gmb` is
  inert (v_bs == 0 identically), `csb` is shorted out, and the PSP `cgb` op-var -- which
  in weak inversion carries essentially ALL of the gate capacitance, because the channel
  is not formed -- lands between gate and source and is folded into `cgs`.
  (Measured on `in_a`: cgg = 250.5 fF of which cgb = 247.4 fF and cgs = 3.1 fF -- so
  taking the `cgs` op-var alone as the gate-to-source capacitance, which is the
  strong-inversion habit, is 81x too small.)
* **The bias rail `vbn` is not an ac ground**: the testbench terminates it with one
  mirror diode, so that diode is part of the model (`xmbn`, geometry copied from the
  design's bias unit at m = 1, exactly as `lab.deck._bias` emits it).
* **`vbr` is generated inside the cell** by the three-device replica branch, so it is a
  solved node, not a rail: the replica is in the matrix.
* **The differential drive is netlist2tf's own `drive="dm"`** (+-1/2 at vinp/vinn), which
  is the bench balun convention verbatim: `vinp - vinn = 1`.

Runs in the PLATFORM venv (it needs `spicexplorer_netlist2tf`); it reads only committed
netlists and the JSON that `extract_bench.py` produced, never the simulator.
"""
from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import sympy as sp
from spicexplorer_core.spice_engine import NetlistView
from spicexplorer_netlist2tf import (
    Fidelity,
    build_system,
    extract_tf,
    ingest_netlist,
    small_signal_model,
    transimpedance,
)
from spicexplorer_netlist2tf.tf import S

REPO = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"

PORT_OUT = ("voutp", "voutn")
PORT_IN = ("vinp", "vinn")

# Small-signal symbol roots netlist2tf mints per instance, at Fidelity.FULL.
SYMBOL_ROOTS = ("gm", "ro", "gmb", "cgs", "cgd", "cdb", "csb")


# --------------------------------------------------------------------- netlist prep --
def _prep(text: str) -> str:
    """Upper-case every device reference and prepend a title comment.

    Both are `spicelib` parser requirements, not netlist2tf ones: `detect_encoding`
    demands a leading `*`, and `SpiceComponent` rejects a lower-case reference designator
    outright.  The certified decks are lower-case throughout, so this normalisation is
    unavoidable; it is deliberately the ONLY edit made to the as-built text.
    """
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s and s[0].isalpha():
            head, _, rest = s.partition(" ")
            s = head.upper() + (" " + rest if rest else "")
        out.append(s)
    return "* analysis copy (refs upper-cased for spicelib)\n" + "\n".join(out) + "\n.end\n"


_BIAS_UNIT = re.compile(r"(?im)^\s*xm9\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(.*)$")

# The PDK MIM capacitor, as `lab.dut` draws and values it (CMIM_CAREA / CMIM_CJSW):
# `m` identical square units of side `s` um.  A small-signal model needs the farads, and
# the PDK's own subckt is not resolvable outside a simulator run, so the card is rewritten
# into a plain `C` here -- with the SAME arithmetic `lab.dut.cmim_value` uses, so the
# model's capacitance is the design's realised capacitance to the last digit.
CMIM_CAREA = 1.5e-15          # F / um^2
CMIM_CJSW = 40e-18            # F / um of perimeter
_MIM_CARD = re.compile(
    r"(?im)^(\s*)x(\S+)\s+(\S+)\s+(\S+)\s+cap_cmim\s+w=([\d.eE+-]+)u?\s+"
    r"l=([\d.eE+-]+)u?\s+m=(\d+)\s*$")


def _mim_value(s_um: float, m: int) -> float:
    """Realised farads of `m` square MIM units of side `s_um` (`lab.dut.cmim_value`)."""
    return m * (CMIM_CAREA * s_um * s_um + 2 * CMIM_CJSW * (2 * s_um))


def _numericize_mim(text: str) -> tuple[str, dict[str, float]]:
    """Rewrite every `cap_cmim` instance as a plain capacitor of its realised value."""
    got: dict[str, float] = {}

    def rep(m: re.Match) -> str:
        indent, ref, n1, n2 = m.group(1), m.group(2), m.group(3), m.group(4)
        side, mult = float(m.group(5)), int(m.group(7))
        val = _mim_value(side, mult)
        got[ref.lower()] = val
        # Keep the reference designator the netlist already uses (`xc13` -> `c13`), so the
        # half-circuit's cap tables still recognise it by name.
        name = ref if ref[:1].lower() == "c" else "c" + ref
        return f"{indent}{name} {n1} {n2} {val:.12g}"

    return _MIM_CARD.sub(rep, text), got


def _mirror_card(core_text: str) -> str:
    """The bench's `vbn` mirror diode, geometry copied from the design's bias unit."""
    m = _BIAS_UNIT.search(core_text)
    if not m:
        raise ValueError("no bias unit (xm9) in this netlist to copy the mirror diode from")
    model, params = m.group(1), re.sub(r"\bm=\d+\b", "m=1", m.group(2))
    return f"  xmbn vbn vbn 0 0 {model} {params}"


def load_core(core_sp: Path | str, *, mirror_from: str | None = None, extra: str = ""):
    """Ingest an as-built `.subckt lpf_core ...` into the netlist2tf IR.

    `mirror_from` is the schematic netlist text to copy the `vbn` mirror diode out of --
    needed because the post-layout netlist's instances are called `XM_n` and carry no
    role, so it cannot name its own bias unit.
    """
    body, _mim = _numericize_mim(Path(core_sp).read_text().replace("$", "_"))
    card = _mirror_card(mirror_from if mirror_from is not None else body)
    body = re.sub(r"(?im)^(\.ends.*)$", (card + "\n" + extra).rstrip() + r"\n\1", body, count=1)
    f = Path(tempfile.mkdtemp()) / "core.sp"
    f.write_text(_prep(body))
    view = NetlistView.from_file(f).get_subcircuit_named("lpf_core")
    return ingest_netlist(view, name="lpf_core", ports={"in": PORT_IN, "out": PORT_OUT})


# ------------------------------------------------------------------ operating point --
@dataclass(frozen=True)
class OpBinding:
    """Measured small-signal parameters, keyed by the symbol names netlist2tf mints."""

    subs: dict[str, float]
    per_instance: dict[str, dict[str, float]]
    roles: dict[str, str | None]

    def instances_of(self, role: str) -> list[str]:
        return [i for i, r in self.roles.items() if r == role]


def _label(ref: str) -> str:
    """netlist2tf's per-instance symbol label (`models._label`): strip an X wrapper."""
    up = ref.upper()
    return ref[1:].lower() if up.startswith(("XM", "XR", "XC", "XL")) else ref.lower()


def bind_op(bench_json: Path | str) -> OpBinding:
    """Bind the measured per-instance operating point onto netlist2tf's symbols.

    Capacitance folding, all four consequences of bulk == source in this cell:

        cgs_eff = cgs + cgb    the subthreshold gate charge sits on the bulk terminal
        cgd_eff = cgd
        cdb_eff = cdb + cjd    intrinsic drain-bulk plus the drain junction
        csb_eff = 0            source and bulk are one node: the cap is shorted out
        gmb     = 0            v_bs == 0 identically

    Every value is taken |.| because PSP reports a PMOS's gm/ids negative.
    """
    rec = json.loads(Path(bench_json).read_text())
    subs: dict[str, float] = {}
    per: dict[str, dict[str, float]] = {}
    roles: dict[str, str | None] = {}
    for inst, o in rec["op"].items():
        nets = o.get("nets", {})
        if nets and nets.get("s") != nets.get("b"):
            raise ValueError(f"{inst}: bulk {nets.get('b')} is not the source {nets.get('s')} "
                             "-- the gmb/cgb folding below is only valid when they are one node")
        lab = _label("x" + inst if not inst.lower().startswith("x") else inst)
        vals = {
            "gm": abs(o["gm"]),
            "ro": 1.0 / abs(o["gds"]),
            "gmb": 0.0,
            "cgs": abs(o.get("cgs", 0.0)) + abs(o.get("cgb", 0.0)),
            "cgd": abs(o.get("cgd", 0.0)),
            "cdb": abs(o.get("cdb", 0.0)) + abs(o.get("cjd", 0.0)),
            "csb": 0.0,
        }
        per[lab] = vals
        roles[lab] = o.get("role")
        for k, v in vals.items():
            subs[f"{k}_{lab}"] = v
    return OpBinding(subs=subs, per_instance=per, roles=roles)


# ------------------------------------------------------------------------- the solve --
def build(core_sp: Path | str, op: OpBinding, *, level: Fidelity = Fidelity.FULL,
          numeric: bool = True, mirror_from: str | None = None, extra: str = ""):
    """(ir, ssir, system) for one as-built netlist at one measured operating point.

    `numeric=True` substitutes every measured symbol at stamp time, leaving only `s`
    symbolic -- that is what makes the full 4th-order DIFFERENTIAL solve (13 nodes, 16
    transistors, every device capacitance) both tractable and exact.  `numeric=False`
    keeps it fully symbolic, which is only usable on a reduced half-circuit.
    """
    ir = load_core(core_sp, mirror_from=mirror_from, extra=extra)
    ssir = small_signal_model(ir, level=level)
    system = build_system(ssir, subs=op.subs if numeric else None)
    missing = sorted(n for n in system.free_symbols if n != "s" and numeric)
    if missing:
        raise ValueError(f"unbound symbols after numericization: {missing[:10]}")
    return ir, ssir, system


def h_diff(system):
    """H(s) = (voutp - voutn) / (vinp - vinn), the differential transfer function."""
    return extract_tf(system, PORT_OUT, PORT_IN, drive="dm")


def z_noise(system, inject: tuple[str, str]):
    """Transimpedance from a unit current forced `inject[0]` -> `inject[1]` to the
    differential output: the noise transfer function of a generator across that pair."""
    return transimpedance(system, PORT_OUT, inject)


def poly_coeffs(expr: sp.Expr) -> tuple[list[complex], list[complex]]:
    """(numerator, denominator) coefficients of H(s), highest power first."""
    num, den = sp.fraction(sp.cancel(sp.together(expr)))
    pn = sp.Poly(sp.expand(num), S)
    pd = sp.Poly(sp.expand(den), S)
    return [complex(c) for c in pn.all_coeffs()], [complex(c) for c in pd.all_coeffs()]


# ------------------------------------------------------- the differential half-circuit --
# Nets that lie ON the symmetry axis of the fully differential cell: they are shared by both
# halves and carry no differential signal, so a differential excitation leaves them at their
# dc value.  In the DM half-circuit they are ac grounds.
CM_NETS = ("vbn", "vbr", "rep_x", "vdd", "vbp")
# The two halves, as (P-half instance, N-half instance).  Only the P half survives.
HALF_PAIRS = (("m2", "m5"), ("m4", "m8"), ("m9", "m10"), ("mst", "mstn"),
              ("m0", "m1"), ("m14", "m15"))
# Devices in the shared branch: they sit on the axis and drop out of the DM half-circuit.
SHARED_DEVS = ("r1", "r2", "r3", "mbn")
# Capacitors that bridge the two halves.  Under differential excitation the far plate moves
# by exactly -v, so a floating C between the halves loads one half with 2C to the virtual
# ground -- the "floating differential capacitor" of the `fvf-2nd` technique, which is why
# the drawn farads are half what a grounded realisation would need.
CROSS_CAPS = {"c19": ("vout_1", "c2_a"), "c12": ("voutp", "c2_b")}
# Capacitors wholly inside one half: kept verbatim (P half), N-half twin dropped.
HALF_CAPS = {"c13": "c1_a", "c1": "c1_b"}
DROP_CAPS = ("c17", "c10")

# Readable names for the four design capacitors in the symbolic form.
CAP_SYMBOL = {"c1_a": "C1a", "c2_a": "C2a", "c1_b": "C1b", "c2_b": "C2b"}
# Readable names for the six half-circuit devices, by instance.
DEV_SYMBOL = {"m2": "ia", "m4": "fa", "m9": "ba", "mst": "br", "m0": "ib", "m14": "fb"}

_CARD = re.compile(r"(?im)^\s*([a-z]\S*)\s+(.*)$")


def half_circuit(core_sp: Path | str, *, symbolic_caps: bool = False
                 ) -> tuple[str, dict[str, float]]:
    """The exact DM half-circuit of the as-built cell, as SPICE text.

    Exact, not approximate: the cell is drawn perfectly symmetric (same devices, same
    sizes, both halves), so under a differential excitation every axis net is a virtual
    ground and the two halves are mirror images.  `symbolic_tf.py` proves it numerically
    by comparing this half-circuit's H(s) against the full 13-node differential solve and
    against the ac sweep.

    `symbolic_caps` emits the four design capacitors as the SYMBOLS `C1a, C2a, C1b, C2b`
    (a cross cap as `2*C2x`, which is where the factor of two becomes visible in the
    algebra) instead of their farads -- that is what turns the exact solve into a readable
    equation rather than a pile of floats.

    Returns the netlist and the cross-cap doubling it applied, so the caller can report it.
    """
    text, _mim = _numericize_mim(Path(core_sp).read_text().replace("$", "_"))
    keep_dev = {p for p, _ in HALF_PAIRS}
    drop_dev = {n for _, n in HALF_PAIRS} | set(SHARED_DEVS)
    lines, doubled = [], {}
    for raw_line in text.splitlines():
        s = raw_line.strip()
        m = _CARD.match(s)
        if not m or s.lower().startswith(("." , "*")):
            continue
        ref, rest = m.group(1).lower(), m.group(2)
        base = ref[1:] if ref.startswith("x") else ref
        if base in drop_dev or base in DROP_CAPS:
            continue
        if base in keep_dev:
            lines.append(f"  {ref} {rest}")
        elif base in CROSS_CAPS:
            node, name = CROSS_CAPS[base]
            val = float(rest.split()[-1])
            doubled[name] = 2 * val
            sym = "2*" + CAP_SYMBOL[name]
            lines.append(f"  {ref} {node} 0 " + ("{" + sym + "}" if symbolic_caps
                                                 else f"{2 * val:.10g}"))
        elif base in HALF_CAPS:
            if symbolic_caps:
                nodes = " ".join(rest.split()[:2])
                lines.append(f"  {ref} {nodes} " + "{" + CAP_SYMBOL[HALF_CAPS[base]] + "}")
            else:
                lines.append(f"  {ref} {rest}")
    body = "\n".join(lines)
    return f".subckt lpf_half vinp voutp vbn vbr vdd\n{body}\n.ends lpf_half\n", doubled


def build_half(core_sp: Path | str, op: OpBinding | None = None, *,
               level: Fidelity = Fidelity.FULL, numeric: bool = True,
               symbolic_caps: bool = False):
    """(ir, ssir, system, doubled) for the DM half-circuit; axis nets forced to ac ground."""
    text, doubled = half_circuit(core_sp, symbolic_caps=symbolic_caps)
    f = Path(tempfile.mkdtemp()) / "half.sp"
    f.write_text(_prep(text))
    view = NetlistView.from_file(f).get_subcircuit_named("lpf_half")
    ir = ingest_netlist(view, name="lpf_half",
                        ports={"in": ("vinp", "0"), "out": ("voutp", "0")})
    ssir = small_signal_model(ir, level=level)
    system = build_system(ssir, subs=(op.subs if (op and numeric) else None),
                          extra_grounds=set(CM_NETS))
    return ir, ssir, system, doubled


def h_half(system):
    """H(s) = voutp / vinp on the half-circuit == the differential H(s) of the full cell
    (both the input and the output are halved by the same factor, so the ratio is equal)."""
    return extract_tf(system, ("voutp", "0"), ("vinp", "0"))


def rename_symbols(expr: sp.Expr) -> sp.Expr:
    """Rewrite netlist2tf's per-instance symbols into the design's role names.

    `gm_m2` -> `gm_ia` (the biquad-A input follower), `gm_mst` -> `gm_br` (the bridge), and
    so on, so the printed equation reads in the language of `doc/design-reference.md`
    instead of in netlist instance numbers.
    """
    sub = {}
    for inst, role in DEV_SYMBOL.items():
        for root in SYMBOL_ROOTS:
            old = sp.Symbol(f"{root}_{inst}", positive=True)
            if old in expr.free_symbols:
                sub[old] = sp.Symbol(f"{root}_{role}", positive=True)
    return expr.subs(sub)
