"""Thevenin equivalents of resistor/capacitor ladders hanging on a transistor terminal (set 5F).

A Ladder is read from the transistor terminal outward:
    Ladder('s1', [Node('s1', [Sh(R('R4','2k'), -5)]), Ser(R('R5','1k')), Node('x1', [Sh(R('R6','3k'), 5), Sh(R('R7','6k'), 0)])])
Node(name, shunts): a junction; every shunt Sh(z, src) connects it through z to a source: a supply voltage, 0 (ground)
or 'vi' (the AC input). Ser(z): a series element towards the next junction.
The march starts at the far end and keeps a Thevenin pair (V_th, Z_th) for everything already visited:
parallel branches combine by Millman's rule, a series element adds to Z_th. DC: supplies at their values, v_i = 0,
capacitors open. AC: supplies are ground, v_i = 1, 'infinite' capacitors are shorts."""
import sympy as sp

from common.units import num_tex, eng_tex
from common.tf import s, rational_tex
from lecture4.bjtnet import Col


class Sh:
    def __init__(self, z, src):
        self.z, self.src = z, src


class Node:
    def __init__(self, name, shunts):
        self.name, self.shunts = name, shunts


class Ser:
    def __init__(self, z):
        self.z = z


class Ladder:
    def __init__(self, terminal, items):
        self.terminal, self.items = terminal, items

    def nodes(self):
        return [it for it in self.items if isinstance(it, Node)]

    def internal(self):
        return [n.name for n in self.nodes() if n.name != self.terminal]


def is_cap(z):
    return getattr(z, 'kind', None) == 'C'


def zval(z, mode):
    """Impedance of element z: None = open, 0 = short."""
    if mode == 'dc':
        if is_cap(z):
            return None
        return sp.Float(float(z.value))
    if is_cap(z) and getattr(z, 'inf', False):
        return sp.Integer(0)
    return z.z()


def src_val(src, mode):
    if src == 'vi':
        return sp.Integer(1) if mode == 'ac' else sp.Integer(0)
    return sp.Float(float(src)) if mode == 'dc' else sp.Integer(0)


def src_tex(src, mode):
    if src == 'vi':
        return 'v_i' if mode == 'ac' else '0'
    if mode == 'ac':
        return '0'
    return f'{src:g}' if src >= 0 else f'({src:g})'


def ztex_val(z, mode):
    if mode == 'dc':
        return eng_tex(float(z), '\\Omega')
    return rational_tex(sp.nsimplify(z, rational=True)) if z.has(s) else eng_tex(float(z), '\\Omega')


def vtex_val(v, mode):
    if mode == 'dc':
        return num_tex(float(v), 4) + '\\,\\mathrm{V}'
    v = sp.cancel(sp.together(v))
    if v == 0:
        return '0'
    return rational_tex(v) + '\\,v_i'


def march(lad, mode, disp):
    """Returns (V_th, Z_th, steps). V_th is in volts (DC) or as a multiple of v_i (AC)."""
    steps = []
    state = None        # (V, Z, description of what it contains)
    for it in reversed(lad.items):
        if isinstance(it, Ser):
            if state is None:
                continue
            zv = zval(it.z, mode)
            if zv is None:
                steps.append(f'${it.z.tex}$ is open at DC: nothing beyond it matters.')
                state = None
                continue
            V, Z = state
            state = (V, Z + zv)
            if zv != 0:
                steps.append(f'Through ${it.z.tex}$ in series: $Z_{{th}}$ grows by ${it.z.z_tex() if mode == "ac" else it.z.tex}$: '
                             f'$(V_{{th}}, Z_{{th}}) = ({vtex_val(state[0], mode)},\\ {ztex_val(sp.cancel(state[1]), mode)})$.'
                             .replace('Z_{th}', 'R_{th}' if mode == 'dc' else 'Z_{th}'))
            else:
                steps.append(f'${it.z.tex}$ is a short ($\\infty$ capacitor): the pair is unchanged.')
            continue
        # a junction: combine the pair arriving from the far side with the shunts of this node
        branches = []
        names = []
        if state is not None:
            branches.append(state)
            names.append('the part already reduced')
        for sh in it.shunts:
            zv = zval(sh.z, mode)
            if zv is None:
                continue
            branches.append((src_val(sh.src, mode), zv))
            names.append(f'${sh.z.tex}$ to ${src_tex(sh.src, mode)}$')
        if not branches:
            state = None
            continue
        shorts = [b for b in branches if b[1] == 0]
        if shorts:
            state = (shorts[0][0], sp.Integer(0))
            steps.append(f'At ${disp(it.name)}$ a short to ${vtex_val(shorts[0][0], mode)}$ fixes the node: '
                         f'$(V_{{th}}, Z_{{th}}) = ({vtex_val(shorts[0][0], mode)}, 0)$.')
            continue
        g = sum(1 / z for _, z in branches)
        V = sp.cancel(sp.together(sum(v / z for v, z in branches) / g))
        Z = sp.cancel(sp.together(1 / g))
        if len(branches) == 1:
            state = (V, Z)
            steps.append(f'Start at ${disp(it.name)}$: only {names[0]}, i.e. $(V_{{th}}, R_{{th}}) = '
                         f'({vtex_val(V, mode)},\\ {ztex_val(Z, mode)})$.'.replace('R_{th}', 'R_{th}' if mode == 'dc' else 'Z_{th}'))
        else:
            sym = 'R' if mode == 'dc' else 'Z'
            steps.append(f'At ${disp(it.name)}$ combine in parallel ' + ', '.join(names)
                         + f' (Millman): \\[V_{{th}} = \\frac{{\\sum V_k/{sym}_k}}{{\\sum 1/{sym}_k}} = {vtex_val(V, mode)},'
                           f'\\qquad {sym}_{{th}} = {" \\| ".join(ztex_val(z, mode) for _, z in branches)} = '
                           f'{ztex_val(Z, mode)}\\]')
            state = (V, Z)
    if state is None:
        return None, None, steps
    return state[0], state[1], steps


def columns(lad, side=1, pair=True):
    """Columns (and series links) that draw the ladder. Each node gets its shunts; a node with one shunt up (to a
    positive supply) and one down (ground / negative supply) is drawn as one divider column."""
    cols, links, src = [], [], None
    prev = lad.terminal
    pending = None
    for it in lad.items:
        if isinstance(it, Ser):
            pending = it.z
            continue
        if pending is not None and prev is not None:
            links.append((pending, prev, it.name))
            pending = None
        ups = [sh for sh in it.shunts if sh.src != 'vi' and sh.src > 0]
        dns = [sh for sh in it.shunts if sh.src != 'vi' and sh.src <= 0]
        vis = [sh for sh in it.shunts if sh.src == 'vi']
        if pair and ups and dns:
            u, d = ups.pop(0), dns.pop(0)
            cols.append(Col([u.z, it.name, d.z], top=u.src, bottom=d.src, gap=3.2))
        for u in ups:
            cols.append(Col([u.z, it.name], top=u.src, bottom=None, gap=3.2))
        for d in dns:
            cols.append(Col([d.z], top_node=it.name, bottom=d.src, gap=3.2))
        for v in vis:
            src = (it.name, v.z)
        prev = it.name
    return cols, links, src
