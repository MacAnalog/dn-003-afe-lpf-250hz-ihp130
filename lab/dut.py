"""The DUT: four super-source-follower (SSF) low-pass topologies, as netlist.

Everything the design does lives here.  A topology is a *function* from a
`Design` (device geometries + capacitor values) to a `lpf_core` subckt, so a
sizing sweep is a loop over `Design`s and never a text edit.

All four are FULLY DIFFERENTIAL 4th-order low-pass filters built from **two
cascaded SSF biquads** with no CMFB -- the common mode is defined by the
followers themselves.  Nets, per side:

    vinp -> [ biquad A ] -> vout_1 -> [ biquad B ] -> voutp
    net2  = biquad A's internal (high-impedance) node, P side
    net4  = biquad B's internal node, P side
    net3 / net1 / vout_2 / voutn = the N-side mirrors of net2 / net4 / vout_1 / voutp

An SSF biquad is: an input FOLLOWER (gate = input, source = the biquad output),
a SHUNT-FEEDBACK transconductor gm_f (gate = the internal node, drain = the
biquad output), one bias current per node, and two capacitors.  Its pole pair is

    w0^2 = gm_i * gm_f / (C1 * C2)          Q = sqrt(gm_i * C2 / (gm_f * C1))

with C1 across (internal node -> biquad output) and C2 the differential cap
across the biquad's two outputs.  Both biquads are complementary: biquad A has an
n-type input follower with a p-type gm_f, biquad B the other way round.

Technology mapping note (the one structural change vs. the originating design)
-----------------------------------------------------------------------------
The originating campaign ran in a technology with an isolated (triple-well)
NMOS, so EVERY device could have bulk tied to its own source and no device saw
body effect.  The open SG13G2 PDK has **no deep-n-well NMOS**: an n-channel
device's bulk is the shared p-substrate.  So:

    * p-channel devices keep bulk = source (each sits in its own n-well)  -- as drawn
    * n-channel devices must take bulk = GND                             -- forced

Only the n-type INPUT FOLLOWERS are affected (their sources swing); n-type
gm_f and bias devices already sit with their source at GND.  The consequence is
a body-effect term on biquad A's follower, which is absorbed by re-sizing rather
than by changing the topology.  See doc/journal/nmos-bulk-tie.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

# Device flavour map.  The originating design used thick-oxide (2.5 V-class)
# long-channel devices at a 1 V supply for their low flicker noise and their
# high output resistance at nano-amp bias.  The SG13G2 equivalent is the
# **hv (3.3 V, thick oxide)** pair, not the lv pair: an lv n-channel device at
# W = 17 um / L = 8 um already carries 2.5 nA at Vgs = 0, so it cannot be biased
# at 1 nA at all, and its gm/gds is ~70 against ~2900 for the hv device at the
# same geometry.  Measured in doc/pdk-notes.md.
NCH = "sg13_hv_nmos"
PCH = "sg13_hv_pmos"

# The lv **p**-channel device is a live option; the lv n-channel device is not.
#
# Why it matters: the all-p follower cascade shifts the common mode UP by one
# |V_SG| per stage, and |V_SG| is threshold-set.  Measured in this repo at the
# 021 cell's own geometry (W 15.6 um / L 10.4 um) and its own branch currents:
#
#     sg13_hv_pmos   0.4574 V @ 0.662 nA   0.5015 V @ 2.005 nA
#     sg13_lv_pmos   0.1682 V @ 0.662 nA   0.2028 V @ 2.005 nA
#
# i.e. 289 and 299 mV less shift, and the cascade shifts twice -- **588 mV of
# common-mode headroom**, which is the difference between an input CM stuck at
# 0.20 V and one at VDD/2.  Width cannot do this: |V_SG| falls only n*U_T per
# e-fold (~92 mV/decade), and the ~30x width needed converts ~47 pF of linear
# MIM capacitance into non-linear GATE capacitance, which cost 12 dB of THD when
# it was tried (experiments/021-publication-cell).
#
# The costs are real and must be re-measured per design, not assumed: gate-
# referred flicker is ~9 % worse (13.01 -> 14.20 uVrms over 0.5-200 Hz at equal
# geometry and current), and gm/gds is lower (~3690-5080 vs ~3710-8700 at these
# lengths), which is what pins H(0) = 1 against the 0.2 dB S3 box.
#
# `sg13_lv_nmos` stays closed: it carries 1.6-5.1 nA at Vgs = 0, i.e. more than
# this filter's whole branch current, so there is no gate voltage that biases
# it.  See doc/pdk-notes.md 2.2 and 2.4.
PCH_LV = "sg13_lv_pmos"
LV_MODELS = frozenset({PCH_LV})

# Which design ROLES are n-channel.  Every signal-path follower is p-type (see
# `build_reference`); the n-channel devices are the shunt-feedback
# transconductors and the internal-node bias sinks, whose sources sit at gnd and
# therefore see no body effect either way.
NROLES = frozenset({"bias_a_int", "gmf_a", "bias_b_int", "gmf_b"})


@dataclass
class Dev:
    """One transistor geometry.  `w`/`l` in metres, `ng` fingers, `m` multiplier."""

    w: float
    l: float
    ng: int = 1
    m: int = 1

    def card(self, inst: str, d: str, g: str, s: str, b: str, model: str) -> str:
        return (f"x{inst} {d} {g} {s} {b} {model} "
                f"w={self.w:.6g} l={self.l:.6g} ng={self.ng} m={self.m}")

    def area(self) -> float:
        return self.w * self.l * self.m


@dataclass
class Design:
    """A complete sizing point for one topology.

    Device keys are the ROLE, not an instance name, so the same `Design` reads
    the same way across topologies:

        in_a    biquad A input follower (n-type)
        gmf_a   biquad A shunt-feedback transconductor (p-type)
        bias_a_int   bias source feeding biquad A's internal node
        bias_a_out   bias sink at biquad A's output
        in_b    biquad B input follower (p-type)
        gmf_b   biquad B shunt-feedback transconductor (n-type)
        bias_b_int   bias sink at biquad B's internal node
        bias_b_out   bias source at biquad B's output
        bridge  the branch-stacking device (topologies a/b/c only)

    Capacitors:  c1_a (internal->out, per side), c2_a (differential across
    biquad A), c1_b, c2_b (same for biquad B).
    """

    topology: str
    devs: dict[str, Dev]
    c1_a: float
    c2_a: float
    c1_b: float
    c2_b: float
    # bias reference current (per the mirror unit); the testbench mirrors it.
    iref: float = 1e-9
    # Input / expected-output common mode.  These are a property of the
    # TOPOLOGY, not of the bench: the all-p reference shifts the common mode UP
    # by one |Vgs| per stage, while the branch-stacked family alternates n and p
    # followers so the two shifts partly cancel.  Carrying them on the Design
    # keeps a candidate from being scored at the reference's operating point.
    vicm: float = 0.25
    vocm: float = 1.25
    # Realise each `c2_*` as two grounded capacitors instead of one floating
    # one (see `_caps`).  Same differential response, 4x the drawn farads on
    # that element -- the control that turns `fvf-2nd`'s floating-cap technique
    # into a measured area saving instead of an asserted one.
    c2_grounded: bool = False
    # Roles built from the lv (thin-oxide) p-channel device instead of hv.  This
    # is the common-mode knob: an lv p-follower needs ~290 mV less |V_SG| than
    # the hv one at the same current, and the cascade shifts twice, so moving
    # the four p-type signal roles to lv is worth ~588 mV of input common mode
    # (measured -- see the PCH_LV note).  Empty = the all-hv design, which emits
    # exactly the netlist it always has.
    lv_roles: frozenset = frozenset()
    # dc hint for the INTER-STAGE node (vout_1/vout_2), which sits one |V_SG|
    # above vicm and is NOT at vocm.  `deck._core` hints all four output-side
    # nodes at `vocm` when this is None, which is what it has always done and
    # what the sha-pinned reference deck contains; on the reference the error is
    # ~0.5 V and the operating point absorbs it, but on a cell whose stage
    # voltages are spread further apart the same hint aims the solver at a node
    # voltage the circuit cannot reach and the THD deck fails as
    # "Transient op failed, timestep too small" -- a convergence failure that
    # reads like stiffness and is really a bad initial guess.  Set it from a
    # MEASURED op probe, never from arithmetic.
    vmid: float | None = None
    note: str = ""
    # How the six capacitors are REALISED.  "ideal" emits the plain `c` elements
    # every certified deck has always had (sha-pinned reference: this branch is
    # byte-identical).  "cmim" emits each as the PDK's MIM capacitor `cap_cmim`
    # (`cornerCAP.lib`): `m` identical square units of side <= CMIM_UNIT_MAX,
    # sized so the realised value (area * cap_carea + perimeter * CJSW) equals
    # the design farads -- see `cmim_geom`.  The design still stores farads, so
    # every fitter keeps working; the geometry is derived at emit time.
    cap_model: str = "ideal"
    # A VERBATIM `.subckt lpf_core <PORTS> ... .ends` text that REPLACES the
    # built netlist when set -- the layout lane's hook: a kpex-extracted
    # post-layout netlist, or a sensitivity-injection variant of the built one,
    # scored through the same frozen benches (`lab.metrics`, `lab.thd`,
    # `lab.corners`) as the schematic.  Never serialised into design.json; the
    # ledger records its sha so a post-layout row cannot masquerade as the
    # schematic's.  Ports must match `PORTS`; `subckt()` asserts the header.
    dut_override: str | None = None

    def model(self, role: str) -> str:
        """The compact model this role instantiates, honouring `lv_roles`."""
        return model_of(self.topology, role, self.lv_roles)

    def libs(self) -> tuple[str, ...]:
        """Corner libraries this design needs, in load order.

        A mixed-flavour design needs BOTH, because the lv and hv models live in
        separate corner files and a netlist that instantiates `sg13_lv_pmos`
        without `cornerMOSlv.lib` fails with `Unknown model type`, not with a
        wrong answer.
        """
        from . import config as C
        libs = (C.MOS_LIB_HV, C.MOS_LIB_LV) if self.lv_roles else (C.MOS_LIB_HV,)
        if self.cap_model == "cmim":
            libs = libs + (C.CAP_LIB,)
        return libs

    def cap(self, name: str) -> float:
        """The REALISED value of one design capacitor: the design farads for
        ideal caps, the geometry-quantised value for the PDK MIM."""
        c = getattr(self, name)
        return cmim_value(*cmim_geom(c)) if self.cap_model == "cmim" else c

    def total_cap(self) -> float:
        """Total DRAWN capacitance (both sides), in farads -- the area report."""
        if self.cap_model == "cmim":
            k2 = 4.0 if self.c2_grounded else 1.0
            return (2 * self.cap("c1_a") + k2 * self.cap("c2_a")
                    + 2 * self.cap("c1_b") + k2 * self.cap("c2_b"))
        k2 = 4.0 if self.c2_grounded else 1.0
        return 2 * self.c1_a + k2 * self.c2_a + 2 * self.c1_b + k2 * self.c2_b

    def total_gate_area(self) -> float:
        return sum(d.area() for d in self.devs.values()) * 2

    def with_(self, **kw) -> "Design":
        return replace(self, **kw)

    def scaled_caps(self, k: float) -> "Design":
        return replace(self, c1_a=self.c1_a * k, c2_a=self.c2_a * k,
                       c1_b=self.c1_b * k, c2_b=self.c2_b * k)


# --------------------------------------------------------------------------
# topologies
# --------------------------------------------------------------------------
# Every builder returns the body lines of `.subckt lpf_core vinp vinn voutp
# voutn vbn vbp vdd gnd`.  Net names follow the originating design so the
# small-signal derivations in doc/design-reference.md transfer verbatim.


# IHP SG13G2 MIM capacitor (cornerCAP.lib, section cap_typ): C = cap_carea*w*l +
# 2*CJSW*(w+l), cap_carea 1.5 fF/um^2, CJSW 40 aF/um (capacitors_mod.lib
# `.model cmim_core`).  A design capacitor is realised as `m` identical SQUARE
# units of side s <= CMIM_UNIT_MAX -- the shape a layout array takes -- with s
# solved so the realised value equals the design farads to the 10 nm grid.
CMIM_CAREA = 1.5e-15          # F / um^2
CMIM_CJSW = 40e-18            # F / um   (per unit of perimeter)
CMIM_UNIT_MAX = 50.0          # um, side of the largest unit we draw
CMIM_MODEL = "cap_cmim"


def cmim_value(s_um: float, m: int) -> float:
    """Realised farads of `m` square MIM units of side `s_um` (um)."""
    return m * (CMIM_CAREA * s_um * s_um + 2 * CMIM_CJSW * (2 * s_um))


def cmim_geom(c: float) -> tuple[float, int]:
    """(side_um, m) realising `c` farads: the fewest units of side <= CMIM_UNIT_MAX,
    side rounded to 0.01 um."""
    import math
    m = max(1, math.ceil(c / cmim_value(CMIM_UNIT_MAX, 1) - 1e-9))
    a, b, cc = CMIM_CAREA, 4 * CMIM_CJSW, -c / m
    s = (-b + math.sqrt(b * b - 4 * a * cc)) / (2 * a)
    return round(s, 2), m


def _cmim_line(name: str, n1: str, n2: str, c: float) -> str:
    s, m = cmim_geom(c)
    return f"x{name} {n1} {n2} {CMIM_MODEL} w={s:g}u l={s:g}u m={m}"


def _caps(d: Design) -> list[str]:
    """The six capacitors.  `c2_*` is ONE floating cap across the pair.

    That is `fvf-2nd`'s area technique, and it is worth 4x on this element, not
    2x: in a balanced pair a floating C between the two halves loads each half
    with 2C, so the grounded realisation of the same pole needs 2C per side --
    four drawn farads where the floating version draws one.  Set
    `Design.c2_grounded` to emit that realisation instead; the DIFFERENTIAL
    response is identical by construction and the drawn capacitance is not,
    which is what makes the saving measurable rather than asserted.

    The two are not identical in COMMON mode -- a floating cap loads the
    differential mode only, a grounded pair loads both -- so the grounded arm is
    an area control, not a drop-in alternative for a cell with no CMFB.
    """
    # Line ORDER is load-bearing: `decks/reference/` is sha-pinned by
    # `make lint`, so the default (floating) branch must emit exactly the lines
    # it always has, in the order it always has.  The grounded branch is the
    # only thing that may add or move anything.
    if d.cap_model == "cmim":
        if d.c2_grounded:
            raise ValueError("cap_model='cmim' with c2_grounded is not emitted")
        return [_cmim_line("c13", "net2", "vout_1", d.c1_a),
                _cmim_line("c17", "net3", "vout_2", d.c1_a),
                _cmim_line("c19", "vout_2", "vout_1", d.c2_a),
                _cmim_line("c1", "voutp", "net4", d.c1_b),
                _cmim_line("c10", "voutn", "net1", d.c1_b),
                _cmim_line("c12", "voutn", "voutp", d.c2_b)]
    if d.cap_model != "ideal":
        raise ValueError(f"unknown cap_model {d.cap_model!r}")
    c19 = ([f"c19 vout_1 0 {2 * d.c2_a:.6g}", f"c19b vout_2 0 {2 * d.c2_a:.6g}"]
           if d.c2_grounded else [f"c19 vout_2 vout_1 {d.c2_a:.6g}"])
    c12 = ([f"c12 voutn 0 {2 * d.c2_b:.6g}", f"c12b voutp 0 {2 * d.c2_b:.6g}"]
           if d.c2_grounded else [f"c12 voutn  voutp  {d.c2_b:.6g}"])
    return [
        f"c13 net2   vout_1 {d.c1_a:.6g}",
        f"c17 net3   vout_2 {d.c1_a:.6g}",
    ] + c19 + [
        f"c1  voutp  net4   {d.c1_b:.6g}",
        f"c10 voutn  net1   {d.c1_b:.6g}",
    ] + c12


def build_reference(d: Design) -> list[str]:
    """The expert baseline: two independent SSF biquads, EIGHT bias devices.

    BOTH biquads are p-input followers with an n-type shunt-feedback device.
    Every node carries its own dedicated bias current source -- which is exactly
    what makes the bias devices dominate the noise budget (they are 61.7 % of
    the noise power in the originating measurement).  This is the design every
    candidate has to beat.

    Why both stages are p-type (the port's one structural decision)
    ---------------------------------------------------------------
    The originating design ALTERNATED an n-input biquad with a p-input biquad,
    so the two |Vgs| level shifts cancelled and the output common mode returned
    to the input's.  That works only when both followers have bulk tied to their
    own source.  SG13G2 has no isolated NMOS, so an n-type follower necessarily
    has its bulk at the substrate, and a gate-driven follower with bulk at the
    rail has dc gain **exactly 1/n** in weak inversion (gmb = (n-1)*gm).

    Measured here, stage by stage, on the alternating structure:
        stage A (n-input, bulk at substrate) : -2.328 dB
        stage B (p-input, bulk at source)    : -0.003 dB
    i.e. the n-stage alone burns the whole S3 budget (|DC| <= 0.2 dB) an order
    of magnitude over, and no re-sizing recovers it -- 1/n is set by the process,
    not by geometry.  Making both stages p-type restores exact unity gain and,
    with it, the SELF-REFERENCED GAIN that the whole candidate family's mismatch
    yield rests on.  The cost is that the common mode now climbs one |Vgs| per
    stage instead of cancelling, which is absorbed by placing the input CM low
    (lab.config.VICM).  See doc/journal/all-p-followers.md.
    """
    D = d.devs
    M = d.model
    L = []
    # --- biquad A : p-input follower, n-type shunt feedback
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", M("in_a")),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", M("in_a"))]
    L += [D["bias_a_int"].card("m3", "net2", "vbn", "0", "0", M("bias_a_int")),
          D["bias_a_int"].card("m13", "net3", "vbn", "0", "0", M("bias_a_int"))]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", M("gmf_a")),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", M("gmf_a"))]
    L += [D["bias_a_out"].card("m9", "vout_1", "vbp", "vdd", "vdd", M("bias_a_out")),
          D["bias_a_out"].card("m10", "vout_2", "vbp", "vdd", "vdd", M("bias_a_out"))]
    # --- biquad B : p-input follower, n-type shunt feedback
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", M("in_b")),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", M("in_b"))]
    L += [D["bias_b_int"].card("m11", "net4", "vbn", "0", "0", M("bias_b_int")),
          D["bias_b_int"].card("m12", "net1", "vbn", "0", "0", M("bias_b_int"))]
    L += [D["gmf_b"].card("m6", "voutp", "net4", "0", "0", M("gmf_b")),
          D["gmf_b"].card("m7", "voutn", "net1", "0", "0", M("gmf_b"))]
    L += [D["bias_b_out"].card("m14", "voutp", "vbp", "vdd", "vdd", M("bias_b_out")),
          D["bias_b_out"].card("m15", "voutn", "vbp", "vdd", "vdd", M("bias_b_out"))]
    return L + _caps(d)


def build_a(d: Design) -> list[str]:
    """020A -- BRANCH-STACKED followers, shunt feedback NOT merged.

    Both input followers share ONE dc branch through a p-type BRIDGE, so both
    internal-node bias pairs are deleted.  The series ladder is

        vdd -> {gmf_b + bias_b_out} -> voutp -> in_b -> net4 -> bridge
             -> vout_1 -> in_a -> net2 -> bias_a_int -> gnd

    and the SAME ampere does the gm work of both followers.  What distinguishes
    this cell from 020B is that biquad B's output node keeps **two** p-devices:
    a dedicated bias source (gate on the bias rail) and a separate shunt-feedback
    transconductor (gate on the internal node).  020B merges them into one.
    So 020A is the branch-stacking mechanism ALONE, and the difference between
    the two cells isolates exactly what the merge buys.

    Realisation note.  The originating drawing alternated an n-type follower
    under a p-type one and tied the bridge's gate to the rail.  Neither survives
    here: an n-type follower has no source-tied bulk in this PDK and loses 1/n
    of dc gain, and a rail-tied bridge forces
    ``|Vsg|(gmf_b) + |Vsg|(bridge) = VDD``, which at 1.5 V drives both devices
    out of weak inversion and the bridge into triode (measured: 46 mV across it,
    gm/gds = 1).  Biasing the bridge's gate from the mirror instead frees that
    constraint AND makes the ladder current mirror-referenced rather than
    threshold-referenced -- which is the fix the originating campaign itself
    identified as the required next step for this family.
    """
    D = d.devs
    M = d.model
    L = []
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", M("in_a")),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", M("in_a"))]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", M("gmf_a")),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", M("gmf_a"))]
    L += [D["bias_a_int"].card("m9", "net2", "vbn", "0", "0", M("bias_a_int")),
          D["bias_a_int"].card("m10", "net3", "vbn", "0", "0", M("bias_a_int"))]
    L += [D["bridge"].card("mst", "vout_1", "vbn", "net4", "net4", M("bridge")),
          D["bridge"].card("mstn", "vout_2", "vbn", "net1", "net1", M("bridge"))]
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", M("in_b")),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", M("in_b"))]
    # separate shunt feedback ...
    L += [D["gmf_b"].card("m6", "voutp", "net4", "vdd", "vdd", M("gmf_b")),
          D["gmf_b"].card("m7", "voutn", "net1", "vdd", "vdd", M("gmf_b"))]
    # ... and a dedicated bias source (this pair is what 020B's merge deletes)
    L += [D["bias_b_out"].card("m14", "voutp", "vbp", "vdd", "vdd", M("bias_b_out")),
          D["bias_b_out"].card("m15", "voutn", "vbp", "vdd", "vdd", M("bias_b_out"))]
    return L + _caps(d)


def build_b(d: Design) -> list[str]:
    """020B -- the gm_f MERGE (the new topology; the round's headline result).

    Structural delta vs 020A: biquad B's output bias source has its GATE
    re-wired from the vbp rail to biquad B's own internal node (net4/net1).
    The same physical device, carrying the same current, is now simultaneously
    the branch's bias source AND the SSF loop's shunt-feedback transconductor --
    so the separate n-type gm_f pair is DELETED.

    That removes the last large pure-bias pair from the noise ledger: what was a
    current source injecting its full shot and flicker noise into the output
    node becomes an in-loop signal device whose noise is shaped by the same
    feedback that sets the pole.

    The re-wire also changes what sets the ladder current.  net4 is now pinned
    by two exponentials at once -- V(net4) = V_SG(bridge) (gate at gnd) and
    V(net4) = VDD - V_SG(gmf_b) -- so the branch current is the unique solution
    of  V_SG(gmf_b)(I) + V_SG(bridge)(I) = VDD.  Sizing gmf_b therefore moves the
    ENTIRE ladder exponentially, not proportionally.

    Realisation in this PDK (differs from the originating drawing)
    --------------------------------------------------------------
    The originating cell stacked an n-type follower under a p-type one and
    bridged the two INTERNAL nodes (net4 -> net2).  Here every signal-path
    follower must be p-type (no isolated NMOS => an n-type follower loses 1/n of
    dc gain; measured -3.11 dB on the faithful redraw, against an S3 box of
    0.2 dB).  With both followers p-type the two internal nodes sit at the SAME
    low level, so there is no voltage across a bridge placed between them.

    The stack therefore moves up one node: the bridge runs from biquad B's
    internal node into biquad A's OUTPUT, and the dc ladder becomes

        vdd -> gmf_b -> voutp -> in_b -> net4 -> bridge -> vout_1
             -> in_a -> net2 -> bias_a_int -> gnd

    which descends monotonically and leaves exactly TWO bias devices per side.
    This works only because the merge puts a p-type device at the top of the
    ladder: with a separate n-type gm_f (the un-merged 020A arrangement) net4
    would have to be both a gm_f gate voltage (~0.4 V) and a bridge source
    (~0.95 V) at once.  In a PDK without an isolated NMOS, branch stacking and
    an exact 0 dB passband are compatible ONLY in the merged form.
    """
    D = d.devs
    M = d.model
    L = []
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", M("in_a")),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", M("in_a"))]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", M("gmf_a")),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", M("gmf_a"))]
    L += [D["bias_a_int"].card("m9", "net2", "vbn", "0", "0", M("bias_a_int")),
          D["bias_a_int"].card("m10", "net3", "vbn", "0", "0", M("bias_a_int"))]
    L += [D["bridge"].card("mst", "vout_1", "vbn", "net4", "net4", M("bridge")),
          D["bridge"].card("mstn", "vout_2", "vbn", "net1", "net1", M("bridge"))]
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", M("in_b")),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", M("in_b"))]
    # THE MERGE: gate = the internal node, not the bias rail.
    L += [D["gmf_b"].card("m14", "voutp", "net4", "vdd", "vdd", M("gmf_b")),
          D["gmf_b"].card("m15", "voutn", "net1", "vdd", "vdd", M("gmf_b"))]
    return L + _caps(d)


def build_c(d: Design) -> list[str]:
    """020C -- the merge re-allocated under a total-capacitance ruling.

    Identical topology to 020B; it is its own cell because the sizing answers a
    different question -- spend the noise surplus on AREA and POWER instead of
    on noise.  A smaller gm_f puts the same pole on less capacitance, trading
    part of 020B's noise margin for a smaller die and a lower ladder current.
    """
    return build_b(d)


def build_d(d: Design) -> list[str]:
    """023D -- the merge (020B) with a REPLICA-BIASED ladder.

    Same signal path as `build_b`, device for device: the only re-wire is that
    the two bridge gates leave the n-mirror rail `vbn` and take a new rail
    `vbr`, generated by ONE shared replica branch (three devices, both halves):

        vdd -> xr1 (p, DIODE, replica of gmf_b) -> rep_x
            -> xr2 (p, DIODE, replica of bridge) -> vbr
            -> xr3 (n, gate = vbn, the mirror sink)          -> gnd

    Why.  In 020B the ladder current is the solution of

        |V_SG|(gmf_b) + |V_SG|(bridge) = VDD - vbn

    i.e. two p-thresholds against the supply minus an n-diode -- THRESHOLD-
    referenced.  Measured on the sign-off cells: fc 13.6 -> 524 Hz across
    ss/ff at nominal V/T, dI/I = dVDD/(2 n U_T) on the rail, and the whole
    1/22 PVT count of the family (signoff/COMPARISON.md).  The replica pins the
    same sum from the other side:  vbr = VDD - |V_SG|(xr1) - |V_SG|(xr2) at the
    sink's mirrored current I_t, so with xr1 == gmf_b and xr2 == bridge in
    geometry and flavour the ladder solves to I_L = I_t -- MIRROR-referenced,
    like every current in the un-stacked reference.  VDD, temperature and
    process now enter only through Vds/gds terms and replica-to-ladder
    mismatch, not through an exponential.

    Costs, all measured in experiments/023-replica-bias: one extra branch of
    I_t (~1-3 nA, ~2-4 nW at 1.5 V, INSIDE the core so S6 sees it), three
    devices, and a new mismatch term (replica vs ladder) that the MC has to
    price.  Nothing in the signal path moves, so the S8 provenance of 020B
    (branch stacking + the gm_f merge + floating caps) is untouched.

    Roles:  rep_gmfb (p, must match gmf_b's flavour: put it in `lv_roles`
    whenever gmf_b is), rep_bridge (p, matches bridge), rep_sink (n, a ratio
    mirror off vbn -- same L as bias_a_int, W sets I_t).
    """
    D = d.devs
    M = d.model
    L = []
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", M("in_a")),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", M("in_a"))]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", M("gmf_a")),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", M("gmf_a"))]
    L += [D["bias_a_int"].card("m9", "net2", "vbn", "0", "0", M("bias_a_int")),
          D["bias_a_int"].card("m10", "net3", "vbn", "0", "0", M("bias_a_int"))]
    # THE RE-WIRE: bridge gate = the replica rail, not the n-mirror rail.
    L += [D["bridge"].card("mst", "vout_1", "vbr", "net4", "net4", M("bridge")),
          D["bridge"].card("mstn", "vout_2", "vbr", "net1", "net1", M("bridge"))]
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", M("in_b")),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", M("in_b"))]
    L += [D["gmf_b"].card("m14", "voutp", "net4", "vdd", "vdd", M("gmf_b")),
          D["gmf_b"].card("m15", "voutn", "net1", "vdd", "vdd", M("gmf_b"))]
    # THE REPLICA: one branch, shared by both halves.
    L += [D["rep_gmfb"].card("r1", "rep_x", "rep_x", "vdd", "vdd", M("rep_gmfb")),
          D["rep_bridge"].card("r2", "vbr", "vbr", "rep_x", "rep_x", M("rep_bridge")),
          D["rep_sink"].card("r3", "vbr", "vbn", "0", "0", M("rep_sink"))]
    return L + _caps(d)


def replica_of(d: Design, i_t_units: float, *, model_check: bool = True) -> Design:
    """A `b`/`c` sizing re-issued as topology `d` with a matched replica.

    `rep_gmfb`/`rep_bridge` copy gmf_b/bridge (geometry AND flavour), so the
    ladder current equals the replica's; `rep_sink` is the mirror unit
    (bias_a_int's geometry) at `i_t_units` = I_t / iref -- an integer becomes
    the multiplier `m` (a layout-friendly unit-copy mirror, like every current
    in the reference), a non-integer scales W.  Nothing else moves.
    """
    if d.topology not in ("b", "c"):
        raise ValueError(f"replica_of expects a merged (b/c) sizing, got {d.topology!r}")
    devs = dict(d.devs)
    devs["rep_gmfb"] = replace(d.devs["gmf_b"])
    devs["rep_bridge"] = replace(d.devs["bridge"])
    u = d.devs["bias_a_int"]
    if float(i_t_units).is_integer():
        devs["rep_sink"] = Dev(w=u.w, l=u.l, ng=u.ng, m=int(i_t_units) * u.m)
    else:
        devs["rep_sink"] = Dev(w=u.w * i_t_units, l=u.l, ng=u.ng, m=1)
    lv = set(d.lv_roles)
    if "gmf_b" in lv:
        lv.add("rep_gmfb")
    if "bridge" in lv:
        lv.add("rep_bridge")
    return replace(d, topology="d", devs=devs, lv_roles=frozenset(lv))


# Which roles are n-channel, per topology.  The reference is all-p in the signal
# path (see build_reference); the 020 family must alternate to close its dc
# ladder, so its biquad A follower is n-type.
NROLES_BY_TOPOLOGY = {
    "reference": NROLES,
    "a": frozenset({"gmf_a", "bias_a_int"}),
    "b": frozenset({"gmf_a", "bias_a_int"}),
    "c": frozenset({"gmf_a", "bias_a_int"}),
    "d": frozenset({"gmf_a", "bias_a_int", "rep_sink"}),
}


BUILDERS = {
    "reference": build_reference,
    "a": build_a,
    "b": build_b,
    "c": build_c,
    "d": build_d,
}

PORTS = "vinp vinn voutp voutn vbn vbp vdd"


def subckt(d: Design, name: str = "lpf_core") -> str:
    """The DUT as a standalone `.subckt` block (or `d.dut_override` verbatim)."""
    if d.dut_override is not None:
        import re
        head = re.search(rf"(?im)^\.subckt\s+{name}\s+(.*)$", d.dut_override)
        if not head or head.group(1).split() != PORTS.split():
            raise ValueError(f"dut_override must define `.subckt {name} {PORTS}` verbatim")
        return d.dut_override.rstrip("\n") + "\n"
    body = BUILDERS[d.topology](d)
    head = f".subckt {name} {PORTS}"
    return "\n".join([head, *(f"  {ln}" for ln in body), f".ends {name}", ""])


def device_table(d: Design) -> str:
    """Human-readable build sheet -- what goes in a scorecard."""
    rows = [f"| {'role':12s} | {'type':13s} | W (um) | L (um) | m | area (um2) |",
            "|---|---|---|---|---|---|"]
    ntype = NROLES_BY_TOPOLOGY.get(d.topology, NROLES)
    for role, dev in d.devs.items():
        model = NCH if role in ntype else PCH
        rows.append(f"| {role:12s} | {model:13s} | {dev.w*1e6:.3f} | {dev.l*1e6:.3f} | "
                    f"{dev.m} | {dev.area()*1e12:.1f} |")
    rows.append(f"\nTotal drawn capacitance: **{d.total_cap()*1e12:.2f} pF** "
                f"(c1_a {d.c1_a*1e12:.3f} / c2_a {d.c2_a*1e12:.3f} / "
                f"c1_b {d.c1_b*1e12:.3f} / c2_b {d.c2_b*1e12:.3f} pF)")
    return "\n".join(rows)


# Role -> the instance names that implement it, per topology (P side, N side).
# Kept next to the builders so an operating-point probe can address a device by
# its DESIGN ROLE instead of by a netlist name nobody remembers.
INSTANCES = {
    "reference": {
        "in_a": ("m2", "m5"), "bias_a_int": ("m3", "m13"),
        "gmf_a": ("m4", "m8"), "bias_a_out": ("m9", "m10"),
        "in_b": ("m0", "m1"), "bias_b_int": ("m11", "m12"),
        "gmf_b": ("m6", "m7"), "bias_b_out": ("m14", "m15"),
    },
    "a": {
        "in_a": ("m2", "m5"), "gmf_a": ("m4", "m8"),
        "bias_a_int": ("m9", "m10"), "bridge": ("mst", "mstn"),
        "in_b": ("m0", "m1"), "gmf_b": ("m6", "m7"),
        "bias_b_out": ("m14", "m15"),
    },
    "b": {
        "in_a": ("m2", "m5"), "gmf_a": ("m4", "m8"),
        "bias_a_int": ("m9", "m10"), "bridge": ("mst", "mstn"),
        "in_b": ("m0", "m1"), "gmf_b": ("m14", "m15"),
    },
}
INSTANCES["c"] = INSTANCES["b"]
# The replica devices are single (shared) instances; the probe reads insts[0].
INSTANCES["d"] = {**INSTANCES["b"], "rep_gmfb": ("r1", "r1"),
                  "rep_bridge": ("r2", "r2"), "rep_sink": ("r3", "r3")}

# Internal nets worth reporting in an operating-point table, in ladder order.
LADDER_NETS = ("voutp", "net4", "vout_1", "net2")


def model_of(topology: str, role: str, lv_roles: frozenset = frozenset()) -> str:
    """The compact model a role instantiates.

    `lv_roles` names roles built from the lv (thin-oxide) flavour.  Only
    p-channel roles may appear in it -- `sg13_lv_nmos` cannot be biased at this
    filter's branch current at all (see the PCH_LV note above), so an n-role
    request is a design error and is refused rather than silently ignored.
    """
    n = role in NROLES_BY_TOPOLOGY.get(topology, NROLES)
    if role in lv_roles:
        if n:
            raise ValueError(
                f"role {role!r} is n-channel in topology {topology!r}; there is "
                "no usable lv n-channel device in this PDK (it carries "
                "1.6-5.1 nA at Vgs = 0, more than the whole branch current)")
        return PCH_LV
    return NCH if n else PCH
