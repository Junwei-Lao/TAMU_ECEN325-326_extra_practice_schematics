"""Rectifiers (half-wave, center-tapped full-wave, bridge) with an optional filter capacitor, and the AC-adapter
design procedure of the slides. All formulas follow the lecture (f = 60 Hz, 120 Vrms = 170 V peak mains)."""
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import schemdraw
import schemdraw.elements as elm

from common.units import eng, eng_tex, num_tex, sig
from common import texdoc as T

F = 60.0
MAINS_PK = 170.0
DROP = {'half': 0.7, 'center': 0.7, 'bridge': 1.4}
NAME = {'half': 'half-wave rectifier', 'center': 'center-tapped full-wave rectifier', 'bridge': 'bridge rectifier'}


class RectProb:
    """mode 'analysis': given vs (secondary peak, per half for center-tap) or N, RL, C (None = no filter)
       mode 'find_C': given vs or N, RL and either vr (ripple, V) or vomin (minimum output, V)
       mode 'design': given vo, kr (ripple ratio), il (max load current)."""

    def __init__(self, level, topo, mode, vs=None, N=None, RL=None, C=None, vr=None, vomin=None,
                 vo=None, kr=None, il=None, note=''):
        self.level, self.topo, self.mode = level, topo, mode
        self.vs, self.N, self.RL, self.C, self.vr, self.vomin = vs, N, RL, C, vr, vomin
        self.vo, self.kr, self.il, self.note = vo, kr, il, note


def V(x):
    return eng_tex(x, '\\mathrm{V}')


def A_(x):
    return eng_tex(x, '\\mathrm{A}')


def Ohm(x):
    return eng_tex(x, '\\Omega')


def Fd(x):
    return eng_tex(x, '\\mathrm{F}')


# ------------------------------------------------------------------------------------------ numbers
def compute(p):
    r = {}
    full = p.topo != 'half'
    r['T'] = 1 / (2 * F) if full else 1 / F
    r['drop'] = DROP[p.topo]
    if p.mode == 'design':
        r['RL'] = p.vo / p.il
        r['vp'] = p.vo
        r['vs'] = p.vo + r['drop']
        r['N'] = MAINS_PK / (2 * r['vs']) if p.topo == 'center' else MAINS_PK / r['vs']
        r['C'] = r['T'] / (r['RL'] * p.kr)
        r['vr'] = p.kr * r['vp']
        r['il'] = p.il
    else:
        if p.N is not None:
            r['N'] = p.N
            sec = MAINS_PK / p.N
            r['sec'] = sec
            r['vs'] = sec / 2 if p.topo == 'center' else sec
        else:
            r['vs'] = p.vs
        r['vp'] = r['vs'] - r['drop']
        r['RL'] = p.RL
        r['il'] = r['vp'] / p.RL
        if p.mode == 'find_C':
            r['vr'] = p.vr if p.vr is not None else r['vp'] - p.vomin
            r['C'] = r['vp'] * r['T'] / (p.RL * r['vr'])
        elif p.C is not None:
            r['C'] = p.C
            r['vr'] = r['vp'] * r['T'] / (p.RL * p.C)
    if 'vr' in r:
        q = math.sqrt(2 * r['vp'] / r['vr'])
        r['q'] = q
        r['idav'] = r['il'] * (1 + math.pi * q)
        r['idmax'] = r['il'] * (1 + 2 * math.pi * q)
    filt = 'vr' in r
    if p.topo == 'bridge':
        r['piv'] = r['vs'] - 0.7
    elif p.topo == 'center':
        r['piv'] = 2 * r['vs'] - 0.7
    else:
        r['piv'] = (2 * r['vs'] - 0.7) if filt else r['vs']
    return r


