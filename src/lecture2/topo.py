"""Op-amp circuits that are NOT a single standard block, solved by nodal analysis (Sample Problems 1-4 style).
Each topology behaves like a block (build / draw / H / explain) so it can start a cascade."""
import sympy as sp

from common import texdoc as T
from lecture1.ladder import NamedZ
from .blocks import Block, zname, zdefs, YIN
from .draw2 import OA_H, hwidth, vwidth
from .netlist import Net, solve_exact
from .kcl import kcl_derivation


class Topo(Block):
    roles = ()
    nodal = True
    title = ''

    def __init__(self, **z):
        self.raw = z
        self.load = z.pop('load', None)

    def name(self, k):
        self.k = k
        self.z = {r: zname(self.raw.get(r), f'Z_{{{r}}}') for r in self.roles}

    def named(self):
        return []           # the KCL derivation names elements directly

    def label(self, nin, nout):
        return {}

    def H(self):
        sub = Net()
        self.build(sub, 'i', 'o')
        return solve_exact(sub)['o']

    def H_tex(self):
        return None

    def explain(self, vi, vo):
        sub = Net()
        self.build(sub, 'i', 'o')
        lab = self.label('i', 'o')
        lab['o'] = vo.replace('V_{', '').rstrip('}')
        txt, H = kcl_derivation(sub, lab, 'o')
        assert sp.simplify(H - self.H()) == 0
        defs = zdefs([z for z in self.z.values() if isinstance(z, NamedZ)])
        return (f'{self.title} This is not a standard block, so use nodal analysis. '
                + (('Short names for the composite branches:' + T.align(defs)) if defs else '') + txt)


# ------------------------------------------------------------------------------------------ helpers
def _zg_zf_below(sch, oa, yin, xm, xz1, zg, zf):
    """Draw the - input network below a '+ on top' op-amp: zg to ground, zf (or a wire) to the output."""
    ym = yin - OA_H
    sch.line(oa['minus'], (xm, ym))
    if zg is not None:
        sch.dot((xm, ym))
        sch.line((xm, ym), (xz1, ym))
        sch.vdown(zg, (xz1, ym), 2.2)
    yfb = ym - 1.8
    sch.line((xm, ym), (xm, yfb))
    end = sch.h(zf, (xm, yfb), stack=-1) if zf is not None else (xm, yfb)
    xo = max(oa['out'][0] + 0.7, end[0] + 0.5)
    sch.path(end, (xo, yfb), (xo, ym + OA_H / 2))
    sch.line(oa['out'], (xo, ym + OA_H / 2))
    sch.dot((xo, ym + OA_H / 2))
    return xo


