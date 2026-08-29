# 2026-08-28 — `LPF_BIAS_ALPHA` is part of a temperature measurement's identity, and its default is not the delivered cell

KIND: journal entry | type: procedural | status: live

**The trap.** `lab.config.BIAS_ALPHA` defaults to **0** — a constant reference
CURRENT. The delivered cells were certified with **`LPF_BIAS_ALPHA=1.1`**, the ideal
constant-`gm` shaping (`signoff/post-pvt/README.md`: "Bias law for the temperature
rows"). At 27 °C the two are the same current, so a nominal run cannot tell them
apart and nothing warns you. At every other temperature they are different circuits.

**What it cost.** A first 29-corner analytical sweep taken with the default read
`fc` 70.3–552.0 Hz and `ph_max` down to 146.9° — an uncompensated cell reported as if
it were the delivered one. Re-run at `alpha = 1.1` the same set spans `fc`
70.1–449.4 Hz with `ph_max` no lower than 155.1° (every extreme at −40 °C, 1.35 V —
the `fc` floor at `ss`, the ceiling and the `ph_max` floor at `sf`; corners far outside
the certified window), and on the certified axes the cell holds every line.

**The rule.** Any sweep with a temperature axis must set the bias law explicitly and
RECORD it. `extract_bench.py` now writes `bias_alpha` into every bench record and tags
the filenames (`bench_pvt_<dut>_a1p1_<slug>.json`), so two sweeps at different bias
laws cannot overwrite each other or be silently compared.

**Watch for the second-order effect.** With `alpha != 0` the reference becomes a
BEHAVIOURAL source (`bref ... i = iref*pow((temper+273.15)/300.15, alpha)`) rather
than a plain dc source. At 27 °C it carries the same current but the transient solves
it slightly differently: the nominal two-tone IIP3 moves in the third decimal
(−3.248 vs −3.250 dBVp). Not an error, but it means an `alpha = 1.1` nominal row is
not bit-identical to an `alpha = 0` one.

**Provenance.** `lab/config.py:153-170`, `lab/deck.py::_bias`,
`signoff/paper-draft/scripts/extract_bench.py::alpha_tag`,
`signoff/paper-draft/validation.md` §8 and §10.2.
