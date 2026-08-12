# agentic-design-250hz-lpf-ihp130

An **agent-first analog design challenge**: cut the input-referred noise of a
250 Hz, 4th-order, fully differential super-source-follower low-pass filter by
more than 20 %, in an **open** PDK, with every number reproducible from a
command in this repo.

Everything here is publishable. The PDK is **IHP SG13G2** (130 nm BiCMOS,
Apache-2.0) and the simulator is **ngspice 45 built with OSDI** (GPL), so decks,
model references, logs and schematics all live in git with nothing redacted.

## The challenge

Beat the reference baseline on noise without giving anything else back.

| # | spec | target | reference baseline (measured here) |
|---|---|---|---|
| S1 | two true biquads: max unwrapped phase lag / stopband | ph_max ≥ 330° and \|H\|@1 kHz ≤ −48 dB | **346.43°** / **−48.43 dB** |
| S2 | cutoff | 250 Hz ±2 % | **250.00 Hz** |
| S3 | passband gain | \|dc\| ≤ 0.2 dB | **−0.0047 dB** |
| S4 | peaking | ≤ 0.2 dB | **0.023 dB** |
| S5 | **input-referred noise, 0.5–200 Hz** | **< 40 µVrms** | **50.18 µVrms** ← the number to beat |
| S6 | filter-core power (bias reference excluded) | < 50 nW | **12.07 nW** @ 1.5 V (8.04 nA) |
| S7 | THD, 175 mVpp differential, fin = 50 Hz | ≤ −40 dB | measured per delivery |
| S8 | provenance | ≥ 2 papers from `pdf/` combined | — |
| — | total drawn capacitance | **reported, never specced** | **98.01 pF** |

The required cut is **−20.3 %** on S5. S6 leaves roughly 4× headroom
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
w0^2 = gm_i * gm_f / (c1 * c2)        Q = sqrt(gm_i * gm_f * c1 / c2) / gm_i
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
| `lab/` | the harness. `config` (paths, lanes, PDK names, operating point) · `dut` (Dev/Design/topologies/`subckt`/`device_table`) · `deck` (ac+noise, op-only, THD transient, vdd sweep — decks are *built*, never text-edited) · `ngspice` (runner, `preflight`, `SimError`) · `raw` (rawfile reader + metric primitives) · `metrics` (SPEC, `evaluate`, `gate`, `table`, `explain`) · `ledger` (append-only run log) · `parallel` (batches) · `shape` (Butterworth cap fitting) |
| `decks/reference/` | the **frozen** reference testbench + core deck, its `design.json` sizing point and `build-sheet.md`. sha-pinned by `make lint`; splice against it, never edit it |
| `experiments/NNN-<name>/` | one directory per technique: `README.md` (hypothesis → verdict) + scripts |
| `experiments/_template/` | copy me to start a new experiment |
| `xschem/` | the schematic lane: `.sch`/`.sym` of record, the generators that emit them, the canonical netlist comparator, the headless renderer, and committed `.png` evidence |
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
| `scripts/` | `lint.py`, `baseline.py`, `runs.py`, `context_pack.py` — the Makefile's implementation |

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
