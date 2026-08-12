"""ngspice rawfile reader + the frequency-domain metric primitives.

This is the module the rest of `lab` measures through.  A rawfile written by
ngspice's `write <file>` holds one *plot* per analysis, concatenated:

    Title: ...
    Date: ...
    Plotname: AC Analysis
    Flags: complex
    No. Variables: 7
    No. Points: 61
    Variables:
            0       frequency       frequency       grid=3
            1       v(voutp)        voltage
            ...
    Binary:
    <No. Points * No. Variables * (8 or 16) bytes>

Everything here is stdlib + numpy so the harness runs anywhere the simulator
does.

Naming note: the fast-iteration metrics live here; the *certifying* numbers are
produced by `lab.verify` on the reference bench (see doc/benches.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Vector names ngspice may use for the same physical quantity.  ngspice
# lower-cases everything and spells node voltages `v(name)`.
_ALIASES = {
    "frequency": ("frequency", "freq"),
    "time": ("time",),
}


@dataclass
class Plot:
    """One analysis' worth of vectors."""

    name: str            # e.g. "AC Analysis"
    flags: str           # "real" or "complex"
    vectors: dict        # name -> np.ndarray
    scale: str           # name of the sweep variable ("frequency"/"time"/...)

    def __getitem__(self, key: str) -> np.ndarray:
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        return self._resolve(key) is not None

    def _resolve(self, key: str):
        k = key.lower().strip()
        if k in self.vectors:
            return k
        for canon, alts in _ALIASES.items():
            if k in alts or k == canon:
                for a in (canon,) + alts:
                    if a in self.vectors:
                        return a
        # v(x) <-> x
        m = re.fullmatch(r"v\((.+)\)", k)
        bare = m.group(1) if m else k
        for cand in (f"v({bare})", bare):
            if cand in self.vectors:
                return cand
        return None

    def get(self, key: str) -> np.ndarray:
        r = self._resolve(key)
        if r is None:
            raise KeyError(
                f"{key!r} not in plot {self.name!r}; have: "
                f"{sorted(self.vectors)[:24]}{' ...' if len(self.vectors) > 24 else ''}"
            )
        return self.vectors[r]

    @property
    def x(self) -> np.ndarray:
        return self.vectors[self.scale]


def read_raw(path) -> list[Plot]:
    """Parse an ngspice rawfile (binary or ascii) into a list of Plots."""
    data = Path(path).read_bytes()
    plots: list[Plot] = []
    pos = 0
    while True:
        head_end = _find_payload(data, pos)
        if head_end is None:
            break
        kind, hdr_start, body_start = head_end
        header = data[hdr_start:body_start].decode("latin-1", "replace")
        meta, names = _parse_header(header)
        npts = meta["points"]
        nvar = meta["variables"]
        if kind == "binary":
            width = 16 if meta["complex"] else 8
            nbytes = npts * nvar * width
            body = data[body_start:body_start + nbytes]
            dt = np.dtype("<c16") if meta["complex"] else np.dtype("<f8")
            arr = np.frombuffer(body, dtype=dt, count=npts * nvar)
            arr = arr.reshape(npts, nvar)
            pos = body_start + nbytes
        else:  # ascii "Values:"
            arr, pos = _parse_ascii(data, body_start, npts, nvar, meta["complex"])
        vectors = {names[i]: np.ascontiguousarray(arr[:, i]) for i in range(nvar)}
        # ngspice writes the sweep variable first
        plots.append(Plot(meta["plotname"], "complex" if meta["complex"] else "real",
                          vectors, names[0]))
    if not plots:
        raise ValueError(f"no plots found in {path}")
    return plots


def _find_payload(data: bytes, pos: int):
    ib = data.find(b"Binary:\n", pos)
    ia = data.find(b"Values:\n", pos)
    cands = [(i, k) for i, k in ((ib, "binary"), (ia, "ascii")) if i != -1]
    if not cands:
        return None
    idx, kind = min(cands)
    # header starts at the previous "Title:"/"Plotname:" boundary -- simply take
    # everything since `pos`, which is exactly one plot's header.
    return kind, pos, idx + len(b"Binary:\n")


def _parse_header(header: str):
    meta = {"plotname": "", "complex": False, "points": 0, "variables": 0}
    names: list[str] = []
    in_vars = False
    for line in header.splitlines():
        if in_vars:
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                names.append(parts[1].lower())
                continue
            in_vars = False
        low = line.lower()
        if low.startswith("plotname:"):
            meta["plotname"] = line.split(":", 1)[1].strip()
        elif low.startswith("flags:"):
            meta["complex"] = "complex" in low
        elif low.startswith("no. points:"):
            meta["points"] = int(line.split(":", 1)[1])
        elif low.startswith("no. variables:"):
            meta["variables"] = int(line.split(":", 1)[1])
        elif low.startswith("variables:"):
            in_vars = True
    if not meta["points"] or not meta["variables"]:
        raise ValueError("malformed rawfile header")
    return meta, names


