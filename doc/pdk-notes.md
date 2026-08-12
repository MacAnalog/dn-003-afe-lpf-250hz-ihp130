# PDK notes — IHP SG13G2 device map for this filter

**KIND: REFERENCE.** Read this *before* choosing a device flavour, a length, or
a bias point. Every number below was measured in this repo with ngspice 45 +
OSDI against the installed SG13G2 model cards, at 27 °C, on single devices —
not carried forward from anywhere. Where a claim is arithmetic on a measured
number rather than a measurement, it says so.

The PDK is **open source (Apache-2.0)**. There is no NDA: model cards, corner
files, device parameters and simulator logs may be read, quoted, diffed and
committed. The only standing rule is the weaker one — **never commit PDK
content or generated rawfiles into this repo**; reference them by name and let
`sourcepath` resolve them.

---

## 1. What a deck must include

Models are referenced by **bare filename**, resolved by ngspice's `sourcepath`,
which the lane sets up (`doc/environment.md`). Decks therefore carry no host
paths and are byte-identical between the Docker and native lanes.

```spice
.lib cornerMOShv.lib mos_tt        ; sg13_hv_nmos / sg13_hv_pmos  <- what this design uses
```

The four library files and their roles (`lab/config.py:MOS_LIB_LV/HV/CAP_LIB/RES_LIB`):

| library | devices it defines | section names |
|---|---|---|
| `cornerMOShv.lib` | `sg13_hv_nmos`, `sg13_hv_pmos` (3.3 V class, thick oxide) | `mos_tt` `mos_ss` `mos_ff` `mos_sf` `mos_fs` |
| `cornerMOSlv.lib` | `sg13_lv_nmos`, `sg13_lv_pmos` (1.5 V class, thin oxide) | same five |
| `cornerCAP.lib` | `cap_cmim` (MIM), `cap_rfcmim` | **read them out of the installed file — do not guess** |
| `cornerRES.lib` | `rsil`, `rhigh`, `rppd` | **read them out of the installed file — do not guess** |

The five MOS section names are the corner set this repo scores
(`lab.config.CORNERS`, nominal `mos_tt`). The reference deck draws **ideal
linear capacitors** (`c13 net2 vout_1 2.94678e-11`), so it needs no cap library
today; the moment a physical `cap_cmim` is instantiated, the matching
`.lib cornerCAP.lib <section>` line has to be added and the section name taken
from the installed library, not from this doc.

### Instantiation syntax

Every SG13G2 device is a **subcircuit**, so instances are `x`-prefixed:

```spice
xm2  net2 vinp vout_1 vout_1  sg13_hv_pmos  w=4e-06 l=4e-06 ng=1 m=1
xm3  net2 vbn  0      0       sg13_hv_nmos  w=5e-06 l=8e-06 ng=1 m=1
```

Terminal order is **D G S B**. Never rely on a default `l` — always write it.
Operating-point parameters of a device inside the DUT are addressed through the
subcircuit, e.g. `@n.xdut.xm2.nsg13_hv_pmos[gm]`, i.e.
`@n.<instance path>.n<model name>[<param>]`; they must be named in a `save`
*before* a sweep or they read back as a constant (`doc/environment.md` §4.8).

### The OSDI requirement (non-negotiable)

SG13G2 MOS devices **are PSP 103.6 Verilog-A compact models**, loaded as
OpenVAF-compiled OSDI objects. A stock ngspice cannot simulate this PDK at all:

```
Unknown model type psp103va
```

That string is in `lab.ngspice._FATAL`, so a lane without the `.osdi` objects
fails loudly instead of producing zeros. Both lanes must load them
(`doc/environment.md` §2).

---

## 2. Device flavours — and why this design is all-`hv`

The originating design used thick-oxide, long-channel devices at nano-amp bias.
The SG13G2 equivalent is the **hv (3.3 V, thick oxide)** pair, not the lv pair.
Three independent measurements force that choice, and the third one is
decisive.

### 2.1 gm/ID at the weak-inversion limit (⇒ the body factor n)

`n` is arithmetic on the measured gm/ID limit: `n = 1/(gm/ID · U_T)`,
`U_T = 25.85 mV` at 27 °C.

| device | gm/ID max (V⁻¹) | n (arithmetic) |
|---|---|---|
| `sg13_hv_nmos` | **28.1** | **1.38** |
| `sg13_hv_pmos` | **25.1** | **1.54** |
| `sg13_lv_nmos` | 31.9 | 1.21 |
| `sg13_lv_pmos` | 32.0 | 1.21 |

The lv pair is closer to ideal (n = 1.21), which matters only for a
bulk-at-rail follower — see §3.

