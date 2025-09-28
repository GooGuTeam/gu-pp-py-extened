"""
Tau性能计算器，模仿rosu-pp的接口风格
"""

import math
from typing import Dict, Any
from dataclasses import dataclass, field
from ..attributes import TauDifficultyAttributes
from ..mods import TauMods


@dataclass
class TauPerformanceContext:
    """Tau性能计算上下文"""
    score: Dict[str, Any]  # ScoreInfo模拟
    difficulty_attributes: TauDifficultyAttributes
    effective_miss_count: float = 0.0
    
    @property
    def accuracy(self) -> float:
        return self.score.get('accuracy', 0.0)
    
    @property
    def score_max_combo(self) -> int:
        return self.score.get('max_combo', 0)
    
    @property
    def count_great(self) -> int:
        return self.score.get('statistics', {}).get('great', 0)
    
    @property
    def count_ok(self) -> int:
        return self.score.get('statistics', {}).get('ok', 0)
    
    @property
    def count_miss(self) -> int:
        return self.score.get('statistics', {}).get('miss', 0)
    
    @property
    def total_hits(self) -> int:
        return self.count_great + self.count_ok + self.count_miss


@dataclass
class TauPerformanceAttributes:
    """Tau性能属性"""
    aim: float = 0.0
    speed: float = 0.0
    accuracy: float = 0.0
    complexity: float = 0.0
    total: float = 0.0
    effective_miss_count: float = 0.0


