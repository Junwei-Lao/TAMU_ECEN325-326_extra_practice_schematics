"""Set 1C: cascaded stages separated by dependent sources (like Sample Problems 2, 3).
Easy: two stages, each first order. Medium: elements across sources, VCCS into networks,
three stages. Hard: second-order stages, inductors, nested branches, phase-shifted inputs."""
from .spec import *  # noqa: F401,F403

CODE = '1C'
SLUG = 'dependent_sources'
TITLE = 'Set 1C: Stages Coupled by Dependent Sources'
INTRO = r"""
\textbf{What this set trains.} Circuits split into stages by dependent sources (diamond symbols). A VCVS
($kV_x$) forces its output voltage; a VCCS ($gV_x$) pushes a current into the impedance on its node. Because a
dependent source does not load the node it watches, $H(s)$ is simply the product of the stage gains, and each
stage is solved with voltage dividers. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem
before looking at its solution.
"""

PROBLEMS = [
    # ---------------- easy ----------------
    Prob('easy', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '1k')), Tap('x'),
                  VCVS(10, 'x'), Series(R('R3', '1k')), Shunt(C('C1', '100n')), Out()],
         Sine(0.1, 1000)),
    Prob('easy', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '2k')), Tap('x'),
                  VCVS(-5, 'x'), Series(R('R2', '1k')), Shunt(R('R3', '4k')), Out()],
         Sine(0.2, 100)),
    Prob('easy', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '4k')), Tap('x'),
                  VCCS('0.01', 'x', 'down'), Shunt(R('R3', '2k')), Shunt(C('C1', '100n')), Out()],
         Sine(0.05, 500)),
    Prob('easy', [Src(), Shunt(R('R1', '10k')), Series(C('C1', '470n')), Shunt(R('R2', '4.7k')), Tap('x'),
                  VCCS('0.002', 'x', 'up'), Shunt(R('R3', '10k')), Out()],
         Sine(0.1, 200)),
    Prob('easy', [Src(), Series(R('R1', '2k')), Shunt(R('R2', '2k')), Shunt(C('C1', '1u')), Tap('x'),
                  VCVS(20, 'x'), Shunt(C('C2', '1n')), Series(R('R3', '10k')), Shunt(C('C3', '10n')), Out()],
         Sine(0.05, 300)),
    Prob('easy', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k')), Tap('x'),
                  VCCS('0.005', 'x', 'down'), Shunt(R('R2', '1k')), Shunt(C('C2', '1u')), Out()],
         Sine(0.2, 50)),
    # ---------------- medium ----------------
    Prob('medium', [Src(), Shunt(R('R1', '5k')), Series(C('C1', '2.2u')), Series(R('R2', '1k')),
                    Shunt(R('R3', '4k')), Tap('x'),
                    VCVS(-8, 'x'), Shunt(C('C2', '10p')), Series(C('C3', '22n')), Shunt(R('R4', '10k')), Out()],
         Sine(0.1, 1000)),
    Prob('medium', [Src(), Shunt(C('C1', '47p')), Series(R('R1', '1k')), Shunt(R('R2', '4k')),
                    Shunt(C('C2', '50n')), Tap('x'),
                    VCCS('0.02', 'x', 'down'), Shunt(C('C3', '2.2u')), Series(R('R3', '2k')),
                    Shunt(R('R4', '3k')), Out()],
         Sine(0.05, 2000)),
    Prob('medium', [Src(), Series(C('C1', '100n')), Series(R('R1', '1k')), Shunt(R('R2', '9k')), Tap('x'),
                    VCVS(4, 'x'), Series(R('R3', '2k')), Shunt(Ser(R('R4', '2k'), C('C2', '10n'))), Out()],
         Sine(0.2, 5000)),
    Prob('medium', [Src(), Series(R('R1', '9k')), Shunt(Ser(R('R2', '1k'), C('C1', '1u'))), Tap('x'),
                    VCVS(-2, 'x'), Series(C('C2', '47n')), Shunt(R('R3', '10k')), Out()],
         Sine(0.5, 100)),
    Prob('medium', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '1k')), Tap('x'),
                    VCCS('0.004', 'x', 'up'), Shunt(R('R3', '5k')), Series(L('L1', '50m')),
                    Shunt(R('R4', '5k')), Out()],
         Sine(0.2, 20000)),
    Prob('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '1k')), Tap('x'),
                    VCVS(3, 'x'), Series(R('R2', '1k')), Shunt(C('C2', '100n')), Tap('y'),
                    VCCS('0.001', 'y', 'down'), Shunt(R('R3', '10k')), Shunt(C('C3', '1n')), Out()],
         Sine(0.1, 1000)),
    # ---------------- hard ----------------
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '10k')), Series(R('R2', '1k')),
                  Shunt(C('C2', '10n')), Tap('x'),
                  VCVS(-10, 'x'), Series(R('R3', '1k')), Shunt(R('R4', '9k')), Shunt(C('C3', '1n')), Out()],
         Sine(0.05, 2000)),
    Prob('hard', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '4k')), Shunt(Ser(R('R3', '200'), C('C1', '1u'))),
                  Tap('x'),
                  VCCS('0.05', 'x', 'down'), Shunt(C('C2', '1u')), Series(R('R4', '1k')),
                  Shunt(R('R5', '4k')), Out()],
         Sine(0.02, 1000)),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '2k')), Tap('x'),
                  VCVS(5, 'x'), Series(R('R2', '1k')), Shunt(C('C2', '100n')), Shunt(R('R3', '1k')), Tap('y'),
                  VCCS('0.002', 'y', 'down'), Shunt(R('R4', '20k')), Series(R('R5', '10k')),
                  Shunt(C('C3', '1n')), Out()],
         Sine(0.1, 2000, phase_pi='1/4')),
    Prob('hard', [Src(), Series(R('R1', '1k')), Shunt(R('R2', '3k')), Shunt(C('C1', '100n')), Tap('x'),
                  VCVS(-4, 'x'), Series(Par(R('R3', '10k'), C('C2', '10n'))), Shunt(R('R4', '1k')), Out()],
         Sine(0.1, 3000, fn='cos')),
    Prob('hard', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '1k')), Series(R('R2', '1k')),
                  Shunt(R('R3', '1k')), Tap('x'),
                  VCCS('0.01', 'x', 'up'), Shunt(L('L1', '10m')), Shunt(R('R4', '1k')), Out()],
         Sine(0.2, 5000, phase_pi='-1/6')),
    Prob('hard', [Src(), Shunt(R('R1', '10k')), Series(R('R2', '2k')), Shunt(Ser(R('R3', '1k'), C('C1', '100n'))),
                  Shunt(R('R4', '3k')), Tap('x'),
                  VCCS('0.02', 'x', 'down'), Shunt(C('C2', '1u')), Shunt(R('R5', '2k')), Tap('y'),
                  VCVS(-2, 'y'), Series(C('C3', '470n')), Shunt(R('R6', '10k')), Out()],
         Sine(0.01, 500, phase_pi='1/3', fn='cos')),
]
