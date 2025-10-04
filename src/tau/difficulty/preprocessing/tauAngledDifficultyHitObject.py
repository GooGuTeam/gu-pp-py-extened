"""
TauAngledDifficultyHitObject类，用于表示角度难度计算中的击打物件
"""

import math
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...objects import AngledTauHitObject, TauHitObject

from .tauDifficultyHitObject import TauDifficultyHitObject


class TauAngledDifficultyHitObject(TauDifficultyHitObject):
    """Tau角度难度击打物件"""
    
    def __init__(self, hit_object: 'AngledTauHitObject', last_object: 'TauHitObject',
                 clock_rate: float, objects: List['TauDifficultyHitObject'], index: int,
                 last_angled: Optional['TauAngledDifficultyHitObject'] = None):
        """
        初始化Tau角度难度击打物件
        
        Args:
            hit_object: 当前角度击打物件
            last_object: 上一个击打物件
            clock_rate: 时钟速率
            objects: 物件列表
            index: 索引
            last_angled: 上一个角度物件
        """
        super().__init__(hit_object, last_object, clock_rate, objects, index)
        
        self.last_angled = last_angled
        
        # 从beatmap获取属性
        self.angle_range = getattr(hit_object, 'angle_range', 0) if hit_object else 0
        self.distance = 0.0
        self.angle_delta = 0.0  # signed difference (current - lastAbsolute)
        self.rhythm_bucket = 0  # will be set based on strain_time
        
        # 滑条相关属性
        self.travel_distance = 0.0
        self.lazy_travel_distance = 0.0
        self.travel_time = 0.0
        
        if (hasattr(hit_object, 'angle') and 
            last_angled is not None and 
            hasattr(last_angled, 'base_object') and
            hasattr(last_angled.base_object, 'angle')):
            offset = 0.0
            
            # 如果上一个物件有偏移角度
            if last_angled.base_object is not None and hasattr(last_angled.base_object, 'get_offset_angle') and callable(getattr(last_angled.base_object, 'get_offset_angle', None)):
                offset += last_angled.base_object.get_offset_angle()
            
            # 计算角度差
            if last_angled.base_object is not None and hasattr(hit_object, 'angle') and hasattr(last_angled.base_object, 'angle'):
                raw_delta = self._get_delta_angle(hit_object.angle, (last_angled.base_object.angle + offset))
                self.angle_delta = raw_delta
                self.distance = abs(raw_delta)
                self.strain_time = max(self.strain_time, self.start_time - last_angled.start_time)
            
            # 如果上一个物件是StrictHardBeat，需要增加距离
            if last_angled.base_object is not None and hasattr(last_angled.base_object, 'range'):
                self.distance += last_angled.base_object.range / 2
        
        # 如果是滑条
        if hasattr(hit_object, 'path') and hit_object.path is not None and hasattr(hit_object.path, 'calculated_distance'):
            self.travel_distance = hit_object.path.calculated_distance
            if hasattr(hit_object.path, 'calculate_lazy_distance'):
                self.lazy_travel_distance = hit_object.path.calculate_lazy_distance(self.angle_range / 2)
            self.travel_time = getattr(hit_object, 'duration', 0) / clock_rate if hasattr(hit_object, 'duration') else 0

        # classify rhythm bucket for complexity usage (thresholds heuristic; can be tuned)
        # buckets: 0: very fast (<120ms), 1: fast (<200ms), 2: medium (<320ms), 3: slow (<500ms), 4: very slow
        st = self.strain_time
        if st < 120:
            self.rhythm_bucket = 0
        elif st < 200:
            self.rhythm_bucket = 1
        elif st < 320:
            self.rhythm_bucket = 2
        elif st < 500:
            self.rhythm_bucket = 3
        else:
            self.rhythm_bucket = 4
    
    def _get_delta_angle(self, a: float, b: float) -> float:
        """
        计算两个角度之间的差值
        
        Args:
            a: 角度a
            b: 角度b
            
        Returns:
            float: 角度差值
        """
        # 使用模运算处理负数情况
        return ((a - b) + 180) % 360 - 180