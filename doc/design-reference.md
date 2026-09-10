# Design reference — the circuit knowledge

**KIND: REFERENCE.** What the DUT *is*, the algebra that predicts it, and the
facts that kill naive ideas. Read this before touching the DUT or modelling it.
The spec box lives in [target-spec.md](target-spec.md); the measurement contract
in [benches.md](benches.md).

**Provenance discipline used throughout.** A number is either
**MEASURED HERE** (this repo, this PDK, in `runs/ledger.ndjson` or
`doc/pdk-notes.md`), **DERIVED** (arithmetic on measured inputs — stated as
such), or **CARRIED FORWARD** (a result of the originating campaign, on another
technology at another supply, kept because the *mechanism* transfers). Carried-
forward numbers are hypotheses to re-test here, never claims about this design.

---

## 1. What it is

A fully differential **4th-order low-pass filter: two cascaded super-source-
follower (SSF) biquads**, no CMFB anywhere — the followers themselves define the
common mode. Every transistor is in weak inversion at ≈ 1 nA per branch.

```
vinp/vinn ──▶ [ biquad A ] ──▶ vout_1/vout_2 ──▶ [ biquad B ] ──▶ voutp/voutn
                 net2/net3                          net4/net1
                 (A's internal nodes, P/N)          (B's internal nodes, P/N)
```

One SSF biquad is: an **input follower** (gate = the biquad input, source = the
biquad output), a **shunt-feedback transconductor gm_f** (gate = the internal
node, drain = the biquad output), **one bias current per node**, and **two
capacitors** — `c1` from the internal node to that half's output, `c2`
differential across the biquad's two outputs.

**BOTH biquads here use a p-type input follower with an n-type shunt-feedback
transconductor.** That is this port's one structural departure from the
originating design, and it is forced by the process — see §5.

Code: `lab.dut.build_reference` (topology `"reference"`); frozen netlist
`decks/reference/lpf_core.sp`; build sheet `decks/reference/build-sheet.md`.

---

## 2. Device / net / role table — the reference baseline

16 transistors + 6 capacitors. Roles are the keys of `lab.dut.Design.devs`;
instance names match `lab.dut.build_reference`. `NCH = sg13_hv_nmos`,
`PCH = sg13_hv_pmos` (`lab.dut`). Terminal order as emitted: **d g s b**.

### Biquad A — p-input follower, n-type shunt feedback

| inst | role | type | d | g | s | b | W/L (µm) | m | function |
|---|---|---|---|---|---|---|---|---|---|
| `xm2` | `in_a` | PCH | `net2` | `vinp` | `vout_1` | `vout_1` | 4 / 4 | 1 | **input follower**, P half. Bulk → source (own n-well) |
| `xm5` | `in_a` | PCH | `net3` | `vinn` | `vout_2` | `vout_2` | 4 / 4 | 1 | input follower, N half |
| `xm4` | `gmf_a` | NCH | `vout_1` | `net2` | `0` | `0` | 4 / 4 | 1 | **shunt-feedback gm_f**, P half |
| `xm8` | `gmf_a` | NCH | `vout_2` | `net3` | `0` | `0` | 4 / 4 | 1 | shunt-feedback gm_f, N half |
| `xm3` | `bias_a_int` | NCH | `net2` | `vbn` | `0` | `0` | 5 / 8 | 1 | internal-node current sink, P half |
| `xm13` | `bias_a_int` | NCH | `net3` | `vbn` | `0` | `0` | 5 / 8 | 1 | internal-node current sink, N half |
| `xm9` | `bias_a_out` | PCH | `vout_1` | `vbp` | `vdd` | `vdd` | 5 / 12 | **2** | output-node current source, P half |
| `xm10` | `bias_a_out` | PCH | `vout_2` | `vbp` | `vdd` | `vdd` | 5 / 12 | **2** | output-node current source, N half |

### Biquad B — identical structure, driven by A

