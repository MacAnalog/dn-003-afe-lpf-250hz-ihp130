# 2026-08-15 — The merged ladder's three top devices share two |V_SG|'s: the supply/temperature window is min(|V_SG|(gmf_b), |V_SG|(in_b)) − 2·Vds_min, and it drifts 3δ with temperature

KIND: journal entry | type: semantic | status: live

**Symptom.** With the ladder current mirror-referenced (the replica of
`replica-bias-mirror-references-the-ladder`), the sign-off cells still failed
dc gain / ripple at `ss`, at the low rail and at both temperature extremes —
`E-rep`: gmf_b |Vds| 35 mV at nominal, 0.064 V at `ss`, ~0 at 1.35 V;
`B-rep`: 78 mV nominal. Op probes at every failing corner
(experiments/023-replica-bias/screen_headroom*.py, ~1000 sims) show it is one
device or another leaving saturation, never the bias.

**The identity.** In `build_b`/`build_d` three node voltages are pinned by three
gate–source drops: `vout_1 = vicm + |V_SG|(in_a)`, `voutp = vout_1 + |V_SG|(in_b)`,
`net4 = VDD − |V_SG|(gmf_b)` (the merge puts gmf_b's gate on net4). Write
X = VDD − vicm − |V_SG|(in_a) for the voltage available above biquad A's output.
Then the three devices between vout_1 and VDD get

    |V_SD|(bridge) = X − |V_SG|(gmf_b)
    |V_SD|(gmf_b)  = X − |V_SG|(in_b)
    |V_SD|(in_b)   = |V_SG|(gmf_b) + |V_SG|(in_b) − X

so all three saturate only for X in
`[max(V_SG(gmf_b), V_SG(in_b)) + m, V_SG(gmf_b) + V_SG(in_b) − m]` — a window of
width **min(V_SG(gmf_b), V_SG(in_b)) − 2m** (m ≈ 4 kT/q). Adding the bottom
constraint `vicm + |V_SG|(in_a) ≥ V_GS(gmf_a) + m` gives the whole-supply budget
**VDD ≥ V_GS(gmf_a) + max(V_SG(gmf_b), V_SG(in_b)) + 2m**, independent of the
followers' flavour (in_a's flavour only moves where vicm has to sit).

**Consequences, each confirmed by the screens (`headroom*_*.json`):**

* **gmf_b must be hv.** The E/F/G cells' lv gmf_b (|V_SG| ≈ 0.38 V) gives a
  0.14 V window — narrower than the ±0.15 V supply box; no vicm helps
  (`screen_headroom.py`, all `lvB`/`lvIN+B` arms negative). A moderate-inversion
  lv gmf_b (D-thdjump's 0.81/62.4) is still too small (`screen_headroom5.py`).
* **in_b and gmf_b narrow/long, both |V_SG| ≈ 0.55–0.6 V** (2/30 and 2/31.2 µm
  hv): window ≈ 0.35 V. Wider gmf_b (8/15.6) hands the window to `in_b`'s
  side; narrower `in_b` alone hands it to `bridge` — the pair must move together.
* **in_a lv, vicm ≈ 0.40 V** centres X at 27 °C (`B1`: margins in_a 87 /
  bridge 194 / in_b 226 / gmf_b 192 mV; every process corner and both rails pass
  every spec line).
* **Temperature drifts the window 3δ.** Each |V_SG| moves ≈ −1.5 mV/K in weak
  inversion while X moves the other way, so over −40…125 °C (δ ≈ 0.15 V) the
  constraint drifts ~0.45 V against a 0.35 V window. **A merged ladder cannot
  hold the industrial range at 1.5 V in weak inversion.** Measured on `B1`:
  0…70 °C positive margins, −40 °C fails only fc (1/T at constant current;
  passes with a PTAT reference), +125 °C is a headroom failure (in_b −161 mV).
* **THD pulls the other way** (`thd-follows-inversion-level`): a moderate-
  inversion gmf_a raises V_GS(gmf_a) by ~70 mV and eats it straight out of the
  supply budget (`B4`: 1.35 V fails again). The reconciliation is a slightly
  wider gmf_b (|V_SG| −50 mV) — see the 023 README for the cell that lands it.

**How to apply.** Before sizing a merged cell, write X and the three lines
above; put the two |V_SG|'s ≥ 0.55 V, then pick vicm to centre X. Check the
op-only `headroom()` instrument (experiments/023-replica-bias/common.py) at
`lab.corners.AXES` before any cap fit — it is ~10 sims per arm and finds every
failure a 22-point PVT would attribute to "supply".
