"""Strict PR #701 Performance (PP) implementation.

Formula (mirrors placeholders in PR #701):
base_pp = ((5 * max(1, SR / 0.0049) - 4)^2) / 100000
length_bonus = 0.95 + (0.3 * min(1, maxCombo/2500) + (maxCombo>2500 ? log10(maxCombo/2500)*0.475 : 0))
value = base_pp * length_bonus
value *= 0.97^miss_count
value *= min((score.maxCombo^0.35)/(maxCombo^0.35), 1)
value *= accuracy^5.5
combo_progress = maxCombo / score.maximumAchievableCombo
total = value * combo_progress
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import math
from .difficulty import SentakkiPR701DifficultyAttributes

@dataclass
class SentakkiPR701PerformanceAttributes:
    total: float = 0.0
    base_pp: float = 0.0
    length_bonus: float = 0.0

class SentakkiPR701PerformanceCalculator:
    def calculate(self, score: Dict[str, Any], difficulty: SentakkiPR701DifficultyAttributes) -> SentakkiPR701PerformanceAttributes:
        acc = float(score.get('accuracy', 0.0))
        # clamp accuracy to [0,1] for robustness (safeguard; PR 原始逻辑隐式假定合法)
        if acc < 0: acc = 0.0
        if acc > 1: acc = 1.0
        stats = score.get('statistics', {}) or {}
        count_miss = int(stats.get('miss', 0))
        max_combo = int(difficulty.max_combo or 0)
        score_combo = int(score.get('max_combo', 0))
        maximum_achievable_combo = int(score.get('maximum_achievable_combo', max_combo if max_combo else score_combo)) or 1

        sr = float(difficulty.star_rating)
        base_pp = (math.pow((5.0 * max(1.0, sr / 0.0049)) - 4.0, 2.0)) / 100000.0
        length_bonus = 0.95 + (0.3 * min(1.0, max_combo / 2500.0) + (math.log10(max_combo / 2500.0) * 0.475 if max_combo > 2500 else 0.0)) if max_combo > 0 else 0.95
        value = base_pp * length_bonus
        value *= math.pow(0.97, count_miss)
        if max_combo > 0 and score_combo > 0:
            value *= min(math.pow(score_combo, 0.35) / math.pow(max_combo, 0.35), 1.0)
        value *= math.pow(acc, 5.5)
        combo_progress = (max_combo / maximum_achievable_combo) if maximum_achievable_combo > 0 else 1.0
        total = value * combo_progress
        return SentakkiPR701PerformanceAttributes(total=total, base_pp=base_pp, length_bonus=length_bonus)

__all__ = ['SentakkiPR701PerformanceCalculator','SentakkiPR701PerformanceAttributes']
