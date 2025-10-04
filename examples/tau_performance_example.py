"""Tau 模式综合示例 (使用 Difficulty V2 + PerformanceCalculator)

演示步骤:
 1. 构建一个简单谱面 (Beat/HardBeat/StrictHardBeat)
 2. 计算难度 (TauDifficultyCalculator)
 3. 构造一个成绩字典并计算 PP

所需字段 (score):
  accuracy: 0~1 浮点
  max_combo: 实际玩家连击
  statistics: { great, ok, miss }

运行: python -m examples.tau_performance_example
"""
from tau.difficulty import TauDifficultyCalculator
from tau.performance.tauPerformanceCalculator import TauPerformanceCalculator
from tau.beatmap import TauBeatmap
from tau.objects import Beat, HardBeat, StrictHardBeat


def build_map() -> TauBeatmap:
    bm = TauBeatmap()
    t = 0
    # 简单 3 连 + HardBeat + StrictHardBeat
    for ang in (30, 75, 140):
        b = Beat(); b.start_time = t; b.angle = ang; bm.add_hit_object(b); t += 450
    hb = HardBeat(); hb.start_time = t; hb.angle = 210; bm.add_hit_object(hb); t += 500
    shb = StrictHardBeat(); shb.start_time = t; shb.angle = 320; bm.add_hit_object(shb)
    return bm


def main():
    beatmap = build_map()
    calc = TauDifficultyCalculator(beatmap, mods=0)
    diff = calc.calculate()

    score = {
        'accuracy': 0.985,
        'max_combo': diff.max_combo,  # 假设全连
        'statistics': {
            'great': diff.notes_count,  # 简化：全部 Great
            'ok': 0,
            'miss': 0,
        },
        'mods': 0,
    }
    perf_calc = TauPerformanceCalculator()
    perf = perf_calc.calculate(score, diff)

    print("=== Tau 示例 (V2) ===")
    print(f"对象数: {len(beatmap.hit_objects)}  MaxCombo={diff.max_combo}")
    print(f"Star: {diff.star_rating:.3f}")
    print(f"Aim: {diff.aim_difficulty:.3f}  Speed: {diff.speed_difficulty:.3f}  Complexity: {diff.complexity_difficulty:.3f}")
    print(f"AR: {diff.approach_rate:.2f}  OD: {diff.overall_difficulty:.2f}")
    print("-- Performance --")
    print(f"Total PP: {perf.total:.3f}")
    print(f"(Aim={perf.aim:.3f}, Speed={perf.speed:.3f}, Acc={perf.accuracy:.3f}, Complex={perf.complexity:.3f})")


if __name__ == '__main__':  # pragma: no cover
    main()