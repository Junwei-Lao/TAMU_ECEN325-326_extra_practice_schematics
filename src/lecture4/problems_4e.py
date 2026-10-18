"""Set 4E: amplifier design with the procedures of the slides (one-, two- and three-stage designs, Sample Problem 11).
Easy: one CE stage (procedure #1). Medium: CE stage + emitter follower driving R_L. Hard: two CE stages + follower."""
from .ampdesign import AmpSpec

CODE = '4E'
SLUG = 'amplifier_design'
TITLE = 'Set 4E: BJT Amplifier Design'
FIG_H = '6cm'
INTRO = r"""
\textbf{What this set trains.} Designing a complete amplifier from a specification table, with the design procedures
of the lecture: pick $V_{RE}$ for $V_{BE}$-insensitivity, the largest $V_{RC}$ the output swing allows, $R_H$ of the
output follower from current clipping, then the largest bias current that still meets the input-resistance
specification; every resistor follows from Ohm's law and the gain formula. Each solution ends with an exact analysis
of the finished circuit ($\beta = 100$, base currents included) and, where needed, the small adjustment the slides
do in simulation (trim $R_{G1}$ for the exact gain, lower $R_H$ if the follower would clip). Problems 1--6 are easy,
7--12 medium, 13--18 hard. Try each problem before looking at its solution.
"""

P = AmpSpec
k = 1e3
m = 1e-3
PROBLEMS = [
    # ---------------- easy: one CE stage ----------------
    P('easy', ('npn',), 12, 2, 50, 5 * k, thd=0.02),
    P('easy', ('npn',), 10, 1.5, 80, 3 * k, thd=0.03),
    P('easy', ('npn',), 15, 3, 30, 10 * k, thd=0.02),
    P('easy', ('pnp',), 12, 2, 40, 4 * k, thd=0.02),
    P('easy', ('npn',), 9, 1, 100, 2 * k, thd=0.03),
    P('easy', ('pnp',), 5, 1, 50, 1 * k, thd=0.05),
    # ---------------- medium: CE + follower ----------------
    P('medium', ('pnp', 'F'), 9, 1.5, 40, 4 * k, rl=500, thd=0.03, vo_d=1.8),
    P('medium', ('npn', 'F'), 12, 2, 60, 5 * k, rl=1 * k, thd=0.03, vo_d=2.4),
    P('medium', ('pnp', 'F'), 5, 1, 30, 1.5 * k, rl=200, thd=0.05, vo_d=1.2),
    P('medium', ('npn', 'F'), 10, 1.5, 100, 3 * k, rl=300, thd=0.05, vo_d=1.8),
    P('medium', ('pnp', 'F'), 15, 3, 30, 10 * k, rl=1 * k, thd=0.03, vo_d=3.5, n=20),
    P('medium', ('npn', 'F'), 6, 1, 25, 2 * k, rl=100, thd=0.03, vo_d=1.2),
    # ---------------- hard: two CE stages + follower ----------------
    P('hard', ('pnp', 'npn', 'F'), 5, 1, 100, 2 * k, rl=150, thd=0.03, vo_d=1.3, n=20, vre=(1.8, 1.0),
      av_mid=(6,), ic_mid=(8 * m,), rh=50, note='(These are the specifications of Sample Problem 11.)'),
    P('hard', ('pnp', 'pnp', 'F'), 10, 2, 200, 5 * k, rl=500, thd=0.05, vo_d=2.4, vre=(1.0, 1.0), av_mid=(10,)),
    P('hard', ('npn', 'pnp', 'F'), 12, 2, 150, 4 * k, rl=1 * k, thd=0.05, vo_d=2.4, n=20, vre=(1.5, 1.0), av_mid=(8,)),
    P('hard', ('npn', 'pnp', 'F'), 9, 1.5, 120, 3 * k, rl=300, thd=0.05, vo_d=1.8, vre=(1.0, 1.0), av_mid=(8,)),
    P('hard', ('pnp', 'npn', 'F'), 9, 2, 150, 2 * k, rl=200, thd=0.05, vo_d=2.5, n=20, vre=(1.5, 1.0), av_mid=(8,)),
    P('hard', ('pnp', 'pnp', 'F'), 12, 3, 300, 2 * k, rl=1 * k, thd=0.05, vo_d=3.5, vre=(1.0, 1.0), av_mid=(12,)),
]
