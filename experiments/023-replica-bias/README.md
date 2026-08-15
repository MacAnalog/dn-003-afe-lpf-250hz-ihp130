# 023 — replica-biased reuse ladder: PVT and yield for the branch-stacked cell

**KIND: experiment.** Status: **MEASURED — verdict filed**; see **Hand-off** at
the end for the two deliverable cells and what remains before sign-off.

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

`B1` passes every line at all four process corners and both rails at 27 °C
(7/9 AXES; the two temperature vertices fail) but measures **THD −35.8 dB**
(S7 fail): the headroom re-centring put `gmf_a` at 7.8/5.2 µm (0.9 nA/sq, deep
weak inversion — see `thd-follows-inversion-level`). `B1-y2` (bridge ×9, bias
unit ×6, gmf_b ×2 area) keeps the same op point and lifts MC yield 49 → 81 %
(σ fc 7.5 → 3.7 Hz) at 4° of phase (337 → 333).

### 5. What the temperature axis is (and is not) — `diag_temp.py`, `tsw_*.json`

Op-only probes of `B1-y2` at 1.5 V, vicm 0.30–0.60, T = −40/27/85/125 °C,
PTAT bias (`LPF_BIAS_ALPHA=1`):

| T (°C) | vicm window with every signal device saturated | limiting device |
|---|---|---|
| −40 | 0.35 … 0.45 | `in_a` below, `bridge`/`gmf_b` above |
| +27 | 0.35 … 0.55 | `in_a` below, `gmf_b` above |
| +85 | 0.45 … 0.60+ | `in_b` below |
| +125 | **empty** (in_b −51 mV even at 0.60) | `in_b` |

Two mechanisms, both structural to the merged ladder at 1.5 V:

* the window drifts up ~+1.5 mV/K (`merged-ladder-headroom-identity`), so
  −40 and +85 °C have no common vicm — a **fixed input CM cannot cover the
  industrial range**; a CM that tracked ~+1.5 mV/K would (system-level, not
  claimed here);
* above ~100 °C the lv `in_a` runs out of |V_SG| altogether (measured
  vout_1 − vicm: 168 mV at 27 °C, 96 mV at 85 °C, **29 mV at 125 °C**), X grows
  by that much and `in_b` is in triode at every vicm. That is what the −18…−25 dB
  dc gain at +125 °C in every robustness table is; it is not an fc drift.

At constant current (α = 0) fc ∝ 1/T on top of that (320 / 250 / 156 Hz at
−40 / 27 / 125 °C), so a PTAT-class reference is the necessary first fix.
Measured on `B1-y2` at 1.5 V (`tsw_B1-y2_a*_1p5.json`):

| bias law | fc @ −40 / 27 / 70 °C | passes every line over | first fail |
|---|---|---|---|
| α = 0 (constant I) | 320.0 / 250.0 / 215.9 | 27 °C only | fc everywhere else |
| α = 1 (PTAT) | 253.9 / 250.0 / 244.9 | **−40 … +55 °C** | +70: fc 244.9 (0.1 Hz) |
| **α = 1.1** (constant-gm class) | **248.0 / 250.0 / 248.1** | **−40 … +70 °C** | +85: dc −0.50 dB (in_b) |
| α = 1.2 | 242.3 / 250.0 / 251.4 | −20 … +70 °C | −40: fc 242.3 |

α ≈ 1.1 flattens the residual n(T) slope: fc stays within 248.0–250.0 Hz over
110 K. The +85 °C wall is headroom, not bias — no α moves it. `vicm` 0.45
instead of 0.40 (`tsw_B1-y2_v0p45_a1_1p5.json`) buys nothing at the top and
costs −40 °C margin.

### 6. The S7 ↔ supply trade, measured — the `C`/`D`/`E` arms

* **Wider `gmf_b`/`in_b`** (`screen_headroom7.py`, 36 op-only arms, +T
  vertices): lowering the p |V_SG|'s relaxes the budget wall as the identity
  predicts (best worst-margin +5 → +21 mV at gmf_b 12/31.2, in_b 12/30, vicm
  0.50), but the arms built from it (`C1`–`C4`, gmf_a 1.5–3/45) lose the S1
  phase certificate (ph 311–328°): the extra gate capacitance on `net4`/`voutp`
  costs more phase than the headroom is worth. **`gmf_b` ≤ 6/31.2 with `gmf_a`
  1–1.5/45** is the phase-legal region (B5-g6v50 332.5°, E3 332.3°).
