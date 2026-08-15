# signoff/ — the deliverable, in two sets

**KIND: SIGN-OFF (router).** Two self-contained sets; each has its own
`README.md` / `COMPARISON.md`, per-cell directories, and (for `pre-pvt/`) the
`verify.py` reviewer script.

| set | what | when to read |
|---|---|---|
| [`pre-pvt/`](pre-pvt/) | The original nine sizings of the branch-stacked SSF cell (`A-minarea` … `H-shipped`), certified through both identity gates (schematic ≡ netlist ≡ simulation), with MC and the 22-point PVT screen. **PVT-unaware**: bias is threshold-referenced (1/22 corners clean), and eight of nine cells use lv devices (`in_a` and/or `gmf_b`) — not admissible at VDD = 1.5 V. Frozen; the yardstick for what follows. | provenance, the identity gates, the S8 paper combination |
| [`post-pvt/`](post-pvt/) | The cells from `experiments/023-replica-bias/`: **all-hv**, replica-biased ladder (topology `d` — signal path device-for-device the same as `pre-pvt`, plus one 3-device bias branch), headroom-centred, sized so every S1–S8 line passes at nominal with margin, with measured process / supply / temperature envelopes and MC yield. Schematic lane pending (`draw_xschem.py` topology `d`). | the cell to take forward |

Scripts select the set with `LPF_SIGNOFF_SET=pre-pvt|post-pvt`
(`scripts/build_signoff.py`, `scripts/plot_signoff.py`); default `pre-pvt`.
