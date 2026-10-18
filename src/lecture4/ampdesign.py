"""Amplifier design with the procedures of the slides (one-, two- and three-stage designs, Sample Problem 11).

Chain: a list of common-emitter stages ('npn'/'pnp'), optionally followed by an emitter follower ('F', of the opposite
type of the last CE stage). Stage 1 has a base divider and a coupling capacitor at its input; every later stage is
direct-coupled (its base is the previous collector). Each CE stage has R_C, R_E and R_G (R_G in series with an
'infinite' bypass capacitor, parallel to R_E). The follower has R_H; the load R_L is capacitively coupled.

Design order (as in the slides): the output stage fixes V_RC from the swing, the follower R_H from current clipping,
middle stages use a chosen gain and current, the input stage gets I_C,max from the input-resistance spec.
Everything is then checked by analysis (exact DC with beta, exact small-signal gain) and R_G1 is trimmed."""
import math

from common.units import num_tex, eng_tex
from lecture1.ladder import Ser, Par
from .bjtnet import R, C, Q, Col, BJTCircuit, Src, Load
from .dc import exact_dc
from .ac import ACView
from common.tf import s

VT = 0.025
VSAT = 0.2
BETA = 100
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]


def e12_floor(x):
    k = math.floor(math.log10(x))
    m = x / 10 ** k
    best = max(v for v in E12 if v <= m * (1 + 1e-9))
    return best * 10 ** k


def e12_ceil(x):
    k = math.floor(math.log10(x))
    m = x / 10 ** k
    c = [v for v in E12 if v >= m * (1 - 1e-9)]
    return (c[0] if c else 10.0) * 10 ** k


def Om(x):
    return eng_tex(x, '\\Omega')


def A(x):
    return eng_tex(x, '\\mathrm{A}')


def Vv(x):
    return num_tex(round(x, 9) + 0.0, 4) + '\\,\\mathrm{V}'


def par2(a, b):
    return a * b / (a + b)


class AmpSpec:
    """chain: e.g. ('npn',), ('pnp', 'F'), ('pnp', 'npn', 'F').
    vo: specified minimum 0-to-peak output swing; vo_d: swing used in the design (vo plus a margin).
    vre: V_RE of each CE stage; av_mid: chosen |A_v| of CE stages 2..k; ic_mid: chosen I_C of CE stages 2..k
    (None = smallest E12 value >= N I_C(next)/beta); rh: chosen R_H (None = largest E12 value <= R_H,max);
    ic1: chosen I_C1 (None = largest E12 value <= I_C1,max)."""
    def __init__(self, level, chain, vcc, vo, av, ri, rl=None, thd=None, vo_d=None, n=10, vre=None, av_mid=(),
                 ic_mid=None, rh=None, ic1=None, note=''):
        self.level, self.chain, self.vcc, self.vo, self.av, self.ri, self.rl = level, chain, vcc, vo, av, ri, rl
        self.thd, self.vo_d, self.n = thd, vo_d or vo, n
        self.ces = [c for c in chain if c != 'F']
        self.follower = 'F' in chain
        self.vre = list(vre) if vre else [1.0] * len(self.ces)
        self.av_mid = list(av_mid)
        self.ic_mid = list(ic_mid) if ic_mid else [None] * (len(self.ces) - 1)
        self.rh, self.ic1, self.note = rh, ic1, note


# ------------------------------------------------------------------------------------------ circuit
def roles(p):
    """Resistor names in drawing order and their roles. Returns {role: name} and [(name, role tex)]."""
    k = [0]
    role, order = {}, []

    def nxt(r, tex):
        k[0] += 1
        role[r] = f'R{k[0]}'
        order.append((f'R{k[0]}', tex))

    nxt('B1', 'R_{B1}')
    nxt('B2', 'R_{B2}')
    for i, kind in enumerate(p.ces, 1):
        if kind == 'npn':
            nxt(f'C{i}', f'R_{{C{i}}}')
            nxt(f'E{i}', f'R_{{E{i}}}')
            nxt(f'G{i}', f'R_{{G{i}}}')
        else:
            nxt(f'E{i}', f'R_{{E{i}}}')
            nxt(f'G{i}', f'R_{{G{i}}}')
            nxt(f'C{i}', f'R_{{C{i}}}')
    if p.follower:
        nxt('H', 'R_H')
    if p.rl:
        role['L'] = 'R_L'
    return role, order


