"""DC analysis of MOSFET circuits the way the slides do it (square law, every transistor assumed active, I_G = 0):
gate voltages from dividers, one quadratic per transistor from the KVL loop gate -> source -> resistor -> known node,
series chains of diode-connected transistors (current references), mirrors by W/L ratio, drain voltages by KCL;
then the region check |V_DS| >= V_ov. An exact nodal solve (scipy) is the independent check."""
import math

import numpy as np
from scipy.optimize import fsolve

from common.units import num_tex, eng_tex
from lecture4.dc import flat_resistors, term_sign
from .mosnet import wl_tex


def V_(x):
    return num_tex(round(x, 9) + 0.0, 3) + '\\,\\mathrm{V}'


def I_(x):
    return eng_tex(x, '\\mathrm{A}')


def Rn(x):
    return eng_tex(float(x), '')


def par(x):
    return f'({num_tex(x, 4)})' if x < 0 else num_tex(x, 4)


def vgs_sym(q):
    k = q.name[1:]
    return f'V_{{GS{k}}}' if q.s > 0 else f'V_{{SG{k}}}'


def id_sym(q):
    return f'I_{{D{q.name[1:]}}}'


def k_num(q):
    return eng_tex(q.k, '')


def pp(sym):
    """'(a + b)' for a sum, plain 'a' for a single symbol."""
    return f'({sym})' if ('+' in sym or '-' in sym) else sym


def quad_text(a, b, c, x, root, other, var, vt):
    """'a x^2 + b x + c = 0 => x = r1 or r2' with the choice explained."""
    def term(v, s, first=False):
        sgn = '-' if v < 0 else ('' if first else '+')
        return f'{sgn} {num_tex(abs(v), 4)}{s}'
    eq = (term(a, var + '^2', True) + ' ' + term(b, var) + ' ' + term(c, '')).strip()
    lo, hi = sorted((root, other))
    return (f'{eq} = 0 \\;\\Rightarrow\\; {var} = {num_tex(lo, 4)}\\ \\text{{or}}\\ {num_tex(hi, 4)}\\,\\mathrm{{V}}',
            f'The root ${num_tex(other, 3)}$\\,V is below $|V_t| = {num_tex(vt)}$\\,V (the transistor would be off), '
            f'so ${var} = {num_tex(root, 4)}$\\,V.')


