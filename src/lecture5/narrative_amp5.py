"""Statement and worked solution for set 5E (MOSFET amplifier design, Sample Problem 5)."""
from common.units import num_tex, eng_tex
from common.tf import s
from common import texdoc as T
from .ampdesign5 import design, build, Om, A
from .dc5 import solve_dc5, region_checks, id_sym
from .ac5 import ACView5
from .mosnet import mos_params


def spec_table(p):
    rows = [['Dual supply voltage', f'$+{num_tex(p.vdd)}$\\,V / $-{num_tex(p.vss)}$\\,V']]
    if p.rl:
        rows.append(['Load resistance $R_L$', f'${Om(p.rl)}$'])
    rows += [['0-to-peak output swing $\\hat V_o$', f'$\\ge {num_tex(p.vo)}$\\,V'],
             ['Voltage gain $|A_v|$', f'${num_tex(p.av)}$'],
             ['Input resistance $R_i$', f'$\\ge {Om(p.ri)}$']]
    if p.thd:
        rows.append([f'THD at $\\hat V_o = {num_tex(p.vo)}$\\,V', f'$\\le {num_tex(100 * p.thd)}\\,\\%$'])
    rows.append(['DC voltage drop on $R_3$', f'$\\ge {num_tex(p.vr3)}$\\,V'])
    return T.table(['specification', 'value'], rows, 'll').replace('\\begin{center}', '\\begin{center}\\small')


def statement(p):
    circ, _ = build(p)
    rule = ([f'$I_{{D3}} = {A(p.id3)}$'] if p.id3 else []) + \
           ([f'$V_{{R4}} = {num_tex(p.vr4)}$\\,V'] if p.vr4 else
            ['$V_{R3}$ at its minimum and $V_{R4}$ at the next multiple of 0.5\\,V above its lower bound'])
    if not p.single and p.ratio != 1:
        rule.append(f'$M_4$ has $k_4 = {num_tex(p.ratio)}\\,k_3$')
    st = (r'Design the amplifier below (find all resistor values) for the specifications in the table. Assume '
          + mos_params(circ) + ('; $M_2$, $M_3$ (and $M_4$) have the same $k$' if not p.single else '')
          + r', $r_o = \infty$; capacitors marked $\infty$ are shorts at the signal frequency. Design choices: '
          + '; '.join(rule) + '.' + ((' ' + p.note) if p.note else ''))
    return st, spec_table(p)


def solution(p, figs):
    steps, vals, d = design(p)
    parts = []
    parts.append('\\solstep{1}{Plan}Follow the procedure of Sample Problem 5: '
                 + ('' if p.single else 'size the output current sink for the load current, then the follower; ')
                 + 'budget the supply voltage around the drain swing; get $V_{ov1}$ from the gain '
                 '($|A_v| = g_mR = 2V_R/V_{ov}$), then the resistors; finally the gate divider from the input resistance. '
                 'Distortion of a common-source stage: $HD_2 \\approx \\frac{\\hat v_{gs}}{4V_{ov}}$ '
                 '(from $i_D = \\frac{k}{2}(V_{ov} + v_{gs})^2$).')
    for i, (title, body) in enumerate(steps, 2):
        parts.append(f'\\solstep{{{i}}}{{{title}}}' + body)
    n = len(steps) + 2
    circ, stages = build(p, vals)
    _, V, ID, VG = solve_dc5(circ)
    lines, ok = region_checks(circ, V, ID, VG)
    rows = [[f'${q.tex}$', f'${A(ID[q.name])}$', f'${num_tex(VG[q.name] - q.vt, 3)}$\\,V',
             f'${num_tex(abs(V[q.c] - V[q.e]), 4)}$\\,V'] for q in circ.bjts]
    view = ACView5(circ, ID)
    av = abs(complex(view.exact(circ.out).subs(s, 1j)))
    ri = 1 / (1 / vals['R1'] + 1 / vals['R2'])
    q1 = next(q for q in circ.bjts if q.name == 'M1')
    vov1 = VG['M1'] - q1.vt
    sw = [('$M_1$ leaves saturation', abs(V[q1.c] - V[q1.e]) - vov1)]
    if p.single:
        sw.append(('the drain reaches the supply', d['vr4']))
        gain_after = 1.0
    else:
        q2, q3 = (next(q for q in circ.bjts if q.name == nm) for nm in ('M2', 'M3'))
        gain_after = d['av2']
        sw[0] = ('$M_1$ leaves saturation', (abs(V[q1.c] - V[q1.e]) - vov1) * gain_after)
        sw.append(('$M_3$ leaves saturation', abs(V[q3.c] - V[q3.e]) - (VG['M3'] - q3.vt)))
        sw.append(('$M_2$ leaves saturation', abs(V[q2.c] - V[q2.e]) - (VG['M2'] - q2.vt)))
        sw.append(('$M_3$ cannot sink more current (current clipping)', ID['M3'] * p.rl))
    lim = min(v for _, v in sw)
    hd2 = (p.vo / av) / (4 * vov1)
    ok_all = ok and lim >= p.vo - 1e-9 and ri >= p.ri * (1 - 1e-9) and abs(av / p.av - 1) < 1e-6 \
        and (not p.thd or hd2 <= p.thd)
    items = [f'Gain (exact small-signal analysis of the finished circuit): $|A_v| = {num_tex(av, 4)}$ \\checkmark',
             f'Input resistance $R_1\\|R_2 = {Om(ri)} \\ge {Om(p.ri)}$ \\checkmark',
             'Output swing before clipping: ' + '; '.join(f'{w} at $\\hat V_o = {num_tex(v, 3)}$\\,V' for w, v in sw)
             + f'. The smallest is ${num_tex(lim, 3)}$\\,V $\\ge {num_tex(p.vo)}$\\,V '
             + ('\\checkmark' if lim >= p.vo - 1e-9 else '\\textbf{fails}')]
    if p.thd:
        items.append(f'THD $\\approx HD_2 = \\frac{{\\hat v_{{gs1}}}}{{4V_{{ov1}}}} = \\frac{{{num_tex(p.vo, 3)}/{num_tex(av, 4)}}}'
                     f'{{4\\cdot{num_tex(vov1, 3)}}} = {num_tex(100 * hd2, 2)}\\,\\%$ $\\le {num_tex(100 * p.thd)}\\,\\%$ '
                     + ('\\checkmark' if hd2 <= p.thd else '\\textbf{fails}'))
    parts.append(f'\\solstep{{{n}}}{{Check by analysis}}DC analysis of the finished circuit (as in sets 5A/5B):'
                 + T.table(['', '$I_D$', '$V_{ov}$', '$|V_{DS}|$'], rows, 'cccc')
                 + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + x for x in lines + items)
                 + '\n\\end{itemize}\n')
    order = sorted(vals, key=lambda k: int(k[1:]))
    parts.append(T.figure(figs['designed'], width=r'0.85\linewidth', height='6cm'))
    parts.append('\\begin{ansbox}\n' + ',\\quad '.join(f'${k[0]}_{{{k[1:]}}} = {Om(vals[k])}$' for k in order)
                 + '\n\\end{ansbox}\n')
    return '\n'.join(parts), vals, dict(ok=ok_all, av=av, ri=ri, swing=lim, thd=hd2)
