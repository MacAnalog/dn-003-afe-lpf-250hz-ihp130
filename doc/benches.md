# Benches — the measurement contract

**KIND: REFERENCE.** Every number in [target-spec.md](target-spec.md) means
whatever *this* bench measures. Read this before measuring anything, and before
believing a measurement someone else made.

**Reference-first policy.** The frozen deck in `decks/reference/` is the
canonical measurement definition. The `lab/` harness exists for *speed*: fast
metrics iterate, the frozen reference deck certifies. Every fast metric must map
to a statement in this document; a fast substitute that cannot be mapped is not
a measurement, it is a guess.

---

## 1. What the testbench is

**Decks are BUILT, never text-edited.** `lab.deck` takes a `lab.dut.Design`
(device geometries + capacitor values) plus an analysis and emits a complete
runnable deck. A sizing sweep changes the `Design`; every deck in the run — ac,
noise, THD, corner — is regenerated from it. That is what makes it impossible to
score a netlist from one sizing point with a measurement from another.

The whole bench, in emission order (`lab.deck.ac_noise`):

```
.title  lpf reference -- ac + noise
.lib cornerMOShv.lib mos_tt              ; lab.config.MOS_LIB_HV, CORNER_NOM

.subckt lpf_core vinp vinn voutp voutn vbn vbp vdd
  ... 16 devices + 6 capacitors ...      ; lab.dut.subckt(design)
.ends lpf_core

vdd_meas vdd_top 0 1.5                   ; whole-testbench supply   (report-only)
vflt     vdd_top vdd 0                   ; FILTER-CORE probe        (S6)
xdut vinp vinn voutp voutn vbn vbp vdd lpf_core
.nodeset v(xdut.vout_1)=1.25 v(xdut.vout_2)=1.25 v(voutp)=1.25 v(voutn)=1.25

iref  vdd_top vbn 1e-09                  ; the reference: AHEAD of vflt
xmbn  vbn vbn 0 0        sg13_hv_nmos w=5u l=8u  ng=1 m=1
xmbp  vbp vbn 0 0        sg13_hv_nmos w=5u l=8u  ng=1 m=1
xmbpd vbp vbp vdd_top vdd_top sg13_hv_pmos w=5u l=12u ng=1 m=1

vcm  vcm 0 0.25                          ; input common mode
vsig sig vcm dc 0 ac 1                   ; THE differential source == the iprobe
evp  vinp vcm sig vcm  0.5               ; balun +
evn  vinn vcm sig vcm -0.5               ; balun -
.temp 27.0
```

Net and role detail is in [design-reference.md](design-reference.md); the
config constants are `lab.config` (`VDD`, `VICM`, `VOCM`, `IN_SRC`,
`CORE_PROBE`, `SUPPLY_PROBE`, `OUT_P`/`OUT_N`, `CORNER_NOM`, `TEMP_NOM`).

---

## 2. The balun — why `vsig`'s amplitude *is* the differential input

```
evp vinp vcm sig vcm  0.5
evn vinn vcm sig vcm -0.5     ⇒   vinp − vinn = vsig   exactly
```

Both controlled sources are referenced to the common-mode node `vcm`, with gains
that sum to 1 and difference to 0. So the pair injects `vsig` **purely
differentially** on top of a common mode that `vsig` does not move at all.

Three consequences, all definitional rather than incidental:

1. **Amplitude.** `vsig`'s own amplitude is the differential amplitude. The S7
   drive of **175 mVpp differential** is therefore `ampl = 87.5 m`
   (`lab.metrics.THD_AMPL = 87.5e-3`) — *not* 175 m, and *not* 43.75 m.
2. **Noise referral.** The noise analysis names `vsig` as its input source, so
   `inoise_spectrum` is the **differential** input-referred density with a 1:1
   referral. There is no gain de-embedding step and no place for one to go
   wrong. Output noise is a different quantity (`onoise_uv`, report-only) and is
   *not* IRN even inside the band, because the filter's gain is already well
   below 1 at 200 Hz.
3. **One definition of "the differential input"** is shared by S5 and S7. The
   noise referral and the distortion drive cannot drift apart.

**`ac 1` must stay on `vsig` in every deck**, including the transient ones: an
input source with no `ac` spec makes ngspice abort the noise analysis with
`doAnalyses: ac input not found`.

