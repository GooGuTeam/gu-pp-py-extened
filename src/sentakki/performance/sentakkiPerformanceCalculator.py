"""
Sentakki性能计算器，按照官方实现
按照PR #701 (https://github.com/LumpBloom7/sentakki/pull/701) 实现
"""

import math
from typing import Dict
from ..difficulty.difficultyCalculator import SentakkiDifficultyAttributes


class SentakkiPerformanceCalculator:
    """Sentakki性能计算器"""
    
    def __init__(self):
        """初始化性能计算器"""
        pass
    
    def calculate(self, score_info: Dict, difficulty_attributes: SentakkiDifficultyAttributes) -> Dict:
        """
        根据分数和难度属性计算性能值(PP)
        
        Args:
            score_info: 分数信息字典，包含'accuracy', 'count_miss', 'max_combo', 'achievable_combo'等键
            difficulty_attributes: 难度属性对象
            
        Returns:
            Dict: 包含性能计算结果的字典，包括total, base_pp, length_bonus等
        """
        # 从分数信息中获取所需数据
        accuracy = score_info.get('accuracy', 0.0) / 100.0  # 转换为小数形式
        count_miss = score_info.get('count_miss', 0)
        score_max_combo = score_info.get('max_combo', 0)
        
        # 从难度属性中获取数据
        star_rating = difficulty_attributes.star_rating
        beatmap_max_combo = difficulty_attributes.max_combo
        
        # 1. 计算基础PP值
        base_value = math.pow((5.0 * max(1.0, star_rating / 0.0049)) - 4.0, 2.0) / 100000.0
        
        # 2. 计算长度奖励
        length_bonus = 0.95 + (0.3 * min(1.0, beatmap_max_combo / 2500.0))
        if beatmap_max_combo > 2500:
            length_bonus += math.log10(beatmap_max_combo / 2500.0) * 0.475
        
        # 3. 应用长度奖励到基础值
        value = base_value * length_bonus
        
        # 4. 应用Miss惩罚
        value *= math.pow(0.97, count_miss)
        
        # 5. 应用连击惩罚（如果谱面有连击）
        if beatmap_max_combo > 0:
            value *= min(
                math.pow(score_max_combo, 0.35) / math.pow(beatmap_max_combo, 0.35),
                1.0
            )
        
        # 6. 应用准确率加成
        value *= math.pow(accuracy, 5.5)
        
        # 7. 应用连击进度（直到难度计算实现之前的临时方案）
        achievable_combo = score_info.get('achievable_combo', beatmap_max_combo)
        if achievable_combo > 0:
            combo_progress = beatmap_max_combo / achievable_combo
            total_value = value * combo_progress
        else:
            total_value = value
        
        # 返回包含所有计算指标的字典
        return {
            'total': total_value,
            'base_pp': base_value,
            'length_bonus': length_bonus,
            'accuracy_bonus': math.pow(accuracy, 5.5),
            'miss_penalty': math.pow(0.97, count_miss),
            'combo_bonus': min(math.pow(score_max_combo, 0.35) / math.pow(beatmap_max_combo, 0.35), 1.0) if beatmap_max_combo > 0 else 1.0
        }