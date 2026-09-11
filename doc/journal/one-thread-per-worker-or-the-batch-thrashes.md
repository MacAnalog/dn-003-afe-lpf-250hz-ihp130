# 2026-08-29 — One thread per worker, or the batch runs 20× slower than one process suggests

KIND: journal entry | type: procedural | status: live

**Corrected in place 2026-09-10.** The rule below held and still holds; the
*explanation* under it was wrong, and because it was wrong the rule capped the
workers while leaving ngspice's own threads uncapped. This is a partial
correction in the sense of `doc/memory/README.md` §5 — the verdict survives, the
mechanism is struck — so the entry stays `live` rather than being retired: a
batch still needs this rule, and a retired entry never reaches the context pack.
Dead claims are marked `~~…~~ **CORRECTED 2026-09-10**` where they stand.
Everything labelled *(2026-08-29)* is as originally measured on the 128-core
host; everything labelled *(R1–R5)* is a 2026-09-10 measurement on the 16-core
lab workstation and does **not** describe that host.

**The trap.** A single extraction takes **1.1 s wall** on this host — and **13.6 s of
CPU** *(2026-08-29)* — ~~because ngspice runs the PSP/OSDI device evaluation
multithreaded and helps itself to about eleven threads~~ **CORRECTED 2026-09-10**:
ngspice *is* multithreaded on this repo's decks, but "eleven" matches nothing
checkable. 13.6/1.1 = 12.4 is the CPU/wall ratio restated, not a counted team; that
host's ngspice would have run **2** threads with no `num_threads` set, **8** with the
stock `spinit`, or whatever it set. Leave the number unresolved rather than
re-attribute it. `lab.parallel` defaults to `cpu_count() - 2` workers, so a 1024-draw
Monte Carlo asks for 126 ~~processes~~ **workers** × an unknown thread count on 128
cores. Nothing errors; it just crawls. (Second correction: `lab/parallel.py:10-11`
wraps a **thread** pool, so that is one Python process with 126 worker threads and 126
ngspice children — not 126 processes. It also means there is one numpy/OpenBLAS pool
per *campaign*, not one per draw.)

**What it cost** *(2026-08-29, unchanged)*. The first attempt at the 1024-draw run was
measured at **5 draws per minute** (load average 619), an ETA of **156 minutes** for
work that should take ten. The per-process wall time had gone from 1.1 s to about 17 s
while each process still used only 4 CPU-seconds — that ratio, high concurrency with
idle-looking workers, is the signature of oversubscription rather than of a slow bench.

**The fix, measured** *(2026-08-29, numbers unchanged)*. With `OMP_NUM_THREADS=1` a
draw costs **4.4 CPU-seconds** instead of 13.6, with no change in its wall time.
~~the threads were pure overhead at this problem size~~ **CORRECTED 2026-09-10**: the
env var never reached ngspice (see below), so it did not cut the simulator's threads —
and note 4.4/1.1 is still a ratio of **4.0**, i.e. something stayed multithreaded that
the env var demonstrably did not touch. Throughput is highest at **~32 workers,
1.8 draws/s** (128 draws in 70 s); at 64 workers it drops to 0.69 draws/s, so more
workers is worse well before the core count. 1024 draws then take about ten minutes.

**What the explanation got wrong.** Three things, in order of how load-bearing they are.

1. **`OMP_NUM_THREADS` cannot control ngspice — on any host.**
   `ngspice-45/src/spicelib/analysis/cktsetup.c:89-92`, inside `#ifdef USE_OMP`:
   `if (!cp_getvar("num_threads", CP_NUM, &nthreads, 0)) nthreads = 2;` then
   `omp_set_num_threads(nthreads);`. That call is unconditional and runs at every
   circuit setup, and an explicit `omp_set_num_threads()` overrides the
   `OMP_NUM_THREADS` ICV. It is the only such call in the tree. So whatever that
   host's `spinit` said, the env var could not have moved the simulator's thread
   count — the 13.6 → 4.4 drop is **not** ngspice.
