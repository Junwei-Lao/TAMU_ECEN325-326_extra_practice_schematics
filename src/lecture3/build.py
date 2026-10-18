"""Build all Lecture-3 practice sets.

    python -m lecture3.build [3A 3B 3C 3D] [--no-pdf]      (run from the src/ folder)

Figures go to output/lecture3/<set>/, LaTeX + compiled PDF to src/lecture3/tex/.
"""
import os
import sys

from common import texdoc as T
from common.units import num_tex
from lecture1 import draw as draw1
from .pwl import analyse, numeric_check, lin_tex, interval_tex
from .circuits import from_ladder, from_chain, plot_transfer, plot_time
from .narrative3 import solve_pwl, pipeline_card
from . import problems_3a, problems_3b, problems_3c, problems_3d, rect
from lecture2.chain import Chain

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'output', 'lecture3')
TEX = os.path.join(ROOT, 'src', 'lecture3', 'tex')
LEVELS = {'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard'}


def pwl_statement(p, opamps=False):
    model = ('the constant-voltage-drop model ($V_{D,on}=0.7$\\,V)' if p.model == 'CVD' else
             'the ideal-diode model')
    st = (f'For the circuit below{" (ideal op-amps)" if opamps else ""}, use {model}. Find $V_o$ as a function of '
          f'$V_i$ and sketch $V_o$ versus $V_i$.')
    if p.vin:
        amp, f, fn = p.vin
        st += f' Also sketch $V_o(t)$ for $V_i(t) = {num_tex(amp)}\\{fn}(2\\pi\\cdot {num_tex(f)}\\,t)$.'
    return st + ((' ' + p.note) if p.note else '')


def pwl_finish(pn, p, pid, odir, k, draw_fn, opamps=False):
    base = f'p{k:02d}'
    good, bad = analyse(pn)
    numeric_check(pn, good)
    figs = dict(circuit=f'{base}_circuit', transfer=f'{base}_transfer', time=f'{base}_time')
    draw_fn(os.path.join(odir, figs['circuit']))
    plot_transfer(good, os.path.join(odir, figs['transfer']))
    if p.vin:
        plot_time(good, os.path.join(odir, figs['time']), *p.vin)
    body = solve_pwl(pn, good, bad, figs, vin=p.vin, model=p.model)
    line = ' | '.join(f'{interval_tex(s)}: {lin_tex(s["vo"])}' for s in good)
    return pwl_statement(p, opamps), body, figs['circuit'], line


def ladder_build(k, p, pid, odir):
    circ, pn = from_ladder(p.items, von=0.7 if p.model == 'CVD' else 0)
    return pwl_finish(pn, p, pid, odir, k, lambda b: draw1.draw_full(circ, b))


problems_3a.BUILD = ladder_build


def chain_build(k, p, pid, odir):
    chain = Chain(p.blocks)
    pn = from_chain(chain, von=0.7 if p.model == 'CVD' else 0)
    return pwl_finish(pn, p, pid, odir, k, lambda b: chain.draw(b, label_outputs=len(p.blocks) > 1), opamps=True)


problems_3b.BUILD = chain_build


