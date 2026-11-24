"""Worked solutions for Lecture 5 (MOSFETs): pipeline card and the DC-analysis solution."""
from common.units import num_tex
from common import texdoc as T
from .dc5 import solve_dc5, exact_dc5, region_checks, I_, id_sym


def pipeline_card():
    return r"""
\begin{cardbox}{The Lecture-5 pipeline (use it for every problem in this lecture)}
\textbf{Tools --- this is all the theory you need (plus the Lecture-1--4 tools):}
\begin{enumerate}[label=\textbf{T\arabic*},leftmargin=2.2em,itemsep=1pt]
\item \emph{Square law} ($I_G = 0$ always). NMOS: $V_{ov} = V_{GS} - V_{tn}$; PMOS: $V_{ov} = V_{SG} - |V_{tp}|$.
      Cutoff if $V_{ov}\le 0$; active (saturation) if $|V_{DS}| \ge V_{ov}$:
      $I_D = \frac{k'}{2}\frac{W}{L}V_{ov}^2$; otherwise triode.
      A diode-connected transistor (gate tied to drain) is always active.
\item \emph{One quadratic per transistor:} with the gate voltage known, KVL gate $\to$ source $\to$ resistor $\to$
      known node gives $V_{known} = V_{GS} + R\,I_D$ with $I_D = \frac{k}{2}(V_{GS}-V_t)^2$. Of the two roots keep
      the one with $V_{GS} > V_t$.
\item \emph{Current mirror:} transistors with the same gate node and the same source node have the same $V_{GS}$,
      so their currents scale with $W/L$: $\frac{I_{D2}}{I_{D1}} = \frac{(W/L)_2}{(W/L)_1}$.
\item \emph{Small signal} ($r_o = \infty$): $g_m = k'\frac{W}{L}V_{ov} = \sqrt{2k'\frac{W}{L}I_D} = \frac{2I_D}{V_{ov}}$.
      Node impedances: $Z_{gate} = \infty$, $Z_{drain} = \infty$, $Z_{source} = \frac{1}{g_m}$. Gains: CS
      $\frac{v_d}{v_g} = -\frac{Z_D}{1/g_m + Z_S}$, CD $\frac{v_s}{v_g} = \frac{Z_S}{1/g_m + Z_S}$, CG
      $\frac{v_d}{v_s} = \frac{Z_D}{1/g_m}$ ($Z_D$, $Z_S$: everything else hanging on that node). For AC, DC supplies
      are ground and ``$\infty$'' capacitors are shorts.
\item \emph{Thevenin:} a linear network seen from two terminals is a source $V_{th}$ (its open-circuit voltage) in
      series with $R_{th}$ (its resistance with all sources set to zero). Branches $(V_k, R_k)$ in parallel combine to
      $V_{th} = \frac{\sum V_k/R_k}{\sum 1/R_k}$, $R_{th} = R_1\|R_2\|\dots$; a series resistor adds to $R_{th}$.
\end{enumerate}
\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{DC:} assume every transistor active; gate voltages from dividers ($I_G=0$); one quadratic (or a mirror
      ratio) per transistor; then node voltages by KCL; \emph{verify} $V_{ov} > 0$ and $|V_{DS}| \ge V_{ov}$.
\item \emph{AC:} $g_m$ of every transistor; node impedances; multiply the node-to-node gains along the signal path;
      then standard form, Bode plot and output as in Lecture 1.
\item \emph{Design:} run the same relations backwards with the stated design rules, then check by analysis.
\end{enumerate}
\end{cardbox}
"""


def dc_solution(circ):
    steps, V, ID, VG = solve_dc5(circ)
    parts = []
    parts.append('\\solstep{1}{Assumptions}Assume every transistor is active (saturation, tool T1). No current '
                 'flows into any gate, so gate voltages come from the resistor networks alone.')
    parts.append('\\solstep{2}{Walk through the circuit}'
                 + '\\begin{enumerate}[leftmargin=*,itemsep=3pt]\n' + '\n'.join('\\item ' + s for s in steps)
                 + '\n\\end{enumerate}\n')
    lines, ok = region_checks(circ, V, ID, VG)
    Vx, IDx = exact_dc5(circ, V)
    err = max(abs(ID[n] - IDx[n]) / IDx[n] for n in ID)
    parts.append('\\solstep{3}{Verify the operating modes}'
                 + '\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + l for l in lines)
                 + '\n\\end{itemize}\n'
                 + 'Unlike the BJT, nothing was neglected here ($I_G = 0$ exactly), so these results are exact for the '
                   'square-law model: a full nodal solve of the circuit gives the same currents.')
    ans = ',\\quad '.join(f'${id_sym(q)} = {I_(ID[q.name])}$' for q in circ.bjts)
    parts.append('\\begin{ansbox}\n' + ans + ('\\\\[2pt] all transistors active.' if ok else '') + '\n\\end{ansbox}\n')
    return '\n'.join(parts), V, ID, ok, err


def ac_solution(circ, ID, stages, sig_in, figs):
    """Lecture-5 small-signal solution: g_m, input resistances, gains, H(s), Bode plot, output."""
    from common.tf import TF, f_txt
    from lecture1 import narrative as N1
    from .ac5 import solve_ac5
    parts = []
    cur = ', '.join(f'${id_sym(st.q)} = {I_(ID[st.q.name])}$' for st in stages)
    ap, H, view = solve_ac5(circ, ID, stages)
    parts.append('\\solstep{1}{DC currents and transconductances}The DC drain currents are given: ' + cur + '. For AC '
                 'every DC supply is ground and every ``$\\infty$\'\' capacitor is a short. ' + ap[0])
    parts.append('\\solstep{2}{Input resistance of each stage}' + ap[1])
    parts.append('\\solstep{3}{Gain along the signal path}' + ap[2])
    tf = TF.from_expr(H)
    parts.append('\\solstep{4}{Transfer function}Multiply and simplify:' + T.eq('H(s) = ' + tf.rational_tex()))
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + N1.standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + N1.bode_section(tf, figs['bode']))
    txt, amp, ph = N1.output_section(tf, sig_in, None)
    parts.append('\\solstep{7}{Steady-state output}' + txt)
    corners = ', '.join(f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$'
                 + (f'\\quad (corners: {corners})' if corners else '')
                 + '\\\\[4pt]\n$' + N1.vo_tex(sig_in, 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), tf, H, view, dict(amp=amp, phase=ph)
