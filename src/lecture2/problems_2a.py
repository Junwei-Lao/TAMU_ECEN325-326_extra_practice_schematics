"""Set 2A: ideal op-amp blocks and cascades (inverting, non-inverting, difference, summing, T-network).
Easy: one block, one corner. Medium: two corners, T-network, DC + AC summer, two-block cascades.
Hard: three blocks, DC blocked/passed between blocks, pole-zero cascades, phase-shifted inputs."""
from lecture1.ladder import R, C, Ser, Par
from lecture1.narrative import Sine
from .blocks import Inv, NonInv, Diff, Sum, InvT

CODE = '2A'
SLUG = 'opamp_blocks'
TITLE = 'Set 2A: Ideal Op-Amp Blocks and Cascades'
INTRO = r"""
\textbf{What this set trains.} Circuits built from the standard op-amp blocks (inverting, non-inverting,
difference, summing and T-network). With the two ideal op-amp rules (virtual short, no input current) every block
reduces to a one-line formula in terms of impedances, and a cascade is the product of its blocks. Problems 1--6 are
easy, 7--12 medium, 13--18 hard. All op-amps are ideal. Try each problem before looking at its solution.
"""


class ChainProb:
    def __init__(self, level, blocks, vin, note='', nonideal=None, label_outputs=False):
        self.level, self.blocks, self.vin, self.note = level, blocks, vin, note
        self.nonideal, self.label_outputs = nonideal, label_outputs


P = ChainProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [Inv(R('R1', '1k'), Par(R('R2', '10k'), C('C1', '10n')))], Sine(0.1, 2000)),
    P('easy', [Inv(Ser(R('R1', '2k'), C('C1', '1u')), R('R2', '20k'))], Sine(0.2, 50)),
    P('easy', [NonInv(zg=R('R1', '1k'), zf=Par(R('R2', '9k'), C('C1', '10n')))], Sine(0.1, 5000)),
    P('easy', [NonInv(zg=R('R1', '1k'), zf=R('R2', '4k'), za=C('C1', '100n'), zb=R('R3', '10k'))],
      Sine(0.2, 100)),
    P('easy', [Inv(Ser(R('R1', '1k'), C('C1', '1u')), Par(R('R2', '10k'), C('C2', '1n')))], Sine(0.05, 1000)),
    P('easy', [NonInv(za=R('R1', '10k'), zb=C('C1', '10n'))], Sine(1, 3000, fn='cos')),
    # ---------------- medium ----------------
    P('medium', [Inv(R('R1', '1k'), Par(R('R2', '10k'), C('C1', '10n'))),
                 Inv(Ser(R('R3', '1k'), C('C2', '1u')), R('R4', '2k'))], Sine(0.02, 500)),
    P('medium', [NonInv(zg=Ser(R('R1', '1k'), C('C1', '100n')), zf=R('R2', '9k'))], Sine(0.1, 500)),
    P('medium', [InvT(R('R1', '10k'), R('R2', '10k'), R('R3', '10k'), Ser(R('R4', '1k'), C('C1', '100n')))],
      Sine(0.1, 1000)),
    P('medium', [NonInv(zg=R('R1', '1k'), zf=R('R2', '2k'), za=C('C1', '1u'), zb=R('R3', '10k')),
                 Inv(R('R4', '10k'), Par(R('R5', '20k'), C('C2', '1n')))], Sine(0.1, 2000)),
    P('medium', [Sum(R('R1', '10k'), R('R2', '20k'), Par(R('R3', '20k'), C('C1', '10n')), -3)],
      Sine(0.5, 1000)),
    P('medium', [Inv(R('R1', '2k'), Ser(R('R2', '8k'), Par(R('R3', '10k'), C('C1', '100n'))))],
      Sine(0.2, 300)),
    # ---------------- hard ----------------
    P('hard', [Inv(Ser(R('R1', '1k'), C('C1', '1u')), R('R2', '10k')),
               Inv(R('R3', '10k'), Par(R('R4', '10k'), C('C2', '1n'))),
               NonInv(zg=R('R5', '1k'), zf=Par(R('R6', '1k'), C('C3', '100n')))], Sine(0.01, 2000)),
    P('hard', [NonInv(zg=Ser(R('R3', '1k'), C('C2', '1u')), zf=R('R4', '9k'),
                      za=R('R1', '10k'), zb=Ser(R('R2', '1k'), C('C1', '100n')))], Sine(0.1, 1000, phase_pi='1/4')),
    P('hard', [Sum(Ser(R('R1', '1k'), C('C1', '1u')), R('R2', '10k'), Par(R('R3', '5k'), C('C2', '10n')), 2),
               NonInv(zg=Ser(R('R4', '1k'), C('C3', '470n')), zf=R('R5', '4k'))], Sine(0.05, 1000),
      note='(The DC supply in the first block is $+2\\,\\mathrm{V}$.)'),
    P('hard', [Inv(Par(R('R1', '1k'), C('C1', '40n')), Par(R('R2', '5.6k'), C('C2', '56.8n'))),
               Inv(Par(R('R3', '1k'), C('C3', '16n')), Par(R('R4', '5.6k'), C('C4', '284p')))], Sine(0.01, 2000)),
    P('hard', [Diff(R('R1', '1k'), Par(R('R2', '2k'), C('C1', '10n')), R('R3', '1k'), R('R4', '4k'))],
      Sine(0.5, 10000, phase_pi='-1/3', fn='cos')),
    P('hard', [Inv(Ser(R('R1', '2k'), C('C1', '1u')), R('R2', '4k'), load=R('R3', '1k')),
               Diff(R('R4', '1k'), Par(R('R5', '2k'), C('C2', '10n')), R('R6', '1k'), R('R7', '4k'))],
      Sine(0.1, 3000, phase_pi='1/6')),
]
