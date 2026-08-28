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

import argparse
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

from lab import config as C, corners as K, metrics as M, ngspice as ng, raw as R  # noqa: E402
from lab.deck import _bias, _core, _libs, _stim_ac  # noqa: E402
from lab.dut import INSTANCES, Design, Dev, subckt  # noqa: E402
from lab.oppoint import PARAMS  # noqa: E402
from lab.mc import _seeded  # noqa: E402
from lab.parallel import batch, jobs  # noqa: E402

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


def node_saves(index: dict) -> list[str]:
    """`save` entries for every net a device terminal touches.

    `save all` covers the TOP-LEVEL nodes only -- a subcircuit's internal nets have to
    be named, and an unsaved one is silently absent rather than an error.  These are
    what `parse_nodes` reads, and what lets a probe deck reproduce a device's bias from
    absolute node voltages instead of from a sign-folded `vgs`/`vds`.
    """
    top = {"vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd", "0"}
    nets = {n for m in index.values() for n in m["nets"].values()}
    return ([f"v({n})" for n in sorted(nets & top) if n != "0"]
            + [f"v(xdut.{n})" for n in sorted(nets - top)])


def build_deck(d: Design, c: K.Corner = K.NOMINAL) -> tuple[str, dict]:
    saves, prints, index = op_probe_lines(d)
    saves = saves + node_saves(index)
    deck = f""".title lpf {d.topology} -- reviewer analysis bench (op + ac + noise)
{_libs(c.process, d)}
{subckt(d)}
{_core(d, vdd=c.vdd)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {c.temp}
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


def build_acnoise_deck(d: Design, c: K.Corner = K.NOMINAL) -> str:
    """AC + noise WITH the per-device noise summary.  Kept separate from the op deck because
    an explicit `save` starves the noise analysis (`lab.deck` documents the trap)."""
    return f""".title lpf {d.topology} -- ac + noise with per-device contributions
{_libs(c.process, d)}
{subckt(d)}
{_core(d, vdd=c.vdd)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {c.temp}
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


def parse_nodes(rundir: Path, index: dict) -> dict:
    """Every node's dc voltage at the operating point, by ABSOLUTE name.

    The PSP op-vars give each device a `vgs`/`vds`, but for a p-channel those are
    reported in the model's own source-referenced convention, and rebuilding a device's
    bias from them means re-deriving that convention correctly for every flavour.  The
    node voltages carry no convention at all: a probe deck that pins d/g/s/b to these
    numbers reproduces the device's operating point whatever the model does internally.
    """
    plot = R.pick(ng.plots(rundir), "op")
    # `save all` on an OSDI model also dumps every Verilog-A internal node
    # (`xm0.nsg13_hv_pmos#int1`, ...).  Keep only the nets a device terminal names --
    # the rest is model plumbing, and storing it would triple the record for nothing.
    want = {n for m in index.values() for n in m["nets"].values()} - {"0"}
    out = {}
    for name in plot.vectors:
        low = name.lower()
        if not (low.startswith("v(") and low.endswith(")")) or "@" in low:
            continue                      # `v(@inst[param])` is an op-var, not a node
        net = low[2:-1].split("xdut.")[-1]
        if net in want:
            out[net] = float(np.real(np.asarray(plot[name])).ravel()[0])
    missing = want - set(out)
    if missing:
        raise ValueError(f"node voltages missing from the op plot: {sorted(missing)}")
    return out


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


def dut_design(label: str) -> tuple[Design, str, object]:
    """The `Design` for one DUT label, with the override already applied."""
    cell, override = DUTS[label]
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
    return d, cell, override


def extract(label: str, c: K.Corner = K.NOMINAL, *, tag: str | None = None,
            seed: int | None = None) -> dict:
    """One DUT at one PVT point: op + ac + noise, as the record every analysis reads.

    `c = NOMINAL` reproduces the nominal deck byte-for-byte, so the four committed
    analyses are unaffected by the corner axis existing.
    """
    d, cell, override = dut_design(label)
    tag = tag or label
    deck, index = build_deck(d, c)
    if seed is not None:
        deck = _seeded(deck, seed)
    rd = ng.run(deck, f"rev_op_{tag}")
    ops = parse_op(rd, index)
    nodes = parse_nodes(rd, index)

    acn = build_acnoise_deck(d, c)
    plots = ng.plots(ng.run(_seeded(acn, seed) if seed is not None else acn,
                            f"rev_acn_{tag}"))
    f, h = R.diff_tf(R.pick(plots, "ac"), C.OUT_P, C.OUT_N)
    score = M.score_plots(plots, d)
    return {
        "label": label,
        "cell": cell,
        "dut": {"LUMPED": "post-layout: schematic devices + extracted Cext",
                None: "schematic"}.get(override, "post-layout kpex CC"),
        "corner": c.as_dict(),
        "bias_alpha": C.BIAS_ALPHA,
        "seed": seed,
        "op": ops,
        "nodes": nodes,
        "ac": {"f": f.tolist(), "re": h.real.tolist(), "im": h.imag.tolist()},
        "noise": parse_noise(plots),
        "scorecard": {k: (None if v is None else float(v))
                      for k, v in score.values.items()},
        "caps_f": {n: d.cap(n) for n in ("c1_a", "c2_a", "c1_b", "c2_b")},
    }


def _line(rec: dict, what: str) -> str:
    s = rec["scorecard"]
    return (f"[{what}] {len(rec['op'])} instances, "
            f"{len(rec['noise']['contrib'])} noise vectors, "
            f"fc={s.get('fc_hz'):.3f} Hz, IRN={s.get('irn_uv'):.3f} uV, "
            f"ph_max={s.get('ph_max_deg'):.3f} deg")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for label in DUTS:
        rec = extract(label)
        (OUT / f"bench_{label}.json").write_text(json.dumps(rec))
        summary[label] = {"scorecard": rec["scorecard"],
                          "n_instances": len(rec["op"]),
                          "n_noise_vectors": len(rec["noise"]["contrib"])}
        print(_line(rec, label))
    (OUT / "bench_summary.json").write_text(json.dumps(summary, indent=1))


# --------------------------------------------------------------------- PVT --

#: The corner sets this script will sweep.  `reduced` is the 22-point screen the
#: delivered cells' certified scorecards were measured on, so every analytical row
#: lands beside an existing scorecard row; `axes` is the 9-point one-axis-at-a-time
#: diagnostic, which is what separates a process shift from a headroom shift.
#: The window `H12-pdk-cap` is actually certified over, from `signoff/post-pvt/README.md`:
#: process at 27 C / 1.5 V, supply **1.40-1.65 V at 27 C**, temperature **0..+70 C at
#: 1.5 V**, with `LPF_BIAS_ALPHA=1.1` on the temperature rows.  Note the shape of that
#: claim: it is ONE AXIS AT A TIME, like `lab.corners.AXES`, not a box.  It is also
#: narrower than the harness default (which sweeps +-10 % of 1.5 V and -40..+125 C) --
#: every failing grid corner of the delivered cells contains 1.35 V or a sub-zero
#: temperature, so sweeping the harness box alone answers a question about a part
#: nobody is shipping.
CERT_VDDS = (1.40, 1.65)
CERT_TEMPS = (0.0, 70.0)
CERT_AXES: tuple[K.Corner, ...] = (
    (K.NOMINAL,)
    + tuple(K.Corner(p, C.TEMP_NOM, C.VDD) for p in K.PROCESSES if p != C.CORNER_NOM)
    + tuple(K.Corner(C.CORNER_NOM, C.TEMP_NOM, v) for v in CERT_VDDS)
    + tuple(K.Corner(C.CORNER_NOM, t, C.VDD) for t in CERT_TEMPS))

#: The CROSS PRODUCT of the same endpoints -- 45 points that were never certified.
#: Sweeping it asks whether the one-axis-at-a-time claim superposes.  It does not,
#: and that is a result rather than a failure: see the PVT section of `validation.md`.
CERT_BOX: tuple[K.Corner, ...] = K.grid(temps=(CERT_TEMPS[0], C.TEMP_NOM, CERT_TEMPS[1]),
                                        vdds=(CERT_VDDS[0], C.VDD, CERT_VDDS[1]))

SETS = {"reduced": K.REDUCED, "axes": K.AXES, "full": K.CORNERS,
        "cert-axes": CERT_AXES, "cert-box": CERT_BOX,
        "both": tuple(dict.fromkeys(K.REDUCED + K.AXES))}


def alpha_tag() -> str:
    """`LPF_BIAS_ALPHA` is part of a temperature measurement's identity.

    `alpha = 0` (constant reference current) makes `gm`, and therefore `fc`, CTAT;
    `alpha = 1.1` is the constant-gm shaping the delivered cells were certified with
    (experiment 023).  At 27 C the two are the same current, so the nominal bench is
    unaffected -- but every temperature corner differs, and a sweep that silently used
    the default would report an UNCOMPENSATED cell as if it were the delivered one.
    """
    return "" if not C.BIAS_ALPHA else f"_a{C.BIAS_ALPHA:g}".replace(".", "p")


def pvt(which: str = "both", label: str = "pre_mim", workers: int | None = None) -> None:
    """Extract one DUT over a corner set, one bench JSON per point.

    Only the analytical quantities need this: the poles, the per-biquad Q and the
    noise budget are functions of the operating point, so each corner needs its own
    `op` + per-generator noise extraction.  The scorecard columns come along free and
    are asserted against `lab.corners` scoring the same point.
    """
    cs = SETS[which]
    a = alpha_tag()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"PVT: {len(cs)} corners x {label}, bias alpha={C.BIAS_ALPHA:g}, "
          f"{workers or jobs()} workers")

    def one(c: K.Corner) -> dict:
        rec = extract(label, c, tag=f"pvt_{label}{a}_{c.slug}")
        (OUT / f"bench_pvt_{label}{a}_{c.slug}.json").write_text(json.dumps(rec))
        return rec

    recs = batch(list(cs), one, workers=workers)
    index, bad = [], []
    for c, r in zip(cs, recs):
        if isinstance(r, BaseException):
            bad.append((c, r))
            print(f"[{c.slug}] FAILED: {r!r}")
            continue
        index.append({"slug": c.slug, "corner": c.as_dict(),
                      "file": f"bench_pvt_{label}{a}_{c.slug}.json",
                      "scorecard": r["scorecard"]})
        print(_line(r, c.slug))
    (OUT / f"pvt_index_{label}{a}_{which}.json").write_text(json.dumps(
        {"dut": label, "set": which, "bias_alpha": C.BIAS_ALPHA,
         "n_ok": len(index), "n_failed": len(bad),
         "failed": [c.slug for c, _ in bad], "corners": index}, indent=1))
    print(f"\n{len(index)}/{len(cs)} corners extracted"
          + (f", {len(bad)} failed" if bad else ""))


