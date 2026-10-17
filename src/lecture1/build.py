"""Build all Lecture-1 practice sets.

    python -m lecture1.build [1A 1B 1C 1D] [--no-pdf]      (run from the src/ folder)

For every problem: draw the schematic + DC/AC equivalents + Bode plot into
output/lecture1/<set>/, cross-check the derived answer (independent nodal (MNA) solve for
circuits, direct polynomial evaluation for 1D), write src/lecture1/tex/L1_<set>.tex and
compile it to the PDF next to it.
"""
import math
import os
import sys

import numpy as np

from common import mna, texdoc as T
from common.bode import plot_bode, plot_bode_problem, plot_bode_factors
from common.tf import TF
from . import draw
from .ladder import Circuit, netlist
from .narrative import solve, pipeline_card
from .narrative_1d import solve_1d, pipeline_card_1d
from . import problems_1a, problems_1b, problems_1c, problems_1d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'output', 'lecture1')
TEX = os.path.join(ROOT, 'src', 'lecture1', 'tex')

SETS = [problems_1a, problems_1b, problems_1c, problems_1d]
LEVELS = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


def verify(circ, tf, vodc, pid):
    nl, names = netlist(circ, 'ac')
    for f in (3.0, 97.0, 1.3e3, 2.9e4, 7.7e5):
        w = 2 * math.pi * f
        ref = mna.solve(nl, w)[names['o']]
        got = tf.at(w)
        if abs(ref - got) > 1e-6 * max(1e-9, abs(ref)) + 1e-12:
            raise AssertionError(f'{pid}: H mismatch at {f} Hz: MNA {ref} vs derived {got}')
    if circ.has_dc():
        nl, names = netlist(circ, 'dc')
        ref = mna.solve(nl)[names['o']].real
        if abs(ref - vodc) > 1e-6 * max(1.0, abs(ref)):
            raise AssertionError(f'{pid}: Vodc mismatch MNA {ref} vs derived {vodc}')


def statement(sig_in):
    return (r'For the circuit below: (a) find the AC transfer function $H(s)=\dfrac{V_o(s)}{V_i(s)}$ and '
            r'sketch its magnitude Bode plot; (b) find the steady-state output $V_o(t)$ for $'
            + sig_in.tex() + '$.')


def build_one(k, p, pid, odir):
    base = f'p{k:02d}'
    circ = Circuit(p.items)
    figs = dict(circuit=f'{base}_circuit', ac=f'{base}_ac', dc=f'{base}_dc', bode=f'{base}_bode')
    body, tf, ans = solve(circ, p.vin, figs)
    verify(circ, tf, ans['vodc'], pid)
    draw.draw_full(circ, os.path.join(odir, figs['circuit']))
    draw.draw_ac(circ, os.path.join(odir, figs['ac']))
    if circ.has_dc():
        draw.draw_dc(circ, os.path.join(odir, figs['dc']))
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)

    st = statement(p.vin) + ((' ' + p.note) if p.note else '')
    wide = len(circ.stages) > 1
    prob = (f'\\begin{{probbox}}{{Problem {pid} \\hfill {LEVELS[p.level]}}}\n{st}\n'
            + T.figure(figs['circuit'], width=r'\linewidth' if wide else r'0.8\linewidth', height='5.5cm')
            + '\\end{probbox}\n')
    sol = (f'\\newpage\n\\subsection*{{Solution {pid} \\hfill {LEVELS[p.level]}}}\n'
           + T.figure(figs['circuit'], width=r'0.8\linewidth', height='4.5cm') + body)
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = (f'{pid:6s} {p.level:6s} K={tf.K:<10.4g} corners(Hz)=[{corners}]  '
            f'Vodc={ans["vodc"]:.3g}  amp={ans["amp"]:.3g} ph={ans["phase"]:.3g}')
    return prob, sol, line


def bode_tf(p):
    """TF of a 1D problem: K is whatever makes the asymptote pass through the marked level."""
    poles = [2 * math.pi * f for f in p.poles]
    zeros = [2 * math.pi * f for f in p.zeros]
    unit = TF.from_bode(1.0, p.m, poles, zeros)
    K = 10 ** ((p.L - unit.asym_db(2 * math.pi * p.f_ref)) / 20)
    return TF.from_bode(K, p.m, poles, zeros)


