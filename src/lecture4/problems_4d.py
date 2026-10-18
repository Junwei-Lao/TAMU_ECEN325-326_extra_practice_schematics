"""Set 4D: small-signal transfer functions of BJT amplifiers (like Sample Problems 7-10).
Easy: one stage (CE, CC, CB) with one or two capacitors. Medium: two stages, bypass capacitors, a CB stage.
Hard: three or four stages, direct and capacitive coupling."""
from lecture1.ladder import Ser, Par
from lecture1.narrative import Sine
from .bjtnet import R, C, Q, Col, BJTCircuit, Src, Load
from .parts import div
from .ac import Stage

CODE = '4D'
SLUG = 'small_signal'
TITLE = 'Set 4D: BJT Amplifiers --- Small-Signal Analysis'
INTRO = r"""
\textbf{What this set trains.} The small-signal transfer function of single- and multi-stage BJT amplifiers with the
node-impedance method: $r_e$ of every transistor, the input resistance of every stage (from the last one
backwards), and the product of the node-to-node gains along the signal path. Then the Bode plot and the
steady-state output. $\beta = 100$, $V_T = 25$\,mV, $r_o = \infty$; capacitors marked $\infty$ are shorts at the signal
frequencies. The DC collector currents are given (they follow from a DC analysis as in sets 4A/4B). Problems 1--6
are easy, 7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""


class ACProb:
    def __init__(self, level, build, vin, note=''):
        self.level, self.build, self.vin, self.note = level, build, vin, note


def ce1(re_z, c1='inf', c2='inf', rs=None, rl='10k', cl=None, vcc=12, r1='30k', r2='10k', rc='5.6k'):
    q1 = Q('Q1', 'npn', base='b1')
    cols = [div('R1', r1, 'b1', 'R2', r2, vcc, 0),
            Col([R('R3', rc), 'c1', q1, 'e1', re_z], top=vcc, bottom=0)]
    if cl:
        cols.append(Col([C('C3', cl)], top_node='c1', bottom=0, gap=3.0))
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R6', rs) if rs else None, c=C('C1', c1) if c1 else None),
                      load=Load('c1', c=C('C2', c2) if c2 else None, rl=R('R5', rl) if rl else None))
    return circ, [Stage(q1, 'CE')]


def cc1(c1='1u', c2='10u', rl='1k', vcc=10, rs=None):
    q1 = Q('Q1', 'npn', base='b1')
    cols = [div('R1', '20k', 'b1', 'R2', '20k', vcc, 0), Col([q1, 'e1', R('R3', '2.15k')], top=vcc, bottom=0)]
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R6', rs) if rs else None, c=C('C1', c1)),
                      load=Load('e1', c=C('C2', c2), rl=R('R5', rl)))
    return circ, [Stage(q1, 'CC')]


def cb1(c1='10u', rl='5k', rs='50', vcc=10):
    q1 = Q('Q1', 'npn', base='b1', face='right')
    cols = [Col([R('R4', '4.7k'), 'c1', q1, 'e1', R('R3', '1.3k')], top=vcc, bottom=0),
            Col([R('R1', '8k'), 'b1', Par(R('R2', '2k'), C('C3', 'inf'))], top=vcc, bottom=0, gap=3.4)]
    circ = BJTCircuit(cols, src=Src('e1', rs=R('R6', rs), c=C('C1', c1)), load=Load('c1', c=C('C2', 'inf'),
                                                                               rl=R('R5', rl)))
    return circ, [Stage(q1, 'CB')]


def ce_cc(c1='1u', c2='10u', rl='1k', bypass='inf'):
    q1, q2 = Q('Q1', 'npn', base='b1'), Q('Q2', 'npn', base='c1')
    cols = [div('R1', '9.4k', 'b1', 'R2', '2k', 12, 0),
            Col([R('R3', '4.7k'), 'c1', q1, 'e1', Par(R('R4', '1k'), C('C3', bypass))], top=12, bottom=0),
            Col([q2, 'e2', R('R7', '2.2k')], top=12, bottom=0)]
    circ = BJTCircuit(cols, src=Src('b1', c=C('C1', c1)), load=Load('e2', c=C('C2', c2), rl=R('R5', rl)))
    return circ, [Stage(q1, 'CE'), Stage(q2, 'CC')]


def cc_ce(c1='1u', c3='22u', rl='4.7k'):
    q1, q2 = Q('Q1', 'npn', base='b1'), Q('Q2', 'npn', base='e1')
    cols = [div('R1', '4k', 'b1', 'R2', '2k', 6, -6),
            Col([q1, 'e1', R('R3', '3.3k')], top=6, bottom=-6),
            Col([R('R4', '1k'), 'c2', q2, 'e2', Par(R('R7', '1.5k'), C('C3', c3))], top=6, bottom=-6)]
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R6', '1k'), c=C('C1', c1)),
                      load=Load('c2', c=C('C2', 'inf'), rl=R('R5', rl)))
    return circ, [Stage(q1, 'CC'), Stage(q2, 'CE')]


def ce_ce(cc='1u', c1='inf', rl='10k'):
    q1, q2 = Q('Q1', 'npn', base='b1'), Q('Q2', 'npn', base='b2')
    cols = [div('R1', '30k', 'b1', 'R2', '10k', 12, 0),
            Col([R('R3', '5.6k'), 'c1', q1, 'e1', Par(R('R4', '2.3k'), C('C3', 'inf'))], top=12, bottom=0),
            div('R7', '30k', 'b2', 'R8', '10k', 12, 0),
            Col([R('R9', '3.3k'), 'c2', q2, 'e2', Ser(R('R10', '100'), Par(R('R11', '2.2k'), C('C4', 'inf')))],
                top=12, bottom=0)]
    circ = BJTCircuit(cols, src=Src('b1', c=C('C1', c1)), load=Load('c2', c=C('C2', 'inf'), rl=R('R5', rl)),
                      links=[(C('C5', cc), 'c1', 'b2')])
    return circ, [Stage(q1, 'CE'), Stage(q2, 'CE')]


def sp8_like(c2='10n', rl='100', r4='1.5k'):
    q1, q2, q3 = Q('Q1', 'npn', base='vi'), Q('Q2', 'pnp', base='b2'), Q('Q3', 'pnp', base='c2')
    cols = [div('R2', '6k', 'b2', 'R3', '4k', 0, -5),
            Col([q1, 'e1', Par(R('R1', '2k'), C('C1', 'inf')), 'e2', q2, 'c2', Par(R('R4', r4), C('C2', c2))],
                top=0, bottom=-5),
            Col([R('R5', '1k'), 'e3', q3], top=0, bottom=-5)]
    circ = BJTCircuit(cols, src=Src('vi'), load=Load('e3', c=C('C3', 'inf'), rl=R('R6', rl)))
    return circ, [Stage(q1, 'CC'), Stage(q2, 'CB'), Stage(q3, 'CC')]


def ce_cb(c3='1u', rl='2k'):
    """CE whose collector feeds the emitter of a CB stage (folded, like Sample Problem 7)."""
    q1 = Q('Q1', 'pnp', base='b1')
    q2 = Q('Q2', 'npn', base='b2', face='right')
    cols = [div('R1', '1k', 'b1', 'R2', '3k', 5, -5),
            Col([Par(R('R3', '2k'), C('C2', 'inf')), 'e1', q1, 'x'], top=5, bottom=None),
            Col([R('R5', '1k'), 'c2', q2, 'x', Par(R('R4', '1k'), C('C3', c3))], top=5, bottom=-5),
            Col([Par(R('R7', '2k'), C('C4', 'inf')), 'b2', R('R6', '8k')], top=0, bottom=-5, gap=3.4)]
    circ = BJTCircuit(cols, src=Src('b1', c=C('C1', '1u')), load=Load('c2', c=C('C5', 'inf'), rl=R('R8', rl)))
    return circ, [Stage(q1, 'CE'), Stage(q2, 'CB')]


def ce_ce_cc(cc='1u', cl='2n'):
    q1, q2, q3 = Q('Q1', 'npn', base='b1'), Q('Q2', 'npn', base='b2'), Q('Q3', 'npn', base='c2')
    cols = [div('R1', '30k', 'b1', 'R2', '10k', 12, 0),
            Col([R('R3', '5.6k'), 'c1', q1, 'e1', Ser(R('R4', '200'), Par(R('R5', '2.1k'), C('C3', 'inf')))],
                top=12, bottom=0),
            div('R6', '30k', 'b2', 'R7', '10k', 12, 0),
            Col([R('R8', '4.7k'), 'c2', q2, 'e2', Par(R('R9', '2.3k'), C('C4', 'inf'))], top=12, bottom=0),
            Col([q3, 'e3', R('R10', '2.2k')], top=12, bottom=0)]
    if cl:
        cols.insert(4, Col([C('C6', cl)], top_node='c2', bottom=0, gap=3.0))
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R12', '600'), c=C('C1', 'inf')),
                      load=Load('e3', c=C('C2', '10u'), rl=R('R11', '1k')),
                      links=[(C('C5', cc), 'c1', 'b2')])
    return circ, [Stage(q1, 'CE'), Stage(q2, 'CE'), Stage(q3, 'CC')]


def cc_ce_cc():
    q1, q2, q3 = Q('Q1', 'npn', base='b1'), Q('Q2', 'npn', base='e1'), Q('Q3', 'npn', base='c2')
    cols = [div('R1', '4k', 'b1', 'R2', '2k', 6, -6),
            Col([q1, 'e1', R('R3', '3.3k')], top=6, bottom=-6),
            Col([R('R4', '2k'), 'c2', q2, 'e2', Ser(R('R5', '100'), Par(R('R6', '1.4k'), C('C3', '47u')))],
                top=6, bottom=-6),
            Col([q3, 'e3', R('R7', '2.2k')], top=6, bottom=-6)]
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R9', '5k'), c=C('C1', '1u')),
                      load=Load('e3', c=C('C2', 'inf'), rl=R('R8', '500')))
    return circ, [Stage(q1, 'CC'), Stage(q2, 'CE'), Stage(q3, 'CC')]


def pnp_ce_cc():
    q1, q2 = Q('Q1', 'pnp', base='b1'), Q('Q2', 'npn', base='c1')
    cols = [div('R1', '2k', 'b1', 'R2', '4k', 9, 0),
            Col([Par(R('R3', '2.3k'), C('C3', '4.7u')), 'e1', q1, 'c1', R('R4', '3k')], top=9, bottom=0),
            Col([q2, 'e2', R('R7', '1.2k')], top=9, bottom=0)]
    circ = BJTCircuit(cols, src=Src('b1', rs=R('R6', '300'), c=C('C1', '10u')),
                      load=Load('e2', c=C('C2', 'inf'), rl=R('R5', '1k')))
    return circ, [Stage(q1, 'CE'), Stage(q2, 'CC')]


P = ACProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', lambda: ce1(Par(R('R4', '2.3k'), C('C3', 'inf')), c1='1u'), Sine(0.005, 1000)),
    P('easy', lambda: ce1(R('R4', '2.3k'), c1='470n'), Sine(0.05, 2000)),
    P('easy', lambda: cc1(), Sine(0.5, 1000)),
    P('easy', lambda: cb1(), Sine(0.01, 1000)),
    P('easy', lambda: ce1(Par(R('R4', '2.3k'), C('C3', 'inf')), c1='inf', cl='10n'), Sine(0.002, 5000)),
    P('easy', lambda: ce1(Par(R('R4', '2.3k'), C('C3', '22u')), c1='inf', rs='500'), Sine(0.005, 300)),
    # ---------------- medium ----------------
    P('medium', lambda: ce1(Ser(R('R4', '300'), Par(R('R7', '2k'), C('C3', '10u'))), c1='inf', cl='4.7n'),
      Sine(0.01, 2000)),
    P('medium', lambda: ce_cc(), Sine(0.002, 1000)),
    P('medium', lambda: cc_ce(), Sine(0.005, 500)),
    P('medium', lambda: ce_ce(), Sine(0.0005, 1000)),
    P('medium', lambda: cb1(c1='4.7u', rl='2k', rs='200'), Sine(0.02, 200)),
    P('medium', lambda: sp8_like(), Sine(0.02, 10000)),
    # ---------------- hard ----------------
    P('hard', lambda: ce_cb(), Sine(0.005, 2000)),
    P('hard', lambda: sp8_like(c2='4.7n', rl='200', r4='1.2k'), Sine(0.05, 20000, phase_pi='1/4')),
    P('hard', lambda: ce_ce_cc(), Sine(0.0005, 2000)),
    P('hard', lambda: pnp_ce_cc(), Sine(0.01, 500)),
    P('hard', lambda: ce_cc(c1='470n', c2='4.7u', rl='500', bypass='10u'), Sine(0.002, 200, phase_pi='-1/3', fn='cos')),
    P('hard', lambda: cc_ce_cc(), Sine(0.01, 1000)),
]