def mc(n: int = 64, label: str = "pre_mim", workers: int | None = None) -> None:
    """One FULL extraction per mismatch draw, so the analytical pipeline runs unchanged.

    The alternative -- fitting a 4-pole rational to each sample's ac sweep -- is cheaper
    but ill-posed here: `tf_analysis.fit_poles_from_sim` documents that the (f0, Q) split
    of two nearly co-located pairs is weakly determined by the response, so a Q
    DISTRIBUTION built that way would mostly measure the fit's conditioning.  Extracting
    the operating point per draw and running the same pencil solve as every other number
    in this pack costs about two seconds a draw on a many-core host, which is cheap
    enough that the well-posed route is also the practical one.
    """
    corner = C.mismatch_corner(C.CORNER_NOM)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"MC: {n} draws x {label} at {corner} / {C.TEMP_NOM:g} C, "
          f"{workers or jobs()} workers")
    c = K.Corner(corner, C.TEMP_NOM, C.VDD)

    def one(seed: int) -> dict:
        rec = extract(label, c, tag=f"mc_{label}_s{seed:05d}", seed=seed)
        (OUT / f"bench_mc_{label}_s{seed:05d}.json").write_text(json.dumps(rec))
        return rec

    seeds = list(range(1, n + 1))
    recs = batch(seeds, one)
    index, bad = [], []
    for s, r in zip(seeds, recs):
        if isinstance(r, BaseException):
            bad.append(s)
            continue
        index.append({"seed": s, "corner": c.as_dict(),
                      "file": f"bench_mc_{label}_s{seed_name(s)}.json",
                      "scorecard": r["scorecard"]})
    (OUT / f"mc_index_{label}.json").write_text(json.dumps(
        {"dut": label, "corner": c.as_dict(), "n_ok": len(index), "n_failed": len(bad),
         "failed": bad, "draws": index}, indent=1))
    print(f"{len(index)}/{n} draws extracted" + (f", {len(bad)} failed" if bad else ""))


def seed_name(s: int) -> str:
    return f"{s:05d}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pvt", choices=sorted(SETS), default=None,
                    help="sweep a corner set instead of the four nominal DUTs")
    ap.add_argument("--dut", default="pre_mim", choices=sorted(DUTS),
                    help="which DUT to sweep over corners (default: the pre-layout "
                         "DUT of record)")
    ap.add_argument("--mc", type=int, default=None,
                    help="mismatch draws to extract instead of the nominal DUTs")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    if a.mc:
        mc(a.mc, a.dut, a.workers)
    elif a.pvt:
        pvt(a.pvt, a.dut, a.workers)
    else:
        main()
