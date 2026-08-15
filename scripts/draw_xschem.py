"""Draw the *human-readable* schematic of record for a certified LPF cell.

`gen_xschem.py` emits a machine grid: devices on a lattice, every connection a
`lab_pin` sitting on a pin, not one wire.  It is correct and unreviewable.  This
emitter carries forward the **originating campaign's hand-placed drawing** of
this topology -- its coordinate frame, its two-stage left/right arrangement, its
routed wires, its rails and its port placement -- and re-homes it on the open
PDK.  Nothing about the picture is invented where the prior drawing had an
answer.

WHAT THE PORT HAD TO CHANGE, AND WHY (this is not a symbol swap).  The prior
drawing's biquad A is the OPPOSITE POLARITY to this cell's: there the input
follower is n-type, the shunt gm_f is a p-device pulling up from the supply and
the bias sink hangs on vout_1, with the bridge landing on net2.  Here biquad A
is p-type: the follower descends vout_1 -> net2, the gm_f is an n-device sinking
vout_1 to ground, the bias sink hangs on net2, and the bridge lands on vout_1
with its gate on vbn rather than on ground.  Six of the twelve devices therefore
have different terminals, and biquad A's two internal rails swap places
vertically (vout_1 above net2, because a p-follower's source pin is its top
one).  Everything else -- both halves of biquad B, the differential caps, the
rails, the ports, the feedback lanes -- ports coordinate-for-coordinate.

The symbol swap itself is free: `devices/{n,p}mos4.sym` and the IHP
`sg13g2_pr/sg13_*_{n,p}mos.sym` carry IDENTICAL pin geometry -- p: D (20,+30)
G (-20,0) S (20,-30) B (20,0); n: D and S swapped -- so every wire endpoint of
the prior drawing stays valid.  The IHP devices are `.subckt` wrappers, so each
instance additionally carries `spiceprefix=X`.

Three things this emitter does NOT do, on purpose:

*   it never types a size.  Every w/l/ng/m/value, every net and every model
    comes from the as-built netlist in `signoff/asbuilt/`, and each placement is
    ASSERTED against that netlist, so a cell whose connectivity differs from the
    one this layout was drawn for fails loudly instead of drawing a lie.
*   it never rewrites the testbench.  The bench fragment and the `.control`
    block are lifted VERBATIM out of the certified `_tb_*.sp` decks, so the
    drawing's bench cannot drift from the bench that certified the numbers.
*   it never re-orders the devices.  The `C {...}` lines are emitted in the
    order the certified netlist lists them, because xschem netlists instances in
    FILE order -- and element order is not cosmetic here:

    ORDER IS LOAD-BEARING.  ngspice's default dc tolerances (reltol 1e-3,
    vntol 1e-6 V) are loose next to a 2 nA subthreshold ladder.  Permuting the
    device lines inside the subckt changes the Newton trajectory and lands the
    solver on a different point of the same basin: measured on this cell, up to
    6.3 uV on net2/net3 -- the gate of the biquad-A gm_f -- which at gm/ID ~ 25 /V
    is ~1.6e-4 of that branch's current.  That moves biquad A's pole and shows up
    as fc -6.7 mHz, ripple_db -6.3e-4 dB, |H|@1kHz -1.8e-3 dB while dc, phase,
    noise and power all still agree to ~1e-5.  Emitting in netlist order removes
    it EXACTLY (every scorecard field agrees to the last printed digit); it is a
    drawing bug, not a tolerance to widen.  File order is independent of the
    drawn coordinates, so readability costs nothing.

    uv run python scripts/draw_xschem.py build <asbuilt.sp> <outdir> --name CELL
    uv run python scripts/draw_xschem.py check <asbuilt.sp> <outdir> --name CELL
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The testbench sheets DRAW their bench -- sources, balun, supply probe and
# bias mirror as placed, wired components -- reusing the record cell's proven
# schematic IR (wire splitting, pin transforms, short/overlap checks) so both
# drawers keep one wiring idiom.  Only non-component lines (.lib/.nodeset/
# .options/.temp and the .control block) remain text on the sheet.
from draw_lpf_core_022 import Sch, parse_deck, pin  # noqa: E402

HDR = "v {xschem version=3.4.4 file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n"
PR = "sg13g2_pr"
PORTS = ("vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd")

# ------------------------------------------------------------- the netlist --


@dataclass
class Mos:
    name: str
    nets: tuple            # d g s b
    model: str
    params: dict


@dataclass
class Cap:
    name: str
    nets: tuple            # p m
    value: str             # farads (ideal) or "" for a PDK MIM instance
    model: str = ""        # "" (ideal `c` element) or e.g. cap_cmim (an `xc` instance)
    params: dict = None    # w/l/m of the MIM instance


def read_asbuilt(path: Path) -> tuple[list, list]:
    """Instances of the `.subckt lpf_core` body, in FILE ORDER."""
    mos, caps, inside = [], [], False
    for ln in path.read_text().splitlines():
        s = ln.strip()
        if s.lower().startswith(".subckt"):
            inside = True
            continue
        if s.lower().startswith(".ends"):
            inside = False
            continue
        if not inside or not s or s.startswith("*"):
            continue
        t = s.split()
        if t[0].lower().startswith("xc"):          # a PDK MIM capacitor instance
            caps.append(Cap(t[0].lower(), tuple(n.lower() for n in t[1:3]), "",
                            t[3], dict(kv.split("=", 1) for kv in t[4:])))
        elif t[0].lower().startswith("x"):
            mos.append(Mos(t[0].lower(), tuple(n.lower() for n in t[1:5]),
                           t[5], dict(kv.split("=", 1) for kv in t[6:])))
        elif t[0].lower().startswith("c"):
            caps.append(Cap(t[0].lower(), tuple(n.lower() for n in t[1:3]), t[3]))
    if not mos or not caps:
        raise SystemExit(f"{path}: no subckt body found")
    return mos, caps


# ---------------------------------------------------------------- geometry --
# All coordinates below are the originating drawing's own, kept verbatim except
# where biquad A's polarity forced a re-route (marked PORTED-CHANGE).  y grows
# DOWNWARD: the vdd rail is at -560 and ground at +60.

MIR_A, MIR_B = 620, 2460          # mirror axes of the two stages
Y_VDD, Y_GND = -560, 60

# device -> (x, y, expected nets d g s b) on the P half
DEV_A = {"xm2":  (40, -320, ("net2", "vinp", "vout_1", "vout_1")),
         "xm9":  (40, -110, ("net2", "vbn", "0", "0")),
         "xm4":  (180, -110, ("vout_1", "net2", "0", "0"))}     # PORTED-CHANGE
DEV_B = {"xm14": (960, -450, ("voutp", "net4", "vdd", "vdd")),
         "xm0":  (960, -260, ("net4", "vout_1", "voutp", "voutp")),
         "xmst": (960, -70, ("vout_1", "vbn", "net4", "net4"))}
# rot 2 puts pin p at the BOTTOM, so `c13 net2 vout_1` keeps its netlist pin
# order now that biquad A's two rails have swapped places vertically.
# x/y are nudged off the prior drawing's only where the IHP symbols' longer
# `@model` / `@value` strings would otherwise print on top of each other -- the
# devices' own value text is the thing a reviewer reads.
CAP_A = {"c13": (110, -230, 2, ("net2", "vout_1"))}
CAP_B = {"c1":  (1050, -190, 0, ("voutp", "net4"))}
CAP_D = {"c19": (310, -380, 1, ("vout_2", "vout_1")),
         "c12": (1230, -320, 1, ("voutn", "voutp"))}
# Topology `d` (experiments/023): the two bridge gates leave `vbn` for a rail
# `vbr` generated by ONE shared replica branch -- xr1 (p, diode, = gmf_b),
# xr2 (p, diode, = bridge), xr3 (n, gate vbn, mirror sink).  It is drawn as a
# single column to the RIGHT of biquad B, hanging off the same vdd rail and
# landing on its own ground symbol, so the signal-path picture is untouched:
# the only visible change inside the two stages is the bridge-gate label.
# Devices are un-mirrored (rot 0, flip 0): p: D (20,+30) G (-20,0) S (20,-30)
# B (20,0); n: D/S swapped.
X_REP = 1800
DEV_R = {"xr1": (X_REP, -450, ("rep_x", "rep_x", "vdd", "vdd")),
         "xr2": (X_REP, -260, ("vbr", "vbr", "rep_x", "rep_x")),
         "xr3": (X_REP, -70, ("vbr", "vbn", "0", "0"))}
WIRES_R = [
    (1820, -560, 1820, -480), (1820, -480, 1820, -450),      # xr1 source / bulk
    (1820, -420, 1820, -320), (1780, -450, 1760, -450),      # xr1 drain / gate
    (1760, -450, 1760, -320), (1760, -320, 1820, -320),      # xr1 diode tie
    (1820, -290, 1820, -320), (1820, -260, 1820, -290),      # xr2 source / bulk
    (1820, -230, 1820, -140), (1780, -260, 1760, -260),      # xr2 drain / gate
    (1760, -260, 1760, -140), (1760, -140, 1820, -140),      # xr2 diode tie
    (1820, -100, 1820, -140), (1820, -70, 1820, -40),        # xr3 drain / bulk
    (1820, -40, 1820, 60), (1780, -70, 1760, -70),           # xr3 source / gate
    (1820, -320, 1860, -320), (1820, -140, 1860, -140),      # rep_x / vbr taps
    (1820, 60, 1820, 110),                                   # to ground symbol
]
LAB_R = [(1860, -320, "rep_x"), (1860, -140, "vbr"), (1760, -70, "vbn")]

TWIN = {"xm2": "xm5", "xm9": "xm10", "xm4": "xm8", "xm14": "xm15",
        "xm0": "xm1", "xmst": "xmstn", "c13": "c17", "c1": "c10"}
NMAP = {"vout_1": "vout_2", "net2": "net3", "net4": "net1", "voutp": "voutn",
        "vinp": "vinn", "vdd": "vdd", "vbn": "vbn", "0": "0"}

# Wire segments of the P half of each stage.  Split at EVERY junction: xschem
# joins wires whose ENDPOINTS touch, so a rail written as one long segment with
# taps hanging off its middle is a pile of open circuits.
WIRES_A = [
    (60, -350, 60, -380), (60, -350, 60, -320),          # xm2 source up / bulk
    (60, -290, 60, -180), (-20, -320, 20, -320),         # xm2 drain down / gate
    (60, -140, 60, -180), (60, -110, 60, -80),           # xm9 drain / bulk
    (60, -80, 60, 60), (0, -110, 20, -110),              # xm9 source / gate
    (200, -140, 200, -380), (200, -110, 200, -80),       # xm4 drain / bulk   |
    (200, -80, 200, 60), (160, -110, 160, -180),         # xm4 source / gate  | PORTED
    (110, -260, 110, -380), (110, -200, 110, -180),      # c13                | CHANGE
    (60, -380, 100, -380), (100, -380, 110, -380),       # vout_1 rail (was net2)
    (110, -380, 200, -380), (200, -380, 280, -380),
    (60, -180, 100, -180), (100, -180, 110, -180),       # net2 rail (was vout_1)
    (110, -180, 160, -180),
    (60, 60, 200, 60), (200, 60, 310, 60),               # ground rail
]
WIRES_B = [
    (980, -560, 980, -480), (980, -480, 980, -450),      # xm14 source / bulk
    (980, -420, 980, -320), (920, -450, 940, -450),      # xm14 drain / gate
    (820, -450, 920, -450), (820, -450, 820, -140),      # the SSF feedback lane
    (820, -140, 980, -140),
    (980, -290, 980, -320), (980, -260, 980, -290),      # xm0 source / bulk
    (980, -230, 980, -140), (920, -260, 940, -260),      # xm0 drain / gate
    (980, -100, 980, -140), (980, -70, 980, -100),       # xmst source / bulk
    (980, -40, 980, 10), (920, -70, 940, -70),           # xmst drain / gate
    (1050, -220, 1050, -320), (1050, -160, 1050, -140),  # c1
    (980, -320, 1050, -320), (1050, -320, 1090, -320),   # voutp rail
    (1090, -320, 1160, -320), (1160, -320, 1200, -320),
    (1090, -360, 1090, -320), (1090, -360, 1130, -360),  # voutp pin riser
    (980, -140, 1020, -140), (1020, -140, 1050, -140),   # net4 rail
]
# lab_pin net names, P half of each stage
LAB_A = [(100, -380, "vout_1"), (100, -180, "net2"), (0, -110, "vbn")]
LAB_B = [(920, -260, "vout_1"), (980, 10, "vout_1"), (920, -70, "vbn"),
         (1020, -140, "net4")]
PIN_A = [("ipin", -20, -320, "vinp")]
PIN_B = [("opin", 1130, -360, "voutp")]


def core_sch(mos: list, caps: list, cell: str) -> str:
    out = [HDR]
    W, C, T = [], [], []
    names = {m.name for m in mos}
    replica = bool(names & set(DEV_R))            # topology d
    if replica and not set(DEV_R) <= names:
        raise SystemExit(f"partial replica branch in netlist: {sorted(names & set(DEV_R))}")
    gate_rail = "vbr" if replica else "vbn"       # what the bridge gates sit on
    NMAP["vbr"] = "vbr"

    def wire(x1, y1, x2, y2, lab=""):
        W.append(f"N {x1} {y1} {x2} {y2} {{{'lab=' + lab if lab else ''}}}")

    def sym(path, x, y, rot, flip, attrs):
        C.append(f"C {{{path}}} {x} {y} {rot} {flip} {{{attrs}}}")

    def text(txt, x, y, size, flip=0):
        T.append(f"T {{{txt}}} {x} {y} 0 {flip} {size} {size} {{}}")

    def mirror(seg, axis):
        return [(axis - x1, y1, axis - x2, y2) for x1, y1, x2, y2 in seg]

    # ---- wires: each stage's P half plus its mirror image
    for seg in (WIRES_A, mirror(WIRES_A, MIR_A), WIRES_B, mirror(WIRES_B, MIR_B)):
        for x1, y1, x2, y2 in seg:
            wire(x1, y1, x2, y2)
    if replica:
        for x1, y1, x2, y2 in WIRES_R:
            wire(x1, y1, x2, y2)
        wire(1660, Y_VDD, 1820, Y_VDD, "vdd")
        wire(1820, Y_VDD, 1900, Y_VDD, "vdd")
    # supply rail, split at the two taps it feeds; nothing in biquad B touches
    # ground, so the ground rail spans biquad A only and ends on a gnd symbol.
    wire(-40, Y_VDD, 980, Y_VDD, "vdd")
    wire(980, Y_VDD, 1480, Y_VDD, "vdd")
    wire(1480, Y_VDD, 1660, Y_VDD, "vdd")
    wire(310, Y_GND, 310, Y_GND + 50)
    wire(-40, -670, 20, -670)
    wire(-40, -630, 20, -630)

    # ---- labels, ports, ground
    for x, y, net in LAB_A:
        sym("devices/lab_pin.sym", x, y, 0, 0, f"name=la_{x}_{y} lab={net}")
        sym("devices/lab_pin.sym", MIR_A - x, y, 0, 1,
            f"name=lan_{x}_{y} lab={NMAP[net]}")
    for x, y, net in LAB_B:
        if net == "vbn" and (x, y) == (920, -70):
            net = gate_rail                       # the bridge gate
        sym("devices/lab_pin.sym", x, y, 0, 0, f"name=lb_{x}_{y} lab={net}")
        sym("devices/lab_pin.sym", MIR_B - x, y, 0, 1,
            f"name=lbn_{x}_{y} lab={NMAP[net]}")
    if replica:
        for x, y, net in LAB_R:
            sym("devices/lab_pin.sym", x, y, 0, 0, f"name=lr_{x}_{y} lab={net}")
        sym("devices/gnd.sym", 1820, Y_GND + 50, 0, 0, "name=g1 lab=0")
    for (kind, x, y, net), axis in ((PIN_A[0], MIR_A), (PIN_B[0], MIR_B)):
        sym(f"devices/{kind}.sym", x, y, 0, 0, f"name=p_{net} lab={net}")
        sym(f"devices/{kind}.sym", axis - x, y, 0, 1,
            f"name=p_{NMAP[net]} lab={NMAP[net]}")
    sym("devices/ipin.sym", -40, Y_VDD, 0, 0, "name=p_vdd lab=vdd")
    sym("devices/lab_pin.sym", 1660, Y_VDD, 0, 1, "name=l_vdd lab=vdd")
    sym("devices/ipin.sym", -40, -630, 0, 0, "name=p_vbn lab=vbn")
    sym("devices/lab_pin.sym", 20, -630, 0, 1, "name=l_vbn lab=vbn")
    sym("devices/ipin.sym", -40, -670, 0, 0, "name=p_vbp lab=vbp")
    sym("devices/lab_pin.sym", 20, -670, 0, 1, "name=l_vbp lab=vbp")
    sym("devices/gnd.sym", 310, Y_GND + 50, 0, 0, "name=g0 lab=0")

    # ---- devices, IN NETLIST ORDER (see the module docstring)
    def check(inst, got, want):
        if tuple(got) != tuple(want):
            raise SystemExit(
                f"layout/netlist mismatch on {inst}: the netlist wires it "
                f"{got}, this layout was drawn for {want}. Refusing to draw a "
                f"picture that is not the certified cell.")

    place = {}
    for tab, axis in ((DEV_A, MIR_A), (DEV_B, MIR_B)):
        for k, (x, y, nets) in tab.items():
            if k == "xmst":
                nets = (nets[0], gate_rail, nets[2], nets[3])
            place[k] = (x, y, 0, nets)
            place[TWIN[k]] = (axis - x, y, 1, tuple(NMAP[n] for n in nets))
    if replica:
        for k, (x, y, nets) in DEV_R.items():
            place[k] = (x, y, 0, nets)
    cplace = {}
    for tab, axis in ((CAP_A, MIR_A), (CAP_B, MIR_B)):
        for k, (x, y, rot, nets) in tab.items():
            cplace[k] = (x, y, rot, 0, nets)
            cplace[TWIN[k]] = (axis - x, y, rot, 1, tuple(NMAP[n] for n in nets))
    for k, (x, y, rot, nets) in CAP_D.items():
        cplace[k] = (x, y, rot, 0, nets)

    for m in mos:
        x, y, flip, want = place[m.name]
        check(m.name, m.nets, want)
        p = m.params
        # The IHP devices are `.subckt` wrappers, so `spiceprefix=X` supplies the
        # leading X the netlist already carries -- name the instance WITHOUT it
        # or the netlister emits `Xxm2` and the instance-set compare fails on a
        # purely cosmetic difference.
        sym(f"{PR}/{m.model}.sym", x, y, 0, flip,
            f"name={m.name[1:]} w={p['w']} l={p['l']} ng={p['ng']} m={p['m']} "
            f"model={m.model} spiceprefix=X")
    for c in caps:
        key = c.name[1:] if c.model else c.name           # xc13 -> c13
        x, y, rot, flip, want = cplace[key]
        check(c.name, c.nets, want)
        if c.model:
            # PDK MIM: the IHP symbol has the SAME pin geometry as devices/capa
            # (c0 (0,-30) / c1 (0,+30)), so it drops into the ideal cap's place;
            # `spiceprefix=X` + name without the x, as for the MOS instances.
            p = c.params
            sym(f"{PR}/{c.model}.sym", x, y, rot, flip,
                f"name={key} model={c.model} w={p['w']} l={p['l']} m={p['m']} "
                f"spiceprefix=X")
        else:
            sym("devices/capa.sym", x, y, rot, flip,
                f'name={c.name} m=1 value={c.value} footprint=1206 '
                f'device="ceramic capacitor"')

    # ---- annotation.  No braces inside T {} (they delimit xschem attributes)
    #      and no non-ASCII (it renders as ???).
    from datetime import datetime, timezone
    text(f"{cell} -- fully differential 4th-order 250 Hz low-pass core, "
         f"IHP SG13G2, VDD 1.5 V", 0, -760, 0.5)
    text(datetime.now(timezone.utc).strftime(
        "generated %Y-%m-%d %H:%M UTC by scripts/draw_xschem.py"),
        0, -685, 0.18)
    text("Layout carried forward from the originating campaign's drawing of "
         "this topology; biquad A is re-drawn because this cell inverts its "
         "polarity. Sizes, models and connectivity read verbatim from the "
         "certified netlist.", 0, -720, 0.25)
    text("BIQUAD A - input stage: p-type follower xm2/xm5 descends vout_1 -> "
         "net2; n-type gm_f xm4/xm8 sinks vout_1 to ground, gate on net2; "
         "n-type bias sink xm9/xm10 on net2; c13/c17 Miller, c19 differential "
         "load", 0, 130, 0.2)
    text("BIQUAD B - output stage: p-type follower xm0/xm1; THE MERGE - "
         "xm14/xm15 is branch-top bias source AND gm_f in one device, its gate "
         "driven by the internal node net4/net1; c1/c10 Miller, c12 "
         "differential load", 0, 160, 0.2)
    text("Biquad A never touches vdd and biquad B never touches ground, so the "
         "supply rail spans biquad B and the ground rail spans biquad A: the "
         "only dc path between the rails runs down the ladder through the "
         "bridge. vbp is brought out as a port but is unused inside this cell.",
         0, 190, 0.2)
    lv = sorted({m.name for m in mos if "_lv_" in m.model})
    mim = any(c.model for c in caps)
    text((f"{'/'.join(lv)} are the thin-oxide flavour; every other device is "
          "thick-oxide. " if lv else "Every device is the thick-oxide (hv) flavour. ")
         + ("Capacitors are the PDK MIM (cap_cmim): m identical square units per "
            "capacitor, sized so area*1.5 fF/um2 + perimeter*40 aF/um equals the "
            "fitted value; corner section cap_typ (cap_typ_mismatch in MC)."
            if mim else
            "Capacitors are ideal - mapping farads to area is a "
            "layout decision, not an electrical one."), 0, 220, 0.2)
    if replica:
        text("REPLICA BIAS - xr1 (= gmf_b) and xr2 (= bridge) diode-stacked from "
             "vdd, sunk by xr3 (mirror unit off vbn): vbr = vdd - |Vsg|(xr1) - "
             "|Vsg|(xr2), so the ladder current equals the replica's (mirror-"
             "referenced). Shared by both halves; signal path unchanged.",
             0, 250, 0.2)
        text("REPLICA", 1740, -600, 0.3)
        text("bridge gates on vbr", 1720, -520, 0.2)
    else:
        text("bridge gates on vbn", 1720, -520, 0.2)
    text("BIQUAD A - biquad 1", 150, -600, 0.3)
    text("BIQUAD B - biquad 2", 1000, -600, 0.3)
    text("SSF loop: net4 -> gate of xm14", 560, -500, 0.25)
    text("SSF loop: net1 -> gate of xm15", 1560, -500, 0.25, flip=1)
    text("bridge: net4 -> vout_1", 920, -30, 0.2)
    text("bridge: net1 -> vout_2", 1540, -30, 0.2, flip=1)
    C.append('C {devices/title.sym} 0 300 0 0 {name=l1 '
             'author="drawn from signoff/asbuilt/"}')
    return "\n".join(out + W + C + T) + "\n"


def core_sym(cell: str) -> str:
    """A real box symbol.  THE PIN ORDER IN THIS FILE IS THE SUBCKT PORT ORDER;
    a reordered pin list is a silent miswiring no netlist diff of the cell alone
    would catch.  The pin GEOMETRY is the record cell's (`draw_lpf_core_022`),
    so every cell's symbol drops into the same drawn-bench wiring."""
    pos = {"vinp": (-140, -40), "vinn": (-140, 40), "voutp": (140, -40),
           "voutn": (140, 40), "vbn": (40, 120), "vbp": (-40, 120),
           "vdd": (0, -120)}
    out = ['v {xschem version=3.4.4 file_version=1.2}', "G {}",
           'K {type=subcircuit', 'format="@name @pinlist @symname"',
           'template="name=x1"', "}", "V {}", "S {}", "E {}",
           "L 4 -100 -80 100 -80 {}", "L 4 100 -80 100 80 {}",
           "L 4 -100 80 100 80 {}", "L 4 -100 -80 -100 80 {}"]
    for p in PORTS:                       # ORDER MATTERS -- never sort this
        x, y = pos[p]
        if abs(x) == 140:
            out.append(f"L 4 {100 if x > 0 else -100} {y} {x} {y} {{}}")
            tx, ty = (x + 12 if x < 0 else x - 52), y - 6
        else:
            out.append(f"L 4 {x} {80 if y > 0 else -80} {x} {y} {{}}")
            tx, ty = x - 18, (y - 22 if y > 0 else y + 10)
        # dir must agree with the ipin/opin the .sch declares, or xschem warns
        d = "out" if p.startswith("vout") else "in"
        out.append(f"B 5 {x-2.5} {y-2.5} {x+2.5} {y+2.5} {{name={p} dir={d}}}")
        out.append(f"T {{{p}}} {tx} {ty} 0 0 0.25 0.25 {{}}")
    out.append(f"T {{{cell}}} -78 -14 0 0 0.4 0.4 {{}}")
    out.append("T {@name} -100 -100 0 0 0.3 0.3 {}")
    out.append("T {4th-order SSF LPF, differential} -92 18 0 0 0.2 0.2 {}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------- testbench --
# The bench is DRAWN: every element line of the certified deck (sources, balun
# VCVS pair, supply + series core-current probe, bias reference and mirror)
# becomes a placed, wired component; a bench element that reached the sheet
# only as text would be a schematic that lies about what it simulates.  Values
# and nets still come VERBATIM from the deck -- nothing is re-derived -- and
# the element set is asserted, so a deck whose bench grows a component this
# layout does not know about fails loudly instead of drawing around it.
# Layout carried forward from the record cell's reviewed bench sheet
# (`draw_lpf_core_022.tb_sch`); only the non-component lines (.lib/.nodeset/
# .options/.temp, .control) remain as text blocks.

TB_ELS = {"vdd_meas", "vflt", "xdut", "iref", "xmbn", "xmbp", "xmbpd",
          "vcm", "vsig", "evp", "evn"}
TB_NOTE = {
    "acnoise": "",
    "thd": "",
    "gd": "The .control computes tau(f) = -dphi/dw in-deck and saves the PSP "
          "op-vars, so the PDK live annotator fills from this bench's sim.raw.",
    "mc": "Mismatch corner with one seeded draw: edit .option seed= per "
          "sample; the n=100 distribution runner is lab.mc.",
}


def tb_sch(cell: str, tb: dict, what: str, analysis: str) -> Sch:
    s, e = Sch(), tb["els"]
    assert set(e) == TB_ELS, \
        f"bench elements drifted: {sorted(set(e) ^ TB_ELS)} -- teach tb_sch"
    val = lambda n: e[n]["value"]                              # noqa: E731
    nets = lambda n: e[n]["nets"]                              # noqa: E731

    # ------------------------------------------------- stimulus + balun
    s.comp("devices/vsource.sym", 300, 300, 0, 0,
           f'name=vsig value="{val("vsig")}" savecurrent=false')
    s.comp("devices/vsource.sym", 300, 500, 0, 0,
           f'name=vcm value={val("vcm")} savecurrent=false')
    for nm, y in (("vsig", 300), ("vcm", 500)):
        for p, net in zip(("p", "m"), nets(nm)):
            s.node(net, *pin("vsrc", p, 300, y), f"{nm}.{p}")
    for nm, y in (("evp", 240), ("evn", 560)):
        s.comp("devices/vcvs.sym", 600, y, 0, 0, f"name={nm} value={val(nm)}")
        for p, net in zip(("p", "m", "cp", "cm"), nets(nm)):
            s.node(net, *pin("vcvs", p, 600, y), f"{nm}.{p}")
    # ------------------------------------------------- device under test
    s.comp(f"{cell}.sym", 1200, 400, 0, 0, "name=xdut")
    dutmap = dict(zip(("vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd"),
                      nets("xdut")))
    for nm, (dx, dy) in (("vinp", (-140, -40)), ("vinn", (-140, 40)),
                         ("voutp", (140, -40)), ("voutn", (140, 40)),
                         ("vbn", (40, 120)), ("vbp", (-40, 120)),
                         ("vdd", (0, -120))):
        s.node(dutmap[nm], 1200 + dx, 400 + dy, f"xdut.{nm}")
    # ---------------------------- supply, core-current probe, bias mirror
    s.comp("devices/vsource.sym", 1450, 140, 0, 0,
           f'name=vflt value={val("vflt")} savecurrent=false')
    s.comp("devices/vsource.sym", 2050, 140, 0, 0,
           f'name=vdd_meas value={val("vdd_meas")} savecurrent=false')
    s.comp("devices/isource.sym", 1600, 140, 0, 0,
           f'name=iref value={val("iref")}')
    for nm, x in (("vflt", 1450), ("vdd_meas", 2050)):
        for p, net in zip(("p", "m"), nets(nm)):
            s.node(net, *pin("vsrc", p, x, 140), f"{nm}.{p}")
    for p, net in zip(("p", "m"), nets("iref")):
        s.node(net, *pin("isrc", p, 1600, 140), f"iref.{p}")
    for nm, x, y in (("xmbn", 1550, 380), ("xmbp", 1900, 380),
                     ("xmbpd", 1900, 180)):
        s.mos(nm[1:], e[nm], x, y, 0, e[nm]["nets"])
    # ------------------------------------------------------------ wiring
    s.wire("sig", (300, 270), (300, 180), (560, 180), (560, 220))
    s.wire("sig", (460, 180), (460, 540), (560, 540))
    s.wire("vcm", (300, 330), (300, 470))
    s.wire("vcm", (300, 400), (500, 400))
    s.wire("vcm", (500, 260), (500, 610))
    s.wire("vcm", (500, 260), (560, 260))
    s.wire("vcm", (500, 290), (600, 290), (600, 270))
    s.wire("vcm", (500, 580), (560, 580))
    s.wire("vcm", (500, 610), (600, 610), (600, 590))
    s.wire("0", (300, 530), (300, 580))
    s.wire("vinp", (600, 210), (1060, 210), (1060, 360))
    s.wire("vinn", (600, 530), (1000, 530), (1000, 440), (1060, 440))
    s.wire("voutp", (1340, 360), (1420, 360))
    s.wire("voutn", (1340, 440), (1420, 440))
    s.wire("vdd_top", (1450, 60), (2050, 60))
    s.wire("vdd_top", (1450, 60), (1450, 110))
    s.wire("vdd_top", (1600, 60), (1600, 110))
    s.wire("vdd_top", (1920, 60), (1920, 180))
    s.wire("vdd_top", (2050, 60), (2050, 110))
    s.wire("vdd", (1450, 170), (1450, 220), (1200, 220), (1200, 280))
    s.wire("vbn", (1600, 170), (1600, 300))
    s.wire("vbn", (1400, 300), (1750, 300))
    s.wire("vbn", (1570, 300), (1570, 350))
    s.wire("vbn", (1500, 300), (1500, 380), (1530, 380))
    s.wire("vbn", (1750, 300), (1750, 380), (1880, 380))
    # vbn rises to the mirror in the channel between the DUT box and its output
    # pins; vbp returns further right than the whole bias block.  Any other
    # pairing makes the two bias nets cross each other.
    s.wire("vbn", (1240, 520), (1240, 620), (1320, 620), (1320, 300), (1400, 300))
    s.wire("vbp", (1850, 250), (1920, 250))
    s.wire("vbp", (1920, 210), (1920, 350))
    s.wire("vbp", (1880, 180), (1850, 180), (1850, 250))
    s.wire("vbp", (1160, 520), (1160, 700), (2120, 700), (2120, 250), (1920, 250))
    s.wire("0", (1570, 380), (1570, 470))
    s.wire("0", (1920, 380), (1920, 470))
    s.wire("0", (1570, 470), (1920, 470))
    s.wire("0", (2050, 170), (2050, 230))
    for x, y in ((300, 580), (1750, 470), (2050, 230)):
        s.label("0", x, y, sym="gnd")
    # EVERY top-level net gets a visible name.  An unlabelled net still
    # netlists, but xschem invents `#net<N>` for it -- which is how a bench
    # silently stops probing what its .control block thinks it probes.
    for net, x, y in (("sig", 380, 180), ("vcm", 400, 400),
                      ("vdd_top", 1750, 60), ("vdd", 1320, 220),
                      ("vinp", 900, 210), ("vinn", 860, 530),
                      ("vbp", 1600, 700)):
        s.label(net, x, y)
    s.label("vbn", 1320, 560, flip=1)   # text away from the DUT box edge
    for net, y in (("voutp", 360), ("voutn", 440)):
        s.label(net, 1420, y, flip=1)   # text away from the DUT's pin caption
    # ------------------------- directives + control, verbatim from as-built
    direct = [d for d in tb["directives"] if not d.lower().startswith(".end")]
    s.comp("devices/code_shown.sym", 200, 820, 0, 0,
           'name=DIRECTIVES only_toplevel=false value="'
           + "\n".join(direct).replace('"', '\\"') + '"')
    s.comp("devices/code_shown.sym", 200, 1000, 0, 0,
           'name=CTRL only_toplevel=false value="'
           + "\n".join(tb["control"]).replace('"', '\\"') + '"')
    s.text(f"{cell} sign-off testbench -- {what}", 200, 40, 0.5)
    s.text("balun gains +-0.5 so the vsig amplitude IS the differential input.",
           200, 75, 0.3)
    s.text("vflt is a 0 V series probe carrying the CORE current only. The bias "
           "reference sits AHEAD of it, so S6 excludes the reference by "
           "construction rather than by subtraction.", 200, 760, 0.3)
    if TB_NOTE[analysis]:
        s.text(TB_NOTE[analysis], 200, 105, 0.3)
    from datetime import datetime, timezone
    # below the tallest .control block (the gd bench's), not the shortest
    s.text(datetime.now(timezone.utc).strftime(
        "generated %Y-%m-%d %H:%M UTC by scripts/draw_xschem.py"),
        200, 1450, 0.2)
    s.comp("devices/title.sym", 200, 1490, 0, 0,
           f'name=l1 author="{cell} testbench -- {analysis}"')
    return s


# ------------------------------------------------------------------ gate 1 --

IFACE = set(PORTS) | {"0"}


def parse_spice_subckt(text: str) -> tuple[dict, dict]:
    mos, caps, inside = {}, {}, False
    for ln in text.splitlines():
        s = ln.strip()
        if s.lower().startswith(".subckt"):
            inside = True
            continue
        if s.lower().startswith(".ends"):
            inside = False
            continue
        if not inside or not s or s.startswith("*"):
            continue
        t = s.split()
        if t[0].lower().startswith("xc"):          # PDK MIM instance
            caps[t[0].lower()] = (
                tuple(n.lower() for n in t[1:3]), None, t[3].lower(),
                {k.lower(): _num(v) for k, v in
                 (kv.split("=", 1) for kv in t[4:] if "=" in kv)})
        elif t[0].lower().startswith("x"):
            mos[t[0].lower()] = (
                t[5].lower(), tuple(n.lower() for n in t[1:5]),
                {k.lower(): float(v) for k, v in
                 (kv.split("=", 1) for kv in t[6:] if "=" in kv)})
        elif t[0].lower().startswith("c"):
            caps[t[0].lower()] = (tuple(n.lower() for n in t[1:3]), float(t[3]), "", {})
    return mos, caps


_SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "meg": 1e6}


