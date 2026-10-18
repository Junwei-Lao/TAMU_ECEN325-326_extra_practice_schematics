"""Worked solutions for the Lecture-4 design sets (4C bias design, 4E amplifier design)."""
from common.units import num_tex, eng_tex
from common import texdoc as T
from .dc import solve_dc, checks, exact_dc, V_, I_
from .design import design_dc, supply_current, sensitivity, par


def Om(x):
    return eng_tex(x, '\\Omega')


def spec_rows(p, circ):
    rows = [[f'$I_{{C{n[1:]}}}$', f'${I_(v)}$'] for n, v in p.ic.items()]
    rows += [[f'${circ.disp(n)}$', f'${V_(v)}$'] for n, v in p.given.items()]
    if p.vce_min > 0.2:
        rows.append(['$|V_{CE}|$ (all transistors)', f'$\\ge {num_tex(p.vce_min)}$\\,V'])
    if p.idc_max:
        rows.append(['$I_{dc}$ (supply current)', f'$\\le {I_(p.idc_max)}$'])
    return rows


def dc_design_statement(p, circ):
    extra = [c.stmt for c in p.choices if c.stmt]
    rule = any(c.kind == 'VR' and not c.stmt for c in p.choices)
    st = (r'Design the circuit below (find all resistor values) for the specifications in the table, such that every '
          r'$I_B$ is negligible and $|V_{BE}| = 0.7 \pm 0.1$\,V changes every $I_C$ by less than 10\,\%. '
          r'$\beta = 100$.')
    if rule or extra:
        st += ' Where the specifications leave a choice, use ' + ', '.join(
            (['the smallest emitter-resistor voltage the $V_{BE}$ rule allows'] if rule else []) + extra) + '.'
    if p.note:
        st += ' ' + p.note
    return st, T.table(['specification', 'value'], spec_rows(p, circ), 'll').replace('\\begin{center}', '\\begin{center}\\small')


