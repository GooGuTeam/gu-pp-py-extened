"""
Tau谱面属性和难度属性定义
"""

from typing import Optional, List, Any
from dataclasses import dataclass, field
from .objects import TauHitObject
from .mods import TauMods, calculate_hit_windows


@dataclass
class BeatmapAttributes:
    """
    Tau谱面属性，类似于rosu-pp中的BeatmapAttributes
    """
    # 谱面基础属性
    approach_rate: float = 5.0
    overall_difficulty: float = 5.0
    circle_size: float = 5.0
    drain_rate: float = 5.0
    
    # 游戏相关属性
    clock_rate: float = 1.0
    
    # 时间窗口属性
    hit_windows: Optional['HitWindows'] = None


@dataclass
class HitWindows:
    """
    击打时间窗口，类似于rosu-pp中的HitWindows
    """
    # 接近时间（以毫秒为单位）
    approach_rate: float
    
    # 不同判定的时间窗口（以毫秒为单位）
    great: float  # 300分判定
    ok: Optional[float] = None    # 100分判定
    meh: Optional[float] = None   # 50分判定


@dataclass
class TauDifficultyAttributes:
    """Tau难度属性"""
    star_rating: float = 0.0
    aim_difficulty: float = 0.0
    speed_difficulty: float = 0.0
    complexity_difficulty: float = 0.0
    approach_rate: float = 5.0
    overall_difficulty: float = 5.0
    drain_rate: float = 5.0
    slider_factor: float = 1.0
    notes_count: int = 0
    slider_count: int = 0
    hard_beat_count: int = 0
    max_combo: int = 0
    mods: List[Any] = field(default_factory=list)
    
    def __post_init__(self):
        if self.mods is None:
            self.mods = []

class BeatmapAttributesBuilder:
    """
    谱面属性构建器，类似于rosu-pp中的BeatmapAttributesBuilder
    """
    
    def __init__(self):
        self.ar = 5.0
        self.od = 5.0
        self.cs = 5.0
        self.hp = 5.0
        self.clock_rate = 1.0
        self.mods = 0  # 使用整数表示mod
        
    def ar_value(self, ar: float, with_mods: bool = False) -> 'BeatmapAttributesBuilder':
        """
        设置AR值
        
        Args:
            ar: 接近速率值
            with_mods: 是否已应用mods
        """
        self.ar = ar
        return self
        
    def od_value(self, od: float, with_mods: bool = False) -> 'BeatmapAttributesBuilder':
        """
        设置OD值
        
        Args:
            od: 整体难度值
            with_mods: 是否已应用mods
        """
        self.od = od
        return self
        
    def cs_value(self, cs: float, with_mods: bool = False) -> 'BeatmapAttributesBuilder':
        """
        设置CS值
        
        Args:
            cs: 圆圈大小值
            with_mods: 是否已应用mods
        """
        self.cs = cs
        return self
        
    def hp_value(self, hp: float, with_mods: bool = False) -> 'BeatmapAttributesBuilder':
        """
        设置HP值
        
        Args:
            hp: 生命值 drain rate
            with_mods: 是否已应用mods
        """
        self.hp = hp
        return self
        
    def with_clock_rate(self, clock_rate: float) -> 'BeatmapAttributesBuilder':
        """
        设置时钟速率
        
        Args:
            clock_rate: 时钟速率 (默认为1.0)
        """
        self.clock_rate = clock_rate
        return self
        
    def with_mods(self, mods: int) -> 'BeatmapAttributesBuilder':
        """
        设置mods
        
        Args:
            mods: mods的位掩码表示
        """
        self.mods = mods
        return self
        
    def build(self) -> BeatmapAttributes:
        """
        构建BeatmapAttributes对象
        
        Returns:
            BeatmapAttributes: 构建的谱面属性对象
        """
        # 计算mods对属性的影响
        ar, od, cs, hp = self._apply_mods()
        
        # 计算时间窗口
        hit_windows = self._calculate_hit_windows(ar, od)
        
        return BeatmapAttributes(
            approach_rate=ar,
            overall_difficulty=od,
            circle_size=cs,
            drain_rate=hp,
            clock_rate=self.clock_rate,
            hit_windows=hit_windows
        )
        
    def _apply_mods(self) -> tuple:
        """
        应用mods到属性
        
        Returns:
            tuple: (ar, od, cs, hp) 应用mods后的属性值
        """
        # 使用TauMods枚举来处理mods
        mods = TauMods(self.mods)
        
        ar = self.ar
        od = self.od
        cs = self.cs
        hp = self.hp
        
        # EZ mod
        if mods & TauMods.EASY:
            ar = max(0, ar * 0.5)
            od = max(0, od * 0.5)
            cs = max(0, cs * 0.5)
            hp = min(10, hp * 0.5)
            
        # HR mod
        if mods & TauMods.HARD_ROCK:
            ar = min(10, ar * 1.4)
            od = min(10, od * 1.4)
            cs = min(10, cs * 1.3)
            hp = min(10, hp * 1.4)
            
        # HT mod
        if mods & TauMods.HALF_TIME:
            ar = max(0, ar * 0.75)
            od = max(0, od * 0.75)
            
        # DT mod
        if mods & TauMods.DOUBLE_TIME:
            ar = min(10, ar * 1.5)
            od = min(10, od * 1.5)
            
        return ar, od, cs, hp
        
    def _calculate_hit_windows(self, ar: float, od: float) -> HitWindows:
        """
        根据AR和OD计算击打时间窗口
        
        Args:
            ar: 接近速率
            od: 整体难度
            
        Returns:
            HitWindows: 击打时间窗口对象
        """
        hit_windows = calculate_hit_windows(ar, od)
        return HitWindows(
            approach_rate=hit_windows.approach_rate,
            great=hit_windows.great,
            ok=hit_windows.ok,
            meh=hit_windows.meh
        )
