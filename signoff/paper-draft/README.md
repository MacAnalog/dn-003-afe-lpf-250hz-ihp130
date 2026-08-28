# Reviewer response pack — equations, poles/zeros, noise, linearity

**[REFERENCE]** — the answer to [`request.md`](request.md), for the delivered
4th-order 250 Hz SSF low-pass filter (IHP SG13G2, VDD = 1.5 V), **pre-layout and
post-layout**.

Everything here is derived from committed netlists and re-derivable with the commands in
§4.  No number in this pack is quoted without the script and the artifact that produced it.

| file | what it is |
|---|---|
| [`theory.md`](theory.md) | **the derivations** — `H(s)`, the noise equation, the distortion equation, IMD3/IIP3, and the assumption ledger.  Hand-written; symbolic; stable. |
| [`validation.md`](validation.md) | **every number, and what checks it** — DC operating point, poles/zeros, model-vs-simulation, the noise budget, the linearity tables.  **Generated** by `scripts/report.py`; do not hand-edit. |
| `figures/` | the six figures, PNG + PDF |
| `scripts/` | the generating scripts (§4) |
| `data/` | the extracted and analysed JSON (§5) |

---

## 1. The request, answered

| # | reviewer's ask | answer | where |
|---|---|---|---|
| 1 | **transfer function** | exact symbolic 4th-order `H(s)`, and the identity `D(s) = D_A·D_B + κ·s²` proved by symbolic expansion (residual exactly 0) | [theory §2.2](theory.md#22-the-result), numbers in [validation §2.1](validation.md#21-the-closed-form-at-the-measured-operating-point) |
| 2 | **noise equation** | `S_out = Σ_k \|Z_T,k\|²·S_i,k`, `IRN² = ∫S_out/\|H\|²`, with each generator's port established from the data | [theory §3](theory.md#3-the-noise-equation), [validation §5](validation.md#5-the-noise-equation-checked-generator-by-generator) |
| 3 | **THD / linearity equation** | `HD3(ω) = \|Σ_k Z_T,k(j3ω)·I_D,k·2I₃(a_k)/I₀(a_k)\| / \|V_out,fund\|` from the weak-inversion exponential, with a stated validity window | [theory §4](theory.md#4-the-distortion-equation), [validation §6.1–6.2](validation.md#61-hd3-versus-amplitude--the-a²-law) |
| 4 | **pole / zero locations** | 4 poles (2 complex pairs), 4 zeros (2 complex pairs), 7 pole–zero cancellations reported with their residuals; pre- and post-layout | [validation §4](validation.md#4-poles-and-zeros--the-map) |
| 5 | **Q of each biquad** | given **twice**: isolated-stage Q (2.10 / 0.46) and the filter's pole-pair Q (**0.543 / 1.307**, essentially Butterworth).  The two differ because the current-reuse bridge contributes `κ` = 11.78 % of the quartic's `s²` coefficient — the closed form says exactly how. | [theory §2.3](theory.md#23-per-biquad-f₀-and-q--and-which-q-the-reviewer-should-be-given), [validation §2.1](validation.md#21-the-closed-form-at-the-measured-operating-point) |
| 6 | **IIP3, IMD3** | IIP3 = **−3.28 dBV** pre-layout, **−3.35 dBV** post-layout, from a 5-point two-tone ladder with a verified 3:1 slope; IMD3 tabulated, plus a spacing sweep | [theory §5](theory.md#5-imd3-and-iip3), [validation §6.3](validation.md#63-two-tone-imd3-and-iip3) |
| 7 | **proof of the equations, checked against sim** | see the table in §2 below — every equation has a numeric closure against the simulator | [validation §3, §5.1, §6](validation.md#3-model-versus-simulation) |
| 8 | **pole/zero plane plot; real or imaginary; verified by DC ops and sim data** | `figures/pz_plane.png`, plus **three independent verification legs** — see §3 below | [validation §3.2, §4](validation.md#32-what-the-simulation-says-about-the-poles-on-its-own) |

The topology identification in `request.md` needed no action and none was taken; the
device-level reading is restated in [theory §1.1](theory.md#11-the-cell) so the equations
can be read against it.

---

## 2. "The proof of the equations" — the closures, in one table

Each equation is checked against the simulator on its own terms.  These are the numbers a
reviewer should look at first.

| equation | check | pre-layout | post-layout |
|---|---|---|---|
| `H(s)` | max Δ\|H\| vs the ac sweep, dc–1 kHz | **0.0267 dB** | 0.0265 dB |
| `H(s)` | max Δφ vs the ac sweep, dc–1 kHz | **0.3448°** | 0.3427° |
| `H(s)` | max Δ group delay, dc–1 kHz | 0.997 % | 1.023 % |
| `D = D_A·D_B + κs²` | symbolic residual after expansion | **exactly 0** | — |
| `H(0) = 1` | closed form vs full model / simulator | 1 vs −0.008148 dB (finite `ro`) | same |
| noise `Σ_k` | max Δ`S_out` vs the simulator's own total, per frequency | **2.0·10⁻⁷ %** | 2.0·10⁻⁷ % |
| noise | integrated IRN vs the certified sign-off number | **exact** (29.1990 µV) | exact (29.1959 µV) |
| `Z_T` | `netlist2tf.transimpedance` vs the independent pencil solve | 1.7·10⁻⁸ | 2.6·10⁻⁹ |
| `HD3 ∝ A²` | fitted slope vs 40 dB/decade | **42.63** (resid 0.51 dB) | — |
| `HD3(ω)` | model vs measured, 35–65 Hz | **±2 dB** | — |
| IMD3 slope | fitted vs 40 dB/decade | **41.71** (resid 0.26 dB) | 42.29 (resid 0.20 dB) |
| IIP3 | spread over the three in-regime amplitudes | 0.52 dB | 0.69 dB |

---

## 3. "Real or imaginary — verified by the DC ops and the sim data"

The reviewer asked for the pole/zero plane **and** for it to be verified two ways.  Three
independent legs are provided, and they are deliberately independent:

1. **The DC-ops leg.**  One `.op` on the as-built netlist gives every device's `gm`, `ro`
   and capacitances ([validation §1](validation.md#1-the-dc-operating-point--the-root-of-every-number-below));
   those bind the MNA pencil; the poles are its generalised eigenvalues.  Every symbol in
   every equation traces to that one table.
2. **The sim-data leg, with a falsification test.**  A 4-pole rational is fitted directly
   to the measured complex response — no model, no netlist, no operating point.  It fits to
   0.215 dB.  Refitting with both Q's forced ≤ 0.5, i.e. **all four poles real**, the best
   achievable residual is **4.85 dB / 52°**, with both Q's pinned against the bound.  So
   **the measured response cannot be produced by any all-real-pole 4th-order model** — the
   poles are complex, and that is established by the simulation data alone
   ([validation §3.2](validation.md#32-what-the-simulation-says-about-the-poles-on-its-own)).
3. **The overlay leg.**  The pole-bound model is evaluated at every ac point and matched
   against the sweep: 0.027 dB, 0.34°, 1 % on group delay.

`ngspice`'s own `.pz` cannot do this job here — it aborts with *"the input signal is shorted
on the way to the output"* for any input port carrying its dc bias, which a subthreshold
gate must; confirmed on a one-transistor deck, so it is the analysis and not the netlist.
The three legs above replace it and are stronger than a single `.pz` listing.

**The answer:** four poles, **two complex-conjugate pairs**, at
(249.72 Hz, Q 0.543) and (251.08 Hz, Q 1.307) pre-layout — a Butterworth-like quartic
realised by frequency-coincident, differently damped sections.  Four zeros, **two complex
pairs**, at 3.85 kHz and 5.05 kHz, both far out of band, both traced by ablation to the
followers' gate–source capacitance.  Post-layout the poles move to (248.18 Hz, Q 0.546) and
(249.97 Hz, Q 1.304) and nothing else changes qualitatively.

### Figures

| figure | what it shows | script |
|---|---|---|
| `figures/half_circuit.png` | the DM half-circuit the algebra describes, each branch labelled with its equation symbol, the `κ` loop in red | `scripts/figures.py::fig_half_circuit` |
| `figures/pz_plane.png` | the pole/zero plane, both conjugate members, pre- vs post-layout, cancellations hollow | `scripts/figures.py::fig_pz` |
| `figures/bode_model_vs_sim.png` | \|H\| and phase, model over simulation, plus the residual | `scripts/figures.py::fig_bode` |
| `figures/noise_budget.png` | `S_out(f)`, the sum of generators, and the top contributors | `scripts/figures.py::fig_noise` |
| `figures/distortion.png` | HD3 vs amplitude and vs frequency, measured against the equation | `scripts/figures.py::fig_thd` |
| `figures/iip3.png` | the two-tone ladder and the IIP3 extrapolation | `scripts/figures.py::fig_iip3` |

---

## 4. Regenerating everything

The symbolic lane needs `spicexplorer_netlist2tf`, so it runs in the **platform** venv; the
simulation lane runs in this repo's venv.  **Set the ngspice lane first** — the default is
the Docker lane, and on a host without a usable Docker socket every simulation step fails
with `rc=126` (see [`doc/environment.md`](../../doc/environment.md)):

```bash
export LPF_NGSPICE=/path/to/ngspice PDK_ROOT=/path/to/pdks   # native lane; omit for Docker
```

Then, from the repo root:

```bash
# 1. simulation lane -- op + ac + per-generator noise for all four DUTs   (~2 min)
.venv/bin/python signoff/paper-draft/scripts/extract_bench.py
# 2. simulation lane -- THD ladder, THD profile, two-tone, spacing sweep  (~25 min)
.venv/bin/python signoff/paper-draft/scripts/linearity_runs.py
.venv/bin/python signoff/paper-draft/scripts/twotone_spacing.py
.venv/bin/python signoff/paper-draft/scripts/hd3_vs_fin.py
# 3. symbolic lane -- transfer function, poles/zeros, noise, distortion   (~8 min)
PF=../../spicexplorer-platform/.venv/bin/python
$PF signoff/paper-draft/scripts/tf_analysis.py
$PF signoff/paper-draft/scripts/noise_analysis.py
$PF signoff/paper-draft/scripts/linearity_analysis.py
# 4. the pack
#    report.py is stdlib-only but needs Python >= 3.12 (it uses backslash escapes inside
#    f-string expressions), so it runs in the REPO venv, not the platform's 3.11 one.
.venv/bin/python signoff/paper-draft/scripts/report.py   # rewrites validation.md
$PF signoff/paper-draft/scripts/figures.py               # rewrites figures/
```

| script | role |
|---|---|
| `extract_bench.py` | one `op` deck and one `ac`+`noise` deck per DUT; per-instance operating point, per-generator noise vectors, and the `post_lumped` netlist |
| `n2tf_model.py` | the one place that turns an as-built subckt into an MNA system bound to the measured operating point; the DM half-circuit; the symbol renaming |
| `pencil.py` | poles, zeros, `H(jω)` and `Z_T` from the matrix pencil `G + sC` |
| `tf_analysis.py` | the symbolic `H(s)`, the factorisation proof, the pole/zero map, the capacitance ablation, the validation and the sim-only fit |
| `noise_analysis.py` | per-generator port identification, the noise equation, the closure and the transimpedance cross-check |
| `linearity_runs.py`, `twotone_spacing.py`, `hd3_vs_fin.py` | the transient benches |
| `linearity_analysis.py` | the HD3 model, the amplitude/frequency laws, the memoryless test, IIP3 |
| `report.py` | renders `validation.md` |
| `figures.py` | renders `figures/` |

---

## 5. What is committed, and what is regenerated

Committed: the scripts, the figures, `validation.md`, `theory.md`, and the small analysis
JSON (`tf.json`, `noise.json`, `linearity*.json`, `twotone_spacing.json`, `hd3_vs_fin.json`,
`post_lumped_core.sp`).  **Not committed**: `data/bench_*.json` — 2.7 MB of raw op + ac +
noise vectors, regenerated in ~2 minutes by step 1 above, and simulator output under the
repo's never-commit rule.  Every downstream script fails loudly with the missing path if
they are absent — `tf_analysis.py` prints `[<case>] SKIPPED` and moves on, and the
`report.py` render then raises on the missing case, so a stale `validation.md` cannot be
produced silently.

The two pre-layout DUTs and the two post-layout DUTs, and why there are four of each kind,
are in [validation §7](validation.md#7-the-four-duts-side-by-side).

---

## 6. Open items

* **The low-frequency third-harmonic residual.**  Below ~35 Hz the measured third harmonic
  exceeds the distortion equation by **0.18–0.28 µV — constant in volts** while the
  equation's own prediction moves by a factor of 39 over the same span.  That additive
  signature says a mechanism is missing rather than mis-scaled; drain-conductance
  nonlinearity is the natural candidate, and confirming it needs a `g_ds(V_DS)` expansion
  term the present model does not have.  The whole residual is **61.7 dB below** the
  256 µV third harmonic the cell produces at the S7 operating point, so it is a modelling
  gap and not a performance one, and it is stated as a bounded observation rather than a
  fitted claim.
* **Corners and Monte Carlo for the new quantities.**  Everything in this pack is at the
  nominal corner.  The poles, Q, IIP3 and the noise budget have not been swept over PVT or
  mismatch; the existing PVT/MC evidence covers the scorecard metrics only.
* **PSRR / CMRR / offset** remain unmeasured (`doc/paper/README.md` G12); the per-generator
  noise *spectrum* added here narrows that gap but does not close it.