2. **The fix was confounded.** Two knobs moved together — the env var *and*
   `LPF_JOBS` 126 → 32 — and no 32-worker run was recorded **without** the env var.
   Our own 1.8-vs-0.69 draws/s at 32 vs 64 workers explains the recovery by the
   worker cap alone. The cap is demonstrated; the env var's contribution is not.
3. **Where the 9.2 CPU-s probably went — hypothesis, not a measurement.**
   `OMP_NUM_THREADS` also sets OpenBLAS's thread count, and the draw path runs in a
   numpy process (`lab/raw.py`, `lab/metrics.py`). A parent-process BLAS pool that
   spins and then sleeps fits the observed shape — large CPU drop, unchanged wall —
   and dn-004 later measured the same lane's parent at 6531 % CPU with zero ngspice
   children. **Nobody measured it here.** What is established is only "not ngspice's
   device-eval thread count".

**What ngspice actually does** *(R1–R5, macanalog-ws1, 16 cores, native ngspice-45,
PSP103-via-OSDI deck, `.tran 20p 400n` — this host only)*.

- **R1** — uncapped vs `OMP_NUM_THREADS=1`, 60 devices, 3 reps alternating: CPU/wall
  7.04/7.05/7.05 vs 7.02/7.02/7.02. The env var changes **nothing**, as §1 predicts.
- **R2** — ngspice's own knob: default 10.46 s wall / 73.40 s CPU (7.02);
  `set num_threads=1` 14.01 s wall / 13.85 s CPU (0.99). The knob works. On *this*
  deck the thread team buys **1.34× wall for 5.3× CPU** — about 17 % parallel
  efficiency. (A draw here is `.op` + `ac dec`, a much smaller problem, so do not
  assume the same 1.34× applies to it in either direction.)
- **R3** — `/proc/<pid>/status` reports `Threads: 8` during a default run.
- **R4** — 1, 2, 4, 8, 16, 32, 60 devices: ratio 7.47 → 7.92. The team spins up for
  **one transistor**, which is the tell that most of the CPU is not device evaluation:
  `src/osdi/osdiload.c:190-191` opens `#pragma omp parallel` / `#pragma omp single`
  *before* any instance count is known and issues one `#pragma omp task` per instance
  (`:204`) on every device-load call — every Newton iteration of every timestep. One
  task, seven threads at the implicit barrier; ngspice sets neither `OMP_WAIT_POLICY`
  nor `GOMP_SPINCOUNT` (`grep -rn` over `src/` returns nothing), so libgomp busy-waits
  and the spin is charged to user time. The matrix-stamping loop after the region
  (`:215-227`) is serial, as are KLU factor/solve.
- **R5** — the 8 is **upstream stock, not a lab misconfiguration**:
  `ngspice-45/src/spinit.in:14` is `set num_threads=8`, and the installed
  `share/ngspice/scripts/spinit` is identical to the release template. The
  `spicexplorer-spice-base` image builds the same v45 tarball `--enable-openmp` and
  ships that spinit, so **the docker lane is `num_threads=8` too**. Deleting the line
  does not help: `cktsetup.c:89-90` then falls back to a hard-coded **2**, still
  env-deaf.

**Which decks this applies to.** Only OSDI and BSIM3/BSIM3v32/BSIM4/v5/v6/v7/BSIMSOI/
HiSIM2 have an OpenMP load path — `grep -rl "pragma omp" src/` returns exactly
`osdi/osdiload.c` plus those eight device dirs, nothing else. **This repo is in the
covered class**: `decks/reference/lpf_tb.sp:4-19` instantiates `sg13_hv_pmos` /
`sg13_hv_nmos`, which are PSP 103.6 loaded as `psp103_nqs.osdi`. A lane whose decks are
B-sources, R/C and HICUM devices enters no parallel region at all and is honestly
single-threaded on this very binary — which is why another repo's "the simulator
children are single-threaded" can be true there and false here.

