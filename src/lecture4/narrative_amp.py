"""Worked solutions for set 4E (amplifier design with the procedures of the slides)."""
import math

from common.units import num_tex, eng_tex
from common import texdoc as T
from .ampdesign import design, analyse, swing_and_thd, par2, Om, A, Vv, VT, VSAT, BETA, e12_floor


def spec_table(p):
    rows = [['Supply voltage $V_{CC}$', f'${num_tex(p.vcc)}$\\,V'],
            ['0-to-peak output swing $\\hat V_o$', f'$\\ge {num_tex(p.vo)}$\\,V'],
            ['Voltage gain $|A_v|$', f'${num_tex(p.av)}$'],
            ['Input resistance $R_i$', f'$\\ge {Om(p.ri)}$']]
    if p.rl:
        rows.append(['Load resistance $R_L$', f'${Om(p.rl)}$'])
    if p.thd:
        rows.append([f'THD at $\\hat V_o = {num_tex(p.vo)}$\\,V', f'$\\le {num_tex(100 * p.thd)}\\,\\%$'])
    rows.append(['$\\Delta I_C/I_C$ for $|V_{BE}| = 0.7\\pm0.1$\\,V', '$\\le 10\\,\\%$'])
    return T.table(['specification', 'value'], rows, 'll').replace('\\begin{center}', '\\begin{center}\\small')


def rules_text(p):
    k = len(p.ces)
    r = [f'$N = {p.n}$']
    if p.vo_d != p.vo:
        r.append(f'design for $\\hat V_o = {num_tex(p.vo_d)}$\\,V (margin)')
    r.append(', '.join(f'$V_{{RE{i + 1}}} = {num_tex(v)}$\\,V' for i, v in enumerate(p.vre)))
    for j, a in enumerate(p.av_mid, 2):
        r.append(f'$|A_{{v{j}}}| = {num_tex(a)}$')
    for j, ic in enumerate(p.ic_mid, 2):
        if ic:
            r.append(f'$I_{{C{j}}} = {A(ic)}$')
    if p.rh:
        r.append(f'$R_H = {Om(p.rh)}$')
    if p.ic1:
        r.append(f'$I_{{C1}} = {A(p.ic1)}$')
    return '; '.join(r)


def amp_statement(p):
    st = (r'Design the amplifier below (find all resistor values) for the specifications in the table, insensitive to '
          r'$\beta$ and $V_{BE}$ variations. $\beta = 100$, $V_T = 25$\,mV, $|V_{BE}| = 0.7$\,V, '
          r'$V_{CE,sat} = 0.2$\,V; capacitors marked $\infty$ are shorts at the signal frequency. Use: '
          + rules_text(p) + '. Where a current'
          + (' or $R_H$' if p.follower else '') + r' is not given, take the nearest E12 value on the safe side.')
    if p.note:
        st += ' ' + p.note
    return st, spec_table(p)


