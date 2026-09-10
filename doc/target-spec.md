# Target spec — the design challenge

**KIND: SPEC.** This file is the contract every experiment is judged against.
Its machine-readable twin is `lab.metrics.SPEC` / `SOFT` / `goal_met` plus the
THD constants in `lab.metrics` (`THD_AMPL`, `THD_FIN`, `THD_LIMIT_DB`). **If you
change one, change the other** — they are meant to be kept in sync mechanically.

---

## The challenge

Cut IRN(0.5–200 Hz) from the **49.98 µVrms** reference baseline measured in this
repo to **< 40 µVrms** — a **−20.0 %** reduction — by **combining techniques from
at least TWO papers** in `pdf/`; a single-paper result does not qualify.
Everything else about the filter holds inside the box below: order, cutoff,
flatness, distortion and power. Total capacitance is **reported, never specced**.

## Conditions

| item | value |
|---|---|
| PDK | **IHP SG13G2**, 130 nm BiCMOS, open source (Apache-2.0). No NDA: decks, models and logs may be committed and published. |
| Devices | **`sg13_hv_nmos` / `sg13_hv_pmos`** (thick-oxide, 3.3 V class), selected by measurement — see `doc/pdk-notes.md`. MIM cap `cap_cmim`; resistors `rsil`/`rhigh`/`rppd`. |
| Corner | `.lib cornerMOShv.lib mos_tt` (sections `mos_tt`, `mos_ss`, `mos_ff`, `mos_sf`, `mos_fs`); `lab.config.CORNER_NOM`. |
| Simulator | **ngspice 45 built with OSDI.** IHP MOS devices *are* PSP 103.6 Verilog-A compact models loaded as `.osdi` objects — a stock ngspice cannot simulate this PDK at all (`Unknown model type psp103va`). Default lane = Docker `spicexplorer-spice-base:local`; native lane via `LPF_NGSPICE`. |
| Supply | **VDD = 1.5 V** (`lab.config.VDD`) |
| Common mode | input CM **0.25 V** (`lab.config.VICM`), output CM **≈ 1.25 V** (`lab.config.VOCM`). Every follower is p-type, so each biquad shifts the CM up one \|Vgs\|; the input CM is placed low so the output lands mid-supply. |
| Temperature | 27 °C (`lab.config.TEMP_NOM`) |
| DUT | fully differential 4th-order LPF, **two cascaded SSF biquads, no CMFB** — the followers define the common mode. See `doc/design-reference.md`. |
| Bench | one deck, built (never text-edited) by `lab.deck.ac_noise`; the frozen certificate deck is `decks/reference/lpf_tb.sp`. See `doc/benches.md`. |

---

## S1–S8

The **reference baseline** column is the expert topology, ported to this PDK and
re-sized to spec, frozen in `decks/reference/`. It plays the role the
originating campaign's baseline played: it is the yardstick, not the target.
Every number in that column was **measured in this repo** unless the cell says
otherwise.

| # | requirement | target | reference baseline (measured here) | checked by |
|---|---|---|---|---|
| S1 | filter order / shape | 4th-order low-pass, **two true biquads** (total phase shift → 360°) | **346.74°** max unwrapped lag (ideal 4-pole ceiling **350.53°**); **−48.43 dB** at 1 kHz | `lab.metrics.SPEC["ph_max_deg"] >= 330.0` **and** `SPEC["a1000_db"] <= -48.0` |
| S2 | cutoff | 250 Hz ± 2 % ⇒ **245.0 – 255.0 Hz** | **250.37 Hz** | `SPEC["fc_hz"] in (245.0, 255.0)` |
| S3 | passband gain | 0 dB, **\|dc\| ≤ 0.2 dB**, flat ≤ 150 Hz | **−0.0047 dB** dc; **ripple 0.2512 dB — FAILS** the flatness clause on a dense sweep (see note) | `SPEC["dc_db"] abs<= 0.2` |
| S4 | peaking | none, **≤ 0.2 dB** numerically | **0.0227 dB** | `SPEC["peak_db"] <= 0.2` |
| S5 | **IRN, 0.5–200 Hz** | **< 40 µVrms** | **49.98 µVrms** ← the number to beat | `SPEC["irn_uv"] < 40.0`; `lab.metrics.goal_met` |
| S6 | **filter-core power** (core only — **excludes** the bias reference) | **< 50 nW** (= 33.3 nA of core current at 1.5 V) | **12.07 nW** (8.04 nA) — 4.1× headroom | `SPEC["p_core_nw"] < 50.0`, from the `vflt` series probe |
| S7 | THD @ 175 mVpp differential, **fin = 50 Hz** | **≤ −40 dB**, harmonics 2–10; higher fins are an informative profile only | **−48.37 dB** (HD3-dominated; HD2/HD4 sit at the ≈ −148 dB numerical floor, as a balanced differential cell should) | `lab.thd.measure` → `lab.metrics.THD_LIMIT_DB`; coherent strobed transient + DFT (`lab.deck.tran_thd`) |
| S8 | technique provenance | **≥ 2 papers** from `pdf/` combined | — | the experiment README's `**Paper` row |

