"""Build all Lecture-2 practice sets.

    python -m lecture2.build [2A 2B 2C 2D 2E] [--no-pdf]      (run from the src/ folder)

Figures go to output/lecture2/<set>/, LaTeX + compiled PDF to src/lecture2/tex/.
Every answer is checked against an exact nodal solve and an independent numeric MNA solve.
"""
import math
import os
import sys

import sympy as sp

from common import texdoc as T
from common.bode import plot_bode
from common.tf import s
from .netlist import solve_exact, verify
from .chain import Chain
from .narrative2 import solve_chain, solve_slew, solve_design, pipeline_card
from . import problems_2a, problems_2b, problems_2c, problems_2d, problems_2e

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'output', 'lecture2')
TEX = os.path.join(ROOT, 'src', 'lecture2', 'tex')
LEVELS = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


def A_of(nonideal):
    A0, fb = nonideal
    wb = sp.Rational(repr(2 * math.pi * fb))
    return sp.Rational(str(A0)) / (1 + s / wb)


def same_tf(a, b, where):
    for f in (5.0, 230.0, 4.4e3, 7.1e4, 9.0e5):
        jw = 2j * math.pi * f
        x, y = complex(a.subs(s, jw)), complex(b.subs(s, jw))
        if abs(x - y) > 1e-7 * max(abs(x), 1e-9):
            raise AssertionError(f'{where}: H mismatch at {f} Hz: {x} vs {y}')


def statement(sig_in, extra=''):
    return (r'For the circuit below' + extra + r': (a) find $H(s)=\dfrac{V_o(s)}{V_i(s)}$ and sketch its magnitude '
            r'Bode plot; (b) find the steady-state output $V_o(t)$ for $' + sig_in.tex() + '$.')


def build_chain_problem(k, p, pid, odir):
    base = f'p{k:02d}'
    chain = Chain(p.blocks)
    figs = dict(circuit=f'{base}_circuit', bode=f'{base}_bode')
    body, tf, H, ans = solve_chain(chain, p.vin, figs, p.nonideal)
    # --- independent checks
    net = chain.net()
    A = None if p.nonideal is None else A_of(p.nonideal)
    exact = solve_exact(net, A)
    same_tf(H, exact['o'], pid)
    verify(net, exact, ['o'], A_expr=A, where=pid)
    if chain.has_dc():
        dc = solve_exact(net, A, mode='dc')['o']
        assert abs(float(dc) - ans['vodc']) < 1e-9 * max(1, abs(float(dc))), f'{pid}: DC mismatch'
    chain.draw(os.path.join(odir, figs['circuit']), label_outputs=p.label_outputs)
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)
    if p.nonideal is None:
        extra = ' (ideal op-amps)'
    else:
        A0, fb = p.nonideal
        extra = (f', where every op-amp has the open-loop gain $A(s)=\\dfrac{{{T_num(A0)}}}{{1+\\dfrac{{s}}{{2\\pi\\cdot '
                 f'{T_num(fb)}}}}}$')
    st = statement(p.vin, extra) + ((' ' + p.note) if p.note else '')
    return st, body, tf, ans


def T_num(x):
    from common.units import num_tex
    return num_tex(x)


def build_set(mod, make_pdf=True):
    odir = os.path.join(OUT, f'{mod.CODE}_{mod.SLUG}')
    os.makedirs(odir, exist_ok=True)
    probs, sols, summary, errors = [], [], [], []
    last_level = None
    for k, p in enumerate(mod.PROBLEMS, 1):
        pid = f'{mod.CODE}.{k}'
        try:
            st, body, fig, line = mod.BUILD(k, p, pid, odir)
        except Exception as e:  # report every broken problem, not just the first
            import traceback
            errors.append(f'{pid}: {type(e).__name__}: {e}\n{traceback.format_exc(limit=-3)}')
            continue
        if p.level != last_level:
            probs.append(f'\\subsection*{{{LEVELS[p.level]} problems}}')
            last_level = p.level
        probs.append(f'\\begin{{probbox}}{{Problem {pid} \\hfill {LEVELS[p.level]}}}\n{st}\n'
                     + T.figure(fig, width=r'\linewidth', height='5.6cm') + '\\end{probbox}\n')
        sols.append(f'\\newpage\n\\subsection*{{Solution {pid} \\hfill {LEVELS[p.level]}}}\n'
                    + T.figure(fig, width=r'\linewidth', height='5cm') + body)
        summary.append(f'{pid:6s} {p.level:6s} {line}')
    if errors:
        raise SystemExit('\n'.join(errors))
    body = (mod.INTRO + '\n' + pipeline_card()
            + '\n\\section*{Problems}\n' + '\n'.join(probs)
            + '\n\\newpage\n\\section*{Solutions}\n'
            + 'Every solution follows the steps of the Lecture-2 pipeline card.\n' + '\n'.join(sols))
    gp = f'../../../output/lecture2/{mod.CODE}_{mod.SLUG}/'
    doc = T.document(mod.TITLE, 'ECEN 325 --- Lecture 2 (Operational Amplifiers) practice set', gp, body)
    T.check_balanced(doc, mod.CODE)
    os.makedirs(TEX, exist_ok=True)
    tex_path = os.path.join(TEX, f'L2_{mod.CODE}_{mod.SLUG}.tex')
    with open(tex_path, 'w', encoding='utf-8') as fh:
        fh.write(doc)
    if make_pdf:
        summary.append('PDF: ' + T.compile_pdf(tex_path))
    return summary