# ------------------------------------------------------------------------------------------ narrative
def statement(p):
    t = NAME[p.topo]
    if p.mode == 'design':
        return design_statement(p)
    tr = (f' fed from the $120\\,\\mathrm{{V_{{rms}}}}$, $60$\\,Hz mains through a transformer with turns ratio '
          f'$N={num_tex(p.N)}:1$' + (' (primary : whole secondary)' if p.topo == 'center' else '')
          if p.N is not None else '')
    src = '' if p.N is not None else (f' driven by a $60$\\,Hz sinusoid of peak $\\hat V_S = {V(p.vs)}$'
                                      + (' on each half of the secondary' if p.topo == 'center' else ''))
    base = f'The {t} below{tr}{src} drives $R_L={Ohm(p.RL)}$'
    if p.mode == 'find_C':
        spec = (f'a peak-to-peak ripple of at most ${V(p.vr)}$' if p.vr is not None else
                f'an output that never drops below ${V(p.vomin)}$')
        return (base + f'. Find the filter capacitance $C$ for {spec}, the diode currents $I_{{D,av}}$, $I_{{D,max}}$ '
                f'and the peak inverse voltage (PIV) of the diodes. Use the constant-voltage-drop model ($0.7$\\,V).')
    if p.C is None:
        return (base + ' (no filter capacitor). Using the constant-voltage-drop model ($0.7$\\,V), find the peak output '
                'voltage and the peak inverse voltage (PIV) of the diodes, and sketch $V_O(t)$.')
    return (base + f' with a filter capacitor $C={Fd(p.C)}$. Using the constant-voltage-drop model ($0.7$\\,V), find '
            f'the peak output $V_p$, the ripple $V_r$, the minimum output, the diode currents $I_{{D,av}}$ and '
            f'$I_{{D,max}}$, and the PIV.')


def design_statement(p):
    what = {'center': 'a center-tapped transformer and a full-wave rectifier',
            'bridge': 'a single transformer and a bridge rectifier',
            'half': 'a transformer and a half-wave rectifier'}[p.topo]
    return (f'Design an AC adapter using {what} (constant-voltage-drop diodes, $0.7$\\,V; mains '
            f'$120\\,\\mathrm{{V_{{rms}}}}$, $60$\\,Hz) for: output voltage $V_o={V(p.vo)}$, maximum ripple '
            f'${num_tex(100 * p.kr)}\\%$, load current $0$--${A_(p.il)}$. Find the transformer ratio $N$, the '
            f'capacitance $C$ and the minimum diode ratings ($I_{{D,max}}$, $I_{{D,av}}$, reverse breakdown voltage).')


