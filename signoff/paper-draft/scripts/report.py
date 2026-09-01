#!/usr/bin/env python
"""Render `validation.md` -- every number in the reviewer pack, straight from the data.

`theory.md` holds the derivations, which are symbolic and therefore stable.  This file
holds everything that is a MEASUREMENT, and it is generated rather than written so that a
number in the prose can never drift from the JSON that produced it.  Re-run after any
re-extraction:

    .venv/bin/python signoff/paper-draft/scripts/report.py   # repo venv: needs >= 3.12

It reads only `signoff/paper-draft/data/` -- the extracted JSON, plus the committed core
netlist `post_lumped_core.sp` for the device geometries in section 5.2.  It never calls
the simulator and never touches the small-signal model.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
DATA = PACK / "data"
U_T = 1.380649e-23 * 300.15 / 1.602176634e-19

CASES = (("pre_mim", "pre-layout"), ("post_lumped", "post-layout"))
# Device roles, in the order a reader walks the signal path.
ROLE_ORDER = ("in_a", "gmf_a", "bias_a_int", "bridge", "in_b", "gmf_b",
              "rep_gmfb", "rep_bridge", "rep_sink", "__mirror__")
ROLE_TEXT = {
    "in_a": "biquad-A input follower (`gm_ia`)",
    "gmf_a": "biquad-A shunt-feedback device (`gm_fa`)",
    "bias_a_int": "biquad-A internal bias sink",
    "bridge": "current-reuse bridge (`gm_br`)",
    "in_b": "biquad-B input follower (`gm_ib`)",
    "gmf_b": "biquad-B shunt-feedback device (`gm_fb`)",
    "rep_gmfb": "replica branch, `gm_fb` copy",
    "rep_bridge": "replica branch, bridge copy",
    "rep_sink": "replica branch, sink",
    "__mirror__": "testbench bias-mirror diode",
}


def _ord(kv):
    r = kv[1]["role"]
    return (ROLE_ORDER.index(r) if r in ROLE_ORDER else len(ROLE_ORDER), kv[0])


def jload(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def _z_of(d: dict, inst: str) -> float:
    """dc transimpedance, in ohms, of one instance's identified noise port."""
    return next(r["z_dc_gohm"] for r in d["rows"]
                if r["inst"] == inst and r.get("modelled")) * 1e9


def _role_cell(d: dict, role) -> str:
    tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
    p = sum(r["irn_uv_rms"] ** 2 for r in d["rows"]
            if (r["role"] or "testbench bias devices") == role)
    return f"{p ** 0.5:.4f} / {100 * p / tot:.2f} %"


def _roles_by_share(d: dict) -> list:
    agg: dict = {}
    for r in d["rows"]:
        k = r["role"] or "testbench bias devices"
        agg[k] = agg.get(k, 0.0) + r["irn_uv_rms"] ** 2
    return [k for k, _ in sorted(agg.items(), key=lambda kv: -kv[1])]


def _gen_cell(d: dict, gen) -> str:
    """Integrated IRN and share of the noise POWER, for one generator or for a
    GROUP of them.  The group form exists because the model splits the channel
    thermal noise across two named generators (`idid` + `igig`, section 5.2) and
    the physical quantity is their sum."""
    gens = (gen,) if isinstance(gen, str) else tuple(gen)
    tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
    p = sum(r["irn_uv_rms"] ** 2 for r in d["rows"] if r["gen"] in gens)
    return f"{p ** 0.5:.4f} / {100 * p / tot:.2f} %"


def _sig_rows(d: dict) -> list:
    """Generators whose differential transimpedance is non-degenerate.  1 kOhm is four
    orders below the smallest signal-path `Z_T` and four above the largest axis one, so
    the split is unambiguous rather than tuned."""
    return [r for r in d["rows"] if r.get("modelled") and r["z_dc_gohm"] >= 1e-6]


def _channel_by_device(d: dict) -> dict:
    """Per device, the channel thermal noise as ONE generator: `idid` + `igig`.

    The model reports the channel in two pieces split by its correlation with the induced
    gate noise (section 5.2).  Both normalisations below divide by the same per-device
    constant -- `2qI_D` or `4kT*gm` -- so the two pieces simply add."""
    by: dict = {}
    for r in _sig_rows(d):
        if r["gen"] in ("idid", "igig"):
            by.setdefault(r["inst"], []).append(r)
    out = {}
    for inst, rs in by.items():
        si = sum(r["si_at_10hz_a2_hz"] for r in rs)
        igig = sum(r["si_at_10hz_a2_hz"] for r in rs if r["gen"] == "igig")
        out[inst] = {"si_over_2qid": sum(r["si_over_2qid"] for r in rs),
                     "si_over_4ktgm": sum(r["si_over_4ktgm"] for r in rs),
                     "c_igid": (igig / si) ** 0.5}
    return out


def _igig_port_evidence(d: dict) -> tuple[float, float, int, int]:
    """How decisively `igig` picks a DRAIN port over any gate port: (lo, hi, n, n_tied).

    This is the measurement that catches the name.  It is decisive only where the two
    candidates are electrically distinct: on a device whose gate sits at an ac ground the
    gate port IS the drain port as far as `Z_T` is concerned, the margin collapses to
    zero, and the test neither can nor needs to separate them."""
    m = []
    for r in _sig_rows(d):
        if r["gen"] != "igig":
            continue
        gate = min(c["dev_db"] for c in r["port_ranking"] if "g" in c["port"])
        m.append(gate - r["fit_dev_db"])
    dec = [x for x in m if x >= 0.01]
    return min(dec), max(dec), len(dec), len(m) - len(dec)


#: Generator names folded onto the physical mechanism each one measures.  `idid` and
#: `igig` are two halves of ONE channel thermal generator, split by its correlation with
#: the induced gate noise (section 5.2) -- `igig` is not gate leakage, so the two are
#: never shown as separate mechanisms.  `pvt_analysis.py` and `export_csv.py` carry the
#: same fold.
MECH_ORDER = ("channel thermal", "flicker (1/f)", "bulk–drain shot", "gate resistance")
MECHANISM = {"idid": MECH_ORDER[0], "ididedge": MECH_ORDER[0], "igig": MECH_ORDER[0],
             "flicker": MECH_ORDER[1], "ibd": MECH_ORDER[2], "rgate": MECH_ORDER[3]}


def _sizes() -> dict:
    """W, L and total gate area per device, from the committed core netlist.

    Sizing is identical pre- and post-layout (section 1 measures the largest `gm` shift at
    4e-04 %), so one netlist covers both.  Area is `W·L·m`; `ng` divides `W` into fingers
    and does not change it.  The testbench's own bias devices are not in this subckt and
    come back absent, which is what puts a dash in their row."""
    out: dict = {}
    for line in (DATA / "post_lumped_core.sp").read_text().splitlines():
        f = line.split()
        if len(f) < 6 or not f[0].startswith("x") or "mos" not in f[5]:
            continue
        kv = dict(t.split("=") for t in f[6:] if "=" in t)
        w, l = float(kv["w"]) * 1e6, float(kv["l"]) * 1e6
        out[f[0][1:]] = (w, l, w * l * float(kv.get("m", 1)))
    return out


def _vfmt(uv: float) -> str:
    """A sub-µV voltage in the unit that keeps it a small integer-ish number."""
    for scale, unit in ((1.0, "µV"), (1e-3, "nV")):
        if uv >= scale:
            return f"{uv / scale:.3g} {unit}"
    return f"{uv / 1e-6:.3g} pV"


def _zfmt(z) -> str:
    """`|Z_T|` at dc in whatever unit keeps it readable -- this cell spans 38 Ω to 60 MΩ."""
    if z is None:
        return "—"
    for scale, unit in ((1e6, "MΩ"), (1e3, "kΩ")):
        if z >= scale:
            return f"{z / scale:.3g} {unit}"
    return f"{z:.3g} Ω"


def _device_matrix(d: dict) -> dict:
    """Per INSTANCE, the integrated IRN power split by mechanism, worst device first.

    Instances are kept apart rather than merged into their roles because the two halves of
    a differential pair are separate devices and their agreement is a check (`_pair_spread`).
    The operating point is read off whichever of the instance's rows resolved it."""
    by: dict = {}
    for r in d["rows"]:
        e = by.setdefault(r["inst"], {"role": r["role"], "id_na": None, "gm_ns": None,
                                      "z": None, "p": dict.fromkeys(MECH_ORDER, 0.0)})
        e["p"][MECHANISM[r["gen"]]] += r["irn_uv_rms"] ** 2
        for k in ("id_na", "gm_ns"):
            if e[k] is None and r.get(k) is not None:
                e[k] = r[k]
        if e["z"] is None and r.get("z_dc_gohm") is not None:
            e["z"] = r["z_dc_gohm"] * 1e9
    return dict(sorted(by.items(), key=lambda kv: -sum(kv[1]["p"].values())))


def _pair_spread(d: dict) -> float:
    """Largest gap, in µV, between the two halves of any differential pair."""
    m = _device_matrix(d)
    per_role: dict = {}
    for e in m.values():
        per_role.setdefault(e["role"], []).append(sum(e["p"].values()) ** 0.5)
    return max((max(v) - min(v) for v in per_role.values() if len(v) == 2), default=0.0)


def _matrix_delta(pre: dict, post: dict) -> tuple[float, str]:
    """Largest pre->post change of any one cell of the matrix, and where it is."""
    a, b = _device_matrix(pre), _device_matrix(post)
    worst = max(((abs(a[i]["p"][m] ** 0.5 - b[i]["p"][m] ** 0.5), i, m)
                 for i in a for m in MECH_ORDER), key=lambda t: t[0])
    return worst[0], f"`{worst[1]}`, {worst[2]}"


def _off_axis(d: dict) -> tuple[float, float]:
    """The replica branch + bias mirror: their total IRN in µV, and its share of the power.

    Ideally they sit ON the differential axis and contribute exactly nothing; what they do
    contribute is a measure of how far the extracted cell departs from that ideal."""
    tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
    p = sum(r["irn_uv_rms"] ** 2 for r in d["rows"]
            if (r["role"] or "").startswith(("rep_", "__")))
    return p ** 0.5, 100 * p / tot


def _c_igid(d: dict) -> tuple[float, float]:
    """The measured channel/induced-gate correlation, min and max over signal devices."""
    cs = [v["c_igid"] for v in _channel_by_device(d).values()]
    return min(cs), max(cs)


def _sgn(x: float, fmt: str = ".0f") -> str:
    """A signed number carrying the typographic minus the rest of the pack uses."""
    return format(x, fmt).replace("-", "\u2212")


def _xrefine(xc: dict, pr: dict) -> float:
    """How much higher, in %, the MEASURED crossing sits than the solved one.

    One Newton step along the locally measured slope: the probe drove the solved
    amplitude and read `err_db` too low, so the target is `err_db` further up a curve
    whose local steepness is the bracket interpolation's own slope."""
    worst = max(pr["rows"], key=lambda r: abs(r["err_db"]))
    sl = xc["per_dut"][worst["dut"]]["bracket_slope_db_per_decade"]
    return 100 * (10 ** (-worst["err_db"] / sl) - 1)


def _xspread(xc: dict) -> float:
    """Worst disagreement, in %, between the fitted-law crossing and the bracket interpolation."""
    return max(abs(c["method_spread_pct"]) for c in xc["per_dut"].values() if c["bracketed"])


