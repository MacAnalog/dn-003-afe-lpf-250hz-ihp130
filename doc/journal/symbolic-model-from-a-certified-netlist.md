# 2026-08-27 — Getting an EXACT symbolic H(s), Z_T and pole/zero map out of a certified netlist: the recipe and its five traps

KIND: journal entry | type: procedural | status: live

**What this buys.** `spicexplorer_netlist2tf` turns an as-built subckt plus one
measured operating point into the MNA pencil `Y(s) = G + s·C` *exactly* — so
poles, zeros, driving-point impedances and transimpedances are eigenvalue and
linear-solve problems, not fits. On this cell it closes on the ac sweep to
**0.027 dB / 0.34°** over dc–1 kHz and on the simulator's own per-generator noise
total to **2·10⁻⁷ %**. The pack that uses it is `signoff/paper-draft/`
(`scripts/n2tf_model.py` is the one module that knows how to do the binding).

**The recipe.**

1. **Extract the operating point with the capacitance block**, not just `cgg`:
   `lab.oppoint.PARAMS` now carries `cgs, cgd, cgb, cdb, csb, cjd, cjs`. See
   [weak-inversion-model-traps](weak-inversion-model-traps.md) for why `cgg`
   alone is not enough here.
2. **Bind by role, assert the structure.** `bind_op` folds `cgb → cgs`,
   `cjd → cdb`, sets `gmb = csb = 0`, and *refuses the netlist* if any device has
   bulk ≠ source — the assumption those folds rest on.
3. **Use the DM half-circuit for symbols, the full differential system for
   numbers.** For a perfectly symmetric cell the half-circuit is exact (identical
   poles, dc gain and sim residual), and it is small enough that
   `extract_tf` returns a readable `H(s)`. Cross caps become `2·C`.
4. **Poles/zeros from the matrix pencil, not from `extract_tf`.** Berkowitz on
   the full 15×15 symbolic system does not terminate in useful time; the finite
   generalised eigenvalues of `(−G_rr, C_rr)` (and the bordered pencil for zeros)
   are the same algebra in floating point, in milliseconds.

**The five traps, each of which cost a debugging cycle.**

| trap | symptom | fix |
|---|---|---|
| `spicelib` parser | `EncodingDetectError`, then `NotImplementedError` on lower-case refs | prepend a `*` title line and upper-case the leading token — caller-side only, `_prep()` |
| PDK X-wrapped MOS | `xr1 … sg13_hv_pmos` typed `DeviceKind.SUBCKT`, so the device vanishes from the model | fixed **in the platform**: `ingest._x_wrapped_mos` types a 3/4-terminal `X` card by its model name |
| ngspice `$` sigil | `save @n.xdut.XM$1[gm]` expands to nothing, and the op probe silently returns 0 instances | rename `$`→`_` in the PEX netlist (proven inert against the certified scorecard); and lower-case **both** sides of the probe-name match, because ngspice echoes names lower-cased |
| singular pencil | poles come back in the MHz | the driven input rows are all-zero; partition the driven nodes out before the QZ |
| generator-name regex | the per-generator noise sum came out √2 too big | `sg13_\w+?` splits `nsg13_hv_pmos` into model + a phantom generator; anchor on `sg13_\w+?mos` |

**`ngspice .pz` is unusable on any cell whose input gate carries its dc bias.**
It aborts with *"the input signal is shorted on the way to the output"* — checked
on a one-transistor deck too, so it is the analysis and not the netlist. Replace
it with three legs, which together are stronger: (a) the op-bound pencil,
(b) a 4-pole rational fitted to the **measured** response only, and (c) a
point-by-point model-vs-sim overlay. Leg (b) also gives a falsification test the
`.pz` never could: refit with both Q's forced ≤ 0.5 (all-real poles) and the
residual goes 0.215 → **4.85 dB**, which proves the poles are complex from the
simulation data alone.

**Two-tone spacing must be even.** Both tones and all four third-order products
have to land on DFT bins; an odd spacing puts them on half-bins and the "IMD3"
that comes back is scalloping (measured once at −0.79 dBc, which no circuit
produces). Keep the rect-vs-Hann agreement guard on every coherent transient.

## Addendum (2026-08-28) — the pencil math is now upstream

The matrix-pencil pole/zero solve described above no longer lives in this repo. It was
contributed to the platform as `spicexplorer_netlist2tf.poles_zeros`, and
`signoff/paper-draft/scripts/pencil.py` is now a thin adapter over it. What stays local is
what the package does not provide: numeric `H(jω)` and `Z_T(jω)` sweeps.

Two things came out of that move, both worth carrying forward:

* **Reuse found a bug in the local version.** The pack bordered the *partitioned* `Y_rr`
  by hand; the package borders the *augmented* matrix, where the source constraint is
  explicit. On the capacitance-ablation diagnostic the two disagreed about a near-exact
  pole–zero pair at ~200 kHz — a classification flip either side of the 1e-4 cancellation
  threshold, three orders of magnitude outside the band, but a difference that only
  appeared because a second implementation existed to disagree.
* **Verify a root, don't trust a solver.** `σ_min(G + sC)/σ_max` is ~0 at a real root and
  sits at the noise floor at a non-root, and that test is independent of how the root was
  found. It is what settled the disagreement, and it is now a test in the platform package.
  Evaluate it at the **complex** root, not at `2πjf` of its magnitude — doing the latter
  cost an hour and produced a confident wrong conclusion.
