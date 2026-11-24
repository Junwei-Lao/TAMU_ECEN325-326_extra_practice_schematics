"""Set 5C: MOSFET bias design --- choose resistors (and W/L of mirror outputs) for target currents and voltages.
Easy: one transistor, or one mirror to size. Medium: two direct-coupled transistors, mirror-fed stages, reference
chains. Hard: three or four transistors mixing resistive and mirror biasing."""
from .mosnet import M, R, Col, BJTCircuit
from .design5 import MosDesign, vr, ir, rpar

CODE = '5C'
SLUG = 'bias_design'
TITLE = 'Set 5C: MOSFET Bias Design'
FIG_H = '6cm'
BUILD_ARG = True
INTRO = r"""
\textbf{What this set trains.} Designing the bias of MOSFET circuits: from target drain currents and node voltages
to resistor values and transistor sizes. It is the DC analysis of sets 5A/5B run backwards --- a target current
fixes $V_{GS}$, Ohm's law gives every resistor, the $W/L$ ratio sets every mirror current --- and each solution ends
by analysing the finished circuit. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking
at its solution.
"""

m = 1e-3
u = 1e-6
SL = (1.1e-3, 1.4, 0.85e-3, 1.3)
KN, VTN, KPP, VTP = 200e-6, 0.7, 100e-6, 0.8


def tools(v):
    """r(name): resistor (designed value or blank); n/p: devices with the slides' k'W/L; ns/ps: sized devices."""
    def r(name):
        return R(name, repr(float(v[name])) if v else '1k')

    def n(name, **kw):
        return M(name, 'nmos', kw=SL[0], vt=SL[1], **kw)

    def p(name, **kw):
        return M(name, 'pmos', kw=SL[2], vt=SL[3], **kw)

    def nw(name, wl, size=False, **kw):
        if size:
            return M(name, 'nmos', kp=KN, vt=VTN, wl=(v[name], wl[1]) if v else wl, size_me=not v, **kw)
        return M(name, 'nmos', kp=KN, vt=VTN, wl=wl, **kw)

    def pw(name, wl, size=False, **kw):
        if size:
            return M(name, 'pmos', kp=KPP, vt=VTP, wl=(v[name], wl[1]) if v else wl, size_me=not v, **kw)
        return M(name, 'pmos', kp=KPP, vt=VTP, wl=wl, **kw)
    return r, n, p, nw, pw


def div(r, a, node, b, top, bot, label=()):
    return Col([r(a), node, r(b)], top=top, bottom=bot, gap=3.2, label_nodes=label)


B = BJTCircuit
P = MosDesign


# ---------------------------------------------------------------- easy
def e1(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 10, 0),
              Col([r('R3'), 'd1', n('M1', gate='g1'), 's1', r('R4')], top=10, bottom=0, label_nodes=('d1',))])


def e2(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 10, 0),
              Col([r('R3'), 's1', p('M1', gate='g1'), 'd1', r('R4')], top=10, bottom=0, label_nodes=('d1',))])


def e3(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 12, 0),
              Col([n('M1', gate='g1'), 's1', r('R3')], top=12, bottom=0, label_nodes=('s1',))])


def e4(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([r('R1'), 'd1', n('M1', gate='0'), 's1', r('R2')], top=5, bottom=-5, label_nodes=('d1',))])


def e5(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([r('R1'), 'm', nw('M1', (10, 1), diode=True)], top=5, bottom=0, gap=4.6),
              Col([r('R2'), 'd2', nw('M2', (10, 1), size=True, gate='m')], top=5, bottom=0, label_nodes=('d2',)),
              Col([r('R3'), 'd3', nw('M3', (10, 1), size=True, gate='m')], top=5, bottom=0, label_nodes=('d3',))])


def e6(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([pw('M1', (20, 1), diode=True), 'm', r('R1')], top=5, bottom=-5, gap=4.6),
              Col([pw('M2', (20, 1), size=True, gate='m'), 'd2', r('R2')], top=5, bottom=-5, label_nodes=('d2',))])


# ---------------------------------------------------------------- medium
def m7(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 10, 0),
              Col([r('R3'), 'd1', n('M1', gate='g1'), 's1', r('R4')], top=10, bottom=0),
              Col([r('R5'), 's2', p('M2', gate='d1'), 'd2', r('R6')], top=10, bottom=0, label_nodes=('d2',))])


