"""Set 4B: DC analysis of BJT circuits biased with current mirrors (like Sample Problems 4-5).
Easy: one mirror (npn or pnp), one or two outputs. Medium: npn + pnp mirrors from one reference, mirror-biased
stages. Hard: several stages, two references, sources and sinks."""
from .bjtnet import R, Q, Col, BJTCircuit
from .parts import div

CODE = '4B'
SLUG = 'current_mirrors'
TITLE = 'Set 4B: BJT Biasing with Current Mirrors'
INTRO = r"""
\textbf{What this set trains.} DC analysis when the bias currents come from current mirrors. The reference current is
set by a resistor and diode-connected transistor(s); every transistor that shares the base and emitter nodes of a
diode-connected transistor copies its current. Then continue node by node as in set 4A and verify the assumptions.
$\beta = 100$ throughout. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking at its
solution.
"""


class DCProb:
    def __init__(self, level, build, note=''):
        self.level, self.build, self.note = level, build, note


B = BJTCircuit


def nref(rname, rval, node, qname, top, bot):
    """npn reference: top rail -R- node = collector = base of a diode-connected npn, emitter at the bottom rail."""
    return Col([R(rname, rval), node, Q(qname, 'npn', diode=True)], top=top, bottom=bot, gap=4.6)


def pref(rname, rval, node, qname, top, bot):
    """pnp reference: diode-connected pnp at the top rail, then -R- to the bottom rail."""
    return Col([Q(qname, 'pnp', diode=True), node, R(rname, rval)], top=top, bottom=bot, gap=4.6)


P = DCProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', lambda: B([nref('R1', '4.65k', 'm', 'Q1', 5, -5),
                         Col([R('R2', '2k'), 'c2', Q('Q2', 'npn', base='m')], top=5, bottom=-5)])),
    P('easy', lambda: B([pref('R1', '8.3k', 'm', 'Q1', 9, 0),
                         Col([Q('Q2', 'pnp', base='m'), 'c2', R('R2', '4.7k')], top=9, bottom=0)])),
    P('easy', lambda: B([nref('R1', '5.65k', 'm', 'Q1', 12, 0),
                         Col([R('R2', '3.3k'), 'c2', Q('Q2', 'npn', base='m')], top=12, bottom=0),
                         Col([R('R3', '4.7k'), 'c3', Q('Q3', 'npn', base='m')], top=12, bottom=0)])),
    P('easy', lambda: B([nref('R1', '8.3k', 'm', 'Q1', 0, -9),
                         Col([R('R2', '5.6k'), 'c2', Q('Q2', 'npn', base='m')], top=0, bottom=-9)])),
    P('easy', lambda: B([pref('R1', '4.3k', 'm', 'Q1', 5, -5),
                         Col([Q('Q2', 'pnp', base='m'), 'c2', R('R2', '1.5k')], top=5, bottom=-5)])),
    P('easy', lambda: B([nref('R1', '2.15k', 'm', 'Q1', 5, 0),
                         Col([R('R2', '2.2k'), 'c2', Q('Q2', 'npn', base='m')], top=5, bottom=0)])),
    # ---------------- medium ----------------
    P('medium', lambda: B([Col([Q('Q3', 'pnp', base='mp', face='right'), 'c3', R('R1', '1k')], top=3, bottom=-3),
                           Col([Q('Q1', 'pnp', diode=True), 'mp', R('R3', '2.3k'), 'mn', Q('Q2', 'npn', diode=True)],
                               top=3, bottom=-3, gap=4.6),
                           Col([R('R2', '1k'), 'c4', Q('Q4', 'npn', base='mn')], top=3, bottom=-3)])),
    P('medium', lambda: B([nref('R1', '4.3k', 'm', 'Q1', 5, -5),
                           Col([R('R2', '2k'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='m')],
                               top=5, bottom=-5)])),
    P('medium', lambda: B([div('R2', '10k', 'b2', 'R3', '10k', 5, -5),
                           Col([Q('Q2', 'npn', base='b2'), 'e2', Q('Q3', 'npn', base='m', face='right')],
                               top=5, bottom=-5),
                           nref('R1', '9.3k', 'm', 'Q1', 5, -5)])),
    P('medium', lambda: B([pref('R1', '5.65k', 'm', 'Q1', 6, -6),
                           Col([Q('Q2', 'pnp', base='m'), 'e3', Q('Q3', 'pnp', base='0'), 'c3', R('R2', '2.2k')],
                               top=6, bottom=-6)])),
    P('medium', lambda: B([nref('R1', '4.3k', 'm', 'Q1', 5, -5),
                           Col([R('R2', '1.5k'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='m')],
                               top=5, bottom=-5),
                           Col([R('R3', '1k'), 'e4', Q('Q4', 'pnp', base='c2')], top=5, bottom=-5)])),
    P('medium', lambda: B([Col([Q('Q3', 'pnp', base='mp', face='right'), 'c3', R('R1', '2k')], top=5, bottom=-5),
                           Col([Q('Q1', 'pnp', diode=True), 'mp', R('R3', '4.3k'), 'mn', Q('Q2', 'npn', diode=True)],
                               top=5, bottom=-5, gap=4.6),
                           Col([R('R2', '2k'), 'c4', Q('Q4', 'npn', base='mn')], top=5, bottom=-5),
                           Col([R('R4', '1k'), 'c5', Q('Q5', 'npn', base='mn')], top=5, bottom=-5)])),
    # ---------------- hard ----------------
    P('hard', lambda: B([nref('R1', '2.3k', 'mn', 'Q5', 3, -3),
                         Col([R('R2', '1k'), 'c1', Q('Q1', 'npn', base='0'), 'e1', Q('Q6', 'npn', base='mn')],
                             top=3, bottom=-3),
                         Col([Q('Q3', 'pnp', base='mp', face='right'), 'e2', Q('Q2', 'pnp', base='c1'), 'c2',
                              R('R3', '1k')], top=3, bottom=-3),
                         pref('R4', '2.3k', 'mp', 'Q4', 3, -3)])),
    P('hard', lambda: B([nref('R1', '4.3k', 'mn', 'Q1', 5, -5),
                         Col([R('R2', '1.5k'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='mn')],
                             top=5, bottom=-5),
                         Col([Q('Q4', 'npn', base='c2'), 'e4', Q('Q5', 'npn', base='mn')], top=5, bottom=-5)])),
    P('hard', lambda: B([pref('R1', '5.3k', 'mp', 'Q1', 6, -6),
                         Col([Q('Q2', 'pnp', base='mp'), 'e3', Q('Q3', 'pnp', base='0'), 'c3', R('R2', '1.8k')],
                             top=6, bottom=-6),
                         Col([R('R3', '1k'), 'c4', Q('Q4', 'npn', base='c3'), 'e4', R('R4', '1.2k')], top=6, bottom=-6)])),
    P('hard', lambda: B([nref('R1', '4.3k', 'mn', 'Q1', 5, -5),
                         Col([R('R2', '2k'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='mn')],
                             top=5, bottom=-5),
                         Col([Q('Q4', 'pnp', base='mp', face='right'), 'e5', Q('Q5', 'pnp', base='c2'), 'c5',
                              R('R3', '2.2k')], top=5, bottom=-5),
                         pref('R4', '8.6k', 'mp', 'Q6', 5, -5)])),
    P('hard', lambda: B([Col([Q('Q3', 'pnp', base='mp', face='right'), 'c3', R('R1', '3.3k')], top=9, bottom=-9),
                         Col([Q('Q1', 'pnp', diode=True), 'mp', R('R3', '8.2k'), 'mn', Q('Q2', 'npn', diode=True)],
                             top=9, bottom=-9, gap=4.6),
                         Col([R('R2', '2.2k'), 'c4', Q('Q5', 'npn', base='0'), 'e5', Q('Q4', 'npn', base='mn')],
                             top=9, bottom=-9),
                         Col([R('R4', '1k'), 'e6', Q('Q6', 'pnp', base='c4')], top=9, bottom=-9)])),
    P('hard', lambda: B([nref('R1', '4.3k', 'mn', 'Q1', 5, -5),
                         Col([R('R2', '1k'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='mn')],
                             top=5, bottom=-5),
                         Col([Q('Q4', 'npn', base='c2'), 'e4', Q('Q5', 'npn', base='mn')], top=5, bottom=-5),
                         Col([R('R3', '1k'), 'e6', Q('Q6', 'pnp', base='e4')], top=5, bottom=-5)])),
]
