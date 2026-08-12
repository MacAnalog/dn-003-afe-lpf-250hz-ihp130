"""Run an ngspice deck and hand back its rawfiles.

Two interchangeable lanes (see `lab.config.lane`):

* **docker** (default) -- `spicexplorer-spice-base:local`, which carries ngspice
  built with OSDI plus the IHP PDK model cards and the OpenVAF-compiled
  PSP103 / r3_cmc / mosvar OSDI objects.  IHP MOS devices *are* PSP 103.6
  Verilog-A compact models, so a stock ngspice with no `.osdi` loaded cannot
  simulate this PDK at all -- it reports `Unknown model type psp103va`.
* **native** -- set `LPF_NGSPICE=/path/to/ngspice` on a host whose `~/.spiceinit`
  loads those same OSDI objects and puts the PDK's `models/` on `sourcepath`.

Every run lands in its own directory under `lab.config.WORK` so runs are
reproducible after the fact and parallel batches never share a filename.
"""
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import time
from pathlib import Path

from . import config as C
from .raw import Plot, read_raw


class SimError(RuntimeError):
    """ngspice exited non-zero, or produced no usable rawfile."""


def deck_hash(text: str) -> str:
    """Stable 12-hex identity of a deck -- the ledger's provenance key."""
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def run(deck: str, tag: str, *, timeout: int = 1800, extra_files: dict | None = None) -> Path:
    """Write `deck` into WORK/<tag>/, simulate it, return the run directory.

    `deck` must contain its own `.control` block ending in `write <name>.raw`.
    `extra_files` maps relative filename -> text for anything the deck includes.
    """
    rundir = C.WORK / tag
    rundir.mkdir(parents=True, exist_ok=True)
    for stale in rundir.glob("*.raw"):
        stale.unlink()
    (rundir / "deck.sp").write_text(deck)
    for name, text in (extra_files or {}).items():
        (rundir / name).write_text(text)

    t0 = time.time()
    cmd = _cmd(rundir)
    proc = subprocess.run(cmd, cwd=rundir, capture_output=True, text=True, timeout=timeout)
    wall = time.time() - t0
    (rundir / "ngspice.out").write_text(proc.stdout + "\n---- stderr ----\n" + proc.stderr)
    (rundir / "wall.txt").write_text(f"{wall:.3f}\n")

    raws = sorted(rundir.glob("*.raw"))
    if proc.returncode != 0 and not raws:
        raise SimError(
            f"ngspice failed for {tag} (rc={proc.returncode})\n"
            f"cmd: {' '.join(shlex.quote(c) for c in cmd)}\n"
            f"{_tail(proc.stdout)}\n{_tail(proc.stderr)}"
        )
    if not raws:
        raise SimError(f"{tag}: ngspice wrote no rawfile.\n{_tail(proc.stdout)}")
    _check_convergence(rundir, proc.stdout)
    return rundir


def plots(rundir: Path, name: str = "sim.raw") -> list[Plot]:
    p = Path(rundir) / name
    if not p.exists():
        found = sorted(Path(rundir).glob("*.raw"))
        if not found:
            raise SimError(f"no rawfile in {rundir}")
        p = found[0]
    return read_raw(p)


def simulate(deck: str, tag: str, **kw) -> list[Plot]:
    """run() + plots() -- the common path."""
    return plots(run(deck, tag, **kw))


def wall_time(rundir: Path) -> float:
    try:
        return float((Path(rundir) / "wall.txt").read_text())
    except Exception:
        return float("nan")


# ------------------------------------------------------------------ internals

def _cmd(rundir: Path) -> list[str]:
    if C.lane() == "native":
        return [C.NGSPICE, "-b", "deck.sp"]
    return [
        C.DOCKER, "run", "--rm",
        "-v", f"{rundir}:/w", "-w", "/w",
        "-u", f"{os.getuid()}:{os.getgid()}",
        C.DOCKER_IMAGE, "ngspice", "-b", "deck.sp",
    ]


_FATAL = (
    "doAnalyses: iteration limit reached",
    "Transient solution failed",
    "singular matrix",
    "no such vector",
    "Unknown model type",
    "could not find a valid modelname",
)


def _check_convergence(rundir: Path, out: str) -> None:
    """Fail loudly on the errors ngspice reports without a non-zero exit code.

    ngspice happily returns 0 after a failed DC operating point, leaving a
    rawfile full of zeros.  A silent zero-filled result that scores as a PASS is
    the single most expensive failure mode in this harness, so it is checked
    here rather than trusted downstream.
    """
    bad = [line for line in out.splitlines() if any(f in line for f in _FATAL)]
    if bad:
        raise SimError(f"{rundir.name}: simulator error\n  " + "\n  ".join(bad[:8]))


def _tail(s: str, n: int = 40) -> str:
    lines = [ln for ln in s.splitlines() if ln.strip()]
    return "\n".join(lines[-n:])


def preflight() -> dict:
    """Cheap 'is the lane alive?' probe -- what `make doctor` reports."""
    info = {"lane": C.lane(), "pdk": C.PDK, "ok": False, "note": ""}
    deck = f""".title lane preflight
.lib {C.MOS_LIB_HV} {C.CORNER_NOM}
vd d 0 0.5
vg g 0 0.4
xm1 d g 0 0 sg13_hv_nmos w=10u l=1u ng=1 m=1
.control
op
write sim.raw
.endc
.end
"""
    try:
        pl = simulate(deck, "_preflight", timeout=300)
        info["ok"] = any("operating point" in p.name.lower() for p in pl)
        info["note"] = "; ".join(p.name for p in pl)
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        info["note"] = str(exc)[:400]
    return info


if __name__ == "__main__":  # `python -m lab.ngspice`
    import json
    print(json.dumps(preflight(), indent=2))
