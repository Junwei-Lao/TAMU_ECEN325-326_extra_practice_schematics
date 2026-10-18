"""Set 3A: transfer characteristics V_o(V_i) of resistive diode circuits (like Sample Problems 1-2).
Easy: one diode, one breakpoint. Medium: diodes with DC references, two diodes (clippers), diodes
bypassing resistors. Hard: two or three diodes with references and loads, several breakpoints."""
from lecture1.ladder import R, Ser, Par, Src, Series, Shunt, Out
from .pwl import D

CODE = '3A'
SLUG = 'diode_transfer'
TITLE = 'Set 3A: Diode Transfer Characteristics'
INTRO = r"""
\textbf{What this set trains.} Finding $V_o$ as a function of $V_i$ for circuits with diodes, resistors and DC
references, and sketching it. One method handles every circuit: assume each diode ON or OFF, solve the linear
circuit, and keep only the assumptions that check out. Each valid assumption gives one straight piece of the
characteristic. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""


class PWLProb:
    def __init__(self, level, items, model='CVD', vin=None, note=''):
        self.level, self.items, self.model, self.vin, self.note = level, items, model, vin, note


P = PWLProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [Src(), Series(D('D1')), Shunt(R('R1', '1k')), Out()], vin=(5, 60, 'sin')),
    P('easy', [Src(), Series(R('R1', '1k')), Shunt(D('D1')), Out()], vin=(3, 1000, 'sin')),
    P('easy', [Src(), Series(R('R1', '2k')), Shunt(R('R2', '2k')), Shunt(D('D1', flip=True)), Out()],
      model='ideal', vin=(4, 1000, 'sin')),
    P('easy', [Src(), Series(R('R1', '1k')), Shunt(D('D1'), rail=2), Out()], vin=(5, 1000, 'sin')),
    P('easy', [Src(), Series(R('R1', '2k')), Shunt(Ser(R('R2', '1k'), D('D1'))), Shunt(R('R3', '4k')), Out()]),
    P('easy', [Src(), Series(D('D1')), Shunt(R('R1', '3k')), Series(R('R2', '1k')), Shunt(R('R3', '2k')), Out()],
      model='ideal'),
    # ---------------- medium ----------------
    P('medium', [Src(), Series(Par(R('R1', '1k'), D('D1', flip=True))), Shunt(R('R2', '2k')), Series(R('R3', '3k')),
                 Shunt(R('R4', '4k')), Out()]),
    P('medium', [Src(), Series(R('R1', '1k')), Shunt(D('D1')), Shunt(D('D2', flip=True)), Out()],
      vin=(2, 1000, 'sin')),
    P('medium', [Src(), Series(R('R1', '1k')), Shunt(Ser(R('R2', '1k'), D('D1', flip=True)), rail=-3),
                 Shunt(R('R3', '3k')), Out()]),
    P('medium', [Src(), Series(Par(R('R1', '2k'), D('D1'))), Shunt(R('R2', '2k'), rail=5), Shunt(R('R3', '2k')),
                 Out()]),
    P('medium', [Src(), Series(R('R1', '1k')), Shunt(D('D1'), rail=2), Shunt(D('D2', flip=True), rail=-1), Out()],
      model='ideal', vin=(4, 500, 'sin')),
    P('medium', [Src(), Series(R('R1', '1k')), Shunt(Ser(D('D1'), R('R2', '1k')), rail=1), Series(R('R3', '1k')),
                 Shunt(R('R4', '2k')), Out()]),
    # ---------------- hard ----------------
    P('hard', [Src(), Series(R('R1', '1k')), Shunt(Ser(R('R2', '1k'), D('D1')), rail=1),
               Shunt(Ser(R('R3', '2k'), D('D2', flip=True)), rail=-2), Shunt(R('R4', '4k')), Out()],
      vin=(6, 1000, 'sin')),
    P('hard', [Src(), Series(Par(R('R1', '1k'), D('D1', flip=True))), Shunt(R('R2', '2k')),
               Shunt(Ser(R('R5', '1k'), D('D2')), rail=1), Series(R('R3', '3k')), Shunt(R('R4', '4k')), Out()]),
    P('hard', [Src(), Series(Par(R('R1', '2k'), D('D1'))), Shunt(Ser(R('R2', '1k'), D('D2', flip=True)), rail=-1),
               Shunt(R('R3', '2k')), Out()]),
    P('hard', [Src(), Series(R('R1', '1k')), Shunt(D('D1'), rail=2), Shunt(Ser(R('R2', '1k'), D('D2')), rail=1),
               Shunt(D('D3', flip=True), rail=-2), Out()], vin=(5, 1000, 'sin')),
    P('hard', [Src(), Series(D('D1')), Shunt(R('R1', '2k'), rail=-5), Series(R('R2', '1k')),
               Shunt(Ser(D('D2'), R('R3', '1k')), rail=2), Shunt(R('R4', '4k')), Out()]),
    P('hard', [Src(), Series(Par(R('R1', '1k'), Ser(R('R2', '1k'), D('D1')))), Shunt(R('R3', '2k'), rail=3),
               Shunt(Ser(R('R4', '1k'), D('D2', flip=True)), rail=-3), Shunt(R('R5', '2k')), Out()],
      vin=(8, 1000, 'sin')),
]
