import math
from tau.beatmap import TauBeatmap
from tau.objects import Beat
from tau.difficulty import TauDifficultyCalculator


def _make_map_with_angles(delta_angle: float):
    bm = TauBeatmap()
    # first beat
    b1 = Beat(); b1.start_time = 0; b1.angle = 0; bm.add_hit_object(b1)
    # second beat (provides last_angled for the third)
    b2 = Beat(); b2.start_time = 500; b2.angle = 15; bm.add_hit_object(b2)
    # third beat with desired delta from second
    b3 = Beat(); b3.start_time = 1000; b3.angle = delta_angle; bm.add_hit_object(b3)
    return bm


def test_angle_range_gating_aim():
    # Small delta angle (likely below computed angle_range) => aim difficulty ~ 0
    # small final angle => delta from second (15) = 5 (< angle_range ~9) => gated
    small_map = _make_map_with_angles(20)
    # large final angle => delta from second (15) = 75 (> angle_range) => contributes
    large_map = _make_map_with_angles(90)

    small_attrs = TauDifficultyCalculator(small_map).calculate()
    large_attrs = TauDifficultyCalculator(large_map).calculate()

    # 断言大角度的 aim 难度应显著高于小角度 (小角度可被 gating 掉接近 0)
    # 大角度应该能产生非零 aim
    assert large_attrs.aim_difficulty > 0
    # 小角度被 gating
    assert small_attrs.aim_difficulty == 0
    # 且大角度 > 小角度
    assert large_attrs.aim_difficulty > small_attrs.aim_difficulty