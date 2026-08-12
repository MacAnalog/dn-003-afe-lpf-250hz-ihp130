# 2026-08-12 — For a ported topology, port the DRAWING too: the originating schematics transfer almost verbatim

KIND: journal entry | type: procedural | status: live

**The mistake.** This repo's cells are ports — the topology is carried forward
unchanged. The originating campaign's checkout already contains a properly drawn,
human-placed xschem schematic for each of them. I generated new ones from the
sizing JSON instead, and produced a machine grid of devices connected by
`lab_pin` labels with **zero routed wires** — correct, gate-passing, and not
reviewable. The originating drawing of the same cell is 168 lines with **107 wire
segments**.

**Why the port is nearly free.** The originating schematics instantiate the
*generic* `devices/pmos4.sym` / `nmos4.sym`, and those have pin geometry
**identical** to the IHP `sg13g2_pr` symbols:

| | D | G | S | B |
|---|---|---|---|---|
| p (`devices/pmos4` and `sg13_*_pmos`) | (20, +30) | (−20, 0) | (20, −30) | (20, 0) |
| n (`devices/nmos4` and `sg13_hv_nmos`) | (20, **−30**) | (−20, 0) | (20, **+30**) | (20, 0) |

So every wire endpoint stays valid across a symbol swap. **Keep every `N …` line
and every coordinate**; the port is only:

1. symbol path → `sg13g2_pr/sg13_{lv,hv}_{n,p}mos.sym`, per role;
2. add **`spiceprefix=X`** to every device instance — the IHP models are
   *subcircuits*, so they need `X<name> … <model>`, not the generic symbol's
   `M<name> …`;
3. `w` / `l` and the capacitor values from this repo's as-built netlist
   (`signoff/asbuilt/*.sp`), which differ from the originating sizing.

**Two hard requirements.**

* **Scrub before the file enters git.** The originating drawings carry device
  model names and title-block text that `scripts/lint.py`'s node-scrub check
  forbids outright — a hit is a build failure, not a style note. Run
  `python scripts/lint.py` and confirm node-scrub passes *before* reporting. The
  pattern list is in `scripts/lint.py`; never paste a source file in unscrubbed
  "to fix later".
* **There is no testbench to port.** Every schematic in that tree is a core cell
  (plus one bias cell); none contains a `.control` block, a source, or any bench
  element. The bench — balun ±0.5 so the source amplitude IS the differential
  input, the series `vflt` core-current probe, the bias reference ahead of that
  probe, the `.nodeset`, and the two `.control` blocks — is always new work here,
  and is what `signoff/schematic/lpf_tb_*.sch` carries.

**The general rule this is an instance of.** Before generating *any* artefact for
a ported design — schematic, symbol, build sheet, bench skeleton — grep the
originating checkout for it first. The failure mode is not that the generated
artefact is wrong; it is that it is unreviewable, and that a human-placed drawing
already existed. `scripts/gen_xschem.py` remains useful as a *fallback* for a
cell with no prior drawing, and as the connectivity reference to check a port
against.