def rect_build(k, p, pid, odir):
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', wave=f'{base}_wave')
    body, r = rect.solve(p, figs)
    # independent check: simulate the circuit and compare peak / ripple with the formulas
    import numpy as np
    if 'vr' in r:
        w = 2 * np.pi * rect.F
        RC = r['RL'] * r['C']
        t = np.linspace(0, 20 / rect.F, 400000)
        vs = r['vs'] * np.sin(w * t)
        src = np.maximum(vs - r['drop'], 0) if p.topo == 'half' else np.maximum(np.abs(vs) - r['drop'], 0)
        vo = np.empty_like(t)
        vo[0] = 0
        decay = np.exp(-(t[1] - t[0]) / RC)
        for i in range(1, len(t)):
            vo[i] = max(src[i], vo[i - 1] * decay)
        tail = vo[len(t) // 2:]
        sim_vr = tail.max() - tail.min()
        assert abs(tail.max() - r['vp']) < 1e-3 * r['vp'], f'{pid}: peak'
        # the lecture formula assumes the capacitor discharges for a whole T: slightly pessimistic
        assert sim_vr <= r['vr'] * 1.001 and sim_vr > 0.75 * r['vr'], f'{pid}: ripple sim {sim_vr} vs {r["vr"]}'
    rect.draw_rect(p, r, os.path.join(odir, figs['circuit']))
    rect.plot_wave(p, r, os.path.join(odir, figs['wave']))
    keys = ('N', 'vp', 'vr', 'C', 'idav', 'idmax', 'piv')
    line = ' '.join(f'{k_}={r[k_]:.4g}' for k_ in keys if k_ in r)
    return rect.statement(p), body, figs['circuit'], line


problems_3c.BUILD = rect_build


def ss_statement(p, opamp):
    import math as _m
    from .smallsig import SSLadder
    if p.model == 'CVD':
        dcm = 'the constant-voltage-drop model of the diode ($0.7$\\,V)'
    else:
        dcm = (f'the exponential model of the diode ($I_S = {num_tex(p.IS)}$\\,A, $n = {num_tex(p.n)}$, '
               f'$V_T = 25$\\,mV)')
    if opamp:
        head = (f'In the circuit below the op-amp is ideal and the input is $V_{{DC}} + v_i(t)$ with '
                f'$V_{{DC}} = {num_tex(p.vdc)}$\\,V and ${p.vin.tex("v_i(t)")}$.')
    else:
        head = f'In the circuit below, ${p.vin.tex()}$.'
    return (head + f' (a) Using {dcm}, find the DC diode current $I_D$ and the DC output voltage $V_{{o,dc}}$. '
            f'(b) Find the small-signal transfer function $\\frac{{V_o(s)}}{{V_i(s)}}$ (use $n={num_tex(p.n)}$, '
            f'$V_T = 25$\\,mV for $r_d$) and sketch its magnitude Bode plot. (c) Find the total output $V_o(t)$.'
            + ((' ' + p.note) if p.note else ''))


def ss_build(k, p, pid, odir):
    import math as _m
    import numpy as np
    import sympy as sp
    from common.bode import plot_bode
    from common import mna
    from lecture1.ladder import netlist
    from lecture2.netlist import solve_exact, verify, numeric_netlist
    from . import smallsig as SS
    base = f'p{k:02d}'
    figs = dict(circuit=f'{base}_circuit', ac=f'{base}_ac', dc=f'{base}_dc', bode=f'{base}_bode')
    w_in = 2 * _m.pi * p.vin.f
    if isinstance(p, SS.SSLadder):
        parts, tf, vodc, circ_ac, ids, rd = SS.solve_ladder(p, figs)
        circ, pn = from_ladder(p.items)
        draw1.draw_full(circ, os.path.join(odir, figs['circuit']))
        draw1.draw_ac(circ_ac, os.path.join(odir, figs['ac']))
        # AC check against an independent MNA solve of the AC circuit
        nl, names = netlist(circ_ac, 'ac')
        for f in (7.0, 310.0, 4.7e3, 8.8e4):
            ref = mna.solve(nl, 2 * _m.pi * f)[names['o']]
            assert abs(ref - tf.at(2 * _m.pi * f)) < 1e-6 * abs(ref), f'{pid}: AC mismatch at {f} Hz'
        # DC check: the state method on the whole circuit at V_i = 0 (CVD) / diode equation residual (exp)
        if p.model == 'CVD':
            from .pwl import vo_of
            try:
                good, _ = analyse(pn)
            except (AssertionError, ValueError):
                good = None   # e.g. diodes in series: some states are undetermined; skip the sweep check
            if good is not None:
                assert abs(vo_of(good, 0.0) - vodc) < 1e-9, f'{pid}: DC mismatch'
        else:
            idd = list(ids.values())[0]
            vd = p.n * 0.025 * _m.log(idd / p.IS)
            import copy
            pn1 = copy.copy(pn)
            pn1.von = sp.Rational(repr(vd))
            pn1.fixed['i'] = sp.Integer(0)
            from .pwl import solve_state
            res = solve_state(pn1, frozenset(ids))
            assert abs(float(res['I_' + list(ids)[0]]) - idd) < 1e-6 * idd, f'{pid}: iteration not converged'
        vd_amp = None
        sol = mna.solve(nl, w_in)
        for e in nl:
            if e[0] == 'R' and any(abs(e[3] - float(v)) < 1e-12 * float(v) for v in rd.values()):
                vd_amp = abs(sol.get(e[1], 0) - sol.get(e[2], 0)) * p.vin.A
                break
    else:
        parts, tf, vodc, chain_ac, ids, rd = SS.solve_opamp(p, figs)
        chain = Chain(p.blocks)
        chain.draw(os.path.join(odir, figs['circuit']), dc_bias=p.vdc)
        chain_ac.draw(os.path.join(odir, figs['ac']))
        net = chain_ac.net()
        ex = solve_exact(net)
        verify(net, ex, ['o'], where=pid)
        for f in (7.0, 310.0, 4.7e3, 8.8e4):
            jw = 2j * _m.pi * f
            assert abs(complex(ex['o'].subs(sp.Symbol('s'), jw)) - tf.at(2 * _m.pi * f)) < 1e-6 * abs(tf.at(2 * _m.pi * f))
        nl, ids_n, _ = numeric_netlist(net, 'ac')
        for o in net.opamps:
            nl.append(('O', ids_n[o.plus] if o.plus in ids_n else 0, ids_n[o.minus], ids_n[o.out]))
        sol = mna.solve(nl, w_in)
        vd_amp = None
        for e in nl:
            if e[0] == 'R' and any(abs(e[3] - float(v)) < 1e-12 * float(v) for v in rd.values()):
                vd_amp = abs(sol.get(e[1], 0) - sol.get(e[2], 0)) * p.vin.A
                break
    plot_bode(tf, os.path.join(odir, figs['bode']), f_in=p.vin.f)
    body, amp, ph = SS.finish(parts, tf, vodc, p.vin, figs, vd_amp, p.n)
    line = (f'ID={[f"{v * 1e3:.4g}mA" for v in ids.values()]} rd={[f"{v:.4g}" for v in rd.values()]} '
            f'Vodc={vodc:.4g} K={tf.K:.4g} amp={amp:.3g} ph={ph:.3g} vd={vd_amp and f"{vd_amp:.3g}"}')
    return ss_statement(p, not isinstance(p, SS.SSLadder)), body, figs['circuit'], line


problems_3d.BUILD = ss_build
SETS = [problems_3a, problems_3b, problems_3c, problems_3d]


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
        figtex = T.figure(fig, width=r'\linewidth', height='5.6cm') if fig else ''
        probs.append(f'\\begin{{probbox}}{{Problem {pid} \\hfill {LEVELS[p.level]}}}\n{st}\n' + figtex
                     + '\\end{probbox}\n')
        sols.append(f'\\newpage\n\\subsection*{{Solution {pid} \\hfill {LEVELS[p.level]}}}\n'
                    + (T.figure(fig, width=r'0.9\linewidth', height='5cm') if fig else '') + body)
        summary.append(f'{pid:6s} {p.level:6s} {line}')
    if errors:
        raise SystemExit('\n'.join(errors))
    body = (mod.INTRO + '\n' + pipeline_card()
            + '\n\\section*{Problems}\n' + '\n'.join(probs)
            + '\n\\newpage\n\\section*{Solutions}\n'
            + 'Every solution follows the steps of the Lecture-3 pipeline card.\n' + '\n'.join(sols))
    gp = f'../../../output/lecture3/{mod.CODE}_{mod.SLUG}/'
    doc = T.document(mod.TITLE, 'ECEN 325 --- Lecture 3 (Diodes) practice set', gp, body)
    T.check_balanced(doc, mod.CODE)
    os.makedirs(TEX, exist_ok=True)
    tex_path = os.path.join(TEX, f'L3_{mod.CODE}_{mod.SLUG}.tex')
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