**The common mode is set once, at `vcm` = `lab.config.VICM` = 0.25 V**, and both
balun sources hang off it. Never introduce a second CM definition; the p-type
follower ladder (§design-reference §4.2) depends on this one.

---

## 3. The series core probe — why S6 is one measurement, not a subtraction

```
vdd_meas vdd_top 0 1.5      ; the real supply source
vflt     vdd_top vdd 0      ; 0 V series source: everything downstream is the CORE
xdut ... vdd lpf_core       ; the DUT's supply pin is on the DOWNSTREAM node
iref vdd_top vbn 1e-09      ; the reference hangs off the UPSTREAM node
xmbpd vbp vbp vdd_top vdd_top ...
```

`vflt` is a zero-volt source, so it perturbs nothing and reads a branch current
directly. Everything that draws through it is the filter core and nothing else.

```
i_core_na    = |i(vflt)|     * 1e9
p_core_nw    = |i(vflt)| * VDD * 1e9      <- S6
idd_total_na = |i(vdd_meas)| * 1e9        <- report-only
```

`lab.metrics.score_plots` reads both out of the `op` plot. Take `abs()`: a
voltage source's branch current is positive into its `+` node.

**MEASURED, reference baseline:** core **8.043 nA / 12.07 nW**, whole bench
**10.049 nA**. The 2.006 nA difference is the reference current plus its mirror
leg.

**Never re-introduce the shortcut "core current in nA equals core power in nW".**
That identity holds only at a 1 V rail. The conversion is explicit
(`i_core * config.VDD * 1e9`) precisely so a supply change cannot silently
under-report power by 1.5×.

### What is excluded from S6, and why

Excluded: **`iref` and the three mirror devices** (`xmbn`, `xmbp`, `xmbpd`) —
2.006 nA of the 10.049 nA total.

* **The spec says so.** S6 is a *filter-core* budget. A bias reference is a
  shared block, amortised across channels and shared with everything else on the
  die; charging one filter for a whole reference measures the reference, not the
  filter.
* **It keeps the comparison honest.** The reference here is deliberately
  **ideal** — one current source into a real mirror. If it were a real
  beta-multiplier, a candidate could "win" by having a cheaper reference while
  its actual filter got worse. Holding the reference fixed and ideal means a
  scorecard difference is a *filter* difference.
* **The mirror stays real.** Only the current source is ideal. The two diode
  devices are built from the design's **own** `bias_*_int` / `bias_*_out`
  geometry at `m = 1`, so a DUT bias device drawn at `m = k` carries exactly
  `k · iref`. An arbitrary diode geometry rescales every branch current by a W/L
  ratio: the internal node rails, the shunt-feedback device switches off, and the
  ac response still looks like a plausible (if mis-tuned) low-pass. That failure
  mode passes every eyeball test — see `doc/journal/mirror-unit-must-match.md`.

What is **not** excluded: the eight in-DUT bias devices. They are part of the
filter, they are a large share of its noise, and idealising them would destroy
comparability with the baseline.

---

## 4. The analyses, exactly

### 4.1 Scorecard deck — `lab.deck.ac_noise` (op + ac + noise, one run, one rawfile)

```
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec 10 0.1 100k
write sim.raw
noise v(voutp,voutn) vsig dec 10 0.1 1k
setplot noise1
write sim.raw
.endc
```

| setting | value | why it is not a free choice |
|---|---|---|
| ac sweep | **0.1 Hz → 100 kHz, `dec 10`** | The `dec 10` grid is what the S1 phase certificate and its 150° resolvability guard are calibrated against. Densifying moves the certificate; do it for a diagnostic, never to re-anchor the box. The 0.1 Hz start point *is* the definition of `dc_db`. The 100 kHz stop is what lets the −100 dB floor find the feed-through plateau. |
| noise sweep | **0.1 Hz → 1 kHz, `dec 10`**, output `v(voutp,voutn)`, input `vsig` | The output is differential and the input is the balun source, so `inoise_spectrum` is the differential IRN density directly. The 0.5–200 Hz integration band is applied afterwards, in Python. |
| op | before both | supplies `i(vflt)` and `i(vdd_meas)` for S6. |
| `.temp` | 27.0 | `lab.config.TEMP_NOM`. |
| corner | `.lib cornerMOShv.lib mos_tt` | `lab.config.CORNER_NOM`; the other sections are `mos_ss`, `mos_ff`, `mos_sf`, `mos_fs`. |

### 4.2 Operating point — `lab.deck.op_only`

