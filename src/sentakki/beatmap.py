"""
Sentakki谱面类
"""

from typing import List, Dict, Any
from .core import SentakkiHitObject


class SentakkiBeatmap:
    """Sentakki谱面"""
    
    def __init__(self):
        """初始化谱面"""
        self.hit_objects: List[SentakkiHitObject] = []
        self.difficulty_attributes: Dict[str, float] = {
            'approach_rate': 5.0,
            'overall_difficulty': 5.0,
            'drain_rate': 5.0
        }
        self.metadata: Dict[str, str] = {}
    
    def add_hit_object(self, hit_object: SentakkiHitObject):
        """
        添加击打物件
        
        Args:
            hit_object: 击打物件
        """
        self.hit_objects.append(hit_object)
    
    def set_difficulty_attribute(self, attribute: str, value: float):
        """
        设置难度属性
        
        Args:
            attribute: 属性名
            value: 属性值
        """
        self.difficulty_attributes[attribute] = value
    
    def set_metadata(self, key: str, value: str):
        """
        设置元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def get_max_combo(self) -> int:
        """
        获取最大连击数
        
        Returns:
            int: 最大连击数
        """
        # 简化计算
        combo = len(self.hit_objects)
        
        # Slide和Hold物件会增加combo
        for obj in self.hit_objects:
            if hasattr(obj, '__class__') and obj.__class__.__name__ in ['Hold', 'Slide']:
                combo += 1
                
        return combo