**Two lines are NOT spec lines and must stay that way:**

| line | reference value | the rule |
|---|---|---|
| total drawn capacitance | **98.01 pF** (`c1_a` 29.468 / `c2_a` 6.221 / `c1_b` 11.453 / `c2_b` 9.946 pF) | a *report* column (die cost), subordinate to noise. A candidate may spend or save capacitance freely; it must disclose the number |
| `idd_total_na` (whole-testbench supply) | **10.05 nA** | report-only. 2.01 nA of it is the reference current and its mirror, which S6 excludes by construction |

**Soft box is empty.** `lab.metrics.SOFT` names report-only columns
(`c_total_pf`, `idd_total_na`, `i_core_na`, `onoise_uv`, `ph_step_deg`,
`f_scored_hi`, `mono_db`); none of them is a pass/fail.

### Reference-baseline detail (all measured here, `runs/ledger.ndjson` tag `ref_fit`)

| quantity | value |
|---|---|
| fc | 250.37 Hz |
| passband gain (dc, absolute, at 0.1 Hz) | −0.0047 dB |
| peaking | 0.0227 dB |
| ripple to 150 Hz (S3 flatness) | **0.2512 dB — over the 0.2 dB bound** |
| `mono_db` (worst rise of \|H\| below fc) | 0.0227 dB — essentially monotone |
| \|H\| at 1 kHz | −48.43 dB (4th-order Butterworth arithmetic: −48.16 dB) |
| ph_max (S1 certificate) | 346.74° |
| ph_step (resolvability, report-only) | 46.94° |
| highest scored frequency (−100 dB floor) | 3162.3 Hz |
| IRN 0.5–200 Hz | **49.98 µVrms** |
| output noise 0.1 Hz–1 kHz | 73.11 µVrms |
| core current / power | 8.04 nA / **12.07 nW @ 1.5 V** |
| total testbench supply | 10.05 nA |
| total drawn capacitance | 98.01 pF |
| devices | 16 transistors + 6 capacitors |
| bias | one ideal reference current into a real n/p mirror; every bias device is an integer multiple of that unit (per side: 2 units at each biquad output ⇒ 8 nA core) |

### The S6 ruling (stated explicitly, because it is the one supply-coupled line)

The originating campaign ran at a different supply, so S6 had to be re-ruled on
port. **The spec is stated in WATTS, so the box stays `< 50 nW`.** At 1.5 V that
is **33.3 nA** of core current — a *tighter* current budget than a
hold-the-current reading would have given, and the stricter of the two
candidate rulings. The reference draws 8.04 nA = 12.07 nW, leaving ≈ 4× of
headroom to spend on slew, linearity or gm.

The conversion is explicit in code — `p_core_nw = i_core * config.VDD * 1e9`
(`lab.metrics.score_plots`). Never re-introduce the shortcut "current in nA is
numerically power in nW"; that identity holds only at a 1 V rail.

### S7 (closed — measured here)

`lab.thd.measure` scores the coherent strobed transient (`lab.deck.tran_thd`)
against the constants in `lab.metrics` (`THD_AMPL = 87.5e-3`, `THD_FIN = 50.0`,
`THD_LIMIT_DB = -40.0`). The reference baseline measures **−48.37 dB**,
HD3-dominated, with HD2/HD4 at the ≈ −148 dB numerical floor — which is the
balance check as much as the distortion number: a differential cell whose even
harmonics climb off the floor has an asymmetry or a bug, not a linearity result.
Nothing here is carried forward from the originating campaign.

### S3's flatness clause: the reference does not meet it

Stated plainly because the reference is the yardstick and it must not be
described as "on spec except for noise". Re-certified on a 50 pts/decade sweep,
the reference measures **`ripple_db` = 0.2512 dB** against the 0.2 dB bound. It
passed at 10 pts/decade only because the samples straddled the feature — the
same resolution problem that hid passband sags on every candidate.

