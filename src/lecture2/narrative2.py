"""Worked solutions for Lecture 2 (op-amps). Every set follows the same Lecture-2 pipeline card;
steps 5-7 (standard form, Bode, sinusoidal output) are shared with Lecture 1."""
import math

import sympy as sp

from common.tf import TF, s, rational_tex, f_txt
from common.units import num_tex, sig
from common import texdoc as T
from lecture1.narrative import (standard_form_section, bode_section, output_section, vo_tex, Vt, Vr, Ohm, Rn)
from .blocks import zdefs, at0


def vn(n):
    return 'V_{' + n + '}'


# ---------------------------------------------------------------------------------------- DC
def chain_dc_section(chain):
    lines = ['DC rules: $V_i=0$ and every capacitor is an open circuit (no inductors appear in these circuits). '
             'A block passes DC with its gain at $s=0$, i.e. $H_k(0)$.']
    items = []
    vdc = 0.0
    for k, b in enumerate(chain.blocks):
        vi, vo = vn(chain.vin(k)), vn(chain.outs[k])
        if b.kind == 'sum':
            yi = at0(1 / b.zin.z())
            yd = at0(1 / b.zd.z())
            yf = at0(1 / b.zf.z())
            out = float(-(yi * sp.Rational(str(vdc)) + yd * sp.Rational(str(b.vdc))) / yf)
            zi, zd, zf = (b.zin.z_tex(), b.zd.z_tex(), b.zf.z_tex())
            rf, rd = 1 / float(yf), 1 / float(yd)
            if yi == 0 or vdc == 0:
                why = (f'${zi}$ contains a capacitor, so it is open and carries no DC current'
                       if yi == 0 else f'its input has no DC')
                items.append(
                    f'Block {k + 1} (summer): {why}. Only the supply drives a DC current, '
                    f'$\\frac{{V_{{DC}}}}{{{zd}}}$, through ${zf}$ (at DC ${zd}={Ohm(rd)}$, ${zf}={Ohm(rf)}$):'
                    + T.eq(f'{vo}\\big|_{{dc}} = -{zf}\\frac{{V_{{DC}}}}{{{zd}}} = -{Rn(rf)}\\cdot'
                           f'\\frac{{{num_tex(b.vdc)}}}{{{Rn(rd)}}} = {Vt(out)}'))
            else:
                ri = 1 / float(yi)
                items.append(
                    f'Block {k + 1} (summer): at DC ${zi}={Ohm(ri)}$, ${zd}={Ohm(rd)}$, ${zf}={Ohm(rf)}$:'
                    + T.eq(f'{vo}\\big|_{{dc}} = -{Rn(rf)}\\left(\\frac{{{num_tex(vdc)}}}{{{Rn(ri)}}} + '
                           f'\\frac{{{num_tex(b.vdc)}}}{{{Rn(rd)}}}\\right) = {Vt(out)}'))
        else:
            h0 = at0(b.H())
            out = float(h0) * vdc
            if vdc == 0:
                items.append(f'Block {k + 1}: its input has no DC, so ${vo}\\big|_{{dc}} = 0$.')
            else:
                items.append(f'Block {k + 1}: $H_{k + 1}(0) = {num_tex(float(h0))}$ (capacitors open), so '
                             f'${vo}\\big|_{{dc}} = {num_tex(float(h0))}\\times '
                             f'{"(" + num_tex(vdc) + ")" if vdc < 0 else num_tex(vdc)} = {Vt(out)}$.')
        vdc = out
    lines.append('\\begin{enumerate}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + i for i in items)
                 + '\n\\end{enumerate}\n')
    lines.append(T.eq(f'\\boxed{{V_{{o,dc}} = {Vt(vdc)}}}'))
    return '\n'.join(lines), vdc


