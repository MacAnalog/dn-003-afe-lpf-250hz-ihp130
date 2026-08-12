"""Starting sizing points for the three ported candidate topologies.

Geometry is the originating design's, carried over verbatim as a STARTING
POINT only -- the two technologies share neither threshold, oxide, nor body tie,
so every one of these numbers is expected to move.  What is carried over and
must NOT move is the topology and the operating-point INTENT (which device is
the ladder reference, which node is high-Z, the pole/Q allocation).
"""
from lab.dut import Dev, Design

U = 1e-6
P = 1e-12


def a0() -> Design:
    """020A -- branch-stacked followers."""
    return Design(
        topology="a",
        devs={
            "in_a":       Dev(32 * U, 8 * U),     # n follower, biquad A
            "gmf_a":      Dev(2 * U, 120 * U),    # p shunt feedback, biquad A
            "bias_a_out": Dev(13.4 * U, 8 * U),   # n sink at vout_1  (mirror unit)
            "bridge":     Dev(1 * U, 8.4 * U),    # p common-gate bridge
            "in_b":       Dev(4 * U, 14 * U),     # p follower, biquad B
            "gmf_b":      Dev(1 * U, 80 * U),     # n shunt feedback -- SETS I_ladder
            "bias_b_out": Dev(12.1 * U, 12 * U),  # p source at voutp (mirror unit)
        },
        c1_a=7.348 * P, c2_a=16.026 * P, c1_b=30.615 * P, c2_b=9.374 * P,
        iref=2.4e-9, vicm=0.70, vocm=0.80,
        note="a0: originating 020A geometry, unretuned",
    )


def b0() -> Design:
    """020B -- the gm_f merge."""
    return Design(
        topology="b",
        devs={
            "in_a":       Dev(4 * U, 4 * U),      # p follower, biquad A
            "gmf_a":      Dev(4 * U, 4 * U),      # n shunt feedback, biquad A
            "bias_a_int": Dev(5 * U, 8 * U),      # n sink at net2 (mirror unit)
            "bridge":     Dev(1 * U, 8.4 * U),    # p common-gate bridge
            "in_b":       Dev(4 * U, 4 * U),      # p follower, biquad B
            "gmf_b":      Dev(5 * U, 12 * U),     # MERGED: bias source AND gm_f
        },
        c1_a=9.636 * P, c2_a=20.592 * P, c1_b=40.524 * P, c2_b=12.408 * P,
        iref=1.0e-9, vicm=0.25, vocm=1.25,
        note="b0: originating 020B geometry, unretuned",
    )


def c0() -> Design:
    """020C -- the merge under the total-capacitance allocation."""
    return Design(
        topology="c",
        devs={
            "in_a":       Dev(4 * U, 4 * U),
            "gmf_a":      Dev(4 * U, 4 * U),
            "bias_a_int": Dev(5 * U, 8 * U),
            "bridge":     Dev(1 * U, 8.4 * U),
            "in_b":       Dev(4 * U, 4 * U),
            "gmf_b":      Dev(4 * U, 16 * U),
        },
        c1_a=7.043 * P, c2_a=15.051 * P, c1_b=30.248 * P, c2_b=7.814 * P,
        iref=0.8e-9, vicm=0.25, vocm=1.25,
        note="c0: originating 020C geometry, unretuned",
    )
