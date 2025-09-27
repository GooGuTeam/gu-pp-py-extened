"""
Tau游戏物件数据结构的Python定义
"""

import math
from typing import List, Optional, Tuple, TypeVar
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class HitSampleInfo:
    """击打采样信息"""
    name: str
    volume: int = 100
    custom_sample_bank: int = 0
    priority: int = 0


class IHasAngle(ABC):
    """具有角度属性的接口"""
    
    @property
    @abstractmethod
    def angle(self) -> float:
        pass
    
    @angle.setter
    @abstractmethod
    def angle(self, value: float):
        pass


class IHasOffsetAngle(IHasAngle):
    """具有偏移角度的接口"""
    
    @abstractmethod
    def get_offset_angle(self) -> float:
        pass
    
    def get_absolute_angle(self) -> float:
        return normalize_angle(self.angle + self.get_offset_angle())


@dataclass
class SliderNode:
    """滑条节点"""
    time: float
    angle: float
    
    def __str__(self) -> str:
        return f"T: {self.time} | A: {self.angle}"


class PolarSliderPath:
    """极坐标滑条路径"""
    
    def __init__(self, nodes: List[SliderNode]):
        self.nodes: List[SliderNode] = sorted(nodes, key=lambda node: node.time) if nodes else []
        self._version: int = 0
        self._calculated_length: float = 0
        self._node_index: int = 0
    
    @property
    def duration(self) -> float:
        """路径持续时间"""
        if not self.nodes:
            return 0
        return self.end_node.time - self.start_node.time if self.end_node and self.start_node else 0
    
    @property
    def end_node(self) -> Optional[SliderNode]:
        """结束节点"""
        return self.nodes[-1] if self.nodes else None
    
    @property
    def start_node(self) -> Optional[SliderNode]:
        """起始节点"""
        return self.nodes[0] if self.nodes else None
    
    @property
    def calculated_distance(self) -> float:
        """计算路径距离"""
        self._ensure_valid()
        return self._calculated_length
    
    def _ensure_valid(self):
        """确保路径有效"""
        self._calculate_length()
    
    def _calculate_length(self):
        """计算路径长度"""
        self._calculated_length = 0
        
        if len(self.nodes) <= 0:
            return
        
        last_angle = self.nodes[0].angle
        
        for node in self.nodes:
            delta = get_delta_angle(node.angle, last_angle)
            self._calculated_length += abs(delta)
            last_angle = node.angle
    
    def seek_to(self, time: float):
        """寻找指定时间的节点"""
        while self._node_index > 0 and self.nodes[self._node_index - 1].time > time:
            self._node_index -= 1
        while (self._node_index + 1 < len(self.nodes) and 
               self.nodes[self._node_index + 1].time <= time):
            self._node_index += 1
    
    def nodes_between(self, start: float, end: float) -> List[SliderNode]:
        """获取指定时间范围内的节点"""
        self.seek_to(start)
        result = []
        for i in range(self._node_index + 1, len(self.nodes)):
            if self.nodes[i].time <= end:
                result.append(self.nodes[i])
            else:
                break
        return result
    
    def segments_between(self, start: float, end: float) -> List[Tuple[SliderNode, SliderNode]]:
        """获取指定时间范围内的段"""
        self.seek_to(start)
        index = max(self._node_index - 1, 0)
        result = []
        
        for i in range(index, len(self.nodes) - 1):
            from_node = self.nodes[i]
            to_node = self.nodes[i + 1]
            
            # 如果下一个节点时间超过结束时间，则调整
            if to_node.time > end and to_node.time != from_node.time:
                delta_angle = get_delta_angle(to_node.angle, from_node.angle)
                duration = to_node.time - from_node.time
                to_node = SliderNode(
                    end,
                    from_node.angle + delta_angle * (end - from_node.time) / duration
                )
            
            # 如果当前节点时间小于开始时间，则调整
            if from_node.time < start and to_node.time != from_node.time:
                delta_angle = get_delta_angle(to_node.angle, from_node.angle)
                duration = to_node.time - from_node.time
                from_node = SliderNode(
                    start,
                    from_node.angle + delta_angle * (start - from_node.time) / duration
                )
            
            result.append((from_node, to_node))
            if to_node.time >= end:
                break
                
        return result
    
    def node_at(self, time: float) -> Optional[SliderNode]:
        """获取指定时间的插值节点"""
        if not self.nodes:
            return None
        
        if time <= self.nodes[0].time:
            return self.nodes[0]
        
        if time >= self.nodes[-1].time:
            return self.nodes[-1]
        
        self.seek_to(time)
        from_node = self.nodes[self._node_index]
        to_node = self.nodes[self._node_index + 1]
        delta = get_delta_angle(to_node.angle, from_node.angle)
        
        # 计算插值
        if to_node.time != from_node.time:  # 避免除零错误
            interpolated_angle = from_node.angle + delta * (time - from_node.time) / (to_node.time - from_node.time)
        else:
            interpolated_angle = from_node.angle
            
        return SliderNode(time, interpolated_angle)
    
    def angle_at(self, time: float) -> Optional[float]:
        """获取指定时间的角度"""
        node = self.node_at(time)
        return node.angle if node else None
    
    def calculate_lazy_distance(self, half_tolerance: float) -> float:
        """计算懒人距离"""
        if len(self.nodes) <= 0:
            return 0

        length = 0.0
        last_angle = self.nodes[0].angle

        for node in self.nodes:
            delta = get_delta_angle(node.angle, last_angle)

            if abs(delta) > half_tolerance:
                last_angle += delta - (half_tolerance if delta > 0 else -half_tolerance)
                length += abs(delta)

        return length


