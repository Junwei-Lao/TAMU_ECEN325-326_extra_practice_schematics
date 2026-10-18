"""Turn Lecture-1 ladders and Lecture-2 op-amp circuits into PNet (diode netlists), plus the diode/op-amp
topologies of Sample Problems 4-5 and the precision rectifier."""
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from common.units import sig, num_tex
from lecture1.ladder import Circuit, El
from lecture2.blocks import YIN
from lecture2.topo import Topo, _zg_zf_below
from lecture2.draw2 import OA_H, hwidth, vwidth
from .pwl import PNet, X, vo_of, merged


# ------------------------------------------------------------------------------------------ converters
def from_ladder(items, von=0.7):
    """Lecture-1 ladder (single stage) -> (Circuit for drawing, PNet)."""
    circ = Circuit(items)
    st = circ.stages[0]
    pn = PNet(von)
    names = []
    for j, nd in enumerate(st.nodes):
        n = 'i' if j == 0 else (nd.name if nd.name else f'n{j}')
        names.append(n)
        if nd.name and n != 'i':
            pn.label[n] = nd.name
    for j, nd in enumerate(st.nodes):
        if j:
            pn.add(nd.series_in, names[j - 1], names[j])
        for z, rail in nd.shunts:
            if rail is None:
                pn.add(z, names[j], '0')
            else:
                r = f'rail{float(rail):+g}'
                pn.dc(r, rail)
                pn.add(z, names[j], r)
    pn.auto_labels()
    return circ, pn


def from_chain(chain, von=0.7):
    """Lecture-2 Chain (ideal op-amps; diodes may appear inside impedances) -> PNet."""
    net = chain.net()
    pn = PNet(von)
    for z, a, b in net.branches:
        pn.add(z, a, b)
    for o in net.opamps:
        pn.opamp(o.name, o.plus, o.minus, o.out)
    for n, v in net.dcs.items():
        pn.dc(n, v)
    multi = len(net.opamps) > 1
    for n in pn.nodes():
        if n.startswith('m') and n[1:].isdigit():
            pn.label[n] = '-' if not multi else f'-{n[1:]}'
        elif n.startswith('p') and n[1:].isdigit():
            pn.label[n] = '+' if not multi else f'+{n[1:]}'
        elif n.startswith('u') and n[1:].isdigit():
            pn.label[n] = 'u' if not multi else f'u{n[1:]}'
        elif n.startswith('o') and n[1:].isdigit():
            pn.label[n] = n
        elif n == 'o':
            pn.label[n] = 'o'
    pn.auto_labels()
    return pn


# ------------------------------------------------------------------------------------------ topologies
class DiodeOut(Topo):
    """Op-amp whose output drives a diode; the feedback is taken AFTER the diode (Sample Problem 5).
    + input: Vi -a- p, b: p to ground. Output u -D- o. g: - input to ground, f: o to - input, l: o to ground."""
    roles = ('a', 'b', 'g', 'f', 'l', 'd')
    title = ''

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        net.add(z['a'], nin, f'p{k}').add(z['b'], f'p{k}', '0')
        net.add(z['d'], f'u{k}', nout)
        net.add(z['g'], f'm{k}', '0').add(z['f'], nout, f'm{k}').add(z['l'], nout, '0')
        net.opamp(f'U{k}', f'p{k}', f'm{k}', f'u{k}')

    def draw(self, sch, p):
        r = self.raw
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        x = e[0] + 1.0
        sch.line(e, (x, yin))
        sch.dot((x, yin))
        sch.vdown(r['b'], (x, yin), 2.6)
        xz1 = x + 2.9
        xm = xz1 + 2.0
        xoa = xm + 0.6
        sch.line((x, yin), (xoa, yin))
        oa = sch.opamp(xoa, yin, plus_on_top=True, label=f'U{self.k}')
        ym = yin - OA_H
        sch.line(oa['minus'], (xm, ym))
        sch.dot((xm, ym))
        sch.line((xm, ym), (xz1, ym))
        sch.vdown(r['g'], (xz1, ym), 2.2)
        # output -> diode -> node o
        xu = oa['out'][0] + 0.5
        sch.line(oa['out'], (xu, y0))
        sch.node_label((xu, y0), 'V_u', dx=0.0, dy=0.45, halign='center')
        e = sch.h(r['d'], (xu, y0))
        xo = e[0] + 0.8
        sch.line(e, (xo, y0))
        sch.dot((xo, y0))
        yfb = ym - 1.8
        sch.line((xm, ym), (xm, yfb))
        end = sch.h(r['f'], (xm, yfb), stack=-1)
        sch.path(end, (xo, yfb), (xo, y0))
        xl = xo + 1.3
        sch.line((xo, y0), (xl, y0))
        sch.dot((xl, y0))
        sch.vdown(r['l'], (xl, y0), 2.4)
        return (xl, y0)


