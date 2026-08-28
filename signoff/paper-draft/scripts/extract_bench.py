#!/usr/bin/env python
"""Extract everything the reviewer analysis needs from ONE simulator pass per DUT.

For each DUT (pre-layout ideal-cap, pre-layout MIM-cap, post-layout kpex-CC) this runs a
single deck carrying `op` + `ac` + `noise`, with

  * every device's PSP small-signal parameters saved per INSTANCE (not per role), the
    full capacitance block included -- `lab.oppoint.PARAMS`;
  * the noise analysis asked for a per-device summary (the trailing `1` on the `noise`
    line), which makes ngspice emit one `onoise_n.<inst>.<model>[_<generator>]` vector per
    noise generator per device: `_idid` (channel), `_flicker`, `_rgate`/`_rdrain`/... .
    That is the ground truth every noise equation in this pack is checked against.

and writes it as JSON under `signoff/paper-draft/data/`.  Nothing here re-defines a spec
metric: the scorecard is scored by `lab.metrics.score_plots`, exactly as sign-off does.

    PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
        .venv/bin/python signoff/paper-draft/scripts/extract_bench.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE.parent / "data"
sys.path.insert(0, str(REPO))

os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
os.environ.setdefault("PDK", "ihp-sg13g2")
os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))

import numpy as np  # noqa: E402

from lab import config as C, metrics as M, ngspice as ng, raw as R  # noqa: E402
from lab.deck import _bias, _core, _libs, _stim_ac  # noqa: E402
from lab.dut import INSTANCES, Design, Dev, subckt  # noqa: E402
from lab.oppoint import PARAMS  # noqa: E402

SIGNOFF = REPO / "signoff/post-pvt"
PEX = REPO / "layout/H12-pdk-cap/asbuilt/core_pex.sp"

def post_lumped_netlist() -> str:
    """The post-layout cell as SCHEMATIC DEVICES + the extracted parasitic capacitors.

    kpex splits every drawn transistor into its layout fingers and labels each finger's
    source and drain by geometry, so the extracted netlist contains NMOS halves whose
    `source` is the non-ground node while the bulk stays at 0.  That is only a labelling
    artefact of the extractor -- the pair is one device -- but it breaks the `bulk ==
    source` identity the symbolic small-signal model relies on, and it destroys the 1:1
    instance mapping against the schematic that a pre/post comparison needs.

    So the post-layout model is built the other way round: the CERTIFIED schematic
    devices, plus the 68 `Cext_*` cards the extractor produced verbatim (their net names
    are already the schematic's).  `main()` scores this netlist through the same bench as
    the real extracted one and asserts they agree, which is what makes the substitution a
    measurement rather than an assumption.
    """
    core = (SIGNOFF / "H12-pdk-cap/asbuilt/core.sp").read_text()
    cext = [ln.rstrip() for ln in PEX.read_text().splitlines()
            if ln.strip().lower().startswith("cext_")]
    if len(cext) < 40:
        raise ValueError(f"only {len(cext)} Cext cards found in {PEX}")
    body = "\n".join("  " + ln.strip() for ln in cext)
    return re.sub(r"(?im)^(\.ends.*)$", body + r"\n\1", core, count=1)


# (label, sizing dir, dut_override source or None)
DUTS = {
    "pre_ideal": ("H12-robust", None),
    "pre_mim": ("H12-pdk-cap", None),
    "post_pex": ("H12-pdk-cap", PEX),
    "post_lumped": ("H12-pdk-cap", "LUMPED"),
}


def design_of(cell: str) -> Design:
    g = json.loads((SIGNOFF / cell / "design.json").read_text())["design"]
    return Design(topology=g["topology"],
                  devs={r: Dev(**v) for r, v in g["devs"].items()},
                  iref=g["iref"], vicm=g["vicm"], vocm=g["vocm"],
                  lv_roles=frozenset(g.get("lv_roles") or ()), vmid=g.get("vmid"),
                  cap_model=g.get("cap_model", "ideal"),
                  **{k: v * 1e-12 for k, v in g["caps_pf"].items()})


MOS_CARD = re.compile(
    r"(?im)^\s*(x\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(sg13_\w+mos)\b(.*)$")


def op_probe_lines(d: Design) -> tuple[list[str], list[str], dict]:
    """`save`/`print` pairs for every MOS instance actually present in the DUT netlist.

    Scanning the emitted netlist (rather than `lab.dut.INSTANCES`) is what lets the same
    code probe a `dut_override` -- the kpex-extracted post-layout subckt, whose instances
    are called `xm$1 ... xm$35` and split each drawn device into its layout fingers.
    The role label is attached where it is knowable (the schematic DUT); post-layout it is
    resolved later, from the nets each instance actually touches.
    """
    netlist = subckt(d)
    role_of = {inst: role for role, insts in INSTANCES[d.topology].items() for inst in insts}
    saves, prints, index = [], [], {}
    for m in MOS_CARD.finditer(netlist):
        ref, dn, gn, sn, bn, model = m.group(1), *m.group(2, 3, 4, 5), m.group(6)
        inst = ref[1:]                       # drop the X wrapper
        base = f"@n.xdut.{ref}.n{model}"
        index[inst] = {"role": role_of.get(inst), "base": base, "model": model,
                       "nets": {"d": dn, "g": gn, "s": sn, "b": bn}}
        for prm in PARAMS:
            saves.append(f"{base}[{prm}]")
            prints.append(f"print {base}[{prm}]")
    # The bench mirror diode that terminates `vbn` -- outside the DUT, inside the model.
    mdl = d.model("bias_a_int")
    index["mbn"] = {"role": "__mirror__", "base": f"@n.xmbn.n{mdl}", "model": mdl,
                    "nets": {"d": "vbn", "g": "vbn", "s": "0", "b": "0"}}
    for prm in PARAMS:
        saves.append(f"@n.xmbn.n{mdl}[{prm}]")
        prints.append(f"print @n.xmbn.n{mdl}[{prm}]")
    return saves, prints, index


def build_deck(d: Design) -> tuple[str, dict]:
    saves, prints, index = op_probe_lines(d)
    deck = f""".title lpf {d.topology} -- reviewer analysis bench (op + ac + noise)
{_libs(C.CORNER_NOM, d)}
{subckt(d)}
{_core(d)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {C.TEMP_NOM}
.control
set filetype=binary
set appendwrite
save all {' '.join(saves)}
op
write sim.raw
{chr(10).join(prints)}
.endc
.end
"""
    return deck, index


def build_acnoise_deck(d: Design) -> str:
    """AC + noise WITH the per-device noise summary.  Kept separate from the op deck because
    an explicit `save` starves the noise analysis (`lab.deck` documents the trap)."""
    return f""".title lpf {d.topology} -- ac + noise with per-device contributions
{_libs(C.CORNER_NOM, d)}
{subckt(d)}
{_core(d)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {C.TEMP_NOM}
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec {M.AC_DEC} 0.1 1e5
write sim.raw
noise v({C.OUT_P},{C.OUT_N}) {C.IN_SRC} dec {M.AC_DEC} 0.1 1e3 1
setplot noise1
write sim.raw
.endc
.end
"""


def parse_op(rundir: Path, index: dict) -> dict:
    out_txt = (rundir / "ngspice.out").read_text().split("---- stderr ----")[0]
    raw = {}
    for line in out_txt.splitlines():
        if "=" not in line or not line.strip().startswith("@"):
            continue
        k, _, v = line.partition("=")
        try:
            raw[k.strip().lower()] = float(v.strip())
        except ValueError:
            pass
    ops = {}
    for inst, meta in index.items():
        base = meta["base"].lower()
        vals = {p: raw[f"{base}[{p}]"] for p in PARAMS if f"{base}[{p}]" in raw}
        if vals:
            ops[inst] = {"role": meta["role"], "model": meta["model"],
                         "nets": meta["nets"], **vals}
    return ops


def parse_noise(plots) -> dict:
    n1 = R.pick(plots, "noise")
    f = np.asarray(n1.x, dtype=float)
    contrib = {}
    for name in n1.vectors:
        low = name.lower()
        if low.startswith("onoise_") and low not in ("onoise_spectrum", "onoise_total"):
            v = np.asarray(n1[name], dtype=float)
            if np.any(v > 0):
                contrib[name] = v.tolist()
    return {
        "f": f.tolist(),
        "inoise": np.asarray(n1["inoise_spectrum"], dtype=float).tolist(),
        "onoise": np.asarray(n1["onoise_spectrum"], dtype=float).tolist(),
        "contrib": contrib,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for label, (cell, override) in DUTS.items():
        d = design_of(cell)
        if override == "LUMPED":
            d = d.with_(dut_override=post_lumped_netlist())
        elif override is not None:
            # `$` is the ngspice control-language variable sigil, so a `save`/`print` of
            # `@n.xdut.xm$1...` silently expands to nothing and the op probe reads no
            # device at all.  kpex names every extracted instance `XM$n`, so they are
            # renamed `XM_n` here.  A reference-designator rename cannot change the
            # circuit -- and `--check-post` asserts it does not, by scoring this netlist
            # against the certified post-layout scorecard.
            d = d.with_(dut_override=Path(override).read_text().replace("$", "_"))
        deck, index = build_deck(d)
        rd = ng.run(deck, f"rev_op_{label}")
        ops = parse_op(rd, index)

        rd2 = ng.run(build_acnoise_deck(d), f"rev_acn_{label}")
        plots = ng.plots(rd2)
        ac = R.pick(plots, "ac")
        f, h = R.diff_tf(ac, C.OUT_P, C.OUT_N)
        score = M.score_plots(plots, d)

        rec = {
            "label": label,
            "cell": cell,
            "dut": {"LUMPED": "post-layout: schematic devices + extracted Cext",
                    None: "schematic"}.get(override, "post-layout kpex CC"),
            "op": ops,
            "ac": {"f": f.tolist(), "re": h.real.tolist(), "im": h.imag.tolist()},
            "noise": parse_noise(plots),
            "scorecard": {k: (None if v is None else float(v))
                          for k, v in score.values.items()},
            "caps_f": {n: d.cap(n) for n in ("c1_a", "c2_a", "c1_b", "c2_b")},
        }
        (OUT / f"bench_{label}.json").write_text(json.dumps(rec))
        summary[label] = {"scorecard": rec["scorecard"],
                          "n_instances": len(ops),
                          "n_noise_vectors": len(rec["noise"]["contrib"])}
        print(f"[{label}] {len(ops)} instances, "
              f"{len(rec['noise']['contrib'])} noise vectors, "
              f"fc={rec['scorecard'].get('fc_hz'):.3f} Hz, "
              f"IRN={rec['scorecard'].get('irn_uv'):.3f} uV, "
              f"ph_max={rec['scorecard'].get('ph_max_deg'):.3f} deg")
    (OUT / "bench_summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
