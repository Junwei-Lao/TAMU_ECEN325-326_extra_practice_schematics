"""Draw ladder circuits with schemdraw: the problem schematic and its DC / AC equivalents."""
import schemdraw
import schemdraw.elements as elm

from common.units import eng, num_tex
from .ladder import El, Ser, Par, NamedZ, Src, VCVS, VCCS, kept, merge_shunts_ac, name_tex

schemdraw.use('matplotlib')

EL = 2.6        # horizontal element length
H = 3.6         # height of the top rail above ground
UP = 2.4        # length of a shunt that goes up to a positive rail
VOFF = 2.0      # vertical offset of the second branch of a horizontal parallel pair
VCOL = 2.2      # horizontal spacing of columns of a vertical parallel combination
GAP = 1.3       # rail wire before the first shunt of a node
GAP_SAME = 2.7  # between two shunts on the same side of the rail (room for both labels)
GAP_OPP = 1.0   # between an up-going and a down-going shunt
STAGE_GAP = 4.2


class Wire:
    """A shorted element in the DC view (inductor -> wire)."""
    def __init__(self, el):
        self.el = el


def _mtext(t):
    return '$' + t + '$'


def _rail_txt(v):
    v = float(v)
    return ('+' if v > 0 else '−') + eng(abs(v), 'V')


def _el_elem(z):
    k = z.kind
    if k == 'R':
        return elm.Resistor()
    if k == 'C':
        return elm.Capacitor()
    return elm.Inductor2(loops=3)


def _name_val(z, show_values):
    name = _mtext(name_tex(z.name))
    val = z.value_txt() if show_values else ''
    return name, val


# ---------------------------------------------------------------- sizes
def hwidth(z):
    if isinstance(z, (El, Wire)):
        return EL
    if isinstance(z, Ser):
        return sum(hwidth(p) for p in z.parts)
    if isinstance(z, Par):
        return max(hwidth(p) for p in z.parts)
    raise TypeError(z)


def vwidth(z):
    if isinstance(z, (El, Wire)):
        return 0.0
    if isinstance(z, Ser):
        return max(vwidth(p) for p in z.parts)
    if isinstance(z, Par):
        return sum(vwidth(p) for p in z.parts) + VCOL * (len(z.parts) - 1)
    raise TypeError(z)


def vweight(z):
    if isinstance(z, (El, Wire)):
        return 1
    if isinstance(z, Ser):
        return sum(vweight(p) for p in z.parts)
    return max(vweight(p) for p in z.parts)


