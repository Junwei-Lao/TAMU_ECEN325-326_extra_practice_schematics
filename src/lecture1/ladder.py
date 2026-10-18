"""Ladder-network model for Lecture 1 problems.

A problem circuit is a list of items read left to right:

    Src('V_i')                         AC input source (ideal voltage source to ground)
    Series(z)                          element/composite in the top rail -> new node
    Shunt(z, rail=None)                element/composite from the current node to ground
                                       (rail=None) or to a DC supply rail (rail=+5, -3, ...)
    Tap('x')                           name the current node V_x
    Out('o')                           the output is the current node (V_o)
    VCVS(gain, 'x')                    start a new stage driven by gain*V_x (voltage source)
    VCCS(gm, 'x', 'down'|'up')         start a new stage driven by a current source gm*V_x
                                       ('down' = current flows from the node to ground)

z is an element R('R1','2k'), C('C1','100n'), L('L1','10m') or a composite
Ser(z1, z2, ...) / Par(z1, z2, ...).
"""
from fractions import Fraction

import sympy as sp

from common.units import parse, eng, eng_tex, num_tex, unit_of, unit_txt
from common.tf import s

ZERO = Fraction(0)


def sym(f):
    return sp.Rational(f.numerator, f.denominator)


def name_tex(name):
    """'R12' -> 'R_{12}', 'C1' -> 'C_{1}'."""
    head = name.rstrip('0123456789')
    tail = name[len(head):]
    return f'{head}_{{{tail}}}' if tail else head


# ----------------------------------------------------------------- elements
class El:
    def __init__(self, kind, name, value):
        self.kind, self.name, self.value = kind, name, parse(value)

    @property
    def tex(self):
        return name_tex(self.name)

    def z(self):
        v = sym(self.value)
        return {'R': v, 'C': 1 / (s * v), 'L': s * v}[self.kind]

    def z_tex(self):
        return {'R': self.tex, 'C': r'\frac{1}{s' + self.tex + '}', 'L': 's' + self.tex}[self.kind]

    def dc(self):
        """DC resistance: None = open circuit."""
        return {'R': self.value, 'C': None, 'L': ZERO}[self.kind]

    def elems(self):
        return [self]

    def value_txt(self):
        return eng(self.value, unit_txt(self.kind))

    def value_tex(self):
        return eng_tex(self.value, unit_of(self.kind))

    def is_simple(self):
        return True


def R(name, v):
    return El('R', name, v)


def C(name, v):
    return El('C', name, v)


def L(name, v):
    return El('L', name, v)


class Ser:
    def __init__(self, *parts):
        flat = []
        for p in parts:
            flat += p.parts if isinstance(p, Ser) else [p]
        self.parts = flat

    def z(self):
        return sum((p.z() for p in self.parts), sp.Integer(0))

    def z_tex(self):
        return ' + '.join(r'\left(' + p.z_tex() + r'\right)' if isinstance(p, Par) else p.z_tex()
                          for p in self.parts)

    def dc(self):
        tot = ZERO
        for p in self.parts:
            r = p.dc()
            if r is None:
                return None
            tot += r
        return tot

    def elems(self):
        return [e for p in self.parts for e in p.elems()]

    def is_simple(self):
        return False


class Par:
    def __init__(self, *parts):
        flat = []
        for p in parts:
            flat += p.parts if isinstance(p, Par) else [p]
        self.parts = flat

    def z(self):
        return 1 / sum((1 / p.z() for p in self.parts), sp.Integer(0))

    def z_tex(self):
        return r' \parallel '.join(r'\left(' + p.z_tex() + r'\right)' if isinstance(p, Ser) else p.z_tex()
                                   for p in self.parts)

    def dc(self):
        rs = [p.dc() for p in self.parts]
        rs = [r for r in rs if r is not None]
        if not rs:
            return None
        if any(r == 0 for r in rs):
            return ZERO
        return 1 / sum(1 / r for r in rs)

    def elems(self):
        return [e for p in self.parts for e in p.elems()]

    def is_simple(self):
        return False


class NamedZ:
    """An impedance given a short name (Z_1, R_{12}, ...) inside a derivation."""
    def __init__(self, tex, inner):
        self.tex_name, self.inner = tex, inner

    def z(self):
        return self.inner.z()

    def z_tex(self):
        return self.tex_name

    def dc(self):
        return self.inner.dc()

    def elems(self):
        return self.inner.elems()

    def is_simple(self):
        return True


