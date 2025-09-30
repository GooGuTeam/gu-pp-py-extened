from enum import Enum


class Pos:
    x: int
    y: int

class HitSound(int,Enum):
    Normal=0
    Whistle=2
    Finish=4
    Clap=8

class CurveType(str,Enum):
    Bezier="B"
    Catmull_rom="C"
    linear="L"
    perfrct="P"

class Curve:
    type: CurveType
    control_points: list[Pos]