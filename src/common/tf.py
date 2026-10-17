"""Rational transfer-function analysis used by every lecture pipeline.

A transfer function is written in the "factored" form

    H(s) = c * s^m / s^k * prod(s + z_i) / prod(s + p_j)

and then rewritten into the "Bode-ready" form used in class

    H(s) = K * prod[s/(s+p)] * prod(1 + s/z) / prod(1 + s/p)

where each s at the origin is paired with one of the lowest poles, so that every
factor except K tends to 1 inside the pass-band.
"""
from dataclasses import dataclass, field
import cmath
import math

import sympy as sp

from .units import num_tex, sig, eng, db

s = sp.Symbol('s')


class ComplexRootError(ValueError):
    pass


def poly_coeffs(expr):
    """Return (num_coeffs, den_coeffs) high->low as exact sympy numbers, monic denominator."""
    expr = sp.cancel(sp.together(expr))
    num, den = sp.fraction(expr)
    pn = sp.Poly(sp.expand(num), s)
    pd = sp.Poly(sp.expand(den), s)
    lead = pd.LC()
    return [c / lead for c in pn.all_coeffs()], [c / lead for c in pd.all_coeffs()]


def _origin_order(coeffs):
    """Number of trailing zero coefficients (= roots at s=0)."""
    m = 0
    for c in reversed(coeffs):
        if c == 0:
            m += 1
        else:
            break
    return m


def _neg_real_roots(coeffs, what):
    """Roots of the polynomial (high->low coeffs) returned as positive numbers r (factor s+r)."""
    if len(coeffs) <= 1:
        return []
    poly = sp.Poly(coeffs, s)
    roots = []
    if poly.degree() <= 2:
        roots = [complex(sp.N(r, 30)) for r in sp.roots(poly, multiple=True)]
    else:
        roots = [complex(r) for r in poly.nroots(n=30, maxsteps=200)]
    out = []
    for r in roots:
        if abs(r.imag) > 1e-6 * max(1.0, abs(r)):  # repeated roots pick up tiny numerical imag parts
            raise ComplexRootError(f'complex {what} {r}')
        if r.real >= 0:
            raise ComplexRootError(f'non-LHP {what} {r}')
        out.append(-r.real)
    return sorted(out)


