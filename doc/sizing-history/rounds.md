# Sizing history — every round attempted, and what it returned

**KIND: REFERENCE.** Built from the round JSONs by
[`build.py`](build.py), never typed; [`rounds.json`](rounds.json) is the
machine-readable twin. `PASS` means all nine lines met at the nominal corner;
`fail(n)` counts the spec lines missed (THD is scored separately and is not in
that count, so a `fail(0)` row is one that met the cheap box and missed S7).

The dead ends are kept deliberately. Two of them are the most useful rows here:
`qwalk` (Q allocation does **not** set THD — the fit pulls it straight back) and
`vdd2_area` (growing **all** device areas buys mismatch yield and then fails S1
on phase, where growing only the bias devices does not).

## `qwalk` — Walk biquad B's Q allocation at fixed w0 — the THD hypothesis (FALSIFIED)

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `qw_r0p4` | 90.55 | 0.0000 | -47.15 | 250.0 | 33.44 | 6.60 | 210.9 | -41.87 | — | fail(4) |
| `qw_r0p6` | 259.38 | 4.7455 | -47.89 | 307.0 | 26.30 | 6.60 | 246.4 | -26.13 | — | fail(5) |
| `qw_r1` | 249.86 | 0.0002 | -48.77 | 337.4 | 27.24 | 6.60 | 167.0 | -35.77 | — | fail(0) |
| `qw_r1p6` | 249.84 | 0.0000 | -48.64 | 337.2 | 27.25 | 6.60 | 166.7 | -36.31 | — | fail(0) |
| `qw_r2p5` | 10.91 | 0.0000 | -48.02 | 133.0 | 84.56 | 6.60 | 1602.8 | -36.95 | — | fail(4) |
| `qw_r4` | 55.57 | 0.0000 | -47.29 | 239.6 | 28.66 | 6.60 | 293.0 | -39.48 | — | fail(4) |

## `fitcells` — Template re-fit of the frozen 020B/020C cells

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `020B-frozen` | 249.85 | 0.0000 | -48.99 | 368.6 | 28.05 | 5.39 | 135.1 | -44.78 | — | **PASS** |
| `020C-frozen` | 249.86 | 0.0000 | -49.04 | 359.8 | 39.70 | 4.15 | 104.4 | -41.69 | — | **PASS** |
| `020B-cert` | 249.85 | 0.0000 | -48.30 | 346.1 | 33.95 | 9.69 | 241.6 | -40.24 | — | **PASS** |

## `scale` — Uniform I–C scaling of 020C (devices + iref + caps × k)

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `020C-frozen_x1` | 249.86 | 0.0000 | -49.04 | 339.8 | 39.70 | 4.15 | 104.4 | -41.69 | — | **PASS** |
| `020C-frozen_x1.5` | 250.14 | 0.0000 | -49.40 | 339.6 | 32.46 | 5.99 | 153.2 | -40.50 | — | **PASS** |
| `020C-frozen_x2` | 250.06 | 0.0000 | -49.56 | 339.5 | 28.12 | 7.88 | 202.7 | -39.97 | — | fail(0) |
| `020C-frozen_x2.5` | 250.00 | 0.0000 | -49.64 | 339.5 | 25.16 | 9.78 | 252.5 | -39.71 | — | fail(0) |
| `020C-frozen_x3` | 249.97 | 0.0000 | -49.68 | 339.5 | 22.97 | 11.70 | 302.4 | -39.56 | — | fail(0) |

## `area` — Gate area at fixed W/L on the stacked hv cell

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `area_x1.32` | 249.93 | 0.0154 | -49.80 | 337.3 | 31.39 | 6.00 | 151.8 | -40.03 | 75 % | **PASS** |
| `area_x1.69` | 249.87 | 0.0000 | -49.60 | 333.3 | 30.71 | 6.01 | 150.6 | -42.22 | 78 % | **PASS** |
| `area_x2.10` | 249.98 | 0.0226 | -50.36 | 331.3 | 30.15 | 6.03 | 150.7 | -40.96 | 67 % | **PASS** |

