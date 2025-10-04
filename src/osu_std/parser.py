"""轻量级 osu!standard .osu 文件解析器

不依赖外部库，支持解析以下关键段落：
- General
- Metadata
- Difficulty
- TimingPoints
- HitObjects (circle / slider / spinner / hold note(LN) from mania convert 可忽略) 这里只面向 std

实现要点：
1. .osu 文件按节(section)划分，以 [SectionName] 行开始到下一个方括号为止。
2. key=value 行解析为字典；HitObjects 与 TimingPoints 使用逗号分隔字段。
3. Slider 解析： x,y,time,type,hitSound,curveType|points...,repeat,pixelLength,edgeSounds,edgeSets,hitSample
   我们仅保留曲线点串、repeat 次数、pixelLength 供后续星级/pp 可能使用。
4. 支持 osu 文件 format 版本行: "osu file format v14" 等。
5. 提供统一 OsuBeatmap 数据结构。

参考官方 wiki: https://osu.ppy.sh/wiki/en/Client/File_formats/Osu_%28file_format%29
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re, math
from .hitobjects import HitObject, SliderInfo, SpinnerInfo, parse_hit_object

# ---- 数据模型 ----

@dataclass
class TimingPoint:
    time: float
    beat_length: float
    meter: int
    sample_set: int
    sample_index: int
    volume: int
    uninherited: bool
    effects: int

    @property
    def bpm(self) -> Optional[float]:
        if self.beat_length > 0:
            return 60000.0 / self.beat_length
        return None

## HitObject / SliderInfo / SpinnerInfo 已移动到 hitobjects.py

@dataclass
class OsuBeatmap:
    format_version: int = 0
    general: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    difficulty: Dict[str, Any] = field(default_factory=dict)
    editor: Dict[str, Any] = field(default_factory=dict)
    timing_points: List[TimingPoint] = field(default_factory=list)
    hit_objects: List[HitObject] = field(default_factory=list)

    # 便捷属性
    @property
    def ar(self) -> float:
        return float(self.difficulty.get('ApproachRate', self.difficulty.get('OverallDifficulty', 5)))

    @property
    def od(self) -> float:
        return float(self.difficulty.get('OverallDifficulty', 5))

    @property
    def cs(self) -> float:
        return float(self.difficulty.get('CircleSize', 5))

    @property
    def hp(self) -> float:
        return float(self.difficulty.get('HPDrainRate', 5))

    # ---- 计算最大连击 ----
    def compute_max_combo(self) -> int:
        """估算最大连击数 (近似实现，遵循 osu!standard 规则)

        算法参考（简化版）：
        - HitCircle: +1
        - Spinner: +1
        - Slider: head + tail + (repeat_count - 1) + 所有 span 的 ticks
            * span_count = repeat (osu 文件里的 repeat 字段)
            * span_length = pixel_length / span_count
            * slider_velocity = slider_multiplier * 100 * sv_multiplier (像素/beat)
              其中 sv_multiplier 来自继承绿线: sv_multiplier = 100 / -beat_length (当 beat_length < 0)
            * tick_distance = 100 * slider_multiplier * sv_multiplier / slider_tick_rate
            * 每个 span 的可用 tick 数 = floor((span_length - 0.01) / tick_distance) (排除尾端 0.01 容差)
        注意：这是一个近似，不包含 legacy 零 tick 限制、速度变化细节或 stack 影响。
        """
        slider_multiplier = float(self.difficulty.get('SliderMultiplier', 1.0))
        slider_tick_rate = float(self.difficulty.get('SliderTickRate', 1.0)) or 1.0

        # 预处理 timing points，维护当前 base beat length 与 sv multiplier
        timing_points_sorted = sorted(self.timing_points, key=lambda t: t.time)
        base_beat_length = 500.0  # 默认
        sv_multiplier = 1.0
        tp_index = 0

        def update_timing(current_time: float):
            nonlocal tp_index, base_beat_length, sv_multiplier
            while tp_index + 1 < len(timing_points_sorted) and timing_points_sorted[tp_index + 1].time <= current_time:
                tp_index += 1
                tp = timing_points_sorted[tp_index]
                if tp.uninherited:  # 红线
                    base_beat_length = tp.beat_length if tp.beat_length > 0 else base_beat_length
                    sv_multiplier = 1.0  # 重置 SV
                else:
                    # 绿线，beat_length 通常为负：真实 SV = 100 / -beat_length
                    if tp.beat_length < 0:
                        sv_multiplier = 100.0 / -tp.beat_length

        max_combo = 0
        for obj in self.hit_objects:
            update_timing(obj.time)
            # Circle
            if obj.extras.get('circle') is not None:
                max_combo += 1
                continue
            # Spinner
            if obj.extras.get('spinner') is not None:
                max_combo += 1
                continue
            # Slider
            slider_data = obj.extras.get('slider')
            if isinstance(slider_data, SliderInfo):
                span_count = max(1, slider_data.repeat)
                span_length = slider_data.pixel_length / span_count if span_count else slider_data.pixel_length
                # 计算 tick distance
                effective_sv = slider_multiplier * sv_multiplier
                # 避免除零
                if slider_tick_rate <= 0:
                    tick_distance = span_length + 1  # 无 tick
                else:
                    tick_distance = (100 * effective_sv) / slider_tick_rate
                tick_count_per_span = 0
                if tick_distance > 0:
                    # 末尾留出 0.01 容差，避免计入尾圆
                    usable = max(0.0, span_length - 0.01)
                    tick_count_per_span = int(math.floor(usable / tick_distance))
                total_ticks = tick_count_per_span * span_count
                # scoring pieces: head + tail + (repeat_count -1) + ticks
                repeats = span_count - 1
                slider_combo = 1 + 1 + repeats + total_ticks
                max_combo += slider_combo
                continue

        return max_combo

# ---- 解析器 ----
class OsuFileParser:
    section_header_re = re.compile(r"^\[(.+)]\s*$")
    key_value_re = re.compile(r"^([^:]+):\s*(.*)$")
    format_re = re.compile(r"^osu file format v(\d+)\s*$")

    def parse(self, text: str) -> OsuBeatmap:
        beatmap = OsuBeatmap()
        current_section: Optional[str] = None

        lines = text.splitlines()
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith('//'):  # 注释/空行
                continue

            # 文件格式版本
            m_format = self.format_re.match(line)
            if m_format:
                beatmap.format_version = int(m_format.group(1))
                continue

            # 新 section
            m_sec = self.section_header_re.match(line)
            if m_sec:
                current_section = m_sec.group(1)
                continue

            # 按 section 解析
            if current_section in {"General", "Metadata", "Difficulty", "Editor"}:
                kv = self.key_value_re.match(line)
                if kv:
                    key = kv.group(1).strip()
                    val = kv.group(2).strip()
                    target = getattr(beatmap, current_section.lower())
                    parsed = self._parse_scalar(val)
                    target[key] = parsed
                continue

            if current_section == "TimingPoints":
                tp = self._parse_timing_point(line)
                if tp:
                    beatmap.timing_points.append(tp)
                continue

            if current_section == "HitObjects":
                ho = parse_hit_object(line)
                if ho:
                    beatmap.hit_objects.append(ho)
                continue

        return beatmap

    # ---- 工具方法 ----
    def _parse_scalar(self, val: str) -> Any:
        # 尝试 int -> float -> bool -> 原字符串
        if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
            try:
                return int(val)
            except ValueError:
                pass
        try:
            if '.' in val:
                return float(val)
        except ValueError:
            pass
        lower = val.lower()
        if lower in {"true", "false"}:
            return lower == "true"
        return val

    def _parse_timing_point(self, line: str) -> Optional[TimingPoint]:
        parts = line.split(',')
        if len(parts) < 8:
            return None
        try:
            time = float(parts[0])
            beat_length = float(parts[1])
            meter = int(parts[2])
            sample_set = int(parts[3])
            sample_index = int(parts[4])
            volume = int(parts[5])
            uninherited = parts[6].strip() == '1'
            effects = int(parts[7])
            return TimingPoint(time, beat_length, meter, sample_set, sample_index, volume, uninherited, effects)
        except ValueError:
            return None

    # _parse_hit_object 与 _parse_slider_path 已移动到 hitobjects.py

# 便捷函数
parse_osu = OsuFileParser().parse
