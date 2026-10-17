"""Turn a Lecture-1 ladder problem into a worked LaTeX solution that follows the fixed
7-step pipeline (see pipeline_card())."""
from fractions import Fraction
import math

from common.units import eng_tex, num_tex, sig
from common.tf import TF, rational_tex, poly_coeffs, poly_tex, f_of, f_txt, Factor
from common import texdoc as T
from .ladder import (El, Ser, Par, NamedZ, Src, VCVS, VCCS, kept, merge_shunts_ac,
                     dc_analysis, ac_chain)


# ----------------------------------------------------------------- small formatters
def Vt(x):
    return eng_tex(float(x), r'\mathrm{V}')


def Ohm(x):
    return eng_tex(float(x), r'\Omega')


def Rn(x):
    """Resistance inside a formula without the unit: 2\\,k."""
    return eng_tex(float(x), '')


def vn(name):
    return 'V_{' + name + '}'


def pi_tex(p):
    """Fraction p -> LaTeX for p*pi with sign, '' for 0."""
    p = Fraction(p)
    if p == 0:
        return ''
    sgn = '+' if p > 0 else '-'
    a = abs(p)
    num = '' if a.numerator == 1 else str(a.numerator)
    if a.denominator == 1:
        return f'{sgn}{num}\\pi'
    return f'{sgn}\\frac{{{num}\\pi}}{{{a.denominator}}}'


def cap_phrase(z):
    return 'is a capacitor' if isinstance(z, El) else 'contains a capacitor'


def Vr(v):
    """Supply voltage with an explicit sign: +5 V, -3 V."""
    return ('+' if v > 0 else '') + Vt(v)


def dc_name(z):
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        return z.tex
    if isinstance(z, Ser):
        return ' + '.join(dc_name(p) for p in z.parts)
    return r' \parallel '.join(dc_name(p) for p in z.parts)


class Sine:
    def __init__(self, amp, f, phase_pi=0, fn='sin'):
        self.A = float(amp)
        self.f = float(f)
        self.ph = Fraction(phase_pi)
        self.fn = fn

    @property
    def w(self):
        return 2 * math.pi * self.f

    @property
    def theta(self):
        return float(self.ph) * math.pi

    def arg_tex(self, extra=''):
        return r'2\pi\cdot ' + num_tex(self.f) + r'\,t' + pi_tex(self.ph) + extra

    def tex(self, name='V_i(t)'):
        return f'{name} = {num_tex(self.A)}\\{self.fn}\\left({self.arg_tex()}\\right)'


# ----------------------------------------------------------------- collect named impedances
def _named_in(z, out):
    if isinstance(z, NamedZ):
        _named_in(z.inner, out)
        if z not in out:
            out.append(z)
    elif isinstance(z, (Ser, Par)):
        for p in z.parts:
            _named_in(p, out)


