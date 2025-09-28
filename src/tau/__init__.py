"""
Tau游戏模式的Python实现
"""

from .attributes import TauDifficultyAttributes
from .beatmap import TauBeatmap
from .objects import *
from .mods import TauMods

# 难度计算相关
from .difficulty.difficultyCalculator import TauDifficultyCalculator

# 性能计算相关
from .performance import TauPerformanceCalculator, TauPerformanceAttributes

__all__ = [
    # 基础类
    "TauDifficultyAttributes",
    "TauBeatmap",
    "TauHitObject",
    "AngledTauHitObject",
    "Beat",
    "HardBeat",
    "StrictHardBeat",
    "Slider",
    "PolarSliderPath",
    "SliderNode",
    "TauMods",
    
    # 难度计算
    "TauDifficultyCalculator",
    
    # 性能计算
    "TauPerformanceCalculator",
    "TauPerformanceAttributes"
]