def build(p, vals=None, rs=None):
    """The amplifier; vals: {resistor name: ohms} (None: blank drawing). rs: test source resistance (for R_i)."""
    role, _ = roles(p)

    def r(rl):
        n = role[rl]
        return R(n, repr(float(vals[n])) if vals else '1k')

    vcc = p.vcc
    cols = [Col([r('B1'), 'b1', r('B2')], top=vcc, bottom=0, gap=3.2)]
    kc = [1]

    def cap():
        kc[0] += 1
        return C(f'C{kc[0]}', 'inf')

    base = 'b1'
    for i, kind in enumerate(p.ces, 1):
        q = Q(f'Q{i}', kind, base=base)
        eg = Par(r(f'E{i}'), Ser(cap(), r(f'G{i}')))
        if kind == 'npn':
            cols.append(Col([r(f'C{i}'), f'c{i}', q, f'e{i}', eg], top=vcc, bottom=0))
        else:
            cols.append(Col([eg, f'e{i}', q, f'c{i}', r(f'C{i}')], top=vcc, bottom=0))
        base = f'c{i}'
    out = base
    if p.follower:
        k = len(p.ces) + 1
        if p.ces[-1] == 'pnp':
            cols.append(Col([Q(f'Q{k}', 'npn', base=base), f'e{k}', r('H')], top=vcc, bottom=0))
        else:
            cols.append(Col([r('H'), f'e{k}', Q(f'Q{k}', 'pnp', base=base)], top=vcc, bottom=0))
        out = f'e{k}'
    src = Src('b1', rs=R('R99', repr(float(rs))) if rs else None, c=C('C1', 'inf'))
    load = Load(out, c=cap(), rl=R('R_L', repr(float(p.rl))) if p.rl else None)
    return BJTCircuit(cols, src=src, load=load)