def solve(p, figs):
    r = compute(p)
    parts = []
    full = p.topo != 'half'
    k = 1
    paths = {'half': 'the single diode', 'center': 'one diode (each half of the secondary has its own diode)',
             'bridge': 'two diodes in series (one on each side of the bridge)'}
    if p.mode == 'design':
        parts.append(f'\\solstep{{{k}}}{{Worst-case load}}The ripple is largest at the largest current, so design for '
                     f'$I_L = {A_(p.il)}$: the load looks like $R_L = \\frac{{V_o}}{{I_{{L,max}}}} = '
                     f'\\frac{{{num_tex(p.vo)}}}{{{num_tex(p.il)}}} = {Ohm(r["RL"])}$.')
        k += 1
        if p.topo == 'center':
            ntxt = (f'Each half of the secondary must peak at $\\hat V_S = V_o + 0.7 = {V(r["vs"])}$, so the whole '
                    f'secondary peaks at $2\\hat V_S = {V(2 * r["vs"])}$ and '
                    f'$N = \\frac{{170}}{{2(V_o+0.7)}} = \\frac{{170}}{{{num_tex(2 * r["vs"])}}} = {num_tex(r["N"], 4)}$.')
        else:
            ntxt = (f'The current passes through {paths[p.topo]}, so the secondary must peak at '
                    f'$\\hat V_S = V_o + {num_tex(r["drop"])} = {V(r["vs"])}$, and '
                    f'$N = \\frac{{170}}{{\\hat V_S}} = \\frac{{170}}{{{num_tex(r["vs"])}}} = {num_tex(r["N"], 4)}$.')
        parts.append(f'\\solstep{{{k}}}{{Transformer ratio}}The mains peak is $120\\sqrt2 = 170$\\,V. ' + ntxt)
        k += 1
        parts.append(f'\\solstep{{{k}}}{{Filter capacitor}}{"Full-wave: the capacitor is recharged every half period, $T=1/120$\\,s." if full else "Half-wave: the capacitor is recharged once per period, $T=1/60$\\,s."} '
                     f'Ripple $V_r = V_p\\frac{{T}}{{R_LC}}$ and $K_r = \\frac{{V_r}}{{V_p}} = \\frac{{T}}{{R_LC}}$ (tool T4), so'
                     + T.eq(f'C = \\frac{{T}}{{R_L K_r}} = \\frac{{{num_tex(r["T"], 4)}}}{{{num_tex(r["RL"], 4)}'
                            f'\\times {num_tex(p.kr)}}} = {Fd(r["C"])}'))
        k += 1
    else:
        if p.N is not None:
            sec = (f'The mains peak is $120\\sqrt2 = 170$\\,V, so the secondary peaks at $\\frac{{170}}{{N}} = '
                   f'{V(r["sec"])}$' + (f'; each half of the center-tapped secondary gets $\\hat V_S = {V(r["vs"])}$.'
                                       if p.topo == 'center' else f' $=\\hat V_S$.'))
            parts.append(f'\\solstep{{{k}}}{{Secondary voltage}}' + sec)
            k += 1
        parts.append(f'\\solstep{{{k}}}{{Peak output}}At the peak of the input the current flows through '
                     f'{paths[p.topo]}, each dropping $0.7$\\,V (tool T1):'
                     + T.eq(f'V_p = \\hat V_S - {num_tex(r["drop"])} = {num_tex(r["vs"], 4)} - {num_tex(r["drop"])} = '
                            f'{V(r["vp"])},\\qquad I_L \\approx \\frac{{V_p}}{{R_L}} = {A_(r["il"])}'))
        k += 1
        if 'vr' in r:
            per = ('Full-wave: the capacitor is recharged every half period, $T = 1/120$\\,s.' if full else
                   'Half-wave: the capacitor is recharged once per period, $T = 1/60$\\,s.')
            if p.mode == 'find_C':
                need = (f'$V_r = {V(r["vr"])}$' if p.vr is not None else
                        f'$V_r = V_p - V_{{o,min}} = {num_tex(r["vp"], 4)} - {num_tex(p.vomin)} = {V(r["vr"])}$')
                parts.append(f'\\solstep{{{k}}}{{Filter capacitor}}{per} Between recharges the capacitor discharges '
                             f'through $R_L$ and loses $V_r \\approx V_p\\frac{{T}}{{R_LC}}$ (tool T4). We need {need}:'
                             + T.eq(f'C = \\frac{{V_pT}}{{R_LV_r}} = \\frac{{{num_tex(r["vp"], 4)}\\times '
                                    f'{num_tex(r["T"], 4)}}}{{{num_tex(p.RL)}\\times {num_tex(r["vr"], 4)}}} = '
                                    f'{Fd(r["C"])}'))
            else:
                parts.append(f'\\solstep{{{k}}}{{Ripple}}{per} Between recharges the capacitor discharges through '
                             f'$R_L$ (tool T4):'
                             + T.eq(f'V_r \\approx V_p\\frac{{T}}{{R_LC}} = \\frac{{{num_tex(r["vp"], 4)}\\times '
                                    f'{num_tex(r["T"], 4)}}}{{{num_tex(p.RL)}\\times {num_tex(p.C)}}} = {V(r["vr"])}')
                             + f'so the output swings between $V_p = {V(r["vp"])}$ and '
                               f'$V_p - V_r = {V(r["vp"] - r["vr"])}$ (average $\\approx V_p - V_r/2 = '
                               f'{V(r["vp"] - r["vr"] / 2)}$).')
            k += 1
    if 'vr' in r:
        q = r['q']
        parts.append(f'\\solstep{{{k}}}{{Diode currents}}The diodes only conduct during the short recharge interval, '
                     f'so they must deliver a whole period\'s charge in a short burst (tool T4):'
                     + T.align([f'\\sqrt{{2V_p/V_r}} &= \\sqrt{{2\\times{num_tex(r["vp"], 4)}/{num_tex(r["vr"], 4)}}} = '
                                f'{num_tex(q, 4)}',
                                f'I_{{D,av}} &= I_L\\left(1+\\pi\\sqrt{{2V_p/V_r}}\\right) = {num_tex(r["il"], 4)}'
                                f'\\left(1+\\pi\\times{num_tex(q, 4)}\\right) = {A_(r["idav"])}',
                                f'I_{{D,max}} &= I_L\\left(1+2\\pi\\sqrt{{2V_p/V_r}}\\right) = {A_(r["idmax"])}']))
        k += 1
    if p.topo == 'bridge':
        piv = (f'When a pair of diodes conducts, each of the other two sees the output plus one diode drop: '
               f'PIV $= V_p + 0.7 = \\hat V_S - 0.7 = {V(r["piv"])}$.')
    elif p.topo == 'center':
        piv = (f'When one diode conducts its cathode sits at $V_p = \\hat V_S - 0.7$ while its own half of the '
               f'secondary is at $-\\hat V_S$: PIV $= 2\\hat V_S - 0.7 = {V(r["piv"])}$.')
    elif 'vr' in r:
        piv = (f'At the negative peak the anode is at $-\\hat V_S$ while the capacitor holds the cathode near $V_p$: '
               f'PIV $= \\hat V_S + V_p = 2\\hat V_S - 0.7 = {V(r["piv"])}$.')
    else:
        piv = (f'At the negative peak the diode is OFF, the output is 0 and the whole $\\hat V_S$ appears across the '
               f'diode: PIV $= \\hat V_S = {V(r["piv"])}$.')
    parts.append(f'\\solstep{{{k}}}{{Peak inverse voltage}}' + piv + ' The diodes must have a reverse breakdown voltage '
                 'above the PIV.')
    k += 1
    note = (' The ripple formula assumes the capacitor discharges for a whole $T$; in reality it is recharged a '
            'little earlier, so the true ripple (plotted) is slightly smaller --- the formula errs on the safe side.'
            if 'vr' in r else '')
    parts.append(f'\\solstep{{{k}}}{{Waveforms}}' + T.figure(figs['wave'], width=r'0.7\linewidth', height='5.5cm')
                 + note)
    rows = []
    if p.mode == 'design':
        rows += [f'$N = {num_tex(r["N"], 4)}$', f'$C = {Fd(r["C"])}$', f'$R_L = {Ohm(r["RL"])}$']
    else:
        rows += [f'$V_p = {V(r["vp"])}$']
        if 'vr' in r and p.mode != 'find_C':
            rows += [f'$V_r = {V(r["vr"])}$', f'$V_{{o,min}} = {V(r["vp"] - r["vr"])}$']
        if p.mode == 'find_C':
            rows += [f'$C = {Fd(r["C"])}$']
    if 'vr' in r:
        rows += [f'$I_{{D,av}} = {A_(r["idav"])}$', f'$I_{{D,max}} = {A_(r["idmax"])}$']
    rows += [f'PIV $= {V(r["piv"])}$']
    parts.append('\\begin{ansbox}\n' + ',\\quad '.join(rows) + '\n\\end{ansbox}\n')
    return '\n'.join(parts), r


