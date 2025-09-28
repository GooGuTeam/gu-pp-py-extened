"""
Sentakki难度计算器，模仿rosu-pp的接口风格
"""

import math
from typing import List, Any
from ..core import SentakkiHitObject
from ..tap import Tap
from ..hold import Hold, HoldHead
from ..touch import Touch
from ..slide import Slide, SlideBody, SlideCheckpoint, CheckpointNode, SlideTap
from ..beatmap import SentakkiBeatmap
from .preprocessing.sentakkiDifficultyHitObject import SentakkiDifficultyHitObject
from .sentakkiDifficultyAttributes import SentakkiDifficultyAttributes


class SentakkiDifficultyCalculator:
    """Sentakki难度计算器"""
    
    def __init__(self, beatmap: SentakkiBeatmap, mods: int = 0):
        """
        初始化难度计算器
        
        Args:
            beatmap: Sentakki谱面对象
            mods: 应用的mods
        """
        self.beatmap = beatmap
        self.mods = mods
        self.difficulty_multiplier = 0.0675  # 默认难度倍率
    
    def calculate(self) -> SentakkiDifficultyAttributes:
        """
        计算谱面难度
        
        Returns:
            SentakkiDifficultyAttributes: 难度属性
        """
        max_combo = self._get_max_combo()
        clock_rate = self._get_clock_rate()
        
        # 基于物件密度计算难度
        note_density = self._calculate_note_density()
        type_complexity = self._calculate_type_complexity()
        
        # 基础难度值
        aim_difficulty = note_density * type_complexity * 0.8
        speed_difficulty = note_density * 1.2
        complexity_difficulty = type_complexity * note_density
        
        # 计算星级评分
        base_aim = math.pow(5 * max(1, aim_difficulty / 0.0675) - 4, 3) / 100000
        base_speed = math.pow(5 * max(1, speed_difficulty / 0.0675) - 4, 3) / 100000
        base_complexity = math.pow(5 * max(1, complexity_difficulty / 0.0675) - 4, 3) / 100000
        
        base_performance = math.pow(
            math.pow(base_aim, 1.1) + math.pow(base_speed, 1.1) + math.pow(base_complexity, 1.1),
            1.0 / 1.1
        )
        
        star_rating = 0
        if base_performance > 0.00001:
            star_rating = math.pow(1.12, 1/3) * 0.027 * (math.pow(100000 / math.pow(2, 1 / 1.1) * base_performance, 1/3) + 4)
        
        # 基础星级评分乘以时钟速率
        base_sr = star_rating * clock_rate
        
        # 创建难度属性对象
        attributes = SentakkiDifficultyAttributes()
        attributes.star_rating = base_sr * 1.25  # 转换谱面的星级评分膨胀，鼓励玩家尝试较低难度
        attributes.max_combo = max_combo
        
        return attributes
    
    def _create_difficulty_hit_objects(self) -> List['SentakkiDifficultyHitObject']:
        """
        创建难度击打物件
        
        Returns:
            List[SentakkiDifficultyHitObject]: 难度击打物件列表
        """
        from .preprocessing.sentakkiDifficultyHitObject import SentakkiDifficultyHitObject
        
        difficulty_objects = []
        last_object = None
        
        clock_rate = self._get_clock_rate()
        
        for i, hit_object in enumerate(self.beatmap.hit_objects):
            if last_object is not None:
                obj = SentakkiDifficultyHitObject(
                    hit_object, 
                    last_object, 
                    clock_rate,
                    difficulty_objects,
                    i
                )
                difficulty_objects.append(obj)
            
            last_object = hit_object
        
        return difficulty_objects
    
    def _calculate_note_density(self) -> float:
        """
        计算物件密度
        
        Returns:
            float: 物件密度值
        """
        if len(self.beatmap.hit_objects) < 2:
            return 0.0
        
        # 计算平均物件间隔
        total_time = self.beatmap.hit_objects[-1].start_time - self.beatmap.hit_objects[0].start_time
        if total_time <= 0:
            return 0.0
            
        avg_interval = total_time / (len(self.beatmap.hit_objects) - 1)
        
        # 密度与间隔成反比，间隔越小密度越高
        # 使用指数函数使变化更明显
        return min(10.0, 1000.0 / max(1.0, avg_interval))
    
    def _calculate_type_complexity(self) -> float:
        """
        计算物件类型复杂度
        
        Returns:
            float: 类型复杂度值
        """
        if len(self.beatmap.hit_objects) == 0:
            return 0.0
        
        # 统计各种物件类型
        tap_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Tap))
        hold_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Hold))
        touch_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Touch))
        slide_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Slide))
        
        total_objects = len(self.beatmap.hit_objects)
        
        # 计算类型多样性（使用香农熵）
        entropy = 0.0
        for count in [tap_count, hold_count, touch_count, slide_count]:
            if count > 0:
                p = count / total_objects
                entropy -= p * math.log2(p)
        
        # 将熵值归一化到0-1范围
        max_entropy = math.log2(4)  # 最大熵值（4种类型均匀分布）
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # 复杂度基于多样性，但也考虑slide和touch的固有复杂性
        base_complexity = 1.0 + (slide_count * 0.5 + touch_count * 0.3) / max(1, total_objects)
        
        return base_complexity * (0.5 + 0.5 * normalized_entropy)
    
    def _get_clock_rate(self) -> float:
        """
        获取时钟速率
        
        Returns:
            float: 时钟速率
        """
        clock_rate = 1.0
        
        # 这里应该根据mods调整时钟速率
        # 例如：DT=1.5x, HT=0.75x
        # 目前简化处理
        return clock_rate
    
    def _get_max_combo(self) -> int:
        """
        获取最大连击数
        
        Returns:
            int: 最大连击数
        """
        max_combo = 0
        for obj in self.beatmap.hit_objects:
            max_combo += 1
            # 根据物件类型调整连击数
            if isinstance(obj, Hold):
                # 长按增加头部和尾部两个连击
                max_combo += 1
            elif isinstance(obj, Slide):
                # 滑条根据节点数增加连击
                max_combo += len(getattr(obj, 'slide_info_list', [])) * 2
        
        return max_combo
    
    def _create_empty_difficulty_attributes(self) -> SentakkiDifficultyAttributes:
        """
        创建空的难度属性
        
        Returns:
            SentakkiDifficultyAttributes: 空的难度属性
        """
        attributes = SentakkiDifficultyAttributes()
        attributes.star_rating = 0.0
        attributes.max_combo = 0
        return attributes