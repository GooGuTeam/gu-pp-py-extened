"""
Tau性能计算器使用示例
"""

from ..attributes import TauDifficultyAttributes
from .tauPerformanceCalculator import TauPerformanceCalculator


def example_usage():
    """示例用法"""
    # 创建难度属性
    difficulty_attributes = TauDifficultyAttributes(
        star_rating=5.25,
        aim_difficulty=3.15,
        speed_difficulty=2.85,
        complexity_difficulty=4.20,
        approach_rate=9.2,
        overall_difficulty=8.5,
        drain_rate=5.0,
        slider_factor=0.85,
        notes_count=1245,
        slider_count=321,
        hard_beat_count=42,
        max_combo=1876
    )
    
    # 创建分数信息
    score = {
        'accuracy': 0.985,  # 98.5%准确率
        'max_combo': 1789,  # 最大连击数
        'mods': 0,  # 无mod
        'statistics': {
            'great': 1230,  # Great判定数
            'ok': 15,       # Ok判定数
            'miss': 0       # 失误数
        }
    }
    
    # 创建性能计算器
    calculator = TauPerformanceCalculator()
    
    # 计算性能值
    performance = calculator.calculate(score, difficulty_attributes)
    
    # 输出结果
    print("Tau性能计算结果:")
    print(f"  Aim性能: {performance.aim:.2f}")
    print(f"  Speed性能: {performance.speed:.2f}")
    print(f"  Accuracy性能: {performance.accuracy:.2f}")
    print(f"  Complexity性能: {performance.complexity:.2f}")
    print(f"  总性能: {performance.total:.2f}")
    print(f"  有效失误数: {performance.effective_miss_count:.2f}")


if __name__ == "__main__":
    example_usage()