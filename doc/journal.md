# Journal — index

KIND: index

Kept deliberately small: **one line per entry**. The content lives in
[`doc/journal/`](journal/), one file per entry, so any single entry fits in an
agent context.

**Conventions.** Entries are **dated**, **typed** (`semantic` = distilled design
knowledge; `procedural` = harness / measurement / tooling recipes), and carry
**provenance** (ledger tags, deck hashes, experiment dirs, file:line, paper
eq/fig refs). They are **retired by supersession, never deleted** — prepend
`[superseded <date> — see X]` in the entry file and flip its `status:` line; the
context pack skips superseded entries.
**Adding an entry = write the file + add one line here (lint-enforced).**

Rows are sorted **newest first** (enforced by `scripts/lint.py`); rows sharing a
date are grouped by subject.

| date | entry | type | status | hook |
|---|---|---|---|---|
| 2026-08-31 | [A generator's name is not its physics](journal/a-generator-name-is-not-its-physics.md) | semantic | live | `igig` is the correlated half of the CHANNEL noise, not gate leakage — gate current is exactly 0 on thick oxide; channel = **89 %** of IRN power and `S_i/2qI_D` = **0.87–1.04** |
| 2026-08-28 | [A one-axis corner claim is not a box](journal/one-axis-certification-does-not-superpose.md) | semantic | live | the certified axes all pass; 7/45 cross-product points lose a complex pole pair, incl. one whose three coordinates are each certified |
| 2026-08-28 | [`LPF_BIAS_ALPHA` is part of a temperature measurement](journal/bias-alpha-is-part-of-a-temperature-measurement.md) | procedural | live | default 0 is constant-current; the delivered cells were certified at 1.1, and 27 °C cannot tell them apart |
| 2026-08-29 | [One thread per worker, or the batch thrashes](journal/one-thread-per-worker-or-the-batch-thrashes.md) | procedural | live | ngspice takes ~11 threads/process; 126 workers × 11 threads = 5 draws/min. `OMP_NUM_THREADS=1` + `LPF_JOBS=32` = 1.8 draws/s |
| 2026-08-27 | [symbolic-model-from-a-certified-netlist](journal/symbolic-model-from-a-certified-netlist.md) | procedural | live | recipe for an EXACT `H(s)`/`Z_T`/pole-zero map from an as-built subckt + one `.op` via `netlist2tf` (closes 0.027 dB / 0.34° on ac, 2e-7 % on per-generator noise): extract the capacitance block, bind by role and assert bulk==source, symbols on the DM half-circuit but numbers on the full differential pencil. Five traps (spicelib prep, X-wrapped PDK MOS — fixed in the platform, ngspice `$` sigil + lower-cased probe echo, singular pencil on driven rows, a generator-name regex worth √2). **`ngspice .pz` is unusable** on any cell whose input gate carries dc bias — replaced by pencil + sim-only 4-pole fit + overlay, and the fit's all-real-pole refit (0.215 → 4.85 dB) proves the poles complex from sim data alone. Two-tone spacings must be EVEN or the DFT returns scalloping (−0.79 dBc) |
| 2026-08-27 | [weak-inversion-model-traps](journal/weak-inversion-model-traps.md) | semantic | live | at 0.66–2.6 nA: (1) `cgb` carries 247.4 of `cgg`'s 250.5 fF — there is no channel — so reading `cgs` alone is **81× too small**, and that one capacitance is the entire 2 % closed-form→full-model `fc` gap AND the origin of both out-of-band zero pairs (`cgd` = 3.1 aF, moves nothing); (2)–(3) channel noise is **0.87–1.04 × 2qI_D**, not `4kTγgm`, and arrives as two generators whose SUM is `2qI_D` (corrected 2026-08-31, see above); (4) the two halves' distortion currents add **in phase** (one-half sums under-predict HD3 by 21 dB). Plus the `κs²` branch-stacking term that maps the isolated Q's onto the filter's |
| 2026-08-16 | [dummy-rows-priced-by-build-pex-bench](journal/dummy-rows-priced-by-build-pex-bench.md) | semantic | live | the bias array's dummy ROWS measured 5.6 % of the cell, +2 fF on net2 and −0.05° ph_max for a hand-bound benefit; it14 (rows = 0 + campaign knobs) 228 094 µm² / 331.221° / 30.2 fF — price matching insurance with build→PEX→bench before adopting |
| 2026-08-16 | [gate-net-wire-haul-sets-postlayout-phase](journal/gate-net-wire-haul-sets-postlayout-phase.md) | semantic | live | post-layout phase is set by the C on the second-stage gate nets net2/net3 at 0.0225 °/fF: a 170 µm TopMetal1 haul cost 1.1°; the floorplan (which array sits on the axis) fixed it, routing knobs buy tenths; 195/300 optimizer trials hit the net2 cap |
| 2026-08-16 | [kpex-mim-well-blind-spots-and-klayout-concurrency](journal/kpex-mim-well-blind-spots-and-klayout-concurrency.md) | procedural | live | kpex has no `cap_cmim` (strip MIM, re-add cards; ≤ 15 fF unextracted), n-well junction C in no model (−0.11…−0.26°), RC mesh non-deterministic (CC in loops), HD2 < −97 dB is bench floor, > 2 concurrent KLayout jobs → spurious empty-list DRC/LVS fails |
| 2026-08-16 | [layout-lane-recipe](memory/procedural/layout-lane-recipe.md) | procedural | live | brief → plan gate → generator → DRC/LVS/PEX (kpex CC in loop, RC once) → benches via `Design.dut_override` → snapshot every round → review; commands, environments, gates |
| 2026-08-16 | [h12-layout-parasitic-map](memory/semantic/h12-layout-parasitic-map.md) | semantic | live | it14 layout of record: pre vs post table, per-net C vs budget, unextracted terms, the 3.8 kHz zero / −101 dB feed-through floor, where the area is |
| 2026-08-15 | [replica-bias-mirror-references-the-ladder](journal/replica-bias-mirror-references-the-ladder.md) | semantic | live | the sign-off family's 1/22 PVT is **process** as much as supply: process alone at nominal V/T moves fc 13.6→524 Hz (A) / 28→398 (E) while the un-stacked reference holds 247.8–252.8, because the merged ladder's current solves `|V_SG|(gmf_b)+|V_SG|(bridge)=VDD−vbn`. Topology `d` (`lab.dut.build_d`, `replica_of`) adds ONE shared 3-device replica (diode gmf_b copy → diode bridge copy → m·unit sink) that generates the bridge-gate rail: I_L = m·iref (measured 3.03 vs 3.04 nA), fc span 14× → 1.13× (E), and with headroom re-centred `B1` passes every line at all 4 process corners and both rails; 45-grid 12/45 (20/45 with a PTAT reference) vs reference 0/45. Cost: 3 devices, 3–4.5 nW, and a replica-vs-ladder mismatch term (MC 70 → 49 % before area) |
| 2026-08-15 | [merged-ladder-headroom-identity](journal/merged-ladder-headroom-identity.md) | semantic | live | with X = VDD − vicm − \|V_SG\|(in_a): bridge Vds = X − V_SG(gmf_b), gmf_b Vds = X − V_SG(in_b), in_b Vds = V_SG(gmf_b)+V_SG(in_b) − X ⇒ the top window is **min(V_SG(gmf_b), V_SG(in_b)) − 2·Vds_min** and the supply budget is VDD ≥ V_GS(gmf_a) + max(V_SG) + 2·Vds_min. So gmf_b must be hv (lv's 0.38 V gives a 0.14 V window < the ±0.15 V rail — E/F/G can never be supply-tolerant), in_b/gmf_b narrow-long (0.55–0.6 V), in_a lv, vicm ≈ 0.40; and the window drifts **3δ ≈ 0.45 V** over −40…125 °C against 0.35 V — the merged ladder holds ~0–70 °C at 1.5 V, not the industrial range |
| 2026-08-15 | [thd-follows-inversion-level](journal/thd-follows-inversion-level.md) | semantic | live | S7 in the stacked cell is set by the INVERSION LEVEL of gmf_a/gmf_b (exponential devices whose gate is the swinging internal node), not by caps: at equal flatness the cap family sits at −36…−38 dB, while gmf_a 7.8/5.2 → 2/45 → 1/45 µm gives −35.8 → −41.5 → **−48.0** at unchanged shape (E −55 and G −71 carry 1/45 and 1/15; wider gmf_b made it WORSE, −27). Price: ~70 mV more V_GS(gmf_a), taken straight out of the supply budget — at 1.5 V ±10 % the merged cell has S7 margin or rail margin, not both |
| 2026-08-15 | [one-axis-corner-sets](journal/one-axis-corner-sets.md) | procedural | live | run `lab.corners.AXES` (nominal + process-only + supply-only + temperature-only, 9 pts) BEFORE `REDUCED`: the 22-point screen moves 2–3 axes per row and cannot tell bias from headroom (the sign-off's process failure hid as "supply" for a week). Also: native-lane `corners.MAX_WORKERS`/`mc.WORKERS` follow `LPF_JOBS` (keep ~8–12 on a shared box); `fit_butter(fixed=…)` pins caps but the fit is local — warm-start it (cold analytic starts walked c2_b → 0); `replica_of(d, m)` integer m = unit-copy sink; check `design.iref` (0.662 vs 1 nA families) before choosing m |
| 2026-08-14 | [min-width-projection-moves-fc](journal/min-width-projection-moves-fc.md) | procedural | live | layout legalization is a sizing change: bumping a sub-minimum width at constant **drawn** W/L still moves the reuse-ladder current (PSP ΔW/ΔL don't scale — measured −2.9 % fc on a ×1.16 bump, −16 % on ×1.85) and finger splits cost ~−0.9 Hz more. `lab.grid.legalize` projects (5 nm grid, PDK minima, ≤10 µm on-grid fingers), `lab.retune.restore_fc` retunes ONLY the bumped device's L (log-log secant, 3 sims), and topology identity is circuitgraph-verified with `match_models=True` (the default comparison misses lv↔hv swaps). Everything downstream simulates the projected geometry — `build_signoff.py` asserts the fixed point |
| 2026-08-14 | [xschem-no-cairo-silent-export](journal/xschem-no-cairo-silent-export.md) | procedural | live | a cairo-less xschem (conda-forge build) exits 0 on `--png`/`--svg` export and writes nothing (or a 1×1 svg) — check `ldd \| grep cairo` before trusting renders. Netlisting (`-n -s -q --no_x`) still works headless, which is all the identity gates need (`lab/xsch.py`, `LPF_XSCHEM`); the svg export DOES carry complete geometry behind a broken 1×1 header — `scripts/render_sch.py` repairs the viewBox/strokes and rasterizes via cairosvg (rsvg drops the text), which is the EDA-server render lane; a stale render beside a re-sized schematic must still be deleted, not kept |
| 2026-08-12 | [port-the-drawing-dont-redraw-it](journal/port-the-drawing-dont-redraw-it.md) | procedural | live | for a PORTED topology the originating drawing transfers almost verbatim: it uses generic `devices/{p,n}mos4.sym` whose pin geometry is **identical** to `sg13g2_pr`'s (D 20,+30 · G −20,0 · S 20,−30 · B 20,0; n mirrors D/S), so every wire endpoint survives a symbol swap — keep every `N …` line. Port = symbol path + **`spiceprefix=X`** (IHP models are subcircuits) + w/l from `signoff/asbuilt/`. Two hard requirements: **scrub the node-denylisted tokens before the file enters git**, and note there is **no testbench to port** (every source schematic is a bare core cell). Generating a fresh drawing gave 0 routed wires against the original's 107 |
| 2026-08-12 | [thd-at-50hz-hides-the-corner](journal/thd-at-50hz-hides-the-corner.md) | semantic | live | S7's single 50 Hz point hides a **23 dB** spread: at 175 mVpp across the passband the reference runs −48.4/−43.96/−29.8 dB at 50/100/200 Hz, the unstacked cell tracks it (−44.6/−40.1/−28.1) and the branch-stacked cell collapses (−42.4/**−20.9**/−21.2). Degradation toward fc is a FAMILY property (the internal node is a bandpass tap and peaks there) but the stacked cell's extra 19 dB is a defect of stacking — one shared ladder current cannot serve both taps. **Profile before choosing a cell; the spec point alone picks the wrong one** |
| 2026-08-12 | [lv-pmos-buys-common-mode](journal/lv-pmos-buys-common-mode.md) | semantic | live | the input CM is a THRESHOLD problem: width buys only ~92 mV/decade and the ~30x needed for vicm 0.5 V turns 47 pF of MIM into non-linear GATE capacitance (THD −42→−30 dB, ph_max 438.9); `sg13_lv_pmos` measures 0.168/0.203 V against hv's 0.457/0.502 at this cell's own currents = **588 mV** of CM headroom, and IRN improves 30.71→28.54 because gm/ID is 32 vs 25. Only the FOLLOWERS may move (lv on gmf_b/bridge re-solves the ladder at 408–570 nA), mirror-gated devices stay hv, lv_nmos stays closed. Stops at vicm 0.65 V — the bridge binds, so **VDD/2 and S8 are in tension** |
| 2026-08-12 | [bias-area-buys-yield-phase-pays](journal/bias-area-buys-yield-phase-pays.md) | semantic | live | mismatch fc spread is a BIAS-device problem (σ(I)/I = σ(Vth)/n·U_T ⇒ a few mV is >10 % of current) but the phase cost of area is a SIGNAL-path one, so grow only the bias devices — gates on quiet rails — and yield goes 12 → 87 % for **3.2° of phase across 81×**. NOT monotone: once nominal phase margin is thin, `ph_max` becomes binding and yield collapses (stacked cell peaks at ×9/84 %, falls to 50 % at ×36); the optimum depends on the cell's own phase margin |
| 2026-08-12 | [phase-ceiling-is-350-not-360](journal/phase-ceiling-is-350-not-360.md) | semantic | live | "4 poles ⇒ 360°" is true of H(s) and false of the certificate: pushed through `ph_max_deg`'s −100 dB floor, a **mathematically ideal** 4-pole Butterworth scores **350.53°** (359.57° unfloored) because |H| falls through the floor at 15.9 × fc while the phase is still ~9° short of its asymptote — so the reference's 346.43° is 4° off ideal, and a score above ~351° (G-120 read 360.0°) is parasitic lag, not extra order |
| 2026-08-12 | [flatness-needs-a-shape-metric](journal/flatness-needs-a-shape-metric.md) | procedural | live | a sag-then-recover passband passes **both** scalar flatness bounds — `peak_db` is one-sided (020B: **0.000 dB** alongside 1.46 dB of droop) and `ripple_db` is a spread (G-135: 0.084 against a 0.2 bound) — so scoring bounds gave the fit no gradient toward flat; fixed by `lab.raw.monotone_db` (soft column `mono_db`, on every scorecard) + `lab.shape.fit_butter` against the Butterworth template: `mono_db` 0.151 → **0.0005** on gb12-175. Flatness is **not free** — it cost G-135 **5.8 dB of THD** (−41.57 → −35.74, pre-fit sizing re-measured to confirm) |
| 2026-08-11 | [nmos-bulk-tie](journal/nmos-bulk-tie.md) | semantic | live | no isolated NMOS in SG13G2 ⇒ an n-type follower's bulk is the shared substrate and its dc gain is exactly 1/n; measured −2.328 dB (n-stage) vs −0.003 dB (p-stage), against an S3 budget of 0.2 dB; n = 1.38 from gm/ID = 28.1 V⁻¹, so no sizing recovers it |
| 2026-08-11 | [all-p-followers](journal/all-p-followers.md) | semantic | live | the structural port decision: **both** biquads take a p-type input follower with an n-type shunt feedback — dc −2.3335 dB (`ref_v0`, alternating) → **−0.0047 dB** (`ref_fit`); keeps the self-referenced gain the family's mismatch yield rests on; cost = CM stacks one \|Vgs\| (~0.46 V) per stage, absorbed by VICM = 0.25 V ⇒ VOCM ≈ 1.25 V at VDD 1.5 V, no CMFB anywhere |
| 2026-08-11 | [phase-certificate-floor](journal/phase-certificate-floor.md) | procedural | live | the S1 certificate can be faked: ±180° steps across a feed-through plateau alias into impossible lags (478°/494° vs true 321.4°/329.8°, carried forward) because the unwrapper corrects only steps > 180°; fixed by a −100 dB magnitude floor + a 150° resolvability guard — reference unchanged at **346.43°** with a worst in-band step of **46.94°** |
| 2026-08-11 | [irn-band-definition](journal/irn-band-definition.md) | procedural | live | S5 is **0.5–200 Hz and input-referred**: reference **50.18 µVrms**; ngspice's own integrated total covers the whole 0.1 Hz–1 kHz sweep and is not the metric (the originating campaign read 1.76 mV for 55.59 µV that way); input-referring at 1 kHz multiplies density by 264× (\|H\| = −48.43 dB), and \|H\| is already 0.925 at the 200 Hz edge |
| 2026-08-11 | [ngspice-write-protocol](journal/ngspice-write-protocol.md) | procedural | live | `write` emits only the CURRENT plot ⇒ `set appendwrite` + one `write` per analysis + `setplot noise1` to reach the spectrum (`noise` leaves the *integrated* plot current); plot numbering is only deterministic when each analysis runs once; an explicit `save` **starves** the noise analysis ("no data saved for Noise analysis") and the rawfile then holds the ac plot twice — S5 reads NaN instead of failing |
| 2026-08-11 | [nodeset-not-ic](journal/nodeset-not-ic.md) | procedural | live | dc hints are `.nodeset` (a hint the solver may leave), never `.ic` (a clamp that lands this circuit in a latched basin scoring as a valid PASS); a hint on a subckt node must be instance-qualified — `v(xdut.vout_1)`, else only "Nodeset on non-existent node" and a silent no-op |
| 2026-08-11 | [mirror-unit-must-match](journal/mirror-unit-must-match.md) | procedural | live | mirror diodes must be the design's **own** unit geometry at m = 1, or every branch is scaled by a W/L ratio: biquad A's internal node rails, its shunt-feedback device switches off, and the ac response still reads as a plausible **mis-tuned** low-pass with a full scorecard; bias current is a multiplicity, never a hand calculation |
| 2026-08-11 | [silent-zero-rawfile](journal/silent-zero-rawfile.md) | procedural | live | ngspice exits **0** after a failed operating point and leaves a zero-filled rawfile that scores as a PASS — the most expensive failure mode in this harness; `lab.ngspice` therefore scans stdout for six fatal strings (incl. `Unknown model type`, which is what a non-OSDI ngspice says about this PDK) and raises `SimError` |

---

## Entry format

**Filename**: `doc/journal/<slug>.md` — **slug only, no date prefix.** The
originating campaign date-prefixed filenames to get recency from a
reverse-lexicographic sort; here `lab/` cites entries by name from code
(`lab/metrics.py` → `phase-certificate-floor.md`, `lab/dut.py` →
`nmos-bulk-tie.md`, `lab/deck.py` → `mirror-unit-must-match.md`,
`nodeset-not-ic.md`, `lab/config.py` → `all-p-followers.md`), so a date in the
path would rot every cross-reference on the first re-dating. The date lives in
the **title line** and in the **date column** here, and retrieval orders on that.

```
# YYYY-MM-DD — <one-line title: the lesson stated as a claim>

KIND: journal entry | type: semantic | status: live
[superseded <date> — see <entry>]        <- only when retired; first 400 chars
[carried forward from the originating campaign — …]   <- when the numbers are not this repo's

<body: tables and numbers first; provenance inline; prose is interpretation only>
```

* Line 3 carries `type:` and `status:` and must stay line 3 — the lint regex
  `type: (semantic|procedural)` and the context pack's supersession filter both
  read only the **first 400 bytes**.
* **Provenance is mandatory**: ledger tags (`ref_fit`, `ref_v0`, `020A_v0`),
  deck hashes (`1ae5466ad00c`), experiment dirs, `file:line`, paper eq/fig refs.
* **Numbers that were not measured in this repo are marked carried forward**,
  every time, and are never presented as a measurement here.
* A procedural entry that proposes a `lab/` or `scripts/` change ends with:
  `Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10.`
  and gets a section in `doc/proposed-lab-fixes.md`.
* Cross-links are **relative markdown links**. No wiki-style links.
* **Hard size cap: 20 KB** per entry, and on this index.

## Supersede, don't delete

Retiring a claim is a **three-place edit** and all three are required:

1. the entry's line 3 → `… | type: <t> | status: superseded`;
2. `[superseded <date> — see <entry/section>]` as the **first body line**
   (inside the first 400 characters, where the retrieval filter looks);
3. this index's **status cell** → `**superseded**`.

**Partial supersession is expected**: retire the claim that died, name it
exactly, and re-home anything that survives (a mechanism whose verdict was
overtaken usually belongs in `doc/design-reference.md`). Supersession also runs
across surfaces — when a measurement corrects a paper's premise, strike the
`pdf/INDEX.md` row through in place and mark it `CORRECTED by <exp> (measured)`.

**If you disprove an entry, marking it is part of the fix — a stale lesson is
worse than none.**

See [`doc/memory/README.md`](memory/README.md) for the memory model this index
is one surface of, and the write-risk ordering that governs who may write what.
