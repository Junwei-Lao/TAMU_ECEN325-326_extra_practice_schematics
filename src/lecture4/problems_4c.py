"""Set 4C: DC bias design --- find the resistors for given currents and voltages (like Sample Problems 3 and 6).
Easy: one transistor. Medium: two or three direct-coupled transistors or a mirror-fed stage.
Hard: three to five transistors, mirrors, supply-current budget."""
from .bjtnet import R, Q, Col, BJTCircuit
from .design import DCDesign, vre, idiv, Choice
from .dc import I_

CODE = '4C'
SLUG = 'bias_design'
TITLE = 'Set 4C: BJT DC Bias Design'
FIG_H = '6cm'
INTRO = r"""
\textbf{What this set trains.} Designing a bias network: choose every resistor so that the transistors carry the
specified collector currents and the specified node voltages appear, while the design stays insensitive to $\beta$
($I_B$ negligible) and to $V_{BE}$ ($\pm0.1$\,V changes $I_C$ by less than 10\,\%). The method is the DC analysis of
sets 4A/4B run backwards: fix node voltages and branch currents, then $R=\Delta V/I$ for every resistor. Each solution
ends by checking the finished circuit exactly. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem
before looking at its solution.
"""

m = 1e-3


def rv(v):
    """Resistor factory: blank ('?') drawing values when v is None, designed values otherwise."""
    return lambda n: R(n, repr(float(v[n])) if v else '1k')


def ib(q, ic):
    return f'$I_{{B{q}}} = {I_(ic / 100)}$'


def budget(rname, i, why):
    return Choice('IR', rname, i, why)


def div(r, a, node, b, top, bot, gap=3.2, label=()):
    return Col([r(a), node, r(b)], top=top, bottom=bot, gap=gap, label_nodes=label)


B = BJTCircuit
P = DCDesign


# ---------------------------------------------------------------- easy
def e1(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 12, 0),
              Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=12, bottom=0, label_nodes=('c1',))])


def e2(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 10, 0),
              Col([r('R3'), 'e1', Q('Q1', 'pnp', base='b1'), 'c1', r('R4')], top=10, bottom=0, label_nodes=('c1',))])


def e3(v):
    r = rv(v)
    return B([Col([r('R1'), 'c1', Q('Q1', 'npn', base='0'), 'e1', r('R2')], top=5, bottom=-5, label_nodes=('c1',))])


def e4(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 10, 0),
              Col([Q('Q1', 'npn', base='b1'), 'e1', r('R3')], top=10, bottom=0, label_nodes=('e1',))])


def e5(v):
    r = rv(v)
    return B([Col([r('R1'), 'e1', Q('Q1', 'pnp', base='0'), 'c1', r('R2')], top=5, bottom=-5, label_nodes=('c1',))])


def e6(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 12, -12),
              Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=12, bottom=-12, label_nodes=('c1',))])


# ---------------------------------------------------------------- medium
def m7(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 10, 0),
              Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=10, bottom=0),
              Col([r('R5'), 'e2', Q('Q2', 'pnp', base='c1'), 'c2', r('R6')], top=10, bottom=0, label_nodes=('c2',))])


def m8(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 12, 0),
              Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=12, bottom=0),
              Col([Q('Q2', 'npn', base='c1'), 'e2', r('R5')], top=12, bottom=0, label_nodes=('e2',))])


def m9(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 5, -5),
              Col([r('R3'), 'e1', Q('Q1', 'pnp', base='b1'), 'c1', r('R4')], top=5, bottom=-5),
              Col([r('R5'), 'c2', Q('Q2', 'npn', base='c1'), 'e2', r('R6')], top=5, bottom=-5, label_nodes=('c2',))])


def m10(v):
    r = rv(v)
    return B([Col([r('R1'), 'm', Q('Q1', 'npn', diode=True)], top=10, bottom=0, gap=4.6),
              Col([r('R2'), 'c2', Q('Q2', 'npn', base='m')], top=10, bottom=0),
              Col([r('R3'), 'e3', Q('Q3', 'pnp', base='c2'), 'c3', r('R4')], top=10, bottom=0, label_nodes=('c3',))])


