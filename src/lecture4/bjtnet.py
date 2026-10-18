"""Column-stack description of BJT circuits: one source for the netlist (DC + AC) and the schematic.

A circuit is a list of columns drawn left to right. Each column is a vertical stack between a top rail
(or a node of another column) and a bottom rail/ground:

    Col([R('R1','5k'), 'b1', R('R2','15k')], top=5, bottom=-5)                  # a base divider
    Col([R('R3','2k'), 'e1', Q('Q1','pnp', base='b1'), 'c1', R('R4','1k')], top=5, bottom=-5)

Strings between items name the node there. A Q item is a transistor whose collector/emitter take the nodes
above/below it (npn: collector above; pnp: emitter above). `base` names the node driving the base, optionally
through a series element (base=('c1', C('C2','inf'))). A node name used in two columns joins them.
Other pieces: Src (AC input with optional R_S and coupling C), Load (output through a coupling C into R_L).
"""
import schemdraw
import schemdraw.elements as elm
import matplotlib.pyplot as plt

from common.units import eng, parse
from lecture1.ladder import El, Ser, Par, NamedZ, name_tex
from lecture1.draw import hwidth, vwidth, vweight, _mtext
from lecture2.draw2 import Sch

QH = 1.3933            # schemdraw BJT collector-emitter height
RH = 2.4               # height of one vertical element
BLUE = '#1f4e9e'


def R(name, v):
    return El('R', name, v)


def C(name, v):
    """Capacitor; v='inf' means 'large enough to be a short circuit at signal frequencies'."""
    if v == 'inf':
        e = El('C', name, '1')
        e.inf = True
        return e
    return El('C', name, v)


class Q:
    def __init__(self, name, kind='npn', base=None, beta=100, diode=False, face='left'):
        self.name, self.kind, self.beta, self.diode, self.face = name, kind, beta, diode, face
        if isinstance(base, tuple):
            self.base, self.base_series = base
        else:
            self.base, self.base_series = base, None
        self.c = self.e = self.b = None

    @property
    def s(self):
        return 1 if self.kind == 'npn' else -1

    @property
    def tex(self):
        return name_tex(self.name)


class Col:
    def __init__(self, stack, top=None, bottom=0, top_node=None, gap=4.2, label_nodes=()):
        self.stack, self.top, self.bottom, self.top_node, self.gap = stack, top, bottom, top_node, gap
        self.label_nodes = label_nodes


class Src:
    """AC input V_i at the left, through optional rs and coupling cap c into node `node`."""
    def __init__(self, node, rs=None, c=None, name='V_i'):
        self.node, self.rs, self.c, self.name = node, rs, c, name


class Load:
    """Output: node -> (coupling c) -> V_o terminal, with R_L from V_o to ground (rl may be None)."""
    def __init__(self, node, c=None, rl=None):
        self.node, self.c, self.rl = node, c, rl


