# Environment — lanes, knobs, and every trap this harness has hit

**KIND: REFERENCE.** How a deck gets simulated, what each environment variable
does, how to run one deck by hand, and the complete gotcha list. Every gotcha
below was hit in *this* repo; each one carries its exact error string and its
fix, because most of them fail **silently or with a wrong-but-plausible
result** rather than with an error.

---

## 1. The two lanes

`lab.ngspice` picks a lane at import time from `lab.config.lane()`.

| lane | when | how the PDK resolves | how the OSDI objects resolve |
|---|---|---|---|
| **native** (automatic when the host qualifies) | `ngspice` on PATH **and** `$SPICE_USERINIT_DIR/.spiceinit` (else `~/.spiceinit`) loads osdi objects — the lab workstation shape, `SPICE_USERINIT_DIR` = the PDK's `libs.tech/ngspice`; `LPF_NGSPICE=/path/to/ngspice` forces a binary, `LPF_LANE=docker` forces docker | **you** must put the PDK `models/` on `sourcepath` in your own `~/.spiceinit` | **you** must load the same `.osdi` objects in your own `~/.spiceinit` |
| **docker** (fallback) | wherever Docker runs and the host does not qualify for native | the image's `~/.spiceinit` puts the PDK `models/` dir on ngspice's `sourcepath`, so `.lib cornerMOShv.lib mos_tt` resolves by bare name | the image's `~/.spiceinit` `pre_osdi`-loads the OpenVAF-compiled `psp103`, `r3_cmc` and `mosvar` `.osdi` objects |

The image is `spicexplorer-spice-base:local` (override with `LPF_DOCKER_IMAGE`).
Each run gets its own directory under `LPF_WORK`, bind-mounted at `/w`, and runs
as the calling uid:gid so the rawfiles are not root-owned:

```
docker run --rm -v <rundir>:/w -w /w -u <uid>:<gid> spicexplorer-spice-base:local ngspice -b deck.sp
```

Native is `ngspice -b deck.sp` in the same directory. **The deck text is
identical in both lanes** — that is why models are referenced by bare filename
and never by path.

**A native lane without the OSDI objects is not a degraded lane, it is a dead
one:** SG13G2 MOS devices *are* PSP 103.6 Verilog-A models, so ngspice reports
`Unknown model type psp103va` and nothing simulates. See gotcha §4.7 for why
that string is in the fatal list.

### Is the lane alive?

```
python -m lab.ngspice
```
runs `lab.ngspice.preflight()` — a two-source `op` on one `sg13_hv_nmos` — and
prints `{"lane": ..., "pdk": "ihp-sg13g2", "ok": true, "note": "..."}`. `ok:
false` with a `note` naming `psp103va` means the OSDI objects are missing;
`ok: false` with a docker error means the image is not built.

---

## 2. Environment variables

Everything `lab.config` honours. All are optional; defaults are shown.

| variable | default | what it does |
|---|---|---|
| `LPF_DECK_DIR` | `<repo>/decks/reference` | where the frozen reference bench lives. Point elsewhere to score a different vendored deck. |
| `LPF_DECK_TB` | `lpf_tb.sp` | the testbench filename inside `LPF_DECK_DIR`. |
| `LPF_WORK` | `/tmp/lpf_work-<repo dir name>-<sha1(abs path)[:6]>` — in this checkout `/tmp/lpf_work-dn-003-afe-lpf-250hz-ihp130-b74add` | run directories, one per tag. **Namespaced per checkout** so two worktrees can never clobber each other's runs. The ledger (`runs/ledger.ndjson`) is repo-relative and therefore per-worktree too. |
| `LPF_NGSPICE` | *(empty)* | non-empty ⇒ **native lane**, and this is the binary invoked. Empty ⇒ `lab.config._native_default` decides: **native** when the host qualifies (row 1 of the lane table above), else docker. |
| `LPF_DOCKER_IMAGE` | `spicexplorer-spice-base:local` | the image used by the docker lane. |
| `LPF_DOCKER` | `shutil.which("docker")` or `docker` | the docker CLI. Set it for podman-style shims. |
| `LPF_VDD` | `1.5` | supply, volts. S6 is stated in **watts**, so changing this changes the current budget, not the power box. |
| `LPF_VICM` | `0.25` | input common mode. Low on purpose: both stages are p-type followers, so each biquad shifts the CM **up** by one \|Vgs\| (~0.46 V at 1 nA). See `doc/pdk-notes.md` §3. |
| `LPF_VOCM` | `1.25` | expected output CM — used only as the `.nodeset` dc hint. |
| `LPF_JOBS` | `max(2, cpu_count − 2)` | concurrency cap for `lab.parallel.batch`. Each ngspice is single-threaded but container start-up is not, so leave a couple of cores free. |
| `LPF_EXP` | *(empty)* | stamped into every ledger row's `exp` field by `lab.ledger.log_run`, so a batch can be filtered back out by experiment number. Set it to the experiment directory number while working in one. |
| `LPF_LANE` | *(empty)* | `docker` forces the docker lane even on a host that qualifies for native (`lab.config._native_default`). Any other value is ignored. |
| `LPF_BIAS_ALPHA` | `0` | temperature shaping of the ideal reference, `I(T) = iref·(T/300.15)^alpha`. `0` = constant current; `1` = constant gm (what a beta-multiplier delivers). It is an **ideal** shaping — it bounds what a bias circuit could buy, it does not model a real reference's own spread. See `doc/journal/bias-alpha-is-part-of-a-temperature-measurement.md`. |
| `LPF_CAP_CORNER` | `cap_typ` | the `cornerCAP.lib` section for `cap_model="cmim"` designs: `cap_typ` \| `cap_bcs` (0.9×) \| `cap_wcs` (1.1×). A cap-corner run is a separate invocation, like `LPF_BIAS_ALPHA`. |