It is a shallow one-sided droop, not a bump: `mono_db` = 0.0227 dB says the
response essentially never climbs, which is why it looks right by eye. The
reference stays the yardstick and stays frozen; a candidate that meets the
flatness clause is *better than the reference on that line*, and should say so
rather than quietly inheriting the reference's pass.

---

## Technology-independence: which lines are held verbatim, which were re-anchored

| # | held verbatim (technology-independent) | re-anchored here, and why |
|---|---|---|
| S1 | "two true biquads, 4th-order LP" is pure transfer-function shape. The companion `a1000 ≤ −48 dB` is **arithmetic, not silicon**: a 4-pole maximally flat response at 4× the cutoff is exactly 4⁻⁴ = **−48.16 dB** (`lab.shape.A1000_BUTTER_DB`). The **330°** threshold is also held. | Only the *baseline* moved: the reference measures **346.74°**, clearing the box by 16.74°. The **−100 dB magnitude floor** was re-validated on this repo's own response (scored band ends at **3162.3 Hz**, worst step **46.94°**). **The floor also caps the achievable score, and 360° is not it:** an ideal 4-pole Butterworth returns **350.53°** through the same floor, so a cell scoring **above** ~351° is carrying parasitic lag, not extra order. Derivation and the unfloored comparison: §`ph_max_deg` below. |
| S2 | 250 Hz and ±2 % ⇒ 245.0–255.0 Hz. **Held verbatim.** | Nothing in the number. The *sizing* that hits it (gm and C) is entirely technology-dependent and was re-synthesized — see `doc/design-reference.md`. |
| S3 | 0 dB, \|dc\| ≤ 0.2 dB. Structural: shunt feedback pins H(0) = 1 independently of process. Flatness judged two-sided only **≤ 150 Hz** — do not police ripple *through* the corner. | The **structure** changed: with no isolated NMOS in SG13G2, an n-input follower's dc gain is exactly 1/n and blows this line by 10×. Both stages are p-type here. The measured −0.0047 dB is this repo's reference, not a carried-forward number. See `doc/design-reference.md` §"Body effect". |
| S4 | peaking ≤ 0.2 dB. **Held verbatim.** | Nothing. Implementation note: `lab.raw.peaking_db` scores one-sided (`max(0, …)`) over f ≤ 1 kHz. |
| S5 | The **40 µVrms goal** and the **0.5–200 Hz band** are held verbatim — an ECG-AFE-level requirement, not a device requirement. The band-limiting rationale is technology-independent (density diverges above fc because gain → 0). | **The baseline is re-measured: 49.98 µVrms** (re-certified 2026-08-12 at 50 pts/decade; 50.18 on the old 10 pts/decade grid — the −0.20 µV is the sweep density, not the circuit). The relative ask is therefore **−20.0 %**. Noise-power apportionment (bias share, flicker share) is process-dependent and has **not** been re-measured here — do not quote the originating campaign's percentages as facts about this design. |
| S6 | Structure held: **filter core only**, measured by a 0 V series source in the DUT's supply pin, bias/reference excluded and report-only. | **Re-ruled to `< 50 nW` at 1.5 V** (= 33.3 nA core) because the spec is stated in watts. The nA→nW shortcut was removed from the code. |
| S7 | All four numbers held: **−40 dB**, **175 mVpp differential**, **50 Hz**, harmonics **2–10**. Held too: "higher fins are an informative profile only", and the balun convention (`ampl` = half of Vpp_diff, because the balun gains are ±0.5). | 175 mVpp against a 1.5 V rail is 11.7 % of the supply, so the swing is *relatively* easier than at a lower rail — but the slew-bound characterisation is **unmeasured here** and must be re-run, not inherited. |
| S8 | ≥ 2 papers from `pdf/`, and the corpus itself (all 10 PDFs are process-agnostic academic work). **Held verbatim.** | Nothing. Settle up front, per experiment, whether a pure cap/Q re-allocation counts as a "technique" — it does not; it is the **control** that must be subtracted before crediting anything. |

---

## Notes on the metric definitions (do not re-derive)

These are the definitions the numbers above mean. Re-implementing them
differently silently changes what "49.98 µVrms" or "346.74°" is.

### IRN — input-referred noise, 0.5–200 Hz

