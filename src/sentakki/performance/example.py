"""
Sentakki性能(PP)计算示例
"""

from ..difficulty.difficultyCalculator import SentakkiDifficultyCalculator
from ..difficulty.sentakkiDifficultyAttributes import SentakkiDifficultyAttributes
from ..performance.sentakkiPerformanceCalculator import SentakkiPerformanceCalculator
from ..beatmap import SentakkiBeatmap


def main():
    """主函数"""
    # 创建示例谱面
    beatmap = SentakkiBeatmap()
    
    # 添加一些示例物件
    from ..tap import Tap
    from ..hold import Hold
    from ..touch import Touch
    from ..slide import Slide
    
    # 添加一些示例物件
    tap1 = Tap()
    tap1.start_time = 1000.0
    tap1.lane = 3
    beatmap.add_hit_object(tap1)
    
    tap2 = Tap()
    tap2.start_time = 1500.0
    tap2.lane = 5
    beatmap.add_hit_object(tap2)
    
    hold = Hold()
    hold.start_time = 2000.0
    hold.lane = 1
    hold.duration = 1000.0
    beatmap.add_hit_object(hold)
    
    touch = Touch()
    touch.start_time = 3000.0
    touch.position = (200.0, 150.0)
    beatmap.add_hit_object(touch)
    
    slide = Slide()
    slide.start_time = 4000.0
    slide.lane = 7
    slide.duration = 1500.0
    beatmap.add_hit_object(slide)
    
    # 创建难度计算器
    difficulty_calculator = SentakkiDifficultyCalculator(beatmap)
    
    # 计算难度属性
    difficulty_attributes = difficulty_calculator.calculate()
    
    # 创建性能计算器
    performance_calculator = SentakkiPerformanceCalculator()
    
    # 模拟玩家分数信息
    score_info = {
        'accuracy': 0.95,  # 95%准确率
        'count_miss': 2,   # 2个Miss
        'max_combo': 1200, # 玩家达到的最高连击
        'achievable_combo': 1500  # 谱面理论最高连击
    }
    
    # 计算性能值(PP)
    performance_attributes = performance_calculator.calculate(score_info, difficulty_attributes)
    
    # 输出结果
    print("=== Sentakki性能(PP)计算结果 ===")
    print(f"星级评分: {difficulty_attributes.star_rating:.2f}★")
    print(f"最大连击: {difficulty_attributes.max_combo}")
    print(f"玩家准确率: {score_info['accuracy'] * 100:.1f}%")
    print(f"玩家Miss数: {score_info['count_miss']}")
    print(f"玩家最高连击: {score_info['max_combo']}")
    print(f"\n性能值(PP): {performance_attributes['total']:.2f}")
    print(f"基础PP: {performance_attributes['base_pp']:.2f}")
    print(f"长度奖励: {performance_attributes['length_bonus']:.2f}")


if __name__ == "__main__":
    main()