from enum import Enum


class Pos:
    x: float
    y: float

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Pos(x={self.x}, y={self.y})"

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