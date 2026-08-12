"""Draw the *human-readable* schematic of record for `lpf_core_022`.

Same rule as `scripts/gen_xschem.py` -- generated, never hand-typed -- but this
one draws a schematic a reviewer can read: devices placed on the dc ladder they
actually form, real routed wires instead of a label on every pin, the two
differential halves mirrored about the centre line, and the floating cross-caps
drawn between them.

**Provenance.**  The placement and routing are carried forward from the drawn
schematic of the originating campaign: same frame (vdd rail on top, gnd rail at
the bottom, stage A left / stage B right, each stage's halves mirrored), same
columns, same idiom (ipin/opin at the boundary, `lab_pin` only where a net
jumps between stages).  Stage B ports one-for-one -- every wire coordinate is
the original's.  **Stage A does not**, and could not: this cell's input follower
is p-type where the originating design's was n-type, so its source and drain
swap, `vout_1` and `net2` exchange places in the dc ladder, and the gm_f device
turns from a vdd-referred p-type into a gnd-referred n-type.  Stage A is
therefore re-routed here; the frame around it is the original's.

Every number comes from the as-built netlists in `signoff/asbuilt/`; the tables
below carry only *positions* and the *expected* net of each pin.  If the sizing
or the wiring ever changes, the expected-net assertions fail loudly rather than
drawing a plausible-looking lie.

    uv run python signoff/schematic/draw_lpf_core_022.py

Three traps the code defends against, each of which has already cost a cycle:

*   a label or a device pin connects only when it sits EXACTLY on the wire
    point.  Wires are emitted from polylines that are auto-split at every node
    of their own net, and every device pin is asserted to land on a node of the
    net it is declared to be on (`Sch._check`), which also refuses any point
    that would short two nets.
*   `n` and `p` symbols MIRROR their drain/source pins -- pmos D (20,+30) /
    S (20,-30), nmos D (20,-30) / S (20,+30) -- so one polarity's offsets used
    for both silently swaps D and S on every n-device.  `PINS` is read off the
    IHP `.sym` files.  This is also why a p-for-n symbol swap at fixed wiring is
    never a rename: it re-labels which wire is the drain.
*   xschem stores multi-line property values as REAL newlines inside the quotes;
    a "\\n" escape arrives in the netlist as a literal letter n.
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASB = HERE.parent / "asbuilt"
CELL = "lpf_core_022"
PR = "sg13g2_pr"
HDR = "v {xschem version=3.4.4 file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n"

# ---------------------------------------------------------------- symbol pins
# Read off $PDK_ROOT/.../sg13g2_pr/*.sym and devices/*.sym -- NOT guessed.
PINS = {
    "pmos": {"D": (20, 30), "G": (-20, 0), "S": (20, -30), "B": (20, 0)},
    "nmos": {"D": (20, -30), "G": (-20, 0), "S": (20, 30), "B": (20, 0)},
    "capa": {"p": (0, -30), "m": (0, 30)},
    "vsrc": {"p": (0, -30), "m": (0, 30)},
    "isrc": {"p": (0, -30), "m": (0, 30)},
    "vcvs": {"p": (0, -30), "m": (0, 30), "cp": (-40, -20), "cm": (-40, 20)},
}


def xf(dx: int, dy: int, rot: int = 0, flip: int = 0) -> tuple[int, int]:
    """xschem's own transform, verified empirically against the netlister."""
    x, y = ((dx, dy), (-dy, dx), (-dx, -dy), (dy, -dx))[rot % 4]
    return (-x if flip else x, y)


def pin(kind: str, name: str, x: int, y: int, rot: int = 0, flip: int = 0):
    dx, dy = xf(*PINS[kind][name], rot, flip)
    return (x + dx, y + dy)


