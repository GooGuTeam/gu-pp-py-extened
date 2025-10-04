"""
Tau难度计算器，模仿rosu-pp的接口风格
"""

import math
from typing import List, Type, Any
from ..objects import TauHitObject, AngledTauHitObject, Beat, StrictHardBeat, Slider, SliderRepeat, HardBeat
from ..attributes import TauDifficultyAttributes
from ..mods import TauMods
from ..beatmap import TauBeatmap
from .skills.aim import Aim
from .skills.speed import Speed
from .skills.complexity import Complexity
from .preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from .preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject


class TauDifficultyCalculator:
    """Tau难度计算器"""
    
    def __init__(self, beatmap: TauBeatmap, mods: int = 0):
        """
        初始化难度计算器
        
        Args:
            beatmap: Tau谱面对象
            mods: 应用的mods
        """
        import warnings
        warnings.warn(
            'TauDifficultyCalculator (legacy) 将被弃用，请迁移到 TauDifficultyCalculatorV2',
            DeprecationWarning,
            stacklevel=2
        )
        self.beatmap = beatmap
        self.mods = TauMods(mods)
        self.difficulty_multiplier = 0.0820
    
    def calculate(self) -> TauDifficultyAttributes:
        """
        计算谱面难度
        
        Returns:
            TauDifficultyAttributes: 难度属性
        """
        if len(self.beatmap.hit_objects) == 0:
            return TauDifficultyAttributes()
        # 应用难度类 mods 对基础属性 (AR / OD / CS / HP) 的影响（与上游：EZ 半，HR 放大并上限 10）
        base_ar = self.beatmap.difficulty_attributes.get('approach_rate', 5.0)
        base_od = self.beatmap.difficulty_attributes.get('overall_difficulty', 5.0)
        base_cs = self.beatmap.difficulty_attributes.get('circle_size', 5.0)
        base_hp = self.beatmap.difficulty_attributes.get('drain_rate', 5.0)

        ar, od, cs, hp = self._apply_attribute_mods(base_ar, base_od, base_cs, base_hp)

        # 保存供后续窗口与 preempt 计算
        self._modded_ar = ar
        self._modded_od = od

        # 创建难度击打物件（时间相关计算依赖 clock_rate，因此先确保 clock_rate mod 已应用）
        difficulty_hit_objects = self._create_difficulty_hit_objects()

        # 创建技能（需要使用被 mods 影响后的 OD 计算 great 窗口）
        skills = self._create_skills(difficulty_hit_objects, self._modded_od)

        # 计算技能难度值
        for skill in skills:
            for hit_object in difficulty_hit_objects:
                skill.process(hit_object)

        # 计算各项难度值
        aim = math.sqrt(skills[0].difficulty_value()) * self.difficulty_multiplier
        aim_no_sliders = math.sqrt(skills[1].difficulty_value()) * self.difficulty_multiplier
        speed = math.sqrt(skills[2].difficulty_value()) * self.difficulty_multiplier
        complexity = math.sqrt(skills[3].difficulty_value()) * self.difficulty_multiplier

        # Relax mod影响
        if self.mods & TauMods.RELAX:
            speed = 0.0
            complexity = 0.0

        # Autopilot mod影响
        if self.mods & TauMods.AUTOPILOT:
            aim = 0.0
            aim_no_sliders = 0.0

        # 计算 AR：使用被 mods 影响后的 AR 数值与速率修正
        preempt = self._calculate_preempt(self._modded_ar)
        approach_rate = self._calculate_approach_rate(preempt)

        # 计算基础难度值
        base_aim = math.pow(5 * max(1, aim / 0.0675) - 4, 3) / 100000
        base_speed = math.pow(5 * max(1, speed / 0.0675) - 4, 3) / 100000
        base_complexity = math.pow(5 * max(1, complexity / 0.0675) - 4, 3) / 100000

        base_performance = math.pow(
            math.pow(base_aim, 1.1) + math.pow(base_speed, 1.1) + math.pow(base_complexity, 1.1),
            1.0 / 1.1
        )

        star_rating = 0
        if base_performance > 0.00001:
            star_rating = math.pow(1.12, 1/3) * 0.027 * (math.pow(100000 / math.pow(2, 1 / 1.1) * base_performance, 1/3) + 4)

        # 统计物件数量
        notes_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Beat))
        slider_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, Slider))
        hard_beat_count = sum(1 for obj in self.beatmap.hit_objects if isinstance(obj, HardBeat))

        slider_factor = aim_no_sliders / aim if aim > 0 else 1.0

        return TauDifficultyAttributes(
            star_rating=star_rating,
            aim_difficulty=aim,
            speed_difficulty=speed,
            complexity_difficulty=complexity,
            approach_rate=approach_rate,
            overall_difficulty=self._modded_od,
            drain_rate=hp,
            slider_factor=slider_factor,
            notes_count=notes_count,
            slider_count=slider_count,
            hard_beat_count=hard_beat_count,
            max_combo=self._get_max_combo()
        )
    
    def _create_difficulty_hit_objects(self) -> List[TauDifficultyHitObject]:
        """
        创建难度击打物件
        
        Returns:
            List[TauDifficultyHitObject]: 难度击打物件列表
        """
        difficulty_objects = []
        last_object = None
        last_angled = None
        
        clock_rate = self._get_clock_rate()
        
        for i, hit_object in enumerate(self.beatmap.hit_objects):
            if last_object is not None:
                if isinstance(hit_object, AngledTauHitObject):
                    obj = TauAngledDifficultyHitObject(
                        hit_object, 
                        last_object, 
                        clock_rate,
                        difficulty_objects,
                        i,
                        last_angled
                    )
                    difficulty_objects.append(obj)
                    last_angled = obj
                else:
                    obj = TauDifficultyHitObject(
                        hit_object,
                        last_object,
                        clock_rate,
                        difficulty_objects,
                        i
                    )
                    difficulty_objects.append(obj)
            
            last_object = hit_object
        
        return difficulty_objects
    
    def _create_skills(self, difficulty_hit_objects: List[TauDifficultyHitObject], od_value: float) -> List[Any]:
        """
        创建技能对象
        
        Args:
            difficulty_hit_objects: 难度击打物件列表
            
        Returns:
            List[Any]: 技能对象列表
        """
        # 计算Great窗口大小
        great_window = self._calculate_great_window(od_value) / self._get_clock_rate()

        return [
            Aim(self.mods, [Beat, StrictHardBeat, SliderRepeat, Slider]),
            Aim(self.mods, [Beat, StrictHardBeat]),
            Speed(self.mods, great_window),
            Complexity(self.mods)
        ]
    
    def _calculate_great_window(self, od: float) -> float:
        """
        计算Great判定窗口
        
        Args:
            od: Overall Difficulty
            
        Returns:
            float: Great判定窗口大小(ms)
        """
        if od <= 5:
            return 127 - (od * 3)  # 从127ms到112ms
        else:
            return 112 - ((od - 5) * 3)  # 从112ms到97ms
    
    def _get_clock_rate(self) -> float:
        """
        获取时钟速率
        
        Returns:
            float: 时钟速率
        """
        clock_rate = 1.0
        
        # Nightcore 等价于 DoubleTime；Daycore 等价于 HalfTime
        if self.mods & (TauMods.DOUBLE_TIME | TauMods.NIGHTCORE):
            clock_rate *= 1.5
        elif self.mods & (TauMods.HALF_TIME | TauMods.DAYCORE):
            clock_rate *= 0.75
            
        return clock_rate
    
    def _calculate_preempt(self, ar: float) -> float:
        """
        计算预判时间
        
        Returns:
            float: 预判时间(ms)
        """
        clock_rate = self._get_clock_rate()
        
        if ar <= 5:
            return (1800 - (ar * 120)) / clock_rate
        else:
            return (1200 - ((ar - 5) * 150)) / clock_rate
    
    def _calculate_approach_rate(self, preempt: float) -> float:
        """
        根据预判时间计算AR
        
        Args:
            preempt: 预判时间
            
        Returns:
            float: Approach Rate
        """
        if preempt > 1200:
            return (1800 - preempt) / 120
        else:
            return (1200 - preempt) / 150 + 5

    def _apply_attribute_mods(self, ar: float, od: float, cs: float, hp: float):
        """应用 EZ / HR 等非速率类 mods 对基础属性的变换，保持与上游接近。

        Easy: attribute * 0.5 (下限 0)
        HardRock: AR/OD *1.4 (上限10), CS *1.3 (上限10), HP *1.4 (上限10)
        速率类 (DT/NC/HT/DC) 不在此直接修改 AR/OD，而是通过 clock_rate 影响 preempt / hit window。
        """
        if self.mods & TauMods.EASY:
            ar = max(0.0, ar * 0.5)
            od = max(0.0, od * 0.5)
            cs = max(0.0, cs * 0.5)
            hp = max(0.0, hp * 0.5)

        if self.mods & TauMods.HARD_ROCK:
            ar = min(10.0, ar * 1.4)
            od = min(10.0, od * 1.4)
            cs = min(10.0, cs * 1.3)
            hp = min(10.0, hp * 1.4)

        return ar, od, cs, hp
    
    def _get_max_combo(self) -> int:
        """
        获取最大连击数
        
        Returns:
            int: 最大连击数
        """
        max_combo = 0
        for obj in self.beatmap.hit_objects:
            max_combo += 1
            # 如果是Slider，增加额外的连击点
            if isinstance(obj, Slider):
                # 简化处理，实际应该根据滑条的节点数计算
                max_combo += obj.repeat_count + 1
        
        return max_combo