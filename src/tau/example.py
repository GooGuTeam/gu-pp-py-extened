"""
Tau属性系统使用示例
"""

from .attributes import BeatmapAttributesBuilder, TauDifficultyAttributes
from .objects import Beat, Slider, HardBeat
from .beatmap import TauBeatmap


def example_usage():
    """示例用法"""
    # 创建谱面属性构建器
    builder = BeatmapAttributesBuilder()
    
    # 设置基础属性
    builder.ar_value(9.0) \
           .od_value(8.0) \
           .cs_value(4.0) \
           .hp_value(7.0) \
           .with_clock_rate(1.2) \
           .with_mods(16)  # HR mod
    
    # 构建属性
    attributes = builder.build()
    
    print("谱面属性:")
    print(f"  AR: {attributes.approach_rate}")
    print(f"  OD: {attributes.overall_difficulty}")
    print(f"  CS: {attributes.circle_size}")
    print(f"  HP: {attributes.drain_rate}")
    print(f"  时钟速率: {attributes.clock_rate}")
    
    if attributes.hit_windows:
        print("击打时间窗口:")
        print(f"  Great: {attributes.hit_windows.great}ms")
        print(f"  Ok: {attributes.hit_windows.ok}ms")
    
    # 创建谱面
    beatmap = TauBeatmap()
    
    # 添加一些物件
    beat1 = Beat()
    beat1.start_time = 1000
    beat1.angle = 45
    
    beat2 = Beat()
    beat2.start_time = 2000
    beat2.angle = 90
    
    slider = Slider()
    slider.start_time = 3000
    slider.angle = 180
    slider.repeat_count = 1
    
    hard_beat = HardBeat()
    hard_beat.start_time = 4000
    
    beatmap.hit_objects.extend([beat1, beat2, slider, hard_beat])
    
    # 显示统计信息
    stats = beatmap.get_statistics()
    print("\n谱面统计:")
    for stat in stats:
        print(f"  {stat.name}: {stat.content}")
    
    # 创建难度属性
    difficulty = TauDifficultyAttributes()
    difficulty.star_rating = 5.2
    difficulty.aim_difficulty = 3.1
    difficulty.speed_difficulty = 2.8
    difficulty.complexity_difficulty = 1.9
    difficulty.approach_rate = attributes.approach_rate
    difficulty.overall_difficulty = attributes.overall_difficulty
    difficulty.drain_rate = attributes.drain_rate
    difficulty.slider_factor = 0.7
    difficulty.notes_count = 150
    difficulty.slider_count = 30
    difficulty.hard_beat_count = 10
    difficulty.max_combo = 200
    
    print("\n难度属性:")
    print(f"  难度星级: {difficulty.star_rating}")
    print(f"  Aim难度: {difficulty.aim_difficulty}")
    print(f"  Speed难度: {difficulty.speed_difficulty}")
    print(f"  复杂度难度: {difficulty.complexity_difficulty}")
    print(f"  滑条因子: {difficulty.slider_factor}")
    print(f"  最大连击数: {difficulty.max_combo}")


if __name__ == "__main__":
    example_usage()