def build_one_1d(k, p, pid, odir):
    base = f'p{k:02d}'
    tf = bode_tf(p)
    figs = dict(plot=f'{base}_plot', factors=f'{base}_factors')
    body, ans = solve_1d(tf, p.f_ref, p.vin, figs)
    # checks: the marked level, the K found in the text, and the factor product vs the plain polynomial
    wr = 2 * math.pi * p.f_ref
    assert abs(tf.asym_db(wr) - p.L) < 1e-9, pid
    assert abs(ans['K'] - tf.K) < 1e-9 * tf.K, pid
    for f in (7.0, 300.0, 4.1e3, 6.6e4):
        jw = 2j * math.pi * f
        ref = np.polyval(tf.num, jw) / np.polyval(tf.den, jw)
        assert abs(ref - tf.at(2 * math.pi * f)) < 1e-9 * abs(ref), f'{pid}: factor form mismatch'
    plot_bode_problem(tf, os.path.join(odir, figs['plot']), p.f_ref)
    plot_bode_factors(tf, os.path.join(odir, figs['factors']))
    st = (r'The straight-line (asymptotic) magnitude Bode plot of $H(s)=\dfrac{V_o(s)}{V_i(s)}$ is shown. '
          r'(a) Find $H(s)$ (assume $K>0$ and no right-half-plane poles or zeros). '
          r'(b) Find the steady-state output $V_o(t)$ for $' + p.vin.tex() + '$.')
    prob = (f'\\begin{{probbox}}{{Problem {pid} \\hfill {LEVELS[p.level]}}}\n{st}\n'
            + T.figure(figs['plot'], width=r'0.8\linewidth', height='6cm') + '\\end{probbox}\n')
    sol = (f'\\newpage\n\\subsection*{{Solution {pid} \\hfill {LEVELS[p.level]}}}\n'
           + T.figure(figs['plot'], width=r'0.7\linewidth', height='5cm') + body)
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = (f'{pid:6s} {p.level:6s} K={tf.K:<10.4g} corners(Hz)=[{corners}]  '
            f'amp={ans["amp"]:.3g} ph={ans["phase"]:.3g}')
    return prob, sol, line


def build_set(mod, make_pdf=True):
    odir = os.path.join(OUT, f'{mod.CODE}_{mod.SLUG}')
    os.makedirs(odir, exist_ok=True)
    probs, sols, summary, errors = [], [], [], []
    last_level = None
    for k, p in enumerate(mod.PROBLEMS, 1):
        pid = f'{mod.CODE}.{k}'
        try:
            one = build_one_1d if mod.CODE == '1D' else build_one
            prob, sol, line = one(k, p, pid, odir)
        except Exception as e:  # report every broken problem, not just the first
            errors.append(f'{pid}: {type(e).__name__}: {e}')
            continue
        if p.level != last_level:
            probs.append(f'\\subsection*{{{LEVELS[p.level]} problems}}')
            last_level = p.level
        probs.append(prob)
        sols.append(sol)
        summary.append(line)
    if errors:
        raise SystemExit('\n'.join(errors))
    card, nsteps = (pipeline_card_1d(), 'six') if mod.CODE == '1D' else (pipeline_card(), 'seven')
    body = (mod.INTRO + '\n' + card
            + '\n\\section*{Problems}\n' + '\n'.join(probs)
            + '\n\\newpage\n\\section*{Solutions}\n'
            + f'Every solution follows the same {nsteps} steps of the pipeline card.\n'
            + '\n'.join(sols))
    gp = f'../../../output/lecture1/{mod.CODE}_{mod.SLUG}/'
    doc = T.document(mod.TITLE, 'ECEN 325 --- Lecture 1 (Linear Network Analysis) practice set', gp, body)
    T.check_balanced(doc, mod.CODE)
    os.makedirs(TEX, exist_ok=True)
    tex_path = os.path.join(TEX, f'L1_{mod.CODE}_{mod.SLUG}.tex')
    with open(tex_path, 'w', encoding='utf-8') as fh:
        fh.write(doc)
    if make_pdf:
        summary.append('PDF: ' + T.compile_pdf(tex_path))
    return summary


def main(args):
    make_pdf = '--no-pdf' not in args
    which = [a for a in args if not a.startswith('--')]
    for mod in SETS:
        if which and mod.CODE not in which:
            continue
        print(f'== {mod.CODE} {mod.TITLE}', flush=True)
        for line in build_set(mod, make_pdf):
            print('  ' + line, flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
