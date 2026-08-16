# Figures — what each one is, where it came from, how to regenerate it

Every generated figure ships as **PNG + PDF** at 200 dpi. Every generating script
is in `doc/paper/scripts/` and reads only committed artifacts (or re-runs the
cell's own frozen benches). Curve/sample data that a script produced is kept in
`data/` so a figure and a table can never drift apart.

**House style** — `scripts/_style.py`, applied by every figure script:
IEEE column widths (3.5 in single, **7.2 in** double — all seven of these have
three or more panels, so all are double-column), 8 pt body / 9 pt panel titles,
`constrained_layout=True` so a figure title can never land on a panel title,
colour paired with dash pattern *and* marker so the curves survive a grayscale
print, and numbers carried in **legend entries or one boxed note** rather than in
free-floating annotations that collide. `_style.save()` writes both formats and
prints the pixel size.

**No code jargon in a figure.** Spec identifiers, review-finding ids and internal
round tags are spelled out on the canvas: "phase max ≥ 330° (two true biquads)",
"|H| at 1 kHz ≤ −48 dB", "total harmonic distortion ≤ −40 dB". An iteration id
appears at most once, as "round 4 (it14)", in a legend. Net and device names
(`net2`, `xc13`) are kept — they are what an expert reader needs.

Two interpreters are in play:

| lane | interpreter | why |
|---|---|---|
| scripts that simulate | `<repo>/.venv/bin/python`, **cwd `experiments/023-replica-bias`**, `PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice` | `lab.*` resolves decks and models relative to the experiment dir |
| scripts that only re-read artifacts | `<repo>/.venv/bin/python` from the repo root — except `fig_iterations.py`, which needs PyYAML and runs on the system `python3` | — |

---

## Generated figures

| file | script | what it shows | inputs | sims? |
|---|---|---|---|---|
| `prepost_bode.png/.pdf` | `scripts/fig_prepost_bode.py` | Differential \|H(f)\| and unwrapped phase before layout and after layout rounds 3 and 4, plus the after−before delta. Panel (a) runs down to −137 dB so the **transmission zero and the feed-through floor** are both visible; panel (b) is the two-biquad phase certificate. See the note below on why the phase returns to 0°. | `signoff/post-pvt/H12-pdk-cap/design.json`; PEX it14 = `layout/H12-pdk-cap/asbuilt/core_pex.sp`; PEX it13 = `git show ee6b342:layout/H12-pdk-cap/asbuilt/core_pex.sp` | **yes** — 3 × `lab.deck.ac_noise` at `mos_tt`/27 °C/1.5 V. `--replot` redraws from `data/prepost_bode.json` |
| `mc_hist.png/.pdf` | `scripts/fig_mc.py` | Mismatch Monte Carlo n = 100, **paired pre- vs post-layout** (same seeds 1–100): `fc`, \|H\|@1 kHz, IRN and dc distributions with the spec limits and the out-of-box counts. | same sizing + it14 PEX; cross-checked against the certified summary in `experiments/023-replica-bias/H12-pdk-cap.json` → `mc` | **yes** — 200 ac+noise processes (17 s + 51 s wall at 14 workers). `--replot` redraws from `data/mc_samples.json` |
| `pvt_window.png/.pdf` | `scripts/fig_pvt.py` | The PVT operating window at schematic level: (a) supply sweep, (b) temperature sweep, (c) the five process corners with their input-referred noise, (d) the full 45-point grid as a pass/fail map. | `experiments/023-replica-bias/{vsw_H12-pdk-cap.json, tsw_H12-pdk-cap_a1p1_1p5.json, H12-pdk-cap.robust.a1p1.json}` | no |
| `thd.png/.pdf` | `scripts/fig_thd.py` | Distortion evidence: (a) total harmonic distortion and 3rd harmonic at nine corners against the −40 dB limit, (b) the 30-draw mismatch Monte Carlo, (c) the sweep over input frequency at held drive. | `experiments/023-replica-bias/H12-pdk-cap.prelayout.json` | no |
| `pvt_postlayout.png/.pdf` | `scripts/fig_pvt_postlayout.py` | The same three corner sets (9 / 22 / 45) re-run on the **extracted round-4 cell** and paired point for point against the schematic: (a) one corner axis at a time, (b)/(c) the 45-point grid before and after layout, (d) the coverage scoreboard. Zero of the 45 corners changes verdict. | `signoff/post-pvt/H12-pdk-cap/design.json` + `layout/H12-pdk-cap/asbuilt/core_pex.sp`; `lab.corners` | **yes** — 2 × 76 corner points, **12 s total**. `--replot` redraws from `data/postlayout_pvt.json` |
| `area_campaign.png/.pdf` | `scripts/fig_area_campaign.py` | The two 300-trial area campaigns over the generator's knobs: (a) area vs the binding capacitance budget on `net2` for every trial that reached extraction, coloured by outcome; (b) where the 600 trials went; (c) convergence traces; (d) the cost of the dummy-row decision. | `layout/H12-pdk-cap/opt/results/{campaign_A_trials.jsonl, campaign_B_trials.jsonl, summary.json}` | no |
| `iteration_trail.png/.pdf` | `scripts/fig_iterations.py` | The 14-round designer trail: (a) area per round with the byte-identical rebuilds ringed, (b) phase max against its 330° floor, (c) cutoff inside its 245–255 Hz box, (d) extracted-capacitance count and design-rule violations — including **the one round that failed, snapshotted anyway**. | `layout/H12-pdk-cap/iterations/iterations.yaml` | no |

### Why the phase comes back to 0° — and why it is not an artifact

Above the passband the response does **not** roll off forever. It runs into a
**transmission zero at 3.82 kHz** (−124.6 dB before layout, −122.6 dB after) and
then flattens onto a **direct feed-through floor of ≈ −101 dB**: −101.0 dB before
layout and −100.8 dB after at 30 kHz, −100.5 dB and −0.5° of phase at 100 kHz.
Past the zero the signal no longer travels through the two biquads at all — it
arrives through the direct high-frequency path (the followers' own
C_gs/C_gd plus capacitor feed-forward), which is **in phase**, so the 332° of
accumulated lag unwinds back to zero. That is a real property of the cell, not a
numerical artifact, and the figure's y-range was extended to −137 dB
specifically so a reader can see the mechanism instead of guessing at it.

Two paper-worthy consequences, both measured here:

* **The layout moves the floor by +0.16 dB and does not move the notch** (the
  zero stays put to within the 4.7 % sweep step) — the extracted parasitics
  perturb the feed-through path far less than they perturb the poles.
* **The 3–5 kHz spike in the after−before delta panel is the notch region**, not
  a resonance: a fraction of a dB of movement in a −120 dB null is a large
  *relative* delta. Say so in the caption; a reviewer will otherwise read it as a
  parasitic resonance.

### Data written alongside the figures

| file | written by | contents |
|---|---|---|
| `data/prepost_bode.json` | `fig_prepost_bode.py` | f, \|H\| dB, phase deg (301 pts) + the full scorecard and violation list for all three DUTs |
| `data/mc_samples.json` | `fig_mc.py` | every MC draw of both campaigns (seed, usable, ok, violations, 6 metrics), the per-line yields, the stats, and the certified summary it was checked against |
| `data/postlayout_pvt.json` | `fig_pvt_postlayout.py` | every corner row of both DUTs for all three sets (corner, status, all 18 metric values, violations) + the per-set wall clock |
| `data/iteration_trail.csv` | `fig_iterations.py` | the drawn trail as a flat table: id, area, `ph_max`, `fc`, `a1000`, `irn`, `thd`, DRC n, LVS matched, PEX n_c, GDS sha prefix |

---

## Copied artifacts — `static/`

These are **not** regenerated here; they are copies of committed renders. The
source path is the citation.

| file | source | use |
|---|---|---|
| `schematic_lpf_core.png` | `signoff/post-pvt/H12-pdk-cap/lpf_core_H12pc.png` | the cell schematic of record — ISCAS Fig. 2 candidate |
| `schematic_tb_acnoise.png` | `signoff/post-pvt/H12-pdk-cap/lpf_tb_H12pc.png` | the op + ac + noise testbench (every bench element drawn, only directives as text) |
| `schematic_tb_thd.png` | `signoff/post-pvt/H12-pdk-cap/lpf_tb_H12pc_thd.png` | the coherent-strobed-transient S7 bench |
| `layout_lpf_core.png` | `layout/H12-pdk-cap/lpf_core_layout.png` | the PDK-coloured layout of record (it14) — ISCAS Fig. 3 candidate |
| `layout_it01.png` | `layout/H12-pdk-cap/iterations/it01/layout.png` | round-1 layout, for the before/after pair |
| `layout_it14.png` | `layout/H12-pdk-cap/iterations/it14/layout.png` | round-4 layout (byte-identical to `layout_lpf_core.png`) |
| `review_annotated.png` | `layout/H12-pdk-cap/REVIEW.png` | all 25 review findings drawn, numbered and severity-coloured, over the PDK render — the single best "what a schema'd review buys" figure. Its numbering is the reviewer's own; if it is used in a paper, the caption must gloss the ids |
| `diff_it02_it03.png` | `layout/H12-pdk-cap/iterations/diff_it02_it03.png` | **the failed round**: 5 design-rule violations, no extraction, snapshotted anyway |
| `diff_it05_it06.png` | `layout/H12-pdk-cap/iterations/diff_it05_it06.png` | the bias dummy rows going in (the human's first call) — +13.8 k µm² |
| `diff_it13_it14.png` | `layout/H12-pdk-cap/iterations/diff_it13_it14.png` | the bias dummy rows coming out, plus the campaign's knob point (the reversal) — −19.0 k µm² |
| `coopt_layout_of_record.png` | notebook cell 8, `PF: feat/layout-coopt-notebook` | the 5T-OTA baseline layout, 205.9 µm² |
| `coopt_area_vs_ugf.png` | notebook cell 24 | area vs UGF over all 16 co-optimization trials, feasible vs violating, best ringed — **the only notebook figure reproducible from committed data** (`coopt_replay.json`) |
| `coopt_baseline_vs_best.png` | notebook cell 26 | baseline vs co-optimized geometry side by side, 205.9 / 29.45 MHz vs 208.3 / 32.61 MHz |

The three `coopt_*.png` files were extracted from the notebook's **stored
outputs**; cells 8 and 26 need the live physical stack to re-render, cell 24 does
not.

## Review crops — `review_crops/`

Per-finding zooms from `layout/H12-pdk-cap/review_crops/`. Five of the 25
findings have no crop by design (F4, F9, F10, F23, F24 — their subject is a
knob sweep, a JSON key or an extraction mesh, not a place in the layout).
Copied here, the ones a paper would use:

| file | the finding, spelled out | why it is worth showing |
|---|---|---|
| `F1.png` | major — phase-max objective, **open, owner-accepted** | the one remaining spec miss: phase max 329.751° against a 330° floor at the worst capacitor corner with the current trim |
| `F2.png` | major — parasitic budget, **worse by design, disclosed** | `net2`/`net3` at 1.42× the brief's balanced budget: a priced, disclosed regression, not a slip |
| `F16.png` | note — coupling between the two biquads, **fixed** | the lane-offset knob: capacitance between `net2` and `net3` went to 0.0000 fF — the coupling element is *absent from the extraction*, not merely small |
| `F17.png` | note — device matching, **fixed** | all six current-source members routed identically again: per-device Metal1 mirror mismatch 21.17 → **0.0324 µm² (0.023 %)**, at a disclosed 0.050° cost |
| `F18.png` | note — symmetry guard-rail, **fixed** | the build-time symmetry assertion now fails on the round-1 layout it was installed to reject — 15 rules across 8 layers |

---

## Regenerating everything

All seven generated figures are 7.2 in wide at 200 dpi:
`prepost_bode` 1440×1380 px · `mc_hist` 1440×980 · `pvt_window` 1440×1080 ·
`thd` 1440×980 · `pvt_postlayout` 1440×1240 · `area_campaign` 1440×1400 ·
`iteration_trail` 1440×1320.

```bash
cd <repo>

# artifact-only figures (no simulator)
.venv/bin/python doc/paper/scripts/fig_pvt.py
.venv/bin/python doc/paper/scripts/fig_thd.py
.venv/bin/python doc/paper/scripts/fig_area_campaign.py
python3            doc/paper/scripts/fig_iterations.py     # needs PyYAML

# figures that simulate (native ngspice lane)
cd experiments/023-replica-bias
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_BIAS_ALPHA=1.1 LPF_JOBS=14 \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_pvt_postlayout.py
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_prepost_bode.py
PDK_ROOT=~/local/pdks LPF_NGSPICE=~/local/bin/ngspice LPF_JOBS=14 \
    ../../.venv/bin/python ../../doc/paper/scripts/fig_mc.py
```

Add `--replot` to either simulating script to redraw from the stored data
without touching the simulator.
