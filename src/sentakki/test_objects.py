"""
测试Sentakki游戏物件
"""

from . import *


def test_objects():
    # 测试基础对象
    hit_object = HitObject()
    hit_object.start_time = 1000.0
    assert hit_object.start_time == 1000.0
    
    # 测试SentakkiHitObject
    sentakki_object = SentakkiHitObject()
    sentakki_object.start_time = 1500.0
    assert sentakki_object.start_time == 1500.0
    assert sentakki_object.base_score_weighting == 1
    assert sentakki_object.score_weighting == 1
    
    # 测试break状态
    sentakki_object.break_state = True
    assert sentakki_object.score_weighting == 5
    
    # 测试轨道对象
    laned_object = SentakkiLanedHitObject()
    laned_object.lane = 3
    assert laned_object.lane == 3
    
    # 测试Tap对象
    tap = Tap()
    tap.lane = 2
    tap.start_time = 2000.0
    assert tap.lane == 2
    assert tap.start_time == 2000.0
    
    # 测试Hold对象
    hold = Hold()
    hold.lane = 1
    hold.start_time = 2500.0
    hold.duration = 1000.0
    assert hold.lane == 1
    assert hold.start_time == 2500.0
    assert hold.duration == 1000.0
    assert hold.end_time == 3500.0
    
    # 测试Touch对象
    touch = Touch()
    touch.position = (100.0, 200.0)
    touch.start_time = 3000.0
    assert touch.position == (100.0, 200.0)
    assert touch.start_time == 3000.0
    
    # 测试Slide对象
    slide = Slide()
    slide.lane = 4
    slide.start_time = 3500.0
    slide.duration = 1500.0
    assert slide.lane == 4
    assert slide.start_time == 3500.0
    assert slide.duration == 1500.0
    assert slide.end_time == 5000.0
    
    # 测试SlideTap对象
    slide_tap = SlideTap()
    slide_tap.lane = 5
    slide_tap.start_time = 4000.0
    assert slide_tap.lane == 5
    assert slide_tap.start_time == 4000.0
    
    # 测试HoldHead对象
    hold_head = HoldHead()
    hold_head.lane = 6
    hold_head.start_time = 4500.0
    assert hold_head.lane == 6
    assert hold_head.start_time == 4500.0
    
    # 测试SlideCheckpoint对象
    checkpoint = SlideCheckpoint()
    checkpoint.start_time = 5000.0
    checkpoint.progress = 0.5
    assert checkpoint.start_time == 5000.0
    assert checkpoint.progress == 0.5
    
    # 测试CheckpointNode对象
    node = CheckpointNode((300.0, 400.0))
    node.start_time = 5500.0
    node.position = (350.0, 450.0)
    assert node.start_time == 5500.0
    assert node.position == (350.0, 450.0)
    
    print("所有测试通过！")


if __name__ == "__main__":
    test_objects()