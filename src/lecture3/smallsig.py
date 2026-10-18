"""Small-signal diode problems (Sample Problems 6-8): DC operating point (CVD or exponential model),
r_d = nV_T/I_D, then the AC circuit with the diode replaced by r_d, solved with the Lecture-1/2 pipelines."""
import copy
import math

import sympy as sp

from common.units import num_tex, eng_tex, sig
from common.tf import TF, s
from common import texdoc as T
from lecture1.ladder import El, Ser, Par, NamedZ, Series, Shunt, Circuit, ac_chain
from lecture1 import narrative as N1
from lecture2.chain import Chain
from lecture2 import narrative2 as N2
from .pwl import PNet, solve_state, state_section, X, A
from .circuits import from_ladder

VT = 0.025


class SSLadder:
    def __init__(self, level, items, vin, model='CVD', n=1.8, IS=None, note=''):
        self.level, self.items, self.vin, self.model, self.n, self.IS, self.note = level, items, vin, model, n, IS, note


class SSOpamp:
    """Inverting op-amp stage(s); the first block contains the diode (in zin or zf); the input is V_DC + v_i."""
    def __init__(self, level, blocks, vdc, vin, model='exp', n=1.8, IS=2.6e-9, note=''):
        self.level, self.blocks, self.vdc, self.vin = level, blocks, vdc, vin
        self.model, self.n, self.IS, self.note = model, n, IS, note


# ------------------------------------------------------------------------------------------ helpers
def replace_diodes(z, rd):
    """Copy of an impedance tree with every diode replaced by its small-signal resistance."""
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        if z.kind == 'D':
            return El('R', 'r_d' if len(rd) == 1 else f'r_{{d{z.name[1:]}}}', rd[z.name])
        return z
    if isinstance(z, Ser):
        return Ser(*[replace_diodes(p, rd) for p in z.parts])
    if isinstance(z, Par):
        return Par(*[replace_diodes(p, rd) for p in z.parts])
    return z


def diodes_in(z):
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        return [z] if z.kind == 'D' else []
    if isinstance(z, (Ser, Par)):
        return [d for p in z.parts for d in diodes_in(p)]
    return []


def mA(x):
    return eng_tex(x, '\\mathrm{A}')


def V(x):
    return eng_tex(x, '\\mathrm{V}')


def iterate(vth, rth, n, IS, steps=5):
    """V_D <-> I_D iteration for a diode fed by (V_th, R_th). Returns rows and the final (VD, ID)."""
    vd = 0.7
    rows = []
    for k in range(steps):
        idd = (vth - vd) / rth
        vd_new = n * VT * math.log(idd / IS)
        rows.append((k + 1, vd, idd, vd_new))
        vd = vd_new
    idd = (vth - vd) / rth
    return rows, vd, idd


def iteration_tex(rows, vth, rth, n, IS):
    tr = [[str(k), f'${num_tex(vd, 4)}$', f'$I_D = \\frac{{{num_tex(vth, 4)} - {num_tex(vd, 4)}}}{{{num_tex(rth, 4)}}} = '
           f'{mA(idd)}$', f'${num_tex(vn, 4)}$'] for k, vd, idd, vn in rows]
    return ('Two equations, two unknowns: the circuit gives $I_D = \\frac{V_{th}-V_D}{R_{th}}$ and the diode gives '
            f'$V_D = nV_T\\ln\\frac{{I_D}}{{I_S}}$ (tool T1, $n={num_tex(n)}$, $V_T = 25$\\,mV, '
            f'$I_S = {eng_tex(IS, "\\mathrm{A}")}$). Solve by iteration: guess $V_D = 0.7$\\,V, compute $I_D$, '
            'update $V_D$, repeat until nothing changes:'
            + T.table(['step', '$V_D$ used (V)', 'circuit $\\Rightarrow I_D$', 'diode $\\Rightarrow$ new $V_D$ (V)'],
                      tr, 'cccc'))


