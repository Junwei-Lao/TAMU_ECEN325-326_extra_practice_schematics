"""Set 5F: MOSFET circuits where a Thevenin equivalent is the efficient route (DC and AC)."""
import math

import sympy as sp

from common.units import num_tex, eng_tex
from common.tf import s, TF, f_txt
from common import texdoc as T
from lecture1 import narrative as N1
from .mosnet import M, R, C, Col, BJTCircuit, Src, Load, mos_params
from .thev5 import Ladder, march, columns
from .dc5 import exact_dc5, vgs_sym, id_sym, I_, V_, par, quad_text
from .ac5 import ACView5, solve_ac5, Stage


class TDev:
    """One transistor. gate: Ladder, the name of another node (e.g. 'd1'), or 0. source/drain: Ladder or a supply."""
    def __init__(self, q, gate, source, drain):
        self.q, self.gate, self.source, self.drain = q, gate, source, drain

    @property
    def k(self):
        return self.q.name[1:]


class TProb:
    """devs in solving order. ac: None (a DC problem) or dict(stages=[('M1', 'CS'), ...], load=(node, C, R_L))."""
    def __init__(self, level, devs, ac=None, vin=None, note=''):
        self.level, self.devs, self.ac, self.vin, self.note = level, devs, ac, vin, note


def num(x):
    return isinstance(x, (int, float))


def build(p):
    cols, links, src = [], [], None
    for dv in p.devs:
        q, k = dv.q, dv.k
        if isinstance(dv.gate, Ladder):
            c_, l_, s_ = columns(dv.gate)
            cols += list(reversed(c_))          # far end leftmost, the gate's own node next to the transistor
            links += l_
            src = src or s_
            q.base = dv.gate.terminal
        else:
            q.base = dv.gate if dv.gate != 0 else '0'
        top_spec, bot_spec = (dv.drain, dv.source) if q.s > 0 else (dv.source, dv.drain)
        top_name, bot_name = (f'd{k}', f's{k}') if q.s > 0 else (f's{k}', f'd{k}')
        stack = ([] if num(top_spec) else [top_name]) + [q] + ([] if num(bot_spec) else [bot_name])
        cols.append(Col(stack, top=top_spec if num(top_spec) else None,
                        bottom=bot_spec if num(bot_spec) else None))
        for lad in (dv.drain, dv.source):
            if isinstance(lad, Ladder):
                c_, l_, s_ = columns(lad)
                cols += c_
                links += l_
                src = src or s_
    load = None
    if p.ac:
        node, cap, rl = p.ac['load']
        load = Load(node, c=cap, rl=rl)
    sobj = None
    if src:
        node, z = src
        sobj = Src(node, rs=None if z.kind == 'C' else z, c=z if z.kind == 'C' else None)
    return BJTCircuit(cols, src=sobj, load=load, links=links)


def n_internal(circ):
    """Unknown node voltages of the full circuit (what plain KCL would have to solve for)."""
    from lecture4.dc import flat_resistors
    nodes = set()
    for el, a, b in flat_resistors(circ):
        nodes.update((a, b))
    for q in circ.bjts:
        nodes.update((q.b, q.c, q.e))
    return len(nodes - set(circ.fixed))


