"""Everything a problem file needs, in one import."""
from .ladder import R, C, L, Ser, Par, Src, Series, Shunt, Tap, Out, VCVS, VCCS  # noqa: F401
from .narrative import Sine  # noqa: F401


class Prob:
    def __init__(self, level, items, vin, note=''):
        assert level in ('easy', 'medium', 'hard')
        self.level, self.items, self.vin, self.note = level, items, vin, note
