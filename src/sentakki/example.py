"""
Sentakki难度计算示例
"""

from .tap import Tap
from .hold import Hold
from .touch import Touch
from .slide import Slide
from .beatmap import SentakkiBeatmap
from .difficulty.difficultyCalculator import SentakkiDifficultyCalculator


def create_example_beatmap() -> SentakkiBeatmap:
    """创建示例谱面"""
    beatmap = SentakkiBeatmap()
    
    # 设置难度属性
    beatmap.set_difficulty_attribute('approach_rate', 9.5)
    beatmap.set_difficulty_attribute('overall_difficulty', 8.5)
    beatmap.set_difficulty_attribute('drain_rate', 7.0)
    
    # 设置元数据
    beatmap.set_metadata('title', 'Example Song')
    beatmap.set_metadata('artist', 'Example Artist')
    beatmap.set_metadata('version', 'Expert')
    
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
    
    return beatmap


def main():
    """主函数"""
    # 创建示例谱面
    beatmap = create_example_beatmap()
    
    # 创建难度计算器
    calculator = SentakkiDifficultyCalculator(beatmap)
    
    # 计算难度
    difficulty = calculator.calculate()
    
    # 输出结果
    print("=== Sentakki难度计算结果 ===")
    print(f"歌曲标题: {beatmap.metadata.get('title', 'Unknown')}")
    print(f"难度等级: {beatmap.metadata.get('version', 'Unknown')}")
    print(f"星级评分: {difficulty['star_rating']:.2f}★")
    print(f"Aim难度: {difficulty['aim_difficulty']:.2f}")
    print(f"速度难度: {difficulty['speed_difficulty']:.2f}")
    print(f"复杂度: {difficulty['complexity_difficulty']:.2f}")
    print(f"AR: {difficulty['approach_rate']:.1f}")
    print(f"OD: {difficulty['overall_difficulty']:.1f}")
    print(f"HP: {difficulty['drain_rate']:.1f}")
    print(f"最大连击: {difficulty['max_combo']}")
    print("\n物件统计:")
    print(f"  Tap: {difficulty['tap_count']} 个")
    print(f"  Hold: {difficulty['hold_count']} 个")
    print(f"  Touch: {difficulty['touch_count']} 个")
    print(f"  Slide: {difficulty['slide_count']} 个")


if __name__ == "__main__":
    main()