class HitObject:
    """基础击打物件"""
    
    def __init__(self):
        self.start_time: float = 0
        self.samples: List[HitSampleInfo] = []


class TauHitObject(HitObject):
    @property
    def angle(self) -> float:
        return getattr(self, '_angle', 0.0)

    @angle.setter
    def angle(self, value: float):
        self._angle = value

    def get_offset_angle(self) -> float:
        return 0.0

    @property
    def range(self) -> float:
        return getattr(self, '_range', 0.0)

    @range.setter
    def range(self, value: float):
        self._range = value
    """Tau游戏基础物件"""
    
    def __init__(self):
        super().__init__()
        self.time_preempt: float = 600
        self.time_fade_in: float = 400
        self.new_combo: bool = False
        self.combo_offset: int = 0
        self.index_in_current_combo: int = 0
        self.combo_index: int = 0
        self.combo_index_with_offsets: int = 0
        self.last_in_combo: bool = False
        self.start_time: float = 0.0  # 补充 start_time 属性


class AngledTauHitObject(TauHitObject, IHasAngle):
    """具有角度的Tau物件"""
    
    def __init__(self):
        super().__init__()
        self._angle: float = 0.0
        self.angle_range: float = 0.0
        self.path = None  # 补充 path 属性，滑条相关
        self.duration: float = 0.0  # 补充 duration 属性
    
    @property
    def angle(self) -> float:
        return self._angle
    
    @angle.setter
    def angle(self, value: float):
        self._angle = value


class Beat(AngledTauHitObject):
    """节拍物件"""
    pass


class HardBeat(TauHitObject):
    """硬节拍物件"""
    pass


class StrictHardBeat(HardBeat):
    """严格硬节拍物件"""
    
    def __init__(self):
        super().__init__()
        self.range: float = 0.0


class Slider(AngledTauHitObject, IHasOffsetAngle):
    """滑条物件"""
    
    BASE_SCORING_DISTANCE: int = 100
    
    def __init__(self):
        super().__init__()
        self.is_hard: bool = False
        self.path: Optional[PolarSliderPath] = None
        self.head_beat: Optional[AngledTauHitObject] = None
        self.tail_samples: List[HitSampleInfo] = []
        self.velocity: float = 0
        self.tick_distance: float = 0
        self.tick_distance_multiplier: float = 2
        self.repeat_count: int = 0
        self.node_samples: List[List[HitSampleInfo]] = []
        self._span_duration: float = 0
        self.nested_hit_objects: List[HitObject] = []
    # self.duration: float = 0.0  # 移除重复声明，避免与 @property 冲突
    
    @property
    def duration(self) -> float:
        """滑条持续时间"""
        return self.path.duration if self.path else 0
    
    @property
    def end_time(self) -> float:
        """滑条结束时间"""
        return self.start_time + self.duration
    
    @property
    def span_duration(self) -> float:
        """单个跨度的持续时间"""
        span_count = self.repeat_count + 1
        return self.duration / span_count if span_count > 0 else 0
    
    def get_offset_angle(self) -> float:
        """获取偏移角度"""
        if self.path and self.path.end_node:
            return self.path.end_node.angle
        return 0


class SliderHeadBeat(Beat, IHasOffsetAngle):
    """滑条头部节拍"""
    
    def __init__(self):
        super().__init__()
        self.parent_slider: Optional[Slider] = None
    
    def get_offset_angle(self) -> float:
        """获取偏移角度"""
        return self.parent_slider.angle if self.parent_slider else 0


class SliderHardBeat(StrictHardBeat, IHasOffsetAngle):
    """滑条硬节拍"""
    
    def __init__(self):
        super().__init__()
        self.parent_slider: Optional[Slider] = None
    
    def get_offset_angle(self) -> float:
        """获取偏移角度"""
        return self.parent_slider.angle if self.parent_slider else 0


class SliderRepeat(AngledTauHitObject, IHasOffsetAngle):
    """滑条重复点"""
    
    def __init__(self):
        super().__init__()
        self.parent_slider: Optional[Slider] = None
        self.repeat_index: int = 0
    
    def get_offset_angle(self) -> float:
        """获取偏移角度"""
        return self.parent_slider.angle if self.parent_slider else 0


class SliderTick(AngledTauHitObject, IHasOffsetAngle):
    """滑条刻度点"""
    
    def __init__(self):
        super().__init__()
        self.parent_slider: Optional[Slider] = None
    
    def get_offset_angle(self) -> float:
        """获取偏移角度"""
        return self.parent_slider.angle if self.parent_slider else 0


def from_polar_coordinates(distance: float, angle: float) -> Tuple[float, float]:
    """从极坐标获取笛卡尔坐标位置"""
    x = -(distance * math.cos(math.radians(angle + 90)))
    y = -(distance * math.sin(math.radians(angle + 90)))
    return (x, y)


def normalize_angle(angle: float) -> float:
    """将角度标准化到0-360范围内"""
    if angle < 0:
        angle += 360
    if angle >= 360:
        angle %= 360
    return angle


def get_delta_angle(a: float, b: float) -> float:
    """获取两个角度之间的差值"""
    m = (a - b + 180) % 360
    return m - 180 if m >= 0 else m + 360 - 180


def remap(value: float, x1: float, x2: float, y1: float, y2: float) -> float:
    """将值从一个范围重新映射到另一个范围"""
    if x2 == x1:  # 避免除零错误
        return y1
    m = (y2 - y1) / (x2 - x1)
    c = y1 - m * x1
    return m * value + c