# ------------------------------------------------------------------------------------------ design
def design(p):
    """Returns dict(steps=[(title, latex)], vals={R name: ohms}, st=per-stage data)."""
    role, order = roles(p)
    k = len(p.ces)
    vcc, vo, n = p.vcc, p.vo_d, p.n
    steps = []
    st = [dict(kind=c) for c in p.ces]
    vals = {}

    def put(rl, v):
        vals[role[rl]] = v

    # ---------------- output CE stage and follower
    last = st[-1]
    vre_k = p.vre[-1]
    last['vre'] = vre_k
    t = []
    t.append(f'$V_{{BE}}$-insensitive: $V_{{RE{k}}} \\ge 1$\\,V; use $V_{{RE{k}}} = {num_tex(vre_k)}$\\,V.')
    vrc_max = vcc - vo - vre_k - VSAT
    if k == 1:
        t.append('To avoid clipping at saturation the collector must be able to swing down by $\\hat V_o$ without '
                 '$V_{CE}$ dropping below $V_{CE,sat}$, and at cutoff $V_{RC}$ must be at least $\\hat V_o$: '
                 f'$V_{{CC}} - \\hat V_o - V_{{RE1}} - V_{{CE,sat}} \\ge V_{{RC1}} \\ge \\hat V_o$. Take the largest value '
                 f'(most gain, best linearity): \\[V_{{RC1}} = {num_tex(vcc)} - {num_tex(vo)} - {num_tex(vre_k)} - '
                 f'{num_tex(VSAT)} = {Vv(vrc_max)} \\;\\ge\\; \\hat V_o = {Vv(vo)}\\ \\checkmark\\]')
        avmax = vrc_max / VT
        t.append(f'Maximum available gain ($R_G=0$, $R_C$ only): $|A_v|_{{max}} = \\frac{{R_C}}{{r_e}} = '
                 f'\\frac{{V_{{RC1}}/I_C}}{{V_T/I_C}} = \\frac{{V_{{RC1}}}}{{V_T}} = \\frac{{{num_tex(vrc_max)}}}{{0.025}} = '
                 f'{num_tex(avmax, 4)} \\ge {num_tex(p.av)}$ \\checkmark')
        assert avmax > p.av
    else:
        t.append(f'Collector swing of $Q_{{{k}}}$: about $\\hat V_o$ (the follower has a gain close to 1). '
                 f'Largest $V_{{RC{k}}}$ without clipping: \\[V_{{RC{k}}} = V_{{CC}} - \\hat V_o - V_{{RE{k}}} - '
                 f'V_{{CE,sat}} = {num_tex(vcc)} - {num_tex(vo)} - {num_tex(vre_k)} - {num_tex(VSAT)} = {Vv(vrc_max)}\\]')
    last['vrc'] = vrc_max
    if p.follower:
        rl = p.rl
        vrh = vrc_max - 0.7
        rh_max = rl * (vrh - vo) / vo
        rh = p.rh if p.rh else e12_floor(rh_max)
        ic_f = vrh / rh
        re_f = VT / ic_f
        rhl = par2(rh, rl)
        ri_f = (BETA + 1) * (re_f + rhl)
        av_f = rhl / (re_f + rhl)
        put('H', rh)
        t.append(f'Follower $Q_{{{k + 1}}}$: its emitter sits at $0.7$\\,V from the collector of $Q_{{{k}}}$, so '
                 f'$V_{{RH}} = V_{{RC{k}}} - 0.7 = {Vv(vrh)}$. To avoid current clipping the DC current in $R_H$ must '
                 f'stay larger than the peak current pushed into $R_L$: \\[\\frac{{V_{{RC{k}}} - 0.7 - \\hat V_o}}{{R_H}} '
                 f'\\ge \\frac{{\\hat V_o}}{{R_L}} \\Rightarrow R_H \\le R_L\\frac{{V_{{RC{k}}} - 0.7 - \\hat V_o}}{{\\hat V_o}} = '
                 f'{Om(rl)}\\cdot\\frac{{{num_tex(vrh)} - {num_tex(vo)}}}{{{num_tex(vo)}}} = {Om(rh_max)}\\]'
                 + (f'Use $R_H = \\mathbf{{{Om(rh)}}}$ (given). ' if p.rh else
                    f'Take the E12 value just below: $R_H = \\mathbf{{{Om(rh)}}}$. ')
                 + f'Then $I_{{C{k + 1}}} \\approx \\frac{{V_{{RH}}}}{{R_H}} = \\frac{{{num_tex(vrh)}}}{{{Om(rh)}}} = {A(ic_f)}$, '
                 f'$r_{{e{k + 1}}} = \\frac{{V_T}}{{I_{{C{k + 1}}}}} = {Om(re_f)}$, and with $R_H \\| R_L = {Om(rhl)}$:'
                 f'\\[A_{{v{k + 1}}} = \\frac{{R_H\\|R_L}}{{r_{{e{k + 1}}} + R_H\\|R_L}} = {num_tex(av_f, 4)},\\qquad '
                 f'R_{{i{k + 1}}} = (\\beta+1)(r_{{e{k + 1}}} + R_H\\|R_L) = {Om(ri_f)}\\]')
        fol = dict(rh=rh, ic=ic_f, re=re_f, ri=ri_f, av=av_f, rhl=rhl, vrh=vrh)
        load_k = ri_f
    else:
        fol = None
        load_k = p.rl if p.rl else math.inf
        av_f = 1.0
    steps.append(('Output stage' + (' and follower' if p.follower else ''), '\n\n'.join(x for x in t if x)))

    # ---------------- gains of the CE stages
    av_ce = [None] * k
    for j in range(1, k):
        av_ce[j] = p.av_mid[j - 1]
    av_ce[0] = p.av / (av_f * math.prod(av_ce[1:]))

    # ---------------- later CE stages (k .. 2), from the output backwards
    load = load_k
    for j in range(k - 1, 0, -1):
        sj = st[j]
        i = j + 1
        if j < k - 1:
            sj['vre'] = p.vre[j]
        sj.setdefault('vre', p.vre[j])
        if j < k - 1:   # a middle stage below another CE stage: V_RC fixed by the next base
            nxt = st[j + 1]
            sj['vrc'] = coupled_vrc(sj['kind'], nxt['kind'], vcc, nxt['vre'])
        nxt_ic = (fol['ic'] if (j == k - 1 and fol) else st[j + 1]['ic']) if (j < k - 1 or fol) else None
        icmin = n * nxt_ic / BETA if nxt_ic else 0
        ic = p.ic_mid[j - 1] or e12_ceil(icmin)
        sj['ic'] = ic
        t = []
        if j < k - 1:
            t.append(f'$V_{{RE{i}}} = {num_tex(sj["vre"])}$\\,V; the base of $Q_{{{i + 1}}}$ fixes '
                     f'$V_{{RC{i}}} = {Vv(sj["vrc"])}$.')
        if nxt_ic:
            t.append(f'$\\beta$-insensitive: $I_{{C{i}}} \\ge N\\frac{{I_{{C{i + 1}}}}}{{\\beta}} = '
                     f'{n}\\cdot\\frac{{{A(nxt_ic)}}}{{{BETA}}} = {A(icmin)}$; '
                     + (f'use $I_{{C{i}}} = {A(ic)}$ (given).' if p.ic_mid[j - 1] else
                        f'take the E12 value just above, $I_{{C{i}}} = {A(ic)}$.'))
        t += stage_resistors(sj, i, ic, load, av_ce[j], put, given_gain=True)
        load = sj['ri']
        steps.append((f'Stage {i} (common emitter, $Q_{{{i}}}$)', '\n\n'.join(x for x in t if x)))

    # ---------------- input stage
    s1 = st[0]
    s1['vre'] = p.vre[0]
    t = []
    if k > 1:
        s1['vrc'] = coupled_vrc(s1['kind'], st[1]['kind'], vcc, st[1]['vre'])
        prod = av_f * math.prod(av_ce[1:])
        t.append(f'Gain left for stage 1: $|A_{{v1}}| = \\frac{{|A_v|}}{{'
                 + ' '.join(f'|A_{{v{j + 1}}}|' for j in range(1, k)) + (f' A_{{v{k + 1}}}' if p.follower else '')
                 + f'}} = \\frac{{{num_tex(p.av)}}}{{{num_tex(prod, 4)}}} = {num_tex(av_ce[0], 4)}$. '
                 f'The base of $Q_2$ fixes the collector of $Q_1$: $V_{{RC1}} = {Vv(s1["vrc"])}$. '
                 + vre1_text(s1, st, vcc, vo, av_f, av_ce, k))
    vrb_e = s1['vre'] + 0.7
    vrb_c = vcc - vrb_e
    vb1 = vrb_e if s1['kind'] == 'npn' else vcc - vrb_e
    vrb1 = vcc - vb1
    vrb2 = vb1
    s1['vrb1'], s1['vrb2'] = vrb1, vrb2
    icmax = (BETA / p.ri) / (n / vrb_e + n / vrb_c + av_ce[0] / s1['vrc'])
    ic1 = p.ic1 or e12_floor(icmax)
    s1['ic'] = ic1
    t.append(f'Divider: $V_{{RB2}} = V_{{B1}} = {Vv(vb1)}$, $V_{{RB1}} = V_{{CC}} - V_{{B1}} = {Vv(vrb1)}$ '
             f'($|V_{{RE1}}| + 0.7$ on the emitter side). '
             f'$\\beta$-insensitive: the divider current is $N$ times the base current, $I_{{RB}} = N\\frac{{I_{{C1}}}}{{\\beta}}$, '
             f'$N = {n}$. Input resistance (all three in parallel, with $(\\beta+1)(r_e + R_E\\|R_G) \\approx '
             f'\\beta\\frac{{R_{{C1}}}}{{|A_{{v1}}|}} = \\beta\\frac{{V_{{RC1}}}}{{I_{{C1}}|A_{{v1}}|}}$):'
             f'\\[R_i \\approx \\frac{{\\beta/I_{{C1}}}}{{\\frac{{N}}{{V_{{RB1}}}} + \\frac{{N}}{{V_{{RB2}}}} + '
             f'\\frac{{|A_{{v1}}|}}{{V_{{RC1}}}}}} \\ge R_{{i,spec}} \\;\\Rightarrow\\; I_{{C1}} \\le '
             f'\\frac{{\\beta/R_{{i,spec}}}}{{\\frac{{{n}}}{{{num_tex(vrb1)}}} + \\frac{{{n}}}{{{num_tex(vrb2)}}} + '
             f'\\frac{{{num_tex(av_ce[0], 4)}}}{{{num_tex(s1["vrc"])}}}}} = {A(icmax)}\\]'
             + (f'Use $I_{{C1}} = {A(ic1)}$ (given). ' if p.ic1 else
                f'Take the E12 value just below: $I_{{C1}} = {A(ic1)}$. '))
    if k > 1:
        icmin = n * st[1]['ic'] / BETA
        t.append(f'Check $I_{{C1}} \\ge N\\frac{{I_{{C2}}}}{{\\beta}} = {A(icmin)}$ '
                 + ('\\checkmark. ' if ic1 >= icmin else '\\textbf{fails}. '))
        assert ic1 >= icmin * (1 - 1e-9), 'I_C1 too small for stage 2'
    while True:
        tt = stage_resistors(s1, 1, ic1, load, av_ce[0], put, given_gain=k > 1)
        ib = ic1 / BETA
        rb1, rb2 = vrb1 / (n * ib), vrb2 / (n * ib)
        put('B1', rb1)
        put('B2', rb2)
        tt.append(f'\\[R_{{B1}} = \\frac{{V_{{RB1}}}}{{N I_{{C1}}/\\beta}} = \\frac{{{num_tex(vrb1)}}}{{{A(n * ib)}}} = '
                  f'\\mathbf{{{Om(rb1)}}},\\qquad R_{{B2}} = \\frac{{V_{{RB2}}}}{{N I_{{C1}}/\\beta}} = '
                  f'\\frac{{{num_tex(vrb2)}}}{{{A(n * ib)}}} = \\mathbf{{{Om(rb2)}}}\\]')
        zb = (BETA + 1) * (s1['r_e'] + s1['reg'])
        ri = 1 / (1 / rb1 + 1 / rb2 + 1 / zb)
        tt.append(f'Check: $R_i = R_{{B1}}\\|R_{{B2}}\\|(\\beta+1)(r_{{e1}} + R_{{E1}}\\|R_{{G1}}) = {Om(rb1)}\\|{Om(rb2)}\\|'
                  f'{Om(zb)} = {eng_tex(ri, chr(92) + "Omega", 4)}$ ')
        if ri >= p.ri or p.ic1:
            tt[-1] += f'$\\ge {Om(p.ri)}$ \\checkmark.' if ri >= p.ri else '.'
            t += tt
            break
        lower = e12_floor(ic1 * 0.999)
        t += tt
        t.append(f'$< {Om(p.ri)}$: the estimate above ignored that $R_{{C1}}$ is loaded by the next stage (and used '
                 f'$\\beta$ for $\\beta+1$). Take the next lower E12 value, $I_{{C1}} = {A(lower)}$, and repeat:')
        ic1 = lower
        s1['ic'] = ic1
    steps.append(('Input stage ($Q_1$)' if k > 1 else 'Bias current and resistors', '\n\n'.join(x for x in t if x)))
    return dict(steps=steps, vals=vals, st=st, fol=fol, av_ce=av_ce, role=role, order=order, icmax=icmax)


