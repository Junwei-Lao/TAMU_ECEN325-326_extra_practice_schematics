"""Set 1D: magnitude Bode plot -> H(s) -> steady-state output (like Sample Problem 4).
Easy: one or two corners, level marked in a flat band. Medium: two-three corners, s^2 starts,
double poles, level marked on a slope or outside the pass-band. Hard: four-plus corners, mixed
poles/zeros, double roots, level far from the pass-band, phase-shifted inputs.

Each problem gives: m (starting slope = +20m dB/dec), poles and zeros in Hz (repeat for a double
root), and the marked point (f_ref in Hz, level in dB). K follows from the marked level."""
from .narrative import Sine

CODE = '1D'
SLUG = 'bode_to_tf'
TITLE = 'Set 1D: From a Bode Plot to $H(s)$'
INTRO = r"""
\textbf{What this set trains.} Reading an asymptotic (straight-line) magnitude Bode plot backwards: from the
corner frequencies and slopes, write $H(s)$ factor by factor; use the one marked level to find the gain $K$;
then compute the steady-state output for a sinusoidal input. Problems 1--6 are easy, 7--12 medium, 13--18 hard.
Try each problem before looking at its solution.
"""


class BodeProb:
    def __init__(self, level, m, poles, zeros, ref, vin):
        self.level, self.m, self.poles, self.zeros, self.vin = level, m, poles, zeros, vin
        self.f_ref, self.L = ref
        self.note = ''


PROBLEMS = [
    # ---------------- easy ----------------
    BodeProb('easy', 0, [1000], [], (100, 20), Sine(0.5, 2000)),
    BodeProb('easy', 1, [200], [], (2000, 6), Sine(1, 100)),
    BodeProb('easy', 0, [5000], [], (500, -6), Sine(2, 10000, fn='cos')),
    BodeProb('easy', 1, [100, 10000], [], (1000, 0), Sine(1, 1000)),
    BodeProb('easy', 0, [10000], [1000], (100, 0), Sine(0.5, 3000)),
    BodeProb('easy', 0, [100], [1000], (10, 12), Sine(1, 500)),
    # ---------------- medium ----------------
    BodeProb('medium', 1, [50, 5000], [], (500, 30), Sine(0.1, 20000)),
    BodeProb('medium', 0, [1000, 20000], [], (100, 40), Sine(0.05, 5000)),
    BodeProb('medium', 1, [100, 20000], [2000], (100000, 20), Sine(0.2, 1000)),
    BodeProb('medium', 2, [200, 1000], [], (10000, 10), Sine(0.5, 400)),
    BodeProb('medium', 0, [2000, 2000], [], (100, 6), Sine(1, 4000)),
    BodeProb('medium', 1, [1000], [], (100, -20), Sine(1, 2000, phase_pi='1/4')),
    # ---------------- hard ----------------
    BodeProb('hard', 2, [500, 2000, 8000], [16000], (100000, 15), Sine(0.3, 10000)),
    BodeProb('hard', 1, [20, 5000, 50000], [500], (1000, 10), Sine(0.2, 2000, phase_pi='1/3')),
    BodeProb('hard', 0, [100, 100, 10000], [1000], (30000, -20), Sine(0.1, 300)),
    BodeProb('hard', 2, [50, 500, 50000], [5000], (200000, 26), Sine(0.05, 1000, phase_pi='-1/6', fn='cos')),
    BodeProb('hard', 0, [200, 2000, 200000], [20000], (100, 34), Sine(0.02, 5000, phase_pi='1/2')),
    BodeProb('hard', 1, [10, 100, 20000, 20000], [1000, 1000], (100, 0), Sine(0.5, 3000)),
]
