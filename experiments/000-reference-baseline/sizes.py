"""Sizing points for the SG13G2 reference baseline (the expert topology).

Geometry is carried over from the originating design and then re-tuned here,
because the two technologies share neither a threshold, an oxide, nor a body
tie.  Both biquads are p-input followers (see `lab.dut.build_reference`).

Current budget: every bias device is an integer multiple of the `iref` mirror
unit, so the core current is exact by construction:

    biquad A: bias_a_out (m=2) sources vout_1 ; bias_a_int (m=1) sinks net2
    biquad B: bias_b_out (m=2) sources voutp  ; bias_b_int (m=1) sinks net4
    => per side 2 + 2 = 4 units, both sides = 8 units = 8 nA at iref = 1 nA
"""
from lab.dut import Dev, Design

U = 1e-6
P = 1e-12


def v0() -> Design:
    """First guess: the originating geometries on hv devices, all-p followers."""
    return Design(
        topology="reference",
        devs={
            "in_a":       Dev(4 * U, 4 * U),          # p follower, biquad A
            "bias_a_int": Dev(5 * U, 8 * U),          # n sink at net2   (1 unit)
            "gmf_a":      Dev(4 * U, 4 * U),          # n shunt feedback, biquad A
            "bias_a_out": Dev(5 * U, 12 * U, m=2),    # p source at vout_1 (2 units)
            "in_b":       Dev(4 * U, 4 * U),          # p follower, biquad B
            "bias_b_int": Dev(5 * U, 8 * U),          # n sink at net4   (1 unit)
            "gmf_b":      Dev(4 * U, 4 * U),          # n shunt feedback, biquad B
            "bias_b_out": Dev(5 * U, 12 * U, m=2),    # p source at voutp (2 units)
        },
        c1_a=34.96 * P, c2_a=4.29 * P, c1_b=12.13 * P, c2_b=12.36 * P,
        iref=1e-9, vicm=0.25, vocm=1.25,
        note="v0: originating geometry, all-p followers, unretuned",
    )
