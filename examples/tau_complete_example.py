"""
Tau模式完整示例
包含谱面创建、难度计算和PP计算
"""

from src.tau.attributes import BeatmapAttributesBuilder
from src.tau.objects import Beat, StrictHardBeat, HardBeat
from src.tau.beatmap import TauBeatmap
from src.tau.difficulty import TauDifficultyCalculator

def main():
    # 1. 创建谱面属性
    builder = BeatmapAttributesBuilder()
    attributes = builder.ar_value(9.0)\
                       .od_value(8.0)\
                       .cs_value(4.0)\
                       .hp_value(7.0)\
                       .with_clock_rate(1.0)\
                       .with_mods(0)\
                       .build()
    
    # 2. 创建谱面
    beatmap = TauBeatmap()
    
    # 添加普通Beat物件
    beat1 = Beat()
    beat1.start_time = 1000
    beat1.angle = 45
    beatmap.add_hit_object(beat1)
    
    # 添加HardBeat物件
    hard_beat = HardBeat()
    hard_beat.start_time = 2000
    hard_beat.angle = 90
    beatmap.add_hit_object(hard_beat)
    
    # 添加StrictHardBeat物件（替代Slider，因为Slider需要更复杂的设置）
    hard_beat2 = StrictHardBeat()
    hard_beat2.start_time = 3000
    hard_beat2.angle = 180
    beatmap.add_hit_object(hard_beat2)
    
    # 3. 难度计算
    mods = 0  # 无Mod
    difficulty_calc = TauDifficultyCalculator(beatmap, mods)
    difficulty_attributes = difficulty_calc.calculate()
    
    # 4. 输出结果
    print("\nTau模式谱面信息:")
    print(f"谱面物件数: {len(beatmap.hit_objects)}")
    print("\n谱面属性:")
    print(f"AR: {attributes.approach_rate}")
    print(f"OD: {attributes.overall_difficulty}")
    print(f"CS: {attributes.circle_size}")
    print(f"HP: {attributes.drain_rate}")
    
    print("\n难度属性:")
    print(f"星级: {difficulty_attributes.star_rating:.2f}")
    print(f"速度难度: {difficulty_attributes.speed_difficulty:.2f}")
    print(f"准度难度: {difficulty_attributes.aim_difficulty:.2f}")


if __name__ == "__main__":
    main()