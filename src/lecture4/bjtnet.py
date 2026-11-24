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


def _hits(rects, x1, x2, y, ends=()):
    """True if the horizontal segment x1..x2 at height y crosses an element body (ends: x of its own end points)."""
    for a, b, lo, hi, *_ in rects:
        if lo < y < hi and a < x2 - 0.05 and b > x1 + 0.05:
            if any(a - 0.05 <= e <= b + 0.05 for e in ends) and not (a > x1 + 0.05 and b < x2 - 0.05):
                continue          # the body of the element the wire starts or ends at
            return True
    return False


def _vhits(rects, x, y1, y2, labels=False):
    lo, hi = min(y1, y2), max(y1, y2)
    if labels:
        return any(a < x < b and l < hi - 0.05 and h > lo + 0.05 for a, b, l, h, _, _ in rects)
    return any(a < x < b and l < hi - 0.05 and h > lo + 0.05 for _, _, l, h, a, b in rects)   # bodies only


def _pin_h(pins, x1, x2, y):
    """A horizontal wire would run through (or right next to) a junction of another node."""
    return any(x1 + 0.05 < px < x2 - 0.05 and abs(py - y) < 0.3 for px, py in pins)


def _pin_v(pins, x, y1, y2):
    lo, hi = min(y1, y2), max(y1, y2)
    return any(abs(px - x) < 0.2 and lo - 0.05 < py < hi + 0.05 for px, py in pins)


def _seg_h(segs, x1, x2, y):
    return any(abs(sy - y) < 0.25 and a < x2 - 0.05 and b > x1 + 0.05 for sy, a, b in segs[0])


def _seg_v(segs, x, y1, y2):
    lo, hi = min(y1, y2), max(y1, y2)
    return any(abs(sx - x) < 0.25 and a < hi - 0.05 and b > lo + 0.05 for sx, a, b in segs[1])


def _path_segs(pts):
    hs, vs = [], []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if abs(y1 - y2) < 1e-9:
            hs.append((y1, min(x1, x2), max(x1, x2)))
        else:
            vs.append((x1, min(y1, y2), max(y1, y2)))
    return hs, vs


def _route(rects, start, k, gate, pins=(), segs=((), ())):
    """Wire from a node to a gate/base: node -> (k, y*) -> gate, with the horizontal run at a free height y*
    (no element body, label, junction or parallel wire of another node on the way)."""
    (nx, ny), (bx, by) = start, gate

    def free_h(x1, x2, y, ends=()):
        return not _hits(rects, x1, x2, y, ends) and not _pin_h(pins, x1, x2, y) and not _seg_h(segs, x1, x2, y)

    def free_v(x, y1, y2, labels=False):
        return not _vhits(rects, x, y1, y2, labels) and not _pin_v(pins, x, y1, y2) and not _seg_v(segs, x, y1, y2)

    if free_h(min(nx, k), max(nx, k), ny, (nx,)) and free_v(k, ny, by) and free_h(min(k, bx), max(k, bx), by, (bx,)):
        return [(nx, ny), (k, ny), (k, by), (bx, by)]
    ys = sorted({round(ny + d * 0.25, 2) for d in range(-48, 49)} | {by},
                key=lambda y: abs(y - by) + 0.3 * abs(y - ny))
    for y in ys:
        d = 1 if k > nx else -1
        for sx in (nx + 0.5 * d, nx - 0.5 * d, nx + 1.6 * d, nx - 1.6 * d):   # lanes beside the node
            if free_h(min(sx, k), max(sx, k), y) and free_v(sx, ny, y, True) and free_v(k, y, by) \
                    and free_h(min(nx, sx), max(nx, sx), ny, (nx,)):
                return [(nx, ny), (sx, ny), (sx, y), (k, y), (k, by), (bx, by)]
    return [(nx, ny), (k, ny), (k, by), (bx, by)]