# ------------------------------------------------------------------- parsing
def parse_deck(path: Path, subckt_body: bool = False) -> dict:
    """name -> dict(nets=[...], model=..., params=..., value=...).

    `.subckt`/`.ends` are CONSUMED, never passed through as directives: they are
    structure, and a `.subckt` that reaches the bench's code block without its
    `.ends` is an unbalanced deck ngspice refuses to run.  Set `subckt_body`
    when the text IS one subcircuit's body and its devices are wanted.
    """
    els, directives, control = {}, [], []
    in_ctrl, depth = False, 0
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("*"):
            continue
        low = s.lower()
        if low.startswith(".subckt"):
            depth += 1
            continue
        if low.startswith(".ends"):
            depth = max(0, depth - 1)
            continue
        if depth and not subckt_body:
            continue
        if low.startswith(".control"):
            in_ctrl = True
        if in_ctrl:
            control.append(s)
            if low.startswith(".endc"):
                in_ctrl = False
            continue
        if s.startswith("."):
            directives.append(s)
            continue
        t = s.split()
        nm = t[0].lower()
        if nm.startswith("xdut"):
            els[nm] = dict(nets=t[1:-1], sub=t[-1])
        elif nm.startswith("x"):
            model = next(w for w in t[1:] if w.startswith("sg13"))
            i = t.index(model)
            els[nm] = dict(nets=t[1:i], model=model,
                           params=dict(p.split("=", 1) for p in t[i + 1:]))
        elif nm.startswith("c"):
            els[nm] = dict(nets=t[1:3], value=t[3])
        elif nm.startswith("e"):
            els[nm] = dict(nets=t[1:5], value=" ".join(t[5:]))
        elif nm.startswith(("v", "i")):
            els[nm] = dict(nets=t[1:3], value=" ".join(t[3:]))
    return dict(els=els, directives=directives, control=control)


def core_body(path: Path) -> dict:
    """Only the lines between `.subckt lpf_core` and `.ends`."""
    txt = path.read_text()
    m = re.search(r"^\.subckt\s+lpf_core\b.*?^\.ends", txt, re.S | re.M)
    tmp = Path("/tmp/_lpf_core_body.sp")
    tmp.write_text(m.group(0) if m else txt)
    return parse_deck(tmp, subckt_body=True)


