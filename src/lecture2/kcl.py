"""Nodal analysis written out for students: virtual short, KCL at every node, step-by-step elimination.

Works on any Net with ideal op-amps whose AC input is node 'i' and output node `out`.
`label` maps internal node names to the subscripts shown in the solution ('x1' -> 'x').
"""
import sympy as sp

from common.tf import s, rational_tex
from common import texdoc as T
from lecture1.ladder import El, NamedZ
from .netlist import admittance


def _v(lbl):
    return 'V_{' + lbl + '}'


def _lin_tex(coefs, names):
    """sum of coef*V in LaTeX; coefs: dict var -> sympy rational function."""
    terms = []
    for var, c in coefs.items():
        c = sp.cancel(sp.together(c))
        if c == 0:
            continue
        rt = rational_tex(c)
        if rt.startswith('-') and '\\dfrac' not in rt and ' ' not in rt[1:]:
            terms.append(('-', rt[1:] + '\\,' + names[var]))
        elif rt == '1':
            terms.append(('+', names[var]))
        elif rt == '-1':
            terms.append(('-', names[var]))
        elif '\\dfrac' in rt or ' + ' in rt or ' - ' in rt:
            terms.append(('+', '\\left(' + rt + '\\right)' + names[var]))
        else:
            terms.append(('+', rt + '\\,' + names[var]))
    if not terms:
        return '0'
    out = ('-' if terms[0][0] == '-' else '') + terms[0][1]
    for sg, body in terms[1:]:
        out += f' {sg} {body}'
    return out


def kcl_derivation(net, label, out='o'):
    """Returns (latex, H) where H = V_out / V_i (exact)."""
    fixed = {'0': None, 'i': 'i'}
    # ---------- virtual short: merge each op-amp's inputs
    alias = {}

    def find(n):
        while n in alias:
            n = alias[n]
        return n

    vs_lines = []
    for o in net.opamps:
        a, b = find(o.plus), find(o.minus)
        if a == b:
            continue
        # keep the "nicer" survivor: fixed nodes first, then the + side
        if b in fixed:
            alias[a] = b
            keep, gone = b, a
        else:
            alias[b] = a
            keep, gone = a, b
        def disp(n):
            return '0' if n == '0' else _v(label.get(n, n))
        vs_lines.append(f'{o.name}: $V_- = V_+$, so ${disp(gone)}$ is the same voltage '
                        f'as ${disp(keep)}$' + (' (virtual ground)' if keep == '0' else '') + '.')

    def disp_node(n):
        r = find(n)
        if r == '0':
            return '0'
        return _v(label.get(r, r))

    outs = {o.out for o in net.opamps}
    nodes = sorted(net.nodes() - set(fixed) - set(net.dcs))
    kcl_nodes = [n for n in nodes if n not in outs]
    unknown_roots = sorted({find(n) for n in nodes} - set(fixed))
    syms = {r: sp.Symbol('U_' + r) for r in unknown_roots}
    syms_i = sp.Symbol('U_i')
    names = {syms[r]: _v(label.get(r, r)) for r in unknown_roots}
    names[syms_i] = 'V_i'

    def sym_of(n):
        r = find(n)
        if r == '0':
            return 0
        if r == 'i':
            return syms_i
        return syms[r]

    eq_tex, eqs = [], []
    for n in kcl_nodes:
        terms, expr = [], 0
        a = disp_node(n)
        for z, p, q in net.branches:
            if n not in (p, q):
                continue
            other = q if p == n else p
            b = disp_node(other)
            if find(other) == find(n):
                continue  # both ends at the same voltage: no current
            diff = a if b == '0' else f'{a} - {b}'
            if isinstance(z, El) and z.kind == 'C':
                terms.append(f's{z.tex}{a}' if b == '0' and a != '0' else f's{z.tex}\\left({diff}\\right)')
            else:
                zt = z.z_tex()
                terms.append(f'\\frac{{{diff}}}{{{zt}}}')
            expr += admittance(z) * (sym_of(n) - sym_of(other))
        if not terms:
            continue
        where = _v(label.get(n, n))
        if find(n) != n:   # merged by the virtual short: name the physical node, show its value
            where += f'\\,(={a})'
        eq_tex.append((label.get(n, n), ' + '.join(terms) + ' = 0', where))
        eqs.append(sp.expand(expr))

    parts = []
    if vs_lines:
        parts.append('Virtual short (tool T1): ' + ' '.join(vs_lines))
    parts.append('KCL (tool T3) at every node that is not an op-amp output or a source; no current flows into the '
                 'op-amp inputs, so the op-amps do not appear in these sums:')
    lines = []
    for k, (lbl, t, a) in enumerate(eq_tex, 1):
        lines.append(f'&\\text{{({k}) at }}{a}: && {t}')
    parts.append(T.align(lines))
    # ---------- elimination
    out_sym = sym_of(out)
    remaining = list(range(len(eqs)))
    cur = list(eqs)
    steps = []
    unknowns = set(syms.values())
    while True:
        live = [k for k in remaining if any(cur[k].has(u) for u in unknowns)]
        if not live:
            break
        others = [u for u in unknowns if u != out_sym]
        if not others:
            k = live[0]
            break
        # equation with the fewest unknowns that contains a non-output unknown
        cand = [k for k in live if any(cur[k].has(u) for u in others)]
        k = min(cand, key=lambda j: (sum(1 for u in unknowns if cur[j].has(u)), j))
        var = next(u for u in sorted(others, key=lambda u: str(u)) if cur[k].has(u))
        sol = sp.solve(cur[k], var)[0]
        coefs = {u: sp.diff(sol, u) for u in sorted(unknowns - {var}, key=str) if sol.has(u)}
        if sol.has(syms_i):
            coefs[syms_i] = sp.diff(sol, syms_i)
        steps.append(f'\\text{{from ({k + 1}):}}\\quad {names[var]} &= {_lin_tex(coefs, names)}')
        remaining.remove(k)
        unknowns.discard(var)
        for j in remaining:
            cur[j] = sp.expand(sp.together(cur[j].subs(var, sol)))
            cur[j] = sp.expand(sp.numer(sp.together(cur[j])))
    # final equation in V_out and V_i
    k = [j for j in remaining if cur[j].has(out_sym)][0]
    H = sp.cancel(sp.solve(cur[k], out_sym)[0] / syms_i)
    parts.append('Solve them one at a time (tool T4): take the equation with the fewest unknowns, solve it for one '
                 'node voltage and substitute that into the remaining equations. With the component values:')
    if steps:
        parts.append(T.align(steps))
    vout = _v(label.get(out, out))
    same = '' if names[out_sym] == vout else f' Since ${vout} = {names[out_sym]}$ (virtual short),'
    lhs = f'\\frac{{{vout}}}{{V_i}}' + ('' if not same else f' = \\frac{{{names[out_sym]}}}{{V_i}}')
    parts.append(f'Substituting everything into ({k + 1}) leaves only ${names[out_sym]}$ and $V_i$.{same}'
                 + T.eq(f'{lhs} = {rational_tex(H)}'))
    return '\n'.join(parts), H