# ---------------------------------------------------------------------------------------- AC, ideal
def chain_ac_section(chain):
    out = []
    n = len(chain.blocks)
    if n > 1:
        frs = '\\cdot'.join(f'\\frac{{{vn(chain.outs[k])}}}{{{vn(chain.vin(k))}}}' for k in range(n))
        out.append('Each op-amp output is an ideal voltage source, so a block\'s output does not change when the '
                   'next block is connected: the blocks can be solved one at a time and multiplied.'
                   + T.eq('H(s) = \\frac{V_o}{V_i} = ' + frs))
    loads = [k for k, b in enumerate(chain.blocks) if b.load is not None]
    if loads:
        names = ', '.join('$' + chain.blocks[k].load.z_tex() + '$' for k in loads)
        out.append(f'The load {names} hangs on an op-amp output (an ideal voltage source): it draws current but '
                   f'does not change the output voltage, so it drops out of $H(s)$.')
    for k, b in enumerate(chain.blocks):
        vi, vo = vn(chain.vin(k)), vn(chain.outs[k])
        part = f'\\textbf{{Block {k + 1} (U{k + 1}).}} ' + b.explain(vi, vo)
        defs = zdefs(b.named())
        if defs:
            part += T.align(defs)
        if b.H_tex() is not None:   # topologies end their KCL derivation with the result already
            part += T.eq(f'\\frac{{{vo}}}{{{vi}}} = {b.H_tex()} = {rational_tex(b.H())}')
        out.append(part)
    return '\n'.join(out)


