# 2026-08-16 — Post-layout phase in the stacked SSF cell is set by the wire on the two second-stage GATE nets (net2/net3): 0.0225 ° per fF, so a 170 µm top-metal haul cost 1.1° and a floorplan change (not routing) recovered it

KIND: journal entry | type: semantic | status: live

**Symptom.** Round-1 layout: ph_max 332.38° (schematic) → 330.73° post-layout, and
the pre-layout worst passing cap corner (`cap_bcs`, iref ×0.9: 331.02°) went to
329.30° < 330°.

**Mechanism.** The extraction put 50.0 / 44.9 fF on net2/net3 (the gates of the
second-stage followers; brief budget 22.8 fF nominal, 9.6 fF over PVT). 42 fF of
it was one 170.5 µm TopMetal1 haul from the followers to the `xc13`/`xc17` arrays,
because bank A had `xc19` on the symmetry axis and `xc13`/`xc17` outboard. What-if
deletion of the net2/net3 parasitics alone gives back 1.117° (REPORT §5); the
sensitivity is 0.0225 °/fF (round-4 what-ifs, `scorecard_post.json`).

**What fixed it and what did not.**

| change | net2 (fF) | ph_max |
|---|---|---|
| round 1 | 50.04 | 330.732° |
| knob-only best (cc13 → 1 column) | 42.52 | 330.87° |
| **xc13/xc17 onto the axis, xc19 split outboard** (floorplan mode) | 32.71 | 331.14° |
| spine Metal2 → Metal5, minimal Metal1 straps | 26.46 | 331.21° |
| identical Metal1 drain bar on all six bias-sink units (matching rule; +5.9 fF) | 32.33 | 331.16° |
| dummy rows removed + area-campaign knobs (it14) | 30.20 | 331.221° |

The 600-trial area campaign confirms it from the other side: with the floorplan
fixed, 195/300 trials violated the net2 cap because *every* gap you shrink
moves a plate or a rail toward these two nets. Routing knobs buy tenths of a
degree; the floorplan (which array sits on the axis, and one spine per half)
bought a full degree at zero area.

**Rule.** Put the highest-sensitivity nets' terminals on the axis first and
route the rest around them; make "which sub-array is on the axis" a generator
knob so the optimizer can reach it; measure sensitivity (°/fF, Hz/fF) per net
from the brief's injection sweep before drawing.

Provenance: `layout/H12-pdk-cap/{BRIEF.md,REPORT.md,REVIEW.md,iterations/iterations.yaml,opt/results/}`; reviewer round-1 F2/F5/F6.