def solve_dc5(circ):
    """Returns (steps, V, ID, VG) with VG = {name: |V_GS|}."""
    res = flat_resistors(circ)
    V = dict(circ.fixed)
    ID, VG = {}, {}
    steps = []
    disp = circ.disp
    devs = circ.bjts

    def terms_at(n):
        return [(q, r) for q in devs for r, m in (('c', q.c), ('e', q.e)) if m == n]

    def res_at(n):
        return [(el, b if a == n else a) for el, a, b in res if n in (a, b)]

    def top(q):
        return q.c if q.s > 0 else q.e

    def bot(q):
        return q.e if q.s > 0 else q.c

    nodes = set(V)
    for el, a, b in res:
        nodes.update((a, b))
    for q in devs:
        nodes.update((q.b, q.c, q.e))

    def set_vgs(q, vgs):
        VG[q.name] = vgs
        ID[q.name] = q.id_of(vgs - q.vt)

    progress = True
    while progress:
        progress = False
        # ---- node voltage by KCL (all currents known)
        for n in sorted(nodes - set(V)):
            rs = res_at(n)
            if not rs or any(m not in V for _, m in rs):
                continue
            ts = terms_at(n)
            if any(q.name not in ID for q, _ in ts):
                continue
            g = sum(1 / float(el.value) for el, _ in rs)
            inj = sum(-term_sign(q, r) * ID[q.name] for q, r in ts)
            v = (sum(V[m] / float(el.value) for el, m in rs) + inj) / g
            V[n] = v
            gates = [q for q in devs if q.b == n]
            if len(rs) == 2 and not ts:
                (ra, ma), (rb, mb) = rs
                steps.append(f'{"No current flows into a gate ($I_G = 0$), so " if gates else ""}'
                             f'${disp(n)}$ is set by the divider ${ra.tex}$--${rb.tex}$:'
                             f'\\[{disp(n)} = {num_tex(V[mb])} + ({num_tex(V[ma])} - {par(V[mb])})'
                             f'\\frac{{{Rn(rb.value)}}}{{{Rn(ra.value)} + {Rn(rb.value)}}} = {V_(v)}\\]')
            elif len(rs) == 1 and ts:
                el, m = rs[0]
                cur = [q for q, r in ts if -term_sign(q, r) > 0]       # currents INTO the node
                out = [q for q, r in ts if -term_sign(q, r) < 0]
                if out and not cur:
                    sy = ' + '.join(id_sym(q) for q in out)
                    steps.append(f'${sy}$ flows from ${disp(m)}$ through ${el.tex}$: ${disp(n)} = {disp(m)} - '
                                 f'{el.tex}{pp(sy)} = {num_tex(V[m])} - {Rn(el.value)}\\times{I_(-inj)} = {V_(v)}$.')
                else:
                    sy = ' + '.join(id_sym(q) for q in cur) + ''.join(' - ' + id_sym(q) for q in out)
                    steps.append(f'${sy} = {I_(inj)}$ flows through ${el.tex}$ to ${disp(m)}$: ${disp(n)} = '
                                 f'{disp(m)} + {el.tex}{pp(sy)} = {num_tex(V[m])} + {Rn(el.value)}\\times{I_(inj)} = '
                                 f'{V_(v)}$.')
            else:
                tt = ' + '.join(f'\\frac{{{disp(m)} - {disp(n)}}}{{{el.tex}}}' for el, m in rs)
                if ts:
                    tt += ' ' + ' '.join(f'{"+" if -term_sign(q, r) > 0 else "-"} {id_sym(q)}' for q, r in ts)
                steps.append(f'KCL at ${disp(n)}$ (currents in, $I_G = 0$): ${tt} = 0 \\Rightarrow {disp(n)} = {V_(v)}$.')
            progress = True
        # ---- resistor string between two known nodes (only gates hang on it)
        for n in sorted(nodes - set(V)):
            if terms_at(n) or len(res_at(n)) != 2:
                continue
            path = string_path(n, V, res_at, terms_at)
            if path is None:
                continue
            a_node, b_node, els, inner = path
            rtot = sum(float(e.value) for e in els)
            i = (V[a_node] - V[b_node]) / rtot
            vv = V[a_node]
            vals = []
            for e, nn in zip(els[:-1], inner):
                vv -= float(e.value) * i
                V[nn] = vv
                vals.append(f'${disp(nn)} = {num_tex(V[a_node])} - '
                            f'({" + ".join(Rn(x.value) for x in els[:els.index(e) + 1])})\\times{I_(i)} = {V_(vv)}$')
            steps.append(f'No current flows into a gate ($I_G = 0$), so the string '
                         + '--'.join(f'${e.tex}$' for e in els)
                         + f' carries one current: $I = \\frac{{{num_tex(V[a_node])} - {par(V[b_node])}}}'
                           f'{{{" + ".join(Rn(e.value) for e in els)}}} = {I_(i)}$. Hence ' + ', '.join(vals) + '.')
            progress = True
            break
        # ---- mirror rule
        for q1 in devs:
            for q2 in devs:
                if q1 is not q2 and q1.s == q2.s and q1.b == q2.b and q1.e == q2.e \
                        and q1.name in ID and q2.name not in ID:
                    ID[q2.name] = ID[q1.name] * q2.k / q1.k
                    VG[q2.name] = q2.vt + q2.vov(ID[q2.name])
                    if q1.wl and q2.wl:
                        ratio = (f'\\frac{{{wl_tex(q2)}}}{{{wl_tex(q1)}}} = '
                                 f'\\frac{{{q2.wl[0]:g}/{q2.wl[1]:g}}}{{{q1.wl[0]:g}/{q1.wl[1]:g}}}')
                    else:
                        ratio = f'\\frac{{k_{{{q2.name[1:]}}}}}{{k_{{{q1.name[1:]}}}}}'
                    same = abs(q2.k / q1.k - 1) < 1e-12
                    steps.append(f'${q2.tex}$ has the same gate and source nodes as ${q1.tex}$, hence the same '
                                 f'$V_{{GS}}$ (current mirror)'
                                 + (f': ${id_sym(q2)} = {id_sym(q1)} = {I_(ID[q2.name])}$.' if same else
                                    f'; the currents scale with $W/L$: ${id_sym(q2)} = {id_sym(q1)}\\,{ratio} = '
                                    f'{I_(ID[q2.name])}$.'))
                    progress = True
        # ---- V_GS from a known current
        for q in devs:
            if q.name in ID and q.name not in VG:
                VG[q.name] = q.vt + q.vov(ID[q.name])
            if q.name not in ID:
                continue
            vgs = VG[q.name]
            if q.b in V and q.e not in V:
                V[q.e] = V[q.b] - q.s * vgs
                steps.append(f'${q.tex}$ carries ${id_sym(q)} = {I_(ID[q.name])}$, so $V_{{ov{q.name[1:]}}} = '
                             f'\\sqrt{{2{id_sym(q)}/k_{{{q.name[1:]}}}}} = {num_tex(vgs - q.vt, 4)}$\\,V and '
                             f'${vgs_sym(q)} = {num_tex(q.vt)} + {num_tex(vgs - q.vt, 4)} = {num_tex(vgs, 4)}$\\,V: '
                             f'${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} {vgs_sym(q)} = {V_(V[q.e])}$.')
                progress = True
            elif q.e in V and q.b not in V:
                V[q.b] = V[q.e] + q.s * vgs
                steps.append(f'${q.tex}$ carries ${id_sym(q)} = {I_(ID[q.name])}$, so $V_{{ov{q.name[1:]}}} = '
                             f'\\sqrt{{2{id_sym(q)}/k_{{{q.name[1:]}}}}} = {num_tex(vgs - q.vt, 4)}$\\,V and '
                             f'${vgs_sym(q)} = {num_tex(vgs, 4)}$\\,V: ${disp(q.b)} = {disp(q.e)} '
                             f'{"+" if q.s > 0 else "-"} {vgs_sym(q)} = {V_(V[q.b])}$'
                             + (' (diode-connected: this is also its drain voltage).' if q.diode else '.'))
                progress = True
        if progress:
            continue
        # ---- gate known: KVL gate -> source -> resistor -> known node (one quadratic)
        for q in devs:
            if q.name in ID or q.b not in V or q.diode:
                continue
            k = q.name[1:]
            if q.e in V:
                vgs = q.s * (V[q.b] - V[q.e])
                if vgs <= q.vt:
                    raise ValueError(f'{q.name} is off')
                set_vgs(q, vgs)
                steps.append(f'Gate and source of ${q.tex}$ are known: ${vgs_sym(q)} = {num_tex(vgs, 4)}$\\,V, '
                             f'$V_{{ov{k}}} = {num_tex(vgs - q.vt, 4)}$\\,V, so '
                             f'${id_sym(q)} = \\frac{{k_{{{k}}}}}{{2}}V_{{ov{k}}}^2 = {I_(ID[q.name])}$.')
                progress = True
                break
            rs = res_at(q.e)
            ts = [(qq, r) for qq, r in terms_at(q.e) if qq is not q]
            if len(rs) != 1 or rs[0][1] not in V or any(qq.name not in ID for qq, _ in ts):
                continue
            el, m = rs[0]
            Rv = float(el.value)
            ioth = sum(-term_sign(qq, r) * ID[qq.name] for qq, r in ts)     # other currents INTO the source node
            veff = q.s * (V[q.b] - V[m]) - q.s * Rv * ioth
            a = Rv * q.k / 2
            b = 1 - 2 * a * q.vt
            c = a * q.vt ** 2 - veff
            disc = b * b - 4 * a * c
            r1, r2 = (-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)
            root, other = (r1, r2) if r1 > q.vt else (r2, r1)
            assert root > q.vt and other < q.vt
            set_vgs(q, root)
            V[q.e] = V[q.b] - q.s * root
            idx = ID[q.name]
            # the KVL equation as the slides write it
            oth = [(qq, r) for qq, r in ts if ID[qq.name] > 0]
            cur = id_sym(q) + ''.join((' + ' if -term_sign(qq, r) * q.s > 0 else ' - ') + id_sym(qq) for qq, r in oth)
            lhs = (f'{disp(q.b)} - {disp(m)}' if q.s > 0 else f'{disp(m)} - {disp(q.b)}')
            num = q.s * (V[q.b] - V[m])
            kvl = (f'{lhs} = {num_tex(num, 4)} = {vgs_sym(q)} + {el.tex}{pp(cur)}')
            known = (f'{num_tex(num, 4)} - {Rn(Rv)}\\times{I_(abs(ioth))}' if abs(ioth) > 0 else f'{num_tex(num, 4)}')
            sub = (f'{id_sym(q)} = \\frac{{{known} - {vgs_sym(q)}}}{{{Rn(Rv)}}} = \\frac{{{k_num(q)}}}{{2}}'
                   f'({vgs_sym(q)} - {num_tex(q.vt)})^2')
            qt, why = quad_text(a, b, c, None, root, other, vgs_sym(q), q.vt)
            steps.append(f'KVL from the gate of ${q.tex}$ through ${vgs_sym(q)}$ and ${el.tex}$ ($I_G = 0$, '
                         f'${q.tex}$ assumed active):\\[{kvl}\\]\\[{sub}\\]\\[{qt}\\]{why} Then '
                         f'${id_sym(q)} = {I_(idx)}$ and ${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} '
                         f'{vgs_sym(q)} = {V_(V[q.e])}$.')
            progress = True
            break
        if progress:
            continue
        # ---- series chain of resistors and diode-connected transistors between two known nodes
        for q0 in devs:
            if not q0.diode or q0.name in ID:
                continue
            ch = chain(q0, V, res, devs, terms_at, res_at, top, bot)
            if ch is None:
                continue
            a_node, b_node, items = ch
            qs = [it for kind, it, _ in items if kind == 'q']
            rs = [it for kind, it, _ in items if kind == 'r']
            qa = qs[0]
            vtot = V[a_node] - V[b_node]
            rtot = sum(float(r.value) for r in rs)
            cfac = [math.sqrt(qa.k / qq.k) for qq in qs]
            svt = sum(qq.vt for qq in qs)
            a = rtot * qa.k / 2
            b = sum(cfac) - 2 * a * qa.vt
            c = a * qa.vt ** 2 - sum(cfac) * qa.vt + svt - vtot
            if a == 0:
                root, other = -c / b, None
            else:
                disc = b * b - 4 * a * c
                r1, r2 = (-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)
                root, other = (r1, r2) if r1 > qa.vt else (r2, r1)
            idx = qa.id_of(root - qa.vt)
            for qq, cf in zip(qs, cfac):
                set_vgs(qq, qq.vt + (root - qa.vt) * cf)
            # node voltages down the chain
            path_txt = []
            seq = [(kind, it) for kind, it, _ in items]
            vcur = V[a_node]
            for kind, it, lo in items:
                if kind == 'r':
                    vcur -= float(it.value) * idx
                    nn = lo
                else:
                    vcur -= VG[it.name]
                    nn = bot(it)
                if nn not in V:
                    V[nn] = vcur
                    path_txt.append(f'${disp(nn)} = {V_(vcur)}$')
            kvl = ' + '.join((f'{it.tex}I_D' if kind == 'r' else vgs_sym(it)) for kind, it in seq)
            txt = (f'The reference branch is one series path from ${disp(a_node)}$ to ${disp(b_node)}$: '
                   + ', '.join(f'${it.tex}$' for _, it in seq)
                   + '. All of them carry the same current $I_D$ (gates draw none), and every diode-connected '
                     'transistor is active ($V_{DS} = V_{GS} > V_{GS} - V_t$). KVL:'
                   + f'\\[{num_tex(vtot, 4)} = {kvl}\\]')
            if len(qs) > 1:
                txt += ('Equal currents, $\\frac{k_i}{2}V_{ov,i}^2$ the same for all, give '
                        + ', '.join(f'$V_{{ov{qq.name[1:]}}} = V_{{ov{qa.name[1:]}}}\\sqrt{{k_{{{qa.name[1:]}}}/'
                                    f'k_{{{qq.name[1:]}}}}} = {num_tex(cf, 4)}\\,V_{{ov{qa.name[1:]}}}$'
                                    for qq, cf in zip(qs[1:], cfac[1:]))
                        + f'. With $I_D = \\frac{{{k_num(qa)}}}{{2}}({vgs_sym(qa)} - {num_tex(qa.vt)})^2$ '
                          f'everything is a function of ${vgs_sym(qa)}$:')
            else:
                txt += (f'With $I_D = \\frac{{{k_num(qa)}}}{{2}}({vgs_sym(qa)} - {num_tex(qa.vt)})^2$:')
            if other is not None:
                qt, why = quad_text(a, b, c, None, root, other, vgs_sym(qa), qa.vt)
                txt += f'\\[{qt}\\]{why} '
            txt += (f'Hence $I_D = {I_(idx)}$' + ''.join(f', ${vgs_sym(qq)} = {num_tex(VG[qq.name], 4)}$\\,V'
                                                         for qq in qs[1:])
                    + (', and ' + ', '.join(path_txt) if path_txt else '') + '.')
            steps.append(txt)
            progress = True
            break
        if progress:
            continue
        # ---- device current by KCL at a node whose other currents are known
        for n in sorted(nodes - set(circ.fixed)):
            ts = [(q, r) for q, r in terms_at(n) if q.name not in ID]
            if len(ts) != 1:
                continue
            q, r = ts[0]
            rs = res_at(n)
            if rs and (n not in V or any(m not in V for _, m in rs)):
                continue
            known = [(qq, rr) for qq, rr in terms_at(n) if qq.name in ID]
            if not rs and not known:
                continue
            leave = sum((V[n] - V[m]) / float(el.value) for el, m in rs) + \
                sum(term_sign(qq, rr) * ID[qq.name] for qq, rr in known)
            i = -leave / term_sign(q, r)
            ID[q.name] = i
            parts = [f'\\frac{{{disp(m)} - {disp(n)}}}{{{el.tex}}}' if term_sign(q, r) > 0 else
                     f'\\frac{{{disp(n)} - {disp(m)}}}{{{el.tex}}}' for el, m in rs]
            parts += [('-' if (term_sign(qq, rr) > 0) == (term_sign(q, r) > 0) else '+') + ' ' + id_sym(qq)
                      for qq, rr in known]
            expr = ' + '.join(parts).replace('+ -', '- ').replace('+ +', '+ ')
            if not rs and len(known) == 1:
                steps.append(f'${q.tex}$ is in series with ${known[0][0].tex}$ (nothing else draws current at '
                             f'${disp(n)}$): ${id_sym(q)} = {id_sym(known[0][0])} = {I_(i)}$.')
            else:
                steps.append(f'KCL at ${disp(n)}$: ${id_sym(q)} = {expr.lstrip("+ ")} = {I_(i)}$.')
            progress = True
            break
    missing = [q.name for q in devs if q.name not in ID]
    if missing:
        raise ValueError(f'DC propagation stuck: {missing}, known {sorted(V)}')
    return steps, V, ID, VG


