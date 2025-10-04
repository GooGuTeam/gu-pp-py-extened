from __future__ import annotations
from typing import Sequence, Optional

class SentakkiBeatmap:
    def __init__(self, star_rating: float, max_combo: int, approach_rate: float = 5.0, objects: Optional[Sequence[object]] = None):
        self.star_rating = star_rating
        self.max_combo = max_combo
        self.approach_rate = approach_rate
        self.objects: Sequence[object] = objects or []

__all__ = ["SentakkiBeatmap"]