Read by the tooling rather than by `lab.config`: `LPF_XSCHEM` (a host xschem
binary ⇒ the native netlisting lane, `lab/xsch.py`), `LPF_SIGNOFF_SET`
(`pre-pvt` \| `post-pvt`, `scripts/plot_signoff.py`), `PDK_ROOT` and
`SPICE_USERINIT_DIR` (where the PDK and its `.spiceinit` live).

---

## 3. Running one deck by hand

The harness builds decks (`lab.deck`), never text-edits them — but when a run
misbehaves you want the raw thing. The frozen reference bench is a complete,
self-simulating deck:

```sh
mkdir -p /tmp/handrun && cp decks/reference/lpf_tb.sp /tmp/handrun/deck.sp
docker run --rm -v /tmp/handrun:/w -w /w -u "$(id -u):$(id -g)" \
    spicexplorer-spice-base:local ngspice -b deck.sp
#   native: cd /tmp/handrun && "$LPF_NGSPICE" -b deck.sp
```

It writes `sim.raw` containing three plots (op, ac, noise spectrum) — read them
with the repo's reader rather than by eye:

```sh
python -c "from lab.raw import read_raw; [print(p.name, len(p.vectors)) for p in read_raw('/tmp/handrun/sim.raw')]"
```

Every harness run leaves the same artefacts in `LPF_WORK/<tag>/`: `deck.sp`,
`ngspice.out` (stdout + stderr), `wall.txt`, and the rawfiles. **Read
`ngspice.out` first** on any surprise — most of §4 is invisible in the rawfile
and obvious in the log.

---

## 4. Gotchas — the full list

Nine traps, all hit here, all of which produce a *plausible wrong answer*
unless handled. Numbered so other docs can cite them.

### 4.1 `write` emits only the CURRENT plot

A multi-analysis deck that ends in a single `write` silently stores one
analysis. The reference deck's `.control` block is the pattern to copy:

```spice
.control
set filetype=binary
set appendwrite
op
write sim.raw
ac dec 50 0.1 100000
write sim.raw
noise v(voutp,voutn) vsig dec 50 0.1 1000
setplot noise1
write sim.raw
.endc
```

`set appendwrite` plus **one `write` per analysis**. `setplot noise1` is
required to reach the noise **spectrum** — the `noise` command leaves the
*integrated* plot (`noise2`) current, and `noise2` holds a whole-sweep integral
over 0.1 Hz–1 kHz, which is not the S5 band and is meaningless on a 250 Hz
filter.

**Plot names are only deterministic when each analysis runs exactly once.** A
`while`/`repeat` loop that re-runs `op` renumbers the plots, and `setplot
noise1` then silently addresses the *wrong* plot. If you need a loop, write to
a per-iteration rawfile instead of relying on plot numbering.

### 4.2 An explicit `save` list STARVES the noise analysis

```
Error: no data saved for Noise analysis; analysis not run
```

ngspice prints that, **then leaves the previous plot current**, so the rawfile
silently contains the AC plot **twice** and the scorecard reads NaN for S5
instead of failing. Fix: the ac+noise deck must **not** restrict its saves.
Only the transient deck uses `save` (see §4.9), where the file size actually
matters. This is documented at `lab.deck.SIGNAL_NETS`.

