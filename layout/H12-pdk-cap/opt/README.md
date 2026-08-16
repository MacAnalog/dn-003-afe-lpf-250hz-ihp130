# H12-pdk-cap layout-area optimization — through the spicexplorer platform

The search `../optimize_area.py` runs stand-alone (Nevergrad over the generator's numeric knobs;
build → DRC → LVS → PEX → the block's frozen benches; round-3 gates as constraints), expressed as
an ordinary `spicexplorer` project: `sim_engine: layout` selects the platform's layout-flow
backend (`spicexplorer.backends.layout`), the 25 numeric knobs are `dut_params`, ONE testbench
is the flow (`flow.yaml`), and the round-3 gates are target specs. Nevergrad, checkpoints and
reports are the platform's ordinary path; the LPF benches still run in this repo's own venv.

```bash
cd <workspace>/spicexplorer-platform            # has nevergrad + the leaf tools (uv sync --extra layout)
uv run spicexplorer-optimize ../external/agentic-design-250hz-lpf-ihp130/layout/H12-pdk-cap/opt/project_setup.yaml \
    --budget 240 --workers 8 --outdir /path/to/scratch/h12_layoutopt
```

Requirements (this server): `~/miniconda3/envs/ai_env/bin/python` (gdsfactory; `GDS_PYTHON`
overrides), `klayout` + kpex (`~/miniconda3/envs/pex/bin/kpex` fallback), `PDK_ROOT=~/local/pdks`,
this repo's `.venv` (the benches) and `~/local/bin/ngspice` (`LPF_NGSPICE`).

## Files

| File | Role |
|---|---|
| `flow.yaml` | `layout-flow/1`: generator `../gen_H12_pdk_cap.py`, cell `lpf_core`, sizing `signoff/post-pvt/H12-pdk-cap/design.json`, the 8 categorical/floorplan knobs pinned in `fixed_params`, DRC, LVS via the generator's `write_lvs_reference` (per candidate — the reference depends on the knobs), kpex CC on the **MIM-stripped** GDS with the schematic `xc*` cards re-inserted and the header rewritten to `.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd`, `ac_gnd_nets` (→ `c_net2_ff` = C(net2 → AC ground), the brief's budget number), and the **`measure:` hook** below. |
| `measure_post.py` | The block's frozen scorecard on the extracted core (`lab.metrics.evaluate` through `Design.dut_override`, exactly `_bench` in `../optimize_area.py`), run in `.venv` with cwd `experiments/023-replica-bias`; returns every nominal value (`ph_max_deg`, `fc_hz`, `a1000_db`, `irn_uv`, `p_core_nw`, …) + `n_violations`. Speaks `spicexplorer_layout.measure_protocol` (JSON in / one JSON line out); honours `corner.options.cap_corner` (→ `LPF_CAP_CORNER`) and `corner.params.iref_scale`. |
| `project_setup.yaml` | 25 numeric `dut_params` (`BOUNDS`, `init` = round-3 defaults, `is_integer` for the counts), testbench `layout`, targets: `area_um2` minimize (target = round-3 247 137 µm², `reward_type: log` — monotonic below the target; `relative-log` rewards proximity to the target and mis-ranks a minimize objective), `ph_max_deg ≥ 331.10`, `c_net2_ff ≤ 32.4`, `c_net3_ff ≤ 32.4`, `n_violations == 0`, `drc_pass == 1`, `lvs_match == 1`, `pex_ok == 1`; TwoPointsDE, `seed_from_init: true` (trial 0 = the layout of record). |

Why the `measure:` hook here (and `postlayout:` in the platform's 5T OTA example): the LPF
scorecard is this repo's own harness (S1..S7 definitions, corners, cap models, iref) — the
hook runs it unchanged in the LPF venv; `postlayout:` is for a block whose benches ARE platform
ngspice decks (then Tier-1 registry recipes read the post-layout waves through the layout
testbench with no extra code).

## Parity (round-3 layout of record = trial 0)

`--budget 3 --workers 3` on this server (2026-08-16): trial 0 = the defaults →
**area 247 136.9 µm², ph_max 331.1595°, c_net2 32.328 fF, c_net3 32.329 fF, fc 248.64 Hz,
n_violations 0, DRC 0 / LVS match / PEX ok** — the round-3 numbers of `../REPORT.md` and
`../optimize_area.py`'s baseline (~150 s per trial: build 7 s, DRC 85 s, LVS 28 s, PEX 19 s,
benches 9 s). Trials 1–2 (random DE candidates) failed the generator's own symmetry
assertions at build → `build_fail`, every metric NaN → maximal penalty (the stand-alone script's
`build_fail` rows).

Artifacts per trial: `<outdir>/layout/layout/run_<n>_layout/{lpf_core.gds, drc/, lvs/, pex/,
lpf_core_pex_cc.sp, measure.log, summary.json}`; checkpoints under the platform's `work/auto_save/`.
