# 2026-08-14 — layout legalization is a sizing change: a min-width bump at constant drawn W/L still moves the ladder current, so the projection must retune and re-certify, never just snap

KIND: journal entry | type: procedural | status: live

**Context.** The sign-off sizings came out of a continuous optimizer: off-grid
widths (SG13G2 grid is 5 nm), three cells with an hv bridge below the 0.30 µm
PDK minimum, and widths above the 10 µm PCell finger bound. `lab/grid.py`
(`legalize`) projects a `Design` onto the legal lattice: snap to grid, bump
sub-minimum widths at constant **drawn** W/L, split wide devices into equal
on-grid fingers (`ng`).

**Symptom.** The deliverable's bridge (0.259 → 0.30 µm, L scaled ×1.1585 to
preserve drawn W/L) moved fc from 250.03 to 242.90 Hz — **−2.9 %**, outside the
±2 % S2 box — even though drawn W/L was preserved to 1 part in 10⁴. The finger
split (in_a ng 1→2, bias ng 1→3) cost a further −0.9 Hz. On the D cell (bridge
0.162 → 0.30 µm, ×1.854) the shift was −16 %: fc 210.5 Hz.

**Mechanism.** PSP's effective geometry is W−ΔW / L−ΔL. The edge corrections ΔW,
ΔL do not scale with the drawing, so equal drawn-W/L ratios at different (W, L)
are **different effective W/L** — and the reuse ladder's branch current rides
exponentially on the resulting |V_SG| split. Preserving the drawn ratio is a
first-order fix only; the bigger the bump factor, the bigger the residual.

**Rule.**

1. `legalize()` is a *projection*, not a certified sizing: everything simulated
   afterwards must be the projected geometry (`build_signoff.py` asserts
   `legalize(d)` is a fixed point before writing anything).
2. When the projection breaks S2, `lab/retune.py` (`restore_fc`) retunes **only
   the device the min-width bump reshaped** — a log-log secant on its L (fc vs
   L is a clean power law here; 2 probes + 1 refinement lands within 60 mHz).
   Nothing else moves, so it is the projection completing itself, not a new
   design lever. Measured: H/022 bridge L 31.625 → 28.74 µm (fc 242.17 →
   249.99), D 80.965 → 49.98 µm (210.53 → 250.00).
3. Topology identity across the projection is **verified, not assumed**:
   old-vs-new `core.sp` must be circuitgraph-equivalent with
   **`match_models=True`** (platform `spicexplorer_circuitgraph.compare
   .compare_netlists`, `pdk=IHP_SG13G2`, `on_unknown="error"`, flattened
   subckt body). The default comparison classes devices only by type/polarity,
   so an lv↔hv flavour swap is invisible without that flag — measured: a
   deliberate `sg13_lv_pmos → sg13_hv_pmos` mutant passes the default test and
   is caught with `match_models=True`. All 11 signoff decks pass the strict
   test across the legalization.
4. Fingering caveat: `ng` splits satisfy the 10 µm PCell bound only if the
   per-finger width is itself on-grid — total width must be divisible; a
   remainder means nudging the total, which is a reportable geometry move.

**Provenance.** `lab/grid.py`, `lab/retune.py`, `scripts/build_signoff.py`
(feat/signoff-grid-legal); isolation table in the session ledger tags
`iso_original/iso_bridge-only/iso_ng-only/iso_full-legal`; per-cell moves are
printed by `build_signoff.py` and recorded in `signoff/<cell>/design.json`.