def amp_solution(p, figs):
    d = design(p)
    vals = dict(d['vals'])
    role, order = d['role'], d['order']
    k = len(p.ces)
    parts = []
    rmap = ', '.join(f'${n[0]}_{{{n[1:]}}} = {tex}$' for n, tex in order)
    parts.append(
        '\\solstep{1}{Plan}Name the resistors by their job: ' + rmap + '. '
        'Every stage is biased like the one-stage design of the slides: $V_{RE}\\ge1$\\,V ($V_{BE}$-insensitive), the '
        'divider and every collector current much larger than the base current it feeds ($\\beta$-insensitive, '
        'factor $N$), and $V_{RC}$ as large as the swing allows. Small-signal tools: $r_e = V_T/I_C$, CE gain '
        '$|A_v| = \\frac{Z_C}{r_e + R_E\\|R_G}$, follower gain $\\frac{Z_E}{r_e+Z_E}$, base resistance '
        '$(\\beta+1)(r_e + Z_E)$ (the $\\infty$ capacitors put $R_G$ in parallel with $R_E$ for AC only). '
        'Design from the output back to the input, because each stage loads the one before it.')
    for i, (title, body) in enumerate(d['steps'], 2):
        parts.append(f'\\solstep{{{i}}}{{{title}}}' + body)
    nstep = len(d['steps']) + 2
    # ---------------- check by analysis
    circ, V, IC, H, ri = analyse(p, vals)
    s1 = d['st'][0]
    rows = []
    for q in circ.bjts:
        ic_d = d['fol']['ic'] if (p.follower and q.name == f'Q{k + 1}') else d['st'][int(q.name[1:]) - 1]['ic']
        rows.append([f'${q.tex}$', f'${A(ic_d)}$', f'${A(IC[q.name])}$',
                     f'${Vv(abs(V[q.c] - V[q.e]))}$'])
    txt = ('Solve the finished circuit exactly ($\\beta=100$, base currents included) for the DC point, then the '
           'small-signal gain with the exact $r_e$ values:'
           + T.table(['', 'design $I_C$', 'exact $I_C$', 'exact $|V_{CE}|$'], rows, 'cccc'))
    worst = max(abs(IC[q.name] / (d['fol']['ic'] if (p.follower and q.name == f'Q{k + 1}') else d['st'][int(q.name[1:]) - 1]['ic']) - 1) for q in circ.bjts)
    if worst > 0.05:
        txt += ('The exact currents are a little off the design values: $N$ only makes each base current $N$ times '
                'smaller than the current it disturbs, so the base voltages sag slightly, and along direct-coupled '
                'stages each shift is passed on (and amplified) to the next stage. The slides handle this the same '
                'way: simulate, then adjust. ')
    trim = False
    for _ in range(4):
        av0 = abs(H)
        if abs(av0 / p.av - 1) > 0.005:
            trim = True
            rg1 = role['G1']
            re1 = vals[role['E1']]
            r_e = VT / IC['Q1']
            reg_old = par2(re1, vals[rg1])
            reg_new = (r_e + reg_old) * av0 / p.av - r_e
            rg_new = 1 / (1 / reg_new - 1 / re1)
            txt += (f'The exact gain is $|A_v| = {num_tex(av0, 4)}$ instead of ${num_tex(p.av)}$ (the hand design '
                    'ignored $\\alpha$ and the base currents). As the slides suggest, trim $R_{G1}$: the gain is '
                    'proportional to $1/(r_{e1} + R_{E1}\\|R_{G1})$, so scale that sum by '
                    f'${num_tex(av0, 4)}/{num_tex(p.av)}$ (exact $r_{{e1}} = {Om(r_e)}$):'
                    f'\\[R_{{E1}}\\|R_{{G1}} = ({Om(r_e)} + {Om(reg_old)})\\frac{{{num_tex(av0, 4)}}}{{{num_tex(p.av)}}}'
                    f' - {Om(r_e)} = {Om(reg_new)} \\;\\Rightarrow\\; R_{{G1}} = \\mathbf{{{Om(rg_new)}}}\\]')
            vals[rg1] = rg_new
            circ, V, IC, H, ri = analyse(p, vals)
            assert abs(abs(H) / p.av - 1) < 0.003, f'trim failed: {abs(H)}'
            txt += f'Re-analysis: $|A_v| = {num_tex(abs(H), 4)}$ \\checkmark. '
        else:
            txt += (f'The exact gain is $|A_v| = {num_tex(av0, 4)}$, within $0.5\\,\\%$ of the specification '
                    '\\checkmark. ')
        sw, thd = swing_and_thd(p, d, V, IC, H)
        lim = min(v for _, v in sw)
        who = min(sw, key=lambda x: x[1])[0]
        if lim >= p.vo - 1e-9 or who != 'follower':
            break
        rh = role['H']
        lower = e12_floor(vals[rh] * 0.999)
        qf = f'Q{k + 1}'
        txt += (f'\\par The follower would clip at $\\hat V_o = I_{{E{k + 1}}}(R_H\\|R_L) = {A(IC[qf])}\\times'
                f'{Om(par2(vals[rh], p.rl))} = {Vv(lim)} < {num_tex(p.vo)}$\\,V: its exact current is below the design '
                f'value because the base currents shift the DC voltages along the direct-coupled chain. Adjust: '
                f'lower $R_H$ to the next E12 value, $R_H = \\mathbf{{{Om(lower)}}}$ (more follower current), and '
                'analyse again. ')
        vals[rh] = lower
        circ, V, IC, H, ri = analyse(p, vals)
    ok_ri = ri >= p.ri * (1 - 1e-6)
    ok_sw = lim >= p.vo - 1e-9
    items = [f'Input resistance (exact): $R_i = {Om(ri)}$ $\\ge {Om(p.ri)}$ '
             + ('\\checkmark' if ok_ri else '\\textbf{fails}')]
    sw_t = []
    for name, v in sw:
        if name == 'follower':
            sw_t.append(f'follower current clipping at $\\hat V_o = I_{{E{k + 1}}}(R_H\\|R_L) = {Vv(v)}$')
        else:
            sw_t.append(f'${name[0]}_{{{name[1:]}}}$ clips (saturation or cutoff) at $\\hat V_o = {Vv(v)}$')
    items.append('Output swing: ' + '; '.join(sw_t) + f'. The smallest, ${Vv(lim)}$, is $\\ge {num_tex(p.vo)}$\\,V '
                 + ('\\checkmark' if ok_sw else '\\textbf{fails}'))
    total = sum(h for *_, h in thd)
    ok_thd = (not p.thd) or total <= p.thd
    hd = ' + '.join(f'{num_tex(100 * h, 2)}' for *_, h in thd)
    if len(thd) == 1:
        hd = ''
    else:
        hd += '\\,\\% = '
    items.append('Distortion: each CE stage adds $HD_2 \\approx \\frac{\\hat v_b}{4V_T}\\left(\\frac{r_e}{r_e + '
                 'R_E\\|R_G}\\right)^2$ ($\\hat v_b$ = its input amplitude at the specified output; for one stage '
                 'this is the slides\' $\\frac{\\hat V_o V_T |A_v|}{4V_{RC}^2}$): THD $\\approx ' + hd
                 + f'{num_tex(100 * total, 2)}\\,\\%$'
                 + (f' $\\le {num_tex(100 * p.thd)}\\,\\%$ ' + ('\\checkmark' if ok_thd else '\\textbf{fails}')
                    if p.thd else ''))
    vres = [s['vre'] for s in d['st']]
    items.append('$V_{BE}$-insensitive: ' + ', '.join(f'$V_{{RE{i + 1}}} = {num_tex(v)}$\\,V' for i, v in enumerate(vres))
                 + ' $\\ge 1$\\,V \\checkmark')
    txt += '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + x for x in items) + '\n\\end{itemize}\n'
    parts.append(f'\\solstep{{{nstep}}}{{Check by analysis}}' + txt)
    rows = [[f'${n[0]}_{{{n[1:]}}}$ (${tex}$)', f'${Om(vals[n])}$'] for n, tex in order]
    parts.append(T.table(['resistor', 'value'], rows, 'll') + T.figure(figs['designed'], width=r'0.9\linewidth',
                                                                       height='6.5cm'))
    ans = ',\\quad '.join(f'${n[0]}_{{{n[1:]}}} = {Om(vals[n])}$' for n, _ in order)
    parts.append('\\begin{ansbox}\n' + ans + '\n\\end{ansbox}\n')
    rep = dict(ok=ok_ri and ok_sw and ok_thd, av=abs(H), ri=ri, swing=lim, thd=total, trim=trim)
    return '\n'.join(parts), vals, rep
