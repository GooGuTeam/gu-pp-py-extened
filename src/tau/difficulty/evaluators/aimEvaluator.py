"""
AimEvaluator类，用于评估瞄准难度
"""

import math
from typing import List, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from ..preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject


class AimEvaluator:
    """瞄准评估器"""
    
    SLIDER_MULTIPLIER = 1.2
    
    @staticmethod
    def evaluate_difficulty(current: 'TauAngledDifficultyHitObject', 
                          last: 'TauAngledDifficultyHitObject', 
                          allowed_hit_objects: List[Type]) -> float:
        """
        评估难度
        
        Args:
            current: 当前角度难度击打物件
            last: 上一个角度难度击打物件
            allowed_hit_objects: 允许的击打物件类型列表
            
        Returns:
            float: 难度值
        """
        velocity = AimEvaluator._calculate_velocity(current.distance, current.strain_time)
        
        # 检查是否允许Slider类型但上一个物件不是Slider
        slider_allowed = any(hasattr(t, '__name__') and 'Slider' in t.__name__ for t in allowed_hit_objects)
        last_is_not_slider = not (hasattr(last.base_object, '__class__') and 
                                 hasattr(last.base_object.__class__, '__name__') and
                                 'Slider' in last.base_object.__class__.__name__)
        
        if slider_allowed and last_is_not_slider:
            return velocity
        
        # Slider计算
        travel_velocity = AimEvaluator._calculate_velocity(last.lazy_travel_distance, last.travel_time)
        movement_velocity = AimEvaluator._calculate_velocity(current.distance, current.strain_time)
        
        velocity = max(velocity, movement_velocity + travel_velocity)
        velocity += AimEvaluator._calculate_velocity(last.lazy_travel_distance, last.travel_time) * AimEvaluator.SLIDER_MULTIPLIER
        
        return velocity
    
    @staticmethod
    def _calculate_velocity(distance: float, time: float) -> float:
        """
        计算速度
        https://www.desmos.com/calculator/5yu0ov3zka
        
        Args:
            distance: 距离
            time: 时间
            
        Returns:
            float: 速度值
        """
        return distance / (math.pow((math.pow(time, 1.4) - 77) / 100, 2) * 0.1 + 25)