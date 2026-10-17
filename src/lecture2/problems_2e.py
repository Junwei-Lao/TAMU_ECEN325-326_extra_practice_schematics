"""Set 2E: slew-rate limits (like the slew-rate problems P1-P8).
Easy: one op-amp. Medium: two op-amps (which output distorts first?), finite-gain models.
Hard: three op-amps, frequency-dependent stages, capacitive finite-gain circuits, a DC offset."""
from lecture1.ladder import R, C, Ser, Par
from .blocks import Inv, NonInv, Diff, Sum

CODE = '2E'
SLUG = 'slew_rate'
TITLE = 'Set 2E: Slew-Rate Limits'
INTRO = r"""
\textbf{What this set trains.} An op-amp output cannot change faster than its slew rate $SR$. For a sinusoid of
amplitude $\hat V$ at $\omega$ the fastest change is $\omega\hat V$, so every op-amp output must satisfy
$\omega\hat V\le SR$. You find the gain from $V_i$ to every op-amp output at the input frequency, pick the largest
one, and solve for the largest input amplitude. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each
problem before looking at its solution.
"""


class SlewProb:
    def __init__(self, level, blocks, SR, f, nonideal=None, note=''):
        self.level, self.blocks, self.SR, self.f, self.nonideal, self.note = level, blocks, SR, f, nonideal, note


P = SlewProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [Inv(R('R1', '1k'), R('R2', '10k'))], 0.5, 20000),
    P('easy', [NonInv(zg=R('R1', '1k'), zf=R('R2', '4k'))], 1, 50000),
    P('easy', [Inv(R('R1', '1k'), Par(R('R2', '10k'), C('C1', '10n')))], 0.2, 10000),
    P('easy', [Inv(Ser(R('R1', '1k'), C('C1', '100n')), R('R2', '20k'))], 2, 10000),
    P('easy', [NonInv()], 0.3, 100000),
    P('easy', [NonInv(zg=R('R1', '1k'), zf=R('R2', '2k'), za=R('R3', '10k'), zb=C('C1', '1n'))], 1, 20000),
    # ---------------- medium ----------------
    P('medium', [Inv(R('R1', '1k'), R('R2', '10k')), Inv(R('R3', '10k'), Par(R('R4', '5k'), C('C1', '1n')))],
      1, 50000),
    P('medium', [NonInv(zg=R('R1', '1k'), zf=R('R2', '9k')), Inv(Ser(R('R3', '1k'), C('C1', '10n')), R('R4', '3k'))],
      0.5, 3000),
    P('medium', [Inv(Par(R('R1', '10k'), C('C1', '10n')), R('R2', '10k')),
                 NonInv(zg=R('R3', '1k'), zf=Par(R('R4', '4k'), C('C2', '1n')))], 1, 10000),
    P('medium', [NonInv(zg=R('R1', '1k'), zf=R('R2', '8k'), load=R('R3', '8k')),
                 Inv(R('R4', '2k'), R('R5', '16k'), load=R('R6', '16k'))], 2, 200000, nonideal=(1e5, 20)),
    P('medium', [Diff(R('R1', '1k'), R('R2', '10k'), R('R3', '2k'), R('R4', '4k'))], 3, 50000,
      nonideal=(1e5, 10)),
    P('medium', [Inv(R('R1', '2k'), Par(R('R2', '20k'), C('C1', '2n'))),
                 Inv(R('R3', '10k'), Par(R('R4', '5k'), C('C2', '2n')))], 0.5, 8000),
    # ---------------- hard ----------------
    P('hard', [Inv(Ser(R('R1', '1k'), C('C1', '1u')), R('R2', '10k')),
               Inv(R('R3', '10k'), Par(R('R4', '10k'), C('C2', '1n'))),
               NonInv(zg=R('R5', '1k'), zf=Par(R('R6', '1k'), C('C3', '100n')))], 1, 20000),
    P('hard', [Inv(Par(R('R1', '1k'), C('C1', '40n')), Par(R('R2', '5.6k'), C('C2', '56.8n'))),
               Inv(Par(R('R3', '1k'), C('C3', '16n')), Par(R('R4', '5.6k'), C('C4', '284p')))], 0.5, 2000),
    P('hard', [Inv(C('C1', '3n'), C('C2', '1n'), zm=C('C3', '2n'))], 5, 500000, nonideal=(1e5, 30)),
    P('hard', [NonInv(zg=R('R1', '1k'), zf=R('R2', '4k')), Inv(R('R3', '2k'), R('R4', '10k')), NonInv()],
      2, 100000, nonideal=(1e5, 10)),
    P('hard', [Sum(R('R1', '10k'), R('R2', '20k'), Par(R('R3', '40k'), C('C1', '200p')), 5),
               Inv(R('R4', '10k'), Par(R('R5', '20k'), C('C2', '1n')))], 0.2, 10000),
    P('hard', [NonInv(zg=Ser(R('R1', '1k'), C('C1', '100n')), zf=R('R2', '9k')),
               Diff(R('R3', '1k'), Par(R('R4', '2k'), C('C2', '10n')), R('R5', '1k'), R('R6', '4k')),
               Inv(R('R7', '1k'), Par(R('R8', '3k'), C('C3', '2n')))], 0.8, 6000),
]
