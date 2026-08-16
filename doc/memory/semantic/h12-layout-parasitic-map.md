# 2026-08-17 — H12-pdk-cap layout — where the parasitics are, what they cost, and where the area is

KIND: semantic overflow | type: semantic | status: live

Layout of record = `layout/H12-pdk-cap/iterations/it14` (round 4, 2026-08-17):
432.0 × 528.0 µm = **228 094 µm²**, DRC 0 (no waivers), LVS match, kpex CC 69 C
(RC 69 C + 6 331 R agrees to 0.0003°). Numbers below from `scorecard_post.json`
(post) and `signoff/post-pvt/H12-pdk-cap/scorecard.json` (pre).

| line | pre-layout | post-layout it14 | Δ | mechanism |
|---|---|---|---|---|
| fc | 249.775 Hz | 248.664 Hz | −1.11 Hz | ≈ 135 fF extracted onto net4/net1/vout nodes vs 184 pF drawn — 0.6 % |
| ph_max | 332.382° | 331.221° | −1.16° | **net2/net3 gate nets** 30.2 fF each × 0.0225 °/fF ≈ 0.7°, well/output nodes the rest |
| \|H\|@1 kHz | −49.026 dB | −49.218 dB | −0.19 dB | more C on the internal nodes |
| ripple | 0.0523 dB | 0.0363 dB | −0.016 | |
| IRN 0.5–200 Hz | 29.199 µV | 29.194 µV | 0.000 | noise is device-set |
| power | 11.913 nW | 11.914 nW | 0 | |
| THD @175 mVpp/50 Hz | −50.40 dB | −49.73 dB | +0.68 dB | HD3-dominated; HD2 at bench floor (≈ −97…−104 dB) |
| worst cap corner (`cap_bcs`, iref ×0.9) | 331.02° | 329.82° | −1.20° | the only spec miss post-layout (limit 330°), accepted by the owner |

**Per-net C to the bench ac grounds (kpex CC, fF; brief budget nominal / PVT):**
net2 30.20 / net3 30.22 (22.8 / 9.6; Δ 0.02) · net4 ≈ 67.6 / net1 ≈ 67.5 (82.8) ·
voutp ≈ 460 / voutn ≈ 439 (455 PVT) · net2↔net3, net4↔net1 and A↔B (net2∪net3 to
net4∪net1∪vout*) = **0.000 fF** (asserted at build). Not extracted: MIM top-plate
environment (≤ 15 fF on net2/net3, kpex limitation) and n-well junction C
(16–39 fF/half on net4/net1; −0.11 … −0.26° if modelled).

**High-frequency shape** (real, not an artifact): the 4th-order roll-off meets a
transmission zero at 3.80 kHz (−124 dB pre / −122 dB post) and then a
feed-through floor ≈ −101 dB (follower Cgs/Cgd + capacitor feed-forward, in
phase → the unwrapped phase returns to 0). Layout moves the floor by ≈ +0.2 dB
and does not move the notch. Plot with the y-axis to −130 dB or it looks like a
phase-unwrap error.

**Where the area is** (it13 → it14): MIM 122 253 µm² (fixed by the design, 49 → 54 %
of the cell); active silicon ≈ 16–21 k µm²; the rest is spacing. Knob-only
optimization with the floorplan fixed recovers ≤ 2.5 %; the bias dummy rows
were 5.6 %; the next 20 %+ needs caps over the device band (new plan gate).
Total C is a schematic decision — layout cannot shrink it.

Provenance: `layout/H12-pdk-cap/{REPORT.md,REVIEW.md,scorecard_post.json,opt/results/}`, `doc/paper/figures/data/prepost_bode.json`.
