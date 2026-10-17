"""Design a cascade of inverting op-amp stages that realizes a Bode-ready H(s) (Sample Problem 5 style).

Stage library (every stage uses R1 = R_IN at its input; gain G = R2/R1):
    'pz' : Zin = R1 || C1, Zf = R2 || C2   -> -G (1+s/z)/(1+s/p)      C1 = 1/(z R1), C2 = 1/(p R2)
    'lp' : Zin = R1,       Zf = R2 || C2   -> -G / (1+s/p)            C2 = 1/(p R2)
    'hp' : Zin = R1 + C1,  Zf = R2         -> -G s/(s+p)              C1 = 1/(p R1)
    'bp' : Zin = R1 + C1,  Zf = R2 || C2   -> -G s/(s+ph) /(1+s/pl)   C1 = 1/(ph R1), C2 = 1/(pl R2)
    'inv': Zin = R1,       Zf = R2 = R1    -> -1
Pairing: zeros with low-pass poles first, then high-pass factors with the remaining low-pass poles,
then whatever is left on its own. All of |K| goes into the first stage. If the number of stages is odd,
a unity-gain inverter is appended so the overall sign is +.
"""
from fractions import Fraction

from common.units import eng
from lecture1.ladder import El, Ser, Par
from .blocks import Inv

R_IN = 10e3


def _val(x):
    """Exact-enough Fraction for a component value (keeps 6 significant digits)."""
    return Fraction(float(f'{x:.6g}'))


def plan(tf):
    hps = [f.w for f in tf.factors if f.kind == 'hp']
    lps = sorted(f.w for f in tf.factors if f.kind == 'lp')
    zs = sorted(f.w for f in tf.factors if f.kind == 'zero')
    stages = []
    for z in zs:
        if not lps:
            raise ValueError('more zeros than low-pass poles: not supported by this stage library')
        # pair each zero with the nearest unused low-pass pole
        p = min(lps, key=lambda w: abs(w - z))
        lps.remove(p)
        stages.append(dict(kind='pz', z=z, p=p))
    for h in hps:
        if lps:
            p = lps.pop(0)
            stages.append(dict(kind='bp', ph=h, pl=p))
        else:
            stages.append(dict(kind='hp', p=h))
    for p in lps:
        stages.append(dict(kind='lp', p=p))
    order = {'bp': 0, 'hp': 1, 'pz': 2, 'lp': 3}
    stages.sort(key=lambda s: order[s['kind']])
    if len(stages) % 2:
        stages.append(dict(kind='inv'))
    return stages


def build(tf):
    """Returns (blocks, rows) where rows describe each stage for the solution table."""
    stages = plan(tf)
    K = abs(tf.K)
    blocks, rows = [], []
    nR = nC = 0

    def R(v):
        nonlocal nR
        nR += 1
        return El('R', f'R{nR}', _val(v))

    def C(v):
        nonlocal nC
        nC += 1
        return El('C', f'C{nC}', _val(v))

    for k, st in enumerate(stages):
        G = K if k == 0 else 1.0
        kind = st['kind']
        r1 = R(R_IN)
        if kind == 'inv':
            r2 = R(R_IN)
            blocks.append(Inv(r1, r2))
            rows.append(dict(kind=kind, G=1.0, parts=[r1, r2], st=st))
            continue
        r2 = R(G * R_IN)
        if kind == 'pz':
            c1, c2 = C(1 / (st['z'] * R_IN)), C(1 / (st['p'] * G * R_IN))
            blocks.append(Inv(Par(r1, c1), Par(r2, c2)))
            parts = [r1, c1, r2, c2]
        elif kind == 'lp':
            c2 = C(1 / (st['p'] * G * R_IN))
            blocks.append(Inv(r1, Par(r2, c2)))
            parts = [r1, r2, c2]
        elif kind == 'hp':
            c1 = C(1 / (st['p'] * R_IN))
            blocks.append(Inv(Ser(r1, c1), r2))
            parts = [r1, c1, r2]
        else:  # bp
            c1, c2 = C(1 / (st['ph'] * R_IN)), C(1 / (st['pl'] * G * R_IN))
            blocks.append(Inv(Ser(r1, c1), Par(r2, c2)))
            parts = [r1, c1, r2, c2]
        rows.append(dict(kind=kind, G=G, parts=parts, st=st))
    return blocks, rows


def parts_txt(parts):
    return ', '.join(f'{p.name} = {eng(p.value, {"R": "Ω", "C": "F"}[p.kind])}' for p in parts)
