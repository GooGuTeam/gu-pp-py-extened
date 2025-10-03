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
    """Complexity技能类"""
    
    def __init__(self, mods: TauMods):
        """
        初始化Complexity技能
        
        Args:
            mods: 应用的mods
        """
        super().__init__(mods)
        # Use a persistent ComplexityEvaluator so history (mono patterns) is tracked across objects
        self._evaluator = ComplexityEvaluator()
        self.skill_multiplier = 60
        self.strain_decay_base = 0.35
    
    def strain_value_of(self, current: TauDifficultyHitObject) -> float:
        """
        计算当前物件的应变值
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 应变值
        """
        # Delegate to the persistent evaluator so mono history and repetition penalties accumulate
        return self._evaluator._evaluate(current)