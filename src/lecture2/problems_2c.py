"""Set 2C: design an op-amp circuit from a magnitude Bode plot (like Sample Problem 5).
Easy: one stage (+ sign-fixing inverter). Medium: two stages. Hard: three or four stages, double poles,
zeros, an s^2 start."""
from lecture1.narrative import Sine
from lecture1.problems_1d import BodeProb

CODE = '2C'
SLUG = 'design_from_bode'
TITLE = 'Set 2C: Op-Amp Filter Design from a Bode Plot'
INTRO = r"""
\textbf{What this set trains.} A design problem runs the pipeline backwards: read $H(s)$ from a straight-line Bode
plot (exactly as in Lecture 1, set 1D), split it into first-order factors, realize each group of factors with one
inverting op-amp stage, and compute the component values. Design rules used in every problem (they make the answer
unique so you can check it): $R_1=10\,\mathrm{k}\Omega$ at the input of every stage; all of $|K|$ in the first stage;
a unity-gain inverter at the end if needed so that $K>0$. Then find the steady-state output for the given input.
Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""

P = BodeProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', 0, [1000], [], (100, 20), Sine(0.1, 2000)),
    P('easy', 1, [200], [], (2000, 14), Sine(0.2, 100)),
    P('easy', 0, [5000], [], (500, 0), Sine(1, 10000, fn='cos')),
    P('easy', 1, [100, 10000], [], (1000, 20), Sine(0.05, 300)),
    P('easy', 0, [100], [1000], (10, 20), Sine(0.1, 500)),
    P('easy', 0, [10000], [1000], (100, 0), Sine(0.5, 3000)),
    # ---------------- medium ----------------
    P('medium', 0, [1000, 20000], [], (100, 26), Sine(0.05, 5000)),
    P('medium', 2, [100, 1000], [], (10000, 20), Sine(0.1, 300)),
    P('medium', 1, [100, 20000], [2000], (100000, 20), Sine(0.2, 1000)),
    P('medium', 0, [100, 10000], [1000], (10, 12), Sine(0.2, 2000)),
    P('medium', 1, [20, 2000, 20000], [], (200, 20), Sine(0.1, 5000)),
    P('medium', 0, [500, 5000], [], (50, 0), Sine(1, 1000, phase_pi='1/4')),
    # ---------------- hard ----------------
    P('hard', 0, [500, 100000], [4000, 10000], (100, 30), Sine(0.01, 2000)),
    P('hard', 2, [500, 2000, 8000], [16000], (100000, 15), Sine(0.3, 10000)),
    P('hard', 1, [20, 5000, 50000], [500], (1000, 10), Sine(0.2, 2000, phase_pi='1/3')),
    P('hard', 0, [100, 100, 10000], [1000], (10, 20), Sine(0.1, 300)),
    P('hard', 2, [50, 500, 50000], [5000], (200000, 26), Sine(0.05, 1000, phase_pi='-1/6', fn='cos')),
    P('hard', 1, [10, 100, 20000, 20000], [1000, 1000], (100, 0), Sine(0.5, 3000)),
]
