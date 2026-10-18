"""Piecewise-linear analysis of circuits with diodes (constant-voltage-drop or ideal model) and op-amps.

For every ON/OFF combination of the diodes the circuit is linear:
    OFF diode -> open circuit,   condition  V_D = V_anode - V_cathode < V_on
    ON  diode -> V_on source,    condition  I_D (anode -> cathode) > 0
Op-amps are modelled as V_out = A (V+ - V-) with A -> infinity; in a given state an op-amp is either
closed-loop (finite output: virtual short) or open-loop (output runs away to +/- infinity).
Each state therefore holds on an interval of V_i; the valid intervals tile the V_i axis.
"""
import itertools

import sympy as sp

from common.units import num_tex
from common import texdoc as T
from lecture1.ladder import El, Ser, Par, NamedZ

X = sp.Symbol('V_i')
A = sp.Symbol('A', positive=True)


def D(name, flip=False):
    """Diode element. In a branch (a, b) the anode is at a, unless flip=True."""
    e = El('D', name, '0')
    e.flip = flip
    return e


class PNet:
    """Flattened circuit: elementary branches only (R and D), named nodes."""

    def __init__(self, von=0.7):
        self.br = []          # (El, a, b)
        self.opamps = []      # (name, plus, minus, out)
        self.fixed = {'0': sp.Integer(0), 'i': X}
        self.von = sp.Rational(str(von))
        self._k = 0
        self.label = {}       # node -> display subscript

    def _new(self):
        self._k += 1
        return f'_{self._k}'

    def add(self, z, a, b):
        if isinstance(z, NamedZ):
            z = z.inner
        if isinstance(z, El):
            if z.kind == 'C':
                return  # transfer characteristics are DC: capacitors are open
            self.br.append((z, a, b))
        elif isinstance(z, Ser):
            cur = a
            for k, p in enumerate(z.parts):
                nxt = b if k == len(z.parts) - 1 else self._new()
                self.add(p, cur, nxt)
                cur = nxt
        elif isinstance(z, Par):
            for p in z.parts:
                self.add(p, a, b)
        return self

    def opamp(self, name, plus, minus, out):
        self.opamps.append((name, plus, minus, out))

    def dc(self, node, value):
        self.fixed[node] = sp.Rational(str(value))

    def diodes(self):
        out = []
        for el, a, b in self.br:
            if el.kind == 'D':
                out.append((el, b, a) if getattr(el, 'flip', False) else (el, a, b))
        return out

    def nodes(self):
        ns = set()
        for _, a, b in self.br:
            ns.update((a, b))
        for o in self.opamps:
            ns.update(o[1:])
        return ns

    def disp(self, n):
        if n == '0':
            return '0'
        if n == 'i':
            return 'V_i'
        if n in self.fixed:
            return num_tex(float(self.fixed[n]))
        return 'V_{' + self.label.get(n, n) + '}'

    def auto_labels(self, used=()):
        """Give every unnamed internal node a short name (a, b, c, ...)."""
        letters = iter('abcdefghjkmpqrstuvwyz')
        taken = set(self.label.values()) | set(used)
        for n in sorted(self.nodes()):
            if n in self.fixed or n in self.label:
                continue
            l = next(letters)
            while l in taken:
                l = next(letters)
            self.label[n] = l
            taken.add(l)


# ------------------------------------------------------------------------------------------ solving
def _lead(f):
    """f = p(A)*x + q(A). Return (p, q) of the dominant order as A -> infinity."""
    f = sp.together(sp.expand(f))
    p = sp.diff(f, X)
    q = sp.simplify(f - p * X)
    for k in (2, 1, 0):
        pk = sp.limit(p / A ** k, A, sp.oo)
        qk = sp.limit(q / A ** k, A, sp.oo)
        if (pk != 0 or qk != 0) and pk.is_finite and qk.is_finite:
            return pk, qk, k
    raise ValueError('cannot find the leading behaviour')


