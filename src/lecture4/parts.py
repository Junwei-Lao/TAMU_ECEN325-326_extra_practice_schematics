"""Small builders for the column stacks used by the Lecture-4 problem sets."""
from .bjtnet import R, C, Q, Col


def div(r1, v1, node, r2, v2, top, bot, gap=3.2):
    """Base divider: top rail -r1- node -r2- bottom rail."""
    return Col([R(r1, v1), node, R(r2, v2)], top=top, bottom=bot, gap=gap)


def ce_npn(q, base, rc, vrc, re, vre, top, bot, c=None, e=None, beta=100, face='left', gap=4.2):
    st = []
    st += [R(rc, vrc)] if rc else []
    st += [c] if c else []
    st += [Q(q, 'npn', base=base, beta=beta, face=face)]
    st += [e] if e else []
    st += [re if not isinstance(re, str) else R(re, vre)] if re else []
    return Col(st, top=top, bottom=bot, gap=gap)


def ce_pnp(q, base, re, vre, rc, vrc, top, bot, c=None, e=None, beta=100, face='left', gap=4.2):
    st = []
    st += [re if not isinstance(re, str) else R(re, vre)] if re else []
    st += [e] if e else []
    st += [Q(q, 'pnp', base=base, beta=beta, face=face)]
    st += [c] if c else []
    st += [R(rc, vrc)] if rc else []
    return Col(st, top=top, bottom=bot, gap=gap)
