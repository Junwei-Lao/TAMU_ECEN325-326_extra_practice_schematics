"""Tiny modified-nodal-analysis solver, used ONLY to cross-check generated solutions.

Netlist entries (node 0 is ground):
    ('R'|'C'|'L', a, b, value)
    ('V', p, n, value)                  independent voltage source, V(p) - V(n) = value
    ('E', p, n, cp, cn, gain)           VCVS: V(p) - V(n) = gain * (V(cp) - V(cn))
    ('G', frm, to, cp, cn, gm)          VCCS: current gm*(V(cp)-V(cn)) leaves node `frm`
                                        and enters node `to` through the source
    ('O', plus, minus, out)             ideal op-amp (nullor): V(plus) = V(minus), output supplies
                                        whatever current is needed
Gains may be complex (e.g. a finite op-amp gain A(jw) modelled with 'E').
"""
import numpy as np


def solve(netlist, w=None):
    """w=None -> DC (C open, L short). Otherwise AC at angular frequency w.
    Returns dict node -> complex voltage."""
    nodes = set()
    for e in netlist:
        nodes.update(x for x in e[1:{'E': 5, 'G': 5, 'O': 4}.get(e[0], 3)] if isinstance(x, int))
    nodes.discard(0)
    idx = {n: i for i, n in enumerate(sorted(nodes))}
    N = len(idx)
    vsrc = [e for e in netlist if e[0] in ('V', 'E', 'O') or (e[0] == 'L' and w is None)]
    M = N + len(vsrc)
    A = np.zeros((M, M), dtype=complex)
    b = np.zeros(M, dtype=complex)

    def stamp_y(a, c, y):
        if a:
            A[idx[a], idx[a]] += y
        if c:
            A[idx[c], idx[c]] += y
        if a and c:
            A[idx[a], idx[c]] -= y
            A[idx[c], idx[a]] -= y

    for n in idx:  # gmin keeps nodes isolated by open capacitors solvable
        A[idx[n], idx[n]] += 1e-12
    k = N
    for e in netlist:
        t = e[0]
        if t == 'R':
            stamp_y(e[1], e[2], 1 / e[3])
        elif t == 'C':
            if w is not None:
                stamp_y(e[1], e[2], 1j * w * e[3])
        elif t == 'L':
            if w is not None:
                stamp_y(e[1], e[2], 1 / (1j * w * e[3]))
        elif t == 'G':
            _, frm, to, cp, cn, gm = e
            for node, sgn in ((frm, 1), (to, -1)):
                if node:
                    if cp:
                        A[idx[node], idx[cp]] += sgn * gm
                    if cn:
                        A[idx[node], idx[cn]] -= sgn * gm
    for e in vsrc:
        t = e[0]
        if t == 'O':  # unknown output current enters `out`; constraint V(plus) - V(minus) = 0
            _, pl, mi, out = e
            if out:
                A[idx[out], k] += 1
            if pl:
                A[k, idx[pl]] += 1
            if mi:
                A[k, idx[mi]] -= 1
            k += 1
            continue
        p, n = e[1], e[2]
        if p:
            A[idx[p], k] += 1
            A[k, idx[p]] += 1
        if n:
            A[idx[n], k] -= 1
            A[k, idx[n]] -= 1
        if t == 'V':
            b[k] = e[3]
        elif t == 'E':
            _, _, _, cp, cn, g = e
            if cp:
                A[k, idx[cp]] -= g
            if cn:
                A[k, idx[cn]] += g
        # 'L' at DC: 0 V source (short)
        k += 1
    x = np.linalg.solve(A, b)
    out = {0: 0}
    for n, i in idx.items():
        out[n] = x[i]
    return out
