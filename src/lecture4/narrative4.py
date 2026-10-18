"""Worked solutions for Lecture 4 (BJTs)."""
import math

from common.units import num_tex, eng_tex
from common.tf import TF, f_txt
from common import texdoc as T
from lecture1 import narrative as N1
from .dc import solve_dc, checks, exact_dc
from .ac import solve_ac


def pipeline_card():
    return r"""
\begin{cardbox}{The Lecture-4 pipeline (use it for every problem in this lecture)}
\textbf{Tools --- this is all the theory you need (plus the Lecture-1--3 tools):}
\begin{enumerate}[label=\textbf{T\arabic*},leftmargin=2.2em,itemsep=1pt]
\item \emph{Active BJT at DC:} npn $V_{BE}=0.7$\,V, pnp $V_{EB}=0.7$\,V; $I_C=\beta I_B$, $I_E=(\beta+1)I_B$, so
      $I_C\approx I_E$ and, when $\beta$ is large, $I_B\approx 0$. Active needs $|V_{CE}|\ge 0.2$\,V.
\item \emph{Current mirror:} transistors with the same base node and the same emitter node have the same $V_{BE}$,
      hence the same $I_C$.
\item \emph{Small-signal parameters:} $r_e = \frac{V_T}{I_C}$ ($V_T=25$\,mV), $\alpha=\frac{\beta}{\beta+1}$, $r_o=\infty$.
      For AC, DC supplies are ground and ``$\infty$'' capacitors are shorts.
\item \emph{Node impedances and gains:} $Z_{base}=(\beta+1)(r_e+Z_E)$, $Z_{emitter}=r_e+\frac{Z_B}{\beta+1}$,
      $Z_{collector}=\infty$;\ \ CE $\frac{v_c}{v_b}=-\alpha\frac{Z_C}{r_e+Z_E}$, CB $\frac{v_c}{v_e}=\alpha\frac{Z_C}{Z_{emitter}}$,
      CC $\frac{v_e}{v_b}=\frac{Z_E}{r_e+Z_E}$. $Z_C$, $Z_E$, $Z_B$ are everything else hanging on that node
      (including the input resistance of the next stage).
\end{enumerate}
\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{DC:} assume every transistor active and $I_B\approx0$; walk through the circuit node by node
      (dividers, $V_{BE}$, KCL for $I_E$, $I_C\approx I_E$, collector voltages); then \emph{verify}: $I_B\ll$ bias currents and
      $|V_{CE}|\ge0.2$\,V.
\item \emph{AC:} $r_e$ of every transistor; input resistance of every stage from the last one backwards; multiply the
      node-to-node gains along the signal path; then standard form, Bode plot and output as in Lecture 1.
\item \emph{Design:} run the same relations backwards, choosing the free quantities with the stated design rules, then
      check the result by analysing the finished circuit.
\end{enumerate}
\end{cardbox}
"""


def I_(x):
    return eng_tex(x, '\\mathrm{A}')


def dc_solution(circ, beta=100):
    steps, V, IC = solve_dc(circ)
    parts = []
    parts.append('\\solstep{1}{Assumptions}Assume every transistor is in the active region and that every base '
                 'current is negligible ($I_B\\approx0$, tool T1): then $|V_{BE}| = 0.7$\\,V, $I_C\\approx I_E$, and no '
                 'current flows into any base, so a base network behaves like a plain resistor divider.')
    parts.append('\\solstep{2}{Walk through the circuit}'
                 + '\\begin{enumerate}[leftmargin=*,itemsep=3pt]\n' + '\n'.join('\\item ' + s for s in steps)
                 + '\n\\end{enumerate}\n')
    lines, ok = checks(circ, V, IC)
    parts.append('\\solstep{3}{Verify the assumptions}'
                 + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + l for l in lines)
                 + '\n\\end{itemize}\n')
    Vx, ICx = exact_dc(circ)
    rows = [[f'${q.tex}$', f'${I_(IC[q.name])}$', f'${I_(ICx[q.name])}$',
             f'${num_tex(100 * (IC[q.name] - ICx[q.name]) / ICx[q.name], 2)}\\%$'] for q in circ.bjts]
    worst = max(abs(IC[n] - ICx[n]) / ICx[n] for n in IC)
    note = ('' if worst < 0.06 else
            ' The differences grow along the chain: every base current slightly shifts the collector voltage that '
            'biases the next transistor, and $\\alpha = \\beta/(\\beta+1)$ makes each $I_C$ about 1\\,\\% smaller '
            'than its $I_E$. A shift is amplified when the next stage has only a small voltage across its emitter '
            'resistor. Hand analysis with $I_B\\approx0$ is still the standard first pass.')
    parts.append('\\solstep{4}{How good was $I_B\\approx 0$?}If we keep the base currents ($I_C=\\beta I_B$ with '
                 f'$\\beta={beta}$) and solve the circuit exactly, the currents change only a little:'
                 + T.table(['transistor', '$I_C$ (with $I_B\\approx0$)', '$I_C$ (exact)', 'difference'], rows, 'cccc')
                 + note)
    ans = ',\\quad '.join(f'$I_{{C{q.name[1:]}}} = {I_(IC[q.name])}$' for q in circ.bjts)
    parts.append('\\begin{ansbox}\n' + ans + ('\\\\[2pt] all transistors active, all base currents negligible.'
                                               if ok else '') + '\n\\end{ansbox}\n')
    return '\n'.join(parts), V, IC, ICx, ok


def ac_solution(circ, IC, stages, sig_in, figs, ic_given=True):
    parts = []
    cur = ', '.join(f'$I_{{C{q.q.name[1:]}}} = {I_(IC[q.q.name])}$' for q in stages)
    ap, H, view = solve_ac(circ, IC, stages)
    parts.append('\\solstep{1}{DC currents and small-signal parameters}'
                 + (f'The DC collector currents are given: {cur}. ' if ic_given else '')
                 + 'For AC every DC supply is ground and every ``$\\infty$\'\' capacitor is a short (tool T3). '
                 + ap[0])
    parts.append('\\solstep{2}{Input resistance of each stage}' + ap[1])
    parts.append('\\solstep{3}{Gain along the signal path}' + ap[2])
    tf = TF.from_expr(H)
    parts.append('\\solstep{4}{Transfer function}Multiply and simplify:' + T.eq('H(s) = ' + tf.rational_tex()))
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + N1.standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + N1.bode_section(tf, figs['bode']))
    txt, amp, ph = N1.output_section(tf, sig_in, None)
    parts.append('\\solstep{7}{Steady-state output}' + txt)
    corners = ', '.join(f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\quad (corners: ' + corners + ')\\\\[4pt]\n$'
                 + N1.vo_tex(sig_in, 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), tf, H, view, dict(amp=amp, phase=ph)
