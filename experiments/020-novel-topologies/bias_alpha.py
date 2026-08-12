"""Does a constant-gm (beta-multiplier) reference buy yield in SG13G2?

The bench's reference is an ideal CURRENT source, and prior art says that is the
wrong ideal for a gm/C filter: in weak inversion gm = I/(n*U_T), so pinning the
current makes gm CTAT and fc walks with temperature anyway.  A beta-multiplier
delivers I = n*U_T*ln(K)/R, hence **gm = ln(K)/R** -- n and U_T cancel, and gm
is set by a device ratio and one resistor.  That is a constant-GM reference,
which is `alpha = 1` in `lab.config.BIAS_ALPHA`'s I(T) = iref*(T/Tnom)^alpha.

This measures the ceiling, not a circuit: the shaped source is ideal, so it
carries none of a real reference's own process spread.  For a beta-multiplier
that spread is dominated by the degeneration RESISTOR, because gm = ln(K)/R
passes R's process corner straight through to fc.  Read the result as "this is
the most a bias fix can buy"; a built reference lands between alpha = 0 and it.

    uv run python experiments/020-novel-topologies/bias_alpha.py            # all
    uv run python experiments/020-novel-topologies/bias_alpha.py 0.76 G-135 # one

`alpha` must be set in the ENVIRONMENT before `lab.config` is imported, so each
value runs as its own subprocess.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "bias_alpha.json"

ALPHAS = (0.0, 0.76, 1.0)
CELLS = ("reference", "G-135", "gb12-175")


def _child(alpha: float, cell: str) -> dict:
    """Run one (alpha, cell) corner sweep -- executed in the subprocess."""
    sys.path.insert(0, str(REPO))
    from lab import config as C
    from lab import corners as X

    assert abs(C.BIAS_ALPHA - alpha) < 1e-9, "env did not reach lab.config"

    import importlib.util
    spec = importlib.util.spec_from_file_location("s020", HERE / "state.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    design = mod.load()[cell]

    slug = f"a{alpha:g}".replace(".", "p")
    res = X.run(design, f"bias_{slug}_{cell.replace('-', '')}")
    s = X.summary(res)
    def col(key):
        vals = [r.get(key) for r in res if r.measured]
        return [v for v in vals if v == v]          # drop NaN

    fc, irn = col("fc_hz"), col("irn_uv")
    return {
        "alpha": alpha, "cell": cell,
        "n": s["n_corners"], "clean": s["n_pass"],
        "nonconv": s["n_nonconv"] + s["n_error"],
        "fc_lo": min(fc) if fc else None, "fc_hi": max(fc) if fc else None,
        "fc_span": (max(fc) / min(fc)) if fc else None,
        "irn_lo": min(irn) if irn else None, "irn_hi": max(irn) if irn else None,
    }


def table(rows: list[dict]) -> str:
    head = ("| cell | bias I(T) | corners clean | fc lo | fc hi | **fc span** "
            "| IRN lo | IRN hi | non-conv |\n" + "|" + "---|" * 9)
    name = {0.0: "constant **current** (today)",
            0.76: "I ∝ T^0.76 (fc-flattest)",
            1.0: "constant **gm** (β-multiplier / PTAT)"}
    out = [head]
    for r in sorted(rows, key=lambda r: (CELLS.index(r["cell"]), r["alpha"])):
        out.append(
            f"| {r['cell']} | {name.get(r['alpha'], r['alpha'])} | "
            f"**{r['clean']}/{r['n']}** | {r['fc_lo']:.1f} | {r['fc_hi']:.1f} | "
            f"**×{r['fc_span']:.3f}** | {r['irn_lo']:.1f} | {r['irn_hi']:.1f} | "
            f"{r['nonconv']} |")
    return "\n".join(out)


if __name__ == "__main__":
    if os.environ.get("_BIAS_CHILD"):
        a, cell = float(sys.argv[1]), sys.argv[2]
        print("@@" + json.dumps(_child(a, cell)))
        raise SystemExit(0)

    alphas = [float(sys.argv[1])] if len(sys.argv) > 1 else list(ALPHAS)
    cells = sys.argv[2:] or list(CELLS)
    rows = []
    for cell in cells:
        for a in alphas:
            env = dict(os.environ, LPF_BIAS_ALPHA=f"{a:g}", _BIAS_CHILD="1")
            print(f"  running {cell} at alpha={a:g} ...", flush=True)
            p = subprocess.run([sys.executable, __file__, f"{a:g}", cell],
                               env=env, capture_output=True, text=True)
            hit = [l for l in p.stdout.splitlines() if l.startswith("@@")]
            if not hit:
                print(p.stdout[-2000:], p.stderr[-2000:])
                raise SystemExit(f"{cell} alpha={a}: child produced no result")
            rows.append(json.loads(hit[-1][2:]))
    OUT.write_text(json.dumps(rows, indent=2))
    print("\n" + table(rows))
