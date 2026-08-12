# 2026-08-12 — Scalar peak/ripple bounds cannot see a sag-then-recover passband: score the *shape*, with `mono_db`

KIND: journal entry | type: procedural | status: live

**Symptom.** Every optimiser-fitted candidate had a visible bump in the
passband, and every one of them *passed* the flatness box. The reviewer caught
it by eye; no metric in the repo did.

**Why the box could not see it.** S3/S4 are scored by two scalars, and the
failure shape defeats both:

* `peak_db` is **one-sided** — `max(0, |H| − |H(dc)|)` — so a response that dips
  below dc and comes back reads **0.000 dB**.
* `ripple_db` is a **peak-to-peak spread** over the flat band, so a curve that
  sags 0.09 dB and lifts 0.09 dB reads **0.084 dB** against a 0.2 dB bound.

Both numbers pass, comfortably, on a response that is not maximally flat. The
fit objective (`lab.shape.cost`) scored those same two bounds, so the optimiser
had no gradient toward flatness once it was inside them — it was free to
stagger the two biquads' poles for whatever else the cost rewarded.

**Measured, before any re-fit** (dense sweep, `dec = 100`):

| cell | reference | n6-98 | gb12-175 | G-120 | G-135 | 020B |
|---|---|---|---|---|---|---|
| `mono_db` | **0.023** | 0.150 | 0.151 | 0.179 | 0.184 | 0.362 |
| `ripple_db` | 0.251 | 0.150 | 0.086 | 0.080 | 0.084 | **1.463** |
| `peak_db` | 0.023 | 0.150 | 0.066 | 0.101 | 0.102 | **0.000** |

020B is the clearest case: `peak_db` of exactly 0.000 dB alongside 1.46 dB of
passband droop.

**Fix, in two parts.**

1.  `lab.raw.monotone_db` — the worst *rise* of |H| with frequency below the
    corner; zero iff the response never climbs. Reported on every scorecard as
    the soft column `mono_db` and included in `lab.metrics.COLS`, so it appears
    in every table without anyone having to ask for it.
2.  `lab.shape.fit_butter` — fits against the 4-pole Butterworth **template**
    (rms + worst deviation over the passband and corner) instead of against
    scalar bounds. A maximally-flat response is monotone by construction, so
    "no bump" stops being a side condition and becomes the objective.

Scored over the passband **and corner only** (`fmax = 1.25·fc`): past the corner
a real cell rolls off *faster* than the template, and scoring that surplus as
"deviation" would push the fit to make the skirt worse. The stopband stays a
separate one-sided constraint (`a1000_db ≤ −48`).

**Result of the re-fit** (devices held fixed, only the four capacitors move, so
this is its own re-allocation control):

| cell | `mono_db` before → after | template rms after | THD before → after |
|---|---|---|---|
| gb12-175 | 0.151 → **0.0005** | 0.0032 dB | −35.71 → −35.76 dB |
| n6-98 | 0.150 → **0.0000** | 0.0032 dB | −28.88 → −28.61 dB |
| G-135 | 0.186 → 0.0718 | 0.0343 dB | −41.57 → **−35.74 dB** |

**The lesson that cost the most.** Flatness is not free: G-135 lost **5.8 dB of
THD** to it, and the loss was confirmed by re-measuring the pre-fit sizing
(−41.57 dB, reproducing its recorded −41.56). Distortion in this family tracks
where the high-Q pole pair sits, because a high-Q stage lets its internal node
swing further relative to its output and that excursion *is* the follower's Vgs
modulation. Cells with THD margin survive being flattened; cells without it do
not. Pick the starting point accordingly.

**Do not** re-tighten `ripple_db` instead. The defect sits *inside* every
numeric bound; a tighter bound on the wrong statistic just moves the artefact,
it does not remove it.