# ------------------------------------------------------------------------------------------ figures
def plot_wave(p, r, base):
    w = 2 * math.pi * F
    t = np.linspace(0, 2.5 / F, 3000)
    vs = r['vs'] * np.sin(w * t)
    if p.topo == 'half':
        src = np.maximum(vs - r['drop'], 0)
    else:
        src = np.maximum(np.abs(vs) - r['drop'], 0)
    if 'C' in r:
        RC = r['RL'] * r['C']
        vo = np.zeros_like(t)
        for k in range(1, len(t)):
            vo[k] = max(src[k], vo[k - 1] * math.exp(-(t[k] - t[k - 1]) / RC))
    else:
        vo = src
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.plot(t * 1e3, vs, color='0.6', ls='--', lw=1.1, label='$V_S(t)$ (one secondary half)' if p.topo == 'center'
            else '$V_S(t)$')
    ax.plot(t * 1e3, vo, color='tab:blue', lw=2.0, label='$V_O(t)$')
    ax.axhline(0, color='0.6', lw=0.7)
    ax.axhline(r['vp'], color='tab:blue', lw=0.6, ls=':')
    ax.annotate(f'$V_p$ = {sig(r["vp"], 3)} V', (t[-1] * 1e3, r['vp']), textcoords='offset points',
                xytext=(-4, 4), ha='right', fontsize=8, color='tab:blue')
    if 'vr' in r:
        ax.axhline(r['vp'] - r['vr'], color='tab:red', lw=0.6, ls=':')
        ax.annotate(f'$V_p-V_r$ = {sig(r["vp"] - r["vr"], 3)} V', (t[-1] * 1e3, r['vp'] - r['vr']),
                    textcoords='offset points', xytext=(-4, -11), ha='right', fontsize=8, color='tab:red')
    ax.set_xlabel('t (ms)')
    ax.set_ylabel('V')
    ax.legend(fontsize=8, loc='lower left')
    ax.grid(True, color='0.92')
    fig.tight_layout()
    fig.savefig(base + '.pdf')
    fig.savefig(base + '.png', dpi=130)
    plt.close(fig)