# --------------------------------------------------------------- schematic IR
class Sch:
    """Collects components, wires, labels and text; emits a `.sch`.

    Wires are given as polylines per net; every polyline is split at every node
    of that net (device pins, labels, vertices of the net's other polylines) so
    a T-junction is always a shared segment ENDPOINT -- the only thing xschem's
    netlister is guaranteed to treat as a connection.
    """

    def __init__(self):
        self.comps: list[str] = []
        self.texts: list[str] = []
        self.paths: dict[str, list[list[tuple[int, int]]]] = {}
        self.nodes: dict[str, set[tuple[int, int]]] = {}
        self.labels: list[tuple[str, int, int, str, int, int]] = []
        self.pins: list[tuple[str, str, int, int]] = []

    # -- placement -----------------------------------------------------------
    def comp(self, sym: str, x: int, y: int, rot: int, flip: int, attrs: str):
        self.comps.append(f"C {{{sym}}} {x} {y} {rot} {flip} {{{attrs}}}")

    def text(self, s: str, x: int, y: int, size: float = 0.3):
        assert "{" not in s and "}" not in s, f"braces in T text: {s}"
        assert s.isascii(), f"non-ascii in T text: {s}"
        self.texts.append(f"T {{{s}}} {x} {y} 0 0 {size} {size} {{}}")

    def node(self, net: str, x: int, y: int, what: str = ""):
        self.nodes.setdefault(net, set()).add((x, y))
        if what:
            self.pins.append((net, what, x, y))

    def wire(self, net: str, *pts: tuple[int, int]):
        self.paths.setdefault(net, []).append(list(pts))
        for p in pts:
            self.nodes.setdefault(net, set()).add(p)

    def label(self, net: str, x: int, y: int, sym: str = "lab_pin",
              rot: int = 0, flip: int = 0):
        self.labels.append((sym, x, y, net, rot, flip))
        self.node(net, x, y)

    def mos(self, inst: str, el: dict, x: int, y: int, flip: int,
            expect: list[str]):
        assert el["nets"] == expect, \
            f"x{inst}: netlist says {el['nets']}, layout expects {expect}"
        kind = "nmos" if "nmos" in el["model"] else "pmos"
        p = el["params"]
        self.comp(f"{PR}/{el['model']}.sym", x, y, 0, flip,
                  f"name={inst} w={p['w']} l={p['l']} ng={p['ng']} m={p['m']} "
                  f"model={el['model']} spiceprefix=X")
        for nm, net in zip(("D", "G", "S", "B"), expect):
            self.node(net, *pin(kind, nm, x, y, 0, flip), f"{inst}.{nm}")

    def cap(self, inst: str, el: dict, x: int, y: int, rot: int,
            expect: list[str]):
        assert el["nets"] == expect, \
            f"{inst}: netlist says {el['nets']}, layout expects {expect}"
        self.comp("devices/capa.sym", x, y, rot, 0,
                  f'name={inst} m=1 value={el["value"]} footprint=1206 '
                  f'device="ceramic capacitor"')
        for nm, net in zip(("p", "m"), expect):
            self.node(net, *pin("capa", nm, x, y, rot), f"{inst}.{nm}")

    # -- checks --------------------------------------------------------------
    def _check(self):
        seen: dict[tuple[int, int], str] = {}
        for net, what, x, y in self.pins:
            assert (x, y) in self.nodes.get(net, ()), \
                f"{what} at ({x},{y}) is not a node of net {net}"
        for net, pts in self.nodes.items():
            for p in pts:
                if p in seen and seen[p] != net:
                    raise AssertionError(f"short: {p} on {seen[p]} and {net}")
                seen[p] = net
        for net, segs in self._segments().items():
            for (a, b) in segs:
                for other, pts in self.nodes.items():
                    if other == net:
                        continue
                    for p in pts:
                        if _on_seg(p, a, b):
                            raise AssertionError(
                                f"short: {other} node {p} on {net} {a}-{b}")

    def _segments(self) -> dict[str, list]:
        out: dict[str, list] = {}
        for net, polys in self.paths.items():
            nodes = self.nodes[net]
            segs = []
            for poly in polys:
                for a, b in zip(poly, poly[1:]):
                    cuts = sorted({a, b} | {p for p in nodes if _on_seg(p, a, b)},
                                  key=lambda p: (abs(p[0] - a[0]), abs(p[1] - a[1])))
                    segs += list(zip(cuts, cuts[1:]))
            out[net] = [s for s in segs if s[0] != s[1]]
        return out

    def crossings(self) -> list:
        """Pure X crossings (no shared endpoint): legal, but worth counting."""
        segs = [(n, s) for n, ss in self._segments().items() for s in ss]
        out = []
        for i, (n1, (a, b)) in enumerate(segs):
            for n2, (c, d) in segs[i + 1:]:
                if n1 == n2:
                    continue
                if a[0] == b[0] and c[1] == d[1]:
                    v, h = (a, b), (c, d)
                elif a[1] == b[1] and c[0] == d[0]:
                    v, h = (c, d), (a, b)
                else:
                    continue
                x, y = v[0][0], h[0][1]
                if (min(v[0][1], v[1][1]) < y < max(v[0][1], v[1][1])
                        and min(h[0][0], h[1][0]) < x < max(h[0][0], h[1][0])):
                    out.append((x, y, n1, n2))
        return out

    # -- emit ----------------------------------------------------------------
    def render(self) -> str:
        self._check()
        body = [HDR]
        for net, segs in sorted(self._segments().items()):
            for (a, b) in segs:
                body.append(f"N {a[0]} {a[1]} {b[0]} {b[1]} {{lab={net}}}")
        body += self.comps
        for sym, x, y, net, rot, flip in self.labels:
            body.append(f"C {{devices/{sym}.sym}} {x} {y} {rot} {flip} "
                        f"{{name=l{len(net)}_{x}_{y} lab={net}}}")
        body += self.texts
        return "\n".join(body) + "\n"

    def stats(self) -> str:
        n = sum(len(v) for v in self._segments().values())
        return (f"{len(self.comps)} components, {n} wire segments, "
                f"{len(self.crossings())} crossings {self.crossings() or ''}")


