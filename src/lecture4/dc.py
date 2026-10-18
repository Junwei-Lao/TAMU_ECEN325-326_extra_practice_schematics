"""DC bias analysis of BJT circuits, step by step like the slides:
assume every transistor active with I_B ~ 0 (V_BE = 0.7 V, I_C = I_E), propagate known voltages/currents node by node,
then verify I_B << bias currents and |V_CE| >= 0.2 V. An exact finite-beta solve is used as an independent check."""
import sympy as sp

from common.units import num_tex, eng_tex
from lecture1.ladder import El, Ser, Par, NamedZ

VBE = 0.7


def dc_open(z):
    """True if the impedance tree carries no DC current (capacitors are open)."""
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        return z.kind == 'C'
    if isinstance(z, Ser):
        return any(dc_open(p) for p in z.parts)
    if isinstance(z, Par):
        return all(dc_open(p) for p in z.parts)
    return False


def flat_resistors(circ):
    """DC view: list of (El R, a, b); capacitors are open, composites are expanded."""
    out = []
    k = [0]

    def new():
        k[0] += 1
        return f'_dc{k[0]}'

    def place(z, a, b):
        if isinstance(z, NamedZ):
            z = z.inner
        if isinstance(z, El):
            if z.kind == 'R':
                out.append((z, a, b))
            return
        if isinstance(z, Ser):
            if any(dc_open(p) for p in z.parts):
                return          # a part that blocks DC (a capacitor, or only capacitors) opens the series path
            cur = a
            for i, p in enumerate(z.parts):
                nxt = b if i == len(z.parts) - 1 else new()
                place(p, cur, nxt)
                cur = nxt
        elif isinstance(z, Par):
            for p in z.parts:
                place(p, a, b)

    for z, a, b in circ.branches:
        place(z, a, b)
    return out


def V_(x):
    return num_tex(round(x, 9) + 0.0, 3) + '\\,\\mathrm{V}'


def I_(x):
    return eng_tex(x, '\\mathrm{A}')


def Rn(x):
    return eng_tex(float(x), '')


def term_sign(q, role):
    """+1 if the transistor current LEAVES the node at this terminal (flows into the device)."""
    if role == 'c':
        return 1 if q.kind == 'npn' else -1
    if role == 'e':
        return -1 if q.kind == 'npn' else 1
    return 0


