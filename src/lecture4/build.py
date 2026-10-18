"""Build all Lecture-4 practice sets.

    python -m lecture4.build [4A 4B 4C 4D 4E] [--no-pdf]      (run from the src/ folder)

Figures go to output/lecture4/<set>/, LaTeX + compiled PDF to src/lecture4/tex/.
"""
import math
import os
import sys

from common import texdoc as T
from .narrative4 import dc_solution, ac_solution, pipeline_card
from .narrative_design import dc_design_solution, dc_design_statement
from .narrative_amp import amp_solution, amp_statement
from . import problems_4a, problems_4b, problems_4c, problems_4d, problems_4e

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'output', 'lecture4')
TEX = os.path.join(ROOT, 'src', 'lecture4', 'tex')
LEVELS = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


def dc_build(k, p, pid, odir):
    circ = p.build()
    base = f'p{k:02d}_circuit'
    body, V, IC, ICx, ok = dc_solution(circ)
    assert ok, f'{pid}: assumptions fail'
    err = max(abs(IC[n] - ICx[n]) / ICx[n] for n in IC)
    assert err < 0.2, f'{pid}: I_B ~ 0 too inaccurate ({100 * err:.1f}%)'
    circ.draw(os.path.join(odir, base), fontsize=11 + max(0, len(circ.cols) - 4))
    st = ('For the circuit below, find the DC collector currents $I_C$ of all transistors and verify all assumptions, '
          'including the operating region of every transistor. Assume $\\beta = 100$.' + ((' ' + p.note) if p.note else ''))
    line = ' '.join(f'{n}={v * 1e3:.3f}mA' for n, v in IC.items()) + f'  exact-err={100 * err:.1f}%'
    return st, body, base, line


problems_4a.BUILD = dc_build
problems_4b.BUILD = dc_build


def ac_build(k, p, pid, odir):
    import sympy as sp
    from common.bode import plot_bode
    from common.tf import s
    from common.units import eng_tex
    from .dc import solve_dc
    circ, stages = p.build()
    _, V, IC = solve_dc(circ)
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', bode=f'{base}_bode')
    body, tf, H, view, ans = ac_solution(circ, IC, stages, p.vin, figs)
    ex = view.exact(circ.out)
    for f in (3.0, 120.0, 2.3e3, 4.1e4, 6.6e5):
        w = 2 * math.pi * f
        ref = complex(ex.subs(s, 1j * w))
        assert abs(ref - tf.at(w)) < 1e-6 * abs(ref), f'{pid}: AC mismatch at {f} Hz: {ref} vs {tf.at(w)}'
    circ.draw(os.path.join(odir, figs['circuit']), fontsize=11 + max(0, len(circ.cols) - 4))
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)
    cur = ', '.join(f'$I_{{C{q.q.name[1:]}}} = {eng_tex(IC[q.q.name], chr(92) + "mathrm{A}")}$' for q in stages)
    st = (r'For the amplifier below, find the small-signal transfer function $H(s)=\dfrac{V_o(s)}{V_i(s)}$ and sketch '
          r'its magnitude Bode plot. Also find the steady-state output $V_o(t)$ for $' + p.vin.tex() + r'$. '
          r'$\beta = 100$, $V_T = 25$\,mV; the DC collector currents are ' + cur + '.'
          + ((' ' + p.note) if p.note else ''))
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = f'K={tf.K:.4g} corners(Hz)=[{corners}] amp={ans["amp"]:.3g} ph={ans["phase"]:.3g}'
    return st, body, figs['circuit'], line


problems_4d.BUILD = ac_build


