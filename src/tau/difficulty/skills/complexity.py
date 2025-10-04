"""
Complexity技能类，用于计算复杂度难度
"""

import math
from typing import List, Type, Any
from .tauStrainSkill import TauStrainSkill
from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from ...mods import TauMods
from ..evaluators.complexityEvaluator import ComplexityEvaluator


class Complexity(TauStrainSkill):
    """Complexity 技能（使用持续状态的 ComplexityEvaluator）。"""

    # 近似官方参数
    skill_multiplier = 60.0
    strain_decay_base = 0.35
    reduced_section_count = 10  # 继承 TauStrainSkill 的机制

    def __init__(self, mods: TauMods):
        super().__init__(mods)
        self._evaluator = ComplexityEvaluator()

    def strain_value_of(self, current: TauDifficultyHitObject) -> float:  # type: ignore[override]
        return self._evaluator.evaluate_difficulty(current)