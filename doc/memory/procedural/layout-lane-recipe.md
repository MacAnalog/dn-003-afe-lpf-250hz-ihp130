# 2026-08-17 — Layout lane recipe — certified cell → parameterized GDS → DRC/LVS/PEX → post-layout benches → review

KIND: procedural overflow | type: procedural | status: live

The ordered flow that took `H12-pdk-cap` from `signoff/post-pvt/` to a layout of
record (`layout/H12-pdk-cap/`, 14 iterations, 4 rounds, 3 independent
reviews). Agents: `layout-brief-author`, `layout-designer`, `layout-reviewer`
(meta-repo `.claude/agents/`, generic across cells); runners in the platform
packages `spicexplorer-signoff` (DRC/LVS/PEX/postlayout/sensitivity) and
`spicexplorer-layout` (generator contract, review DSL, iteration trail).
Environments on this host: gdsfactory + `ihp-gdsfactory` in conda `ai_env`,
kpex in conda `pex`, KLayout wheel in the platform `uv` venv, PDK at
`$PDK_ROOT`, benches in this repo's `.venv` with `LPF_NGSPICE` (native lane).

| step | what | gate / failure mode |
|---|---|---|
| 0 | **Brief** (`layout-brief-author`): inject C/R/leakage into the frozen benches (`spicexplorer_signoff.sensitivity`) → per-net budgets balanced / one-sided / A↔B, matching tolerances, well & pin intent → `BRIEF.md`/`brief.json` | numbers, not adjectives; a budget with no measurement is not a budget |
| 1 | **Plan** (`layout-designer`): device table by matching class, floorplan sketch, knob list = `LayoutParams` + `BOUNDS`, sensitivity → concrete constraints → `PLAN.md` | **human approval** before any pixel; decisions a human might reject listed explicitly (H12: R2.8 Q1–Q4) |
| 2 | **Generator** `gen_<cell>.py`: `build(params, sizing)`, deterministic (same params → same sha), net names = netlist names, LVS reference written by the generator (`write_lvs_reference(p, out=)`) because dummy/split cards depend on knobs; build-time asserts (mirror-XOR, keep-apart) | a raise inside `build()` is a failed round, snapshot it |
| 3 | **DRC** `signoff.run_drc` (PDK deck, `--no_density`), **LVS** `signoff.run_lvs` vs the regenerated reference, **PEX** kpex CC in the loop (`strip_mim_for_pex` — kpex has no `cap_cmim`), RC once at the end; ≤ 2 concurrent KLayout jobs per host | DRC 0, no silent waivers; LVS matched; PEX ok |
| 4 | **Post-layout benches**: `postlayout.prep_pex_subckt` → header `.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd`, VSS/VSUBS → 0, re-add schematic `xc*` cards → `Design.dut_override` → `lab.metrics.evaluate`, `lab.thd`, `lab.corners` (9-pt AXES + cap corners incl. `cap_bcs` with `iref×0.9`) | S1–S7 same definitions as pre-layout; every Δ > noise floor attributed by a what-if (zero that parasitic, re-run) |
| 5 | **Snapshot every round**: `spicexplorer_layout.iterations.snapshot(iter_dir, note=<one-line headline>, detail=…, gen_path, gds, drc, lvs, pex, scorecard)` + `diff_png(prev, this)`; `REPORT.md` §Iterations = `iterations_table_md()` | it01 must reproduce the previous layout of record's sha; failed builds are rounds too |
| 6 | **Review** (`layout-reviewer`, report-only): rebuild → re-run everything → `REVIEW.md` + `REVIEW.yaml` (layout-review/1) + `REVIEW.png` + crops; re-scores prior findings by measurement | verdict PASS-with-notes only when every remaining miss is an approved decision, front-paged |
| 7 | **Area / knob optimization**: `layout/H12-pdk-cap/optimize_area.py` (stand-alone) or `opt/project_setup.yaml` via `spicexplorer-optimize` (`sim_engine: layout`, platform PR #101); constraints = the round's own gates | infeasible ≠ silent: net2 cap was the binding constraint 195/300 trials |

Commands (from the platform dir unless stated):
`uv run spicexplorer-layout build|knobs|render|snapshot|diff|iterations-md|annotate|validate-review …`;
`uv run python ../external/…/layout/H12-pdk-cap/optimize_area.py --budget N --workers 8 --out-dir <scratch>`;
LPF benches: `.venv/bin/python` in `experiments/023-replica-bias` with `from common import from_json, M`.

Rules the flow enforces: layouts are code, versioned; DRC/LVS/PEX always; designer ≠ reviewer; snapshots every round; a plan change is a human gate; iteration notes are one-line expert headlines (problem → fix → effect), no spec/finding codes.

Provenance: `layout/H12-pdk-cap/{PLAN.md,REPORT.md,REVIEW.md,iterations/}`, meta `doc/layout-lane.md`, platform package READMEs.