def solve_dc(circ):
    """Returns (steps, V, IC). steps: list of LaTeX strings in the order a student would do them."""
    res = flat_resistors(circ)
    V = dict(circ.fixed)
    IC = {}
    steps = []
    disp = circ.disp

    def terms_at(n):
        """[(q, role)] of transistor terminals at node n (bases carry no current)."""
        out = []
        for q in circ.bjts:
            if q.c == n:
                out.append((q, 'c'))
            if q.e == n:
                out.append((q, 'e'))
        return out

    nodes = set(V)
    for el, a, b in res:
        nodes.update((a, b))
    for q in circ.bjts:
        nodes.update((q.b, q.c, q.e))
    progress = True
    while progress:
        progress = False
        # V_BE rule
        for q in circ.bjts:
            if q.b in V and q.e not in V:
                V[q.e] = V[q.b] - q.s * VBE
                steps.append(f'${q.tex}$ is {q.kind} and assumed active: $V_{{BE}} = {"" if q.s > 0 else "-"}0.7$\\,V, so '
                             f'${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} 0.7 = {V_(V[q.e])}$.')
                progress = True
            elif q.e in V and q.b not in V:
                V[q.b] = V[q.e] + q.s * VBE
                steps.append(f'${q.tex}$ {"(diode-connected) " if q.diode else ""}is active: '
                             f'${disp(q.b)} = {disp(q.e)} {"+" if q.s > 0 else "-"} 0.7 = {V_(V[q.b])}$.')
                progress = True
        # mirror rule
        for q1 in circ.bjts:
            for q2 in circ.bjts:
                if q1 is not q2 and q1.kind == q2.kind and q1.b == q2.b and q1.e == q2.e \
                        and q1.name in IC and q2.name not in IC:
                    IC[q2.name] = IC[q1.name]
                    steps.append(f'${q2.tex}$ has the same base and emitter nodes as ${q1.tex}$, hence the same '
                                 f'$V_{{BE}}$ and the same current (current mirror): $I_{{C{q2.name[1:]}}} = '
                                 f'I_{{C{q1.name[1:]}}} = {I_(IC[q2.name])}$.')
                    progress = True
        # node voltage by KCL (all currents at the node known)
        for n in sorted(nodes - set(V)):
            rs = [(el, b if a == n else a) for el, a, b in res if n in (a, b)]
            if not rs or any(m not in V for _, m in rs):
                continue
            ts = terms_at(n)
            if any(q.name not in IC for q, _ in ts):
                continue
            g = sum(1 / float(el.value) for el, _ in rs)
            inj = sum(-term_sign(q, r) * IC[q.name] for q, r in ts)     # current INTO the node
            v = (sum(V[m] / float(el.value) for el, m in rs) + inj) / g
            V[n] = v
            bases = [q for q in circ.bjts if q.b == n]
            if len(rs) == 2 and not ts:
                (ra, ma), (rb, mb) = rs
                steps.append(f'{"No current flows into the base ($I_B$ is negligible), so " if bases else ""}'
                             f'${disp(n)}$ is set by the divider ${ra.tex}$--${rb.tex}$ between ${disp(ma)}$ and '
                             f'${disp(mb)}$ (Lecture-1 tool):'
                             f'\\[{disp(n)} = {num_tex(V[mb])} + ({num_tex(V[ma])} - ({num_tex(V[mb])}))'
                             f'\\frac{{{Rn(rb.value)}}}{{{Rn(ra.value)} + {Rn(rb.value)}}} = {V_(v)}\\]')
            elif len(rs) == 1 and len(ts) >= 1:
                el, m = rs[0]
                cur = ' + '.join(f'I_{{C{q.name[1:]}}}' for q, r in ts if -term_sign(q, r) > 0) or '0'
                out_ = ' + '.join(f'I_{{C{q.name[1:]}}}' for q, r in ts if -term_sign(q, r) < 0)
                if out_ and cur == '0':
                    steps.append(f'${", ".join("$" + q.tex + "$" for q, _ in ts).strip("$")}$ draw{"s" if len(ts) == 1 else ""} '
                                 f'${out_} = {I_(-inj)}$ from ${disp(n)}$ through ${el.tex}$: '
                                 f'${disp(n)} = {disp(m)} - {el.tex}\\,({out_}) = {num_tex(V[m])} - {Rn(el.value)}'
                                 f'\\times{I_(-inj)} = {V_(v)}$.')
                else:
                    steps.append(f'The current ${cur}{(" - " + out_) if out_ else ""} = {I_(inj)}$ flows from '
                                 f'${disp(n)}$ through ${el.tex}$: ${disp(n)} = {disp(m)} + {el.tex}\\,({cur}'
                                 f'{(" - " + out_) if out_ else ""}) = {num_tex(V[m])} + {Rn(el.value)}\\times'
                                 f'{I_(inj)} = {V_(v)}$.')
            else:
                tt = ' + '.join(f'\\frac{{{disp(m)} - {disp(n)}}}{{{el.tex}}}' for el, m in rs)
                if ts:
                    tt += ' ' + ' '.join(f'{"+" if -term_sign(q, r) > 0 else "-"} I_{{C{q.name[1:]}}}' for q, r in ts)
                steps.append(f'KCL at ${disp(n)}$ (currents in): ${tt} = 0 \\Rightarrow {disp(n)} = {V_(v)}$.')
            progress = True
        # transistor current by KCL at a node whose voltage is known
        for n in sorted(set(V) - set(circ.fixed)):
            ts = [(q, r) for q, r in terms_at(n) if q.name not in IC]
            if len(ts) != 1:
                continue
            q, r = ts[0]
            rs = [(el, b if a == n else a) for el, a, b in res if n in (a, b)]
            if any(m not in V for _, m in rs):
                continue
            known = [(qq, rr) for qq, rr in terms_at(n) if qq.name in IC]
            if not rs and not known:
                continue
            leave = sum((V[n] - V[m]) / float(el.value) for el, m in rs) + \
                sum(term_sign(qq, rr) * IC[qq.name] for qq, rr in known)
            i = -leave / term_sign(q, r)
            IC[q.name] = i
            what = 'emitter' if r == 'e' else 'collector'
            parts = []
            for el, m in rs:
                parts.append(f'\\frac{{{disp(m)} - {disp(n)}}}{{{el.tex}}}' if term_sign(q, r) > 0 else
                             f'\\frac{{{disp(n)} - {disp(m)}}}{{{el.tex}}}')
            for qq, rr in known:
                parts.append(('-' if (term_sign(qq, rr) > 0) == (term_sign(q, r) > 0) else '+')
                             + f' I_{{C{qq.name[1:]}}}')
            expr = ' + '.join(parts).replace('+ -', '- ').replace('+ +', '+ ')
            if expr.startswith('+ '):
                expr = expr[2:]
            nums = ' + '.join(f'\\frac{{{num_tex(V[m] if term_sign(q, r) > 0 else V[n])} - '
                              f'({num_tex(V[n] if term_sign(q, r) > 0 else V[m])})}}{{{Rn(el.value)}}}' for el, m in rs)
            lab = 'E' if r == 'e' else 'C'
            steps.append(f'KCL at the {what} of ${q.tex}$ (base current neglected): '
                         f'\\[I_{{{lab}{q.name[1:]}}} = {expr} = {I_(i)}'
                         f'{(", \\qquad I_{C" + q.name[1:] + "} \\approx I_{E" + q.name[1:] + "}") if r == "e" else ""}\\]')
            progress = True
    missing = [q.name for q in circ.bjts if q.name not in IC]
    if missing:
        raise ValueError(f'DC propagation stuck: {missing}, known nodes {sorted(V)}')
    return steps, V, IC


