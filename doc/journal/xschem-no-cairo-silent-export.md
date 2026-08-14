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
3. Never leave a stale render beside a re-sized schematic — a wrong-numbers
   picture is worse than none. The signoff renders were briefly removed on
   feat/signoff-grid-legal for exactly this reason.
4. **The render lane exists after all** (found later the same day): the SVG
   export writes COMPLETE geometry — every path, every text — but with a
   broken document header (`width="1" height="1"`, no viewBox: the coordinates
   are scaled into the 1×1 Tk window that never maps under Xvfb) and the CSS
   stroke-width left in screen pixels (rasterize that and you get the
   solid-colour blobs). Both are repairable after the fact:
   `scripts/render_sch.py` recomputes the bounding box from the path data,
   rewrites the header, rescales the strokes, and rasterizes with **cairosvg**
   (`rsvg-convert` silently drops the text elements at these font sizes).
   All signoff renders are produced this way on the EDA server.

**Provenance.** `scripts/render_sch.py`, `signoff/schematic/README.md`
(render row), `lab/xsch.py`; session experiments on Xvfb :77–:79 and the
E-combo render inspection, 2026-08-14.
