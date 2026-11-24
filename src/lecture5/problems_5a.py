"""Set 5A: DC bias analysis of MOSFET circuits with resistive biasing (like Sample Problem 1).
Easy: one transistor. Medium: two direct-coupled transistors (one shares a resistor with the other). Hard: three or four
transistors, NMOS and PMOS mixed."""
from .mosnet import M, R, Col, BJTCircuit

CODE = '5A'
SLUG = 'dc_bias'
TITLE = 'Set 5A: MOSFET DC Bias Analysis'
INTRO = r"""
\textbf{What this set trains.} Finding the DC drain currents of MOSFET circuits biased with resistors and verifying
that every transistor is active. Gate voltages come from dividers ($I_G = 0$); each transistor then needs one
quadratic from the KVL loop through its gate--source voltage; drain voltages follow by Ohm's law. Problems 1--6 are
easy, 7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""

SLIDES = (1.1e-3, 1.4, 0.85e-3, 1.3)
ALT1 = (2e-3, 1.0, 1e-3, 1.0)
ALT2 = (0.5e-3, 0.8, 0.4e-3, 0.8)


class DCProb:
    def __init__(self, level, build, note=''):
        self.level, self.build, self.note = level, build, note


def dev(par):
    kn, vtn, kp, vtp = par

    def n(name, **kw):
        return M(name, 'nmos', kw=kn, vt=vtn, **kw)

    def p(name, **kw):
        return M(name, 'pmos', kw=kp, vt=vtp, **kw)
    return n, p


def div(a, va, node, b, vb, top, bot):
    return Col([R(a, va), node, R(b, vb)], top=top, bottom=bot, gap=3.2)


B = BJTCircuit
P = DCProb


def e1():
    n, p = dev(SLIDES)
    return B([div('R1', '600k', 'g1', 'R2', '400k', 10, 0),
              Col([R('R3', '4k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '2k')], top=10, bottom=0)])


def e2():
    n, p = dev(SLIDES)
    return B([div('R1', '300k', 'g1', 'R2', '700k', 10, 0),
              Col([R('R3', '2k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '3k')], top=10, bottom=0)])


def e3():
    n, p = dev(ALT1)
    return B([div('R1', '800k', 'g1', 'R2', '200k', 9, 0),
              Col([R('R3', '6k'), 'd1', n('M1', gate='g1')], top=9, bottom=0)])


def e4():
    n, p = dev(SLIDES)
    return B([Col([R('R1', '5k'), 'd1', n('M1', gate='0'), 's1', R('R2', '4k')], top=5, bottom=-5)])


def e5():
    n, p = dev(ALT1)
    return B([Col([R('R1', '3k'), 's1', p('M1', gate='0'), 'd1', R('R2', '2k')], top=5, bottom=-5)])


def e6():
    n, p = dev(SLIDES)
    return B([div('R1', '500k', 'g1', 'R2', '500k', 12, 0),
              Col([n('M1', gate='g1'), 's1', R('R3', '2.2k')], top=12, bottom=0)])


# ---------------------------------------------------------------- medium
def m7():
    n, p = dev(SLIDES)
    return B([div('R1', '700k', 'g1', 'R2', '300k', 10, 0),
              Col([R('R3', '10k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '5k')], top=10, bottom=0),
              Col([R('R5', '2k'), 's2', p('M2', gate='d1'), 'd2', R('R6', '3k')], top=10, bottom=0)])


def m8():
    n, p = dev(ALT1)
    return B([div('R1', '750k', 'g1', 'R2', '250k', 10, 0),
              Col([R('R3', '20k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '5k')], top=10, bottom=0),
              Col([n('M2', gate='d1'), 's2', R('R5', '3k')], top=10, bottom=0)])


def m9():
    n, p = dev(SLIDES)
    return B([div('R1', '30k', 'g1', 'R2', '70k', 5, -5),
              Col([R('R3', '10k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '10k')], top=5, bottom=-5),
              Col([R('R5', '15k'), 'd2', n('M2', gate='0', face='right'), 'd1'], top=5, bottom=None)])


def m10():
    n, p = dev(ALT2)
    return B([div('R1', '200k', 'g1', 'R2', '800k', 5, -5),
              Col([R('R3', '5k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '20k')], top=5, bottom=-5),
              Col([R('R5', '10k'), 'd2', n('M2', gate='d1'), 's2', R('R6', '5k')], top=5, bottom=-5)])


def m11():
    n, p = dev(SLIDES)
    return B([div('R1', '400k', 'g1', 'R2', '600k', 6, -6),
              Col([n('M1', gate='g1'), 's1', R('R3', '20k')], top=6, bottom=-6),
              Col([R('R4', '4k'), 'd2', n('M2', gate='s1'), 's2', R('R5', '3k')], top=6, bottom=-6)])


def m12():
    n, p = dev(ALT1)
    return B([div('R1', '500k', 'g1', 'R2', '500k', 5, -5),
              Col([R('R3', '4k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '5k')], top=5, bottom=-5),
              Col([R('R5', '2k'), 's2', p('M2', gate='d1'), 'd2', R('R6', '4k')], top=5, bottom=-5)])


# ---------------------------------------------------------------- hard
def sp1():
    n, p = dev(SLIDES)
    return B([div('R1', '30k', 'g1', 'R2', '70k', 5, -5),
              Col([R('R3', '10k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '10k')], top=5, bottom=-5),
              Col([R('R5', '20k'), 'd2', n('M2', gate='g2', face='right'), 'd1'], top=5, bottom=None),
              div('R7', '50k', 'g2', 'R6', '50k', 5, -5),
              Col([R('R9', '3k'), 's3', p('M3', gate='d2'), 'd3', R('R8', '8k')], top=5, bottom=-5),
              Col([n('M4', gate='d3'), 's4', R('R10', '500')], top=5, bottom=-5)])


def h14():
    n, p = dev(SLIDES)
    return B([div('R1', '400k', 'g1', 'R2', '600k', 5, -5),
              Col([R('R3', '10k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '8k')], top=5, bottom=-5),
              Col([R('R5', '4k'), 's2', p('M2', gate='d1'), 'd2', R('R6', '10k')], top=5, bottom=-5),
              Col([n('M3', gate='d2'), 's3', R('R7', '2k')], top=5, bottom=-5)])


def h15():
    n, p = dev(ALT1)
    return B([div('R1', '600k', 'g1', 'R2', '400k', 6, -6),
              Col([R('R3', '6k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '5k')], top=6, bottom=-6),
              Col([R('R5', '8k'), 'd2', n('M2', gate='d1'), 's2', R('R6', '6k')], top=6, bottom=-6),
              Col([R('R7', '3k'), 's3', p('M3', gate='d2'), 'd3', R('R8', '4k')], top=6, bottom=-6),
              Col([n('M4', gate='d3'), 's4', R('R9', '1k')], top=6, bottom=-6)])


def h16():
    n, p = dev(SLIDES)
    return B([div('R1', '40k', 'g1', 'R2', '60k', 5, -5),
              Col([R('R3', '8k'), 's1', p('M1', gate='g1'), 'd1', R('R4', '6k')], top=5, bottom=-5),
              Col([R('R5', '14k'), 'd2', n('M2', gate='0', face='right'), 'd1'], top=5, bottom=None),
              Col([R('R6', '2k'), 's3', p('M3', gate='d2'), 'd3', R('R7', '8k')], top=5, bottom=-5),
              Col([n('M4', gate='d3'), 's4', R('R8', '1k')], top=5, bottom=-5)])


def h17():
    n, p = dev(ALT2)
    return B([div('R1', '300k', 'g1', 'R2', '700k', 6, -6),
              Col([R('R3', '5k'), 'd1', n('M1', gate='g1'), 's1', R('R4', '10k')], top=6, bottom=-6),
              Col([R('R5', '5k'), 's2', p('M2', gate='d1'), 'd2', R('R6', '20k')], top=6, bottom=-6),
              Col([R('R7', '10k'), 'd3', n('M3', gate='d2'), 's3', R('R8', '4k')], top=6, bottom=-6),
              Col([R('R9', '2k'), 's4', p('M4', gate='d3'), 'd4', R('R10', '5k')], top=6, bottom=-6)])


def h18():
    n, p = dev(SLIDES)
    return B([div('R1', '700k', 'g1', 'R2', '300k', 10, 0),
              Col([R('R3', '4k'), 'x', n('M1', gate='g1'), 's1', R('R4', '2k')], top=10, bottom=0),
              Col([p('M2', gate='g2', face='right'), 'd2', R('R5', '20k')], top_node='x', bottom=0),
              div('R6', '400k', 'g2', 'R7', '600k', 10, 0),
              Col([R('R8', '8k'), 'd3', n('M3', gate='d2'), 's3', R('R9', '1k')], top=10, bottom=0),
              Col([R('R10', '2k'), 's4', p('M4', gate='d3'), 'd4', R('R11', '2k')], top=10, bottom=0)])


PROBLEMS = [
    P('easy', e1), P('easy', e2), P('easy', e3), P('easy', e4), P('easy', e5), P('easy', e6),
    P('medium', m7), P('medium', m8), P('medium', m9), P('medium', m10), P('medium', m11), P('medium', m12),
    P('hard', sp1, note='(This is Sample Problem 1 of the lecture.)'), P('hard', h14), P('hard', h15), P('hard', h16),
    P('hard', h17), P('hard', h18),
]
