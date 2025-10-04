"""
Speed技能类，用于计算速度难度
"""

import math
from typing import List, Type
from .tauStrainSkill import TauStrainSkill
from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from ..preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject
from ...mods import TauMods
from ..evaluators.speedEvaluator import SpeedEvaluator


class Speed(TauStrainSkill):
    """Speed技能类 (使用 TauStrainSkill 的峰值削减逻辑)。"""
    
    def __init__(self, mods: TauMods, hit_window_great: float):
        """
        初始化Speed技能
        
        Args:
            mods: 应用的mods
            hit_window_great: Great判定窗口大小
        """
        super().__init__(mods)
        self.hit_window_great = hit_window_great
        # 依据 C# Speed.cs: skill_multiplier=515, strain_decay_base=0.3,
        # ReducedSectionCount=5, DifficultyMultiplier=1.37
        self.skill_multiplier = 515.0
        self.strain_decay_base = 0.3
        self.reduced_section_count = 5
        self.difficulty_multiplier_final = 1.37

    def strain_value_of(self, current: TauDifficultyHitObject) -> float:  # type: ignore[override]
        # 将节奏复杂度作为 multiplier 融合到单物件应变值中
        base = SpeedEvaluator.evaluate_difficulty(current, self.hit_window_great)
        rhythm = SpeedEvaluator.evaluate_rhythm_difficulty(current, self.hit_window_great)
        return base * rhythm