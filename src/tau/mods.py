"""
Tau游戏模式中的Mods实现
"""

from enum import IntFlag
from typing import Dict, Tuple
from dataclasses import dataclass
from typing import Optional


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


class TauMods(IntFlag):
    """Tau模式中的Mods枚举"""
    NOMOD = 0
    # Difficulty Reducing Mods
    EASY = 1 << 1  # EZ
    HALF_TIME = 1 << 8  # HT
    DAYCORE = 1 << 11  # DC
    NO_FAIL = 1 << 0  # NF
    
    # Difficulty Increasing Mods
    HARD_ROCK = 1 << 4  # HR
    DOUBLE_TIME = 1 << 6  # DT
    NIGHTCORE = 1 << 9  # NC
    
    # Special Mods
    FLASHLIGHT = 1 << 10  # FL
    RELAX = 1 << 7  # RX
    AUTOPILOT = 1 << 12  # AP


# Mod对属性的影响系数
MOD_MULTIPLIERS = {
    TauMods.EASY: 0.5,
    TauMods.HALF_TIME: 0.75,
    TauMods.HARD_ROCK: 1.4,
    TauMods.DOUBLE_TIME: 1.5,
}


def apply_mods_to_attributes(attributes: BeatmapAttributes, mods: TauMods) -> BeatmapAttributes:
    """
    应用mods到谱面属性
    
    Args:
        attributes: 原始谱面属性
        mods: 应用的mods
        
    Returns:
        BeatmapAttributes: 应用mods后的谱面属性
    """
    # 复制原始属性
    modified_attributes = BeatmapAttributes(
        approach_rate=attributes.approach_rate,
        overall_difficulty=attributes.overall_difficulty,
        circle_size=attributes.circle_size,
        drain_rate=attributes.drain_rate,
        clock_rate=attributes.clock_rate,
        hit_windows=attributes.hit_windows
    )
    
    # 应用EZ mod
    if mods & TauMods.EASY:
        modified_attributes.approach_rate = max(0, modified_attributes.approach_rate * MOD_MULTIPLIERS[TauMods.EASY])
        modified_attributes.overall_difficulty = max(0, modified_attributes.overall_difficulty * MOD_MULTIPLIERS[TauMods.EASY])
        modified_attributes.circle_size = max(0, modified_attributes.circle_size * MOD_MULTIPLIERS[TauMods.EASY])
        modified_attributes.drain_rate = min(10, modified_attributes.drain_rate * MOD_MULTIPLIERS[TauMods.EASY])
    
    # 应用HT mod
    if mods & TauMods.HALF_TIME:
        modified_attributes.approach_rate = max(0, modified_attributes.approach_rate * MOD_MULTIPLIERS[TauMods.HALF_TIME])
        modified_attributes.overall_difficulty = max(0, modified_attributes.overall_difficulty * MOD_MULTIPLIERS[TauMods.HALF_TIME])
        modified_attributes.clock_rate *= MOD_MULTIPLIERS[TauMods.HALF_TIME]
    
    # 应用HR mod
    if mods & TauMods.HARD_ROCK:
        modified_attributes.approach_rate = min(10, modified_attributes.approach_rate * MOD_MULTIPLIERS[TauMods.HARD_ROCK])
        modified_attributes.overall_difficulty = min(10, modified_attributes.overall_difficulty * MOD_MULTIPLIERS[TauMods.HARD_ROCK])
        modified_attributes.circle_size = min(10, modified_attributes.circle_size * MOD_MULTIPLIERS[TauMods.HARD_ROCK])
        modified_attributes.drain_rate = min(10, modified_attributes.drain_rate * MOD_MULTIPLIERS[TauMods.HARD_ROCK])
    
    # 应用DT mod
    if mods & TauMods.DOUBLE_TIME:
        modified_attributes.approach_rate = min(10, modified_attributes.approach_rate * MOD_MULTIPLIERS[TauMods.DOUBLE_TIME])
        modified_attributes.overall_difficulty = min(10, modified_attributes.overall_difficulty * MOD_MULTIPLIERS[TauMods.DOUBLE_TIME])
        modified_attributes.clock_rate *= MOD_MULTIPLIERS[TauMods.DOUBLE_TIME]
    
    # 更新时间窗口
    if modified_attributes.hit_windows:
        modified_attributes.hit_windows = calculate_hit_windows(
            modified_attributes.approach_rate,
            modified_attributes.overall_difficulty
        )
    
    return modified_attributes


def calculate_hit_windows(ar: float, od: float) -> 'HitWindows':
    """
    根据AR和OD计算击打时间窗口
    
    Args:
        ar: 接近速率
        od: 整体难度
        
    Returns:
        HitWindows: 击打时间窗口对象
    """
    # Great判定窗口 (ms)
    if ar <= 5:
        great_window = 64 - (ar * 3)  # 从64ms到49ms
    else:
        great_window = 49 - ((ar - 5) * 3)  # 从49ms到34ms
        
    # Ok判定窗口 (ms)
    if od <= 5:
        ok_window = 127 - (od * 3)  # 从127ms到112ms
    else:
        ok_window = 112 - ((od - 5) * 3)  # 从112ms到97ms
        
    return HitWindows(
        approach_rate=ar,
        great=great_window,
        ok=ok_window
    )


def get_mod_score_multiplier(mods: TauMods) -> float:
    """
    获取mod的分数倍数
    
    Args:
        mods: 应用的mods
        
    Returns:
        float: 分数倍数
    """
    multiplier = 1.0
    
    # 根据taulazer/tau项目中的实现
    if mods & TauMods.EASY:
        multiplier *= 0.50  # EZ
    
    if mods & TauMods.HARD_ROCK:
        multiplier *= 1.06  # HR
    
    if mods & TauMods.DOUBLE_TIME:
        multiplier *= 1.12  # DT
    
    if mods & TauMods.HALF_TIME:
        multiplier *= 0.30  # HT
    
    # NC包含DT，所以只需要计算一次
    if mods & TauMods.NIGHTCORE and not (mods & TauMods.DOUBLE_TIME):
        multiplier *= 1.12  # NC (作为DT的特殊情况)
    
    return multiplier