def dc_design_build(k, p, pid, odir):
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', designed=f'{base}_designed')
    circ0 = p.build(None)
    body, val, circ, rep = dc_design_solution(p, figs)
    assert rep['ok'], f'{pid}: design fails its own checks'
    assert rep['dev'] < 0.2, f'{pid}: exact I_C off by {100 * rep["dev"]:.1f}%'
    assert rep['var'] < 0.105, f'{pid}: V_BE sensitivity {100 * rep["var"]:.1f}%'
    fs = 11 + max(0, len(circ.cols) - 4)
    circ0.draw(os.path.join(odir, figs['circuit']), fontsize=fs, show_values=False)
    circ.draw(os.path.join(odir, figs['designed']), fontsize=fs)
    st = dc_design_statement(p, circ0)
    line = ' '.join(f'{n}={v:.4g}' for n, v in sorted(val.items(), key=lambda kv: int(kv[0][1:])))
    line += f'  dev={100 * rep["dev"]:.1f}% var={100 * rep["var"]:.1f}%'
    return st, body, figs['circuit'], line


problems_4c.BUILD = dc_design_build


def amp_design_build(k, p, pid, odir):
    from .ampdesign import build as amp_circuit
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', designed=f'{base}_designed')
    body, vals, rep = amp_solution(p, figs)
    assert rep['ok'], f'{pid}: design fails its checks {rep}'
    assert abs(rep['av'] / p.av - 1) < 0.006, f'{pid}: gain {rep["av"]}'
    fs = 11 + max(0, len(p.chain) - 2)
    amp_circuit(p).draw(os.path.join(odir, figs['circuit']), fontsize=fs, show_values=False)
    amp_circuit(p, vals).draw(os.path.join(odir, figs['designed']), fontsize=fs)
    line = ' '.join(f'{n}={v:.4g}' for n, v in sorted(vals.items(), key=lambda kv: int(kv[0][1:])))
    line += f'  Av={rep["av"]:.4g} Ri={rep["ri"]:.4g} swing={rep["swing"]:.3g} thd={100 * rep["thd"]:.2g}%'
    st, side = amp_statement(p)
    return ((st, side) if len(p.chain) <= 2 else st + side), body, figs['circuit'], line


problems_4e.BUILD = amp_design_build
SETS = [problems_4a, problems_4b, problems_4c, problems_4d, problems_4e]


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
        if isinstance(st, tuple):     # (text, side table): circuit and specification table side by side
            st, side = st
            figtex = ('\n\\smallskip\\noindent\\begin{minipage}{0.6\\linewidth}\\centering\\includegraphics[width='
                      f'\\linewidth,height={getattr(mod, "FIG_H", "7cm")},keepaspectratio]{{{fig}}}\\end{{minipage}}'
                      '\\hfill\\begin{minipage}{0.38\\linewidth}' + side + '\\end{minipage}\n')
        else:
            figtex = T.figure(fig, width=r'\linewidth', height=getattr(mod, 'FIG_H', '7cm'))
        probs.append(f'\\begin{{probbox}}{{Problem {pid} \\hfill {LEVELS[p.level]}}}\n{st}\n'
                     + figtex + '\\end{probbox}\n')
        sols.append(('\\newpage\n' if sols else '') + f'\\subsection*{{Solution {pid} \\hfill {LEVELS[p.level]}}}\n'
                    + T.figure(fig, width=r'0.9\linewidth', height='6cm') + body)
        summary.append(f'{pid:6s} {p.level:6s} {line}')
    if errors:
        raise SystemExit('\n'.join(errors))
    body = (mod.INTRO + '\n' + pipeline_card()
            + '\n\\section*{Problems}\n' + '\n'.join(probs)
            + '\n\\newpage\n\\section*{Solutions}\n'
            + 'Every solution follows the steps of the Lecture-4 pipeline card.\n' + '\n'.join(sols))
    gp = f'../../../output/lecture4/{mod.CODE}_{mod.SLUG}/'
    doc = T.document(mod.TITLE, 'ECEN 325 --- Lecture 4 (Bipolar Junction Transistors) practice set', gp, body)
    T.check_balanced(doc, mod.CODE)
    os.makedirs(TEX, exist_ok=True)
    tex_path = os.path.join(TEX, f'L4_{mod.CODE}_{mod.SLUG}.tex')
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
