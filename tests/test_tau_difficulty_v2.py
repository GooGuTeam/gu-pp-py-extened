import math
from tau.beatmap import TauBeatmap
from tau.objects import Beat, Slider, SliderNode, PolarSliderPath
from tau.difficulty.calculator import TauDifficultyCalculatorV2


def make_simple_map():
    bm = TauBeatmap()
    t = 0
    # 5 beats spaced 500ms
    for i in range(5):
        b = Beat()
        b.start_time = t
        b.angle = (i * 45) % 360
        bm.add_hit_object(b)
        t += 500
    # add one simple slider between last two times
    s = Slider()
    s.start_time = 2600
    s.angle = 180
    s.path = PolarSliderPath([SliderNode(0, 180), SliderNode(300, 270)])
    s.repeat_count = 0
    bm.add_hit_object(s)
    return bm


def test_v2_basic_attributes():
    bm = make_simple_map()
    v2 = TauDifficultyCalculatorV2(bm).calculate()

    # star rating should be non-negative
    assert v2.star_rating >= 0
    # counts
    assert v2.notes_count == 5  # beats
    assert v2.slider_count == 1
    # slider factor bounded
    assert 0 <= v2.slider_factor <= 1.0
    # aim non-negative
    assert v2.aim_difficulty >= 0
    # approach_rate 合理范围校验
    assert 0 <= v2.approach_rate <= 11