**The rule, corrected.** Two knobs, not one:

    # (a) the generated deck's .control block (lab/deck.py:330), first line:
    set num_threads=1
    # (b) the shell, for THIS process's BLAS pool -- not for ngspice:
    export OMP_NUM_THREADS=1 LPF_JOBS=32

(a) is the one that caps ngspice, and the deck is the **only** lane-proof place for it:
`lab/ngspice.py:99-104` builds `docker run --rm -v … -u … image ngspice -b deck.sp` with
no `-e`, so no exported variable ever crosses into the container. R2 shows a `set`-level
value takes effect because `cp_getvar` runs at analysis time. Without it, the "fixed"
configuration was still 32 workers × 8 threads = **256 runnable threads on 128 cores**.
(b) stays — it is correct for numpy/OpenBLAS, most likely what the 13.6 → 4.4 drop
actually was — but do not credit it to the simulator.

Three traps around (a). The **frozen reference deck is sha-lint-pinned and must never be
hand-edited**, so it can only take the setting from `$SPICE_USERINIT_DIR/.spiceinit` on
the native lane. That lookup is **first-match-wins** (`main.c:1267-1320`: deck dir →
`$SPICE_USERINIT_DIR` → cwd → `$HOME`, `break` on the first that reads, exactly one file)
— so dropping a `.spiceinit` into a run directory would shadow the PDK's file and
silently kill its `osdi` loads. And **~32 workers is the knee measured under the old
uncapped-ngspice regime**; with the decks capped at one thread the optimum may well move
up, so re-measure it rather than treating 32 as physics.

**Two false leads worth naming** *(2026-08-29, unchanged)* so they are not re-followed:
the work directory had accumulated 24 248 entries and 8.8 GB, and clearing it changed
throughput by **4 %** — it was not the cause; and the historical "64 extractions in
31.5 s" note is about **2 draws/s**, which is the same rate the fixed configuration
reaches, so that number never implied 126-way scaling.

**Where the check lives.** Still nowhere automatic — this is a contract, not a lint. Two
symptoms now, not one: a load average several times the core count while `ps` shows the
workers at ~100 % CPU each; and, for the simulator half, a single deck run under
`/usr/bin/time` whose CPU/wall ratio is far above 1. That second check is the cheap one
and it is the one that would have caught this in 2026-08: `OMP_NUM_THREADS=1` leaves the
ratio unchanged, `set num_threads=1` drives it to ~1.
**The cheapest fix of all, measured after the above** *(R6, 2026-09-10, 16-core
workstation, 60-device PSP103 deck, 2 alternating reps)*. Most of that CPU is not work —
it is libgomp busy-waiting at the task barrier, and one environment variable removes it
without touching a deck:

| setting | wall | CPU | CPU/wall |
|---|---|---|---|
| default | 10.53 s | 73.6 s | 6.99 |
| `OMP_WAIT_POLICY=PASSIVE` | 11.83 s | 23.6 s | **2.00** |
| `GOMP_SPINCOUNT=0` | 11.91 s | 24.1 s | 2.02 |
| `set num_threads=1` | 14.01 s | 13.9 s | 0.99 |

So of 73.6 CPU-seconds, about **50 (68 %) was pure spin**; real parallelism is ~2×, not
8×. `OMP_WAIT_POLICY` *is* honoured — ngspice never calls `omp_set_wait_policy`, so
libgomp reads the environment — which makes it the one knob that works from a wrapper
script, needs no deck edit, and cannot shadow the PDK's `.spiceinit`. For a batch,
prefer `set num_threads=1` (lowest CPU per draw, 1.34× wall) and fall back to
`OMP_WAIT_POLICY=PASSIVE` wherever the deck cannot be touched.

**The corrected rule.**

    export OMP_NUM_THREADS=1 OMP_WAIT_POLICY=PASSIVE LPF_JOBS=32   # then re-measure the knee

`OMP_NUM_THREADS=1` stays — it is right for numpy/OpenBLAS. `OMP_WAIT_POLICY=PASSIVE` is
the new half, and it is the one that reaches the simulator.
