"""
Sentakki滑条物件
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple
from .core import SentakkiLanedHitObject, SentakkiHitObject
from .base import IHasDuration


@dataclass
class SlideBodyInfo:
    """滑条主体信息"""
    duration: float = 0.0
    path_type: str = "linear"  # 路径类型：linear, bezier等
    path_points: List[Tuple[float, float]] = field(default_factory=list)  # 路径点列表


class Slide(SentakkiLanedHitObject, IHasDuration):
    """滑条物件"""
    
    class TapType(Enum):
        """滑条起始点类型"""
        STAR = "star"
        TAP = "tap"
        NONE = "none"
    
    def __init__(self):
        super().__init__()
        self._duration: float = 0
        self.tap_type: 'Slide.TapType' = Slide.TapType.STAR
        self.slide_info_list: List['SlideBodyInfo'] = []  # SlideBodyInfo列表
    
    @property
    def duration(self) -> float:
        # 返回所有slide info中的最大持续时间
        if not self.slide_info_list:
            return 0
        return max(info.duration for info in self.slide_info_list)
    
    @duration.setter
    def duration(self, value: float):
        self._duration = value


class SlideBody(SentakkiLanedHitObject, IHasDuration):
    """滑条主体物件"""
    
    def __init__(self, slide_body_info=None):
        super().__init__()
        self.slide_body_info = slide_body_info
        self._duration: float = 0 if slide_body_info is None else slide_body_info.duration
    
    @property
    def duration(self) -> float:
        return self._duration
    
    @duration.setter
    def duration(self, value: float):
        self._duration = value


class SlideCheckpoint(SentakkiHitObject):
    """滑条检查点物件"""
    
    def __init__(self):
        super().__init__()
        self.slide_duration: float = 0
        self.progress: float = 0.0
        self.node_positions: List[Tuple[float, float]] = []
        self.nodes_to_pass: int = 1
        self._start_time: float = 0
    
    @property
    def start_time(self) -> float:
        return self._start_time
    
    @start_time.setter
    def start_time(self, value: float):
        self._start_time = value


class CheckpointNode(SentakkiHitObject):
    """检查点节点"""
    
    def __init__(self, position: Tuple[float, float]):
        super().__init__()
        self._position = position
        self.slide_duration: float = 0
        self._start_time: float = 0
    
    @property
    def position(self) -> Tuple[float, float]:
        return self._position
    
    @position.setter
    def position(self, value: Tuple[float, float]):
        self._position = value
    
    @property
    def start_time(self) -> float:
        return self._start_time
    
    @start_time.setter
    def start_time(self, value: float):
        self._start_time = value


class SlideTap(SentakkiLanedHitObject):
    """滑条起始点物件"""
    pass