# ------------------------------------------------------------------------------------------ ladder family
def solve_ladder(p, figs):
    circ, pn = from_ladder(p.items, von=0.7)
    pn.fixed['i'] = sp.Integer(0)                # DC: the AC source is zero
    diodes = [el.name for el, _, _ in pn.diodes()]
    parts = []
    caps = [e.tex for e in circ.elements() if e.kind == 'C']
    rails = circ.rails()
    s1 = (f'DC rules (tool T3): $v_i = 0$ and every capacitor is open ($' + ', '.join(caps) + '$). '
          if caps else 'DC rules: $v_i=0$. ')
    on = frozenset(diodes)
    if p.model == 'CVD':
        res = solve_state(pn, on)
        st = dict(on=on, res=res, open_loop=[], conds=[])
        ids = {d: float(sp.limit(res['I_' + d], A, sp.oo)) for d in diodes}
        assert all(v > 0 for v in ids.values()), 'diode is not ON at the operating point'
        s1 += ('Assume the diode is ON (constant-voltage-drop model, $0.7$\\,V) and solve the DC circuit:'
               if len(diodes) == 1 else 'Assume both diodes are ON ($0.7$\\,V each) and solve the DC circuit:')
        txt = state_section(pn, st, diodes).split('Check the assumptions')[0]
        s1 += '\n\n' + txt + ' ' + ', '.join(f'$I_{{{d[0]}_{{{d[1:]}}}}} = {mA(ids[d])} > 0$' for d in diodes) + \
              ' \\checkmark, so the assumption holds.'
        vodc = float(sp.limit(res['o'], A, sp.oo))
    else:
        assert len(diodes) == 1
        d = diodes[0]
        off = solve_state(pn, frozenset())
        vth = float(off['VD_' + d])
        pn0 = copy.copy(pn)
        pn0.von = sp.Integer(0)
        short = solve_state(pn0, on)
        isc = float(short['I_' + d])
        rth = vth / isc
        s1 += ('With the exponential model the diode voltage is unknown, so first reduce the rest of the circuit to '
               'what the diode sees: a Thevenin source. Remove the diode and solve the circuit (Lecture 2 KCL): the '
               f'open-circuit voltage across it is $V_{{th}} = {V(vth)}$. Short the diode instead: the current is '
               f'$I_{{sc}} = {mA(isc)}$. So $R_{{th}} = \\frac{{V_{{th}}}}{{I_{{sc}}}} = {eng_tex(rth, "\\Omega")}$.')
        rows, vd, idd = iterate(vth, rth, p.n, p.IS)
        s1 += '\n\n' + iteration_tex(rows, vth, rth, p.n, p.IS)
        s1 += f'Converged: $V_D = {num_tex(vd, 4)}$\\,V, $I_D = {mA(idd)}$.'
        ids = {d: idd}
        pn1 = copy.copy(pn)
        pn1.von = sp.Rational(repr(vd))
        res = solve_state(pn1, on)
        vodc = float(sp.limit(res['o'], A, sp.oo))
        s1 += f' With this $V_D$ the rest of the DC circuit gives $V_{{o,dc}} = {V(vodc)}$.'
    parts.append('\\solstep{1}{DC operating point}' + s1 + T.eq(f'\\boxed{{V_{{o,dc}} = {V(vodc)}}}'))
    rd = {d: p.n * VT / ids[d] for d in diodes}
    parts.append('\\solstep{2}{Small-signal resistance}'
                 + ' '.join(f'$r_{{d}} = \\frac{{nV_T}}{{I_D}} = \\frac{{{num_tex(p.n)}\\times 25\\,\\mathrm{{mV}}}}'
                            f'{{{mA(ids[d])}}} = {eng_tex(rd[d], "\\Omega")}$' for d in diodes)
                 + ' (tool T3). For the AC analysis the diode is just this resistor.')
    # AC circuit: diodes -> r_d
    rdv = {d: sp.Rational(repr(rd[d])) for d in diodes}
    items_ac = []
    for it in p.items:
        it2 = copy.copy(it)
        if isinstance(it, (Series, Shunt)):
            it2.z = replace_diodes(it.z, {k: v for k, v in rd.items()})
        items_ac.append(it2)
    circ_ac = Circuit(items_ac)
    links, H, analyses = ac_chain(circ_ac)
    tf = TF.from_expr(H)
    parts.append('\\solstep{3}{AC circuit}' + N1.ac_circuit_section(circ_ac, analyses, figs['ac']))
    parts.append('\\solstep{4}{Transfer function by a chain of dividers}' + N1.chain_section(circ_ac, links)
                 + ('Multiply the links and simplify:' if len(links) > 1 else 'So:') + T.eq('H(s) = ' + tf.rational_tex()))
    return parts, tf, vodc, circ_ac, ids, rd


