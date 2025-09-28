"""
Sentakki性能属性类
"""

from typing import List, Dict, Any


class SentakkiPerformanceAttributes:
    """Sentakki性能属性"""
    
    def __init__(self):
        """初始化性能属性"""
        self.total: float = 0.0
        self.base_pp: float = 0.0
        self.length_bonus: float = 0.0
        self.attributes: Dict[str, Any] = {}
    
    def get_attributes_for_display(self) -> List[Dict[str, Any]]:
        """
        获取用于显示的属性列表
        
        Returns:
            List[Dict[str, Any]]: 属性显示列表
        """
        attributes = []
        
        # 添加基础属性
        attributes.append({
            'name': 'Total',
            'display_name': 'Total PP',
            'value': self.total
        })
        
        attributes.append({
            'name': 'Base_PP',
            'display_name': 'Base PP',
            'value': self.base_pp
        })
        
        attributes.append({
            'name': 'Length_Bonus',
            'display_name': 'Length Bonus',
            'value': self.length_bonus
        })
        
        return attributes