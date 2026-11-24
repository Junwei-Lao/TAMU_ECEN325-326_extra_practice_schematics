"""Set 5B: MOSFET biasing with current mirrors (like the mirror examples and Sample Problem 2).
Easy: one mirror, one or more outputs with W/L ratios. Medium: NMOS + PMOS mirrors from one reference, mirror-fed
followers and stacked transistors. Hard: several mirrors, reference chains, cascode-style stacks."""
from .mosnet import M, R, Col, BJTCircuit

CODE = '5B'
SLUG = 'current_mirrors'
TITLE = 'Set 5B: MOSFET Biasing with Current Mirrors'
INTRO = r"""
\textbf{What this set trains.} DC analysis when the bias currents come from current mirrors. The reference current
follows from one quadratic (a resistor in series with diode-connected transistors); every transistor that shares the
gate and source nodes of a diode-connected transistor copies its current scaled by the $W/L$ ratio. Then continue
node by node and verify that every transistor is active. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each
problem before looking at its solution.
"""

KN, VTN, KPP, VTP = 200e-6, 0.7, 100e-6, 0.8       # k'_n, V_tn, k'_p, |V_tp| (W/L given per transistor)
SL = (1.1e-3, 1.4, 0.85e-3, 1.3)                    # the slides' k'W/L values (Sample Problem 2)


class DCProb:
    def __init__(self, level, build, note=''):
        self.level, self.build, self.note = level, build, note


def n(name, wl, **kw):
    return M(name, 'nmos', kp=KN, wl=wl, vt=VTN, **kw)


def p(name, wl, **kw):
    return M(name, 'pmos', kp=KPP, wl=wl, vt=VTP, **kw)


def nref(r, rv, node, q, wl, top, bot):
    return Col([R(r, rv), node, n(q, wl, diode=True)], top=top, bottom=bot, gap=4.6)


def pref(q, wl, node, r, rv, top, bot):
    return Col([p(q, wl, diode=True), node, R(r, rv)], top=top, bottom=bot, gap=4.6)


B = BJTCircuit
P = DCProb


def e1():
    return B([nref('R1', '20k', 'm', 'M1', (10, 1), 5, 0),
              Col([R('R2', '10k'), 'd2', n('M2', (20, 1), gate='m')], top=5, bottom=0)])


def e2():
    return B([pref('M1', (10, 1), 'm', 'R1', '40k', 5, -5),
              Col([p('M2', (30, 1), gate='m'), 'd2', R('R2', '10k')], top=5, bottom=-5)])


def e3():
    return B([nref('R1', '25k', 'm', 'M1', (10, 0.5), 2.5, -2.5),
              Col([R('R2', '20k'), 'd2', n('M2', (5, 0.5), gate='m')], top=2.5, bottom=-2.5),
              Col([R('R3', '5k'), 'd3', n('M3', (20, 0.5), gate='m')], top=2.5, bottom=-2.5),
              Col([R('R4', '4k'), 'd4', n('M4', (30, 0.5), gate='m')], top=2.5, bottom=-2.5)])


def e4():
    return B([pref('M1', (20, 1), 'm', 'R1', '20k', 5, 0),
              Col([p('M2', (10, 1), gate='m'), 'd2', R('R2', '30k')], top=5, bottom=0),
              Col([p('M3', (40, 1), gate='m'), 'd3', R('R3', '5k')], top=5, bottom=0)])


def e5():
    return B([nref('R1', '50k', 'm', 'M1', (5, 0.5), 5, -5),
              Col([R('R2', '10k'), 'd2', n('M2', (15, 0.5), gate='m')], top=5, bottom=-5)])


def e6():
    return B([pref('M1', (10, 1), 'm', 'R1', '30k', 3, -3),
              Col([p('M2', (20, 2), gate='m'), 'd2', R('R2', '20k')], top=3, bottom=-3),
              Col([p('M3', (20, 1), gate='m'), 'd3', R('R3', '10k')], top=3, bottom=-3)])


# ---------------------------------------------------------------- medium
def m7():
    return B([Col([p('M3', (20, 1), gate='mp', face='right'), 'd3', R('R2', '15k')], top=3, bottom=-3),
              Col([p('M1', (10, 1), diode=True), 'mp', R('R1', '20k'), 'mn', n('M2', (5, 1), diode=True)],
                  top=3, bottom=-3, gap=4.6),
              Col([R('R3', '10k'), 'd4', n('M4', (10, 1), gate='mn')], top=3, bottom=-3)])


def m8():
    return B([nref('R1', '30k', 'mn', 'M1', (10, 1), 5, 0),
              Col([p('M3', (10, 1), diode=True), 'mp', n('M2', (20, 1), gate='mn')], top=5, bottom=0, gap=4.6),
              Col([p('M4', (30, 1), gate='mp'), 'd4', R('R2', '5k')], top=5, bottom=0)])


def m9():
    return B([Col([R('R2', '400k'), 'g3', R('R3', '600k')], top=5, bottom=-5, gap=3.2),
              Col([n('M3', (10, 1), gate='g3'), 's3', n('M2', (10, 1), gate='m', face='right')], top=5, bottom=-5),
              nref('R1', '40k', 'm', 'M1', (5, 1), 5, -5)])


def m10():
    return B([pref('M1', (10, 1), 'mp', 'R1', '25k', 5, 0),
              Col([p('M2', (10, 1), gate='mp'), 'mn', n('M3', (10, 1), diode=True)], top=5, bottom=0, gap=4.6),
              Col([R('R2', '10k'), 'd4', n('M4', (20, 1), gate='mn')], top=5, bottom=0),
              Col([R('R3', '20k'), 'd5', n('M5', (5, 1), gate='mn')], top=5, bottom=0)])


