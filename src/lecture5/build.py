"""Build all Lecture-5 practice sets.

    python -m lecture5.build [5A 5B 5C 5D 5E 5F] [--no-pdf]      (run from the src/ folder)

Figures go to output/lecture5/<set>/, LaTeX + compiled PDF to src/lecture5/tex/.
"""
import os
import sys

from lecture4.build import build_set as _build_set
from .narrative5 import dc_solution, pipeline_card
from .mosnet import mos_params
from .narrative_design5 import design_solution, design_statement
from . import problems_5a, problems_5b, problems_5c, problems_5d, problems_5e, problems_5f

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'output', 'lecture5')
TEX = os.path.join(ROOT, 'src', 'lecture5', 'tex')


def fs_of(circ):
    return 11 + max(0, len(circ.cols) - 4)


def dc_build(k, p, pid, odir):
    circ = p.build()
    base = f'p{k:02d}_circuit'
    body, V, ID, ok, err = dc_solution(circ)
    assert ok, f'{pid}: a transistor is not active'
    assert err < 1e-6, f'{pid}: hand and exact solutions differ ({err})'
    circ.draw(os.path.join(odir, base), fontsize=fs_of(circ))
    st = ('For the circuit below, find the DC drain currents $I_D$ of all transistors and verify their operating '
          'modes. Assume ' + mos_params(circ) + '.' + ((' ' + p.note) if p.note else ''))
    line = ' '.join(f'{n}={v * 1e3:.4g}mA' for n, v in ID.items())
    return st, body, base, line


problems_5a.BUILD = dc_build
problems_5b.BUILD = dc_build


def design_build(k, p, pid, odir):
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', designed=f'{base}_designed')
    circ0 = p.build(None)
    body, vals, circ, ok = design_solution(p, figs)
    assert ok, f'{pid}: designed circuit has a transistor out of the active region'
    circ0.draw(os.path.join(odir, figs['circuit']), fontsize=fs_of(circ0), show_values=False)
    circ.draw(os.path.join(odir, figs['designed']), fontsize=fs_of(circ))
    line = ' '.join(f'{n}={v:.4g}' for n, v in vals.items())
    return design_statement(p, circ0), body, figs['circuit'], line


problems_5c.BUILD = design_build


def ac_build(k, p, pid, odir):
    import math
    from common.bode import plot_bode
    from common.tf import s
    from .dc5 import solve_dc5, region_checks, I_
    from .narrative5 import ac_solution
    circ, stages = p.build()
    _, V, ID, VG = solve_dc5(circ)
    _, ok = region_checks(circ, V, ID, VG)
    assert ok, f'{pid}: DC point not all active'
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', bode=f'{base}_bode')
    body, tf, H, view, ans = ac_solution(circ, ID, stages, p.vin, figs)
    ex = view.exact(circ.out)
    for f in (3.0, 120.0, 2.3e3, 4.1e4, 6.6e5):
        w = 2 * math.pi * f
        ref = complex(ex.subs(s, 1j * w))
        assert abs(ref - tf.at(w)) < 1e-6 * abs(ref), f'{pid}: AC mismatch at {f} Hz: {ref} vs {tf.at(w)}'
    circ.draw(os.path.join(odir, figs['circuit']), fontsize=fs_of(circ))
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)
    cur = ', '.join(f'$I_{{D{st.q.name[1:]}}} = {I_(ID[st.q.name])}$' for st in stages)
    st = (r'For the amplifier below, find the small-signal transfer function $H(s)=\dfrac{V_o(s)}{V_i(s)}$ and sketch '
          r'its magnitude Bode plot. Also find the steady-state output $V_o(t)$ for $' + p.vin.tex() + r'$. Assume '
          + mos_params(circ) + r', $r_o = \infty$; the DC drain currents are ' + cur + '.'
          + ((' ' + p.note) if p.note else ''))
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = f'K={tf.K:.4g} corners(Hz)=[{corners}] amp={ans["amp"]:.3g} ph={ans["phase"]:.3g}'
    return st, body, figs['circuit'], line


problems_5d.BUILD = ac_build


def amp_build(k, p, pid, odir):
    from .ampdesign5 import build as amp_circuit
    from .narrative_amp5 import solution, statement
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', designed=f'{base}_designed')
    body, vals, rep = solution(p, figs)
    assert rep['ok'], f'{pid}: design fails its checks {rep}'
    c0, _ = amp_circuit(p)
    c1, _ = amp_circuit(p, vals)
    c0.draw(os.path.join(odir, figs['circuit']), fontsize=fs_of(c0), show_values=False)
    c1.draw(os.path.join(odir, figs['designed']), fontsize=fs_of(c1))
    line = ' '.join(f'{n}={v:.4g}' for n, v in sorted(vals.items(), key=lambda kv: int(kv[0][1:])))
    line += f'  Av={rep["av"]:.4g} swing={rep["swing"]:.3g} thd={100 * rep["thd"]:.2g}%'
    st, side = statement(p)
    return ((st, side) if p.single else st + side), body, figs['circuit'], line


problems_5e.BUILD = amp_build


def thev_build(k, p, pid, odir):
    import math
    from common.bode import plot_bode
    from common.tf import s
    from .narrative_thev5 import dc_solution, ac_solution, statement_dc, statement_ac
    from .draw_thev5 import draw5f
    base = f'p{k:02d}'
    if p.ac is None:
        figs = dict(circuit=f'{base}_circuit', equivalent=f'{base}_equivalent')
        body, circ, ID, err, eq = dc_solution(p, figs)
        assert err < 1e-6, f'{pid}: Thevenin result differs from the full nodal solve ({err})'
        draw5f(p, os.path.join(odir, figs['circuit']))
        eq.draw(os.path.join(odir, figs['equivalent']), fontsize=12)
        line = 'DC ' + ' '.join(f'{n}={v * 1e3:.4g}mA' for n, v in ID.items())
        return statement_dc(p, circ), body, figs['circuit'], line
    figs = dict(circuit=f'{base}_circuit', bode=f'{base}_bode')
    body, circ, tf, view, ID, ans, stages = ac_solution(p, figs)
    ex = view.exact(circ.out)
    for f in (3.0, 120.0, 2.3e3, 4.1e4, 6.6e5):
        w = 2 * math.pi * f
        ref = complex(ex.subs(s, 1j * w))
        assert abs(ref - tf.at(w)) < 1e-6 * abs(ref), f'{pid}: AC mismatch at {f} Hz: {ref} vs {tf.at(w)}'
    draw5f(p, os.path.join(odir, figs['circuit']))
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)
    corners = ', '.join(f'{w / 2 / math.pi:.4g}' for w, _ in tf.corners())
    line = f'AC K={tf.K:.4g} corners(Hz)=[{corners}] amp={ans["amp"]:.3g}'
    return statement_ac(p, circ, ID, stages), body, figs['circuit'], line


problems_5f.BUILD = thev_build
SETS = [problems_5a, problems_5b, problems_5c, problems_5d, problems_5e, problems_5f]


def build_set(mod, make_pdf=True):
    return _build_set(mod, make_pdf, lec=5, subtitle='Lecture 5 (MOS Field-Effect Transistors)', card=pipeline_card,
                      out=OUT, tex=TEX)


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
