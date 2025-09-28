"""
TauDifficultyHitObject类，用于表示难度计算中的击打物件
"""

import math
from typing import List, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...objects import TauHitObject


class TauDifficultyHitObject:
    """Tau难度击打物件"""
    
    MIN_DELTA_TIME = 25  # 最小时间差为25ms
    
    def __init__(self, hit_object: 'TauHitObject', last_object: 'TauHitObject', 
                 clock_rate: float, objects: List['TauDifficultyHitObject'], index: int):
        """
        初始化Tau难度击打物件
        
        Args:
            hit_object: 当前击打物件
            last_object: 上一个击打物件
            clock_rate: 时钟速率
            objects: 物件列表
            index: 索引
        """
        self.base_object = hit_object
        self.last_object = last_object
        self.clock_rate = clock_rate
        self.objects = objects
        self.index = index
        
        # 计算时间差
        self.start_time = hit_object.start_time
        self.delta_time = (hit_object.start_time - last_object.start_time) / clock_rate
        
        # 至少25ms的时间差，防止同时物件导致难度计算异常
        self.strain_time = max(self.delta_time, self.MIN_DELTA_TIME)
    
    def previous(self, backwards_index: int) -> 'Optional[TauDifficultyHitObject]':
        """
        获取前一个物件
        
        Args:
            backwards_index: 向前的索引
            
        Returns:
            Optional[TauDifficultyHitObject]: 前一个物件或 None
        """
        try:
            target_index = self.index - backwards_index
            if target_index < 0:
                return None
            return self.objects[target_index]
        except IndexError:
            return None