### 2.2 Vgs needed to carry 1 nA (W = 10 µm)

| device | L | Vgs at I_D = 1 nA |
|---|---|---|
| `sg13_hv_nmos` | 4 µm | **+0.36 V** |
| `sg13_hv_pmos` | 4 µm | **−0.46 V** |
| `sg13_lv_pmos` | 4 µm | −0.18 V |
| `sg13_lv_nmos` | — | **cannot reach 1 nA** — see below |

**`sg13_lv_nmos` cannot be biased at 1 nA at these geometries.** At W = 17 µm /
L = 8 µm it already carries **2.5 nA at Vgs = 0**, and **3.57 nA at
W = 10 µm / L = 4 µm**. There is no gate voltage that puts it at the design's
branch current, so it is unusable for every role in this filter — signal
device, shunt-feedback transconductor and bias tail alike. This alone closes
the lv-nmos question.

### 2.3 Output resistance: gm/gds at 1 nA vs channel length

| device | L = 0.5 µm | L = 4 µm | L = 20 µm |
|---|---|---|---|
| `sg13_hv_nmos` | 58.6 | **1200** | **8170** |
| `sg13_hv_pmos` | 242 | **3710** | **8700** |
| `sg13_lv_nmos` | 33 | 59 | 91 |
| `sg13_lv_pmos` | 651 | 3690 | 5080 |

The hv n-channel device beats the lv n-channel device by **20×** at L = 0.5 µm
and by **90×** at L = 20 µm. That matters directly: `H(0)` of the follower
biquad is pinned at 1 by shunt feedback only to the extent that `g_ds` is
negligible against `gm`, and S3 allows |dc| ≤ 0.2 dB total.

### 2.4 Drain leakage at Vgs = 0 (W = 10 µm)

| device | I_D at Vgs = 0 |
|---|---|
| `sg13_hv_nmos` | ~5 × 10⁻¹⁴ A |
| `sg13_hv_pmos` | ~1 × 10⁻¹³ A |
| `sg13_lv_pmos` | 1 × 10⁻¹² … 3 × 10⁻¹¹ A |
| `sg13_lv_nmos` | **1.6 … 5.1 nA** |

At a 1 nA branch current the lv-nmos "off" current is **1.6–5× the signal
current**. The hv devices leak 4–5 orders of magnitude below the branch.

### 2.5 Gate-referred noise, integrated 0.5–200 Hz, at I_D = 1 nA

This is the band S5 is scored over, so it is the only noise number worth
comparing devices on.

| W/L (µm) | `sg13_hv_nmos` | `sg13_hv_pmos` | `sg13_lv_pmos` |
|---|---|---|---|
| 10 / 8 | **10.95 µV** | 11.18 µV | 12.35 µV |
| 17 / 8 | **10.38 µV** | 11.31 µV | 11.61 µV |
| 12 / 4 | 11.72 µV | 12.18 µV | 13.24 µV |
| 2 / 100 | 11.39 µV | 13.44 µV | 13.20 µV |

(`sg13_lv_nmos` has no row: it cannot be held at 1 nA, §2.2.)

Spread across every flavour and geometry is **10.38 … 13.44 µV**, i.e. ±13 %
around 11.9 µV. **Device flavour is not a noise lever here.** Big-WL /
small-I_B still helps at the margin (17/8 beats 12/4 by 1.3 µV on the hv
n-channel device), but nothing in this table buys the −20.3 % that S5 needs.

### 2.6 Conclusion, as recorded

> **hv is the correct map for the originating design's thick-oxide long-L
> devices** — comparable flicker noise (§2.5, within 13 %), but **20–100×
> better gm/gds** (§2.3) and, decisively, **they can actually be biased at
> 1 nA** (§2.2, §2.4).

`lab.dut` hard-codes this: `NCH = "sg13_hv_nmos"`, `PCH = "sg13_hv_pmos"`.
VDD = 1.5 V against a 3.3 V-class oxide leaves the devices at less than half
their rated field, so there is no reliability term to trade against.

---

## 3. The constraint that changed the topology: no isolated NMOS

**SG13G2 has no deep-n-well / isolated NMOS.** An n-channel device's bulk is
the shared p-substrate and *cannot* follow its source. p-channel devices are
unaffected — each sits in its own n-well, so bulk = source is free.

Consequences, in order of how much they cost:

1. **An n-channel source follower has dc gain exactly 1/n.** In weak inversion
   `gmb = (n − 1)·gm`, so a gate-driven follower whose bulk sits at the rail
   divides by `n`. With n = 1.38 (§2.1) that is a floor of −2.79 dB — and no
   re-sizing recovers it, because `n` is a process constant, not a design
   variable.
