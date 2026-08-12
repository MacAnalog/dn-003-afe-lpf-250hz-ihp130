# Experiment log

**KIND: TODO/log.** One line per experiment, **newest last**. Details live in
each experiment's `README.md`; keep this table honest the moment a verdict
lands. Every `experiments/NNN-*` directory must appear here.

Goal: **IRN(0.5–200 Hz) < 40 µVrms** from the certified reference baseline's
**50.18 µVrms** (−20.3 %), combining techniques from **≥ 2 papers** in `pdf/`,
while holding two true biquads, 250 Hz ±2 %, |dc| ≤ 0.2 dB, peaking ≤ 0.2 dB,
THD ≤ −40 dB at 175 mVpp / 50 Hz, and filter-core power < 50 nW.

| # | technique | paper(s) | verdict | IRN 0.5–200 Hz | C total |
|---|---|---|---|---|---|
| `000-reference-baseline` | expert topology ported and re-sized to spec; both input followers p-type; one ideal reference current into a real n/p mirror | — | **CLOSED — certified reference**; this is the yardstick every candidate is scored against | **50.18 µV** | **98.01 pF** |
| [`020-novel-topologies`](../experiments/020-novel-topologies/) | port the three signed-off candidate topologies (branch stacking, the gm_f merge, the merge under a capacitance ruling) | carried forward: `gmc-compact`+`tian2023`, `ssf-33mhz` | **IN PROGRESS — mechanism CONFIRMED, dc ladder PARTIALLY FALSIFIED.** 020A ported reaches **IRN 37.57 µV at 7.77 nW** (goal met on the noise axis, unretuned) but fails S3 at −3.12 dB and S1 at 318.5°: branch stacking needs an n-type input follower, and with no isolated NMOS that follower costs exactly 1/n of gain. The all-p re-derivation was built and **falsified** — a common-gate bridge's high-Z drain lands on a node that must be low-Z, and ph_max collapses to 254–266° across a 16-point scan. Next: restore the n-follower's gain (`bulk-neutral` / `selfcomp-gain` are re-opened by this PDK) | **37.57 µV** (020A, shape unmet) | 101.3 pF |

---

## 000 — the certified reference baseline (CLOSED)

Frozen in `decks/reference/` (`lpf_core.sp`, `lpf_tb.sp`, `design.json`,
`build-sheet.md`). It plays the role the originating campaign's reference
design played: **every candidate is scored against it, in the same batch, with
the same deck builder.**

| metric | measured | spec line |
|---|---|---|
| fc | **250.00 Hz** | S2: 250 Hz ±2 % (245–255) |
| passband gain (dc) | **−0.0047 dB** | S3: \|dc\| ≤ 0.2 dB |
| peaking | **0.023 dB** | S4: ≤ 0.2 dB |
| \|H\| at 1 kHz | **−48.43 dB** | S1 companion: ≤ −48 dB |
| ph_max (S1 order certificate) | **346.43°** | S1: ≥ 330° |
| **IRN 0.5–200 Hz** | **50.18 µVrms** | S5 goal: < 40 µV — **the number to beat** |
| core current | **8.04 nA** | — |
| core power | **12.07 nW** @ 1.5 V | S6: < 50 nW (4× headroom) |
| total drawn C | **98.01 pF** | reported, never specced |
| device count | 16 transistors + 6 capacitors | — |

Capacitors (pF): `c1_a 29.468` · `c2_a 6.221` · `c1_b 11.453` · `c2_b 9.946`.

Two properties of the measurement worth keeping in mind before quoting it:

- **−48.43 dB at 1 kHz against a 4th-order Butterworth arithmetic of −48.16 dB**
  — the shape is Butterworth to within 0.27 dB, so the S1 companion is not
  slack: there is 0.43 dB between the reference and the box, and any technique
  that trades stopband away will hit it first.
- **ph_max 346.43° against a 330° box** — 16.4° of margin. A single forward-path
  LHP zero caps the achievable lag well below 330°, so `ph_max` is the metric
  that catches an order defect a magnitude-only scorecard would pass.
- **Bias:** one ideal reference current into a *real* n/p mirror; every bias
  device is an integer multiple of that unit (per side, 2 units at each biquad
  output ⇒ 8 nA total). The reference sits ahead of the core supply probe, so
  it is excluded from S6 by construction, not by subtraction.

