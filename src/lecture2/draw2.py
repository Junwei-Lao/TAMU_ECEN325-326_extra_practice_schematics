"""Drawing helpers for op-amp schematics (schemdraw), built on the Lecture-1 composite pen."""
import schemdraw.elements as elm

from common.units import eng
from lecture1.draw import Pen, hwidth, vwidth, EL, _mtext

OA_W = 3.415      # schemdraw op-amp: input pins to output pin
OA_H = 1.25       # distance between the two input pins
BLUE = '#1f4e9e'


class Sch(Pen):
    """Pen + op-amp / source / label helpers. All coordinates are absolute."""

    def opamp(self, x_in, y_top, plus_on_top=False, label=None):
        """Place an op-amp whose upper input pin is at (x_in, y_top). Returns dict of pin points."""
        e = elm.Opamp(leads=True)
        if plus_on_top:
            e = e.flip()
        e = e.at((x_in, y_top)).anchor('in2' if plus_on_top else 'in1')
        if label:
            e = e.label(label, loc='center', fontsize=9)
        self.d.add(e)
        top, bot = (x_in, y_top), (x_in, y_top - OA_H)
        out = (x_in + OA_W, y_top - OA_H / 2)
        return dict(plus=top if plus_on_top else bot, minus=bot if plus_on_top else top, out=out)

    def path(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.line(a, b)

    def ground(self, p):
        self.d.add(elm.Ground().at(p))

    def source(self, p_top, label='$V_i$', length=2.4):
        x, y = p_top
        self.d.add(elm.SourceSin().at((x, y - length)).up().length(length).label(label, loc='top'))
        self.ground((x, y - length))

    def rail(self, p, volts, up=True):
        txt = ('+' if volts > 0 else '−') + eng(abs(volts), 'V')
        if up:
            self.d.add(elm.Vdd().at(p).label(txt))
        else:
            self.d.add(elm.Vss().at(p).label(txt, loc='bottom'))

    def terminal(self, p, label):
        self.dot(p, open_=True)
        self.text((p[0] + 0.2, p[1]), _mtext(label), halign='left', color=BLUE)

    def node_label(self, p, label, dx=-0.12, dy=0.45, halign='right'):
        self.text((p[0] + dx, p[1] + dy), _mtext(label), halign=halign, color=BLUE)

    def vdown(self, z, p, length=2.2):
        """Element/composite from p straight down, ending in ground."""
        end = self.v(z, p, length, -1)
        self.ground(end)
        return end


__all__ = ['Sch', 'OA_W', 'OA_H', 'hwidth', 'vwidth', 'EL', 'BLUE']
