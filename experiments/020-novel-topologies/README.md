# 020 — porting the three signed-off candidate topologies to SG13G2

**Status: OPEN. 020A ported and measured; 020B/020C blocked on one structural
collision, isolated and characterised below.**

| | |
|---|---|
| **Paper(s)** | carried forward: branch stacking (`gmc-compact` + `tian2023`), the gm_f merge (originating campaign, new), cap/Q re-allocation (`ssf-33mhz`) |
| **Hypothesis** | The three signed-off candidate topologies are technology-independent — their mechanism is *which devices carry signal instead of only bias*, not any property of the silicon — so each should port to SG13G2, re-size, and keep its win over the reference baseline. Falsified if a mechanism turns out to depend on a device property this PDK does not have. |
| **Verdict so far** | **PARTIALLY FALSIFIED, with the dependency identified.** The noise mechanism ports and is confirmed (020A reaches **IRN 37.57 µVrms**, under the 40 µV goal, at 7.77 nW). The *dc ladder* does not: branch stacking structurally requires an n-type input follower, and in a PDK with no isolated NMOS that follower costs exactly 1/n of passband gain — measured **−3.11 dB** against an S3 box of ±0.2 dB. |

## 1. The result that matters

The mechanism the whole family rests on — *delete the pure-bias devices from the
noise ledger by making every remaining ampere do signal work* — **is real and it
ports**. On the faithful 020A redraw, at its natural supply:

| | reference baseline | **020A (ported, unretuned)** |
|---|---|---|
| IRN 0.5–200 Hz | 50.18 µVrms | **37.57 µVrms** (−25.1 %) |
| filter-core power | 12.07 nW | **7.77 nW** (−35.6 %) |
| total drawn C | 98.01 pF | 101.3 pF |
| \|H\| at 1 kHz | −48.43 dB | −47.97 dB |

That is the challenge goal (< 40 µVrms) met on the noise axis, at lower power,
on the very first sizing point — before any tuning. Ledger tag `A_vdd1`.

It is **not** a deliverable, because two shape lines fail (§2): S3 at −3.12 dB
and S1 at 318.5°, and fc sits at 210.6 Hz. Reporting the noise number without
those is exactly the failure mode the originating campaign's own sign-off rule
exists to prevent, so it is stated here as a *mechanism confirmation*, not a
cell.

## 2. The collision — measured, not argued

Branch stacking puts both input followers in ONE dc branch, so the same ampere
does the gm work of both. The ladder descends monotonically:

```
vdd -> bias_b_out -> voutp -> in_b(p) -> net4 -> bridge(p) -> net2
     -> in_a(n) -> vout_1 -> bias_a_out -> gnd
```

It closes **only** if the two followers have opposite polarity — the n-type
follower's source sits below its gate and the p-type follower's above it. That
is what lets the levels descend at all.

But this PDK has no deep-n-well NMOS, so an n-type follower's bulk is the shared
substrate, and a gate-driven follower with bulk at the rail has dc gain exactly
**1/n** in weak inversion (gmb = (n−1)·gm; n ≈ 1.38 here). Measured on the
ported 020A, stage by stage:

| stage | follower | dc gain |
|---|---|---|
| A | n-type, bulk at substrate | **−3.111 dB** |
| B | p-type, bulk at its source | **−0.007 dB** |

So: **the mechanism needs the n-follower; the spec forbids it.** The reference
baseline escapes by making both stages p-type ([000](../000-reference-baseline/)),
but that route is closed here — with both followers p-type the two internal
nodes sit at the same low level and there is no voltage across a bridge placed
between them.

### 2.1 The all-p re-derivation, and why it fails

The obvious repair is to move the stack up one node: bridge from biquad B's
internal node into biquad A's *output* rather than its internal node,

```
vdd -> gmf_b(p, merged) -> voutp -> in_b(p) -> net4 -> bridge(p) -> vout_1
     -> in_a(p) -> net2 -> bias_a_int(n) -> gnd
```

