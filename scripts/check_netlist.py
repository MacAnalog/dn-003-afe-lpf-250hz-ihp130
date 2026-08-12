"""GATE 1 -- the drawing netlists to the as-built deck, device for device.

`signoff/verify.py` proves the stronger, final claim (the drawing *simulates* to
the certified scorecard).  This proves the structural one underneath it, which
is what makes a drawing bug legible instead of just numerically loud: same
instance set, same model per instance, same w/l/ng/m and cap values, and the
same connectivity under a net bijection checked in BOTH directions, with the
interface nets pinned to identity.

    uv run python signoff/schematic/check_netlist.py

Comparison is canonical, not textual: the deck builder and xschem's netlister
order lines differently, spell `xm2` vs `Xm2`, and xschem appends `m=1` to the
capacitor cards.  None of that is a difference in the circuit.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASB = HERE.parent / "asbuilt"
IMAGE = "spicexplorer-spice-base:local"
IFACE = {"vinp", "vinn", "voutp", "voutn", "vbn", "vbp", "vdd", "vdd_top",
         "sig", "vcm", "0"}
# ngspice: BOTH `M` and `m` mean milli; only MEG is mega.  A table that maps a
# bare M to 1e6 silently accepts a 1e9x error, so it is spelled out here.
SUF = {"t": 1e12, "g": 1e9, "meg": 1e6, "k": 1e3, "m": 1e-3, "u": 1e-6,
       "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18}


def num(tok: str) -> float:
    t = tok.strip().lower()
    m = re.match(r"^([-+0-9.eE]+)\s*([a-z]*)$", t)
    if not m:
        return float("nan")
    v, suf = m.group(1), m.group(2)
    try:
        x = float(v)
    except ValueError:
        return float("nan")
    for k in ("meg", "t", "g", "k", "m", "u", "n", "p", "f", "a"):
        if suf.startswith(k):
            return x * SUF[k]
    return x


def parse(text: str, sub: str | None = None) -> dict:
    """subckt (or top level) -> {inst: (kind, model, nets, params)}."""
    if sub:
        m = re.search(rf"^\.subckt\s+{sub}\b(.*?)^\.ends", text, re.S | re.M)
        text = m.group(1) if m else ""
    else:                                    # top level: drop every subckt body
        text = re.sub(r"^\.subckt\b.*?^\.ends.*?$", "", text, flags=re.S | re.M)
    out = {}
    for raw in text.splitlines():
        s = raw.split("*")[0].strip()
        if not s or s.startswith((".", "*", "+")):
            continue
        t = s.split()
        nm = t[0].lower()
        if nm.startswith("x"):
            mdl = next((w for w in t[1:] if not re.match(r"^[\w.]+=", w)
                        and w != t[0] and w.lower() not in ("",)), None)
            # the model/subckt name is the last token that is not a k=v pair
            kv = [w for w in t[1:] if "=" in w]
            pos = [w for w in t[1:] if "=" not in w]
            mdl, nets = pos[-1], pos[:-1]
            p = {k.lower(): num(v) for k, v in (w.split("=", 1) for w in kv)}
            out[nm] = ("x", mdl.lower(), nets, p)
        elif nm.startswith("c"):
            out[nm] = ("c", "cap", t[1:3], {"c": num(t[3])})
        elif nm[0] in "vie":
            n = 4 if nm[0] == "e" else 2
            out[nm] = (nm[0], nm[0], t[1:1 + n],
                       {"v": num(t[1 + n]) if len(t) > 1 + n else 0.0})
    return out


def compare(a: dict, b: dict, what: str) -> list[str]:
    bad = []
    if set(a) != set(b):
        bad.append(f"{what}: instance set differs: "
                   f"only-drawing={sorted(set(a) - set(b))} "
                   f"only-asbuilt={sorted(set(b) - set(a))}")
        return bad
    fwd, rev = {}, {}
    for inst in sorted(a):
        ka, ma, na, pa = a[inst]
        kb, mb, nb, pb = b[inst]
        # the drawn cell is namespaced (`lpf_core_022`); the deck builder emits
        # the generic `lpf_core`.  Same subcircuit, and its body is compared
        # separately -- so this one rename is the only allowed alias.
        alias = {ma, mb} == {"lpf_core_022", "lpf_core"}
        if (ka, ma) != (kb, mb) and not alias:
            bad.append(f"{what}: {inst}: model {ma} vs {mb}")
            continue
        if len(na) != len(nb):
            bad.append(f"{what}: {inst}: {len(na)} vs {len(nb)} terminals")
            continue
        for x, y in zip(na, nb):
            x, y = x.lower(), y.lower()
            if (x in IFACE or y in IFACE) and x != y:
                bad.append(f"{what}: {inst}: interface net {x} vs {y}")
            if fwd.setdefault(x, y) != y or rev.setdefault(y, x) != x:
                bad.append(f"{what}: {inst}: net {x}<->{y} breaks the bijection "
                           f"({x}->{fwd.get(x)}, {y}->{rev.get(y)})")
        for k in sorted(set(pa) | set(pb)):
            va, vb = pa.get(k), pb.get(k)
            if va is None or vb is None:
                bad.append(f"{what}: {inst}: parameter {k} only on one side")
            elif abs(va - vb) > max(1e-30, abs(vb) * 1e-3):
                bad.append(f"{what}: {inst}: {k}={va} vs {vb}")
    return bad, fwd


def netlist(name: str) -> str:
    subprocess.run(["docker", "run", "--rm", "-v", f"{HERE}:/sch", "-w", "/sch",
                    IMAGE, "sh", "-lc",
                    f"xschem -n -s -q --rcfile /sch/xschemrc /sch/{name}.sch"],
                   check=True, capture_output=True, text=True)
    return (HERE / f"{name}.spice").read_text()


def main() -> int:
    bad: list[str] = []
    print("GATE 1 -- xschem netlist vs signoff/asbuilt, canonical compare\n")
    for cell, asb, sub in (("lpf_tb_022", "022-reuse-final_tb_acnoise",
                            ("lpf_core_022", "lpf_core")),
                           ("lpf_tb_022_thd", "022-reuse-final_tb_thd",
                            ("lpf_core_022", "lpf_core"))):
        drawn, built = netlist(cell), (ASB / f"{asb}.sp").read_text()
        for lvl, (sa, sb) in (("core", sub), ("bench", (None, None))):
            e, bij = compare(parse(drawn, sa), parse(built, sb),
                             f"{cell}/{lvl}")
            bad += e
            n = len(parse(drawn, sa))
            noniden = {k: v for k, v in bij.items() if k != v}
            print(f"  {cell:16s} {lvl:6s} {n:2d} instances  "
                  f"{'PASS' if not e else 'FAIL'}   "
                  f"net bijection: {len(bij)} nets, "
                  f"{'identity' if not noniden else noniden}")
    if bad:
        print("\n" + "\n".join(bad))
    print(f"\nGATE 1  drawing == as-built netlist : "
          f"{'PASS' if not bad else 'FAIL'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
