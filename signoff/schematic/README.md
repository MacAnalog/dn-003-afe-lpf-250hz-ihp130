# Schematic of record — `lpf_core_022`

**Generated, and drawn.** `draw_lpf_core_022.py` emits every `.sch`/`.sym` here
from the as-built netlists in `../asbuilt/` — no size, value or model is typed
by hand — but it emits a schematic laid out the way the circuit actually works:
devices on the dc ladder they form, **real routed wires**, the differential
halves mirrored, and the cross-caps drawn between them.

| file | what |
|---|---|
| `lpf_core_022.sch` | the DUT — stage A left, stage B right, halves mirrored |
| `lpf_core_022.sym` | its symbol (7 ports, in the order `lab.deck` instantiates) |
| `lpf_tb_022.sch` | testbench: op + ac + noise, with its `.control` block |
| `lpf_tb_022_thd.sch` | testbench: coherent strobed transient for S7 |
| `*.png` | renders (visual evidence) — **absent in this revision**: the EDA server's native xschem is built without cairo, so its `--png`/`--svg` export silently writes nothing; regenerate in the docker lane (cairo xschem) with `xschem -q --plotfile <f>.png --png <f>.sch` when it is available. The `.sch` sources and both identity gates are the binding evidence. |
| `*.spice` | the netlists xschem produced from the above |
| `draw_lpf_core_022.py` | the generator |
| `check_netlist.py` | gate 1 — canonical netlist compare vs `../asbuilt/` |
| `xschemrc` | library path — PDK symbols + xschem devices + this folder |

## Provenance of the layout

Placement and routing are **carried forward from the originating campaign's
drawn schematic** of the same topology: same frame (vdd rail on top, gnd at the
bottom, stage A left / stage B right), same columns, same idiom (`ipin`/`opin`
at the boundary, `lab_pin` only where a net jumps between stages).

**Stage B ports one-for-one** — every wire coordinate is the original's, because
its connectivity is identical device for device.
**Stage A does not, and cannot.** This cell's input follower is p-type where the
originating design's was n-type. A p-type follower's source and drain are the
other way up, so `vout_1` and `net2` exchange places in the dc ladder, the bias
sink moves from `vout_1` to `net2`, and gm_f,a turns from a vdd-referred p-type
into a gnd-referred n-type. Stage A is therefore re-routed; only its frame is
inherited. A symbol-for-symbol swap at fixed wiring would have produced a
netlist that still builds and is wrong in every stage-A device.

## The two gates

```bash
uv run python signoff/schematic/draw_lpf_core_022.py   # redraw
uv run python signoff/schematic/check_netlist.py       # gate 1: connectivity
uv run python signoff/verify.py                        # gate 2: the numbers
```

**Gate 1** — same instance set, same model per instance, w/l/ng/m and cap values
within 0.1 %, connectivity equal under a net bijection checked in both
directions with the interface nets pinned to identity. Currently: 19 core
instances and 11 bench instances, bijection **identity**, PASS.

**Gate 2** — the drawing's own netlist simulated through `lab.metrics` matches
what `lab.deck` builds from the same sizing, and matches `signoff/scorecard.json`.

> `--regen` now dispatches each drawing to **its own** drawer, because the two
> lay out differently: regenerating with the wrong one would silently replace a
> reviewed schematic with a different (still gate-passing) one.

## Opening it

```bash
docker run --rm -it -v "$PWD/signoff/schematic:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_022.sch
```

## Conventions, and the traps behind them

**A label or a device pin connects only when it sits EXACTLY on the wire point.**
Off by one grid step and xschem silently invents `#net<N>`: the netlist still
builds, with every device present and every connection wrong. The generator
therefore auto-splits each net's polylines at every node of that net, asserts
that every device pin lands on a node of the net it is declared to be on, and
refuses any point that would short two nets. `check_netlist.py` is the
independent confirmation.

**Name every top-level net.** An unlabelled bench net still netlists — as
`#net<N>` — which is how a bench silently stops probing what its `.control`
block thinks it probes.

**n and p symbols mirror their D/S pins.** Read off the IHP symbols:

| | D | G | S | B |
|---|---|---|---|---|
| `sg13_*_pmos` | (20, +30) | (−20, 0) | (20, −30) | (20, 0) |
| `sg13_*_nmos` | (20, **−30**) | (−20, 0) | (20, **+30**) | (20, 0) |

This is also why swapping a p symbol for an n symbol at fixed wiring is never
just a rename: it re-labels which wire is the drain.

**`flip=1` mirrors about the vertical axis; `rot=1` maps (x,y) → (−y,x).**
Verified against the netlister, not assumed. Crossing wires do **not** connect
(no shared endpoint); `gnd.sym` with `lab=0` emits node `0`.

**Capacitors are ideal `devices/capa.sym`.** Sizing them as `cap_cmim` maps
farads to area and is a layout decision; drawing a MIM here would put an
un-verified area model between the schematic and the certified result.

**The bias reference lives in the testbench**, ahead of the `vflt` core-current
probe — exactly as the frozen bench has it, so S6 excludes the reference by
construction rather than by subtraction.