## 020 — topology port: all-p input followers (IN PROGRESS)

The one structural change against the originating design, and it is forced by
the process, not chosen.

SG13G2 has **no deep-n-well / isolated NMOS**, so an n-channel device's bulk is
the shared p-substrate and cannot follow its source. In weak inversion a
gate-driven source follower with its bulk at the rail has dc gain exactly `1/n`
(`gmb = (n−1)·gm`), and n = 1.38 for these devices (`doc/pdk-notes.md` §2.1).

Measured here on the alternating n/p structure the originating design used:

| stage | input follower | bulk | measured dc gain |
|---|---|---|---|
| A | n-type | shared p-substrate (forced) | **−2.328 dB** |
| B | p-type | its own source | **−0.003 dB** |

The n-stage alone overruns S3 (|dc| ≤ 0.2 dB) by **more than 10×**, and **no
re-sizing recovers it** — `1/n` is set by the process. Making both stages
p-type restores exact unity gain and preserves the **self-referenced gain** the
follower family's mismatch yield depends on (`doc/prior-findings.md` §4). Cost:
the common mode climbs one |Vgs| per stage instead of cancelling, absorbed by
placing the input CM at 0.25 V so the output lands at ~1.25 V mid-supply.

**Open in 020:** the transferable-learning write-up
(`doc/journal/nmos-bulk-tie.md`, `doc/journal/all-p-followers.md`), and a full
4th-order scorecard of the alternating structure as the negative control (so
the decision is on the record as a measurement, not as an argument).

---

## Queue — what is open

Ordered by expected value per simulation, not by number.

1. **Where is the noise?** A per-device noise breakdown of the reference
   baseline, integrated over 0.5–200 Hz, plus the thermal/flicker split. The
   originating campaign found 61.7 % of noise *power* in the eight bias
   sources and only 5.3 % in flicker — **both numbers are technology-bound and
   must be re-measured here before any technique is chosen**
   (`doc/prior-findings.md` §2). Until this exists, every candidate technique
   is aimed blind.
2. **The technique-free control curve.** The I–C homothety (scale every device
   multiplier *and* every capacitor by k) predicts `IRN ∝ 1/√k` exactly, at
   invariant fc/Q/dc/THD, with power ∝ k. At 12.07 nW against a 50 nW box
   there is **k ≈ 4 of headroom**, which alone would put IRN at ~25 µV. This
   must be measured and published as the control **before** any technique is
   credited — a technique's result is its distance from this curve, not its
   distance from the baseline.
3. **Cap/Q re-allocation control.** Silicon cost per biquad is `2·C1 + C2`, so
   the high-Q pole pair belongs on the biquad with the larger `gm_i`. Pure
   re-allocation, no circuit change. Must be run as a control for every
   experiment, and — open ruling — **does re-allocation ∘ homothety count
   toward the "≥ 2 papers" requirement?** Settle this before a candidate is
   delivered, not after.
4. **Bias-source degeneration with a real resistor** (`rhigh`). Only a genuine
   resistor removes a subthreshold source's shot noise; `R > 2·V_T/I` at 1 nA
   is tens of MΩ, so this is an area question as much as a noise one.
5. **S7 (THD) has never been measured on this reference.** The scorecard rows
   above are ac + noise only. Run it before any technique that touches swing,
   caps or bias — and re-measure **HD2** while there, because "THD ≈ HD3" is a
   carried-forward property of a different differential layout, not a law
   (`doc/prior-findings.md` §6).
6. **Corners and mismatch.** Five MOS corner sections exist (`mos_tt/ss/ff/sf/fs`).
   The mismatch lane does not exist yet; when it is built, the **first** action
   is to prove the samples actually differ — a dead mismatch lane returns
   bit-identical samples and every yield number it prints is a lie
   (`doc/prior-findings.md` §5).

**Ruled out, deliberately not queued:** see `doc/prior-findings.md` §3 — but
note that list is carried forward from a different technology and a 1 V rail.
Anything whose stated blocker was headroom is **re-opened here at 1.5 V**, and
anything whose blocker was bulk-tied-to-source is re-opened because this
process cannot tie an n-channel bulk to its source at all.