# ----------------------------------------------------------------- ladder items
class Src:
    def __init__(self, name='V_i'):
        self.name = name


class Series:
    def __init__(self, z):
        self.z = z


class Shunt:
    def __init__(self, z, rail=None):
        self.z = z
        self.rail = None if rail is None else Fraction(rail)


class Tap:
    def __init__(self, label):
        self.label = label


class Out:
    def __init__(self, label='o'):
        self.label = label


class VCVS:
    def __init__(self, gain, ctrl):
        self.gain, self.ctrl = Fraction(str(gain)), ctrl


class VCCS:
    def __init__(self, gm, ctrl, direction='down'):
        self.gm, self.ctrl, self.direction = Fraction(str(gm)), ctrl, direction


# ----------------------------------------------------------------- structure
class Node:
    def __init__(self, series_in=None):
        self.series_in = series_in   # impedance between previous node and this one
        self.shunts = []             # list of (z, rail)
        self.label = None            # e.g. 'x' -> V_x
        self.is_out = False
        self.name = None             # analysis name assigned later ('i', 'x', '1', ...)


class Stage:
    def __init__(self, src):
        self.src = src               # Src | VCVS | VCCS
        self.nodes = [Node()]


class Circuit:
    def __init__(self, items):
        self.items = items
        self.stages = []
        for it in items:
            if isinstance(it, (Src, VCVS, VCCS)):
                self.stages.append(Stage(it))
                continue
            st = self.stages[-1]
            if isinstance(it, Series):
                st.nodes.append(Node(it.z))
            elif isinstance(it, Shunt):
                st.nodes[-1].shunts.append((it.z, it.rail))
            elif isinstance(it, Tap):
                st.nodes[-1].label = it.label
            elif isinstance(it, Out):
                st.nodes[-1].label = it.label
                st.nodes[-1].is_out = True
        self._name_nodes()

    # every node that matters gets a name; plain pass-through nodes are merged away
    def _name_nodes(self):
        k = 1
        for si, st in enumerate(self.stages):
            for ni, nd in enumerate(st.nodes):
                if nd.label:
                    nd.name = nd.label
                elif si == 0 and ni == 0:
                    nd.name = 'i'
                elif ni == 0 or nd.shunts or ni == len(st.nodes) - 1:
                    nd.name = str(k)
                    k += 1

    def elements(self):
        out = []
        for st in self.stages:
            for nd in st.nodes:
                if nd.series_in is not None:
                    out += nd.series_in.elems()
                for z, _ in nd.shunts:
                    out += z.elems()
        return out

    def rails(self):
        return sorted({r for st in self.stages for nd in st.nodes for _, r in nd.shunts
                       if r is not None})

    def has_dc(self):
        return bool(self.rails())

    def out_location(self):
        for si, st in enumerate(self.stages):
            for ni, nd in enumerate(st.nodes):
                if nd.is_out:
                    return si, ni
        raise ValueError('no output')

    def node_of(self, label):
        for si, st in enumerate(self.stages):
            for ni, nd in enumerate(st.nodes):
                if nd.name == label:
                    return si, ni
        raise KeyError(label)


def kept(stage):
    """Analysis view of a stage: list of (node, series_impedance_from_previous_kept_node)."""
    out = []
    pending = []
    for ni, nd in enumerate(stage.nodes):
        if nd.series_in is not None:
            pending.append(nd.series_in)
        if nd.name is not None:
            z = None
            if pending:
                z = pending[0] if len(pending) == 1 else Ser(*pending)
            out.append((nd, z))
            pending = []
    return out


# ----------------------------------------------------------------- AC analysis
def merge_shunts_ac(node):
    """AC shunts of a node (rails are AC ground). Plain resistors in parallel are merged
    into one named resistor (R_{12}) so the derivation stays short."""
    zs = [z for z, _ in node.shunts]
    import re
    def plain_r(z):  # only ordinary resistors R1, R2, ... are merged (r_d of a diode stays visible)
        return isinstance(z, El) and z.kind == 'R' and re.fullmatch(r'R\d+', z.name) is not None
    rs = [z for z in zs if plain_r(z)]
    rest = [z for z in zs if not plain_r(z)]
    merges = []
    if len(rs) >= 2:
        digits = ''.join(r.name.lstrip('R') for r in rs)
        val = 1 / sum(1 / r.value for r in rs)
        m = El('R', 'R' + digits, val)
        merges.append((m, rs))
        rs = [m]
    return rs + rest, merges


