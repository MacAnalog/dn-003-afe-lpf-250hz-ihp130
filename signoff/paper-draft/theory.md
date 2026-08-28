# theory.md — the equations, and their derivations

**[REFERENCE]** — hand-written; the derivations below are symbolic and do not change when
the data is re-extracted.  Every number that *does* change lives in
[validation.md](validation.md), which is generated.  The map from the reviewer's request
to these sections is [README.md](README.md).

Four equations are derived here, in the order they depend on each other:

| § | equation | what it is used for |
|---|---|---|
| [2](#2-the-transfer-function) | `H(s)` — exact, symbolic, 4th order | poles, zeros, per-biquad `f₀` and `Q` |
| [3](#3-the-noise-equation) | `S_out = Σ_k \|Z_T,k\|²·S_i,k` | IRN and the per-device noise budget |
| [4](#4-the-distortion-equation) | `HD3(ω)` from the exponential device law | THD, and the amplitude/frequency laws |
| [5](#5-imd3-and-iip3) | `IMD3`, `IIP3` and the memoryless identity | two-tone linearity, and why the identity fails here |

§3 and §4 deliberately share one object, `Z_T,k` — the transimpedance from device *k*'s
drain–source port to the differential output.  A device's noise current and its distortion
current are injected at the same place, so they must be propagated by the same operator.
Establishing `Z_T,k` once, from the data, is what makes the distortion equation a
prediction rather than a fit.

---

## 1. The object, and the two reductions that make it tractable

### 1.1 The cell

A fully differential 4th-order low-pass filter: **two super-source-follower (SSF) biquads
in cascade, branch-stacked so that biquad B's bias current is reused as biquad A's output
current**, with a shared three-device replica generating the bridge gate bias `vbr`.
(The reviewer's reading of the topology — a PMOS super-source-follower with current reuse
of a cascoded PMOS flipped-voltage-follower — is the same circuit described from the
device side; no action was requested and none is taken.)

**The drawing of record.**  The cell's xschem schematic is committed, and every symbol
below is bound to a device on it:

![the delivered cell](../post-pvt/H12-pdk-cap/lpf_core_H12pc.png)

*`signoff/post-pvt/H12-pdk-cap/lpf_core_H12pc.png` — the pre-layout DUT of record,
rendered from `lpf_core_H12pc.sch` by `scripts/render_sch.py`.  Sizes, models and
connectivity are read verbatim from the certified netlist; the drawing shows biquad A on
the left, biquad B in the middle and the three-device replica on the right.*

Reading the equations against that drawing:

| instance | role | equation symbol | connection (this half) |
|---|---|---|---|
| `xm2` (`xm5`) | biquad-A input follower | `gm_ia` | g = `vinp`, s = `vout_1`, d = `net2` |
| `xm4` (`xm8`) | biquad-A shunt feedback | `gm_fa` | g = `net2`, d = `vout_1`, s = 0 |
| `xm9` (`xm10`) | biquad-A internal bias sink | — (absent from `H(s)`) | g = `vbn`, d = `net2`, s = 0 |
| `xmst` (`xmstn`) | **the current-reuse bridge** | `gm_br` | g = `vbr`, s = `net4`, d = `vout_1` |
| `xm0` (`xm1`) | biquad-B input follower | `gm_ib` | g = `vout_1`, s = `voutp`, d = `net4` |
| `xm14` (`xm15`) | biquad-B shunt feedback | `gm_fb` | g = `net4`, d = `voutp`, s = `vdd` |
| `xc13` (`xc17`) | biquad-A Miller cap | `C1a` | `net2` — `vout_1` |
| `xc19` | biquad-A load, floating | `C2a` (→ `2·C2a`) | `vout_1` — `vout_2` |
| `xc1` (`xc10`) | biquad-B Miller cap | `C1b` | `voutp` — `net4` |
| `xc12` | biquad-B load, floating | `C2b` (→ `2·C2b`) | `voutp` — `voutn` |
| `xr1`, `xr2`, `xr3` | replica generating `vbr` | — (an ac ground) | shared by both halves |

Two absences in that table are worth naming, because they are not the same absence.  The
**bias sinks** (`xm9`/`xm10`) are missing from `H(s)` because an ideal current source is
an open circuit to small signals — yet they carry **38.9 % of the IRN power**
(validation.md §5.2), within a hair of the input follower's 39.8 % and far ahead of
everything else, because they inject their current at `net2`, a node the signal uses.  The **replica** is missing from both: it sits
on the differential axis, so its noise is rejected along with its signal
(4.5·10⁻¹¹ % of the IRN power).  "Not in the transfer function" and "not in the noise" are
different statements, and only the model tells them apart.

Two structural facts drive everything:

* **The bridge `xmst` is the current-reuse element.**  Its source is biquad B's internal
  node `net4` and its drain is biquad A's output `vout_1`, with its gate on the replica
  rail.  Small-signal, it is a common-gate device: it *adds* a transconductance at `net4`
  alongside `gmf_b`, and it *injects* `gm_br·v_net4` into `vout_1`.  That injection is a
  path from biquad B back into biquad A, and §2.3 shows it is exactly the term that stops
  `H(s)` from being a product of two independent biquads.
* **`C2a` and `C2b` are drawn as single floating capacitors between the two halves.**
  Under differential excitation the far plate moves by exactly `−v`, so each half is loaded
  by `2·C2` to the virtual ground.  Every `2` in the algebra below is this factor, and it is
  why the drawn farads are half what a single-ended realisation would need.

### 1.2 Reduction 1 — the differential-mode half-circuit, and why it is exact here

Under a differential excitation `vinp = +½`, `vinn = −½`, every net on the symmetry axis
(`vbn`, `vbr`, `rep_x`, `vdd`, and the replica's internal nodes) is a virtual ground, and
the two halves carry equal and opposite signals.  This is **not an approximation for this
cell**: the two halves are drawn from the same device list with identical sizes, so the
system matrix is exactly symmetric under the half-swap permutation, and the differential
eigenspace is invariant.

Stripped to the half, and drawn as the branches the algebra actually contains:

![the DM half-circuit, labelled with the equation's symbols](figures/half_circuit.png)

*`figures/half_circuit.png` (`scripts/figures.py::fig_half_circuit`).  The same cell as the
schematic above, reduced to one half and to its small-signal branches, with each branch
labelled by the symbol it carries into §2.  The red branch is the bridge — the only path
between the two biquads, and the reason `κ ≠ 0`.*

The reduction is discharged numerically rather than asserted: the half-circuit's `H(s)` is
compared against the **full 13-node differential solve** at the same operating point and
against the ac sweep, and gives identical poles, identical dc gain and the same residual
against simulation ([validation.md §2–3](validation.md#2-the-transfer-function-evaluated)).
The half-circuit is used only where a *readable symbolic* answer is wanted; every reported
pole, zero and transimpedance comes from the full differential system.

### 1.3 Reduction 2 — the small-signal model, and the four things weak inversion changes

Each MOS becomes `gm`, `gmb`, `ro`, `cgs`, `cgd`, `cdb`, `csb`.  Four bindings are specific
to this cell and each is asserted in code (`scripts/n2tf_model.py::bind_op` refuses the
netlist if any fails):

| binding | why |
|---|---|
| `gmb = 0` | every device has bulk tied to source, so `v_bs ≡ 0` |
| `csb = 0` | source and bulk are the same node; the capacitor is shorted out |
| `cgs ← cgs + cgb` | **in weak inversion there is no channel**, so the PSP `cgb` op-var carries essentially all of `cgg`; with bulk at the source it lands gate-to-source |
| `cdb ← cdb + cjd` | intrinsic drain–bulk plus the drain junction |

The third is the one that matters numerically and the one a hand-written model gets wrong:
measured on the biquad-A input follower, `cgg` = 250.5 fF of which **`cgb` = 247.4 fF and
`cgs` = only 3.1 fF**.  Reading those op-vars with strong-inversion habits — take `cgs` as
the gate-to-source capacitance and leave `cgb` on the bulk — puts **81× too little**
capacitance on the node.  In weak inversion there is no inversion layer to terminate the
gate field, so the charge lands on the bulk; bulk is the source here, so it is
gate-to-source capacitance in every sense that matters to the circuit.   [validation.md §2.2](validation.md#22-reconciling-the-three-pole-estimates--closed-form-full-model-simulation)
shows this single capacitance is the entire 2 % gap between the design equation and the
simulator, as well as the origin of both out-of-band zero pairs.

---

## 2. The transfer function

### 2.1 The construction

With the small-signal model in place, the half-circuit's MNA system is *exactly* a linear
matrix pencil in `s`:

```
    Y(s)·v = b ,        Y(s) = G + s·C
```

`G` collects conductances and controlled sources (`gm`, `1/ro`), `C` collects capacitances,
and `b` is the excitation.  No approximation has been made yet: `Y(s)` is affine in `s`
because every element is either a conductance or a capacitance.

The transfer function follows by Cramer's rule on the reduced (grounded-node-removed)
system, which is what `spicexplorer_netlist2tf.extract_tf` computes symbolically:

```
    H(s)  =  V_out(s)/V_in(s)  =  det M(s) / det Y_rr(s)
```

with `M(s)` the bordered pencil that replaces the output column by the input injection.
For the 5-node half-circuit this is a symbolic determinant of manageable size; for the full
13-node differential cell it is not, and the poles and zeros are taken instead as the
finite generalised eigenvalues of `(−G_rr, C_rr)` and of the bordered pencil respectively
(`scripts/pencil.py`).  **The two routes are the same algebra**, one solved in symbols and
one in floating point; §3 of validation.md checks them against each other and against the
simulator.

### 2.2 The result

At `Fidelity.IDEAL` — transconductances and the four design capacitors, no device
parasitics — the exact result is

```
                       gm_fa · gm_ia · gm_ib · (gm_br + gm_fb)
    H(s)  =  ─────────────────────────────────────────────────────────
                  a₄·s⁴ + a₃·s³ + a₂·s² + a₁·s + a₀   ≡   D(s)
```

with, in full — this is the whole transfer function, nothing elided:

```
  a₄ = 4·C1a·C1b·C2a·C2b

  a₃ = 2·C1a·( C1b·C2a·gm_br + C1b·C2a·gm_fb + C1b·C2b·gm_fa + 2·C2a·C2b·gm_br )

  a₂ = C1a·C1b·gm_fa·(gm_br + gm_fb)
     + 2·C1a·C2a·gm_ib·(gm_br + gm_fb)
     + 2·C1a·C2b·gm_br·(gm_fa + gm_ib)
     + 2·C1b·C2b·gm_fa·gm_ia

  a₁ = gm_fa·( C1a·gm_ib·(gm_br + gm_fb) + C1b·gm_ia·(gm_br + gm_fb) + 2·C2b·gm_br·gm_ia )

  a₀ = gm_fa·gm_ia·gm_ib·(gm_br + gm_fb)
```

Printed verbatim by `scripts/tf_analysis.py` into `data/tf.json` (`symbolic.quartic_coeffs`,
and `symbolic.h_latex` for the LaTeX form).  Grouped as written above, the structure is
already half visible: `gm_br` and `gm_fb` travel together almost everywhere — the bridge
acting as extra shunt feedback for biquad B — and the few places `gm_br` appears alone are
what branch stacking adds.  Making that precise:

The denominator factors **exactly** — this is a symbolic identity, verified by
`sympy.expand(D − (D_A·D_B + κ·s²)) == 0` in `scripts/tf_analysis.py::symbolic_form`,
which raises if the residual is anything but zero:

```
    D(s)  =  D_A(s) · D_B(s)  +  κ · s²

    D_A(s) =  2·C1a·C2a·s²  +  C1a·gm_fa·s  +  gm_fa·gm_ia
    D_B(s) =  2·C1b·C2b·s²  +  [C1b·(gm_br + gm_fb) + 2·C2b·gm_br]·s  +  gm_ib·(gm_br + gm_fb)
    κ      =  2·C1a·C2b·gm_br·gm_ib
```

**Reading the three pieces.**

* `D_A` is the textbook SSF biquad.  Dividing through by `gm_fa·gm_ia`,

  ```
      D_A/(gm_fa·gm_ia)  =  1 + s·C1a/gm_ia + s²·C1a·(2·C2a)/(gm_ia·gm_fa)
  ```

  which is exactly the validated single-biquad model of `doc/design-reference.md` §3 with
  its single-ended load `C2_single = 2·C2a`.  The two derivations were done independently
  and agree symbol for symbol — that agreement is itself one of the checks.
* `D_B` is the same biquad with the **two things branch stacking does to it**:
  1. the bridge's transconductance **adds** to the shunt-feedback device, `gm_fb → gm_fb + gm_br`,
     because both devices terminate `net4` against an ac ground; and
  2. the bridge contributes an **extra damping term** `2·C2b·gm_br` on the `s` coefficient,
     because the bridge's own source node carries the output capacitance.
* `κ·s²` is the **price of the current reuse**, and it is the red branch of the
  half-circuit figure in §1.2.  It is the only term coupling the two
  biquads, and its ingredients name the loop precisely: `gm_ib` (B's follower senses A's
  output), `gm_br` (the bridge feeds B's internal node back into A's output), `C1a` and
  `C2b` (the two capacitors that loop is closed through).  Set `gm_br → 0` and the whole
  structure collapses in one step: `κ = 0`, `D_B` becomes a plain SSF biquad, `a₀` becomes
  `gm_fa·gm_ia·gm_ib·gm_fb`, and `H(s)` is the product of two independent second-order
  sections.  The bridge is the entire difference between "two biquads" and "this filter".

**The numerator, and why the dc gain is structural.**  The numerator is
`gm_fa·gm_ia·gm_ib·(gm_br + gm_fb)`, which is precisely the constant term of `D_A·D_B`
(and `κ·s²` has no constant term).  Therefore

```
    H(0) = 1  exactly, for any sizing.
```

The passband gain is a property of the topology, not an outcome of the sizing — it is why
the `|dc| ≤ 0.2 dB` clause is a structural guarantee here rather than a knob.  At
`Fidelity.FULL` the finite `ro` of the followers moves it to −0.0081 dB, and nothing else
does.

### 2.3 Per-biquad `f₀` and `Q` — and which Q the reviewer should be given

Each factor is a standard second-order denominator `a·s² + b·s + c`, so
`ω₀ = √(c/a)` and `Q = √(a·c)/b`:

```
                gm_fa · gm_ia                                    ⎡ 2·C2a · gm_ia ⎤
    ω₀,A²  =  ─────────────── ,          Q_A  =  sqrt ⎢ ───────────── ⎥
               2·C1a · C2a                                       ⎣ C1a  · gm_fa  ⎦

               gm_ib · (gm_br + gm_fb)                sqrt[ 2·C1b·C2b·gm_ib·(gm_br + gm_fb) ]
    ω₀,B²  =  ───────────────────────,     Q_B  =  ───────────────────────────────────────────
                    2·C1b · C2b                       C1b·(gm_br + gm_fb)  +  2·C2b·gm_br
```

`Q_A` is the classic SSF result — a *capacitance ratio* at fixed devices, which is why the
filter's shape can be tuned at constant power.  `Q_B` is not: the bridge appears in the
numerator through `gm_br + gm_fb` (under a square root) and again, alone and linearly, in
the denominator's `2·C2b·gm_br` term.  Differentiating, `∂Q_B/∂gm_br < 0` for every
positive parameter set — the square root can never outrun the linear term — so **raising
the bridge's transconductance strictly lowers `Q_B`**.  The current reuse buys its power
saving partly out of biquad B's Q, which is a trade-off the closed form makes visible and
a simulation sweep would only hint at.

**Which Q to quote.**  These two are the Q's of the **isolated stages** (`κ = 0`).  At the
measured operating point they are **2.10 and 0.46** — and they are *not* the filter's Q's,
because `κ` is 11.78 % of the quartic's own `s²` coefficient, which is far too large to
neglect.  The filter's actual pole pairs, from the roots of the full quartic
`D_A·D_B + κ·s²`, are

```
    pair A:  f₀ = 249.72 Hz,  Q = 0.5430          pair B:  f₀ = 251.08 Hz,  Q = 1.3074
```

i.e. essentially a **4th-order Butterworth** (0.5412 / 1.3066), realised by two
frequency-coincident, differently damped pairs.  So the answer to *"the quality factor of
each biquad"* is stated in both forms, deliberately:

| | biquad A | biquad B | meaning |
|---|---|---|---|
| isolated-stage Q (`κ = 0`) | 2.10 | 0.46 | what each section would do on its own |
| **filter pole-pair Q** | **0.543** | **1.307** | what the cascade actually realises |

**The coupling is the design.**  A reader who sizes the two sections independently to
Q = 0.54 and 1.31 and then stacks them will not get a Butterworth response; the stacking
maps (2.10, 0.46) onto (0.543, 1.307).  That mapping is `κ`, and it is the single most
useful thing the closed form says about this topology.

### 2.4 Zeros

At `Fidelity.IDEAL` the numerator is a constant: the design capacitors alone produce **no
finite zeros**, and the response is all-pole.  Finite zeros appear only when device
capacitance is added, because a source follower's gate-to-source capacitance is a direct
feed-forward path from its input to its output.  The measured consequence — two complex
pairs at 3.85 kHz and 5.05 kHz, and their disappearance when `cgs` is zeroed while `cgd`
changes nothing — is in
[validation.md §2.2 and §4](validation.md#4-poles-and-zeros--the-map).  Both are more than
15× above the pole frequency and neither affects the passband or the 1 kHz stopband number.

---

## 3. The noise equation

### 3.1 Derivation

A noise source is a current generator `i_k` across a device port `(p, q)`.  Because the
system is linear, superposition applies exactly, and the output voltage produced by that
generator alone is

```
    v_out,k(jω)  =  Z_T,k(jω) · i_k ,       Z_T,k(jω) ≡ V_out(jω) / I_inj at port (p,q)
```

`Z_T,k` is obtained from the *same* pencil `Y(s) = G + s·C`: drive `+1 A` into node `p` and
`−1 A` out of node `q`, ground the input port, solve, and read the differential output.
That is one linear solve per port per frequency, and it is what
`spicexplorer_netlist2tf.transimpedance` computes.

Distinct generators are uncorrelated (they are independent physical processes in distinct
devices, or distinct mechanisms in one device), so their **powers** add:

```
    S_out(f)  =  Σ_k  |Z_T,k(j2πf)|² · S_i,k(f)                                     (N1)
```

and, referring to the input through the filter's own response and integrating over the
sign-off band,

```
    IRN²  =  ∫[0.5, 200] S_out(f) / |H(j2πf)|²  df                                  (N2)
```

`(N1)` is the noise equation the reviewer asked for.  It contains no fitted quantity:
`S_i,k(f)` is the simulator's own per-generator noise vector and `Z_T,k` is a solve on the
operating-point-bound matrices.

### 3.2 What the generators are, in this bias regime

For a MOS in weak inversion and saturation the channel current is a sequence of
independent barrier-crossing events, so the channel generator is **shot noise**:

```
    S_id  =  2·q·I_D          (equivalently  2·n·kT·gm,  since gm = I_D/(n·U_T))
```

not the strong-inversion `4kT·γ·gm` with γ = ⅔.  The two forms differ in both magnitude and
bias dependence, and [validation.md §5.3](validation.md#53-are-the-generators-what-they-claim-to-be)
shows the data selecting the shot-noise form (`S_i/2qI_D` = 0.63–0.72, and the `gm`-referred
column differing from it by exactly `n/2` as it must).  Flicker noise adds
`S_flicker ∝ 1/f^(1+δ)` at the gate, and the gate-current generator `igig` — normally
ignorable and emphatically not ignorable here, at **27 % of the total IRN power** against
62 % for the channel and 11 % for flicker — adds the shot noise of the gate leakage
itself.  A sub-nW filter is one of the few places that term surfaces, and a hand model
that drops it is 1.4 dB optimistic on IRN before it starts.

### 3.3 Which port each generator belongs to — established, not assumed

`(N1)` is only meaningful if each `S_i,k` is paired with the right `Z_T,k`.  Rather than
assume the pairing, it is **selected from the data**: for each generator, every candidate
device port is tried, and the one whose implied `S_i = S_out/|Z_T,port|²` comes out closest
to the shape the physics demands (frequency-flat for channel and gate-leakage noise, `1/f`
for flicker) wins, with the full ranking and the margin over the runner-up recorded
(`scripts/noise_analysis.py::identify_port`).  Every channel generator selects
drain–source and every gate generator selects gate–source.

This matters beyond noise: it is the evidence that licenses **re-using the same `Z_T,k` for
the distortion current in §4**, which is what turns the distortion equation into a
prediction with no free parameters.

### 3.4 The closure that makes it a proof rather than a plausibility argument

`(N1)` is checked three ways at once, all in
[validation.md §5.1](validation.md#51-closure):

1. `Σ_k |Z_T,k|²·S_i,k` reproduces the simulator's own total output noise to 2·10⁻⁷ % **at
   every frequency** — so no generator is missing, none double-counted, and the `Σ` is
   complete.
2. `(N2)` reproduces the certified sign-off IRN exactly, using the frozen `lab.metrics`
   integrator rather than a re-derivation.
3. `spicexplorer_netlist2tf.transimpedance` and the independent matrix-pencil solve agree
   to ~10⁻⁸ relative — two implementations of `Z_T` rather than one.

---

## 4. The distortion equation

### 4.1 Generation: what an exponential device emits

Every device is below threshold (validation.md §1), so

```
    I_D  =  I_S · exp( v_GS / (n·U_T) ) ,      n = 1/((gm/I_D)·U_T),   U_T = kT/q
```

With a sinusoidal gate–source excursion `v_gs(t) = V_e·cos ωt`, define the **modulation
index**

```
    a  =  V_e / (n·U_T)
```

and use the Jacobi–Anger expansion of the exponential in modified Bessel functions:

```
    exp(a·cos ωt)  =  I₀(a)  +  2·Σ_{k≥1} I_k(a)·cos(k·ωt)
```

The dc term of the drain current is `I_S·I₀(a)`, which is *what a dc measurement of `I_D`
already reports*.  Dividing through, the k-th harmonic current is

```
    i_k  =  I_D · 2·I_k(a) / I₀(a)          →      i₃ ≈ I_D·a³/24 ,  i₂ ≈ I_D·a²/4   (a ≪ 1)
```

The exact Bessel ratio is used everywhere in the code, not the truncation: the two agree to
1 % below a ≈ 0.3 and diverge above it, and the frequency sweep deliberately goes above it.

**`a` is not a free parameter.**  `n` comes from the measured `gm/I_D`, and `V_e` is read
out of the exact small-signal model at the drive amplitude — it is the follower's own
gate-minus-source excursion, which the shunt feedback makes small and strongly frequency
dependent.  Nothing in the distortion equation is fitted.

### 4.2 Propagation: the same `Z_T` as the noise

`i₃,k` appears across device *k*'s drain–source port — the port §3.3 established from the
data — so it reaches the output through the same transimpedance, evaluated at the third
harmonic:

```
    HD3(ω)  =  | Σ_k  Z_T,k(j3ω) · I_D,k · 2·I₃(a_k(ω))/I₀(a_k(ω)) |  /  |V_out,fund(ω)|   (D1)
```

Two details that are easy to get wrong and that cost real dB:

* **The sum is coherent, and it runs over both halves.**  Under differential drive the two
  halves' gate excursions are opposite *and* their transimpedances to the differential
  output are opposite; the two sign flips cancel, so the N-half device adds **in phase**
  with its P-half twin, not against it.  Summing only one half under-predicts HD3 by about
  21 dB — a mistake made and caught during this work.
* **Each term carries the phase `exp(3j·arg v_gs)`.**  The devices' `v_gs` phasors are not
  aligned (the internal nodes lag the outputs), so the terms partially cancel.  `(D1)` is
  reported alongside a worst-case `Σ|·|` bound so the size of that cancellation is visible.

### 4.3 The two laws `(D1)` predicts, and their scope

**Amplitude.**  At fixed ω, `a ∝ A` and the fundamental is linear in `A`, so
`HD3 ∝ a³/A ∝ A²` — **40 dB/decade**.  Measured: 42.63 dB/decade with a 0.51 dB worst
residual over the three drives inside the model's window
([validation.md §6.1](validation.md#61-hd3-versus-amplitude--the-a²-law)).
`THD ≈ HD3` throughout, because HD2 is 25–50 dB below HD3 — the differential topology
cancels even-order terms, and the residual HD2 is mismatch-free simulation, i.e. numerical.

**Frequency.**  A follower's own `v_gs` is the *error* of the follower:
`v_gs = v_in − v_out ∝ (1 − H(jω))·v_in`, and at low frequency `|1 − H| → ω·C1/gm_i`.  So
`V_e ∝ ω`, `a³` gives `ω³`, and the falling `|Z_T(j3ω)|` returns one power — the
**`HD3 ∝ ω²`, 40 dB/decade** asymptote.  That asymptote needs `3ω ≪ ω₀`, which at
f_in = 50 Hz is already violated (3ω sits at 0.6·f_c); `(D1)` keeps `|1 − H(jω)|` and
`Z_T(j3ω)` exactly and is correspondingly steeper near the corner.

**Stated scope.**  `(D1)` is a weak-inversion, small-`a`, quasi-static, linear-propagation
model.  Measured against simulation at 43.75 mVpp it holds to **±2 dB over 35–65 Hz**;
below that an additive residual of 0.18–0.28 µV dominates — constant in volts while the
model itself moves 32 dB, which is the signature of a mechanism `(D1)` does not contain —
and above ~100 Hz
`a` exceeds 0.3 and the propagation stops being linear.  Every claim made from `(D1)` in
this pack is made inside that window, and the full error table is
[validation.md §6.2](validation.md#62-hd3-versus-frequency--the-ω²-law-and-where-the-model-stops).

---

## 5. IMD3 and IIP3

### 5.1 The definitions used

Two equal tones at `f₁`, `f₂` (`f₁ < f₂`, spacing `Δ = f₂ − f₁`), each of peak amplitude
`A` at the differential input.  The third-order intermodulation products fall at
`2f₁ − f₂` and `2f₂ − f₁`; `IMD3` is their level relative to one output fundamental, and

```
    IIP3|_dBV  =  A|_dBV  −  IMD3|_dBc / 2                                          (I1)
```

which is the usual 3:1-slope extrapolation, written in dBV because this is a voltage-mode
cell with no reference impedance anywhere in it (§6.3 of validation.md says why no dBm
figure is quoted).  `(I1)` is only meaningful where `IMD3` really does move at 3 dB/dB;
that is tested rather than assumed — the measured IMD3 slope is 41.7 dB/decade against the
theoretical 40, and the IIP3 extrapolated from each of the three in-regime amplitudes
agrees to 0.52 dB.

### 5.2 The memoryless identity, and why it must fail here

For a **memoryless** cubic nonlinearity `y = α₁x + α₃x³`, driven at the same per-tone
amplitude, the third-order products are larger than the single-tone third harmonic by
exactly a factor of 3:

```
    IMD3  =  HD3  +  20·log₁₀ 3  =  HD3 + 9.54 dB                                   (I2)
```

`(I2)` is a *test*, not a prediction, and §4.3 already says it must fail: `HD3` here rises
steeply with frequency, so the third-order response is far from memoryless.  Measured
excess: **+6.95 dB**.

The useful question is *which* memory.  There are two candidates, and they are
distinguishable by experiment:

* **Envelope (baseband) memory** — the cell's response at the difference frequency `Δ`.
  This would make IMD3 depend strongly on tone spacing.
* **Carrier-frequency dependence** — the third-order response varying with `f`, which is
  exactly the mechanism of §4.3.  This is nearly independent of spacing at fixed centre
  frequency.

The spacing sweep decides it: over a **15× change in Δ**, IMD3 moves **1.76 dB**
([validation.md §6.4](validation.md#64-is-the-cell-memoryless--the-imd3--hd3--954-db-test)).
Envelope memory is therefore ruled out and the 6.95 dB excess is attributed to carrier
frequency dependence.  The engineering consequence is worth stating plainly: **for this
cell, HD3 at one frequency does not predict IMD3 — measure IMD3.**

### 5.3 A measurement constraint that is part of the equation's validity

`IMD3` is read from a DFT of a coherent strobed transient.  Both tones and all four
third-order products must land exactly on DFT bins, which forces the spacing to be an even
multiple of the DFT bin.  An odd spacing puts the tones on half-bins, and the resulting
"IMD3" is spectral leakage rather than distortion — observed once at −0.79 dBc, which is a
number no circuit produces.  Every two-tone result in this pack uses even spacings, and
every transient carries a rectangular-vs-Hann agreement guard as the coherence check.

---

## 6. Assumptions, and where each one is discharged

| # | assumption | discharged by |
|---|---|---|
| A1 | the DM half-circuit is exact for this cell | identical poles/dc gain/residual against the full 13-node differential solve — validation.md §2–3 |
| A2 | bulk is tied to source on every device (`gmb = 0`, `csb = 0`) | asserted in `n2tf_model.bind_op`, which refuses the netlist otherwise; visible in the `core.sp` device lines |
| A3 | `cgb` folds into `cgs` in weak inversion | measured `cgg` = 250.5 fF, `cgb` = 247.4 fF on the input follower; the ablation of validation.md §2.2 shows this capacitance alone closes the model-to-simulator gap |
| A4 | small-signal linearity for `H(s)`, `Z_T` | 0.027 dB / 0.34° against the ac sweep over the scored band — validation.md §3.1 |
| A5 | noise generators are uncorrelated (powers add) | `Σ_k` closes on the simulator's total to 2·10⁻⁷ % at every frequency — validation.md §5.1 |
| A6 | each generator's port | selected from the data with a recorded ranking and margin — validation.md §5.3 |
| A7 | weak-inversion exponential device law | every device below threshold; and the exponential law's own prediction (40 dB/decade) confirmed at 42.63 — validation.md §1, §6.1 |
| A8 | `(D1)`'s validity window | ±2 dB over 35–65 Hz, with both failure modes named and bounded — validation.md §6.2 |
| A9 | `post_lumped` stands in for the extracted post-layout netlist in the symbolic lane | `fc` within 0.003 Hz and `ph_max` within 0.05° of the certified post-layout scorecard — validation.md §7 |

**One open item**, carried honestly rather than closed: below ~35 Hz the measured third
harmonic exceeds `(D1)` by an amount that is **constant in volts** — 0.18, 0.21 and
0.28 µV at 10, 20 and 35 Hz, while `(D1)`'s own prediction moves by a factor of 39 over
the same span.  An additive, frequency-independent excess is a different mechanism, not a
mis-scaled version of the modelled one; drain-conductance nonlinearity is the natural
candidate, since a small-signal `Z_T` linearises it away by construction.  The whole
residual sits **61.7 dB below** the third harmonic the cell produces at the S7 operating
point (256 µV at 175 mVpp, 50 Hz), so it is a modelling gap and not a performance one.
Closing it needs a `g_ds(V_DS)` expansion term the present model does not have.
