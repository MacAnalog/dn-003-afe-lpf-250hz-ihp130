# 2026-08-14 — a cairo-less xschem "exports" png/svg without error and without output: check the binary before trusting any render, and treat the .sch + gates as the only binding evidence

KIND: journal entry | type: procedural | status: live

**Symptom.** On the EDA server (native lane), `xschem -q --plotfile f.png
--png f.sch` exits 0, prints nothing, and writes nothing. `--svg` "succeeds"
but emits a `width="1" height="1"` file with no geometry (rasterizing it gives
solid color blobs). Every flag combination, `--command`-driven print, and
xvfb-run variant behaves the same.

**Mechanism.** The conda-forge xschem 3.4.5 in `ai_env` is built **without
cairo** (`ldd | grep cairo` → nothing): the png/svg export paths are compiled
out and fail silently rather than erroring. The one cairo-enabled xschem on the
host (`~/local/tools/tools/xschem`) needs glibc ≥ 2.34 against the EL8 host's
2.28, and there is no container runtime, so no native render lane exists today.

**Rule.**

1. Before relying on xschem image export, check `ldd $(which xschem) | grep
   cairo`. No cairo → no renders; do not burn time on flags.
2. **Netlisting is unaffected** — `xschem -n -s -q --no_x` works headless on
   the cairo-less build, which is what the identity gates need (`lab/xsch.py`,
   `LPF_XSCHEM` mirror of the `LPF_NGSPICE` lane switch). The `.sch` sources
   plus Gate 1/Gate 2 are the binding evidence; the pngs are a convenience.
3. Regenerate renders only in a lane whose xschem links cairo (the docker
   image), and never leave a stale render beside a re-sized schematic — a
   wrong-numbers picture is worse than none. The signoff renders were removed
   on feat/signoff-grid-legal for exactly this reason.

**Provenance.** `signoff/schematic/README.md` (render row),
`lab/xsch.py`; session experiments on Xvfb :77–:79, 2026-08-14.