* **Bridge inversion is not a THD lever** (`D0`–`D3`, caps frozen): bridge
  4.86 → 1.0 → 0.5/32.8 µm (13 → 63 → 126 nA/sq) moves THD −35.9 → −36.6 →
  −37.1 dB and mis-tunes the shape (peaking 0.4–0.7 dB). THD is `gmf_a`'s, at
  biquad A's high-Q internal node, as `thd-follows-inversion-level` says.
* **vicm around B5-g6v50** (`E1`–`E4`): 0.52 buys `sf` and loses `ss`
  (dc −0.36); 0.54 loses `ss` harder. **`E3` = gmf_a 1.5/45, gmf_b 6/31.2,
  in_b 2/30, vicm 0.50** is the point where all four process corners and the
  high rail pass with **THD −40.9 dB** — S7 by 0.9 dB, the thinnest margin in
  the set (THD is not MC'd; treat the margin as nominal-only).
* **Supply envelope at 27 °C** (`vsw_*.json`, 1.35 … 1.65 V in nine steps):
  `B1-y2` passes 1.35–1.65 V; `B3-a2`, `B5-g6v50`, `E3` pass **1.40–1.65 V**
  and fail only 1.35 V (dc −0.4 … −1.4 dB, ph 316–320°): the S7-grade cell holds
  −6.7 % / +10 %, i.e. a ±5 % rail with margin, not ±10 %.
* **Yield lever on E3** (`yield.py`, `E3-y*.json`): bridge ×9 / unit ×6 (with
  or without gmf_b ×2) is phase-limited (329.9° / 327.5°, S1 fail); **×4/×4
  (`E3-y0`) is the phase-legal point: 331.3°, yield 48 → 73 %, σ fc 7.3 → 4.1
  Hz**, THD −40.7 dB after the uniform cap re-trim (`E3-y0v.json`).

### 7. The two deliverable cells (all numbers this repo, `*.robust.a1p1.json`, `tsw_*`, `vsw_*`)

| | reference (un-stacked) | sign-off `B-balanced` | **`B1-y2`** | **`E3-y0`** |
|---|---|---|---|---|
| topology | reference | b (merged ladder) | **d** (merged + replica, m = 3) | **d** (merged + replica, m = 3) |
| gmf_a / gmf_b / in_b (µm) | 4/4 · 4/4 · 4/4 | 7.8/5.2 · 2/31.2 · 15.6/10.4 | 7.8/5.2 · 2.83/44.1 · 2/30 | 1.5/45 · 6/31.2 · 2/30 |
| vicm (V) | 0.65 | 0.65 | 0.40 | 0.50 |
| IRN µVrms / P nW / C pF | 50.18 / 12.07 / 98 | 29.38 / 6.01 / 152.9 | **29.3 / 8.93 / 126.0** | **29.5 / 8.93 / 125.8** |
| ph_max ° / ripple dB | — | 332.2 / 0.059 | 333.0 / 0.047 | 331.3 / 0.046 |
| **THD @ 50 Hz, 175 mVpp** | −48.4 | −41.9 | **−35.9 (S7 FAIL)** | **−40.7 (S7 pass, 0.7 dB)** |
| process fc span ss/ff/sf/fs (27 °C, 1.5 V) | 1.02× | 3–38× (family) | **1.010×**, all PASS | **1.016×**, all PASS |
| supply, every line, 27 °C | n/a (IRN 50 by construction; fc 250.2 at both rails, but 116 Hz at ss/1.35 V) | 1/3 (1.5 only) | **1.35–1.65 V** | **1.40–1.65 V** |
| temperature, every line, 1.5 V, α = 1.1 | — (α = 0: 27 °C only) | — | **−40 … +70 °C** | **−20 … +70 °C** (+85: fc 244.9) |
| AXES / REDUCED-22 / full-45 (α = 1.1) | 0/22, 0/45 (α = 0) | 1/22 | 8/9 · 9/22 · 21/45 | 6/9 · 5/22 · 16/45 |
| MC all-pass yield (n = 100, tt mismatch) | — | 70 % | **81 %** (σ fc 3.7 Hz) | **73 %** (σ fc 4.1 Hz) |
| bridge / unit / gmf_b area vs B1 | — | — | ×9 / ×6 / ×2 | ×4 / ×4 / ×1 |

Every failing 45-grid corner of both cells is a two- or three-axis corner
containing 1.35 V, −40 °C or ≥ 100 °C; none is a bias failure (fc span over the
passing region ≤ 1.02×). What the two cells cannot do, and why, is §5.

## Findings — verdict

**Verdict: the hypothesis holds on process and supply and is falsified on
temperature; the S7 ↔ supply trade is real and is resolved as two cells.**

* **Process:** replica bias (three devices, signal path untouched) takes the
  merged ladder's fc span at 27 °C / 1.5 V from 14× (`E-combo`) / 3–38× (family)
  to **1.01–1.02×** — the same figure as the un-stacked, fully mirrored
  reference — for 1 replica branch (m = 3 → ~3 nW inside S6). Confirmed on
  every cell built here.
* **Supply:** with `in_a` lv, `in_b`/`gmf_b` hv narrow/long and vicm centring
  X, `B1-y2` holds every S1–S6 line over **1.35–1.65 V**; the S7-grade `E3-y0`
  holds **1.40–1.65 V**. The 1.35 V line is the budget wall
  `VDD ≥ V_GS(gmf_a) + max V_SG + 2m` (§3): moderate-inversion `gmf_a` costs it.
* **Temperature:** a constant-gm-class reference (α ≈ 1.1) holds fc within
  ±0.4 % over −40…+70 °C; **the full −40…+125 °C range is not reachable by any
  sizing of this ladder at 1.5 V** — the saturation window drifts ~1.5 mV/K
  against a fixed vicm and the lv `in_a` has no |V_SG| left above ~100 °C
  (§5). This is a topology property of stacking p-followers under a p-type
  gm_f at a 1.5 V rail, consistent with the external reviewer's expectation
  that a nA-class filter does not meet a full PVT box; the honest claim is the
  measured envelope, not the box.
* **Yield:** the replica adds a mismatch term; bias-device area buys it back
  (81 % / 73 %) until the S1 phase certificate caps the area (`E3-y1/y2`,
  `B1-y3`).
* **THD:** unchanged conclusion of `thd-follows-inversion-level` — bridge
  inversion, gmf_b width and cap allocation are not levers at flat shape.
  `E3-y0`'s −40.7 dB is a nominal-only number; a THD MC / corner THD is the
  first thing to run before it is quoted.

**Prediction table, scored:** process span ≤ 1.15× — **met** (1.01–1.13×);
supply ±1 % where headroom holds — **met** (fc 249.5–250.2 over 1.35–1.65 V on
B1-y2); temperature 1/T unchanged at α = 0 — **met**, and the PTAT fix is
measured; MC — 81 % / 73 %, replica term visible (σ fc 3.7–4.1 Hz vs 2.2–3.3
on the sign-off cells at larger area).

## Hand-off (2026-08-15, second session)

**Cells** (all `<name>.json` here; numbers at 27 °C / 1.5 V / tt unless stated):

| cell | what | nominal | THD | axes | 45-grid α=0 / α=1 / α=1.1 | MC |
|---|---|---|---|---|---|---|
| `E-rep`, `B-rep` | sign-off cell + replica, nothing else | PASS | −55.0 / −41.6 | 2/9, 4/9 | — | — |
| `B1` | B + replica m=3 + in_b 2/30, gmf_b 2/31.2 hv, vicm 0.40, caps re-fit | PASS (IRN 30.8, 8.9 nW, ph 337) | −35.8 (S7 FAIL) | 7/9 | 12/45 / 20/45 / — | 49 % |
| **`B1-y2`** | B1 + area bridge ×9, unit ×6, gmf_b ×2 | PASS (ph 333) | −35.9 (S7 FAIL) | 7/9 (8/9 at α ≥ 1) | 12 / 20 / **21**/45 | **81 %** |
| `B3-a2`, `B3-a45`, `B4-*`, `B5-*` | gmf_a 1–2/45 (moderate inversion), vicm 0.42–0.52 | PASS | −41.5 … −48.0 | 4–5/9: 1.35 V + one of ss/sf | — | — |
| `C1`–`C4` | gmf_b 12–16/31.2, in_b 12/30 (headroom7 arms) | **S1 FAIL** (ph 311–328) | −20 … −52 | — | — | — |
| `D0`–`D3` | B1-y2 with bridge 1.0 / 0.5 µm (THD probe, caps frozen) | shape moves | −35.9 → −37.1 | — | — | — |
| `E1`, `E2`, `E4` | B5-g6v50 at vicm 0.52/0.54, gmf_a 1/1.5 | PASS | −42 … −44 | ss fails | — | — |
| `E3` | gmf_a 1.5/45, gmf_b 6/31.2, in_b 2/30, vicm 0.50 | PASS (ph 332.3) | **−40.9** | **6/9** (all process + 1.65 V) | — / — / 16/45 | 48 % |
| **`E3-y0`** (`E3-y0v.json` has THD + axes) | E3 + area bridge ×4, unit ×4 | PASS (ph 331.3) | **−40.7** | 6/9 | — / — / **16**/45 | **73 %** |
| `E3-y1`, `E3-y2` | E3 + ×9/×6 (+ gmf_b ×2) | **S1 FAIL** (329.9 / 327.5) | — | — | — | 2 % / 0 % |

**Envelopes:** `tsw_<cell>_a<α>_1p5.json` (nine temperatures at 1.5 V),
`vsw_<cell>.json` (nine supplies at 27 °C); `robust_*_a1p1.log` /
`*.robust.a1p1.json` are the boxes at α = 1.1.

**Next steps, in order:**

1. **THD at corners / THD MC for `E3-y0`** — its S7 margin is 0.7 dB nominal.
   If it does not survive, the S7 cell is `B3-a45`-class (−48 dB) with the
   `sf`/`ss` corner conceded, and that trade is stated.
2. **fc trim of +1 Hz nominal on both cells** (caps ×0.996) buys +85 °C on
   `E3-y0` (fc 244.86) and is free; do it in the cap re-fit, not by hand.
3. Move `B1-y2` and `E3-y0` toward `signoff/`: `scripts/draw_xschem.py` needs
   topology `d` (the replica branch + `vbr` rail are not drawn yet; `verify.py`
   refuses until then). Sign-off must state per cell: rail range, temperature
   range at α = 1.1, and that the bench reference is ideal (α is a model of a
   constant-gm reference, not a circuit here).
4. Graduate to `doc/journal/`: (a) *temperature window of the merged ladder:
   fixed vicm cannot cover −40…+125 °C; lv in_a runs out of |V_SG| above 100 °C*;
   (b) *α ≈ 1.1 (constant-gm) not α = 1 flattens fc*; (c) *phase certificate
   caps the bias-area yield lever*. Add one experiment-log row.
5. Layout: no layout lane exists in this repo yet; `klayout`, `magic`, `netgen`,
   `gdsfactory` + `ihp-gdsfactory` are installed on the research server, and
   the PDK ships `libs.tech/parasitics`. Post-layout is the next phase once a
   cell is signed off (item 3).

**Harness changes in this branch (procedural, review):** `lab/dut.py` topology
`d` + `replica_of`; `lab/corners.py` `PROCESS_ONLY/SUPPLY_ONLY/TEMP_ONLY/AXES`
+ native-lane `MAX_WORKERS`; `lab/mc.py` native-lane `WORKERS`;
`lab/shape.py` `fit_butter(fixed=)`. `make lint` green. Second session added
only experiment-local scripts (`diag_temp.py`, `tsweep.py`, `vsweep.py`,
`screen_headroom7.py`) — no `lab/` edits. Known harness weakness: `fit_butter`
warm-started from B1's caps lands in the wrong cap basin (THD −20 dB, phase
fail) when device gm's move by more than ~2× (`C1`, `C2`, `C4`); start from the
nearest built cell of the same gm class instead.

## Files

| file | what |
|---|---|
| `common.py` | loaders, replica helper, op-only `headroom()` instrument, corner sets |
| `screen_headroom*.py` / `headroom*_*.json` | the four op-only screens (flavour × vicm × gmf_a; in_b × gmf_b × vicm) |
| `build.py`, `variant.py`, `polish.py` | candidate builders (replica → caps → scorecard → THD → AXES) |
| `robust.py` | the expensive box for one candidate: AXES + REDUCED (+ full) + MC, at `LPF_BIAS_ALPHA` 0 or 1 |
| `<name>.json` | each candidate's sizing (`to_json`) + nominal + axes rows |
| `<name>.robust.a<α>.json` | the robustness box results |
| `diag_temp.py` | op-only vicm × T probe of the saturation window (§5) |
| `tsweep.py`, `vsweep.py`, `tsw_*.json`, `vsw_*.json` | temperature envelope (nine T at 1.5 V) and supply envelope (nine V at 27 °C) of one cell |
| `screen_headroom7.py` / `headroom7_B1.json` | wider gmf_b/in_b arms + temperature vertices |
