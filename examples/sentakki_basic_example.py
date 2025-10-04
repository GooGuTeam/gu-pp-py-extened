"""Sentakki 难度/PP 计算使用示例

当前实现基于 C# 项目现状：
- Star Rating = 输入 star_rating * 1.25
- PP 计算尚未实现，返回 0

后续官方若更新算法，可在本库扩展。
"""
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sentakki.difficulty.difficultyCalculator import SentakkiBeatmap, SentakkiDifficultyCalculator
from sentakki.performance.performanceCalculator import SentakkiPerformanceCalculator
from sentakki.mods import SentakkiMods

# 假设一个转换谱面的 star rating (来自 osu! 转换) = 3.2, 最大连击 500
beatmap = SentakkiBeatmap(star_rating=3.2, max_combo=500, approach_rate=7.5)
calc = SentakkiDifficultyCalculator(beatmap, mods=SentakkiMods.DOUBLE_TIME | SentakkiMods.HARD_ROCK)
diff = calc.calculate()
print("Sentakki Star Rating:", diff.star_rating)
print("Approach Rate (after mods):", diff.approach_rate)
print("Max Combo:", diff.max_combo)

# 伪造一个分数对象
score = {"accuracy": 0.98, "max_combo": 480, "mods": int(SentakkiMods.DOUBLE_TIME | SentakkiMods.HARD_ROCK)}
pp_calc = SentakkiPerformanceCalculator()
pp_attr = pp_calc.calculate(score, diff)
print("PP Total (placeholder):", pp_attr.total)
