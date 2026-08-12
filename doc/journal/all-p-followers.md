# 2026-08-11 — Both biquads take a p-type input follower: the only structure in this PDK that keeps unity dc gain, paid for by common-mode stacking absorbed at the input

KIND: journal entry | type: semantic | status: live

**Symptom / forcing fact.** The originating design alternates follower polarity
between the two biquads (n-type in stage A, p-type in stage B) so the two
|Vgs| shifts cancel and the output common mode returns to the input common mode.
In this PDK that structure cannot meet S3: the n-stage's dc gain is pinned at
`1/n` = **−2.328 dB** measured, against a budget of |dc| ≤ 0.2 dB, and no
re-sizing recovers it — see [`nmos-bulk-tie.md`](nmos-bulk-tie.md).

**Decision.** **Both** biquads use a **p-type input follower** (bulk = source, in
its own n-well) with an **n-type shunt-feedback transconductor** whose source
sits at ground. Per biquad: input follower (gate = input, source = biquad
output), feedback `gm_f` (gate = internal node, drain = biquad output), one bias
current per node, `c1` from internal node to biquad output and `c2` differential
across the biquad's outputs. Pole pair unchanged:

    w0² = gm_i·gm_f / (c1·c2),   Q = sqrt(gm_i·gm_f·c1/c2) / gm_i

Nets: `vinp/vinn` → [biquad A] → `vout_1/vout_2` → [biquad B] → `voutp/voutn`;
`net2/net3` are biquad A's internal nodes, `net4/net1` biquad B's
(`lab/dut.py:build_reference`).

**What it buys.**

| | alternating n/p | both p-type |
|---|---|---|
| dc gain (measured) | −2.3335 dB (`ref_v0`) / −2.3315 dB (`ref_v1`) | **−0.0047 dB** (`ref_fit`) |
| S3 (|dc| ≤ 0.2 dB) | fails by >10× | passes with 40× margin |
| gain reference | body effect ⇒ process constant `1/n` | **self-referenced**: the same device's gate drives and its own source follows |

The second row is the one that matters beyond dc. A *self-referenced* gain
(input gate and feedback source on the **same** device) converts a threshold
mismatch into an **offset**, whereas a matched-pair *ratio* gain converts the
same ΔV_T into a gain error, δH/H ≈ ΔV_T/(n·U_T). The originating campaign
measured σ(dc) of 0.0002–0.0038 dB for the self-referenced follower class against
**0.370 dB** for gate-driven pair-ratio topologies — *carried forward, not
re-measured here*; but the mechanism is process-independent, and it is the
property the whole candidate family's mismatch yield rests on. Falling back to
the n-type follower would have traded that away as well as S3.

**What it costs.** The two |Vgs| shifts no longer cancel — they **stack**. Each
p-type follower moves the common mode **up** by one |Vgs|; at nano-amp bias that
is ≈ 0.46 V for `sg13_hv_pmos` at W = 10 µm / L = 4 µm and 1 nA
(`doc/pdk-notes.md`).

**Absorption.** Place the input common mode **low** so the output lands
mid-supply:

| knob | value | why |
|---|---|---|
| `VDD` | 1.5 V | sg13g2 analog supply, hv devices |
| `VICM` (input CM) | **0.25 V** | two stacked |Vgs| ⇒ output lands mid-rail |
| `VOCM` (output CM, and the dc hint) | **1.25 V** | ≈ 0.25 + 2·0.5 V |
| temperature | 27 °C | |

(`lab/config.py:78-95`.) There is **no CMFB anywhere in the filter** — the
followers define the common mode, which is exactly why the CM must be *placed*
rather than *servoed*, and why `VICM` is a first-class design variable rather
than a testbench convenience. Getting it wrong does not produce a common-mode
error; it produces a device out of saturation and a silently mis-tuned filter.

**Certified reference scorecard after the change** (frozen in
`decks/reference/`, ledger `ref_fit`, deck `1ae5466ad00c`):

| metric | value |
|---|---|
| fc | 250.00 Hz |
| passband gain (dc) | −0.0047 dB |
| peaking | 0.023 dB |
| |H| at 1 kHz | −48.43 dB (4th-order Butterworth arithmetic: −48.16) |
| `ph_max_deg` (S1) | 346.43° |
| IRN 0.5–200 Hz | **50.18 µVrms** |
| core current / power | 8.04 nA / 12.07 nW @ 1.5 V |
| total drawn C | 98.01 pF |
| devices | 16 transistors + 6 capacitors |

**Rule.**

1. In this PDK, **every signal-path follower is p-type**. `lab/dut.py:NROLES`
   lists the only n-channel roles (`gmf_a`, `gmf_b`, `bias_a_int`,
   `bias_b_int`) — devices whose source sits at ground.
2. A polarity change is a **common-mode** change: whenever a candidate alters
   follower polarity or stage count, re-derive the CM stack and re-place `VICM`
   in the same edit. Never inherit `VICM` across a structural change.
3. Report the CM ladder (input CM, each internal node, output CM, and the
   worst |V_DS| margin) with any candidate that touches it. Without CMFB, the
   CM plan **is** part of the design, not part of the bench.

Provenance: `lab/config.py:78-95`, `lab/dut.py:39,160-185`, ledger
`ref_v0`/`ref_v1`/`ref_v2`/`ref_fit`, `doc/pdk-notes.md`.
