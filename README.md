# agentic-design-250hz-lpf-ihp130

An **agent-first analog design challenge**: cut the input-referred noise of a
250 Hz, 4th-order, fully differential super-source-follower low-pass filter by
more than 20 %, in an **open** PDK, with every number reproducible from a
command in this repo.

Everything here is publishable. The PDK is **IHP SG13G2** (130 nm BiCMOS,
Apache-2.0) and the simulator is **ngspice 45 built with OSDI** (GPL), so decks,
model references, logs and schematics all live in git with nothing redacted.

## Result

**Solved.** [`signoff/`](signoff/README.md) holds the delivered cell,
`022-reuse-final` — the originating **branch-stacked** super-source-follower,
bridge and current reuse intact, ported by *device type and size only* (all 42
device connections identical to the drawn topology).

| | reference (yardstick) | **delivered** |
|---|---|---|
| IRN 0.5–200 Hz | 49.98 µVrms | **28.07 µVrms** (−43.8 %) |
| THD @ 175 mVpp, 50 Hz | −48.37 dB | **−56.46 dB** |
| core power | 12.07 nW | 14.45 nW |
| ph_max (S1) | 346.74° | 341.42° |
| passband ripple | **0.2512 dB — fails S3** | **0.0691 dB** |
| drawn capacitance | 98.0 pF | 366.3 pF |
| mismatch yield | — | **95 %** (100 samples) |

All of S1–S8 pass. `uv run python signoff/verify.py --regen` re-derives the whole
sign-off — it regenerates the schematics from the sizing, netlists them with
xschem, simulates *those* netlists and checks them against both the deck builder
and the certified scorecard. The story is in
[`doc/campaign-report.md`](doc/campaign-report.md); every sizing round attempted
is in [`doc/sizing-history/rounds.md`](doc/sizing-history/rounds.md).

**Known limitation, stated up front:** the cell is not supply-tolerant (fc
250.0 → 206.5 Hz at VDD 1.45 V) and that is *proven* unfixable by device type or
size — the reuse ladder is threshold-referenced, so holding ±2 % fc over a ±10 %
rail would need a device slope of ~1.9 V per e-fold against 0.04–0.2 V for real
MOS. It needs a supply-independent bias, i.e. added components.

## The challenge

Beat the reference baseline on noise without giving anything else back.

| # | spec | target | reference baseline (measured here) |
|---|---|---|---|
| S1 | two true biquads: max unwrapped phase lag / stopband | ph_max ≥ 330° and \|H\|@1 kHz ≤ −48 dB | **346.74°** / **−48.43 dB** |
| S2 | cutoff | 250 Hz ±2 % | **250.37 Hz** |
| S3 | passband gain | \|dc\| ≤ 0.2 dB | **−0.0047 dB** |
| S4 | peaking | ≤ 0.2 dB | **0.0227 dB** |
| S3f | passband flatness to 150 Hz | ripple ≤ 0.2 dB | **0.2512 dB — the reference FAILS this line** |
| S5 | **input-referred noise, 0.5–200 Hz** | **< 40 µVrms** | **49.98 µVrms** ← the number to beat |
| S6 | filter-core power (bias reference excluded) | < 50 nW | **12.07 nW** @ 1.5 V (8.04 nA) |
| S7 | THD, 175 mVpp differential, fin = 50 Hz | ≤ −40 dB | **−48.37 dB** (HD3-dominated) |
| S8 | provenance | ≥ 2 papers from `pdf/` combined | — |
| — | total drawn capacitance | **reported, never specced** | **98.01 pF** |

