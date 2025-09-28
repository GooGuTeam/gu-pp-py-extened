"""
Tau谱面数据结构的Python定义
"""

from typing import List, Optional, Dict, Any
from .objects import TauHitObject, Beat, Slider, HardBeat


class BeatmapStatistics:
    """谱面统计信息"""
    
    def __init__(self, name: str, content: str, icon: Optional[str] = None):
        self.name = name
        self.content = content
        self.icon = icon


class TauBeatmap:
    """Tau谱面类"""
    
    def __init__(self):
        self.hit_objects: List[TauHitObject] = []
        self.metadata: Dict[str, Any] = {}
        self.difficulty_attributes: Dict[str, float] = {
            'approach_rate': 5.0,
            'overall_difficulty': 5.0,
            'circle_size': 5.0,
            'drain_rate': 5.0
        }
        self.timing_points: List[Any] = []  # 存储时间点信息
        self.file_version: int = 0  # 文件版本
    
    def get_statistics(self) -> List[BeatmapStatistics]:
        """
        获取谱面统计信息
        
        Returns:
            List[BeatmapStatistics]: 包含谱面统计信息的列表
        """
        beats = len([obj for obj in self.hit_objects if isinstance(obj, Beat)])
        sliders = len([obj for obj in self.hit_objects if isinstance(obj, Slider)])
        hard_beats = len([obj for obj in self.hit_objects if isinstance(obj, HardBeat)])
        
        return [
            BeatmapStatistics("Beat Count", str(beats), "square"),
            BeatmapStatistics("Slider Count", str(sliders), "sliders"),
            BeatmapStatistics("Hard Beat Count", str(hard_beats), "circle")
        ]
    
    def add_hit_object(self, hit_object: TauHitObject):
        """
        添加击打物件到谱面
        
        Args:
            hit_object (TauHitObject): 要添加的击打物件
        """
        self.hit_objects.append(hit_object)
    
    def remove_hit_object(self, hit_object: TauHitObject):
        """
        从谱面移除击打物件
        
        Args:
            hit_object (TauHitObject): 要移除的击打物件
        """
        if hit_object in self.hit_objects:
            self.hit_objects.remove(hit_object)
    
    def clear_hit_objects(self):
        """清空所有击打物件"""
        self.hit_objects.clear()
    
    def get_max_combo(self) -> int:
        """
        获取谱面最大连击数
        
        Returns:
            int: 最大连击数
        """
        max_combo = 0
        for obj in self.hit_objects:
            max_combo += 1
            # 如果是Slider，增加额外的连击点
            if isinstance(obj, Slider):
                # 简化处理，实际应该根据滑条的节点数计算
                max_combo += obj.repeat_count + 1
        return max_combo
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        stat_str = ", ".join([f"{stat.name}: {stat.content}" for stat in stats])
        return f"TauBeatmap({stat_str})"