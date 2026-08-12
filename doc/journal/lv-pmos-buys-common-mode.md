# 2026-08-12 — The input common mode is a THRESHOLD problem, not a width problem: `sg13_lv_pmos` buys 588 mV

KIND: journal entry | type: semantic | status: live

**The constraint.** Every signal-path follower in this family is p-type (forced —
see [all-p-followers](all-p-followers.md)), so the cascade shifts the common mode
**up** one |V_SG| per stage: `vocm ≈ vicm + 2·|V_SG|`. At VDD = 1.5 V with hv
devices that pins the usable input CM near **0.20 V**, which is an integration
burden: a preceding stage has to deliver it.

**Why width is the wrong lever.** In weak inversion
`|V_SG| = V_th + n·U_T·ln(I/(I₀·W/L))`, so widening buys only `n·U_T` per e-fold
— measured **≈ 92 mV per decade** of width. Reaching vicm = 0.5 V needs ~30×,
and at that width the cell breaks in a way that has nothing to do with dc:

| | drawn C | fc | THD | ph_max |
|---|---|---|---|---|
| 1× width | 150.6 pF | 250 Hz | −42.22 dB | 333.3° |
| 30× width | **104.0 pF** | 250 Hz | **−30.34 dB** | **438.9°** |

The drawn capacitance *fell 47 pF at the same cutoff* because that much of the
pole-setting capacitance became **transistor gate** — which is voltage-dependent.
THD collapsed 12 dB and the response stopped being 4-pole. **Past a point, width
is not a common-mode knob; it is a linearity sink.**

**The lever that works.** `sg13_lv_pmos` attacks `V_th` directly. Measured in
this repo at the 021 cell's own geometry (W 15.6 / L 10.4 µm) and its own branch
currents — not quoted from the PDK notes' W 10 / L 4 µm row:

| flavour | \|Vgs\| @ 0.662 nA | \|Vgs\| @ 2.005 nA |
|---|---|---|
| `sg13_hv_pmos` | 0.4574 V | 0.5015 V |
| `sg13_lv_pmos` | **0.1682 V** | **0.2028 V** |

289 mV and 299 mV less, and the cascade shifts twice: **588 mV of common-mode
headroom**, at no width cost and therefore with no gate-capacitance penalty.

**Three rules that came out of getting it wrong first.**

1.  **Only the FOLLOWERS may move.** `gmf_b` and `bridge` set the branch current
    through `V_SG(gmf_b) + V_SG(bridge) = VDD`. Putting them on a lower-threshold
    flavour re-solves that sum at **408–570 nA** instead of 2 nA — a 250× current
    error that looks like a broken bias, not like a flavour choice.
2.  **Anything gated by a mirror stays hv.** `bias_*_out` gates sit on `vbp`,
    which an hv diode sets; mixing flavours across a current mirror mirrors the
    *threshold difference*, not the current.
3.  **`sg13_lv_nmos` remains closed.** It carries 1.6–5.1 nA at Vgs = 0, more
    than this filter's whole branch current, so no gate voltage biases it
    (`doc/pdk-notes.md` §2.2, §2.4). Only the p-side has this option.

**What it costs.** Gate-referred flicker is ~9 % worse (13.01 → 14.20 µVrms over
0.5–200 Hz at equal geometry and current) and gm/gds is lower (~3690–5080 vs
~3710–8700 at these lengths), which is what pins H(0) = 1 against the 0.2 dB S3
box. But lv also gives **gm/ID = 32 against 25**, so at equal current it buys
more gm, hence more capacitance at the same fc, hence *less* noise overall:
measured on the stacked cell, IRN **30.71 → 28.54 µV**. The swap paid for itself.

**Where it stops.** With `in_a` on lv the branch-stacked cell certifies at
vicm = **0.65 V** and will not go further: the **bridge** needs 104 mV between
`vout_1` and `net4` while `net4` is pinned by the mirror, and at vicm = 0.75 V
every combination of follower flavour, bridge width and mirror width leaves it at
42–75 mV. Reaching VDD/2 means dropping the bridge — i.e. giving up branch
stacking, and with it one of the two techniques S8 rests on. **The VDD/2
requirement and S8 are in direct tension in this PDK**, and that is a result, not
an oversight.