# ---------------------------------------------------------------------------------------- AC, finite A
def chain_nonideal_section(chain, A0, fb):
    wb = 2 * math.pi * fb
    out = []
    out.append(f'Non-ideal op-amp model (tool T5): $V_{{out}} = A(s)\\,(V_+-V_-)$ with '
               f'$A(s)=\\dfrac{{A_0}}{{1+s/\\omega_b}}$, $A_0={num_tex(A0)}$, '
               f'$\\omega_b = 2\\pi\\cdot{num_tex(fb)} = {num_tex(wb)}$\\,rad/s, so the unity-gain frequency is '
               f'$\\omega_t = A_0\\omega_b = {num_tex(A0 * wb)}$\\,rad/s. The virtual short is \\emph{{not}} used; '
               f'only ``no current into the inputs\'\' is still true.')
    out.append('Recipe for each op-amp: write $V_+$ and $V_-$ by superposition of the block input and the op-amp '
               'output (each alone is a plain divider): $V_+ = \\alpha_+V_{in}$, $V_- = \\alpha_-V_{in}+\\beta V_{out}$. '
               'Then $V_{out} = A(\\alpha_+-\\alpha_-)V_{in} - A\\beta V_{out}$, i.e.'
               + T.eq('\\frac{V_{out}}{V_{in}} = \\frac{A(\\alpha_+-\\alpha_-)}{1+A\\beta} '
                      '= \\frac{G}{1+\\dfrac{1}{A\\beta}},\\qquad G = \\frac{\\alpha_+-\\alpha_-}{\\beta}'
                      '\\ \\text{(the ideal gain)}')
               + 'With $A(s)$ inserted and constant $\\alpha,\\beta$:'
               + T.eq('\\frac{V_{out}}{V_{in}} = G\\,\\frac{A_0\\beta}{1+A_0\\beta}\\cdot'
                      '\\frac{1}{1+\\dfrac{s}{\\omega_b(1+A_0\\beta)}},\\qquad '
                      '\\omega_b(1+A_0\\beta)\\approx\\beta\\,\\omega_t'))
    A = sp.Rational(str(A0)) / (1 + s / sp.Float(wb, 30))
    loads = [k for k, b in enumerate(chain.blocks) if b.load is not None]
    if loads:
        names = ', '.join('$' + chain.blocks[k].load.z_tex() + '$' for k in loads)
        out.append(f'The load {names} sits on an op-amp output, modelled as the ideal source $A(V_+-V_-)$: '
                   f'it does not change the output voltage and drops out.')
    stage_exprs = []
    for k, b in enumerate(chain.blocks):
        vi, vo = vn(chain.vin(k)), vn(chain.outs[k])
        ap, am, beta = b.ab()
        at = b.ab_tex(vi, vo)
        part = f'\\textbf{{Block {k + 1} (U{k + 1}).}} {at["note"]}'
        defs = zdefs(b.named())
        if defs:
            part += T.align(defs)
        part += T.align([at['plus'].replace('=', '&=', 1), at['minus'].replace('=', '&=', 1)])
        const = all(sp.simplify(sp.diff(sp.cancel(x), s)) == 0 for x in (ap, am, beta))
        if const:
            ap, am, beta = (float(sp.cancel(x)) for x in (ap, am, beta))
            G = (ap - am) / beta
            geff = G * A0 * beta / (1 + A0 * beta)
            wcl = wb * (1 + A0 * beta)
            elems = [e for z in b.named() for e in z.elems()]
            if elems and all(e.kind == 'C' for e in elems):
                part += ('(Only capacitors: every impedance is $\\frac{1}{sC}$, so in each ratio the $s$ cancels, '
                         'e.g. $\\frac{1/(sC_a)}{1/(sC_a)+1/(sC_b)} = \\frac{C_b}{C_a+C_b}$, and '
                         '$\\frac{1}{sC_a}\\parallel\\frac{1}{sC_b} = \\frac{1}{s(C_a+C_b)}$.) ')
            part += (f'So $\\alpha_+ = {num_tex(ap, 4)}$, $\\alpha_- = {num_tex(am, 4)}$, $\\beta = {num_tex(beta, 4)}$: '
                     f'ideal gain $G = \\frac{{\\alpha_+-\\alpha_-}}{{\\beta}} = {num_tex(G, 4)}$, '
                     f'$A_0\\beta = {num_tex(A0 * beta)}$.'
                     + T.eq(f'\\frac{{{vo}}}{{{vi}}} = {num_tex(G, 4)}\\cdot\\frac{{{num_tex(A0 * beta)}}}'
                            f'{{1+{num_tex(A0 * beta)}}}\\cdot\\frac{{1}}{{1+\\dfrac{{s}}{{{num_tex(wcl)}}}}}'
                            f' = \\frac{{{num_tex(geff, 4)}}}{{1+\\dfrac{{s}}{{{num_tex(wcl)}}}}}'))
            part += (f'(closed-loop bandwidth $\\omega_b(1+A_0\\beta) = {num_tex(wcl)}$\\,rad/s, '
                     f'$f = {f_txt(wcl)}$; compare $\\beta\\omega_t = {num_tex(beta * A0 * wb)}$\\,rad/s.)')
        else:
            part += ('Here $\\alpha$ and $\\beta$ depend on $s$, so substitute everything and simplify:'
                     + T.eq(f'\\frac{{{vo}}}{{{vi}}} = \\frac{{A(\\alpha_+-\\alpha_-)}}{{1+A\\beta}} = '
                            f'{rational_tex(chain.H_stage(k, A))}'))
        out.append(part)
        stage_exprs.append(chain.H_stage(k, A))
    return '\n'.join(out), stage_exprs


