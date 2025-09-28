"""
Sentakki难度属性类
"""

from typing import Dict, List, Tuple, Any


class SentakkiDifficultyAttributes:
    """Sentakki难度属性"""
    
    def __init__(self):
        """初始化难度属性"""
        self.star_rating: float = 0.0
        self.mods: List[str] = []
        self.max_combo: int = 0
        self.attributes: Dict[str, Any] = {}
    
    def to_database_attributes(self) -> List[Tuple[str, Any]]:
        """
        转换为数据库属性
        
        Returns:
            List[Tuple[str, Any]]: 属性列表
        """
        attributes = []
        
        # 添加基础属性
        attributes.append(("star_rating", self.star_rating))
        
        return attributes
    
    def from_database_attributes(self, values: Dict[str, float]):
        """
        从数据库属性加载
        
        Args:
            values: 数据库属性值字典
        """
        self.star_rating = values.get("star_rating", 0.0)