`.noise v(voutp,voutn) vsig dec 50 0.1 1k` → the `inoise_spectrum` vector,
trapezoidally integrated over **0.5–200 Hz** (`lab.metrics.IRN_BAND`,
`lab.raw.integrate_noise`). Implementation detail that is part of the
definition: the integral is a **linear-frequency trapezoid on the power**
(`sqrt(∫ S² df)`) applied to a **log-spaced 50 pts/decade** sweep
(`lab.config.AC_DEC`), with the two
band edges added by interpolating the density in log-frequency so 0.5 Hz and
200 Hz are exact endpoints.

**Band-limiting is part of the definition, not a convenience.** Input-referred density
diverges above the cutoff because the gain goes to zero, so the same trace
integrated to 1 kHz reads milli-volts and means nothing. Never use ngspice's
`noise2` / `inoise_total` plot — that is precisely the whole-band artefact.
Output noise ≠ IRN even in band.

`onoise_uv` (the `onoise_spectrum` integrated over the **full** 0.1 Hz–1 kHz
sweep) is a separate, report-only column; it is not IRN and is not a spec line.

### The balun convention (shared by IRN and THD)

```
vcm  vcm 0 0.25
vsig sig vcm dc 0 ac 1            (or ... sin(0 {ampl} {fin}) ac 1)
evp  vinp vcm sig vcm  0.5
evn  vinn vcm sig vcm -0.5
```

⇒ `vinp − vinn = vsig` **exactly**. Two consequences, both definitional:

1. **`vsig`'s own amplitude IS the differential input amplitude**, so 175 mVpp
   differential means `ampl = 87.5 m` (`lab.metrics.THD_AMPL`).
2. The noise analysis refers to `vsig`, so `inoise_spectrum` is the
   **differential** input-referred density with a 1:1 referral — the same
   definition of "the differential input" that the THD drive uses.

Keep `ac 1` on `vsig` even in the transient deck: without an `ac` spec ngspice
aborts the noise analysis with `doAnalyses: ac input not found`.

### `ph_max_deg` — the S1 biquad-order certificate

"Total phase shift → 360°" is the two-biquad requirement, measured operationally
as **maximum unwrapped phase lag**, because a real response never literally
reaches 360°: parasitic feed-through bends the phase back once the magnitude has
collapsed. The box is anchored at **≥ 330°**; the reference measures **346.74°**.

`lab.raw.ph_max_deg(f, h, floor_db=-100.0)`:

1. take the differential response `h = v(voutp) − v(voutn)` from a
   `ac dec 50 0.1 100k` run, as complex;
2. keep only samples where **\|H\| ≥ −100 dB relative to dc**
   (`lab.metrics.PH_FLOOR_DB`);
3. unwrap the phase over that band and return `−min(φ − φ₀)` — the maximum lag,
   positive.

**Rule 1 — the −100 dB floor.** Below it the response is a parasitic
feed-through plateau, not the filter. On this repo's reference the floor cuts
the scored band at **3162.3 Hz** (`f_scored_hi`). Scoring past it does not
measure the filter's order.

**Rule 2 — the aliasing caveat.** An unwrapper corrects a step by
`round(Δ/360)·360`, so **only steps whose magnitude is below 180° go
uncorrected — and those are exactly the ones that alias**: a true −179° step and
a true +181° step are indistinguishable to the sampler. Inside the feed-through
plateau the sampled phase steps by roughly 180° between 10-pts/decade points,
which is how a magnitude-blind certificate manufactures lags far beyond what a
4-pole/1-zero response can physically produce. The floor exists to keep the
scoring out of that region.

**Rule 3 — the resolvability guard.** `lab.raw.max_phase_step_deg` reports the
worst unwrap-corrected step **inside the scored band** as `ph_step_deg`. A band
whose worst step approaches `lab.metrics.PH_STEP_GUARD_DEG = 150.0` is one
sample away from aliasing and its certificate is untrustworthy **however
comfortably it passes**; the remedy is a denser AC sweep, not a bigger number.
Reference: **46.94°**, comfortably resolved.

> **Harness delta to be aware of.** In this port `ph_step_deg` is a *reported*
> SOFT column, not folded into `ph_max_deg` as a fail-closed NaN. Until that is
> changed, **reading `ph_step_deg` is the analyst's job** on every S1 claim.
> Proposing that change is a procedural edit — propose the diff, don't
> self-apply it.

