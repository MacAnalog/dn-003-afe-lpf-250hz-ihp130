"""xschem netlisting, native or docker -- the schematic lane's `lab.ngspice`.

The two identity-gate scripts (`signoff/verify.py`, `scripts/draw_xschem.py`)
need `.sch -> .spice` netlisting.  Historically that shelled into the
`spicexplorer-spice-base` container; on the EDA server there is no docker
daemon but xschem is on the host, so this module mirrors the ngspice lane
switch: set

    export LPF_XSCHEM=$(which xschem)

to netlist natively.  The committed `xschemrc` files carry container paths
(`/usr/share/xschem`, `/opt/pdk`, `/sch`), so the native lane generates its own
rcfile per schematic directory under `lab.config.WORK`, resolving:

*   the system symbol library from the xschem binary's own install prefix,
*   the PDK symbols from `$PDK_ROOT/ihp-sg13g2/libs.tech/xschem`,
*   `netlist_dir` to the schematic directory itself (same contract as docker).
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

from . import config as C

XSCHEM = os.environ.get("LPF_XSCHEM", "")     # non-empty => native lane


def lane() -> str:
    return "native" if XSCHEM else "docker"


def _native_rcfile(schdir: Path) -> Path:
    prefix = Path(XSCHEM).resolve().parents[1]
    pdk = Path(os.environ.get("PDK_ROOT", "/opt/pdk")) / C.PDK / "libs.tech" / "xschem"
    rc = C.WORK / f"xschemrc_{hashlib.sha1(str(schdir).encode()).hexdigest()[:8]}"
    rc.parent.mkdir(parents=True, exist_ok=True)
    rc.write_text(
        f"set XSCHEM_LIBRARY_PATH {prefix}/share/xschem/xschem_library\n"
        f"append XSCHEM_LIBRARY_PATH :{pdk}\n"
        f"append XSCHEM_LIBRARY_PATH :{schdir}\n"
        f"set netlist_dir {schdir}\n")
    return rc


def netlist(schdir: Path, name: str, image: str | None = None) -> str:
    """Netlist `schdir/name.sch`; returns the .spice text it produced."""
    schdir = Path(schdir).resolve()
    if XSCHEM:
        subprocess.run(
            [XSCHEM, "-n", "-s", "-q", "--no_x",
             "--rcfile", str(_native_rcfile(schdir)), f"{name}.sch"],
            cwd=schdir, check=True, capture_output=True, text=True)
    else:
        subprocess.run(
            [C.DOCKER, "run", "--rm", "-v", f"{schdir}:/sch", "-w", "/sch",
             image or C.DOCKER_IMAGE,
             "sh", "-lc", f"xschem -n -s -q --rcfile /sch/xschemrc /sch/{name}.sch"],
            check=True, capture_output=True, text=True)
    return (schdir / f"{name}.spice").read_text()