| inst | role | type | d | g | s | b | W/L (µm) | m | function |
|---|---|---|---|---|---|---|---|---|---|
| `xm0` | `in_b` | PCH | `net4` | `vout_1` | `voutp` | `voutp` | 4 / 4 | 1 | **input follower**, P half |
| `xm1` | `in_b` | PCH | `net1` | `vout_2` | `voutn` | `voutn` | 4 / 4 | 1 | input follower, N half |
| `xm6` | `gmf_b` | NCH | `voutp` | `net4` | `0` | `0` | 4 / 4 | 1 | **shunt-feedback gm_f**, P half |
| `xm7` | `gmf_b` | NCH | `voutn` | `net1` | `0` | `0` | 4 / 4 | 1 | shunt-feedback gm_f, N half |
| `xm11` | `bias_b_int` | NCH | `net4` | `vbn` | `0` | `0` | 5 / 8 | 1 | internal-node current sink, P half |
| `xm12` | `bias_b_int` | NCH | `net1` | `vbn` | `0` | `0` | 5 / 8 | 1 | internal-node current sink, N half |
| `xm14` | `bias_b_out` | PCH | `voutp` | `vbp` | `vdd` | `vdd` | 5 / 12 | **2** | output-node current source, P half |
| `xm15` | `bias_b_out` | PCH | `voutn` | `vbp` | `vdd` | `vdd` | 5 / 12 | **2** | output-node current source, N half |

`lab.dut.NROLES = {bias_a_int, gmf_a, bias_b_int, gmf_b}` — exactly the
n-channel roles. **All four have their source at `0`**, so the absence of an
isolated NMOS costs them nothing; the body-effect problem is confined to the
followers (§5).

### Capacitors (and the placement rule)

| inst | node + | node − | value | role |
|---|---|---|---|---|
| `c13` | `net2` | `vout_1` | **29.468 pF** | `c1_a`, P half — drawn **twice** |
| `c17` | `net3` | `vout_2` | 29.468 pF | `c1_a`, N half |
| `c19` | `vout_2` | `vout_1` | **6.221 pF** | `c2_a` — **one differential cap**, drawn once |
| `c1` | `voutp` | `net4` | **11.453 pF** | `c1_b`, P half |
| `c10` | `voutn` | `net1` | 11.453 pF | `c1_b`, N half |
| `c12` | `voutn` | `voutp` | **9.946 pF** | `c2_b` — differential, drawn once |

Total drawn = 2(29.468) + 6.221 + 2(11.453) + 9.946 = **98.01 pF**
(`Design.total_cap`), which is what `c_total_pf` reports.

**Placement rule — the term every sizing formula in §3 depends on:**

* `c1` bridges the biquad's **internal node → that same half's output**, i.e. it
  is the gate–drain (Miller) capacitance of the shunt-feedback device. **One per
  half ⇒ drawn twice.**
* `c2` is **one differential capacitor between the biquad's two outputs**. Drawn
  once.
* **Algebraic consequence:** the *single-ended* load each half sees is
  `c2_single = 2 × c2_drawn`. Every formula in §3 uses `c2_single`.
  Reference: `c2_a_single` = 12.441 pF, `c2_b_single` = 19.891 pF.

### Bias, and why the mirror unit is not free to choose

The testbench drives `vbn`/`vbp` from **one ideal reference current into a real
n/p mirror** (`lab.deck._bias`). Every bias device in the DUT is an **integer
multiple of that unit**: per side each biquad sinks 1 unit at its internal node
and sources 2 units at its output ⇒ 4 units per side, **8 units total**.

MEASURED HERE: core current **8.0435 nA** ⇒ unit = **1.0054 nA/branch**;
core power **12.07 nW** at 1.5 V.

The mirror diodes are built from the **design's own** `bias_*_int` /
`bias_*_out` geometry at `m = 1`. An arbitrary diode geometry silently scales
every branch current by a W/L ratio: the internal node rails, the shunt-feedback
device switches off, and the ac response still looks like a plausible (if
mis-tuned) low-pass. See `doc/journal/mirror-unit-must-match.md`.

---

## 3. The validated biquad model and the pole algebra