def _parse_ascii(data: bytes, start: int, npts: int, nvar: int, cplx: bool):
    text = data[start:].decode("latin-1", "replace")
    vals = []
    consumed = 0
    for line in text.splitlines(keepends=True):
        consumed += len(line)
        toks = line.split()
        if not toks:
            continue
        if toks[0].isdigit() and len(toks) > 1:
            toks = toks[1:]
        for t in toks:
            if cplx:
                re_, _, im_ = t.partition(",")
                try:
                    vals.append(complex(float(re_), float(im_)))
                except ValueError:
                    pass
            else:
                try:
                    vals.append(float(t))
                except ValueError:
                    pass
        if len(vals) >= npts * nvar:
            break
    arr = np.array(vals[: npts * nvar]).reshape(npts, nvar)
    return arr, start + consumed


# ------------------------------------------------------------------ metrics --

def diff_tf(plot: Plot, outp: str, outn: str) -> tuple[np.ndarray, np.ndarray]:
    """(f, H) for the differential output of an AC plot, referred to its own DC."""
    f = np.real(plot.x).astype(float)
    h = plot.get(outp) - plot.get(outn)
    return f, h


def db(h: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.maximum(np.abs(h), 1e-300))


def db_rel_dc(h: np.ndarray) -> np.ndarray:
    return db(h) - db(h[:1])


def value_at(f: np.ndarray, y: np.ndarray, f0: float) -> float:
    """Log-frequency linear interpolation -- the bench's `value(...)`."""
    return float(np.interp(np.log10(f0), np.log10(f), y))


def f3db(f: np.ndarray, h: np.ndarray) -> float:
    """-3 dB frequency relative to the DC value, by log-log interpolation."""
    y = db_rel_dc(h)
    below = np.where(y <= -3.0)[0]
    if len(below) == 0:
        return float("nan")
    i = below[0]
    if i == 0:
        return float(f[0])
    x0, x1 = np.log10(f[i - 1]), np.log10(f[i])
    y0, y1 = y[i - 1], y[i]
    return float(10 ** (x0 + (-3.0 - y0) * (x1 - x0) / (y1 - y0)))


def peaking_db(f: np.ndarray, h: np.ndarray, fmax: float = 1e3) -> float:
    """Max in-band gain above the DC value (0 if monotone)."""
    y = db_rel_dc(h)
    m = f <= fmax
    return float(max(0.0, np.max(y[m])))


def ripple_db(f: np.ndarray, h: np.ndarray, fmax: float = 150.0) -> float:
    """S3's flatness clause: worst |H(f) - H(dc)| over the flat band, EITHER sign.

    This exists because `peaking_db` only looks for gain ABOVE dc, and the
    failure mode this topology actually has is a passband DIP: the two biquads'
    poles stagger, the magnitude sags mid-band and recovers before the corner.
    A one-sided peaking check reads 0.000 dB straight through it.

    Resolution matters as much as sign.  At 10 points/decade the samples near
    the corner sit ~26 % apart, which is coarse enough to step over a dip
    entirely -- a 1.46 dB sag measured at 200 pts/decade was invisible on the
    sparse grid.  Score this on a dense sweep (see `lab.metrics.AC_DEC`).
    """
    y = db_rel_dc(h)
    m = f <= fmax
    if not np.any(m):
        return float("nan")
    return float(np.max(np.abs(y[m])))


def monotone_db(f: np.ndarray, h: np.ndarray, fmax: float) -> float:
    """Worst RISE of |H| with frequency below `fmax`, in dB.  0 => monotone.

    The third flatness number, and the one the other two cannot see.  `peaking_db`
    is one sided (gain above dc) and `ripple_db` is a peak-to-peak spread, so a
    response that sags 0.09 dB at 80 Hz and climbs 0.09 dB back at 130 Hz scores
    0.000 on the first and a comfortably-passing 0.084 on the second -- while
    visibly not being a maximally-flat low-pass.  A true 4-pole Butterworth is
    monotone by construction, so any non-zero value here is shape error, however
    well it hides inside the S3 and S4 bounds.

    Reference points measured in this repo: the frozen reference scores 0.023 dB;
    optimiser-fitted cells scored 0.15-0.36 dB before they were re-fitted against
    the template, and 0.000-0.001 dB after.
    """
    y = db_rel_dc(h)
    f = np.asarray(np.real(f), float)
    m = f <= fmax
    if np.count_nonzero(m) < 2:
        return float("nan")
    yy = y[m]
    # how far the trace ever climbs back above its own running minimum
    return float(max(0.0, np.max(yy - np.minimum.accumulate(yy))))