def m11():
    return B([Col([R('R2', '25k'), 'g2', R('R3', '25k')], top=5, bottom=0, gap=3.2),
              Col([p('M2', (20, 1), gate='mp'), 's3', p('M3', (20, 1), gate='g2'), 'd3', R('R4', '5k')],
                  top=5, bottom=0),
              pref('M1', (10, 1), 'mp', 'R1', '30k', 5, 0)])


def m12():
    return B([nref('R1', '20k', 'm', 'M1', (10, 1), 5, -5),
              Col([R('R2', '10k'), 'd2', n('M2', (10, 1), gate='m')], top=5, bottom=-5),
              Col([n('M4', (20, 1), gate='d2'), 's4', n('M3', (20, 1), gate='m')], top=5, bottom=-5)])


# ---------------------------------------------------------------- hard
def sp2():
    ns = lambda name, **kw: M(name, 'nmos', kw=SL[0], vt=SL[1], **kw)
    ps = lambda name, **kw: M(name, 'pmos', kw=SL[2], vt=SL[3], **kw)
    return B([Col([R('R7', '25k'), 'g2', R('R8', '8k'), 'g3', R('R9', '17k')], top=5, bottom=0, gap=3.2),
              Col([ps('M1', gate='mp'), 'd1', ps('M2', gate='g2'), 'd2', ps('M3', gate='g3'), 'd3', R('R6', '25k')],
                  top=5, bottom=0),
              Col([R('R1', '15k'), 'd4', ns('M4', gate='d3'), 's4', ns('M5', gate='mn')], top=5, bottom=0),
              Col([ns('M6', gate='d4'), 's6', ns('M7', gate='mn')], top=5, bottom=0),
              Col([ps('M8', diode=True), 'mp', R('R2', '14k'), 'mn', ns('M9', diode=True)], top=5, bottom=0)])


def h14():
    return B([Col([p('M3', (40, 1), gate='mp', face='right'), 'd3', R('R2', '5k')], top=5, bottom=-5),
              Col([p('M1', (10, 1), diode=True), 'mp', R('R1', '30k'), 'mn', n('M2', (10, 1), diode=True)],
                  top=5, bottom=-5, gap=4.6),
              Col([R('R3', '10k'), 'd4', n('M5', (20, 1), gate='0'), 's5', n('M4', (20, 1), gate='mn')],
                  top=5, bottom=-5),
              Col([n('M6', (10, 1), gate='d4'), 's6', n('M7', (5, 1), gate='mn')], top=5, bottom=-5)])


def h15():
    return B([nref('R1', '40k', 'mn', 'M1', (10, 1), 6, 0),
              Col([p('M3', (10, 1), diode=True), 'mp', n('M2', (10, 1), gate='mn')], top=6, bottom=0, gap=4.6),
              Col([p('M4', (20, 1), gate='mp'), 's5', p('M5', (20, 1), gate='g5'), 'd5', R('R2', '15k')],
                  top=6, bottom=0),
              Col([R('R3', '30k'), 'g5', R('R4', '30k')], top=6, bottom=0, gap=3.2),
              Col([R('R5', '10k'), 'd6', n('M6', (30, 1), gate='mn')], top=6, bottom=0)])


def h16():
    return B([Col([p('M1', (10, 1), diode=True), 'mp', R('R1', '20k'), 'm2', n('M2', (10, 1), diode=True), 'mn',
                   n('M3', (10, 1), diode=True)], top=5, bottom=-5, gap=4.6),
              Col([p('M4', (20, 1), gate='mp'), 'd4', R('R2', '10k')], top=5, bottom=-5),
              Col([R('R3', '10k'), 'd5', n('M5', (10, 1), gate='mn')], top=5, bottom=-5)])


def h17():
    return B([pref('M1', (10, 1), 'mp', 'R1', '40k', 5, -5),
              Col([p('M2', (20, 1), gate='mp'), 'mn', n('M3', (10, 1), diode=True)], top=5, bottom=-5, gap=4.6),
              Col([R('R2', '20k'), 'd4', n('M4', (5, 1), gate='mn')], top=5, bottom=-5),
              Col([n('M6', (10, 1), gate='d4'), 's6', n('M5', (20, 1), gate='mn', face='right')], top=5, bottom=-5)])


def h18():
    return B([nref('R1', '15k', 'm1', 'M1', (10, 1), 5, -5),
              Col([p('M3', (10, 1), diode=True), 'mp', n('M2', (5, 1), gate='m1')], top=5, bottom=-5, gap=4.6),
              Col([p('M4', (40, 1), gate='mp'), 'mn', n('M5', (10, 1), diode=True)], top=5, bottom=-5, gap=4.6),
              Col([R('R2', '2k'), 'd6', n('M6', (20, 1), gate='mn')], top=5, bottom=-5),
              Col([R('R3', '2k'), 'd7', n('M7', (10, 1), gate='d6'), 's7', n('M8', (10, 1), gate='mn')],
                  top=5, bottom=-5)])


PROBLEMS = [
    P('easy', e1), P('easy', e2), P('easy', e3), P('easy', e4), P('easy', e5), P('easy', e6),
    P('medium', m7), P('medium', m8), P('medium', m9), P('medium', m10), P('medium', m11), P('medium', m12),
    P('hard', sp2, note='(This is Sample Problem 2 of the lecture.)'), P('hard', h14), P('hard', h15), P('hard', h16),
    P('hard', h17), P('hard', h18),
]
