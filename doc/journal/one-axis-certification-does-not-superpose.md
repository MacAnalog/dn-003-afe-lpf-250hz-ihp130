# 2026-08-28 — A one-axis-at-a-time corner claim is not a box, and the analytical quantities say so first

KIND: journal entry | type: semantic | status: live

**The claim under test.** `signoff/post-pvt/README.md` certifies `H12-pdk-cap` as
process at 27 °C/1.5 V, supply **1.40–1.65 V at 27 °C**, temperature **0…+70 °C at
1.5 V**. That is `lab.corners.AXES` in shape: one axis moves at a time. It is easy
to read such a table as an operating BOX. It is not one.

**Measured.** Re-deriving the poles, the per-biquad `Q` and the noise budget at
every point (`signoff/paper-draft/scripts/pvt_analysis.py`, over
`extract_bench.py --pvt`) gives, on the nine certified points:

* `fc` span **1.022×**, `Q` span **1.002×** and **1.027×**, pair-coincidence ratio
  **1.023×**, and both complex pole pairs present at **9/9** points.

On the 45-point CROSS PRODUCT of the same endpoints — never certified — **7 points
lose a complex pole pair entirely**, i.e. the cell stops being two biquads:
`tt_0c_1v400`, `ss_0c_1v400`, `ss_0c_1v500`, `ss_27c_1v400`, `ff_70c_1v650`,
`sf_70c_1v650`, `fs_0c_1v400`. The first of those is nominal process at 0 °C on
1.40 V — **three coordinates that are each individually inside the certified
window** — and it lands at `ph_max` 270.2° against a 330° line, `fc` 225.5 Hz.

**Why the axes interact.** Experiment 023's headroom identity: the ladder window is
`min(V_SG(gmf_b), V_SG(in_b)) − 2·Vds_min` against `VDD − vicm`, and it drifts
~1.5 mV/K at fixed `vicm`. Cold grows every `|V_SG|` while a low rail shrinks the
budget they must fit in, so temperature and supply squeeze the SAME window. One-axis
sweeps never put both squeezes on at once.

**Why the analytical quantities see it first.** The scorecard reports `ph_max`, which
degrades continuously. The pole solve reports a pair going REAL — a discrete change of
the filter's order-shape. "Two true biquads" is what S1 buys, and a Q averaged across
corners where one of the pairs no longer exists is a category error, so report the
pole-pair census before any Q span.

**What to do with it.** Either sweep `lab.corners.REDUCED`/`CORNERS` and certify a real
box, or state the claim as one-axis-at-a-time and stop implying a box. Do not average or
interpolate between certified axes.

**Provenance.** `signoff/paper-draft/validation.md` §8.1 and §8.2 (generated),
`data/pvt.json`, `data/pvt_index_pre_mim_a1p1_{cert-axes,cert-box}.json`.
Bias law `LPF_BIAS_ALPHA=1.1` on every temperature row — see
[[bias-alpha-is-part-of-a-temperature-measurement]].