def string_path(n, V, res_at, terms_at):
    """Series resistor string through node n between two known nodes, with no transistor terminals on the inner
    nodes. Returns (top known node, bottom known node, [El top..bottom], [inner nodes top..bottom]) or None."""
    (e1, m1), (e2, m2) = res_at(n)

    def walk(m, came):
        els, inner = [came], []
        while m not in V:
            rs = [(e, x) for e, x in res_at(m) if e is not came]
            if terms_at(m) or len(rs) != 1:
                return None
            inner.append(m)
            came, m = rs[0]
            els.append(came)
        return m, els, inner

    w1, w2 = walk(m1, e1), walk(m2, e2)
    if w1 is None or w2 is None:
        return None
    a, els1, in1 = w1
    b, els2, in2 = w2
    if V[a] < V[b]:
        a, b, els1, els2, in1, in2 = b, a, els2, els1, in2, in1
    return a, b, list(reversed(els1)) + els2, list(reversed(in1)) + [n] + in2


def chain(q0, V, res, devs, terms_at, res_at, top, bot):
    """Series path through q0 made of resistors and diode-connected transistors between two known nodes.
    Returns (top node, bottom node, [('r', El, lower node) | ('q', M, None)] from top to bottom) or None."""
    def walk(n, came, up):
        items = []
        while n not in V:
            conns = [('r', el, m) for el, m in res_at(n) if el is not came]
            conns += [('q', q, None) for q, r in terms_at(n) if q is not came]
            if len(conns) != 1:
                return None
            kind, it, m = conns[0]
            if kind == 'r':
                items.append(('r', it, n if up else m))
                came, n = it, m
            else:
                if not it.diode or (up and bot(it) != n) or (not up and top(it) != n):
                    return None
                items.append(('q', it, None))
                came, n = it, (top(it) if up else bot(it))
        return n, items

    w1 = walk(top(q0), q0, True)
    w2 = walk(bot(q0), q0, False)
    if w1 is None or w2 is None:
        return None
    return w1[0], w2[0], list(reversed(w1[1])) + [('q', q0, None)] + w2[1]


