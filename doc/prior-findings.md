# Prior findings — knowledge carried forward from the originating campaign

**KIND: REFERENCE.**

> **Nothing on this page was measured in this repo.** Every number here comes
> from the **originating campaign** — a prior design of the same filter, in a
> different technology, at a **1 V** rail, with a different simulator. No
> technology is identified and none of these numbers may be quoted as a
> property of this repo. This repo's own measurements live in
> `doc/experiment-log.md`, `doc/pdk-notes.md` and `decks/reference/`.

Every row carries a **class**:

| class | meaning | how to use it |
|---|---|---|
| **IND** | technology-independent — algebra, physics of weak inversion, or a property of the transfer function | expected to hold here; use it to *design*, still verify before you *claim* |
| **BOUND** | technology-bound — depends on the device set, the flicker corner, the rail, or the layout | **must be re-measured here before it is trusted**; do not carry the number into any doc as a fact |

The paper-corpus verdicts that came out of this campaign are in
`pdf/INDEX.md`; this file is the circuit and methodology half.

---

## 1. The biquad model and pole algebra — the synthesis recipe

Per differential half, per biquad: input follower **M_i** (gm_i; gate = input,
source = biquad output), shunt-feedback device **M_f** (gm_f; gate = internal
node, drain = biquad output), Miller cap **C1** from internal node to output,
load **C2** at the output.

| finding | carried-forward form / value | class | note for this repo |
|---|---|---|---|
| exact half-circuit solve | `H(s) = 1 / (1 + s·C1/gm_i + s²·C1·C2/(gm_i·gm_f))` | **IND** | sympy-checked there; matches `lab.dut`'s stated pole pair |
| pole pair | `ω0 = √(gm_i·gm_f/(C1·C2))`, `Q = √(gm_i·C2/(gm_f·C1))` | **IND** | `lab.dut` uses exactly this form |
| synthesis at unity forward path | `C1 = gm_i/(ω0·Q)`, `C2 = gm_f·Q/ω0` | **IND** | reproduced the originating caps to 3 digits |
| **a differential cap counts DOUBLE in the half-circuit** | `C2_single = 2 × C2_drawn` | **IND** | the single easiest sizing error to make; every formula above uses the single-ended value |
| model fidelity | validated to ~1 dB against the reference simulator, 10 Hz–2.5 kHz | **IND** (as a method) | re-validate the band on this PDK before trusting hand-sizing |
| silicon cap cost of one biquad | `2·C1 + C2_drawn` (C1 is drawn once per side, C2 once differentially) | **IND** | ⇒ the **high-Q pole pair belongs on the biquad with the larger gm_i** |
| cap/Q re-allocation, no circuit change | measured **−9.0…−9.2 % capacitance and −21.2…−22.1 % IRN at identical power** | **IND** in mechanism, **BOUND** in magnitude | **run it as a control in every experiment** — it is a free move, never a result to claim |
| pole placement inside the box | with devices and bias fixed, `\|H\|@1 kHz ≤ −48 dB` pins the shape to 4th-order Butterworth; re-placing poles inside the box is worth **< 1 %** more | **IND** | this repo's reference measures −48.43 dB against a −48.16 dB Butterworth arithmetic — the same knife-edge |
| exact closed forms | `Z_out = s/(ω0·Q·gm_f)`, `A_int = 1/gm_i`; reproduced every device to **+0.46 %** | **IND** | useful for hand-checking a noise breakdown |

---

## 2. Where the noise actually was (all BOUND — re-measure first)

This is the section most likely to mislead. The originating campaign's noise
split is a property of *its* devices, *its* flicker corner and *its* bias
sizing. **Queue item 1 in `doc/experiment-log.md` exists to replace this whole
table with measurements from this PDK.**