Same bench, `op` only, plus `print` of device-parameter expressions. Addressing
is `@n.<inst>.n<model>[param]`, e.g. `@n.xdut.xm2.nsg13_hv_pmos[gm]`. A device
parameter **must appear in a `save` before a sweep** or it reads back as a
constant. This is the tool for sizing and for the weak-inversion audit
(`gm/ID` near the measured limit, `Vds` above ≈ 4·kT/q on every bias device).

### 4.3 Distortion — `lab.deck.tran_thd`

Coherent, strobed, unwindowed:

```
tran {tper/ppc} {(settle+cycles)*tper} {settle*tper} {tper/ppc}
.options reltol=1e-5 abstol=1e-15 vntol=1e-9 chgtol=1e-16 method=gear maxord=2
```

with `ppc = 512` points per input cycle, `cycles = 20` scored cycles, `settle =
8` discarded cycles, `tper = 1/fin`. The fourth `tran` argument bounds the
internal step so the output grid really is uniform.

* **Coherence is the point.** An exact integer number of points per cycle over an
  exact integer number of cycles puts the fundamental in FFT bin `cycles` (= 20)
  and harmonic *k* in bin `k·20`. No leakage, no window, no correction factor.
  S7 counts harmonics **2–10**.
* **The tolerance set is FROZEN**, not tuned per run. THD is tolerance-sensitive,
  and a certificate that moves when someone loosens `reltol` is not a
  certificate. If it ever has to change, the reference's THD must be re-measured
  and re-frozen in the same commit.
* **Drive:** `lab.deck._stim_sine(fin, ampl)` puts `sin(0 {ampl} {fin})` on
  `vsig` and keeps `ac 1`. The S7 point is `ampl = 87.5 m`, `fin = 50 Hz`.

**Open gap:** the deck exists; the analysis/scoring helper does **not**. S7 has
no measured value for the reference baseline yet. See target-spec §"S7 gap".

### 4.4 Supply droop — `lab.deck.vdd_sweep`

`dc vdd_meas lo hi step`, dc-hints disabled. Report-only; it characterises
VDD_min for a datasheet, it is not a spec line.

---

## 5. ngspice mechanics that are part of the contract

These are not style preferences. Each one, done differently, produces a
plausible-looking wrong number.

1. **`write` emits only the CURRENT plot.** A multi-analysis deck needs
   `set appendwrite` plus **one `write` per analysis**. Plot names are
   deterministic only when each analysis runs **once** — a `while`/`repeat` loop
   that re-runs `op` renumbers the plots, and `setplot noise1` then silently
   addresses the wrong one.
2. **`setplot noise1` is mandatory to reach the noise SPECTRUM.** The `noise`
   command leaves the *integrated* plot current. Integrate the 0.5–200 Hz band
   yourself (`lab.raw.integrate_noise`); ngspice's own integral covers the whole
   sweep, which is exactly the diverging-density artefact S5's band limit exists
   to avoid.
3. **An explicit `save` list STARVES the noise analysis.** ngspice prints
   `Error: no data saved for Noise analysis; analysis not run`, then leaves the
   previous plot current — so the rawfile silently contains the **ac plot
   twice** and the scorecard reads NaN for S5 instead of failing loudly. The
   ac+noise deck therefore does **not** restrict its saves. Only the transient
   deck does, where the ~750 PSP103 internal nodes *per device* genuinely
   dominate the file size (`lab.deck.SIGNAL_NETS` and the comment above it).
4. **`.nodeset` on a node inside a subckt must be instance-qualified** —
   `v(xdut.vout_1)`, not `v(vout_1)`. An unqualified name yields only
   `Warning : Nodeset on non-existent node` and is a **silent no-op**.
5. **Use `.nodeset`, never `.ic`.** A nodeset is a hint the dc solver may leave;
   an `.ic` is a clamp held *through* the operating point, and it lands this
   circuit in a latched basin that scores as a valid pass.
   See `doc/journal/nodeset-not-ic.md`.
6. **The input source needs `ac 1`** or the noise analysis aborts (§2).
7. **Bias mirror diodes must use the design's own unit geometry at `m = 1`**
   (§3).
8. **ngspice returns exit code 0 after a failed dc operating point**, leaving a
   rawfile full of zeros. `lab.ngspice` therefore scans stdout for fatal strings
   and raises `SimError`. **A silent zero-filled result that scores as a PASS is
   the single most expensive failure mode in this harness** — never soften that
   check.