class Q:
    def __init__(self, name, kind='npn', base=None, beta=100, diode=False, face='left'):
        self.name, self.kind, self.beta, self.diode, self.face = name, kind, beta, diode, face
        if isinstance(base, tuple):
            self.base, self.base_series = base
        else:
            self.base, self.base_series = base, None
        self.c = self.e = self.b = None

    ROLES = ('B', 'C', 'E')      # letters of the base / collector / emitter nodes in V_{..} labels
    H = QH                       # drawn height between the top and bottom terminals
    LEAD = 0.0                   # part of H that is an extra wire on the emitter/source side
    DIODE_DY = 0.35              # where the diode connection meets the collector/drain wire

    @property
    def s(self):
        return 1 if self.kind in ('npn', 'nmos') else -1

    def element(self):
        """schemdraw element (theta 0) and the names of its base, collector and emitter anchors."""
        e = (elm.BjtNpn(circle=True) if self.s > 0 else elm.BjtPnp(circle=True)).theta(0)
        if self.face == 'right':
            e = e.reverse()
        return e, ('base', 'collector', 'emitter')

    def tag(self):
        return _mtext(self.tex)

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
                    if it.s > 0:
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
            for role, n in zip(q.ROLES, (q.b, q.c, q.e)):
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
        rects = []           # element bodies (x1, x2, y1, y2) that wires should not cross
        qanch = {}
        x = 0.0 if self.src is None else 1.4 + sum(hwidth(z) for z in (self.src.rs, self.src.c) if z is not None) + (0.6 if self.src.node in [n for s_ in self.col_nodes for n in s_] else 0.0)
        for col, seq in zip(self.cols, self.col_nodes):
            parts = [it for it in col.stack if not isinstance(it, str)]
            hs = [p.H if isinstance(p, Q) else RH * vweight(p) for p in parts]
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
                    e, an = p.element()
                    lead = p.LEAD                   # extra wire on the source/emitter side (room for bias buses)
                    yt = y - (lead if p.s < 0 else 0)
                    if lead and p.s < 0:
                        pen.line((x, y), (x, yt))
                    e = d.add(e.at((x, yt)).anchor(an[1] if p.s > 0 else an[2])
                              .label(p.tag(), loc='right' if p.face == 'left' else 'left', fontsize=fontsize - 1))
                    if lead and p.s > 0:
                        pen.line((x, y - h + lead), (x, y - h))
                    qanch[p.name] = (e, an)
                    gx = getattr(e, an[0])[0]
                    m = 0.2 if lead else 0.0
                    rects.append((min(x, gx) - 0.1, max(x, gx) + 0.1, yt - (h - lead) + m, yt - m,
                                  min(x, gx) - 0.1, max(x, gx) + 0.1))
                else:
                    pen.v(p, (x, y), h, -1)
                    w = max(vwidth(p), 0.7) / 2
                    rects.append((x - w - 0.5, x + w * (2 if not isinstance(p, El) else 1) + (1.2 if show_values else 0.3),
                                  y - 0.8 * h, y - 0.2 * h, x - w, x + w))   # body plus its name/value labels
                y -= h
                pos.setdefault(nb, []).append((x, y))
            if seq[-1] == '0':
                pen.d.add(elm.Ground().at((x, y)))
            elif seq[-1] in self.fixed:
                pen.d.add(elm.Vss().at((x, y)).label(f'{"+" if col.bottom > 0 else "−"}{eng(abs(col.bottom), "V")}',
                                                       loc='bottom'))
            if seq[-1] in self.fixed:        # the supply symbol (and the short lead above it) is an obstacle too
                rects.append((x - 0.5, x + 0.5, y - 0.9, y + 0.3, x - 0.5, x + 0.5))
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
        # links between columns: element drawn horizontally, at the first node's height if that run is free,
        # otherwise at the nearest free height (side lanes next to both nodes)
        wires = []        # (node, horizontal segments, vertical segments)
        for z, a, b in self.links:
            (xa, ya), (xb, yb) = min(((pa, pb) for pa in pos[a] for pb in pos[b]),
                                     key=lambda pp: abs(pp[0][0] - pp[1][0]))
            if xa > xb:
                (xa, ya), (xb, yb), a, b = (xb, yb), (xa, ya), b, a
            w = hwidth(z)
            pins = [pt for nn, pts in pos.items() if nn not in (a, b) for pt in pts]

            def free(y, x1, x2):
                return not _hits(rects, x1, x2, y) and not _pin_h(pins, x1, x2, y)

            if free(ya, xa + 0.05, xb - 0.05) and (abs(ya - yb) < 1e-6 or not _vhits(rects, xb - 0.5, ya, yb)):
                pts1 = [(xa, ya)]
                y = ya
            else:
                y = None
                for cand in sorted({round(ya + d * 0.25, 2) for d in range(-40, 41)}, key=lambda c: abs(c - ya)):
                    if free(cand, xa + 0.45, xb - 0.45) and not _vhits(rects, xa + 0.5, ya, cand, True) \
                            and not _vhits(rects, xb - 0.5, cand, yb, True):
                        y = cand
                        break
                if y is None:
                    y = ya
                    pts1 = [(xa, ya)]
                else:
                    pts1 = [(xa, ya), (xa + 0.5, ya), (xa + 0.5, y)]
            x0 = pts1[-1][0]
            xs = (x0 + xb - 0.5) / 2 - w / 2 if abs(y - yb) > 1e-6 else (x0 + xb) / 2 - w / 2
            pen.path(*pts1, (xs, y))
            end = pen.h(z, (xs, y))
            rects.append((xs, xs + w, y - 0.5, y + 0.5, xs, xs + w))
            if abs(y - yb) > 1e-6:
                pts2 = [end, (xb - 0.5, y), (xb - 0.5, yb), (xb, yb)]
            else:
                pts2 = [end, (xb, yb)]
            pen.path(*pts2)
            hs, vs = _path_segs(pts1 + [(xs, y)])
            hs2, vs2 = _path_segs(pts2)
            wires.append((a, hs + hs2, vs + vs2))
            pen.dot((xa, ya))
            pen.dot((xb, yb))
        # base wiring: diode connections first, then gate/base wires around everything already drawn
        for q in self.bjts:
            if not q.diode:
                continue
            e, an = qanch[q.name]
            bx, by = getattr(e, an[0])
            side = -1 if q.face == 'left' else 1
            cx, cy = getattr(e, an[1])
            k = bx + side * 0.5
            dy = q.DIODE_DY if q.s > 0 else -q.DIODE_DY
            pts = [(bx, by), (k, by), (k, cy + dy), (cx, cy + dy)]
            pen.path(*pts)
            wires.append((q.c, *_path_segs(pts)))
            if q.DIODE_DY == 0:
                pen.dot((cx, cy))
        for q in self.bjts:
            e, an = qanch[q.name]
            bx, by = getattr(e, an[0])
            side = -1 if q.face == 'left' else 1
            if q.diode:
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
                if abs(ny - by) < 1e-6 and not _hits(rects, min(nx, bx), max(nx, bx), ny, (nx, bx)):
                    pen.line((nx, ny), (bx, by))
                else:
                    pins = [pt for nn, pts in pos.items() if nn != q.base for pt in pts]
                    segs = ([s for nn, hs, _ in wires if nn != q.base for s in hs],
                            [s for nn, _, vs in wires if nn != q.base for s in vs])
                    pts = _route(rects, (nx, ny), k, (bx, by), pins, segs)
                    pen.path(*pts)
                    wires.append((q.base, *_path_segs(pts)))
            pen.dot((nx, ny))
        # source and load
        if self.src is not None and self.src.node not in pos:   # source drives a base directly
            q = next(q for q in self.bjts if q.base == self.src.node)
            e, an = qanch[q.name]
            bx, by = getattr(e, an[0])
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
                    left = any(q.LEAD and n in (q.c, q.e) for q in self.bjts)   # keep clear of a MOSFET's labels
                    for (px, py) in pts[:1]:
                        pen.text((px - 0.15 if left else px + 0.15, py + 0.3), _mtext(self.disp(n)),
                                 halign='right' if left else 'left', color=BLUE, fontsize=fontsize - 2)
        pen.save(base)
