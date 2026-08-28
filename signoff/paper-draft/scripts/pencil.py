"""Numeric H(jw) and Z(jw) sweeps over a netlist2tf MNA system, by direct dense solves.

The pole/zero half of this module has been **upstreamed**: `solve()` is now a thin adapter
over `spicexplorer_netlist2tf.poles_zeros`, which does the pencil eigen-solve the platform
package now owns.  What stays here is what the package does not provide -- evaluating
`H(s)` and a transimpedance `Z_T(s)` numerically over a frequency vector, which the noise
and distortion budgets sweep thousands of times.

Why a pencil at all, rather than `extract_tf` + `sympy.roots`: the full differential cell is
a 13-node system whose `Fidelity.FULL` model puts a capacitance on almost every branch, so
the symbolic Berkowitz determinant `extract_tf` computes does not finish in useful time,
and even when it does, expanding a degree-15 polynomial whose coefficients span 40 decades
loses the low-frequency roots to float cancellation.  `extract_tf` remains the right tool
on the DM half-circuit (5 nodes, and it is the SYMBOLIC form the paper quotes).

The mathematics is one line.  netlist2tf's stamped matrix is exactly affine in `s`,

    Y(s) = G + s*C

(every primitive is a conductance, a VCCS, or `s*C`), and the input nodes are driven by
ideal sources, so partitioning into driven (`i`) and solved (`r`) nodes gives

    Y_rr(s) v = -Y_ri(s) u ,    y = L^T v

    H(s) = det(M(s)) / det(Y_rr(s)) ,   M(s) = [[Y_rr(s), Y_ri(s) u], [L^T, 0]]

so the POLES are the finite eigenvalues of the pencil (-G_rr, C_rr) and the ZEROS are the
finite eigenvalues of the corresponding pencil of `M`.  Both are QZ problems: no
polynomial expansion, no cancellation, and the `s`-dependence of the input coupling (the
gate capacitance that feeds the input straight through to the output) is carried exactly,
which is what puts the feed-through zeros where they belong.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp

from spicexplorer_netlist2tf import poles_zeros
from spicexplorer_netlist2tf.tf import S


def split_gc(system) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """(G, C, node order) with Y = G + s*C, asserted exact."""
    Y = system.Y
    n = Y.shape[0]
    G = np.zeros((n, n), dtype=float)
    C = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            e = sp.expand(Y[i, j])
            g, c = e.coeff(S, 0), e.coeff(S, 1)
            if sp.simplify(e - (g + S * c)) != 0:
                raise ValueError(f"Y[{i},{j}] is not affine in s: {e}")
            G[i, j] = float(g)
            C[i, j] = float(c)
    order = [None] * n
    for net in system.nets if hasattr(system, "nets") else []:
        r = system.row_of(net)
        if r is not None:
            order[r] = net
    return G, C, order


@dataclass(frozen=True)
class PZ:
    poles: np.ndarray
    zeros: np.ndarray
    gain_dc: complex
    n_states: int


def solve(system, out: tuple[str, str], drive: dict[str, float]) -> PZ:
    """Poles and zeros of the transfer from `drive` (node -> excitation) to `out`.

    `drive` names the nodes held by ideal sources and the level each is held at:
    `{"vinp": +0.5, "vinn": -0.5}` is the bench's differential convention -- which is
    exactly the package's `drive="dm"`, and `{a: +1, b: +1}` its `drive="cm"`.

    Thin adapter over `spicexplorer_netlist2tf.poles_zeros`; the roots are unpacked back
    into the flat complex arrays the rest of this pack sweeps over.  `gain_dc` still comes
    from `h_at` rather than the package's real-valued `dc_gain`, because the callers here
    want the complex value.
    """
    ports = list(drive)
    if len(ports) != 2:
        raise ValueError(f"expected two driven nodes, got {drive}")
    levels = [drive[k] for k in ports]
    if levels == [0.5, -0.5]:
        mode = "dm"
    elif levels == [1.0, 1.0]:
        mode = "cm"
    else:
        raise ValueError(
            f"drive {drive} is neither the dm (+/-0.5) nor the cm (+1,+1) convention "
            "netlist2tf.poles_zeros accepts"
        )
    if any(system.row_of(k) is None for k in ports):
        raise ValueError(f"a driven node is at ac ground: {drive}")

    res = poles_zeros(system, out, (ports[0], ports[1]), drive=mode)
    unpack = lambda rs: np.array(  # noqa: E731
        [complex(r.value_real, r.value_imag) for r in rs for _ in range(r.multiplicity)]
    )
    poles = unpack(res.poles)
    return PZ(poles=poles, zeros=unpack(res.zeros),
              gain_dc=h_at(system, out, drive, 0.0), n_states=len(poles))


def h_at(system, out: tuple[str, str], drive: dict[str, float],
         s_val: complex) -> complex:
    """H(s) at one `s`, by a direct dense solve -- the reference every fit is checked on."""
    G, C, _ = split_gc(system)
    n = G.shape[0]
    idx_in = [system.row_of(k) for k in drive]
    u = np.array([drive[k] for k in drive], dtype=float)
    rest = [i for i in range(n) if i not in idx_in]
    Y = G + s_val * C
    v = np.linalg.solve(Y[np.ix_(rest, rest)], -Y[np.ix_(rest, idx_in)] @ u)
    got = 0j
    for net, sign in ((out[0], 1.0), (out[1], -1.0)):
        r = system.row_of(net)
        if r is not None:
            got += sign * v[rest.index(r)]
    return complex(got)


def h_over(system, out: tuple[str, str], drive: dict[str, float],
           f: np.ndarray) -> np.ndarray:
    """H(j2*pi*f) over a frequency grid (one factorization per point; the systems here
    are 13x13, so this is milliseconds and needs no cleverness)."""
    return np.array([h_at(system, out, drive, 2j * np.pi * float(x)) for x in f])


def h_from_pz(pz: PZ, f: np.ndarray, *, k: complex | None = None) -> np.ndarray:
    """Reconstruct H(j2*pi*f) from the poles, zeros and the dc gain."""
    s = 2j * np.pi * f
    num = np.ones_like(s)
    for z in pz.zeros:
        num = num * (s - z)
    den = np.ones_like(s)
    for p in pz.poles:
        den = den * (s - p)
    if k is None:
        k = pz.gain_dc * np.prod(-pz.poles) / np.prod(-pz.zeros) if len(pz.zeros) \
            else pz.gain_dc * np.prod(-pz.poles)
    return k * num / den


def biquad(p: complex) -> tuple[float, float]:
    """(f0 in Hz, Q) of a pole (or of a conjugate pair, given either member)."""
    w0 = abs(p)
    q = float("inf") if p.real >= 0 else w0 / (-2.0 * p.real)
    return w0 / (2 * np.pi), q


def pair_up(poles: np.ndarray, tol: float = 1e-6) -> list[tuple[complex, complex | None]]:
    """Group poles into conjugate pairs (a real pole comes back unpaired)."""
    left = list(poles)
    out: list[tuple[complex, complex | None]] = []
    while left:
        p = left.pop(0)
        if abs(p.imag) < tol * max(1.0, abs(p)):
            out.append((p, None))
            continue
        j = min(range(len(left)), key=lambda i: abs(left[i] - np.conj(p)), default=None)
        if j is not None and abs(left[j] - np.conj(p)) < 1e-6 * abs(p):
            out.append((p, left.pop(j)))
        else:
            out.append((p, None))
    return out


def z_transfer(system, out: tuple[str, str], inject: tuple[str, str],
               grounded: tuple[str, ...], f: np.ndarray) -> np.ndarray:
    """Transimpedance Z_T(j2*pi*f) from a unit current forced `inject[0]` -> `inject[1]`
    to the differential output, with every node in `grounded` held at ac ground.

    This is the numeric twin of `spicexplorer_netlist2tf.transimpedance` -- same equations,
    same RHS -- built here because the symbolic Cramer solve the package uses does not
    finish on the full 13-node cell.  `noise_analysis.py` runs BOTH on the DM half-circuit
    and asserts they agree, which is what licenses using this one on the full cell.

    `grounded` is the source-zeroing the noise analysis needs: with the signal source off,
    the bench's balun holds vinp and vinn at their dc level, so both are ac grounds.
    """
    G, C, _ = split_gc(system)
    n = G.shape[0]
    off = {system.row_of(g) for g in grounded} - {None}
    rest = [i for i in range(n) if i not in off]
    ip, im = system.row_of(inject[0]), system.row_of(inject[1])
    rhs = np.zeros(len(rest))
    for r, sign in ((ip, 1.0), (im, -1.0)):
        if r is not None and r in rest:
            rhs[rest.index(r)] += sign
    L = np.zeros(len(rest))
    for net, sign in ((out[0], 1.0), (out[1], -1.0)):
        r = system.row_of(net)
        if r is not None and r in rest:
            L[rest.index(r)] = sign
    Gr, Cr = G[np.ix_(rest, rest)], C[np.ix_(rest, rest)]
    z = np.empty(len(f), dtype=complex)
    for k, x in enumerate(f):
        z[k] = L @ np.linalg.solve(Gr + 2j * np.pi * float(x) * Cr, rhs)
    return z