# ------------------------------------------------------------------------------------------ DC
def dc_solve(p, circ, text=True):
    """Thevenin-based DC solution. Returns (latex parts, V {node: volts} of the terminals, ID, VG)."""
    disp = circ.disp
    V, ID, VG = {}, {}, {}
    parts = []
    eq_cols = []
    for dv in p.devs:
        q, k = dv.q, dv.k
        t = []
        # gate
        if isinstance(dv.gate, Ladder):
            vth, rth, st = march(dv.gate, 'dc', disp)
            vg = float(vth)
            t.append(f'\\emph{{Gate network}} (seen from the gate of ${q.tex}$, transistor removed). '
                     + ' '.join(st) + f' No current flows into the gate, so only $V_{{th}}$ matters: '
                     f'${disp(q.b)} = V_{{th,G{k}}} = {V_(vg)}$.')
            rg = float(rth)
        elif dv.gate == 0:
            vg, rg = 0.0, 0.0
        else:
            vg, rg = V[dv.gate], 0.0
            t.append(f'The gate of ${q.tex}$ is node ${disp(dv.gate)}$, already known: ${disp(q.b)} = {V_(vg)}$.')
        V[q.b] = vg
        # source
        if isinstance(dv.source, Ladder):
            vts, rts, st = march(dv.source, 'dc', disp)
            vts, rts = float(vts), float(rts)
            t.append(f'\\emph{{Source network}} (seen from the source of ${q.tex}$). ' + ' '.join(st))
        else:
            vts, rts = float(dv.source), 0.0
        # drain
        if isinstance(dv.drain, Ladder):
            vtd, rtd, st = march(dv.drain, 'dc', disp)
            vtd, rtd = float(vtd), float(rtd)
            t.append(f'\\emph{{Drain network}} (seen from the drain of ${q.tex}$). ' + ' '.join(st))
        else:
            vtd, rtd = float(dv.drain), 0.0
        # one quadratic
        veff = q.s * (vg - vts)
        if rts == 0:
            vgs = veff
            ID[q.name] = q.id_of(vgs - q.vt)
            t.append(f'The source is held at ${num_tex(vts)}$\\,V: ${vgs_sym(q)} = {num_tex(vgs, 4)}$\\,V and '
                     f'${id_sym(q)} = \\frac{{k}}{{2}}V_{{ov}}^2 = {I_(ID[q.name])}$.')
        else:
            a = rts * q.k / 2
            b = 1 - 2 * a * q.vt
            c = a * q.vt ** 2 - veff
            disc = b * b - 4 * a * c
            r1, r2 = (-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)
            vgs, other = (r1, r2) if r1 > q.vt else (r2, r1)
            ID[q.name] = q.id_of(vgs - q.vt)
            lhs = f'V_{{G{k}}} - V_{{th,S{k}}}' if q.s > 0 else f'V_{{th,S{k}}} - V_{{G{k}}}'
            qt, why = quad_text(a, b, c, None, vgs, other, vgs_sym(q), q.vt)
            t.append(f'With the networks replaced, ${q.tex}$ sees one loop: gate at ${V_(vg)}$, source through '
                     f'$R_{{th,S{k}}} = {eng_tex(rts, chr(92) + "Omega")}$ to $V_{{th,S{k}}} = {V_(vts)}$. KVL '
                     f'(assume ${q.tex}$ active):\\[{lhs} = {num_tex(veff, 4)} = {vgs_sym(q)} + R_{{th,S{k}}}{id_sym(q)},'
                     f'\\qquad {id_sym(q)} = \\frac{{{eng_tex(q.k, "")}}}{{2}}({vgs_sym(q)} - {num_tex(q.vt)})^2\\]'
                     f'\\[{qt}\\]{why} So ${id_sym(q)} = {I_(ID[q.name])}$.')
        VG[q.name] = vgs
        V[q.e] = vg - q.s * vgs
        V[q.c] = vtd - q.s * rtd * ID[q.name]
        t.append(f'Terminal voltages: ${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} {vgs_sym(q)} = {V_(V[q.e])}$'
                 + (f', ${disp(q.c)} = V_{{th,D{k}}} {"-" if q.s > 0 else "+"} R_{{th,D{k}}}{id_sym(q)} = {num_tex(vtd, 4)} '
                    f'{"-" if q.s > 0 else "+"} {eng_tex(rtd, "")}\\times{I_(ID[q.name])} = {V_(V[q.c])}$'
                    if rtd else f', ${disp(q.c)} = {V_(V[q.c])}$') + '.')
        vds = q.s * (V[q.c] - V[q.e])
        vov = vgs - q.vt
        good = vds >= vov
        nm = 'DS' if q.s > 0 else 'SD'
        t.append(f'Check: $V_{{{nm}{k}}} = {num_tex(vds, 4)}$\\,V ' +
                 (f'$\\ge V_{{ov{k}}} = {num_tex(vov, 3)}$\\,V: ${q.tex}$ is active \\checkmark' if good else
                  f'$< V_{{ov{k}}}$: triode!'))
        assert good, f'{q.name} not active'
        parts.append((q, t))
        eq_cols.append((q, vg, rg, vts, rts, vtd, rtd))
    return parts, V, ID, VG, eq_cols


