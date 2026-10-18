"""DC bias design (find the resistors), step by step like Sample Problems 3 and 6:
the specifications fix the collector currents and some node voltages, the design rules fix the rest
(V_RE >= 1 V for V_BE-insensitivity, divider current >> I_B), and every resistor follows from Ohm's law
once both of its node voltages and its current are known. I_B ~ 0 throughout."""
from common.units import num_tex, eng_tex, parse
from .dc import flat_resistors, term_sign, VBE, V_, I_, Rn, exact_dc, checks


class Choice:
    """A design decision.
    kind 'VR': voltage across resistor `target` (upper node minus lower node) = value
    kind 'IR': current through resistor `target` (downwards) = value
    why: LaTeX reason used in the solution; stmt: sentence for the problem statement (None = follows from the rules)."""
    def __init__(self, kind, target, value, why, stmt=None):
        self.kind, self.target, self.value, self.why, self.stmt = kind, target, value, why, stmt


def vre(rname, v=1.0, rule=True):
    why = (f'$V_{{BE}}$-insensitivity: a $0.1$\\,V change of $V_{{BE}}$ changes the voltage across ${rname_tex(rname)}$ '
           f'by $0.1$\\,V, so $\\frac{{\\Delta I_C}}{{I_C}} = \\frac{{0.1}}{{V_{{{rname}}}}} \\le 10\\%$ needs '
           f'$V_{{{rname}}} \\ge 1$\\,V. ' + ('Choose the smallest value, ' if rule else 'As specified (larger, for accuracy), ')
           + f'$V_{{{rname}}} = {num_tex(v)}$\\,V')
    return Choice('VR', rname, v, why, None if rule else f'$V_{{{rname}}} = {num_tex(v)}$\\,V')


def idiv(rname, i, ib_tex, n_txt):
    """Divider current choice. ib_tex: the base current(s) it must dominate, n_txt: e.g. '50 times'."""
    why = (f'The divider current must be much larger than the base current it feeds ({ib_tex}). '
           f'Choose $I_{{{rname}}} = {I_(i)}$ ({n_txt} larger)')
    return Choice('IR', rname, i, why, f'divider current $I_{{{rname}}} = {I_(i)}$')


def rname_tex(n):
    head = n.rstrip('0123456789')
    return f'{head}_{{{n[len(head):]}}}'


class DCDesign:
    """Problem data: build(values) -> BJTCircuit (values: {resistor name: ohms} or None for the blank drawing)."""
    def __init__(self, level, build, ic, given, choices, vce_min=0.2, idc_max=None, note=''):
        self.level, self.build, self.ic, self.given, self.choices = level, build, ic, given, choices
        self.vce_min, self.idc_max, self.note = vce_min, idc_max, note