### 4.3 `.nodeset` inside a subckt must be instance-qualified

```
Warning : Nodeset on non-existent node
```

That is the *entire* consequence — a warning and a no-op. An unqualified
`.nodeset v(vout_1)=1.25` looks like it worked and changes nothing. Correct
form:

```spice
.nodeset v(xdut.vout_1)=1.25 v(xdut.vout_2)=1.25 v(voutp)=1.25 v(voutn)=1.25
```

Top-level nets (`voutp`, `voutn`) need no prefix; DUT-internal nets do.

### 4.4 The noise analysis' input source needs `ac 1`

```
doAnalyses: ac input not found
```

ngspice aborts. The differential source must carry an explicit ac spec even
when the deck is driving a transient:

```spice
vsig sig vcm dc 0 ac 1                        ; ac + noise deck
vsig sig vcm dc 0 sin(0 87.5m 50) ac 1        ; THD deck — the `ac 1` still has to be there
```

This is also what makes the noise referral correct: the balun (`evp`/`evn` at
±0.5) means `vsig`'s own amplitude **is** the differential input, so
`inoise_spectrum` is directly the differential input-referred density.

### 4.5 Use `.nodeset`, never `.ic`, for dc hints

A **nodeset** is a hint the solver is free to leave. An **`.ic` is a clamp held
through the operating point** — and clamping this circuit lands it in a latched
basin that solves cleanly, looks like a valid dc point, and **scores as a
pass**. There is no error message. `lab.deck._core` emits `.nodeset` only.

### 4.6 Bias mirror diodes must use the design's OWN unit geometry at m = 1

An arbitrary diode geometry scales **every** branch current by a W/L ratio.
Observed failure: the internal node rails, the shunt-feedback device switches
off entirely, and **the ac response still looks like a plausible (mis-tuned)
low-pass** — a wrong fc, not an error. `lab.deck._bias` builds the mirror
diodes from `bias_*_int` / `bias_*_out` at `m = 1`, so a bias device drawn at
`m = k` carries exactly `k · iref` by construction.

### 4.7 ngspice returns exit code 0 after a failed dc operating point

It leaves a rawfile **full of zeros**. Nothing raises. A zero-filled result
that scores as a PASS is the single most expensive failure mode in this
harness, so `lab.ngspice._check_convergence` scans stdout for fatal strings and
raises `SimError`:

```
doAnalyses: iteration limit reached
Transient solution failed
singular matrix
no such vector
Unknown model type
could not find a valid modelname
```

If you add an analysis, add its failure string to that tuple. **Never** trust a
return code from this simulator.

### 4.8 Operating-point device parameters need a `save` before a sweep

Address them through the subcircuit path and the model name:

```spice
save @n.xdut.xm2.nsg13_hv_pmos[gm] @n.xdut.xm3.nsg13_hv_nmos[gds]
```

i.e. `@n.<instance path>.n<model>[<param>]`. **Named after a sweep starts, they
read back as a constant** — the value from the first point, repeated. Name them
in the `save` first.

### 4.9 A PSP103 device stores ~750 internal nodes per instance

Without a `save`, a 16-transistor run writes ~12 000 vectors of transient data.
That is why the transient deck restricts its saves to the signal nets and the
probe currents — and why the ac+noise deck **cannot** (§4.2). If a transient
rawfile is hundreds of MB, the `save` list was dropped.

---

## 5. Rules carried forward from the originating campaign

Lane-independent, not re-measured here, but they cost sessions there and the
mechanism is not technology-bound:

- **`pkill -f <script>.py` kills your own shell** when the pattern matches the
  invoking command line. Use `kill $(pgrep -f ...)` from a different pattern.
- **Judge passband flatness two-sided only up to ~0.6·fc (≤ 150 Hz), and
  no-peaking one-sided above it.** A ±ripple rule applied *through* the corner
  (flatness at 245 Hz plus −3 dB at 247 Hz) is infeasible by construction and
  makes a correct design look impossible. `lab.metrics` scores `dc_db` at the
  first ac point and `peak_db` as a one-sided max — keep it that way.
- **Instance names are not unique across a deck.** Any text mutator must be
  scoped to the DUT subckt span and must raise on 0 or >1 matches. This repo
  sidesteps it by *building* decks from a `Design` instead of editing text
  (`lab.deck` docstring) — do not reintroduce text mutation.

See `doc/prior-findings.md` for the full carried-forward list and its
technology classification.