def equivalent_circuit(p, eq_cols):
    """The reduced circuit: every network replaced by its Thevenin pair (drawn as resistor + supply)."""
    cols = []
    for q0, vg, rg, vts, rts, vtd, rtd in eq_cols:
        k = q0.name[1:]
        q = M(q0.name, 'nmos' if q0.s > 0 else 'pmos', kw=q0.kw, vt=q0.vt, wl=q0.wl, kp=q0.kp)
        gate = f'g{k}'
        q.base = gate
        if rg:
            cols.append(Col([R(f'R_{{thG{k}}}', repr(rg)), gate], top=round(vg, 3), bottom=None, gap=3.2))
        else:
            cols.append(Col([gate], top=round(vg, 3), bottom=None, gap=1.5))
        top = (round(vtd, 3), rtd, f'R_{{thD{k}}}') if q.s > 0 else (round(vts, 3), rts, f'R_{{thS{k}}}')
        bot = (round(vts, 3), rts, f'R_{{thS{k}}}') if q.s > 0 else (round(vtd, 3), rtd, f'R_{{thD{k}}}')
        stack = ([R(top[2], repr(top[1]))] if top[1] else []) + [q] + ([R(bot[2], repr(bot[1]))] if bot[1] else [])
        cols.append(Col(stack, top=top[0], bottom=bot[0]))
    return BJTCircuit(cols)


def statement_dc(p, circ):
    nodes = ', '.join(f'${circ.disp(n)}$' for dv in p.devs for n in (dv.q.e, dv.q.c))
    return ('For the circuit below, find the DC drain current of every transistor, the voltages ' + nodes
            + ' and the operating mode. Assume ' + mos_params(circ) + '. Hint: plain node-by-node KCL is long here; '
            'look for a faster way.' + ((' ' + p.note) if p.note else ''))


def dc_solution(p, figs):
    circ = build(p)
    parts, V, ID, VG, eq = dc_solve(p, circ)
    n = n_internal(circ)
    nets = sum(isinstance(x, Ladder) for dv in p.devs for x in (dv.gate, dv.source, dv.drain))
    body = ['\\solstep{1}{Why Thevenin}Plain KCL would need all ' + str(n) + ' unknown node voltages at once, and the '
            'transistor equation is quadratic, so the elimination by hand is long. But each transistor touches every '
            'resistor network at a single terminal, and the gate draws no current. So every network can be replaced '
            'by its Thevenin pair $(V_{th}, R_{th})$ (tool T5), computed with the transistor removed --- '
            + ('one network' if nets == 1 else f'{nets} small networks') + ', each a chain of dividers. What is left is '
            'one loop per transistor with a single quadratic.']
    i = 2
    for q, t in parts:
        body.append(f'\\solstep{{{i}}}{{Transistor ${q.tex}$}}' + '\n\n'.join(t))
        i += 1
    body.append(f'\\solstep{{{i}}}{{Equivalent circuit}}With every network replaced by its Thevenin pair the circuit '
                'is just this (the solution above is the analysis of this circuit):'
                + T.figure(figs['equivalent'], width=r'0.6\linewidth', height='5cm'))
    Vx, IDx = exact_dc5(circ, V)
    err = max(abs(ID[n_] - IDx[n_]) / IDx[n_] for n_ in ID)
    body.append('A full nodal solve of the original circuit (all ' + str(n) + ' node voltages) gives the same currents.')
    ans = ',\\quad '.join(f'${id_sym(dv.q)} = {I_(ID[dv.q.name])}$, ${circ.disp(dv.q.e)} = {V_(V[dv.q.e])}$, '
                          f'${circ.disp(dv.q.c)} = {V_(V[dv.q.c])}$' for dv in p.devs)
    body.append('\\begin{ansbox}\n' + ans + '\\\\[2pt] all transistors active.\n\\end{ansbox}\n')
    return '\n'.join(body), circ, ID, err, equivalent_circuit(p, eq)


