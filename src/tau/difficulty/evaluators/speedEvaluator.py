"""
SpeedEvaluator类，用于评估速度难度
"""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..preprocessing.tauDifficultyHitObject import TauDifficultyHitObject

from ..preprocessing.tauAngledDifficultyHitObject import TauAngledDifficultyHitObject


class SpeedEvaluator:
    """速度评估器"""
    
    SINGLE_SPACING_THRESHOLD = 125
    MIN_SPEED_BONUS = 75  # ~200BPM
    SPEED_BALANCING_FACTOR = 40
    
    @staticmethod
    def evaluate_difficulty(current: 'TauDifficultyHitObject', great_window: float) -> float:
        """
        评估难度
        
        Args:
            current: 当前难度击打物件
            great_window: Great判定窗口大小
            
        Returns:
            float: 难度值
        """
        # 获取应变时间
        strain_time = current.strain_time
        great_window_full = great_window * 2
        speed_window_ratio = strain_time / great_window_full
        
        # 优化节奏模式（快速连续双击与大的时间间隔）
        if current.index > 0:
            prev_obj = current.previous(0)
            if prev_obj and strain_time < great_window_full and prev_obj.strain_time > strain_time:
                strain_time = prev_obj.strain_time + (strain_time - prev_obj.strain_time) * speed_window_ratio
        
        # 将时间间隔限制在OD 300判定窗口内
        # 0.93确保260bpm OD8的流不会被过度削弱，而0.92限制了上限的影响
        strain_time /= max((strain_time / great_window_full) / 0.93, 0.92, 1)
        
        # 计算速度奖励
        speed_bonus = 1.0
        if strain_time < SpeedEvaluator.MIN_SPEED_BONUS:
            speed_bonus = 1 + 0.75 * math.pow((SpeedEvaluator.MIN_SPEED_BONUS - strain_time) / SpeedEvaluator.SPEED_BALANCING_FACTOR, 2)
        
        distance = SpeedEvaluator.SINGLE_SPACING_THRESHOLD
        
        # 如果是角度物件且有前一个角度物件
        if isinstance(current, TauAngledDifficultyHitObject) and current.index > 0:
            prev_obj = current.previous(0)
            if isinstance(prev_obj, TauAngledDifficultyHitObject):
                travel_distance = abs(current.distance)
                distance = min(SpeedEvaluator.SINGLE_SPACING_THRESHOLD, 
                              travel_distance + abs(prev_obj.distance))
        
        return (speed_bonus + speed_bonus * math.pow(distance / SpeedEvaluator.SINGLE_SPACING_THRESHOLD, 3.5)) / strain_time
    
    @staticmethod
    def evaluate_rhythm_difficulty(current: 'TauDifficultyHitObject', great_window: float) -> float:
        """
        评估节奏难度
        
        Args:
            current: 当前难度击打物件
            great_window: Great判定窗口大小
            
        Returns:
            float: 节奏难度值
        """
        return SpeedEvaluator._evaluate_rhythm(current, great_window)
    
    @staticmethod
    def _evaluate_rhythm(current: 'TauDifficultyHitObject', great_window: float) -> float:
        """
        计算与历史数据相关的节奏乘数
        
        Args:
            current: 当前难度击打物件
            great_window: Great判定窗口大小
            
        Returns:
            float: 节奏乘数
        """
        HISTORY_TIME_MAX = 5000  # 5秒最大计算时间
        RHYTHM_MULTIPLIER = 0.75
        
        previous_island_size = 0
        rhythm_complexity_sum = 0
        island_size = 1
        start_ratio = 0  # 存储当前island开始的比率，用于加强更紧凑的节奏
        
        first_delta_switch = False
        rhythm_start = 0
        
        historical_note_count = min(current.index, 32)
        
        # 确定节奏计算的起始点
        while (rhythm_start < historical_note_count - 2):
            prev_obj = current.previous(rhythm_start)
            prev_start_time = prev_obj.start_time if prev_obj is not None else 0
            if current.start_time - prev_start_time < HISTORY_TIME_MAX:
                rhythm_start += 1
            else:
                break
        
        # 反向遍历历史物件计算节奏复杂度
        for i in range(rhythm_start, 0, -1):
            curr_obj = current.previous(i - 1)
            prev_obj = current.previous(i)
            last_obj = current.previous(i + 1)
            curr_start_time = curr_obj.start_time if curr_obj is not None else 0
            prev_start_time = prev_obj.start_time if prev_obj is not None else 0
            last_start_time = last_obj.start_time if last_obj is not None else 0
            curr_historical_decay = (HISTORY_TIME_MAX - (current.start_time - curr_start_time)) / HISTORY_TIME_MAX
            curr_historical_decay = min((historical_note_count - i) / historical_note_count, curr_historical_decay)
            curr_delta = curr_obj.strain_time if curr_obj is not None else 0
            prev_delta = prev_obj.strain_time if prev_obj is not None else 0
            last_delta = last_obj.strain_time if last_obj is not None else 0
            
            # 计算节奏比率
            curr_ratio = 1.0 + 6.0 * min(0.5, math.pow(
                math.sin(math.pi / (min(prev_delta, curr_delta) / max(prev_delta, curr_delta))), 2))
            
            # 窗口惩罚
            window_penalty = min(1, max(0, abs(prev_delta - curr_delta) - great_window * 0.6) / (great_window * 0.6))
            window_penalty = min(1, window_penalty)
            
            effective_ratio = window_penalty * curr_ratio
            
            if first_delta_switch:
                if not (prev_delta > 1.25 * curr_delta or prev_delta * 1.25 < curr_delta):
                    # island仍在继续，计数size
                    if island_size < 7:
                        island_size += 1
                else:
                    # 根据物件类型应用惩罚
                    if curr_obj is not None and hasattr(curr_obj, 'base_object') and hasattr(curr_obj.base_object, '__class__') and 'Slider' in curr_obj.base_object.__class__.__name__:
                        effective_ratio *= 0.125  # BPM变化到滑条，这是简单的acc窗口
                    
                    if prev_obj is not None and hasattr(prev_obj, 'base_object') and hasattr(prev_obj.base_object, '__class__') and 'Slider' in prev_obj.base_object.__class__.__name__:
                        effective_ratio *= 0.25  # BPM变化来自滑条，这通常比circle->circle简单
                    
                    if previous_island_size == island_size:
                        effective_ratio *= 0.25  # 重复的island size（例如：三连音->三连音）
                    
                    if previous_island_size % 2 == island_size % 2:
                        effective_ratio *= 0.50  # 重复的island极性（2->4, 3->5）
                    
                    if last_delta > prev_delta + 10 and prev_delta > curr_delta + 10:
                        effective_ratio *= 0.125  # 上一次增加发生在前一个note，1/1->1/2->1/4，不想加强这个
                    
                    rhythm_complexity_sum += (math.sqrt(effective_ratio * start_ratio) *
                                            curr_historical_decay *
                                            math.sqrt(4 + island_size) / 2 *
                                            math.sqrt(4 + previous_island_size) / 2)
                    
                    start_ratio = effective_ratio
                    previous_island_size = island_size
                    
                    # 如果我们在加速，保持计数；如果在减速，停止计数
                    if prev_delta * 1.25 < curr_delta:
                        first_delta_switch = False
                    
                    island_size = 1
            elif prev_delta > 1.25 * curr_delta:
                # 我们想要加速
                first_delta_switch = True
                start_ratio = effective_ratio
                island_size = 1
        
        # 产生可以应用于应变的乘数。范围[1, infinity)（实际上不是）
        return math.sqrt(4 + rhythm_complexity_sum * RHYTHM_MULTIPLIER) / 2