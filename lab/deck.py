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

def _libs(corner: str = C.CORNER_NOM, d: Design | None = None) -> str:
    """The corner-library lines this deck needs.

    `d=None` (or an all-hv design) emits exactly the single hv line it always
    has -- `decks/reference/lpf_tb.sp` is sha-pinned, so this branch must stay
    byte-identical.  A design with lv roles additionally loads the lv corner
    file; both use the SAME section name, which is what keeps a corner sweep
    meaningful across a mixed-flavour cell.
    """
    libs = d.libs() if d is not None else (C.MOS_LIB_HV,)
    return "\n".join(f".lib {lib} {corner}" for lib in libs)


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
    # alpha = 0 -> a plain dc source, so the deck text (and its hash) is
    # byte-identical to every run made before the knob existed.
    if C.BIAS_ALPHA:
        src = (f"bref vdd_top vbn i = {d.iref:.6g}"
               f"*pow((temper+273.15)/{C.BIAS_TNOM_K:g},{C.BIAS_ALPHA:g})")
    else:
        src = f"iref vdd_top vbn {d.iref:.6g}"
    return "\n".join([
        src,
        f"xmbn vbn vbn 0 0 {NCH} w={un.w:.6g} l={un.l:.6g} ng={un.ng} m=1",
        f"xmbp vbp vbn 0 0 {NCH} w={un.w:.6g} l={un.l:.6g} ng={un.ng} m=1",
        f"xmbpd vbp vbp vdd_top vdd_top {PCH} w={up.w:.6g} l={up.l:.6g} ng={up.ng} m=1",
    ])


def _core(d: Design, ic: bool = True, vdd: float | None = None) -> str:
    """Supply probes, the DUT instance, and the dc-solution hints.

    `vdd` overrides `lab.config.VDD` for THIS deck only.  It is a parameter and
    not a module global on purpose: a supply sweep runs in a thread pool
    (`lab.parallel.batch`), and mutating `C.VDD` per point is a race that
    silently mixes one point's netlist with another point's measurement.
    `vdd=None` reproduces the nominal deck byte-for-byte.
    """
    v = C.VDD if vdd is None else vdd
    lines = [
        f"vdd_meas vdd_top 0 {v}",
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
        # The hint is clamped to the supply: on a drooped rail an output-CM
        # hint ABOVE vdd points the solver at a node voltage the circuit cannot
        # reach, which turns a legitimate "degrades gracefully" point into a
        # spurious non-convergence.  At the nominal supply the clamp is inert
        # (vocm 1.25 < VDD 1.5), so nominal decks are unchanged.
        vh = min(d.vocm, v)
        # vout_1/vout_2 are the INTER-STAGE nodes, one |V_SG| below the output.
        # `vmid=None` keeps the historical single-value hint byte-for-byte (the
        # reference deck is sha-pinned); a design that carries a measured vmid
        # gets a hint that is actually near its own solution.
        vm = vh if d.vmid is None else min(d.vmid, v)
        lines.append(f".nodeset v(xdut.vout_1)={vm} v(xdut.vout_2)={vm} "
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
             fstart: float = 0.1, fstop: float = 1e5, dec: int = C.AC_DEC,
             nstop: float = 1e3, vdd: float | None = None) -> str:
    """The cheap scorecard deck: op + ac + noise in one run, one rawfile.

    `dec = 10` matches the originating bench's sweep density so the phase
    certificate is scored on the same grid it was defined on.  Raise it only for
    a diagnostic (see `lab.metrics.ph_max_hires`).
    """
    return f""".title lpf {d.topology} -- ac + noise
{_libs(corner, d)}
{subckt(d)}
{_core(d, vdd=vdd)}
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
            probes: list[str] | None = None, vdd: float | None = None) -> str:
    """Operating point with per-device parameters printed -- the sizing tool.

    `probes` are ngspice device-parameter expressions; `lab.metrics.op_table`
    builds them from a `Design` so a sizing loop can read gm, gm/ID, Vdsat and
    Vds per role without guessing instance names.
    """
    pr = "\n".join(f"print {p}" for p in (probes or []))
    return f""".title lpf {d.topology} -- operating point
{_libs(corner, d)}
{subckt(d)}
{_core(d, vdd=vdd)}
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
             temp: float = C.TEMP_NOM, vdd: float | None = None) -> str:
    """Coherent strobed transient for THD.

    The transient is STROBED at an exact integer number of points per input
    cycle over an exact integer number of cycles, so the FFT grid lands on the
    fundamental and its harmonics with no leakage and no window needed.  The
    first `settle` cycles are simulated and discarded.

    `ampl` is the DIFFERENTIAL amplitude: 175 mVpp differential => ampl=87.5m.

    On `abstol = 1e-13` (was 1e-15).  A cell containing `sg13_lv_pmos` will not
    solve its transient operating point at 1e-15 -- dynamic gmin, true gmin and
    source stepping all fail and it reports "Transient op failed, timestep too
    small", which reads like stiffness and is really an unreachable current
    tolerance.  1e-13 A is still four decades below this filter's ~2 nA branch
    current, and it was adopted only after checking it does not move the ANSWER
    on the cells already measured at 1e-15:

        021-final   -42.220 -> -42.216 dB   (HD3 -42.56 both)
        reference   -48.375 -> -48.374 dB   (HD3 -48.38 both)

    i.e. 0.004 dB and 0.000 dB, with the even-harmonic numerical floor moving
    -140 -> -138 dB, still ~96 dB below the fundamental.  Every THD number
    measured before this change therefore remains comparable.
    """
    tper = 1.0 / fin
    tstop = (settle + cycles) * tper
    tstep = tper / ppc
    return f""".title lpf {d.topology} -- thd fin={fin:g} ampl={ampl:g}
{_libs(corner, d)}
{subckt(d)}
{_core(d, vdd=vdd)}
{_bias(d)}
{_stim_sine(fin, ampl, d.vicm)}
.temp {temp}
.options reltol=1e-5 abstol=1e-13 vntol=1e-9 chgtol=1e-16 method=gear maxord=2
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
{_libs(corner, d)}
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
