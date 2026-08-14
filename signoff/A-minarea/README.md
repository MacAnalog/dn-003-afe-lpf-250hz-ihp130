# `A-minarea`

**Minimum area and power. The floor of the family -- but only 0.30 uV of S5 margin, so it is a corner marker, not a shipping cell.**

Sizing from round `scale/020C-frozen_x1`. Same topology as every other candidate (branch-stacked SSF, bridge and current reuse intact) — this differs only in device sizes, flavours and capacitor values.

| | |
|---|---|
| input common mode | 0.2 V |
| output common mode | 1.1000 V |
| lv-flavour roles | none (all hv) |

## Spec

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ph_max ≥ 330° | **339.77°** | PASS |
| S1 stopband | |H|@1 kHz ≤ −48 dB | **-49.04 dB** | PASS |
| S2 cutoff | fc 245–255 Hz | **249.86 Hz** | PASS |
| S3 dc | |dc| ≤ 0.2 dB | **-0.0088 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB | **0.0545 dB** | PASS |
| S4 peaking | peak ≤ 0.2 dB | **+0.0000 dB** | PASS |
| S5 irn | IRN < 40 µVrms | **39.70 µV** | PASS |
| S6 power | P < 50 nW | **4.15 nW** | PASS |
| S7 thd | THD ≤ −40 dB | **-41.68 dB** | PASS |

`mono_db` = **0.0000 dB** — the worst *rise* of |H| below the corner; 0 means the response never climbs. Total drawn capacitance **104.4 pF** (reported, never specced).

**All nine lines: PASS.**

## Plots

### Passband — the flatness claim, by eye

![passband](A-minarea_passband.png)

### AC response — magnitude and phase

![bode](A-minarea_bode.png)

### Input-referred noise density

![noise](A-minarea_noise.png)

## Files

| file | what |
|---|---|
| `design.json` | the sizing of record |
| `asbuilt/core.sp` | certified subckt — the sizing source of truth |
| `asbuilt/core_tb_acnoise.sp` | certified op + ac + noise deck |
| `asbuilt/core_tb_thd.sp` | certified coherent-strobed THD deck |
| `lpf_core_A.sch` / `.sym` | the schematic and its symbol |
| `lpf_tb_A.sch` | testbench: op + ac + noise, `.control` on the sheet |
| `lpf_tb_A_thd.sch` | testbench: transient for S7 |
| `scorecard.json` | the measured numbers + per-line pass/fail |

## Run it

```bash
docker run --rm -it -v "$PWD/signoff/A-minarea:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_A.sch

# or re-run both gates headless
uv run python scripts/draw_xschem.py check signoff/A-minarea/asbuilt/core.sp \
    signoff/A-minarea --name lpf_core_A
uv run python scripts/draw_xschem.py sim signoff/A-minarea/asbuilt/core.sp \
    signoff/A-minarea --name lpf_core_A --design signoff/A-minarea/design.json
```

Both gates currently **PASS**: the schematic netlists to the as-built netlist, and that netlist simulates to the numbers above.

See [`../COMPARISON.md`](../COMPARISON.md) for how this cell compares.
