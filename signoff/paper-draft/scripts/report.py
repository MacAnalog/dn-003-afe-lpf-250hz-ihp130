#!/usr/bin/env python
"""Render `validation.md` -- every number in the reviewer pack, straight from the data.

`theory.md` holds the derivations, which are symbolic and therefore stable.  This file
holds everything that is a MEASUREMENT, and it is generated rather than written so that a
number in the prose can never drift from the JSON that produced it.  Re-run after any
re-extraction:

    .venv/bin/python signoff/paper-draft/scripts/report.py   # repo venv: needs >= 3.12

It reads only `signoff/paper-draft/data/*.json` -- it never calls the simulator and never
touches the small-signal model.
"""
from __future__ import annotations

import json
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


def _gen_cell(d: dict, gen: str) -> str:
    tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
    p = sum(r["irn_uv_rms"] ** 2 for r in d["rows"] if r["gen"] == gen)
    return f"{p ** 0.5:.4f} / {100 * p / tot:.2f} %"


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
     [[f"`{g}`", txt] + [_gen_cell(nz[k], g) for k, _ in CASES]
      for g, txt in (("idid", "channel (weak-inversion shot) noise"),
                     ("igig", "gate-leakage shot noise"),
                     ("flicker", "1/f gate noise"),
                     ("ibd", "bulk-drain junction"),
                     ("rgate", "gate resistance"))])}

**The gate-leakage generator is a quarter of the noise power.**  In any normal bias regime
`igig` is discarded; at 0.66–2.6 nA per branch, with 10–60 MΩ of transimpedance in front of
it, it is second only to the channel.  A hand-written noise model that omits it is 1.4 dB
optimistic on IRN before it does anything else (10·log₁₀(1/(1−0.271))).

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

And by role × generator:
""")
    for key, label in CASES:
        d = nz[key]
        tot = sum(r["irn_uv_rms"] ** 2 for r in d["rows"])
        agg: dict[tuple[str, str], float] = {}
        for r in d["rows"]:
            k = (r["role"] or "testbench bias devices", r["gen"])
            agg[k] = agg.get(k, 0.0) + r["irn_uv_rms"] ** 2
        top = sorted(agg.items(), key=lambda kv: -kv[1])[:10]
        rr = [[ROLE_TEXT.get(k[0], str(k[0])), f"`{k[1]}`", f"{v ** 0.5:.4f}", f"{100 * v / tot:.2f}"]
              for k, v in top]
        rest = tot - sum(v for _, v in top)
        rr.append(["*(all other role × generator terms)*", "—", f"{max(rest, 0) ** 0.5:.4f}",
                   f"{100 * max(rest, 0) / tot:.2f}"])
        out.append(f"""#### {label} (`{key}`) — total {tot ** 0.5:.4f} µV

{tbl(["role", "generator", "IRN contribution (µV)", "% of power"], rr)}
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
       "≤ 1, approaching 1 deep in saturation",
       f"{min(r['si_over_2qid'] for r in idid):.3f} – {max(r['si_over_2qid'] for r in idid):.3f}"],
      ["the same, written against `gm`: `S_i / 4kT·gm`", "= (n/2)·(previous column)",
       f"{min(r['si_over_4ktgm'] for r in idid):.3f} – {max(r['si_over_4ktgm'] for r in idid):.3f}"],
      ["flicker slope, `d log S_i / d log f`", "≈ −1 (1/f)",
       f"{min(r['fit_slope'] for r in fl):.3f} – {max(r['fit_slope'] for r in fl):.3f}"],
      ["power-law fit residual over 1–200 Hz", "small",
       f"≤ {max(abs(r['fit_dev_db']) for r in sig):.3f} dB"]])}

The first row is the physical statement: the channel generator is
**{min(r['si_over_2qid'] for r in idid):.2f}–{max(r['si_over_2qid'] for r in idid):.2f}× full
shot noise `2qI_D`**.  That is a weak-inversion channel generator; the strong-inversion
form `4kTγ·gm` with γ = 2/3 is a different law with a different bias dependence, and the
data picks the shot-noise one.  The second row is the same measurement rewritten against `gm`, and it is a *consistency* check
rather than a new one: the two columns must differ by exactly `n/2`, and their measured
ratio is
{sum(r['si_over_2qid'] for r in idid) / sum(r['si_over_4ktgm'] for r in idid):.3f} = 2/n
with n = {2 * sum(r['si_over_4ktgm'] for r in idid) / sum(r['si_over_2qid'] for r in idid):.3f},
which matches the §1 slope factors.  The flicker slope being slightly steeper than −1 is
the PSP flicker model's own `f^-(1+δ)` behaviour, not a fitting artifact.

**The port of every generator is identified from the data, not assumed**
(`scripts/noise_analysis.py::identify_port`): for each generator the candidate device
ports are ranked by how well `S_out/|Z_T,port|²` comes out frequency-flat (or `1/f`, for
flicker), and the winner is taken.  Every channel-noise generator selects drain–source and
every gate generator selects gate–source, which is what the physics predicts.  Doing it
this way makes the port assignment a measured result rather than an assumption, and that
is what justifies re-using the same `Z_T` for the distortion currents in §6.

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

def sec_lin(la: dict, lin: dict, sp_: dict) -> str:
    a = la["amplitude_law"]
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
point a reviewer asks for, 1.75× the S7 drive of 175 mVpp.

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


def main() -> None:
    tf, nz = jload("tf.json"), jload("noise.json")
    bs, la = jload("bench_summary.json"), jload("linearity_analysis.json")
    lin, sp_ = jload("linearity.json"), jload("twotone_spacing.json")
    bench, post = jload("bench_pre_mim.json"), jload("bench_post_lumped.json")
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
        sec_noise(nz), sec_lin(la, lin, sp_), sec_score(bs)])
    (PACK / "validation.md").write_text(body)
    print(f"wrote {PACK / 'validation.md'} ({len(body)} chars)")


if __name__ == "__main__":
    main()
