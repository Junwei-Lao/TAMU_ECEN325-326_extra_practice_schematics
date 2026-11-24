"""Set 5D: small-signal transfer functions of MOSFET amplifiers (like Sample Problems 3 and 4).
Easy: one stage (CS, CD, CG). Medium: two stages. Hard: three or four stages, mirror-biased stages."""
from lecture1.ladder import Ser, Par
from lecture1.narrative import Sine
from .mosnet import M, R, C, Col, BJTCircuit, Src, Load
from .ac5 import Stage

CODE = '5D'
SLUG = 'small_signal'
TITLE = 'Set 5D: MOSFET Amplifiers --- Small-Signal Analysis'
INTRO = r"""
\textbf{What this set trains.} The small-signal transfer function of single- and multi-stage MOSFET amplifiers with
the node-impedance method: $g_m$ of every transistor, the node impedances ($Z_{gate} = Z_{drain} = \infty$,
$Z_{source} = 1/g_m$), and the product of the node-to-node gains along the signal path. Then the Bode plot and the
steady-state output. $r_o = \infty$; capacitors marked $\infty$ are shorts at the signal frequencies. The DC drain
currents are given (they follow from a DC analysis as in sets 5A/5B). Problems 1--6 are easy, 7--12 medium, 13--18
hard. Try each problem before looking at its solution.
"""

SL = (1.1e-3, 1.4, 0.85e-3, 1.3)
ALT = (2e-3, 1.0, 1e-3, 1.0)
KN, VTN, KPP, VTP = 200e-6, 0.7, 100e-6, 0.8


class ACProb:
    def __init__(self, level, build, vin, note=''):
        self.level, self.build, self.vin, self.note = level, build, vin, note


def dev(par=SL):
    kn, vtn, kp, vtp = par
    return (lambda name, **kw: M(name, 'nmos', kw=kn, vt=vtn, **kw),
            lambda name, **kw: M(name, 'pmos', kw=kp, vt=vtp, **kw))


def div(a, va, node, b, vb, top, bot):
    return Col([R(a, va), node, R(b, vb)], top=top, bottom=bot, gap=3.2)


B = BJTCircuit
P = ACProb


# ---------------------------------------------------------------- easy
def e1():
    n, p = dev()
    q = n('M1', gate='g1')
    c = B([div('R1', '600k', 'g1', 'R2', '400k', 10, 0),
           Col([R('R3', '4k'), 'd1', q, 's1', Par(R('R4', '2k'), C('C2', 'inf'))], top=10, bottom=0)],
          src=Src('g1', c=C('C1', '100n')), load=Load('d1', c=C('C3', 'inf'), rl=R('R5', '10k')))
    return c, [Stage(q, 'CS')]


def e2():
    n, p = dev()
    q = p('M1', gate='g1')
    c = B([div('R1', '300k', 'g1', 'R2', '700k', 10, 0),
           Col([R('R3', '2k'), 's1', q, 'd1', R('R4', '3k')], top=10, bottom=0)],
          src=Src('g1', rs=R('R6', '50k'), c=C('C1', '22n')), load=Load('d1', c=C('C2', 'inf'), rl=R('R5', '6k')))
    return c, [Stage(q, 'CS')]


