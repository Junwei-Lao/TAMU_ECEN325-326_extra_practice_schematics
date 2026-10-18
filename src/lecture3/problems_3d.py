"""Set 3D: small-signal diode circuits (Sample Problems 6-8): DC point, r_d, AC transfer function, V_o(t).
Easy: one diode, CVD model or a fixed diode voltage, first-order AC. Medium: the sample problems themselves,
exponential model with iteration. Hard: Thevenin + iteration, two diodes, a second op-amp stage."""
from lecture1.ladder import R, C, Ser, Par, Src, Series, Shunt, Out
from lecture1.narrative import Sine
from lecture2.blocks import Inv
from .pwl import D
from .smallsig import SSLadder, SSOpamp

CODE = '3D'
SLUG = 'small_signal'
TITLE = 'Set 3D: Diode Small-Signal Analysis'
INTRO = r"""
\textbf{What this set trains.} Circuits where a diode is biased by DC and carries a small AC signal. First find the
DC operating point (constant-voltage-drop or exponential model), then replace the diode by its small-signal
resistance $r_d = nV_T/I_D$ and solve the AC circuit exactly as in Lectures 1--2; finally add DC and AC.
Unless stated otherwise $n = 1.8$ and $V_T = 25$\,mV. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each
problem before looking at its solution.
"""

L_, O_ = SSLadder, SSOpamp
PROBLEMS = [
    # ---------------- easy ----------------
    L_('easy', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '1k'), 5), Shunt(D('D1')), Out()],
       Sine(0.002, 5000)),
    L_('easy', [Src(), Series(C('C1', '4.7u')), Shunt(R('R1', '2k'), 10), Shunt(D('D1'), -5),
                Shunt(C('C2', '1u'), -5), Out()], Sine(0.002, 10000)),
    L_('easy', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '1k'), 12), Shunt(R('R2', '1k')), Shunt(D('D1')), Out()],
       Sine(0.001, 2000)),
    O_('easy', [Inv(R('R1', '1k'), Par(D('D1'), C('C1', '100n')))], 0.5, Sine(0.02, 1000), model='CVD'),
    O_('easy', [Inv(D('D1'), Par(R('R1', '2k'), C('C1', '47n')))], 0.55, Sine(0.002, 1000)),
    L_('easy', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '2k'), 5), Series(D('D1')), Shunt(R('R2', '1k'), -5),
                Out()], Sine(0.005, 1000)),
    # ---------------- medium ----------------
    L_('medium', [Src(), Series(C('C1', '5u')), Shunt(R('R1', '1k'), 5), Shunt(D('D1'), -5), Shunt(C('C2', '2u'), -5),
                  Out()], Sine(0.002, 10000)),
    L_('medium', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '1k'), 5), Shunt(D('D1')), Out()],
       Sine(0.002, 5000), model='exp', IS=2.6e-9),
    O_('medium', [Inv(R('R2', '1k'), Par(D('D1'), C('C1', '100n')))], 0.5, Sine(0.05, 1000)),
    O_('medium', [Inv(D('D1'), Par(R('R1', '1k'), C('C1', '100n')))], 0.6, Sine(0.003, 1000)),
    O_('medium', [Inv(R('R1', '2k'), Par(Ser(R('R2', '500'), D('D1')), C('C1', '100n')))], 1.0, Sine(0.05, 2000),
       model='CVD'),
    L_('medium', [Src(), Series(C('C1', '1u')), Shunt(R('R1', '3k'), 9), Shunt(R('R2', '1k')), Shunt(D('D1')),
                  Series(R('R3', '1k')), Shunt(C('C2', '100n')), Out()], Sine(0.002, 1000)),
    # ---------------- hard ----------------
    L_('hard', [Src(), Series(C('C1', '2.2u')), Shunt(R('R1', '4.7k'), 9), Shunt(R('R2', '2.2k')), Shunt(D('D1')),
                Series(R('R3', '1k')), Shunt(C('C2', '47n')), Out()], Sine(0.003, 2000), model='exp', IS=1e-12, n=1),
    O_('hard', [Inv(Ser(R('R1', '1k'), D('D1')), Par(R('R2', '2k'), C('C1', '47n')))], 1.0,
       Sine(0.01, 3000, phase_pi='1/4')),
    L_('hard', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '1k'), 10), Shunt(Ser(D('D1'), D('D2'))),
                Series(R('R2', '100')), Shunt(C('C2', '1u')), Out()], Sine(0.002, 1000)),
    O_('hard', [Inv(R('R1', '1k'), Par(D('D1'), C('C1', '100n'))), Inv(R('R2', '1k'), Par(R('R3', '10k'), C('C2', '10n')))],
       1.0, Sine(0.02, 2000)),
    L_('hard', [Src(), Series(C('C1', '10u')), Shunt(R('R1', '2k'), 5), Series(D('D1')), Shunt(R('R2', '2k'), -5),
                Shunt(C('C2', '1u')), Out()], Sine(0.005, 500), model='exp', IS=2.6e-9),
    O_('hard', [Inv(Ser(R('R1', '500'), D('D1')), Par(R('R2', '1k'), C('C1', '220n')))], 0.8,
       Sine(0.005, 500, phase_pi='-1/3', fn='cos'), IS=1e-12, n=1),
]
