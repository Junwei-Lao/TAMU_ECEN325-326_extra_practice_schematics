"""Worked solutions for Lecture 3 (diodes): transfer characteristics, rectifiers, small-signal analysis."""
import math

import sympy as sp

from common.units import num_tex, sig, eng_tex
from common import texdoc as T
from .pwl import X, lin_tex, state_section, interval_tex, dname, merged


def pipeline_card():
    return r"""
\begin{cardbox}{The Lecture-3 pipeline (use it for every problem in this lecture)}
\textbf{Tools --- this is all the theory you need (plus the Lecture-1/2 tools):}
\begin{enumerate}[label=\textbf{T\arabic*},leftmargin=2.2em,itemsep=1pt]
\item \emph{Diode models.} Ideal: OFF $\Leftrightarrow V_D<0$ (open), ON $\Leftrightarrow I_D>0$ ($V_D=0$).
      Constant-voltage-drop (CVD): OFF $\Leftrightarrow V_D<0.7$\,V (open), ON $\Leftrightarrow I_D>0$ ($V_D=0.7$\,V source).
      Exponential: $I_D = I_S e^{V_D/nV_T}$, i.e. $V_D = nV_T\ln(I_D/I_S)$, $V_T\approx 25$\,mV.
\item \emph{State method.} Assume ON/OFF for every diode, solve the now-linear circuit (KCL, Lecture 2), then check
      the assumptions; each check is a condition on $V_i$. The valid states tile the $V_i$ axis.
\item \emph{Small signal.} Around a DC point $I_D$ the diode is a resistor $r_d = \frac{nV_T}{I_D}$
      (valid while $|v_d|\ll nV_T$). Capacitors: open at DC; $\frac{1}{sC}$ in AC; DC supplies are AC ground.
\item \emph{Rectifier with a filter capacitor} ($f=60$\,Hz, $T = \frac{1}{f}$ half-wave, $\frac{1}{2f}$ full-wave):
      peak $V_p=\hat V_S - (\text{diode drops in the path})$; ripple $V_r \approx V_p\frac{T}{RC}$;
      $I_{D,av} \approx I_L\left(1+\pi\sqrt{2V_p/V_r}\right)$, $I_{D,max}\approx I_L\left(1+2\pi\sqrt{2V_p/V_r}\right)$;
      PIV $=$ the largest reverse voltage a diode sees.
\end{enumerate}
\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{Pick the model} stated in the problem.
\item \emph{Transfer characteristic:} for each ON/OFF state: replace the diodes, solve, check $\Rightarrow$ range of $V_i$;
      then join the pieces (they must meet at the breakpoints) and sketch.
\item \emph{Small signal:} DC operating point first, then $r_d$, then the AC circuit exactly as in Lectures 1--2,
      then add DC and AC.
\item \emph{Rectifiers:} peak $\to$ ripple (or $C$ for a given ripple) $\to$ diode currents $\to$ PIV $\to$ transformer ratio.
\end{enumerate}
\end{cardbox}
"""


def node_names(pn):
    """Describe every named node that is not marked on the schematic, by the elements meeting there."""
    desc = []
    opnodes = {n for o in pn.opamps for n in o[1:]}
    for n in sorted(pn.nodes() - set(pn.fixed), key=lambda n: pn.label.get(n, n)):
        lbl = pn.label.get(n, n)
        if lbl == 'o' or n in opnodes and lbl in ('+', '-', 'u'):
            if lbl in ('+', '-'):
                desc.append(f'${pn.disp(n)}$ = the op-amp\'s {"$+$" if lbl == "+" else "$-$"} input')
            continue
        els = sorted({el.tex for el, a, b in pn.br if n in (a, b)})
        if n in opnodes:
            els.append('the op-amp output')
        desc.append(f'${pn.disp(n)}$ = node joining ${", ".join(els)}$' if els else '')
    desc = [d for d in desc if d]
    if not desc:
        return ''
    return ' Node names used below: ' + '; '.join(desc) + '.'


def cases_tex(good):
    rows = [f'{lin_tex(s["vo"])} & {interval_tex(s)}' for s in merged(good)]
    return 'V_o = \\begin{cases} ' + ' \\\\ '.join(rows) + ' \\end{cases}'


