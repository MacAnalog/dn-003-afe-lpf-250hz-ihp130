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
    note: str = ""

    def total_cap(self) -> float:
        """Total DRAWN capacitance (both sides), in farads -- the area report."""
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
    L = []
    # --- biquad A : p-input follower, n-type shunt feedback
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", PCH),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", PCH)]
    L += [D["bias_a_int"].card("m3", "net2", "vbn", "0", "0", NCH),
          D["bias_a_int"].card("m13", "net3", "vbn", "0", "0", NCH)]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", NCH),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", NCH)]
    L += [D["bias_a_out"].card("m9", "vout_1", "vbp", "vdd", "vdd", PCH),
          D["bias_a_out"].card("m10", "vout_2", "vbp", "vdd", "vdd", PCH)]
    # --- biquad B : p-input follower, n-type shunt feedback
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", PCH),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", PCH)]
    L += [D["bias_b_int"].card("m11", "net4", "vbn", "0", "0", NCH),
          D["bias_b_int"].card("m12", "net1", "vbn", "0", "0", NCH)]
    L += [D["gmf_b"].card("m6", "voutp", "net4", "0", "0", NCH),
          D["gmf_b"].card("m7", "voutn", "net1", "0", "0", NCH)]
    L += [D["bias_b_out"].card("m14", "voutp", "vbp", "vdd", "vdd", PCH),
          D["bias_b_out"].card("m15", "voutn", "vbp", "vdd", "vdd", PCH)]
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
    L = []
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", PCH),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", PCH)]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", NCH),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", NCH)]
    L += [D["bias_a_int"].card("m9", "net2", "vbn", "0", "0", NCH),
          D["bias_a_int"].card("m10", "net3", "vbn", "0", "0", NCH)]
    L += [D["bridge"].card("mst", "vout_1", "vbn", "net4", "net4", PCH),
          D["bridge"].card("mstn", "vout_2", "vbn", "net1", "net1", PCH)]
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", PCH),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", PCH)]
    # separate shunt feedback ...
    L += [D["gmf_b"].card("m6", "voutp", "net4", "vdd", "vdd", PCH),
          D["gmf_b"].card("m7", "voutn", "net1", "vdd", "vdd", PCH)]
    # ... and a dedicated bias source (this pair is what 020B's merge deletes)
    L += [D["bias_b_out"].card("m14", "voutp", "vbp", "vdd", "vdd", PCH),
          D["bias_b_out"].card("m15", "voutn", "vbp", "vdd", "vdd", PCH)]
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
    L = []
    L += [D["in_a"].card("m2", "net2", "vinp", "vout_1", "vout_1", PCH),
          D["in_a"].card("m5", "net3", "vinn", "vout_2", "vout_2", PCH)]
    L += [D["gmf_a"].card("m4", "vout_1", "net2", "0", "0", NCH),
          D["gmf_a"].card("m8", "vout_2", "net3", "0", "0", NCH)]
    L += [D["bias_a_int"].card("m9", "net2", "vbn", "0", "0", NCH),
          D["bias_a_int"].card("m10", "net3", "vbn", "0", "0", NCH)]
    L += [D["bridge"].card("mst", "vout_1", "vbn", "net4", "net4", PCH),
          D["bridge"].card("mstn", "vout_2", "vbn", "net1", "net1", PCH)]
    L += [D["in_b"].card("m0", "net4", "vout_1", "voutp", "voutp", PCH),
          D["in_b"].card("m1", "net1", "vout_2", "voutn", "voutn", PCH)]
    # THE MERGE: gate = the internal node, not the bias rail.
    L += [D["gmf_b"].card("m14", "voutp", "net4", "vdd", "vdd", PCH),
          D["gmf_b"].card("m15", "voutn", "net1", "vdd", "vdd", PCH)]
    return L + _caps(d)


def build_c(d: Design) -> list[str]:
    """020C -- the merge re-allocated under a total-capacitance ruling.

    Identical topology to 020B; it is its own cell because the sizing answers a
    different question -- spend the noise surplus on AREA and POWER instead of
    on noise.  A smaller gm_f puts the same pole on less capacitance, trading
    part of 020B's noise margin for a smaller die and a lower ladder current.
    """
    return build_b(d)


# Which roles are n-channel, per topology.  The reference is all-p in the signal
# path (see build_reference); the 020 family must alternate to close its dc
# ladder, so its biquad A follower is n-type.
NROLES_BY_TOPOLOGY = {
    "reference": NROLES,
    "a": frozenset({"gmf_a", "bias_a_int"}),
    "b": frozenset({"gmf_a", "bias_a_int"}),
    "c": frozenset({"gmf_a", "bias_a_int"}),
}


BUILDERS = {
    "reference": build_reference,
    "a": build_a,
    "b": build_b,
    "c": build_c,
}

PORTS = "vinp vinn voutp voutn vbn vbp vdd"


def subckt(d: Design, name: str = "lpf_core") -> str:
    """The DUT as a standalone `.subckt` block."""
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

# Internal nets worth reporting in an operating-point table, in ladder order.
LADDER_NETS = ("voutp", "net4", "vout_1", "net2")


def model_of(topology: str, role: str) -> str:
    return NCH if role in NROLES_BY_TOPOLOGY.get(topology, NROLES) else PCH
