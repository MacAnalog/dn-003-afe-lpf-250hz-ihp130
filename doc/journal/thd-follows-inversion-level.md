# 2026-08-15 — S7 THD in the stacked cell follows the INVERSION LEVEL of the loop transconductors, not the cap allocation: a moderate-inversion gmf_a is worth 12 dB, and it costs 70 mV of the supply budget

KIND: journal entry | type: semantic | status: live

**Symptom.** Re-sizing `B-balanced` for headroom (in_b 2/30, gmf_b 2/31.2 µm
hv, replica bias) and re-fitting its caps to the Butterworth template gave a
flat cell (ripple 0.054 dB) with THD **−35.8 dB** — an S7 fail — where the
sizing it came from measured −41.6 (`B-rep`) and E-combo measures −55.

**What it is not.** Cap allocation. Twenty-four points of a Q-split scan
(`scan.py`: c1_b·s / c2_b÷s, c1_a÷t / c2_a·t, re-trimmed onto fc) move THD
−24 … −62 dB, but every point with THD better than −40 has ripple > 0.5 dB
(a sagging passband); at equal template error the family sits at −36 … −38.
Analytic Q assignments give −58 / −60 dB with 1.1–1.5 dB of sag. Nor is it
current: caps scale with gm ∝ I, so the peak signal-to-bias current ratio
`2·Q·(f/fc)·V/(n·U_T)` is current-independent in weak inversion (`B1-k4`,
I_L 2.0 → 2.6 nA: −28 / −38 dB after refit).

**What it is.** The devices whose gate is an internal node — gmf_a (n hv) and
gmf_b (p hv) — are exponential in weak inversion; the internal node of the
high-Q section swings most, and the fit always lands the high Q on biquad A.
Move gmf_a toward moderate inversion and THD follows, at unchanged shape:

| gmf_a (W/L µm) | ≈ nA per square | THD @ 50 Hz, 175 mVpp | ripple |
|---|---|---|---|
| 7.8/5.2 (B1) | 0.9 | −35.8 | 0.054 |
| 2/45 (B3-a2) | 30 | −41.5 | 0.061 |
| 1/45 (B3-a45) | 60 | **−48.0** | 0.067 |
| 1/45 + gmf_b 1/50 (B3-a45g1) | 60 / 100 | −44.9 | 0.069 |

The same reading explains the sign-off set: E-combo (−55) and G-maxthd (−71)
carry gmf_a at 1/45 and 1/15; D-thdjump (−52) a 0.81/62.4 lv gmf_b; the
−42 cells (B, C) a 7.8/5.2 gmf_a. Widening gmf_b (8/15.6, deeper WI) made B1
*worse*: −27 dB.

**The price.** Moderate inversion is ~70 mV more V_GS on gmf_a, and the
merged ladder's supply budget is `VDD ≥ V_GS(gmf_a) + max(V_SG(gmf_b),
V_SG(in_b)) + 2·Vds_min` (`merged-ladder-headroom-identity`): `B4`/`B5`
(gmf_a 1/45) pass S7 at −44 … −48 dB and lose the 1.35 V rail and the `sf`
corner that `B1` had. At 1.5 V ±10 % the merged cell can have S7 margin or
supply margin; it cannot have both with hv devices in this PDK — the choice is
recorded per cell in experiments/023-replica-bias/README.md.

**How to apply.** Size gmf_a (and gmf_b) by current density first — ≥ 30 nA
per square for S7 with margin — then check the headroom budget; do not try to
buy S7 back with capacitors, the flat solutions are all within ±2 dB.