def _contradiction(pn, st):
    if st.get('conflict'):
        return ('the ON diodes would have to hold the same node at two different voltages at once, which no circuit '
                'can do')
    parts = []
    for c in st['conds']:
        d = dname(c['d'])
        what = f'$V_{{{d}}}<{num_tex(float(pn.von))}$' if c['kind'] == 'off' else f'$I_{{{d}}}>0$'
        if 'bound' in c:
            parts.append(f'{what} needs $V_i {"<" if c["below"] else ">"} {num_tex(float(c["bound"]), 4)}$')
        else:
            parts.append(f'{what} is {"always" if c["always"] else "never"} true')
    return '; '.join(parts)


def solve_pwl(pn, good, bad, figs, vin=None, model='CVD', what='V_o'):
    names = [el.name for el, _, _ in pn.diodes()]
    nd = len(names)
    parts = []
    mtxt = ('constant-voltage-drop model (tool T1): an OFF diode is an open circuit and needs $V_D<0.7$\\,V; '
            'an ON diode is a $0.7$\\,V source and needs $I_D>0$' if model == 'CVD' else
            'ideal-diode model (tool T1): an OFF diode is an open circuit and needs $V_D<0$; an ON diode is a short '
            '($V_D=0$) and needs $I_D>0$')
    s1 = (f'Use the {mtxt}. With {nd} diode{"s" if nd > 1 else ""} there '
          f'{"are" if nd > 1 else "are"} ${2 ** nd}$ ON/OFF combinations. For each one the circuit is linear: solve it '
          f'with $V_i$ kept as a symbol, then check its assumptions --- each check is a condition on $V_i$ '
          f'(tool T2).')
    if pn.opamps:
        s1 += (' Op-amps are ideal ($A\\to\\infty$). Whether an op-amp has negative feedback can depend on the diode '
               'states, so decide it separately for every combination.')
    s1 += node_names(pn)
    parts.append('\\solstep{1}{Model and method}' + s1)
    k = 2
    for st in good:
        on = st['on']
        title = ', '.join(f'${dname(n)}$ {"ON" if n in on else "OFF"}' for n in names)
        parts.append(f'\\solstep{{{k}}}{{Assume {title}}}' + state_section(pn, st, names)
                     + f' So this state holds for $\\boxed{{{interval_tex(st)}}}$, where $V_o = {lin_tex(st["vo"])}$.')
        k += 1
    if bad:
        items = []
        for st in bad:
            title = ', '.join(f'${dname(n)}$ {"ON" if n in st["on"] else "OFF"}' for n in names)
            items.append(f'{title}: {_contradiction(pn, st)} --- these cannot all hold, so this state never occurs.')
        parts.append(f'\\solstep{{{k}}}{{The other combinations}}'
                     + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + i for i in items)
                     + '\n\\end{itemize}\n')
        k += 1
    # assemble
    s = 'Put the valid states together'
    if len(merged(good)) < len(good):
        s += (' (neighbouring states that give the \\emph{same} $V_o$ are merged: a diode changes state there, but '
              'it does not affect $V_o$)')
    s += ':' + T.eq(cases_tex(good))
    checks = []
    for s1_, s2_ in zip(merged(good), merged(good)[1:]):
        b = s1_['hi']
        v1 = float(s1_['vo'].subs(X, b))
        checks.append(f'at $V_i={num_tex(float(b), 4)}$\\,V both pieces give $V_o={num_tex(v1, 4)}$\\,V')
    if checks:
        s += ('Check: the pieces must meet at each breakpoint --- ' + '; '.join(checks) + '. \\checkmark')
    s += T.figure(figs['transfer'], width=r'0.62\linewidth', height='6cm')
    if vin is not None:
        amp, f, fn = vin
        s += (f'For $V_i(t) = {num_tex(amp)}\\{fn}(2\\pi\\cdot {num_tex(f)}\\,t)$ simply pass every instant of $V_i(t)$ '
              f'through the characteristic above (each piece is a straight line, so each part of the sinusoid is '
              f'scaled and shifted):'
              + T.figure(figs['time'], width=r'0.62\linewidth', height='5cm'))
    parts.append(f'\\solstep{{{k}}}{{Assemble and sketch}}' + s)
    parts.append('\\begin{ansbox}\n$' + cases_tex(good) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts)
