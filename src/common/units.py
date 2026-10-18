"""Value parsing and engineering-notation formatting (plain text and LaTeX)."""
from fractions import Fraction
import math

_PREFIX = {
    'T': Fraction(10) ** 12, 'G': Fraction(10) ** 9, 'M': Fraction(10) ** 6,
    'k': Fraction(10) ** 3, '': Fraction(1), 'm': Fraction(1, 10 ** 3),
    'u': Fraction(1, 10 ** 6), 'µ': Fraction(1, 10 ** 6), 'n': Fraction(1, 10 ** 9),
    'p': Fraction(1, 10 ** 12),
}
_ENG = [(12, 'T'), (9, 'G'), (6, 'M'), (3, 'k'), (0, ''), (-3, 'm'), (-6, 'µ'),
        (-9, 'n'), (-12, 'p')]


def parse(value):
    """'2.2k' -> Fraction(2200), '100n' -> Fraction(1, 10**7). Numbers pass through."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    v = value.strip()
    if v and v[-1] in _PREFIX and v[-1] != '':
        return Fraction(v[:-1]) * _PREFIX[v[-1]]
    return Fraction(v)


def sig(x, n=3):
    """Round x to n significant digits and return a compact string (no exponent)."""
    if x == 0:
        return '0'
    digits = n - 1 - int(math.floor(math.log10(abs(x))))
    r = round(x, digits)
    if digits <= 0:
        return str(int(round(r)))
    s = f'{r:.{digits}f}'
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def eng(x, unit='', n=3, space=''):
    """Engineering notation, plain text: eng(2200, 'Ω') -> '2.2kΩ'."""
    x = float(x)
    if x == 0:
        return f'0{space}{unit}'
    e = int(math.floor(math.log10(abs(x)) / 3) * 3)
    e = max(-12, min(12, e))
    m = x / 10 ** e
    if abs(float(sig(m, n))) >= 1000:  # rounding pushed us to the next prefix
        e += 3
        m = x / 10 ** e
    pre = dict(_ENG)[e]
    return f'{sig(m, n)}{space}{pre}{unit}'


def eng_tex(x, unit='', n=3):
    """Engineering notation for LaTeX math mode: 2200,'\\Omega' -> '2.2\\,\\mathrm{k}\\Omega'."""
    s = eng(x, '', n)
    num = s.rstrip('TGMkmµnp')
    pre = s[len(num):]
    if pre == 'µ':
        pre_tex = r'\mu '
    elif pre:
        pre_tex = r'\mathrm{' + pre + '}'
    else:
        pre_tex = ''
    if not unit and not pre:
        return num
    return num + r'\,' + pre_tex + unit


def num_tex(x, n=3):
    """A plain number for LaTeX: uses a×10^k only when the number is very large/small."""
    x = float(x)
    if x == 0:
        return '0'
    ax = abs(x)
    if 1e-3 <= ax < 1e5:
        return sig(x, n)
    e = int(math.floor(math.log10(ax)))
    m = x / 10 ** e
    ms = sig(m, n)
    if ms in ('10', '-10'):
        e += 1
        ms = sig(x / 10 ** e, n)
    if ms == '1':
        return f'10^{{{e}}}'
    if ms == '-1':
        return f'-10^{{{e}}}'
    return f'{ms}\\times 10^{{{e}}}'


def unit_of(kind):
    return {'R': r'\Omega', 'C': 'F', 'L': 'H', 'D': ''}[kind]


def unit_txt(kind):
    return {'R': 'Ω', 'C': 'F', 'L': 'H', 'D': ''}[kind]


def db(x):
    return 20 * math.log10(abs(x))
