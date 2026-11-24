"""Statement and worked solution for set 5C (MOSFET bias design)."""
from common.units import num_tex, eng_tex
from common import texdoc as T
from .mosnet import mos_params
from .design5 import design5
from .dc5 import solve_dc5, region_checks, I_, V_, id_sym


def spec_rows(p, circ):
    rows = [[f'$I_{{D{n[1:]}}}$', f'${I_(v)}$'] for n, v in p.idt.items()]
    rows += [[f'${circ.disp(n)}$', f'${V_(v)}$'] for n, v in p.given.items()]
    return rows


def design_statement(p, circ):
    sized = [q for q in circ.bjts if q.size_me]
    st = ('Design the circuit below: find all resistor values'
          + (' and the width $W$ of every transistor marked ``?\'\' (keep its length $L$)' if sized else '')
          + ' so that the specifications in the table are met with every transistor active. Assume '
          + mos_params(circ) + '.')
    ch = [c.stmt for c in p.choices if c.stmt]
    if ch:
        st += ' Design choices: ' + '; '.join(ch) + '.'
    if p.note:
        st += ' ' + p.note
    return st, T.table(['specification', 'value'], spec_rows(p, circ), 'll').replace('\\begin{center}',
                                                                                        '\\begin{center}\\small')


def design_solution(p, figs):
    circ0 = p.build(None)
    steps, vals, Vd, IDd = design5(circ0, p.idt, p.given, p.choices)
    circ = p.build(vals)
    _, V, ID, VG = solve_dc5(circ)
    for n, i in p.idt.items():
        assert abs(ID[n] - i) < 1e-6 * i, f'{n}: analysis {ID[n]} vs target {i}'
    for n, v in p.given.items():
        assert abs(V[n] - v) < 1e-6, f'{n}: analysis {V[n]} vs target {v}'
    parts = []
    parts.append('\\solstep{1}{Rules}Run the DC analysis backwards. A target current fixes the gate--source voltage '
                 '(tool T1): $V_{ov} = \\sqrt{2I_D/k}$, $|V_{GS}| = |V_t| + V_{ov}$. A resistor is known as soon as '
                 'the voltages at both of its ends and its current are known: $R = \\Delta V/I$ ($I_G = 0$, so gate '
                 'dividers carry only their own current). A mirror output copies the reference scaled by $W/L$ '
                 '(tool T3). Work from the nodes that are already fixed towards the unknown ones.')
    parts.append('\\solstep{2}{Design, node by node}'
                 + '\\begin{enumerate}[leftmargin=*,itemsep=3pt]\n' + '\n'.join('\\item ' + s for s in steps)
                 + '\n\\end{enumerate}\n')
    rows = []
    for el in sorted([e for e in circ0.elements() if e.kind == 'R'], key=lambda e: int(e.name[1:])):
        rows.append([f'${el.tex}$', f'${eng_tex(vals[el.name], chr(92) + "Omega")}$'])
    for q in circ0.bjts:
        if q.size_me:
            rows.append([f'$(W/L)_{{{q.name[1:]}}}$', f'${num_tex(vals[q.name], 4)}/{q.wl[1]:g}$'])
    parts.append('\\solstep{3}{Designed circuit}' + T.table(['element', 'value'], rows, 'cc')
                 + T.figure(figs['designed'], width=r'0.85\linewidth', height='6cm'))
    lines, ok = region_checks(circ, V, ID, VG)
    chk = [[f'${q.tex}$', f'${I_(p.idt[q.name])}$' if q.name in p.idt else '---', f'${I_(ID[q.name])}$']
           for q in circ.bjts]
    parts.append('\\solstep{4}{Check by analysis}Analyse the finished circuit as in set 5A (one quadratic per '
                 'transistor, mirrors by $W/L$):' + T.table(['', 'target $I_D$', 'analysis $I_D$'], chk, 'ccc')
                 + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + l for l in lines)
                 + '\n\\end{itemize}\n'
                 + 'Every specified current and voltage is reproduced exactly ($I_G = 0$: nothing was neglected).')
    ans = ',\\quad '.join(f'${r[0][1:-1]} = {r[1][1:-1]}$' for r in rows)
    parts.append('\\begin{ansbox}\n' + ans + '\n\\end{ansbox}\n')
    return '\n'.join(parts), vals, circ, ok