# ----------------------------------------------------------------- Step 2: DC
def dc_section(circ, figname):
    vodc, msgs = dc_analysis(circ)
    els = circ.elements()
    caps = [e.tex for e in els if e.kind == 'C']
    inds = [e.tex for e in els if e.kind == 'L']
    out = []
    rules = ['the AC input is set to zero ($V_i=0$: a wire to ground)']
    if caps:
        rules.append('every capacitor is an open circuit ($' + ', '.join(caps) + '$)')
    if inds:
        rules.append('every inductor is a short circuit ($' + ', '.join(inds) + '$)')
    out.append('DC rules: ' + '; '.join(rules) + '. Only the part of the circuit that is still '
               'connected to $V_o$ matters:')
    out.append(T.figure(figname, width=r'0.55\linewidth', height='5cm'))
    out.append('Reduce the circuit with one tool only --- the \\emph{divider between two voltages} '
               '(tool T3) --- walking toward $V_o$ and keeping a Thevenin pair '
               '$(V_{th},R_{th})$ for everything already visited.')
    items = []
    combined_at_out = False
    at_out = False
    for m in msgs:
        k = m.kind
        if k == 'start_left':
            items.append('Start at the input node: since $V_i=0$ it is tied to ground, i.e. it is an '
                         'ideal $0\\,\\mathrm{V}$ source: $(V_{th},R_{th})=(0\\,\\mathrm{V},\\,0\\,\\Omega)$.')
        elif k == 'series_open':
            items.append(f'${dc_name(m.z)}$ {cap_phrase(m.z)} $\\Rightarrow$ open at DC. No DC current '
                         f'can cross it, so everything on its left is disconnected: start fresh after it.')
        elif k == 'series':
            if m.r == 0:
                items.append(f'${dc_name(m.z)}$ is a short at DC (inductor), so the pair is unchanged.')
            else:
                a = m.after
                items.append(f'Walk through ${dc_name(m.z)}$ (${Ohm(m.r)}$ at DC). A series resistor just adds '
                             f'to $R_{{th}}$: $(V_{{th}},R_{{th}}) = ({Vt(a[0])},\\ {Ohm(a[1])})$.')
        elif k == 'open_shunt':
            items.append(f'${dc_name(m.z)}$ (at ${vn(m.node.name or "")}$) {cap_phrase(m.z)}: open at DC, ignore it.'
                         if m.node.name else
                         f'${dc_name(m.z)}$ {cap_phrase(m.z)}: open at DC, ignore it.')
        elif k == 'shunt':
            dest = 'ground' if m.rail is None else f'the ${Vr(m.rail)}$ supply'
            desc = f'${dc_name(m.z)}$ to {dest}'
            vb, rb = m.br
            if m.side == 'O':
                combined_at_out = True
            if m.before is None:
                items.append(f'First DC path here: {desc}, so $(V_{{th}},R_{{th}}) = ({Vt(vb)},\\ {Ohm(rb)})$.')
            elif m.before[1] == 0:
                items.append(f'{desc} hangs on a node that is held by an ideal source, so it does not change '
                             f'that node voltage.')
            elif rb == 0:
                items.append(f'{desc} is a short at DC: the node is forced to ${Vt(vb)}$ ($R_{{th}}=0$).')
            else:
                va, ra = m.before
                v, r = m.after
                items.append(
                    f'Add {desc}. Divider between $V_a={Vt(va)}$ (through $R_a={Ohm(ra)}$) and '
                    f'$V_b={Vt(vb)}$ (through $R_b={Ohm(rb)}$):'
                    + T.eq(f'V_{{th}} = V_b + (V_a-V_b)\\frac{{R_b}}{{R_a+R_b}} = {num_tex(vb)} + '
                           f'\\left({num_tex(va)} - ({num_tex(vb)})\\right)\\frac{{{Rn(rb)}}}{{{Rn(ra)} + {Rn(rb)}}}'
                           f' = {Vt(v)},\\qquad R_{{th}} = R_a\\parallel R_b = {Ohm(r)}'))
        elif k == 'start_right':
            items.append('Now reduce the part to the \\emph{right} of $V_o$ the same way, starting at the far '
                         'right end and moving toward $V_o$.')
        elif k == 'at_out':
            at_out = True
            items.append('Finally, collect everything at the output node $V_o$.')
        elif k == 'join':
            combined_at_out = True
            (va, ra), (vb, rb), (v, r) = m.left, m.right, m.after
            if ra == 0:
                items.append(f'The left side holds $V_o$ with an ideal source, so $V_o={Vt(va)}$.')
            else:
                items.append(
                    f'$V_o$ sits between the left pair $({Vt(va)},\\ {Ohm(ra)})$ and the right pair '
                    f'$({Vt(vb)},\\ {Ohm(rb)})$:'
                    + T.eq(f'V_{{o,dc}} = {num_tex(vb)} + \\left({num_tex(va)} - ({num_tex(vb)})\\right)'
                           f'\\frac{{{Rn(rb)}}}{{{Rn(ra)} + {Rn(rb)}}} = {Vt(v)}'))
    if not combined_at_out:
        items.append('Nothing else draws DC current from $V_o$, so no current flows through $R_{th}$ and there is '
                     'no voltage drop across it: $V_{o,dc}=V_{th}$.')
    out.append('\\begin{enumerate}[leftmargin=*,itemsep=2pt]\n' +
               '\n'.join('\\item ' + it for it in items) + '\n\\end{enumerate}\n')
    out.append(T.eq(f'\\boxed{{V_{{o,dc}} = {Vt(vodc)}}}'))
    return '\n'.join(out), float(vodc)


