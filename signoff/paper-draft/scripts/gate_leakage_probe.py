#!/usr/bin/env python
"""Is there any gate-leakage noise in this cell?  Measured on one device, not argued.

Section 5.2 of `validation.md` used to report the model's `igig` generator as
"gate-leakage shot noise", carrying 27 % of the IRN power.  That was a mislabelling, and
this script is the measurement that settles it.  Three facts, all read off one thick-oxide
device biased where this cell biases them:

1. **The gate current is zero.**  Not small -- zero.  The devices carry no gate current
   at any bias, because the PDK card sets every gate-current pre-factor to zero
   (`iginvlw = igovw = igovdw = 0`) for both thick-oxide flavours.  Direct tunnelling
   through 7.4 nm of oxide at half a volt is unmeasurable, and the model says so by
   construction rather than by arithmetic.
2. **The model's real gate-leakage noise generators are `igs` and `igd`, and both are
   identically zero**, which follows from (1): their PSDs are `2q*I_gs` and `2q*I_gd`.
3. **`igig` is the channel thermal noise.**  The model splits the channel by its
   correlation `c` with the induced gate noise: `idid` carries `(1 - c^2)*S_id` and the
   remaining `c^2*S_id` is injected drain-to-source through an internal noise node under
   the name `igig`.  Added back together they come to `2*q*I_D` -- the full weak-inversion
   shot noise -- while `idid` alone comes to about 0.7 of it.

The test is deliberately a SINGLE device with a resistive load, not this cell: the point
is that the result belongs to the device model and the PDK card, so nothing about the
topology, the transimpedance solve or the bench can be blamed for it.

Needs a live simulator (`LPF_NGSPICE=... ` or the docker lane); runs in the repo venv.

    .venv/bin/python signoff/paper-draft/scripts/gate_leakage_probe.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from lab import config as C          # noqa: E402
from lab import ngspice              # noqa: E402
from lab.raw import read_raw         # noqa: E402

Q_E = 1.602176634e-19
K_B = 1.380649e-23

# The bias this cell actually uses: a long-L thick-oxide n-channel device deep in weak
# inversion, a few nA, with a load big enough that its own noise does not dominate.
W, L = 5e-06, 8e-06
VGS, VDD, RLOAD, FNOISE = 0.46, 1.0, 100e6, 10.0

DECK = f""".title gate-leakage probe -- one thick-oxide device
.lib {C.MOS_LIB_HV} mos_tt
vg g 0 dc {VGS} ac 1
vdd dd 0 {VDD}
rd dd d {RLOAD}
x1 d g 0 0 sg13_hv_nmos w={W} l={L} ng=1 m=1
.control
save all @n.x1.nsg13_hv_nmos[ids] @n.x1.nsg13_hv_nmos[gm] @n.x1.nsg13_hv_nmos[gds]
op
write op.raw
noise v(d) vg lin 1 {FNOISE} {FNOISE} 1
setplot noise1
write sim.raw all
.endc
.end
"""


def _vec(plots, name: str) -> float:
    """First (only) sample of a vector.

    Matched case-insensitively and through the wrapper the rawfile puts round a typed
    vector: an operating-point current comes back as `i(@inst[ids])`, not `@inst[ids]`."""
    want = {name.lower(), f"i({name.lower()})", f"v({name.lower()})"}
    for p in plots:
        for k, v in p.vectors.items():
            if k.lower() in want:
                return float(v[0].real)
    raise KeyError(f"{name} not in {[k for p in plots for k in p.vectors]}")


def main() -> int:
    dev = "n.x1.nsg13_hv_nmos"
    rundir = ngspice.run(DECK, "gate_leakage_probe")
    op = read_raw(rundir / "op.raw")
    nz = read_raw(rundir / "sim.raw")

    ig = abs(_vec(op, "i(vg)"))
    idd = abs(_vec(op, f"@{dev}[ids]"))
    gm = abs(_vec(op, f"@{dev}[gm]"))
    gds = abs(_vec(op, f"@{dev}[gds]"))

    out = {g: _vec(nz, f"onoise_{dev}_{g}") for g in
           ("idid", "igig", "igs", "igd", "flicker")}
    # The load sets the transimpedance; the device's own g_ds is in parallel with it.
    z = 1.0 / (gds + 1.0 / RLOAD)
    si_chan = (out["idid"] ** 2 + out["igig"] ** 2) / z ** 2
    si_idid = out["idid"] ** 2 / z ** 2
    shot = 2 * Q_E * idd

    print(f"  device            sg13_hv_nmos  W/L = {W * 1e6:g}/{L * 1e6:g} um")
    print(f"  I_D               {idd * 1e9:.3f} nA      gm {gm * 1e9:.3f} nS"
          f"      Z_T {z / 1e6:.2f} MOhm")
    print(f"  GATE CURRENT      {ig:.3e} A")
    print(f"  igs, igd          {out['igs']:.3e}, {out['igd']:.3e} V/rtHz")
    print(f"  idid, igig        {out['idid']:.4e}, {out['igig']:.4e} V/rtHz")
    print(f"  (idid+igig)/2qI_D {si_chan / shot:.4f}"
          f"      idid alone {si_idid / shot:.4f}")
    print(f"  c_igid            {(1 - si_idid / si_chan) ** 0.5:.4f}")
    print(f"  channel / 4kT.gm  {si_chan / (4 * K_B * 300.15 * gm):.4f}  = n/2")

    bad = []
    if ig != 0.0:
        bad.append(f"gate current is {ig:.3e} A, expected exactly 0")
    for g in ("igs", "igd"):
        if out[g] != 0.0:
            bad.append(f"{g} is {out[g]:.3e}, expected exactly 0 -- "
                       "the model's gate-leakage noise is supposed to be off")
    if not 0.95 <= si_chan / shot <= 1.05:
        bad.append(f"idid+igig is {si_chan / shot:.3f} x 2qI_D, expected 1 +/- 5 % -- "
                   "the two are supposed to be one channel generator")
    if si_idid / shot > 0.95:
        bad.append(f"idid alone is {si_idid / shot:.3f} x 2qI_D -- if it is already the "
                   "whole shot noise then igig is something else after all")
    for b in bad:
        print(f"  FAIL: {b}")
    print("  gate leakage: none, and igig is the channel" if not bad else "  PROBE FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
