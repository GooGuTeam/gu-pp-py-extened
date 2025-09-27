"""
Sentakki核心游戏物件
"""

from typing import List
from .base import HitObject, IHasLane


class SentakkiHitObject(HitObject):
    """Sentakki基础物件"""
    
    def __init__(self):
        super().__init__()
        self.break_state: bool = False
        self.ex_state: bool = False
        self._base_score_weighting: int = 1
    
    @property
    def score_weighting(self) -> int:
        """得分权重"""
        return 5 if self.break_state else self._base_score_weighting
    
    @property
    def base_score_weighting(self) -> int:
        """基础得分权重"""
        return getattr(self, '_base_score_weighting', 1)
    
    @base_score_weighting.setter
    def base_score_weighting(self, value: int):
        self._base_score_weighting = value


class SentakkiLanedHitObject(SentakkiHitObject, IHasLane):
    """Sentakki轨道物件"""
    
    def __init__(self):
        super().__init__()
        self._lane: int = 0
    
    @property
    def lane(self) -> int:
        return self._lane
    
    @lane.setter
    def lane(self, value: int):
        self._lane = value