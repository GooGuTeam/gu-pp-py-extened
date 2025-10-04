from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

# flag bits
FLAG_BREAK = 1 << 0
FLAG_EX = 1 << 1
FLAG_TWIN = 1 << 2
FLAG_FAN = 1 << 3

@dataclass
class SentakkiObjectBase:
    time: int
    lane: int
    flags: int = 0
    kind: str = "base"
    @property
    def end_time(self) -> int:
        return self.time

@dataclass
class Tap(SentakkiObjectBase):
    kind: str = "tap"

@dataclass
class Hold(SentakkiObjectBase):
    duration: int = 0
    kind: str = "hold"
    @property
    def end_time(self) -> int:
        return self.time + self.duration

@dataclass
class SlideSegment:
    end_lane: int
    duration: int
    fan: bool = False

@dataclass
class SlidePathPart:
    """Slide path part allocation inside a composite slide.

    duration: 实际为该 part 分配的时长 (ms)。
    fan_start_progress: 对于 fan 形状表示风扇动画开始的归一化进度 (0-1)。
    """
    shape: str = "linear"
    duration: int = 0
    mirrored: bool = False
    min_duration: int = 0
    end_offset: int = 0
    fan_start_progress: float = 1.0

@dataclass
class SlideBodyInfo:
    parts: List[SlidePathPart] = field(default_factory=list)
    duration: int = 0
    shoot_delay: int = 0
    fan_start_progress: float = 1.0  # 0-1, when fan begins inside duration
    end_lane: int = 0  # predicted end lane after applying internal path deltas
    complexity: float = 0.0  # aggregated complexity factor for star calc

@dataclass
class Slide(SentakkiObjectBase):
    segments: List[SlideSegment] = field(default_factory=list)  # legacy simple segments
    body: Optional[SlideBodyInfo] = None  # richer info (Phase 2+)
    kind: str = "slide"
    @property
    def end_time(self) -> int:
        if self.body:
            return self.time + self.body.duration
        return self.time + sum(s.duration for s in self.segments)

@dataclass
class Touch(SentakkiObjectBase):
    x: float = 0
    y: float = 0
    kind: str = "touch"

@dataclass
class TouchHold(Touch):
    duration: int = 0
    kind: str = "touch_hold"
    @property
    def end_time(self) -> int:
        return self.time + self.duration

__all__ = [
    'SentakkiObjectBase','Tap','Hold','Slide','SlideSegment','SlidePathPart','SlideBodyInfo','Touch','TouchHold',
    'FLAG_BREAK','FLAG_EX','FLAG_TWIN','FLAG_FAN'
]