def exact_dc5(circ, guess):
    """Nodal solve with the square law (saturation) for every transistor; guess: starting node voltages."""
    res = flat_resistors(circ)
    nodes = set()
    for el, a, b in res:
        nodes.update((a, b))
    for q in circ.bjts:
        nodes.update((q.b, q.c, q.e))
    nodes = sorted(nodes - set(circ.fixed))
    idx = {n: i for i, n in enumerate(nodes)}

    def v(x, n):
        return circ.fixed[n] if n in circ.fixed else x[idx[n]]

    def F(x):
        out = np.zeros(len(nodes))
        for el, a, b in res:
            i = (v(x, a) - v(x, b)) / float(el.value)
            if a in idx:
                out[idx[a]] += i
            if b in idx:
                out[idx[b]] -= i
        for q in circ.bjts:
            vov = q.s * (v(x, q.b) - v(x, q.e)) - q.vt
            i = q.k / 2 * vov ** 2 if vov > 0 else 0.0
            # current flows top -> bottom: nmos drain -> source, pmos source -> drain
            for n, sgn in ((q.c, q.s), (q.e, -q.s)):
                if n in idx:
                    out[idx[n]] += sgn * i
        return out

    x0 = np.array([guess.get(n, 0.0) + 0.05 for n in nodes])
    x, info, ier, msg = fsolve(F, x0, full_output=True, xtol=1e-12)
    assert np.max(np.abs(F(x))) < 1e-11, msg
    Vx = {n: x[idx[n]] for n in nodes}
    Vx.update(circ.fixed)
    IDx = {}
    for q in circ.bjts:
        vov = q.s * (Vx[q.b] - Vx[q.e]) - q.vt
        IDx[q.name] = q.k / 2 * max(vov, 0) ** 2
    return Vx, IDx


def region_checks(circ, V, ID, VG):
    lines, ok = [], True
    for q in circ.bjts:
        k = q.name[1:]
        vov = VG[q.name] - q.vt
        vds = q.s * (V[q.c] - V[q.e])
        nm = 'DS' if q.s > 0 else 'SD'
        a, b = (q.c, q.e) if q.s > 0 else (q.e, q.c)
        if q.diode:
            lines.append(f'${q.tex}$ is diode-connected: $V_{{{nm}{k}}} = {vgs_sym(q)} > V_{{ov{k}}}$, always active '
                         '\\checkmark')
            continue
        good = vds >= vov - 1e-9
        ok &= good and vov > 0
        lines.append(f'$V_{{{nm}{k}}} = {circ.disp(a)} - {circ.disp(b)} = {num_tex(V[a], 4)} - {par(V[b])} = '
                     f'{V_(vds)}$ ' + (f'$\\ge V_{{ov{k}}} = {num_tex(vov, 3)}$\\,V $\\Rightarrow$ ${q.tex}$ is active '
                                       '\\checkmark' if good else
                                       f'$< V_{{ov{k}}} = {num_tex(vov, 3)}$\\,V: ${q.tex}$ is in triode!'))
    return lines, ok