def m11(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 9, 0),
              Col([r('R3'), 'e1', Q('Q1', 'pnp', base='b1'), 'c1', r('R4')], top=9, bottom=0),
              Col([Q('Q2', 'npn', base='c1'), 'e2', r('R5')], top=9, bottom=0, label_nodes=('e2',))])


def m12(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 6, -6),
              Col([Q('Q1', 'npn', base='b1'), 'e1', r('R3')], top=6, bottom=-6),
              Col([r('R4'), 'c2', Q('Q2', 'npn', base='e1'), 'e2', r('R5')], top=6, bottom=-6, label_nodes=('c2',))])


# ---------------------------------------------------------------- hard
def sp3(vcc):
    def f(v):
        r = rv(v)
        return B([div(r, 'R1', 'b1', 'R2', vcc, 0),
                  Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=vcc, bottom=0),
                  Col([r('R5'), 'e2', Q('Q2', 'pnp', base='c1'), 'c2', r('R6')], top=vcc, bottom=0),
                  Col([r('R7'), 'e3', Q('Q3', 'pnp', base='c2')], top=vcc, bottom=0, label_nodes=('e3',))])
    return f


def h15(v):
    r = rv(v)
    return B([div(r, 'R1', 'b1', 'R2', 12, 0),
              Col([r('R3'), 'c1', Q('Q1', 'npn', base='b1'), 'e1', r('R4')], top=12, bottom=0),
              Col([r('R5'), 'e2', Q('Q2', 'pnp', base='c1'), 'c2', r('R6')], top=12, bottom=0),
              Col([r('R7'), 'c3', Q('Q3', 'npn', base='c2'), 'e3', r('R8')], top=12, bottom=0),
              Col([Q('Q4', 'npn', base='c3'), 'e4', r('R9')], top=12, bottom=0, label_nodes=('e4',))])


def h16(v):
    r = rv(v)
    return B([Col([Q('Q1', 'pnp', diode=True), 'mp', r('R1')], top=10, bottom=0, gap=4.6),
              Col([Q('Q2', 'pnp', base='mp'), 'c2', r('R2')], top=10, bottom=0),
              Col([Q('Q3', 'npn', base='c2'), 'e3', r('R3')], top=10, bottom=0),
              Col([r('R4'), 'c4', Q('Q4', 'npn', base='e3'), 'e4', r('R5')], top=10, bottom=0, label_nodes=('c4',))])


def h17(v):
    r = rv(v)
    return B([Col([r('R1'), 'mn', Q('Q1', 'npn', diode=True)], top=5, bottom=-5, gap=4.6),
              Col([r('R2'), 'c2', Q('Q2', 'npn', base='0'), 'e2', Q('Q3', 'npn', base='mn')], top=5, bottom=-5),
              Col([r('R3'), 'e4', Q('Q4', 'pnp', base='c2'), 'c4', r('R4')], top=5, bottom=-5, label_nodes=('c4',))])


def h18(v):
    r = rv(v)
    return B([Col([Q('Q3', 'pnp', base='mp', face='right'), 'c3', r('R2')], top=5, bottom=-5, label_nodes=('c3',)),
              Col([Q('Q1', 'pnp', diode=True), 'mp', r('R1'), 'mn', Q('Q2', 'npn', diode=True)],
                  top=5, bottom=-5, gap=4.6),
              Col([r('R3'), 'c4', Q('Q4', 'npn', base='mn')], top=5, bottom=-5),
              Col([r('R4'), 'e5', Q('Q5', 'pnp', base='c4'), 'c5', r('R5')], top=5, bottom=-5, label_nodes=('c5',))])


SP3_WHY = ('$I_{{dc}} = I_{{R1}} + I_{{C1}} + I_{{C2}} + I_{{C3}} \\le {cap}$ leaves at most ${left}$ for the divider, '
           'and $I_{{R2}}$ must be $\\gg I_{{B1}} = {ib1}$. Choose $I_{{R2}} = {pick}$')

PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', e1, {'Q1': 1 * m}, {'c1': 7.0}, [vre('R4'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')]),
    P('easy', e2, {'Q1': 2 * m}, {'c1': 4.0}, [vre('R3'), idiv('R2', 1 * m, ib(1, 2 * m), '50 times')]),
    P('easy', e3, {'Q1': 1 * m}, {'c1': 2.0}, []),
    P('easy', e4, {'Q1': 5 * m}, {'e1': 5.0}, [idiv('R2', 1 * m, ib(1, 5 * m), '20 times')], vce_min=1),
    P('easy', e5, {'Q1': 2 * m}, {'c1': -1.0}, []),
    P('easy', e6, {'Q1': 2 * m}, {'c1': 4.0}, [vre('R4'), idiv('R2', 1 * m, ib(1, 2 * m), '50 times')]),
    # ---------------- medium ----------------
    P('medium', m7, {'Q1': 1 * m, 'Q2': 2 * m}, {'c2': 4.0},
      [vre('R4'), vre('R5'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    P('medium', m8, {'Q1': 1 * m, 'Q2': 4 * m}, {'e2': 6.0},
      [vre('R4'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    P('medium', m9, {'Q1': 1 * m, 'Q2': 2 * m}, {'c2': 1.0},
      [vre('R3'), vre('R6'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    P('medium', m10, {'Q1': 1 * m, 'Q3': 2 * m}, {'c3': 3.0}, [vre('R3')], vce_min=1),
    P('medium', m11, {'Q1': 1 * m, 'Q2': 3 * m}, {'e2': 3.0},
      [vre('R3'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    P('medium', m12, {'Q1': 1 * m, 'Q2': 2 * m}, {'c2': 2.0},
      [vre('R5'), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    # ---------------- hard ----------------
    P('hard', sp3(5), {'Q1': 2 * m, 'Q2': 4 * m, 'Q3': 6 * m}, {'e3': 2.5},
      [vre('R5'), vre('R4'),
       budget('R2', 1 * m, SP3_WHY.format(cap='14\\,\\mathrm{mA}', left='14 - 2 - 4 - 6 = 2\\,\\mathrm{mA}',
                                          ib1='20\\,\\mu\\mathrm{A}', pick='1\\,\\mathrm{mA}'))],
      vce_min=1, idc_max=14 * m, note='(This is Sample Problem 3 of the lecture.)'),
    P('hard', sp3(9), {'Q1': 1 * m, 'Q2': 2 * m, 'Q3': 5 * m}, {'e3': 5.0},
      [vre('R5'), vre('R4'),
       budget('R2', 0.5 * m, SP3_WHY.format(cap='9\\,\\mathrm{mA}', left='9 - 1 - 2 - 5 = 1\\,\\mathrm{mA}',
                                            ib1='10\\,\\mu\\mathrm{A}', pick='0.5\\,\\mathrm{mA}'))],
      vce_min=1, idc_max=9 * m),
    P('hard', h15, {'Q1': 1 * m, 'Q2': 2 * m, 'Q3': 2 * m, 'Q4': 5 * m}, {'e4': 6.0},
      [vre('R4'), vre('R5', 2.0, rule=False), vre('R8', 2.0, rule=False), idiv('R2', 0.5 * m, ib(1, 1 * m), '50 times')], vce_min=1),
    P('hard', h16, {'Q1': 2 * m, 'Q3': 4 * m, 'Q4': 1 * m}, {'e3': 4.0, 'c4': 7.0}, [], vce_min=1, idc_max=10 * m),
    P('hard', h17, {'Q1': 1 * m, 'Q4': 2 * m}, {'c4': -1.0}, [vre('R3')], vce_min=1),
    P('hard', h18, {'Q1': 1 * m, 'Q5': 2 * m}, {'c3': 2.0, 'c5': -2.0}, [vre('R4')], vce_min=1),
]
