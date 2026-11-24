"""MOSFET amplifier design with the procedure of Sample Problem 5.

Topology 'p' (Sample Problem 5): PMOS common-source M1 (gate divider R1/R2, source resistor R3 bypassed to V_DD,
drain resistor R4 to -V_SS) driving an NMOS source follower M2 whose source is the output; M2 is biased by the NMOS
mirror M3/M4 (reference: R5 from ground into the diode-connected M4).
Topology 'n': the mirror image (NMOS common source, PMOS follower and PMOS mirror).
Topology 'p1' / 'n1': the common-source stage alone, output at the drain.

Procedure: I_D3 >= V_o/R_L -> V_ov3, R5; follower gain A_v2 = R_L/(1/g_m2 + R_L); V_d = V_o/A_v2, |A_v1| = |A_v|/A_v2;
headroom: V_R4 >= V_ov3 + V_ov2 + V_t2 + V_d and V_R4 + V_R3 + V_ov1 + V_d <= V_DD + V_SS; |A_v1| = g_m1 R4 = 2V_R4/V_ov1;
then I_D1, R4, R3, and the divider from R1||R2 = R_i."""
import math

from common.units import num_tex, eng_tex
from .mosnet import M, R, C, Col, BJTCircuit, Src, Load
from .ac5 import Stage


def Om(x):
    return eng_tex(x, '\\Omega')


def A(x):
    return eng_tex(x, '\\mathrm{A}')


class AmpSpec5:
    def __init__(self, level, topo, vdd, vss, vo, av, ri, rl=None, thd=None, vr3=0.5, id3=None, k1=1e-3, vt1=1.0,
                 kf=50e-3, vtf=2.0, ratio=1.0, vr4=None, note=''):
        """k1, vt1: M1 (k'W/L, |V_t|); kf, vtf: follower M2 and sink M3 (same device); ratio = k4/k3 of the mirror."""
        self.level, self.topo, self.vdd, self.vss, self.vo, self.av, self.ri = level, topo, vdd, vss, vo, av, ri
        self.rl, self.thd, self.vr3, self.id3, self.k1, self.vt1 = rl, thd, vr3, id3, k1, vt1
        self.kf, self.vtf, self.ratio, self.vr4, self.note = kf, vtf, ratio, vr4, note

    @property
    def single(self):
        return self.topo in ('p1', 'n1')

    @property
    def m1p(self):
        return self.topo in ('p', 'p1')


def build(p, vals=None):
    """The amplifier; vals: {name: ohms} (None: blank drawing)."""
    def r(name):
        return R(name, repr(float(vals[name])) if vals else '1k')

    t1 = 'pmos' if p.m1p else 'nmos'
    tf = 'nmos' if p.m1p else 'pmos'
    m1 = M('M1', t1, gate='g1', kw=p.k1, vt=p.vt1)
    vdd, vss = p.vdd, -p.vss
    rs = (r('R3'), C('C2', 'inf'))
    from lecture1.ladder import Par
    cols = [Col([r('R1'), 'g1', r('R2')], top=vdd, bottom=vss, gap=3.2)]
    if p.m1p:
        cols.append(Col([Par(*rs), 's1', m1, 'd1', r('R4')], top=vdd, bottom=vss))
    else:
        cols.append(Col([r('R4'), 'd1', m1, 's1', Par(*rs)], top=vdd, bottom=vss))
    stages = [Stage(m1, 'CS')]
    out = 'd1'
    if not p.single:
        k4 = p.kf * p.ratio
        m2 = M('M2', tf, gate='d1', kw=p.kf, vt=p.vtf)
        if p.m1p:      # reference first (left), then the follower whose source is the output
            cols.append(Col([r('R5'), 'mb', M('M4', tf, diode=True, kw=k4, vt=p.vtf)], top=0, bottom=vss, gap=4.6))
            cols.append(Col([m2, 'o', M('M3', tf, gate='mb', kw=p.kf, vt=p.vtf)], top=vdd, bottom=vss))
        else:
            cols.append(Col([M('M4', tf, diode=True, kw=k4, vt=p.vtf), 'mb', r('R5')], top=vdd, bottom=0, gap=4.6))
            cols.append(Col([M('M3', tf, gate='mb', kw=p.kf, vt=p.vtf), 'o', m2], top=vdd, bottom=vss))
        stages.append(Stage(m2, 'CD'))
        out = 'o'
    circ = BJTCircuit(cols, src=Src('g1', c=C('C1', 'inf')),
                      load=Load(out, c=C('C3', 'inf'), rl=R('R_L', repr(float(p.rl))) if p.rl else None))
    return circ, stages


