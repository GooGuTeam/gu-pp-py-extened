# gu-pp-py-extened

PP and star calculation for the more osu! gamemode, organized in the style of [rosu-pp](https://github.com/MaxOhn/rosu-pp).

This library provides Python implementations for calculating difficulty and performance attributes for more rulesets of osu!, similar to how rosu-pp works for other osu! gamemodes.

## 安装 (Installation)

PyPI (计划发布)：

```bash
pip install gu-pp-py-extended
```

当前仓库本地使用（源码）：

```bash
git clone <this-repo-url>
cd gu-pp-py-extened
pip install -e .[dev]
```

uv 用户：

```bash
uv sync --all-extras
```

## 快速开始 (Quick Start)

计算 Tau 难度与 PP：

```python
from tau.beatmap import TauBeatmap
from tau.objects import Beat
from tau.difficulty import TauDifficultyCalculator
from tau.performance.tauPerformanceCalculator import TauPerformanceCalculator

# 构造一个极简谱面
beatmap = TauBeatmap(
   hit_objects=[
      Beat(time=0, angle=0.0),
      Beat(time=500, angle=1.2),
      Beat(time=900, angle=2.4),
   ],
   difficulty_attributes={
      'approach_rate': 9.0,
      'overall_difficulty': 8.0,
      'circle_size': 4.0,
      'hp_drain_rate': 6.0,
   }
)

diff_attrs = TauDifficultyCalculator(beatmap).calculate()
pp = TauPerformanceCalculator(beatmap, diff_attrs, mods=0, combo=len(beatmap.hit_objects), misses=0, accuracy=98.5).calculate()

print(diff_attrs.star_rating, pp)
```

## 作为库使用的模块结构

核心入口：

- `tau.difficulty.TauDifficultyCalculator` 计算并返回 `TauDifficultyAttributes`
- `tau.performance.tauPerformanceCalculator.TauPerformanceCalculator` 计算 PP
- `tau.mods.TauMods` 位标志枚举 / 整数组合
- `tau.attributes` 构建与修正 AR/OD/CS/HP 与命中窗口

可选：

- `sentakki.*` 另一个模式的简单难度/PP 逻辑

目录布局遵循 `src/` 包结构，可通过 `from tau ...` 直接导入（安装后）。

## 发布 (Build & Publish)

构建：

```bash
python -m build
```

校验分发包：

```bash
twine check dist/*
```

上传 PyPI：

```bash
twine upload dist/*
```

（需要先在 PyPI 创建账户并配置 API token 到 `~/.pypirc` 或环境变量。）

## 版本策略

当前为 `0.x` 迭代，API 可能发生不兼容修改。移除 legacy tau 难度已在 0.1.0 后续准备中；建议在升级日志中注明 BREAKING CHANGES。

---


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
