from enum import Enum
from .others import Curve, HitSound, Pos,CurveType

class HitObject:
    pos: Pos
    time: int
    hitsound: int
    is_newcombo: bool

class Circle(HitObject):
    pass

class Slider(HitObject):
    head_hitsound: int
    tail_hitsound: int
    curves: Curve
    repeat_count: int
    length: int

class Spinner(HitObject):
    end_time: int