def solve_state(pn, on):
    """Exact solution with finite A. Returns dict of sympy expressions (node voltages, I_D, V_D)."""
    nodes = sorted(pn.nodes() - set(pn.fixed))
    V = {n: sp.Symbol('V_' + n) for n in nodes}
    I = {el.name: sp.Symbol('I_' + el.name) for el, _, _ in pn.diodes() if el.name in on}

    def v(n):
        return pn.fixed[n] if n in pn.fixed else V[n]

    outs = {o[3] for o in pn.opamps}
    eqs = []
    for n in nodes:
        if n in outs:
            continue
        e = 0
        for el, a, b in pn.br:
            if n not in (a, b):
                continue
            o = b if a == n else a
            if el.kind == 'R':
                e += (v(n) - v(o)) / sp.Rational(el.value)
        for el, an, ca in pn.diodes():
            if el.name in on:
                if n == an:
                    e += I[el.name]
                elif n == ca:
                    e -= I[el.name]
        eqs.append(e)
    for el, an, ca in pn.diodes():
        if el.name in on:
            eqs.append(v(an) - v(ca) - pn.von)
    for name, p, m, o in pn.opamps:
        eqs.append(v(o) - A * (v(p) - v(m)))
    sol = sp.solve(eqs, list(V.values()) + list(I.values()), dict=True)
    if not sol:
        return None   # the ON diodes would force some node to two different voltages
    sol = sol[0]
    if any(V[n] not in sol for n in nodes):
        return None   # a node is left floating (e.g. between two OFF diodes): treat as undetermined
    res = {n: sp.simplify(sol[V[n]]) for n in nodes}
    res.update({n: pn.fixed[n] for n in pn.fixed})
    for el, an, ca in pn.diodes():
        if el.name in on:
            res['I_' + el.name] = sp.simplify(sol[I[el.name]])
        else:
            res['VD_' + el.name] = sp.simplify(res[an] - res[ca])
    return res


def analyse(pn, out='o'):
    """All states, their validity intervals, V_o(V_i) in each."""
    names = [el.name for el, _, _ in pn.diodes()]
    states = []
    for bits in itertools.product((False, True), repeat=len(names)):
        on = frozenset(n for n, b in zip(names, bits) if b)
        res = solve_state(pn, on)
        if res is None:
            states.append(dict(on=on, res=None, valid=False, conflict=True, conds=[]))
            continue
        lo, hi = -sp.oo, sp.oo
        conds = []
        for el, _, _ in pn.diodes():
            if el.name in on:
                f = -res['I_' + el.name]
                kind = 'on'
            else:
                f = res['VD_' + el.name] - pn.von
                kind = 'off'
            p, q, k = _lead(f)
            if p == 0:
                ok = q < 0
                conds.append(dict(d=el.name, kind=kind, p=p, q=q, k=k, always=bool(ok)))
                if not ok:
                    lo, hi = sp.oo, -sp.oo
                continue
            b = -q / p
            if p > 0:
                hi = sp.Min(hi, b)
            else:
                lo = sp.Max(lo, b)
            conds.append(dict(d=el.name, kind=kind, p=p, q=q, k=k, bound=b, below=p > 0))
        vo = sp.limit(res[out], A, sp.oo)
        open_loop = []
        for name, p_, m_, o_ in pn.opamps:
            if sp.limit(res[o_], A, sp.oo).has(sp.oo, -sp.oo, sp.zoo):
                open_loop.append(name)
        valid = bool(lo < hi)
        states.append(dict(on=on, res=res, lo=lo, hi=hi, conds=conds, valid=valid, vo=sp.expand(vo),
                           open_loop=open_loop))
    good = sorted([s for s in states if s['valid']], key=lambda s: float(s['lo']) if s['lo'] != -sp.oo else -1e30)
    # the valid intervals must tile the axis, and V_o must be continuous at every breakpoint
    assert good[0]['lo'] == -sp.oo and good[-1]['hi'] == sp.oo, 'states do not cover the V_i axis'
    for s1, s2 in zip(good, good[1:]):
        assert sp.simplify(s1['hi'] - s2['lo']) == 0, 'gap/overlap between states'
        b = s1['hi']
        assert abs(float(s1['vo'].subs(X, b) - s2['vo'].subs(X, b))) < 1e-9, 'V_o jumps at a breakpoint'
    return good, [s for s in states if not s['valid']]


def merged(good):
    """Adjacent states with the same V_o(V_i) form one piece of the characteristic."""
    out = []
    for s in good:
        if out and sp.simplify(out[-1]['vo'] - s['vo']) == 0:
            out[-1] = dict(out[-1], hi=s['hi'])
        else:
            out.append(dict(lo=s['lo'], hi=s['hi'], vo=s['vo']))
    return out


def vo_of(good, x):
    for s in good:
        if (s['lo'] == -sp.oo or x >= float(s['lo'])) and (s['hi'] == sp.oo or x <= float(s['hi'])):
            return float(s['vo'].subs(X, x))
    raise ValueError(x)