class ACStep:
    """One link of the divider chain: V_to / V_from = ratio."""
    def __init__(self, kind, frm, to, **kw):
        self.kind, self.frm, self.to = kind, frm, to
        self.__dict__.update(kw)


def ac_stage_analysis(stage):
    """Returns (steps, merges, zdefs).
    zdefs: list of (NamedZ) definitions in the order they must be computed (right to left).
    steps: divider links left->right inside the stage."""
    nodes = kept(stage)
    merges_all = []
    shunts = []
    for nd, _ in nodes:
        sh, mg = merge_shunts_ac(nd)
        merges_all += mg
        shunts.append(sh)
    n = len(nodes)
    zr = [None] * n          # impedance looking right from node i (NamedZ / El / None)
    zdefs = []
    for i in range(n - 1, -1, -1):
        parts = list(shunts[i])
        if i < n - 1 and zr[i + 1] is not None:
            parts.append(Ser(nodes[i + 1][1], zr[i + 1]))
        if not parts:
            zr[i] = None
        elif len(parts) == 1 and isinstance(parts[0], El):
            zr[i] = parts[0]
        else:
            inner = parts[0] if len(parts) == 1 else Par(*parts)
            nz = NamedZ(f'Z_{{{nodes[i][0].name}}}', inner)
            zr[i] = nz
            zdefs.append(nz)
    steps = []
    for i in range(1, n):
        zs = nodes[i][1]
        if zr[i] is None:
            steps.append(ACStep('open', nodes[i - 1][0], nodes[i][0], zs=zs))
        else:
            steps.append(ACStep('div', nodes[i - 1][0], nodes[i][0], zs=zs, zp=zr[i]))
    return dict(nodes=nodes, zr=zr, zdefs=zdefs, steps=steps, merges=merges_all, shunts=shunts)


def stage_ratio_expr(step):
    if step.kind == 'open':
        return sp.Integer(1)
    return step.zp.z() / (step.zs.z() + step.zp.z())


def ac_chain(circ):
    """Full chain from V_i to V_o across stages. Returns list of links (dicts) and H expr."""
    so, no = circ.out_location()
    links = []
    H = sp.Integer(1)
    analyses = [ac_stage_analysis(st) for st in circ.stages]
    # figure out which node of each stage we need to reach
    targets = {so: circ.stages[so].nodes[no]}
    for si in range(so, 0, -1):
        src = circ.stages[si].src
        csi, cni = circ.node_of(src.ctrl)
        assert csi == si - 1, 'control node must live in the previous stage'
        targets[si - 1] = circ.stages[csi].nodes[cni]
    for si in range(0, so + 1):
        st = circ.stages[si]
        an = analyses[si]
        n0 = an['nodes'][0][0]
        if si > 0:
            src = st.src
            if isinstance(src, VCVS):
                links.append(dict(kind='vcvs', frm=src.ctrl, to=n0.name, gain=src.gain))
                H *= sym(src.gain)
            else:
                sign = -1 if src.direction == 'down' else 1
                z0 = an['zr'][0]
                links.append(dict(kind='vccs', frm=src.ctrl, to=n0.name, gm=src.gm, sign=sign, z=z0))
                H *= sign * sym(src.gm) * z0.z()
        tgt = targets[si]
        if tgt is n0:
            continue
        for step in an['steps']:
            links.append(dict(kind='step', step=step))
            H *= stage_ratio_expr(step)
            if step.to is tgt:
                break
    return links, H, analyses


# ----------------------------------------------------------------- DC analysis
class DCMsg:
    """One line of the DC Thevenin march."""
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)


def _combine(T, branch):
    """T and branch are (V, R) with R possibly 0 (ideal). Returns the new Thevenin pair."""
    if T is None:
        return branch
    (va, ra), (vb, rb) = T, branch
    if ra == 0:
        return T
    if rb == 0:
        return branch
    v = vb + (va - vb) * rb / (ra + rb)
    r = ra * rb / (ra + rb)
    return (v, r)


def shunt_dc(z, rail):
    r = z.dc()
    if r is None:
        return None
    return (Fraction(0) if rail is None else rail, r)


