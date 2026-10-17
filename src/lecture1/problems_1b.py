"""Set 1B: superposition of DC supplies and an AC input (like Sample Problems 1, 5, 6).
Easy: one coupling/filter element and a bias divider. Medium: Thevenin of a bias network
followed by more parts. Hard: inductors, loads beyond the output, several reactive elements."""
from .spec import *  # noqa: F401,F403

CODE = '1B'
SLUG = 'superposition'
TITLE = 'Set 1B: DC + AC Superposition'
INTRO = r"""
\textbf{What this set trains.} Circuits with DC supplies \emph{and} an AC input. You split the problem in two
(superposition): a DC circuit that gives $V_{o,dc}$ (capacitors open, inductors shorted) and an AC circuit that
gives $H(s)$ and $v_{o,ac}(t)$ (supplies grounded). The DC part uses only one tool, the divider between two
voltages. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""

PROBLEMS = [
    # ---------------- easy ----------------
    Prob('easy', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k'), 10), Shunt(R('R2', '10k')), Out()],
         Sine(0.5, 100)),
    Prob('easy', [Src(), Series(C('C1', '470n')), Shunt(R('R1', '20k'), 12), Shunt(R('R2', '10k'), -12), Out()],
         Sine(1, 50)),
    Prob('easy', [Src(), Series(R('R1', '2k')), Shunt(C('C1', '100n')), Shunt(R('R2', '8k'), 5), Out()],
         Sine(0.5, 1000)),
    Prob('easy', [Src(), Series(C('C1', '220n')), Shunt(R('R1', '30k'), 9), Shunt(R('R2', '15k')),
                  Series(R('R3', '10k')), Out()],
         Sine(0.2, 100)),
    Prob('easy', [Src(), Series(R('R1', '3k')), Shunt(R('R2', '6k'), -6), Shunt(C('C1', '220n')), Out()],
         Sine(1, 500)),
    Prob('easy', [Src(), Series(C('C1', '2.2u')), Series(R('R1', '1k')), Shunt(R('R2', '9k'), 5),
                  Shunt(R('R3', '9k')), Out()],
         Sine(0.3, 20)),
    # ---------------- medium ----------------
    Prob('medium', [Src(), Series(C('C1', '4.7u')), Shunt(R('R1', '3k'), 6), Shunt(R('R2', '1.5k')),
                    Series(R('R3', '2k')), Shunt(C('C2', '22n')), Out()],
         Sine(0.5, 1000)),
    Prob('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '4k'), 5), Shunt(R('R2', '4k'), -5),
                    Series(R('R3', '1k')), Shunt(C('C2', '47n')), Shunt(R('R4', '3k'), 5), Out()],
         Sine(0.5, 2000)),
    Prob('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '20k'), 10), Shunt(R('R2', '10k')),
                    Series(R('R3', '1k')), Shunt(R('R4', '4k')), Shunt(C('C2', '10n')), Out()],
         Sine(1, 500)),
    Prob('medium', [Src(), Series(R('R1', '1k')), Shunt(C('C1', '1u')), Series(R('R2', '1k')),
                    Shunt(R('R3', '2k'), 6), Shunt(C('C2', '10n')), Out()],
         Sine(1, 200)),
    Prob('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k'), 12), Shunt(R('R2', '5k'), -12),
                    Series(L('L1', '50m')), Shunt(R('R3', '1k')), Out()],
         Sine(2, 1000)),
    Prob('medium', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '6k'), 9), Shunt(R('R2', '3k')),
                    Shunt(Ser(R('R3', '500'), C('C2', '1u'))), Out()],
         Sine(0.4, 300)),
    # ---------------- hard ----------------
    Prob('hard', [Src(), Series(Par(L('L1', '200m'), R('R1', '5k'))), Series(R('R2', '5k')),
                  Shunt(Ser(R('R3', '5k'), C('C1', '47n'))), Shunt(R('R4', '5k'), 6), Out()],
         Sine(1.5, 1000, phase_pi='1/4')),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k'), 5), Out(),
                  Series(R('R2', '1k')), Shunt(C('C2', '100n')), Shunt(R('R3', '10k'), -5)],
         Sine(0.5, 300),
         note='Note that $V_o$ is \\emph{not} at the right end: the branch to its right loads it, '
              'both at DC and at AC.'),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k'), 10), Shunt(R('R2', '10k'), -10),
                  Series(C('C2', '100n')), Shunt(R('R3', '20k'), 10), Shunt(R('R4', '10k')), Out()],
         Sine(0.3, 100)),
    Prob('hard', [Src(), Series(C('C1', '2.2u')), Shunt(R('R1', '8k'), 6), Shunt(R('R2', '4k'), -6),
                  Series(R('R3', '1k')), Shunt(C('C2', '100n')), Series(L('L1', '10m')),
                  Shunt(R('R4', '2k'), 6), Out()],
         Sine(1, 1000, fn='cos')),
    Prob('hard', [Src(), Series(R('R1', '2k')), Shunt(Ser(C('C1', '1u'), R('R2', '500'))),
                  Shunt(R('R3', '8k'), 5), Series(C('C2', '1u')), Shunt(R('R4', '10k'), -5),
                  Shunt(R('R5', '10k')), Out()],
         Sine(1, 500, phase_pi='-1/3', fn='cos')),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k'), 12), Shunt(R('R2', '2k')),
                  Series(Par(R('R3', '2k'), C('C2', '47n'))), Shunt(R('R4', '3k'), 12),
                  Shunt(R('R5', '3k')), Out()],
         Sine(0.5, 2000, phase_pi='1/6')),
]