def _num(v: str) -> float:
    """SPICE number with an optional SI suffix (7u, 4.86e-05, 12.5p)."""
    v = v.strip().lower()
    for suf, k in sorted(_SI.items(), key=lambda kv: -len(kv[0])):
        if v.endswith(suf):
            return float(v[:-len(suf)]) * k
    return float(v)


def gate1(asbuilt: str, drawn: str) -> tuple[bool, list]:
    """Canonical compare: instance set, model, w/l/ng/m, and a NET BIJECTION
    checked in BOTH directions with the interface nets pinned to identity."""
    am, ac = parse_spice_subckt(asbuilt)
    dm, dc = parse_spice_subckt(drawn)
    log, ok = [], True

    def bad(msg):
        nonlocal ok
        ok = False
        log.append("FAIL  " + msg)

    if set(am) != set(dm):
        bad(f"instance sets differ: {sorted(set(am) ^ set(dm))}")
    if set(ac) != set(dc):
        bad(f"capacitor sets differ: {sorted(set(ac) ^ set(dc))}")
    fwd, rev = {}, {}

    def link(a, d, who):
        if fwd.setdefault(a, d) != d or rev.setdefault(d, a) != a:
            bad(f"{who}: net map broken -- {a} -> {d} (already {fwd.get(a)})")

    for i in sorted(set(am) & set(dm)):
        (ma, na, pa), (md, nd, pd) = am[i], dm[i]
        if ma != md:
            bad(f"{i}: model {ma} vs {md}")
        for k in ("w", "l", "ng", "m"):
            va, vd = pa.get(k), pd.get(k)
            if va is None or vd is None or abs(vd - va) > max(1e-15, abs(va) * 1e-3):
                bad(f"{i}: {k} {va} vs {vd}")
        for a, d in zip(na, nd):
            link(a, d, i)
    for i in sorted(set(ac) & set(dc)):
        (na, va, ma, pa), (nd, vd, md, pd) = ac[i], dc[i]
        if ma != md:
            bad(f"{i}: cap model {ma!r} vs {md!r}")
        if ma:                                     # PDK MIM: compare geometry
            for k in ("w", "l", "m"):
                x, y = pa.get(k), pd.get(k)
                if x is None or y is None or abs(y - x) > max(1e-15, abs(x) * 1e-3):
                    bad(f"{i}: {k} {x} vs {y}")
        elif abs(vd - va) > abs(va) * 1e-3:
            bad(f"{i}: value {va} vs {vd}")
        for a, d in zip(na, nd):
            link(a, d, i)
    for n in sorted(fwd):
        if n in IFACE and fwd[n] != n:
            bad(f"interface net {n} not pinned to identity (maps to {fwd[n]})")

    log.append(f"instances: {len(am)} mos + {len(ac)} caps, sets equal: "
               f"{set(am) == set(dm) and set(ac) == set(dc)}")
    log.append(f"net bijection ({len(fwd)} nets, injective both ways: "
               f"{len(fwd) == len(rev)}):")
    for n in sorted(fwd):
        log.append(f"    {n:>8s} -> {fwd[n]:<8s}"
                   f"{'   [interface, identity]' if n in IFACE else ''}")
    return ok, log