The required cut is **−20.0 %** on S5. S6 leaves roughly 4× headroom
(50 nW at 1.5 V is 33.3 nA of core current against the reference's 8.04 nA),
so current is available — but in weak inversion noise is not bought down by
current alone, which is exactly what makes the problem interesting.

**The reference design.** Two cascaded super-source-follower biquads, no CMFB
(the followers define the common mode). Per biquad: an input follower
(gate = input, source = biquad output), a shunt-feedback transconductor gm_f
(gate = internal node, drain = biquad output), one bias current per node, and
two capacitors — `c1` from the internal node to the biquad output and `c2`
differentially across the biquad's outputs:

```
w0^2 = gm_i * gm_f / (C1 * C2)        Q = sqrt(gm_i * C2 / (gm_f * C1))
```

16 transistors + 6 capacitors; caps `c1_a 29.468 / c2_a 6.221 / c1_b 11.453 /
c2_b 9.946 pF`; one ideal reference current into a real n/p mirror, with every
bias device an integer multiple of that unit (2 units at each biquad output per
side ⇒ 8 nA total). Build sheet: `decks/reference/build-sheet.md`.

**Both biquads use a p-type input follower**, which is the one structural
change against the originating design (which alternated n and p). SG13G2 has
no deep-n-well / isolated NMOS, so an n-channel source follower's bulk is the
shared p-substrate and cannot follow its source; in weak inversion its dc gain
is then exactly **1/n**, and n ≈ 1.38 for these devices. Measured on the
alternating structure: the n-input stage lands at **−2.328 dB** and the p-input
stage at **−0.003 dB** — the n stage alone overruns the 0.2 dB S3 budget by
more than 10×, and no re-sizing recovers it, because 1/n is set by the process.
Making both stages p-type restores exact unity gain and keeps the
self-referenced gain that the candidate family's mismatch yield depends on. The
cost is that the common mode climbs one |Vgs| per stage instead of cancelling;
it is absorbed by placing the input common mode low (0.25 V) so the output
lands mid-supply (~1.25 V). See `doc/journal/nmos-bulk-tie.md` and
`doc/journal/all-p-followers.md`.

That common-mode shift is also why the **delivered** cell runs at vicm 0.65 V
rather than VDD/2: with the bridge in place 0.65 V is the measured ceiling, and
a level shifter closes the rest. Reaching VDD/2 in-core requires deleting the
bridge — see `signoff/README.md`.

**One honest caveat about the yardstick.** Re-measured on a dense sweep, the
reference does **not** meet its own S3 flatness clause (ripple 0.2512 dB against
a 0.2 dB bound); it passed at 10 pts/decade only because the samples straddled
the feature. It remains the yardstick and remains frozen, but it must not be
described as "on spec except for noise".

**Technology, in one block.** Devices `sg13_hv_nmos` / `sg13_hv_pmos`
(thick-oxide, 3.3 V class) selected via `.lib cornerMOShv.lib mos_tt`
(sections `mos_tt|ss|ff|sf|fs`); MIM cap `cap_cmim`; resistors `rsil` / `rhigh`
/ `rppd`. VDD = 1.5 V, input CM 0.25 V, output CM ≈ 1.25 V, 27 °C. The hv
flavour is the right map for a long-L, low-leakage, nano-amp design: comparable
gate-referred flicker noise to the lv devices, 20–100× better gm/gds, and —
decisively — lv NMOS **cannot be biased at 1 nA** at these widths (17 µm/8 µm
already carries 2.5 nA at Vgs = 0). The measured evidence is in
`doc/pdk-notes.md`.

## Layout

| path | what |
|---|---|
| `lab/` | the harness. `config` (paths, lanes, PDK names, operating point) · `dut` (Dev/Design/topologies/`subckt`/`device_table`) · `deck` (ac+noise, op-only, THD transient, vdd sweep — decks are *built*, never text-edited) · `ngspice` (runner, `preflight`, `SimError`) · `raw` (rawfile reader + metric primitives) · `metrics` (SPEC, `evaluate`, `gate`, `table`, `explain`) · `ledger` (append-only run log) · `parallel` (batches) · `shape` (Butterworth **template** fitting) · `oppoint` (per-device op probe) · `thd` (coherent strobed transient + DFT) · `corners` (PVT) · `mc` (mismatch Monte Carlo) · `droop` (VDD_min) · `plot` (figures) |
| `decks/reference/` | the **frozen** reference testbench + core deck, its `design.json` sizing point and `build-sheet.md`. sha-pinned by `make lint`; splice against it, never edit it |
| `experiments/NNN-<name>/` | one directory per technique: `README.md` (hypothesis → verdict) + scripts |
| `experiments/_template/` | copy me to start a new experiment |
| `signoff/` | **the deliverable and its evidence**: `design/` (sizings of record), `schematic/` (xschem `.sch`/`.sym` + two testbenches with their `.control` blocks + generated netlists), `asbuilt/` (certified decks), `scorecard.json`, and `verify.py` — the one command that re-derives all of it |
| `doc/sizing-history/` | every sizing round attempted and what it returned, **derived** from the round JSONs by `build.py`, never typed. The dead ends are kept deliberately |
| `doc/campaign-report.md` | the narrative: the four diagnoses that drove the design, what device type and size could not fix, and the corrections made to this repo's own record |
| `doc/target-spec.md` | **the design challenge** — S1–S8 and their definitions |
| `doc/benches.md` | **reference-first policy** + the frozen measurement definitions |
| `doc/design-reference.md` | the reference design's facts, validated model, and the constraints that kill naive ideas |
| `doc/pdk-notes.md` | measured device data for this PDK: gm/ID, gm/gds, Vgs at 1 nA, leakage, gate-referred noise |
| `doc/environment.md` | the two simulator lanes, the env vars, and the ngspice/IHP gotcha list |
| `doc/journal.md` + `doc/journal/` | learnings index + one file per entry (typed semantic/procedural, superseded-aware) |
| `doc/memory/` | the memory model (working/episodic/semantic/procedural) + write-risk ordering |
| `doc/experiment-log.md` | one line per experiment + open items |
| `pdf/` | the papers + `INDEX.md` (cite by handle) |
| `pdk/` | regenerated device-characterisation LUTs (git-ignored) |
| `runs/` | `ledger.ndjson` — local observability, git-ignored; keeper numbers graduate into experiment READMEs |
| `scripts/` | `lint.py`, `baseline.py`, `runs.py`, `context_pack.py`, `draw_xschem.py` / `draw_lpf_core_022.py` (schematic drawers), `check_netlist.py` (connectivity gate) — the Makefile's implementation |

No PDK bytes are vendored: model cards are referenced by bare library name and
resolved by the simulator's `sourcepath`, and the PDK's git SHA is pinned in
`doc/environment.md`.

## Quickstart

```bash
uv sync            # this checkout's own .venv (every worktree needs one)
make doctor        # is the simulator lane alive? prints lane, PDK, op-plot names
make baseline      # run the reference deck, print the scorecard
make check         # lint + the reference deck still reproduces its certified numbers
make lint          # repo invariants only (fast, no simulation)
make runs          # query the run ledger

uv run python signoff/verify.py --regen   # re-derive the whole sign-off
```

`make doctor` is the first thing to run on a new machine and the first thing to
suspect when numbers move: it runs a single-transistor operating point through
the whole lane and reports which plots came back.

Start an experiment:

```bash
cp -r experiments/_template experiments/001-<technique>
# fill in the README hypothesis, edit run.py (build Designs, evaluate, table), then:
python experiments/001-<technique>/run.py
```

## The two simulator lanes

IHP's MOS devices **are** PSP 103.6 Verilog-A compact models, loaded into
ngspice as **OSDI** objects. A stock ngspice cannot simulate this PDK at all —
it reports `Unknown model type psp103va`. So both lanes are really "an ngspice
that has the `.osdi` objects loaded":

| lane | selected by | what it is |
|---|---|---|
| **docker** (default) | nothing — it is the default | the workspace image `spicexplorer-spice-base:local`, carrying ngspice 45 built with OSDI, the IHP model cards, and the OpenVAF-compiled PSP103 / r3_cmc / mosvar OSDI objects. Runs anywhere Docker runs, including macOS. |
| **native** | `export LPF_NGSPICE=/path/to/ngspice` | a host ngspice whose `~/.spiceinit` loads those same `.osdi` objects and puts the PDK `models/` dir on `sourcepath`. Faster start-up; use it on a machine that already has the PDK. |

`lab.config.lane()` picks one at import time — `native` if `LPF_NGSPICE` is
set, else `docker`. Every run lands in its own directory under
`LPF_WORK` (default `/tmp/lpf_work-<repo>-<hash>`, namespaced per checkout so
parallel worktrees never collide), so any result can be re-opened after the
fact.

Env vars: `LPF_DECK_DIR` · `LPF_DECK_TB` · `LPF_WORK` · `LPF_NGSPICE` ·
`LPF_DOCKER_IMAGE` · `LPF_JOBS` (default `cpu_count()-2`) · `LPF_EXP` (stamps
ledger rows) · `LPF_VDD` / `LPF_VICM` / `LPF_VOCM` · `PDK_ROOT`.

## Rules of the road

- **Reference first.** The frozen measurement definitions in `lab/metrics.py`
  (and the long-window DFT THD path) define every metric; fast substitutes are
  validated against them, and the frozen method is the sign-off number.
- Every experiment states a **falsifiable hypothesis first**, always runs the
  **control that isolates the technique from cap re-allocation**, and never
  trades stopband away silently.
- **Findings are tables or plots** (`lab.metrics.table`) — an expert must read a
  result in seconds; prose is for interpretation only.
- Verdicts get one line in `doc/experiment-log.md`; transferable learnings get
  an entry file in `doc/journal/` (+ an index row in `doc/journal.md`).
- Batches run in parallel on the netlist lane (`lab.parallel`, `LPF_JOBS`). The
  schematic lane is version-controlled text — no lock, no daemon, no
  single-session rule; just never let two generators write the same `.sch`.

Agent routing, the ten numbered rules, and the parallel-session protocol live in
[CLAUDE.md](CLAUDE.md).