class BJTCircuit:
    def __init__(self, cols, src=None, load=None, vt=0.025, links=()):
        self.cols, self.src, self.load, self.vt, self.links = cols, src, load, vt, list(links)
        self.branches = []    # (z, a, b)  z may be composite
        self.bjts = []
        self.fixed = {'0': 0.0}
        self.label = {}
        self._k = 0
        self._build()

    # ------------------------------------------------------------------ netlist
    def _rail(self, v):
        if v is None:
            return None
        if v == 0:
            return '0'
        n = f'rail{v:+g}'
        self.fixed[n] = float(v)
        return n

    def _auto(self):
        self._k += 1
        return f'n{self._k}'

    def _build(self):
        self.col_nodes = []
        for col in self.cols:
            top = col.top_node if col.top_node else self._rail(col.top)
            # assign names: explicit strings follow the item they come after
            seq = [top]
            k = 0
            for it in col.stack:
                if isinstance(it, str):
                    seq[-1] = it
                else:
                    seq.append(None)
            if seq[-1] is None:
                seq[-1] = self._rail(col.bottom) if col.bottom is not None else '0'
            seq = [s if s is not None else self._auto() for s in seq]
            parts = [it for it in col.stack if not isinstance(it, str)]
            for i, it in enumerate(parts):
                a, b = seq[i], seq[i + 1]
                if isinstance(it, Q):
                    if it.kind == 'npn':
                        it.c, it.e = a, b
                    else:
                        it.e, it.c = a, b
                    if it.diode:
                        it.b = it.c
                    elif it.base_series is not None:
                        mid = self._auto()
                        self.branches.append((it.base_series, it.base, mid))
                        it.b = mid
                    else:
                        it.b = it.base
                    self.bjts.append(it)
                else:
                    self.branches.append((it, a, b))
            self.col_nodes.append(seq)
        for z, a, b in self.links:     # elements between nodes of different columns (e.g. coupling caps)
            self.branches.append((z, a, b))
        if self.src is not None:
            n = self.src.node
            cur = 'vi'
            for z in (self.src.rs, self.src.c):
                if z is not None:
                    nxt = self._auto()
                    self.branches.append((z, cur, nxt))
                    cur = nxt
            # last series element ends on the target node
            if cur != 'vi':
                z, a, _ = self.branches[-1]
                self.branches[-1] = (z, a, n)
            self.fixed['vi'] = 0.0
        if self.load is not None:
            if self.load.c is not None:
                self.branches.append((self.load.c, self.load.node, 'vo'))
                out = 'vo'
            else:
                out = self.load.node
            if self.load.rl is not None:
                self.branches.append((self.load.rl, out, '0'))
            self.out = out
        for q in self.bjts:
            for role, n in (('B', q.b), ('C', q.c), ('E', q.e)):
                if n not in self.fixed and n not in self.label:
                    self.label[n] = role + q.name[1:]

    def disp(self, n):
        if n == '0':
            return '0'
        if n in self.fixed:
            v = self.fixed[n]
            return f'({v:g})' if v < 0 else f'{v:g}'
        return 'V_{' + self.label.get(n, n) + '}'

    def elements(self):
        return [e for z, _, _ in self.branches for e in z.elems()]

    # ------------------------------------------------------------------ drawing
    def draw(self, base, fontsize=11, show_values=True):
        pen = Sch(show_values, fontsize=fontsize)
        d = pen.d
        pos = {}             # node -> list of (x, y) points where it appears
        qanch = {}
        x = 0.0 if self.src is None else 1.4 + sum(hwidth(z) for z in (self.src.rs, self.src.c) if z is not None) + (0.6 if self.src.node in [n for s_ in self.col_nodes for n in s_] else 0.0)
        for col, seq in zip(self.cols, self.col_nodes):
            parts = [it for it in col.stack if not isinstance(it, str)]
            hs = [QH if isinstance(p, Q) else RH * vweight(p) for p in parts]
            ytop = sum(hs)
            y = ytop
            pos.setdefault(seq[0], []).append((x, y))
            if col.top_node is None and col.top is not None:
                if col.top == 0:
                    pen.d.add(elm.Ground().at((x, y)).theta(180))
                else:
                    pen.d.add(elm.Vdd().at((x, y)).label(f'{"+" if col.top > 0 else "−"}{eng(abs(col.top), "V")}'))
            for p, h, nb in zip(parts, hs, seq[1:]):
                if isinstance(p, Q):
                    e = (elm.BjtNpn(circle=True) if p.kind == 'npn' else elm.BjtPnp(circle=True)).theta(0)
                    if p.face == 'right':
                        e = e.reverse()
                    e = d.add(e.at((x, y)).anchor('collector' if p.kind == 'npn' else 'emitter')
                              .label(_mtext(p.tex), loc='right' if p.face == 'left' else 'left', fontsize=fontsize - 1))
                    qanch[p.name] = e
                else:
                    pen.v(p, (x, y), h, -1)
                y -= h
                pos.setdefault(nb, []).append((x, y))
            if seq[-1] == '0':
                pen.d.add(elm.Ground().at((x, y)))
            elif seq[-1] in self.fixed:
                pen.d.add(elm.Vss().at((x, y)).label(f'{"+" if col.bottom > 0 else "−"}{eng(abs(col.bottom), "V")}',
                                                       loc='bottom'))
            col._x = x
            x += col.gap + max([vwidth(p) for p in parts if not isinstance(p, Q)] + [0])
        # join nodes that appear in several columns
        for n, pts in pos.items():
            if len(pts) > 1 and n not in self.fixed:
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    xm = (x1 + x2) / 2 if abs(y1 - y2) > 1e-6 else x2
                    pen.path((x1, y1), (xm, y1), (xm, y2), (x2, y2))
                for pt in pts:
                    pen.dot(pt)
        # links between columns: element drawn horizontally at the height of the first node
        for z, a, b in self.links:
            (xa, ya), (xb, yb) = min(((pa, pb) for pa in pos[a] for pb in pos[b]),
                                     key=lambda pp: abs(pp[0][0] - pp[1][0]))
            if xa > xb:
                (xa, ya), (xb, yb) = (xb, yb), (xa, ya)
            w = hwidth(z)
            xs = (xa + xb) / 2 - w / 2
            pen.line((xa, ya), (xs, ya))
            end = pen.h(z, (xs, ya))
            if abs(ya - yb) > 1e-6:
                pen.path(end, (xb - 0.5, ya), (xb - 0.5, yb), (xb, yb))
            else:
                pen.line(end, (xb, yb))
            pen.dot((xa, ya))
            pen.dot((xb, yb))
        # base wiring
        for q in self.bjts:
            e = qanch[q.name]
            bx, by = e.base
            side = -1 if q.face == 'left' else 1
            if q.diode:
                cx, cy = e.collector
                k = bx + side * 0.5
                pen.path((bx, by), (k, by), (k, cy + (0.35 if q.kind == 'npn' else -0.35)),
                         (cx, cy + (0.35 if q.kind == 'npn' else -0.35)))
                continue
            if q.base == '0':   # grounded base
                k = bx + side * 0.6
                pen.line((bx, by), (k, by))
                pen.d.add(elm.Ground().at((k, by)))
                continue
            tgt = pos.get(q.base)
            if not tgt:
                continue
            nx, ny = min(tgt, key=lambda p: abs(p[0] - bx))
            if q.base_series is not None:
                w = hwidth(q.base_series)
                xs = bx - w if side < 0 else bx
                if side < 0:
                    pen.path((nx, ny), (xs - 0.3, ny), (xs - 0.3, by), (xs, by))
                    pen.h(q.base_series, (xs, by))
                else:
                    pen.h(q.base_series, (bx, by))
                    pen.path((bx + w, by), (bx + w + 0.3, by), (bx + w + 0.3, ny), (nx, ny))
            else:
                k = bx + side * 0.4
                if abs(ny - by) < 1e-6:
                    pen.line((nx, ny), (bx, by))
                else:
                    pen.path((nx, ny), (k, ny), (k, by), (bx, by))
            pen.dot((nx, ny))
        # source and load
        if self.src is not None and self.src.node not in pos:   # source drives a base directly
            q = next(q for q in self.bjts if q.base == self.src.node)
            bx, by = qanch[q.name].base
            d.add(elm.SourceSin().at((0, by - 2.6)).up().length(2.6).label(_mtext(self.src.name), loc='top'))
            pen.d.add(elm.Ground().at((0, by - 2.6)))
            pen.line((0, by), (bx, by))
        elif self.src is not None:
            tx, ty = min(pos[self.src.node], key=lambda p: p[0])
            ys = ty
            d.add(elm.SourceSin().at((0, ys - 2.6)).up().length(2.6).label(_mtext(self.src.name), loc='top'))
            pen.d.add(elm.Ground().at((0, ys - 2.6)))
            p = (0, ys)
            for z in (self.src.rs, self.src.c):
                if z is not None:
                    p = pen.h(z, p)
            pen.path(p, (tx, ys), (tx, ty))
            pen.dot((tx, ty))
        if self.load is not None:
            tx, ty = max(pos[self.load.node], key=lambda p: p[0])
            right = [c._x for c in self.cols if c._x > tx + 0.5]
            if right:   # columns to the right: go over the top of the drawing instead of through them
                ytop = max(py for pts in pos.values() for _, py in pts) + 1.6
                xr = max(right) + 1.4
                pen.path((tx, ty), (tx + 0.6, ty), (tx + 0.6, ytop), (xr, ytop), (xr, ty))
                pen.dot((tx, ty))
                tx = xr - 0.6
            p = (tx, ty)
            pen.line(p, (tx + 0.6, ty))
            p = (tx + 0.6, ty)
            if self.load.c is not None:
                p = pen.h(self.load.c, p)
            pen.line(p, (p[0] + 0.8, ty))
            p = (p[0] + 0.8, ty)
            if self.load.rl is not None:
                pen.dot(p)
                end = pen.v(self.load.rl, p, RH, -1)
                pen.d.add(elm.Ground().at(end))
            pen.line(p, (p[0] + 0.8, ty))
            pen.dot((p[0] + 0.8, ty), open_=True)
            pen.text((p[0] + 1.0, ty), _mtext('V_o'), halign='left', color=BLUE)
        for n, pts in pos.items():
            for col in self.cols:
                if n in col.label_nodes:
                    for (px, py) in pts[:1]:
                        pen.text((px + 0.15, py + 0.35), _mtext(self.disp(n)), halign='left', color=BLUE, fontsize=fontsize - 2)
        pen.save(base)