# ------------------------------------------------------------------------------------------ op-amp family
def solve_opamp(p, figs):
    Chain(p.blocks)   # names the blocks (U1, U2, ...)
    b = p.blocks[0]
    din = diodes_in(b.zin_raw)
    dfb = diodes_in(b.zf_raw)
    parts = []
    s1 = (f'DC rules (tool T3): $v_i = 0$, so the input is just $V_{{DC}} = {V(p.vdc)}$; capacitors are open. The op-amp '
          f'has negative feedback, so $V_- = V_+ = 0$ (virtual ground) and no current enters its inputs.')
    if din:
        d = din[0]
        series_r = [e for e in b.zin_raw.elems() if e.kind == 'R'] if isinstance(b.zin_raw, (Ser, Par)) else []
        if not series_r:
            vd = p.vdc
            idd = p.IS * math.exp(vd / (p.n * VT))
            s1 += (f' The diode sits between $V_{{DC}}$ and the virtual ground, so $V_D = V_{{DC}} = {V(vd)}$ and the '
                   f'exponential model (tool T1) gives'
                   + T.eq(f'I_D = I_S\\,e^{{V_D/nV_T}} = {eng_tex(p.IS, "\\mathrm{A}")}\\times '
                          f'\\exp\\left(\\frac{{{num_tex(vd)}}}{{{num_tex(p.n)}\\times 0.025}}\\right) = {mA(idd)}'))
        else:
            rs = float(series_r[0].value)
            rows, vd, idd = iterate(p.vdc, rs, p.n, p.IS)
            s1 += (f' The diode and ${series_r[0].tex}$ connect $V_{{DC}}$ to the virtual ground: the diode sees '
                   f'$V_{{th}} = V_{{DC}}$ through $R_{{th}} = {series_r[0].tex} = {eng_tex(rs, "\\Omega")}$.\n\n'
                   + iteration_tex(rows, p.vdc, rs, p.n, p.IS) + f'Converged: $I_D = {mA(idd)}$.')
        rf = [e for e in b.zf_raw.elems() if e.kind == 'R']
        rfv = float(rf[0].value)
        vodc = -idd * rfv
        s1 += (f' All of $I_D$ continues through the feedback resistor ${rf[0].tex}$ (the capacitor is open), so'
               + T.eq(f'V_{{o,dc}} = 0 - {rf[0].tex}I_D = -{num_tex(rfv)}\\times{num_tex(idd, 4)} = {V(vodc)}'))
    else:
        d = dfb[0]
        rin = [e for e in b.zin_raw.elems() if e.kind == 'R'][0]
        idd = p.vdc / float(rin.value)
        s1 += (f' The input current $\\frac{{V_{{DC}} - 0}}{{{rin.tex}}} = {mA(idd)}$ cannot enter the op-amp: all of '
               f'it flows through the diode, $I_D = {mA(idd)}$.')
        if p.model == 'CVD':
            vd = 0.7
            s1 += ' Constant-voltage-drop model: $V_D = 0.7$\\,V.'
        else:
            vd = p.n * VT * math.log(idd / p.IS)
            s1 += (' Exponential model (tool T1):' + T.eq(
                f'V_D = nV_T\\ln\\frac{{I_D}}{{I_S}} = {num_tex(p.n)}\\times 0.025\\times\\ln\\frac{{{num_tex(idd, 4)}}}'
                f'{{{num_tex(p.IS)}}} = {V(vd)}'))
        extra = [e for e in b.zf_raw.elems() if e.kind == 'R']
        vr = sum(float(e.value) for e in extra) * idd
        vodc = -(vd + vr)
        drop = f'V_D + {extra[0].tex}I_D' if extra else 'V_D'
        s1 += (f' The diode current flows from the $-$ input (at 0\\,V) toward the output, so the output sits '
               f'${drop}$ below it:' + T.eq(f'V_{{o,dc}} = -({drop}) = {V(vodc)}'))
    ids = {d.name: idd}
    vin_dc = vodc
    for k, bb in enumerate(p.blocks[1:], 2):
        from lecture2.blocks import at0
        h0 = float(at0(bb.H()))
        s1 += (f' Block {k} passes DC with its gain at $s=0$, $H_{k}(0) = {num_tex(h0, 4)}$: '
               f'$V_{{dc}} = {num_tex(h0, 4)}\\times {num_tex(vin_dc, 4)} = {V(h0 * vin_dc)}$.')
        vin_dc *= h0
    vodc = vin_dc
    parts.append('\\solstep{1}{DC operating point}' + s1 + T.eq(f'\\boxed{{V_{{o,dc}} = {V(vodc)}}}'))
    rd = {d.name: p.n * VT / idd}
    parts.append('\\solstep{2}{Small-signal resistance}'
                 + f'$r_d = \\frac{{nV_T}}{{I_D}} = \\frac{{{num_tex(p.n)}\\times 25\\,\\mathrm{{mV}}}}{{{mA(idd)}}} = '
                   f'{eng_tex(rd[d.name], "\\Omega")}$ (tool T3). For the AC analysis the diode is just this resistor, '
                   'and $V_{DC}$ is replaced by a short (AC ground).')
    # AC chain with the diode replaced
    import lecture2.blocks as B
    blocks_ac = []
    for bb in p.blocks:
        nb = copy.copy(bb)
        for attr in ('zin_raw', 'zf_raw', 'zg_raw', 'za_raw', 'zb_raw', 'zm_raw'):
            if hasattr(bb, attr) and getattr(bb, attr) is not None:
                setattr(nb, attr, replace_diodes(getattr(bb, attr), rd))
        blocks_ac.append(nb)
    chain_ac = Chain(blocks_ac)
    H = chain_ac.H_ideal()
    tf = TF.from_expr(H)
    parts.append('\\solstep{3}{AC circuit}' + T.figure(figs['ac'], width=r'0.9\linewidth', height='5cm'))
    parts.append('\\solstep{4}{Transfer function}' + N2.chain_ac_section(chain_ac)
                 + ('Multiply the blocks and simplify:' if len(blocks_ac) > 1 else 'So:') + T.eq('H(s) = ' + tf.rational_tex()))
    return parts, tf, vodc, chain_ac, ids, rd


def finish(parts, tf, vodc, sig_in, figs, vd_amp, n):
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + N1.standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + N1.bode_section(tf, figs['bode']))
    txt, amp, ph = N1.output_section(tf, sig_in, vodc)
    check = ''
    if vd_amp is not None:
        check = (f' Check the small-signal assumption: the AC voltage across the diode has amplitude about '
                 f'${V(vd_amp)}$, well below $nV_T = {V(n * VT)}$ \\checkmark.' if vd_amp < 0.3 * n * VT else
                 f' Small-signal check: the AC voltage across the diode is about ${V(vd_amp)}$, not much smaller than '
                 f'$nV_T={V(n * VT)}$, so the result is only approximate.')
    parts.append('\\solstep{7}{Total output (DC + AC)}' + txt + check)
    corners = ', '.join(N1.f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$\\quad (corners: ' + corners + ')\\\\[4pt]\n$'
                 + N1.vo_tex(sig_in, vodc, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), amp, ph