# ---------------------------------------------------------------------------------------- full chain solution
def solve_chain(chain, sig_in, figs, nonideal=None):
    """nonideal: None or (A0, fb_Hz)."""
    parts = []
    rails = chain.rails()
    srcs = 'the AC input $V_i(t)$'
    if rails:
        srcs += ' and the DC supply ' + ', '.join(f'${Vr(r)}$' for r in rails)
    s1 = f'Independent sources: {srcs}.'
    if rails:
        s1 += (' Both DC and AC are present, so use superposition: $V_o(t) = V_{o,dc}+v_{o,ac}(t)$. '
               'The DC part is Step 2, the AC part Steps 3--7.')
    else:
        s1 += ' No DC source: $V_{o,dc}=0$ and Step 2 is skipped.'
    parts.append('\\solstep{1}{Identify the sources}' + s1)
    vodc = 0.0
    if rails:
        txt, vodc = chain_dc_section(chain)
        parts.append('\\solstep{2}{DC circuit $\\Rightarrow V_{o,dc}$}' + txt)
    else:
        parts.append('\\solstep{2}{DC circuit}No DC sources: $V_{o,dc}=0$.')
    n = len(chain.blocks)
    if nonideal is None:
        nodal = [k for k, b in enumerate(chain.blocks) if getattr(b, 'nodal', False)]
        if nodal and n == 1:
            how = 'The circuit is not a standard block, so it is solved by nodal analysis (tools T3, T4).'
        elif nodal:
            how = ('Block 1 is not a standard block (nodal analysis, tools T3 and T4); the other blocks are standard '
                   '(block formulas, tool T2). The blocks still multiply because every op-amp output is an ideal '
                   'source.')
        elif n > 1:
            how = ('The circuit is a cascade of standard blocks, so each block is solved with its block formula '
                   '(tool T2).')
        else:
            how = 'The circuit is a standard block, so use its block formula (tool T2).'
        parts.append('\\solstep{3}{Op-amp rules}' + (
            f'{"Each op-amp has" if n > 1 or nodal else "The op-amp has"} negative feedback (its output is connected '
            f'back to its $-$ input), so with an ideal op-amp (tool T1): (a) no current flows into the $+$ or $-$ '
            f'input; (b) $V_-=V_+$ (virtual short). ' + how))
        parts.append('\\solstep{4}{Transfer function' + (' by nodal analysis}' if nodal and n == 1 else
                                                          ', block by block}') + chain_ac_section(chain))
        H = chain.H_ideal()
    else:
        A0, fb = nonideal
        txt, exprs = chain_nonideal_section(chain, A0, fb)
        parts.append('\\solstep{3}{Op-amp model}' + txt.split('Recipe')[0])
        parts.append('\\solstep{4}{Transfer function, op-amp by op-amp}Recipe' + txt.split('Recipe', 1)[1])
        H = sp.Integer(1)
        for e in exprs:
            H *= e
        if n > 1:
            parts.append('Each op-amp output is still an ideal source (it is $A(V_+-V_-)$), so the stages multiply.')
    tf = TF.from_expr(H)
    parts.append(('Multiply the blocks and simplify:' if n > 1 else 'So:') + T.eq('H(s) = ' + tf.rational_tex()))
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + bode_section(tf, figs['bode']))
    txt, amp, ph = output_section(tf, sig_in, vodc if rails else None)
    parts.append('\\solstep{7}{Steady-state output}' + txt)
    corners = ', '.join(f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\quad (corners: ' + corners + ')\\\\[4pt]\n$'
                 + vo_tex(sig_in, vodc if rails else 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), tf, H, dict(vodc=vodc, amp=amp, phase=ph)


# ---------------------------------------------------------------------------------------- slew rate
def solve_slew(chain, SR_vus, f_in, nonideal=None):
    """Maximum input amplitude before any op-amp output slews. Returns (tex, answer dict)."""
    w = 2 * math.pi * f_in
    SR = SR_vus * 1e6
    parts = []
    n = len(chain.blocks)
    outs = [vn(o) for o in chain.outs]
    parts.append('\\solstep{1}{What limits the input?}'
                 f'Every op-amp output must obey tool T6. For $V_i = A\\sin(\\omega_{{in}} t)$ each op-amp output is '
                 f'a sinusoid $|H_k(j\\omega_{{in}})|A\\sin(\\omega_{{in}}t+\\dots)$, so its fastest slope is '
                 f'$\\omega_{{in}}|H_k(j\\omega_{{in}})|A$. We need $|H_k(j\\omega_{{in}})|$ from $V_i$ to '
                 f'{"each op-amp output (" + ", ".join("$" + o + "$" for o in outs) + ")" if n > 1 else "the output"}. '
                 f'Here $\\omega_{{in}} = 2\\pi\\cdot{num_tex(f_in)} = {num_tex(w)}$\\,rad/s and '
                 f'$SR = {num_tex(SR_vus)}\\,\\mathrm{{V}}/\\mu\\mathrm{{s}} = {num_tex(SR)}\\,\\mathrm{{V/s}}$.'
                 + (' (A DC offset does not change the slope of a signal, so only the AC part matters.)'
                    if chain.has_dc() else ''))
    # step 2: block gains
    A = None
    if nonideal is not None:
        A0, fb = nonideal
        A = sp.Rational(str(A0)) / (1 + s / sp.Rational(repr(2 * math.pi * fb)))
    s2 = []
    if nonideal is not None:
        A0, fb = nonideal
        s2.append(f'Each op-amp has $A(s)=\\frac{{{num_tex(A0)}}}{{1+s/(2\\pi\\cdot{num_tex(fb)})}}$, so each block is '
                  f'$\\frac{{A(\\alpha_+-\\alpha_-)}}{{1+A\\beta}}$ (tool T5; $\\alpha,\\beta$ from dividers, as in the '
                  f'finite-gain set).')
    else:
        s2.append('Ideal op-amps: each block follows from its block formula (tool T2); a cascade multiplies, '
                  'so $|H_k| = \\prod_{j\\le k}|\\text{block } j|$.')
    rows = []
    mags = []
    run = 1.0
    for k, b in enumerate(chain.blocks):
        vi, vo = vn(chain.vin(k)), outs[k]
        Hk = chain.H_stage(k, A)
        mk = abs(complex(sp.cancel(Hk).subs(s, 1j * w)))
        run *= mk
        mags.append(run)
        defs = zdefs(b.named())
        txt = f'\\textbf{{Block {k + 1} (U{k + 1}).}} '
        if A is None:
            txt += b.explain(vi, vo) + (T.align(defs) if defs else '')
            txt += T.eq(f'\\frac{{{vo}}}{{{vi}}} = {b.H_tex()} = {rational_tex(b.H())}')
        else:
            ap, am, beta = b.ab()
            at = b.ab_tex(vi, vo)
            txt += at['note'] + (T.align(defs) if defs else '')
            txt += T.align([at['plus'].replace('=', '&=', 1), at['minus'].replace('=', '&=', 1)])
            txt += T.eq(f'\\frac{{{vo}}}{{{vi}}} = \\frac{{A(\\alpha_+-\\alpha_-)}}{{1+A\\beta}} = {rational_tex(Hk)}')
        txt += (f'At $s=j\\omega_{{in}}$: $\\left|\\frac{{{vo}}}{{{vi}}}\\right| = {num_tex(mk, 4)}$'
                + (f', so $|H_{k + 1}| = {num_tex(mags[k - 1], 4)}\\times{num_tex(mk, 4)} = {num_tex(run, 4)}$.'
                   if k else '.'))
        s2.append(txt)
        rows.append([f'${vo}$', f'${num_tex(run, 4)}$', f'${num_tex(run, 4)}A$', f'${num_tex(w * run, 4)}A$'])
    s2.append('{\\small (To evaluate a magnitude, put $s=j\\omega_{in}$ and use $|a+jb|=\\sqrt{a^2+b^2}$ for the '
              'numerator and the denominator separately.)}')
    parts.append('\\solstep{2}{Gain to every op-amp output at $\\omega_{in}$}' + '\n\n'.join(s2))
    kmax = max(range(n), key=lambda i: mags[i])
    hmax = mags[kmax]
    parts.append('\\solstep{3}{Which output slews first?}'
                 + T.table(['output', '$|H_k(j\\omega_{in})|$', 'amplitude', 'max slope $\\omega_{in}|H_k|A$ (V/s)'],
                           rows, 'cccc')
                 + (f'All op-amps have the same slew rate, so the output with the \\emph{{largest}} gain, '
                    f'${outs[kmax]}$, reaches the limit first.' if n > 1 else
                    'There is only one op-amp output.'))
    amax = SR / (w * hmax)
    parts.append('\\solstep{4}{Maximum input amplitude}'
                 + T.eq(f'\\omega_{{in}}\\,|H|\\,A \\le SR\\ \\Rightarrow\\ A_{{max}} = \\frac{{SR}}{{\\omega_{{in}}|H|}} = '
                        f'\\frac{{{num_tex(SR)}}}{{{num_tex(w)}\\times{num_tex(hmax, 4)}}} = '
                        f'{eng_v(amax)}'))
    parts.append('\\begin{ansbox}\n'
                 + (f'${outs[kmax]}$ distorts first. ' if n > 1 else '')
                 + f'$A_{{max}} = {eng_v(amax)}$ (input amplitude); at that point ${outs[kmax]}$ has amplitude '
                   f'${eng_v(amax * hmax)}$.\n\\end{{ansbox}}\n')
    return '\n'.join(parts), dict(amax=amax, which=chain.outs[kmax], mags=mags)


def eng_v(x):
    from common.units import eng_tex
    return eng_tex(x, '\\mathrm{V}')


# ---------------------------------------------------------------------------------------- design
def _wt(w):
    from common.tf import w_tex
    return w_tex(w)


def solve_design(tf, f_ref, sig_in, figs, chain, rows):
    from lecture1.narrative_1d import solve_1d
    from common.units import eng_tex
    from .design import R_IN
    head, _ = solve_1d(tf, f_ref, sig_in, dict(factors=figs['factors']))
    head = head.split('\\solstep{5}')[0]
    parts = [head]
    # ---- Step 5: stages
    stage_rows = []
    for k, r in enumerate(rows, 1):
        st = r['st']
        kind = r['kind']
        if kind == 'pz':
            fac = f'\\dfrac{{1+\\frac{{s}}{{{_wt(st["z"])}}}}}{{1+\\frac{{s}}{{{_wt(st["p"])}}}}}'
            blk = 'pole-zero: $Z_{in}=R\\parallel C$, $Z_f = R\\parallel C$'
        elif kind == 'lp':
            fac = f'\\dfrac{{1}}{{1+\\frac{{s}}{{{_wt(st["p"])}}}}}'
            blk = 'low-pass: $Z_{in}=R$, $Z_f=R\\parallel C$'
        elif kind == 'hp':
            fac = f'\\dfrac{{s}}{{s+{_wt(st["p"])}}}'
            blk = 'high-pass: $Z_{in}=R+\\frac{1}{sC}$, $Z_f=R$'
        elif kind == 'bp':
            fac = f'\\dfrac{{s}}{{s+{_wt(st["ph"])}}}\\cdot\\dfrac{{1}}{{1+\\frac{{s}}{{{_wt(st["pl"])}}}}}'
            blk = 'band-pass: $Z_{in}=R+\\frac{1}{sC}$, $Z_f=R\\parallel C$'
        else:
            fac = '1'
            blk = 'unity inverter (fixes the sign)'
        gain = num_tex(r['G'], 4)
        stage_rows.append([f'U{k}', f'${gain}$', f'$\\rule[-1.4em]{{0pt}}{{3.4em}}{fac}$', blk])
    n = len(rows)
    s5 = ('Every inverting stage of the form $-\\frac{Z_f}{Z_{in}}$ with $Z_{in}$, $Z_f$ made of one R and at most '
          'one C realizes \\emph{one} pole, optionally with one zero or one $s$ (tool T2). Pair each zero with a '
          'low-pass pole (pole-zero stage), each $\\frac{s}{s+p}$ with a remaining low-pass pole (band-pass stage), '
          'and give every leftover factor its own stage. Put all of $|K|$ into the first stage. Each stage '
          'inverts, so with an odd number of stages add a unity-gain inverter to make $K>0$.')
    s5 += T.table(['stage', 'gain $\\frac{R_2}{R_1}$', 'factor(s) realized', 'block'], stage_rows, 'cccl')
    parts.append('\\solstep{5}{Split $H(s)$ into op-amp stages}' + s5)
    # ---- Step 6: values
    items = []
    for k, r in enumerate(rows, 1):
        st, kind, p = r['st'], r['kind'], r['parts']
        nm = [e.tex for e in p]
        val = [eng_tex(float(e.value), '\\Omega' if e.kind == 'R' else '\\mathrm{F}') for e in p]
        if kind == 'inv':
            items.append(f'U{k}: ${nm[0]} = {nm[1]} = {val[0]}$ (gain $-1$).')
            continue
        txt = f'U{k}: choose ${nm[0]} = {val[0]}$, then '
        eqs = []
        if kind == 'pz':
            eqs.append(f'{nm[2]} = {num_tex(r["G"], 4)}\\,{nm[0]} = {val[2]}')
            eqs.append(f'{nm[1]} = \\frac{{1}}{{{num_tex(st["z"])}\\,{nm[0]}}} = {val[1]}')
            eqs.append(f'{nm[3]} = \\frac{{1}}{{{num_tex(st["p"])}\\,{nm[2]}}} = {val[3]}')
            form = f'-\\frac{{{nm[2]}}}{{{nm[0]}}}\\cdot\\frac{{1+s{nm[0]}{nm[1]}}}{{1+s{nm[2]}{nm[3]}}}'
        elif kind == 'lp':
            eqs.append(f'{nm[1]} = {num_tex(r["G"], 4)}\\,{nm[0]} = {val[1]}')
            eqs.append(f'{nm[2]} = \\frac{{1}}{{{num_tex(st["p"])}\\,{nm[1]}}} = {val[2]}')
            form = f'-\\frac{{{nm[1]}}}{{{nm[0]}}}\\cdot\\frac{{1}}{{1+s{nm[1]}{nm[2]}}}'
        elif kind == 'hp':
            eqs.append(f'{nm[1]} = \\frac{{1}}{{{num_tex(st["p"])}\\,{nm[0]}}} = {val[1]}')
            eqs.append(f'{nm[2]} = {num_tex(r["G"], 4)}\\,{nm[0]} = {val[2]}')
            form = f'-\\frac{{{nm[2]}}}{{{nm[0]}}}\\cdot\\frac{{s}}{{s+1/({nm[0]}{nm[1]})}}'
        else:
            eqs.append(f'{nm[1]} = \\frac{{1}}{{{num_tex(st["ph"])}\\,{nm[0]}}} = {val[1]}')
            eqs.append(f'{nm[2]} = {num_tex(r["G"], 4)}\\,{nm[0]} = {val[2]}')
            eqs.append(f'{nm[3]} = \\frac{{1}}{{{num_tex(st["pl"])}\\,{nm[2]}}} = {val[3]}')
            form = (f'-\\frac{{{nm[2]}}}{{{nm[0]}}}\\cdot\\frac{{s}}{{s+1/({nm[0]}{nm[1]})}}\\cdot'
                    f'\\frac{{1}}{{1+s{nm[2]}{nm[3]}}}')
        items.append(txt + 'match the stage formula $' + form + '$ to the factors:'
                     + T.eq(',\\qquad '.join(eqs)))
    s6 = (f'Use $R_1 = {eng_tex(R_IN, "\\Omega")}$ at the input of every stage (any convenient value works; it only '
          'scales the other parts). The corner of a factor $1+s/\\omega_c$ is matched by $RC = 1/\\omega_c$ '
          '(corners in rad/s).'
          + '\\begin{enumerate}[leftmargin=*,itemsep=2pt]\n' + '\n'.join('\\item ' + i for i in items)
          + '\n\\end{enumerate}\n')
    parts.append('\\solstep{6}{Component values}' + s6)
    # ---- Step 7: check + output
    s7 = ('The designed circuit:' + T.figure(figs['design'], width=r'\linewidth', height='5.5cm')
          + f'Check: the stage gains multiply to $(-1)^{{{n}}}\\cdot{num_tex(abs(tf.K), 4)}\\cdot(\\text{{factors}}) = H(s)$; '
          f'an independent nodal solve of this circuit reproduces $H(s)$ at every frequency. '
          f'{"(Standard-value resistors and capacitors would move the corners slightly.)"}')
    txt, amp, ph = output_section(tf, sig_in, None)
    parts.append('\\solstep{7}{Check and steady-state output}' + s7 + '\n\n' + txt)
    from .design import parts_txt
    comp = '\\\\\n'.join(f'U{k}: ' + parts_txt(r['parts']).replace('Ω', '$\\Omega$').replace('µ', '$\\mu$')
                         for k, r in enumerate(rows, 1))
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\\\[4pt]\n' + comp + '\\\\[4pt]\n$'
                 + vo_tex(sig_in, 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), dict(amp=amp, phase=ph)


# ---------------------------------------------------------------------------------------- card
def pipeline_card():
    return r"""
\begin{cardbox}{The Lecture-2 pipeline (use it for every problem in this lecture)}
\textbf{Tools --- this is all the theory you need (plus the Lecture-1 tools for impedances, dividers, Bode plots
and sinusoids):}
\begin{enumerate}[label=\textbf{T\arabic*},leftmargin=2.2em,itemsep=1pt]
\item \emph{Ideal op-amp with negative feedback:} no current into $+$ or $-$; $V_-=V_+$ (virtual short).
      Its output is an ideal voltage source (loads on it do not matter).
\item \emph{Block formulas:} inverting $\frac{V_o}{V_{in}}=-\frac{Z_f}{Z_{in}}$; non-inverting
      $\frac{V_o}{V_+}=1+\frac{Z_f}{Z_g}$ (with $V_+$ from the divider at the $+$ input); a follower has gain 1.
      Several blocks in cascade: multiply.
\item \emph{KCL with impedances:} at a node, $\sum_k \frac{V_{node}-V_k}{Z_k}=0$ (for a capacitor
      $\frac{1}{Z}=sC$). Write it at every node except op-amp outputs and source nodes.
\item \emph{Solving KCL equations:} pick the equation with the fewest unknowns, solve it for one node voltage,
      substitute into the rest; repeat until only $V_o$ and $V_i$ remain.
\item \emph{Finite gain:} $V_{out}=A(s)(V_+-V_-)$, $A(s)=\frac{A_0}{1+s/\omega_b}$, $\omega_t=A_0\omega_b$.
      With $V_+=\alpha_+V_{in}$, $V_-=\alpha_-V_{in}+\beta V_{out}$: $\frac{V_{out}}{V_{in}}=\frac{A(\alpha_+-\alpha_-)}{1+A\beta}$.
\item \emph{Slew rate:} for $V_{out}=\hat V\sin\omega t$, the fastest change is $\left|\frac{dV_{out}}{dt}\right|_{max}=\omega\hat V$;
      no distortion requires $\omega\hat V\le SR$.
\end{enumerate}
\textbf{Steps:}
\begin{enumerate}[leftmargin=2.2em,itemsep=1pt]
\item \emph{Sources.} DC and AC both present $\Rightarrow$ superposition.
\item \emph{DC circuit:} $V_i\to0$, $C\to$ open; pass the DC through each block with its gain at $s=0$.
\item \emph{Op-amp rules:} confirm negative feedback; apply T1 (or T5 for a non-ideal op-amp).
\item \emph{Transfer function:} standard blocks $\to$ T2; anything else $\to$ T3 + T4.
\item \emph{Standard form}, \ 6.~\emph{Bode}, \ 7.~\emph{Output} --- exactly as in Lecture 1.
\end{enumerate}
\emph{Variations:} a design problem runs these steps backwards (Bode plot $\to H(s)\to$ blocks $\to$ component values);
a slew-rate problem stops after Step 4 for every op-amp output and applies T6.
\end{cardbox}
"""