@dataclass
class Factor:
    kind: str          # 'K', 'hp' (s/(s+p)), 'lp' (1/(1+s/p)), 'zero' (1+s/z), 's', 'inv_s'
    w: float = 0.0     # corner in rad/s
    value: float = 0.0  # for K

    def at(self, w):
        jw = 1j * w
        if self.kind == 'K':
            return complex(self.value)
        if self.kind == 'hp':
            return jw / (jw + self.w)
        if self.kind == 'lp':
            return 1 / (1 + jw / self.w)
        if self.kind == 'zero':
            return 1 + jw / self.w
        if self.kind == 's':
            return jw
        if self.kind == 'inv_s':
            return 1 / jw
        raise ValueError(self.kind)

    def asym_db(self, w):
        """Straight-line (asymptotic) magnitude of this factor in dB."""
        if self.kind == 'K':
            return 20 * math.log10(abs(self.value))
        if self.kind == 'hp':
            return 20 * math.log10(w / self.w) if w < self.w else 0.0
        if self.kind == 'lp':
            return -20 * math.log10(w / self.w) if w > self.w else 0.0
        if self.kind == 'zero':
            return 20 * math.log10(w / self.w) if w > self.w else 0.0
        if self.kind == 's':
            return 20 * math.log10(w)
        if self.kind == 'inv_s':
            return -20 * math.log10(w)

    def asym_rule_tex(self, w):
        """Why this factor has the asymptotic value it has at w (short LaTeX phrase)."""
        if self.kind == 'hp':
            return (r'$f>f_c$: $\approx 1$' if w >= self.w else
                    r'$f<f_c$: $\approx \frac{\omega}{p}$')
        if self.kind == 'lp':
            return (r'$f<f_c$: $\approx 1$' if w <= self.w else
                    r'$f>f_c$: $\approx \frac{p}{\omega}$')
        if self.kind == 'zero':
            return (r'$f<f_c$: $\approx 1$' if w <= self.w else
                    r'$f>f_c$: $\approx \frac{\omega}{z}$')
        return ''

    def mathtext(self):
        """Short label for matplotlib (mathtext has no \\dfrac)."""
        F = f_txt(self.w).replace(' ', r'\ ').replace('µ', r'\mu ') if self.w else ''
        if self.kind == 'K':
            return f'$K={sig(self.value, 3)}$'
        if self.kind == 'hp':
            return r'$\frac{s}{s+2\pi\cdot' + F + '}$'
        if self.kind == 'lp':
            return r'$1/(1+\frac{s}{2\pi\cdot' + F + '})$'
        if self.kind == 'zero':
            return r'$1+\frac{s}{2\pi\cdot' + F + '}$'
        return '$s$' if self.kind == 's' else '$1/s$'

    def angle(self, w):
        """Phase in rad using the class convention (negative K contributes -pi)."""
        if self.kind == 'K':
            return 0.0 if self.value > 0 else -math.pi
        return cmath.phase(self.at(w))

    def cell_tex(self):
        """Factor for a table cell: an invisible strut reserves the height of tall fractions."""
        h = {'lp': r'\rule[-1.7em]{0pt}{4em}', 'hp': r'\rule[-1.1em]{0pt}{2.8em}',
             'zero': r'\rule[-1.1em]{0pt}{2.8em}', 'inv_s': r'\rule[-1.1em]{0pt}{2.8em}'}.get(self.kind, '')
        return '$' + h + self.tex() + '$'

    def tex(self):
        if self.kind == 'K':
            return num_tex(self.value)
        if self.kind == 'hp':
            return r'\dfrac{s}{s+' + w_tex(self.w) + '}'
        if self.kind == 'lp':
            return r'\dfrac{1}{1+\dfrac{s}{' + w_tex(self.w) + '}}'
        if self.kind == 'zero':
            return r'\left(1+\dfrac{s}{' + w_tex(self.w) + r'}\right)'
        if self.kind == 's':
            return 's'
        if self.kind == 'inv_s':
            return r'\dfrac{1}{s}'

    def mag_tex(self, w):
        """|factor(jw)| written out, e.g. w/sqrt(w^2+p^2)."""
        W = num_tex(w)
        if self.kind == 'K':
            return r'\left|' + num_tex(self.value) + r'\right|'
        if self.kind == 'hp':
            return (r'\dfrac{' + W + r'}{\sqrt{' + W + '^2+' + w_tex(self.w, paren=True) + '^2}}')
        if self.kind == 'lp':
            return (r'\dfrac{1}{\sqrt{1+\left(' + W + '/' + w_tex(self.w, paren=True) + r'\right)^2}}')
        if self.kind == 'zero':
            return (r'\sqrt{1+\left(' + W + '/' + w_tex(self.w, paren=True) + r'\right)^2}')
        if self.kind == 's':
            return W
        if self.kind == 'inv_s':
            return r'1/' + W

    def ang_tex(self, w):
        W = num_tex(w)
        if self.kind == 'K':
            return '0' if self.value > 0 else r'-\pi'
        if self.kind == 'hp':
            return r'\dfrac{\pi}{2}-\tan^{-1}\dfrac{' + W + '}{' + w_tex(self.w) + '}'
        if self.kind == 'lp':
            return r'-\tan^{-1}\dfrac{' + W + '}{' + w_tex(self.w) + '}'
        if self.kind == 'zero':
            return r'\tan^{-1}\dfrac{' + W + '}{' + w_tex(self.w) + '}'
        if self.kind == 's':
            return r'\dfrac{\pi}{2}'
        if self.kind == 'inv_s':
            return r'-\dfrac{\pi}{2}'


def f_of(w):
    return w / (2 * math.pi)


def f_txt(w):
    """Corner frequency in Hz, plain text like '271 Hz' or '12.2 kHz'."""
    return eng(f_of(w), 'Hz', space=' ')


