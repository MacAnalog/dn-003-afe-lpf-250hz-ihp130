# `D-thdjump`

**The lv-gm_f,b lever: THD jumps to -52.29 dB for 0.9 nW and 35 pF over C. First cell with double-digit THD margin.**

Sizing from round `reuse/cr_0p1_4`. Same topology as every other candidate (branch-stacked SSF, bridge and current reuse intact) — this differs only in device sizes, flavours and capacitor values.

| | |
|---|---|
| input common mode | 0.65 V |
| output common mode | 1.3273 V |
| lv-flavour roles | gmf_b, in_a |

## Spec

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ph_max ≥ 330° | **330.66°** | PASS |
| S1 stopband | |H|@1 kHz ≤ −48 dB | **-49.27 dB** | PASS |
| S2 cutoff | fc 245–255 Hz | **250.00 Hz** | PASS |
| S3 dc | |dc| ≤ 0.2 dB | **-0.0131 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB | **0.1604 dB** | PASS |
| S4 peaking | peak ≤ 0.2 dB | **+0.0000 dB** | PASS |
| S5 irn | IRN < 40 µVrms | **28.81 µV** | PASS |
| S6 power | P < 50 nW | **7.47 nW** | PASS |
| S7 thd | THD ≤ −40 dB | **-52.48 dB** | PASS |

`mono_db` = **0.0000 dB** — the worst *rise* of |H| below the corner; 0 means the response never climbs. Total drawn capacitance **187.9 pF** (reported, never specced).

**All nine lines: PASS.**

## Plots

### Passband — the flatness claim, by eye

![passband](D-thdjump_passband.png)

### AC response — magnitude and phase

![bode](D-thdjump_bode.png)

### Input-referred noise density

![noise](D-thdjump_noise.png)

<!-- robustness-dynamics:begin -->
## Robustness & dynamics

Nominal (mos_tt, 27 C, VDD 1.5 V): fc 250.00 Hz - dc -0.0131 dB - group delay tau(0) 1.623 ms, tau_max 2.372 ms (at-fc 2.267 ms)

| artifact | what |
|---|---|
| [`op_lpf_core_D.md`](op_lpf_core_D.md) | measured operating point: per-device ID, gm/ID, gm/gds, **Vds, Vdsat** and saturation margin; the same numbers are stamped on the schematic sheet |
| [`mc.md`](mc.md) | mismatch Monte-Carlo, n = 100: all-pass yield **75.0 %**, with per-line yields and sigmas for fc, dc gain and **group delay** |
| [`pvt.md`](pvt.md) | PVT screen (ss/ff/sf/fs x -40/27/125 C x 1.35/1.5/1.65 V): **1/22 corners clean** — the family's documented supply sensitivity |
| `asbuilt/core_tb_gd.sp` | runnable single-file group-delay bench (tau computed in-deck) — drawn as [`lpf_tb_D_gd.sch`](lpf_tb_D_gd.sch) |
| `asbuilt/core_tb_mc.sp` | runnable single-seed mismatch sample (edit `.option seed=`) — drawn as [`lpf_tb_D_mc.sch`](lpf_tb_D_mc.sch) |

The core schematic [`lpf_core_D.sch`](lpf_core_D.sch) carries the op
annotation on-sheet (render: `lpf_core_D.png`).
<!-- robustness-dynamics:end -->

## Files

| file | what |
|---|---|
| `design.json` | the sizing of record |
| `asbuilt/core.sp` | certified subckt — the sizing source of truth |
| `asbuilt/core_tb_acnoise.sp` | certified op + ac + noise deck |
| `asbuilt/core_tb_thd.sp` | certified coherent-strobed THD deck |
| `lpf_core_D.sch` / `.sym` | the schematic and its symbol |
| `lpf_tb_D.sch` | testbench: op + ac + noise, `.control` on the sheet |
| `lpf_tb_D_thd.sch` | testbench: transient for S7 |
| `scorecard.json` | the measured numbers + per-line pass/fail |

## Run it

```bash
docker run --rm -it -v "$PWD/signoff/D-thdjump:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_D.sch

# or re-run both gates headless
uv run python scripts/draw_xschem.py check signoff/D-thdjump/asbuilt/core.sp \
    signoff/D-thdjump --name lpf_core_D
uv run python scripts/draw_xschem.py sim signoff/D-thdjump/asbuilt/core.sp \
    signoff/D-thdjump --name lpf_core_D --design signoff/D-thdjump/design.json
```

Both gates currently **PASS**: the schematic netlists to the as-built netlist, and that netlist simulates to the numbers above.

See [`../COMPARISON.md`](../COMPARISON.md) for how this cell compares.
