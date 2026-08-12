# Schematic of record — `lpf_core_022`

**Generated, not drawn.** `scripts/gen_xschem.py` emits every file here from
`../design/022-reuse-final.json` — the same JSON `lab.deck` builds its netlist
from. That is what makes "drawing == netlist" true by construction; the half
worth proving is that the drawing still *simulates* to the certified numbers,
which is `signoff/verify.py`.

| file | what |
|---|---|
| `lpf_core_022.sch` | the DUT — both differential sides, ladder order top to bottom |
| `lpf_core_022.sym` | its symbol (7 ports, in the order `lab.deck` instantiates) |
| `lpf_tb_022.sch` | testbench: op + ac + noise, with the `.control` block |
| `lpf_tb_022_thd.sch` | testbench: coherent strobed transient for S7 |
| `*.spice` | the netlists xschem produced from the above |
| `xschemrc` | library path — PDK symbols + xschem devices + this folder |

## Opening it

```bash
docker run --rm -it -v "$PWD/signoff/schematic:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_022.sch
```

(or with a host xschem, pointing `XSCHEM_LIBRARY_PATH` at the PDK's
`libs.tech/xschem` and this directory.)

## Re-netlisting and re-verifying

```bash
uv run python signoff/verify.py --regen
```

## Conventions, and the two traps behind them

**Connections are `lab_pin` labels, not drawn wires.** A generated schematic
that routes wires is unreadable and its connectivity is harder to audit; a label
sitting on the pin states the connection next to the pin it lands on, and the
netlister treats same-named labels as one net either way.

**A label must sit EXACTLY on the pin coordinate.** Off by one grid step and
xschem silently invents `#net<N>` instead of connecting — the netlist still
builds with every device present, and every connection is wrong. Caught here
only by re-simulating.

**n and p symbols mirror their D/S pins.** Read off the IHP symbols:

| | D | G | S | B |
|---|---|---|---|---|
| `sg13_*_pmos` | (20, +30) | (−20, 0) | (20, −30) | (20, 0) |
| `sg13_*_nmos` | (20, **−30**) | (−20, 0) | (20, **+30**) | (20, 0) |

Using one polarity's offsets for both produced a netlist in which every
n-channel device had drain and source swapped — again with no warning. Both
traps are why the identity gate compares *simulated results* and not netlist
text.

**Capacitors are ideal `devices/capa.sym`.** Sizing them as `cap_cmim` maps
farads to area and is a layout decision; drawing a MIM here would put an
unverified area model between the schematic and the certified result.

**The bias reference lives in the testbench `.control`/code block**, ahead of the
`vflt` core-current probe — exactly as the frozen bench has it, so S6 excludes
the reference by construction rather than by subtraction.
