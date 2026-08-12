# `C-lownoise`

**Same power class, better noise (28.54 uV) for 11 pF more.**

Sizing from round `lv065_bias/sb3`. Same topology as every other candidate (branch-stacked SSF, bridge and current reuse intact) — this differs only in device sizes, flavours and capacitor values.

| | |
|---|---|
| input common mode | 0.65 V |
| output common mode | 1.3224 V |
| lv-flavour roles | in_a |

## Spec

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ph_max ≥ 330° | **332.83°** | PASS |
| S1 stopband | |H|@1 kHz ≤ −48 dB | **-49.78 dB** | PASS |
| S2 cutoff | fc 245–255 Hz | **249.85 Hz** | PASS |
| S3 dc | |dc| ≤ 0.2 dB | **-0.0133 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB | **0.0538 dB** | PASS |
| S4 peaking | peak ≤ 0.2 dB | **+0.0000 dB** | PASS |
| S5 irn | IRN < 40 µVrms | **28.54 µV** | PASS |
| S6 power | P < 50 nW | **6.46 nW** | PASS |
| S7 thd | THD ≤ −40 dB | **-42.39 dB** | PASS |

`mono_db` = **0.0000 dB** — the worst *rise* of |H| below the corner; 0 means the response never climbs. Total drawn capacitance **164.0 pF** (reported, never specced).

**All nine lines: PASS.**

## Plots

### Passband — the flatness claim, by eye

![passband](C-lownoise_passband.png)

### AC response — magnitude and phase

![bode](C-lownoise_bode.png)

### Input-referred noise density

![noise](C-lownoise_noise.png)

## Files

| file | what |
|---|---|
| `design.json` | the sizing of record |
| `asbuilt/core.sp` | certified subckt — the sizing source of truth |
| `asbuilt/core_tb_acnoise.sp` | certified op + ac + noise deck |
| `asbuilt/core_tb_thd.sp` | certified coherent-strobed THD deck |
| `lpf_core_C.sch` / `.sym` | the schematic and its symbol |
| `lpf_tb_C.sch` | testbench: op + ac + noise, `.control` on the sheet |
| `lpf_tb_C_thd.sch` | testbench: transient for S7 |
| `scorecard.json` | the measured numbers + per-line pass/fail |

## Run it

```bash
docker run --rm -it -v "$PWD/signoff/C-lownoise:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_C.sch

# or re-run both gates headless
uv run python scripts/draw_xschem.py check signoff/C-lownoise/asbuilt/core.sp \
    signoff/C-lownoise --name lpf_core_C
uv run python scripts/draw_xschem.py sim signoff/C-lownoise/asbuilt/core.sp \
    signoff/C-lownoise --name lpf_core_C --design signoff/C-lownoise/design.json
```

Both gates currently **PASS**: the schematic netlists to the as-built netlist, and that netlist simulates to the numbers above.

See [`../COMPARISON.md`](../COMPARISON.md) for how this cell compares.