which descends correctly with every follower p-type. It was built and measured.
**It does not work, for a reason worth recording:** a common-gate bridge presents
its *source* as a low-impedance node (1/gm) and its *drain* as a high-impedance
one (ro). Moving the drain onto `vout_1` puts a high-impedance node where the
topology needs a follower's low-impedance output, and the biquad pair
degenerates — ph_max collapses to 254–266° across the whole sizing scan (16
points, `scanB_*`), against the ≥ 330° certificate.

This also isolates the merge's second technology dependence. With both the
bridge and the merged gm_f p-type, the ladder current solves
`|Vgs|(gmf_b) + |Vgs|(bridge) = VDD`, so at VDD = 1.5 V both devices must sit
~0.29 V further up their exponentials than a 1 nA device wants to — 7.3 e-folds,
i.e. ~1500× less W/L each. Sizing gmf_b moves the entire ladder **exponentially**,
which the scan shows plainly: core current runs 7.76 → 1.12 nA across a 6.7×
change in one device length.

### 2.2 The supply is not free either

For the stacked family VDD is *determined*, not chosen:
`VDD = Vgs(gmf_b) + |Vgs|(gmf_a) − Vsd(bridge)`. Swept over 0.9–1.5 V, the
faithful 020A ladder closes cleanly at **VDD ≈ 1.0 V** (voutp 0.778 / net4 0.566 /
net2 0.308 / vout_1 0.242 V, I = 7.77 nA) and lands in a degenerate basin at
1.2–1.3 V and rails at 1.5 V. The reference baseline needs the *opposite*:
its all-p signal path costs an extra |Vgs| of headroom and needs VDD ≈ 1.5 V.

Because S6 is stated in watts, each cell is scored at its own natural supply and
both sit far inside the 50 nW box. That is recorded here explicitly so nobody
later reads the two supplies as an inconsistency.

## 3. What the three cells are (topology, carried forward verbatim)

Implemented as parameterised builders in [`lab/dut.py`](../../lab/dut.py) —
`build_a`, `build_b`, `build_c` — so a sizing point is a `Design`, never a text
edit. Starting geometries in [`sizes.py`](sizes.py), carried over as a starting
point only.

| cell | mechanism vs the reference |
|---|---|
| **020A** | branch stacking: both followers in one dc branch through a common-gate bridge; **both internal-node bias pairs deleted** (4 of 8 bias devices leave the noise ledger) |
| **020B** | 020A **+ the gm_f merge**: biquad B's output bias source has its gate re-wired from the bias rail to biquad B's own internal node, so one device is bias source *and* shunt-feedback transconductor, and the separate gm_f pair is deleted |
| **020C** | 020B re-allocated under a total-capacitance ruling: smaller gm_f puts the same pole on less capacitance, trading noise margin for die area and power |

## 4. Next steps, ranked

1. **Restore the n-follower's gain.** This is now the one open design problem,
   and the corpus already contains the answer class: `bulk-neutral` and
   `selfcomp-gain` are the two papers about *bulk-effect gain cancellation*.
   Both were filed as "moot" by the originating campaign **because its
   technology tied every bulk to its source** — the exact assumption this PDK
   removes. They should be re-read against this problem first; see
   [pdf/INDEX.md](../../pdf/INDEX.md).
2. **Re-size 020A to the full box** once (1) lands: fc 210.6 → 250 Hz and the S1
   certificate (318.5° → ≥ 330°) are ordinary cap-allocation work,
   `lab.shape.fit_caps` does it, and neither should cost the 37.57 µV.
3. **Then 020B/020C**, which inherit (1) and additionally need the ladder's
   exponential self-bias re-referenced — which is also the originating
   campaign's own next step for these two cells (drive the bridge gate from a
   corner-tracking replica rather than from a rail).
4. **THD and corners** are gated behind the shape box by `lab.metrics.gate` and
   have deliberately not been run.

## 5. Files

- `sizes.py` — starting sizing points for all three
- `../../lab/dut.py` — the topologies themselves
- ledger tags: `020A_v0`, `A_vdd1`, `020B_allp`, `020C_allp`, `scanB_*`,
  `lad_*` (query with `python scripts/runs.py`)
