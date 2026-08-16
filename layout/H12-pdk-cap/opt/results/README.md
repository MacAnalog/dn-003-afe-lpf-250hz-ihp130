# Area optimization over the generator knobs — campaign 2026-08-16

Tool: `../../optimize_area.py` (stand-alone Nevergrad driver over the platform runners; the
platform-way equivalent is `../project_setup.yaml` + `spicexplorer-optimize`, platform PR #101).
Every trial = build → DRC → LVS (per-trial reference) → kpex CC → frozen LPF benches.
Objective area / 247 137 µm² (round-3 layout); constraints DRC 0, LVS match, S1–S7 pass,
ph_max ≥ 331.10°, net2/net3 ≤ 32.4 fF, |Δ(net2,net3)| ≤ 0.5 fF, C(A↔B) ≤ 0.277 fF.

| campaign | search space | trials | ok | best area | Δ vs round 3 | ph_max | net2 |
|---|---|---|---|---|---|---|---|
| A | 25 numeric knobs, floorplan modes + `bias_dummy_rows=1` fixed | 300 | 17 | 240 890 | **−2.5 %** | 331.175 | 32.14 |
| B | A + `bias_dummy_rows` free | 300 | 39 | 243 181 | −1.6 % | 331.128 | 32.08 |
| single eval | round-3 defaults, `bias_dummy_rows=0` | 1 | ok | 233 346 | **−5.6 %** | 331.207 | 30.24 |
| single eval | A-best knobs + `bias_dummy_rows=0` | 1 | ok | **228 094** | **−7.7 %** | **331.221** | **30.20** |

Findings (all measured, `summary.json` + `campaign_*_trials.jsonl`):
- The binding constraint is **net2/net3 C**: 195/300 (A) trials fail it — nearly every gap/pitch
  reduction moves plates or rails closer to the gate nets. Even relaxed to 35 fF, no explored point
  is below −3.6 %: with the floorplan modes fixed, the knobs do not reach the white space.
- `bias_dummy_rows=1` (round 2's F7 fix) costs **13.8 k µm² (5.6 %), 0.05° of ph_max and 2 fF of
  net2** — measured, against a hand-bound matching benefit. Campaign B never explored it (its 4
  `=0` trials hit the symmetry assertion / LVS on other knobs), which is why B < A.
- Generator gaps found by the loop: `cc12_cols ≠ 7` with `cc12_split="3|1|3"` → LVS mismatch (the
  BOUNDS endpoint sweep was DRC-only; it must include LVS); 47 builds rejected by the mirror-XOR /
  TopVia1 half-plane assertion at legal knob combinations (guard-rail is doing its job, but the
  budget may be over-tight for via layers).
- Candidate for `it14` (needs the owner's call on dummy rows, PLAN R2.8 Q2): A-best knobs +
  `bias_dummy_rows=0` — 228 094 µm² (−1.1 % vs round 1), ph_max 331.221, net2 30.20, all gates pass.
