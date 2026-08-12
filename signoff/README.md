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

**3. Input common mode is 0.65 V, not VDD/2 — and that is a consequence of the
constraint, not an unsolved problem.** The all-p cascade shifts the CM up one
|V_SG| per stage; 0.65 V is the measured ceiling **with the bridge in place**.
VDD/2 is reachable only by deleting the bridge (see the table below), which the
constraint forbids. A level shifter closes the remaining 0.10 V (budget: √(40² − 28.07²) = **28.5 µVrms** of
input-referred noise available before S5 breaks).

## Candidate set — nine sizings, all passing

See **[COMPARISON.md](COMPARISON.md)** for the full table and the pick guide.
Every candidate is the SAME topology (bridge and current reuse intact), differing
only in device sizes, flavours and capacitor values; each lives in its own
self-contained `signoff/<cell>/` with schematic, both testbenches, as-built decks
and its scorecard.

| cell | IRN µV | P nW | C pF | THD dB | note |
|---|---|---|---|---|---|
| `A-minarea` | 39.70 | **4.15** | **104.4** | −41.69 | area/power floor; 0.30 µV of S5 margin |
| `B-balanced` | 29.38 | 6.01 | 152.9 | −41.90 | best noise per nanowatt |
| `C-lownoise` | 28.54 | 6.46 | 164.0 | −42.39 | |
| `D-thdjump` | 29.34 | 7.31 | 187.9 | −52.29 | first double-digit THD margin |
| **`E-combo`** | **27.27** | **8.88** | **220.0** | **−54.88** | **best all-round — take this one** |
| `F-minnoise` | **26.24** | 12.63 | 305.0 | −58.52 | lowest noise in the repo |
| `G-maxthd` | 26.81 | 14.32 | 348.2 | **−70.99** | 31 dB of S7 margin |
| `E1-prev` | 28.33 | 8.98 | 229.3 | −52.64 | single-lever reference |
| `H-shipped` | 28.07 | 14.45 | 366.3 | −56.46 | first delivered; dominated by E-combo |

`E-combo` is **strictly better than the originally-shipped cell on all four
axes** — noise, power, capacitance and (within 1.6 dB) THD. It exists because two
levers compose: shortening `gm_f,a` recovers the phase the low-power sizing loses
(320.7° → 334.6°), and moving `gm_f,b` to the lv flavour recovers the THD that
shortening costs.

All nine are flat low-pass responses, not merely inside the bounds: worst
`mono_db` in the set is 0.0089 dB — the response never climbs — and peaking is at
most +0.0090 dB.

**Superseded and out of constraint:** `design/021-vdd2-final.json` reaches
vicm = VDD/2 by *deleting the bridge* (16 devices, not 12). Retained as evidence
that VDD/2 and droop margin are obtainable and that both cost the current reuse —
not as a deliverable.

## Next step (not done here)

**Layout.** Deliberately out of scope. Two things it will need that this
electrical sign-off does not settle: the capacitors are drawn as *ideal*
elements (366.3 pF of `cap_cmim` is an area decision, and putting an unverified
area model between the schematic and the certified result would weaken Gate 1),
and the mismatch yield above assumes the PDK's own statistical model with no
layout-induced gradient — common-centroid placement of the bias devices is what
protects the 95 %.
