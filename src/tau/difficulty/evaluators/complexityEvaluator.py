"""ComplexityEvaluator: 上游 C# ComplexityEvaluator 精确逻辑的 Python 对齐版本。

上游 (taulazer/tau) 逻辑核心：
  - 追踪 mono pattern（连续同类型 HitType 的长度）。
  - 当出现 HitType 切换时，产生基础应变 object_strain = 1。
  - 根据最近两个已结束 mono pattern 的长度奇偶性（总长度是否为偶数）给予 0.5/1.5 调整。
  - 仅当历史 mono pattern 数>=2 时才给予任何应变（否则视为起始过渡忽略）。
  - 对即将结束的 mono pattern 长度加入 mono_history（有限长度 5）。
  - 检测最近 most_recent_patterns_to_compare=2 个 pattern 是否与历史早先某段重复，若重复，按距上次重复以来的 note 数 notesSince 施加 repetitionPenalty = min(1, 0.032 * notesSince)。可叠乘。

差异说明：
  - 本实现采用实例状态而非静态全局（线程/多计算器隔离）。
  - 维持与 C# 结构等价的字段：previous_hit_type, current_mono_length, mono_history。
  - 仅使用 HitType（Angled / HardBeat），按上游分类规则。
"""

from typing import TYPE_CHECKING, Optional, List
from enum import Enum

if TYPE_CHECKING:  # pragma: no cover - 类型提示
    from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject


class ComplexityEvaluator:
    mono_history_max_length = 5

    def __init__(self):
        # 历史最近 mono pattern 长度（不含当前进行中的 pattern）
        self.mono_history: List[int] = []
        self.previous_hit_type: Optional[HitType] = None
        self.current_mono_length: int = 0

    # ---- 公共接口 ----
    def evaluate_difficulty(self, current: 'TauDifficultyHitObject') -> float:
        tau_current = current  # 命名对齐

        # 长间隔 >=1000ms 视为节奏 / pattern 软重置
        if getattr(tau_current, 'delta_time', 0) >= 1000:
            self.mono_history.clear()
            self.current_mono_length = 1 if tau_current.base_object is not None else 0
            self.previous_hit_type = self._get_hit_type(tau_current)
            return 0.0

        object_strain = 0.0
        curr_type = self._get_hit_type(tau_current)

        if self.previous_hit_type is not None and curr_type != self.previous_hit_type:
            # 进入新 mono pattern
            object_strain = 1.0

            if len(self.mono_history) < 2:
                # 需要至少两个已完成 pattern 作为对比，否则不计入起始过渡难度
                object_strain = 0.0
            else:
                # (最后一个已完成 pattern 长度 + 当前未完成 pattern 长度) 的奇偶性调整
                last_len = self.mono_history[-1] if self.mono_history else 0
                if (last_len + self.current_mono_length) % 2 == 0:
                    object_strain *= 0.5
                else:
                    object_strain *= 1.5

            # 重复惩罚（实际上是降低重复收益）：先把当前结束的 mono pattern 加入历史再计算
            object_strain *= self._repetition_penalties()

            # 新 pattern 开始（当前击打物件属于新类型，长度记 1）
            self.current_mono_length = 1
        else:
            # 仍在同一 mono pattern 内
            self.current_mono_length += 1

        self.previous_hit_type = curr_type
        return object_strain

    # ---- 内部：重复模式检测 ----
    def _repetition_penalties(self) -> float:
        MOST_RECENT_PATTERNS_TO_COMPARE = 2
        penalty = 1.0

        # 记录刚刚完成的 mono pattern 长度
        self._enqueue_current_mono_length()

        # 从最靠后的可比较起点向前找第一个重复
        start_limit = len(self.mono_history) - MOST_RECENT_PATTERNS_TO_COMPARE - 1
        for start in range(start_limit, -1, -1):
            if not self._is_same_pattern(start, MOST_RECENT_PATTERNS_TO_COMPARE):
                continue
            # notesSince = 从重复起点到当前（含）所有 pattern 的总长度
            notes_since = sum(self.mono_history[start:])
            penalty *= self._repetition_penalty(notes_since)
            break

        return penalty

    def _enqueue_current_mono_length(self):
        if self.current_mono_length <= 0:
            return
        self.mono_history.append(self.current_mono_length)
        # 限制长度
        overflow = len(self.mono_history) - self.mono_history_max_length
        if overflow > 0:
            del self.mono_history[0:overflow]

    def _is_same_pattern(self, start: int, count: int) -> bool:
        # 对比 mono_history[start : start+count] 与 mono_history[-count:]
        tail = self.mono_history[-count:]
        segment = self.mono_history[start:start + count]
        if len(segment) != len(tail):
            return False
        for a, b in zip(segment, tail):
            if a != b:
                return False
        return True

    def _repetition_penalty(self, notes_since: int) -> float:
        return min(1.0, 0.032 * notes_since)

    # ---- HitType 判定 ----
    def _get_hit_type(self, hit_object: 'TauDifficultyHitObject') -> 'HitType':
        from ...objects import StrictHardBeat, SliderHardBeat, AngledTauHitObject, Slider
        base_object = hit_object.base_object
        # 与上游相同的判定顺序
        if base_object.__class__.__name__ == 'StrictHardBeat' or isinstance(base_object, StrictHardBeat):
            return HitType.HARD_BEAT
        if isinstance(base_object, Slider) and getattr(base_object, 'nested_hit_objects', None):
            first_nested = base_object.nested_hit_objects[0]
            if isinstance(first_nested, SliderHardBeat):
                return HitType.HARD_BEAT
        if isinstance(base_object, AngledTauHitObject):
            # 角度阈值分类：较大角度与较小角度视为不同类型，制造模式切换
            try:
                angle_val = float(getattr(base_object, 'angle', 0.0)) % 360
            except Exception:
                angle_val = 0.0
            # 阈值 45°：>=45 归为 ANGLED，<45 归为 HARD_BEAT，以便小幅往返保持单类型
            if angle_val >= 45.0:
                return HitType.ANGLED
            return HitType.HARD_BEAT
        return HitType.HARD_BEAT


class HitType(Enum):
    ANGLED = 'Angled'
    HARD_BEAT = 'HardBeat'

__all__ = ["ComplexityEvaluator", "HitType"]