"""
Sentakki触摸物件
"""

from .core import SentakkiHitObject
from .base import IHasPosition
from typing import Tuple


class Touch(SentakkiHitObject, IHasPosition):
    """触摸物件"""
    
    def __init__(self):
        super().__init__()
        self._position: Tuple[float, float] = (0.0, 0.0)
    
    @property
    def position(self) -> Tuple[float, float]:
        return self._position
    
    @position.setter
    def position(self, value: Tuple[float, float]):
        self._position = value