**The ceiling is ~350°, not 360°.** Pushed through `lab.raw.ph_max_deg` on the
scoring grid, a *mathematically ideal* 4-pole Butterworth returns **350.53°**,
because |H| has already fallen through −100 dB (at 15.9 × fc) while the phase is
still ~9° short of its asymptote. Unfloored, the same response returns
**359.57°**. The reference sits 4° under the floored ceiling, and a cell scoring
**above** ~351° is not "more fourth-order" — it is carrying parasitic lag that
the 4-pole model does not contain.

**A cancellation-style LHP zero caps the achievable lag near 293°** and will
fail S1 while the magnitude response still looks like a clean low-pass. That is
the whole reason the certificate exists: magnitude-only scoring lets an order
defect through. Score `ph_max_deg`, not just `a1000_db`.

**The AC sweep density is part of the definition, and it is `dec = 50`.**
`lab.config.AC_DEC = 50` is what the frozen deck sweeps and what every scorecard
number above was measured on. The 150° guard was calibrated against the older
`dec = 10` grid the reference was first certified on (2026-08-11); at 50
pts/decade the per-sample steps are smaller, so the guard is *weaker* — it never
becomes wrong, but a comfortable `ph_step_deg` is less evidence than it was.
Densifying further moves the certificate: densify for a diagnostic, never to
re-anchor the box to the dense number.

### Power probe — S6, filter core only

The testbench inserts a **0 V series source in the DUT's supply pin**:

```
vdd_meas vdd_top 0 1.5      ; whole-testbench supply  -> idd_total_na (report)
vflt     vdd_top vdd 0      ; filter core only        -> i_core_na, p_core_nw (S6)
xdut ... vdd lpf_core
iref vdd_top vbn 1n         ; bias reference: AHEAD of vflt, therefore excluded
```

`i_core_na = |i(vflt)|·1e9`; `p_core_nw = |i(vflt)|·VDD·1e9`. S6 is one
measurement, not a subtraction. What is excluded and why is spelled out in
`doc/benches.md`.

### THD — S7

Differential **175 mVpp** (`THD_AMPL = 87.5e-3` through the ±0.5 balun) at
**fin = 50 Hz** (`THD_FIN`), harmonics **2–10**, limit **−40 dB**
(`THD_LIMIT_DB`). The transient is **coherent and strobed** —
`lab.deck.tran_thd` runs an exact integer number of points per input cycle
(`ppc = 512`) over an exact integer number of cycles (`cycles = 20`) after
discarding `settle = 8` cycles — so the FFT bins land exactly on the fundamental
(bin 20) and its harmonics (bins `k·20`) with no leakage and no window. The
transient tolerance set is **frozen** (`reltol=1e-5 abstol=1e-15 vntol=1e-9
chgtol=1e-16 method=gear maxord=2`) because THD is tolerance-sensitive and the
reference certificate must be reproducible.

Higher input frequencies characterise the slew-bound profile and are
**informative only** — the spec point is 50 Hz.

### The rest of the scorecard

* `dc_db` = 20·log₁₀\|H\| at the **first AC point (0.1 Hz)**, **absolute**
  (referred to the 1 V drive), not normalised.
* `fc_hz` = the first downward crossing of `dc − 3 dB`, **log-log interpolated**
  between the bracketing samples.
* `peak_db` = `max(0, max(\|H\|/\|H(dc)\|))` in dB over f ≤ 1 kHz — one-sided, so a
  monotone response reads exactly 0.
* `a1000_db` = the dB value at 1 kHz, normalised to dc, by **linear
  interpolation in log-frequency** between samples.
* `c_total_pf` = the design's own drawn capacitance
  `2·c1_a + c2_a + 2·c1_b + c2_b`, not a netlist scrape.
* Every `lab.metrics.evaluate()` call appends one row to `runs/ledger.ndjson`
  with the full scorecard, the deck hash, wall time, the violation list and
  `goal_met`. **The ledger is the episodic memory**; keeper numbers graduate
  into an experiment README.

### Sim economy

Expensive runs (THD transients, corner sweeps, Monte Carlo) execute **only after
the cheap scorecard passes the hard box** — `lab.metrics.gate()` raises `Gated`
otherwise. By default `gate(allow=("irn_uv",))` tolerates an S5 failure, because
S5 is the goal being *worked on*; a design that fails the **shape** (order,
cutoff, flatness, power) is not worth an expensive run at all. Do not bypass it
except to debug the harness itself.

---

## The paper corpus

Cite papers **by handle**, everywhere. Every experiment README's `**Paper` row
must name the handle(s) it draws on; the delivered design must combine **≥ 2**.
`pdf/INDEX.md` is the retrieval entry point — pick by the *innovation* column,
then read only what you need.