def m8(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 12, 0),
              Col([r('R3'), 'd1', n('M1', gate='g1'), 's1', r('R4')], top=12, bottom=0),
              Col([n('M2', gate='d1'), 's2', r('R5')], top=12, bottom=0, label_nodes=('s2',))])


def m9(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 5, -5),
              Col([r('R3'), 's1', p('M1', gate='g1'), 'd1', r('R4')], top=5, bottom=-5),
              Col([r('R5'), 'd2', n('M2', gate='d1'), 's2', r('R6')], top=5, bottom=-5, label_nodes=('d2',))])


def m10(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R2', 'g3', 'R3', 5, -5),
              Col([nw('M3', (20, 1), gate='g3'), 's3', nw('M2', (10, 1), size=True, gate='m', face='right')],
                  top=5, bottom=-5, label_nodes=('s3',)),
              Col([r('R1'), 'm', nw('M1', (5, 1), diode=True)], top=5, bottom=-5, gap=4.6)])


def m11(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([pw('M3', (10, 1), size=True, gate='mp', face='right'), 'd3', r('R2')], top=3, bottom=-3,
                  label_nodes=('d3',)),
              Col([pw('M1', (10, 1), diode=True), 'mp', r('R1'), 'mn', nw('M2', (5, 1), diode=True)],
                  top=3, bottom=-3, gap=4.6),
              Col([r('R3'), 'd4', nw('M4', (5, 1), size=True, gate='mn')], top=3, bottom=-3, label_nodes=('d4',))])


def m12(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 5, -5),
              Col([r('R3'), 's1', p('M1', gate='g1'), 'd1', r('R4')], top=5, bottom=-5),
              Col([r('R5'), 'd2', n('M2', gate='0', face='right'), 'd1'], top=5, bottom=None, label_nodes=('d2',))])


# ---------------------------------------------------------------- hard
def h13(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 10, 0),
              Col([r('R3'), 'd1', n('M1', gate='g1'), 's1', r('R4')], top=10, bottom=0),
              Col([r('R5'), 's2', p('M2', gate='d1'), 'd2', r('R6')], top=10, bottom=0),
              Col([n('M3', gate='d2'), 's3', r('R7')], top=10, bottom=0, label_nodes=('s3',))])


def h14(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 5, -5),
              Col([r('R3'), 's1', p('M1', gate='g1'), 'd1', r('R4')], top=5, bottom=-5),
              Col([r('R5'), 'd2', n('M2', gate='0', face='right'), 'd1'], top=5, bottom=None),
              Col([r('R6'), 's3', p('M3', gate='d2'), 'd3', r('R7')], top=5, bottom=-5),
              Col([n('M4', gate='d3'), 's4', r('R8')], top=5, bottom=-5, label_nodes=('s4',))])


def h15(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([r('R1'), 'mn', nw('M1', (10, 1), diode=True)], top=5, bottom=-5, gap=4.6),
              Col([pw('M3', (10, 1), diode=True), 'mp', nw('M2', (10, 1), size=True, gate='mn')], top=5, bottom=-5,
                  gap=4.6),
              Col([pw('M4', (10, 1), size=True, gate='mp'), 'd4', r('R2')], top=5, bottom=-5),
              Col([r('R3'), 'd5', nw('M5', (10, 1), gate='d4'), 's5', nw('M6', (10, 1), size=True, gate='mn')],
                  top=5, bottom=-5, label_nodes=('d5',))])


def h16(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 12, 0),
              Col([r('R3'), 'x', n('M1', gate='g1'), 's1', r('R4')], top=12, bottom=0),
              Col([p('M2', gate='g2', face='right'), 'd2', r('R5')], top_node='x', bottom=0),
              div(r, 'R6', 'g2', 'R7', 12, 0),
              Col([r('R8'), 'd3', n('M3', gate='d2'), 's3', r('R9')], top=12, bottom=0, label_nodes=('d3',))])


def h17(v):
    r, n, p, nw, pw = tools(v)
    return B([Col([pw('M1', (10, 1), diode=True), 'mp', r('R1'), 'mn', nw('M2', (10, 1), diode=True)],
                  top=5, bottom=-5, gap=4.6),
              Col([pw('M3', (10, 1), size=True, gate='mp'), 'd3', r('R2')], top=5, bottom=-5),
              Col([r('R3'), 'd4', nw('M4', (20, 1), gate='d3'), 's4', nw('M5', (10, 1), size=True, gate='mn')],
                  top=5, bottom=-5, label_nodes=('d4',)),
              Col([r('R4'), 's6', pw('M6', (20, 1), gate='d4'), 'd6', r('R5')], top=5, bottom=-5, label_nodes=('d6',))])