def draw_rect(p, r, base):
    """Schematic: source (mains + transformer, or V_S directly), rectifier, C, R_L; individual ground symbols."""
    P = schemdraw.util.Point
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=11, unit=2.5)
    has_tr = p.N is not None or p.mode == 'design'
    if has_tr:
        d.add(elm.SourceSin().at((0, -1.0)).up().length(3.6).label('120 V$_{rms}$\n60 Hz', loc='top'))
        tr = elm.Transformer(t1=4, t2=8 if p.topo == 'center' else 4).theta(0).scale(1.4)
        if p.topo == 'center':
            tr = tr.tap(name='ct', pos=4, side='secondary')
        tr = d.add(tr.at((2.0, 2.6)).anchor('p1'))
        d.add(elm.Line().at((0, 2.6)).to(tr.p1))
        d.add(elm.Line().at((0, -1.0)).to((2.0, -1.0)))
        d.add(elm.Line().at((2.0, -1.0)).to(tr.p2))
        lab = 'N : 1' if p.mode == 'design' else f'N = {sig(r["N"], 4)} : 1'
        d.add(elm.Label().at(((tr.p1.x + tr.s1.x) / 2, max(tr.p1.y, tr.s1.y) + 0.6)).label(lab, fontsize=10))
        s1, s2 = tr.s1, tr.s2
        ct = getattr(tr, 'ct', None)
    else:
        if p.topo == 'center':
            d.add(elm.SourceSin().at((1.0, 0.0)).up().length(2.4).label('$V_S$', loc='top'))
            d.add(elm.SourceSin().at((1.0, -2.4)).up().length(2.4).label('$V_S$', loc='top'))
            s1, s2, ct = P((1.0, 2.4)), P((1.0, -2.4)), P((1.0, 0.0))
        else:
            d.add(elm.SourceSin().at((1.0, -1.6)).up().length(3.6).label('$V_S$', loc='top'))
            s1, s2, ct = P((1.0, 2.0)), P((1.0, -1.6)), None
    gnd_y = min(s2.y, -1.0) - 1.2
    if p.topo == 'half':
        d.add(elm.Diode().at(s1).theta(0).length(2.6).label('$D_1$', loc='top'))
        xo, yo = s1.x + 4.2, s1.y
        d.add(elm.Line().at((s1.x + 2.6, yo)).to((xo, yo)))
        d.add(elm.Line().at(s2).to((s2.x + 0.8, s2.y)))
        d.add(elm.Ground().at((s2.x + 0.8, s2.y)))
    elif p.topo == 'center':
        d.add(elm.Diode().at(s1).theta(0).length(2.6).label('$D_1$', loc='top'))
        xo, yo = s1.x + 4.2, s1.y
        d.add(elm.Line().at((s1.x + 2.6, yo)).to((xo, yo)))
        d.add(elm.Diode().at(s2).theta(0).length(2.6).label('$D_2$', loc='bottom'))
        d.add(elm.Line().at((s2.x + 2.6, s2.y)).to((xo, s2.y)))
        d.add(elm.Line().at((xo, s2.y)).to((xo, yo)))
        d.add(elm.Line().at(ct).to((ct.x + 1.0, ct.y)))
        d.add(elm.Ground().at((ct.x + 1.0, ct.y)))
        gnd_y = s2.y - 1.2
    else:  # bridge diamond
        h = 1.9
        cx, cy = s1.x + 4.4, (s1.y + s2.y) / 2
        top, bot, left, right = (cx, cy + h), (cx, cy - h), (cx - h, cy), (cx + h, cy)
        xr = s1.x + 0.7   # route the secondary wires around the diamond, never through it
        d.add(elm.Line().at(s1).to((xr, s1.y)))
        d.add(elm.Line().at((xr, s1.y)).to((xr, top[1] + 0.6)))
        d.add(elm.Line().at((xr, top[1] + 0.6)).to((cx, top[1] + 0.6)))
        d.add(elm.Line().at((cx, top[1] + 0.6)).to(top))
        d.add(elm.Line().at(s2).to((xr, s2.y)))
        d.add(elm.Line().at((xr, s2.y)).to((xr, bot[1] - 0.6)))
        d.add(elm.Line().at((xr, bot[1] - 0.6)).to((cx, bot[1] - 0.6)))
        d.add(elm.Line().at((cx, bot[1] - 0.6)).to(bot))
        d.add(elm.Diode().at(top).to(right).label('$D_1$', loc='top', fontsize=10))
        d.add(elm.Diode().at(bot).to(right).label('$D_2$', loc='bottom', fontsize=10))
        d.add(elm.Diode().at(left).to(top).label('$D_4$', loc='top', fontsize=10))
        d.add(elm.Diode().at(left).to(bot).label('$D_3$', loc='bottom', fontsize=10))
        for pt in (top, bot, left, right):
            d.add(elm.Dot().at(pt))
        d.add(elm.Ground().at(left))
        xo, yo = cx + h + 1.4, cy
        d.add(elm.Line().at(right).to((xo, yo)))
        gnd_y = cy - h - 1.6
    x = xo
    d.add(elm.Dot().at((x, yo)))
    if 'C' in r:
        lab = f'C = {eng(r["C"], "F")}' if p.mode == 'analysis' else 'C = ?'
        d.add(elm.Capacitor().at((x, yo)).down().length(yo - gnd_y).label(lab, loc='bottom'))
        d.add(elm.Ground().at((x, gnd_y)))
        d.add(elm.Line().at((x, yo)).to((x + 2.8, yo)))
        x += 2.8
        d.add(elm.Dot().at((x, yo)))
    rl = f'$R_L$ = {eng(p.RL, "Ω")}' if p.RL else '$R_L$'
    d.add(elm.Resistor().at((x, yo)).down().length(yo - gnd_y).label(rl, loc='bottom'))
    d.add(elm.Ground().at((x, gnd_y)))
    d.add(elm.Line().at((x, yo)).to((x + 1.0, yo)))
    d.add(elm.Dot(open=True).at((x + 1.0, yo)).label('$V_O$', loc='right', color='#1f4e9e'))
    d.save(base + '.pdf')
    d.save(base + '.png', dpi=110)
    plt.close('all')
