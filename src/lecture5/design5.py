"""MOSFET bias design (find the resistors and W/L ratios) the way Sample Problem 5 does it:
target drain currents fix V_GS = V_t + sqrt(2 I_D / k); the specifications and the stated design choices fix the other
node voltages; every resistor is R = dV / I, every mirror output gets (W/L) = (I_D / I_ref)(W/L)_ref."""
from common.units import num_tex, eng_tex
from lecture4.dc import flat_resistors, term_sign
from .dc5 import V_, I_, Rn, par, vgs_sym, id_sym


class Choice:
    """kind 'VR': voltage across resistor `target` (upper node minus lower node) = value
       kind 'IR': current through resistor `target` = value
       kind 'RPAR': target = (Ra, Rb), the two resistors of a gate divider, with Ra || Rb = value
    why: LaTeX reason in the solution; stmt: sentence for the problem statement."""
    def __init__(self, kind, target, value, why, stmt):
        self.kind, self.target, self.value, self.why, self.stmt = kind, target, value, why, stmt


def vr(rname, v):
    t = rname[0] + '_{' + rname[1:] + '}'
    return Choice('VR', rname, v, f'Design choice: $V_{{{rname}}} = {num_tex(v)}$\\,V across ${t}$',
                  f'$V_{{{rname}}} = {num_tex(v)}$\\,V')


def ir(rname, i):
    return Choice('IR', rname, i, f'Design choice: the divider current is $I_{{{rname}}} = {I_(i)}$ (any value '
                  'works for the bias because $I_G = 0$; it only sets the divider resistance)',
                  f'divider current $I_{{{rname}}} = {I_(i)}$')


def rpar(ra, rb, r):
    ta, tb = (x[0] + '_{' + x[1:] + '}' for x in (ra, rb))
    return Choice('RPAR', (ra, rb), r, f'Input-resistance requirement: ${ta}\\|{tb} = {eng_tex(r, chr(92) + "Omega")}$',
                  f'${ta}\\|{tb} = {eng_tex(r, chr(92) + "Omega")}$ (input resistance)')


class MosDesign:
    """build(vals) -> circuit; vals: {resistor name: ohms, transistor name: W} or None (blank, '?' on unknowns)."""
    def __init__(self, level, build, idt, given, choices, note=''):
        self.level, self.build, self.idt, self.given, self.choices, self.note = level, build, idt, given, choices, note


