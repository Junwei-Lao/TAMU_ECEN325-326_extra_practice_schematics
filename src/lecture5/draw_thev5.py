"""Schematics for set 5F: a transistor with ladder networks drawn as real ladders.

Each transistor is a block: the gate network runs to the LEFT at gate height, the network of the upper terminal
(NMOS drain / PMOS source) runs to the RIGHT along an upper bus, the network of the lower terminal along a lower bus.
Shunts are vertical branches to their supplies; series elements sit on the bus. A second transistor whose gate is a
node of the first one is placed to the right and wired over the top (or under the bottom)."""
import schemdraw.elements as elm

from lecture1.draw import EL, _mtext
from lecture2.draw2 import Sch
from .thev5 import Ladder, Node, Ser

YT, YB = 3.8, -3.8       # upper / lower bus
SH = 2.4                 # shunt length
STEP = 2.2               # spacing of shunt branches along a bus
BLUE = '#1f4e9e'


def _rail(pen, p, v, up):
    if v == 0:
        pen.d.add(elm.Ground().at(p).theta(180) if up else elm.Ground().at(p))
    else:
        pen.rail(p, v, up=up)


def _ladder(pen, lad, x0, y, d, load=None):
    """Draw `lad` from terminal point (x0, y) in direction d (+1 right, -1 left). Returns the extreme x used.
    load = (C, R_L) is drawn after the terminal node's shunts (AC output)."""
    x = x0
    first = True
    for it in lad.items:
        if isinstance(it, Ser):
            a = x + d * 0.4
            pen.line((x, y), (a, y))
            left = a if d > 0 else a - EL
            pen.h(it.z, (left, y))
            x = a + d * EL
            continue
        shunts = it.shunts
        xs = x + d * (1.0 if first else 0.6)
        pen.line((x, y), (xs, y))
        pts = []
        for sh in shunts:
            if sh.src == 'vi':
                continue
            up = sh.src > 0
            end = pen.v(sh.z, (xs, y), SH, 1 if up else -1)
            _rail(pen, end, sh.src, up)
            pts.append(xs)
            xs += d * STEP
        for sh in shunts:
            if sh.src != 'vi':
                continue
            a = xs - d * STEP + d * 0.6 if pts else xs
            pen.line((x, y), (a, y))
            left = a if d > 0 else a - EL
            pen.h(sh.z, (left, y))
            sx = a + d * EL + d * 0.4
            pen.line((a + d * EL, y), (sx, y))
            pen.source((sx, y), label='$V_i$')
            pts.append(sx)
            xs = sx + d * 0.6
        last = pts[-1] if pts else x
        if len(pts) > 1 or (pts and abs(pts[0] - x) > 1e-9):
            pen.line((x, y), (last, y))
        for px in pts[:-1] if len(pts) > 1 else []:
            pen.dot((px, y))
        if first and load is not None:
            c, rl = load
            a = last + d * 0.8
            pen.line((last, y), (a, y))
            pen.dot((last, y)) if pts else None
            end = pen.h(c, (a, y))
            pen.line(end, (end[0] + 0.8, y))
            p = (end[0] + 0.8, y)
            pen.dot(p)
            e2 = pen.v(rl, p, SH, -1)
            _rail(pen, e2, 0, False)
            pen.line(p, (p[0] + 0.8, y))
            pen.dot((p[0] + 0.8, y), open_=True)
            pen.text((p[0] + 1.0, y), _mtext('V_o'), halign='left', color=BLUE)
            last = p[0] + 1.6
        x = last
        first = False
    return x


def draw5f(p, base, show_values=True, fontsize=13):
    pen = Sch(show_values, fontsize=fontsize)
    d = pen.d
    xq = 0.0
    term = {}                   # node name -> (x, y) where it can be reached
    load = None
    if p.ac:
        node, c, rl = p.ac['load']
        load = (node, (c, rl))
    for dv in p.devs:
        q, k = dv.q, dv.k
        # room for the gate network on the left
        if isinstance(dv.gate, Ladder):
            ncols = sum(len(it.shunts) for it in dv.gate.items if isinstance(it, Node)) + \
                sum(1 for it in dv.gate.items if isinstance(it, Ser))
            xq += 1.0 + STEP * ncols + 2.0
        else:
            xq += 2.5
        e, an = q.element()
        g_anchor = 'gate'
        e = d.add(e.at((xq, 0)).anchor(g_anchor).label(q.tag(), loc='right' if q.face == 'left' else 'left',
                                                       fontsize=fontsize - 1))
        gx, gy = e.gate
        top = e.drain if q.s > 0 else e.source
        bot = e.source if q.s > 0 else e.drain
        xt = top[0]
        top_spec, bot_spec = (dv.drain, dv.source) if q.s > 0 else (dv.source, dv.drain)
        top_name, bot_name = (q.c, q.e)
        if q.s < 0:
            top_name, bot_name = q.e, q.c
        xmax = xt + 1.5
        for spec, pin, yb, name, up in ((top_spec, top, YT, top_name, True), (bot_spec, bot, YB, bot_name, False)):
            if isinstance(spec, Ladder):
                pen.line(pin, (xt, yb))
                term[name] = (xt, yb)
                ld = load[1] if load and load[0] == name else None
                xmax = max(xmax, _ladder(pen, spec, xt, yb, 1, ld))
                pen.text((xt - 0.12, yb + (0.35 if up else -0.35)), _mtext(f'V_{{{"D" if name == q.c else "S"}{k}}}'),
                         halign='right', color=BLUE, fontsize=fontsize - 2)
            else:
                ye = pin[1] + (1.0 if up else -1.0)
                pen.line(pin, (xt, ye))
                _rail(pen, (xt, ye), spec, up)
                term[name] = (xt, ye)
        # gate
        if isinstance(dv.gate, Ladder):
            _ladder(pen, dv.gate, gx, gy, -1)
        elif dv.gate == 0:
            pen.line((gx, gy), (gx - 0.6, gy))
            pen.d.add(elm.Ground().at((gx - 0.6, gy)))
        else:
            nx, ny = term[dv.gate]
            yr = YT + 3.4 if ny > 0 else YB - 3.4
            pen.path((gx, gy), (gx - 0.6, gy), (gx - 0.6, yr), (nx - 0.5, yr), (nx - 0.5, ny), (nx, ny))
            pen.dot((nx, ny))
        xq = xmax + 1.0
    pen.save(base)
