"""Set 5F: MOSFET problems that call for a Thevenin equivalent (DC bias and small-signal).
A resistor (or R-C) network hangs on a transistor terminal; node-by-node KCL would need every node of it together
with the quadratic square law, while its Thevenin pair seen from the terminal reduces the problem to one loop.
Easy: one network on one terminal. Medium: two networks or two-level ladders. Hard: networks on several terminals,
two transistors, R-C networks with several corners."""
from lecture1.narrative import Sine
from .mosnet import M, R, C
from .thev5 import Ladder as L, Node as Nd, Sh as S, Ser as Se
from .narrative_thev5 import TDev as D, TProb

CODE = '5F'
SLUG = 'thevenin'
TITLE = 'Set 5F: MOSFET Circuits Solved with Thevenin Equivalents'
INTRO = r"""
\textbf{What this set trains.} Recognising when a Thevenin equivalent turns a long KCL computation into a short one.
In every circuit a resistor (or R-C) network hangs on a transistor terminal. Writing KCL at every node of it would
couple all those node voltages with the quadratic square law (DC) or with each other in $s$ (AC). But the transistor
touches each network at a single terminal and draws no gate current, so each network can be replaced by its Thevenin
pair $(V_{th}, R_{th})$ --- computed from the far end with dividers and Millman's rule, transistor removed --- and the
transistor then sits in one simple loop. Problems 1--6 are easy, 7--12 medium, 13--18 hard (DC and AC mixed). Try
each problem before looking at its solution.
"""

SL = (1.1e-3, 1.4, 0.85e-3, 1.3)


def n(name):
    return M(name, 'nmos', kw=SL[0], vt=SL[1])


def p(name):
    return M(name, 'pmos', kw=SL[2], vt=SL[3])


def gdiv(term, r1, v1, r2, v2):
    return L(term, [Nd(term, [S(R(r1[0], r1[1]), v1), S(R(r2[0], r2[1]), v2)])])


def one(term, rname, rv, rail):
    return L(term, [Nd(term, [S(R(rname, rv), rail)])])


P = TProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [D(n('M1'), gdiv('g1', ('R1', '400k'), 5, ('R2', '600k'), -5),
                 L('s1', [Se(R('R4', '1k')), Nd('x1', [S(R('R5', '3k'), -5), S(R('R6', '6k'), 0)])]),
                 one('d1', 'R3', '5k', 5))]),
    P('easy', [D(p('M1'), gdiv('g1', ('R1', '500k'), 5, ('R2', '500k'), -5),
                 L('s1', [Se(R('R3', '2k')), Nd('x1', [S(R('R4', '2k'), 5), S(R('R5', '8k'), 0)])]),
                 one('d1', 'R6', '6k', -5))]),
    P('easy', [D(n('M1'), L('g1', [Nd('g1', [S(R('R3', '200k'), 0)]), Se(R('R4', '100k')),
                                   Nd('x1', [S(R('R1', '100k'), 12), S(R('R2', '100k'), 0)])]),
                 one('s1', 'R5', '2k', 0), one('d1', 'R6', '4k', 12))]),
    P('easy', [D(n('M1'), 0,
                 L('s1', [Nd('s1', [S(R('R2', '8k'), -6)]), Se(R('R3', '2k')), Nd('x1', [S(R('R4', '6k'), 6),
                                                                                       S(R('R5', '3k'), -6)])]),
                 one('d1', 'R1', '3k', 6))]),
    P('easy', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 10), S(R('R2', '400k'), 0), S(C('C3', 'inf'), 0)])]),
                 L('s1', [Nd('s1', [S(R('R4', '4k'), 0)]), Se(C('C1', 'inf')),
                          Nd('x1', [S(R('R5', '1k'), 0), S(R('R6', '1k'), 'vi')])]),
                 one('d1', 'R3', '8k', 10))],
      ac=dict(stages=[('M1', 'CG')], load=('d1', C('C2', '1u'), R('R7', '10k'))), vin=Sine(10e-3, 1e3)),
    P('easy', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 10), S(R('R2', '400k'), 0)]), Se(C('C1', '10n')),
                                   Nd('x1', [S(R('R3', '10k'), 0), S(R('R4', '10k'), 'vi')])]),
                 L('s1', [Nd('s1', [S(R('R5', '2k'), 0), S(C('C2', 'inf'), 0)])]),
                 one('d1', 'R6', '4k', 10))],
      ac=dict(stages=[('M1', 'CS')], load=('d1', C('C3', 'inf'), R('R7', '10k'))), vin=Sine(20e-3, 20)),
    # ---------------- medium ----------------
    P('medium', [D(n('M1'), L('g1', [Nd('g1', [S(R('R3', '300k'), 0)]), Se(R('R4', '150k')),
                                     Nd('x1', [S(R('R1', '100k'), 10), S(R('R2', '200k'), 0)])]),
                   L('s1', [Se(R('R6', '1k')), Nd('x2', [S(R('R7', '2k'), 0), S(R('R8', '18k'), 10)])]),
                   one('d1', 'R5', '6k', 10))]),
    P('medium', [D(p('M1'), gdiv('g1', ('R1', '500k'), 5, ('R2', '500k'), -5),
                   L('s1', [Se(R('R3', '1k')), Nd('x1', [S(R('R4', '2k'), 5), S(R('R5', '6k'), 0)])]),
                   L('d1', [Se(R('R6', '2k')), Nd('x2', [S(R('R7', '6k'), -5), S(R('R8', '6k'), 0)])]))]),
    P('medium', [D(n('M1'), gdiv('g1', ('R1', '300k'), 6, ('R2', '700k'), -6),
                   L('s1', [Nd('s1', [S(R('R3', '10k'), -6)]), Se(R('R4', '2k')),
                            Nd('x1', [S(R('R5', '4k'), 0)]), Se(R('R6', '1k')),
                            Nd('x2', [S(R('R7', '3k'), -6), S(R('R8', '6k'), 6)])]),
                   one('d1', 'R9', '4k', 6))]),
    P('medium', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 5), S(R('R2', '400k'), -5), S(C('C3', 'inf'), 0)])]),
                   L('s1', [Nd('s1', [S(R('R4', '5k'), -5)]), Se(C('C1', 'inf')), Nd('x1', [S(R('R5', '2k'), 0)]),
                            Se(R('R6', '500')), Nd('x2', [S(R('R7', '1k'), 0), S(R('R8', '1k'), 'vi')])]),
                   one('d1', 'R3', '10k', 5))],
      ac=dict(stages=[('M1', 'CG')], load=('d1', C('C2', '1u'), R('R9', '10k'))), vin=Sine(10e-3, 1e3)),
    P('medium', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '500k'), 5), S(R('R2', '500k'), -5)]), Se(C('C1', 'inf')),
                                     Nd('x0', [S(R('R9', '50k'), 'vi'), S(R('R10', '200k'), 0)])]),
                   L('s1', [Se(R('R4', '500')), Nd('x1', [S(R('R5', '3k'), -5), S(R('R6', '6k'), 0),
                                                         S(C('C2', '10u'), 0)])]),
                   one('d1', 'R3', '8k', 5))],
      ac=dict(stages=[('M1', 'CS')], load=('d1', C('C3', 'inf'), R('R7', '8k'))), vin=Sine(10e-3, 100)),
    P('medium', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '500k'), 12), S(R('R2', '500k'), 0)]), Se(C('C1', '47n')),
                                     Nd('x1', [S(R('R3', '20k'), 0)]), Se(R('R4', '10k')),
                                     Nd('x2', [S(R('R5', '20k'), 0), S(R('R6', '20k'), 'vi')])]),
                   one('s1', 'R7', '2.2k', 0), 12)],
      ac=dict(stages=[('M1', 'CD')], load=('s1', C('C2', 'inf'), R('R8', '1k'))), vin=Sine(0.5, 50)),
    # ---------------- hard ----------------
    P('hard', [D(n('M1'), gdiv('g1', ('R1', '400k'), 5, ('R2', '600k'), -5),
                 L('s1', [Se(R('R3', '1k')), Nd('x1', [S(R('R4', '4k'), -5), S(R('R5', '4k'), 0)])]),
                 L('d1', [Nd('d1', [S(R('R6', '10k'), 5)]), Se(R('R7', '10k')), Nd('x2', [S(R('R8', '20k'), 0)])])),
               D(p('M2'), 'd1',
                 L('s2', [Se(R('R9', '1k')), Nd('x3', [S(R('R10', '1k'), 5), S(R('R11', '9k'), 0)])]),
                 one('d2', 'R12', '4k', -5))]),
    P('hard', [D(n('M1'), L('g1', [Nd('g1', [S(R('R3', '400k'), 0)]), Se(R('R4', '200k')),
                                   Nd('x1', [S(R('R1', '200k'), 6), S(R('R2', '400k'), -6)])]),
                 L('s1', [Se(R('R5', '1k')), Nd('x2', [S(R('R6', '6k'), -6), S(R('R7', '3k'), 0)]), Se(R('R8', '2k')),
                          Nd('x3', [S(R('R9', '4k'), -6)])]),
                 L('d1', [Se(R('R10', '2k')), Nd('x4', [S(R('R11', '2k'), 6), S(R('R12', '8k'), -6)])]))]),
    P('hard', [D(p('M1'), gdiv('g1', ('R1', '350k'), 6, ('R2', '650k'), -6),
                 L('s1', [Se(R('R3', '1k')), Nd('x1', [S(R('R4', '2k'), 6), S(R('R5', '6k'), 0)])]),
                 L('d1', [Nd('d1', [S(R('R6', '20k'), -6)]), Se(R('R7', '5k')), Nd('x2', [S(R('R8', '5k'), 0)])])),
               D(n('M2'), 'd1',
                 L('s2', [Se(R('R9', '2k')), Nd('x3', [S(R('R10', '3k'), -6), S(R('R11', '6k'), 0)])]),
                 one('d2', 'R12', '3k', 6))]),
    P('hard', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 10), S(R('R2', '400k'), 0)]), Se(C('C1', '22n')),
                                   Nd('x1', [S(R('R3', '20k'), 0), S(C('C4', '1n'), 0)]), Se(R('R4', '10k')),
                                   Nd('x2', [S(R('R5', '1k'), 'vi'), S(R('R10', '4k'), 0)])]),
                 L('s1', [Se(R('R8', '500')), Nd('x3', [S(R('R9', '1.5k'), 0), S(C('C2', '22u'), 0)])]),
                 one('d1', 'R6', '6k', 10))],
      ac=dict(stages=[('M1', 'CS')], load=('d1', C('C3', 'inf'), R('R7', '12k'))), vin=Sine(10e-3, 1e3)),
    P('hard', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 10), S(R('R2', '400k'), 0), S(C('C4', 'inf'), 0)])]),
                 L('s1', [Nd('s1', [S(R('R4', '4k'), 0)]), Se(C('C1', '4.7u')), Nd('x1', [S(R('R5', '1k'), 0)]),
                          Se(R('R6', '1k')), Nd('x2', [S(R('R7', '1k'), 0), S(C('C5', '100n'), 0),
                                                       S(R('R8', '1k'), 'vi')])]),
                 one('d1', 'R3', '8k', 10))],
      ac=dict(stages=[('M1', 'CG')], load=('d1', C('C2', 'inf'), R('R9', '10k'))), vin=Sine(10e-3, 500)),
    P('hard', [D(n('M1'), L('g1', [Nd('g1', [S(R('R1', '600k'), 10), S(R('R2', '400k'), 0)]), Se(C('C1', '100n')),
                                   Nd('x1', [S(R('R3', '10k'), 0)]), Se(R('R4', '10k')),
                                   Nd('x2', [S(R('R5', '10k'), 0), S(R('R6', '10k'), 'vi')])]),
                 L('s1', [Nd('s1', [S(R('R7', '2k'), 0), S(C('C2', 'inf'), 0)])]),
                 one('d1', 'R8', '5k', 10)),
               D(n('M2'), 'd1', one('s2', 'R9', '3k', 0), 10)],
      ac=dict(stages=[('M1', 'CS'), ('M2', 'CD')], load=('s2', C('C3', '10u'), R('R10', '500'))),
      vin=Sine(10e-3, 100)),
]
