# gu-pp-py-extened

PP and star calculation for the more osu! gamemode, organized in the style of [rosu-pp](https://github.com/MaxOhn/rosu-pp).

This library provides Python implementations for calculating difficulty and performance attributes for more rulesets of osu!, similar to how rosu-pp works for other osu! gamemodes.

## Tau 游戏模式实现

本项目实现了osu!的Tau游戏模式（taulazer/tau）的难度和PP计算系统，接口风格模仿rosu-pp。

### 主要组件

1. **objects.py** - Tau游戏物件定义
   - TauHitObject 及其子类（Beat, HardBeat, Slider等）
   - 滑条路径系统（PolarSliderPath）
   - 角度和坐标计算工具

2. **beatmap.py** - 谱面数据结构
   - TauBeatmap 类
   - 谱面统计信息

3. **attributes.py** - 谱面和难度属性
   - BeatmapAttributes: 谱面属性（AR, OD, CS, HP）
   - HitWindows: 击打时间窗口
   - TauDifficultyAttributes: Tau模式难度属性
   - BeatmapAttributesBuilder: 属性构建器

### 使用示例

```python
from src.tau.attributes import BeatmapAttributesBuilder

# 创建属性构建器
builder = BeatmapAttributesBuilder()

# 设置基础属性
builder.ar_value(9.0) \
       .od_value(8.0) \
       .cs_value(4.0) \
       .hp_value(7.0) \
       .with_mods(16)  # HR mod

# 构建属性
attributes = builder.build()

print(f"AR: {attributes.approach_rate}")
print(f"OD: {attributes.overall_difficulty}")
print(f"Great判定窗口: {attributes.hit_windows.great}ms")
```

### 支持的Mods

使用TauMods枚举来表示mods:

- EZ (1 << 1)
- HR (1 << 4)
- HT (1 << 8)
- DT (1 << 6)
- NC (1 << 9)
- DC (1 << 11)
- FL (1 << 10)

### Mod使用示例

```python
from src.tau.mods import TauMods, apply_mods_to_attributes, get_mod_score_multiplier

# 应用mods到属性
base_attributes = BeatmapAttributes(approach_rate=9.0, overall_difficulty=8.0)
modified_attributes = apply_mods_to_attributes(base_attributes, TauMods.HARD_ROCK)

# 获取mod的分数倍数
multiplier = get_mod_score_multiplier(TauMods.HARD_ROCK | TauMods.DOUBLE_TIME)
```

更多mod支持可以按需添加。
