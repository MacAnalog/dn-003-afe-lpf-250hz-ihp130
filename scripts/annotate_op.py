"""Stamp measured operating-point data onto a cell's core schematic.

For each MOS instance the drawn sheet gains a small text block with the
numbers a reviewer sizes by -- **Vds and Vdsat first**, then Id, Vgs, gm/ID,
gm/gds -- measured by `lab.oppoint.probe` (PSP103's own `vdss` op-var is the
Vdsat source) at the nominal corner, and a sheet-level banner naming the
condition.  The differential halves are electrically identical, so both
instances of a role carry the P-side probe numbers.

Annotations are TEXT elements only -- they cannot change the netlist, so both
identity gates are unaffected (and are re-run anyway after annotation).  The
script is idempotent: it owns every text element tagged `name=opannot*` and
replaces them wholesale on re-run.

    uv run python scripts/annotate_op.py <cell-dir> --core lpf_core_A
    uv run python scripts/annotate_op.py signoff/schematic --core lpf_core_022 \
        --design signoff/design/022-reuse-final.json

Also writes `<cell-dir>/op_<core>.md` (the full op table + DC ladder +
problems list) and `<cell-dir>/op_<core>.json` (machine-readable per-role
values).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lab import oppoint as OP           # noqa: E402
from lab.dut import INSTANCES, Design, Dev  # noqa: E402

MARK = "opannot"


def design_of(path: Path) -> Design:
    d = json.loads(path.read_text())
    if isinstance(d, list):
        d = d[0]
    g = d.get("design", d)
    return Design(topology=g["topology"],
                  devs={r: Dev(**v) for r, v in g["devs"].items()},
                  iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
                  lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
                  **{k: v * 1e-12 for k, v in g["caps_pf"].items()})


def _fmt(o: OP.DevOp) -> str:
    """The per-device block.  Vds/Vdsat lead -- the reviewer's first question."""
    return (f"Vds={o.vds * 1e3:.0f}m Vdsat={o.vdsat * 1e3:.0f}m\n"
            f"Id={o.id_na:.2f}nA Vgs={abs(o.vals.get('vgs', float('nan'))) * 1e3:.0f}m\n"
            f"gm/ID={o.gm_id:.1f} gm/gds={o.gm_gds:.0f} [{o.region}]")


def annotate(schdir: Path, core: str, design_json: Path, tag: str) -> None:
    d = design_of(design_json)
    ops, volts = OP.probe(d, tag)

    sch_path = schdir / f"{core}.sch"
    text = sch_path.read_text()
    # strip every annotation we own (idempotence) -- baked text AND live blocks
    text = re.sub(r"T \{[^{}]*\} -?\d+ -?\d+ \d \d [\d.]+ [\d.]+ "
                  r"\{name=" + MARK + r"[^{}]*\}\n?", "", text)
    text = re.sub(r"C \{sg13g2_pr/annotate_fet_params\.sym\} [^\n]*"
                  r"\{name=" + MARK + r"_live[^{}]*\}\n?", "", text)

    # instance -> sheet position (drawn names carry no x; spiceprefix adds it)
    pos: dict[str, tuple[int, int]] = {}
    for m in re.finditer(r"C \{sg13g2_pr/[^{}]*\} (-?\d+) (-?\d+) \d \d "
                         r"\{name=(m\w+)\s", text):
        pos[m.group(3)] = (int(m.group(1)), int(m.group(2)))

    add: list[str] = []
    for role, insts in INSTANCES[d.topology].items():
        if role not in ops:
            continue
        block = _fmt(ops[role])
        for k, inst in enumerate(insts):
            xy = pos.get(inst)
            if xy is None:
                continue
            # below-right of the symbol; device value text sits above-right
            add.append(f"T {{{block}}} {xy[0] + 30} {xy[1] + 44} 0 0 0.12 0.12 "
                       f"{{name={MARK}_{inst} layer=11}}")
            if k == 0:
                # The IHP PDK's own LIVE annotator, P half only (symmetry),
                # in a dedicated strip above the circuit so the blocks never
                # collide with devices.  Each block prints its @ref, so the
                # strip is self-labelling.  The text tcleval-s
                # `display_fet_params` against whatever op raw is loaded in
                # the xschem session -- run the *_gd bench (its deck saves
                # the PSP op-vars), load sim.raw, descend.
                add.append(f"C {{sg13g2_pr/annotate_fet_params.sym}} "
                           f"{40 + 250 * len([a for a in add if '_live_' in a])} "
                           f"-680 0 0 {{name={MARK}_live_{inst} ref={inst}}}")
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    banner = (f"OP ANNOTATION (generated {ts}) -- corner mos_tt, 27 C, VDD "
              f"1.5 V, measured by lab.oppoint (PSP vdss = Vdsat). P half "
              f"shown on both halves (differential symmetry). The empty "
              f"L-brackets are the IHP PDK live annotator "
              f"(annotate_fet_params): run the *_gd bench, load its sim.raw "
              f"in xschem, descend into the DUT, and they fill with the same "
              f"numbers plus ft.")
    add.append(f"T {{{banner}}} 40 96 0 0 0.16 0.16 {{name={MARK}_banner layer=11}}")
    sch_path.write_text(text.rstrip("\n") + "\n" + "\n".join(add) + "\n")

    (schdir / f"op_{core}.md").write_text(
        f"# Operating point -- `{core}`\n\n"
        f"Corner `mos_tt`, 27 C, VDD 1.5 V. Probed by `lab.oppoint` "
        f"(PSP103 `vdss` is Vdsat); P half shown, N half identical by "
        f"symmetry.\n\n" + OP.table(ops, volts, d) + "\n\n" +
        ("## Problems\n\n" + "\n".join(f"- {p}" for p in OP.problems(ops)) + "\n"
         if OP.problems(ops) else "All devices saturated and in weak inversion.\n"))
    (schdir / f"op_{core}.json").write_text(json.dumps(
        {role: {**o.vals, "region": o.region, "gm_id": o.gm_id,
                "gm_gds": o.gm_gds} for role, o in ops.items()}, indent=1))
    print(f"{core}: annotated {len(add) - 1} devices; op_{core}.md/.json written")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("celldir", type=Path)
    ap.add_argument("--core", required=True, help="core sheet stem, e.g. lpf_core_A")
    ap.add_argument("--design", type=Path, default=None,
                    help="sizing json (default: <celldir>/design.json)")
    a = ap.parse_args()
    annotate(a.celldir.resolve(), a.core,
             (a.design or a.celldir / "design.json").resolve(),
             tag=f"opann_{a.core[-4:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