def _on_seg(p, a, b) -> bool:
    if p in (a, b):
        return False
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False


# ================================================================ the DUT
# Mirror axes carried forward from the original drawing: stage A about x=310,
# stage B about x=1230.  `A()`/`B()` mirror a P-half x into its N-half twin.
def A(x): return 620 - x
def B(x): return 2460 - x


def core_sch(dut: dict) -> Sch:
    s, e = Sch(), dut["els"]

    # ---------------------------------------------------------- devices
    # stage A: p-type input follower, n-type gm_f, n-type bias sink
    s.mos("m2",  e["xm2"],   40, -320, 0, ["net2", "vinp", "vout_1", "vout_1"])
    s.mos("m9",  e["xm9"],   40, -110, 0, ["net2", "vbn", "0", "0"])
    s.mos("m4",  e["xm4"],  200, -110, 0, ["vout_1", "net2", "0", "0"])
    s.mos("m5",  e["xm5"],  A(40), -320, 1, ["net3", "vinn", "vout_2", "vout_2"])
    s.mos("m10", e["xm10"], A(40), -110, 1, ["net3", "vbn", "0", "0"])
    s.mos("m8",  e["xm8"],  A(200), -110, 1, ["vout_2", "net3", "0", "0"])
    # stage B: branch-top pmos with the merged gm_f, pmos follower, bridge
    s.mos("m14",  e["xm14"], 960, -450, 0, ["voutp", "net4", "vdd", "vdd"])
    s.mos("m0",   e["xm0"],  960, -260, 0, ["net4", "vout_1", "voutp", "voutp"])
    s.mos("mst",  e["xmst"], 960,  -70, 0, ["vout_1", "vbn", "net4", "net4"])
    s.mos("m15",  e["xm15"], B(960), -450, 1, ["voutn", "net1", "vdd", "vdd"])
    s.mos("m1",   e["xm1"],  B(960), -260, 1, ["net1", "vout_2", "voutn", "voutn"])
    s.mos("mstn", e["xmstn"], B(960), -70, 1, ["vout_2", "vbn", "net1", "net1"])
    # capacitors: rot=2 on c13/c17 keeps the netlist's own terminal order
    s.cap("c13", e["c13"], 150, -230, 2, ["net2", "vout_1"])
    s.cap("c17", e["c17"], A(150), -230, 2, ["net3", "vout_2"])
    s.cap("c19", e["c19"], 310, -380, 1, ["vout_2", "vout_1"])
    s.cap("c1",  e["c1"],  1050, -200, 0, ["voutp", "net4"])
    s.cap("c10", e["c10"], B(1050), -200, 0, ["voutn", "net1"])
    s.cap("c12", e["c12"], 1230, -320, 1, ["voutn", "voutp"])

    # ---------------------------------------------------------- rails
    s.wire("vdd", (-40, -560), (1660, -560))
    s.wire("0", (-40, 60), (1660, 60))
    for x in (980, B(980)):                       # m14/m15 source + bulk
        s.wire("vdd", (x, -560), (x, -480), (x, -450))
    for x in (60, 220, A(220), A(60)):            # m9/m4/m8/m10 source + bulk
        s.wire("0", (x, -80), (x, 60))
        s.wire("0", (x, -110), (x, -80))

    # ---------------------------------------------------------- stage A
    def stage_a(mir):
        f = A if mir else (lambda v: v)
        up, dn = ("vout_2", "net3") if mir else ("vout_1", "net2")
        # the upper rail is the follower SOURCE node (vout_1 / vout_2)
        s.wire(up, (f(60), -380), (f(280), -380))
        s.wire(up, (f(60), -350), (f(60), -380))               # m2 S
        s.wire(up, (f(60), -350), (f(60), -320))               # m2 B -> S
        s.wire(up, (f(150), -260), (f(150), -380))             # c13 m
        s.wire(up, (f(220), -140), (f(220), -380))             # m4 D riser
        s.label(up, f(100), -380, flip=int(mir))
        # the lower rail is the follower DRAIN node (net2 / net3)
        s.wire(dn, (f(60), -180), (f(180), -180))
        s.wire(dn, (f(60), -290), (f(60), -180))               # m2 D
        s.wire(dn, (f(60), -140), (f(60), -180))               # m9 D
        s.wire(dn, (f(150), -200), (f(150), -180))             # c13 p
        s.wire(dn, (f(180), -180), (f(180), -110))             # -> m4 gate
        s.label(dn, f(120), -180, flip=int(mir))
        # gates
        s.wire("vinn" if mir else "vinp", (f(20), -320), (f(-20), -320))
        s.wire("vbn", (f(20), -110), (f(0), -110))

    stage_a(False)
    stage_a(True)
    # the two input pins sit at the outer edge of stage A
    s.comp("devices/ipin.sym", -20, -320, 0, 0, "name=p_vinp lab=vinp")
    s.node("vinp", -20, -320, "port.vinp")
    s.comp("devices/ipin.sym", A(-20), -320, 0, 1, "name=p_vinn lab=vinn")
    s.node("vinn", A(-20), -320, "port.vinn")
    s.label("vbn", 0, -110)
    s.label("vbn", A(0), -110, flip=1)

    # ---------------------------------------------------------- stage B
    def stage_b(mir):
        f = B if mir else (lambda v: v)
        out, mid, vo = (("voutn", "net1", "vout_2") if mir
                        else ("voutp", "net4", "vout_1"))
        s.wire(out, (f(980), -320), (f(1200), -320))
        s.wire(out, (f(980), -420), (f(980), -320))            # m14 D
        s.wire(out, (f(980), -290), (f(980), -320))            # m0 S
        s.wire(out, (f(980), -260), (f(980), -290))            # m0 B -> S
        s.wire(out, (f(1050), -230), (f(1050), -320))          # c1 p
        s.wire(out, (f(1090), -360), (f(1090), -320))
        s.wire(out, (f(1090), -360), (f(1130), -360))
        s.wire(mid, (f(820), -140), (f(1050), -140))
        s.wire(mid, (f(980), -230), (f(980), -140))            # m0 D
        s.wire(mid, (f(980), -100), (f(980), -140))            # mst S
        s.wire(mid, (f(980), -70), (f(980), -100))             # mst B -> S
        s.wire(mid, (f(1050), -170), (f(1050), -140))          # c1 m
        # the SSF loop: the branch-top gate is driven by the internal node
        s.wire(mid, (f(940), -450), (f(820), -450), (f(820), -140))
        # a lab_pin draws its text AWAY from the flip side; put both halves'
        # text into the empty span of the rail, not on top of the column wire
        s.label(mid, f(890), -140, flip=1 - int(mir))
        # stage-A nodes reach stage B by name, as in the original drawing
        s.wire(vo, (f(940), -260), (f(920), -260))
        s.label(vo, f(920), -260, flip=int(mir))
        s.wire(vo, (f(980), -40), (f(980), 10))                # mst D
        s.label(vo, f(980), 10, flip=int(mir))
        s.wire("vbn", (f(940), -70), (f(920), -70))            # mst gate
        s.label("vbn", f(920), -70, flip=int(mir))
        s.comp("devices/opin.sym", f(1130), -360, 0, int(mir),
               f"name=p_{out} lab={out}")
        s.node(out, f(1130), -360, f"port.{out}")

    stage_b(False)
    stage_b(True)

    # ------------------------------------------------- supply / bias ports
    s.comp("devices/ipin.sym", -40, -560, 0, 0, "name=p_vdd lab=vdd")
    s.node("vdd", -40, -560, "port.vdd")
    s.label("vdd", 1660, -560, flip=1)
    s.label("0", -40, 60, sym="gnd")
    s.label("0", 1660, 60, sym="gnd")
    for lab, y in (("vbp", -670), ("vbn", -630)):
        s.comp("devices/ipin.sym", -40, y, 0, 0, f"name=p_{lab} lab={lab}")
        s.node(lab, -40, y, f"port.{lab}")
        s.wire(lab, (-40, y), (20, y))
        s.label(lab, 20, y, flip=1)

    # ---------------------------------------------------------- annotation
    s.text(f"{CELL} -- 4th-order 250 Hz super-source-follower low-pass, fully "
           "differential, IHP SG13G2, VDD 1.5 V", 0, -760, 0.5)
    s.text("Schematic of record. Placement and routing carried forward from the "
           "originating campaign's drawing; stage A is re-routed because this "
           "cell's input follower is p-type.", 0, -725, 0.25)
    s.text("The gm_f of stage B is MERGED into the branch-top device: m14/m15 "
           "gates are driven by net4/net1, so the follower loop closes through "
           "the branch top. vbp is a port only -- unused by the core.",
           0, -700, 0.25)
    s.text("STAGE A -- biquad 1  (pmos input followers m2/m5, nmos gm_f m4/m8, "
           "nmos bias sink m9/m10)", 60, -600, 0.3)
    s.text("STAGE B -- biquad 2  (pmos input followers m0/m1, merged gm_f "
           "m14/m15)", 900, -600, 0.3)
    s.text("SSF loop: net4 -> gate of m14", 700, -530, 0.25)
    s.text("SSF loop: net1 -> gate of m15", 1560, -530, 0.25)
    s.text("bridge: net4 -> vout_1", 830, -20, 0.25)
    s.text("bridge: net1 -> vout_2", 1250, -20, 0.25)
    s.text("in_a", -30, -370, 0.25)
    s.text("in_a", A(-30) - 40, -370, 0.25)
    s.text("bias_a_int", -60, -160, 0.25)
    s.text("bias_a_int", A(-60) - 60, -160, 0.25)
    s.text("gm_f,a", 130, -30, 0.25)
    s.text("gm_f,a", A(130) - 20, -30, 0.25)
    s.text("gm_f,b (merged)", 800, -480, 0.25)
    s.text("gm_f,b (merged)", 1540, -480, 0.25)
    s.text("in_b", 830, -300, 0.25)
    s.text("in_b", 1560, -300, 0.25)
    s.text("stage A per half: m2/m5 pmos input follower (bulk tied to source), "
           "m4/m8 shunt gm_f to gnd (gate on net2/net3), m9/m10 vbn bias sink, "
           "c13/c17 the Miller cap, c19 the differential load.", 0, 130, 0.25)
    s.text("stage B per half: m14/m15 branch-top pmos acting as bias source AND "
           "gm_f loop device, m0/m1 pmos input follower, c1/c10 the Miller cap, "
           "c12 the differential load.", 0, 160, 0.25)
    s.text("dc ladder per half, top to bottom: vdd - m14 - voutp - m0 - net4 - "
           "mst - vout_1 - m2 - net2 - m9 - gnd, with m4 shunting vout_1 to gnd. "
           "No CMFB: c12/c19 set the differential poles.", 0, 190, 0.25)
    s.comp("devices/title.sym", 0, 260, 0, 0,
           f'name=l1 author="{CELL} -- drawn from signoff/asbuilt"')
    return s


