"""H12-pdk-cap post-layout bench for the layout flow: the block's frozen scorecard on the
PEX-extracted core (the ``_bench`` step of ../optimize_area.py, as a measure module).

Runs in the LPF venv with cwd = experiments/023-replica-bias (see flow.yaml). The request
(``spicexplorer_layout.measure_protocol``) carries ``pex_subckt`` — the prepared
``.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd`` (VSS→0, schematic MIM cards
re-inserted) — and the active PVT ``corner`` (or null). Returns every nominal scorecard
value (ph_max_deg, fc_hz, a1000_db, irn_uv, p_core_nw, idd_total_na, …) plus
``n_violations`` (S1..S7 spec violations at nominal).

Corner hooks (optional): ``corner.options.cap_corner`` → LPF_CAP_CORNER for the bench;
``corner.params.iref_scale`` → scales the design's iref (the areaopt --cap-corner /
iref-scale knobs). Layout itself is corner-independent.

Standalone:  echo '{"pex_subckt": "core_pex_cc.sp", "work_dir": "/tmp/x"}' | .venv/bin/python measure_post.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXP = REPO / "experiments/023-replica-bias"
SIZING = REPO / "signoff/post-pvt/H12-pdk-cap/design.json"


def measure(req: dict) -> dict[str, float]:
    os.environ.setdefault("PDK_ROOT", os.path.expanduser("~/local/pdks"))
    os.environ.setdefault("PDK", "ihp-sg13g2")
    os.environ.setdefault("LPF_NGSPICE", os.path.expanduser("~/local/bin/ngspice"))
    corner = req.get("corner") or {}
    cap_corner = (corner.get("options") or {}).get("cap_corner")
    if cap_corner:
        os.environ["LPF_CAP_CORNER"] = str(cap_corner)
    iref_scale = float((corner.get("params") or {}).get("iref_scale", 1.0))

    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    os.chdir(EXP)  # lab.* resolves its decks/models relative to the experiment dir
    from common import M, from_json  # noqa: E402  (the LPF harness)

    d = from_json(json.loads(SIZING.read_text())["design"])
    if iref_scale != 1.0:
        d = d.with_(iref=d.iref * iref_scale)
    d = d.with_(dut_override=Path(req["pex_subckt"]).read_text())
    tag = "layoutflow_" + Path(req.get("work_dir") or ".").name
    s = M.evaluate(d, tag, record=False)
    out: dict[str, float] = {}
    for k, v in dict(s.values).items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            pass
    out["n_violations"] = float(len(s.violations))
    return out


if __name__ == "__main__":
    from spicexplorer_layout.measure_protocol import serve

    raise SystemExit(serve(measure))
