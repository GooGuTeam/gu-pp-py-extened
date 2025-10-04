"""Strict PR #701 Difficulty implementation.

Reference behavior (C# sentakki PR #701):
  StarRating = (BeatmapInfo.StarRating * clockRate) * 1.25
No additional skill calculations or strain systems. Only returns star, mods and max combo metadata.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Any
from ..mods import SentakkiMods

@dataclass
class SentakkiPR701DifficultyAttributes:
    star_rating: float = 0.0
    max_combo: int = 0
    mods: List[Any] = field(default_factory=list)
    clock_rate: float = 1.0

class SentakkiPR701DifficultyCalculator:
    def __init__(self, beatmap, mods: int = 0):
        """beatmap 需要至少提供: star_rating, max_combo
        若 beatmap 无 star_rating, 需由调用方预先写入(官方 PR #701 假定已有)。
        """
        self.beatmap = beatmap
        self.mods = SentakkiMods(mods)

    def calculate(self) -> SentakkiPR701DifficultyAttributes:
        clock_rate = self._clock_rate()
        base_star = float(getattr(self.beatmap, 'star_rating', 0.0))
        star = base_star * clock_rate * 1.25
        return SentakkiPR701DifficultyAttributes(
            star_rating=star,
            max_combo=int(getattr(self.beatmap, 'max_combo', 0)),
            mods=[self.mods],
            clock_rate=clock_rate
        )

    def _clock_rate(self) -> float:
        rate = 1.0
        if self.mods & (SentakkiMods.DOUBLE_TIME | SentakkiMods.NIGHTCORE):
            rate *= 1.5
        if self.mods & (SentakkiMods.HALF_TIME | SentakkiMods.DAYCORE):
            rate *= 0.75
        return rate

__all__ = ['SentakkiPR701DifficultyAttributes','SentakkiPR701DifficultyCalculator']
