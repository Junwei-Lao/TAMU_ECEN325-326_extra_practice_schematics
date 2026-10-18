"""Set 4A: DC bias analysis of BJT circuits with resistive biasing (like Sample Problems 1-2).
Easy: one transistor (npn/pnp, divider or grounded base, follower). Medium: two or three direct-coupled
transistors. Hard: three or four transistors, mixed npn/pnp."""
from .bjtnet import R, Q, Col, BJTCircuit
from .parts import div, ce_npn, ce_pnp

CODE = '4A'
SLUG = 'dc_bias'
TITLE = 'Set 4A: BJT DC Bias Analysis'
INTRO = r"""
\textbf{What this set trains.} Finding the DC collector currents of BJT circuits and checking that every transistor
is really active. Assume every transistor active with negligible base current, walk through the circuit node by node
(dividers, $V_{BE}$, KCL), then verify the assumptions. $\beta = 100$ throughout. Problems 1--6 are easy, 7--12
medium, 13--18 hard. Try each problem before looking at its solution.
"""


class DCProb:
    def __init__(self, level, build, note=''):
        self.level, self.build, self.note = level, build, note


def sp2_col():
    return Col([Q('Q1', 'npn', base='0'), 'e1', R('R1', '2k'), 'e2', Q('Q2', 'pnp', base='b2'), 'c2',
                R('R4', '1.5k')], top=0, bottom=-5)


