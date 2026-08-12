"""Generate a schematic from a certified `Design` -- the FALLBACK, not the default.

**Prefer porting.** For a topology carried forward from the originating campaign,
that checkout already holds a human-placed, properly routed drawing, and it
transfers almost verbatim: it uses the generic `devices/{p,n}mos4.sym`, whose pin
geometry is identical to `sg13g2_pr`'s, so every wire endpoint survives a symbol
swap. See doc/journal/port-the-drawing-dont-redraw-it.md. What this script emits
is correct and gate-passing but NOT reviewable -- a grid of devices joined by
`lab_pin` labels with no routed wires. Use it for a cell that has no prior
drawing, and as the connectivity reference to check a port against.

Rule 2 says decks are BUILT, never text-edited.  A schematic is the same kind of
artefact and gets the same treatment: `lpf_core_*.sch`, its symbol and the
testbench are all emitted from the same `Design` JSON that `lab.deck` builds the
netlist from.  That makes "drawing == netlist" true by construction rather than
by inspection, and leaves only the interesting half of the identity gate to
prove: **drawing -> xschem netlist -> ngspice reproduces the certified numbers.**

Two facts about the format make this straightforward:

*   the IHP MOS symbol emits `format="@spiceprefix@name @pinlist @model w=@w
    l=@l ng=@ng m=@m"` with `spiceprefix=X` and pin order **D G S B** -- which is
    character-for-character what `lab.dut.Dev.card` writes.  So the netlister
    produces the same device lines the deck builder does.
*   capacitors are drawn as ideal `devices/capa.sym`, matching the deck.  Sizing
    them as `cap_cmim` is a LAYOUT decision (area -> farads) and belongs to the
    layout step, not to the electrical sign-off; drawing a MIM here would put an
    un-verified area model between the schematic and the certified result.

    uv run python scripts/gen_xschem.py <design.json> <outdir> [--name NNN]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import config as C          # noqa: E402
from lab.dut import Design, Dev, NROLES_BY_TOPOLOGY  # noqa: E402

HDR = ("v {xschem version=3.4.4 file_version=1.2}\nG {}\nK {}\nV {}\nS {}\nE {}\n")
PR = "sg13g2_pr"

# Grid: one column per differential side, devices stacked in ladder order.
DX, DY, X0, Y0 = 260, 120, 0, 0


def _design(path: Path) -> Design:
    d = json.loads(path.read_text())
    if isinstance(d, list):
        d = d[0]
    g = d.get("design", d)
    return Design(topology=g["topology"],
                  devs={r: Dev(**v) for r, v in g["devs"].items()},
                  iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
                  lv_roles=frozenset(g.get("lv_roles") or ()),
                  vmid=g.get("vmid"),
                  **{k: v * 1e-12 for k, v in g["caps_pf"].items()})


def _mos(inst, role, dev, model, d_, g_, s_, b_, x, y):
    """One transistor instance plus the four net labels on its pins.

    Labels rather than drawn wires: a generated schematic that routes wires is
    unreadable and its connectivity is harder to audit, whereas `lab_pin` labels
    make every connection explicit next to the pin it lands on -- and the
    netlister treats same-named labels as the same net either way.
    """
    out = [f'C {{{PR}/{model}.sym}} {x} {y} 0 0 {{name={inst} w={dev.w:.6g} '
           f'l={dev.l:.6g} ng={dev.ng} m={dev.m} model={model} spiceprefix=X}}']
    # Pin coordinates read off the IHP symbols' own pin boxes, NOT guessed --
    # and n and p are MIRRORED, which is the trap:
    #   pmos:  D (20, +30)  S (20, -30)
    #   nmos:  D (20, -30)  S (20, +30)
    #   both:  G (-20, 0)   B (20, 0)
    # A lab_pin connects at its own origin, so it must sit EXACTLY on the pin.
    # Off by one grid step and xschem silently invents `#net<N>`; use one
    # polarity's offsets for both and every n-device comes out drain/source
    # swapped. Either way the netlist still builds with every device present,
    # so the only thing that catches it is re-simulating the drawing.
    dy_d, dy_s = (-30, 30) if "nmos" in model else (30, -30)
    for i, (lab, dx, dy) in enumerate(((d_, 20, dy_d), (g_, -20, 0),
                                       (s_, 20, dy_s), (b_, 20, 0))):
        out.append(f'C {{devices/lab_pin.sym}} {x+dx} {y+dy} 0 0 '
                   f'{{name=l_{inst}_{i} lab={lab}}}')
    return out


def core_sch(d: Design) -> str:
    """The DUT: both differential sides, in ladder order top to bottom."""
    nr = NROLES_BY_TOPOLOGY.get(d.topology, frozenset())
    body = [HDR]
    # ports
    for i, p in enumerate(("vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd")):
        body.append(f'C {{devices/iopin.sym}} {X0 - 200} {Y0 + i*40} 0 0 '
                    f'{{name=p{i} lab={p}}}')
    # ladder order, P side then N side; (inst, role, d, g, s, b)
    P = [("m14", "gmf_b",      "voutp",  "net4",  "vdd",    "vdd"),
         ("m0",  "in_b",       "net4",   "vout_1", "voutp", "voutp"),
         ("mst", "bridge",     "vout_1", "vbn",   "net4",   "net4"),
         ("m2",  "in_a",       "net2",   "vinp",  "vout_1", "vout_1"),
         ("m9",  "bias_a_int", "net2",   "vbn",   "0",      "0"),
         ("m4",  "gmf_a",      "vout_1", "net2",  "0",      "0")]
    N = [("m15", "gmf_b",      "voutn",  "net1",  "vdd",    "vdd"),
         ("m1",  "in_b",       "net1",   "vout_2", "voutn", "voutn"),
         ("mstn", "bridge",    "vout_2", "vbn",   "net1",   "net1"),
         ("m5",  "in_a",       "net3",   "vinn",  "vout_2", "vout_2"),
         ("m10", "bias_a_int", "net3",   "vbn",   "0",      "0"),
         ("m8",  "gmf_a",      "vout_2", "net3",  "0",      "0")]
    for col, side in enumerate((P, N)):
        for row, (inst, role, dd, gg, ss, bb) in enumerate(side):
            model = d.model(role)
            body += _mos(inst, role, d.devs[role], model, dd, gg, ss, bb,
                         X0 + col * DX * 3, Y0 + row * DY)
    # capacitors: c1_* per side, c2_* one floating cap across the pair
    caps = [("c13", "net2", "vout_1", d.c1_a), ("c17", "net3", "vout_2", d.c1_a),
            ("c19", "vout_2", "vout_1", d.c2_a),
            ("c1", "voutp", "net4", d.c1_b), ("c10", "voutn", "net1", d.c1_b),
            ("c12", "voutn", "voutp", d.c2_b)]
    for i, (nm, a, b, val) in enumerate(caps):
        x, y = X0 + DX, Y0 + i * DY
        body.append(f'C {{devices/capa.sym}} {x} {y} 0 0 '
                    f'{{name={nm} m=1 value={val:.6g} footprint=1206 device="ceramic capacitor"}}')
        body.append(f'C {{devices/lab_pin.sym}} {x} {y-30} 0 0 {{name=l_{nm}_a lab={a}}}')
        body.append(f'C {{devices/lab_pin.sym}} {x} {y+30} 0 0 {{name=l_{nm}_b lab={b}}}')
    body.append(f'C {{devices/title.sym}} {X0-200} {Y0 + 900} 0 0 '
                f'{{name=l1 author="generated by scripts/gen_xschem.py '
                f'-- topology {d.topology}, lv_roles {sorted(d.lv_roles) or "none"}"}}')
    return "\n".join(body) + "\n"


def core_sym(name: str) -> str:
    """A minimal symbol: the seven ports in the order `lab.deck` instantiates."""
    pins = ("vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd")
    out = [f'v {{xschem version=3.4.4 file_version=1.2}}\nG {{}}\n'
           f'K {{type=subcircuit\nformat="@name @pinlist @symname"\n'
           f'template="name=x1"\n}}\nV {{}}\nS {{}}\nE {{}}']
    out.append("L 4 -60 -110 60 -110 {}\nL 4 60 -110 60 130 {}\n"
               "L 4 -60 130 60 130 {}\nL 4 -60 -110 -60 130 {}")
    for i, p in enumerate(pins):
        y = -90 + i * 30
        out.append(f'B 5 -62.5 {y-2.5} -57.5 {y+2.5} {{name={p} dir=inout}}')
        out.append(f'T {{{p}}} -55 {y-6} 0 0 0.2 0.2 {{}}')
    out.append(f'T {{{name}}} -40 -105 0 0 0.3 0.3 {{}}')
    return "\n".join(out) + "\n"


def tb_sch(d: Design, core: str, analysis: str = "acnoise") -> str:
    """Testbench: the same balun + probes the frozen bench uses, plus .control.

    Mirrors `lab.deck` exactly -- balun gains +-0.5 so `vsig`'s own amplitude IS
    the differential input, a series `vflt` carrying only the core current for
    S6, and the bias reference ahead of that probe so S6 excludes it.
    """
    from lab.deck import _bias
    libs = "\n".join(f".lib {lib} {C.CORNER_NOM}" for lib in d.libs())
    # Reuse the deck builder's OWN bias fragment rather than reimplementing it.
    # `_bias` chooses its mirror units by a fallback rule (any device of the
    # right flavour, in dict order) that is easy to get subtly wrong: a different
    # p-side diode geometry loads `vdd_top` differently, shifts the dc solve in
    # the last digits, and shows up as a ~0.001 dB ripple mismatch in the
    # identity gate -- a real difference, just a tiny one.
    bias = _bias(d)
    vh = min(d.vocm, C.VDD)
    vm = vh if d.vmid is None else min(d.vmid, C.VDD)
    if analysis == "acnoise":
        ctrl = ("op\nwrite sim.raw\nac dec 50 0.1 100000\nwrite sim.raw\n"
                "noise v(voutp,voutn) vsig dec 50 0.1 1000\nsetplot noise1\n"
                "write sim.raw")
        head = "set filetype=binary\nset appendwrite"
    else:
        tper, cyc, settle, ppc = 1/50.0, 20, 8, 512
        ctrl = (f"op\ntran {tper/ppc:.10g} {(settle+cyc)*tper:.10g} "
                f"{settle*tper:.10g} {tper/ppc:.10g}\nwrite sim.raw")
        head = "set filetype=binary"
    stim = (f"vsig sig vcm dc 0 ac 1" if analysis == "acnoise"
            else f"vsig sig vcm dc 0 sin(0 87.5m 50) ac 1")
    spice = "\n".join([
        libs,
        f"vdd_meas vdd_top 0 {C.VDD}",
        "vflt vdd_top vdd 0",
        bias,
        f"vcm vcm 0 {d.vicm}",
        stim,
        "evp vinp vcm sig vcm 0.5",
        "evn vinn vcm sig vcm -0.5",
        f".nodeset v(xdut.vout_1)={vm} v(xdut.vout_2)={vm} v(voutp)={vh} v(voutn)={vh}",
        f".temp {C.TEMP_NOM}",
    ] + ([".options reltol=1e-5 abstol=1e-13 vntol=1e-9 chgtol=1e-16 "
          "method=gear maxord=2"] if analysis != "acnoise" else []))
    # xschem keeps multi-line property values as REAL newlines inside the
    # quotes.  Writing "\\n" escapes instead puts a literal letter 'n' into the
    # netlist -- which is how ".lib cornerMOShv.lib mos_ttn.lib ..." happens.
    spice_esc = spice.replace('"', '\\"')
    body = [HDR,
            f'C {{{core}.sym}} 300 0 0 0 {{name=xdut}}']
    for i, p in enumerate(("vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd")):
        body.append(f'C {{devices/lab_pin.sym}} 240 {-90 + i*30} 0 0 '
                    f'{{name=t{i} lab={p}}}')
    body.append(f'C {{devices/code_shown.sym}} 700 -200 0 0 {{name=BENCH '
                f'only_toplevel=false value="{spice_esc}"}}')
    body.append(f'C {{devices/code_shown.sym}} 700 300 0 0 {{name=CTRL '
                f'only_toplevel=false value=".control\n{head}\n{ctrl}\n.endc"}}')
    body.append(f'C {{devices/title.sym}} 0 500 0 0 {{name=l1 '
                f'author="LPF sign-off testbench ({analysis}) -- generated"}}')
    return "\n".join(body) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design"); ap.add_argument("outdir")
    ap.add_argument("--name", default="lpf_core_022")
    a = ap.parse_args()
    d = _design(Path(a.design))
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.name}.sch").write_text(core_sch(d))
    (out / f"{a.name}.sym").write_text(core_sym(a.name))
    (out / f"{a.name.replace('core', 'tb')}.sch").write_text(tb_sch(d, a.name, "acnoise"))
    (out / f"{a.name.replace('core', 'tb')}_thd.sch").write_text(tb_sch(d, a.name, "thd"))
    print(f"wrote {a.name}.sch / .sym and the two testbenches into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