class LadderInv(Topo):
    """Inverting amplifier with an L/T input network: Vi -za- x -zc- (-), zb from x to ground, zf feedback."""
    roles = ('a', 'b', 'c', 'f')
    title = 'Inverting amplifier whose input network has a shunt branch.'

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        net.add(z['a'], nin, f'x{k}').add(z['b'], f'x{k}', '0').add(z['c'], f'x{k}', f'm{k}')
        net.add(z['f'], f'm{k}', nout).opamp(f'U{k}', '0', f'm{k}', nout)

    def label(self, nin, nout):
        return {f'x{self.k}': 'x', f'm{self.k}': '-'}

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        r = self.raw
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        xx = e[0] + 1.0
        sch.line(e, (xx, yin))
        sch.dot((xx, yin))
        sch.node_label((xx, yin), 'V_x', dy=0.45)
        sch.vdown(r['b'], (xx, yin), 2.6)
        xs = xx + vwidth(r['b']) + 1.2
        sch.line((xx, yin), (xs, yin))
        e = sch.h(r['c'], (xs, yin))
        xn = e[0] + 0.6
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xo = max(oa['out'][0] + 0.7, xn + hwidth(r['f']) + 0.5)
        sch.line(oa['out'], (xo, y0))
        yfb = yin + 1.8
        sch.line((xn, yin), (xn, yfb))
        end = sch.h(r['f'], (xn, yfb))
        sch.path(end, (xo, yfb), (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)


class PiBuf(Topo):
    """Passive two-section ladder into a non-inverting amplifier (follower if g/f are absent):
    Vi -a- x -b- y(+), c: x to ground, d: y to ground."""
    roles = ('a', 'b', 'c', 'd', 'g', 'f')
    title = 'A two-section passive ladder drives the $+$ input.'

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        net.add(z['a'], nin, f'x{k}').add(z['c'], f'x{k}', '0').add(z['b'], f'x{k}', f'y{k}')
        net.add(z['d'], f'y{k}', '0')
        if z['g'] is not None:
            net.add(z['g'], f'm{k}', '0').add(z['f'], nout, f'm{k}')
            net.opamp(f'U{k}', f'y{k}', f'm{k}', nout)
        else:
            net.opamp(f'U{k}', f'y{k}', nout, nout)

    def label(self, nin, nout):
        return {f'x{self.k}': 'x', f'y{self.k}': 'y', f'm{self.k}': '-'}

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        r = self.raw
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        xx = e[0] + 1.0
        sch.line(e, (xx, yin))
        sch.dot((xx, yin))
        sch.node_label((xx, yin), 'V_x', dy=0.45)
        sch.vdown(r['c'], (xx, yin), 2.6)
        xs = xx + vwidth(r['c']) + 1.2
        sch.line((xx, yin), (xs, yin))
        e = sch.h(r['b'], (xs, yin))
        xy = e[0] + 1.0
        sch.line(e, (xy, yin))
        sch.dot((xy, yin))
        sch.node_label((xy, yin), 'V_y', dy=0.45)
        sch.vdown(r['d'], (xy, yin), 2.6)
        xz1 = xy + vwidth(r['d']) + 2.9
        has_g = r.get('g') is not None
        xm = xz1 + (2.0 if has_g else 0)
        xoa = xm + 0.6
        sch.line((xy, yin), (xoa, yin))
        oa = sch.opamp(xoa, yin, plus_on_top=True, label=f'U{self.k}')
        xo = _zg_zf_below(sch, oa, yin, xm, xz1, r.get('g'), r.get('f'))
        return (xo, y0)


class SallenKey(Topo):
    """Vi -a- x -b- y(+); c: x to the output (positive feedback), d: y to ground;
    optional e: x to ground and h: Vi node to ground; g/f: non-inverting gain network (follower if absent)."""
    roles = ('a', 'b', 'c', 'd', 'e', 'h', 'g', 'f')
    title = 'Sallen-Key stage: the network feeds back from the output to node $V_x$.'

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        if z['h'] is not None:
            net.add(z['h'], nin, '0')
        net.add(z['a'], nin, f'x{k}').add(z['b'], f'x{k}', f'y{k}').add(z['c'], f'x{k}', nout)
        net.add(z['d'], f'y{k}', '0')
        if z['e'] is not None:
            net.add(z['e'], f'x{k}', '0')
        if z['g'] is not None:
            net.add(z['g'], f'm{k}', '0').add(z['f'], nout, f'm{k}')
            net.opamp(f'U{k}', f'y{k}', f'm{k}', nout)
        else:
            net.opamp(f'U{k}', f'y{k}', nout, nout)

    def label(self, nin, nout):
        return {f'x{self.k}': 'x', f'y{self.k}': 'y', f'm{self.k}': '-'}

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        r = self.raw
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        xs = x0 + 0.4
        if r.get('h') is not None:
            sch.line((xs, yin), (xs + 1.0, yin))
            xs += 1.0
            sch.dot((xs, yin))
            sch.vdown(r['h'], (xs, yin), 2.6)
            xs += vwidth(r['h']) + 1.2
            sch.line((xs - vwidth(r['h']) - 1.2, yin), (xs, yin))
        e = sch.h(r['a'], (xs, yin))
        xx = e[0] + 1.0
        sch.line(e, (xx, yin))
        sch.dot((xx, yin))
        sch.node_label((xx, yin), 'V_x', dx=0.15, dy=-0.5, halign='left')
        xe = xx
        if r.get('e') is not None:
            sch.vdown(r['e'], (xx, yin), 2.6)
            xe = xx + vwidth(r['e']) + 1.2
            sch.line((xx, yin), (xe, yin))
        e = sch.h(r['b'], (xe, yin))
        xy = e[0] + 1.0
        sch.line(e, (xy, yin))
        sch.dot((xy, yin))
        sch.node_label((xy, yin), 'V_y', dy=0.45)
        sch.vdown(r['d'], (xy, yin), 2.6)
        has_g = r.get('g') is not None
        xz1 = xy + vwidth(r['d']) + 2.9
        xm = xz1 + (2.0 if has_g else 0)
        xoa = xm + 0.6
        sch.line((xy, yin), (xoa, yin))
        oa = sch.opamp(xoa, yin, plus_on_top=True, label=f'U{self.k}')
        xo = _zg_zf_below(sch, oa, yin, xm, xz1, r.get('g'), r.get('f'))
        # positive-feedback branch from x over the top to the output
        ytop = yin + 2.0
        sch.line((xx, yin), (xx, ytop))
        end = sch.h(r['c'], (xx, ytop))
        sch.path(end, (xo, ytop), (xo, y0))
        return (xo, y0)


class MFB(Topo):
    """Multiple-feedback (inverting) stage: Vi -a- x; b: x to ground (optional); c: x to the - input;
    d: x to the output; f: - input to the output."""
    roles = ('a', 'b', 'c', 'd', 'f')
    title = 'Multiple-feedback stage: node $V_x$ is fed back from the output through a second branch.'

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        net.add(z['a'], nin, f'x{k}').add(z['c'], f'x{k}', f'm{k}').add(z['d'], f'x{k}', nout)
        if z['b'] is not None:
            net.add(z['b'], f'x{k}', '0')
        net.add(z['f'], f'm{k}', nout).opamp(f'U{k}', '0', f'm{k}', nout)

    def label(self, nin, nout):
        return {f'x{self.k}': 'x', f'm{self.k}': '-'}

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        r = self.raw
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        xx = e[0] + 1.0
        sch.line(e, (xx, yin))
        sch.dot((xx, yin))
        sch.node_label((xx, yin), 'V_x', dx=0.15, dy=-0.5, halign='left')
        xc = xx
        if r.get('b') is not None:
            sch.vdown(r['b'], (xx, yin), 2.6)
            xc = xx + vwidth(r['b']) + 1.2
            sch.line((xx, yin), (xc, yin))
        e = sch.h(r['c'], (xc, yin))
        xn = e[0] + 0.6
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xo = max(oa['out'][0] + 0.7, xn + hwidth(r['f']) + 0.5, xx + hwidth(r['d']) + 0.5)
        sch.line(oa['out'], (xo, y0))
        y1 = yin + 1.8
        sch.line((xn, yin), (xn, y1))
        end = sch.h(r['f'], (xn, y1))
        sch.path(end, (xo, y1))
        y2 = yin + 3.9
        sch.line((xx, yin), (xx, y2))
        end = sch.h(r['d'], (xx, y2))
        sch.path(end, (xo, y2), (xo, y0))
        sch.dot((xo, y1))
        sch.dot((xo, y0))
        return (xo, y0)


class Loop(Topo):
    """Two op-amps in a loop. U1: inverting summer (Vi through a, feedback f1, and the loop return through r);
    U2: non-inverting amplifier of U1's output (g2 to ground, f2 feedback); U2's output is returned through r."""
    roles = ('a', 'f1', 'r', 'g2', 'f2')
    title = ('Two op-amps in a loop: $U_2$ amplifies $V_{o1}$ and feeds it back into the summing node of $U_1$, '
             'so the stages cannot simply be multiplied.')

    def build(self, net, nin, nout):
        k, z = self.k, self.z
        o1 = f'q{k}'
        net.add(z['a'], nin, f'm{k}').add(z['f1'], f'm{k}', o1).add(z['r'], nout, f'm{k}')
        net.opamp(f'U{k}', '0', f'm{k}', o1)
        net.add(z['g2'], f'n{k}', '0').add(z['f2'], nout, f'n{k}')
        net.opamp(f'U{k + 1}', o1, f'n{k}', nout)

    def label(self, nin, nout):
        return {f'm{self.k}': '-', f'q{self.k}': 'o1', f'n{self.k}': 'n'}

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        r = self.raw
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(r['a'], (x0 + 0.4, yin))
        xr = e[0] + 0.8
        xn = xr + 1.2
        sch.line(e, (xn, yin))
        sch.dot((xr, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xo1 = max(oa['out'][0] + 0.7, xn + hwidth(r['f1']) + 0.5)
        sch.line(oa['out'], (xo1, y0))
        yfb = yin + 1.8
        sch.line((xn, yin), (xn, yfb))
        end = sch.h(r['f1'], (xn, yfb))
        sch.path(end, (xo1, yfb), (xo1, y0))
        sch.dot((xo1, y0))
        sch.node_label((xo1, y0), 'V_{o1}', dx=0.15, dy=0.4, halign='left')
        # U2: non-inverting
        xa = xo1 + 1.4
        sch.path((xo1, y0), (xa, y0), (xa, yin))
        xz1 = xa + 1.0
        xm = xz1 + 2.0 + vwidth(r['g2'])
        xoa = xm + 0.6
        sch.line((xa, yin), (xoa, yin))
        oa2 = sch.opamp(xoa, yin, plus_on_top=True, label=f'U{self.k + 1}')
        xo = _zg_zf_below(sch, oa2, yin, xm, xz1, r['g2'], r['f2'])
        # loop return under everything, through r, into the summing node
        ybot = y0 - 5.2
        sch.line((xo, y0), (xo, ybot))
        w = hwidth(r['r'])
        xs = (xr + xo) / 2 - w / 2
        sch.line((xo, ybot), (xs + w, ybot))
        sch.h(r['r'], (xs, ybot))
        sch.path((xs, ybot), (xr, ybot), (xr, yin))
        return (xo, y0)