P = DCProb
B = BJTCircuit
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', lambda: B([div('R1', '6k', 'b1', 'R2', '2k', 12, 0),
                         ce_npn('Q1', 'b1', 'R3', '2.2k', 'R4', '1k', 12, 0, c='c1', e='e1')])),
    P('easy', lambda: B([div('R1', '10k', 'b1', 'R2', '10k', 5, -5),
                         ce_npn('Q1', 'b1', 'R3', '1k', 'R4', '2.15k', 5, -5, c='c1', e='e1')])),
    P('easy', lambda: B([div('R1', '4k', 'b1', 'R2', '6k', 10, 0),
                         ce_pnp('Q1', 'b1', 'R3', '1.1k', 'R4', '1k', 10, 0, c='c1', e='e1')])),
    P('easy', lambda: B([div('R1', '15k', 'b1', 'R2', '15k', 5, -5),
                         ce_pnp('Q1', 'b1', 'R3', '2.15k', 'R4', '1.5k', 5, -5, c='c1', e='e1')])),
    P('easy', lambda: B([ce_npn('Q1', '0', 'R1', '4.7k', 'R2', '4.3k', 5, -5, c='c1', e='e1')])),
    P('easy', lambda: B([div('R1', '4k', 'b1', 'R2', '4k', 10, 0),
                         ce_npn('Q1', 'b1', None, None, 'R3', '2.15k', 10, 0, e='e1')])),
    # ---------------- medium ----------------
    P('medium', lambda: B([div('R1', '8k', 'b1', 'R2', '2k', 10, 0),
                           ce_npn('Q1', 'b1', 'R3', '1.65k', 'R4', '650', 10, 0, c='c1', e='e1'),
                           ce_pnp('Q2', 'c1', 'R5', '1.3k', 'R6', '2k', 10, 0, c='c2', e='e2')])),
    P('medium', lambda: B([div('R1', '9.4k', 'b1', 'R2', '2k', 12, 0),
                           ce_npn('Q1', 'b1', 'R3', '4.7k', 'R4', '1k', 12, 0, c='c1', e='e1'),
                           ce_npn('Q2', 'c1', None, None, 'R5', '2.2k', 12, 0, e='e2')])),
    P('medium', lambda: B([div('R2', '6k', 'b2', 'R3', '4k', 0, -5), sp2_col(),
                           ce_pnp('Q3', 'c2', 'R5', '1k', None, None, 0, -5, e='e3')])),
    P('medium', lambda: B([div('R1', '2k', 'b1', 'R2', '4k', 9, 0),
                           ce_pnp('Q1', 'b1', 'R3', '2.3k', 'R4', '3k', 9, 0, c='c1', e='e1'),
                           ce_npn('Q2', 'c1', 'R5', '2k', 'R6', '1.15k', 9, 0, c='c2', e='e2')])),
    P('medium', lambda: B([div('R1', '4k', 'b1', 'R2', '2k', 6, -6),
                           ce_npn('Q1', 'b1', None, None, 'R3', '3.3k', 6, -6, e='e1'),
                           ce_npn('Q2', 'e1', 'R4', '1k', 'R5', '1.5k', 6, -6, c='c2', e='e2')])),
    P('medium', lambda: B([div('R1', '2k', 'b1', 'R2', '6k', 5, -5),
                           ce_npn('Q1', 'b1', 'R3', '1k', 'R4', '2.4k', 5, -5, c='c1', e='e1'),
                           ce_pnp('Q2', 'c1', 'R5', '470', None, None, 5, -5, e='e2')])),
    # ---------------- hard ----------------
    P('hard', lambda: B([div('R1', '8k', 'b1', 'R2', '2k', 10, 0),
                         ce_npn('Q1', 'b1', 'R3', '1.65k', 'R4', '650', 10, 0, c='c1', e='e1'),
                         ce_pnp('Q2', 'c1', 'R5', '1.3k', 'R6', '2k', 10, 0, c='c2', e='e2'),
                         ce_npn('Q3', 'c2', None, None, 'R7', '1k', 10, 0, e='e3')])),
    P('hard', lambda: B([div('R1', '1k', 'b1', 'R2', '3k', 5, -5),
                         ce_pnp('Q1', 'b1', 'R3', '2k', 'R4', '3k', 5, -5, c='c1', e='e1'),
                         ce_npn('Q2', 'c1', 'R5', '3k', 'R6', '2k', 5, -5, c='c2', e='e2'),
                         ce_pnp('Q3', 'c2', 'R7', '1.8k', 'R8', '2.2k', 5, -5, c='c3', e='e3'),
                         ce_npn('Q4', 'c3', None, None, 'R9', '1k', 5, -5, e='e4')])),
    P('hard', lambda: B([div('R1', '6k', 'b1', 'R2', '2k', 12, -12),
                         ce_npn('Q1', 'b1', None, None, 'R3', '6.8k', 12, -12, e='e1'),
                         ce_npn('Q2', 'e1', 'R4', '5.6k', 'R5', '3.3k', 12, -12, c='c2', e='e2'),
                         ce_pnp('Q3', 'c2', 'R6', '1k', 'R7', '2.2k', 12, -12, c='c3', e='e3')])),
    P('hard', lambda: B([div('R2', '6k', 'b2', 'R3', '4k', 0, -5), sp2_col(),
                         ce_pnp('Q3', 'c2', 'R5', '1k', 'R6', '470', 0, -5, c='c3', e='e3'),
                         ce_npn('Q4', 'c3', None, None, 'R7', '1k', 0, -5, e='e4')])),
    P('hard', lambda: B([div('R1', '2k', 'b1', 'R2', '5.4k', 9, -9),
                         ce_pnp('Q1', 'b1', 'R3', '3.9k', 'R4', '4.7k', 9, -9, c='c1', e='e1'),
                         ce_npn('Q2', 'c1', 'R5', '2.2k', 'R6', '1.8k', 9, -9, c='c2', e='e2'),
                         ce_npn('Q3', 'c2', None, None, 'R7', '1.5k', 9, -9, e='e3')])),
    P('hard', lambda: B([div('R1', '4k', 'b1', 'R2', '2k', 6, -6),
                         ce_npn('Q1', 'b1', None, None, 'R3', '2.2k', 6, -6, e='e1'),
                         ce_npn('Q2', 'e1', 'R4', '2k', 'R5', '1k', 6, -6, c='c2', e='e2'),
                         ce_pnp('Q3', 'c2', 'R6', '1.5k', 'R7', '1.2k', 6, -6, c='c3', e='e3'),
                         ce_npn('Q4', 'c3', None, None, 'R8', '1.5k', 6, -6, e='e4')])),
]
