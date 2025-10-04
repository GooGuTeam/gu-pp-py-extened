from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
"""
Aim技能类，用于计算瞄准难度
"""

import math
from typing import List, Type
from .tauStrainSkill import BaseStrainSkill
from ..preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject
from ...mods import TauMods
from ..evaluators.aimEvaluator import AimEvaluator


class Aim(BaseStrainSkill):
    """Aim技能类"""
    
    def __init__(self, mods: TauMods, allowed_hit_objects: List[Type]):
        """
        初始化Aim技能
        
        Args:
            mods: 应用的mods
            allowed_hit_objects: 允许的击打物件类型列表
        """
        super().__init__(mods)
        self.allowed_hit_objects = allowed_hit_objects
        self.skill_multiplier = 7.4
        self.strain_decay_base = 0.25  # decay base (<1 表示衰减)
    
    def strain_value_of(self, current: 'TauDifficultyHitObject') -> float:
        """
        计算当前物件的应变值
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 应变值
        """
        # 检查是否为TauAngledDifficultyHitObject且有前一个物件
        if current.index <= 1 or not isinstance(current, TauAngledDifficultyHitObject) or current.last_angled is None:
            return 0
        
        # 如果距离小于角度范围，则返回0
        if current.distance < current.angle_range:
            return 0
        
        return AimEvaluator.evaluate_difficulty(current, current.last_angled, self.allowed_hit_objects)
    
    def _evaluate_difficulty(self, current: TauAngledDifficultyHitObject, last: TauAngledDifficultyHitObject) -> float:
        """
        评估难度
        
        Args:
            current: 当前角度难度击打物件
            last: 上一个角度难度击打物件
            
        Returns:
            float: 难度值
        """
        velocity = self._calculate_velocity(current.distance, current.strain_time)

        # Determine if sliders are allowed by checking class names in allowed_hit_objects
        slider_allowed = any(hasattr(t, '__name__') and 'Slider' in t.__name__ for t in self.allowed_hit_objects)

        # Check whether the last object's base_object is a slider by class name
        last_is_not_slider = True
        try:
            last_base = getattr(last, 'base_object', None)
            if last_base is not None and hasattr(last_base, '__class__') and hasattr(last_base.__class__, '__name__'):
                last_is_not_slider = not ('Slider' in last_base.__class__.__name__)
        except Exception:
            last_is_not_slider = True

        if slider_allowed and last_is_not_slider:
            return velocity
        
        # Slider计算
        travel_velocity = self._calculate_velocity(last.lazy_travel_distance, last.travel_time)
        movement_velocity = self._calculate_velocity(current.distance, current.strain_time)
        
        velocity = max(velocity, movement_velocity + travel_velocity)
        velocity += self._calculate_velocity(last.lazy_travel_distance, last.travel_time) * 1.2  # slider_multiplier
        
        return velocity
    
    def _calculate_velocity(self, distance: float, time: float) -> float:
        """
        计算速度
        
        Args:
            distance: 距离
            time: 时间
            
        Returns:
            float: 速度值
        """
        # https://www.desmos.com/calculator/5yu0ov3zka
        return distance / (math.pow((math.pow(time, 1.4) - 77) / 100, 2) * 0.1 + 25)