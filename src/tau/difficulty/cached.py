"""Caching structures for tau difficulty preprocessing.

This introduces a light-weight cache similar in spirit to upstream implementations
so future evaluators (especially Complexity) can access pre-computed geometric and
slider traversal data without recomputing per skill.

Current usage: Built once inside TauDifficultyCalculatorV2.calculate() and can be
extended later. For now it does not alter existing difficulty semantics; angle_range
on objects is only populated if absent (>0 left untouched) to avoid side-effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..objects import AngledTauHitObject, Slider, TauHitObject, StrictHardBeat


@dataclass
class TauCachedProperties:
    base_object: AngledTauHitObject
    absolute_angle: float
    normalized_angle: float
    angle_range: float
    travel_distance: float
    lazy_travel_distance: float
    travel_time: float


def _normalize_angle(angle: float) -> float:
    if angle < 0:
        angle %= 360
    if angle >= 360:
        angle %= 360
    return angle


def _angle_range_from_od(od: float) -> float:
        """Compute a base angle range (in degrees) from overall difficulty.

        Assumption (placeholder until upstream spec is available):
            - OD0  -> wide lenience 14°
            - OD5  -> mid          9°
            - OD10 -> tight        5°
        Linear interpolation across OD.
        """
        od = max(0.0, min(10.0, od))
        # piecewise linear: map [0,5] 14->9, [5,10] 9->5
        if od <= 5:
                return 14 - (14 - 9) * (od / 5)
        return 9 - (9 - 5) * ((od - 5) / 5)


def build_cached_properties(hit_objects: List[TauHitObject], overall_difficulty: float = 5.0) -> Dict[int, TauCachedProperties]:
    """Create cached properties for all angled tau hit objects.

    Args:
        hit_objects: raw beatmap hit object list in time order.
    Returns:
        dict keyed by id(base_object) -> TauCachedProperties
    """
    cache: Dict[int, TauCachedProperties] = {}
    for obj in hit_objects:
        if not isinstance(obj, AngledTauHitObject):
            continue

        # Derive absolute & normalized angles (with potential offset if it exists)
        offset = 0.0
        if hasattr(obj, 'get_offset_angle') and callable(getattr(obj, 'get_offset_angle')):
            try:
                offset = float(obj.get_offset_angle())
            except Exception:
                offset = 0.0
        absolute_angle = obj.angle + offset
        normalized_angle = _normalize_angle(absolute_angle)

        # Angle range: keep existing if already set, else leave 0 for now (future: compute based on difficulty settings)
        angle_range = getattr(obj, 'angle_range', 0.0) or 0.0
        if angle_range <= 0:
            # Base range from OD
            angle_range = _angle_range_from_od(overall_difficulty)
            # StrictHardBeat 可按自身range属性（假定其定义为命中区域宽度角度）再扩大 50%
            if isinstance(obj, StrictHardBeat):
                try:
                    strict_range = float(getattr(obj, 'range', 0.0))
                    if strict_range > 0:
                        angle_range = max(angle_range, strict_range * 1.5)
                except Exception:
                    pass

        travel_distance = 0.0
        lazy_travel_distance = 0.0
        travel_time = 0.0
        if isinstance(obj, Slider) and obj.path is not None:
            # Use path's precalculated metrics
            try:
                travel_distance = getattr(obj.path, 'calculated_distance', 0.0)
            except Exception:
                travel_distance = 0.0
            # Lazy travel distance uses angle_range/2 as tolerance if available
            if hasattr(obj.path, 'calculate_lazy_distance'):
                try:
                    lazy_travel_distance = obj.path.calculate_lazy_distance(angle_range / 2 if angle_range else 0.0)
                except Exception:
                    lazy_travel_distance = 0.0
            # Duration is property on Slider
            try:
                travel_time = obj.duration
            except Exception:
                travel_time = 0.0

        cache[id(obj)] = TauCachedProperties(
            base_object=obj,
            absolute_angle=absolute_angle,
            normalized_angle=normalized_angle,
            angle_range=angle_range,
            travel_distance=travel_distance,
            lazy_travel_distance=lazy_travel_distance,
            travel_time=travel_time,
        )

        # Always ensure object has the computed angle_range to allow gating in Aim
        setattr(obj, 'angle_range', angle_range)

    return cache


__all__ = [
    'TauCachedProperties',
    'build_cached_properties',
]