def checks(circ, V, IC):
    """I_B negligible + active-region checks. Returns (latex lines, ok flags)."""
    res = flat_resistors(circ)
    lines, ok = [], True
    for q in circ.bjts:
        ib = IC[q.name] / q.beta
        n = q.b
        sib = sum(IC[qq.name] / qq.beta for qq in circ.bjts if qq.b == n)
        cur = [abs(V[a] - V[b]) / float(el.value) for el, a, b in res if n in (a, b)]
        ref = max(cur) if cur else None
        if ref:
            good = sib < 0.1 * ref
            ok &= good
            others = [qq for qq in circ.bjts if qq.b == n and qq is not q]
            lines.append(f'$I_{{B{q.name[1:]}}} = \\frac{{I_{{C{q.name[1:]}}}}}{{\\beta}} = {I_(ib)}$'
                         + (f' (all bases on this node: ${I_(sib)}$)' if others else '')
                         + f' {"$\\ll$" if good else "is NOT $\\ll$"} the ${I_(ref)}$ flowing in the base network '
                         + ('\\checkmark' if good else '(the result is only approximate)'))
    for q in circ.bjts:
        vce = (V[q.c] - V[q.e]) * q.s
        good = vce >= 0.2
        ok &= good
        nm = 'CE' if q.kind == 'npn' else 'EC'
        a, b = (q.c, q.e) if q.kind == 'npn' else (q.e, q.c)
        lines.append(f'$V_{{{nm}{q.name[1:]}}} = {circ.disp(a)} - {circ.disp(b)} = {num_tex(V[a], 4)} - '
                     f'({num_tex(V[b], 4)}) = {V_(vce)}$ '
                     + (f'$\\ge 0.2$\\,V $\\Rightarrow$ ${q.tex}$ is active \\checkmark' if good else
                        f'$< 0.2$\\,V: ${q.tex}$ is saturated!'))
    return lines, ok


def exact_dc(circ, vbe=VBE):
    """Finite-beta solve (V_BE = 0.7 or a {name: V_BE} dict, I_C = beta I_B, I_E = (beta+1) I_B), all transistors active."""
    res = flat_resistors(circ)
    nodes = set()
    for el, a, b in res:
        nodes.update((a, b))
    for q in circ.bjts:
        nodes.update((q.b, q.c, q.e))
    nodes -= set(circ.fixed)
    V = {n: sp.Symbol('V_' + n) for n in nodes}
    IB = {q.name: sp.Symbol('IB_' + q.name) for q in circ.bjts}

    def v(n):
        return circ.fixed[n] if n in circ.fixed else V[n]

    eqs = []
    for n in nodes:
        e = 0
        for el, a, b in res:
            if n in (a, b):
                m = b if a == n else a
                e += (v(n) - v(m)) / sp.Float(float(el.value))
        for q in circ.bjts:
            if q.b == n:
                e += q.s * IB[q.name]
            if q.c == n:
                e += q.s * q.beta * IB[q.name]
            if q.e == n:
                e -= q.s * (q.beta + 1) * IB[q.name]
        eqs.append(e)
    seen = {}
    for q in circ.bjts:
        key = (q.kind, q.b, q.e)
        if key in seen:   # matched transistors with the same V_BE carry the same current
            eqs.append(IB[q.name] - IB[seen[key]])
        else:
            seen[key] = q.name
            vq = vbe.get(q.name, VBE) if isinstance(vbe, dict) else vbe
            eqs.append(v(q.b) - v(q.e) - q.s * vq)
    sol = sp.solve(eqs, list(V.values()) + list(IB.values()), dict=True)[0]
    Vx = {n: float(sol[V[n]]) for n in nodes}
    Vx.update(circ.fixed)
    ICx = {q.name: float(q.beta * sol[IB[q.name]]) for q in circ.bjts}
    return Vx, ICx
