"""Tau 游戏模式公共导出。

集中整理对外 API，避免星号导入带来不稳定符号外泄。
"""

from .attributes import TauDifficultyAttributes, BeatmapAttributes, BeatmapAttributesBuilder, HitWindows
from .beatmap import TauBeatmap
from .objects import (
    TauHitObject,
    AngledTauHitObject,
    Beat,
    HardBeat,
    StrictHardBeat,
    Slider,
    SliderHeadBeat,
    SliderHardBeat,
    SliderRepeat,
    SliderTick,
    PolarSliderPath,
    SliderNode,
)
from .mods import TauMods, get_mod_score_multiplier, apply_mods_to_attributes, calculate_hit_windows
from .difficulty import TauDifficultyCalculator  # re-export统一名字
from .performance import TauPerformanceCalculator, TauPerformanceAttributes
from .convertor import convert_osu_beatmap

__all__ = [
    # 属性相关
    "TauDifficultyAttributes",
    "BeatmapAttributes",
    "BeatmapAttributesBuilder",
    "HitWindows",
    # 谱面与物件
    "TauBeatmap",
    "TauHitObject",
    "AngledTauHitObject",
    "Beat",
    "HardBeat",
    "StrictHardBeat",
    "Slider",
    "SliderHeadBeat",
    "SliderHardBeat",
    "SliderRepeat",
    "SliderTick",
    "PolarSliderPath",
    "SliderNode",
    # Mods
    "TauMods",
    "get_mod_score_multiplier",
    "apply_mods_to_attributes",
    "calculate_hit_windows",
    # 计算器
    "TauDifficultyCalculator",
    "TauPerformanceCalculator",
    "TauPerformanceAttributes",
    # 转换
    "convert_osu_beatmap",
]