| handle | file (in `pdf/`) | innovation (the mechanism, one line) |
|---|---|---|
| `tian2023` | `paper01-A_Low-Noise_and_Low-Power_Multi-Channel_ECG_AFE_Based_on_Orthogonal_Current-Reuse_Amplifier.pdf` | cross-coupled current-cancellation CS-LPF; drain-cross gm scaling at constant bias — the only power-neutral gm multiplier |
| `fvf-2nd` | `paper02-0.6-V_Sub-nW_second-order_lowpass_filters_using_flipped_voltage_followers.pdf` | the FVF's internal two-pole loop used *as* a complete biquad; the **floating differential cap** (2× effective C per farad drawn); orthogonal sizing (I_B↔fc, cap ratio↔Q) |
| `selfcomp-gain` | `paper03-A_1.5_V_5.2_nW_60_dB-DR_Lowpass_Filter_With_Self-Compansated_Gain_in_0.35_m_CMOS_Suitable_for_Biomedical_Applications.pdf` | complementary bulk-effect gains cancel across an n-then-p cascade ⇒ exact 0 dB at zero extra power |
| `ssf-33mhz` | `paper04-A_33_MHz_70_dB-SNR_Super-Source-Follower-Based_Low-Pass_Analog_Filter 1.pdf` | canonical SSF-biquad theory: the local loop collapses output noise toward the input device; **Q set purely by the cap ratio** |
| `follower-63nw` | `paper05-A_63_nW_250_Hz_70_dB-DR_Subthreshold_CMOS_Follower-Based_LPF_for_ECG_Detection.pdf` | CSCP composite input: the signal splits across two series gate junctions ⇒ 2× linear range, gm halved ⇒ C halved at the same fc; gives the slew check `I/C > 2π·fc·Vp` |
| `bulk-neutral` | `paper07-A_Nanopower_Biopotential_Lowpass_Filter_Using_Subthreshold_Current-Reuse_Biquads_With_Bulk_Effect_Self-Neutralization.pdf` | all bulks to the rails ⇒ every gms = I_B/U_T; the noise bookkeeping `∝ kT/C₂·S(Q)`, **independent of I_B**; HD3 ∝ (1+LG)³ |
| `buffer-biquad` | `paper08-A_Subthreshold_Buffer-Based_Biquadratic_Cell_and_its_Application_to_Biopotential_Filter_Design.pdf` | 3T current-reuse buffer biquad: gate-driven pair + shared-branch CS device in global unity feedback, gm ≈ gms/3 ⇒ ~3× less C at the same fc. Its buried line — *"current sources dominate its noise → degenerate them"* — is the one that points at this DUT's real budget |
| `gmc-compact` | `paper06-A_compact_subthreshold_CMOS_2nd-order_gm-C_lowpass_filter.pdf` | 7T biquad: global unity feedback linearizes the passband; **two gm's stacked in ONE bias branch** (2× gm at zero added current) |
| `gmc-4p6nw` | `paper10-Electronics Letters - 2025 - Huang - A 4 6‐nW  100‐Hz  63 88‐dB DR  Second‐Order Subthreshold Gm‐C Filter for Portable.pdf` | SCP replaces the follower + **self-cascode composites** (bottom device in subthreshold triode as free local degeneration); HD3 → λ²Vm²/8 |
| `biodevices` | `paper09-biodevices.pdf` | six identical 5T follower-integrators (gate-driven pair, unity feedback): feedback beats linearization; gate-drive slew margin `A/(2·n·U_T)` vs a follower's `A/V_T` ⇒ 3–4× more headroom per nA |

**Triage rule.** Fill a row's "content / innovation" with ONE line — the
mechanism, not the abstract. "usable here for" says what it could buy on *this*
filter toward IRN / THD / power — **or "nothing, because …"**. A ruled-out paper
is a result too. Keep this table and `pdf/INDEX.md` in sync when files are added.

**Carry-forward warning on `pdf/INDEX.md`.** The classified inventory of what carries
and what does not is [prior-findings.md](prior-findings.md). Several of the
index's cells record
verdicts measured in the originating campaign, on another technology at another
supply — including the claims that `selfcomp-gain` is void on this DUT, that the
`ssf-33mhz` input-device noise floor does not hold, and that the `gmc-4p6nw`
self-cascode is not a noise lever. The *mechanisms* transfer; the *percentages
and verdicts do not* until they are re-measured here. Treat every such cell as a
hypothesis with a citation, not as a measurement of this repo.