# ------------------------------------------------------------------------------------------ AC
def ac_solution(p, figs):
    circ = build(p)
    _, V, ID, VG, _ = dc_solve(p, circ)
    Vx, IDx = exact_dc5(circ, V)
    assert max(abs(ID[n_] - IDx[n_]) / IDx[n_] for n_ in ID) < 1e-6
    devs = {dv.q.name: dv for dv in p.devs}
    stages = [Stage(devs[nm].q, conf) for nm, conf in p.ac['stages']]
    first = stages[0]
    dv1 = devs[first.q.name]
    lad = dv1.gate if first.conf in ('CS', 'CD') else dv1.source
    disp = circ.disp
    vth, zth, st = march(lad, 'ac', disp)
    vth, zth = sp.cancel(sp.together(vth)), sp.cancel(sp.together(zth))
    ap, Hrest, view = solve_ac5(circ, ID, stages, skip_input=True)
    k = first.q.name[1:]
    parts = []
    cur = ', '.join(f'${id_sym(s_.q)} = {I_(ID[s_.q.name])}$' for s_ in stages)
    parts.append('\\solstep{1}{DC currents and transconductances}The DC drain currents are given: ' + cur
                 + '. For AC every supply is ground and every ``$\\infty$\'\' capacitor is a short. ' + ap[0])
    gm = sp.Rational(repr(view.gm[first.q.name]))
    if first.conf in ('CS', 'CD'):
        ratio = vth
        from common.tf import rational_tex
        tail = (f'No current flows into the gate, so $Z_{{th}}$ plays no role: \\[\\frac{{v_{{g{k}}}}}{{v_i}} = '
                f'\\frac{{V_{{th}}}}{{v_i}} = {rational_tex(ratio)}\\]')
        where = 'gate'
    else:
        from common.tf import rational_tex
        ratio = sp.cancel(sp.together(vth * (1 / gm) / (zth + 1 / gm)))
        tail = (f'The source of the common-gate stage presents $1/g_{{m{k}}} = {eng_tex(float(1 / gm), chr(92) + "Omega")}$ '
                f'to this Thevenin source, a voltage divider: \\[\\frac{{v_{{s{k}}}}}{{v_i}} = \\frac{{V_{{th}}}}{{v_i}}'
                f'\\cdot\\frac{{1/g_{{m{k}}}}}{{Z_{{th}} + 1/g_{{m{k}}}}} = {rational_tex(ratio)}\\]')
        where = 'source'
    n = n_internal(circ)
    parts.append(f'\\solstep{{2}}{{Thevenin equivalent of the input network}}Between $v_i$ and the {where} of '
                 f'${first.q.tex}$ there is a whole network (with KCL: one equation per node, in $s$). The transistor '
                 f'touches it only at its {where}, so replace it by its Thevenin pair $(V_{{th}}(s), Z_{{th}}(s))$ seen from '
                 f'there (tool T5), marching from the far end: ' + ' '.join(st) + ' ' + tail)
    parts.append('\\solstep{3}{Rest of the signal path}' + ap[1] + ap[2])
    H = sp.cancel(sp.together(ratio * Hrest))
    tf = TF.from_expr(H)
    parts.append('\\solstep{4}{Transfer function}Multiply and simplify:' + T.eq('H(s) = ' + tf.rational_tex()))
    parts.append('\\solstep{5}{Standard (Bode-ready) form}' + N1.standard_form_section(tf))
    parts.append('\\solstep{6}{Magnitude Bode plot}' + N1.bode_section(tf, figs['bode']))
    txt, amp, ph = N1.output_section(tf, p.vin, None)
    parts.append('\\solstep{7}{Steady-state output}' + txt)
    corners = ', '.join(f_txt(w).replace('µ', '$\\mu$') for w, _ in tf.corners())
    parts.append('\\begin{ansbox}\n$H(s) = ' + tf.bode_form_tex() + '$'
                 + (f'\\quad (corners: {corners})' if corners else '')
                 + '\\\\[4pt]\n$' + N1.vo_tex(p.vin, 0, amp, ph) + '$\n\\end{ansbox}\n')
    return '\n'.join(parts), circ, tf, view, ID, dict(amp=amp, phase=ph), stages


def statement_ac(p, circ, ID, stages):
    cur = ', '.join(f'${id_sym(s_.q)} = {I_(ID[s_.q.name])}$' for s_ in stages)
    return (r'For the amplifier below, find the small-signal transfer function $H(s)=\dfrac{V_o(s)}{V_i(s)}$ and sketch '
            r'its magnitude Bode plot. Also find the steady-state output $V_o(t)$ for $' + p.vin.tex() + r'$. Assume '
            + mos_params(circ) + r', $r_o = \infty$; the DC drain currents are ' + cur
            + '. Hint: look for a faster way than writing KCL at every node.' + ((' ' + p.note) if p.note else ''))
