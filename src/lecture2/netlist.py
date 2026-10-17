"""Named-node netlist for op-amp circuits + exact (sympy) and numeric (MNA) solvers.

Nodes are strings; '0' is ground, 'i' is the AC input V_i. A DC supply is a node fixed by
`net.dc(node, value)`. Branches carry Lecture-1 impedances (El / Ser / Par).
"""
import math

import sympy as sp

from common import mna
from common.tf import s
from lecture1.ladder import El, Ser, Par, NamedZ, sym


class OpAmp:
    def __init__(self, name, plus, minus, out):
        self.name, self.plus, self.minus, self.out = name, plus, minus, out


class Net:
    def __init__(self):
        self.branches = []          # (z, a, b)
        self.opamps = []
        self.dcs = {}               # node -> DC volts

    def add(self, z, a, b):
        self.branches.append((z, a, b))
        return self

    def opamp(self, name, plus, minus, out):
        self.opamps.append(OpAmp(name, plus, minus, out))
        return self

    def dc(self, node, value):
        self.dcs[node] = value
        return self

    # ------------------------------------------------------------------ helpers
    def nodes(self):
        ns = set()
        for _, a, b in self.branches:
            ns.update((a, b))
        for o in self.opamps:
            ns.update((o.plus, o.minus, o.out))
        return ns

    def fixed(self):
        return {'0', 'i'} | set(self.dcs)

    def unknowns(self):
        return sorted(self.nodes() - self.fixed())

    def elements(self):
        return [e for z, _, _ in self.branches for e in z.elems()]

    def has_dc(self):
        return bool(self.dcs)

    def opamp_outputs(self):
        return [o.out for o in self.opamps]


# ---------------------------------------------------------------------- exact solve
def admittance(z):
    return sp.cancel(1 / z.z())


def solve_exact(net, A=None, mode='ac'):
    """Solve all node voltages.
    mode 'ac': V_i = 1, DC supplies = 0 -> node voltages ARE transfer functions from V_i.
    mode 'dc': V_i = 0, DC supplies on, s -> 0.
    A: None for ideal op-amps (virtual short) or a sympy expression A(s) for every op-amp."""
    V = {n: sp.Symbol('V_' + n) for n in net.unknowns()}
    fixedv = {'0': 0, 'i': 1 if mode == 'ac' else 0}
    for n, v in net.dcs.items():
        fixedv[n] = 0 if mode == 'ac' else sp.Rational(str(v))

    def vol(n):
        return V[n] if n in V else fixedv[n]

    outs = set(net.opamp_outputs())
    eqs = []
    for n in V:
        if n in outs:
            continue
        expr = 0
        for z, a, b in net.branches:
            if n in (a, b):
                other = b if a == n else a
                expr += admittance(z) * (vol(n) - vol(other))
        eqs.append(expr)
    for o in net.opamps:
        if A is None:
            eqs.append(vol(o.plus) - vol(o.minus))
        else:
            eqs.append(vol(o.out) - A * (vol(o.plus) - vol(o.minus)))
    if mode == 'dc':
        eqs = [sp.cancel(sp.together(e)).subs(s, 0) for e in eqs]
    sol = sp.solve(eqs, list(V.values()), dict=True)
    if not sol:
        raise ValueError('no solution (is every op-amp in negative feedback?)')
    sol = sol[0]
    out = {n: sp.cancel(sp.together(sol[V[n]])) for n in V}
    out.update({k: sp.Integer(v) if isinstance(v, int) else v for k, v in fixedv.items()})
    return out


# ---------------------------------------------------------------------- numeric check
def numeric_netlist(net, mode, A_of_w=None):
    """Integer-node netlist for common.mna. mode 'ac' or 'dc'."""
    ids = {'0': 0}
    nl = []

    def nid(n):
        if n not in ids:
            ids[n] = len(ids)
        return ids[n]

    cnt = [1000]

    def internal():
        cnt[0] += 1
        return cnt[0]

    def place(z, a, b):
        if isinstance(z, NamedZ):
            z = z.inner
        if isinstance(z, El):
            nl.append((z.kind, a, b, float(z.value)))
        elif isinstance(z, Ser):
            cur = a
            for k, p in enumerate(z.parts):
                nxt = b if k == len(z.parts) - 1 else internal()
                place(p, cur, nxt)
                cur = nxt
        elif isinstance(z, Par):
            for p in z.parts:
                place(p, a, b)

    nl.append(('V', nid('i'), 0, 1.0 if mode == 'ac' else 0.0))
    for n, v in net.dcs.items():
        nl.append(('V', nid(n), 0, 0.0 if mode == 'ac' else float(v)))
    for z, a, b in net.branches:
        place(z, nid(a), nid(b))
    return nl, ids, A_of_w


def solve_numeric(net, w=None, A=None):
    """w=None -> DC. A: None (ideal) or complex open-loop gain at this w."""
    nl, ids, _ = numeric_netlist(net, 'dc' if w is None else 'ac')
    for o in net.opamps:
        p, m, out = ids.setdefault(o.plus, len(ids)), ids.setdefault(o.minus, len(ids)), \
            ids.setdefault(o.out, len(ids))
        if A is None:
            nl.append(('O', p, m, out))
        else:
            nl.append(('E', out, 0, p, m, A))
    res = mna.solve(nl, w)
    return {n: res.get(i, 0) for n, i in ids.items()}


def verify(net, exact, nodes, A_expr=None, freqs=(3.0, 97.0, 1.3e3, 2.9e4, 3.3e5), where=''):
    """Compare exact transfer functions (sympy, in s) with an independent numeric MNA solve."""
    for f in freqs:
        w = 2 * math.pi * f
        Aw = None if A_expr is None else complex(A_expr.subs(s, 1j * w))
        num = solve_numeric(net, w, Aw)
        for n in nodes:
            ref = num[n]
            got = complex(exact[n].subs(s, 1j * w))
            if abs(ref - got) > 1e-6 * max(abs(ref), 1e-6):
                raise AssertionError(f'{where}: node {n} at {f} Hz: MNA {ref} vs exact {got}')