def dc_analysis(circ):
    """Thevenin march on stage 1 (only stage that can carry DC in these problems).
    Returns (Vodc, messages)."""
    so, no = circ.out_location()
    assert so == 0, 'DC analysis supports a single-stage circuit'
    st = circ.stages[0]
    nodes = st.nodes
    o = no
    msgs = []

    def add_shunts(T, nd, side):
        for z, rail in nd.shunts:
            br = shunt_dc(z, rail)
            if br is None:
                msgs.append(DCMsg('open_shunt', node=nd, z=z))
                continue
            newT = _combine(T, br)
            msgs.append(DCMsg('shunt', node=nd, z=z, rail=rail, br=br, before=T, after=newT, side=side))
            T = newT
        return T

    # left side: node 0 is the shorted input source -> ideal 0 V
    T = (Fraction(0), Fraction(0))
    msgs.append(DCMsg('start_left'))
    for i in range(1, o + 1):
        zs = nodes[i].series_in
        r = zs.dc()
        if r is None:
            if T is not None:
                msgs.append(DCMsg('series_open', z=zs, node=nodes[i]))
            T = None
        elif T is not None:
            newT = (T[0], T[1] + r)
            msgs.append(DCMsg('series', z=zs, r=r, before=T, after=newT, node=nodes[i]))
            T = newT
        T = add_shunts(T, nodes[i], 'L') if i < o else T
    TL_before_out = T
    # right side
    TR = None
    if o < len(nodes) - 1:
        msgs.append(DCMsg('start_right'))
        for i in range(len(nodes) - 1, o, -1):
            TR = add_shunts(TR, nodes[i], 'R')
            zs = nodes[i].series_in
            r = zs.dc()
            if r is None:
                if TR is not None:
                    msgs.append(DCMsg('series_open', z=zs, node=nodes[i - 1]))
                TR = None
            elif TR is not None:
                newT = (TR[0], TR[1] + r)
                msgs.append(DCMsg('series', z=zs, r=r, before=TR, after=newT, node=nodes[i - 1]))
                TR = newT
    # output node: own shunts, then right side, then left side
    msgs.append(DCMsg('at_out'))
    T = TL_before_out
    if o == 0:
        T = (Fraction(0), Fraction(0))
    T = add_shunts(T, nodes[o], 'O')
    if TR is not None:
        newT = _combine(T, TR)
        msgs.append(DCMsg('join', left=T, right=TR, after=newT))
        T = newT
    if T is None:
        raise ValueError('output node has no DC path')
    return T[0], msgs


# ----------------------------------------------------------------- netlist (for MNA check)
def netlist(circ, mode):
    """mode 'ac': Vi = 1 V AC, rails grounded.  mode 'dc': Vi = 0, rails active."""
    nl = []
    nid = [0]
    names = {}

    def new():
        nid[0] += 1
        return nid[0]

    rail_nodes = {}

    def rail_node(v):
        if mode == 'ac' or v is None:
            return 0
        if v not in rail_nodes:
            n = new()
            rail_nodes[v] = n
            nl.append(('V', n, 0, float(v)))
        return rail_nodes[v]

    def place(z, a, b):
        if isinstance(z, El):
            nl.append((z.kind, a, b, float(z.value)))
        elif isinstance(z, Ser):
            cur = a
            for k, p in enumerate(z.parts):
                nxt = b if k == len(z.parts) - 1 else new()
                place(p, cur, nxt)
                cur = nxt
        elif isinstance(z, Par):
            for p in z.parts:
                place(p, a, b)
        elif isinstance(z, NamedZ):
            place(z.inner, a, b)

    for si, st in enumerate(circ.stages):
        prev = None
        for ni, nd in enumerate(st.nodes):
            n = new()
            if nd.name:
                names[nd.name] = n
            if ni == 0:
                if isinstance(st.src, Src):
                    nl.append(('V', n, 0, 1.0 if mode == 'ac' else 0.0))
                elif isinstance(st.src, VCVS):
                    nl.append(('E', n, 0, ('ctrl', st.src.ctrl), 0, float(st.src.gain)))
                else:
                    if st.src.direction == 'down':
                        nl.append(('G', n, 0, ('ctrl', st.src.ctrl), 0, float(st.src.gm)))
                    else:
                        nl.append(('G', 0, n, ('ctrl', st.src.ctrl), 0, float(st.src.gm)))
            else:
                place(nd.series_in, prev, n)
            for z, rail in nd.shunts:
                place(z, n, rail_node(rail))
            prev = n
    fixed = []
    for e in nl:
        if e[0] in 'EG':
            e = tuple(names[x[1]] if isinstance(x, tuple) else x for x in e)
        fixed.append(e)
    return fixed, names
