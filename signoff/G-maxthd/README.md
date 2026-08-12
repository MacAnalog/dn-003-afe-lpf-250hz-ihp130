# `G-maxthd`

**Maximum linearity: -70.99 dB THD at 26.81 uV, 14.32 nW, 348.2 pF. 31 dB of S7 margin.**

Sizing from round `combo/cb_0p1_0p16_2p5`. Same topology as every other candidate (branch-stacked SSF, bridge and current reuse intact) — this differs only in device sizes, flavours and capacitor values.

| | |
|---|---|
| input common mode | 0.32 V |
| output common mode | 1.3617 V |
| lv-flavour roles | gmf_b |

## Spec

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ph_max ≥ 330° | **343.53°** | PASS |
| S1 stopband | |H|@1 kHz ≤ −48 dB | **-48.69 dB** | PASS |
| S2 cutoff | fc 245–255 Hz | **249.88 Hz** | PASS |
| S3 dc | |dc| ≤ 0.2 dB | **-0.0417 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB | **0.0541 dB** | PASS |
| S4 peaking | peak ≤ 0.2 dB | **+0.0029 dB** | PASS |
| S5 irn | IRN < 40 µVrms | **26.81 µV** | PASS |
| S6 power | P < 50 nW | **14.32 nW** | PASS |
| S7 thd | THD ≤ −40 dB | **-70.98 dB** | PASS |

`mono_db` = **0.0029 dB** — the worst *rise* of |H| below the corner; 0 means the response never climbs. Total drawn capacitance **348.2 pF** (reported, never specced).

**All nine lines: PASS.**

## Plots

### Passband — the flatness claim, by eye

![passband](G-maxthd_passband.png)

### AC response — magnitude and phase

![bode](G-maxthd_bode.png)

### Input-referred noise density

![noise](G-maxthd_noise.png)

## Files

| file | what |
|---|---|
| `design.json` | the sizing of record |
| `asbuilt/core.sp` | certified subckt — the sizing source of truth |
| `asbuilt/core_tb_acnoise.sp` | certified op + ac + noise deck |
| `asbuilt/core_tb_thd.sp` | certified coherent-strobed THD deck |
| `lpf_core_G.sch` / `.sym` | the schematic and its symbol |
| `lpf_tb_G.sch` | testbench: op + ac + noise, `.control` on the sheet |
| `lpf_tb_G_thd.sch` | testbench: transient for S7 |
| `scorecard.json` | the measured numbers + per-line pass/fail |

## Run it

```bash
docker run --rm -it -v "$PWD/signoff/G-maxthd:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_G.sch

# or re-run both gates headless
uv run python scripts/draw_xschem.py check signoff/G-maxthd/asbuilt/core.sp \
    signoff/G-maxthd --name lpf_core_G
uv run python scripts/draw_xschem.py sim signoff/G-maxthd/asbuilt/core.sp \
    signoff/G-maxthd --name lpf_core_G --design signoff/G-maxthd/design.json
```

Both gates currently **PASS**: the schematic netlists to the as-built netlist, and that netlist simulates to the numbers above.

See [`../COMPARISON.md`](../COMPARISON.md) for how this cell compares.
