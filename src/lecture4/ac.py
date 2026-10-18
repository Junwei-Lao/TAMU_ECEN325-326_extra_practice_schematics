"""Small-signal (AC) analysis of multistage BJT amplifiers with the node-impedance method of the slides:
    Z_base = (beta+1)(r_e + Z_E),  Z_emitter = r_e + Z_B/(beta+1),  Z_collector = infinity (r_o = infinity)
    CE: v_c/v_b = -alpha Z_C/(r_e + Z_E)   CB: v_c/v_e = alpha Z_C / Z_emitter   CC: v_e/v_b = Z_E/(r_e + Z_E)
An exact nodal solve with the hybrid-pi model (r_pi = (beta+1) r_e, g_m = alpha/r_e) is the independent check."""
import sympy as sp

from common.tf import s, rational_tex
from common.units import num_tex, eng_tex
from common import texdoc as T
from lecture1.ladder import El, Ser, Par, NamedZ, sym

CONF = {'CE': ('b', 'c'), 'CB': ('e', 'c'), 'CC': ('b', 'e')}


class Stage:
    def __init__(self, q, conf):
        self.q, self.conf = q, conf


# ------------------------------------------------------------------------------------------ AC view
def short_inf(z):
    """AC view of an impedance tree: an 'infinite' capacitor is a short. Returns 'short', None (open) or a tree."""
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        return 'short' if (z.kind == 'C' and getattr(z, 'inf', False)) else z
    if isinstance(z, Par):
        parts = [short_inf(p) for p in z.parts]
        if 'short' in parts:
            return 'short'
        parts = [p for p in parts if p is not None]
        return parts[0] if len(parts) == 1 else Par(*parts)
    if isinstance(z, Ser):
        parts = [short_inf(p) for p in z.parts]
        if any(p is None for p in parts):
            return None
        parts = [p for p in parts if p != 'short']
        if not parts:
            return 'short'
        return parts[0] if len(parts) == 1 else Ser(*parts)
    return z



class ACView:
    """Rails -> ground, infinite capacitors -> shorts (node merging), everything else as impedances."""

    def __init__(self, circ, IC, beta=100):
        self.circ = circ
        self.parent = {}
        simp = [(short_inf(z), a, b) for z, a, b in circ.branches]
        for z, a, b in simp:
            if z == 'short':
                self._union(a, b)
        for n in circ.fixed:
            if n != 'vi':
                self._union(n, '0')
        self.br = []
        for z, a, b in simp:
            if z == 'short' or z is None:
                continue
            fa, fb = self.f(a), self.f(b)
            if fa != fb:
                self.br.append((z, fa, fb))
        self.IC = IC
        self.re = {q.name: circ.vt / IC[q.name] for q in circ.bjts}

    def _find(self, n):
        while self.parent.get(n, n) != n:
            n = self.parent[n]
        return n

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra == rb:
            return
        if rb == '0':
            ra, rb = rb, ra
        self.parent[rb] = ra      # ground always stays the root of its group

    def f(self, n):
        return self._find(n)

    # exact hybrid-pi solve: V(out)/V(vi)
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
            re = sp.Rational(repr(self.re[q.name]))
            beta = q.beta
            rpi = (beta + 1) * re
            gm = sp.Rational(beta, beta + 1) / re
            b, c, e = self.f(q.b), self.f(q.c), self.f(q.e)
            vbe = v(b) - v(e)
            for n, cur in ((b, vbe / rpi), (e, -vbe / rpi - gm * vbe), (c, gm * vbe)):
                if n in eqs:
                    eqs[n] += cur
        sol = sp.solve(list(eqs.values()), list(V.values()), dict=True)[0]
        return sp.cancel(sp.together(sol[V[self.f(out)]]))


