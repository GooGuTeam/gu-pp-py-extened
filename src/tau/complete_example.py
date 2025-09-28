"""
Tau完整示例：展示如何使用难度和性能计算器
"""

from .beatmap import TauBeatmap
from .objects import Beat, Slider, HardBeat, PolarSliderPath, SliderNode
from .difficulty.difficultyCalculator import TauDifficultyCalculator
from .performance.tauPerformanceCalculator import TauPerformanceCalculator
from .mods import TauMods


def create_sample_beatmap() -> TauBeatmap:
    """创建示例谱面"""
    beatmap = TauBeatmap()
    
    # 设置难度属性
    beatmap.difficulty_attributes = {
        'approach_rate': 9.0,
        'overall_difficulty': 8.0,
        'circle_size': 4.0,
        'drain_rate': 5.0
    }
    
    # 添加一些示例物件
    # 添加一些Beat物件
    for i in range(10):
        beat = Beat()
        beat.start_time = i * 500  # 每0.5秒一个物件
        beat.angle = (i * 36) % 360  # 角度递增36度
        beatmap.hit_objects.append(beat)
    
    # 添加一些HardBeat物件
    for i in range(5):
        hard_beat = HardBeat()
        hard_beat.start_time = (i * 2 + 10) * 500  # 从第5秒开始，每隔1秒一个
        beatmap.hit_objects.append(hard_beat)
    
    # 添加一个Slider物件
    slider = Slider()
    slider.start_time = 15 * 500  # 从第15秒开始
    slider.angle = 45  # 起始角度45度
    
    # 创建滑条路径
    nodes = [
        SliderNode(0, 45),
        SliderNode(200, 90),
        SliderNode(400, 135),
        SliderNode(600, 180)
    ]
    slider.path = PolarSliderPath(nodes)
    slider.repeat_count = 1  # 1次重复
    
    beatmap.hit_objects.append(slider)
    
    return beatmap


def main():
    """主函数"""
    print("=== Tau难度和性能计算示例 ===\n")
    
    # 创建示例谱面
    beatmap = create_sample_beatmap()
    print(f"创建了包含{len(beatmap.hit_objects)}个物件的示例谱面")
    for stat in beatmap.get_statistics():
        print(f"  {stat.name}: {stat.content}")
    print()
    
    # 创建难度计算器（无mod）
    difficulty_calculator = TauDifficultyCalculator(beatmap, 0)
    
    # 计算难度
    print("计算谱面难度（无mod）...")
    difficulty_attributes = difficulty_calculator.calculate()
    print(f"  星级: {difficulty_attributes.star_rating:.2f}")
    print(f"  Aim难度: {difficulty_attributes.aim_difficulty:.2f}")
    print(f"  Speed难度: {difficulty_attributes.speed_difficulty:.2f}")
    print(f"  Complexity难度: {difficulty_attributes.complexity_difficulty:.2f}")
    print(f"  AR: {difficulty_attributes.approach_rate:.2f}")
    print(f"  OD: {difficulty_attributes.overall_difficulty:.2f}")
    print(f"  最大连击数: {difficulty_attributes.max_combo}")
    print()
    
    # 创建难度计算器（DT mod）
    dt_difficulty_calculator = TauDifficultyCalculator(beatmap, TauMods.DOUBLE_TIME)
    
    # 计算DT下的难度
    print("计算谱面难度（DT mod）...")
    dt_difficulty_attributes = dt_difficulty_calculator.calculate()
    print(f"  星级: {dt_difficulty_attributes.star_rating:.2f}")
    print(f"  Aim难度: {dt_difficulty_attributes.aim_difficulty:.2f}")
    print(f"  Speed难度: {dt_difficulty_attributes.speed_difficulty:.2f}")
    print(f"  Complexity难度: {dt_difficulty_attributes.complexity_difficulty:.2f}")
    print(f"  AR: {dt_difficulty_attributes.approach_rate:.2f}")
    print(f"  OD: {dt_difficulty_attributes.overall_difficulty:.2f}")
    print(f"  最大连击数: {dt_difficulty_attributes.max_combo}")
    print()
    
    # 创建性能计算器
    performance_calculator = TauPerformanceCalculator()
    
    # 模拟一个高分成绩
    high_score = {
        'accuracy': 0.99,  # 99%准确率
        'max_combo': difficulty_attributes.max_combo,  # 完整连击
        'mods': 0,  # 无mod
        'statistics': {
            'great': 14,  # Great判定数
            'ok': 1,      # Ok判定数
            'miss': 0     # 失误数
        }
    }
    
    # 计算性能值
    print("计算高分成绩的性能值...")
    high_performance = performance_calculator.calculate(high_score, difficulty_attributes)
    print(f"  总性能: {high_performance.total:.2f}")
    print(f"  Aim性能: {high_performance.aim:.2f}")
    print(f"  Speed性能: {high_performance.speed:.2f}")
    print(f"  Accuracy性能: {high_performance.accuracy:.2f}")
    print(f"  Complexity性能: {high_performance.complexity:.2f}")
    print()
    
    # 模拟一个较低分数的成绩
    low_score = {
        'accuracy': 0.85,  # 85%准确率
        'max_combo': int(difficulty_attributes.max_combo * 0.7),  # 70%连击
        'mods': 0,  # 无mod
        'statistics': {
            'great': 10,  # Great判定数
            'ok': 2,      # Ok判定数
            'miss': 3     # 失误数
        }
    }
    
    # 计算性能值
    print("计算较低分数成绩的性能值...")
    low_performance = performance_calculator.calculate(low_score, difficulty_attributes)
    print(f"  总性能: {low_performance.total:.2f}")
    print(f"  Aim性能: {low_performance.aim:.2f}")
    print(f"  Speed性能: {low_performance.speed:.2f}")
    print(f"  Accuracy性能: {low_performance.accuracy:.2f}")
    print(f"  Complexity性能: {low_performance.complexity:.2f}")
    print()
    
    print("=== 示例完成 ===")


if __name__ == "__main__":
    main()