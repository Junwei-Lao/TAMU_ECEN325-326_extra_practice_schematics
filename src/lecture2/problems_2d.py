"""Set 2D: finite gain-bandwidth op-amps, A(s) = A0/(1+s/wb) (like Sample Problems 6-8).
Easy: one op-amp, resistive or capacitive feedback. Medium: cascades, difference amplifier, a shunt at the
- input, high gain. Hard: three op-amps, frequency-dependent dividers, RC feedback."""
from lecture1.ladder import R, C, Ser, Par
from lecture1.narrative import Sine
from .blocks import Inv, NonInv, Diff
from .problems_2a import ChainProb

CODE = '2D'
SLUG = 'finite_gbw'
TITLE = 'Set 2D: Op-Amps with Finite Gain-Bandwidth'
INTRO = r"""
\textbf{What this set trains.} Real op-amps have a finite open-loop gain $A(s)=\frac{A_0}{1+s/\omega_b}$.
Instead of the virtual short you write $V_{out}=A(V_+-V_-)$, express $V_+$ and $V_-$ with dividers (superposition),
and solve. For resistive (or purely capacitive) feedback the result is always the ideal gain times a single pole
near $\beta\omega_t$: the gain-bandwidth trade-off. Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each
problem before looking at its solution.
"""

P = ChainProb
NI = lambda a0, fb: (a0, fb)  # noqa: E731

PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', [NonInv(zg=R('R1', '1k'), zf=R('R2', '9k'))], Sine(0.1, 50000), nonideal=NI(1e5, 10)),
    P('easy', [Inv(R('R1', '1k'), R('R2', '4k'))], Sine(0.2, 100000), nonideal=NI(2e5, 5)),
    P('easy', [NonInv()], Sine(1, 500000), nonideal=NI(1e5, 20)),
    P('easy', [NonInv(zg=R('R1', '2k'), zf=R('R2', '18k'), za=R('R3', '1k'), zb=R('R4', '1k'))],
      Sine(0.2, 20000), nonideal=NI(1e5, 10)),
    P('easy', [Inv(R('R1', '10k'), R('R2', '100k'), load=R('R3', '2k'))], Sine(0.05, 50000),
      nonideal=NI(1e5, 10)),
    P('easy', [Inv(C('C1', '2n'), C('C2', '1n'))], Sine(0.2, 200000), nonideal=NI(1e5, 10)),
    # ---------------- medium ----------------
    P('medium', [NonInv(zg=R('R1', '1k'), zf=R('R2', '8k'), load=R('R3', '8k')),
                 Inv(R('R4', '2k'), R('R5', '16k'), load=R('R6', '16k'))], Sine(0.01, 100000),
      nonideal=NI(1e5, 20)),
    P('medium', [Diff(R('R1', '1k'), R('R2', '10k'), R('R3', '2k'), R('R4', '4k'))], Sine(0.1, 20000),
      nonideal=NI(1e5, 10)),
    P('medium', [Inv(R('R1', '1k'), R('R2', '10k')), Inv(R('R3', '1k'), R('R4', '10k'))], Sine(0.01, 50000),
      nonideal=NI(1e5, 10)),
    P('medium', [Inv(C('C1', '3n'), C('C2', '1n'), zm=C('C3', '2n'))], Sine(0.05, 500000),
      nonideal=NI(1e5, 30)),
    P('medium', [NonInv(zg=R('R1', '1k'), zf=R('R2', '99k'))], Sine(0.01, 5000), nonideal=NI(1e5, 10)),
    P('medium', [NonInv(), NonInv(zg=R('R1', '1k'), zf=R('R2', '4k'))], Sine(0.1, 200000),
      nonideal=NI(2e5, 5)),
    # ---------------- hard ----------------
    P('hard', [NonInv(zg=R('R1', '1k'), zf=R('R2', '4k')), Inv(R('R3', '2k'), R('R4', '10k'), load=R('R5', '1k')),
               NonInv()], Sine(0.02, 100000), nonideal=NI(1e5, 10)),
    P('hard', [Diff(R('R1', '1k'), R('R2', '5k'), R('R3', '1k'), R('R4', '2k')), Inv(R('R5', '1k'), R('R6', '2k'))],
      Sine(0.05, 50000, phase_pi='1/4'), nonideal=NI(1e5, 20)),
    P('hard', [Inv(R('R1', '2k'), R('R2', '20k'), zm=R('R3', '1k'))], Sine(0.05, 20000, fn='cos'),
      nonideal=NI(1e5, 10)),
    P('hard', [NonInv(zg=R('R1', '1k'), zf=R('R2', '9k'), za=R('R3', '10k'), zb=C('C1', '1n'))],
      Sine(0.1, 10000), nonideal=NI(1e5, 10)),
    P('hard', [Inv(R('R1', '1k'), Par(R('R2', '10k'), C('C1', '1n')))], Sine(0.1, 30000, phase_pi='-1/6'),
      nonideal=NI(1e5, 10)),
    P('hard', [Inv(C('C1', '4n'), C('C2', '1n'), zm=C('C3', '5n')), NonInv(zg=R('R1', '1k'), zf=R('R2', '1k'))],
      Sine(0.02, 100000), nonideal=NI(1e5, 10)),
]
