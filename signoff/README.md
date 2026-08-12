# Sign-off — `022-reuse-final`

**KIND: SIGN-OFF.** The deliverable and the evidence for it. Everything here is
re-derivable from `design/022-reuse-final.json` by one command:

```bash
uv run python signoff/verify.py --regen
```

which regenerates the schematics from the sizing, netlists them with xschem,
simulates *those* netlists, and checks them against both the deck builder and
the certified scorecard. Last run: **both gates PASS**.

## What this is

The originating **branch-stacked super-source-follower** low-pass filter — the
bridge and its current reuse intact — ported to the open IHP SG13G2 130 nm PDK
by **device type and size only**. All 42 device connections are identical to the
drawn topology; no component was added or removed.

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ≥ 330° (ideal-4-pole ceiling 350.53°) | **341.42°** | PASS |
| S1 stopband | ≤ −48 dB @ 1 kHz | **−49.55 dB** | PASS |
| S2 cutoff | 250 Hz ± 2 % | **249.99 Hz** | PASS |
| S3 dc gain | \|dc\| ≤ 0.2 dB | **−0.0209 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB to 150 Hz | **0.0691 dB** | PASS |
| S4 peaking | ≤ 0.2 dB | **+0.0068 dB** | PASS |
| S5 IRN 0.5–200 Hz | < 40 µVrms | **28.07 µV** | PASS |
| S6 core power | < 50 nW | **14.45 nW** | PASS |
| S7 THD @ 175 mVpp, 50 Hz | ≤ −40 dB | **−56.46 dB** | PASS |
| S8 provenance | ≥ 2 papers combined | branch stacking + floating cap | PASS |

`mono_db` **0.0068 dB** — the passband never climbs. Total drawn capacitance
**366.3 pF** (reported, never specced). Mismatch yield **95 %** over 100
attempted samples, σ(fc) 2.42 Hz.

Against the certified reference: **IRN −43.8 %** (28.07 vs 49.98 µVrms),
**THD 8.1 dB better** at the spec point, and it meets the S3 flatness clause
the reference itself misses.

## Layout

| | |
|---|---|
| `design/` | the sizing of record, plus the two alternative cells |
| `schematic/` | xschem schematic, symbol, two testbenches, generated netlists |
| `scorecard.json` | the certified numbers `verify.py` checks against |
| `verify.py` | the one command that re-derives everything |
| `results/` | figures |

## The two identity gates

**Gate 1 — the drawing IS the design.** The xschem netlist and the `lab.deck`
netlist, simulated separately, agree on every scorecard metric to better than
1 part in 10⁵ (and on THD to 0.016 dB). The comparison is deliberately on
*results*, not netlist text: the deck builder and the netlister order lines
differently and neither ordering means anything.

**Gate 2 — nothing drifted.** Those numbers still match `scorecard.json`.

Both gates are re-run by `verify.py`; neither is asserted anywhere by hand.

## Known limitations — read before using this cell

**1. It is not supply-tolerant, and that cannot be fixed by sizing.**

| VDD | fc |
|---|---|
| 1.50 V | 249.99 Hz |
| 1.45 V | 206.52 Hz |
| 1.40 V | 162.43 Hz |

S2 is what breaks. The reuse ladder sets its branch current by
`|V_SG|(gmf_b) + |V_SG|(bridge) = VDD − vbn`, so it is *threshold-referenced*:
`dI/I = dVDD/(2·n·U_T)`. Holding fc inside ±2 % needs the current inside ±4 %,
which over a ±10 % rail would require a device slope of ~1.9 V per e-fold
against 0.04 V (weak inversion) to ~0.2 V (strong) for real MOS. Moving `gmf_b`
to the lv flavour roughly halved the sensitivity (supply-current ratio 6.4 →
2.7) and got nowhere near enough. **A supply-independent bias is required, and
that means adding components.** The 1/22 corner count has the same root cause.

Neither supply droop nor corner yield is an S1–S8 line, and the frozen reference
does not survive the ±10 % box either. This cell is fully spec-compliant; what
it is not is supply-tolerant.

**2. In-band THD above 100 Hz is ~15 dB behind the reference.**

| fin | 20 Hz | 50 Hz | 100 Hz | 150 Hz | 200 Hz |
|---|---|---|---|---|---|
| reference | −69.58 | −48.37 | −43.96 | −32.62 | −29.77 |
| **022-reuse-final** | −67.10 | **−56.46** | −28.57 | −22.64 | −23.62 |

Degradation toward the corner is a *family* property — the reference does it too,
because a follower biquad's internal node is a bandpass tap whose swing peaks
near fc. The extra gap is stacking's: one shared ladder current cannot serve both
internal-node peaks. S7 is specified at 50 Hz only, where this cell beats the
reference by 8 dB.

**3. Input common mode is 0.65 V, not VDD/2.** The all-p cascade shifts the CM up
one |V_SG| per stage. 0.65 V is the ceiling with the bridge in place; a level
shifter closes the rest (budget: √(40² − 28.07²) = **28.5 µVrms** of
input-referred noise available before S5 breaks).

## The two alternative cells

Kept in `design/` because the choice is real:

| | `022-reuse-final` | `021-lv-final` | `021-vdd2-final` |
|---|---|---|---|
| topology | **b** (stacked) | b (stacked) | reference (unstacked) |
| S8 | PASS | PASS | **FAIL** (1 technique) |
| vicm | 0.65 V | 0.65 V | **0.75 V = VDD/2** |
| IRN | **28.07 µV** | 28.54 | 34.85 |
| THD @ 50 Hz | **−56.46** | −42.39 | −44.64 |
| power | 14.45 nW | **6.46 nW** | 24.01 nW |
| capacitance | 366.3 pF | **164.0 pF** | 245.0 pF |
| mismatch yield | **95 %** | 84 % | 82 % |
| VDD_min | 1.50 V | 1.50 V | **1.25 V** |

`021-lv-final` is the low-power / low-area option. `021-vdd2-final` is the only
supply-tolerant one and the only one at VDD/2, and it is a technique short of S8.

## Next step (not done here)

**Layout.** Deliberately out of scope. Two things it will need that this
electrical sign-off does not settle: the capacitors are drawn as *ideal*
elements (366.3 pF of `cap_cmim` is an area decision, and putting an unverified
area model between the schematic and the certified result would weaken Gate 1),
and the mismatch yield above assumes the PDK's own statistical model with no
layout-induced gradient — common-centroid placement of the bias devices is what
protects the 95 %.
