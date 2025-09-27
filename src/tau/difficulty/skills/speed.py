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
    """Speed技能类"""
    
    def __init__(self, mods: TauMods, hit_window_great: float):
        """
        初始化Speed技能
        
        Args:
            mods: 应用的mods
            hit_window_great: Great判定窗口大小
        """
        super().__init__(mods)
        self.hit_window_great = hit_window_great
        self.skill_multiplier = 515
        self.strain_decay_base = 0.3
        
        self.current_strain = 0.0
        self.current_rhythm = 0.0
    
    def process(self, hit_object: TauDifficultyHitObject):
        """
        处理击打物件
        
        Args:
            hit_object: 难度击打物件
        """
        self.current_strain *= self._strain_decay(hit_object.delta_time)
        self.current_strain += SpeedEvaluator.evaluate_difficulty(hit_object, self.hit_window_great) * self.skill_multiplier
        
        self.current_rhythm = SpeedEvaluator.evaluate_rhythm_difficulty(hit_object, self.hit_window_great)
        
        # 将组合应变值存储到物件中供后续使用
        strain_value = self.current_strain * self.current_rhythm
        self.current_section_peak = max(strain_value, self.current_section_peak)
        
        # 检查是否是新的段落
        next_time = hit_object.start_time + hit_object.delta_time
        if self._is_new_section(next_time):
            self._save_current_peak()
            self._start_new_section_from(next_time)
    
    def _calculate_initial_strain(self, time: float, current: TauDifficultyHitObject) -> float:
        """
        计算初始应变值
        
        Args:
            time: 时间
            current: 当前难度击打物件
        Returns:
            float: 初始应变值
        """
        prev = current.previous(0)
        prev_start_time = prev.start_time if prev is not None else 0
        return (self.current_strain * self.current_rhythm) * self._strain_decay(time - prev_start_time)
    
    def strain_value_of(self, current: TauDifficultyHitObject) -> float:
        """
        计算当前物件的应变值
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 应变值
        """
        # Speed技能在process方法中处理应变值计算
        # 这里返回0，因为实际计算在process中完成
        return 0