# 2026-08-29 — One thread per worker, or the batch runs 20× slower than one process suggests

KIND: journal entry | type: procedural | status: live

**The trap.** A single extraction takes **1.1 s wall** on this host — and **13.6 s of
CPU**, because ngspice runs the PSP/OSDI device evaluation multithreaded and helps itself
to about eleven threads. `lab.parallel` defaults to `cpu_count() - 2` workers, so a
1024-draw Monte Carlo asks for 126 processes × 11 threads ≈ **1400 runnable threads on
128 cores**. Nothing errors; it just crawls.

**What it cost.** The first attempt at the 1024-draw run was measured at **5 draws per
minute** (load average 619), an ETA of **156 minutes** for work that should take ten. The
per-process wall time had gone from 1.1 s to about 17 s while each process still used only
4 CPU-seconds — that ratio, high concurrency with idle-looking workers, is the signature
of oversubscription rather than of a slow bench.

**The fix, measured.** `OMP_NUM_THREADS=1` cuts a draw from 13.6 to **4.4 CPU-seconds**
with no change in its wall time — the threads were pure overhead at this problem size.
With one thread per worker, throughput is highest at **~32 workers, 1.8 draws/s** (128
draws in 70 s); at 64 workers it drops to 0.69 draws/s, so more workers is worse well
before the core count. 1024 draws then take about ten minutes.

    export OMP_NUM_THREADS=1 LPF_JOBS=32

**The rule.** Any batch of more than a few dozen netlist-lane runs sets
`OMP_NUM_THREADS=1` and caps `LPF_JOBS` around 32. The pack README's regeneration block
does both. Two false leads are worth naming so they are not re-followed: the work
directory had accumulated 24 248 entries and 8.8 GB, and clearing it changed throughput by
**4 %** — it was not the cause; and the historical "64 extractions in 31.5 s" note is
about **2 draws/s**, which is the same rate the fixed configuration reaches, so that
number never implied 126-way scaling.

**Where the check lives.** Nowhere automatic yet — this is a contract, not a lint. The
symptom to recognise is a load average several times the core count while `ps` shows the
workers at ~100 % CPU each and the batch is slower than a serial estimate.
