"""
Tau应变技能基类
"""

import math
from abc import ABC, abstractmethod
from typing import List
from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject
from ...mods import TauMods


class TauStrainSkill(ABC):
    """Tau应变技能基类"""
    
    def __init__(self, mods: TauMods):
        """
        初始化应变技能
        
        Args:
            mods: 应用的mods
        """
        self.mods = mods
        self.skill_multiplier = 1.0
        self.strain_decay_base = 0.0
        
        # 存储应变值历史
        self.current_strain = 0.0
        self.current_section_peak = 0.0
        self.strain_peaks = []
        # track last section index so we can detect section changes reliably
        self._last_section_index = -1
        
    def process(self, hit_object: TauDifficultyHitObject):
        """
        处理击打物件
        
        Args:
            hit_object: 难度击打物件
        """
        if hit_object.index == 0:
            self.current_section_peak = 0.0
            self.strain_peaks.clear()
            
        self.current_strain *= self._strain_decay(hit_object.delta_time)
        self.current_strain += self.strain_value_of(hit_object) * self.skill_multiplier
        
        self.current_section_peak = max(self.current_strain, self.current_section_peak)
        
        # 检查是否是新的段落
        next_time = hit_object.start_time + hit_object.delta_time
        if self._is_new_section(next_time):
            self._save_current_peak()
            self._start_new_section_from(next_time)
    
    def _strain_decay(self, time: float) -> float:
        """
        计算应变衰减
        
        Args:
            time: 时间间隔(ms)
            
        Returns:
            float: 衰减因子
        """
        return math.pow(self.strain_decay_base, time / 1000) if self.strain_decay_base > 0 else 0
    
    def _is_new_section(self, time: float) -> bool:
        """
        检查是否是新的段落
        
        Args:
            time: 时间
            
        Returns:
            bool: 是否是新的段落
        """
        # 默认每10秒为一个段落
        section_index = int(time / 10000)
        if section_index != self._last_section_index:
            self._last_section_index = section_index
            return True
        return False
    
    def _save_current_peak(self):
        """保存当前段落峰值"""
        self.strain_peaks.append(self.current_section_peak)
    
    def _start_new_section_from(self, time: float):
        """
        从指定时间开始新段落
        
        Args:
            time: 时间
        """
        # 保存当前峰值并开始新段落
        self.current_section_peak = 0.0
    
    @abstractmethod
    def strain_value_of(self, current: TauDifficultyHitObject) -> float:
        """
        计算当前物件的应变值
        
        Args:
            current: 当前难度击打物件
            
        Returns:
            float: 应变值
        """
        pass
    
    def difficulty_value(self) -> float:
        """
        计算技能难度值
        
        Returns:
            float: 难度值
        """
        self.strain_peaks.sort(reverse=True)
        
        if not self.strain_peaks:
            return 0.0
            
        difficulty = 0.0
        weight = 1.0
        
        for strain in self.strain_peaks:
            difficulty += strain * weight
            weight *= 0.9
            
        return difficulty