# ---------------------------------------------------------------- primitives
class Pen:
    def __init__(self, show_values=True, fontsize=11):
        self.d = schemdraw.Drawing(show=False)
        self.d.config(fontsize=fontsize, unit=2.5)
        self.show_values = show_values

    def line(self, a, b):
        if a != b:
            self.d.add(elm.Line().at(a).to(b))

    def dot(self, p, open_=False):
        self.d.add(elm.Dot(open=open_).at(p))

    def text(self, p, t, **kw):
        self.d.add(elm.Label().at(p).label(t, **kw))

    # horizontal composite from p to the right, returns end point
    def h(self, z, p, stack=1):
        x, y = p
        if isinstance(z, Wire):
            end = (x + EL, y)
            self.line(p, end)
            self.text((x + EL / 2, y + 0.45), _mtext(name_tex(z.el.name)) + ' (short)', fontsize=9)
            return end
        if isinstance(z, El):
            name, val = _name_val(z, self.show_values)
            e = _el_elem(z).right().at(p).length(EL).label(name, loc='top')
            if val:
                e = e.label(val, loc='bottom')
            self.d.add(e)
            return (x + EL, y)
        if isinstance(z, Ser):
            for part in z.parts:
                p = self.h(part, p, stack)
            return p
        if isinstance(z, Par):
            W = hwidth(z)
            for k, part in enumerate(z.parts):
                yk = y + stack * k * VOFF
                if k:
                    self.line((x, y), (x, yk))
                end = self.h(part, (x, yk), stack)
                self.line(end, (x + W, yk))
                if k:
                    self.line((x + W, yk), (x + W, y))
            if len(z.parts) > 1:
                self.dot((x, y))
                self.dot((x + W, y))
            return (x + W, y)
        raise TypeError(z)

    # vertical composite starting at p going down (sign=-1) or up (sign=+1), total length
    def v(self, z, p, length, sign=-1):
        x, y = p
        if isinstance(z, Wire):
            end = (x, y + sign * length)
            self.line(p, end)
            self.text((x + 0.25, y + sign * length / 2), _mtext(name_tex(z.el.name)) + ' (short)',
                      fontsize=9, loc='right', halign='left')
            return end
        if isinstance(z, El):
            name, val = _name_val(z, self.show_values)
            e = _el_elem(z).at(p).length(length)
            e = e.down() if sign < 0 else e.up()
            e = e.label(name, loc='top')
            if val:
                e = e.label(val, loc='bottom')
            self.d.add(e)
            return (x, y + sign * length)
        if isinstance(z, Ser):
            tot = vweight(z)
            for part in z.parts:
                p = self.v(part, p, length * vweight(part) / tot, sign)
            return p
        if isinstance(z, Par):
            cx = x
            bottoms = []
            for k, part in enumerate(z.parts):
                if k:
                    self.line((prev_x, y), (cx, y))
                b = self.v(part, (cx, y), length, sign)
                if k:
                    self.line(bottoms[-1], b)
                bottoms.append(b)
                prev_x = cx
                cx += vwidth(part) + VCOL
            self.dot((x, y))
            return bottoms[0]
        raise TypeError(z)

    def shunt(self, z, rail, p):
        """Shunt from rail-point p; returns the x extent used to the right of p."""
        if rail is not None and rail > 0:
            top = self.v(z, p, UP, +1)
            self.d.add(elm.Vdd().at(top).label(_rail_txt(rail)))
        else:
            bot = self.v(z, p, H, -1)
            if rail is None:
                self.d.add(elm.Ground().at(bot))
            else:
                self.d.add(elm.Vss().at(bot).label(_rail_txt(rail), loc='bottom'))
        self.dot(p)
        return vwidth(z)

    def save(self, base):
        self.d.save(base + '.pdf')
        self.d.save(base + '.png', dpi=110)
        import matplotlib.pyplot as plt
        plt.close('all')


# ---------------------------------------------------------------- stages
def _src_label(src):
    if isinstance(src, Src):
        return _mtext(src.name)
    if isinstance(src, VCVS):
        return _mtext(num_tex(src.gain) + 'V_{' + src.ctrl + '}')
    return _mtext(num_tex(src.gm) + 'V_{' + src.ctrl + '}')


def draw_stage(pen, x0, start, nodes):
    """start: 'src' object | 'short' (DC: shorted input) | None (floating start).
    nodes: list of dicts {series, shunts:[(z,rail)], label, is_out}."""
    p = (x0, H)
    if start is not None and start != 'short':
        if isinstance(start, VCCS):
            e = elm.SourceControlledI().at((x0, H)).down().length(H) if start.direction == 'down' \
                else elm.SourceControlledI().at((x0, 0)).up().length(H)
        elif isinstance(start, VCVS):
            e = elm.SourceControlledV().at((x0, 0)).up().length(H)
        else:
            e = elm.SourceSin().at((x0, 0)).up().length(H)
        pen.d.add(e.label(_src_label(start), loc='top'))
        pen.d.add(elm.Ground().at((x0, 0)))
    elif start == 'short':
        pen.line((x0, 0), (x0, H))
        pen.d.add(elm.Ground().at((x0, 0)))
        pen.text((x0 - 0.3, H / 2), _mtext('V_i') + '\n= 0', fontsize=9, halign='right')
    x = x0
    for k, nd in enumerate(nodes):
        if nd['series'] is not None:
            p = pen.h(nd['series'], (x, H))
            x = p[0]
        terminal = nd['is_out'] and k == len(nodes) - 1
        label_pt = None
        prev_side = None
        for z, rail in nd['shunts']:
            side = 'up' if rail is not None and rail > 0 else 'down'
            if prev_side is None:
                gap = 0 if (k == 0 and start is None) else GAP
            else:
                gap = GAP_SAME if side == prev_side else GAP_OPP
            pen.line((x, H), (x + gap, H))
            x += gap
            if label_pt is None:
                label_pt = (x, H)
            w = pen.shunt(z, rail, (x, H))
            if w:
                pen.line((x, H), (x + w, H))
                x += w
            prev_side = side
        if nd.get('label') and not terminal:
            first_up = bool(nd['shunts']) and nd['shunts'][0][1] is not None and nd['shunts'][0][1] > 0
            if label_pt is None:
                label_pt = (x, H)
                pen.dot(label_pt)
            # put the name on the side of the rail that has no element at this dot
            pen.text((label_pt[0] - 0.12, H - 0.5 if first_up else H + 0.5), _mtext('V_{' + nd['label'] + '}'),
                     halign='right', color='#1f4e9e')
        if nd['shunts'] and (terminal or k < len(nodes) - 1):
            pen.line((x, H), (x + GAP * 0.6, H))
            x += GAP * 0.6
        if nd['is_out'] and k == len(nodes) - 1:
            pen.line((x, H), (x + 0.8, H))
            x += 0.8
            pen.dot((x, H), open_=True)
            pen.text((x + 0.2, H), _mtext('V_{' + nd['label'] + '}'), halign='left',
                     color='#1f4e9e')
            x += 0.6
    return x