def e3():
    n, p = dev()
    q = n('M1', gate='g1')
    c = B([div('R1', '500k', 'g1', 'R2', '500k', 12, 0),
           Col([q, 's1', R('R3', '2.2k')], top=12, bottom=0)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('s1', c=C('C2', '1u'), rl=R('R4', '1k')))
    return c, [Stage(q, 'CD')]


def e4():
    n, p = dev(ALT)
    q = n('M1', gate='g1', face='right')
    c = B([Col([R('R3', '5k'), 'd1', q, 's1', R('R4', '3k')], top=10, bottom=0),
           Col([R('R1', '700k'), 'g1', Par(R('R2', '300k'), C('C3', 'inf'))], top=10, bottom=0, gap=3.4)],
          src=Src('s1', rs=R('R6', '100'), c=C('C1', '10u')), load=Load('d1', c=C('C2', 'inf'), rl=R('R5', '10k')))
    return c, [Stage(q, 'CG')]


def e5():
    n, p = dev(ALT)
    q = n('M1', gate='g1')
    c = B([div('R1', '800k', 'g1', 'R2', '200k', 9, 0),
           Col([R('R3', '6k'), 'd1', q], top=9, bottom=0),
           Col([C('C2', '2n')], top_node='d1', bottom=0, gap=3.0)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('d1', c=C('C3', 'inf'), rl=R('R4', '12k')))
    return c, [Stage(q, 'CS')]


def e6():
    n, p = dev()
    q = p('M1', gate='g1')
    c = B([div('R1', '400k', 'g1', 'R2', '600k', 10, 0),
           Col([R('R3', '3k'), 's1', q], top=10, bottom=0)],
          src=Src('g1', c=C('C1', '47n')), load=Load('s1', c=C('C2', 'inf'), rl=R('R4', '2k')))
    return c, [Stage(q, 'CD')]


# ---------------------------------------------------------------- medium
def m7():
    n, p = dev()
    q1, q2 = n('M1', gate='g1'), n('M2', gate='d1')
    c = B([div('R1', '750k', 'g1', 'R2', '250k', 12, 0),
           Col([R('R3', '20k'), 'd1', q1, 's1', Par(R('R4', '2k'), C('C2', 'inf'))], top=12, bottom=0),
           Col([q2, 's2', R('R5', '3k')], top=12, bottom=0)],
          src=Src('g1', c=C('C1', '220n')), load=Load('s2', c=C('C3', 'inf'), rl=R('R6', '1k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CD')]


def m8():
    n, p = dev()
    q1, q2 = p('M1', gate='g1'), n('M2', gate='0', face='right')
    c = B([div('R1', '30k', 'g1', 'R2', '70k', 5, -5),
           Col([Par(R('R3', '10k'), C('C2', 'inf')), 's1', q1, 'd1', R('R4', '10k')], top=5, bottom=-5),
           Col([R('R5', '15k'), 'd2', q2, 'd1'], top=5, bottom=None)],
          src=Src('g1', c=C('C1', '100n')), load=Load('d2', c=C('C3', 'inf'), rl=R('R6', '30k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CG')]


def m9():
    n, p = dev()
    q1, q2 = n('M1', gate='g1'), n('M2', gate='s1')
    c = B([div('R1', '400k', 'g1', 'R2', '600k', 6, -6),
           Col([q1, 's1', R('R3', '20k')], top=6, bottom=-6),
           Col([R('R4', '4k'), 'd2', q2, 's2', Par(R('R5', '3k'), C('C2', '10u'))], top=6, bottom=-6)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('d2', c=C('C3', 'inf'), rl=R('R6', '8k')))
    return c, [Stage(q1, 'CD'), Stage(q2, 'CS')]


def m10():
    n, p = dev()
    q1, q2 = n('M1', gate='g1'), p('M2', gate='d1')
    c = B([div('R1', '700k', 'g1', 'R2', '300k', 10, 0),
           Col([R('R3', '10k'), 'd1', q1, 's1', R('R4', '5k')], top=10, bottom=0),
           Col([Par(R('R5', '2k'), C('C2', 'inf')), 's2', q2, 'd2', R('R6', '3k')], top=10, bottom=0)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('d2', c=C('C3', '1u'), rl=R('R7', '3k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CS')]


def m11():
    n, p = dev(ALT)
    q1, q2 = n('M1', gate='g1', face='right'), n('M2', gate='d1')
    c = B([Col([R('R3', '20k'), 'd1', q1, 's1', R('R4', '5k')], top=10, bottom=0),
           Col([R('R1', '750k'), 'g1', Par(R('R2', '250k'), C('C3', 'inf'))], top=10, bottom=0, gap=3.4),
           Col([q2, 's2', R('R5', '3k')], top=10, bottom=0)],
          src=Src('s1', rs=R('R7', '200'), c=C('C1', 'inf')), load=Load('s2', c=C('C2', '1u'), rl=R('R6', '1k')))
    return c, [Stage(q1, 'CG'), Stage(q2, 'CD')]


def m12():
    n, p = dev(ALT)
    q1, q2 = n('M1', gate='g1'), p('M2', gate='d1')
    c = B([div('R1', '500k', 'g1', 'R2', '500k', 5, -5),
           Col([R('R3', '4k'), 'd1', q1, 's1', Par(R('R4', '5k'), C('C2', '4.7u'))], top=5, bottom=-5),
           Col([R('R5', '2k'), 's2', q2, 'd2', R('R6', '4k')], top=5, bottom=-5)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('d2', c=C('C3', 'inf'), rl=R('R7', '4k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CS')]


# ---------------------------------------------------------------- hard
def sp3():
    n, p = dev()
    q1, q2, q3, q4 = p('M1', gate='g1'), n('M2', gate='g2', face='right'), p('M3', gate='d2'), n('M4', gate='d3')
    c = B([div('R1', '30k', 'g1', 'R2', '70k', 5, -5),
           Col([Par(R('R3', '10k'), C('C2', 'inf')), 's1', q1, 'd1', Par(R('R4', '10k'), C('C3', '5n'))],
               top=5, bottom=-5),
           Col([R('R5', '20k'), 'd2', q2, 'd1'], top=5, bottom=None),
           div('R7', '50k', 'g2', 'R6', '50k', 5, -5),
           Col([Par(R('R9', '3k'), C('C5', 'inf')), 's3', q3, 'd3', R('R8', '8k')], top=5, bottom=-5),
           Col([q4, 's4', R('R10', '500')], top=5, bottom=-5)],
          src=Src('g1', c=C('C1', '100n')), load=Load('s4', c=C('C6', 'inf'), rl=R('R11', '1k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CG'), Stage(q3, 'CS'), Stage(q4, 'CD')]


def sp4():
    n, p = dev()
    q2, q3, q4, q6 = p('M2', gate='g2'), p('M3', gate='g3'), n('M4', gate='d3'), n('M6', gate='d4')
    c = B([Col([R('R7', '25k'), 'g2', R('R8', '8k'), 'g3', Par(R('R9', '17k'), C('C1', 'inf'))], top=5, bottom=0,
               gap=3.4),
           Col([p('M1', gate='mp'), 'd1', q2, 'd2', q3, 'd3', R('R6', '25k')], top=5, bottom=0),
           Col([C('C4', 'inf'), 'd1'], top=5, bottom=None, gap=2.4),
           Col([C('C3', '2n'), 'd2'], top=5, bottom=None, gap=3.0),
           Col([R('R1', '15k'), 'd4', q4, 's4', n('M5', gate='mn')], top=5, bottom=0),
           Col([C('C5', 'inf')], top_node='s4', bottom=0, gap=3.0),
           Col([q6, 's6', n('M7', gate='mn')], top=5, bottom=0),
           Col([p('M8', diode=True), 'mp', R('R2', '14k'), 'mn', n('M9', diode=True)], top=5, bottom=0)],
          src=Src('g2', c=C('C2', '200n')), load=Load('s6', c=C('C6', 'inf'), rl=R('R10', '10k')))
    return c, [Stage(q2, 'CS'), Stage(q3, 'CG'), Stage(q4, 'CS'), Stage(q6, 'CD')]


def h15():
    n, p = dev()
    q1, q2, q3 = n('M1', gate='g1'), p('M2', gate='d1'), n('M3', gate='d2')
    c = B([div('R1', '400k', 'g1', 'R2', '600k', 5, -5),
           Col([R('R3', '10k'), 'd1', q1, 's1', Par(R('R4', '8k'), C('C2', 'inf'))], top=5, bottom=-5),
           Col([Par(R('R5', '4k'), C('C3', '1u')), 's2', q2, 'd2', R('R6', '10k')], top=5, bottom=-5),
           Col([q3, 's3', R('R7', '2k')], top=5, bottom=-5)],
          src=Src('g1', rs=R('R9', '10k'), c=C('C1', '100n')), load=Load('s3', c=C('C4', 'inf'), rl=R('R8', '2k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CS'), Stage(q3, 'CD')]


def h16():
    n, p = dev()
    q1, q2, q3, q4 = p('M1', gate='g1'), n('M2', gate='0', face='right'), p('M3', gate='d2'), n('M4', gate='d3')
    c = B([div('R1', '40k', 'g1', 'R2', '60k', 5, -5),
           Col([Par(R('R3', '8k'), C('C2', 'inf')), 's1', q1, 'd1', R('R4', '6k')], top=5, bottom=-5),
           Col([R('R5', '14k'), 'd2', q2, 'd1'], top=5, bottom=None),
           Col([C('C3', '1n')], top_node='d2', bottom=0, gap=3.0),
           Col([Par(R('R6', '2k'), C('C4', 'inf')), 's3', q3, 'd3', R('R7', '8k')], top=5, bottom=-5),
           Col([q4, 's4', R('R8', '1k')], top=5, bottom=-5)],
          src=Src('g1', c=C('C1', '470n')), load=Load('s4', c=C('C5', 'inf'), rl=R('R9', '1k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CG'), Stage(q3, 'CS'), Stage(q4, 'CD')]


def h17():
    n = lambda name, wl, **kw: M(name, 'nmos', kp=KN, vt=VTN, wl=wl, **kw)
    p = lambda name, wl, **kw: M(name, 'pmos', kp=KPP, vt=VTP, wl=wl, **kw)
    q2, q4 = n('M2', (20, 1), gate='g2'), n('M4', (20, 1), gate='d2')
    c = B([div('R1', '500k', 'g2', 'R2', '500k', 5, -5),
           Col([R('R5', '10k'), 'd2', q2, 's2', n('M5', (20, 1), gate='mn')], top=5, bottom=-5),
           Col([C('C2', 'inf')], top_node='s2', bottom=0, gap=3.0),
           Col([q4, 's4', n('M6', (20, 1), gate='mn')], top=5, bottom=-5),
           Col([p('M1', (10, 1), diode=True), 'mp', R('R3', '40k'), 'mn', n('M7', (10, 1), diode=True)],
               top=5, bottom=-5)],
          src=Src('g2', c=C('C1', '100n')), load=Load('s4', c=C('C3', '1u'), rl=R('R4', '2k')))
    return c, [Stage(q2, 'CS'), Stage(q4, 'CD')]


def h18():
    n, p = dev(ALT)
    q1, q2, q3, q4 = p('M1', gate='g1'), n('M2', gate='d1'), p('M3', gate='d2'), n('M4', gate='d3')
    c = B([div('R1', '600k', 'g1', 'R2', '400k', 6, -6),
           Col([Par(R('R3', '6k'), C('C2', 'inf')), 's1', q1, 'd1', R('R4', '5k')], top=6, bottom=-6),
           Col([R('R5', '8k'), 'd2', q2, 's2', Par(R('R6', '6k'), C('C3', '2.2u'))], top=6, bottom=-6),
           Col([Par(R('R7', '3k'), C('C4', 'inf')), 's3', q3, 'd3', R('R8', '4k')], top=6, bottom=-6),
           Col([q4, 's4', R('R9', '1k')], top=6, bottom=-6)],
          src=Src('g1', c=C('C1', 'inf')), load=Load('s4', c=C('C5', 'inf'), rl=R('R10', '1k')))
    return c, [Stage(q1, 'CS'), Stage(q2, 'CS'), Stage(q3, 'CS'), Stage(q4, 'CD')]


PROBLEMS = [
    P('easy', e1, Sine(10e-3, 100)), P('easy', e2, Sine(20e-3, 1e3)), P('easy', e3, Sine(0.5, 50)),
    P('easy', e4, Sine(5e-3, 200)), P('easy', e5, Sine(10e-3, 20e3)), P('easy', e6, Sine(0.2, 5)),
    P('medium', m7, Sine(5e-3, 10)), P('medium', m8, Sine(5e-3, 1e3)), P('medium', m9, Sine(10e-3, 100)),
    P('medium', m10, Sine(2e-3, 100)), P('medium', m11, Sine(5e-3, 1e3)), P('medium', m12, Sine(5e-3, 20)),
    P('hard', sp3, Sine(5e-3, 1e3), note='(This is Sample Problem 3 of the lecture.)'),
    P('hard', sp4, Sine(10e-3, 5e3), note='(This is Sample Problem 4 of the lecture.)'),
    P('hard', h15, Sine(1e-3, 1e3)), P('hard', h16, Sine(1e-3, 2e3)), P('hard', h17, Sine(10e-3, 100)),
    P('hard', h18, Sine(0.5e-3, 1e3)),
]