def w_tex(w, paren=False):
    """Angular frequency written as 2π·f with f in Hz, e.g. 2\\pi(12.2\\mathrm{k})."""
    f = f_of(w)
    t = eng(f)
    num = t.rstrip('TGMkmµnp')
    pre = t[len(num):]
    pre = {'µ': r'\mu', '': ''}.get(pre, r'\mathrm{' + pre + '}' if pre else '')
    out = r'2\pi\cdot ' + num + pre
    return '(' + out + ')' if paren else out


def poly_tex(coeffs):
    """Polynomial in s (coefficients high->low) as LaTeX."""
    terms = []
    n = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        p = n - i
        c = float(c)
        if c == 0:
            continue
        mag = abs(c)
        if p == 0:
            body = num_tex(mag)
        else:
            sp_ = 's' if p == 1 else f's^{{{p}}}'
            body = sp_ if abs(mag - 1) < 1e-12 else num_tex(mag) + r'\,' + sp_
        sign = '-' if c < 0 else '+'
        terms.append((sign, body))
    if not terms:
        return '0'
    out = ('-' if terms[0][0] == '-' else '') + terms[0][1]
    for sign, body in terms[1:]:
        out += f' {sign} {body}'
    return out


def rational_tex(expr):
    """Simplified rational function of s with a monic denominator, as LaTeX."""
    num, den = poly_coeffs(expr)
    if len(den) == 1:
        return poly_tex(num)
    return r'\dfrac{' + poly_tex(num) + '}{' + poly_tex(den) + '}'


