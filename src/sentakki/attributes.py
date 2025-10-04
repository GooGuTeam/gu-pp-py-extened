"""Sentakki 难度属性

参考 Tau / rosu-pp 的接口风格，并映射 C# SentakkiDifficultyCalculator 的最小实现：
C# 版本当前逻辑： StarRating = beatmap.BeatmapInfo.StarRating * 1.25f
尚未提供其它技能细分，这里只保留 star 与基础元数据。
"""
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class SentakkiDifficultyAttributes:
    star_rating: float = 0.0
    max_combo: int = 0
    mods: List[Any] = field(default_factory=list)
    approach_rate: float = 5.0  # 先占位
    clock_rate: float = 1.0
    # Prototype skill outputs

    # 预留：后续若加入技能难度可扩展

