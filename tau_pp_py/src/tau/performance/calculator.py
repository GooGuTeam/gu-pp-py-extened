"""
Performance calculator for tau mode.
"""

from typing import Optional
from ...model.beatmap import Beatmap
from ..difficulty.calculator import DifficultyAttributes, TauDifficultyCalculator


class PerformanceAttributes:
    """
    Stores the performance attributes of a score.
    """
    def __init__(self):
        self.pp: float = 0.0
        self.aim_pp: float = 0.0
        self.speed_pp: float = 0.0
        self.accuracy_pp: float = 0.0
        self.flashlight_pp: float = 0.0
        self.effective_miss_count: float = 0.0


class TauPerformanceCalculator:
    """
    Calculates the performance points (pp) of a score on a tau beatmap.
    """
    def __init__(self, difficulty: DifficultyAttributes, beatmap: Optional[Beatmap] = None):
        self.difficulty = difficulty
        self.beatmap = beatmap
        self.score = 0
        self.accuracy = 1.0
        self.max_combo = 0
        self.misses = 0
        self.mods = []

    def calculate(self) -> PerformanceAttributes:
        """
        Calculate the performance points of the score.
        """
        attributes = PerformanceAttributes()
        
        # Calculate total pp
        attributes.pp = self.calculate_total_pp()
        
        # Calculate specific skill pp
        attributes.aim_pp = self.calculate_aim_pp()
        attributes.speed_pp = self.calculate_speed_pp()
        attributes.accuracy_pp = self.calculate_accuracy_pp()
        
        # Calculate effective miss count
        attributes.effective_miss_count = self.calculate_effective_miss_count()
        
        return attributes

    def calculate_total_pp(self) -> float:
        """
        Calculate the total performance points.
        """
        aim_pp = self.calculate_aim_pp()
        speed_pp = self.calculate_speed_pp()
        accuracy_pp = self.calculate_accuracy_pp()
        
        # Combine different skills with balance factors
        total = pow(
            pow(aim_pp, 1.1) +
            pow(speed_pp, 1.1) +
            pow(accuracy_pp, 1.1),
            1.0 / 1.1
        )
        
        # Penalty for misses
        if self.misses > 0 and self.beatmap:
            total *= 0.95 ** self.misses
            
        return total

    def calculate_aim_pp(self) -> float:
        """
        Calculate the aim performance points.
        """
        aim_value = pow(5.0 * max(1.0, self.difficulty.aim_difficulty / 0.0675) - 4.0, 3.0) / 100000.0
        
        # Length bonus
        if self.beatmap:
            length_bonus = 0.95 + 0.4 * min(1.0, len(self.beatmap.hit_objects) / 2000.0)
            if len(self.beatmap.hit_objects) > 2000:
                length_bonus += 0.3 * min(1.0, (len(self.beatmap.hit_objects) - 2000) / 2000.0)
            aim_value *= length_bonus
        
        # Miss penalty
        aim_value *= 0.97 ** self.misses
        
        # Combo penalty
        if self.difficulty.max_combo > 0:
            aim_value *= min(pow(self.max_combo, 0.8) / pow(self.difficulty.max_combo, 0.8), 1.0)
            
        # AR bonus
        if self.difficulty.approach_rate > 9.0:
            aim_value *= 1.0 + 0.1 * (self.difficulty.approach_rate - 9.0)  # 10% bonus for AR10+
        elif self.difficulty.approach_rate < 8.0:
            aim_value *= 1.0 + 0.01 * (8.0 - self.difficulty.approach_rate)  # Small bonus for AR<8
            
        return aim_value

    def calculate_speed_pp(self) -> float:
        """
        Calculate the speed performance points.
        """
        speed_value = pow(5.0 * max(1.0, self.difficulty.speed_difficulty / 0.0675) - 4.0, 3.0) / 100000.0
        
        # Length bonus
        if self.beatmap:
            length_bonus = 0.95 + 0.4 * min(1.0, len(self.beatmap.hit_objects) / 2000.0)
            if len(self.beatmap.hit_objects) > 2000:
                length_bonus += 0.3 * min(1.0, (len(self.beatmap.hit_objects) - 2000) / 2000.0)
            speed_value *= length_bonus
        
        # Miss penalty
        speed_value *= 0.97 ** self.misses
        
        # Combo penalty
        if self.difficulty.max_combo > 0:
            speed_value *= min(pow(self.max_combo, 0.8) / pow(self.difficulty.max_combo, 0.8), 1.0)
            
        # AR bonus
        if self.difficulty.approach_rate > 9.0:
            speed_value *= 1.0 + 0.1 * (self.difficulty.approach_rate - 9.0)  # 10% bonus for AR10+
        elif self.difficulty.approach_rate < 8.0:
            speed_value *= 1.0 + 0.01 * (8.0 - self.difficulty.approach_rate)  # Small bonus for AR<8
            
        return speed_value

    def calculate_accuracy_pp(self) -> float:
        """
        Calculate the accuracy performance points.
        """
        # OD bonus for accuracy
        od_bonus = 0.0
        if self.difficulty.overall_difficulty > 8.0:
            od_bonus = 0.05 * (self.difficulty.overall_difficulty - 8.0)
        elif self.difficulty.overall_difficulty < 5.0:
            od_bonus = 0.01 * (5.0 - self.difficulty.overall_difficulty)
            
        accuracy_value = pow(1.52163, self.difficulty.overall_difficulty) * pow(self.accuracy, 24.0) * 2.83
        
        # Bonus for high accuracy
        accuracy_value *= 1.0 + od_bonus
        
        # Length bonus
        if self.beatmap:
            accuracy_value *= min(1.15, pow(len(self.beatmap.hit_objects) / 1000.0, 0.3))
            
        # Miss penalty
        accuracy_value *= 0.96 ** self.misses
        
        return accuracy_value

    def calculate_effective_miss_count(self) -> float:
        """
        Calculate the effective miss count.
        """
        # In a more complex implementation, this would consider slider breaks and other factors
        return float(self.misses)