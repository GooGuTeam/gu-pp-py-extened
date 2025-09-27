"""
Hit object models for tau mode.
"""

from enum import Enum
from typing import List


class HitObjectType(Enum):
    """
    Types of hit objects in tau mode.
    """
    BEAT = 1
    HARD_BEAT = 2
    SLIDER = 3
    SLIDER_HEAD = 4
    SLIDER_REPEAT = 5
    SLIDER_TICK = 6


class HitObject:
    """
    Base class for all hit objects in tau mode.
    """
    def __init__(self):
        self.start_time: float = 0.0
        self.angle: float = 0.0
        self.offset_angle: float = 0.0
        self.combo_index: int = 0
        self.combo_color_index: int = 0
        self.combo_increase: int = 1
        self.type: HitObjectType = HitObjectType.BEAT

    def __str__(self):
        return f"{self.type.name} at {self.start_time}"


class Beat(HitObject):
    """
    A beat hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.BEAT


class HardBeat(HitObject):
    """
    A hard beat hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.HARD_BEAT


class Slider(HitObject):
    """
    A slider hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.SLIDER
        self.end_time: float = 0.0
        self.duration: float = 0.0
        self.repeats: int = 0
        self.distance: float = 0.0
        self.velocity: float = 0.0
        self.tick_distance: float = 0.0
        self.ticks: List[float] = []
        self.repeat_points: List[float] = []


class SliderHead(HitObject):
    """
    A slider head hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.SLIDER_HEAD


class SliderRepeat(HitObject):
    """
    A slider repeat hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.SLIDER_REPEAT


class SliderTick(HitObject):
    """
    A slider tick hit object.
    """
    def __init__(self):
        super().__init__()
        self.type = HitObjectType.SLIDER_TICK