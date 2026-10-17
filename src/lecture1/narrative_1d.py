"""Worked solutions for set 1D: magnitude Bode plot -> H(s) -> steady-state output.
Follows the fixed 6-step reverse pipeline of pipeline_card_1d()."""
import math

from common.units import num_tex, sig
from common.tf import f_txt
from common import texdoc as T
from .narrative import output_section, vo_tex


def _f(w):
    return f_txt(w).replace('µ', '$\\mu$')


def _slope(sv):
    return f'${sv:+d}$' if sv else '$0$'


def solve_1d(tf, f_ref, sig_in, figs):
    parts = []
    corners = tf.corners()
    # ---- Step 1: read the plot
    groups = []  # (w, total change)
    for w, d in corners:
        if groups and abs(groups[-1][0] - w) < 1e-9 * w:
            groups[-1][1] += d
        else:
            groups.append([w, d])
    segs = tf.segments()
    rows = []
    slope = 20 * tf.m
    for w, d in groups:
        after = slope + d
        n = abs(d) // 20
        what = (f'{"one" if n == 1 else "two" if n == 2 else n} '
                f'{"pole" if d < 0 else "zero"}{"s" if n > 1 else ""} at $f_c$')
        rows.append([_f(w), _slope(slope), _slope(after), f'${d:+d}$', what])
        slope = after
    s1 = ('Go left to right along the plot and write down the slope of every straight segment. At each corner '
          'frequency the slope changes by a multiple of 20\\,dB/dec: every $-20$ is one pole, every $+20$ is one '
          'zero (tool T6 read backwards).')
    s1 += T.table(['corner $f_c$', 'slope before', 'slope after', 'change', 'meaning'], rows, 'ccccl')
    parts.append('\\solstep{1}{Read the corners and slopes}' + s1)

    # ---- Step 2: low-frequency slope
    m = tf.m
    if m == 0:
        s2 = ('The plot starts \\emph{flat} (0\\,dB/dec), so there is no factor $s$ in the numerator: every pole is '
              'written as $\\frac{1}{1+s/p}$ and every zero as $\\left(1+\\frac{s}{z}\\right)$, which are all '
              '$\\approx1$ (0\\,dB) at low frequency.')
    else:
        pw = 's' if m == 1 else f's^{m}'
        lows = ', '.join(_f(w) for w in sorted(tf.poles)[:m])
        s2 = (f'The plot starts with a slope of ${20 * m:+d}$\\,dB/dec, i.e. $|H|\\propto\\omega^{m}$ at low frequency: '
              f'the numerator contains ${pw}$. As in class, pair each $s$ with one of the \\emph{{lowest}} poles '
              f'({lows}) as $\\frac{{s}}{{s+p}}$: such a factor rises at $+20$\\,dB/dec below $p$ and is '
              f'$\\approx1$ (0\\,dB) above it. The remaining poles are written $\\frac{{1}}{{1+s/p}}$ and the zeros '
              f'$\\left(1+\\frac{{s}}{{z}}\\right)$.')
    s2 += (' Every corner is an angular frequency $\\omega_c=2\\pi f_c$.')
    parts.append('\\solstep{2}{Starting slope $\\Rightarrow$ factors of $s$}' + s2)

    # ---- Step 3: assemble
    body = r'\,'.join(f.tex() for f in tf.factors[1:])
    parts.append('\\solstep{3}{Assemble $H(s)$}Put one factor per pole/zero in front of an unknown constant $K$:'
                 + T.eq('H(s) = K\\,' + body))

    # ---- Step 4: K from the marked level
    wr = 2 * math.pi * f_ref
    L = round(tf.asym_db(wr), 9) + 0.0
    rows = []
    tot = 0.0
    for f in tf.factors[1:]:
        a = round(f.asym_db(wr), 9) + 0.0
        tot += a
        rows.append([f.cell_tex(), _f(f.w) if f.w else '', f.asym_rule_tex(wr), f'${sig(a, 3)}$'])
    rows.append(['\\textbf{sum}', '', '', f'$\\mathbf{{{sig(tot, 3)}}}$'])
    kdb = L - tot
    K = 10 ** (kdb / 20)
    s4 = (f'The plot marks the level ${sig(L, 3)}$\\,dB at $f=$\\,{_f(wr)}. On the straight-line plot every '
          f'factor is either exactly 0\\,dB (where it is $\\approx1$) or a $\\pm20$\\,dB/dec line, so evaluate the '
          f'\\emph{{asymptote}} of each factor at that frequency (the level of a line with slope $\\pm20$\\,dB/dec '
          f'is $\\pm20\\log_{{10}}(f/f_c)$):')
    s4 += T.table(['factor', '$f_c$', f'at $f=$\\,{_f(wr)}', 'asymptote (dB)'], rows, 'cccc')
    s4 += ('The dB values of the factors \\emph{add} (magnitudes multiply), so'
           + T.eq(f'20\\log_{{10}}K = {sig(L, 3)} - ({sig(tot, 3)}) = {sig(kdb, 3)}\\ \\mathrm{{dB}}'
                  f'\\quad\\Rightarrow\\quad K = 10^{{{sig(kdb, 3)}/20}} = {num_tex(K)}'))
    parts.append('\\solstep{4}{Find $K$ from the marked level}' + s4)
    parts.append('So' + T.eq('\\boxed{H(s) = ' + tf.bode_form_tex() + '}'))

    # ---- Step 5: check
    rows = []
    for seg in segs:
        lo, hi = seg['w_lo'], seg['w_hi']
        rng = (f'$f<$ {_f(hi)}' if lo is None else f'$f>$ {_f(lo)}' if hi is None else f'{_f(lo)} -- {_f(hi)}')
        lv = []
        if seg['db_lo'] is not None:
            lv.append(f"{sig(seg['db_lo'], 3)} dB at start")
        if seg['db_hi'] is not None:
            lv.append(f"{sig(seg['db_hi'], 3)} dB at end")
        rows.append([rng, _slope(seg['slope']) + ' dB/dec', ', '.join(lv)])
    s5 = ('Rebuild the plot from the factors: each factor\'s straight-line plot (green) is added to get $|H|$ '
          '(blue). It must reproduce every slope of the given plot and the marked level.')
    s5 += T.figure(figs['factors'], width=r'0.82\linewidth', height='9cm')
    s5 += T.table(['frequency range', 'slope', 'asymptote level'], rows, 'lcl')
    parts.append('\\solstep{5}{Check}' + s5)

    # ---- Step 6: output
    txt, amp, ph = output_section(tf, sig_in, None)
    parts.append('\\solstep{6}{Steady-state output}' + txt.replace('(tool T5)', '(tool T5; use the \\emph{exact} '
                                                                   'factors here, not the straight lines)'))
    corners_txt = ', '.join(_f(w) for w, _ in corners)
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\quad (corners: ' + corners_txt
                 + ')\\\\[4pt]\n$' + vo_tex(sig_in, 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), dict(K=K, amp=amp, phase=ph)


def pipeline_card_1d():
    return r"""
\begin{cardbox}{The reverse pipeline: magnitude Bode plot $\to H(s)$ (use it for every problem in this set)}
\textbf{Assumptions (as in class):} a magnitude plot cannot show the sign of $K$ or whether a zero is in the
right half-plane, so take $K>0$ and all poles/zeros in the left half-plane.

\textbf{Tools:} T5 (sinusoid through $H$) and T6 (Bode rules) from the Lecture-1 card, plus:
a factor $\frac{s}{s+p}$ is $+20$\,dB/dec below $p$ and $0$\,dB above; $\frac{1}{1+s/p}$ is $0$\,dB below and
$-20$\,dB/dec above; $\left(1+\frac{s}{z}\right)$ is $0$\,dB below and $+20$\,dB/dec above; dB values of factors add.

\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{Read the plot:} slope of every segment; at each corner, change $=-20k$ means $k$ poles, $+20k$ means $k$ zeros.
\item \emph{Starting slope} $+20m$\,dB/dec $\Rightarrow s^m$ in the numerator; pair each $s$ with a lowest pole as $\frac{s}{s+p}$.
\item \emph{Assemble} $H(s)=K\cdot\prod(\text{factors})$ with $\omega_c=2\pi f_c$.
\item \emph{Find $K$:} at the marked frequency, add the straight-line dB of every factor; $20\log_{10}K =$ marked level $-$ that sum.
\item \emph{Check:} the sum of the factor plots must reproduce the given plot.
\item \emph{Output:} evaluate the exact factors at $s=j\omega_{in}$, multiply magnitudes, add angles, apply T5.
\end{enumerate}
\end{cardbox}
"""
