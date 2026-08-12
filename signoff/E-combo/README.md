# `E-combo`

**BEST on the stated priorities. Combines both levers: gm_f,a shortened to recover the phase the low-power sizing lost, and gm_f,b moved to lv to recover the THD that shortening cost. 27.27 uV / 8.88 nW / 220.0 pF / -54.88 dB -- strictly better than E1-prev on ALL FOUR axes at once.**

Sizing from round `combo/cb_0p3_0p16_4`. Same topology as every other candidate (branch-stacked SSF, bridge and current reuse intact) — this differs only in device sizes, flavours and capacitor values.

| | |
|---|---|
| input common mode | 0.32 V |
| output common mode | 1.3421 V |
| lv-flavour roles | gmf_b |

## Spec

| line | requirement | measured | |
|---|---|---|---|
| S1 phase | ph_max ≥ 330° | **334.63°** | PASS |
| S1 stopband | |H|@1 kHz ≤ −48 dB | **-48.92 dB** | PASS |
| S2 cutoff | fc 245–255 Hz | **249.87 Hz** | PASS |
| S3 dc | |dc| ≤ 0.2 dB | **-0.0207 dB** | PASS |
| S3 flatness | ripple ≤ 0.2 dB | **0.0544 dB** | PASS |
| S4 peaking | peak ≤ 0.2 dB | **+0.0016 dB** | PASS |
| S5 irn | IRN < 40 µVrms | **27.27 µV** | PASS |
| S6 power | P < 50 nW | **8.88 nW** | PASS |
| S7 thd | THD ≤ −40 dB | **-54.88 dB** | PASS |

`mono_db` = **0.0016 dB** — the worst *rise* of |H| below the corner; 0 means the response never climbs. Total drawn capacitance **220.0 pF** (reported, never specced).

**All nine lines: PASS.**

## Plots

### Passband — the flatness claim, by eye

![passband](E-combo_passband.png)

### AC response — magnitude and phase

![bode](E-combo_bode.png)

### Input-referred noise density

![noise](E-combo_noise.png)

## Files

| file | what |
|---|---|
| `design.json` | the sizing of record |
| `asbuilt/core.sp` | certified subckt — the sizing source of truth |
| `asbuilt/core_tb_acnoise.sp` | certified op + ac + noise deck |
| `asbuilt/core_tb_thd.sp` | certified coherent-strobed THD deck |
| `lpf_core_E.sch` / `.sym` | the schematic and its symbol |
| `lpf_tb_E.sch` | testbench: op + ac + noise, `.control` on the sheet |
| `lpf_tb_E_thd.sch` | testbench: transient for S7 |
| `scorecard.json` | the measured numbers + per-line pass/fail |

## Run it

```bash
docker run --rm -it -v "$PWD/signoff/E-combo:/sch" -w /sch \
    spicexplorer-spice-base:local xschem --rcfile /sch/xschemrc lpf_tb_E.sch

# or re-run both gates headless
uv run python scripts/draw_xschem.py check signoff/E-combo/asbuilt/core.sp \
    signoff/E-combo --name lpf_core_E
uv run python scripts/draw_xschem.py sim signoff/E-combo/asbuilt/core.sp \
    signoff/E-combo --name lpf_core_E --design signoff/E-combo/design.json
```

Both gates currently **PASS**: the schematic netlists to the as-built netlist, and that netlist simulates to the numbers above.

See [`../COMPARISON.md`](../COMPARISON.md) for how this cell compares.
