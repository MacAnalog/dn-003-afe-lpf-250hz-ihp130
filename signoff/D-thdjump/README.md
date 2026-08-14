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
