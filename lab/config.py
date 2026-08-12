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

# ------------------------------------------------------------- mismatch -----
# Every corner section in cornerMOS{lv,hv}.lib ships a `<corner>_mismatch` twin.
# The twin is the SAME process corner; what it adds is `sg13g2_moshv_mismatch.lib`
# + `sg13g2_moshv_mod_mismatch.lib`, which make every device instance draw its
# own local deviations at netlist-parse time:
#
#     delvto = agauss(0, A_VT  / sqrt(m*l*w*1e12), 1)     [V]
#     factuo = agauss(1, A_FACT/ sqrt(m*l*w*1e12), 1)     [-]  (mobility factor)
#     w      = agauss(w, 3 nm, 1)   l = agauss(l, 3 nm, 1)
#
# with the A-coefficients below (units: V*um and um, i.e. the sqrt argument is
# the gate area in um^2).  Read off
# ihp-sg13g2/libs.tech/ngspice/models/sg13g2_moshv_mismatch.lib and
# .../sg13g2_moshv_mod_mismatch.lib -- do not retype them from a paper.
MISMATCH_SUFFIX = "_mismatch"
CORNER_MM_NOM = CORNER_NOM + MISMATCH_SUFFIX
CORNERS_MM = tuple(c + MISMATCH_SUFFIX for c in CORNERS)

# Pelgrom-style coefficients of the hv (thick-oxide) pair, as the PDK states
# them.  Report-only: the simulator applies them, the harness never re-derives
# a sigma from them.
MISMATCH_A_VT = {"sg13_hv_nmos": 7.0e-3, "sg13_hv_pmos": 4.5e-3}      # V*um
MISMATCH_A_FACT = {"sg13_hv_nmos": 5.0e-3, "sg13_hv_pmos": 4.0e-3}    # um
MISMATCH_DW = MISMATCH_DL = 3e-9                                      # m, 1 sigma


def is_mismatch(corner: str) -> bool:
    """True if `corner` names a section that enables per-instance mismatch."""
    return corner.endswith(MISMATCH_SUFFIX)


def mismatch_corner(corner: str = CORNER_NOM) -> str:
    """The `_mismatch` twin of a corner section (idempotent)."""
    return corner if is_mismatch(corner) else corner + MISMATCH_SUFFIX


def base_corner(corner: str) -> str:
    """The plain process corner underneath a `_mismatch` section (idempotent)."""
    return corner[: -len(MISMATCH_SUFFIX)] if is_mismatch(corner) else corner


# The random draws happen while the NETLIST IS PARSED, before the `.control`
# block ever runs -- so `set rndseed=<n>` inside `.control` is too late and every
# seed yields the identical sample (measured: seeds 1/2/3 all gave
# 1.340305 nA / 1.515478 nA on a two-device probe).  The seed must be a netlist
# directive.  One process per sample; never an in-ngspice loop with `reset`
# (that renumbers the analysis plots -- doc/journal/ngspice-write-protocol.md).
def seed_directive(seed: int) -> str:
    return f".option seed={int(seed)}"

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

# AC sweep density used for SCORING (points per decade).  See lab.metrics.
AC_DEC = 50

# ------------------------------------------------------------------ bias ----
# The testbench reference is an IDEAL current source into a real mirror pair.
# `BIAS_ALPHA` shapes it with temperature:  I(T) = iref * (T/300.15)^alpha.
#
#   alpha = 0     constant CURRENT  -- the default, and what every number in
#                 this repo before 2026-08-11 was measured with.
#   alpha = 1     constant GM (a PTAT source).  In weak inversion gm = I/(n*U_T),
#                 so pinning the current makes gm CTAT; a gm/C filter's fc
#                 tracks gm, not I.  This is what a beta-multiplier delivers:
#                 I = n*U_T*ln(K)/R, hence gm = ln(K)/R -- n and U_T cancel and
#                 gm is set by a device RATIO and one resistor.
#   0 < alpha < 1 the compromise a curvature-corrected reference can hit.  The
#                 originating campaign measured fc (not gm) flattest near 0.76,
#                 because not every branch is fully subthreshold.
#
# It is an IDEAL shaping, so it bounds what a bias circuit could buy; it does
# NOT model a real reference's own process spread, which for a beta-multiplier
# is dominated by the degeneration resistor.
BIAS_ALPHA = float(os.environ.get("LPF_BIAS_ALPHA", "0"))
BIAS_TNOM_K = 300.15                      # 27 degC, the reference temperature
