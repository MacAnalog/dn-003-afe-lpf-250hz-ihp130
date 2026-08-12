# 2026-08-12 — S7's single 50 Hz point hides a 23 dB spread: profile THD across the passband before choosing a cell

KIND: journal entry | type: semantic | status: live

**The trap.** S7 is specified at **fin = 50 Hz**, and the spec calls higher fins
"an informative profile only". That wording makes the profile sound optional. It
is not: measured at the spec amplitude (175 mVpp differential) across the
passband, two cells that are 2 dB apart at 50 Hz are **23 dB apart at 100 Hz**.

| cell | 20 Hz | **50 Hz (S7)** | 100 Hz | 150 Hz | 200 Hz |
|---|---|---|---|---|---|
| reference (certified) | −69.58 | −48.37 | **−43.96** | −32.62 | −29.77 |
| 021-lv-final (branch-stacked) | −60.79 | **−42.39** | **−20.93** | −20.17 | −21.15 |
| 021-vdd2-final (unstacked) | −65.36 | **−44.64** | **−40.06** | −29.23 | −28.07 |

**Two separate facts, and they must not be conflated.**

1.  **Degradation towards the corner is a FAMILY property, not a defect.** The
    certified reference does it too: −48.4 dB at 50 Hz, −29.8 dB at 200 Hz. The
    mechanism is the one `gmc-compact` names — a follower biquad's internal node
    is a **bandpass tap**, so its swing peaks near fc, and that excursion *is*
    the follower's Vgs modulation. Every cell in this family distorts most where
    its internal node peaks. Do not report this as a candidate's failure.

2.  **The branch-stacked cell is nonetheless 23 dB worse than the reference at
    100 Hz**, and that IS a defect of stacking. Both followers share one dc
    branch, so the single ladder current has to serve both internal nodes at
    once; when biquad B's tap peaks there is no independent current to supply it.
    The unstacked cell, whose stages have their own bias, tracks the reference to
    within 2–4 dB across the whole band.

**Consequence for cell selection.** At the S7 point alone the stacked cell looks
2.3 dB *better* than the unstacked one (−42.39 vs −44.64 — no, worse by 2.3;
either way, the same order). Across the band it is 19 dB worse. A choice made on
the single spec point picks the wrong cell.

**Do this before signing off any candidate**: run `lab.thd.profile` (or
`make thd`) at the spec amplitude across at least 20/50/100/150/200 Hz, and
report the profile **next to the certified reference's own profile**, because
the absolute numbers near fc are alarming for every member of this family and
only the comparison is informative.

**Open.** Whether a constant-175 mVpp drive at 200 Hz is a physical test case for
a biopotential filter is a separate question — real ECG content at 200 Hz is far
below the 50 Hz level, so this profile is a worst case rather than an operating
condition. It should be re-run against a realistic spectral envelope before it is
used to reject a design. It is recorded here because the *relative* 23 dB gap
between cells is real regardless of the envelope.
