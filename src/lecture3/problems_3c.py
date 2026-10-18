"""Set 3C: rectifiers and AC-adapter design (the rectifier slides and AC Adapter Design Examples 1-2).
Easy: analysis without/with a filter capacitor. Medium: transformers, choosing C for a ripple spec.
Hard: complete AC-adapter designs (transformer ratio, capacitor, diode ratings)."""
from .rect import RectProb

CODE = '3C'
SLUG = 'rectifiers'
TITLE = 'Set 3C: Rectifiers and AC-Adapter Design'
INTRO = r"""
\textbf{What this set trains.} Half-wave, center-tapped full-wave and bridge rectifiers: peak output, ripple with a
filter capacitor, diode currents and peak inverse voltage --- and, run backwards, the design of an AC adapter
(transformer ratio, capacitor, diode ratings) from its specifications. All diodes use the constant-voltage-drop
model ($0.7$\,V); the mains is $120\,\mathrm{V_{rms}}$ ($170$\,V peak), $60$\,Hz. Problems 1--6 are easy, 7--12
medium, 13--18 hard (design). Try each problem before looking at its solution.
"""

P = RectProb
PROBLEMS = [
    # ---------------- easy ----------------
    P('easy', 'half', 'analysis', vs=10, RL=1e3),
    P('easy', 'half', 'analysis', vs=12, RL=1e3, C=100e-6),
    P('easy', 'bridge', 'analysis', vs=15, RL=2e3),
    P('easy', 'center', 'analysis', vs=9, RL=1e3),
    P('easy', 'bridge', 'analysis', vs=12, RL=1e3, C=220e-6),
    P('easy', 'center', 'analysis', vs=10, RL=500, C=470e-6),
    # ---------------- medium ----------------
    P('medium', 'half', 'analysis', N=10, RL=500, C=470e-6),
    P('medium', 'center', 'analysis', N=8, RL=200, C=1000e-6),
    P('medium', 'bridge', 'analysis', N=12, RL=100, C=2200e-6),
    P('medium', 'bridge', 'find_C', vs=10, RL=100, vr=0.5),
    P('medium', 'half', 'find_C', N=12, RL=1e3, vomin=11),
    P('medium', 'center', 'find_C', N=10, RL=50, vr=0.4),
    # ---------------- hard ----------------
    P('hard', 'bridge', 'design', vo=3, kr=0.05, il=0.4),
    P('hard', 'center', 'design', vo=5, kr=0.10, il=1.5),
    P('hard', 'bridge', 'design', vo=12, kr=0.05, il=1.0),
    P('hard', 'center', 'design', vo=9, kr=0.05, il=0.5),
    P('hard', 'half', 'design', vo=5, kr=0.10, il=0.1),
    P('hard', 'bridge', 'design', vo=15, kr=0.05, il=0.8),
]