def coupled_vrc(kind, nkind, vcc, vre_next):
    """V_RC of a CE stage whose collector drives the base of the next CE stage."""
    vb_next = vre_next + 0.7 if nkind == 'npn' else vcc - vre_next - 0.7
    return vcc - vb_next if kind == 'npn' else vb_next


def vre1_text(s1, st, vcc, vo, av_f, av_ce, k):
    swing = vo / (av_f * math.prod(av_ce[1:]))
    vmax = vcc - s1['vrc'] - VSAT - swing
    s1['vre_max'] = vmax
    assert s1['vre'] <= vmax + 1e-9 and s1['vre'] >= 1
    return (f'Its collector swing is only $\\hat V_o/(\\text{{gain after it}}) = {Vv(swing)}$, so '
            f'$V_{{RE1}} \\le V_{{CC}} - V_{{RC1}} - V_{{CE,sat}} - {num_tex(swing, 3)} = {Vv(vmax)}$; '
            f'with $V_{{RE1}} \\ge 1$\\,V use $V_{{RE1}} = {num_tex(s1["vre"])}$\\,V.')


def stage_resistors(sd, i, ic, load, av, put, given_gain=True):
    """R_C, R_E, R_G of CE stage i. load: AC resistance at its collector besides R_C (inf if none)."""
    vrc, vre = sd['vrc'], sd['vre']
    rc, re_, r_e = vrc / ic, vre / ic, VT / ic
    rcl = rc if math.isinf(load) else par2(rc, load)
    reg = rcl / av - r_e
    assert 0 < reg < re_, f'stage {i}: R_E||R_G = {reg} not in (0, R_E = {re_})'
    rg = 1 / (1 / reg - 1 / re_)
    ri = (BETA + 1) * (r_e + reg)
    sd.update(ic=ic, rc=rc, re=re_, r_e=r_e, rg=rg, reg=reg, ri=ri, rcl=rcl, av=av)
    put(f'C{i}', rc)
    put(f'E{i}', re_)
    put(f'G{i}', rg)
    zc = f'R_{{C{i}}}' if math.isinf(load) else f'R_{{C{i}}}\\|R_{{i{i + 1}}}'
    t = [f'\\[R_{{C{i}}} = \\frac{{V_{{RC{i}}}}}{{I_{{C{i}}}}} = \\frac{{{num_tex(vrc)}}}{{{A(ic)}}} = \\mathbf{{{Om(rc)}}},'
         f'\\quad R_{{E{i}}} = \\frac{{V_{{RE{i}}}}}{{I_{{C{i}}}}} = \\frac{{{num_tex(vre)}}}{{{A(ic)}}} = \\mathbf{{{Om(re_)}}},'
         f'\\quad r_{{e{i}}} = \\frac{{V_T}}{{I_{{C{i}}}}} = {Om(r_e)}\\]',
         f'Gain $|A_{{v{i}}}| = \\frac{{{zc}}}{{r_{{e{i}}} + R_{{E{i}}}\\|R_{{G{i}}}}} = {num_tex(av, 4)}$'
         + ('' if math.isinf(load) else f' with ${zc} = {Om(rcl)}$') + ':'
         f'\\[R_{{E{i}}}\\|R_{{G{i}}} = \\frac{{{zc}}}{{|A_{{v{i}}}|}} - r_{{e{i}}} = {Om(reg)} \\;\\Rightarrow\\; '
         f'R_{{G{i}}} = \\frac{{1}}{{\\frac{{1}}{{{Om(reg)}}} - \\frac{{1}}{{{Om(re_)}}}}} = \\mathbf{{{Om(rg)}}}\\]',
         f'Its input resistance: $R_{{i{i}}} = (\\beta+1)(r_{{e{i}}} + R_{{E{i}}}\\|R_{{G{i}}}) = {Om(ri)}$.' if i > 1 else '']
    return t


