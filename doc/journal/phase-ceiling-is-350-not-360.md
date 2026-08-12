# 2026-08-12 — "4 poles ⇒ 360°" is true of the transfer function and false of the certificate: the ceiling is 350.5°

KIND: journal entry | type: semantic | status: live

**The trap.** S1 certifies "two true biquads" as ≥ 330° of unwrapped phase lag,
and it is natural to read the ideal as 360° and treat a cell at 340° as 20°
short of perfect. That reading is wrong, and acting on it pushes the design the
wrong way.

`lab.raw.ph_max_deg` scores phase **only where |H| ≥ −100 dB relative to dc**
(see [phase-certificate-floor](phase-certificate-floor.md) — below the floor the
response is a parasitic feed-through plateau where sampled phase aliases and
manufactures lags a 4-pole cannot produce). A 4-pole rolls off at 80 dB/decade,
so it falls through that floor at **15.9 × fc** — while its phase is still ~9°
short of its asymptote.

**Measured** by pushing a *mathematically ideal* 4-pole Butterworth
(Q = 0.541196, 1.306563, both at ω₀ = ω_c) through the repo's own scoring grid
and the repo's own function:

| quantity | ideal 4-pole Butterworth | this repo's reference |
|---|---|---|
| `ph_max_deg`, −100 dB floor | **350.53°** | **346.43°** |
| `ph_max_deg`, no floor | 359.57° | — |
| |H| reaches −100 dB at | 3981 Hz = 15.9 × fc | 3162 Hz |
| worst unwrap-corrected step | 45.6° | 46.94° |
| `a1000_db` | −48.16 | −48.43 |

**Three consequences.**

1.  **~350°, not 360°, is the ceiling.** The reference sits 4° under the ideal;
    it *is* a true 4-pole, and there is no 14° of missing order to go and find.
2.  **A score materially above ~351° is a warning, not a win.** It means the
    cell carries lag the 4-pole model does not contain — a parasitic pole, or a
    response falling through the floor later than an all-pole cell should. One
    candidate (G-120) read 360.0°; that is 9.5° above what a perfect 4-pole can
    score, and it should be investigated rather than celebrated.
3.  **Quote both numbers.** The floored value is the certificate; the unfloored
    value is what "does it drop 360°?" actually asks. Reporting only one invites
    exactly the misreading above.

**Provenance.** Computed directly against `lab.raw.ph_max_deg` and
`lab.raw.max_phase_step_deg` on the scoring grid (`dec = 10`, 0.1 Hz–100 kHz);
reference values from ledger `cert_reference`. No simulation is involved in the
ideal column — it is the closed-form Butterworth evaluated on the same grid,
which is the point: the ceiling is a property of the *measurement definition*,
not of any silicon.
