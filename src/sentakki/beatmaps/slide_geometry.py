from __future__ import annotations
from math import pi

LANE_COUNT = 8
LANE_ANGLE = 2 * pi / LANE_COUNT

SHAPE_BASE_ANGLE = {
    'linear': 0.0,
    'circle_cw': LANE_ANGLE * 1.0,
    'circle_ccw': -LANE_ANGLE * 1.0,
    'zigzag': LANE_ANGLE * 0.9,
    'fan': LANE_ANGLE * 2.0,
}

def part_angle(shape: str, mirrored: bool) -> float:
    base = SHAPE_BASE_ANGLE.get(shape, 0.0)
    if 'fan' in shape and mirrored:
        return -base
    if shape == 'zigzag' and mirrored:
        return -base
    return base

def angle_to_lane_delta(angle_acc: float) -> int:
    if abs(angle_acc) < 1e-6:
        return 0
    return int(round(angle_acc / LANE_ANGLE))

__all__ = ['part_angle','angle_to_lane_delta','LANE_ANGLE']
