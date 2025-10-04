from sentakki.pr701 import (
    SentakkiPR701DifficultyCalculator,
    SentakkiPR701PerformanceCalculator,
)
from dataclasses import dataclass

@dataclass
class SimpleBeatmap:
    star_rating: float
    max_combo: int

def test_pr701_strict_basic():
    bm = SimpleBeatmap(star_rating=3.2, max_combo=800)
    diff_calc = SentakkiPR701DifficultyCalculator(bm, mods=0)
    diff = diff_calc.calculate()
    assert abs(diff.star_rating - 3.2 * 1.25) < 1e-6, 'Star inflation mismatch'

    perf_calc = SentakkiPR701PerformanceCalculator()
    score = {
        'accuracy': 0.98,
        'max_combo': 780,
        'maximum_achievable_combo': 800,
        'statistics': {'miss': 2}
    }
    perf = perf_calc.calculate(score, diff)
    assert perf.total > 0, 'Performance total should be positive'

if __name__ == '__main__':
    test_pr701_strict_basic()
    print('PR701 strict test passed:',)