def chain_build(k, p, pid, odir):
    st, body, tf, ans = build_chain_problem(k, p, pid, odir)
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = (f'K={tf.K:<10.4g} corners(Hz)=[{corners}]  Vodc={ans["vodc"]:.3g} amp={ans["amp"]:.3g} '
            f'ph={ans["phase"]:.3g}')
    return st, body, f'p{k:02d}_circuit', line


problems_2a.BUILD = chain_build
problems_2d.BUILD = chain_build
problems_2b.BUILD = chain_build


def slew_build(k, p, pid, odir):
    chain = Chain(p.blocks)
    body, ans = solve_slew(chain, p.SR, p.f, p.nonideal)
    net = chain.net()
    A = None if p.nonideal is None else A_of(p.nonideal)
    exact = solve_exact(net, A)
    verify(net, exact, chain.outs, A_expr=A, where=pid)
    w = 2 * math.pi * p.f
    for o, m in zip(chain.outs, ans['mags']):
        ref = abs(complex(exact[o].subs(s, 1j * w)))
        assert abs(ref - m) < 1e-7 * ref, f'{pid}: |H| mismatch at {o}: {ref} vs {m}'
    base = f'p{k:02d}_circuit'
    chain.draw(os.path.join(odir, base), label_outputs=True)
    if p.nonideal is None:
        model = 'ideal op-amps (except for the slew rate)'
    else:
        A0, fb = p.nonideal
        model = (f'op-amps with open-loop gain $A(s)=\\dfrac{{{T_num(A0)}}}{{1+\\dfrac{{s}}{{2\\pi\\cdot {T_num(fb)}}}}}$')
    n = len(chain.blocks)
    st = (f'In the circuit below ({model}), every op-amp has the slew rate $SR = {T_num(p.SR)}\\,\\mathrm{{V}}/\\mu'
          f'\\mathrm{{s}}$. The input is $V_i(t) = A\\sin(2\\pi\\cdot {T_num(p.f)}\\,t)$. Find the largest '
          f'amplitude $A$ for which no op-amp output is slew-rate limited'
          + (', and say which op-amp output distorts first.' if n > 1 else '.') + ((' ' + p.note) if p.note else ''))
    line = f'Amax={ans["amax"]:.4g} V  limited at {ans["which"]}  gains={[round(m, 4) for m in ans["mags"]]}'
    return st, body, base, line


problems_2e.BUILD = slew_build
def design_build(k, p, pid, odir):
    from common.bode import plot_bode_problem, plot_bode_factors
    from lecture1.build import bode_tf
    from . import design
    tf = bode_tf(p)
    blocks, rows = design.build(tf)
    chain = Chain(blocks)
    base = f'p{k:02d}'
    figs = dict(plot=f'{base}_plot', factors=f'{base}_factors', design=f'{base}_design')
    body, ans = solve_design(tf, p.f_ref, p.vin, figs, chain, rows)
    # check: the designed circuit (independent nodal solve) realizes the target H(s)
    net = chain.net()
    exact = solve_exact(net)
    verify(net, exact, ['o'], where=pid)
    for f in (3.0, 230.0, 4.4e3, 7.1e4):
        w = 2 * math.pi * f
        got, ref = complex(exact['o'].subs(s, 1j * w)), tf.at(w)
        assert abs(got - ref) < 1e-4 * abs(ref), f'{pid}: design misses H at {f} Hz: {got} vs {ref}'
    plot_bode_problem(tf, os.path.join(odir, figs['plot']), p.f_ref)
    plot_bode_factors(tf, os.path.join(odir, figs['factors']))
    chain.draw(os.path.join(odir, figs['design']))
    st = (r'Design a circuit with op-amps, resistors and capacitors whose transfer function $H(s)=\dfrac{V_o(s)}{V_i(s)}$ '
          r'has the straight-line magnitude Bode plot below ($K>0$, no right-half-plane poles or zeros; use the design '
          r'rules stated at the top of this set). Then find the steady-state output $V_o(t)$ for $' + p.vin.tex() + '$.')
    line = f'K={tf.K:.4g} stages={[r["kind"] for r in rows]} amp={ans["amp"]:.3g} ph={ans["phase"]:.3g}'
    return st, body, figs['plot'], line


problems_2c.BUILD = design_build
SETS = [problems_2a, problems_2b, problems_2c, problems_2d, problems_2e]


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