class PrecisionRect(Topo):
    """Inverting precision half-wave rectifier: Vi -a- (-); d1 from (-) to the op-amp output u (anode at -);
    d2 from u to o (anode at u); f from o back to (-); l: o to ground."""
    roles = ('a', 'd1', 'd2', 'f', 'l')
    title = ''

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        net.add(z['a'], nin, f'm{k}').add(z['d1'], f'm{k}', f'u{k}').add(z['d2'], f'u{k}', nout)
        net.add(z['f'], nout, f'm{k}').add(z['l'], nout, '0')
        net.opamp(f'U{k}', '0', f'm{k}', f'u{k}')

    def draw(self, sch, p):
        r = self.raw
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        xn = e[0] + 0.6
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xu = oa['out'][0] + 0.6
        sch.line(oa['out'], (xu, y0))
        sch.dot((xu, y0))
        sch.node_label((xu, y0), 'V_u', dx=0.15, dy=-0.55, halign='left')
        # D1 from the - node over the op-amp to u (inner loop)
        y1 = yin + 1.8
        sch.line((xn, yin), (xn, y1))
        ed = sch.h(r['d1'], (xn + 0.6, y1))
        sch.line((xn, y1), (xn + 0.6, y1))
        sch.path(ed, (xu, y1), (xu, y0))
        # D2 from u to o, f from o back to the - node (outer loop)
        e2 = sch.h(r['d2'], (xu + 0.4, y0))
        sch.line((xu, y0), (xu + 0.4, y0))
        xo = e2[0] + 0.8
        sch.line(e2, (xo, y0))
        sch.dot((xo, y0))
        y2 = yin + 3.8
        sch.line((xn, y1), (xn, y2))
        ef = sch.h(r['f'], (xn + 0.6, y2))
        sch.line((xn, y2), (xn + 0.6, y2))
        sch.path(ef, (xo, y2), (xo, y0))
        xl = xo + 1.3
        sch.line((xo, y0), (xl, y0))
        sch.dot((xl, y0))
        sch.vdown(r['l'], (xl, y0), 2.4)
        return (xl, y0)


# ------------------------------------------------------------------------------------------ plots
def plot_transfer(good, base, xr=None):
    good = merged(good)
    bps = [float(s['hi']) for s in good[:-1]]
    span = max([abs(b) for b in bps] + [1.0])
    lo, hi = (min(bps + [0]) - 1.6 * span, max(bps + [0]) + 1.6 * span) if xr is None else xr
    xs = np.linspace(lo, hi, 400)
    ys = [vo_of(good, x) for x in xs]
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    ax.axhline(0, color='0.6', lw=0.8)
    ax.axvline(0, color='0.6', lw=0.8)
    ax.plot(xs, ys, color='tab:blue', lw=2.2)
    for b in bps:
        yb = vo_of(good, b)
        ax.plot([b], [yb], 'o', color='tab:red', ms=5)
        ax.plot([b, b], [0, yb], color='tab:red', lw=0.8, ls=':')
        ax.annotate(f'({sig(b, 3)} V, {sig(yb, 3)} V)', (b, yb), textcoords='offset points', xytext=(8, -14),
                    fontsize=8, color='tab:red', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none'))
    for s in good:
        a = float(sp.diff(s['vo'], X))
        l = float(s['lo']) if s['lo'] != -sp.oo else lo
        h = float(s['hi']) if s['hi'] != sp.oo else hi
        xm = (max(l, lo) + min(h, hi)) / 2
        ax.annotate(f'slope {sig(a, 3)}', (xm, vo_of(good, xm)), textcoords='offset points', xytext=(-6, 10),
                    ha='right', fontsize=8, color='tab:blue')
    ax.set_xlabel('$V_i$ (V)')
    ax.set_ylabel('$V_o$ (V)')
    ax.grid(True, color='0.92')
    fig.tight_layout()
    fig.savefig(base + '.pdf')
    fig.savefig(base + '.png', dpi=130)
    plt.close(fig)


def plot_time(good, base, amp, f, fn='sin'):
    t = np.linspace(0, 2 / f, 600)
    vi = amp * (np.sin if fn == 'sin' else np.cos)(2 * math.pi * f * t)
    vo = [vo_of(good, v) for v in vi]
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    ax.plot(t * 1e3, vi, color='0.55', ls='--', lw=1.2, label='$V_i(t)$')
    ax.plot(t * 1e3, vo, color='tab:blue', lw=2.2, label='$V_o(t)$')
    ax.axhline(0, color='0.6', lw=0.8)
    ax.set_xlabel('t (ms)')
    ax.set_ylabel('V')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, color='0.92')
    fig.tight_layout()
    fig.savefig(base + '.pdf')
    fig.savefig(base + '.png', dpi=130)
    plt.close(fig)