| finding | carried-forward value | class |
|---|---|---|
| baseline IRN, 0.5–200 Hz | **55.59 µVrms** (this repo's reference measures 49.98 µV — a different circuit in a different process; the two are **not** comparable) | **BOUND** |
| noise power split | 8 bias current sources **43.68 µV = 61.7 %**; input followers 29.32 µV = 27.8 %; shunt feedback 17.98 µV = 10.5 %; testbench bias/reference network **0.00 µV = 0.0 %** | **BOUND** |
| thermal / flicker split | 54.09 / 12.85 µV = **94.7 % / 5.3 %** | **BOUND** |
| ⇒ chopping is pre-refuted | a *perfect* chopper removes only the flicker term: 55.59 → 54.09 µV = **−2.7 %** | **IND** given the split; the split itself is **BOUND** — if flicker is a larger share here, re-open |
| ideal-bias ceiling | replacing the eight in-DUT bias sources with ideal ones measures **33.92 µV** | **BOUND** — but the *method* (an ideal-source ablation as a ceiling) is **IND** and worth copying |
| node sensitivity | internal-node sources 9.6 % and 10.7 % each; output-node sources only 1.7 % | **BOUND** |
| **I–C homothety law** | scale every device multiplier **and** every capacitor by k: fc, Q, dc gain, ph_max and THD are **invariant**, power ∝ k, and **IRN = IRN₀/√k exactly** (predicted 39.31/32.09/22.69 for k = 2/3/6, measured 39.30/32.08/22.68) | **IND** — this is the technique-free control curve; quote every technique against it |
| shrinking C by shrinking gm | costs exactly `√(C₀/C)`: gm/2 & C/2 measured **78.68 µV (+41.5 %)** vs a √2 prediction of 78.62 | **IND** |
| **a MOS cannot degenerate another MOS's noise in weak inversion** | any MOS carrying the full branch current contributes ≥ 2qI; a subthreshold device in triode carries `S_id = 2qI·coth(V_DS/2V_T) ≥ 2qI`. Only a genuine resistor `R > 2·V_T/I` removes it. Self-cascode composite measured **−4.6 %** vs **−21 %** for an ideal resistor | **IND** |
| ideal-resistor degeneration | **34.54 µV at 7.9 nW and −10 % capacitance**; resistors 26.8–63.9 MΩ | **BOUND** in value, **IND** in mechanism |
| device noise magnitude | device noise is **4γqI**, not 2qI (2qI is wrong by 1.7–2×) | **IND** |
| noise is I_B-independent at fixed C | `noise ∝ kT/C2 · S(Q)` in weak inversion; at fixed **fc** it becomes `IRN ∝ 1/√I` (the homothety) | **IND** |

---

## 3. Falsified by measurement — do not re-run

These were closed with evidence. Re-running them costs simulations and buys
nothing **unless** the "re-open" column says otherwise.

| mechanism | why it died | class | re-open here? |
|---|---|---|---|
| **chopping / auto-zeroing** | best case −2.7 % (flicker was only 5.3 % of noise power) | **BOUND** | **Yes, conditionally** — re-measure the flicker share first (queue 1). If flicker is again ~5 %, it stays dead. |
| **input-side current cancellation at any useful strength** | the forward-path LHP zero must clear ~13 kHz to keep the order certificate ⇒ k ≳ 0.98 ⇒ nothing left to cancel. Measured placements: gate-cross **−8.594 dB** dc gain, source-cross **+12.253 dB**, drain-cross −0.074 dB (baseline) but fc 246.4 → 59.2 Hz at N = 3 | **IND** | No. And the general rule generalises: **any topology that adds a forward-path zero inherits this** — score `ph_max`, not just magnitude. |
| feedback-side current cancellation | zero-free, but a pure capacitance-for-noise exchange: **−2.4 % C per +3.2 % IRN** | **IND** | No — it is a trade, not a win. |
| **self-cascode composite as a noise lever** | −4.6 % vs −21 % for an ideal resistor; the triode device itself became the top contributor | **IND** | No, as a *noise* lever. Its **HD3** claim was never tested and may still stand. |
| **moderate-inversion re-biasing** | lowers gm at fixed current ⇒ raises IRN. It is an **area** lever that *worsens* noise | **IND** | No. |
| **bulk-driven inputs** | same mechanism — lower gm at fixed current | **IND** | No. |
| **adding a CMFB** | the follower-defined common mode is the better option. A 5T CMFB clamp is a three-axis servo: σ(dc) **1.1–1.4 dB**, THD **−35.6 dB FAIL**; on the gate-driven family it cost **−13.4 dB THD** and oscillated rail-to-rail | **IND** in mechanism, **BOUND** in numbers | No. **Do not add a CMFB to this topology.** |
| the M1-noise-floor claim from the SSF literature | the canonical "output noise collapses to M1 alone" result assumes **ideal current-source loads**; with real loads the input followers were only 27.8 % of noise power | **IND** (the assumption is stated in the source) | No — but re-derive the split here (queue 1). |
| the self-compensated-gain cascade (n-stage K = 1/n × p-stage K = n) | shunt feedback pins **each** stage at 0 dB (−0.0487 / −0.0250 dB measured), so there is no gain-n stage and downstream noise divides by 1.000, not n² | **IND** as stated *for a bulk-tied-to-source follower* | **RE-OPENED HERE** — see §8. |

---

## 4. The follower-yield theorem — the single most important thing preserved

**Claim (closed form, IND).** In `H(s) = 1/(1 + s·C1/gm_i + s²·C1·C2/(gm_i·gm_f))`
the threshold voltage **V_T appears in no coefficient**. `∂H(0)/∂V_T` enters
only through `g_ds` ratios — second order. A V_T draw on M_i or M_f re-biases
the ladder (an **offset**), it does not move the **gain**.

Contrast with a gm-ratio cell, where the passband gain is a ratio between two
*different* devices: there `∂(ln H0)/∂V_T = gm/I` directly, giving
`σ(dc) ≈ 8.686·(σ(ΔV_T)/(n·U_T))/√k ≈ 0.3–0.5 dB`.

| quantity | carried-forward value | class |
|---|---|---|
| σ(dc) of the follower family | **0.0002 … 0.0038 dB** | **BOUND** in magnitude, **IND** in mechanism |
| σ(dc) of a gm-ratio topology | **0.370 dB** — against an S3 box of ±0.2 dB, i.e. **structurally infeasible** | **BOUND** in magnitude, **IND** in mechanism |
| gain-robustness yield, one experiment | follower **75 %** vs gate-driven **6 %** | **BOUND** |
| honest limit of the campaign | the follower reference won mismatch yield **73–75 % vs 31–33 %** against the lowest-noise candidates at equal power | **BOUND** |

**Why this constrains every candidate here.** This repo's structural port decision — both
input followers p-type (`doc/experiment-log.md` 020) — was taken *specifically*
to keep the gain self-referenced through one device rather than converting it
into a device ratio. Any candidate that replaces a follower with a gm-ratio
stage must carry a mismatch measurement, not an argument.

Also do not change, for the same reason: bulk = source on every **p-channel**
signal device (free here); the pole algebra of §1; and the absence of a CMFB.

---

## 5. Mismatch / yield methodology (the recipe, and the guards that matter)

The recipe is **IND** — it is a measurement protocol. Its per-step
implementation is **BOUND** and has to be rebuilt against what SG13G2 actually
ships.

**The definition of "yield" used there — the ALL-4 box**, i.e. the four
statistics-fragile specs scored per sample:
`|dc_db| ≤ 0.20` · `fc within 250 ± 2 %` · `peak_db ≤ 0.20` · `a1000 ≤ −48.0`.
32 samples from a **seeded** stream, **identical seeds for every design**, with
an untouched reference row as the **first** row of every batch.

Carried-forward baseline (BOUND, illustrative of the spread only):

| design | ALL-4 | σ(dc) | σ(fc) |
|---|---|---|---|
| follower reference | **59 %** | 0.0002 dB | 4.09 Hz |
| a gm-ratio candidate | 28 % | 0.0038 dB | 1.78 Hz |
| best re-centred candidates | 88–91 % | 0.0007–0.0010 dB | 3.03–3.49 Hz |

**Five mandatory guards — all IND, all inherited:**

1. **Area/Pelgrom correction.** Mismatch σ is `f(W, L)` with the textbook
   −0.500 exponent, and the multiplier exponent measured **0.000** — i.e. a
   device netlisted `(W, L, m)` is modelled with the mismatch of area `W·L`
   while its real area is `m·W·L`. Either draw everything at `m = 1` (fold `m`
   into W) or unitize before scoring. This repo's reference has four devices at
   `m = 2` and therefore **needs the correction**.
2. **Fail-closed.** Assert that the number of injected mismatch sources equals
   the number of DUT devices. A silently-inert flag is the default failure.
3. **Negative control.** With σ = 0 the lane must reproduce nominal
   **bit-for-bit**.
4. **Liveness.** If all N samples are bit-identical, the lane is dead and every
   yield number it prints is a lie. In the originating campaign the mismatch
   lane **was dead for the whole campaign** — the statistics section was never
   included, samples were bit-identical, and **no design was ever statistically
   scored**. Prove liveness before quoting a single yield percentage.
5. **Never quote an IRN from the mismatch lane.** The statistical device models
   there gave a *wrong* noise analysis (a 55.59 → 32.59 µV shift). Per-sample
   scorecards are **AC only**.

If SG13G2 ships a statistical/MC section, use it and prove it live (guard 4).
Otherwise the fallback is V_T injection — a series gate source per DUT device,
`σ_Vt = A_VT/√(W·L·m)` with A_VT taken from the PDK separately for n and p —
driven from a seeded loop so the stream is reproducible.

---

## 6. The constraint list (the six facts that killed the naive ideas)

| # | constraint | class | status here |
|---|---|---|---|
| 1 | **Weak inversion pins node conductance.** `gms = gm + gmb = I_D/V_T` **exactly**, so the *sum* of source conductances on a node is set by the branch current. No cross-coupling trick can reduce a driving-point conductance — only a forward-path *difference*. | **IND** | holds; it is why the big Miller cap cannot be shrunk by a parallel device |
| 2 | **DC gain is structural.** Shunt feedback pins `H(0) = 1`; any technique that touches the input device's gate path scales dc gain and disqualifies itself. | **IND** | holds — **with one process-specific exception**: a bulk-at-rail follower divides by `n` regardless (see §8) |
| 3 | **Silicon cap cost = `2·C1 + C2_drawn` per biquad** ⇒ the high-Q pole pair belongs on the larger-`gm_i` biquad; re-allocation is a free control that must be subtracted before crediting any technique. | **IND** | holds |
| 4 | **Judge passband flatness two-sided only up to ~0.6·fc; do not police ripple *through* the corner.** A ±ripple rule at 245 Hz plus −3 dB at 247 Hz is infeasible by construction and made a correct design look impossible. | **IND** | ported into `doc/environment.md` §5 |
| 5 | **Linearity margin is slew-bounded.** THD collapses above ~0.35·fc as the nano-amp followers stop driving the caps at full swing × frequency. Any technique that shrinks bias current or grows caps eats the margin from above. **Re-run THD whenever swing, caps or bias change.** | **IND** in mechanism, **BOUND** in the knee frequency | re-measure — this repo has not measured S7 at all yet |
| 6 | **Power budget is filter-core only**, measured with a series 0 V probe in the core's supply pin; the bias reference is excluded and report-only. Noise is I_B-independent at fixed C, so **spend added current on slew/linearity or on gm_i, not blindly** — at fixed fc the payoff is only `1/√I`. | **IND** | ported: `lab.config.CORE_PROBE = vflt`, and S6 here is stated in **watts** (< 50 nW at 1.5 V = 33.3 nA) |

---

## 7. What won there (context for "what good looks like")

**All BOUND.** Quoted only so nobody re-derives the *shape* of the result; none
of these are targets here.

| result | headline | why it is not a target here |
|---|---|---|
| cap/Q re-allocation only, no circuit change | −9.0 % C, **−22.1 % IRN**, order certificate intact | the mechanism is **IND** and is queue item 3; the numbers are that circuit's |
| gate-driven current-reuse biquad | **−28 % IRN / −63 % C** | won on noise, **lost on mismatch yield** (§4) and was blocked by rail headroom (§8) |
| the same, with MOS capacitors | 14.89 µV at 49.7 nW | needs a MOS-cap C–V characterisation this repo does not have |
| the final merged design | 25.04 µV at 6.09 nW, 88 % ALL-4 yield | delivered against a different acceptance box |

The honest summary of that campaign: **the lowest-noise topologies lost the
yield argument**, and the root cause was inversion level against a 1 V rail.

---

## 8. Re-opened here — and why

Two independent reasons the closed list does not transfer whole.

### 8.1 The rail is 1.5 V, not 1 V

Everything closed with "at 1 V" as the stated blocker is **re-openable**, with
its evidence attached but its verdict suspended:

| closed there because… | re-open here |
|---|---|
| "blocked by 104 mV of V_DS on a branch spending exactly 1.0000 V" (a second current reuse across the biquads) | **yes** — 500 mV of extra rail is exactly this blocker's currency |
| "quad V_GS eats tail V_DS, 77 → 0.4 mV at ×6" | **yes** |
| "not combinable with the branch-stacked bias at 1 V" | **yes** |
| "the gate-driven yield route is CLOSED at 1 V" | **yes** — but it must be re-argued on §4's terms, not just on headroom |

Note the direction of the trade: at 1.5 V the linearity spec also gets easier
(175 mVpp is 11.7 % of the rail instead of 17.5 %), while the power box —
stated in **watts** — gets *tighter* in current terms (33.3 nA, not 50 nA).

### 8.2 This process cannot tie an n-channel bulk to its source

The originating campaign could put every device in its own well, so the entire
**bulk-effect family was moot there** — bulk-effect self-neutralisation was
strictly worse than the bulk-tie it replaced, and the self-compensated-gain
cascade had no gain-`n` stage to exploit.

Here the constraint is the opposite: an n-channel bulk **must** sit at the
rail, so a bulk-at-rail n-follower divides by `n` whether anyone wants it or
not (measured: **−2.328 dB**, `doc/experiment-log.md` 020). That makes the
bulk-effect family **directly relevant rather than moot**:

- `bulk-neutral` and `selfcomp-gain` in `pdf/INDEX.md` are re-shelved as
  **live**, not ruled out.
- The exact-cancellation argument still needs checking against **this** PDK's
  numbers: `n_n = 1.38` vs `n_p = 1.54` for the hv pair (`doc/pdk-notes.md`
  §2.1) — **11 % apart**, so an n/p cascade would leave a residual, not an
  exact 0 dB.
- The reference baseline sidesteps the whole family by making both followers
  p-type. Any candidate that reintroduces an n-type follower is taking on
  `1/n` and owes a measurement of how it gets the dB back.

---

## 9. Instrument defects found there — build the fixes in from day 1

**IND** (they are harness defects, not device physics). Listed so this repo
does not re-earn them.

| defect | consequence | what this repo already does |
|---|---|---|
| the mismatch lane was **dead** for the whole campaign | no design was ever statistically scored | §5 guard 4 — prove liveness before the first yield number |
| an unscoped instance-name regex silently mutated a **testbench** device | bit three independent sessions; signature was a small supply-current shift and a collapsing HD2 | this repo **builds** decks from a `Design` and never text-edits them (`lab.deck`) |
| the order certificate could be **faked** — ±180° phase steps into the parasitic-feedthrough floor aliased into 478°/494° lags | a design with the wrong order scored as a pass | `lab.metrics.PH_FLOOR_DB = −100.0` plus the `PH_STEP_GUARD_DEG = 150.0` resolvability guard |
| S7 measured **HD3 only** | a ~9.7 dB blind spot vs total harmonic distortion | measure h2–h10, and re-measure **HD2** here rather than inheriting "THD ≈ HD3" |
| the reference simulator's exit code was trusted | — | `lab.ngspice._check_convergence` scans stdout for fatal strings (`doc/environment.md` §4.7) |
