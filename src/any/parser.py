from any.models.HitObject import HitObject
from any.models.TimePoint import TimePoint
from typing import List


class OsuBeatmap:

    # Difficulty settings
    cs: float = 0.0
    ar: float = 0.0
    od: float = 0.0
    hp: float = 0.0
    slider_multiplier: float = 0.0
    slider_tick_rate: float = 0.0
    
    # Timing and hit objects
    timing_points: List[TimePoint]
    
    hit_objects: List[HitObject]

    # Derived properties
    bpm: int = -1
    total_hits: int = 0
    play_time: float = 0.0
    drain_time: float = 0.0
    ncircles: int = 0
    nsliders: int = 0
    nspinners: int = 0