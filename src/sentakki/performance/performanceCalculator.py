"""Sentakki 性能计算 (基于 PR #701 逻辑移植)

公式来源(概述)：
base_pp = ((5 * max(1, SR / 0.0049) - 4)^2) / 100000
length_bonus = 0.95 + (0.3 * min(1, maxCombo/2500) + (maxCombo>2500 ? log10(maxCombo/2500)*0.475 : 0))
value = base_pp * length_bonus
value *= 0.97^miss_count
value *= min((score.maxCombo^0.35)/(maxCombo^0.35), 1)
value *= accuracy^5.5
combo_progress = maxCombo / score.maximumAchievableCombo  (在 PR 中使用 difficulty MaxCombo / achievable)
total = value * combo_progress

本实现:
- score dict 需要字段: accuracy(float 0~1), max_combo(int), statistics.miss(int 可选), maximum_achievable_combo(int 可选)
"""
from dataclasses import dataclass, field
from typing import Dict, Any
from ..attributes import SentakkiDifficultyAttributes
import math

@dataclass
class SentakkiPerformanceAttributes:
    total: float = 0.0
    base_pp: float = 0.0
    length_bonus: float = 0.0


class SentakkiPerformanceCalculator:
    def calculate(self, score: Dict[str, Any], difficulty_attributes: SentakkiDifficultyAttributes) -> SentakkiPerformanceAttributes:
        acc = float(score.get('accuracy', 0.0))
        stats = score.get('statistics', {}) or {}
        count_miss = int(stats.get('miss', 0))
        max_combo = difficulty_attributes.max_combo or 0
        score_combo = int(score.get('max_combo', 0))
        maximum_achievable_combo = int(score.get('maximum_achievable_combo', max_combo if max_combo else score_combo)) or 1

        sr = difficulty_attributes.star_rating
        base_pp = (math.pow((5.0 * max(1.0, sr / 0.0049)) - 4.0, 2.0)) / 100000.0
        length_bonus = 0.95 + (0.3 * min(1.0, max_combo / 2500.0) + (math.log10(max_combo / 2500.0) * 0.475 if max_combo > 2500 else 0.0)) if max_combo > 0 else 0.95
        value = base_pp * length_bonus
        value *= math.pow(0.97, count_miss)
        if max_combo > 0 and score_combo > 0:
            value *= min(math.pow(score_combo, 0.35) / math.pow(max_combo, 0.35), 1.0)
        value *= math.pow(acc, 5.5)
        combo_progress = (max_combo / maximum_achievable_combo) if maximum_achievable_combo > 0 else 1.0
        total = value * combo_progress

        return SentakkiPerformanceAttributes(
            total=total,
            base_pp=base_pp,
            length_bonus=length_bonus,
        )
