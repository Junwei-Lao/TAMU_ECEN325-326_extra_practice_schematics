"""Set 5E: MOSFET amplifier design with the procedure of Sample Problem 5.
Easy: one common-source stage. Medium: CS stage + mirror-biased source follower (the topology of Sample Problem 5).
Hard: tighter specifications, the mirror-image (NMOS-input) version, scaled reference transistors."""
from .ampdesign5 import AmpSpec5

CODE = '5E'
SLUG = 'amplifier_design'
TITLE = 'Set 5E: MOSFET Amplifier Design'
FIG_H = '6cm'
INTRO = r"""
\textbf{What this set trains.} Designing a MOSFET amplifier from a specification table with the procedure of
Sample Problem 5: the load current sizes the current sink of the output follower, the follower gain tells how much the
common-source drain must swing, the supply budget bounds $V_{R4}$, the gain fixes $V_{ov1} = 2V_{R4}/|A_{v1}|$, and the
input resistance fixes the gate divider. Every design is checked by analysing the finished circuit (DC point, exact
gain, swing limits, distortion). Problems 1--6 are easy, 7--12 medium, 13--18 hard. Try each problem before looking
at its solution.
"""

P = AmpSpec5
k = 1e3
m = 1e-3
PROBLEMS = [
    # ---------------- easy: one common-source stage ----------------
    P('easy', 'p1', 5, 5, 2, 20, 100 * k, thd=0.06, vr3=0.5, vr4=5.0, k1=1 * m, vt1=1.0),
    P('easy', 'n1', 5, 5, 1.5, 25, 200 * k, thd=0.05, vr3=1.0, vr4=5.0, k1=1 * m, vt1=1.0),
    P('easy', 'p1', 6, 6, 2, 15, 100 * k, thd=0.05, vr3=1.0, vr4=6.0, k1=2 * m, vt1=0.8),
    P('easy', 'n1', 3, 3, 1, 10, 50 * k, thd=0.05, vr3=0.5, vr4=3.0, k1=0.5 * m, vt1=0.7),
    P('easy', 'p1', 5, 5, 1, 40, 1000 * k, thd=0.03, vr3=0.5, vr4=6.0, k1=1 * m, vt1=1.0),
    P('easy', 'n1', 9, 9, 3, 30, 500 * k, thd=0.05, vr3=1.0, vr4=9.0, k1=1 * m, vt1=1.0),
    # ---------------- medium: CS + mirror-biased follower ----------------
    P('medium', 'p', 5, 5, 1, 20, 100 * k, rl=200, thd=0.10, id3=10 * m),
    P('medium', 'p', 6, 6, 2, 30, 200 * k, rl=500, thd=0.10, id3=5 * m),
    P('medium', 'n', 5, 5, 1.5, 25, 50 * k, rl=100, thd=0.10, id3=20 * m, k1=2 * m, vt1=1.0, kf=40 * m, vtf=1.5),
    P('medium', 'p', 5, 5, 1, 15, 100 * k, rl=50, thd=0.10, id3=25 * m),
    P('medium', 'n', 6, 6, 2, 20, 100 * k, rl=200, thd=0.10, id3=12 * m, kf=50 * m, vtf=1.5),
    P('medium', 'p', 5, 5, 1.5, 30, 100 * k, rl=100, thd=0.10, id3=20 * m, ratio=0.2),
    # ---------------- hard ----------------
    P('hard', 'p', 5, 5, 2, 40, 50 * k, rl=100, thd=0.10, vr3=0.5, id3=25 * m,
      note='(These are the specifications of Sample Problem 5.)'),
    P('hard', 'n', 5, 5, 2, 40, 50 * k, rl=100, thd=0.10, vr3=0.5, id3=25 * m),
    P('hard', 'p', 9, 9, 4, 50, 100 * k, rl=100, thd=0.10, vr3=1.0, id3=45 * m),
    P('hard', 'n', 5, 5, 1.5, 30, 200 * k, rl=50, thd=0.08, id3=35 * m, ratio=0.25, kf=60 * m, vtf=1.2, k1=2 * m,
      vt1=0.8),
    P('hard', 'p', 6, 6, 2, 60, 100 * k, rl=75, thd=0.10, id3=30 * m, ratio=0.5),
    P('hard', 'n', 4, 4, 1, 20, 50 * k, rl=100, thd=0.10, id3=12 * m, kf=50 * m, vtf=1.0, k1=1 * m, vt1=0.7),
]
