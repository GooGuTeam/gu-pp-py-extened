"""
Beatmap model for tau mode.
"""

from typing import List, Optional
from .hit_object import HitObject
from .control_point import ControlPointInfo


class Beatmap:
    """
    Represents a beatmap in tau mode.
    """
    def __init__(self):
        self.hit_objects: List[HitObject] = []
        self.control_points = ControlPointInfo()
        self.circle_size: float = 0.0
        self.hp_drain_rate: float = 0.0
        self.overall_difficulty: float = 0.0
        self.approach_rate: float = 0.0
        self.slider_multiplier: float = 0.0
        self.slider_tick_rate: float = 0.0
        self.stack_leniency: float = 0.0
        self.version: int = 0
        self.ar_ns: float = 0.0  # Approach rate in milliseconds

    def max_combo(self) -> int:
        """
        Calculate the maximum combo of this beatmap.
        """
        combo = 0
        for obj in self.hit_objects:
            combo += obj.combo_increase
        return combo


class ControlPointInfo:
    """
    Holds information about control points in a beatmap.
    """
    def __init__(self):
        self.timing_points = []
        self.difficulty_points = []
        self.sample_points = []
        self.effect_points = []