@dataclass
class TF:
    """Analysed transfer function (numbers are floats; exact coefficients kept too)."""
    num: list            # exact coefficients high->low
    den: list            # exact, monic
    c: float = 0.0
    m: int = 0           # zeros at origin
    k: int = 0           # poles at origin
    zeros: list = field(default_factory=list)   # finite zero corners (rad/s, positive)
    poles: list = field(default_factory=list)   # finite pole corners (rad/s, positive)
    factors: list = field(default_factory=list)

    @classmethod
    def from_expr(cls, expr):
        num, den = poly_coeffs(expr)
        # strip leading zeros (can appear after cancellation)
        while len(num) > 1 and num[0] == 0:
            num = num[1:]
        m = _origin_order(num)
        k = _origin_order(den)
        nr = num[:len(num) - m] if m else num
        dr = den[:len(den) - k] if k else den
        c = float(nr[0])
        zeros = _neg_real_roots(nr, 'zero')
        poles = _neg_real_roots(dr, 'pole')
        tf = cls(num=num, den=den, c=c, m=m, k=k, zeros=zeros, poles=poles)
        tf._build_factors()
        return tf

    @classmethod
    def from_bode(cls, K, m, poles, zeros):
        """Build from Bode-ready data: H = K * prod_{lowest m poles} s/(s+p) * prod(1+s/z) / prod(1+s/p).
        poles/zeros in rad/s (repeat a value for a double root)."""
        import numpy as np
        poles, zeros = sorted(poles), sorted(zeros)
        assert m <= len(poles), 'each s must be paired with a pole'
        c = K
        for p in poles[m:]:
            c *= p
        for z in zeros:
            c /= z
        num = np.atleast_1d(np.poly([-z for z in zeros])) * c
        num = list(num) + [0.0] * m
        den = list(np.atleast_1d(np.poly([-p for p in poles])))
        tf = cls(num=num, den=den, c=c, m=m, k=0, zeros=list(zeros), poles=list(poles))
        tf._build_factors()
        return tf

    def _build_factors(self):
        m_left = self.m - self.k
        poles = sorted(self.poles)
        paired = []
        if m_left > 0:
            paired = poles[:m_left]
            poles = poles[m_left:]
            m_left -= len(paired)
        K = self.c
        for z in self.zeros:
            K *= z
        for p in poles:
            K /= p
        f = [Factor('K', value=K)]
        f += [Factor('hp', w=p) for p in paired]
        if m_left > 0:
            f += [Factor('s')] * m_left
        elif m_left < 0:
            f += [Factor('inv_s')] * (-m_left)
        rest = [Factor('zero', w=z) for z in self.zeros] + [Factor('lp', w=p) for p in poles]
        f += sorted(rest, key=lambda x: x.w)   # read left to right in frequency order
        self.factors = f

    @property
    def K(self):
        return self.factors[0].value

    def at(self, w):
        v = 1
        for f in self.factors:
            v *= f.at(w)
        return v

    def angle(self, w):
        a = sum(f.angle(w) for f in self.factors)
        return 0.0 if abs(a) < 1e-12 else a   # symmetric band-pass at its centre: exactly 0

    # ---------- asymptotic Bode magnitude ----------
    def low_gain(self):
        """|H| ~ G0 * w^(m-k) for w below every corner; returns G0."""
        g = abs(self.c)
        for z in self.zeros:
            g *= z
        for p in self.poles:
            g /= p
        return g

    def asym_db(self, w):
        a = db(self.low_gain()) + 20 * (self.m - self.k) * math.log10(w)
        for z in self.zeros:
            if w > z:
                a += 20 * math.log10(w / z)
        for p in self.poles:
            if w > p:
                a -= 20 * math.log10(w / p)
        return a

    def corners(self):
        """Sorted list of (w, +20 or -20)."""
        c = [(z, +20) for z in self.zeros] + [(p, -20) for p in self.poles]
        return sorted(c)

    def segments(self):
        """Piecewise-linear asymptote: list of dicts (w_lo, w_hi, slope dB/dec, db_lo, db_hi)."""
        slope = 20 * (self.m - self.k)
        pts = [w for w, _ in self.corners()]
        segs = []
        lo = None
        for w, d in self.corners():
            segs.append(dict(w_lo=lo, w_hi=w, slope=slope,
                             db_lo=None if lo is None else self.asym_db(lo),
                             db_hi=self.asym_db(w)))
            slope += d
            lo = w
        segs.append(dict(w_lo=lo, w_hi=None, slope=slope,
                         db_lo=None if lo is None else self.asym_db(lo), db_hi=None))
        # coincident corners (double poles/zeros) would leave zero-width segments: drop them
        segs = [g for g in segs if not (g['w_lo'] and g['w_hi'] and abs(g['w_hi'] - g['w_lo']) < 1e-9 * g['w_hi'])]
        for g in segs:  # clean float noise such as -3e-15 dB
            for key in ('db_lo', 'db_hi'):
                if g[key] is not None:
                    g[key] = round(g[key], 9) + 0.0
        return segs

    # ---------- LaTeX helpers ----------
    def poly_tex(self, coeffs):
        return poly_tex(coeffs)

    def rational_tex(self):
        if len(self.den) == 1:
            return self.poly_tex([c / self.den[0] for c in self.num])
        return r'\dfrac{' + self.poly_tex(self.num) + '}{' + self.poly_tex(self.den) + '}'

    def monic_factored_tex(self):
        """c * s^m * prod(s+z) / (s^k prod(s+p))."""
        top = []
        if self.m:
            top.append('s' if self.m == 1 else f's^{{{self.m}}}')
        top += [f'(s+{num_tex(z)})' for z in self.zeros]
        bot = []
        if self.k:
            bot.append('s' if self.k == 1 else f's^{{{self.k}}}')
        bot += [f'(s+{num_tex(p)})' for p in self.poles]
        t = ''.join(top) if top else '1'
        b = ''.join(bot) if bot else '1'
        frac = t if b == '1' else r'\dfrac{' + t + '}{' + b + '}'
        return num_tex(self.c) + r'\,' + frac

    def bode_form_tex(self):
        return r'\,'.join(f.tex() for f in self.factors)

    def corner_table_rows(self):
        rows = []
        for w, d in self.corners():
            kind = 'zero' if d > 0 else 'pole'
            rows.append((kind, num_tex(w), sig(f_of(w), 3), f'{d:+d}'))
        return rows