def numeric_check(pn, good, out='o', xs=None):
    """Independent check: at sample inputs, brute-force every state numerically (large finite A) and
    keep the one(s) whose assumptions hold; V_o must agree with the piecewise result."""
    import numpy as np
    names = [el.name for el, _, _ in pn.diodes()]
    bps = [float(s['hi']) for s in good[:-1]]
    if xs is None:
        span = max([abs(b) for b in bps] + [1.0])
        xs = list(np.linspace(-3 * span, 3 * span, 37))
    sols = {}
    for bits in itertools.product((False, True), repeat=len(names)):
        on = frozenset(n for n, b in zip(names, bits) if b)
        r = solve_state(pn, on)
        if r is not None:
            sols[on] = r
    for x in xs:
        if any(abs(x - b) < 1e-6 for b in bps):
            continue
        hits = []
        for on, res in sols.items():
            sub = {X: x, A: 10 ** 9}
            ok = True
            for el, _, _ in pn.diodes():
                if el.name in on:
                    ok &= float(res['I_' + el.name].subs(sub)) > -1e-12
                else:
                    ok &= float(res['VD_' + el.name].subs(sub)) < float(pn.von) + 1e-9
            if ok:
                hits.append(float(res[out].subs(sub)))
        if not hits:
            raise AssertionError(f'no consistent state at V_i={x}')
        ref = vo_of(good, x)
        for h in hits:
            if abs(h - ref) > 1e-5 * max(1, abs(ref)):
                raise AssertionError(f'V_o mismatch at V_i={x}: {h} vs {ref}')


# ------------------------------------------------------------------------------------------ narrative
def lin_tex(expr, var='V_i', digits=4):
    """a*V_i + b with numbers."""
    expr = sp.expand(expr)
    a = float(sp.diff(expr, X))
    b = float(expr.subs(X, 0))
    parts = []
    if abs(a) > 1e-12:
        parts.append(('-' if a < 0 else '') + ('' if abs(abs(a) - 1) < 1e-12 else num_tex(abs(a), digits)) + var)
    if abs(b) > 1e-12 or not parts:
        s = num_tex(abs(b), digits) if parts else num_tex(b, digits)
        parts.append((' - ' if b < 0 else ' + ') + s if parts else s)
    return ''.join(parts)


def _state_name(on, names):
    return ', '.join(f'${n[0]}_{{{n[1:]}}}$ {"ON" if n in on else "OFF"}' for n in names)


def dname(n):
    return f'{n[0]}_{{{n[1:]}}}'


