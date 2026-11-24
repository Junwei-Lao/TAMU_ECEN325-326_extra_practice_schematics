"""Small-signal analysis of MOSFET amplifiers with the node-impedance method of the slides (r_o = infinity):
    Z_gate = infinity, Z_drain = infinity, Z_source = 1/g_m
    CS: v_d/v_g = -Z_D/(1/g_m + Z_S)   CD: v_s/v_g = Z_S/(1/g_m + Z_S)   CG: v_d/v_s = Z_D/(1/g_m)
An exact nodal solve (gate draws nothing, i_d = g_m v_gs from drain to source) is the independent check."""
import math

import sympy as sp

from common.tf import s, rational_tex
from common.units import eng_tex
from common import texdoc as T
from lecture1.ladder import El, Ser, NamedZ
from lecture4.ac import ACView, impedance_tree, ztex

CONF = {'CS': ('b', 'c'), 'CG': ('e', 'c'), 'CD': ('b', 'e')}
LET = {'b': 'g', 'c': 'd', 'e': 's'}


class Stage:
    def __init__(self, q, conf):
        self.q, self.conf = q, conf


class ACView5(ACView):
    def __init__(self, circ, ID):
        super().__init__(circ, ID)
        self.gm = {q.name: math.sqrt(2 * q.k * ID[q.name]) for q in circ.bjts}

    def exact(self, out):
        circ = self.circ
        nodes = set()
        for z, a, b in self.br:
            nodes.update((a, b))
        for q in circ.bjts:
            nodes.update((self.f(q.b), self.f(q.c), self.f(q.e)))
        nodes -= {'0', 'vi'}
        V = {n: sp.Symbol('V_' + n) for n in nodes}

        def v(n):
            return 0 if n == '0' else (1 if n == 'vi' else V[n])

        eqs = {n: 0 for n in nodes}
        for z, a, b in self.br:
            y = 1 / z.z()
            if a in eqs:
                eqs[a] += y * (v(a) - v(b))
            if b in eqs:
                eqs[b] += y * (v(b) - v(a))
        for q in circ.bjts:
            gm = sp.Rational(repr(self.gm[q.name]))
            g, d, src = self.f(q.b), self.f(q.c), self.f(q.e)
            i = gm * (v(g) - v(src))          # small-signal drain current, drain -> source (NMOS and PMOS alike)
            if d in eqs:
                eqs[d] += i
            if src in eqs:
                eqs[src] -= i
        sol = sp.solve(list(eqs.values()), list(V.values()), dict=True)[0]
        return sp.cancel(sp.together(sol[V[self.f(out)]]))


def gmr(view, q):
    return sp.Rational(repr(view.gm[q.name]))


