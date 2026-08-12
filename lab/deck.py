"""Deck assembly: a `Design` plus an analysis becomes a runnable ngspice deck.

Decks are BUILT, never text-edited.  That is the whole point of this module: a
sizing sweep changes a `Design`, and every deck in the run -- ac, noise, THD,
corner, Monte-Carlo -- is regenerated from it, so a scorecard can never mix a
netlist from one sizing point with a measurement from another.

The testbench mirrors the originating bench's *measurement contract* exactly,
because every spec number is defined against it (doc/benches.md):

* a **balun** pair of controlled sources (gain +-0.5) drives vinp/vinn from one
  differential source `vsig`, so `vsig`'s own amplitude IS the differential
  input.  175 mVpp differential therefore means `ampl = 87.5 m`, and a noise
  analysis referred to `vsig` is directly the differential input-referred noise.
* a **series supply probe** `vflt` carries the filter core's current and nothing
  else, so S6 (filter-core power) is a single measurement and not a subtraction.
  The bias reference network hangs off the supply ahead of that probe and is
  therefore excluded, exactly as the spec says.
* the bias reference itself is one ideal current source into a real mirror.  It
  is a *reference*, excluded from S6 by definition; keeping it ideal stops a
  reference design choice from contaminating a filter comparison.
"""
from __future__ import annotations

from . import config as C
from .dut import NCH, PCH, Design, subckt

# --------------------------------------------------------------- fragments --

def _libs(corner: str = C.CORNER_NOM) -> str:
    return f".lib {C.MOS_LIB_HV} {corner}"


def _bias(d: Design) -> str:
    """One ideal reference current into a real n/p mirror pair.

    Sits on `vdd_top`, i.e. AHEAD of the core probe -> excluded from S6.

    The two diode devices are built from the DESIGN's own bias unit geometries
    with m = 1, so a bias device drawn at m = k carries exactly k * iref.  Using
    an arbitrary diode geometry instead silently scales every branch current by
    a W/L ratio -- which is what rails biquad A's internal node and leaves the
    shunt-feedback device switched off while the ac response still looks like a
    plausible (if mis-tuned) low-pass.  See doc/journal/mirror-unit-must-match.md.
    """
    from .dut import NROLES_BY_TOPOLOGY
    nr = NROLES_BY_TOPOLOGY.get(d.topology, frozenset())
    def _unit(order, want_n):
        for r in order:
            if r in d.devs and ((r in nr) == want_n):
                return d.devs[r]
        # Fall back to ANY device of the right flavour: a topology that mirrors
        # only one polarity (e.g. the merge, which needs no p-side mirror) still
        # has to emit a well-formed diode for the unused rail.
        for r, dev in d.devs.items():
            if (r in nr) == want_n:
                return dev
        raise KeyError(f"no {'n' if want_n else 'p'}-type device in {d.topology}")

    un = _unit(("bias_a_int", "bias_a_out", "bias_b_int"), True)
    up = _unit(("bias_a_out", "bias_b_out", "bias_a_int"), False)
    return "\n".join([
        f"iref vdd_top vbn {d.iref:.6g}",
        f"xmbn vbn vbn 0 0 {NCH} w={un.w:.6g} l={un.l:.6g} ng={un.ng} m=1",
        f"xmbp vbp vbn 0 0 {NCH} w={un.w:.6g} l={un.l:.6g} ng={un.ng} m=1",
        f"xmbpd vbp vbp vdd_top vdd_top {PCH} w={up.w:.6g} l={up.l:.6g} ng={up.ng} m=1",
    ])


def _core(d: Design, ic: bool = True) -> str:
    """Supply probes, the DUT instance, and the dc-solution hints."""
    lines = [
        f"vdd_meas vdd_top 0 {C.VDD}",
        "vflt vdd_top vdd 0",
        f"xdut vinp vinn voutp voutn vbn vbp vdd lpf_core",
    ]
    if ic:
        # nodeset, not .ic: a nodeset is a HINT the dc solver may leave, an .ic
        # is a CLAMP held through the operating point.  Clamping this circuit
        # lands it in a latched basin that looks like a valid dc point and
        # scores as a pass.  See doc/journal/nodeset-not-ic.md.
        # Internal DUT nodes must be qualified with the instance name; ngspice
        # silently warns "Nodeset on non-existent node" and carries on, so an
        # unqualified hint is a no-op that looks like it worked.
        vh = d.vocm
        lines.append(f".nodeset v(xdut.vout_1)={vh} v(xdut.vout_2)={vh} "
                     f"v(voutp)={vh} v(voutn)={vh}")
    return "\n".join(lines)


# Nets worth naming explicitly in a `save`.  NOTE: an explicit `save` also
# STARVES the noise analysis -- ngspice reports "no data saved for Noise
# analysis; analysis not run" and then leaves the previous plot current, so the
# rawfile silently contains the ac plot twice and the scorecard reads NaN for
# S5 rather than failing loudly.  So the ac+noise deck deliberately does NOT
# restrict its saves; only the transient deck does, where the ~750 PSP103
# internal nodes per device actually dominate the file.
SIGNAL_NETS = ("voutp", "voutn", "vinp", "vinn", "sig", "vcm", "vbn", "vbp", "vdd")


