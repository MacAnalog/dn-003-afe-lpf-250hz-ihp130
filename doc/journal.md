# Journal — index

KIND: index

Kept deliberately small: **one line per entry**. The content lives in
[`doc/journal/`](journal/), one file per entry, so any single entry fits in an
agent context.

**Conventions.** Entries are **dated**, **typed** (`semantic` = distilled design
knowledge; `procedural` = harness / measurement / tooling recipes), and carry
**provenance** (ledger tags, deck hashes, experiment dirs, file:line, paper
eq/fig refs). They are **retired by supersession, never deleted** — prepend
`[superseded <date> — see X]` in the entry file and flip its `status:` line; the
context pack skips superseded entries.
**Adding an entry = write the file + add one line here (lint-enforced).**

Rows are sorted **newest first** (enforced by `scripts/lint.py`); rows sharing a
date are grouped by subject.

| date | entry | type | status | hook |
|---|---|---|---|---|
| 2026-08-11 | [nmos-bulk-tie](journal/nmos-bulk-tie.md) | semantic | live | no isolated NMOS in SG13G2 ⇒ an n-type follower's bulk is the shared substrate and its dc gain is exactly 1/n; measured −2.328 dB (n-stage) vs −0.003 dB (p-stage), against an S3 budget of 0.2 dB; n = 1.38 from gm/ID = 28.1 V⁻¹, so no sizing recovers it |
| 2026-08-11 | [all-p-followers](journal/all-p-followers.md) | semantic | live | the structural port decision: **both** biquads take a p-type input follower with an n-type shunt feedback — dc −2.3335 dB (`ref_v0`, alternating) → **−0.0047 dB** (`ref_fit`); keeps the self-referenced gain the family's mismatch yield rests on; cost = CM stacks one \|Vgs\| (~0.46 V) per stage, absorbed by VICM = 0.25 V ⇒ VOCM ≈ 1.25 V at VDD 1.5 V, no CMFB anywhere |
| 2026-08-11 | [phase-certificate-floor](journal/phase-certificate-floor.md) | procedural | live | the S1 certificate can be faked: ±180° steps across a feed-through plateau alias into impossible lags (478°/494° vs true 321.4°/329.8°, carried forward) because the unwrapper corrects only steps > 180°; fixed by a −100 dB magnitude floor + a 150° resolvability guard — reference unchanged at **346.43°** with a worst in-band step of **46.94°** |
| 2026-08-11 | [irn-band-definition](journal/irn-band-definition.md) | procedural | live | S5 is **0.5–200 Hz and input-referred**: reference **50.18 µVrms**; ngspice's own integrated total covers the whole 0.1 Hz–1 kHz sweep and is not the metric (the originating campaign read 1.76 mV for 55.59 µV that way); input-referring at 1 kHz multiplies density by 264× (\|H\| = −48.43 dB), and \|H\| is already 0.925 at the 200 Hz edge |
| 2026-08-11 | [ngspice-write-protocol](journal/ngspice-write-protocol.md) | procedural | live | `write` emits only the CURRENT plot ⇒ `set appendwrite` + one `write` per analysis + `setplot noise1` to reach the spectrum (`noise` leaves the *integrated* plot current); plot numbering is only deterministic when each analysis runs once; an explicit `save` **starves** the noise analysis ("no data saved for Noise analysis") and the rawfile then holds the ac plot twice — S5 reads NaN instead of failing |
| 2026-08-11 | [nodeset-not-ic](journal/nodeset-not-ic.md) | procedural | live | dc hints are `.nodeset` (a hint the solver may leave), never `.ic` (a clamp that lands this circuit in a latched basin scoring as a valid PASS); a hint on a subckt node must be instance-qualified — `v(xdut.vout_1)`, else only "Nodeset on non-existent node" and a silent no-op |
| 2026-08-11 | [mirror-unit-must-match](journal/mirror-unit-must-match.md) | procedural | live | mirror diodes must be the design's **own** unit geometry at m = 1, or every branch is scaled by a W/L ratio: biquad A's internal node rails, its shunt-feedback device switches off, and the ac response still reads as a plausible **mis-tuned** low-pass with a full scorecard; bias current is a multiplicity, never a hand calculation |
| 2026-08-11 | [silent-zero-rawfile](journal/silent-zero-rawfile.md) | procedural | live | ngspice exits **0** after a failed operating point and leaves a zero-filled rawfile that scores as a PASS — the most expensive failure mode in this harness; `lab.ngspice` therefore scans stdout for six fatal strings (incl. `Unknown model type`, which is what a non-OSDI ngspice says about this PDK) and raises `SimError` |

---

## Entry format

**Filename**: `doc/journal/<slug>.md` — **slug only, no date prefix.** The
originating campaign date-prefixed filenames to get recency from a
reverse-lexicographic sort; here `lab/` cites entries by name from code
(`lab/metrics.py` → `phase-certificate-floor.md`, `lab/dut.py` →
`nmos-bulk-tie.md`, `lab/deck.py` → `mirror-unit-must-match.md`,
`nodeset-not-ic.md`, `lab/config.py` → `all-p-followers.md`), so a date in the
path would rot every cross-reference on the first re-dating. The date lives in
the **title line** and in the **date column** here, and retrieval orders on that.

```
# YYYY-MM-DD — <one-line title: the lesson stated as a claim>

KIND: journal entry | type: semantic | status: live
[superseded <date> — see <entry>]        <- only when retired; first 400 chars
[carried forward from the originating campaign — …]   <- when the numbers are not this repo's

<body: tables and numbers first; provenance inline; prose is interpretation only>
```

* Line 3 carries `type:` and `status:` and must stay line 3 — the lint regex
  `type: (semantic|procedural)` and the context pack's supersession filter both
  read only the **first 400 bytes**.
* **Provenance is mandatory**: ledger tags (`ref_fit`, `ref_v0`, `020A_v0`),
  deck hashes (`1ae5466ad00c`), experiment dirs, `file:line`, paper eq/fig refs.
* **Numbers that were not measured in this repo are marked carried forward**,
  every time, and are never presented as a measurement here.
* A procedural entry that proposes a `lab/` or `scripts/` change ends with:
  `Procedural write (lab/) — flagged for owner review per CLAUDE.md rule 10.`
  and gets a section in `doc/proposed-lab-fixes.md`.
* Cross-links are **relative markdown links**. No wiki-style links.
* **Hard size cap: 20 KB** per entry, and on this index.

## Supersede, don't delete

Retiring a claim is a **three-place edit** and all three are required:

1. the entry's line 3 → `… | type: <t> | status: superseded`;
2. `[superseded <date> — see <entry/section>]` as the **first body line**
   (inside the first 400 characters, where the retrieval filter looks);
3. this index's **status cell** → `**superseded**`.

**Partial supersession is expected**: retire the claim that died, name it
exactly, and re-home anything that survives (a mechanism whose verdict was
overtaken usually belongs in `doc/design-reference.md`). Supersession also runs
across surfaces — when a measurement corrects a paper's premise, strike the
`pdf/INDEX.md` row through in place and mark it `CORRECTED by <exp> (measured)`.

**If you disprove an entry, marking it is part of the fix — a stale lesson is
worse than none.**

See [`doc/memory/README.md`](memory/README.md) for the memory model this index
is one surface of, and the write-risk ordering that governs who may write what.