2. **Measured on the alternating n/p structure the originating design used:**

   | stage | input follower | bulk | measured dc gain |
   |---|---|---|---|
   | A | n-type | shared p-substrate (forced) | **−2.328 dB** |
   | B | p-type | its own source (own n-well) | **−0.003 dB** |

   The n-stage alone overruns the S3 budget (|dc| ≤ 0.2 dB) by **more than
   10×**. −2.328 dB is `1/n_eff` with `n_eff = 1.308` (arithmetic:
   10^(−2.328/20) = 0.7644), i.e. slightly better than the weak-inversion limit
   because the device is not fully in the WI asymptote at this bias — but not
   remotely enough to matter.
3. **Fix: make both input followers p-type.** Unity gain is restored exactly
   (stage B measures −0.003 dB), and — more importantly — the **self-referenced
   gain** of the follower family is preserved: `H(0)` stays a property of one
   device's own ladder rather than a ratio between two devices. That is the
   property the candidate family's mismatch yield depends on
   (`doc/prior-findings.md` §4).
4. **Cost: the common mode now climbs one |Vgs| per stage** instead of
   cancelling between an n-stage and a p-stage. Absorbed by placing the input
   CM low: **VICM = 0.25 V → VOCM ≈ 1.25 V** at VDD = 1.5 V
   (`lab.config.VICM/VOCM`), which lands the output mid-supply with headroom on
   both rails. One |Vgs| is ~0.46 V for an hv p-channel device at 1 nA (§2.2),
   so two stages ≈ 0.92 V of climb, consistent with the 0.25 → 1.25 V measured
   placement.

Which roles are still n-channel, and why it is harmless: the shunt-feedback
transconductors and the internal-node bias sinks (`lab.dut.NROLES` =
`bias_a_int`, `gmf_a`, `bias_b_int`, `gmf_b`). Their **sources sit at ground**,
so bulk = source is satisfied by the substrate tie itself and there is no body
effect either way.

**A corollary for the paper corpus:** because this PDK forces n-channel bulks to
the rail, the bulk-effect self-neutralisation family (`bulk-neutral`,
`selfcomp-gain` in `pdf/INDEX.md`) is **no longer moot here** — it was moot in
the originating campaign only because every device there could tie bulk to
source. See `pdf/INDEX.md` and `doc/prior-findings.md`.

---

## 4. Passives

| primitive | library | notes |
|---|---|---|
| `cap_cmim` | `cornerCAP.lib` | MIM capacitor — the default for the filter's 98 pF |
| `cap_rfcmim` | `cornerCAP.lib` | RF variant; no reason to use it here |
| `rsil` | `cornerRES.lib` | silicided poly — low sheet, large area per MΩ |
| `rhigh` | `cornerRES.lib` | high-sheet poly — the candidate for any degeneration resistor |
| `rppd` | `cornerRES.lib` | p+ poly |

Total drawn capacitance is a **reported** number in this challenge, never a
spec line (reference baseline: 98.01 pF). A MOS capacitor (a gate-connected
device) is available as an area lever but has not been characterised here — its
C–V nonlinearity has to be measured against S7 before it is used.

`rhigh` matters for one specific reason carried forward from the originating
campaign: **only a genuine resistor can degenerate a subthreshold current
source**, because any MOS carrying the full branch current contributes ≥ 2qI
(`doc/prior-findings.md` §3). The required value scales as `R > 2·V_T/I`, which
at 1 nA is tens of MΩ — check `rhigh`'s sheet resistance and the resulting area
before designing around it.

---

## 5. Sizing checklist for an agent

1. Pick `sg13_hv_nmos` / `sg13_hv_pmos`. Do not use lv devices without first
   re-measuring §2.2 and §2.4 for your geometry.
2. Any device whose **source swings** must be p-channel (§3).
3. Target the weak-inversion limit: gm/ID ≈ 28 V⁻¹ (n) / 25 V⁻¹ (p). Check it
   in the operating point — there is no `region` code in ngspice, so gm/ID
   *is* the inversion-level test.
4. Check `V_DS > 4·kT/q` ≈ 103 mV on every bias tail. `gm/gds` collapse, not a
   region flag, is what catches a starved tail.
5. Use L ≥ 4 µm on anything whose output resistance is in the signal path
   (§2.3).
6. Every bias device must be an **integer multiple of the mirror unit**, and
   the mirror diode must be built from that same unit geometry at m = 1
   (`doc/environment.md` §4.6).
7. Noise: device flavour buys nothing (§2.5). Look at the bias sources and the
   capacitor allocation instead (`doc/prior-findings.md` §2–3).