# -------------------------------------------------------------------- main --

def netlist_with_xschem(outdir: Path, name: str, image: str) -> str:
    from lab import xsch
    return xsch.netlist(outdir, name, image)


SCORE_KEYS = ("fc_hz", "dc_db", "ripple_db", "peak_db", "mono_db", "a1000_db",
              "ph_max_deg", "irn_uv", "p_core_nw", "c_total_pf")


def gate2(outdir: Path, tb: str, design_json: Path, image: str) -> tuple[bool, list]:
    """Sim parity: the DRAWING's netlist against the certified scorecard.

    The drawing is simulated through the repo's own certification path -- the
    frozen definitions in `lab.metrics` -- and required to reproduce the numbers
    the netlist lane certified.  Any disagreement is a drawing bug, never a
    tolerance to widen.
    """
    import json
    from lab import metrics as M, ngspice as ng, thd as T
    from lab.dut import Design, Dev

    card = json.loads(design_json.read_text())
    card = card[0] if isinstance(card, list) else card
    g = card.get("design", card)
    # Certified numbers: a sibling scorecard.json (the packaged candidates)
    # beats metric keys on the sizing row itself (the record cells).  Without
    # this, a candidate's gate compares against nothing and passes vacuously.
    sc = design_json.with_name("scorecard.json")
    if sc.exists():
        j = json.loads(sc.read_text())
        card = {**j.get("scorecard", {}), "thd_db": j.get("thd_db")}
    d = Design(topology=g["topology"],
               devs={r: Dev(**v) for r, v in g["devs"].items()},
               iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
               lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
                  cap_model=g.get("cap_model", "ideal"),
               **{k: v * 1e-12 for k, v in g["caps_pf"].items()})

    s = M.score_plots(ng.simulate(netlist_with_xschem(outdir, tb, image) +
                                  "\n.end\n", "sch_ac"), d)
    t = T._score(ng.simulate(netlist_with_xschem(outdir, tb + "_thd", image) +
                             "\n.end\n", "sch_thd"), 50.0, 87.5e-3, 20, 512, "sch")
    ok, log = True, [f"{'metric':12s} {'drawing':>14s} {'certified':>14s} "
                     f"{'delta':>12s}   verdict"]
    for k in SCORE_KEYS + ("thd_db",):
        a = t.thd_db if k == "thd_db" else s.values.get(k)
        # the sizing JSON records monotonicity under its bare name
        b = card.get(k, card.get(k[:-3]) if k.endswith("_db") else None)
        if a is None or b is None:
            continue
        tol = max(1e-4, abs(b) * 5e-4)
        good = abs(a - b) <= tol
        ok &= good
        log.append(f"{k:12s} {a:14.5f} {b:14.5f} {a-b:+12.2e}   "
                   f"{'ok' if good else 'DIFFERS'}")
    log.append(f"spec violations measured from the drawing: {s.violations or 'none'}")
    return ok, log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("build", "check", "sim"))
    ap.add_argument("asbuilt")
    ap.add_argument("outdir")
    ap.add_argument("--name", required=True)
    ap.add_argument("--design", default="", help="sizing JSON for the sim gate")
    ap.add_argument("--image", default="spicexplorer-spice-base:local")
    ap.add_argument("--tb-only", action="store_true",
                    help="redraw symbol + testbench sheets but leave the core "
                         ".sch alone (it may carry op annotations)")
    a = ap.parse_args()
    ab, out = Path(a.asbuilt).resolve(), Path(a.outdir).resolve()
    mos, caps = read_asbuilt(ab)
    tb = a.name.replace("core", "tb")

    if a.cmd == "build":
        out.mkdir(parents=True, exist_ok=True)
        if not a.tb_only:
            (out / f"{a.name}.sch").write_text(core_sch(mos, caps, a.name))
        (out / f"{a.name}.sym").write_text(core_sym(a.name))
        sheets = [("_tb_acnoise", "acnoise", "op + ac + noise", tb),
                  ("_tb_thd", "thd", "coherent strobed transient, S7",
                   tb + "_thd"),
                  # optional reviewer benches -- drawn only when the deck exists
                  ("_tb_gd", "gd", "group delay, tau computed in-deck",
                   tb + "_gd"),
                  ("_tb_mc", "mc", "one seeded mismatch MC sample", tb + "_mc")]
        for suffix, analysis, what, nm in sheets:
            src = ab.with_name(ab.stem + suffix + ab.suffix)
            if suffix in ("_tb_gd", "_tb_mc") and not src.exists():
                continue
            t = tb_sch(a.name, parse_deck(src), what, analysis)
            (out / f"{nm}.sch").write_text(t.render())
            print(f"{nm}.sch: {t.stats()}")
        print(f"drew {a.name}{'.sym' if a.tb_only else '.sch/.sym'} "
              f"+ {tb}*.sch into {out}")
        return 0

    if a.cmd == "check":
        ok, log = gate1(ab.read_text(), netlist_with_xschem(out, tb, a.image))
        print("\n".join(log))
        print(f"\nGATE 1  drawing == as-built netlist : {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    ok, log = gate2(out, tb, Path(a.design).resolve(), a.image)
    print("\n".join(log))
    print(f"\nGATE 2  drawing reproduces the certified scorecard : "
          f"{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
