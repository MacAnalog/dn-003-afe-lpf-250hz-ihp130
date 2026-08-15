# 023 — replica-biased reuse ladder: PVT and yield for the branch-stacked cell

**KIND: experiment.** Status: **IN PROGRESS** — see **Hand-off** at the end
for exactly what is measured, what is running, and the next step.

The sign-off set (`signoff/`) passes S1–S8 at the bench point and **1/22** PVT
corners, MC yield 45–96 %. `signoff/COMPARISON.md` filed that as "the
threshold-referenced supply limitation". This experiment separates the axes,
finds that the limitation is **process, supply and temperature at once**, fixes
the bias mechanism with the smallest topology change that keeps the cell novel
(three devices, signal path untouched), and then measures what the merged
ladder can and cannot do once its current is mirror-referenced.

**Paper(s):** none new. The cell keeps its S8 provenance — branch stacking
(`gmc-compact` + `tian2023`) and the floating differential cap (`fvf-2nd`) are
still visible in the netlist. The replica bias is textbook (a diode-connected
copy of the ladder's top two devices, sunk by a mirror), added as a *bias*
technique, not claimed as a paper technique.

**Hypothesis:** replacing the bridge-gate rail `vbn` by a rail generated from a
matched replica of `gmf_b` and `bridge` (topology `d` in `lab/dut.py`) holds fc
inside 245–255 Hz across `ss/ff/sf/fs` at nominal V/T — from a 13.6–524 Hz
spread on the sign-off cells — at a cost of ≤ 5 nW; and a headroom-recentred
sizing (lv `in_a`, narrow hv `in_b`/`gmf_b`, vicm 0.40 V) then holds every
S1–S7 line over VDD = 1.35–1.65 V at 27 °C.

**Control:** the same sign-off sizing with the replica added and nothing else
(`E-rep`, `B-rep`), and the un-stacked reference measured on the same corner
sets in the same session. Where caps move, the control is the sign-off cell's
own re-fitted caps (`B-rep`).

**Prediction (before running):**

| axis | sign-off cells | predicted with replica | why |
|---|---|---|---|
| process fc span (ss→ff, 27 °C, 1.5 V) | 3–38× | ≤ 1.15× | I_L = m·iref; only Vds/gds terms remain |
| supply fc (1.35–1.65 V) | 96 → 258 Hz | ±1 % where headroom holds | ladder current no longer ∝ exp(VDD) |
| temperature fc (−40/+125 °C, α = 0) | 1/T | 1/T (unchanged) | constant-current bench; needs PTAT (α = 1) |
| MC all-pass yield | 45–96 % | not predicted — new mismatch term (replica vs ladder) | measured, not asserted |

## What was measured

### 1. The one-axis screen the sign-off was missing (`lab.corners.AXES`)

Every off-nominal row of the 22-point `REDUCED` set moves two or three axes at
once, so a bias failure and a headroom failure read the same. Process alone,
at the bench's V and T, on the nine sign-off cells and the reference:

| cell | fc @ ss | ff | sf | fs | span |
|---|---|---|---|---|---|
| A-minarea | 13.6 | 524 | 299 | 205 | 38× |
| E-combo | 28.3 | 398 | 281 | 221 | 14× |
| H-shipped | 125 | 377 | 277 | 224 | 3.0× |
| **reference (un-stacked)** | **247.8** | **252.8** | **251.8** | **248.8** | **1.02×** |

The reference is process-robust because every current in it is mirrored from
`iref`; the merged ladder is not because its current is the solution of
`|V_SG|(gmf_b) + |V_SG|(bridge) = VDD − vbn` — three thresholds against the
supply. That is a topology property, not a sizing one.

### 2. Topology `d` — the replica (three devices, shared by both halves)

```
vdd → xr1 (p, diode, = gmf_b) → rep_x → xr2 (p, diode, = bridge) → vbr → xr3 (n, gate vbn, m·unit) → gnd
```

`vbr = VDD − |V_SG|(xr1) − |V_SG|(xr2)` at I_t = m·iref, so the ladder with its
bridge gate on `vbr` solves to `I_L = I_t`. Measured on E-combo: I_L 3.03 nA vs
sink 3.04 nA (0.4 %). Cost: one branch (I_t·VDD ≈ 3–4.5 nW, inside S6) and a
new replica-to-ladder mismatch term.

**Replica alone (`E-rep`, `B-rep`), one axis at a time:**

| cell | nominal | fc @ ss/ff/sf/fs | fc @ 1.35/1.65 V | verdict on AXES |
|---|---|---|---|---|
| E-rep | PASS, THD −55.0 | 231 / 261 / 252 / 247 | 95 / 258 | 2/9 — ss dc −1.1 dB, ff a1000; **headroom**, not bias |
| B-rep | PASS, THD −41.6 | 221 / 250 / 250 / 245 | 182 / 250.5 | 4/9 — same |

Process fc span 14× → 1.13× (E), but dc gain / ripple still fail at ss and the
low rail: `gmf_b` has 35 mV of |Vds| margin at nominal in E-combo, 78 mV in B.

### 3. The headroom identity of the merged ladder (op-only screens, ~1000 sims)

With X = VDD − vicm − |V_SG|(in_a) (the voltage available above biquad A's
output), the three devices between `vout_1` and VDD have

    |V_SD|(bridge) = X − |V_SG|(gmf_b)
    |V_SD|(gmf_b)  = X − |V_SG|(in_b)
    |V_SD|(in_b)   = |V_SG|(gmf_b) + |V_SG|(in_b) − X

so all three saturate only for X in
`[max(V_SG(gmf_b), V_SG(in_b)) + m, V_SG(gmf_b) + V_SG(in_b) − m]` — a window
of width `min(V_SG(gmf_b), V_SG(in_b)) − 2m`. Consequences, all confirmed by
the screens (`headroom*_*.json`):

- **`gmf_b` must be hv.** The E/F/G cells' lv `gmf_b` (|V_SG| ≈ 0.38 V) gives a
  0.14 V window — narrower than the ±0.15 V supply box. This is why the
  E family cannot be made supply-tolerant by any vicm.
- **`in_a` lv, `in_b`/`gmf_b` hv and narrow/long** (2/30 and 2/31.2 µm): both
  |V_SG| ≈ 0.55–0.6 V, window ≈ 0.35 V.
- **vicm ≈ 0.40 V** centres X in the window at 27 °C; the bottom constraint
  `vicm + |V_SG|(in_a) − V_GS(gmf_a) ≥ m` sets the floor.
- **Temperature drifts the window 3δ** (every |V_SG| moves ~−1.5 mV/K in weak
  inversion, and X moves the other way): the −40…125 °C span (δ ≈ 0.15 V) is
  ~0.45 V of drift against a 0.35 V window. **A merged ladder cannot hold the
  full industrial temperature range at 1.5 V in weak inversion**; the
  passing range is bounded and is measured below rather than assumed.

### 4. Candidate `B1` = B-balanced + replica (m = 3, I_L 1.98 nA) + in_b 2/30, gmf_b 2/31.2, vicm 0.40, caps re-fitted

<!-- B1 tables filled from B1*.json / *.robust.*.json -->

## Findings — verdict

**Verdict:** _pending — filled from the robustness box below._

## Hand-off (2026-08-15, end of session)

**Cells so far** (all `<name>.json` here; numbers at 27 °C / 1.5 V / tt unless
stated; "axes" = `lab.corners.AXES`, 9 points):

| cell | what | nominal | THD | axes | 45-grid α=0 / α=1 | MC |
|---|---|---|---|---|---|---|
| `E-rep`, `B-rep` | sign-off cell + replica, nothing else | PASS | −55.0 / −41.6 | 2/9, 4/9 | — | — |
| **`B1`** | B + replica m=3 + in_b 2/30, gmf_b 2/31.2 hv, vicm 0.40, caps re-fit | PASS (IRN 30.8, 8.9 nW, ph 337, ripple 0.054) | **−35.8 (S7 FAIL)** | **7/9** (all process + both rails; only −40/+125 °C fail) | **12/45 / 20/45** (reference 0/45) | 49 % (σ 7.5 Hz) |
| **`B1-y2`** | B1 + area: bridge ×9, bias unit ×6, gmf_b ×2 | PASS (ph 333) | pending (`B1-y2.json`) | pending (`robust_B1-y2_a*.log`) | pending | **81 %** (σ 3.7 Hz) |
| `B1-y3` | ×16 / ×9 / ×2 | ph 330.75 — phase-limited | | | | 77 % |
| `B3-a45` | B1 + gmf_a 1/45 (moderate inversion), vicm 0.50 | PASS | **−48.0** | in_a margin 30 mV | | |
| `B4-v42/45/48`, `B5-*` | gmf_a 1/45 with in_a/gmf_b/vicm re-balanced | PASS | −42 … −48 | 4–5/9: **1.35 V and `sf` fail** (budget wall) | | |

**The open trade.** `VDD ≥ V_GS(gmf_a) + max(V_SG(gmf_b), V_SG(in_b)) + 2·Vds_min`:
S7 wants gmf_a in moderate inversion (+70 mV), the 1.35 V rail has no 70 mV to
give. `screen_headroom6.py` (72 op-only arms over gmf_a/gmf_b/in_b widths ×
vicm, scored on both rails + 4 process corners) is the last search for a
compromise; read `headroom6_B1.json` / its log, build the top arms with
`variant.py B1 <out> --dev gmf_a W 45 --dev gmf_b W 31.2 --dev in_b W 30 --vicm V --polish 120`
(warm-start from B1's caps — cold analytic starts diverge, see journal
`one-axis-corner-sets`) and read THD + axes. If none passes both, the
deliverable is TWO cells with the trade stated: `B1-y2` (P/V-robust, yield 81 %,
S7 −36) and a `B5`-class cell (S7 pass, ±10 % rail not).

**Then:** fill section 4 + the verdict from `B1-y2.robust.a0/a1.json`
(`robust.py` prints the tables), decide the temperature envelope from a
`TSWEEP` run, and only then move a cell toward `signoff/` (needs
`scripts/draw_xschem.py` support for topology `d` — the replica branch and
the `vbr` rail are not drawn yet; `verify.py`'s gates will refuse until then).

**Harness changes in this branch (procedural, review):** `lab/dut.py` topology
`d` + `replica_of`; `lab/corners.py` `PROCESS_ONLY/SUPPLY_ONLY/TEMP_ONLY/AXES`
+ native-lane `MAX_WORKERS`; `lab/mc.py` native-lane `WORKERS`;
`lab/shape.py` `fit_butter(fixed=)`. `make lint` green.

## Files

| file | what |
|---|---|
| `common.py` | loaders, replica helper, op-only `headroom()` instrument, corner sets |
| `screen_headroom*.py` / `headroom*_*.json` | the four op-only screens (flavour × vicm × gmf_a; in_b × gmf_b × vicm) |
| `build.py`, `variant.py`, `polish.py` | candidate builders (replica → caps → scorecard → THD → AXES) |
| `robust.py` | the expensive box for one candidate: AXES + REDUCED (+ full) + MC, at `LPF_BIAS_ALPHA` 0 or 1 |
| `<name>.json` | each candidate's sizing (`to_json`) + nominal + axes rows |
| `<name>.robust.a<α>.json` | the robustness box results |
