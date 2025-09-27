"""
Tau Mods系统使用示例
"""

from .attributes import BeatmapAttributesBuilder
from .mods import TauMods, get_mod_score_multiplier


def example_usage():
    """示例用法"""
    # 创建谱面属性构建器
    builder = BeatmapAttributesBuilder()
    
    # 设置基础属性
    builder.ar_value(9.0) \
           .od_value(8.0) \
           .cs_value(4.0) \
           .hp_value(7.0) \
           .with_clock_rate(1.0)
    
    # 构建基础属性
    base_attributes = builder.build()
    
    print("基础谱面属性:")
    print(f"  AR: {base_attributes.approach_rate}")
    print(f"  OD: {base_attributes.overall_difficulty}")
    print(f"  CS: {base_attributes.circle_size}")
    print(f"  HP: {base_attributes.drain_rate}")
    if base_attributes.hit_windows:
        print(f"  Great窗口: {base_attributes.hit_windows.great}ms")
        print(f"  Ok窗口: {base_attributes.hit_windows.ok}ms")
    
    # 应用HR mod
    hr_builder = BeatmapAttributesBuilder()
    hr_builder.ar_value(9.0) \
              .od_value(8.0) \
              .cs_value(4.0) \
              .hp_value(7.0) \
              .with_clock_rate(1.0) \
              .with_mods(int(TauMods.HARD_ROCK))
    
    hr_attributes = hr_builder.build()
    
    print("\n应用HR mod后的属性:")
    print(f"  AR: {hr_attributes.approach_rate}")
    print(f"  OD: {hr_attributes.overall_difficulty}")
    print(f"  CS: {hr_attributes.circle_size}")
    print(f"  HP: {hr_attributes.drain_rate}")
    if hr_attributes.hit_windows:
        print(f"  Great窗口: {hr_attributes.hit_windows.great}ms")
        print(f"  Ok窗口: {hr_attributes.hit_windows.ok}ms")
    
    # 应用DT mod
    dt_builder = BeatmapAttributesBuilder()
    dt_builder.ar_value(9.0) \
              .od_value(8.0) \
              .cs_value(4.0) \
              .hp_value(7.0) \
              .with_clock_rate(1.0) \
              .with_mods(int(TauMods.DOUBLE_TIME))
    
    dt_attributes = dt_builder.build()
    
    print("\n应用DT mod后的属性:")
    print(f"  AR: {dt_attributes.approach_rate}")
    print(f"  OD: {dt_attributes.overall_difficulty}")
    print(f"  CS: {dt_attributes.circle_size}")
    print(f"  HP: {dt_attributes.drain_rate}")
    print(f"  时钟速率: {dt_attributes.clock_rate}")
    if dt_attributes.hit_windows:
        print(f"  Great窗口: {dt_attributes.hit_windows.great}ms")
        print(f"  Ok窗口: {dt_attributes.hit_windows.ok}ms")
    
    # 应用EZ mod
    ez_builder = BeatmapAttributesBuilder()
    ez_builder.ar_value(9.0) \
              .od_value(8.0) \
              .cs_value(4.0) \
              .hp_value(7.0) \
              .with_clock_rate(1.0) \
              .with_mods(int(TauMods.EASY))
    
    ez_attributes = ez_builder.build()
    
    print("\n应用EZ mod后的属性:")
    print(f"  AR: {ez_attributes.approach_rate}")
    print(f"  OD: {ez_attributes.overall_difficulty}")
    print(f"  CS: {ez_attributes.circle_size}")
    print(f"  HP: {ez_attributes.drain_rate}")
    if ez_attributes.hit_windows:
        print(f"  Great窗口: {ez_attributes.hit_windows.great}ms")
        print(f"  Ok窗口: {ez_attributes.hit_windows.ok}ms")
    
    # 显示不同mod组合的分数倍数
    print("\n不同mod组合的分数倍数:")
    mod_combinations = [
        (TauMods.NOMOD, "No Mod"),
        (TauMods.HARD_ROCK, "HR"),
        (TauMods.DOUBLE_TIME, "DT"),
        (TauMods.HALF_TIME, "HT"),
        (TauMods.EASY, "EZ"),
        (TauMods.HARD_ROCK | TauMods.DOUBLE_TIME, "HRDT"),
        (TauMods.HARD_ROCK | TauMods.EASY, "HREZ"),
        (TauMods.DOUBLE_TIME | TauMods.EASY, "DTEZ"),
    ]
    
    for mods, name in mod_combinations:
        multiplier = get_mod_score_multiplier(mods)
        print(f"  {name}: {multiplier:.2f}x")


if __name__ == "__main__":
    example_usage()