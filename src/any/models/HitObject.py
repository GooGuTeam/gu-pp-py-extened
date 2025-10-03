from enum import Enum
from typing import List
from .others import Curve, HitSound, Pos, CurveType

class HitObject:
    pos: Pos
    time: int
    hitsound: int
    is_newcombo: bool
    # 新增音效字段
    hit_sample: str = ""

class Circle(HitObject):
    pass

class Slider(HitObject):
    head_hitsound: int
    tail_hitsound: int
    curves: Curve
    repeat_count: int
    length: int
    # 滑条节点音效相关字段
    edge_hitsounds: List[int] = []
    edge_sets: List[str] = []

class Spinner(HitObject):
    end_time: int