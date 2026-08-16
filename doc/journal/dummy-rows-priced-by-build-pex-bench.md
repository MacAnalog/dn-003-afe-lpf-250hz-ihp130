# 2026-08-16 — Matching "insurance" must be priced with a build → PEX → bench evaluation: the bias array's dummy ROWS cost 5.6 % of the cell, 2 fF on the sensitive gate nets and 0.05° of phase, for a benefit that was only ever a hand bound

KIND: journal entry | type: semantic | status: live

**Symptom.** Layout round 2 added `bias_dummy_rows = 1` (full-size units above and
below the 3-row common-centroid bias array) on the reviewer's finding that the
ratio's numerator sat on edge rows. Round 3 delivered 247 137 µm². The area
optimizer could not get below −2.5 % with the rows fixed, and its four
`bias_dummy_rows = 0` trials all died on other knobs — so the cost of the rows
was never seen by the search.

**Measured** (single evaluations, `layout/H12-pdk-cap/opt/results/summary.json`;
same build → DRC → LVS → kpex CC → `lab.metrics.evaluate` chain as every trial):

| point | area µm² | ph_max | net2 (fF) |
|---|---|---|---|
| round 3 (rows = 1) | 247 137 | 331.160° | 32.33 |
| round-3 defaults, rows = 0 | 233 346 (−5.6 %) | 331.207° | 30.24 |
| campaign-A knobs + rows = 0 (**it14**) | **228 094 (−7.7 %)** | **331.221°** | **30.20** |

The rows made the cell taller by 31.8 µm × 434 µm, lengthened the net2/net3
runs across the taller island (+2 fF, +0.05° lost), and their benefit —
identical etch/stress environment for the edge units — was a hand bound
(≈ 1 Hz of fc against a 3.3 Hz margin), not a measurement.

**Rule.** A matching/yield technique in layout is a *knob*, and it is adopted the
way any knob is: build it, extract it, run the frozen benches, and put its
price next to its (measured, or honestly bounded) benefit. Half-height dummies
at the same L and pitch buy the same environment for a third of the cost when
the environment argument is real. The owner reversed the plan's Q2 on these
numbers (PLAN.md R2.8 note, 2026-08-16).

Provenance: `layout/H12-pdk-cap/opt/results/{README.md,summary.json,campaign_A_trials.jsonl,campaign_B_trials.jsonl}`, `layout/H12-pdk-cap/iterations/it14`, `REPORT.md` round 4.