def core_sym() -> str:
    """Ports in the exact order `lab.deck` instantiates them -- the ORDER is the
    contract; only the coordinates are a drawing choice."""
    pins = [("vinp", -140, -40), ("vinn", -140, 40), ("voutp", 140, -40),
            ("voutn", 140, 40), ("vbn", 40, 120), ("vbp", -40, 120),
            ("vdd", 0, -120)]
    out = ['v {xschem version=3.4.4 file_version=1.2}', 'G {}',
           'K {type=subcircuit', 'format="@name @pinlist @symname"',
           'template="name=x1"', '}', 'V {}', 'S {}', 'E {}',
           "L 4 -100 -80 100 -80 {}", "L 4 100 -80 100 80 {}",
           "L 4 -100 80 100 80 {}", "L 4 -100 -80 -100 80 {}"]
    for nm, x, y in pins:
        if abs(x) == 140:
            out.append(f"L 4 {100 if x > 0 else -100} {y} {x} {y} {{}}")
            tx, ty = (x + 12 if x < 0 else x - 52), y - 6
        else:
            out.append(f"L 4 {x} {80 if y > 0 else -80} {x} {y} {{}}")
            tx, ty = x - 18, (y - 22 if y > 0 else y + 10)
        # dir must agree with the ipin/opin the .sch declares, or xschem warns
        d = "out" if nm.startswith("vout") else "in"
        out.append(f"B 5 {x-2.5} {y-2.5} {x+2.5} {y+2.5} {{name={nm} dir={d}}}")
        out.append(f"T {{{nm}}} {tx} {ty} 0 0 0.25 0.25 {{}}")
    out.append(f"T {{{CELL}}} -78 -14 0 0 0.4 0.4 {{}}")
    out.append("T {@name} -100 -100 0 0 0.3 0.3 {}")
    out.append("T {4th-order SSF LPF, differential} -92 18 0 0 0.2 0.2 {}")
    return "\n".join(out) + "\n"


