from tau.beatmap import TauBeatmap
from tau.objects import Beat
from tau.difficulty.calculator import TauDifficultyCalculatorV2


def _make_pattern_map(pattern_angles):
    bm = TauBeatmap()
    t = 0
    last_angle = 0
    # seed first beat
    b0 = Beat(); b0.start_time = t; b0.angle = last_angle; bm.add_hit_object(b0)
    t += 250
    for a in pattern_angles:
        b = Beat(); b.start_time = t; b.angle = a; bm.add_hit_object(b)
        t += 250
    return bm


def test_complexity_alternating_higher():
    # 重复模式：角度小幅往返 0,5,0,5,...
    repetitive = _make_pattern_map([5,0,5,0,5,0,5,0])
    # 交替大跨度：0,70,10,80,... 制造不同 angle/rhythm bucket
    alternating = _make_pattern_map([70,10,80,15,90,20,100,25])

    rep_attr = TauDifficultyCalculatorV2(repetitive).calculate()
    alt_attr = TauDifficultyCalculatorV2(alternating).calculate()

    # 交替应有更高 complexity
    assert alt_attr.complexity_difficulty >= rep_attr.complexity_difficulty
    # 且至少要有明显差距（避免两者都 0）
    assert alt_attr.complexity_difficulty - rep_attr.complexity_difficulty > 0.0001