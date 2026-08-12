# 2026-08-11 — This PDK has no isolated NMOS, so an n-type source follower's dc gain is exactly 1/n — a process constant no sizing can recover

KIND: journal entry | type: semantic | status: live

**Symptom.** The originating design alternates the two biquads: an n-type input
follower in stage A, a p-type input follower in stage B. Ported device-for-device
onto IHP SG13G2 and re-sized, the filter's dc gain came out at **−2.33 dB**
against an S3 budget of **|dc| ≤ 0.2 dB** — an overrun of more than **10×**.
Re-sizing moved fc, Q, noise and power; it did not move the dc gain.

| run | structure | `dc_db` | `fc_hz` | `ph_max_deg` | ledger |
|---|---|---|---|---|---|
| `ref_v0` | alternating n/p followers | **−2.3335** | 136.07 | 334.87 | `runs/ledger.ndjson` |
| `ref_v1` | alternating n/p, re-sized | **−2.3315** | 273.45 | 347.19 | " |
| `ref_v2` | **both followers p-type** | **−0.0048** | 218.83 | 344.05 | " |
| `ref_fit` | both p-type, fitted to spec | **−0.0047** | 250.00 | 346.43 | deck `1ae5466ad00c` |

Split by stage on the alternating structure:

| stage | input device | bulk | dc gain |
|---|---|---|---|
| A | n-channel follower | shared p-substrate (forced) | **−2.328 dB** |
| B | p-channel follower | its own n-well, tied to source | **−0.003 dB** |

The n-stage alone spends the entire S3 budget an order of magnitude over. The
p-stage is unity to three decimals.

**Mechanism.** SG13G2 has **no deep-n-well / isolated NMOS**. An n-channel
device's bulk *is* the shared p-substrate, tied to ground; it cannot follow its
source. A p-channel device sits in its own n-well and keeps bulk = source, as
drawn. For a source follower whose bulk sits at the rail, the source node sees
both `gm` (gate→source) and `gmb` (bulk→source, but with the bulk held fixed the
`gmb` term appears as a load), so

    H(0) = gm / (gm + gmb) = 1 / n,   because gmb = (n − 1)·gm in weak inversion.

`n` is the subthreshold slope factor — a **process** number, not a geometry
number. Measured here from the weak-inversion limit of gm/ID
(`doc/pdk-notes.md`): `sg13_hv_nmos` gm/ID = 28.1 V⁻¹ ⇒ **n = 1.38**, which puts
the hard bound at 20·log₁₀(1/1.38) = **−2.79 dB**. The measured −2.328 dB sits
just inside that bound because the shunt-feedback loop reclaims a few tenths of a
dB; the point is that the *scale* of the error is set by `n`, and **W, L, ng, m
and bias current do not appear in `1/n` at all**.

**Rule.**

1. **No n-channel source follower may sit in the signal path of a design scored
   against |dc| ≤ 0.2 dB in this PDK.** The budget is 0.2 dB; the floor is
   2.3–2.8 dB. There is no sizing solution.
2. n-channel devices take **bulk = GND**, always, in every netlist this repo
   builds (`lab/dut.py`, `NROLES`). p-channel devices take **bulk = source**.
   The `Dev.card()` builder writes both, so the tie is never a hand decision.
3. Devices whose **source does not move** are unaffected: the n-type shunt-
   feedback transconductors and the n-type bias sinks all sit with their source
   at ground and see no body effect either way. Only a *swinging source* pays.
4. When porting a topology across processes, **check which devices are allowed
   to have their own well before checking anything else.** Body effect is not a
   second-order correction here; it is a topology constraint.

**Consequence.** This is what forced the one structural change against the
originating design — both followers p-type. See
[`all-p-followers.md`](all-p-followers.md) for the decision, its common-mode
cost, and what it buys back.

Provenance: `lab/dut.py:25-45` (the technology-mapping note), `doc/pdk-notes.md`
(gm/ID and Vgs-at-1 nA tables), ledger rows `ref_v0`/`ref_v1`/`ref_v2`.