def h18(v):
    r, n, p, nw, pw = tools(v)
    return B([div(r, 'R1', 'g1', 'R2', 6, -6),
              Col([r('R3'), 'd1', n('M1', gate='g1'), 's1', r('R4')], top=6, bottom=-6),
              Col([r('R5'), 's2', p('M2', gate='d1'), 'd2', r('R6')], top=6, bottom=-6),
              Col([r('R7'), 'd3', n('M3', gate='d2'), 's3', r('R8')], top=6, bottom=-6),
              Col([r('R9'), 's4', p('M4', gate='d3'), 'd4', r('R10')], top=6, bottom=-6, label_nodes=('d4',))])


PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', e1, {'M1': 0.5 * m}, {'d1': 6.0}, [vr('R4', 1.0), ir('R2', 10 * u)]),
    P('easy', e2, {'M1': 0.4 * m}, {'d1': 3.0}, [vr('R3', 1.5), rpar('R1', 'R2', 500e3)]),
    P('easy', e3, {'M1': 1 * m}, {'s1': 4.0}, [ir('R2', 20 * u)]),
    P('easy', e4, {'M1': 0.5 * m}, {'d1': 2.0}, []),
    P('easy', e5, {'M1': 100 * u, 'M2': 200 * u, 'M3': 50 * u}, {'d2': 2.0, 'd3': 3.0}, []),
    P('easy', e6, {'M1': 50 * u, 'M2': 150 * u}, {'d2': 0.0}, []),
    # ---------------- medium ----------------
    P('medium', m7, {'M1': 0.2 * m, 'M2': 0.5 * m}, {'d2': 2.0}, [vr('R4', 1.0), vr('R5', 2.0), ir('R2', 5 * u)]),
    P('medium', m8, {'M1': 0.25 * m, 'M2': 1 * m}, {'s2': 5.0}, [vr('R4', 1.0), rpar('R1', 'R2', 1e6)]),
    P('medium', m9, {'M1': 0.2 * m, 'M2': 0.4 * m}, {'d2': 1.0}, [vr('R3', 2.0), vr('R6', 1.0), ir('R2', 10 * u)]),
    P('medium', m10, {'M1': 50 * u, 'M2': 200 * u}, {'s3': -1.0}, [ir('R3', 5 * u)]),
    P('medium', m11, {'M1': 100 * u, 'M3': 300 * u, 'M4': 150 * u}, {'d3': 0.0, 'd4': 0.5}, []),
    P('medium', m12, {'M1': 0.15 * m, 'M2': 0.2 * m}, {'d2': 2.0}, [vr('R3', 1.5), ir('R2', 20 * u)]),
    # ---------------- hard ----------------
    P('hard', h13, {'M1': 0.2 * m, 'M2': 0.5 * m, 'M3': 1 * m}, {'s3': 4.0}, [vr('R4', 1.0), vr('R5', 2.0),
                                                                             rpar('R1', 'R2', 500e3)]),
    P('hard', h14, {'M1': 0.1 * m, 'M2': 0.2 * m, 'M3': 0.5 * m, 'M4': 1 * m}, {'s4': -2.0},
      [vr('R3', 1.5), vr('R6', 1.0), ir('R2', 20 * u)]),
    P('hard', h15, {'M1': 100 * u, 'M2': 50 * u, 'M4': 200 * u, 'M6': 300 * u}, {'d4': -1.0, 'd5': 2.0}, []),
    P('hard', h16, {'M1': 0.3 * m, 'M2': 0.2 * m, 'M3': 0.5 * m}, {'x': 9.0, 'd3': 6.0},
      [vr('R4', 1.0), vr('R9', 1.0), ir('R2', 10 * u), rpar('R6', 'R7', 600e3)]),
    P('hard', h17, {'M1': 100 * u, 'M3': 200 * u, 'M5': 400 * u, 'M6': 300 * u}, {'d3': 0.0, 'd4': 1.0, 'd6': -2.0}, []),
    P('hard', h18, {'M1': 0.2 * m, 'M2': 0.3 * m, 'M3': 0.5 * m, 'M4': 0.8 * m}, {'d4': -3.0},
      [vr('R4', 1.0), vr('R5', 1.5), vr('R8', 1.0), vr('R9', 1.5), ir('R2', 10 * u)]),
]