# ----------------------------------------------------------------- Step 3: AC circuit
def ac_circuit_section(circ, analyses, figname):
    out = []
    rails = circ.rails()
    rule = 'Replace every capacitor by $\\frac{1}{sC}$ and every inductor by $sL$.'
    if rails:
        rule = ('Set every DC supply to zero: each supply rail becomes AC ground. ' + rule)
    out.append(rule)
    notes = []
    for st, an in zip(circ.stages, analyses):
        for m, rs in an['merges']:
            names = ', '.join('$' + r.tex + '$' for r in rs)
            prod = r' \parallel '.join(r.tex for r in rs)
            vals = r' \parallel '.join(Rn(r.value) for r in rs)
            notes.append(f'{names} {"both" if len(rs) == 2 else "all"} go from the same node to (AC) ground, so they are in parallel: '
                         f'${m.tex} = {prod} = {vals} = {Ohm(m.value)}$.')
        n0 = st.nodes[0]
        if n0.shunts and not isinstance(st.src, VCCS):
            what = 'the ideal input source $V_i$' if isinstance(st.src, Src) else \
                'the output of the ideal dependent voltage source'
            names = ', '.join('$' + dc_name(z) + '$' for z, _ in n0.shunts)
            notes.append(f'{names} sits directly across {what}. An ideal voltage source keeps its voltage '
                         f'whatever you connect to it, so {names} cannot change any node voltage: it drops out of $H(s)$.')
    if notes:
        out.append('\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' +
                   '\n'.join('\\item ' + n for n in notes) + '\n\\end{itemize}\n')
    out.append('AC equivalent circuit (nodes named for the next step):')
    out.append(T.figure(figname, width=r'0.95\linewidth', height='5.2cm'))
    return '\n'.join(out)