Small-signal, one half, ideal bias sources, bulk tied to the follower's source
(the case that holds for every follower in this reference). `v_x` = internal
node, `v_o` = biquad output, `gm_i` = input-follower gm, `gm_f` = shunt-feedback
gm, `C1` = the internal→output cap, `C2` = the **single-ended** output load
(= 2 × the drawn differential cap).

KCL at the internal node (its bias source is ideal, so only `C1` and the
follower's drain current terminate there):

```
gm_i (v_o − v_in) = s·C1 (v_x − v_o)                                   (1)
```

KCL at the output node (follower source current in, gm_f drain current and the
load out) reduces, after substituting (1), to

```
0 = gm_f·v_x + s·C2·v_o        ⇒   v_x = − s·C2·v_o / gm_f             (2)
```

Substituting (2) into (1):

```
                gm_i                                  1
H(s) = ────────────────────────────────  =  ───────────────────────────────
        gm_i + s·C1 + s²·C1·C2/gm_f          1 + s·C1/gm_i + s²·C1·C2/(gm_i·gm_f)
```

so

```
w0² = gm_i·gm_f / (C1·C2)                 Q = gm_i / (w0·C1) = sqrt( gm_i·C2 / (gm_f·C1) )
```

and, inverted, the **synthesis recipe**:

```
C1 = gm_i / (w0·Q)              C2_single = gm_f·Q / w0        (drawn diff = C2_single/2)
silicon cost of one biquad = 2·C1 + C2_drawn = 2·C1 + C2_single/2
```

Three things fall straight out and are worth stating:

* **H(0) = 1 exactly.** At dc the internal node is quiet (2) and `gm_i` cancels
  in (1)⇒H. The passband gain is *structural*, not a sizing outcome — which is
  why S3 is a topology constraint and not a knob. **This is the step the body
  effect breaks (§5).**
* **Q is a cap ratio at fixed devices.** `Q² = (gm_i/gm_f)·(C2/C1)`, so the pole
  Q is tuned by moving capacitance between `C1` and `C2` at constant power.
* **`C1` is drawn twice and scales as 1/Q; `C2_drawn` is drawn once and scales
  as Q.** That asymmetry is the whole basis of the re-allocation control (§4.3).

> **Docstring discrepancy — flagged, not fixed.** `lab/dut.py`'s module
> docstring writes `Q = sqrt(gm_i*gm_f*C1/C2)/gm_i`, which is the **reciprocal**
> of the correct expression derived above. Only the docstring is affected — no
> code path computes Q — but it will mislead anyone sizing by hand. The
> numerical check in §4.1 confirms the form used here. Fixing `lab/` is a
> procedural write: propose the diff, do not self-apply it.

### Cancellation variant (kept for continuity)

If a fraction of the follower's forward current is cancelled with strength
`k = (N−1)/(N+1)` (k = 1 ⇒ no cancellation), the model generalises to

```
H(s) = gm_i·[k·gm_f + s·C1(1−k)] / [k·gm_i·gm_f + s·C1(gm_f + (1−k)·gm_i) + s²·C1·C2]
w0   = sqrt( k·gm_i·gm_f / (C1·C2) )
LHP zero, only when k < 1:   f_z = k·gm_f / (2π·(1−k)·C1)
```

CARRIED FORWARD: that forward-path zero is what caps the achievable phase lag
near 293° and fails S1 while the magnitude response still looks clean. Any
technique that introduces a forward-path zero inherits this — **score
`ph_max_deg`, not just `a1000_db`.**

---

## 4. Where the reference baseline actually sits

### 4.1 Pole map (DERIVED — the model closing on the measurement)

Both biquads use the **same devices at the same current**, so `gm_i` and `gm_f`
are common to both. Using the measured weak-inversion gm/ID limits
(`doc/pdk-notes.md`: hv pmos **25.1 V⁻¹**, hv nmos **28.1 V⁻¹**) at the measured
unit current of 1.0054 nA:

```
gm_i ≈ 25.2 nS   (p-type follower)          gm_f ≈ 28.3 nS   (n-type gm_f)
```

These are **upper bounds** — gm/ID at the limit — and are *not* an op-point
extraction. Read the definitive values from a `lab.deck.op_only` run before
quoting them anywhere else.

| biquad | C1 (pF) | C2_drawn (pF) | C2_single (pF) | f0 (Hz) | Q | cost 2·C1+C2_drawn (pF) |
|---|---|---|---|---|---|---|
| A | 29.468 | 6.221 | 12.441 | **221.9** | **0.614** | 65.16 |
| B | 11.453 | 9.946 | 19.891 | **281.6** | **1.246** | 32.85 |
| | | | | **√(f0A·f0B) = 250.0** | | **98.01** |

The geometric mean of the two pole frequencies lands on **250.0 Hz** against a
**measured fc of 250.00 Hz** — the model closes on the measurement using nothing
but the drawn capacitors and the measured gm/ID limit. The pair is a *staggered*
Butterworth-like allocation (reference Butterworth: f0 = 250 Hz both,
Q = 0.5412 / **1.3066**, `lab.shape.BUTTER_Q`), slightly sharper than
maximally flat: measured `a1000_db` = **−48.43 dB** against the Butterworth
arithmetic of **−48.16 dB** (`lab.shape.A1000_BUTTER_DB`). The **high-Q pole
pair sits on biquad B**, the second stage.

### 4.2 DC operating-point map

| node | value | provenance |
|---|---|---|
| VDD | 1.500 V | `lab.config.VDD` |
| input CM (`vcm`) | **0.250 V** | `lab.config.VICM` |
| output CM (`voutp`/`voutn`) | **≈ 1.25 V** | `lab.config.VOCM` (the dc hint) |
| intermediate CM (`vout_1`/`vout_2`) | ≈ 0.75 V — DERIVED: one \|Vgs\| above the input CM | — |
| \|Vgs\| per follower stage | **≈ 0.50 V** — DERIVED from the 0.25 → 1.25 V ladder over two stages | — |
| PDK datum: hv pmos at 1 nA, W = 10 µm, L = 4 µm | \|Vgs\| = **0.46 V** | MEASURED, `doc/pdk-notes.md` |
| unit branch current | **1.0054 nA** | DERIVED from the measured 8.0435 nA core / 8 units |
| core current / power | **8.043 nA / 12.07 nW** | MEASURED |
| whole-testbench supply | **10.049 nA** (2.006 nA of it is the reference + mirror, excluded from S6) | MEASURED |

**Every follower is p-type, so the common mode climbs one \|Vgs\| per stage
instead of cancelling.** That is why the input CM is placed *low* (0.25 V) — so
the output lands mid-supply with headroom on both rails. It is a real cost of
the structural port and it constrains every candidate: a candidate that adds a
third level shift, or that raises \|Vgs\| (narrower devices, higher current
density), spends output headroom.

Per-node op-point voltages and per-device `gm`, `gm/ID`, `Vds`, `Vdsat` are
**not recorded in this doc**. Get them from `lab.deck.op_only` with
device-parameter probes — the addressing is `@n.<inst>.n<model>[gm]`, e.g.
`@n.xdut.xm2.nsg13_hv_pmos[gm]`, and the parameter must appear in a `save`
**before** a sweep or it reads as a constant.

**There is no `region` code in ngspice.** The weak-inversion certificate is
`gm/ID` near the measured limit (25–28 V⁻¹ for these devices) plus a check that
every bias device keeps `Vds` above roughly `4·kT/q` (≈ 103 mV at 27 °C). A
device can sit in weak inversion and still be starved of `Vds`; `gm/ID` alone
will not catch it, `gds` will.

### 4.3 The re-allocation control is degenerate in this reference (DERIVED)

The general rule — CARRIED FORWARD and still true — is: because `C1 ∝ 1/Q` is
drawn twice while `C2_drawn ∝ Q` is drawn once and halved, **the high-Q pole
pair belongs on the biquad with the larger `gm_i`**, and a pure swap of the
`(f0, Q)` pairs between biquads is a *free* control that must be subtracted
before crediting any technique.

**In this reference, both biquads are built from identical devices at identical
current, so `gm_i` and `gm_f` are equal across A and B.** Swapping the `(f0, Q)`
pairs therefore swaps the two cap sets wholesale, and the total capacitance is
**exactly invariant** — 65.16 + 32.85 either way. The area half of the free win
does not exist here.

That does **not** retire the control. Noise referral is not symmetric (the first
stage's noise is referred with unity gain; the second's is shaped by the first
stage's in-band response), so IRN may still move under the swap. **Run the
re-allocation control anyway, and report it as an IRN result with a
zero-capacitance delta.**

---

## 5. The structural port decision: no isolated NMOS

**This is a measured finding of this port, not a carried-forward assumption.**

SG13G2 has **no deep-n-well / isolated NMOS**. An n-channel device's bulk is the
shared p-substrate, so it cannot follow its source. PMOS bulks are free — each
sits in its own n-well.

### The algebra

In weak inversion, with `n` the subthreshold slope factor and `V_T = kT/q`:

```
gm  = I_D / (n·V_T)        gmb = (n−1)·gm        gms = gm + gmb = I_D / V_T   (exactly)
```

Redo the §3 derivation for an n-input follower whose **bulk is at the rail**:
the follower's drain current gains a body term `−gmb·v_o`, so (1) becomes
`gm(v_in − v_o) − gmb·v_o = s·C1(v_x − v_o)`. Equation (2) is unchanged, so at
s = 0 the internal node is still quiet, `v_x = 0`, and

```
H(0) = gm / (gm + gmb) = 1/n            — exactly, and the SSF loop recovers NONE of it
```

With bulk tied to the source, `gmb = 0` and `H(0) = 1` exactly. The difference is
not a sizing question: `1/n` is set by the process.

### The measurement (MEASURED HERE)

Stage-by-stage dc gain, measured on the **alternating n/p structure the
originating design used**, ported to this PDK:

| stage | follower | bulk | dc gain |
|---|---|---|---|
| A | n-input | at the substrate (forced) | **−2.328 dB** |
| B | p-input | at its own source | **−0.003 dB** |

The n-stage alone overruns the S3 budget (\|dc\| ≤ 0.2 dB) by more than **10×**,
and **no re-sizing recovers it**. For calibration: the measured hv-nmos
weak-inversion gm/ID limit of 28.1 V⁻¹ implies **n = 1.38**, i.e. a predicted
1/n = **−2.80 dB**; the −2.328 dB measured corresponds to an effective n = 1.31
at that stage's operating point. Either value is an order of magnitude outside
the box.

### The decision, and what it buys and costs

**Make both stages p-type.** This restores exact unity gain and, with it, the
**self-referenced gain** the candidate family's mismatch yield rests on: H(0) = 1
because `gm_i` cancels against itself, not because two device *ratios* happen to
match, so S3 does not degrade with mismatch the way a ratio-matched cancellation
would.

Costs, both real and both to be respected by every candidate:

1. **The common mode climbs one \|Vgs\| per stage** instead of cancelling. Paid
   for by placing the input CM low (0.25 V) so the output lands at ≈ 1.25 V.
2. **The n/p complementarity is gone**, and with it any technique that depends
   on it. `selfcomp-gain`'s whole mechanism (an n-input stage with K = 1/n
   cascaded with a p-input stage with K = n) is unavailable here **on structural
   grounds** — there is no gain-n stage to pair with, because shunt feedback
   pins every stage at 0 dB. Measured n values here for the record:
   **n = 1.38 (hv nmos), 1.54 (hv pmos)** (`doc/pdk-notes.md`) — **11 % apart**,
   so the cancellation could not have been exact even where it is available.
   `pdf/INDEX.md` re-opens `selfcomp-gain` and `bulk-neutral` on exactly this
   ground: a bulk-at-rail n-follower divides by 1/n whether anyone wants it or
   not, so the complementary n/p cascade is a live 0 dB *candidate* — it is just
   not what this reference does, and it carries an 11 % residual against a
   ±0.2 dB box.

See `doc/journal/all-p-followers.md` and `doc/journal/nmos-bulk-tie.md`.

---

## 6. The constraints every candidate must respect

**C0 — No isolated NMOS (NEW, measured here).** Any n-channel device whose
source swings has its bulk at the substrate and therefore a `1/n` gain division
it cannot size away. Followers, source-degenerated pairs and level shifters must
be p-type, or must not rely on unity source-follower gain. §5.

**C1 — Weak inversion pins node conductance.** `gms = gm + gmb = I_D/V_T`
**exactly**, so the *sum* of source conductances on a node is fixed by that
node's branch current. No cross-coupling trick reduces a driving-point
conductance; only a **forward-path difference** can be manufactured. Process-
independent — it holds here too. (This is what invalidates the naive
current-cancellation scaling in `tian2023` eqs (19)–(21).)

**C2 — DC gain is structural.** Shunt feedback pins H(0) = 1 (§3). Any technique
that touches the input device's *gate* path scales the dc gain and disqualifies
itself against S3. CARRIED FORWARD, ranking only: gate-cross placement measured
−8.6 dB, source-cross +12.3 dB, drain-cross exact. **Re-measure the three
numbers here before quoting them; keep the ranking as the design rule.**

**C3 — Silicon cap cost is `2·C1 + C2_drawn` per biquad**, so the high-Q pair
belongs on the larger-`gm_i` biquad and **a cap re-allocation control must be
run before crediting any technique**. In this reference the area half of that
control is exactly degenerate (§4.3) — run it for IRN. CARRIED FORWARD: with
devices and bias fixed, `a1000 ≤ −48 dB` pins the shape to 4th-order
Butterworth, so re-placing the poles *inside* the box is worth well under 1 %
more.

**C4 — The acceptance box lives in [target-spec.md](target-spec.md).** Passband
flatness is judged **two-sided only ≤ 150 Hz**; no-peaking is judged one-sided.
**Do not police ripple *through* the corner** — a ±ripple rule at 245 Hz
combined with −3 dB at 247 Hz is infeasible by construction and will make a
correct design look impossible.

**C5 — Linearity is slew-bounded, and this reference has little margin.**
DERIVED arithmetic (not a transient measurement — S7 has not been simulated on
this reference): at the S7 point the single-ended peak is
`Vp = 175 mVpp / 2 / 2 = 43.75 mV`, so the slew feasibility check
`I/C > 2π·fc·Vp` demands **68.7 V/s**. In-band the internal node is quiet
(eq. 2), so each output node sees ≈ `C1 + C2_single`, and the one-way current
limit is the output bias source, 2 units = 2.01 nA:

| biquad | C1 + C2_single (pF) | available I/C (V/s) | required (V/s) |
|---|---|---|---|
| A | 41.91 | 48.0 | 68.7 |
| B | 31.34 | 64.1 | 68.7 |

Both sit **at or below** the boundary, so S7 is genuinely at risk and **must be
measured, not assumed**. Any technique that shrinks bias current or grows
capacitance eats this margin from above; lower caps or higher bias current
improve THD. Those are the same currencies as noise and power — re-run THD
whenever swing, capacitance or bias changes.

**C6 — The power budget is filter-core only, and there is headroom.** S6 is
`< 50 nW` measured at the `vflt` series probe; the reference draws 12.07 nW, so
≈ **4× is available**. But in weak inversion, at fixed capacitance, noise is
essentially independent of `I_B` (`∝ kT/C·S(Q)`), and at fixed **fc** an I–C
homothety of factor k gives `IRN ∝ 1/√k`. So added current buys noise only if it
is spent on capacitance too — **spend headroom on slew/linearity or on `gm_i`,
not blindly.**

---

## 7. Carried forward — hypotheses, not measurements of this repo

Everything below was measured in the originating campaign, on another
technology at another supply. The **mechanisms** transfer; the **numbers do
not**. Each is a cheap, high-value experiment to re-run here. The full
classified inventory — technology-independent vs technology-bound, with the
re-opened list — is [prior-findings.md](prior-findings.md); this section is the
subset that constrains DUT design decisions.

| claim | why it matters here | status |
|---|---|---|
| The eight in-DUT bias sources are ≈ 61.7 % of the IRN power; the input followers ≈ 27.8 %; the shunt-feedback devices ≈ 10.5 % | If it reproduces, the whole −20.0 % ask is a bias-source problem, not a follower problem, and the corpus's slew/THD row is irrelevant to it | **NOT re-measured here** |
| The bench's reference/bias network contributes ≈ 0 % of the *differential* IRN (it is common mode and rejected) | Justifies keeping the reference ideal; would make S6's exclusion noise-neutral as well as power-neutral | **NOT re-measured here** |
| Flicker is ≈ 5 % of the noise power ⇒ chopping is worth ≈ −2.7 % at best | Pre-refutes an expensive technique. This repo's gate-referred flicker data (`doc/pdk-notes.md`) is per-device only, not a system split | **NOT re-measured here** |
| I–C homothety: scale every multiplier *and* every capacitor by k ⇒ fc, Q, dc gain, ph_max and THD invariant, power ∝ k, `IRN ∝ 1/√k` | The technique-free control curve. Every technique must be quoted **against** it, or it is just buying noise with current | **NOT re-measured here** |
| Shrinking C by shrinking gm costs exactly `√(C_ref/C)` in IRN | Kills every "smaller caps" idea that does not also add current | **NOT re-measured here** |
| A MOS cannot degenerate another MOS's noise in weak inversion: a subthreshold device in triode carries `S_id = 2qI·coth(V_DS/2V_T) ≥ 2qI`. Only a genuine resistor `R > 2V_T/I` removes it | Rules out the self-cascode composite as a noise lever; keeps resistive degeneration alive | mechanism holds by construction; **magnitudes NOT re-measured here** |
| Device noise is `4γqI`, not `2qI` | Any hand noise budget built on `2qI` is wrong by ~2× | **NOT re-measured here** |
| Exact injection forms `Z_out = s/(w0·Q·gm_f)`, `A_int = 1/gm_i` | Turns a noise breakdown into an analytic ranking of which node to attack | consistent with §3; **NOT re-verified here** |
| A single MOS cap across the differential outputs costs ≈ 8 dB of THD, all HD2; an anti-parallel pair restores balance at identical area | A symmetry argument, so it should transfer; the magnitude will not | **NOT re-measured here** |
| ≥ 2 % plate-to-substrate parasitic on the filter caps kills the SSF's S1 | The SSF is *not* parasitic-immune. Budget the bottom plate explicitly when the caps become `cap_cmim` instead of ideal `C` | **open risk, NOT evaluated here** |
| Adding a real CMFB to this family cost ≈ −13 dB of THD and oscillated rail-to-rail while the differential box showed zero violations | **Do not add a CMFB to this DUT.** If one is ever added, the scorecard needs a CM-step certificate before it can be trusted | **NOT re-measured here** |
| Regulating a bias *voltage* rather than a current is catastrophic in weak inversion (a gate voltage sets an exponential current) | Constrains any future real reference: mirror **currents** by device-multiplier ratio, never clamp `vbn`/`vbp` | **NOT re-measured here** |

### Deliberately not queued (carried forward, and why)

Kept as a permanent section so dead ends are not re-litigated — but note that
several of the originating campaign's closures named a *lower supply* as the
blocker. Those are **re-openable at 1.5 V** and are listed as such.

* **Closed on physics (should still hold here):** bulk-driven inputs and
  moderate-inversion re-biasing — both lower `gm` at fixed current and therefore
  *raise* IRN. Input-side current cancellation at any useful strength — the
  forward-path zero must clear ≈ 13 kHz to keep S1, which forces `k ≳ 0.98`,
  leaving nothing to cancel; feedback-side cancellation is zero-free but is a
  pure capacitance-for-noise exchange.
* **Closed on flicker share:** chopping / auto-zeroing — worth ≈ −2.7 % *if*
  flicker is again ≈ 5 % of the noise power. **Re-measure the flicker share
  first**; the conclusion is conditional on it.
* **RE-OPEN AT 1.5 V:** every closure whose stated blocker was headroom on a
  1.0 V branch — a second current reuse across the biquads, branch-stacking
  combined with a gate-driven pair, and the gate-driven mismatch/yield route.
  This port has 50 % more rail. Re-test the cheapest of these before deriving
  anything new.