def dc_design_solution(p, figs):
    """Returns (body, values, circuit with the designed values, report dict)."""
    circ0 = p.build(None)
    steps, val, Vd, ICd, Ir = design_dc(circ0, p.ic, p.given, p.choices)
    circ = p.build(val)
    _, V, IC = solve_dc(circ)
    for n, i in ICd.items():
        assert abs(IC[n] - i) < 1e-6 * i, f'design re-analysis mismatch {n}: {IC[n]} vs {i}'
    parts = []
    parts.append(
        '\\solstep{1}{Rules}With $I_B\\approx0$ and every transistor active ($|V_{BE}|=0.7$\\,V, $I_C\\approx I_E$), a '
        'resistor is known as soon as the voltages at both of its ends and the current through it are known: '
        '$R = \\Delta V / I$. The specifications give the currents and some node voltages; the remaining freedom is '
        'removed with two rules:'
        '\\begin{itemize}[leftmargin=*,itemsep=1pt]\n'
        '\\item $V_{BE}$-insensitive: the voltage across the resistor that sets an emitter current must be at least '
        '$1$\\,V (then $\\pm0.1$\\,V of $V_{BE}$ changes $I_C$ by at most $10\\,\\%$);\n'
        '\\item $\\beta$-insensitive: a divider current must be much larger ($\\ge 10\\times$) than the base current it '
        'feeds, and a collector current that drives a base must be much larger than that base current.\n'
        '\\end{itemize}\n'
        'Work from the nodes that are already fixed towards the unknown ones.')
    parts.append('\\solstep{2}{Design, node by node}'
                 + '\\begin{enumerate}[leftmargin=*,itemsep=3pt]\n' + '\n'.join('\\item ' + s for s in steps)
                 + '\n\\end{enumerate}\n')
    rows = [[f'${el.tex}$', f'${Om(val[el.name])}$'] for el in sorted(
        [e for e in circ0.elements() if e.kind == 'R'], key=lambda e: int(e.name[1:]))]
    parts.append('\\solstep{3}{Designed circuit}'
                 + T.table(['resistor', 'value'], rows, 'cc')
                 + T.figure(figs['designed'], width=r'0.85\linewidth', height='6cm'))
    lines, ok = checks(circ, V, IC)
    lines = [l for l in lines if not l.startswith('$V_{')]
    for q in circ.bjts:
        vce = (V[q.c] - V[q.e]) * q.s
        nm = 'CE' if q.kind == 'npn' else 'EC'
        a, b = (q.c, q.e) if q.kind == 'npn' else (q.e, q.c)
        if q.diode:
            lines.append(f'${q.tex}$ is diode-connected: $V_{{{nm}{q.name[1:]}}} = |V_{{BE}}| = 0.7$\\,V, always active '
                         '(the $|V_{CE}|$ specification is meant for the other transistors) \\checkmark')
            continue
        good = vce >= p.vce_min - 1e-9
        ok &= good
        lines.append(f'$V_{{{nm}{q.name[1:]}}} = {circ.disp(a)} - {circ.disp(b)} = {num_tex(V[a], 4)} - '
                     f'{par(V[b])} = {V_(vce)} \\ge {num_tex(p.vce_min)}$\\,V '
                     + ('\\checkmark' if good else '\\textbf{fails}'))
    if p.idc_max:
        top, ps = supply_current(circ, V, IC, Ir)
        idc = sum(i for i, _ in ps)
        good = idc <= p.idc_max * (1 + 1e-9)
        ok &= good
        lines.append(f'$I_{{dc}} = {" + ".join(sym for _, sym in ps)} = {" + ".join(I_(i) for i, _ in ps)} = {I_(idc)} '
                     f'\\le {I_(p.idc_max)}$ ' + ('\\checkmark' if good else '\\textbf{fails}'))
    sens = sensitivity(circ)
    srows, worst_dev, worst_var = [], 0.0, 0.0
    for q in circ.bjts:
        ix, lo, hi = sens[q.name]
        var = max(abs(lo - ix), abs(hi - ix)) / ICd[q.name]
        dev = abs(ix - ICd[q.name]) / ICd[q.name]
        worst_dev, worst_var = max(worst_dev, dev), max(worst_var, var)
        srows.append([f'${q.tex}$', f'${I_(ICd[q.name])}$', f'${I_(ix)}$', f'${I_(lo)}$', f'${I_(hi)}$',
                      f'${num_tex(100 * var, 2)}\\,\\%$'])
    parts.append('\\solstep{4}{Check the design}'
                 + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + l for l in lines)
                 + '\n\\end{itemize}\n'
                 + 'Finally the designed circuit is solved exactly ($\\beta=100$, base currents included), once with '
                   '$|V_{BE}|=0.7$\\,V and once with each transistor\'s $|V_{BE}|$ changed to $0.6$ and $0.8$\\,V:'
                 + T.table(['', 'target $I_C$', 'exact $I_C$', '$|V_{BE}|=0.6$', '$|V_{BE}|=0.8$', 'max change'],
                           srows, 'cccccc')
                 + 'A $\\pm0.1$\\,V change of $V_{BE}$ moves no current by more than about $10\\,\\%$ of its design '
                   'value ($V_{BE}$-insensitive), and the exact currents are close to the targets ($I_B$ negligible).'
                 + ('' if worst_dev < 0.06 else
                    ' The exact currents drift further from the targets along a chain of direct-coupled stages: each '
                    'base current and each $I_C = \\alpha I_E$ slightly shifts the collector voltage that biases the next '
                    'stage, and with only $\\approx1$\\,V across the next emitter resistor that shift is amplified. This '
                    'is the normal accuracy of a hand design with $I_B\\approx0$; a larger emitter-resistor voltage in '
                    'the later stages reduces the drift.'))
    ans = ',\\quad '.join(f'${el}$' for el in (f'{r[0][1:-1]} = {r[1][1:-1]}' for r in rows))
    parts.append('\\begin{ansbox}\n' + ans + '\n\\end{ansbox}\n')
    return '\n'.join(parts), val, circ, dict(ok=ok, dev=worst_dev, var=worst_var)