# ------------------------------------------------------------------------------------------ impedance trees
def impedance_tree(view, node, exclude_branch=None, inputs=None, visited=None):
    """Impedance from `node` to AC ground as a Ser/Par tree. `inputs` maps node -> NamedZ of a downstream
    transistor input resistance attached at that node. Transistor terminals are otherwise open."""
    if node == '0':
        return None          # the node is (AC) ground itself: zero impedance
    visited = set(visited or ()) | {node}
    parts = []
    for i, (z, a, b) in enumerate(view.br):
        if i == exclude_branch or node not in (a, b):
            continue
        m = b if a == node else a
        if m == '0':
            parts.append(z)
        elif m in visited or m == 'vi':
            continue
        else:
            sub = impedance_tree(view, m, i, inputs, visited)
            if sub is not None:
                parts.append(Ser(z, sub))
    if inputs and node in inputs:
        parts.append(inputs[node])
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else Par(*parts)


def ztex(z):
    return z.z_tex() if z is not None else '\\infty'


def zval(z):
    return z.z() if z is not None else None


# ------------------------------------------------------------------------------------------ narrative
def solve_ac(circ, IC, stages):
    """Returns (latex parts, H expr). stages: list of Stage along the signal path."""
    view = ACView(circ, IC)
    parts = []
    f = view.f
    alpha = {q.name: sp.Rational(q.beta, q.beta + 1) for q in circ.bjts}
    beta1 = {q.name: q.beta + 1 for q in circ.bjts}
    # --- step: r_e
    rows = [f'r_{{e{q.name[1:]}}} = \\frac{{V_T}}{{I_{{C{q.name[1:]}}}}} = \\frac{{25\\,\\mathrm{{mV}}}}'
            f'{{{eng_tex(IC[q.name], "\\mathrm{A}")}}} = {eng_tex(view.re[q.name], "\\Omega")}'
            for q in [st.q for st in stages]]
    parts.append(('Small-signal emitter resistances (tool T3):' + T.align([r.replace('=', '&=', 1) for r in rows])))
    # --- input resistances right to left
    inputs = {}
    Ri = {}
    lines = []
    Ztex = {}
    for st in reversed(stages):
        q = st.q
        k = q.name[1:]
        re = El('R', f'r_{{e{k}}}', repr(view.re[q.name]))
        if st.conf in ('CE', 'CC'):
            ze = impedance_tree(view, f(q.e), inputs=inputs)
            ze_named = NamedZ(f'Z_{{E{k}}}', ze) if ze is not None and not isinstance(ze, El) else ze
            ri = (beta1[q.name]) * (re.z() + (ze.z() if ze is not None else 0))
            Ri[q.name] = NamedZ(f'R_{{i{k}}}', El('R', f'R_{{i{k}}}', 1))
            Ri[q.name].z = (lambda v=ri: v)
            inputs[f(q.b)] = Ri[q.name]
            zet = ztex(ze) if ze is not None else '0'
            lines.append(f'R_{{i{k}}} &= Z_{{base,{k}}} = (\\beta+1)(r_{{e{k}}} + {zet}) = '
                         f'{rational_tex(ri) if (ze is not None and ze.z().has(s)) else eng_tex(float(ri), "\\Omega")}')
        else:  # CB: input at the emitter
            zb = impedance_tree(view, f(q.b), inputs=inputs)
            ri = re.z() + (zb.z() / beta1[q.name] if zb is not None else 0)
            Ri[q.name] = NamedZ(f'R_{{i{k}}}', El('R', f'R_{{i{k}}}', 1))
            Ri[q.name].z = (lambda v=ri: v)
            inputs[f(q.e)] = Ri[q.name]
            zbt = ztex(zb) if zb is not None else '0'
            lines.append(f'R_{{i{k}}} &= Z_{{emitter,{k}}} = r_{{e{k}}} + \\frac{{{zbt}}}{{\\beta+1}} = '
                         f'{rational_tex(ri) if (zb is not None and zb.z().has(s)) else eng_tex(float(ri), "\\Omega")}')
    parts.append('Input resistance of every stage, from the last stage back to the first (each one loads the stage '
                 'before it; tool T4):' + T.align(list(reversed(lines))))
    # --- gains along the path
    gl = []
    H = sp.Integer(1)
    frs = []
    # source -> first input node
    first = stages[0]
    nin = f(getattr(first.q, CONF[first.conf][0]))
    ser = [(z, a, b) for z, a, b in view.br if 'vi' in (a, b)]
    zin_node = impedance_tree(view, nin, inputs=inputs)
    vin_name = f'v_{{{CONF[first.conf][0]}{first.q.name[1:]}}}'
    if f('vi') != nin:
        zs, cur, used = None, 'vi', set()
        while cur != nin:   # walk the series path from the source to the first input node
            i, z, a, b = next((i, z, a, b) for i, (z, a, b) in enumerate(view.br)
                              if cur in (a, b) and i not in used and '0' not in (a, b))
            used.add(i)
            zs = z if zs is None else Ser(zs, z)
            cur = b if a == cur else a
        ratio = zin_node.z() / (zs.z() + zin_node.z())
        H *= ratio
        frs.append(f'\\frac{{{vin_name}}}{{v_i}}')
        gl.append(f'\\frac{{{vin_name}}}{{v_i}} &= \\frac{{{ztex(zin_node)}}}{{{zs.z_tex()} + {ztex(zin_node)}}} = '
                  f'{rational_tex(ratio)}')
    for idx, st in enumerate(stages):
        q = st.q
        k = q.name[1:]
        a = alpha[q.name]
        inn, outn = CONF[st.conf]
        nin_, nout = f(getattr(q, inn)), f(getattr(q, outn))
        vin_ = f'v_{{{inn}{k}}}'
        vout = f'v_{{{outn}{k}}}'
        if st.conf == 'CE':
            zc = impedance_tree(view, nout, inputs=inputs)
            ze = impedance_tree(view, f(q.e), inputs=inputs)
            g = -a * zc.z() / (view_re(view, q) + (ze.z() if ze is not None else 0))
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= -\\alpha\\frac{{Z_{{C{k}}}}}{{r_{{e{k}}} + Z_{{E{k}}}}},\\quad '
                      f'Z_{{C{k}}} = {ztex(zc)},\\ Z_{{E{k}}} = {ztex(ze) if ze is not None else "0"}'
                      f'\\ \\Rightarrow\\ {rational_tex(g)}')
        elif st.conf == 'CB':
            zc = impedance_tree(view, nout, inputs=inputs)
            zb = impedance_tree(view, f(q.b), inputs=inputs)
            zem = view_re(view, q) + (zb.z() / beta1[q.name] if zb is not None else 0)
            g = a * zc.z() / zem
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= \\alpha\\frac{{Z_{{C{k}}}}}{{Z_{{emitter,{k}}}}},\\quad '
                      f'Z_{{C{k}}} = {ztex(zc)}\\ \\Rightarrow\\ {rational_tex(g)}')
        else:
            ze = impedance_tree(view, nout, inputs=inputs)
            g = ze.z() / (view_re(view, q) + ze.z())
            gl.append(f'\\frac{{{vout}}}{{{vin_}}} &= \\frac{{Z_{{E{k}}}}}{{r_{{e{k}}} + Z_{{E{k}}}}},\\quad '
                      f'Z_{{E{k}}} = {ztex(ze)}\\ \\Rightarrow\\ {rational_tex(g)}')
        H *= g
        frs.append(f'\\frac{{{vout}}}{{{vin_}}}')
        # link to the next stage (or to the output)
        if idx + 1 < len(stages):
            nq = stages[idx + 1]
            nnext = f(getattr(nq.q, CONF[nq.conf][0]))
            nname = f'v_{{{CONF[nq.conf][0]}{nq.q.name[1:]}}}'
        else:
            nnext = f(circ.out)
            nname = 'v_o'
        if nnext != nout:
            zs = [z for z, a_, b_ in view.br if {a_, b_} == {nout, nnext}][0]
            zt = impedance_tree(view, nnext, inputs=inputs, visited={nout})
            r = zt.z() / (zs.z() + zt.z())
            H *= r
            frs.append(f'\\frac{{{nname}}}{{{vout}}}')
            gl.append(f'\\frac{{{nname}}}{{{vout}}} &= \\frac{{{ztex(zt)}}}{{{zs.z_tex()} + {ztex(zt)}}} = {rational_tex(r)}')
    parts.append('Multiply the node-to-node gains along the signal path (tool T4):'
                 + T.eq('H(s) = ' + '\\cdot'.join(frs)) + T.align(gl))
    return parts, sp.cancel(sp.together(H)), view


def view_re(view, q):
    return sp.Rational(repr(view.re[q.name]))