class TauPerformanceCalculator:
    """Tau性能计算器"""
    
    def __init__(self):
        """初始化性能计算器"""
        pass
    
    def calculate(self, score: Dict[str, Any], difficulty_attributes: TauDifficultyAttributes) -> TauPerformanceAttributes:
        """
        计算性能值
        
        Args:
            score: 分数信息
            difficulty_attributes: 难度属性
            
        Returns:
            TauPerformanceAttributes: 性能属性
        """
        context = TauPerformanceContext(score, difficulty_attributes)
        context.effective_miss_count = self._calculate_effective_miss_count(context)
        
        # Mod multiplier
        multiplier = 1.12
        
        aim_value = self._evaluate_aim_performance(context)
        speed_value = self._evaluate_speed_performance(context)
        accuracy_value = self._compute_accuracy(context)
        complexity_value = self._evaluate_complexity_performance(context)
        
        # NoFail mod影响
        mods = score.get('mods', 0)
        if mods & TauMods.NO_FAIL:
            multiplier *= max(0.90, 1.0 - 0.02 * context.effective_miss_count)
        
        total_value = math.pow(
            math.pow(aim_value, 1.1) + 
            math.pow(accuracy_value, 1.1) + 
            math.pow(speed_value, 1.1) + 
            math.pow(complexity_value, 1.1),
            1.0 / 1.1
        ) * multiplier
        
        return TauPerformanceAttributes(
            aim=aim_value,
            speed=speed_value,
            accuracy=accuracy_value,
            complexity=complexity_value,
            total=total_value,
            effective_miss_count=context.effective_miss_count
        )
    
    def _compute_accuracy(self, context: TauPerformanceContext) -> float:
        """
        计算准确度性能值
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 准确度性能值
        """
        # Relax mod影响
        if context.score.get('mods', 0) & TauMods.RELAX:
            return 0.0
        
        # 这个百分比只考虑任何值的节拍 - 在计算的这部分中，我们专注于击中时间窗口。
        better_accuracy_percentage = 0.0
        amount_hit_objects_with_accuracy = context.difficulty_attributes.notes_count
        
        if amount_hit_objects_with_accuracy > 0:
            better_accuracy_percentage = (
                (context.count_great - (context.total_hits - amount_hit_objects_with_accuracy)) * 3 + 
                context.count_ok
            ) / (amount_hit_objects_with_accuracy * 3)
        else:
            better_accuracy_percentage = 0
        
        # 可能通过此公式达到负准确度。将其限制为零 - 零分。
        if better_accuracy_percentage < 0:
            better_accuracy_percentage = 0
        
        # 来自测试的许多任意值。
        # 考虑以概率方式使用完美准确度的推导 - 假设正态分布。
        accuracy_value = math.pow(1.52163, context.difficulty_attributes.overall_difficulty) * \
                         math.pow(better_accuracy_percentage, 24) * 2.83
        
        # 对于许多（超过1,000个）hitcircles的奖励 - 很难长期保持良好的准确性。
        accuracy_value *= min(1.15, math.pow(amount_hit_objects_with_accuracy / 1000.0, 0.3))
        
        return accuracy_value
    
    def _calculate_effective_miss_count(self, context: TauPerformanceContext) -> float:
        """
        计算有效的失误计数
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 有效失误计数
        """
        # 从连击猜测失误数 + 滑条断连数
        combo_based_miss_count = 0.0
        
        if context.difficulty_attributes.slider_count > 0:
            full_combo_threshold = context.difficulty_attributes.max_combo - 0.1 * context.difficulty_attributes.slider_count
            if context.score_max_combo < full_combo_threshold:
                combo_based_miss_count = full_combo_threshold / max(1.0, context.score_max_combo)
        
        # 限制失误计数，因为它来自连击，可能高于总击打数，这会破坏一些计算
        combo_based_miss_count = min(combo_based_miss_count, context.total_hits)
        
        return max(context.count_miss, combo_based_miss_count)
    
    def _evaluate_aim_performance(self, context: TauPerformanceContext) -> float:
        """
        计算瞄准性能值
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 瞄准性能值
        """
        raw_aim = context.difficulty_attributes.aim_difficulty
        aim_value = math.pow(5.0 * max(1.0, raw_aim / 0.0675) - 4.0, 3.0) / 100000.0
        
        # 对于超过2,000个击打物件的谱面，会增加长度奖励。
        length_bonus = (
            0.95 + 0.4 * min(1.0, context.total_hits / 2000.0) + 
            (math.log10(context.total_hits / 2000.0) * 0.5 if context.total_hits > 2000 else 0.0)
        )
        aim_value *= length_bonus
        
        aim_value *= self._compute_approach_rate_factor(context) * length_bonus
        
        # 通过评估相对于总物件数的失误数来惩罚失误。默认任何数量的失误都会减少3%。
        if context.effective_miss_count > 0:
            aim_value *= 0.97 * math.pow(1 - math.pow(context.effective_miss_count / context.total_hits, 0.775), 
                                         context.effective_miss_count)
        
        if context.difficulty_attributes.slider_count > 0:
            aim_value *= self._compute_slider_nerf(context)
        
        return aim_value * context.accuracy
    
    def _evaluate_speed_performance(self, context: TauPerformanceContext) -> float:
        """
        计算速度性能值
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 速度性能值
        """
        raw_speed = context.difficulty_attributes.speed_difficulty
        speed_value = math.pow(5.0 * max(1.0, raw_speed / 0.0675) - 4.0, 3.0) / 100000.0
        
        # 对于超过2,000个击打物件的谱面，会增加长度奖励。
        length_bonus = (
            0.95 + 0.4 * min(1.0, context.total_hits / 2000.0) + 
            (math.log10(context.total_hits / 2000.0) * 0.5 if context.total_hits > 2000 else 0.0)
        )
        speed_value *= length_bonus
        
        # 通过评估相对于总物件数的失误数来惩罚失误。默认任何数量的失误都会减少3%。
        if context.effective_miss_count > 0:
            speed_value *= 0.97 * math.pow(1 - math.pow(context.effective_miss_count / context.total_hits, 0.775), 
                                           context.effective_miss_count)
        
        return speed_value * context.accuracy
    
    def _evaluate_complexity_performance(self, context: TauPerformanceContext) -> float:
        """
        计算复杂度性能值
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 复杂度性能值
        """
        raw_complexity = context.difficulty_attributes.complexity_difficulty
        complexity_value = math.pow(5.0 * max(1.0, raw_complexity / 0.0675) - 4.0, 3.0) / 100000.0
        
        # 对于超过2,000个击打物件的谱面，会增加长度奖励。
        length_bonus = (
            0.95 + 0.4 * min(1.0, context.total_hits / 2000.0) + 
            (math.log10(context.total_hits / 2000.0) * 0.5 if context.total_hits > 2000 else 0.0)
        )
        complexity_value *= length_bonus
        
        # 通过评估相对于总物件数的失误数来惩罚失误。默认任何数量的失误都会减少3%。
        if context.effective_miss_count > 0:
            complexity_value *= 0.97 * math.pow(1 - math.pow(context.effective_miss_count / context.total_hits, 0.775), 
                                                context.effective_miss_count)
        
        return complexity_value * context.accuracy
    
    def _compute_approach_rate_factor(self, context: TauPerformanceContext) -> float:
        """
        基于谱面的接近速率计算额外因子
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 接近速率因子
        """
        attributes = context.difficulty_attributes
        approach_rate_factor = 0.0
        
        if attributes.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (attributes.approach_rate - 10.33)
        elif attributes.approach_rate < 8.0:
            approach_rate_factor = 0.1 * (8.0 - attributes.approach_rate)
        
        return 1.0 + approach_rate_factor
    
    def _compute_slider_nerf(self, context: TauPerformanceContext) -> float:
        """
        估计并增强谱面中15%的滑条，如果玩家正确完成了它们。
        
        Args:
            context: 性能计算上下文
            
        Returns:
            float: 滑条削弱因子
        """
        attributes = context.difficulty_attributes
        
        # 我们假设谱面中15%的滑条是困难的，因为从性能计算器中无法判断。
        estimate_difficult_sliders = attributes.slider_count * 0.15
        estimate_slider_ends_dropped = max(0, min(
            context.count_ok + context.count_miss,
            attributes.max_combo - context.score_max_combo,
            estimate_difficult_sliders
        ))
        
        return (1 - attributes.slider_factor) * math.pow(1 - estimate_slider_ends_dropped / estimate_difficult_sliders, 3) + attributes.slider_factor