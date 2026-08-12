"""Paths and knobs. Everything is overridable via environment variables.

The simulation lane is **ngspice + the open IHP SG13G2 PDK**.  Nothing in this
repo is under NDA: the PDK is Apache-2.0 and the simulator is GPL, so decks,
models and logs may all be committed and published verbatim.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- decks -----
# The reference deck (the IHP-native expert baseline testbench), vendored into
# the repo so experiments survive /tmp wipes.  Point elsewhere with:
#   export LPF_DECK_DIR=/path/to/deck
DECK_DIR = Path(os.environ.get("LPF_DECK_DIR", REPO / "decks" / "reference"))
DECK_TB = os.environ.get("LPF_DECK_TB", "lpf_tb.sp")

# ------------------------------------------------------------- work dirs ----
# Where simulation runs land (one subdir per tag).  NAMESPACED PER CHECKOUT
# (repo dir name + path hash) so parallel sessions in separate git worktrees can
# never clobber each other's runs -- the blast-radius rule (CLAUDE.md "Parallel
# sessions").  The ledger (runs/ledger.ndjson) is repo-relative, so per-worktree
# too.
_ns = f"{REPO.name}-{hashlib.sha1(str(REPO).encode()).hexdigest()[:6]}"
WORK = Path(os.environ.get("LPF_WORK", f"/tmp/lpf_work-{_ns}"))

# ---------------------------------------------------------------- lanes -----
# Two interchangeable ngspice lanes; `lab.ngspice` picks one at import time.
#
#   docker  (default, works anywhere Docker runs) -- the workspace's
#           `spicexplorer-spice-base` image carries ngspice built with OSDI plus
#           the IHP PDK models and the OpenVAF-compiled PSP103/r3_cmc OSDI
#           objects.  IHP MOS devices are PSP 103.6 compact models: they CANNOT
#           be simulated by a stock ngspice without those .osdi files.
#   native  set LPF_NGSPICE=/path/to/ngspice when the host itself has ngspice
#           with OSDI *and* a ~/.spiceinit that loads the IHP osdi objects and
#           puts the PDK model dir on `sourcepath`.
NGSPICE = os.environ.get("LPF_NGSPICE", "")          # non-empty => native lane
DOCKER_IMAGE = os.environ.get("LPF_DOCKER_IMAGE", "spicexplorer-spice-base:local")
DOCKER = os.environ.get("LPF_DOCKER", shutil.which("docker") or "docker")

def lane() -> str:
    """'native' if LPF_NGSPICE points at a binary, else 'docker'."""
    return "native" if NGSPICE else "docker"

# ------------------------------------------------------------------ PDK -----
PDK = "ihp-sg13g2"
# Model-card libraries, resolved by ngspice's `sourcepath` (set by .spiceinit
# inside the image).  Referenced by BARE NAME so decks stay host-independent.
MOS_LIB_LV = "cornerMOSlv.lib"      # sg13_lv_{n,p}mos  (1.5 V thin oxide)
MOS_LIB_HV = "cornerMOShv.lib"      # sg13_hv_{n,p}mos  (3.3 V thick oxide)
CAP_LIB = "cornerCAP.lib"           # cap_cmim (MIM), cap_rfcmim
RES_LIB = "cornerRES.lib"           # rsil, rhigh, rppd

# The process corners this repo scores.  `mos_tt` etc. are section names inside
# the corner libraries above.
CORNERS = ("mos_tt", "mos_ss", "mos_ff", "mos_sf", "mos_fs")
CORNER_NOM = "mos_tt"

# ------------------------------------------------------------------ DUT -----
# The DUT subckt name inside the deck.
DUT = "lpf_core"

# Differential input / output nets of the testbench.
IN_P, IN_N = "vinp", "vinn"
OUT_P, OUT_N = "voutp", "voutn"

# The differential stimulus source (the noise analysis' input reference, i.e.
# the ngspice equivalent of the original bench's `iprobe`).
IN_SRC = "vsig"

# Series probe carrying ONLY the filter core's supply current (S6).  The
# testbench's bias/reference current does not flow through it.
CORE_PROBE = "vflt"
# Series probe carrying the whole testbench supply current (report-only).
SUPPLY_PROBE = "vdd_meas"

# ------------------------------------------------------------- operating ----
VDD = float(os.environ.get("LPF_VDD", "1.5"))   # sg13g2 analog supply (hv devices)

# Input common mode.  Every stage is a p-type source follower, so each biquad
# shifts the common mode UP by one |Vgs| (~0.5 V at nano-amp bias).  The input
# CM is therefore placed low so the output CM lands mid-supply with headroom on
# both rails.  See doc/journal/all-p-followers.md.
VICM = float(os.environ.get("LPF_VICM", "0.25"))
VOCM = float(os.environ.get("LPF_VOCM", "1.25"))  # expected output CM (dc hint)
TEMP_NOM = 27.0
