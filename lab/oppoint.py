"""Operating-point probe: what every device is actually doing.

This is the sizing instrument.  A scorecard tells you the filter is wrong; an
op table tells you *which device* is wrong and in which direction.  Almost every
failure in this design is one of three things, and all three are visible here
and invisible in an ac sweep:

* a device out of saturation (|Vds| below ~3-4 kT/q) -- its gds couples nodes
  that the topology assumes are isolated;
* a branch current that is not the integer multiple of `iref` the design
  intends -- a mirror-ratio or ladder-equilibrium error;
* a device that has left weak inversion (gm/ID well under the ~25-28 limit) --
  its gm no longer scales with current, so the pole equations stop holding.

Device parameters are addressed as ``@n.<inst>.n<model>[param]``.  They must be
named in a ``save`` BEFORE the analysis or they read back as a constant, and the
instance path has to include the DUT subckt instance (``xdut``).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config as C
from . import ngspice as ng
from .deck import _bias, _core, _libs, _stim_ac
from .dut import INSTANCES, Design, model_of, subckt

# What we pull per device.  `vdsat` is PSP's saturation voltage; the region call
# below compares |Vds| against it plus a weak-inversion floor.
PARAMS = ("ids", "gm", "gmb", "gds", "vgs", "vds", "vth", "cgg")

# Below ~4 kT/q a subthreshold device is not really saturated whatever the model
# reports, because its drain current still depends on Vds through DIBL.
VDS_FLOOR = 0.104          # 4 * kT/q at 300 K


@dataclass
class DevOp:
    role: str
    inst: str
    model: str
    vals: dict

    @property
    def id_na(self) -> float:
        return abs(self.vals.get("ids", float("nan"))) * 1e9

    @property
    def gm_ns(self) -> float:
        return abs(self.vals.get("gm", float("nan"))) * 1e9

    @property
    def gm_id(self) -> float:
        i = abs(self.vals.get("ids", 0.0))
        return abs(self.vals.get("gm", 0.0)) / i if i else float("nan")

    @property
    def gm_gds(self) -> float:
        g = abs(self.vals.get("gds", 0.0))
        return abs(self.vals.get("gm", 0.0)) / g if g else float("inf")

    @property
    def vds(self) -> float:
        return abs(self.vals.get("vds", float("nan")))

    @property
    def saturated(self) -> bool:
        """PSP103's OSDI build exposes no `vdsat`, so saturation is judged the
        way weak inversion actually behaves: a subthreshold device is saturated
        once |Vds| clears a few kT/q, and its gm/gds says whether that is
        really true.  A device at gm/gds of order 1 is in triode however its
        |Vds| reads."""
        return self.vds >= VDS_FLOOR and self.gm_gds >= 50

    @property
    def region(self) -> str:
        if not self.saturated:
            return "TRIODE"
        return "sat/weak" if self.gm_id > 20 else "sat/mod"


def probe(d: Design, tag: str, *, corner: str = C.CORNER_NOM,
          temp: float = C.TEMP_NOM, vdd: float | None = None) -> tuple[dict, dict]:
    """Simulate the dc operating point; return ({role: DevOp}, {net: volts}).

    `vdd` overrides the nominal supply for this deck only (see `lab.deck._core`)
    -- it is what makes a supply-droop sweep able to attribute a failure to the
    device that left saturation.  `None` = `lab.config.VDD`.
    """
    roles = INSTANCES[d.topology]
    saves, prints = [], []
    for role, insts in roles.items():
        inst = insts[0]                       # P side is representative
        base = f"@n.xdut.x{inst}.n{model_of(d.topology, role)}"
        for p in PARAMS:
            saves.append(f"{base}[{p}]")
            prints.append(f'print {base}[{p}]')
    nets = ["voutp", "voutn"] + [f"xdut.{n}" for n in ("vout_1", "vout_2", "net1",
                                                       "net2", "net3", "net4")]
    # An explicit `save` keeps ONLY what it lists -- node voltages and branch
    # currents included.  Omit them and every net reads back as
    # "vector ... is not available or has zero length".
    saves += [f"v({n})" for n in nets] + [f"i({C.CORE_PROBE})", f"i({C.SUPPLY_PROBE})"]
    prints += [f"print v({n})" for n in nets]
    prints += [f"print i({C.CORE_PROBE}) i({C.SUPPLY_PROBE})"]

    deck = f""".title lpf {d.topology} -- operating point probe
{_libs(corner)}
{subckt(d)}
{_core(d, vdd=vdd)}
{_bias(d)}
{_stim_ac(d.vicm)}
.temp {temp}
.control
set filetype=binary
save {' '.join(saves)}
op
write sim.raw
{chr(10).join(prints)}
.endc
.end
"""
    rundir = ng.run(deck, tag)
    out = (rundir / "ngspice.out").read_text().split("---- stderr ----")[0]

    raw: dict = {}
    volts: dict = {}
    for line in out.splitlines():
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        try:
            f = float(val)
        except ValueError:
            continue
        if key.startswith("v(") or key.startswith("i("):
            volts[key] = f
        elif key.startswith("@"):
            raw[key] = f

    ops = {}
    for role, insts in roles.items():
        inst = insts[0]
        base = f"@n.xdut.x{inst}.n{model_of(d.topology, role)}"
        vals = {p: raw[f"{base}[{p}]"] for p in PARAMS if f"{base}[{p}]" in raw}
        ops[role] = DevOp(role, inst, model_of(d.topology, role), vals)
    return ops, volts


def table(ops: dict, volts: dict, d: Design | None = None,
          vdd: float | None = None) -> str:
    """Markdown build/bias sheet -- the table that goes in a scorecard."""
    v_supply = C.VDD if vdd is None else vdd
    rows = ["| role | inst | type | ID (nA) | gm (nS) | gm/ID | gm/gds | "
            "\\|Vds\\| (mV) | region |",
            "|---|---|---|---|---|---|---|---|---|"]
    for role, o in ops.items():
        rows.append(
            f"| `{role}` | {o.inst} | {o.model[-4:]} | {o.id_na:.3f} | {o.gm_ns:.2f} | "
            f"{o.gm_id:.1f} | {o.gm_gds:.0f} | {o.vds*1e3:.0f} | "
            f"{'**' + o.region + '**' if not o.saturated else o.region} |")
    lad = " → ".join(
        f"{n.split('.')[-1]} {volts.get(f'v({n})', float('nan'))*1e3:.0f}"
        for n in ("voutp", "xdut.net4", "xdut.vout_1", "xdut.net2")
        if f"v({n})" in volts)
    rows.append(f"\nDC ladder (mV): VDD {v_supply*1e3:.0f} → {lad} → 0")
    if "i(vflt)" in volts:
        i = abs(volts["i(vflt)"])
        rows.append(f"Core current **{i*1e9:.3f} nA** → **{i*v_supply*1e9:.3f} nW** "
                    f"@ {v_supply} V")
    if d is not None:
        rows.append(f"iref {d.iref*1e9:.3g} nA · vicm {d.vicm} V · "
                    f"C_total {d.total_cap()*1e12:.2f} pF")
    return "\n".join(rows)


def problems(ops: dict) -> list[str]:
    """Every device that is not doing what a subthreshold design assumes."""
    out = []
    for role, o in ops.items():
        if not o.saturated:
            out.append(f"{role} ({o.inst}) is not saturated: |Vds| {o.vds*1e3:.0f} mV "
                       f"(floor {VDS_FLOOR*1e3:.0f}), gm/gds {o.gm_gds:.0f}")
        elif o.gm_id < 18:
            out.append(f"{role} ({o.inst}) has left weak inversion: "
                       f"gm/ID {o.gm_id:.1f}")
    return out
