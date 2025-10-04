"""Sentakki 模式完整示例（严格 PR#701 逻辑移植版）

当前上游 (sentakki PR #701) 难度逻辑极简：StarRating = Beatmap(StarRating * clockRate) * 1.25；
无真实技能拆分。因此本示例主要演示：
 1. 构建一个简单谱面
 2. 应用 Mods (可选) 计算难度
 3. 计算性能值

注意：示例中的对象类位于 sentakki.beatmaps.objects 中，而非根级 tap/hold 模块。
"""
from sentakki.difficulty.difficultyCalculator import SentakkiDifficultyCalculator
from sentakki.performance.performanceCalculator import SentakkiPerformanceCalculator
from sentakki.mods import SentakkiMods
from sentakki.beatmaps.objects import Tap, Hold, Slide, Touch
from sentakki.difficulty.beatmap_base import SentakkiBeatmap


def build_sample_beatmap() -> SentakkiBeatmap:
    objs = [
        Tap(time=0, lane=0),
        Tap(time=500, lane=3),
        Hold(time=1000, lane=2, duration=1200),
        Touch(time=1600, lane=4, x=100, y=120),
        Slide(time=2200, lane=6),
    ]
    star = 2.4
    max_combo = len(objs)  # 简化：一物件=一连击
    return SentakkiBeatmap(star_rating=star, max_combo=max_combo, approach_rate=5.0, objects=objs)


def main():
    beatmap = build_sample_beatmap()

    mods = SentakkiMods.DOUBLE_TIME | SentakkiMods.HARD_ROCK  # 演示可叠加（时钟+难度）
    calc = SentakkiDifficultyCalculator(beatmap, int(mods))
    diff = calc.calculate()

    # 构造成绩：accuracy 期望 0~1
    score = {
        'accuracy': 0.985,
        'max_combo': beatmap.max_combo,
        'statistics': {
            'miss': 0,
        }
    }
    perf_calc = SentakkiPerformanceCalculator()
    perf = perf_calc.calculate(score, diff)

    print("=== Sentakki 示例 ===")
    print(f"Mods: {mods}")
    print(f"对象数量: {len(beatmap.objects)}  (MaxCombo={beatmap.max_combo})")
    print(f"星级: {diff.star_rating:.3f}  (clock_rate={diff.clock_rate})")
    print(f"AR(带mods): {diff.approach_rate:.2f}")
    print("-- 性能 --")
    print(f"Base PP: {perf.base_pp:.4f}")
    print(f"Length Bonus: {perf.length_bonus:.4f}")
    print(f"Total PP: {perf.total:.4f}")


if __name__ == "__main__":  # pragma: no cover
    main()