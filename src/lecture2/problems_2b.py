"""Set 2B: op-amp circuits that need nodal analysis (like Sample Problems 1-4): Sallen-Key, multiple feedback,
ladders into a buffer, two op-amps in a loop.
Easy: one or two KCL equations. Medium: positive feedback with gain, multiple feedback, extra capacitors.
Hard: a nodal stage followed by a block, and two-op-amp loops."""
from lecture1.ladder import R, C, Ser, Par
from lecture1.narrative import Sine
from .blocks import Inv, NonInv
from .topo import LadderInv, PiBuf, SallenKey, MFB, Loop
from .problems_2a import ChainProb

CODE = '2B'
SLUG = 'nodal_analysis'
TITLE = 'Set 2B: Op-Amp Circuits by Nodal Analysis'
INTRO = r"""
\textbf{What this set trains.} Op-amp circuits that are not one of the standard blocks. The recipe never changes:
apply the virtual short, write KCL at every node that is not an op-amp output, and eliminate the unknown node
voltages one at a time until only $V_o$ and $V_i$ are left. All op-amps are ideal. Problems 1--6 are easy, 7--12
medium, 13--18 hard. Try each problem before looking at its solution.
"""

P = ChainProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [LadderInv(a=R('R1', '1k'), b=C('C1', '100n'), c=R('R2', '1k'), f=R('R3', '10k'))], Sine(0.1, 2000)),
    P('easy', [LadderInv(a=R('R1', '2k'), b=R('R2', '2k'), c=C('C1', '100n'), f=R('R3', '10k'))], Sine(0.2, 500)),
    P('easy', [PiBuf(a=R('R1', '1k'), c=C('C1', '100n'), b=R('R2', '10k'), d=C('C2', '1n'))], Sine(1, 5000)),
    P('easy', [SallenKey(a=R('R1', '10k'), b=R('R2', '10k'), c=C('C1', '10n'), d=C('C2', '47n'))], Sine(0.5, 1000)),
    P('easy', [SallenKey(a=C('C1', '10n'), b=C('C2', '10n'), c=R('R1', '20k'), d=R('R2', '1k'))], Sine(0.5, 50000)),
    P('easy', [LadderInv(a=R('R1', '1k'), b=C('C1', '1u'), c=R('R2', '1k'), f=Par(R('R3', '10k'), C('C2', '10n')))],
      Sine(0.1, 500, fn='cos')),
    # ---------------- medium ----------------
    P('medium', [SallenKey(a=R('R1', '1k'), b=R('R2', '10k'), c=C('C1', '10n'), d=C('C2', '100n'),
                           g=R('R3', '10k'), f=R('R4', '5k'))], Sine(0.2, 1000)),
    P('medium', [SallenKey(a=C('C1', '100n'), b=C('C2', '10n'), c=R('R1', '10k'), d=R('R2', '1k'),
                           g=R('R3', '10k'), f=R('R4', '5k'))], Sine(0.2, 30000)),
    P('medium', [MFB(a=R('R1', '10k'), c=C('C1', '100n'), d=C('C2', '100n'), f=R('R3', '2k'))], Sine(1, 300)),
    P('medium', [MFB(a=R('R1', '10k'), b=C('C1', '10n'), c=R('R2', '10k'), d=R('R3', '10k'), f=C('C2', '100n'))],
      Sine(0.5, 200)),
    P('medium', [SallenKey(a=R('R1', '2k'), b=R('R2', '10k'), c=C('C1', '10n'), d=C('C2', '47n'),
                           e=C('C3', '100n'), h=C('C4', '10n'))], Sine(0.5, 500, phase_pi='1/4')),
    P('medium', [PiBuf(a=R('R1', '1k'), c=C('C1', '1u'), b=R('R2', '10k'), d=C('C2', '10n'),
                       g=R('R3', '1k'), f=R('R4', '4k'))], Sine(0.1, 1000)),
    # ---------------- hard ----------------
    P('hard', [SallenKey(a=R('R1', '10k'), b=R('R2', '10k'), c=C('C1', '1n'), d=C('C2', '100n'),
                         g=R('R3', '10k'), f=R('R4', '10k')),
               Inv(R('R5', '10k'), Par(R('R6', '20k'), C('C3', '1n')))], Sine(0.1, 2000)),
    P('hard', [MFB(a=R('R1', '10k'), b=R('R2', '10k'), c=C('C1', '10n'), d=C('C2', '100n'), f=R('R3', '1k')),
               NonInv(zg=R('R4', '1k'), zf=R('R5', '99k'))], Sine(0.05, 2000)),
    P('hard', [Loop(a=Ser(R('R1', '1k'), C('C2', '1u')), f1=C('C1', '10n'), r=R('R2', '10k'),
                    g2=R('R3', '1k'), f2=R('R4', '3k'))], Sine(0.05, 1000)),
    P('hard', [Loop(a=R('R1', '10k'), f1=C('C1', '10n'), r=R('R2', '10k'), g2=R('R3', '1k'), f2=R('R4', '1k'))],
      Sine(0.2, 5000, phase_pi='-1/4', fn='cos')),
    P('hard', [SallenKey(a=C('C1', '100n'), b=C('C2', '10n'), c=R('R1', '10k'), d=R('R2', '1k'),
                         g=R('R3', '10k'), f=R('R4', '5k')),
               Inv(R('R5', '10k'), Par(R('R6', '10k'), C('C3', '1n')))], Sine(0.1, 20000)),
    P('hard', [PiBuf(a=C('C1', '1u'), c=R('R1', '1k'), b=C('C2', '10n'), d=R('R2', '100k')),
               Inv(R('R3', '10k'), Par(R('R4', '50k'), C('C3', '1n')))], Sine(0.05, 1000, phase_pi='1/3')),
]
