"""Upstream-aligned Tau difficulty calculator (steps A-D).

Implements:
 A. CreateDifficultyHitObjects (with clock rate & angled link)
 B. CreateSkills (Aim(AimNoSliders), Speed, Complexity) using new skill framework
 C. Aggregate TauDifficultyAttributes incl. counts & slider_factor
 D. Ensure evaluator state (Complexity) reset per calculation

Notes:
 - Preempt / AR uses DifficultyRange(AR, 1800,1200,450)
 - Great window approximated via OD formula (placeholder until dedicated HitWindows)
 - Mods (Relax/Autopilot) zero out skill pairs as upstream
"""
from __future__ import annotations
import math
from typing import List

from ..beatmap import TauBeatmap
from ..objects import Beat, Slider, HardBeat, StrictHardBeat, SliderRepeat, TauHitObject, AngledTauHitObject
from ..mods import TauMods
from ..attributes import TauDifficultyAttributes

from .preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from .preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject
from .skills.aim import Aim
from .skills.speed import Speed
from .skills.complexity import Complexity
from .cached import build_cached_properties, TauCachedProperties

DIFFICULTY_MULTIPLIER = 0.0820

class TauDifficultyCalculatorV2:
    def __init__(self, beatmap: TauBeatmap, mods: int = 0):
        self.beatmap = beatmap
        self.mods = TauMods(mods)

    # Public API similar to previous calculate()
    def calculate(self) -> TauDifficultyAttributes:
        if not self.beatmap.hit_objects:
            return TauDifficultyAttributes()

        clock_rate = self._get_clock_rate()
    # ComplexityEvaluator 由 Complexity 技能内部自管理实例，无需外部 reset
        # Build cached properties (future use by evaluators). Currently non-intrusive.
        self._cached = build_cached_properties(
            self.beatmap.hit_objects,
            self.beatmap.difficulty_attributes.get('overall_difficulty', 5.0)
        )

        diff_objects = self._create_difficulty_hit_objects(clock_rate)
        skills = self._create_skills(clock_rate)

        # (debug removed)

        for skill in skills:
            for obj in diff_objects:
                skill.process(obj)

        aim = math.sqrt(skills[0].difficulty_value()) * DIFFICULTY_MULTIPLIER
        aim_no_sliders = math.sqrt(skills[1].difficulty_value()) * DIFFICULTY_MULTIPLIER
        speed = math.sqrt(skills[2].difficulty_value()) * DIFFICULTY_MULTIPLIER
        complexity = math.sqrt(skills[3].difficulty_value()) * DIFFICULTY_MULTIPLIER

        # Mod adjustments
        if self.mods & TauMods.RELAX:
            speed = 0.0
            complexity = 0.0
        if self.mods & TauMods.AUTOPILOT:
            aim = 0.0
            aim_no_sliders = 0.0

        # AR / Preempt
        ar = self.beatmap.difficulty_attributes.get('approach_rate', 5.0)
        preempt = self._difficulty_range(ar, 1800, 1200, 450) / clock_rate
        approach_rate = self._approach_from_preempt(preempt)

        base_aim = self._base_skill(aim)
        base_speed = self._base_skill(speed)
        base_complexity = self._base_skill(complexity)

        base_performance = math.pow(
            math.pow(base_aim, 1.1) + math.pow(base_speed, 1.1) + math.pow(base_complexity, 1.1),
            1.0 / 1.1
        )
        star_rating = (
            math.pow(1.12, 1/3) * 0.027 * (math.pow(100000 / math.pow(2, 1 / 1.1) * base_performance, 1/3) + 4)
            if base_performance > 1e-5 else 0.0
        )

        notes_count = sum(isinstance(o, Beat) for o in self.beatmap.hit_objects)
        slider_count = sum(isinstance(o, Slider) for o in self.beatmap.hit_objects)
        hard_beat_count = sum(isinstance(o, HardBeat) for o in self.beatmap.hit_objects)
        slider_factor = aim_no_sliders / aim if aim > 0 else 1.0

        return TauDifficultyAttributes(
            star_rating=star_rating,
            aim_difficulty=aim,
            speed_difficulty=speed,
            complexity_difficulty=complexity,
            approach_rate=approach_rate,
            overall_difficulty=self.beatmap.difficulty_attributes.get('overall_difficulty', 5.0),
            drain_rate=self.beatmap.difficulty_attributes.get('drain_rate', 5.0),
            slider_factor=slider_factor,
            notes_count=notes_count,
            slider_count=slider_count,
            hard_beat_count=hard_beat_count,
            max_combo=self._get_max_combo(),
            mods=[self.mods]
        )

    # ---- internal helpers ----
    def _create_difficulty_hit_objects(self, clock_rate: float) -> List[TauDifficultyHitObject]:
        diff: List[TauDifficultyHitObject] = []
        last: TauHitObject | None = None
        last_angled: TauAngledDifficultyHitObject | None = None
        for hit in self.beatmap.hit_objects:
            if last is not None:
                if isinstance(hit, AngledTauHitObject):
                    obj = TauAngledDifficultyHitObject(hit, last, clock_rate, diff, len(diff), last_angled)
                    diff.append(obj)
                    last_angled = obj
                else:
                    diff.append(TauDifficultyHitObject(hit, last, clock_rate, diff, len(diff)))
            last = hit
        return diff

    def _create_skills(self, clock_rate: float):
        od = self.beatmap.difficulty_attributes.get('overall_difficulty', 5.0)
        great_win = self._great_window(od) / clock_rate
        return [
            Aim(self.mods, [Beat, StrictHardBeat, SliderRepeat, Slider]),
            Aim(self.mods, [Beat, StrictHardBeat]),
            Speed(self.mods, great_win),
            Complexity(self.mods)
        ]

    def _great_window(self, od: float) -> float:
        return (127 - 3 * od) if od <= 5 else (112 - 3 * (od - 5))

    def _difficulty_range(self, value: float, min_: float, mid: float, max_: float) -> float:
        if value > 5:
            return mid + (max_ - mid) * (value - 5) / 5
        if value < 5:
            return mid - (mid - min_) * (5 - value) / 5
        return mid

    def _approach_from_preempt(self, preempt: float) -> float:
        return (1800 - preempt) / 120 if preempt > 1200 else (1200 - preempt) / 150 + 5

    def _base_skill(self, v: float) -> float:
        return math.pow(5 * max(1.0, v / 0.0675) - 4.0, 3.0) / 100000.0

    def _get_max_combo(self) -> int:
        max_combo = 0
        for obj in self.beatmap.hit_objects:
            max_combo += 1
            if isinstance(obj, Slider):
                max_combo += obj.repeat_count + 1
        return max_combo

    def _get_clock_rate(self) -> float:
        rate = 1.0
        if self.mods & TauMods.DOUBLE_TIME:
            rate *= 1.5
        elif self.mods & TauMods.HALF_TIME:
            rate *= 0.75
        return rate
