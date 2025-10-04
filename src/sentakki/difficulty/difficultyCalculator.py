"""Sentakki 难度计算 (初始移植版)

原 C# SentakkiDifficultyCalculator 当前实现：
- 不生成 DifficultyHitObjects / Skills
- 返回 DifficultyAttributes 仅包含 StarRating = BeatmapInfo.StarRating * 1.25, Mods, MaxCombo

因此这里亦保持最小逻辑，并可与项目中其它模式统一接口： calculator.calculate() -> SentakkiDifficultyAttributes
后续若官方添加真实难度算法，可在此扩展。
"""
from __future__ import annotations
from typing import Sequence, Optional
from ..attributes import SentakkiDifficultyAttributes
from ..mods import SentakkiMods
from .beatmap_base import SentakkiBeatmap


class SentakkiDifficultyCalculator:
    def __init__(self, beatmap: SentakkiBeatmap, mods: int = 0):
        self.beatmap = beatmap
        self.mods = SentakkiMods(mods)

    def calculate(self) -> SentakkiDifficultyAttributes:
        clock_rate = self._clock_rate()
        # PR #701: baseSR = beatmapSR * clockRate; inflated *1.25
        # Strict PR#701: StarRating = (beatmap.star_rating * clock_rate) * 1.25
        star = (self.beatmap.star_rating * clock_rate) * 1.25
        # Enhanced skills removed in strict mode; keep fields for backward compatibility (set to 0)
        return SentakkiDifficultyAttributes(
            star_rating=star,
            max_combo=self.beatmap.max_combo,
            mods=[self.mods],
            approach_rate=self._apply_mods_to_ar(self.beatmap.approach_rate),
            clock_rate=clock_rate
        )

    def _apply_mods_to_ar(self, ar: float) -> float:
        return self.mods.apply_ar(ar)

    def _clock_rate(self) -> float:
        rate = 1.0
        if self.mods & (SentakkiMods.DOUBLE_TIME | SentakkiMods.NIGHTCORE):
            rate *= 1.5
        if self.mods & (SentakkiMods.HALF_TIME | SentakkiMods.DAYCORE):
            rate *= 0.75
        return rate

    # Strict mode: prototype skills removed.
