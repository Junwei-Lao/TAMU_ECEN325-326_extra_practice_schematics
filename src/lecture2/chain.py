"""A cascade of op-amp blocks driven by V_i (plus optional DC supplies inside Sum blocks)."""
import sympy as sp

from common.tf import s
from .netlist import Net
from .draw2 import Sch


class Chain:
    def __init__(self, blocks):
        self.blocks = blocks
        for k, b in enumerate(blocks, 1):
            b.name(k)
        n = len(blocks)
        self.outs = [f'o{k}' for k in range(1, n)] + ['o']

    def vin(self, k):
        """Name of the voltage feeding block k (0-based)."""
        return 'i' if k == 0 else self.outs[k - 1]

    def net(self):
        net = Net()
        for k, b in enumerate(self.blocks):
            b.build(net, self.vin(k), self.outs[k])
            if b.load is not None:
                net.add(b.load, self.outs[k], '0')
        return net

    def has_dc(self):
        return any(b.kind == 'sum' for b in self.blocks)

    def rails(self):
        return sorted(b.vdc for b in self.blocks if b.kind == 'sum')

    def H_ideal(self):
        H = sp.Integer(1)
        for b in self.blocks:
            H *= b.H()
        return H

    def H_stage(self, k, A=None):
        b = self.blocks[k]
        if A is None:
            return b.H()
        ap, am, beta = b.ab()
        return sp.cancel(sp.together(A * (ap - am) / (1 + A * beta)))

    def draw(self, base, label_outputs=False, dc_bias=None):
        sch = Sch(True, fontsize=11 + 2 * (len(self.blocks) - 1))  # wide drawings get scaled down
        if dc_bias is None:
            sch.source((0, 0))
        else:  # DC bias in series with the AC input (v_i on top, V_DC below)
            import schemdraw.elements as elm
            from common.units import eng
            sch.d.add(elm.SourceSin().at((0, -2.4)).up().length(2.4).label('$v_i$', loc='top'))
            sch.d.add(elm.SourceV().at((0, -4.8)).up().length(2.4).label(
                f'$V_{{DC}}$\n{eng(dc_bias, "V")}', loc='top'))
            sch.ground((0, -4.8))
        p = (0.6, 0)
        sch.line((0, 0), p)
        for k, b in enumerate(self.blocks):
            p = b.draw(sch, p)
            last = k == len(self.blocks) - 1
            if b.load is not None:
                sch.line(p, (p[0] + 1.3, p[1]))
                p = (p[0] + 1.3, p[1])
                sch.vdown(b.load, p, 2.4)
                sch.dot(p)
            if not last:
                if label_outputs:
                    sch.node_label(p, 'V_{' + self.outs[k] + '}', dx=0.15, dy=0.4, halign='left')
                sch.line(p, (p[0] + 1.0, p[1]))
                p = (p[0] + 1.0, p[1])
        sch.line(p, (p[0] + 0.8, p[1]))
        sch.terminal((p[0] + 0.8, p[1]), 'V_o')
        sch.save(base)
