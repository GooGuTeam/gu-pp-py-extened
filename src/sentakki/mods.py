"""Sentakki 模式 Mods 定义 (基于 sentakki C# 规则集中的可用 mods 分类)

当前仅用于难度/PP计算：
- 只实现会影响速度/节奏的时间类 Mods: HalfTime / Daycore / DoubleTime / Nightcore
- 以及难度类: HardRock
其它（Hidden/Autoplay 等）暂不对计算有直接影响，占位保留以便未来扩展。

注意：原 C# 项目还没有真正的难度与性能算法，这里尽量保持最小可行接口，后续如果官方实现更新，可再同步。
"""
from enum import IntFlag

class SentakkiMods(IntFlag):
    NOMOD = 0
    HALF_TIME = 1 << 0
    DAYCORE = 1 << 1  # 与 HT 等价，只做别名占位
    DOUBLE_TIME = 1 << 2
    NIGHTCORE = 1 << 3  # 与 DT 等价，只做别名占位
    HARD_ROCK = 1 << 4
    HIDDEN = 1 << 5
    AUTOPLAY = 1 << 6
    NOTOUCH = 1 << 7
    CLASSIC = 1 << 8
    MIRROR = 1 << 9
    DIFFICULTY_ADJUST = 1 << 10
    EXPERIMENTAL = 1 << 11
    CHALLENGE = 1 << 12
    ACCURACY_CHALLENGE = 1 << 13
    PERFECT = 1 << 14
    SUDDEN_DEATH = 1 << 15
    BARREL_ROLL = 1 << 16
    SYNESTHESIA = 1 << 17
    MUTED = 1 << 18
    WIND_UP = 1 << 19
    WIND_DOWN = 1 << 20
    TOUCH_DEVICE = 1 << 21

    @property
    def clock_rate(self) -> float:
        rate = 1.0
        if self & (SentakkiMods.DOUBLE_TIME | SentakkiMods.NIGHTCORE):
            rate *= 1.5
        if self & (SentakkiMods.HALF_TIME | SentakkiMods.DAYCORE):
            rate *= 0.75
        return rate

    def apply_ar(self, ar: float) -> float:
        # 目前没有官方公式，这里保持与 Tau 类似的处理方式示例，可后续修正
        if self & SentakkiMods.HARD_ROCK:
            ar = min(10, ar * 1.4)
        if self & (SentakkiMods.HALF_TIME | SentakkiMods.DAYCORE):
            ar = max(0, ar * 0.75)
        if self & (SentakkiMods.DOUBLE_TIME | SentakkiMods.NIGHTCORE):
            ar = min(10, ar * 1.5)
        return ar