def ph_max_deg(f: np.ndarray, h: np.ndarray, floor_db: float = -100.0) -> float:
    """The biquad-order certificate: max unwrapped phase LAG, in degrees.

    Scored only where |H| >= `floor_db` relative to DC.  Above that the response
    collapses into a parasitic feed-through floor where the sampled phase steps
    by ~180 deg between points and ALIASES -- an unwrapper cannot tell a real
    -179 deg step from a +181 deg one, which manufactures fake lags far beyond
    360 deg on a 4-pole response.  Only steps whose magnitude is BELOW 180 deg
    alias; larger steps get a full-turn correction and are safe.

    See doc/journal/phase-certificate-floor.md.
    """
    return _ph_stats(f, h, floor_db)[0]


def _floor_prefix(h: np.ndarray, floor_db: float) -> int:
    """Index of the FIRST fall through the floor -- the end of the scored band.

    Selecting every point above the floor is not the same thing, and the
    difference is not academic.  A real cell falls through the floor, then
    RECOVERS onto a parasitic feed-through plateau: measured on the 021
    candidate, |H| crosses -100 dB at 3.2 kHz, comes back at 14.5 kHz and sits
    at -98.5 dB out to 100 kHz.  A boolean mask keeps both sides of that gap,
    `np.unwrap` then runs straight across an 11 kHz discontinuity, and the
    certificate reads **368.6 deg** for a cell whose true lag saturates at
    **320.7 deg** -- i.e. it turns an S1 FAIL into an apparent PASS, by 38 deg.

    The step guard does not catch it: the spurious step measured only 75 deg,
    half the 150 deg alarm.  Contiguity has to be enforced structurally.
    """
    below = np.flatnonzero(db_rel_dc(h) < floor_db)
    return int(below[0]) if below.size else len(h)


def _ph_stats(f: np.ndarray, h: np.ndarray, floor_db: float) -> tuple:
    n = _floor_prefix(h, floor_db)
    if n < 2:
        return float("nan"), float("nan"), float("nan")
    ph = np.unwrap(np.angle(h[:n])) * 180.0 / np.pi
    fx = np.asarray(np.real(f), float)
    return (float(-np.min(ph - ph[0])),
            float(np.max(np.abs(np.diff(ph)))) if n > 1 else float("nan"),
            float(fx[n - 1]))


def max_phase_step_deg(f: np.ndarray, h: np.ndarray, floor_db: float = -100.0) -> float:
    """Largest unwrap-corrected phase step inside the scored band.

    The resolvability guard that accompanies `ph_max_deg`: a band whose worst
    step approaches 180 deg is one sample away from aliasing, so its certificate
    is not trustworthy however comfortably it passes.
    """
    return _ph_stats(f, h, floor_db)[1]


def f_scored_hi(f: np.ndarray, h: np.ndarray, floor_db: float = -100.0) -> float:
    """Highest frequency the phase certificate actually scored, in Hz.

    Report it beside `ph_max_deg`: a certificate scored to 400 x fc is not a
    4-pole measurement, it is a measurement that ran into a feed-through floor.
    """
    return _ph_stats(f, h, floor_db)[2]


def integrate_noise(f: np.ndarray, dens: np.ndarray, f_lo: float, f_hi: float) -> float:
    """rms of a noise density (V/sqrt(Hz)) over [f_lo, f_hi], trapezoidal in f.

    Band limits matter: an input-referred density diverges above the cutoff
    (the gain goes to zero), so integrating to 1 kHz on a 250 Hz filter reads
    milli-volts and means nothing.
    """
    f = np.real(f).astype(float)
    d = np.abs(dens).astype(float)
    m = (f >= f_lo) & (f <= f_hi)
    fs, ds = f[m], d[m]
    if len(fs) < 2:
        return float("nan")
    # include the exact end points by interpolating the density there
    if fs[0] > f_lo:
        fs = np.insert(fs, 0, f_lo)
        ds = np.insert(ds, 0, np.interp(np.log10(f_lo), np.log10(f), d))
    if fs[-1] < f_hi:
        fs = np.append(fs, f_hi)
        ds = np.append(ds, np.interp(np.log10(f_hi), np.log10(f), d))
    return float(np.sqrt(np.trapezoid(ds ** 2, fs)))


def pick(plots: list[Plot], kind: str) -> Plot:
    """First plot whose name matches `kind` ('ac', 'noise', 'tran', 'op', ...)."""
    k = kind.lower()
    want = {
        "ac": ("ac analysis",),
        "noise": ("noise spectral density curves", "noise analysis"),
        "noise_total": ("integrated noise", "total noise"),
        "tran": ("transient analysis",),
        "op": ("operating point",),
        "dc": ("dc transfer characteristic", "dc analysis"),
    }.get(k, (k,))
    for p in plots:
        pn = p.name.lower()
        if any(w in pn for w in want):
            return p
    raise KeyError(f"no {kind!r} plot; have {[p.name for p in plots]}")
