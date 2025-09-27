"""
ComplexityEvaluator类，用于评估复杂度难度
"""

import math
from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject


class ComplexityEvaluator:
    """复杂度评估器"""
    
    # 历史记录最大长度
    MONO_HISTORY_MAX_LENGTH = 5
    
    def __init__(self):
        """初始化复杂度评估器"""
        # 存储最近mono模式长度的队列，最新的值在队列末尾
        self.mono_history = deque(maxlen=ComplexityEvaluator.MONO_HISTORY_MAX_LENGTH)
        
        # 上一个击打物件的类型
        self.previous_hit_type: Optional['HitType'] = None
        
        # 当前mono模式的长度
        self.current_mono_length = 0
    
    @staticmethod
    def evaluate_difficulty(current: 'TauDifficultyHitObject') -> float:
        """
        评估难度
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 难度值
        """
        evaluator = ComplexityEvaluator()
        return evaluator._evaluate(current)
    
    def _evaluate(self, current: 'TauDifficultyHitObject') -> float:
        """
        评估难度（内部方法）
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 难度值
        """
        if current.delta_time >= 1000:
            # 长时间间隔，重置历史记录
            self.mono_history.clear()
            
            current_hit = current.base_object
            self.current_mono_length = 1 if current_hit else 0
            self.previous_hit_type = self._get_hit_type(current)
        
        object_strain = 0.0
        
        current_hit_type = self._get_hit_type(current)
        if (self.previous_hit_type is not None and 
            current_hit_type != self.previous_hit_type):
            # 击打类型发生变化
            object_strain = 1.0
            
            # 检查历史记录长度
            if len(self.mono_history) < 2:
                object_strain = 0.0
            elif (self.mono_history[-1] + self.current_mono_length) % 2 == 0:
                # 模式检查
                object_strain = 0.0
            
            # 应用重复惩罚
            object_strain *= self._repetition_penalties()
            self.current_mono_length = 1
        else:
            # 击打类型相同，增加当前mono长度
            self.current_mono_length += 1
        
        self.previous_hit_type = current_hit_type
        return object_strain
    
    def _repetition_penalties(self) -> float:
        """
        应用重复模式惩罚
        
        Returns:
            float: 惩罚因子
        """
        MOST_RECENT_PATTERNS_TO_COMPARE = 2
        penalty = 1.0
        
        self.mono_history.append(self.current_mono_length)
        
        # 检查历史模式是否重复
        for start in range(len(self.mono_history) - MOST_RECENT_PATTERNS_TO_COMPARE - 1, -1, -1):
            if self._is_same_pattern(start, MOST_RECENT_PATTERNS_TO_COMPARE):
                notes_since = sum(self.mono_history[i] for i in range(start, len(self.mono_history)))
                penalty *= self._repetition_penalty(notes_since)
                break
        
        return penalty
    
    def _is_same_pattern(self, start: int, most_recent_patterns_to_compare: int) -> bool:
        """
        检查最近的模式是否在历史中重复
        
        Args:
            start: 起始索引
            most_recent_patterns_to_compare: 要比较的最近模式数量
            
        Returns:
            bool: 是否相同模式
        """
        for i in range(most_recent_patterns_to_compare):
            if (self.mono_history[start + i] != 
                self.mono_history[len(self.mono_history) - most_recent_patterns_to_compare + i]):
                return False
        return True
    
    def _repetition_penalty(self, notes_since: int) -> float:
        """
        计算模式重复的应变惩罚
        
        Args:
            notes_since: 自上次重复模式以来的note数量
            
        Returns:
            float: 惩罚值
        """
        return min(1.0, 0.032 * notes_since)
    
    def _get_hit_type(self, hit_object: 'TauDifficultyHitObject') -> 'HitType':
        """
        获取击打物件类型
        
        Args:
            hit_object: 难度击打物件
            
        Returns:
            HitType: 击打类型
        """
        from ...objects import StrictHardBeat, SliderHardBeat, AngledTauHitObject, Slider
        
        base_object = hit_object.base_object
        
        # 检查是否为StrictHardBeat
        if isinstance(base_object, StrictHardBeat):
            return HitType.HARD_BEAT

        # 检查嵌套物件是否包含SliderHardBeat
        if isinstance(base_object, Slider) and hasattr(base_object, 'nested_hit_objects') and base_object.nested_hit_objects:
            if isinstance(base_object.nested_hit_objects[0], SliderHardBeat):
                return HitType.HARD_BEAT

        # 检查是否为角度物件
        if isinstance(base_object, AngledTauHitObject):
            return HitType.ANGLED

        return HitType.HARD_BEAT


class HitType(Enum):
    """击打类型枚举"""
    ANGLED = "Angled"
    HARD_BEAT = "HardBeat"