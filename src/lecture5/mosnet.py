"""MOSFETs for the column-stack circuits of lecture4/bjtnet.py.

An M item is placed in a column like a BJT: NMOS drain above / source below, PMOS source above / drain below.
`gate` names the node driving the gate (or '0' for a grounded gate); diode=True ties gate and drain.
Device strength: k = k' W/L, given either directly (kw) or as k' (kp) times W/L (wl = (W, L) in um)."""
import math

import schemdraw.elements as elm

from lecture1.draw import _mtext
from lecture4.bjtnet import Q, R, C, Col, BJTCircuit, Src, Load
from common.units import eng_tex, num_tex


class M(Q):
    ROLES = ('G', 'D', 'S')
    LEAD = 0.6
    DIODE_DY = 0.0
    H = 1.5 + LEAD

    def __init__(self, name, kind='nmos', gate=None, kw=None, vt=None, wl=None, kp=None, diode=False, face='left',
                 size_me=False):
        super().__init__(name, kind, base=gate, beta=None, diode=diode, face=face)
        self.kw, self.vt, self.wl, self.kp = kw, vt, wl, kp
        self.size_me = size_me      # W is unknown (to be designed); wl = (placeholder W, L)

    @property
    def k(self):
        """k' W/L in A/V^2."""
        if self.kw is not None:
            return self.kw
        return self.kp * self.wl[0] / self.wl[1]

    @property
    def sym(self):
        return 'n' if self.s > 0 else 'p'

    def element(self):
        e = (elm.NFet() if self.s > 0 else elm.PFet()).theta(0)
        if self.face == 'left':
            e = e.reverse()
        return e, ('gate', 'drain', 'source')

    def tag(self):
        t = _mtext(self.tex)
        if self.wl:
            t += '\n' + (f'?/{self.wl[1]:g}' if self.size_me else f'{self.wl[0]:.3g}/{self.wl[1]:g}')
        return t

    # ---- square law
    def vov(self, i):
        return math.sqrt(2 * i / self.k)

    def id_of(self, vov):
        return self.k / 2 * vov ** 2


def wl_tex(q):
    return f'\\left(\\frac{{W}}{{L}}\\right)_{{{q.name[1:]}}}'


def k_tex(q, value=True):
    """k' W/L of transistor q as LaTeX (symbol, or number)."""
    if not value:
        return f"k'_{q.sym}" + (wl_tex(q) if q.wl else '\\frac{W}{L}')
    return eng_tex(q.k, '\\mathrm{A/V^2}')


def mos_params(circ):
    """Problem-statement sentence with the device parameters (common k'W/L per type, or k' and W/L per device)."""
    ns = [q for q in circ.bjts if q.s > 0]
    ps = [q for q in circ.bjts if q.s < 0]
    out = []
    for grp, sym in ((ns, 'n'), (ps, 'p')):
        if not grp:
            continue
        vt = grp[0].vt
        sign = '' if sym == 'n' else '-'
        if any(q.wl for q in grp):
            out.append(f"$k'_{sym} = {eng_tex(grp[0].kp, chr(92) + 'mathrm{A/V^2}')}$, "
                       f"$V_{{t{sym}}} = {sign}{num_tex(vt)}$\\,V")
        elif len({round(q.k, 12) for q in grp}) == 1:
            out.append(f"$k'_{sym}\\frac{{W}}{{L}} = {eng_tex(grp[0].k, chr(92) + 'mathrm{A/V^2}')}$, "
                       f"$V_{{t{sym}}} = {sign}{num_tex(vt)}$\\,V")
        else:
            out.append(', '.join(f"$k'_{sym}\\frac{{W}}{{L}}\\big|_{{{q.name[1:]}}} = "
                                 f"{eng_tex(q.k, chr(92) + 'mathrm{A/V^2}')}$" for q in grp)
                       + f", $V_{{t{sym}}} = {sign}{num_tex(vt)}$\\,V")
    wl = any(q.wl for q in circ.bjts)
    return ', '.join(out) + (' (W/L next to each transistor)' if wl else '')


__all__ = ['M', 'R', 'C', 'Col', 'BJTCircuit', 'Src', 'Load', 'mos_params', 'k_tex', 'wl_tex']
