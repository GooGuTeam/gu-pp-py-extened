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

        # 与上游：固定基础 multiplier 1.12
        multiplier = 1.12

        mods = score.get('mods', 0)

        # 计算各面向（按 upstream 先算再统一聚合）
        aim_value = self._evaluate_aim_performance(context)
        speed_value = self._evaluate_speed_performance(context)
        accuracy_value = self._compute_accuracy(context)
        complexity_value = self._evaluate_complexity_performance(context)
        # 注意：Relax / Autopilot 已在难度层面把对应面向清零，这里不再重复强制归零，保持与上游一致。

        # NoFail 惩罚（不低于 0.90）
        if mods & TauMods.NO_FAIL:
            multiplier *= max(0.90, 1.0 - 0.02 * context.effective_miss_count)

        total_value = math.pow(
            math.pow(max(aim_value, 0.0), 1.1) +
            math.pow(max(accuracy_value, 0.0), 1.1) +
            math.pow(max(speed_value, 0.0), 1.1) +
            math.pow(max(complexity_value, 0.0), 1.1),
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
        # 与上游：基于连击阈值推测 miss + slider 断连（不做 -1 修正）
        combo_based_miss_count = 0.0

        if context.difficulty_attributes.slider_count > 0:
            full_combo_threshold = context.difficulty_attributes.max_combo - 0.1 * context.difficulty_attributes.slider_count
            if context.score_max_combo < full_combo_threshold:
                combo_based_miss_count = full_combo_threshold / max(1.0, context.score_max_combo)

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
        # 上游：再次乘以 length_bonus 与 AR 因子（双 length 奖励）
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
        attrs = context.difficulty_attributes
        raw_speed = attrs.speed_difficulty
        speed_value = math.pow(5.0 * max(1.0, raw_speed / 0.0675) - 4.0, 3.0) / 100000.0

        length_bonus = (
            0.95 + 0.4 * min(1.0, context.total_hits / 2000.0) +
            (math.log10(context.total_hits / 2000.0) * 0.5 if context.total_hits > 2000 else 0.0)
        )
        speed_value *= length_bonus

        # miss 惩罚：speed 使用指数 0.875
        if context.effective_miss_count > 0:
            speed_value *= 0.97 * math.pow(
                1 - math.pow(context.effective_miss_count / context.total_hits, 0.775),
                math.pow(context.effective_miss_count, 0.875)
            )

        # 连击缩放（与上游 getComboScalingFactor 等价实现）
        if attrs.max_combo > 0 and context.score_max_combo > 0:
            combo_factor = min(
                math.pow(context.score_max_combo, 0.8) / math.pow(attrs.max_combo, 0.8),
                1.0
            )
            speed_value *= combo_factor

        # 高 AR 长谱加成（approachRateFactor * length_bonus）
        approach_rate_factor = 0.0
        if attrs.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (attrs.approach_rate - 10.33)
        speed_value *= 1.0 + approach_rate_factor * length_bonus

        # FadeIn 模式（若存在）提升对低 AR 的奖励：暂未实现（无该 mod 标志位）；如需请扩展 TauMods。

        # 精确度与 OD 影响
        speed_value *= (0.95 + math.pow(attrs.overall_difficulty, 2) / 750.0) * math.pow(
            max(context.accuracy, 1e-9),
            (14.5 - max(attrs.overall_difficulty, 8)) / 2
        )

        return speed_value
    
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
        
        # 长度奖励
        length_bonus = (
            0.95 + 0.4 * min(1.0, context.total_hits / 2000.0) +
            (math.log10(context.total_hits / 2000.0) * 0.5 if context.total_hits > 2000 else 0.0)
        )
        complexity_value *= length_bonus

        # miss 惩罚（与上游相同，不带 0.875 指数）
        if context.effective_miss_count > 0:
            complexity_value *= 0.97 * math.pow(
                1 - math.pow(context.effective_miss_count / context.total_hits, 0.775),
                context.effective_miss_count
            )

        # 不乘以 accuracy（上游无该项）
        return complexity_value
    
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