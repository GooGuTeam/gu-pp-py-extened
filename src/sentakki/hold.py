"""
Sentakki长按物件
"""

from .core import SentakkiLanedHitObject
from .base import IHasDuration


class Hold(SentakkiLanedHitObject, IHasDuration):
    """长按物件"""
    
    def __init__(self):
        super().__init__()
        self._duration: float = 0
    
    @property
    def duration(self) -> float:
        return self._duration
    
    @duration.setter
    def duration(self, value: float):
        self._duration = value


class HoldHead(SentakkiLanedHitObject):
    """长按头部物件"""
    pass