def design5(circ, idt, given, choices):
    """Returns (steps, values, V, ID)."""
    res = flat_resistors(circ)
    disp = circ.disp
    devs = circ.bjts
    V = dict(circ.fixed)
    V.update(given)
    ID = dict(idt)
    VG = {}
    val, Ir, Ilab = {}, {}, {}
    steps = []
    pending = list(choices)
    by_name = {el.name: (el, a, b) for el, a, b in res}
    sized = {}

    def terms_at(n):
        return [(q, r) for q in devs for r, m in (('c', q.c), ('e', q.e)) if m == n]

    progress = True
    while progress:
        progress = False
        # Ohm's law first, so each resistor follows right after its current
        for el, a, b in res:
            if el.name in val or el.name not in Ir or a not in V or b not in V:
                continue
            r = (V[a] - V[b]) / Ir[el.name]
            if not r > 0:
                raise ValueError(f'{el.name}: non-positive resistance {r}')
            val[el.name] = r
            steps.append(f'$\\displaystyle {el.tex} = \\frac{{{disp(a)} - {disp(b)}}}{{{Ilab[el.name]}}} = '
                         f'\\frac{{{num_tex(V[a], 4)} - {par(V[b])}}}{{{I_(Ir[el.name])}}} = '
                         f'\\mathbf{{{eng_tex(r, chr(92) + "Omega")}}}$')
            progress = True
        # design choices
        for ch in list(pending):
            if ch.kind == 'IR':
                el, a, b = by_name[ch.target]
                Ir[el.name] = ch.value
                Ilab[el.name] = f'I_{{{el.name}}}'
                steps.append(ch.why + '.')
            elif ch.kind == 'VR':
                el, a, b = by_name[ch.target]
                if a in V and b not in V:
                    V[b] = V[a] - ch.value
                    steps.append(ch.why + f': ${disp(b)} = {disp(a)} - {num_tex(ch.value)} = {V_(V[b])}$.')
                elif b in V and a not in V:
                    V[a] = V[b] + ch.value
                    steps.append(ch.why + f': ${disp(a)} = {disp(b)} + {num_tex(ch.value)} = {V_(V[a])}$.')
                else:
                    continue
            else:   # RPAR: both divider voltages known -> R_a = V_a X, R_b = V_b X
                (ea, a1, b1), (eb, a2, b2) = by_name[ch.target[0]], by_name[ch.target[1]]
                if not all(n in V for n in (a1, b1, a2, b2)):
                    continue
                va, vb = V[a1] - V[b1], V[a2] - V[b2]
                x = ch.value * (va + vb) / (va * vb)
                for el, v in ((ea, va), (eb, vb)):
                    val[el.name] = v * x
                    Ir[el.name] = 1 / x
                    Ilab[el.name] = 'I'
                steps.append(ch.why + f'. Both resistors carry the same current $I$ ($I_G = 0$), so '
                             f'${ea.tex} = V_{{{ea.name}}}/I = {num_tex(va, 4)}X$ and ${eb.tex} = {num_tex(vb, 4)}X$ '
                             f'with $X = 1/I$. Then ${ea.tex}\\|{eb.tex} = \\frac{{{num_tex(va, 4)}\\cdot{num_tex(vb, 4)}}}'
                             f'{{{num_tex(va + vb, 4)}}}X = {eng_tex(ch.value, chr(92) + "Omega")}$ gives '
                             f'$X = {eng_tex(x, chr(92) + "Omega")}$: $\\mathbf{{{ea.tex} = '
                             f'{eng_tex(va * x, chr(92) + "Omega")}}}$, $\\mathbf{{{eb.tex} = '
                             f'{eng_tex(vb * x, chr(92) + "Omega")}}}$.')
            pending.remove(ch)
            progress = True
        # mirror: sizing (unknown W) or copying a current (known W/L)
        for q1 in devs:
            for q2 in devs:
                if q1 is q2 or q1.s != q2.s or q1.b != q2.b or q1.e != q2.e or q1.name not in ID:
                    continue
                ref_ok = not getattr(q1, 'size_me', False) or q1.name in sized    # q1's W/L is known
                if not ref_ok:
                    continue
                if getattr(q2, 'size_me', False) and q2.name not in sized and q2.name in ID:
                    w = q1.wl[0] * ID[q2.name] / ID[q1.name]
                    sized[q2.name] = w
                    q2.wl = (w, q1.wl[1])
                    VG[q2.name] = q2.vt + q2.vov(ID[q2.name])
                    steps.append(f'${q2.tex}$ shares gate and source with ${q1.tex}$ (same $V_{{GS}}$), so its current '
                                 f'scales with $W/L$: $\\left(\\frac{{W}}{{L}}\\right)_{{{q2.name[1:]}}} = '
                                 f'\\frac{{{id_sym(q2)}}}{{{id_sym(q1)}}}\\left(\\frac{{W}}{{L}}\\right)_{{{q1.name[1:]}}} = '
                                 f'\\frac{{{I_(ID[q2.name])}}}{{{I_(ID[q1.name])}}}\\cdot\\frac{{{q1.wl[0]:g}}}{{{q1.wl[1]:g}}}'
                                 f' = \\mathbf{{{num_tex(w, 4)}/{q1.wl[1]:g}}}$ (keep $L = {q1.wl[1]:g}\\,\\mu$m).')
                    progress = True
                elif not getattr(q2, 'size_me', False) and q2.name not in ID:
                    ID[q2.name] = ID[q1.name] * q2.k / q1.k
                    steps.append(f'${q2.tex}$ mirrors ${q1.tex}$: ${id_sym(q2)} = {I_(ID[q2.name])}$.')
                    progress = True
        # V_GS from a known current
        for q in devs:
            if q.name not in ID or (getattr(q, 'size_me', False) and q.name not in sized):
                continue
            if q.name not in VG:
                VG[q.name] = q.vt + q.vov(ID[q.name])
                k = q.name[1:]
                vgs = VG[q.name]
                if q.b in V and q.e not in V:
                    V[q.e] = V[q.b] - q.s * vgs
                    tail = f': ${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} {vgs_sym(q)} = {V_(V[q.e])}$.'
                elif q.e in V and q.b not in V:
                    V[q.b] = V[q.e] + q.s * vgs
                    tail = (f': ${disp(q.b)} = {disp(q.e)} {"+" if q.s > 0 else "-"} {vgs_sym(q)} = {V_(V[q.b])}$'
                            + (' (diode-connected: also its drain).' if q.diode else '.'))
                else:
                    tail = '.'
                    VG[q.name] = vgs
                steps.append(f'${q.tex}$ must carry ${id_sym(q)} = {I_(ID[q.name])}$: $V_{{ov{k}}} = '
                             f'\\sqrt{{\\frac{{2{id_sym(q)}}}{{k_{{{k}}}}}}} = \\sqrt{{\\frac{{2\\cdot{I_(ID[q.name])}}}'
                             f'{{{eng_tex(q.k, chr(92) + "mathrm{A/V^2}")}}}}} = {num_tex(vgs - q.vt, 4)}$\\,V, '
                             f'${vgs_sym(q)} = {num_tex(q.vt)} + {num_tex(vgs - q.vt, 4)} = {num_tex(vgs, 4)}$\\,V' + tail)
                progress = True
            else:
                vgs = VG[q.name]
                if q.b in V and q.e not in V:
                    V[q.e] = V[q.b] - q.s * vgs
                    steps.append(f'${disp(q.e)} = {disp(q.b)} {"-" if q.s > 0 else "+"} {vgs_sym(q)} = {V_(V[q.e])}$.')
                    progress = True
                elif q.e in V and q.b not in V:
                    V[q.b] = V[q.e] + q.s * vgs
                    steps.append(f'${disp(q.b)} = {disp(q.e)} {"+" if q.s > 0 else "-"} {vgs_sym(q)} = {V_(V[q.b])}$.')
                    progress = True
        # device current by KCL (series transistors, or all other currents known)
        for n in sorted({m for q in devs for m in (q.c, q.e)} - set(circ.fixed)):
            ts = terms_at(n)
            unk = [(q, r) for q, r in ts if q.name not in ID]
            rs = [(x, xa, xb) for x, xa, xb in res if n in (xa, xb)]
            if len(unk) != 1 or any(x.name not in Ir for x, _, _ in rs) or (not rs and len(ts) < 2):
                continue
            q, r = unk[0]
            terms = [(Ir[x.name] if n == xb else -Ir[x.name], Ilab[x.name]) for x, xa, xb in rs]
            terms += [(-term_sign(qq, rr) * ID[qq.name], id_sym(qq)) for qq, rr in ts if qq is not q]
            ID[q.name] = sum(t for t, _ in terms) / term_sign(q, r)
            expr = ' '.join(f'{"+" if t * term_sign(q, r) > 0 else "-"} {sym}' for t, sym in terms).lstrip('+ ')
            steps.append(f'KCL at ${disp(n)}$ ($I_G = 0$): ${id_sym(q)} = {expr} = {I_(ID[q.name])}$.')
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
                if any(x.name not in Ir for x, _, _ in others) or any(q.name not in ID for q, _ in ts):
                    continue
                terms = [(Ir[x.name] if n == xb else -Ir[x.name], Ilab[x.name]) for x, xa, xb in others]
                terms += [(-term_sign(q, r) * ID[q.name], id_sym(q)) for q, r in ts]
                inflow = sum(t for t, _ in terms)
                Ir[el.name] = inflow if n == a else -inflow
                sgn = 1 if n == a else -1
                if len(terms) == 1:
                    Ilab[el.name] = terms[0][1]
                    steps.append(f'The only current through ${el.tex}$ is ${terms[0][1]} = {I_(abs(Ir[el.name]))}$ '
                                 '($I_G = 0$).')
                else:
                    Ilab[el.name] = f'I_{{{el.name}}}'
                    expr = ' '.join(f'{"+" if sgn * t > 0 else "-"} {lab}' for t, lab in terms if abs(t) > 0).lstrip('+ ')
                    steps.append(f'KCL at ${disp(n)}$: $I_{{{el.name}}} = {expr} = {I_(Ir[el.name])}$.')
                progress = True
                break
            if progress:
                break
    missing = [el.name for el, _, _ in res if el.name not in val]
    if missing or pending:
        raise ValueError(f'design stuck: {missing}, choices {[c.target for c in pending]}, V {sorted(V)}')
    out = dict(val)
    out.update(sized)
    return steps, out, V, ID
