"""
Control point models for tau mode.
"""

from typing import List


class ControlPoint:
    """
    Base class for all control points.
    """
    def __init__(self):
        self.time: float = 0.0


class TimingPoint(ControlPoint):
    """
    Represents a timing point that changes the BPM or offsets of hit objects.
    """
    def __init__(self):
        super().__init__()
        self.beat_length: float = 0.0
        self.time_signature: int = 4


class DifficultyPoint(ControlPoint):
    """
    Represents a difficulty point that changes the speed of hit objects.
    """
    def __init__(self):
        super().__init__()
        self.slider_velocity: float = 1.0
        self.generate_ticks: bool = True


class SamplePoint(ControlPoint):
    """
    Represents a sample point that changes the sample sounds of hit objects.
    """
    def __init__(self):
        super().__init__()
        self.sample_bank: str = "normal"
        self.sample_volume: int = 100
        self.sample_index: int = 0


class EffectPoint(ControlPoint):
    """
    Represents an effect point that changes the effects of hit objects.
    """
    def __init__(self):
        super().__init__()
        self.kiai_mode: bool = False
        self.omit_first_bar_line: bool = False