# ----------------------------------------------------------------- Step 4: divider chain
def chain_section(circ, links):
    out = []
    names = []
    fr = []
    for ln in links:
        if ln['kind'] == 'step':
            a, b = ln['step'].frm.name, ln['step'].to.name
        else:
            a, b = ln['frm'], ln['to']
        fr.append(f'\\frac{{{vn(b)}}}{{{vn(a)}}}')
        names.append((a, b))
    path = ' \\to '.join([vn(names[0][0])] + [vn(b) for _, b in names])
    if len(links) == 1:
        out.append(f'Walk from the input to the output through the named nodes: ${path}$. There is a single '
                   f'link, so $H(s)$ is just one voltage divider (tool T2).')
    else:
        out.append(f'Walk from the input to the output through the named nodes: ${path}$. '
                   f'The transfer function is the product of the node-to-node ratios (each one is a simple '
                   f'divider, tool T2, or a dependent source, tool T4):')
        out.append(T.eq('H(s) = \\frac{V_o}{V_i} = ' + '\\cdot'.join(fr)))
    # impedances needed
    needed = []
    for ln in links:
        if ln['kind'] == 'step' and ln['step'].kind == 'div':
            _named_in(ln['step'].zp, needed)
        if ln['kind'] == 'vccs':
            _named_in(ln['z'], needed)
    if needed:
        out.append('Impedances seen \\emph{looking right} from a node (everything from that node to ground, '
                   'excluding what is on its left). Compute them from the far right toward the input:')
        lines = []
        for nz in needed:
            lines.append(f'{nz.tex_name} &= {nz.inner.z_tex()} = {rational_tex(nz.z())}')
        out.append(T.align(lines))
    out.append('Now each link. {\\small (Algebra tip: to simplify a fraction that contains fractions, multiply '
               'its top and bottom by every inner denominator; then divide top and bottom by the leading '
               'coefficient of the denominator so that it starts with a plain $s^n$.)}')
    lines = []
    for ln in links:
        if ln['kind'] == 'step':
            st = ln['step']
            lhs = f'\\frac{{{vn(st.to.name)}}}{{{vn(st.frm.name)}}}'
            if st.kind == 'open':
                lines.append(f'{lhs} &= 1 &&\\text{{(nothing connected after ${st.zs.z_tex()}$: no current, no drop)}}')
            else:
                zp = st.zp.z_tex()
                zs = st.zs.z_tex()
                expr = st.zp.z() / (st.zs.z() + st.zp.z())
                lines.append(f'{lhs} &= \\frac{{{zp}}}{{{zs} + {zp}}} = {rational_tex(expr)}')
        elif ln['kind'] == 'vcvs':
            lhs = f'\\frac{{{vn(ln["to"])}}}{{{vn(ln["frm"])}}}'
            lines.append(f'{lhs} &= {num_tex(ln["gain"])} &&\\text{{(ideal VCVS: ${vn(ln["to"])} = '
                         f'{num_tex(ln["gain"])}{vn(ln["frm"])}$)}}')
        else:
            lhs = f'\\frac{{{vn(ln["to"])}}}{{{vn(ln["frm"])}}}'
            g = float(ln['gm'])
            sgn = '-' if ln['sign'] < 0 else ''
            z = ln['z']
            expr = ln['sign'] * g * z.z()
            lines.append(f'{lhs} &= {sgn}{num_tex(g)}\\,{z.z_tex()} = {rational_tex(expr)}')
    out.append(T.align(lines))
    for ln in links:
        if ln['kind'] == 'vccs':
            d = 'out of' if ln['sign'] < 0 else 'into'
            out.append(f'(VCCS: the current ${num_tex(ln["gm"])}{vn(ln["frm"])}$ flows {d} node '
                       f'${vn(ln["to"])}$ and through ${ln["z"].z_tex()}$ to ground, so '
                       f'${vn(ln["to"])} = {"-" if ln["sign"] < 0 else ""}{num_tex(ln["gm"])}{vn(ln["frm"])}\\,'
                       f'{ln["z"].z_tex()}$ by Ohm\'s law.)')
    return '\n'.join(out)


# ----------------------------------------------------------------- Step 5: standard form
def roots_tex(coeffs, var_names):
    """Explain how to get the roots of a monic-ish polynomial (coeffs high->low, no s=0 roots)."""
    deg = len(coeffs) - 1
    lead = float(coeffs[0])
    c = [float(x) / lead for x in coeffs]
    pre = ''
    if abs(lead - 1) > 1e-12:
        pre = (f'divide by the leading coefficient ${num_tex(lead)}$ (this does not move the roots): '
               f'${poly_tex(c)}$; ')
    if deg == 1:
        return pre + f'$s + {num_tex(c[1])} = 0 \\Rightarrow s = -{num_tex(c[1])}$.'
    if deg == 2:
        a1, a0 = c[1], c[2]
        disc = a1 * a1 - 4 * a0
        if abs(disc) < 1e-6 * a1 * a1:   # double root (rounding can make it slightly negative)
            disc = 0.0
        r1 = (-a1 + math.sqrt(disc)) / 2
        r2 = (-a1 - math.sqrt(disc)) / 2
        return (pre + 'quadratic formula:' + T.eq(
            f's = \\frac{{-{num_tex(a1)} \\pm \\sqrt{{({num_tex(a1)})^2 - 4({num_tex(a0)})}}}}{{2}}'
            f' = \\frac{{-{num_tex(a1)} \\pm {num_tex(math.sqrt(disc))}}}{{2}}'
            f' \\Rightarrow s = {num_tex(r1)},\\ {num_tex(r2)}'))
    import numpy as np
    rts = sorted((r.real for r in np.roots(c)), reverse=True)
    return (pre + f'this is degree {deg}: use a calculator\'s polynomial solver (or \\texttt{{numpy.roots}}) '
            f'$\\Rightarrow s = ' + ',\\ '.join(num_tex(r) for r in rts) + '$.')


