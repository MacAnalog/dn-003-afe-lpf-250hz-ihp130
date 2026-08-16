# 2026-08-16 — Extraction blind spots and tool traps in the open layout lane: kpex 2.5D cannot extract the PDK MIM (strip it, re-add the cards), n-well junction C is in no model, kpex RC meshes are run-to-run different, and > 2 concurrent KLayout jobs produce spurious DRC/LVS failures with empty violation lists

KIND: journal entry | type: procedural | status: live

1. **kpex 2.5D + `cap_cmim`.** klayout-pex 0.3.12's IHP tech names the MIM top
   layer `"<TODO>"` and has no MIM rows in its cap tables → `KeyError` on any
   GDS with MIM. Workaround in `spicexplorer_signoff.pex.strip_mim_for_pex`:
   remove MIM(36/0), Vmim(129/0) and TopMetal1∩MIM, extract, then re-insert the
   schematic `xc*` cards verbatim (`postlayout.prep_pex_subckt` recipe). Cost:
   the MIM top-plate environment is *not* extracted — bounded at ≤ 15 fF on
   net2/net3 (REPORT §4/§9), an over-count.
2. **n-well ↔ substrate junction C** is in neither the kpex tech (NWell only as
   an overlap bottom layer) nor the PSP cards (AS/AD/PS/PD only). Seven signal
   wells ⇒ 16–39 fF/half unbudgeted on net4/net1; what-if −0.11 … −0.26° of
   phase (REVIEW round 3 F3). Add a `Cj(area, perimeter, V)` term to the splice
   before claiming a post-layout corner to better than 0.3°.
3. **kpex RC is not deterministic**: same GDS, same C/R element counts,
   different `net.$n.m` sub-node names and mesh; one mesh drove ngspice to a
   shorted DC state (fc 0.11 Hz) — re-extract. Three RC meshes spread fc by
   0.047 Hz, larger than the 0.041 Hz CC↔RC delta. Use CC in any loop; RC once,
   as a cross-check.
4. **HD2 below ≈ −97 dB is bench floor**: reordering identical C cards moves it
   5 dB; THD/HD3 hold to 0.002 dB.
5. **Concurrent KLayout**: 8 parallel `run_drc.py`/`run_lvs.py` jobs on one host
   produced 7 spurious DRC "failures" and 7 spurious LVS "mismatches" with
   *empty* violation lists; at 2 workers all passed and only the two real
   mismatches reproduced. Cap DRC/LVS concurrency at 2 per host, or re-run
   any failure that carries no locations before believing it.

Provenance: `layout/H12-pdk-cap/REPORT.md` §4/§9, `REVIEW.md` (rounds 1–3), it14 designer log (`scorecard_post.json` endpoint results); platform `spicexplorer-signoff` README.
