"""Set 1A: AC transfer function of passive RLC networks (no DC sources).
Easy: one reactive element. Medium: two reactive elements or a pole-zero pair.
Hard: second/third order, loads beyond the output, nested branches, phase-shifted inputs."""
from .spec import *  # noqa: F401,F403

CODE = '1A'
SLUG = 'ac_transfer'
TITLE = 'Set 1A: AC Transfer Functions of RLC Networks'
INTRO = r"""
\textbf{What this set trains.} Finding $H(s)=V_o/V_i$ of a passive network with \emph{voltage dividers only},
turning it into Bode-ready form, sketching the magnitude Bode plot, and computing the steady-state sinusoidal
output. There are no DC sources here, so Step~2 of the pipeline is always trivial. Problems 1--6 are easy,
7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""

PROBLEMS = [
    # ---------------- easy: first order ----------------
    Prob('easy', [Src(), Series(R('R1', '1k')), Shunt(C('C1', '100n')), Out()],
         Sine(2, 1000)),
    Prob('easy', [Src(), Series(C('C1', '470n')), Shunt(R('R1', '3.3k')), Out()],
         Sine(1, 200)),
    Prob('easy', [Src(), Series(R('R1', '2k')), Shunt(L('L1', '20m')), Out()],
         Sine(0.5, 10000)),
    Prob('easy', [Src(), Series(L('L1', '50m')), Shunt(R('R1', '1k')), Out()],
         Sine(3, 5000, fn='cos')),
    Prob('easy', [Src(), Series(R('R1', '4k')), Shunt(R('R2', '4k')), Shunt(C('C1', '10n')), Out()],
         Sine(1, 2000)),
    Prob('easy', [Src(), Shunt(R('R1', '10k')), Series(C('C1', '1u')), Series(R('R2', '1k')),
                  Shunt(R('R3', '4k')), Out()],
         Sine(0.2, 50)),
    # ---------------- medium ----------------
    Prob('medium', [Src(), Series(R('R1', '9k')), Shunt(Ser(R('R2', '1k'), C('C1', '100n'))), Out()],
         Sine(1, 500)),
    Prob('medium', [Src(), Series(Par(R('R1', '9k'), C('C1', '10n'))), Shunt(R('R2', '1k')), Out()],
         Sine(0.5, 5000)),
    Prob('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k')), Series(R('R2', '1k')),
                    Shunt(C('C2', '10n')), Out()],
         Sine(1, 1000)),
    Prob('medium', [Src(), Series(R('R1', '1k')), Shunt(C('C1', '100n')), Series(R('R2', '10k')),
                    Shunt(C('C2', '1n')), Out()],
         Sine(1, 3000)),
    Prob('medium', [Src(), Series(C('C1', '2.2u')), Shunt(R('R1', '2k')), Series(L('L1', '10m')),
                    Shunt(R('R2', '1k')), Out()],
         Sine(2, 1000)),
    Prob('medium', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '3k')),
                    Shunt(Ser(R('R3', '500'), C('C1', '1u'))), Out()],
         Sine(1, 1000)),
    # ---------------- hard ----------------
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '4.7k')), Series(R('R2', '2.2k')),
                  Shunt(Ser(C('C2', '22n'), R('R3', '1k'))), Out()],
         Sine(1, 2000, phase_pi='1/4', fn='cos')),
    Prob('hard', [Src(), Series(Par(L('L1', '200m'), R('R1', '2k'))), Series(R('R2', '2k')),
                  Shunt(Ser(R('R3', '2k'), C('C1', '470n'))), Shunt(R('R4', '2k')), Out()],
         Sine(1, 1000, phase_pi='1/3')),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '1k')), Series(L('L1', '10m')),
                  Shunt(R('R2', '1k')), Out()],
         Sine(0.5, 2000)),
    Prob('hard', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '1k')), Series(R('R2', '1k')),
                  Shunt(C('C2', '100n')), Series(R('R3', '10k')), Shunt(C('C3', '1n')), Out()],
         Sine(1, 1000)),
    Prob('hard', [Src(), Series(R('R1', '1k')), Shunt(C('C1', '100n')), Out(),
                  Series(R('R2', '1k')), Shunt(C('C2', '1u'))],
         Sine(1, 500),
         note='Note that $V_o$ is \\emph{not} at the right end: the branch to its right loads it.'),
    Prob('hard', [Src(), Series(Par(R('R1', '10k'), Ser(R('R2', '1k'), C('C1', '100n')))),
                  Shunt(R('R3', '2k')), Shunt(C('C2', '10n')), Out()],
         Sine(1, 2000, phase_pi='-1/6')),
]
