"""Standard single-op-amp blocks. Each block knows how to
  * add itself to a Net (netlist),
  * draw itself (schemdraw) from an input point to an output point,
  * give its ideal transfer function, its DC behaviour, and its non-ideal (finite A) form,
  * explain its derivation in LaTeX using only the op-amp rules + Lecture-1 tools.
"""
import sympy as sp

from common.tf import s, rational_tex
from common.units import num_tex
from lecture1.ladder import El, NamedZ
from .draw2 import OA_H, hwidth, vwidth

YIN = OA_H / 2          # the upper op-amp input sits this far above the signal line


def zname(z, name):
    """Composite impedances get a short name; single elements keep their own symbol."""
    if z is None or isinstance(z, El):
        return z
    return NamedZ(name, z)


def zdefs(zs):
    """LaTeX lines 'Z = structure = rational' for the named (composite) impedances."""
    out = []
    for z in zs:
        if isinstance(z, NamedZ):
            out.append(f'{z.tex_name} &= {z.inner.z_tex()} = {rational_tex(z.z())}')
    return out


def tex_of(z):
    return z.z_tex()


def at0(expr):
    """Value of a rational function of s at s=0 (capacitors open)."""
    return sp.cancel(sp.together(expr)).subs(s, 0)


class Block:
    kind = ''
    load = None

    def named(self):
        return []