def standard_form_section(tf):
    out = []
    out.append('Find the roots. Every root $s=-p$ of the denominator is a \\emph{pole}, every root $s=-z$ of '
               'the numerator is a \\emph{zero}; $|p|$ and $|z|$ are the corner frequencies (rad/s).')
    num = [c for c in tf.num]
    den = [c for c in tf.den]
    m, k = tf.m, tf.k
    nr = num[:len(num) - m] if m else num
    dr = den[:len(den) - k] if k else den
    items = []
    if m:
        items.append(f'Numerator: it has the factor $s{"^" + str(m) if m > 1 else ""}$ '
                     f'$\\Rightarrow$ {m} zero{"s" if m > 1 else ""} at $s=0$.')
    if len(nr) > 1:
        items.append(f'Numerator{" (after taking out the $s$ factor)" if m else ""}: '
                     f'${poly_tex(nr)}$; ' + roots_tex(nr, 'z'))
    if len(dr) > 1:
        items.append(f'Denominator: ${poly_tex(dr)}$; ' + roots_tex(dr, 'p'))
    out.append('\\begin{itemize}[leftmargin=*,itemsep=2pt]\n' +
               '\n'.join('\\item ' + it for it in items) + '\n\\end{itemize}\n')
    out.append('Factored form (leading coefficient in front):')
    out.append(T.eq('H(s) = ' + tf.monic_factored_tex()))
    hp = [f for f in tf.factors if f.kind == 'hp']
    expl = ('Bode-ready form: rewrite every $(s+p) = p\\left(1+\\frac{s}{p}\\right)$ and $(s+z) = '
            'z\\left(1+\\frac{s}{z}\\right)$, and collect all constants into $K$.')
    if hp:
        expl += (' Each $s$ in the numerator is paired with one of the \\emph{lowest} poles as '
                 '$\\frac{s}{s+p}$ (that factor is $\\approx 1$ above $p$).')
    expl += ' Then every factor except $K$ is $\\approx 1$ inside the pass-band:'
    out.append(expl)
    out.append(T.eq('H(s) = ' + tf.bode_form_tex() + r',\qquad K = ' + num_tex(tf.K)))
    rows = []
    for w, d in tf.corners():
        rows.append(['pole' if d < 0 else 'zero', '$' + num_tex(w) + '$', f_txt(w).replace('µ', '$\\mu$'),
                     f'${d:+d}$ dB/dec'])
    out.append(T.table(['type', '$\\omega_c$ (rad/s)', '$f_c=\\omega_c/2\\pi$', 'slope change'], rows))
    return '\n'.join(out)