def _save(extra: tuple[str, ...] = ()) -> str:
    nets = " ".join(f"v({n})" for n in SIGNAL_NETS)
    nets += " " + " ".join(f"v(xdut.{n})" for n in
                           ("vout_1", "vout_2", "net1", "net2", "net3", "net4"))
    cur = f"i({C.CORE_PROBE}) i({C.SUPPLY_PROBE}) i({C.IN_SRC})"
    return "save " + nets + " " + cur + ("" if not extra else " " + " ".join(extra))


def _stim_ac(vicm: float) -> str:
    return "\n".join([
        f"vcm vcm 0 {vicm}",
        f"{C.IN_SRC} sig vcm dc 0 ac 1",
        "evp vinp vcm sig vcm 0.5",
        "evn vinn vcm sig vcm -0.5",
    ])


def _stim_sine(fin: float, ampl: float, vicm: float) -> str:
    return "\n".join([
        f"vcm vcm 0 {vicm}",
        f"{C.IN_SRC} sig vcm dc 0 sin(0 {ampl:.6g} {fin:.6g}) ac 1",
        "evp vinp vcm sig vcm 0.5",
        "evn vinn vcm sig vcm -0.5",
    ])


# ------------------------------------------------------------------ decks ---

def ac_noise(d: Design, *, corner: str = C.CORNER_NOM, temp: float = C.TEMP_NOM,
             fstart: float = 0.1, fstop: float = 1e5, dec: int = 10,
             nstop: float = 1e3) -> str:
    """The cheap scorecard deck: op + ac + noise in one run, one rawfile.

    `dec = 10` matches the originating bench's sweep density so the phase
    certificate is scored on the same grid it was defined on.  Raise it only for
    a diagnostic (see `lab.metrics.ph_max_hires`).
    """
    return f""".title lpf {d.topology} -- ac + noise
{_libs(corner)}
{subckt(d)}
{_core(d)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {temp}
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec {dec} {fstart:.6g} {fstop:.6g}
write sim.raw
noise v({C.OUT_P},{C.OUT_N}) {C.IN_SRC} dec {dec} {fstart:.6g} {nstop:.6g}
setplot noise1
write sim.raw
.endc
.end
"""


def op_only(d: Design, *, corner: str = C.CORNER_NOM, temp: float = C.TEMP_NOM,
            probes: list[str] | None = None) -> str:
    """Operating point with per-device parameters printed -- the sizing tool.

    `probes` are ngspice device-parameter expressions; `lab.metrics.op_table`
    builds them from a `Design` so a sizing loop can read gm, gm/ID, Vdsat and
    Vds per role without guessing instance names.
    """
    pr = "\n".join(f"print {p}" for p in (probes or []))
    return f""".title lpf {d.topology} -- operating point
{_libs(corner)}
{subckt(d)}
{_core(d)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {temp}
.control
set filetype=binary
op
write sim.raw
{pr}
.endc
.end
"""


def tran_thd(d: Design, fin: float, ampl: float, *, cycles: int = 20,
             settle: int = 8, ppc: int = 512, corner: str = C.CORNER_NOM,
             temp: float = C.TEMP_NOM) -> str:
    """Coherent strobed transient for THD.

    The transient is STROBED at an exact integer number of points per input
    cycle over an exact integer number of cycles, so the FFT grid lands on the
    fundamental and its harmonics with no leakage and no window needed.  The
    first `settle` cycles are simulated and discarded.

    `ampl` is the DIFFERENTIAL amplitude: 175 mVpp differential => ampl=87.5m.
    """
    tper = 1.0 / fin
    tstop = (settle + cycles) * tper
    tstep = tper / ppc
    return f""".title lpf {d.topology} -- thd fin={fin:g} ampl={ampl:g}
{_libs(corner)}
{subckt(d)}
{_core(d)}
{_bias(d)}
{_stim_sine(fin, ampl, d.vicm)}
.temp {temp}
.options reltol=1e-5 abstol=1e-15 vntol=1e-9 chgtol=1e-16 method=gear maxord=2
.control
set filetype=binary
op
tran {tstep:.10g} {tstop:.10g} {settle * tper:.10g} {tstep:.10g}
write sim.raw
.endc
.end
"""


def vdd_sweep(d: Design, lo: float, hi: float, step: float,
              *, corner: str = C.CORNER_NOM) -> str:
    """Supply-droop characterisation (report-only; the datasheet's VDD_min)."""
    return f""".title lpf {d.topology} -- vdd sweep
{_libs(corner)}
{subckt(d)}
{_core(d, ic=False)}
{_bias(d)}
{_stim_ac(d.vicm)}
.control
set filetype=binary
dc vdd_meas {lo:.6g} {hi:.6g} {step:.6g}
write sim.raw
.endc
.end
"""