def design_dc(circ, ic, given, choices):
    """Returns (steps, values, V, Ir). ic: {Q name: I_C}, given: {node: volts}."""
    res = flat_resistors(circ)
    disp = circ.disp
    V = dict(circ.fixed)
    V.update(given)
    IC = dict(ic)
    val, Ir, Ilab = {}, {}, {}
    steps = []
    pending = list(choices)
    by_name = {el.name: (el, a, b) for el, a, b in res}

    def terms_at(n):
        return [(q, r) for q in circ.bjts for r, m in (('c', q.c), ('e', q.e)) if m == n]

    progress = True
    while progress:
        progress = False
        # Ohm's law
        for el, a, b in res:
            if el.name in val or el.name not in Ir or a not in V or b not in V:
                continue
            r = (V[a] - V[b]) / Ir[el.name]
            if not r > 0:
                raise ValueError(f'{el.name}: non-positive resistance {r}')
            val[el.name] = r
            steps.append(f'$\\displaystyle {el.tex} = \\frac{{{disp(a)} - {disp(b)}}}{{{Ilab[el.name]}}} = '
                         f'\\frac{{{num_tex(V[a])} - {par(V[b])}}}{{{I_(Ir[el.name])}}} = '
                         f'\\mathbf{{{eng_tex(r, chr(92) + "Omega")}}}$')
            progress = True
        # design choices that can be applied now
        for ch in list(pending):
            el, a, b = by_name[ch.target]
            if ch.kind == 'IR':
                Ir[el.name] = ch.value
                Ilab[el.name] = f'I_{{{el.name}}}'
                steps.append(ch.why + '.')
            elif ch.kind == 'VR':
                if a in V and b not in V:
                    V[b] = V[a] - ch.value
                    steps.append(ch.why + f': ${disp(b)} = {disp(a)} - V_{{{el.name}}} = {num_tex(V[a])} - '
                                 f'{num_tex(ch.value)} = {V_(V[b])}$.')
                elif b in V and a not in V:
                    V[a] = V[b] + ch.value
                    steps.append(ch.why + f': ${disp(a)} = {disp(b)} + V_{{{el.name}}} = {num_tex(V[b])} + '
                                 f'{num_tex(ch.value)} = {V_(V[a])}$.')
                else:
                    continue
            pending.remove(ch)
            progress = True
        # V_BE rule
        for q in circ.bjts:
            if q.b in V and q.e not in V:
                V[q.e] = V[q.b] - q.s * VBE
                steps.append(f'${q.tex}$ is active: ${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} 0.7 = '
                             f'{V_(V[q.e])}$.')
                progress = True
            elif q.e in V and q.b not in V:
                V[q.b] = V[q.e] + q.s * VBE
                steps.append(f'${q.tex}$ {"(diode-connected) " if q.diode else ""}is active: ${disp(q.b)} = {disp(q.e)} {"+" if q.s > 0 else "-"} 0.7 = '
                             f'{V_(V[q.b])}$.')
                progress = True
        # mirror rule
        for q1 in circ.bjts:
            for q2 in circ.bjts:
                if q1 is not q2 and q1.kind == q2.kind and q1.b == q2.b and q1.e == q2.e \
                        and q1.name in IC and q2.name not in IC:
                    IC[q2.name] = IC[q1.name]
                    steps.append(f'${q2.tex}$ mirrors ${q1.tex}$ (same base and emitter nodes): '
                                 f'$I_{{C{q2.name[1:]}}} = I_{{C{q1.name[1:]}}} = {I_(IC[q2.name])}$.')
                    progress = True
        # transistor current by KCL at a node where every other current is known
        for n in sorted({m for q in circ.bjts for m in (q.c, q.e)} - set(circ.fixed)):
            ts = terms_at(n)
            unk = [(q, r) for q, r in ts if q.name not in IC]
            rs = [(x, xa, xb) for x, xa, xb in res if n in (xa, xb)]
            if len(unk) != 1 or any(x.name not in Ir for x, _, _ in rs) or (not rs and len(ts) < 2):
                continue
            q, r = unk[0]
            terms = [(Ir[x.name] if n == xb else -Ir[x.name], Ilab[x.name]) for x, xa, xb in rs]
            terms += [(-term_sign(qq, rr) * IC[qq.name], f'I_{{C{qq.name[1:]}}}') for qq, rr in ts if qq is not q]
            inflow = sum(t for t, _ in terms)
            IC[q.name] = inflow / term_sign(q, r)
            lab = 'E' if r == 'e' else 'C'
            expr = ' '.join(f'{"+" if t * term_sign(q, r) > 0 else "-"} {sym}' for t, sym in terms).lstrip('+ ')
            steps.append(f'KCL at ${disp(n)}$ ($I_B\\approx0$): $I_{{{lab}{q.name[1:]}}} = {expr} = {I_(IC[q.name])}$'
                         + (' $\\approx I_{C' + q.name[1:] + '}$.' if r == 'e' else '.'))
            progress = True
        # resistor current by KCL at one of its ends
        for el, a, b in res:
            if el.name in Ir:
                continue
            for n in (a, b):
                if n in circ.fixed:
                    continue
                others = [(x, xa, xb) for x, xa, xb in res if n in (xa, xb) and x is not el]
                ts = terms_at(n)
                if any(x.name not in Ir for x, _, _ in others) or any(q.name not in IC for q, _ in ts):
                    continue
                terms = []      # (current INTO node n, symbol)
                for x, xa, xb in others:
                    terms.append((Ir[x.name] if n == xb else -Ir[x.name], Ilab[x.name]))
                for q, r in ts:
                    terms.append((-term_sign(q, r) * IC[q.name], f'I_{{{"C" if r == "c" else "E"}{q.name[1:]}}}'))
                inflow = sum(t for t, _ in terms)
                Ir[el.name] = inflow if n == a else -inflow
                sgn = 1 if n == a else -1
                expr = ' '.join(f'{"+" if sgn * t > 0 else "-"} {lab}' for t, lab in terms if abs(t) > 0).lstrip('+ ')
                if len(terms) == 1 and abs(Ir[el.name] - abs(terms[0][0])) < 1e-15:
                    Ilab[el.name] = terms[0][1]
                    steps.append(f'With $I_B\\approx0$ the only current through ${el.tex}$ is ${terms[0][1]}$: '
                                 f'$I_{{{el.name}}} = {terms[0][1]} = {I_(Ir[el.name])}$'
                                 + (' ($I_C\\approx I_E$).' if terms[0][1].startswith('I_{E') else '.'))
                else:
                    Ilab[el.name] = f'I_{{{el.name}}}'
                    steps.append(f'KCL at ${disp(n)}$ ($I_B\\approx0$): $I_{{{el.name}}} = {expr} = {I_(Ir[el.name])}$.')
                progress = True
                break
            if progress:
                break
    missing = [el.name for el, _, _ in res if el.name not in val]
    if missing or pending:
        raise ValueError(f'design stuck: resistors {missing}, choices {[c.target for c in pending]}, V {sorted(V)}')
    return steps, val, V, IC, Ir


def par(x):
    return f'({num_tex(x)})' if x < 0 else num_tex(x)


def supply_current(circ, V, IC, Ir):
    """Current drawn from the most positive rail (I_B ~ 0) and the symbols that make it up."""
    top = max((n for n in circ.fixed if n.startswith('rail')), key=lambda n: circ.fixed[n])
    res = flat_resistors(circ)
    parts = []
    for el, a, b in res:
        if a == top:
            parts.append((Ir[el.name], f'I_{{{el.name}}}'))
    for q in circ.bjts:
        for r, n in (('c', q.c), ('e', q.e)):
            if n == top:
                parts.append((term_sign(q, r) * IC[q.name], f'I_{{C{q.name[1:]}}}'))
    return top, parts


def sensitivity(circ):
    """{Q name: (I_C exact, I_C at V_BE 0.6, I_C at V_BE 0.8)} with only that transistor's V_BE changed."""
    _, base = exact_dc(circ)
    out = {}
    lead = {}
    for q in circ.bjts:
        key = (q.kind, q.b, q.e)
        lead.setdefault(key, q.name)
    for q in circ.bjts:
        k = lead[(q.kind, q.b, q.e)]
        _, lo = exact_dc(circ, {k: VBE - 0.1})
        _, hi = exact_dc(circ, {k: VBE + 0.1})
        out[q.name] = (base[q.name], lo[q.name], hi[q.name])
    return out