def state_section(pn, st, names, out='o'):
    """LaTeX for one assumed state: model, equations, results, conditions."""
    on = st['on']
    res = st['res']
    lines = []
    model = []
    for el, an, ca in pn.diodes():
        if el.name in on:
            model.append(f'${dname(el.name)}$ ON: a ${num_tex(float(pn.von))}$\\,V source '
                         f'(${pn.disp(an)} - {pn.disp(ca)} = {num_tex(float(pn.von))}$) carrying an unknown '
                         f'current $I_{{{dname(el.name)}}}$ from anode to cathode')
        else:
            model.append(f'${dname(el.name)}$ OFF: an open circuit')
    txt = 'Replace ' + '; '.join(model) + '.'
    # op-amps
    for name, p, m, o in pn.opamps:
        if name in st['open_loop']:
            txt += (f' With this assumption {name} has no feedback path from its output back to its $-$ input: it runs '
                    f'\\emph{{open-loop}}, ${pn.disp(o)} = A(V_+ - V_-)$ with $A\\to\\infty$, so its output is pushed '
                    f'to $\\pm\\infty$ (in practice, a supply rail) unless $V_+ = V_-$ exactly.')
        else:
            txt += (f' {name} has negative feedback, so $V_- = V_+$ (virtual short) and no current flows into its '
                    f'inputs.')
    lines.append(txt)
    # equations (KCL with element names)
    outs = {o[3] for o in pn.opamps}
    closed = [o for o in pn.opamps if o[0] not in st['open_loop']]
    alias = {}
    for name, p, m, o in closed:
        if m in pn.fixed:
            alias[p] = m
        else:
            alias[m] = p

    def dv(n):
        n2 = alias.get(n, n)
        return pn.disp(n2)

    eq_lines = []
    for n in sorted(pn.nodes() - set(pn.fixed) - outs, key=lambda n: pn.label.get(n, n)):
        terms = []
        for el, a, b in pn.br:
            if n not in (a, b) or el.kind != 'R':
                continue
            o_ = b if a == n else a
            if dv(o_) == dv(n):
                continue
            diff = dv(n) if dv(o_) == '0' else f'{dv(n)} - {dv(o_)}'
            terms.append(f'\\frac{{{diff}}}{{{el.tex}}}')
        for el, an, ca in pn.diodes():
            if el.name in on and n in (an, ca):
                terms.append(('+' if n == an else '-') + f' I_{{{dname(el.name)}}}')
        if not terms:
            continue
        body = terms[0].lstrip('+ ') if terms[0].startswith('+') else terms[0]
        for t in terms[1:]:
            body += (' ' + t if t.startswith(('+', '-')) else ' + ' + t)
        where = pn.disp(n) + (f'\\,(={dv(n)})' if dv(n) != pn.disp(n) else '')
        eq_lines.append(f'&\\text{{KCL at }}{where}: && {body} = 0')
    for el, an, ca in pn.diodes():
        if el.name in on:
            eq_lines.append(f'&\\text{{{el.name} ON}}: && {dv(an)} - {dv(ca)} = {num_tex(float(pn.von))}')
    if eq_lines:
        lines.append('Equations (KCL at every node that is not an op-amp output, plus the diode voltages):'
                     + T.align(eq_lines))
    # results
    rl = []
    shown = set()

    def show(n):
        if n in pn.fixed or n in shown:
            return
        shown.add(n)
        e = res[n]
        if n in st_outs_open(pn, st):
            p, q, k = _lead(e)
            rl.append(f'{pn.disp(n)} &\\approx A\\left({lin_tex(p * X + q)}\\right)')
        else:
            rl.append(f'{pn.disp(n)} &= {lin_tex(sp.limit(e, A, sp.oo))}')

    show(out)
    for el, an, ca in pn.diodes():
        if el.name in on:
            e = sp.limit(res['I_' + el.name], A, sp.oo)
            rl.append(f'I_{{{dname(el.name)}}} &= {lin_tex(e * 1000)}\\ \\mathrm{{mA}}')
        else:
            e = res['VD_' + el.name]
            if any(o[0] in st['open_loop'] and o[3] in (an, ca) for o in pn.opamps):
                p, q, k = _lead(e)
                if k > 0:
                    rl.append(f'V_{{{dname(el.name)}}} = {pn.disp(an)} - {pn.disp(ca)} &\\approx '
                              f'A\\left({lin_tex(p * X + q)}\\right)')
                    continue
            rl.append(f'V_{{{dname(el.name)}}} = {pn.disp(an)} - {pn.disp(ca)} &= '
                      f'{lin_tex(sp.limit(e, A, sp.oo))}')
    lines.append('Solving these linear equations (substitute one into the other, as in Lecture 2) gives, with '
                 '$V_i$ kept as a symbol:' + T.align(rl))
    # conditions
    cl = []
    for c in st['conds']:
        d = dname(c['d'])
        if c['kind'] == 'off':
            what = (f'$V_{{{d}}} < {num_tex(float(pn.von))}$' if c['k'] == 0 else
                    f'$V_{{{d}}} < {num_tex(float(pn.von))}$; since $A\\to\\infty$ this needs '
                    f'${lin_tex(c["p"] * X + c["q"])} < 0$')
        else:
            what = f'$I_{{{d}}} > 0$'
        if 'bound' in c:
            rng = f'$V_i {"<" if c["below"] else ">"} {num_tex(float(c["bound"]), 4)}$\\,V'
        else:
            rng = 'true for every $V_i$' if c['always'] else 'never true'
        cl.append(f'{what} $\\Rightarrow$ {rng}')
    lines.append('Check the assumptions: ' + '; '.join(cl) + '.')
    return '\n\n'.join(lines)


def st_outs_open(pn, st):
    return {o[3] for o in pn.opamps if o[0] in st['open_loop']}


def interval_tex(st):
    lo, hi = st['lo'], st['hi']
    if lo == -sp.oo:
        return f'V_i < {num_tex(float(hi), 4)}'
    if hi == sp.oo:
        return f'V_i > {num_tex(float(lo), 4)}'
    return f'{num_tex(float(lo), 4)} < V_i < {num_tex(float(hi), 4)}'