## `lvcm` — lv input follower, common mode raised

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `lc50` | 249.86 | 0.0000 | -49.93 | 332.9 | 29.36 | 6.01 | 153.2 | -41.59 | — | **PASS** |
| `lc60` | 249.86 | 0.0000 | -49.92 | 332.8 | 29.37 | 6.01 | 153.0 | -41.62 | — | **PASS** |
| `lc65` | 249.85 | 0.0000 | -49.89 | 332.2 | 29.38 | 6.01 | 152.9 | -41.90 | — | **PASS** |

## `lv065_bias` — Bias-device area on the stacked lv cell

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `sb3` | 249.85 | 0.0000 | -49.78 | 332.8 | 28.54 | 6.46 | 164.0 | -42.39 | 84 % | **PASS** |
| `sb6` | 249.70 | 0.0000 | -49.02 | 330.8 | 28.50 | 6.58 | 165.1 | -44.80 | 50 % | **PASS** |

## `unstacked75` — Unstacked topology at vicm = VDD/2, k-scaled

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `u75k1` | 249.40 | 0.2122 | -51.24 | 346.6 | 51.78 | 12.06 | 125.3 | -42.43 | — | fail(3) |
| `u75k2` | 249.86 | 0.0006 | -48.92 | 343.9 | 36.55 | 24.13 | 244.7 | -44.86 | — | **PASS** |
| `u75k3` | 250.95 | 0.0951 | -51.21 | 346.1 | 30.22 | 36.19 | 380.6 | -42.79 | — | **PASS** |

## `vdd2_area` — All-device area on the VDD/2 cell (costs phase)

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `ua1p6` | 249.86 | 0.0000 | -49.89 | 334.9 | 31.24 | 24.07 | 242.1 | -45.09 | 39 % | **PASS** |
| `ua2p4` | 249.86 | 0.0000 | -52.20 | 322.5 | 28.99 | 24.04 | 237.0 | -45.56 | — | fail(1) |

## `vdd2_bias` — Bias-only area on the VDD/2 cell (does not cost phase)

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `ub2` | 249.86 | 0.0004 | -48.91 | 343.4 | 35.22 | 24.05 | 244.4 | -44.88 | 50 % | **PASS** |
| `ub3` | 249.88 | 0.0032 | -49.02 | 343.0 | 34.97 | 24.03 | 244.7 | -44.76 | 72 % | **PASS** |

## `vdd2_bias2` — Bias-only area, pushed further

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `uc4` | 249.88 | 0.0059 | -49.09 | 342.6 | 34.91 | 24.02 | 244.8 | -44.70 | 78 % | **PASS** |
| `uc6` | 249.90 | 0.0071 | -49.15 | 341.8 | 34.85 | 24.01 | 245.0 | -44.64 | 82 % | **PASS** |

## `reuse` — lv gmf_b + ladder sizing — the current-reuse fix, and the deliverable

| cell | fc | mono | @1k | ph | IRN µV | P nW | C pF | THD | MC | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `cr_0p06_4` | 249.86 | 0.0000 | -50.75 | 330.8 | 30.26 | 6.82 | 175.1 | -52.77 | — | **PASS** |
| `cr_0p06_6` | 249.87 | 0.0000 | -52.61 | 320.5 | 31.34 | 4.52 | 117.6 | -51.90 | — | fail(1) |
| `cr_0p1_4` | 249.86 | 0.0000 | -50.35 | 331.6 | 29.34 | 7.31 | 187.9 | -52.29 | — | **PASS** |
| `cp_0p16_4` | 249.86 | 0.0000 | -49.84 | 333.5 | 28.33 | 8.98 | 229.3 | -52.64 | — | **PASS** |
| `cp_0p25_4` | 249.91 | 0.0075 | -49.62 | 336.0 | 27.44 | 11.96 | 303.7 | -53.85 | — | **PASS** |
| `cp_0p16_2p5` | 249.99 | 0.0068 | -49.55 | 341.4 | 28.07 | 14.45 | 366.3 | -56.46 | — | **PASS** |

---

**37 sizing points across 11 rounds; 25 met all nine lines.**