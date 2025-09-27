"""
Sentakki游戏物件基础类和接口
"""

import math
from typing import List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class HitSampleInfo:
    """击打采样信息"""
    name: str
    volume: int = 100
    custom_sample_bank: int = 0
    priority: int = 0


class IHasLane(ABC):
    """具有轨道属性的接口"""
    
    @property
    @abstractmethod
    def lane(self) -> int:
        pass
    
    @lane.setter
    @abstractmethod
    def lane(self, value: int):
        pass


class IHasPosition(ABC):
    """具有位置属性的接口"""
    
    @property
    @abstractmethod
    def position(self) -> Tuple[float, float]:
        pass
    
    @position.setter
    @abstractmethod
    def position(self, value: Tuple[float, float]):
        pass


class IHasDuration(ABC):
    """具有持续时间属性的接口"""
    
    @property
    @abstractmethod
    def start_time(self) -> float:
        pass
    
    @start_time.setter
    @abstractmethod
    def start_time(self, value: float):
        pass
    
    @property
    @abstractmethod
    def duration(self) -> float:
        pass
    
    @duration.setter
    @abstractmethod
    def duration(self, value: float):
        pass

    @property
    def end_time(self) -> float:
        """结束时间"""
        return self.start_time + self.duration
    
    @end_time.setter
    def end_time(self, value: float):
        """设置结束时间"""
        self.duration = value - self.start_time


class HitObject:
    """基础击打物件"""
    
    def __init__(self):
        self._start_time: float = 0
        self.samples: List[HitSampleInfo] = []
    
    @property
    def start_time(self) -> float:
        return self._start_time
    
    @start_time.setter
    def start_time(self, value: float):
        self._start_time = value