class Inv(Block):
    """Inverting amplifier: V_out/V_in = -Zf/Zin."""
    kind = 'inv'

    def __init__(self, zin, zf, load=None, zm=None):
        """zm: optional branch from the - input to ground (irrelevant for an ideal op-amp)."""
        self.zin_raw, self.zf_raw, self.load, self.zm_raw = zin, zf, load, zm

    def name(self, k):
        self.k = k
        self.zin = zname(self.zin_raw, f'Z_{{in{k}}}')
        self.zf = zname(self.zf_raw, f'Z_{{f{k}}}')
        self.zm = zname(self.zm_raw, f'Z_{{m{k}}}')

    def named(self):
        return [z for z in (self.zin, self.zf, self.zm) if z is not None]

    def build(self, net, nin, nout):
        k = self.k
        net.add(self.zin, nin, f'm{k}').add(self.zf, f'm{k}', nout).opamp(f'U{k}', '0', f'm{k}', nout)
        if self.zm is not None:
            net.add(self.zm, f'm{k}', '0')

    def H(self):
        return -self.zf.z() / self.zin.z()

    def H_tex(self):
        return f'-\\frac{{{tex_of(self.zf)}}}{{{tex_of(self.zin)}}}'

    def explain(self, vi, vo):
        return (f'Inverting block: the $+$ input is grounded, so $V_- = V_+ = 0$ (virtual ground). The current '
                f'$\\frac{{{vi} - 0}}{{{tex_of(self.zin)}}}$ through ${tex_of(self.zin)}$ cannot enter the op-amp, so '
                f'all of it flows through ${tex_of(self.zf)}$: ${vo} = 0 - {tex_of(self.zf)}\\cdot'
                f'\\frac{{{vi}}}{{{tex_of(self.zin)}}}$.'
                + (f' (${tex_of(self.zm)}$ from the $-$ input to ground has $0\\,$V across it, so it carries no '
                   f'current and does not matter here.)' if getattr(self, 'zm', None) is not None else ''))

    def ab(self):
        zi, zf = self.zin.z(), self.zf.z()
        if getattr(self, 'zm', None) is None:
            return sp.Integer(0), zf / (zi + zf), zi / (zi + zf)
        zm = self.zm.z()
        fm = zf * zm / (zf + zm)
        im = zi * zm / (zi + zm)
        return sp.Integer(0), fm / (zi + fm), im / (zf + im)

    def ab_tex(self, vi, vo):
        zi, zf = tex_of(self.zin), tex_of(self.zf)
        if getattr(self, 'zm', None) is not None:
            zm = tex_of(self.zm)
            return dict(plus='V_+ = 0 \\quad(\\text{grounded})',
                        minus=(f'V_- = \\frac{{{zf}\\parallel {zm}}}{{{zi}+{zf}\\parallel {zm}}}{vi} + '
                               f'\\frac{{{zi}\\parallel {zm}}}{{{zf}+{zi}\\parallel {zm}}}{vo}'),
                        note=(f'(superposition: with ${vo}=0$, ${zf}$ and ${zm}$ are in parallel from the $-$ '
                              f'input to ground; with ${vi}=0$, ${zi}$ and ${zm}$ are. ${zm}$ matters now, '
                              f'because $V_-$ is no longer forced to 0.)'))
        return dict(plus='V_+ = 0 \\quad(\\text{grounded})',
                    minus=f'V_- = \\frac{{{zf}}}{{{zi}+{zf}}}{vi} + \\frac{{{zi}}}{{{zi}+{zf}}}{vo}',
                    note=f'(superposition: ${vi}$ alone with ${vo}=0$ gives a divider ${zi}$--${zf}$, and vice versa)')

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(self.zin_raw, (x0 + 0.4, yin))
        xn = e[0] + 0.6
        if self.zm_raw is not None:
            xs = e[0] + 1.0
            sch.dot((xs, yin))
            sch.vdown(self.zm_raw, (xs, yin), 2.6)
            xn = xs + vwidth(self.zm_raw) + 1.9
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xo = max(oa['out'][0] + 0.7, xn + hwidth(self.zf_raw) + 0.5)
        sch.line(oa['out'], (xo, y0))
        yfb = yin + 1.8
        sch.line((xn, yin), (xn, yfb))
        end = sch.h(self.zf_raw, (xn, yfb))
        sch.path(end, (xo, yfb), (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)


class NonInv(Block):
    """Non-inverting amplifier with an optional divider (za series, zb shunt) at the + input.
    zg: - input to ground (None = absent), zf: output to - input (None = wire)."""
    kind = 'noninv'

    def __init__(self, zg=None, zf=None, za=None, zb=None, load=None):
        self.zg_raw, self.zf_raw, self.za_raw, self.zb_raw, self.load = zg, zf, za, zb, load

    def name(self, k):
        self.k = k
        self.zg = zname(self.zg_raw, f'Z_{{g{k}}}')
        self.zf = zname(self.zf_raw, f'Z_{{f{k}}}')
        self.za = zname(self.za_raw, f'Z_{{a{k}}}')
        self.zb = zname(self.zb_raw, f'Z_{{b{k}}}')

    def named(self):
        return [z for z in (self.za, self.zb, self.zg, self.zf) if z is not None]

    def build(self, net, nin, nout):
        k = self.k
        p = f'p{k}' if self.za is not None else nin
        if self.za is not None:
            net.add(self.za, nin, p)
        if self.zb is not None:
            net.add(self.zb, p, '0')
        m = f'm{k}'
        if self.zg is not None:
            net.add(self.zg, m, '0')
        if self.zf is not None:
            net.add(self.zf, nout, m)
        else:
            m = nout  # wire from the output to the - input
        net.opamp(f'U{k}', p, m, nout)

    def divider(self):
        if self.zb is None:
            return sp.Integer(1)
        za = self.za.z() if self.za is not None else 0
        return self.zb.z() / (za + self.zb.z())

    def gain(self):
        if self.zg is None or self.zf is None:
            return sp.Integer(1)
        return 1 + self.zf.z() / self.zg.z()

    def H(self):
        return self.divider() * self.gain()

    def H_tex(self):
        d = '' if self.zb is None else \
            f'\\frac{{{tex_of(self.zb)}}}{{{(tex_of(self.za) + " + ") if self.za is not None else ""}{tex_of(self.zb)}}}'
        g = '1' if (self.zg is None or self.zf is None) else \
            f'\\left(1+\\frac{{{tex_of(self.zf)}}}{{{tex_of(self.zg)}}}\\right)'
        if d and g != '1':
            return d + g
        return d or g

    def explain(self, vi, vo):
        if self.zb is not None:
            za = tex_of(self.za) + ' + ' if self.za is not None else ''
            plus = (f'No current flows into the $+$ input, so ${tex_of(self.zb)}$ and '
                    f'{"$" + tex_of(self.za) + "$" if self.za is not None else "the source"} form a plain voltage divider: '
                    f'$V_+ = \\frac{{{tex_of(self.zb)}}}{{{za}{tex_of(self.zb)}}}{vi}$. ')
        elif self.za is not None:
            plus = (f'No current flows into the $+$ input, so there is no drop across ${tex_of(self.za)}$: '
                    f'$V_+ = {vi}$. ')
        else:
            plus = f'The $+$ input is the block input: $V_+ = {vi}$. '
        if self.zg is None or self.zf is None:
            fb = (f'The output is tied back to the $-$ input'
                  f'{" through " + "$" + tex_of(self.zf) + "$, which carries no current" if self.zf is not None else ""}, '
                  f'so ${vo} = V_- = V_+$ (voltage follower).')
        else:
            fb = (f'The op-amp forces $V_-=V_+$, and ${tex_of(self.zg)}$, ${tex_of(self.zf)}$ divide the output: '
                  f'$V_- = \\frac{{{tex_of(self.zg)}}}{{{tex_of(self.zg)} + {tex_of(self.zf)}}}{vo}$, hence '
                  f'${vo} = \\left(1+\\frac{{{tex_of(self.zf)}}}{{{tex_of(self.zg)}}}\\right)V_+$.')
        return 'Non-inverting block: ' + plus + fb

    def ab(self):
        if self.zg is None or self.zf is None:
            beta = sp.Integer(1)
        else:
            beta = self.zg.z() / (self.zg.z() + self.zf.z())
        return self.divider(), sp.Integer(0), beta

    def ab_tex(self, vi, vo):
        if self.zg is None or self.zf is None:
            minus = f'V_- = {vo}'
        else:
            zg, zf = tex_of(self.zg), tex_of(self.zf)
            minus = f'V_- = \\frac{{{zg}}}{{{zg}+{zf}}}{vo}'
        if self.zb is None:
            plus = f'V_+ = {vi}'
        else:
            za = tex_of(self.za) + ' + ' if self.za is not None else ''
            plus = f'V_+ = \\frac{{{tex_of(self.zb)}}}{{{za}{tex_of(self.zb)}}}{vi}'
        return dict(plus=plus, minus=minus, note='(no current enters either input, so both are plain dividers)')

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        x = x0 + 0.4
        if self.za_raw is not None:
            x = sch.h(self.za_raw, (x, yin))[0]
        if self.zb_raw is not None:
            sch.line((x, yin), (x + 1.2, yin))
            x += 1.2
            sch.vdown(self.zb_raw, (x, yin), 2.6)
            sch.dot((x, yin))
            x += vwidth(self.zb_raw)
        xz1 = x + (2.9 if self.zb_raw is not None else 1.0)
        has_g = self.zg_raw is not None
        xm = xz1 + (2.0 + vwidth(self.zg_raw) if has_g else 0)
        xoa = xm + 0.6
        sch.line((x, yin), (xoa, yin))
        oa = sch.opamp(xoa, yin, plus_on_top=True, label=f'U{self.k}')
        ym = yin - OA_H
        sch.line(oa['minus'], (xm, ym))
        if has_g:
            sch.dot((xm, ym))
            sch.line((xm, ym), (xz1, ym))
            sch.vdown(self.zg_raw, (xz1, ym), 2.2)
        yfb = ym - 1.8
        sch.line((xm, ym), (xm, yfb))
        if self.zf_raw is not None:
            end = sch.h(self.zf_raw, (xm, yfb), stack=-1)
        else:
            end = (xm, yfb)
        xo = max(oa['out'][0] + 0.7, end[0] + 0.5)
        sch.path(end, (xo, yfb), (xo, y0))
        sch.line(oa['out'], (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)


class Diff(Block):
    """Difference amplifier driven by the same signal on both sides:
    zin/zf around the - input, za (series) / zb (shunt) at the + input."""
    kind = 'diff'

    def __init__(self, zin, zf, za, zb, load=None):
        self.zin_raw, self.zf_raw, self.za_raw, self.zb_raw, self.load = zin, zf, za, zb, load

    def name(self, k):
        self.k = k
        self.zin = zname(self.zin_raw, f'Z_{{in{k}}}')
        self.zf = zname(self.zf_raw, f'Z_{{f{k}}}')
        self.za = zname(self.za_raw, f'Z_{{a{k}}}')
        self.zb = zname(self.zb_raw, f'Z_{{b{k}}}')

    def named(self):
        return [self.zin, self.zf, self.za, self.zb]

    def build(self, net, nin, nout):
        k = self.k
        net.add(self.zin, nin, f'm{k}').add(self.zf, f'm{k}', nout)
        net.add(self.za, nin, f'p{k}').add(self.zb, f'p{k}', '0')
        net.opamp(f'U{k}', f'p{k}', f'm{k}', nout)

    def d(self):
        return self.zb.z() / (self.za.z() + self.zb.z())

    def H(self):
        return self.d() * (1 + self.zf.z() / self.zin.z()) - self.zf.z() / self.zin.z()

    def H_tex(self):
        za, zb, zi, zf = map(tex_of, (self.za, self.zb, self.zin, self.zf))
        return (f'\\frac{{{zb}}}{{{za}+{zb}}}\\left(1+\\frac{{{zf}}}{{{zi}}}\\right) - \\frac{{{zf}}}{{{zi}}}')

    def explain(self, vi, vo):
        za, zb, zi, zf = map(tex_of, (self.za, self.zb, self.zin, self.zf))
        return (f'Difference block (both inputs driven by ${vi}$): use superposition. Through the $+$ path the '
                f'signal is divided, $V_+ = \\frac{{{zb}}}{{{za}+{zb}}}{vi}$, and amplified by the non-inverting gain '
                f'$1+\\frac{{{zf}}}{{{zi}}}$; through the $-$ path it is amplified by the inverting gain '
                f'$-\\frac{{{zf}}}{{{zi}}}$. Add the two contributions.')

    def ab(self):
        zi, zf = self.zin.z(), self.zf.z()
        return self.d(), zf / (zi + zf), zi / (zi + zf)

    def ab_tex(self, vi, vo):
        za, zb, zi, zf = map(tex_of, (self.za, self.zb, self.zin, self.zf))
        return dict(plus=f'V_+ = \\frac{{{zb}}}{{{za}+{zb}}}{vi}',
                    minus=f'V_- = \\frac{{{zf}}}{{{zi}+{zf}}}{vi} + \\frac{{{zi}}}{{{zi}+{zf}}}{vo}',
                    note='(each input is a divider; the $-$ input sees both sources, use superposition)')

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        ylow = y0 - 2.6
        xs = x0 + 0.4
        sch.path((x0, y0), (xs, y0))
        sch.dot((xs, y0))
        sch.path((xs, y0), (xs, yin))
        e = sch.h(self.zin_raw, (xs, yin))
        sch.path((xs, y0), (xs, ylow))
        e3 = sch.h(self.za_raw, (xs, ylow), stack=-1)
        xb = e3[0] + 1.0
        xn = max(e[0] + 0.6, xb + vwidth(self.zb_raw) + 1.8)
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        sch.line(e3, (xb, ylow))
        sch.dot((xb, ylow))
        sch.vdown(self.zb_raw, (xb, ylow), 1.8)
        px, py = oa['plus']
        sch.path((xb, ylow), (px - 0.4, ylow), (px - 0.4, py), (px, py))
        xo = max(oa['out'][0] + 0.7, xn + hwidth(self.zf_raw) + 0.5)
        sch.line(oa['out'], (xo, y0))
        yfb = yin + 1.8
        sch.line((xn, yin), (xn, yfb))
        end = sch.h(self.zf_raw, (xn, yfb))
        sch.path(end, (xo, yfb), (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)


class Sum(Inv):
    """Inverting summer: the block input through zin and a DC supply vdc through zd."""
    kind = 'sum'

    def __init__(self, zin, zd, zf, vdc, load=None):
        super().__init__(zin, zf, load)
        self.zd_raw, self.vdc = zd, vdc

    def name(self, k):
        super().name(k)
        self.zd = zname(self.zd_raw, f'Z_{{d{k}}}')

    def named(self):
        return [self.zin, self.zd, self.zf]

    def build(self, net, nin, nout):
        super().build(net, nin, nout)
        net.add(self.zd, f'd{self.k}', f'm{self.k}')
        net.dc(f'd{self.k}', self.vdc)

    def explain(self, vi, vo):
        zi, zd, zf = tex_of(self.zin), tex_of(self.zd), tex_of(self.zf)
        return (f'Summing block: $V_-=V_+=0$ (virtual ground), so the input currents '
                f'$\\frac{{{vi}}}{{{zi}}}$ and $\\frac{{V_{{DC}}}}{{{zd}}}$ simply add and both flow through ${zf}$: '
                f'${vo} = -{zf}\\left(\\frac{{{vi}}}{{{zi}}} + \\frac{{V_{{DC}}}}{{{zd}}}\\right)$. For the AC part the '
                f'supply is zero, so ${zd}$ (from virtual ground to AC ground) carries no AC current and drops out.')

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(self.zin_raw, (x0 + 0.4, yin))
        xd = e[0] + 1.0
        sch.line(e, (xd, yin))
        sch.dot((xd, yin))
        top = sch.v(self.zd_raw, (xd, yin), 2.2, +1)
        sch.rail(top, self.vdc)
        xn = xd + 1.9
        sch.line((xd, yin), (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        xo = max(oa['out'][0] + 0.7, xn + hwidth(self.zf_raw) + 0.5)
        sch.line(oa['out'], (xo, y0))
        yfb = yin + 1.8
        sch.line((xn, yin), (xn, yfb))
        end = sch.h(self.zf_raw, (xn, yfb))
        sch.path(end, (xo, yfb), (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)


class InvT(Block):
    """Inverting amplifier with a T-network feedback: za (from - input to T), zb (T to output),
    zc (T to ground)."""
    kind = 'invT'

    def __init__(self, zin, za, zb, zc, load=None):
        self.zin_raw, self.za_raw, self.zb_raw, self.zc_raw, self.load = zin, za, zb, zc, load

    def name(self, k):
        self.k = k
        self.zin = zname(self.zin_raw, f'Z_{{in{k}}}')
        self.za = zname(self.za_raw, f'Z_{{a{k}}}')
        self.zb = zname(self.zb_raw, f'Z_{{b{k}}}')
        self.zc = zname(self.zc_raw, f'Z_{{c{k}}}')

    def named(self):
        return [self.zin, self.za, self.zb, self.zc]

    def build(self, net, nin, nout):
        k = self.k
        net.add(self.zin, nin, f'm{k}').add(self.za, f'm{k}', f't{k}')
        net.add(self.zb, f't{k}', nout).add(self.zc, f't{k}', '0')
        net.opamp(f'U{k}', '0', f'm{k}', nout)

    def H(self):
        za, zb, zc = self.za.z(), self.zb.z(), self.zc.z()
        return -(za + zb + za * zb / zc) / self.zin.z()

    def H_tex(self):
        za, zb, zc, zi = map(tex_of, (self.za, self.zb, self.zc, self.zin))
        return f'-\\frac{{{za} + {zb} + \\frac{{{za}\\,{zb}}}{{{zc}}}}}{{{zi}}}'

    def explain(self, vi, vo):
        za, zb, zc, zi = map(tex_of, (self.za, self.zb, self.zc, self.zin))
        return (f'T-network block. Virtual ground: $V_-=0$, so $I = \\frac{{{vi}}}{{{zi}}}$ flows through ${zi}$ and '
                f'(no current into the op-amp) on through ${za}$. The T node is at $V_T = 0 - {za}I$. '
                f'${zc}$ takes $\\frac{{V_T}}{{{zc}}}$ to ground, so KCL at the T node leaves '
                f'$I_b = I - \\frac{{V_T}}{{{zc}}} = I\\left(1+\\frac{{{za}}}{{{zc}}}\\right)$ for ${zb}$. Then '
                f'${vo} = V_T - {zb}I_b = -\\left({za}+{zb}+\\frac{{{za}{zb}}}{{{zc}}}\\right)I$.')

    def draw(self, sch, p):
        x0, y0 = p
        yin = y0 + YIN
        sch.path((x0, y0), (x0 + 0.4, y0), (x0 + 0.4, yin))
        e = sch.h(self.zin_raw, (x0 + 0.4, yin))
        xn = e[0] + 0.6
        sch.line(e, (xn, yin))
        sch.dot((xn, yin))
        oa = sch.opamp(xn + 0.8, yin, label=f'U{self.k}')
        sch.line((xn, yin), oa['minus'])
        px, py = oa['plus']
        sch.path((px, py), (px - 0.4, py), (px - 0.4, py - 0.7))
        sch.ground((px - 0.4, py - 0.7))
        yfb = yin + 4.6
        sch.line((xn, yin), (xn, yfb))
        ea = sch.h(self.za_raw, (xn, yfb))
        xt = ea[0] + 1.5
        sch.line(ea, (xt, yfb))
        sch.dot((xt, yfb))
        sch.vdown(self.zc_raw, (xt, yfb), 2.4)
        eb = sch.h(self.zb_raw, (xt + vwidth(self.zc_raw) + 0.6, yfb))
        sch.line((xt, yfb), (xt + vwidth(self.zc_raw) + 0.6, yfb))
        xo = max(oa['out'][0] + 0.7, eb[0] + 0.5)
        sch.path(eb, (xo, yfb), (xo, y0))
        sch.line(oa['out'], (xo, y0))
        sch.dot((xo, y0))
        return (xo, y0)