# ----------------------------------------------------------------- Step 6: Bode
def bode_section(tf, figname):
    out = []
    g0 = tf.low_gain()
    mk = tf.m - tf.k
    if mk == 0:
        low = (f'Below every corner, all factors are $\\approx$ constant: $|H| \\approx {num_tex(g0)}$ '
               f'$= {sig(20 * math.log10(g0), 3)}$\\,dB (flat, 0 dB/dec).')
    else:
        pw = '' if abs(mk) == 1 else '^' + str(abs(mk))
        approx = f'{num_tex(g0)}\\,s{pw}' if mk > 0 else f'\\frac{{{num_tex(g0)}}}{{s{pw}}}'
        low = (f'Below every corner $|H(s)|\\approx {approx}$, so the plot starts with a slope of '
               f'${20 * mk:+d}$\\,dB/dec.')
    out.append(low + ' Then, moving right, each pole bends the line down by 20\\,dB/dec and each zero bends it '
               'up by 20\\,dB/dec (tool T6):')
    rows = []
    for seg in tf.segments():
        lo, hi = seg['w_lo'], seg['w_hi']
        if lo is None:
            rng = f'$f<$ {f_txt(hi)}'
        elif hi is None:
            rng = f'$f>$ {f_txt(lo)}'
        else:
            rng = f'{f_txt(lo)} -- {f_txt(hi)}'
        rng = rng.replace('µ', '$\\mu$')
        lv = []
        if seg['db_lo'] is not None:
            lv.append(f"{sig(seg['db_lo'], 3)} dB at start")
        if seg['db_hi'] is not None:
            lv.append(f"{sig(seg['db_hi'], 3)} dB at end")
        rows.append([rng, f"${seg['slope']:+d}$ dB/dec" if seg['slope'] else '$0$ dB/dec (flat)',
                     ', '.join(lv)])
    out.append(T.table(['frequency range', 'slope', 'asymptote level'], rows, 'lcl'))
    flats = [s for s in tf.segments() if s['slope'] == 0 and (s['w_lo'] or s['w_hi'])]
    if flats and not tf.zeros and tf.m == sum(1 for f in tf.factors if f.kind == 'hp'):
        out.append(f'The flat (pass-band) level is $20\\log_{{10}}|K| = 20\\log_{{10}}{num_tex(abs(tf.K))} = '
                   f'{sig(20 * math.log10(abs(tf.K)), 3)}$\\,dB.')
    out.append(T.figure(figname, width=r'0.78\linewidth', height='6.5cm'))
    out.append('{\\small Blue: the straight-line sketch you are expected to draw. Dashed grey: the exact curve '
               '(about 3\\,dB below the corner of an isolated pole). Red dot: the input frequency of Step 7.}')
    return '\n'.join(out)


# ----------------------------------------------------------------- Step 7: output
def output_section(tf, sig_in, vodc):
    w = sig_in.w
    out = []
    out.append(f'The input is ${sig_in.tex()}$, so $\\omega_{{in}} = 2\\pi\\cdot {num_tex(sig_in.f)} = '
               f'{num_tex(w)}$\\,rad/s. Put $s=j\\omega_{{in}}$ in each factor (tool T5): magnitudes multiply, '
               f'angles add.')
    out.append('{\\small Rules: $\\left|\\frac{s}{s+p}\\right| = \\frac{\\omega}{\\sqrt{\\omega^2+p^2}}$, '
               '$\\angle = \\frac{\\pi}{2}-\\tan^{-1}\\frac{\\omega}{p}$;\\quad '
               '$\\left|\\frac{1}{1+s/p}\\right| = \\frac{1}{\\sqrt{1+(\\omega/p)^2}}$, '
               '$\\angle = -\\tan^{-1}\\frac{\\omega}{p}$;\\quad '
               '$\\left|1+\\frac{s}{z}\\right| = \\sqrt{1+(\\omega/z)^2}$, $\\angle = \\tan^{-1}\\frac{\\omega}{z}$;'
               '\\quad a negative $K$ adds $-\\pi$.}')
    rows = []
    for f in tf.factors:
        v = f.at(w)
        rows.append([f.cell_tex(), '$' + num_tex(abs(v), 4) + '$',
                     '$' + num_tex(f.angle(w), 3) + '$'])
    mag = abs(tf.at(w))
    ang = tf.angle(w)
    rows.append(['\\textbf{total}', f'$\\mathbf{{{num_tex(mag, 4)}}}$ (product)',
                 f'$\\mathbf{{{num_tex(ang, 3)}}}$ (sum)'])
    out.append(T.table(['factor', 'magnitude', 'angle (rad)'], rows, 'ccc'))
    amp = mag * sig_in.A
    ph = sig_in.theta + ang
    ph_line = f'\\theta + \\angle H = {num_tex(ang, 3)}' if sig_in.ph == 0 else \
        f'\\theta + \\angle H = {pi_tex(sig_in.ph).lstrip("+")} + ({num_tex(ang, 3)}) = {num_tex(ph, 3)}'
    lines = [f'|H(j\\omega_{{in}})| &= {num_tex(mag, 3)}, \\qquad \\angle H(j\\omega_{{in}}) = {num_tex(ang, 3)}\\ \\mathrm{{rad}}',
             f'v_{{o,ac}}(t) &= {num_tex(mag, 3)}\\times {num_tex(sig_in.A)}\\,\\{sig_in.fn}\\left(2\\pi\\cdot '
             f'{num_tex(sig_in.f)}\\,t {"+" if ph >= 0 else "-"} {num_tex(abs(ph), 3)}\\right) = {num_tex(amp, 3)}\\,\\{sig_in.fn}\\left('
             f'2\\pi\\cdot {num_tex(sig_in.f)}\\,t {"+" if ph >= 0 else "-"} {num_tex(abs(ph), 3)}\\right)']
    out.append(T.align(lines))
    if sig_in.ph != 0:
        out.append(f'(phase: ${ph_line}$\\,rad.)')
    vo = vo_tex(sig_in, vodc, amp, ph)
    if vodc is not None and vodc != 0:
        out.append('Add the DC part from Step 2 (superposition):')
    out.append(T.eq('\\boxed{' + vo + '}'))
    return '\n'.join(out), amp, ph


