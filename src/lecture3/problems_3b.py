"""Set 3B: transfer characteristics of op-amp circuits with diodes (like Sample Problems 4-5):
limiters, diodes in the feedback path, precision rectifiers, diodes after the op-amp output.
Easy: one diode. Medium: two diodes, soft limiting, offsets. Hard: cascades and three diodes."""
from lecture1.ladder import R, Ser, Par
from lecture2.blocks import Inv, InvT, Sum
from .pwl import D
from .circuits import DiodeOut, PrecisionRect

CODE = '3B'
SLUG = 'diode_opamp'
TITLE = 'Set 3B: Op-Amp Circuits with Diodes'
INTRO = r"""
\textbf{What this set trains.} The same state method as set 3A, now with ideal op-amps. In each assumed state an
op-amp either has negative feedback (virtual short) or has lost it because a diode in its feedback path is OFF; then
it runs open-loop and its output swings until a diode turns on (Sample Problem 5). Problems 1--6 are easy, 7--12
medium, 13--18 hard. Try each problem before looking at its solution.
"""


class ChainPWL:
    def __init__(self, level, blocks, model='CVD', vin=None, note=''):
        self.level, self.blocks, self.model, self.vin, self.note = level, blocks, model, vin, note


P = ChainPWL
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [Inv(R('R1', '1k'), Ser(R('R2', '5k'), Par(R('R3', '4k'), D('D1', flip=True))))]),
    P('easy', [Inv(R('R1', '1k'), Par(R('R2', '10k'), D('D1')))], vin=(1, 1000, 'sin')),
    P('easy', [DiodeOut(a=R('R1', '1k'), b=R('R2', '1k'), g=R('R3', '2k'), f=R('R4', '2k'), l=R('R5', '10k'),
                        d=D('D1'))], vin=(2, 500, 'sin')),
    P('easy', [PrecisionRect(a=R('R1', '1k'), d1=D('D1'), d2=D('D2'), f=R('R2', '2k'), l=R('R3', '10k'))],
      vin=(1, 1000, 'sin')),
    P('easy', [Inv(Ser(R('R1', '1k'), D('D1')), R('R2', '2k'))], vin=(3, 1000, 'sin')),
    P('easy', [Inv(R('R1', '1k'), Par(R('R2', '2k'), D('D1')))], model='ideal', vin=(2, 1000, 'sin')),
    # ---------------- medium ----------------
    P('medium', [Inv(R('R1', '1k'), Par(R('R2', '10k'), D('D1'), D('D2', flip=True)))], vin=(0.5, 1000, 'sin')),
    P('medium', [DiodeOut(a=R('R1', '1k'), b=R('R2', '2k'), g=R('R3', '3k'), f=R('R4', '4k'), l=R('R5', '5k'),
                          d=D('D1', flip=True))], vin=(2, 500, 'sin')),
    P('medium', [Inv(R('R1', '1k'), Par(R('R2', '10k'), Ser(R('R3', '1k'), D('D1'))))], vin=(1, 1000, 'sin')),
    P('medium', [Inv(R('R1', '1k'), Par(R('R2', '10k'), Ser(R('R3', '1k'), D('D1')),
                                     Ser(R('R4', '2k'), D('D2', flip=True))))], vin=(1, 1000, 'sin')),
    P('medium', [Sum(R('R1', '10k'), R('R2', '10k'), Par(R('R3', '10k'), D('D1')), -2)], vin=(4, 1000, 'sin')),
    P('medium', [PrecisionRect(a=R('R1', '2k'), d1=D('D1'), d2=D('D2'), f=R('R2', '2k'), l=R('R3', '10k')),
                 Inv(R('R4', '10k'), R('R5', '20k'))], vin=(1, 1000, 'sin')),
    # ---------------- hard ----------------
    P('hard', [Inv(R('R1', '1k'), Par(R('R2', '10k'), D('D1'), D('D2', flip=True))), Inv(R('R3', '1k'), R('R4', '3k'))],
      vin=(0.3, 1000, 'sin')),
    P('hard', [DiodeOut(a=R('R1', '1k'), b=R('R2', '3k'), g=R('R3', '1k'), f=R('R4', '1k'), l=R('R5', '5k'),
                        d=D('D1')), Inv(R('R6', '1k'), R('R7', '2k'))], vin=(1, 500, 'sin')),
    P('hard', [InvT(R('R1', '10k'), R('R2', '10k'), R('R3', '10k'), Ser(R('R4', '1k'), D('D1', flip=True)))],
      vin=(1, 1000, 'sin')),
    P('hard', [PrecisionRect(a=R('R1', '1k'), d1=D('D1'), d2=D('D2'), f=R('R2', '1k'), l=R('R3', '10k')),
               Sum(R('R4', '10k'), R('R5', '10k'), R('R6', '10k'), -1)], vin=(2, 1000, 'sin')),
    P('hard', [Inv(R('R1', '1k'), Par(R('R2', '4k'), Ser(D('D1'), R('R3', '1k')), Ser(D('D2', flip=True), R('R4', '2k')))),
               Inv(R('R5', '1k'), Par(R('R6', '2k'), D('D3')))], vin=(2, 1000, 'sin')),
    P('hard', [Sum(R('R1', '10k'), R('R2', '10k'), Par(R('R3', '20k'), Ser(R('R4', '5k'), D('D1')),
                                                        Ser(R('R5', '5k'), D('D2', flip=True))), 1)],
      vin=(3, 1000, 'sin')),
]