# ============================================================== testbenches
def tb_sch(tb: dict, analysis: str) -> Sch:
    s, e = Sch(), tb["els"]
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
    s.comp(f"{CELL}.sym", 1200, 400, 0, 0, "name=xdut")
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
           'name=BENCH only_toplevel=false value="'
           + "\n".join(direct).replace('"', '\\"') + '"')
    s.comp("devices/code_shown.sym", 200, 1000, 0, 0,
           'name=CTRL only_toplevel=false value="'
           + "\n".join(tb["control"]).replace('"', '\\"') + '"')
    what = ("op + ac + noise" if analysis == "acnoise"
            else "coherent strobed transient (THD)")
    s.text(f"{CELL} sign-off testbench -- {what}", 200, 40, 0.5)
    s.text("balun gains +-0.5 so the vsig amplitude IS the differential input.",
           200, 75, 0.3)
    s.text("vflt is a 0 V series probe carrying the CORE current only. The bias "
           "reference sits AHEAD of it, so S6 excludes the reference by "
           "construction rather than by subtraction.", 200, 760, 0.3)
    s.comp("devices/title.sym", 200, 1260, 0, 0,
           f'name=l1 author="{CELL} testbench -- {analysis}"')
    return s


# ------------------------------------------------------------------------ main
def main() -> int:
    s = core_sch(core_body(ASB / "022-reuse-final.sp"))
    (HERE / f"{CELL}.sch").write_text(s.render())
    (HERE / f"{CELL}.sym").write_text(core_sym())
    print(f"{CELL}.sch: {s.stats()}")
    for tag, f in (("acnoise", "lpf_tb_022"), ("thd", "lpf_tb_022_thd")):
        t = tb_sch(parse_deck(ASB / f"022-reuse-final_tb_{tag}.sp"), tag)
        (HERE / f"{f}.sch").write_text(t.render())
        print(f"{f}.sch: {t.stats()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