# ------------------------------------------------------------------------------------------ verification
def analyse(p, vals):
    """Exact DC (beta = 100) and exact small-signal analysis of the designed amplifier."""
    circ = build(p, vals)
    V, IC = exact_dc(circ)
    view = ACView(circ, IC)
    H = complex(view.exact(circ.out).subs(s, 1j))
    t = build(p, vals, rs=1000.0)
    _, ICt = exact_dc(t)
    g = abs(complex(ACView(t, ICt).exact('b1').subs(s, 1j)))
    ri = 1000.0 * g / (1 - g)
    return circ, V, IC, H, ri


def swing_and_thd(p, d, V, IC, H):
    """Available output swing (no clipping) and the THD estimate of every CE stage, from the exact DC point."""
    role = d['role']
    vals = d['vals']
    k = len(p.ces)
    out = []
    gains_after = []
    g = 1.0
    if p.follower:
        rh = vals[role['H']]
        rhl = par2(rh, p.rl)
        qf = f'Q{k + 1}'
        ref = VT / IC[qf]
        g = rhl / (ref + rhl)
        out.append(('follower', IC[qf] * rhl))      # peak output before the follower cuts off
    for j in range(k - 1, -1, -1):
        gains_after.insert(0, g)
        q = f'Q{j + 1}'
        kind = p.ces[j]
        rc = vals[role[f'C{j + 1}']]
        re_ = vals[role[f'E{j + 1}']]
        rg = vals[role[f'G{j + 1}']]
        r_e = VT / IC[q]
        reg = par2(re_, rg)
        if j == k - 1:
            zl = (BETA + 1) * (VT / IC[f'Q{k + 1}'] + par2(vals[role['H']], p.rl)) if p.follower else (p.rl or math.inf)
        else:
            nq = f'Q{j + 2}'
            zl = (BETA + 1) * (VT / IC[nq] + par2(vals[role[f'E{j + 2}']], vals[role[f'G{j + 2}']]))
        rcl = rc if math.isinf(zl) else par2(rc, zl)
        vce = abs(V[circuit_node(j, 'c')] - V[circuit_node(j, 'e')])
        sat = (vce - VSAT) * g
        cut = IC[q] * rcl * g
        out.append((f'Q{j + 1}', min(sat, cut)))
        avj = 100 / 101 * rcl / (r_e + reg)
        g *= avj
    # THD: HD2 of each CE stage = vb/(4 V_T) (r_e/(r_e + R_E||R_G))^2 with vb its input amplitude
    thd = []
    vo = p.vo
    for j in range(k):
        q = f'Q{j + 1}'
        r_e = VT / IC[q]
        reg = par2(vals[role[f'E{j + 1}']], vals[role[f'G{j + 1}']])
        vb = vo / abs(H) * stage_gain_before(p, d, IC, j)
        thd.append((q, vb, r_e, reg, vb / (4 * VT) * (r_e / (r_e + reg)) ** 2))
    return out, thd


def circuit_node(j, which):
    return f'{which}{j + 1}'


def stage_gain_before(p, d, IC, j):
    """|v_b(Q_{j+1}) / v_i| using the exact currents (input coupled directly to b1)."""
    role, vals = d['role'], d['vals']
    k = len(p.ces)
    g = 1.0
    for i in range(j):
        q = f'Q{i + 1}'
        r_e = VT / IC[q]
        reg = par2(vals[role[f'E{i + 1}']], vals[role[f'G{i + 1}']])
        rc = vals[role[f'C{i + 1}']]
        nq = f'Q{i + 2}'
        zl = (BETA + 1) * (VT / IC[nq] + par2(vals[role[f'E{i + 2}']], vals[role[f'G{i + 2}']]))
        g *= 100 / 101 * par2(rc, zl) / (r_e + reg)
    return g