def design(p):
    """Returns (steps [(title, latex)], vals, data)."""
    steps = []
    vals = {}
    tot = p.vdd + p.vss
    d = {}
    vo = p.vo
    if not p.single:
        t = []
        imin = vo / p.rl
        id3 = p.id3 or imin
        vov3 = math.sqrt(2 * id3 / p.kf)
        k4 = p.kf * p.ratio
        id4 = id3 * p.ratio
        vov4 = vov3
        vr5 = (p.vss if p.m1p else p.vdd) - p.vtf - vov4
        r5 = vr5 / id4
        vals['R5'] = r5
        t.append(f'The sink $M_3$ must deliver the whole peak load current: $I_{{D3}} \\ge \\frac{{\\hat V_o}}{{R_L}} = '
                 f'\\frac{{{num_tex(vo)}}}{{{Om(p.rl)}}} = {A(imin)}$; use $I_{{D3}} = {A(id3)}$ (given). '
                 f'Then $\\frac{{k_3}}{{2}}V_{{ov3}}^2 = I_{{D3}} \\Rightarrow V_{{ov3}} = \\sqrt{{\\frac{{2\\cdot{A(id3)}}}'
                 f'{{{eng_tex(p.kf, chr(92) + "mathrm{A/V^2}")}}}}} = {num_tex(vov3, 4)}$\\,V.')
        if p.ratio == 1:
            t.append(f'$M_4$ is identical to $M_3$ and has the same $V_{{GS}}$, so $I_{{D4}} = I_{{D3}}$ and '
                     f'$V_{{ov4}} = V_{{ov3}}$.')
        else:
            t.append(f'$M_4$ has the same $V_{{GS}}$ as $M_3$ but $k_4 = {num_tex(p.ratio)}\\,k_3$, so '
                     f'$I_{{D4}} = {num_tex(p.ratio)}\\,I_{{D3}} = {A(id4)}$ (same $V_{{ov}}$).')
        rail = f'{num_tex(p.vss)}' if p.m1p else f'{num_tex(p.vdd)}'
        t.append(f'\\[R_5 = \\frac{{{rail} - |V_{{t}}| - V_{{ov4}}}}{{I_{{D4}}}} = \\frac{{{rail} - {num_tex(p.vtf)} - '
                 f'{num_tex(vov4, 4)}}}{{{A(id4)}}} = \\mathbf{{{Om(r5)}}}\\]')
        id2 = id3
        vov2 = math.sqrt(2 * id2 / p.kf)
        gm2 = p.kf * vov2
        av2 = p.rl / (1 / gm2 + p.rl)
        vd = vo / av2
        av1 = p.av / av2
        t.append(f'The follower $M_2$ carries the same current, $I_{{D2}} = I_{{D3}}$, so $V_{{ov2}} = {num_tex(vov2, 4)}$\\,V, '
                 f'$g_{{m2}} = k_2V_{{ov2}} = {eng_tex(gm2, chr(92) + "mathrm{A/V}")}$, $1/g_{{m2}} = {Om(1 / gm2)}$ and '
                 f'(the sink $M_3$ is a current source, $Z = \\infty$) \\[A_{{v2}} = \\frac{{R_L}}{{1/g_{{m2}} + R_L}} = '
                 f'\\frac{{{Om(p.rl)}}}{{{Om(1 / gm2)} + {Om(p.rl)}}} = {num_tex(av2, 4)}\\]'
                 f'So the drain of $M_1$ must swing $\\hat V_d = \\hat V_o/A_{{v2}} = {num_tex(vd, 4)}$\\,V and '
                 f'$|A_{{v1}}| = |A_v|/A_{{v2}} = {num_tex(av1, 4)}$.')
        steps.append(('Output stage: sink, reference and follower', '\n\n'.join(t)))
        low = vov3 + vov2 + p.vtf + vd
        lowtxt = (f'V_{{R4}} \\ge V_{{ov3}} + V_{{ov2}} + |V_{{t2}}| + \\hat V_d = {num_tex(vov3, 3)} + {num_tex(vov2, 3)} + '
                  f'{num_tex(p.vtf)} + {num_tex(vd, 3)} = {num_tex(low, 4)}\\,\\mathrm{{V}}')
        lowwhy = (f'At the {"lowest" if p.m1p else "highest"} drain voltage of $M_1$ the follower and the sink must both '
                  'stay active (the drain of $M_1$ sits one $|V_{GS2}|$ away from the output, which needs $V_{ov3}$ of '
                  'room above the rail)')
        d.update(id3=id3, vov3=vov3, id4=id4, vov2=vov2, gm2=gm2, av2=av2, r5=r5)
    else:
        vd = vo
        av1 = p.av
        low = vo
        lowtxt = f'V_{{R4}} \\ge \\hat V_o = {num_tex(vo)}\\,\\mathrm{{V}}'
        lowwhy = 'At its extreme the drain cannot pass the supply on the $R_4$ side'
    t = []
    hi = (tot - p.vr3 - vd) / (1 + 2 / av1)
    vr4 = p.vr4 or math.ceil(low / 0.5 - 1e-9) * 0.5
    assert low <= vr4 <= hi + 1e-9, f'no room for V_R4: {low} .. {hi} (chose {vr4})'
    t.append(f'Voltage budget of the $V_{{DD}} + V_{{SS}} = {num_tex(tot)}$\\,V branch through $R_3$, $M_1$, $R_4$. '
             f'{lowwhy}: \\[{lowtxt}\\]'
             f'$M_1$ must stay active at the other extreme: $V_{{R3}} + V_{{ov1}} + \\hat V_d + V_{{R4}} \\le {num_tex(tot)}$, '
             f'and with $V_{{ov1}} = 2V_{{R4}}/|A_{{v1}}|$ (below): \\[V_{{R4}}\\left(1 + \\frac{{2}}{{|A_{{v1}}|}}\\right) '
             f'\\le {num_tex(tot)} - V_{{R3}} - \\hat V_d \\Rightarrow V_{{R4}} \\le {num_tex(hi, 4)}\\,\\mathrm{{V}}\\]'
             f'$V_{{R3}} = {num_tex(p.vr3)}$\\,V (its minimum) and '
             + (f'$V_{{R4}} = {num_tex(vr4)}$\\,V (given).' if p.vr4 else
                f'$V_{{R4}} = {num_tex(vr4)}$\\,V (the next multiple of $0.5$\\,V above the lower bound).'))
    vov1 = 2 * vr4 / av1
    id1 = p.k1 / 2 * vov1 ** 2
    r4, r3 = vr4 / id1, p.vr3 / id1
    vals['R4'], vals['R3'] = r4, r3
    t.append(f'Gain of the common-source stage ($R_3$ is bypassed, the follower\'s gate loads nothing): '
             f'\\[|A_{{v1}}| = g_{{m1}}R_4 = k_1V_{{ov1}}\\frac{{V_{{R4}}}}{{\\frac{{k_1}}{{2}}V_{{ov1}}^2}} = '
             f'\\frac{{2V_{{R4}}}}{{V_{{ov1}}}} \\Rightarrow V_{{ov1}} = \\frac{{2\\cdot{num_tex(vr4)}}}{{{num_tex(av1, 4)}}} = '
             f'{num_tex(vov1, 4)}\\,\\mathrm{{V}}\\]'
             f'$I_{{D1}} = \\frac{{k_1}}{{2}}V_{{ov1}}^2 = {A(id1)}$, '
             f'$R_4 = \\frac{{V_{{R4}}}}{{I_{{D1}}}} = \\mathbf{{{Om(r4)}}}$, $R_3 = \\frac{{V_{{R3}}}}{{I_{{D1}}}} = '
             f'\\mathbf{{{Om(r3)}}}$.')
    vside = p.vr3 + p.vt1 + vov1
    vother = tot - vside
    x = p.ri * tot / (vside * vother)
    rs_, ro_ = ('R1', 'R2') if p.m1p else ('R2', 'R1')
    vals[rs_], vals[ro_] = vside * x, vother * x
    t.append(f'Gate divider: the resistor on the source side of $M_1$ carries $V_{{{rs_}}} = V_{{R3}} + |V_{{t1}}| + V_{{ov1}} = '
             f'{num_tex(vside, 4)}$\\,V, the other one $V_{{{ro_}}} = {num_tex(tot)} - {num_tex(vside, 4)} = '
             f'{num_tex(vother, 4)}$\\,V. Both carry the same current ($I_G = 0$): ${rs_[0]}_{{{rs_[1:]}}} = '
             f'{num_tex(vside, 4)}X$, ${ro_[0]}_{{{ro_[1:]}}} = {num_tex(vother, 4)}X$, and the input resistance is their '
             f'parallel combination: \\[R_1\\|R_2 = \\frac{{{num_tex(vside, 4)}\\cdot{num_tex(vother, 4)}}}{{{num_tex(tot)}}}X '
             f'\\ge {Om(p.ri)} \\Rightarrow X = {Om(x)}:\\quad \\mathbf{{R_1 = {Om(vals["R1"])}}},\\ '
             f'\\mathbf{{R_2 = {Om(vals["R2"])}}}\\]')
    steps.append(('Common-source stage' if not p.single else 'Design of the stage', '\n\n'.join(t)))
    hd2 = (vd / av1) / (4 * vov1)
    d.update(vd=vd, av1=av1, vr4=vr4, low=low, hi=hi, vov1=vov1, id1=id1, hd2=hd2)
    return steps, vals, d