def solve_ac5(circ, ID, stages, skip_input=False):
    """Returns (latex parts [g_m, input resistances, gains], H, view)."""
    view = ACView5(circ, ID)
    f = view.f
    parts = []
    rows = []
    for st in stages:
        q = st.q
        k = q.name[1:]
        vov = q.vov(ID[q.name])
        gm = view.gm[q.name]
        rows.append(f'g_{{m{k}}} &= k_{{{k}}}V_{{ov{k}}} = \\sqrt{{2k_{{{k}}}I_{{D{k}}}}} = '
                    f'\\sqrt{{2\\cdot{eng_tex(q.k, chr(92) + "mathrm{A/V^2}")}\\cdot{eng_tex(ID[q.name], chr(92) + "mathrm{A}")}}}'
                    f' = {eng_tex(gm, chr(92) + "mathrm{A/V}")},\\qquad \\frac{{1}}{{g_{{m{k}}}}} = '
                    f'{eng_tex(1 / gm, chr(92) + "Omega")}\\quad(V_{{ov{k}}} = {vov:.3g}\\,\\mathrm{{V}})')
    parts.append('Transconductances (tool T4):' + T.align(rows))
    # input resistances: only a common-gate stage presents a finite resistance (1/g_m at its source)
    inputs = {}
    lines = []
    for st in reversed(stages):
        q = st.q
        k = q.name[1:]
        if st.conf == 'CG':
            ri = 1 / gmr(view, q)
            z = NamedZ(f'R_{{i{k}}}', El('R', f'R_{{i{k}}}', 1))
            z.z = (lambda v=ri: v)
            inputs[f(q.e)] = z
            lines.append(f'R_{{i{k}}} &= Z_{{source,{k}}} = \\frac{{1}}{{g_{{m{k}}}}} = {eng_tex(float(ri), chr(92) + "Omega")}'
                         '\\quad\\text{(common gate)}')
        else:
            lines.append(f'R_{{i{k}}} &= Z_{{gate,{k}}} = \\infty\\quad\\text{{(input at the gate: it loads nothing)}}')
    parts.append('Input resistance of every stage, from the last back to the first (each one loads the stage before '
                 'it):' + T.align(list(reversed(lines))))
    # gains along the path
    gl, frs = [], []
    H = sp.Integer(1)
    first = stages[0]
    nin = f(getattr(first.q, CONF[first.conf][0]))
    vin_name = f'v_{{{LET[CONF[first.conf][0]]}{first.q.name[1:]}}}'
    if f('vi') != nin and not skip_input:
        zin_node = impedance_tree(view, nin, inputs=inputs)
        zs, cur, used = None, 'vi', set()
        while cur != nin:
            i, z, a, b = next((i, z, a, b) for i, (z, a, b) in enumerate(view.br)
                              if cur in (a, b) and i not in used and '0' not in (a, b))
            used.add(i)
            zs = z if zs is None else Ser(zs, z)
            cur = b if a == cur else a
        if zin_node is None:          # nothing to ground at the gate: no current, v_g = v_i
            ratio = sp.Integer(1)
            gl.append(f'\\frac{{{vin_name}}}{{v_i}} &= 1\\quad\\text{{(no current flows into the gate)}}')
        else:
            ratio = zin_node.z() / (zs.z() + zin_node.z())
            gl.append(f'\\frac{{{vin_name}}}{{v_i}} &= \\frac{{{ztex(zin_node)}}}{{{zs.z_tex()} + {ztex(zin_node)}}} = '
                      f'{rational_tex(ratio)}')
        H *= ratio
        frs.append(f'\\frac{{{vin_name}}}{{v_i}}')
    for idx, st in enumerate(stages):
        q = st.q
        k = q.name[1:]
        g1 = gmr(view, q)
        inn, outn = CONF[st.conf]
        nout = f(getattr(q, outn))
        vin_ = f'v_{{{LET[inn]}{k}}}'
        vout = f'v_{{{LET[outn]}{k}}}'
        if st.conf == 'CS':
            zd = impedance_tree(view, nout, inputs=inputs)
            zs_ = impedance_tree(view, f(q.e), inputs=inputs)
            g = -zd.z() / (1 / g1 + (zs_.z() if zs_ is not None else 0))
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= -\\frac{{Z_{{D{k}}}}}{{1/g_{{m{k}}} + Z_{{S{k}}}}},\\quad '
                      f'Z_{{D{k}}} = {ztex(zd)},\\ Z_{{S{k}}} = {ztex(zs_) if zs_ is not None else "0"}'
                      f'\\ \\Rightarrow\\ {rational_tex(g)}')
        elif st.conf == 'CG':
            zd = impedance_tree(view, nout, inputs=inputs)
            g = zd.z() * g1
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= \\frac{{Z_{{D{k}}}}}{{1/g_{{m{k}}}}},\\quad Z_{{D{k}}} = {ztex(zd)}'
                      f'\\ \\Rightarrow\\ {rational_tex(g)}')
        else:
            zs_ = impedance_tree(view, nout, inputs=inputs)
            g = zs_.z() / (1 / g1 + zs_.z())
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= \\frac{{Z_{{S{k}}}}}{{1/g_{{m{k}}} + Z_{{S{k}}}}},\\quad '
                      f'Z_{{S{k}}} = {ztex(zs_)}\\ \\Rightarrow\\ {rational_tex(g)}')
        H *= g
        frs.append(f'\\frac{{{vout}}}{{{vin_}}}')
        if idx + 1 < len(stages):
            nq = stages[idx + 1]
            nnext = f(getattr(nq.q, CONF[nq.conf][0]))
            nname = f'v_{{{LET[CONF[nq.conf][0]]}{nq.q.name[1:]}}}'
        else:
            nnext = f(circ.out)
            nname = 'v_o'
        if nnext != nout:
            zs2 = [z for z, a_, b_ in view.br if {a_, b_} == {nout, nnext}][0]
            zt = impedance_tree(view, nnext, inputs=inputs, visited={nout})
            r = zt.z() / (zs2.z() + zt.z())
            H *= r
            frs.append(f'\\frac{{{nname}}}{{{vout}}}')
            gl.append(f'\\frac{{{nname}}}{{{vout}}} &= \\frac{{{ztex(zt)}}}{{{zs2.z_tex()} + {ztex(zt)}}} = '
                      f'{rational_tex(r)}')
    parts.append('Multiply the node-to-node gains along the signal path (tool T4):'
                 + T.eq('H(s) = ' + '\\cdot'.join(frs)) + T.align(gl))
    return parts, sp.cancel(sp.together(H)), view