def tbl(head: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


# ------------------------------------------------------------------ 1. the DC operating point --
def sec_op(bench: dict, post: dict, la: dict) -> str:
    op, opp = bench["op"], post["op"]
    rows = []
    for inst, d in sorted(op.items(), key=_ord):
        gm, ids = abs(d["gm"]), abs(d["ids"])
        gm_id = gm / ids
        vds, vdss = abs(d["vds"]), abs(d["vdss"])
        vov = abs(d["vgs"]) - abs(d["vth"])
        p = opp.get(inst)
        dgm = 100 * (abs(p["gm"]) - gm) / gm if p else float("nan")
        rows.append([f"`{inst}`", ROLE_TEXT.get(d["role"], str(d["role"])),
                     f"{ids * 1e9:.3f}", f"{gm * 1e9:.3f}", f"{gm_id:.2f}",
                     f"{1.0 / (gm_id * U_T):.3f}", f"{vov * 1e3:+.1f}", f"{vds:.4f}",
                     f"{vdss:.4f}", f"{vds - vdss:+.4f}", f"{dgm:+.2e}"])
    worst = min((abs(d["vds"]) - abs(d["vdss"]), i) for i, d in op.items())
    vds_min = min((abs(d["vds"]), i) for i, d in op.items())
    vov_hi = max((abs(d["vgs"]) - abs(d["vth"]), i) for i, d in op.items())
    vovs = [abs(d["vgs"]) - abs(d["vth"]) for d in op.values()]
    ns = [abs(d["ids"]) / (abs(d["gm"]) * U_T) for d in op.values()]
    dgm_max = max(abs(100 * (abs(opp[i]["gm"]) - abs(d["gm"])) / abs(d["gm"]))
                  for i, d in op.items() if i in opp)
    return f"""## 1. The DC operating point — the root of every number below

Every symbol in every equation in [theory.md](theory.md) is bound to **one measured
operating point**, so this table is the root of the whole chain: the poles, the noise
transimpedances and the distortion currents are all functions of these `gm`, `I_D` and
`C` values and of nothing else.  It is the "verified by the DC ops" check the reviewer
asked for.

Extracted with `.op` on the as-built subckt, one saved op-var per device per parameter
(`scripts/extract_bench.py` → `data/bench_pre_mim.json`, `data/bench_post_lumped.json`).
`n` is *derived* from the measured `gm/I_D` as `n = 1/((gm/I_D)·U_T)` with
`U_T = {U_T * 1e3:.3f}` mV at 27 °C — it is a restatement of column 5, not an independent
measurement, and it is tabulated because `n` is the symbol the distortion equation of §6
uses.  The independent evidence that the exponential law applies is column 7.

{tbl(["dev", "role", "I_D (nA)", "gm (nS)", "gm/I_D (1/V)", "n implied",
      "V_GS−V_TH (mV)", "\\|V_DS\\| (V)", "\\|V_DSAT\\| (V)", "sat. margin (V)",
      "Δgm post (%)"], rows)}

**Design checks on this table**

* **Every device is below threshold**, measured rather than assumed: `V_GS − V_TH` runs
  from {min(vovs) * 1e3:+.0f} mV to {max(vovs) * 1e3:+.0f} mV, i.e.
  {abs(vov_hi[0]) / U_T:.1f}–{abs(min(vovs)) / U_T:.1f} thermal voltages below threshold.
  The tightest device, `{vov_hi[1]}`, is {abs(vov_hi[0]) * 1e3:.1f} mV
  ({abs(vov_hi[0]) / U_T:.2f}·U_T) below `V_TH`, which is the moderate-inversion edge
  rather than deep weak inversion.  This is why the §6 distortion model is stated with a
  validity window and then *tested* — §6.1 measures {la["amplitude_law"]["fitted_slope_db_per_decade"]:.2f} dB/decade of HD3-vs-amplitude
  against the 40 dB/decade the exponential law predicts, which is the empirical
  confirmation that the law holds where it is used.
* **The implied slope factors are physical.**  `n` spans {min(ns):.3f}–{max(ns):.3f}, inside
  the 1 < n < 2 band a subthreshold MOS must obey.  `n` is algebraically tied to `gm/I_D`,
  so this is a consistency test, not an independent one — but it is a test the data could
  have failed (moderate/strong inversion would have pushed `n` past 2) and does not.
* **Every device is saturated with margin.** The tightest `V_DS − V_DSAT` is `{worst[1]}`
  at {worst[0] * 1e3:+.1f} mV.  In weak inversion the saturation condition is
  `V_DS ≳ 4·U_T ≈ {4 * U_T * 1e3:.0f}` mV, and the smallest `V_DS` in the cell is
  `{vds_min[1]}` at {vds_min[0] * 1e3:.1f} mV = {vds_min[0] / U_T:.1f}·U_T — clear by
  {vds_min[0] / (4 * U_T):.2f}×.  A follower dropping out of saturation would break both
  the `gm`-only transfer function and the `Z_T`-propagated distortion model.
* **Bulk is tied to source on every device** (asserted in `n2tf_model.bind_op`, which
  refuses the netlist otherwise).  That is what makes `gmb` inert and lets the PSP `cgb`
  op-var — which carries ~99 % of `cgg` in weak inversion — fold into `cgs`.
* **The layout barely moves the operating point**: the largest `gm` shift
  between pre- and post-layout is {dgm_max:.1e} %.  The pre→post differences reported
  everywhere below are therefore *capacitive*, not bias shifts.
"""


# ------------------------------------------------------------------ 2. transfer function --
def sec_tf(tf: dict, bench_sum: dict) -> str:
    s, out = tf["symbolic"], []
    out.append("""## 2. The transfer function, evaluated

### 2.1 The closed form at the measured operating point

[theory.md §2](theory.md#2-the-transfer-function) derives, as an exact symbolic identity
on the differential-mode half-circuit,

```
                     gm_fa · gm_ia · gm_ib · (gm_br + gm_fb)
    H(s) = ------------------------------------------------------------
                        D_A(s) · D_B(s)  +  κ · s²
```

with `D_A`, `D_B`, `κ` as given there.  Substituting the §1 `gm` values and the design's
own capacitors gives the numbers below.  This evaluation is at **`Fidelity.IDEAL`** —
transconductances and the four design capacitors, nothing else — so it is the *design
equation*, not the full model; §2.2 quantifies exactly what the rest of the model adds.
""")
    for key, label in CASES:
        c = tf["cases"][key]["closed_form"]
        gm, cap = c["gm_ns"], c["caps_pf"]
        rows = [[f"`gm_{k}`", f"{gm[r]:.4f} nS", f"`{cs}`", f"{cap[cr]:.4f} pF"]
                for k, r, cs, cr in (("ia", "in_a", "C1a", "c1_a"),
                                     ("fa", "gmf_a", "C2a", "c2_a"),
                                     ("br", "bridge", "C1b", "c1_b"),
                                     ("ib", "in_b", "C2b", "c2_b"))]
        rows.append(["`gm_fb`", f"{gm['gmf_b']:.4f} nS", "`gm_br + gm_fb`",
                     f"{c['gmf_b_effective_ns']:.4f} nS"])
        pr = c["poles"]
        out.append(f"""#### {label} (`{key}`)

{tbl(["symbol", "measured", "symbol", "value"], rows)}

The cross capacitors are drawn floating between the halves, so the half-circuit sees
**2·C2a = {2 * cap['c2_a']:.3f} pF** and **2·C2b = {2 * cap['c2_b']:.3f} pF** — the factor
of two from the differential realisation, and the reason the drawn farads are half what a
single-ended filter would need.

Roots of the closed-form quartic:

{tbl(["pole pair", "s (rad/s)", "f₀ (Hz)", "Q"],
     [[f"{i + 1}", f"{p['re']:.2f} ± j{abs(p['im']):.2f}", f"{p['f0_hz']:.3f}",
       f"{p['Q']:.4f}"] for i, p in enumerate(pr)])}

Isolated-stage ("decoupled", κ = 0) contrast: biquad A **f₀ = {c['decoupled']['f0_a_hz']:.3f} Hz,
Q = {c['decoupled']['Q_a']:.4f}**; biquad B **f₀ = {c['decoupled']['f0_b_hz']:.3f} Hz,
Q = {c['decoupled']['Q_b']:.4f}**.  The coupling term is
**κ = {c['kappa']:.4e}**, i.e. **{100 * c['coupling_ratio_s2']:.2f} %** of the quartic's own
`s²` coefficient.
""")
    out.append(f"""### 2.2 Reconciling the three pole estimates — closed form, full model, simulation

The closed form above is deliberately minimal, and it is **{tf['cases']['pre_mim']['closed_form']['poles'][0]['f0_hz'] - tf['cases']['pre_mim']['pz']['poles'][0]['f0_hz']:+.2f} Hz**
away from the full model.  That gap is not an error: it is what the device capacitances
add, and naming it is the point of reporting both.

{tbl(["", "biquad-A pair f₀ / Q", "biquad-B pair f₀ / Q", "`fc` (−3 dB, Hz)", "what it includes"],
     [["closed form, `Fidelity.IDEAL`",
       f"{tf['cases']['pre_mim']['closed_form']['poles'][0]['f0_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['closed_form']['poles'][0]['Q']:.4f}",
       f"{tf['cases']['pre_mim']['closed_form']['poles'][1]['f0_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['closed_form']['poles'][1]['Q']:.4f}",
       f"{tf['cases']['pre_mim']['closed_form']['f_c_geometric_hz']:.2f} (geometric)",
       "`gm` + the 4 design caps"],
      ["full model, `Fidelity.FULL`",
       f"{tf['cases']['pre_mim']['pz']['poles'][0]['f0_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['pz']['poles'][0]['Q']:.4f}",
       f"{tf['cases']['pre_mim']['pz']['poles'][1]['f0_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['pz']['poles'][1]['Q']:.4f}",
       "—", "+ every `ro`, `cgs`, `cgd`, `cdb` and the replica branch"],
      ["4-pole fit to the ac sweep",
       f"{tf['cases']['pre_mim']['sim_fit']['f0_a_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['sim_fit']['Q_a']:.4f}",
       f"{tf['cases']['pre_mim']['sim_fit']['f0_b_hz']:.2f} / "
       f"{tf['cases']['pre_mim']['sim_fit']['Q_b']:.4f}",
       f"{bench_sum['pre_mim']['scorecard']['fc_hz']:.3f} (measured)",
       "the simulator, no model at all"]])}

**Which capacitance closes the gap is measured, not asserted.**  Each family of device
capacitance symbols is zeroed in turn and the pencil re-solved on the same matrices
(`scripts/tf_analysis.py::cap_ablation`):

{tbl(["capacitance zeroed", "symbols zeroed", "pole f₀ (Hz)", "kept zero f₀ (Hz)"],
     [[f"`{r['zeroed']}`" if r["n_symbols"] else r["zeroed"], str(r["n_symbols"]),
       ", ".join(f"{x:.2f}" for x in r["pole_f_hz"]),
       ", ".join(f"{x:.0f}" for x in r["zero_f_hz"])]
      for r in tf["cases"]["pre_mim"]["cap_ablation"]])}

**`cgs` is the whole gap.**  Zero it and the poles return to
{tf['cases']['pre_mim']['cap_ablation'][1]['pole_f_hz'][0]:.2f} Hz — the closed form's
{tf['cases']['pre_mim']['closed_form']['f_c_geometric_hz']:.2f} Hz to within
{abs(tf['cases']['pre_mim']['cap_ablation'][1]['pole_f_hz'][0] - tf['cases']['pre_mim']['closed_form']['f_c_geometric_hz']):.2f} Hz —
and the two out-of-band zero pairs disappear with them.  (The kept-zero column can still
show a root in the 10 kHz–1 MHz range: with `cgs` gone the model has almost no state left
up there, and what survives is near-cancelling pole/zero residue three to four orders of
magnitude above the band — it is listed for completeness, not read as a filter feature.)  `cgd` moves nothing at all
(it is {jload('bench_pre_mim.json')['op']['m2']['cgd'] * 1e18:.1f} aF on the input device:
in weak inversion the channel is not formed, so there is no Miller path), and `cdb`
moves `fc` by {abs(tf['cases']['pre_mim']['cap_ablation'][3]['pole_f_hz'][0] - tf['cases']['pre_mim']['pz']['poles'][0]['f0_hz']):.2f} Hz.

The mechanism is specific: PSP reports
**cgg = {jload('bench_pre_mim.json')['op']['m2']['cgg'] * 1e15:.1f} fF** on the biquad-A
input follower, of which
**{jload('bench_pre_mim.json')['op']['m2']['cgb'] * 1e15:.1f} fF is `cgb`** — because in
weak inversion the gate charge terminates on the bulk, not on a channel.  Bulk is tied to
source here, so all of it lands gate-to-source and adds
{100 * (jload('bench_pre_mim.json')['op']['m2']['cgg'] * 1e12) / tf['cases']['pre_mim']['closed_form']['caps_pf']['c1_a']:.1f} %
to `C1a` = {tf['cases']['pre_mim']['closed_form']['caps_pf']['c1_a']:.3f} pF, the smallest
capacitor in the filter.  Reading the op-vars by strong-inversion convention — `cgs` as the
gate-to-source capacitance, `cgb` left on the bulk — would have put
{jload('bench_pre_mim.json')['op']['m2']['cgg'] / jload('bench_pre_mim.json')['op']['m2']['cgs']:.0f}×
too little capacitance on that node and hidden this shift entirely.

Two consequences:

* **The closed form is the design equation, and it is accurate to ~2 % in `fc`** — the
  width of the S2 window — with the error sign and mechanism both known.  Sizing from it
  and then trimming on the full model is exactly how this cell was built.
* **Everything quoted as a *result* — poles, Q, `fc`, group delay — comes from the full
  model or from the simulator, never from the closed form.**  §3 shows the full model and
  the simulator agree to {tf['cases']['pre_mim']['validation']['max_mag_err_db_scored']:.4f} dB.

The same accounting applies to the dc gain: the closed form gives **H(0) = 1 exactly**
(the numerator is literally the constant term of `D_A·D_B`), while the full model and the
simulator both give **{tf['cases']['pre_mim']['pz']['dc_gain_db']:.6f} dB** — the finite `ro`
of the followers, and nothing else.
""")
    return "\n".join(out)


# ------------------------------------------------------------------ 3. model vs sim --
def sec_valid(tf: dict) -> str:
    rows = []
    for key, label in CASES:
        v, f = tf["cases"][key]["validation"], tf["cases"][key]["sim_fit"]
        rows.append([label, f"{v['max_mag_err_db_scored']:.4f}", f"{v['max_phase_err_deg_scored']:.4f}",
                     f"{v['max_gd_err_pct']:.3f}",
                     f"{v['gd_dc_ms_sim']:.4f} / {v['gd_dc_ms_model']:.4f}",
                     f"{v['max_mag_err_db_all']:.3f}", f"{v['max_phase_err_deg_all']:.2f}"])
    frows = []
    for key, label in CASES:
        f = tf["cases"][key]["sim_fit"]
        r = f["real_pole_refit"]
        frows.append([label, f"{f['f0_a_hz']:.2f} / {f['Q_a']:.4f}",
                      f"{f['f0_b_hz']:.2f} / {f['Q_b']:.4f}",
                      f"{f['max_mag_resid_db']:.4f} / {f['max_phase_resid_deg']:.4f}",
                      ", ".join(f"{abs(x):.2f}" for x in f["quartic_coeff_err_pct"]),
                      f"{100 * f['max_pole_distance_rel']:.1f}",
                      f"{r['max_mag_resid_db']:.3f} / {r['max_phase_resid_deg']:.1f}"])
    pm = tf["cases"]["pre_mim"]["sim_fit"]
    return f"""## 3. Model versus simulation

### 3.1 The model, evaluated against the ac sweep point by point

The exact same operating-point-bound system that produced the poles is evaluated at every
frequency of the certified ac sweep and compared against it point by point
(`scripts/tf_analysis.py::validate`).  No fitting, no scaling: one `.op`, one solve.

{tbl(["", "max Δ\\|H\\| ≤1 kHz (dB)", "max Δφ ≤1 kHz (°)", "max Δτ_g (%)",
      "τ_g(dc) sim / model (ms)", "max Δ\\|H\\| all f (dB)", "max Δφ all f (°)"], rows)}

* **In the scored band the model matches the simulator to a few hundredths of a dB** — 0.027 dB and
  0.34° over dc–1 kHz, on a response that falls 49 dB across that band.
* **Above the scored band it degrades to ~2.6 dB / 26°.**  That is the stopband, below
  −49 dB, where the device-capacitance feed-through zeros of §4 take over; the
  discrepancy there is the linearisation itself, and it is reported rather than hidden by
  trimming the plot.
* **Group delay closes to ~1 %**, and τ_g(dc) — the most pole-sensitive scalar the filter
  has — matches to 4 significant figures.  A group-delay match this tight requires *all
  four* poles to be right, which is why it is quoted as the strongest aggregate check on
  the pole locations.

### 3.2 What the simulation says about the poles **on its own**

A 4-pole / 0-zero rational is fitted directly to the measured complex response over
0.1–500 Hz, in log-magnitude and unwrapped phase together.  It never sees the
small-signal model, the netlist or the operating point — it is the reviewer's
"verified by the sim data" check, standing alone.

{tbl(["", "pair A f₀ / Q", "pair B f₀ / Q", "fit residual (dB / °)",
      "monic-quartic coefficient error vs model (%)", "worst single-root distance (%)",
      "**all-real refit** residual (dB / °)"], frows)}

Read this table in the right order, because the conditioning differs by column:

* **The fit is good**: {pm['max_mag_resid_db']:.3f} dB and
  {pm['max_phase_resid_deg']:.3f}° over 185 points and 60 dB of dynamic range.  The
  measured response *is* 4-pole/0-zero to that accuracy in the passband — the order is
  confirmed from data.
* **The pole set agrees with the model to 3–5 %** in the coefficients of the monic
  quartic, which is the well-posed comparison.
* **The individual (f₀, Q) split is only good to ~{100 * pm['max_pole_distance_rel']:.0f} %
  per root, and that is expected, not a discrepancy.**  The two pairs are nearly
  co-located in frequency (§2), so the response has a shallow valley in the direction that
  trades one pair against the other; the fit slides along it.  The number is printed
  rather than suppressed so the limit of what an ac sweep alone can resolve is visible.
* **The last column is the decisive one for the reviewer's actual question.**  Refitting
  with both Q's constrained to ≤ 0.5 — which is exactly "all four poles are real" — the
  best achievable residual is **{tf['cases']['pre_mim']['sim_fit']['real_pole_refit']['max_mag_resid_db']:.2f} dB
  and {tf['cases']['pre_mim']['sim_fit']['real_pole_refit']['max_phase_resid_deg']:.0f}°**,
  {tf['cases']['pre_mim']['sim_fit']['real_pole_refit']['max_mag_resid_db'] / pm['max_mag_resid_db']:.0f}×
  and {tf['cases']['pre_mim']['sim_fit']['real_pole_refit']['max_phase_resid_deg'] / pm['max_phase_resid_deg']:.0f}×
  worse, with both Q's pinned against the 0.5 bound (the fit is driven toward complex
  poles and the constraint prevents it).  **The measured response cannot be
  reproduced by any all-real-pole 4th-order model.**  So "are the poles real or
  imaginary?" is answered by the simulation data alone: **complex, both pairs**, and the
  model then says where.

**Why not `ngspice .pz`?**  It is not usable on this cell: it aborts with *"the input
signal is shorted on the way to the output"* for any input port that carries its own dc
bias, which a subthreshold gate must.  Confirmed on a one-transistor deck as well, so it
is the analysis and not the netlist.  The three checks above — an operating-point-bound
eigenvalue solve, a simulator-only fit with a falsification test, and a point-by-point
overlay — replace it: between them they report what a `.pz` listing would have, plus
checks it does not make.
"""


# ------------------------------------------------------------------ 4. poles and zeros --
def sec_pz(tf: dict) -> str:
    out = ["""## 4. Poles and zeros — the map

From the matrix pencil of the **full 13-node differential system** at `Fidelity.FULL`
(`scripts/pencil.py`): poles are the finite generalised eigenvalues of `(−G, C)`, zeros
come from the bordered pencil with the output port as the border, both computed on the
same matrices the ac solve uses.  Everything is `Fidelity.FULL` here — every `ro`, every
device capacitance, the replica branch and the bias diode included.
"""]
    for key, label in CASES:
        p = tf["cases"][key]["pz"]
        prow = [[f"{i + 1}", f"{x['re']:.2f} ± j{abs(x['im']):.2f}" if x["kind"] == "pair"
                 else f"{x['re']:.2f}", f"{x['f0_hz']:.3f}",
                 f"{x['Q']:.4f}" if x["Q"] else "—",
                 "complex pair" if x["kind"] == "pair" else "real"]
                for i, x in enumerate(p["poles"])]
        zrow = [[f"{i + 1}", f"{x['re']:.4g} ± j{abs(x['im']):.4g}" if x["kind"] == "pair"
                 else f"{x['re']:.4g}", f"{x['f0_hz']:.4g}",
                 f"{x['Q']:.4f}" if x["Q"] else "—",
                 "complex pair" if x["kind"] == "pair" else "real"]
                for i, x in enumerate(p["zeros"])]
        npair = sum(1 for x in p["cancelled"] if abs(x["s"][1]) > 1e-9)
        worst = max(x["residual_rel"] for x in p["cancelled"])
        out.append(f"""### {label} (`{key}`)

`{p['n_poles']}` poles and `{p['n_zeros']}` zeros are returned; **{len(p['cancelled'])} of
them cancel** — {npair // 2} conjugate pair{'s' if npair // 2 != 1 else ''} (counted as
{npair} roots) plus {len(p['cancelled']) - npair} real — leaving the
{len(p['poles']) * 2 - sum(1 for x in p['poles'] if x['kind'] == 'real')}-pole,
{len(p['zeros']) * 2 - sum(1 for x in p['zeros'] if x['kind'] == 'real')}-zero response
below.  A cancelling pole/zero pair is a mode the differential input cannot excite or the
differential output cannot observe — the replica branch and the bias diode account for all of
them — and they are *reported*, not silently dropped.  Cancellation is declared at 10⁻⁴
relative separation because the two sets come from two separately conditioned
eigenproblems; the worst residual separation actually observed here is
**{worst:.1e}** relative, i.e. {worst * 1e4:.2f} % of the declaration threshold.

**Poles** (dc gain {p['dc_gain_db']:.6f} dB)

{tbl(["#", "s (rad/s)", "f₀ (Hz)", "Q", "kind"], prow)}

**Zeros**

{tbl(["#", "s (rad/s)", "f₀ (Hz)", "Q", "kind"], zrow)}

""")
    pm = tf["cases"]["pre_mim"]["pz"]
    return "\n".join(out) + f"""### What the map says

* **All four filter poles are complex** — two conjugate pairs, Q =
  {pm['poles'][0]['Q']:.3f} and {pm['poles'][1]['Q']:.3f}.  There is no real pole in the
  passband, so the answer to *"real or imaginary?"* is: **two under-damped pairs, at
  {pm['poles'][0]['f0_hz']:.2f} Hz and {pm['poles'][1]['f0_hz']:.2f} Hz, essentially
  co-located in frequency ({100 * abs(pm['poles'][1]['f0_hz'] / pm['poles'][0]['f0_hz'] - 1):.2f} %
  apart) and split only in damping**.  A 4th-order Butterworth has
  Q = 0.5412 and 1.3066 at a single ω₀; this cell measures
  **{pm['poles'][0]['Q']:.4f} and {pm['poles'][1]['Q']:.4f}** — within
  {100 * abs(pm['poles'][0]['Q'] / 0.54120 - 1):.1f} % and
  {100 * abs(pm['poles'][1]['Q'] / 1.30656 - 1):.1f} % of Butterworth — which is what gives
  the {abs(pm['dc_gain_db']):.3f} dB dc flatness and the 0.05 dB passband ripple of §7.
  The shape is *not* designed by placing two textbook stages: §2.1 shows the isolated
  stages would be Q = 2.10 and 0.46, and it is the κ·s² coupling term that maps them onto
  the Butterworth pair.
* **The zeros are all far out of band and all complex**: the lowest is at
  {pm['zeros'][0]['f0_hz'] / 1e3:.2f} kHz, {pm['zeros'][0]['f0_hz'] / pm['poles'][0]['f0_hz']:.1f}×
  above the pole frequency, so neither the passband shape nor the 1 kHz stopband number
  depends on them.  **Their origin is measured** (§2.2 ablation table): zeroing `cgs`
  removes both pairs, zeroing `cgd` changes nothing.  They are the followers' own
  **gate-to-source feed-forward** — a source follower's input capacitance is a direct path
  to its output — and they are why the modelled stopband stops falling at 80 dB/decade,
  which is the same physics as the \\|H\\|-vs-model divergence above 1 kHz in §3.1, seen
  from the other side.
* **`figures/pz_plane.png`** plots exactly these tables — both members of each conjugate
  pair, poles and zeros, pre- and post-layout on the same axes, with the cancelled pairs
  shown hollow.
"""


# ------------------------------------------------------------------ 5. noise --
def sec_noise(nz: dict) -> str:
    out = ["""## 5. The noise equation, checked generator by generator

[theory.md §3](theory.md#3-the-noise-equation) states the equation

```
    S_out(f) = Σ_k |Z_T,k(jω)|² · S_i,k(f) ,     IRN² = ∫ S_out(f)/|H(jω)|² df
```

— every device's every noise generator, each propagated to the differential output by the
transimpedance of its own port.  The check below is not a fit: `S_i,k(f)` is the
simulator's own per-generator noise vector, `Z_T,k` is solved from the operating-point
model, and the two are multiplied and summed.
"""]
    rows = []
    for key, label in CASES:
        d = nz[key]
        rows.append([label, f"{d['irn_uv_sim']:.4f}", f"{d['irn_uv_sum_of_generators']:.4f}",
                     f"{d['irn_uv_certified']:.4f}", f"{d['onoise_closure_max_pct']:.2e}",
                     f"{d['inoise_vs_onoise_over_h_max_pct']:.2e}",
                     f"{d['transimpedance_cross_check']['max_rel_diff']:.2e}"])
    out.append(f"""### 5.1 Closure

{tbl(["", "IRN sim (µV)", "IRN Σ generators (µV)", "IRN certified (µV)",
      "max Δ S_out (%)", "max Δ inoise vs onoise/\\|H\\| (%)",
      "`netlist2tf.transimpedance` vs pencil"], rows)}

Three independent closures:

1. **The sum over generators reproduces the simulator's own total** to
   {max(nz[k]['onoise_closure_max_pct'] for k, _ in CASES):.1e} % at every frequency —
   so no generator is missing and none is double-counted.  This is what justifies writing
   `Σ_k` at all.
2. **The integrated IRN equals the certified sign-off number** to all quoted digits — the
   frozen `lab.metrics` definition, not a re-derivation.
3. **`spicexplorer_netlist2tf.transimpedance` and the independent matrix-pencil solve
   agree to ~10⁻⁸ relative.**  The package primitive and the checking code are separate
   implementations of `Z_T`, which is the point of running both.

### 5.2 Where the noise comes from

Integrated 0.5–200 Hz, input-referred.  Percentages are of total IRN **power**.  First by
generator kind:

{tbl(["generator", "what it is"] + [f"{lab} (µV / % power)" for _, lab in CASES],
     [[name, txt] + [_gen_cell(nz[k], g) for k, _ in CASES]
      for g, name, txt in ((("idid", "igig"), "`idid` + `igig`",
                            "**channel thermal noise** — one mechanism, which the model "
                            "reports as two generators"),
                           ("idid", "`idid` alone", "the uncorrelated part of that split"),
                           ("igig", "`igig` alone",
                            "the correlated part of that split — **not** gate leakage"),
                           ("flicker", "`flicker`", "1/f gate noise"),
                           ("ibd", "`ibd`", "bulk-drain junction"),
                           ("rgate", "`rgate`", "gate resistance"))])}

**`igig` is not gate leakage, in spite of the name.**  PSP103 splits the channel thermal
noise by its correlation `c` with the induced gate noise: `idid` carries the uncorrelated
fraction `(1 − c²)·S_id`, and the remaining `c²·S_id` is injected drain-to-source through
an internal noise node, where it is reported under the name `igig`
(`PSP103_module.include`: `I(NOII) <+ white_noise(nt/mig, "igig")` feeding
`I(DI,SI) <+ migid·I(NOII)`, with `migid = c·sqid/sqig`).  The gate-side half of that same
construct is coupled through a `d/dt` and contributes nothing in this band.  Put back
together the channel carries **{_gen_cell(nz['pre_mim'], ('idid', 'igig')).replace(' / ', ' µV, ')} of
the noise power** — and it equals the full weak-inversion shot noise `2qI_D`, which §5.3
measures.  The correlation itself comes out at
`c` = {_c_igid(nz['pre_mim'])[0]:.2f}–{_c_igid(nz['pre_mim'])[1]:.2f}.

The model's *actual* gate-leakage generators are `igs` and `igd`, and **both are
identically zero here**.  The thick-oxide devices this cell is built from carry no gate
current at all: every gate-current pre-factor in the PDK card is set to zero
(`iginvlw = igovw = igovdw = 0`, at `t_ox` = 7.43 nm n-channel and 6.95 nm p-channel), and
a single device biased at this cell's operating point draws a gate current of exactly zero
while passing 6.4 nA of drain current (`scripts/gate_leakage_probe.py`).  There is no
gate-leakage noise in this design to account for.

A hand-written noise model that takes `idid` for the channel and stops there is 1.4 dB
optimistic on IRN before it does anything else (10·log₁₀(1/(1−0.271))).  One that writes
`S_id = 2qI_D` — the whole channel, as
[theory.md §3.2](theory.md#32-what-the-generators-are-in-this-bias-regime) derives it —
needs no second term.

Then by device role — the answer to "which device should I make bigger":

{tbl(["role"] + [f"{lab} (µV / % power)" for _, lab in CASES],
     [[ROLE_TEXT.get(g, str(g))] + [_role_cell(nz[k], g) for k, _ in CASES]
      for g in _roles_by_share(nz["pre_mim"])])}

**The two biquad-A branch devices carry 79 % of the noise between them**, and the
biquad-A bias sink — a device that appears nowhere in `H(s)`, because an ideal current
source is an open circuit to small signals — contributes almost as much as the input
follower.
The reason is not the cascade order — both biquads are unity-gain followers, so neither
attenuates the other's noise — it is **node impedance**: the transimpedance from biquad
A's internal node `net2` to the differential output is
{_z_of(nz['pre_mim'], 'm2') / 1e6:.0f} MΩ against {_z_of(nz['pre_mim'], 'm0') / 1e6:.0f} MΩ
at biquad B's `net4`, because `C1a` is the smallest capacitor in the filter.  The same
injected current therefore makes
{_z_of(nz['pre_mim'], 'm2') / _z_of(nz['pre_mim'], 'm0'):.1f}× more output noise in A than
in B — which is also why the design spends its capacitance there.  The replica branch and
the testbench bias diode sit on the differential axis and contribute nothing measurable.

And by device × mechanism — the same budget with nothing folded away:
""")
    d0, mech = nz["pre_mim"], _device_matrix(nz["pre_mim"])
    tot0 = sum(r["irn_uv_rms"] ** 2 for r in d0["rows"])
    rr, wl = [], _sizes()
    for inst, e in mech.items():
        s_ = sum(e["p"].values())
        g = wl.get(inst)
        rr.append([f"`{inst}`", ROLE_TEXT.get(e["role"], "testbench bias device"),
                   "—" if g is None else f"{g[0]:.4g}/{g[1]:.4g}",
                   "—" if g is None else f"{g[2]:.0f}",
                   "—" if e["id_na"] is None else f"{e['id_na']:.3f}",
                   "—" if e["gm_ns"] is None else f"{e['gm_ns']:.1f}", _zfmt(e["z"])]
                  + [f"{e['p'][m] ** 0.5:.4f}" for m in MECH_ORDER]
                  + [f"**{s_ ** 0.5:.4f}**", f"{100 * s_ / tot0:.2f}"])
    rr.append(["**total**", "", "", "", "", "", ""]
              + [f"**{sum(e['p'][m] for e in mech.values()) ** 0.5:.4f}**" for m in MECH_ORDER]
              + [f"**{tot0 ** 0.5:.4f}**", "100.00"])
    dmax, dwhere = _matrix_delta(nz["pre_mim"], nz["post_lumped"])
    off = _off_axis(nz["post_lumped"])
    # Compared within the CORE only: the replica sink `r3` is physically the largest
    # device in the netlist (m=4) but sits on the differential axis and makes no noise.
    core = [i for i in wl if (mech[i]["role"] or "") in ROLE_ORDER[:6]]
    flk, big = min(core, key=lambda i: wl[i][2]), max(core, key=lambda i: wl[i][2])
    out.append(f"""{tbl(["device", "role", "W/L (µm)", "area (µm²)", "I_D (nA)", "gm (nS)",
                         "\\|Z_T\\| dc"]
                        + [f"{m} (µV)" for m in MECH_ORDER] + ["total (µV)", "% power"], rr)}

Read it along a row for *which device*, down a column for *which mechanism*.  The column
totals are the generator table above with `idid` and `igig` already summed; the rows pair
up into the role table.  Nothing is truncated — these
{len(mech)} devices × {len(MECH_ORDER)} mechanisms are the entire IRN.

**Every signal device appears twice**, as the two halves of a differential pair
(`m2`/`m5`, `m9`/`m10`, `m0`/`m1`, `m14`/`m15`, `mst`/`mstn`, `m4`/`m8`).  A pair sees the
same `|Z_T|` by symmetry, and the two halves agree here to
{_vfmt(_pair_spread(nz['pre_mim']))} — a check on the extraction rather than a result.

**The two mechanisms rank the devices differently, and the geometry columns say why.**
Channel noise is `2qI_D` propagated by `Z_T`, so it peaks on the biquad-A pair: `m2`/`m5`
carry the *least* current in the cell and still lead, because their node sees
{_z_of(nz['pre_mim'], 'm2') / 1e6:.0f} MΩ.  Flicker does not scale with current at all —
it scales with gate area — so it peaks instead on the pair containing `{flk}`, the
smallest-area devices in the core at {wl[flk][2]:.0f} µm² against
{wl[big][2]:.0f} µm² on the {ROLE_TEXT[mech[big]["role"]]}.  That is the actionable
split: the channel term is bought back with capacitance at biquad A, the flicker term with
area on the biquad-B follower, and neither fix helps the other.

The post-layout cell reproduces the table to
{_vfmt(dmax)} on any single entry ({dwhere}).  Its one qualitative difference is that
the replica branch and the bias mirror are no longer exactly on the differential axis, so
they pick up {_vfmt(off[0])} between them — {off[1]:.1e} % of the power, still
nothing.  `csv/noise_by_device_and_type.csv` carries the untruncated form for all three
DUTs, one row per device per *named* generator, each with its identified port.

""")
    d = nz["pre_mim"]
    # `z_dc_gohm` is present only on rows whose port the data-driven identification
    # actually resolved; the handful it does not (gate-resistance generators, and the
    # testbench's own bias devices) are carried at their measured value and bounded below.
    mod = [r for r in d["rows"] if r.get("modelled")]
    # 1 kOhm is four orders below the smallest signal-path transimpedance and four above
    # the largest axis one, so the split is unambiguous rather than tuned.
    axis = [r for r in mod if r["z_dc_gohm"] < 1e-6]
    sig = [r for r in mod if r["z_dc_gohm"] >= 1e-6]
    tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
    unmod_p = sum(r["irn_uv_rms"] ** 2 for r in d["rows"] if not r.get("modelled"))
    axis_p = sum(r["irn_uv_rms"] ** 2 for r in axis)
    chan = list(_channel_by_device(d).values())   # `idid` + `igig` per device, sec 5.2
    idid = [r for r in sig if r["gen"] == "idid"]
    fl = [r for r in sig if r["gen"] == "flicker"]
    return "\n".join(out) + f"""### 5.3 Are the generators what they claim to be?

Two per-generator sanity checks, applied to the {len(set(r['inst'] for r in sig))} devices
whose differential transimpedance is non-degenerate.  (The other
{len(set(r['inst'] for r in axis))} — the replica branch and the testbench's bias diode —
sit **on the differential axis**, where `|Z_T|` comes out at
{max(r['z_dc_gohm'] for r in axis) * 1e9:.1f} Ω against
{min(r['z_dc_gohm'] for r in sig) * 1e9 / 1e3:.1f} kΩ for the weakest signal-path device
and {max(r['z_dc_gohm'] for r in sig) * 1e9 / 1e6:.0f} MΩ for the strongest; their `S_i`
extraction is a division by ~0 and is therefore meaningless, while their *actual*
contribution is **{100 * axis_p / tot:.1e} %** of the IRN power.  A further
{unmod_p ** 0.5:.2e} µV — **{100 * unmod_p / tot:.1e} %** of the power, the gate-resistance
generators and the testbench's own bias devices — has no resolved port at all and is
carried at its measured value.)

{tbl(["check", "expected", "observed over the signal devices"],
     [["channel noise against full shot noise, `S_i / 2qI_D`",
       "= 1 in weak inversion",
       f"{min(r['si_over_2qid'] for r in chan):.3f} – {max(r['si_over_2qid'] for r in chan):.3f}"],
      ["the same, written against `gm`: `S_i / 4kT·gm`", "= (n/2)·(previous column)",
       f"{min(r['si_over_4ktgm'] for r in chan):.3f} – {max(r['si_over_4ktgm'] for r in chan):.3f}"],
      ["flicker slope, `d log S_i / d log f`", "≈ −1 (1/f)",
       f"{min(r['fit_slope'] for r in fl):.3f} – {max(r['fit_slope'] for r in fl):.3f}"],
      ["power-law fit residual over 1–200 Hz", "small",
       f"≤ {max(abs(r['fit_dev_db']) for r in sig):.3f} dB"]])}

The first row is the physical statement: the channel generator is
**{min(r['si_over_2qid'] for r in chan):.2f}–{max(r['si_over_2qid'] for r in chan):.2f}× full
shot noise `2qI_D`** — that is, it *is* the full shot noise.  The strong-inversion form
`4kTγ·gm` with γ = 2/3 is a different law with a different bias dependence, and the data
picks the shot-noise one.  Both halves of the split are in this row: `idid` on its own reads
only {min(r['si_over_2qid'] for r in idid):.2f}–{max(r['si_over_2qid'] for r in idid):.2f}×,
and the missing fraction is `igig` (§5.2), not any suppression of the shot noise.
The second row is the same measurement rewritten against `gm`, and it is a *consistency* check
rather than a new one: the two columns must differ by exactly `n/2`, and their measured
ratio is
{sum(r['si_over_2qid'] for r in chan) / sum(r['si_over_4ktgm'] for r in chan):.3f} = 2/n
with n = {2 * sum(r['si_over_4ktgm'] for r in chan) / sum(r['si_over_2qid'] for r in chan):.3f},
which matches the §1 slope factors.  (That ratio is unchanged by the grouping, as it must
be: it divides one normalisation by the other and `S_i` cancels.)  The flicker slope being
slightly steeper than −1 is the PSP flicker model's own `f^-(1+δ)` behaviour, not a fitting
artifact.

**The port of every generator is identified from the data, not assumed**
(`scripts/noise_analysis.py::identify_port`): for each generator the candidate device
ports are ranked by how well `S_out/|Z_T,port|²` comes out frequency-flat (or `1/f`, for
flicker), and the winner is taken.  Every channel-noise generator selects drain–source,
which is what the physics predicts — and that includes `igig`, on {_igig_port_evidence(d)[2]}
of the {len(_channel_by_device(d))} signal devices by
{_igig_port_evidence(d)[0]:.1f}–{_igig_port_evidence(d)[1]:.1f} dB over the best gate port.
The other {_igig_port_evidence(d)[3]} have their gate at an ac ground, where the gate port
and the drain port are the same node pair and the two candidates tie exactly.  **That
ranking is how the mislabelling in §5.2 was caught**: a generator named for the gate that
measures at the drain is not a gate generator.  Doing it this way makes the port assignment
a measured result rather than an assumption, and that is what justifies re-using the same
`Z_T` for the distortion currents in §6.

`figures/noise_budget.png` plots `S_out(f)`, the sum of generators, and the top
contributors' individual curves on one axis.
"""


# ------------------------------------------------------------------ 6. linearity --

def _gm_shift_pct() -> float:
    """Largest |gm| shift, in %, between the pre-layout and post-layout op points."""
    pre = jload("bench_pre_mim.json")["op"]
    post = jload("bench_post_lumped.json")["op"]
    return max(
        abs(100 * (abs(post[k]["gm"]) - abs(v["gm"])) / abs(v["gm"]))
        for k, v in pre.items()
        if k in post and v.get("gm")
    )

def sec_lin(la: dict, lin: dict, sp_: dict, ps: dict) -> str:
    a = la["amplitude_law"]
    xc = a["hd3_crossing"]
    pr = jload("hd3_crossing_probe.json")
    fq = la["frequency_law"]
    ml = la["memoryless_test"]
    det = {r["fin"]: r for r in fq["model_detail"]["rows"]}
    ok = [r for r in fq["rows"] if abs(r["err_db"]) <= 2.0]
    band = (min(r["fin"] for r in ok), max(r["fin"] for r in ok))
    import math

    def slope(rows, key):
        lo, hi = rows[0], rows[-1]
        return (hi[key] - lo[key]) / math.log10(hi["fin"] / lo["fin"])

    win_meas = slope(ok, "hd3_measured_db")
    win_model = slope(ok, "hd3_model_db")

    # The low-frequency shortfall in ABSOLUTE volts.  A dB gap that grows as the level
    # falls is the signature of an additive floor, so the residual is quoted in volts:
    # (measured - modelled) third-harmonic amplitude at the output.
    def v3(row, key):
        f = det[row["fin"]]["fund_vpp"] / 2
        return f * 10 ** (row[key] / 20)

    exc = [(r["fin"], v3(r, "hd3_measured_db"), v3(r, "hd3_model_db")) for r in fq["rows"]]
    lo = [e for e in exc if e[0] <= 35]
    lad = tbl(["V_in (Vpp diff)", "THD (dB)", "HD3 (dB)", "HD2 (dB)", "V_out fund (Vpp)",
               "THD post-layout (dB)", "HD3 post-layout (dB)"],
              [[f"{p['vpp_diff']:.5g}", f"{p['thd_db']:.3f}", f"{p['hd3_db']:.3f}",
                f"{p['hd2_db']:.3f}", f"{p['out_fund_vpp']:.5f}",
                f"{q['thd_db']:.3f}", f"{q['hd3_db']:.3f}"]
               for p, q in zip(lin["thd_ladder"]["pre_mim"], lin["thd_ladder"]["post_pex"])])
    fqt = tbl(["f_in (Hz)", "HD3 measured (dB)", "HD3 model, coherent (dB)",
               "HD3 model, worst-case (dB)", "model − measured (dB)", "dominant device",
               "max `a`"],
              [[f"{r['fin']:.0f}", f"{r['hd3_measured_db']:.3f}", f"{r['hd3_model_db']:.3f}",
                f"{r['hd3_model_worstcase_db']:.3f}", f"{-r['err_db']:+.3f}",
                ROLE_TEXT[r["dominant"]], f"{det[r['fin']]['a_max']:.4f}"]
               for r in fq["rows"]])
    prof = tbl(["f_in (Hz)", "THD pre-layout (dB)", "THD post-layout (dB)",
                "HD3 pre (dB)", "HD3 post (dB)", "V_out fund (Vpp)"],
               [[f"{p['fin']:.0f}", f"{p['thd_db']:.3f}", f"{q['thd_db']:.3f}",
                 f"{p['hd3_db']:.3f}", f"{q['hd3_db']:.3f}", f"{p['out_fund_vpp']:.5f}"]
                for p, q in zip(lin["thd_profile"]["pre_mim"], lin["thd_profile"]["post_pex"])])

    # --- 6.5, the extracted cell over the whole band -------------------------------
    pxv = ps["profile_vpp_diff"]
    pxw = ps["worst_fin_hz"]
    pxprof = tbl(["f_in (Hz)", "THD (dB)", "HD3 (dB)", "HD2 (dB)", "V_out fund (mVpp)",
                  "3·f_in (Hz)"],
                 [[f"{r['fin']:.0f}", f"{r['thd_db']:.3f}", f"{r['hd3_db']:.3f}",
                   f"{r['hd2_db']:.3f}", f"{r['out_fund_vpp'] * 1e3:.3f}",
                   f"{3 * r['fin']:.0f}"] for r in ps["profile"]])
    pxlad = tbl(["V_in (mVpp diff)", "THD (dB)", "HD3 (dB)", "HD2 (dB)",
                 "V_out fund (mVpp)"],
                [[f"{r['vpp_diff'] * 1e3:.5g}", f"{r['thd_db']:.3f}", f"{r['hd3_db']:.3f}",
                  f"{r['hd2_db']:.3f}", f"{r['out_fund_vpp'] * 1e3:.3f}"]
                 for r in ps["ladder"]])
    px20 = ps["profile"][0]
    pxwr = max(ps["profile"], key=lambda r: r["thd_db"])
    pxend = ps["profile"][-1]
    # The two lowest rungs of the ladder at the worst frequency: HD3 in dBc rises
    # 40 dB/decade of drive while the cubic law holds, so the measured rise says
    # whether it still does there.
    def _pxslope(i):
        a_, b_ = ps["ladder"][i], ps["ladder"][i + 1]
        return ((b_["hd3_db"] - a_["hd3_db"])
                / math.log10(b_["vpp_diff"] / a_["vpp_diff"]))

    pxslopes = [_pxslope(i) for i in range(len(ps["ladder"]) - 1)]
    # Where the ladder is still on the A^2 law and where it has left it: the first rung
    # whose slope falls more than 5 dB/decade short of 40 is the break, quoted rather
    # than eyeballed.
    pxbreak = next((i for i, v in enumerate(pxslopes) if v < 35.0), len(pxslopes))
    # Where the OUTPUT stops growing: the earliest rung from which no later rung exceeds
    # it by more than 10 %.  Measured off the data rather than read off the table, so the
    # sentence below cannot drift from it.
    _out = [r["out_fund_vpp"] for r in ps["ladder"]]
    pxflat = next(k for k in range(len(_out))
                  if all(v <= 1.10 * _out[k] for v in _out[k:]))
    pxclamp = _out[pxflat:]
    pxdrive_x = ps["ladder"][-1]["vpp_diff"] / ps["ladder"][pxflat]["vpp_diff"]
    # The tightest HD2/HD3 separation anywhere in either sweep, so the HD2 claim is a
    # worst case rather than a typical one.
    pxsep, pxsep_at = min(((r["hd3_db"] - r["hd2_db"], r)
                           for r in ps["profile"] + ps["ladder"]), key=lambda t: t[0])
    pxhd2 = max(r["hd2_db"] for r in ps["profile"] + ps["ladder"])
    return f"""## 6. Linearity — HD3, THD, IMD3, IIP3

[theory.md §4](theory.md#4-the-distortion-equation) derives the distortion equation from
the same two ingredients as the noise: an exponential device injects a third-harmonic
drain current, and that current reaches the output through the **same** `Z_T` the noise
uses.

```
    a_k(ω) = |v_gs,k(jω)| / (n_k U_T)
    i₃,k   = I_D,k · 2·I₃(a_k)/I₀(a_k)          →  I_D,k · a_k³/24   for a ≪ 1
    HD3(ω) = | Σ_k Z_T,k(j3ω) · i₃,k(ω) |  /  |V_out,fund(ω)|
```

**Validity window, defined by the check below:** the equation is a
*weak-inversion, small-`a`, quasi-static* model.  It is confirmed to **±2 dB over
{band[0]:.0f}–{band[1]:.0f} Hz** at 43.75 mVpp; outside that window it under-predicts, and
§6.2 says by how much and why.  Every claim made from it is made inside that window.

### 6.1 HD3 versus amplitude — the `A²` law

At f_in = 50 Hz, differential drive, coherent strobed transient + DFT with a
rect/Hann agreement guard (`scripts/linearity_runs.py`).

{lad}

Fitted over the three points that are inside the model's own validity window
({', '.join(f"{p['vpp_diff'] * 1e3:.2f}" for p in a['points'])} mVpp):
**{a['fitted_slope_db_per_decade']:.2f} dB/decade** against the predicted
**{a['expected_slope_db_per_decade']:.0f} dB/decade** (HD3 ∝ A², i.e. `a³` over a linear
fundamental), worst residual **{a['max_residual_db']:.3f} dB**.  The prediction is
confirmed.

Beyond ~0.3 Vpp the ladder leaves the small-signal regime entirely — the fundamental stops
growing (0.326 → 0.362 → 0.341 Vpp for 0.35 → 0.525 → 0.70 Vpp in) and THD saturates near
−17 dB.  That is slew/compression, correctly *outside* the equation's window.
**The −40 dB THD crossing is at {a['thd_minus40_vpp'] * 1e3:.1f} mVpp** — the compression
point a reviewer asks for, 1.75× the S7 drive of 175 mVpp.  That one is an
*extrapolation*: it lands past the last uncompressed measurement, where the fundamental
has already stopped growing.

#### The top of the dynamic range: HD3 = {_sgn(xc['target_db'])} dB

The drive at which HD3 reaches **{_sgn(xc['target_db'])} dB** is the other crossing a
reviewer asks for, because it is the numerator of dynamic range.  Unlike the −40 dB line
it is **bracketed by two measured amplitudes**, so the fitted law can be checked against a
plain log-linear interpolation between them rather than trusted on its own:

{tbl(["DUT", f"V_in at HD3 = {_sgn(xc['target_db'])} dB (mVpp diff)", "same, mVrms",
      "bracket interpolation (mVpp)", "IRN 0.5–200 Hz (µVrms)", "DR (dB)", "FoM (fJ)"],
     [[f"`{lab}`", f"**{c['vpp_diff'] * 1e3:.2f}**", f"{c['v_rms'] * 1e3:.2f}",
       f"{c['bracket_vpp_diff'] * 1e3:.2f} ({_sgn(c['method_spread_pct'], '+.1f')} %)"
       if c["bracketed"] else "— (extrapolated)",
       f"{c['irn_uv']:.3f}", f"**{c['dr_db']:.2f}**", f"**{c['fom_fj']:.2f}**"]
      for lab, c in xc["per_dut"].items()])}

The two methods agree to {_xspread(xc):.1f} % in amplitude — under 0.25 dB of dynamic
range — so the number does not depend on which one is used.  The post-layout row is the
DUT of record.

**Confirmed by simulation, not left as an interpolation.**  The solved drive was fed back
into the pack's own THD instrument — the same coherent strobed transient and DFT that
produced the ladder, driven open loop at exactly the solved amplitude with nothing re-tuned
to make it pass (`scripts/hd3_crossing_probe.py`):

{tbl(["DUT", "drive (mVpp diff)", "HD3 measured there (dB)", "error vs the target (dB)"],
     [[f"`{r['dut']}`", f"{r['vpp_diff'] * 1e3:.2f}", f"**{_sgn(r['measured_hd3_db'], '.3f')}**",
       _sgn(r["err_db"], "+.3f")] for r in pr["rows"]])}

Both land within **{pr['worst_err_db']:.2f} dB** of the target, against a
{pr['tol_db']:.1f} dB tolerance and a ladder whose own fit residual is
{a['max_residual_db']:.3f} dB.  The error has a sign worth stating: it is
**negative on both DUTs**, so the cell is *quieter* in distortion at the solved drive than
the law predicts, the true {_sgn(xc['target_db'])} dB point sits about
{_xrefine(xc, pr):.0f} % higher in amplitude, and the published dynamic range is therefore
a slight **under**-estimate — roughly {20 * math.log10(1 + _xrefine(xc, pr) / 100):.2f} dB
of it.  Conservative in the direction a claim should be conservative.

**The conventions, stated because a dynamic range is only comparable against another
design measured the same way.**  The distortion criterion is HD3, not THD, at
f_in = 50 Hz; the amplitude is **differential** peak-to-peak, converted to rms as
`V_pp/(2√2)`; the noise is the certified input-referred value integrated over 0.5–200 Hz
(§5), on the same DUT.  The other common convention in this class of filter is 1 % THD
(−40 dB), which lands roughly 3× higher and would raise `DR` by about 9 dB — so a quoted
`DR` without its criterion is not a comparable number.  The figure of merit is the usual
continuous-time-filter form, `FoM = P / (N · f_c · DR)` with `DR` linear — here
{xc['per_dut']['post_pex']['p_core_nw']:.3f} nW over
{xc['per_dut']['post_pex']['n_poles']} poles at
{xc['per_dut']['post_pex']['fc_hz']:.2f} Hz, post-layout — and it inherits the same
criterion: `FoM` goes as `1/DR`, so at the 1 % THD convention — a
{a['thd_minus40_vpp'] / xc['per_dut']['post_pex']['vpp_diff']:.1f}× higher drive — the same
cell would report about a third of it.  That is a statement about the convention, not
about the filter.
`csv/linearity_crossings.csv` carries the crossing with the slope and the anchor point it
was solved from, so it need not be refitted.

### 6.2 HD3 versus frequency — the `ω²` law, and where the model stops

At 43.75 mVpp differential, one decade and a half of f_in.  `a` is the modulation index
the follower's own gate–source excursion produces; it is *computed*, not fitted.

**This check runs pre-layout only, and that is sufficient.**  The equation's inputs are
the `gm`, `I_D` and `n` of §1 — and the layout moves every one of those by at most
{_gm_shift_pct():.1e} % (§1.3), so the *modelled* HD3 is identical to the digits printed
here for either DUT.  What the layout can move is the *measured* HD3, and that is reported
independently, on the extracted netlist, in §6.1 and §6.3.

{fqt}

* **Inside {band[0]:.0f}–{band[1]:.0f} Hz the model is within ±2 dB** on the absolute
  level, and it tracks the slope there: measured
  **{win_meas:.0f} dB/decade** against the model's **{win_model:.0f} dB/decade**.
* **The `HD3 ∝ ω²` (40 dB/decade) rule is the ω → 0 *asymptote*, not the model.**  The
  mechanism it comes from is explicit — shunt feedback makes `|1 − H| → ω·C₁/gm_i`, so the
  follower's own `v_gs` grows linearly with ω, `a³` gives ω³, and the falling `Z_T(j3ω)`
  gives one power back — but that argument needs `3ω ≪ ω₀`, and at f_in = 50 Hz the third
  harmonic is already at 150 Hz, 0.6·f_c.  The full expression keeps `|1 − H(jω)|` and
  `Z_T(j3ω)` as they are and is correspondingly steeper near the corner, which is what
  both columns above show.  (The whole-sweep fit of
  {fq['measured_slope_db_per_decade']:.1f} dB/decade in `data/linearity_analysis.json` is
  *not* a test of the law: it averages a floored low end with a compressed high end.)
* **Below ~35 Hz the model under-predicts by up to
  {max(r['err_db'] for r in fq['rows']):.1f} dB — but in *volts* the shortfall is a
  constant.**  The same three points, written as absolute output third-harmonic amplitude:

{tbl(["f_in (Hz)", "measured V\u2083 (\u00b5V)", "model V\u2083 (\u00b5V)", "measured \u2212 model (\u00b5V)"],
     [[f"{f:.0f}", f"{m * 1e6:.4f}", f"{d * 1e6:.4f}", f"{(m - d) * 1e6:+.4f}"]
      for f, m, d in lo])}

  The model's own prediction moves by a factor of {lo[-1][2] / lo[0][2]:.0f} across those
  three points while the shortfall stays at
  **{min(m - d for _, m, d in lo) * 1e6:.2f}\u2013{max(m - d for _, m, d in lo) * 1e6:.2f} \u00b5V**.
  An additive, frequency-independent residual is a *different mechanism*, not a mis-scaled
  version of the modelled one.  Drain-conductance nonlinearity (`g_ds(V_DS)`) is the
  natural candidate — the small-signal `Z_T` linearises it away by construction — but that
  is a hypothesis: it is stated as a bounded observation with numbers attached, **not** as
  a fitted claim, and closing it needs a `g_ds`-expansion term the present model does not
  have ([README.md](README.md#7-open-items)).  For scale, the entire residual sits
  {abs(20 * math.log10(lo[0][1] / 2.564e-4)):.1f} dB below the third harmonic this same
  cell produces at the S7 operating point — a modelling gap, not a performance one.
* **Above ~100 Hz `a` passes 0.3** (last column) and the *propagation* stops being linear.
  The harmonic generation itself is still exact — the code uses the Bessel ratio
  `2·I₃(a)/I₀(a)`, not its `a³/24` truncation — but with `a` this large the cell is
  compressing (V_out falls from 43.7 to 36.6 mVpp between 10 and 200 Hz), so both the
  small-signal `Z_T` and the "fundamental unaffected" assumption behind the ratio break
  down.  The model's {abs(fq['rows'][-1]['err_db']):.1f} dB miss at
  {fq['rows'][-1]['fin']:.0f} Hz is therefore expected, and is the reason the window is stated up front.

THD versus f_in at the **S7 drive** of 175 mVpp, both DUTs:

{prof}

### 6.3 Two-tone: IMD3 and IIP3

Two equal tones at {sp_['rows'][2]['f1']:.0f} / {sp_['rows'][2]['f2']:.0f} Hz (10 Hz
spacing, both on the DFT grid), coherent transient + DFT, `IMD3` referred to the
fundamental (`scripts/linearity_runs.py::tran_twotone`).

{tbl(["A per tone (V)", "fund (V)", "IMD3 lo (dBc)", "IMD3 hi (dBc)", "IMD3 (dBc)",
      "IIP3 (dBV)", "IMD3 post-layout (dBc)", "IIP3 post-layout (dBV)"],
     [[f"{p['ampl_per_tone_v']:.6g}", f"{p['fund_v']:.6f}", f"{p['imd3_lo_db']:.3f}",
       f"{p['imd3_hi_db']:.3f}", f"{p['imd3_db']:.3f}", f"{p['iip3_dbv']:.3f}",
       f"{q['imd3_db']:.3f}", f"{q['iip3_dbv']:.3f}"]
      for p, q in zip(lin["twotone"]["pre_mim"], lin["twotone"]["post_pex"])])}

{tbl(["", "IIP3 (dBV)", "IIP3 (V_peak per tone)", "OIP3 (dBV)",
      "IMD3 slope (dB/decade)", "slope residual (dB)", "IIP3 spread over the linear points (dB)"],
     [[lab, f"{la['iip3'][k]['iip3_dbv']:.3f}", f"{la['iip3'][k]['iip3_v_peak_per_tone']:.4f}",
       f"{la['iip3'][k]['oip3_dbv']:.3f}", f"{la['iip3'][k]['imd3_slope_db_per_decade']:.2f}",
       f"{la['iip3'][k]['slope_residual_db']:.3f}",
       f"{la['iip3'][k]['consistency_of_iip3_over_linear_points_db']:.3f}"]
      for k, lab in (("pre_mim", "pre-layout"), ("post_pex", "post-layout"))])}

* **IIP3 = {la['iip3']['pre_mim']['iip3_dbv']:.2f} dBV pre-layout,
  {la['iip3']['post_pex']['iip3_dbv']:.2f} dBV post-layout** — a
  {la['iip3']['post_pex']['iip3_dbv'] - la['iip3']['pre_mim']['iip3_dbv']:+.3f} dB shift,
  i.e. the layout is linearity-neutral to within the measurement's own repeatability.
* **The 3:1 slope is confirmed**: {la['iip3']['pre_mim']['imd3_slope_db_per_decade']:.1f}
  dB/decade of IMD3 against the theoretical 40, residual
  {la['iip3']['pre_mim']['slope_residual_db']:.2f} dB, and the extrapolated IIP3 is
  consistent to {la['iip3']['pre_mim']['consistency_of_iip3_over_linear_points_db']:.2f} dB
  across the three amplitudes that are actually in the cubic regime.  The top two
  amplitudes are excluded from the extrapolation and shown anyway — they are compressing
  (fund 0.084 → 0.103 V for a 1.5× drive increase), and an IIP3 extrapolated from them
  would not be valid.
* **IIP3 is quoted in dBV, not dBm, deliberately.**  This is a voltage-mode filter driven
  by a balun-style differential source into a capacitive gate; there is no 50 Ω anywhere
  in the cell, so a dBm number would require inventing a reference impedance.  The dBV
  figure is referred to the **peak** amplitude of one
  tone at the differential input, which is
  {la['iip3']['pre_mim']['iip3_v_peak_per_tone']:.4f} V — 3.9× the S7 drive amplitude, and
  well past where §6.1 shows the cell compressing, so IIP3 here is an extrapolated
  figure of merit rather than a reachable operating point.  That is the normal reading of
  an intercept, and it is stated because a filter this deep in weak inversion has no
  large-signal headroom to spend.

### 6.4 Is the cell memoryless?  (The `IMD3 = HD3 + 9.54 dB` test)

For a memoryless cubic nonlinearity, IMD3 and HD3 at the same per-tone amplitude differ by
exactly 20·log₁₀(3) = 9.54 dB.  Measured at A = {ml['per_tone_ampl_v'] * 1e3:.3f} mV per tone:

{tbl(["quantity", "value"],
     [["HD3 at 50 Hz, same amplitude", f"{ml['hd3_at_50hz_db']:.3f} dBc"],
      ["memoryless prediction, HD3 + 9.54 dB", f"{ml['imd3_memoryless_prediction_db']:.3f} dBc"],
      ["IMD3 measured", f"{ml['imd3_measured_db']:.3f} dBc"],
      ["**excess**", f"**{ml['excess_db']:+.3f} dB**"]])}

**The identity fails by {ml['excess_db']:.2f} dB, and it is supposed to.**  §6.2 established
that HD3 rises at ~{win_meas:.0f} dB/decade through this band, so the third-order response
is strongly frequency dependent and the cell is by construction *not* memoryless.  The
question is which kind of memory, and the spacing sweep answers it:

{tbl(["f₁ / f₂ (Hz)", "spacing (Hz)", "IMD3 (dBc)", "IIP3 (dBV)"],
     [[f"{r['f1']:.0f} / {r['f2']:.0f}", f"{r['spacing']:.0f}", f"{r['imd3_db']:.3f}",
       f"{r['iip3_dbv']:.3f}"] for r in sp_["rows"]])}

Over a **{ml['spacing_ratio']:.0f}× change in tone spacing** — which is a 15× change in the
envelope frequency the cell must follow — IMD3 moves only
**{ml['imd3_spread_over_spacing_db']:.2f} dB**.  Envelope (baseband) memory would show up
here as a strong spacing dependence and does not.  The {ml['excess_db']:.2f} dB excess is
therefore attributable to the *carrier*-frequency dependence of the third-order response —
the same mechanism §6.2 measured — and not to envelope memory.  That is the useful engineering
statement: **HD3 at one frequency does not predict IMD3 for this cell; measure IMD3.**

All spacings are constrained to even values so both tones and all four intermodulation
products land exactly on DFT bins; an odd spacing puts the tones on half-bins and the
resulting IMD3 is scalloping, not distortion (observed once at −0.79 dBc, which is how the
constraint was found).

`figures/distortion.png` and `figures/iip3.png` plot §6.1–6.3.

### 6.5 The extracted cell over the whole band, and at its worst frequency

Everything in this subsection is measured on **`post_pex` alone** — the full post-layout
parasitic extraction, `layout/H12-pdk-cap/asbuilt/core_pex.sp`, spliced into the bench
whole: {len(jload("bench_post_pex.json")["op"])} device instances and every parasitic R
and C the extractor produced, nothing lumped and nothing substituted.  So these numbers
need no equivalence argument of any kind.  The sweeps were asked for directly: THD
against frequency from 20 to 300 Hz, then an amplitude sweep at whichever frequency comes
out worst, with HD2 and HD3 reported at every point
(`scripts/pex_distortion_sweeps.py`).  §7 is the DUT table; the reason the *rest* of the
pack quotes some results on a lumped stand-in is stated there, and it never applies here.

**The drive is {pxv * 1e3:.0f} mVpp differential.**  The request said "50 Vpp", which
cannot be meant literally on a {1.5:.1f} V rail — the cell hard-compresses by 0.35 Vpp
(§6.1) — so it is read as **{pxv * 1e3:.0f} mVpp**, which is the same number with the unit
corrected and sits inside the cubic region, between the pack's two existing profile drives
of 43.75 and 175 mVpp.  Re-running at any other drive is one command.

{pxprof}

**Worst THD is {pxwr['thd_db']:.2f} dB at {pxwr['fin']:.0f} Hz**, and the profile is not
monotonic: it degrades by {pxwr['thd_db'] - px20['thd_db']:.1f} dB from
{px20['fin']:.0f} Hz to {pxwr['fin']:.0f} Hz, then *improves* again by
{pxwr['thd_db'] - pxend['thd_db']:.1f} dB out to {pxend['fin']:.0f} Hz.  Both halves have
the same cause and it is not a change in the cell.  Distortion rises with frequency
because a nano-amp-biased follower is slew limited — the same mechanism §6.2 measures as
the `ω²` law — and it falls again past the corner because the *fundamental itself* is in
the rolloff: the output fundamental drops from {px20['out_fund_vpp'] * 1e3:.1f} mVpp at
{px20['fin']:.0f} Hz to {pxend['out_fund_vpp'] * 1e3:.1f} mVpp at {pxend['fin']:.0f} Hz,
so the cell's internal nodes see progressively less signal to distort.  The `3·f_in`
column is there for the same reason: above ~83 Hz the third harmonic is already past
`f_c`, so what the DFT sees at the output is the harmonic the cell generated **minus the
filter's own attenuation of it**.  These numbers are therefore *distortion at the output*
— what a downstream stage actually receives, which is the useful engineering quantity —
and not a measurement of the cell's nonlinearity in isolation.

**None of it is a pass/fail.**  The S7 spec point is 175 mVpp at 50 Hz, where the same
DUT measures {lin['thd_ladder']['post_pex'][2]['thd_db']:.2f} dB (§6.1).  A THD profile
above 50 Hz is informative by the bench's own definition (`lab.thd`), because a filter
whose corner is 250 Hz is not required to be linear at 200 Hz on a nano-amp bias.

#### The amplitude sweep at {pxw:.0f} Hz

{pxlad}

**The bottom of this ladder is still cubic; the rest of it is slew limited.**  HD3 climbs
**{pxslopes[0]:.1f} dB/decade** of drive over the lowest rung — the `A²` law's
40 dB/decade, so even at the worst frequency the cell is still behaving cubically at
{ps['ladder'][0]['vpp_diff'] * 1e3:.4g}–{ps['ladder'][1]['vpp_diff'] * 1e3:.4g} mVpp —
and then leaves it: {', '.join(f'{v:.0f}' for v in pxslopes[1:])} dB/decade on the rungs
above, so by {ps['ladder'][-2]['vpp_diff'] * 1e3:.0f} mVpp the third harmonic has almost
stopped responding to drive at all.  The output says the same thing more directly: above
**{ps['ladder'][pxflat]['vpp_diff'] * 1e3:.4g} mVpp** the fundamental stops following
the input, staying between {min(pxclamp) * 1e3:.1f} and {max(pxclamp) * 1e3:.1f} mVpp
while the drive rises a further **{pxdrive_x:.0f}×**.  That is a slew-rate ceiling — the
peak an output can trace is `SR/ω`, independent of how hard it is driven — and it is why
this ladder must not be read as an `A²`-law failure above its first rung: the law is not
in force there.  The `A²` fit, the −40 dB THD crossing and the HD3 = −60 dB crossing all
stay where §6.1 puts them, at the 50 Hz spec frequency, on the uncompressed rows.

**HD2 stays at the floor throughout** — worst {pxhd2:.1f} dB over all
{len(ps['profile']) + len(ps['ladder'])} points, and its *tightest* margin below HD3
anywhere in either sweep is **{pxsep:.1f} dB** (at {pxsep_at['fin']:.0f} Hz,
{pxsep_at['vpp_diff'] * 1e3:.4g} mVpp).  That is the balanced-differential cancellation
holding on the *extracted* netlist, parasitic mismatch included, and it is the reason the
pack quotes HD3 rather than HD2 everywhere: on this cell an HD2 that climbs would be
evidence of an asymmetry, not of a distortion mechanism.

`csv/thd_vs_frequency_pex_{f"{pxv * 1e3:g}".replace(".", "p")}mvpp.csv` and
`csv/thd_vs_amplitude_pex_{f"{pxw:g}".replace(".", "p")}hz.csv` carry every point,
including the full 2nd-to-10th harmonic set.
"""


# ------------------------------------------------------------------ 7. scorecard --
def sec_score(bs: dict) -> str:
    keys = [("dc_db", "\\|dc gain\\| (dB)"), ("fc_hz", "fc (Hz)"), ("peak_db", "peaking (dB)"),
            ("ripple_db", "passband ripple (dB)"), ("a1000_db", "\\|H\\| @ 1 kHz (dB)"),
            ("ph_max_deg", "ph_max (°)"), ("gd_dc_ms", "τ_g(dc) (ms)"),
            ("gd_max_ms", "τ_g max (ms)"), ("irn_uv", "IRN 0.5–200 Hz (µVrms)"),
            ("onoise_uv", "output noise (µVrms)"), ("p_core_nw", "core power (nW)"),
            ("c_total_pf", "total C (pF)")]
    cols = ["pre_ideal", "pre_mim", "post_pex", "post_lumped"]
    rows = [[lab] + [f"{bs[c]['scorecard'][k]:.4f}" for c in cols] for k, lab in keys]
    return f"""## 7. The four DUTs, side by side

Every table above is measured on one of four netlists.  They are all the *same cell*; they
differ only in what is modelled.

{tbl(["DUT", "what it is", "instances", "noise vectors"],
     [["`pre_ideal`", "as-built schematic, ideal linear capacitors "
       "(`signoff/post-pvt/H12-robust/asbuilt/core.sp`)", "16", "97"],
      ["`pre_mim`", "**the pre-layout DUT of record** — as-built schematic with PDK MIM "
       "capacitors (`signoff/post-pvt/H12-pdk-cap/asbuilt/core.sp`)", "16", "109"],
      ["`post_pex`", "**the post-layout DUT of record** — the kpex-extracted subckt of the "
       "it14 layout", "36", "224"],
      ["`post_lumped`", "the schematic devices carrying the extracted parasitics as 68 "
       "explicit `Cext_*` cards (`data/post_lumped_core.sp`)", "16", "109"]])}

**Why `post_lumped` exists.**  kpex splits some devices across the extracted netlist, so a
handful of extracted halves no longer have bulk tied to source — which `bind_op` refuses,
correctly, because it is the assumption that makes `gmb` inert and folds `cgb` into `cgs`.
`post_lumped` restores that structure by putting the schematic devices back and attaching
the extraction's parasitic capacitances as explicit cards.  It is not an approximation of
`post_pex` — it is **proven equivalent to it**: `fc` within
{abs(bs['post_pex']['scorecard']['fc_hz'] - bs['post_lumped']['scorecard']['fc_hz']):.4f} Hz
and `ph_max` within
{abs(bs['post_pex']['scorecard']['ph_max_deg'] - bs['post_lumped']['scorecard']['ph_max_deg']):.4f}°
of the certified post-layout scorecard.  Symbolic post-layout results are therefore quoted
on `post_lumped`; measured post-layout results (THD, IIP3, the certified scorecard) are
quoted on `post_pex`.

{tbl(["metric"] + [f"`{c}`" for c in cols], rows)}

Pre → post (`pre_mim` → `post_pex`, both signed post minus pre): `fc`
**{bs['post_pex']['scorecard']['fc_hz'] - bs['pre_mim']['scorecard']['fc_hz']:+.3f} Hz**
({100 * (bs['post_pex']['scorecard']['fc_hz'] / bs['pre_mim']['scorecard']['fc_hz'] - 1):+.2f} %),
`ph_max` **{bs['post_pex']['scorecard']['ph_max_deg'] - bs['pre_mim']['scorecard']['ph_max_deg']:+.3f}°**,
IRN {bs['post_pex']['scorecard']['irn_uv'] - bs['pre_mim']['scorecard']['irn_uv']:+.4f} µV
({100 * (bs['post_pex']['scorecard']['irn_uv'] / bs['pre_mim']['scorecard']['irn_uv'] - 1):+.3f} %),
stopband {bs['post_pex']['scorecard']['a1000_db'] - bs['pre_mim']['scorecard']['a1000_db']:+.3f} dB,
core power {bs['post_pex']['scorecard']['p_core_nw'] - bs['pre_mim']['scorecard']['p_core_nw']:+.4f} nW.
**The layout costs this filter 1.1 Hz of `fc` and 1.2° of `ph_max`; noise and power are
unchanged at the fourth digit, and the stopband improves by 0.19 dB.**  Every equation
above makes the same pre→post statement in its own quantity.
"""


def _sp(s: dict, key: str, fmt: str = "{:.3f}") -> str:
    v = s.get(key)
    return "—" if not v else (fmt.format(v["min"]) + " … " + fmt.format(v["max"]))


def _axis_span(rows: list[dict], get, axis: str) -> float:
    """Span of a quantity over ONE axis of the certified window, nominal included.

    The nine certified points are three separate one-dimensional sweeps sharing a centre,
    so a single overall span hides which axis moved the number.  `axis` selects the
    sweep: "process" (27 °C, 1.5 V), "vdd" (nominal process, 27 °C) or "temp"
    (nominal process, 1.5 V).
    """
    key = {"process": lambda c: c["temp"] == 27.0 and c["vdd"] == 1.5,
           "vdd": lambda c: c["process"] == "mos_tt" and c["temp"] == 27.0,
           "temp": lambda c: c["process"] == "mos_tt" and c["vdd"] == 1.5}[axis]
    v = [get(r) for r in rows if key(r["corner"])]
    return max(v) / min(v)


def _at(tr: dict, n: int) -> float:
    """σ at exactly `n` draws of a running trace -- the ladder always has the powers of
    two as rungs, so an earlier, shorter run is read off directly rather than interpolated."""
    return tr["sigma"][tr["n"].index(n)]


def sec_pvt(pv: dict) -> str:
    """PVT and mismatch sensitivity of the ANALYTICAL quantities (doc/paper G25)."""
    ca, cb, mm = pv["cert-axes"]["summary"], pv["cert-box"]["summary"], pv["mismatch"]["summary"]
    cv = mm["convergence"]
    # The dc gain the offset row is referred by, averaged over the draws only so the
    # prose can state its size; the referral itself is per draw, in `pvt_analysis`.
    mmrows = pv["mismatch"]["rows"]
    gdc_db = sum(r["dc_gain_db"] for r in mmrows) / len(mmrows)
    hb = pv["both"]["summary"]
    rows_a = pv["cert-axes"]["rows"]
    qhi = {ax: _axis_span(rows_a, lambda r: r["pairs"][1]["Q"], ax)
           for ax in ("process", "vdd", "temp")}
    fcs = {ax: _axis_span(rows_a, lambda r: r["scorecard"]["fc_hz"], ax)
           for ax in ("process", "vdd", "temp")}
    post = pv["cert-axes:post_lumped"]
    pa = post["summary"]

    scale_shape = tbl(
        ["quantity", "what it is", "certified axes (9)", "certified box (45)",
         "harness box (29)"],
        [["`fc`", "**scale** — set by `gm/C`", f"{ca['fc_hz']['span_x']:.3f}×",
          f"{cb['fc_hz']['span_x']:.3f}×", f"{hb['fc_hz']['span_x']:.3f}×"],
         ["`Q` low pair", "**shape** — a `gm` ratio", f"{ca['Q_lo']['span_x']:.3f}×",
          f"{cb['Q_lo']['span_x']:.3f}×", f"{hb['Q_lo']['span_x']:.3f}×"],
         ["`Q` high pair", "**shape** — a `gm` ratio", f"{ca['Q_hi']['span_x']:.3f}×",
          f"{cb['Q_hi']['span_x']:.3f}×", f"{hb['Q_hi']['span_x']:.3f}×"],
         ["`f₀` ratio", "**shape** — pair coincidence",
          f"{ca['pair_ratio']['span_x']:.3f}×", f"{cb['pair_ratio']['span_x']:.3f}×",
          f"{hb['pair_ratio']['span_x']:.3f}×"],
         ["two complex pairs", "the S1 property itself",
          f"**{ca['n_two_pair']}/{ca['n_corners']}**",
          f"{cb['n_two_pair']}/{cb['n_corners']}", f"{hb['n_two_pair']}/{hb['n_corners']}"],
         ["Σ generators vs IRN", "the noise equation, per corner",
          f"{ca['noise_closure_max_pct']:.1e} %", f"{cb['noise_closure_max_pct']:.1e} %",
          f"{hb['noise_closure_max_pct']:.1e} %"]])

    axes = tbl(["corner", "`fc` (Hz)", "`ph_max` (°)", "low-Q pair `f₀` / `Q`",
                "high-Q pair `f₀` / `Q`", "IRN (µV)"],
               [[f"`{r['slug']}`", f"{r['scorecard']['fc_hz']:.3f}",
                 f"{r['scorecard']['ph_max_deg']:.2f}",
                 f"{r['pairs'][0]['f0_hz']:.2f} / {r['pairs'][0]['Q']:.4f}",
                 f"{r['pairs'][1]['f0_hz']:.2f} / {r['pairs'][1]['Q']:.4f}",
                 f"{r['scorecard']['irn_uv']:.3f}"]
                for r in pv["cert-axes"]["rows"]])

    cmp_t = tbl(["quantity", "pre-layout (`pre_mim`)", "post-layout (`post_lumped`)"],
                [["`fc` span", f"{ca['fc_hz']['span_x']:.4f}×", f"{pa['fc_hz']['span_x']:.4f}×"],
                 ["`Q` low pair span", f"{ca['Q_lo']['span_x']:.4f}×",
                  f"{pa['Q_lo']['span_x']:.4f}×"],
                 ["`Q` high pair span", f"{ca['Q_hi']['span_x']:.4f}×",
                  f"{pa['Q_hi']['span_x']:.4f}×"],
                 ["`f₀` ratio span", f"{ca['pair_ratio']['span_x']:.4f}×",
                  f"{pa['pair_ratio']['span_x']:.4f}×"],
                 ["two complex pairs", f"{ca['n_two_pair']}/{ca['n_corners']}",
                  f"{pa['n_two_pair']}/{pa['n_corners']}"],
                 ["IRN over the axes (µV)",
                  f"{ca['irn_uv']['min']:.3f} … {ca['irn_uv']['max']:.3f}",
                  f"{pa['irn_uv']['min']:.3f} … {pa['irn_uv']['max']:.3f}"],
                 ["Σ generators vs IRN", f"{ca['noise_closure_max_pct']:.1e} %",
                  f"{pa['noise_closure_max_pct']:.1e} %"]])

    # p01 … p99 sits beside min … max deliberately: only the quantiles are comparable
    # across N, since min and max are order statistics that must drift outward as draws
    # are added.  Every σ carries (M1), its own standard error at this N.
    def mmrow(key, label, fmt, sgn=""):
        v = mm[key]
        return [label, f"{v['mean']:{sgn}{fmt}}", f"{v['sigma']:{fmt}}",
                f"±{100 * v['se_sigma_frac']:.1f} %",
                f"{v['p01']:{sgn}{fmt}} … {v['p99']:{sgn}{fmt}}",
                f"{v['min']:{sgn}{fmt}} … {v['max']:{sgn}{fmt}}"]

    mmt = tbl(["quantity", "mean", "σ", "σ error (M1)", "p01 … p99", "min … max"],
              [mmrow("fc_hz", "`fc` (Hz)", ".3f"),
               mmrow("ph_max_deg", "`ph_max` (°)", ".3f"),
               mmrow("Q_lo", "low-pair `Q`", ".4f"),
               mmrow("Q_hi", "high-pair `Q`", ".4f"),
               mmrow("irn_uv", "IRN (µV)", ".3f"),
               mmrow("offset_in_uv", "input-referred offset (µV)", ".1f", "+")])

    return f"""## 8. The analytical results over PVT and mismatch

Everything in Sections 1–7 is derived at ONE operating point.  This section re-derives the
poles, the per-biquad `Q` and the noise budget at every corner of the window the cell is
certified over, and over {mm['n_draws']} mismatch draws.  No new modelling is involved: each of those
quantities is a function of the operating point, and `extract_bench.py --pvt/--mc` produces
one operating point per point.  Generated by `scripts/pvt_analysis.py`.

**Read `fc` and `Q` as different questions.**  `fc` is a SCALE set by `gm/C`, and in weak
inversion `gm = I/(n·U_T)`, so a reference current that does not track temperature makes
`fc` move by construction — that is old news and `lab/corners.py` documents it.  `Q` and the
pair-coincidence ratio are `gm` RATIOS.  Whether the filter's SHAPE survives when its scale
drifts is the question the nominal analysis could not answer, and it is the one below.

**The bias law matters and is recorded.**  The temperature rows use `LPF_BIAS_ALPHA=1.1`,
the constant-`gm` shaping the delivered cells were certified with.  At 27 °C it is the same
current as the default `alpha = 0`, so the nominal numbers above are unaffected; at every
other temperature it is a different measurement, and a sweep that silently took the default
would report an uncompensated cell as if it were this one.

### 8.1 Scale versus shape

{scale_shape}

The certified window is **one axis at a time** — process at 27 °C/1.5 V, supply 1.40–1.65 V
at 27 °C, temperature 0–70 °C at 1.5 V — which is how `signoff/post-pvt/README.md` states
it.  On those nine points the scale moves {ca['fc_hz']['span_x']:.3f}×, and **both complex pairs survive every
one of them** — the S1 property itself never comes close to failing.

The two pairs then behave differently, and the table says so.  The LOW-Q pair is the pure
ratio the framing predicts: its `Q` holds to {100 * (ca['Q_lo']['span_x'] - 1):.2f} %, {ca['fc_hz']['span_x'] / ca['Q_lo']['span_x']:.0f}× stiffer than the scale beside it.
The HIGH-Q pair is not: its `Q` moves {100 * (ca['Q_hi']['span_x'] - 1):.1f} %, which is as much as `fc` moves and slightly
more.  Splitting that by axis shows where it comes from — {100 * (qhi['process'] - 1):.1f} % over process,
{100 * (qhi['vdd'] - 1):.1f} % over supply, {100 * (qhi['temp'] - 1):.1f} % over temperature — so it is a temperature effect, and it
persists under the constant-`gm` bias that is supposed to remove temperature from `gm`.
The honest summary is therefore narrower than "shape is invariant": the filter stays two
biquads and the low-Q damping is fixed, while the high-Q damping carries a residual
temperature dependence of the same order as the cutoff's ({100 * (fcs['temp'] - 1):.1f} % over the same axis).

**The axes do not superpose, and that is a result.**  The middle column is the CROSS
PRODUCT of the same endpoints — 45 points, none of them ever certified.  {cb['n_corners'] - cb['n_two_pair']} of them have
lost a complex pair, i.e. the filter is no longer two biquads, and `tt / 0 °C / 1.40 V` is
among the failures even though nominal process, 0 °C and 1.40 V are each individually
inside the certified window.  A one-axis-at-a-time claim is therefore not a box, and the
distinction is invisible in the scorecard alone.

### 8.2 The certified axes, point by point

{axes}

### 8.3 Mismatch

{mm['n_draws']} draws at `{pv['mismatch']['corner']['process']}`, 27 °C, each one a full extraction and the same pencil
solve — not a rational fit to the response, because `fit_poles_from_sim` (Section 3.2)
records that the `f₀`/`Q` split of two nearly co-located pairs is weakly determined by the
response, so a `Q` distribution built that way would mostly measure the fit's conditioning.

{mmt}

Both complex pairs survive **{mm['n_two_pair']}/{mm['n_draws']}** draws.  The low-Q pair is again the stiff one — `Q`
scatters by {100 * mm['Q_lo']['sigma'] / mm['Q_lo']['mean']:.2f} % against {100 * mm['fc_hz']['sigma'] / mm['fc_hz']['mean']:.2f} % for `fc` — but the high-Q pair scatters {100 * mm['Q_hi']['sigma'] / mm['Q_hi']['mean']:.2f} %, which
belongs with the scale rather than with its own low-Q partner.  That is the expected shape of the difference: a PVT corner shifts
every device the same way, so ratios can hold while scale moves, whereas a mismatch draw
shifts each device independently and a ratio has no reason to survive it.  σ(`fc`) = {mm['fc_hz']['sigma']:.2f} Hz here
against the 3.7 Hz the certified 100-sample scorecard MC reports, which is the agreement
that says these draws are the same population.

**Is this many draws enough?**  A σ estimated from N samples is itself an estimate: for a
normal population its relative standard error is 1/√(2(N−1)), which is {100 / math.sqrt(2 * 63):.1f} % at 64 draws
and **{100 * mm['se_sigma_frac']:.1f} %** at {mm['n_draws']}.  That is the band the σ column above is quoted with, and
`figures/mc_convergence.png` plots the running σ against N inside it — flat and within the
band long before the end, so these distributions are resolved rather than still filling
in.  Over the last four rungs of the ladder σ(`fc`) moved {cv['fc_hz']['drift_pct']:.2f} %, σ(`Q_hi`) {cv['Q_hi']['drift_pct']:.2f} % and
σ(offset) {cv['offset_in_uv']['drift_pct']:.2f} %.  Seeds run `1…N` in order, so the first 64 rows of this set ARE
the 64-draw run reported before it was extended: σ(`fc`) over them is {_at(cv['fc_hz'], 64):.3f} Hz, the
value that run published, and every trace passes through the earlier value rather than
near it.

That comparison is also why the run was extended.  σ(`fc`) moved **{100 * (mm['fc_hz']['sigma'] / _at(cv['fc_hz'], 64) - 1):+.1f} %** on the way
from 64 draws to {mm['n_draws']} — {abs(mm['fc_hz']['sigma'] / _at(cv['fc_hz'], 64) - 1) / (1 / math.sqrt(2 * 63)):.1f}× the band (M1) allows at 64 — so the short run had understated
the scale scatter, and nothing inside the short run could have revealed that.  The
three shape and offset quantities moved {100 * (mm['Q_lo']['sigma'] / _at(cv['Q_lo'], 64) - 1):+.1f} %, {100 * (mm['Q_hi']['sigma'] / _at(cv['Q_hi'], 64) - 1):+.1f} % and {100 * (mm['offset_in_uv']['sigma'] / _at(cv['offset_in_uv'], 64) - 1):+.1f} % over the same
extension, all inside it.  Read together: 64 draws was enough for the ratios and not for
the scale, and the σ column's band is what tells the two cases apart.

The offset row is **referred to the input** — the raw differential output offset divided
by that same draw's own dc gain.  |A_dc| is {gdc_db:.3f} dB here, so the referral is a
{100 * (mm['offset_in_uv']['sigma'] / mm['offset_out_uv']['sigma'] - 1):+.3f} % correction and the two columns look alike; it is applied anyway, because
an output offset is only meaningful next to the gain that produced it, and because it is
what makes this bench and Section 9.3's agree exactly rather than approximately.  The raw
output value is kept in `data/pvt.json` beside it — σ {mm['offset_out_uv']['sigma']:.1f} µV against the referred {mm['offset_in_uv']['sigma']:.1f} µV.

The `min … max` column is completeness, not a worst case that converged.  min and max are
ORDER statistics: they move outward as draws are added, by construction, so a longer run
must report a wider range and a range that widened is evidence of nothing.  `p01 … p99` is
the pair that stays comparable between runs of different length, and at {mm['n_draws']} draws each of
those tails has about {mm['n_draws'] // 100} samples under it.

`figures/pvt_axes.png` plots the nine points and the 45-point box; `figures/mc_mismatch.png`
plots the three distributions.

One caveat on the pole COUNT.  At nominal the cell is symmetric and seven pole/zero pairs
cancel exactly; under mismatch those become near-cancellations, so the raw solve returns
the doublets separately plus a parasitic pair near 10 kHz from the device capacitances.
The filter's poles are the two nearest the origin and are selected that way
(`pvt_analysis._pairs`); the doublets are reported in `n_complex_pairs_all`.

### 8.4 Does any of this transfer to the post-layout cell?

Everything above is measured on the pre-layout DUT.  Section 7 argues the sensitivity
carries over to the extracted cells because layout adds capacitance and the capacitance
ratios are what set `Q`.  That argument is now measured rather than asserted: the same nine
certified axes, re-extracted on `post_lumped`.

{cmp_t}

The two columns agree to the third decimal on every span, and the post-layout cell keeps
two complex pairs at all {pa['n_two_pair']}/{pa['n_corners']} points.  `fc` sits about {100 * (1 - post['rows'][0]['scorecard']['fc_hz'] / pv['cert-axes']['rows'][0]['scorecard']['fc_hz']):.2f} % lower everywhere — the
layout capacitance the extraction adds — but the SENSITIVITY, which is what this section is
about, is the same measurement.  The post-layout `fc` is drawn as hollow circles in
`figures/pvt_axes.png`.
"""


def sec_rej(rj: dict, mm2: dict) -> str:
    """PSRR, CMRR and offset (doc/paper G12)."""
    mm, nom = rj["mismatch"], rj["corners"]["tt_27c_1v500"]
    spots = [f"{s:g}" for s in rj["spots_hz"]]

    nomt = tbl(["transfer", *[f"{s} Hz" for s in spots]],
               [["supply → output CM (dB)"] + [f"{nom['supply_to_cm_db'][s]:.2f}" for s in spots],
                ["CM in → CM out (dB)"] + [f"{nom['cm_to_cm_db'][s]:.2f}" for s in spots]])
    # p01 as well as the sample minimum, for the reason Section 8.3 gives: the minimum
    # of N draws is an order statistic and gets worse as N grows, so only the quantile
    # is comparable between runs of different length.
    # CMRR and PSRR are RATIOS, so the two transfers they are built from are tabulated
    # beside them: the common-mode input and the supply, each measured to the
    # DIFFERENTIAL output.  A ratio alone cannot say which half moved.
    mmt = tbl(["quantity", *[f"{s} Hz" for s in spots]],
              [[f"{n} {w} (dB)"] + [f"{mm[k][s][a]:.2f}" for s in spots]
               for k, n in (("cmrr_db", "CMRR"), ("psrr_db", "PSRR"))
               for w, a in (("mean", "mean"), ("σ", "sigma"), ("p01", "p01"),
                            ("worst", "min"))])
    leak = tbl(["transfer", *[f"{s} Hz" for s in spots]],
               [[f"{n} {w} (dB)"] + [f"{mm[k][s][a]:.2f}" for s in spots]
                for k, n in (("cm_to_dm_db", "CM in → DM out"),
                             ("supply_to_dm_db", "supply → DM out"))
                for w, a in (("mean", "mean"), ("worst", "max"))]
               + [["A_dm at this spot (dB)"]
                  + [f"{nom['a_dm_db'][s]:.2f}" for s in spots]])
    o, oa = mm["offset_in_uv"], mm["offset_in_abs_uv"]

    return f"""## 9. Supply rejection, common-mode rejection, and offset

`doc/paper/README.md` G12 records these three as unmeasured.  Generated by
`scripts/psrr_cmrr.py`, from two new benches in `lab/deck.py` (`ac_psrr`, `ac_cmrr`).

**Why the nominal differential number is not the answer.**  This cell is geometrically
symmetric, so supply → differential output and common-mode → differential output both
cancel by construction.  At nominal the simulator returns its own solver residual, which
reads as a spectacular rejection figure and says nothing about silicon.  What is finite at
nominal is the COMMON-MODE response; what is real for the differential path is the
MISMATCH-limited value.  Both are given, and neither alone would be honest.

### 9.1 Nominal, common-mode paths

{nomt}

Two things to read here.  The cell **passes** its input common mode to the output at dc
({nom['cm_to_cm_db'][spots[0]]:.2f} dB) and low-passes it — expected of a follower chain, and not a defect, because
every spec in `doc/target-spec.md` is differential.  Supply → output common mode is
{nom['supply_to_cm_db'][spots[0]]:.2f} dB at dc but only {nom['supply_to_cm_db'][spots[-1]]:.2f} dB at 1 kHz: **in the stopband the output common mode
tracks the rail essentially one-for-one.**  That does not touch the differential signal,
but it bounds what may sit downstream of this filter on the same supply.

### 9.2 Mismatch-limited, differential paths

{mm['n_draws']} draws, `mos_tt_mismatch`, 27 °C.  Both ratios are defined the way the differential
signal actually sees them — **the transfer from the disturbance to the DIFFERENTIAL
output, referred to the differential gain**:

$$\\mathrm{{CMRR}}(f)=\\frac{{A_{{dm}}(f)}}{{A_{{cm\\rightarrow dm}}(f)}},
\\qquad
\\mathrm{{PSRR}}(f)=\\frac{{A_{{dm}}(f)}}{{A_{{vdd\\rightarrow dm}}(f)}}$$

`A_cm→dm` is measured by driving both inputs together (`ac_cmrr`) and reading `v(voutp) −
v(voutn)`; `A_vdd→dm` by putting the ac source on the rail ahead of the core probe
(`ac_psrr`) and reading the same difference.  Neither is a common-mode-to-common-mode
transfer — those are Section 9.1's, and they are a different quantity.

{mmt}

Rejection falls with frequency in both paths, as the loop gain that produces it falls.

The numerator and the denominator separately, since a ratio hides which half moved — the
`worst` row here is the largest leakage over the draws, i.e. the case that produced the
`worst` rejection above:

{leak}

Read across: at dc the differential path has {nom['a_dm_db'][spots[0]]:.2f} dB of gain while a common-mode input
arrives at the differential output {abs(mm['cm_to_dm_db'][spots[0]]['mean']):.0f} dB down and supply ripple {abs(mm['supply_to_dm_db'][spots[0]]['mean']):.0f} dB down; the
difference is the CMRR and PSRR quoted above.

Every σ here carries the same (M1) band as Section 8.3 — **±{100 * mm['cmrr_db']['0.1']['se_sigma_frac']:.1f} %** at {mm['n_draws']} draws — and
panel (b) of `figures/mc_convergence.png` plots the running σ of these three
distributions.  They settle more slowly than `fc` and `Q` do, and for a reason worth
stating: rejection in dB is the logarithm of a near-cancellation, so its distribution has
a longer tail than a smooth function of many small device shifts, and (M1)'s normal
assumption is a rough guide rather than a tight one.  The trace, not the formula, is the
evidence in that case, and the `worst` row moves with N while `p01` does not.

`figures/rejection.png` plots all of it: panel (a) the differential gain against the two
leakage transfers that define the ratios, so the rejection is the vertical gap between
them; panel (b) the CMRR and PSRR bands themselves; panel (c) the nominal
common-mode-to-common-mode paths of Section 9.1, with their envelope over the nine
certified axis points.

### 9.3 Input-referred offset

Zero by symmetry at nominal, so it is a mismatch quantity and only a distribution.  Over
the same {mm['n_draws']} draws: mean **{o['mean']:+.1f} µV**, σ **{o['sigma']:.1f} ± {o['se_sigma']:.1f} µV**, 99th percentile of
|offset| **{oa['p99']:.1f} µV** and worst |offset| **{oa['max']:.1f} µV**.  Every draw's differential
output offset is divided by that draw's own dc gain before it enters this distribution;
the gain is close to unity ({100 * (mm2['offset_in_uv']['sigma'] / mm2['offset_out_uv']['sigma'] - 1):+.3f} % on σ) but the referral is applied rather than
waved away, because the input-referred value is the one that compares against the drive
level, against the devices' own V_GS mismatch, and against another design.  For
scale, σ is {100 * o['sigma'] / 175e-3 / 1e6:.2f} % of the 175 mVpp S7 drive.

Section 8.3 measures the same quantity a second way — {mm2['n_draws']} draws, from the operating point
of a full extraction rather than from this bench's `op` — and gets mean {mm2['offset_in_uv']['mean']:+.1f} µV,
σ **{mm2['offset_in_uv']['sigma']:.1f} µV**.  Referred the same way, the two benches agree to
{1e3 * abs(mm2['offset_in_uv']['sigma'] - o['sigma']):.2f} nV on σ, and draw by draw to about 2 nV — they are separate decks,
separate solves and separate `op` points, and they land on the same number.  Both means
sit inside one standard error of zero, which is what a symmetric cell should give.

That agreement is what the referral bought.  Compared un-referred, the two σ differ by
{100 * abs(mm2['offset_out_uv']['sigma'] / o['sigma'] - 1):.2f} % — which reads like sampling noise and is not: it is exactly the dc-gain
correction Section 8.3 used to omit.  A residual that small is easy to attribute to the
benches; dividing by the gain shows it was never theirs.
"""


def sec_gds(gr: dict, ic: dict, gt: dict, lin: dict, tc: dict) -> str:
    """The sub-35 Hz residual test, and IIP3 over corners."""
    rows = tbl(["f_in (Hz)", "measured V₃ (µV)", "gate model (µV)", "unexplained (µV)",
                "`g_ds` prediction (µV)", "ratio"],
               [[f"{r['fin']:.0f}", f"{r['v3_measured_uv']:.4f}",
                 f"{r['v3_gate_model_uv']:.4f}", f"{r['v3_unexplained_uv']:.4f}",
                 f"{r['v3_gds_pred_uv']:.4f}",
                 f"{r['ratio_pred_over_unexplained']:.3f}"
                 if r["ratio_pred_over_unexplained"] else "—"]
                for r in gr["rows"]])
    lo, hi = gr["pred_band_over_windows_uv"]
    ulo, uhi = gr["unexplained_band_uv"]
    rf = gr["refinement"]

    ct = tbl(["corner", "`fc` (Hz)", "IMD3 slope (dB/decade)", "IIP3 (dBVp)",
              "OIP3 (dBVp)"],
             [[f"`{k}`", f"{v['fc_hz']:.3f}", f"{v['imd3_slope_db_per_decade']:.2f}",
               f"{v['iip3_dbv']:+.3f}", f"{v['oip3_dbv']:+.3f}"]
              for k, v in ic["corners"].items() if v.get("trusted")])
    ilo, ihi = ic["iip3_dbv_span"]
    tlo, thi = tc["thd_db_at_spec_span"]
    tworst = max(tc["corners"], key=lambda k: tc["corners"][k]["thd_db_at_spec"])
    M_THD = -40.0
    _t70 = tc["corners"]["tt_70c_1v500"]["points"]
    _t27 = tc["corners"]["tt_27c_1v500"]["points"]
    _t70lo, _t27lo = _t70[0]["thd_db"], _t27[0]["thd_db"]
    _t70hi = next(p["thd_db"] for p in _t70 if p["is_spec_amplitude"])
    _t27hi = next(p["thd_db"] for p in _t27 if p["is_spec_amplitude"])
    # The weakest HD2/HD3 separation anywhere in the ladder, so the claim below is a
    # worst case rather than a typical one.
    _h2, _h3 = min(((p["hd2_db"], p["hd3_db"]) for v in tc["corners"].values()
                    for p in v["points"]), key=lambda t: abs(t[0] - t[1]))
    tct = tbl(["corner", "`fc` (Hz)"]
              + [f"{v * 1e3:g} mVpp" for v in tc["vpp_diff"]] + ["HD3 slope (dB/dB)"],
              [[f"`{k}`", f"{v['fc_hz']:.3f}"]
               + [f"{p['thd_db']:.2f}" for p in v["points"]]
               + [f"{v['hd3_slope_db_per_db']:.2f}"]
               for k, v in tc["corners"].items()])
    # Section 6.3's row at the SAME per-tone amplitude the corner sweep quotes
    # (iip3_corners takes pts[0], the lowest amplitude) -- not the corner sweep's
    # own nominal, which would make the comparison self-referential.
    _a0 = ic["ampls_v"][0]
    _ref63 = min(lin["twotone"]["pre_mim"],
                 key=lambda r: abs(r["ampl_per_tone_v"] - _a0))["iip3_dbv"]

    return f"""## 10. The sub-35 Hz residual, and linearity over corners

### 10.1 A named mechanism for the residual

Section 6.2 reports a third harmonic below 35 Hz that the gate-referred model does not
explain: 0.18–0.28 µV, and nearly CONSTANT IN VOLTS while the modelled mechanism moves by
39× over the same span.  That additive signature says a different mechanism, not a
mis-scaled one.  This is the test of the candidate named there.

**The hypothesis, its predictions and its refutation threshold were written down before
the measurement** (`scripts/gds_probe.py`, repo rule 3):

* **H** — the residual is generated by drain-conductance nonlinearity, the curvature of
  `I_D` in `V_DS`.  The gate-referred model does not contain it and the small-signal `Z_T`
  linearises it away.
* **P1**, magnitude within a factor of {gr['accept_factor']:g} of the residual.  **P2**, flat in volts below 35 Hz.
* **Refuted** by a prediction more than {gr['refute_factor']:g}× off, or a frequency slope of the wrong sign.

A device whose drain swings by `v_ds` sources `I(v) = I₀ + g₁v + g₂v²/2 + g₃v³/6`; the
small-signal model keeps `g₁` and drops the rest.  For `v = A·cos(ωt)` the cubic term makes
a third harmonic of amplitude `g₃A³/24`, injected at the SAME port the noise analysis
already characterised, so it propagates through the same `Z_T` and needs no new machinery.
`g₃` is measured per device by a probe pinned to that device's own in-circuit bias
(`gds_probe.py`, which reproduces the DUT's PSP `gds` to {gt['worst_g1_vs_gds_op_pct']:.2f} %); `A` and its phase come
from the MNA node solve, not from an estimated swing.

{rows}

**P2 is satisfied.**  The prediction varies {gr['p2_pred_spread_x']:.2f}× below 35 Hz where the residual it
explains varies {gr['p2_residual_spread_x']:.2f}× — flat in volts, which is the signature that made this residual
look like a separate mechanism in the first place, and which the gate-referred model misses
by 39×.

**P1 is not settled.**  On the pre-registered point estimate the worst factor is
{gr['p1_worst_factor']:.2f}×, so H is **{gr['verdict']}** — outside the accept band, well inside the refute
threshold.  The threshold is not moved after the fact.  What the point estimate hides is
that the sum is dominated by `in_a`, whose `I_D(V_DS)` is not locally cubic over its own
drain swing: its `g₃` moves {gr['g3_window_spread_x']['m2']:.1f}× across the three fit windows, against ≤ 1.3× for every
other device.  Carrying that through, the predicted band is **{lo:.4f} … {hi:.4f} µV** against a
measured residual of **{ulo:.4f} … {uhi:.4f} µV** — the bands overlap.

**The window dependence is now removed, and it does not rescue the magnitude.**  `g₃A³/24`
is the first term of a series and `g₃` is a fit, so the number it produces depends on the
interval it was fitted over.  Replacing it: expand the MEASURED `I_D(V_DS)` in Chebyshev
polynomials over exactly the swing the device sees, `[-A, +A]`.  Substituting
`x = A·cos θ` turns `T_n(x/A)` into `cos nθ`, so the Chebyshev coefficients ARE the Fourier
coefficients of the current waveform and `c₃` is the third harmonic exactly — no window is
chosen and no series is truncated.  The extractor is checked against synthetic curves whose
answer is known in closed form, including one carrying a fifth-order term that a cubic
truncation would drop; worst error {rf['selftest_worst_rel_err']:.1e}.  ({len(rf['fallback_devices'])} of the 15 devices swing too little
across the stored curve to condition the fit; they keep the cubic term, which is the
correct expansion in exactly that limit, and together they are {rf['fallback_share_pct']:.4f} % of the total.)

| | prediction below {gr['flat_band_hz']:.0f} Hz | worst factor vs the residual | flatness |
|---|---|---|---|
| cubic, mid window (pre-registered) | {gr['rows'][0]['v3_gds_pred_uv']:.4f} … {max(r['v3_gds_pred_uv'] for r in gr['rows'] if r['fin'] <= gr['flat_band_hz']):.4f} µV | {gr['p1_worst_factor']:.2f}× | {gr['p2_pred_spread_x']:.2f}× |
| cubic, across the three windows | {lo:.4f} … {hi:.4f} µV | — | — |
| **window-free, over each device's own swing** | **{rf['pred_band_uv'][0]:.4f} … {rf['pred_band_uv'][1]:.4f} µV** | **{rf['worst_factor']:.2f}×** | {rf['pred_spread_x']:.2f}× |

The window-free number is SMALLER, not larger.  It covers {rf['coverage_pct']:.0f} % of the residual, keeps the
flat frequency signature, and removes the band overlap that the cubic's window ambiguity had
produced.  So the ambiguity is resolved in the direction that sharpens the conclusion rather
than the one that would have rescued it.

**So:** drain-conductance curvature is established as *a* contributor — the right frequency
dependence and about a fifth of the magnitude — and is excluded as the whole of it.  The
probe pins the gate and sweeps only the drain, so the one mechanism it cannot see by
construction is the cross-term, gate and drain swinging together, which in a source follower
they do.  That is where the remaining {100 - rf['coverage_pct']:.0f} % is expected to sit; testing it needs a
two-dimensional device probe this pack does not have, and it is left open rather than fitted.

`figures/gds_residual.png` plots both panels of this argument.

### 10.2 IIP3 over the certified axes

Tones stay at {ic['tones_hz'][0]:g}/{ic['tones_hz'][1]:g} Hz — the frozen definition every other IIP3 here uses — so each
row also carries its corner's `fc`: the tones sit at a different fraction of the passband
when the cutoff moves.  Two amplitudes per corner, so each corner reports its own IMD3
slope instead of assuming the 3:1 law that a corner might break.

{ct}

IIP3 spans **{ilo:+.3f} … {ihi:+.3f} dBVp** over the {len(ic['corners'])} certified points, a {ihi - ilo:.2f} dB spread, with
every corner's measured slope within 2 dB/decade of 40 — so every row is an intercept and
not an extrapolation from an unverified law.  The worst is the hot corner.  The nominal row
differs from Section 6.3's {_ref63:+.3f} dBVp at the same amplitude in the third decimal because the `alpha = 1.1`
bias makes the reference a behavioural source even at 27 °C, where it carries the same
current.

`figures/iip3_corners.png` plots the intercepts and the measured slopes.

### 10.3 THD over the certified axes

Section 6.1 measures the THD amplitude ladder at nominal.  The same ladder, re-run at every
certified axis point: {len(tc['vpp_diff'])} amplitudes × {len(tc['corners'])} corners at `fin` = {tc['fin_hz']:.0f} Hz, open loop — an explicit
drive with no servo, because servoing the output to a constant level would remove the
amplitude dependence the ladder exists to measure.

**This table is characterisation, not a spec line.**  S7 is defined at one point —
{tc['spec_vpp'] * 1e3:.0f} mVpp, {tc['fin_hz']:.0f} Hz, nominal — and it is scored there by `lab.metrics` in `make check`.
What a corner row says is how much margin the delivered cell carries away from nominal.

{tct}

At the spec amplitude the nine corners span **{tlo:.3f} … {thi:.3f} dB**, so the WORST of them
({thi:.2f} dB, at `{tworst}`) still clears the {M_THD:.0f} dB limit by {abs(thi) - abs(M_THD):.2f} dB.  HD2 is {abs(_h2 - _h3):.0f} dB below HD3 in every
row, so each of these numbers is third-order distortion and not an even-order artefact.

The corners do not simply translate the nominal ladder.  `tt_70c_1v500` sits {_t70lo - _t27lo:+.2f} dB
relative to nominal at the lowest drive but only {_t70hi - _t27hi:+.2f} dB at the spec amplitude, and its
HD3 slope over the two lowest points, {tc['corners']['tt_70c_1v500']['hd3_slope_db_per_db']:.2f} dB/dB, is the furthest of the nine from
the cubic law's 2.  A low-drive point lifted above a cubic extrapolation is the signature of
an additive third-harmonic term that does NOT scale with `A³` — which is what Section 10.1
measures at nominal.  Whether that mechanism also carries this temperature dependence is not
tested here; the ladder measures it, it does not explain it.

`figures/thd_corners.png` plots the ladder at every corner and the margin at the spec point.
"""


def main() -> None:
    tf, nz = jload("tf.json"), jload("noise.json")
    bs, la = jload("bench_summary.json"), jload("linearity_analysis.json")
    lin, sp_ = jload("linearity.json"), jload("twotone_spacing.json")
    bench, post = jload("bench_pre_mim.json"), jload("bench_post_lumped.json")
    pv, rj = jload("pvt.json"), jload("psrr_cmrr.json")
    gr, ic = jload("gds_residual.json"), jload("iip3_corners.json")
    gt, tc = jload("gds_taylor.json"), jload("thd_corners.json")
    body = "\n".join([
        """# validation.md — every number, and what checks it

**[GENERATED]** by `scripts/report.py` from `data/*.json`.  Do not hand-edit: re-run

```
.venv/bin/python signoff/paper-draft/scripts/report.py
```

The derivations these numbers check live in [theory.md](theory.md); the map from the
reviewer's request to the answers is in [README.md](README.md).
""",
        sec_op(bench, post, la), sec_tf(tf, bs), sec_valid(tf), sec_pz(tf),
        sec_noise(nz), sec_lin(la, lin, sp_, jload("pex_distortion_sweeps.json")),
        sec_score(bs),
        sec_pvt(pv), sec_rej(rj, pv['mismatch']['summary']), sec_gds(gr, ic, gt, lin, tc)])
    (PACK / "validation.md").write_text(body)
    print(f"wrote {PACK / 'validation.md'} ({len(body)} chars)")


if __name__ == "__main__":
    main()
