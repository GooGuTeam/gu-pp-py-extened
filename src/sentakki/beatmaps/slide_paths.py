"""Predefined slide path prototypes (approximation of official C# dataset).

Each entry describes a path archetype used during composite slide construction.
This is NOT a geometric implementation yet, only metadata driving:
 - minimum duration eligibility
 - whether it can appear multiple times
 - whether it is a fan path
 - base weight influencing random selection

Future work: attach actual control point sequences / easing curves.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class SlidePathPrototype:
    name: str
    min_duration: int
    weight: int = 1
    allow_multiple: bool = True
    is_fan: bool = False
    # When chosen, if is_fan, progress at which fan animation begins (relative to full slide body duration).
    # If None, converter computes based on accumulated durations before the fan part.
    default_fan_progress: float | None = None


PROTOTYPES: List[SlidePathPrototype] = [
    SlidePathPrototype("linear", min_duration=180, weight=6),
    SlidePathPrototype("circle_cw", min_duration=320, weight=4),
    SlidePathPrototype("circle_ccw", min_duration=320, weight=4),
    SlidePathPrototype("zigzag", min_duration=260, weight=3),
    # Fan paths (only appended when flag enabled & long enough slider)
    SlidePathPrototype("fan", min_duration=480, weight=2, is_fan=True, allow_multiple=False, default_fan_progress=None),
]

__all__ = ["SlidePathPrototype", "PROTOTYPES"]
