"""Yield: process/voltage/temperature corners and mismatch Monte Carlo.

Two different questions, reported separately because they fail differently.

**Corners** (`lab.corners`) are the GLOBAL axes -- process skew, 27 +- 40/125 C,
supply +-10 %.  Read the result against the reference baseline in the same
table and nothing else: corner yield is not one of S1-S8, and the frozen
reference itself does not survive this box, so a candidate's corner count is a
comparison, never a pass/fail.  The binding column here is the LOW supply, where
the stack runs out of headroom rather than out of gain -- which is why the
useful number alongside it is VDD_min (`lab.droop`), not a +-10 % verdict.

**Mismatch** (`lab.mc`) is the LOCAL axis and is the one that answers "yield" as
a fab would mean it: every device draws its own delvto/factuo/dw/dl from the
PDK's agauss expressions.  The headline is the all-pass fraction over ATTEMPTED
samples, so a non-converged sample can only lower it.  For this follower family
the figure of merit is sigma(dc_db): a source follower's passband gain is
self-referenced, so a threshold shift moves the operating point and barely moves
the gain -- a topology that loses that property shows it here first.

    uv run python experiments/021-publication-cell/robust.py <cell.json> [n_mc]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

from lab import corners as X                            # noqa: E402
from lab import droop as D                              # noqa: E402
from lab import mc as MC                                # noqa: E402
from lab.dut import Design, Dev                         # noqa: E402

OUT = HERE / "robust.json"


def design_from(d: dict) -> Design:
    return Design(topology=d["topology"],
                  devs={r: Dev(**g) for r, g in d["devs"].items()},
                  iref=d["iref"], vicm=d["vicm"], vocm=d["vocm"],
                  # lv_roles selects the device FLAVOUR and vmid is the
                  # inter-stage dc hint; a rebuild that drops either is a
                  # different circuit or a non-converging one, not a detail.
                  lv_roles=frozenset(d.get("lv_roles") or ()),
                  vmid=d.get("vmid"),
                  **{k: v * 1e-12 for k, v in d["caps_pf"].items()})


def one(name: str, d: Design, n_mc: int) -> dict:
    print(f"\n########## {name} ##########", flush=True)
    print("--- PVT corners (lab.corners.REDUCED, 22 points) ---", flush=True)
    cr = X.run(d, f"rb_cor_{name}")
    print(X.table(cr), flush=True)
    cs = X.summary(cr)

    print("\n--- supply droop: how far the rail can fall ---", flush=True)
    dr = D.sweep(d, f"rb_droop_{name}")
    vmin = D.vdd_min(dr)
    print(f"VDD_min (all spec lines still met) = {vmin}", flush=True)

    print(f"\n--- mismatch Monte Carlo, n = {n_mc} ---", flush=True)
    mr = MC.run(d, f"rb_mc_{name}", n=n_mc)
    print(MC.table(mr), flush=True)
    MC.histogram(mr, str(HERE / f"mc_{name}.png"), title=f"{name} — mismatch MC")

    return {"name": name, "corners": cs, "vdd_min": vmin, "mc": mr.summary()}


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    path = Path(sys.argv[1])
    n_mc = int(sys.argv[2]) if len(sys.argv) > 2 else 64
    payload = json.loads(path.read_text())
    rows = payload if isinstance(payload, list) else [payload]
    out = []
    for r in rows:
        d = design_from(r["design"] if "design" in r else r)
        out.append(one(r.get("name", path.stem), d, n_mc))
    OUT.write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
