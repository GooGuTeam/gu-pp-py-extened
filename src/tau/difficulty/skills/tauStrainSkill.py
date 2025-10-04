"""Tau应变技能基类与加权逻辑（更贴近官方 C# 实现）。

参考 taulazer/tau C# 逻辑：
 - Aim 继承 StrainDecaySkill（简单权重、无 peak 削减）
 - Speed / Complexity 继承 TauStrainSkill（对最高若干 section 进行缩放与再排序加权）

这里做一个统一抽象：
 - BaseStrainSkill: 处理分段、记录峰值、基础加权。
 - TauStrainSkill: 增加 ReducedSectionCount / ReducedStrainBaseline / DifficultyMultiplier 的 peak 减弱逻辑。
 - 具体技能（Speed/Complexity）继承 TauStrainSkill；Aim 继续使用简单逻辑（可直接继承 BaseStrainSkill 并设定参数）。

注：官方实现按时间固定步长切分（osu! 中通常 400ms）。原 Python 版本用 10s 段落过粗，现改为 400ms 以提高还原度。
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List
from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from ...mods import TauMods

STRAIN_STEP_MS = 400.0  # 与 osu! 系列规则集保持一致的 section 时长
DECAY_WEIGHT = 0.9      # section 权重衰减


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class BaseStrainSkill(ABC):
    """基础应变技能：仅按 section 取峰值后排序衰减加权。"""

    def __init__(self, mods: TauMods):
        self.mods = mods
        self.current_strain = 0.0
        self.current_section_end = 0.0
        self.current_section_peak = 0.0
        self.section_peaks: List[float] = []

    # ----- 可覆盖参数 -----
    skill_multiplier: float = 1.0
    strain_decay_base: float = 1.0  # <1 会衰减；=1 不衰减

    def process(self, current: TauDifficultyHitObject):
        # 初始化第一个 section 结束时间
        if not self.section_peaks and self.current_section_end == 0:
            self.current_section_end = self._round_up_section_end(current.start_time)

        # 开启新 section（可能跨越多个 section）
        while current.start_time > self.current_section_end:
            self._save_current_peak()
            self._start_new_section(self.current_section_end)

        # 衰减旧应变
        self.current_strain *= self._strain_decay(current.delta_time)

        # 叠加当前物件应变
        self.current_strain += self.strain_value_of(current) * self.skill_multiplier

        # 更新 section 峰值
        if self.current_strain > self.current_section_peak:
            self.current_section_peak = self.current_strain

    def _round_up_section_end(self, time_ms: float) -> float:
        return (math.floor(time_ms / STRAIN_STEP_MS) + 1) * STRAIN_STEP_MS

    def _start_new_section(self, section_end_time: float):
        self.current_section_end = section_end_time + STRAIN_STEP_MS
        self.current_section_peak = self.current_strain

    def _save_current_peak(self):
        self.section_peaks.append(self.current_section_peak)

    def _strain_decay(self, ms: float) -> float:
        # 与 osu! 逻辑类似：decay_base ** (delta / 1000)
        return self.strain_decay_base ** (ms / 1000.0)

    @abstractmethod
    def strain_value_of(self, current: TauDifficultyHitObject) -> float:  # pragma: no cover - 由子类实现
        ...

    def difficulty_value(self) -> float:
        # 结束时保存最后一个 section 峰值
        self._save_current_peak()
        # 过滤掉零峰值（保持与官方“排除 0 section”一致的思想）
        peaks = [p for p in self.section_peaks if p > 0]
        if not peaks:
            return 0.0
        peaks.sort(reverse=True)
        difficulty = 0.0
        weight = 1.0
        for v in peaks:
            difficulty += v * weight
            weight *= DECAY_WEIGHT
        return difficulty


class TauStrainSkill(BaseStrainSkill):
    """带 peak 削减与额外最终乘子的 Tau 技能（Speed / Complexity）。"""

    # 默认与 C# TauStrainSkill 对齐
    reduced_section_count: int = 10
    reduced_strain_baseline: float = 0.75
    difficulty_multiplier_final: float = 1.06

    def difficulty_value(self) -> float:
        self._save_current_peak()
        peaks = [p for p in self.section_peaks if p > 0]
        if not peaks:
            return 0.0
        peaks.sort(reverse=True)

        # 对最高 reduced_section_count 个 section 应用缩放
        limit = min(len(peaks), self.reduced_section_count)
        for i in range(limit):
            # scale = log10( lerp(1,10, i / reduced_section_count) )
            t = i / self.reduced_section_count if self.reduced_section_count > 0 else 1
            scale = math.log10(lerp(1.0, 10.0, max(0.0, min(1.0, t))))
            peaks[i] *= lerp(self.reduced_strain_baseline, 1.0, scale)

        # 再次排序（缩放后次序可能变化）
        peaks.sort(reverse=True)

        difficulty = 0.0
        weight = 1.0
        for v in peaks:
            difficulty += v * weight
            weight *= DECAY_WEIGHT
        return difficulty * self.difficulty_multiplier_final


__all__ = [
    "BaseStrainSkill",
    "TauStrainSkill",
]