def vo_tex(sig_in, vodc, amp, ph):
    acp = (f'{num_tex(amp, 3)}\\,\\{sig_in.fn}\\left(2\\pi\\cdot {num_tex(sig_in.f)}\\,t '
           f'{"+" if ph >= 0 else "-"} {num_tex(abs(ph), 3)}\\right)')
    if vodc:
        return f'V_o(t) = {num_tex(vodc, 3)} + {acp}\\ \\mathrm{{V}}'
    return f'V_o(t) = {acp}\\ \\mathrm{{V}}'


# ----------------------------------------------------------------- full solution
def solve(circ, sig_in, figs):
    """figs: dict with keys circuit, ac, dc, bode (file names relative to graphicspath)."""
    links, H, analyses = ac_chain(circ)
    tf = TF.from_expr(H)
    parts = []
    rails = circ.rails()
    dep = len(circ.stages) > 1
    # Step 1
    srcs = 'the AC input $V_i(t)$'
    if rails:
        srcs += ' and the DC supplies ' + ', '.join(f'${Vr(r)}$' for r in rails)
    s1 = f'Independent sources: {srcs}.'
    if dep:
        s1 += (' The diamond-shaped sources are \\emph{dependent} sources: they are not inputs, they only '
               'copy/scale a voltage that already exists in the circuit, so they stay in the circuit in every step.')
    if rails:
        s1 += (' Because there are both DC and AC sources, use superposition: '
               '$V_o(t) = V_{o,dc} + v_{o,ac}(t)$. Solve the DC circuit (Step 2) and the AC circuit '
               '(Steps 3--7) separately, then add.')
    else:
        s1 += ' There is no DC source, so $V_{o,dc}=0$ and $V_o(t)=v_{o,ac}(t)$: Step 2 is skipped.'
    parts.append('\\solstep{1}{Identify the sources}' + s1)
    vodc = 0.0
    if rails:
        txt, vodc = dc_section(circ, figs['dc'])
        parts.append('\\solstep{2}{DC circuit $\\Rightarrow V_{o,dc}$}' + txt)
    else:
        parts.append('\\solstep{2}{DC circuit}No DC sources: $V_{o,dc}=0$.')
    parts.append('\\solstep{3}{AC circuit}' + ac_circuit_section(circ, analyses, figs['ac']))
    parts.append('\\solstep{4}{Transfer function by a chain of dividers}' + chain_section(circ, links))
    parts.append(('Multiply the links and simplify (common factors cancel):' if len(links) > 1 else 'So:') +
                 T.eq('H(s) = ' + tf.rational_tex()))
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + bode_section(tf, figs['bode']))
    txt, amp, ph = output_section(tf, sig_in, vodc if rails else None)
    parts.append('\\solstep{7}{Steady-state output}' + txt)
    corners = ', '.join(f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    ans = ('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\quad (corners: ' + corners + ')\\\\[4pt]\n$'
           + vo_tex(sig_in, vodc if rails else 0, amp, ph) + '$\n\\end{ansbox}\n')
    parts.append(ans)
    return '\n'.join(parts), tf, dict(vodc=vodc, amp=amp, phase=ph)


def pipeline_card():
    return r"""
\begin{cardbox}{The Lecture-1 pipeline (use it for every problem in this set)}
\textbf{Tools --- this is all the theory you need:}
\begin{enumerate}[label=\textbf{T\arabic*},leftmargin=2.2em,itemsep=1pt]
\item \emph{Impedances:} $Z_R=R$, $Z_C=\frac{1}{sC}$, $Z_L=sL$. Series: add. Parallel:
      $Z_a\parallel Z_b=\frac{Z_aZ_b}{Z_a+Z_b}$.
\item \emph{Voltage divider:} if $Z_{top}$ connects $V_{in}$ to a node and $Z_{bot}$ is everything from that
      node to ground, then $V_{node}=V_{in}\,\frac{Z_{bot}}{Z_{top}+Z_{bot}}$.
\item \emph{Divider between two voltages (DC):} a node tied to $V_a$ through $R_a$ and to $V_b$ through $R_b$ sits at
      $V=V_b+(V_a-V_b)\frac{R_b}{R_a+R_b}$, and looks like a source $V$ with resistance $R_a\parallel R_b$
      (its Thevenin pair).
\item \emph{Dependent sources:} a VCVS forces $V=kV_x$; a VCCS drives the current $gV_x$ through the impedance $Z$
      hanging on its node, so $V=\pm gV_x Z$ (sign from the arrow).
\item \emph{Sinusoids:} $A\sin(\omega t+\theta)\ \to\ |H(j\omega)|\,A\sin\big(\omega t+\theta+\angle H(j\omega)\big)$.
\item \emph{Bode rules:} a pole at $p$ bends the magnitude by $-20$\,dB/dec above $p$, a zero by $+20$\,dB/dec;
      $\frac{1}{1+s/p}$ is $0$\,dB below $p$; $\frac{s}{s+p}$ is $0$\,dB above $p$.
\end{enumerate}
\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{Sources.} DC and AC both present $\Rightarrow$ superposition $V_o=V_{o,dc}+v_{o,ac}$.
\item \emph{DC circuit:} $V_i\to0$, $C\to$ open, $L\to$ short; reduce toward $V_o$ with T3.
\item \emph{AC circuit:} DC supplies $\to 0$ (rails become ground); merge parallel resistors.
\item \emph{Divider chain:} name the nodes from $V_i$ to $V_o$; $H=\prod$ (node-to-node ratios), each by T2 or T4,
      using the impedance seen looking right from each node.
\item \emph{Standard form:} simplify, find the roots, write $H=K\cdot\prod(\text{factors})$.
\item \emph{Bode:} start from the low-frequency slope, bend by $\pm20$\,dB/dec at each corner.
\item \emph{Output:} evaluate each factor at $s=j\omega_{in}$, multiply magnitudes, add angles, apply T5 and add $V_{o,dc}$.
\end{enumerate}
\end{cardbox}
"""
