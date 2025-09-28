"""
Sentakki模式完整示例
包含谱面创建、难度计算和PP计算
"""

from src.sentakki.beatmap import SentakkiBeatmap
from src.sentakki.tap import Tap
from src.sentakki.hold import Hold
from src.sentakki.touch import Touch
from src.sentakki.slide import Slide
from src.sentakki.difficulty.difficultyCalculator import SentakkiDifficultyCalculator
from src.sentakki.performance.sentakkiPerformanceCalculator import SentakkiPerformanceCalculator

def main():
    # 1. 创建谱面
    beatmap = SentakkiBeatmap()
    
    # 添加Tap音符
    tap1 = Tap()
    tap1.start_time = 1000.0
    tap1.lane = 3
    beatmap.add_hit_object(tap1)
    
    tap2 = Tap()
    tap2.start_time = 1500.0
    tap2.lane = 5
    beatmap.add_hit_object(tap2)
    
    # 添加Hold音符
    hold = Hold()
    hold.start_time = 2000.0
    hold.lane = 1
    hold.duration = 1000.0
    beatmap.add_hit_object(hold)
    
    # 添加Touch音符
    touch = Touch()
    touch.start_time = 3000.0
    touch.position = (200.0, 150.0)
    beatmap.add_hit_object(touch)
    
    # 添加Slide音符
    slide = Slide()
    slide.start_time = 4000.0
    slide.lane = 7
    slide.duration = 1500.0
    beatmap.add_hit_object(slide)
    slide.start_time = 4000.0
    slide.lane = 7
    slide.duration = 1500.0
    beatmap.add_hit_object(slide)

    # 2. 难度计算
    difficulty_calc = SentakkiDifficultyCalculator(beatmap)
    difficulty_attributes = difficulty_calc.calculate()
    
    # 3. PP计算
    performance_calc = SentakkiPerformanceCalculator()
    # 创建分数信息字典
    score_info = {
        'accuracy': 95.0,  # 准确率
        'count_miss': 0,   # Miss数
        'max_combo': len(beatmap.hit_objects),  # 最大连击数
        'score': 950000    # 分数
    }
    
    result = performance_calc.calculate(score_info, difficulty_attributes)
    
    # 4. 输出结果
    print("\nSentakki模式谱面信息:")
    print(f"谱面物件数: {len(beatmap.hit_objects)}")
    
    print("\n谱面组成:")
    print(f"Tap数量: 2")
    print(f"Hold数量: 1")
    print(f"Touch数量: 1")
    print(f"Slide数量: 1")
    
    print("\n难度属性:")
    print(f"星级: {difficulty_attributes.star_rating:.2f}")
    
    print("\nPP计算结果:")
    print(f"总PP: {result.get('total', 0):.2f}")
    print(f"分数: {score_info['score']}")
    print(f"准确率: {score_info['accuracy']}%")

if __name__ == "__main__":
    main()