def _nodes_full(stage):
    return [dict(series=nd.series_in, shunts=list(nd.shunts), label=nd.label,
                 is_out=nd.is_out) for nd in stage.nodes]


def draw_full(circ, base, show_values=True):
    pen = Pen(show_values)
    x = 0
    for st in circ.stages:
        x = draw_stage(pen, x, st.src, _nodes_full(st)) + STAGE_GAP
    pen.save(base)


def draw_ac(circ, base):
    """AC equivalent: rails -> ground, parallel resistors merged, every analysis node named."""
    pen = Pen(True)
    x = 0
    for st in circ.stages:
        nodes = []
        for nd, zs in kept(st):
            sh, _ = merge_shunts_ac(nd)
            nodes.append(dict(series=zs, shunts=[(z, None) for z in sh],
                              label=nd.name if nd.name != 'i' else None, is_out=nd.is_out))
        x = draw_stage(pen, x, st.src, nodes) + STAGE_GAP
    pen.save(base)


# ---------------------------------------------------------------- DC view
def dc_view(z):
    """Transform an impedance for DC: C -> None (open), L -> Wire (short)."""
    if isinstance(z, NamedZ):
        z = z.inner
    if isinstance(z, El):
        if z.kind == 'C':
            return None
        if z.kind == 'L':
            return Wire(z)
        return z
    if isinstance(z, Ser):
        parts = [dc_view(p) for p in z.parts]
        if any(p is None for p in parts):
            return None
        return Ser(*parts) if len(parts) > 1 else parts[0]
    if isinstance(z, Par):
        parts = [dc_view(p) for p in z.parts]
        parts = [p for p in parts if p is not None]
        if not parts:
            return None
        return Par(*parts) if len(parts) > 1 else parts[0]
    raise TypeError(z)


def draw_dc(circ, base):
    """DC equivalent of stage 1: only the part that is DC-connected to the output."""
    st = circ.stages[0]
    nodes = []
    for nd in st.nodes:
        ser = dc_view(nd.series_in) if nd.series_in is not None else 'first'
        shunts = [(dc_view(z), r) for z, r in nd.shunts]
        shunts = [(z, r) for z, r in shunts if z is not None]
        nodes.append(dict(series=ser, shunts=shunts, label=nd.label, is_out=nd.is_out))
    o = next(i for i, nd in enumerate(st.nodes) if nd.is_out)
    lo = 0
    for i in range(o, 0, -1):
        if nodes[i]['series'] is None:
            lo = i
            break
    hi = len(nodes) - 1
    for i in range(o + 1, len(nodes)):
        if nodes[i]['series'] is None:
            hi = i - 1
            break
    seg = nodes[lo:hi + 1]
    start = 'short' if lo == 0 else None
    seg[0] = dict(seg[0], series=None)
    if lo == 0:  # the shorted input pins this node to 0 V; its shunts change nothing
        seg[0]['shunts'] = []
    pen = Pen(True)
    draw_stage(pen, 0, start, seg)
    pen.save(base)