9. **The PDK needs OSDI.** IHP MOS devices *are* PSP 103.6 Verilog-A compact
   models loaded as `.osdi` objects; a stock ngspice reports
   `Unknown model type psp103va` and cannot simulate this PDK at all. Default
   lane is the Docker image `spicexplorer-spice-base:local`; the native lane
   needs `LPF_NGSPICE` pointing at an ngspice whose `~/.spiceinit` loads those
   objects (`lab.config.lane`).

---

## 6. Metric ↔ statement map

Every fast metric, and the bench statement it is defined against. This table is
the "originals-first" referent: if a metric cannot be pointed at a row here, it
is not a measurement.

| metric | bench statement | Python | definition |
|---|---|---|---|
| `dc_db` | `ac dec 10 0.1 100k`, first point | `R.db(h)[0]` | 20·log₁₀\|H\| at **0.1 Hz**, **absolute** (vs the 1 V drive), not normalised |
| `fc_hz` | same sweep | `R.f3db` | first downward crossing of dc − 3 dB, **log-log interpolated** between bracketing samples |
| `peak_db` | same sweep, f ≤ 1 kHz | `R.peaking_db` | `max(0, max \|H\|/\|H(dc)\|)` in dB — one-sided, so a monotone response reads exactly 0 |
| `a1000_db` | same sweep | `R.value_at(f, y, 1000)` | dB relative to dc at 1 kHz, **linearly interpolated in log-frequency** |
| `ph_max_deg` | same sweep, `v(voutp)−v(voutn)` complex | `R.ph_max_deg(..., PH_FLOOR_DB)` | max unwrapped **lag**, scored only where \|H\| ≥ **−100 dB** rel. dc |
| `ph_step_deg` | same | `R.max_phase_step_deg` | worst unwrap-corrected step inside the scored band; guard 150° |
| `f_scored_hi` | same | `f[y >= PH_FLOOR_DB][-1]` | top of the scored band — reference **3162.3 Hz** |
| `irn_uv` | `noise ... vsig dec 10 0.1 1k`, `noise1` | `R.integrate_noise(f, inoise, 0.5, 200)` | trapezoid on the **power** over **0.5–200 Hz**, band edges interpolated exactly |
| `onoise_uv` | same plot | `R.integrate_noise(f, onoise, 0.1, 1e3)` | output noise over the **full** sweep — report-only, **not** IRN |
| `i_core_na`, `p_core_nw` | `op`, `i(vflt)` | `abs(...)`, `× VDD` | S6, filter core only |
| `idd_total_na` | `op`, `i(vdd_meas)` | `abs(...)` | whole bench — report-only |
| `c_total_pf` | — | `Design.total_cap()` | `2·c1_a + c2_a + 2·c1_b + c2_b`, from the design, not a netlist scrape |
| THD | `lab.deck.tran_thd`, coherent FFT | **helper not written** | harmonics 2–10 of the strobed transient at 175 mVpp / 50 Hz |

---

## 7. Reference-first policy in practice

* **The frozen deck certifies.** `decks/reference/lpf_tb.sp` + `lpf_core.sp` +
  `design.json` + `build-sheet.md` are the reference baseline as built. Do not
  edit them to make a comparison come out; regenerate them from the `Design` and
  say so in the commit.
* **Fast metrics iterate.** `lab.metrics.evaluate()` is cheap (sub-second per
  point) and every call auto-records a ledger row keyed by the deck hash. A
  sizing sweep lives entirely here.
* **Sim economy is enforced, not advised.** `lab.metrics.gate()` refuses an
  expensive run (THD transient, corner set, Monte Carlo) unless the cheap
  scorecard passes the **hard box** — order, cutoff, flatness, power. By default
  it tolerates an S5 failure, because S5 is the goal being worked on. Do not
  bypass it except to debug the harness itself.
* **A candidate is only delivered when it is measured on this bench.** The DUT
  subckt is the only thing that may differ between a reference run and a
  candidate run: same balun, same reference current, same mirror unit rule, same
  probes, same analyses, same corner, same temperature. If anything else moved,
  the comparison is not a comparison.
* **Findings are tables or plots.** `lab.metrics.table()` produces the findings
  table; prose is interpretation only. Keeper numbers graduate from
  `runs/ledger.ndjson` into the experiment README — the repo is the memory.
