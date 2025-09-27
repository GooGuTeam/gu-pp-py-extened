"""
Difficulty calculator for tau mode.
"""

from typing import List
from ...model.beatmap import Beatmap
from ...model.hit_object import HitObject


class DifficultyAttributes:
    """
    Stores the difficulty attributes of a beatmap.
    """
    def __init__(self):
        self.star_rating: float = 0.0
        self.max_combo: int = 0
        self.aim_difficulty: float = 0.0
        self.speed_difficulty: float = 0.0
        self.flashlight_rating: float = 0.0
        self.slider_factor: float = 0.0
        self.approach_rate: float = 0.0
        self.overall_difficulty: float = 0.0


class TauDifficultyCalculator:
    """
    Calculates the difficulty of a tau beatmap.
    """
    def __init__(self, beatmap: Beatmap):
        self.beatmap = beatmap
        self.mods = []
        self.section_length = 1000.0

    def calculate(self) -> DifficultyAttributes:
        """
        Calculate the difficulty of the beatmap.
        """
        attributes = DifficultyAttributes()
        
        # Calculate main difficulty attributes
        attributes.star_rating = self.calculate_star_rating()
        attributes.max_combo = self.beatmap.max_combo()
        attributes.approach_rate = self.beatmap.approach_rate
        attributes.overall_difficulty = self.beatmap.overall_difficulty
        
        # Calculate specific difficulty skills
        attributes.aim_difficulty = self.calculate_aim_difficulty()
        attributes.speed_difficulty = self.calculate_speed_difficulty()
        
        return attributes

    def calculate_star_rating(self) -> float:
        """
        Calculate the star rating of the beatmap.
        """
        # Simplified star rating calculation
        # In a real implementation, this would be much more complex
        object_count = len(self.beatmap.hit_objects)
        if object_count == 0:
            return 0.0
            
        # Base rating based on object count and timing
        base_rating = object_count / 100.0
        
        # Adjust based on overall difficulty
        od_factor = self.beatmap.overall_difficulty / 10.0
        
        # Adjust based on approach rate
        ar_factor = self.beatmap.approach_rate / 10.0
        
        return (base_rating * 1.5 + od_factor + ar_factor) / 3.0

    def calculate_aim_difficulty(self) -> float:
        """
        Calculate the aim difficulty of the beatmap.
        """
        # Simplified aim difficulty calculation
        angle_changes = self.calculate_angle_changes()
        if not angle_changes:
            return 0.0
            
        # Average angle change contributes to aim difficulty
        avg_change = sum(angle_changes) / len(angle_changes)
        return avg_change / 10.0

    def calculate_speed_difficulty(self) -> float:
        """
        Calculate the speed difficulty of the beatmap.
        """
        # Simplified speed difficulty calculation
        intervals = self.calculate_intervals()
        if not intervals:
            return 0.0
            
        # Average interval contributes to speed difficulty
        avg_interval = sum(intervals) / len(intervals) if intervals else 1000.0
        # Shorter intervals mean higher speed difficulty
        return max(0.0, (1000.0 - avg_interval) / 100.0)

    def calculate_angle_changes(self) -> List[float]:
        """
        Calculate the angle changes between consecutive objects.
        """
        angles = []
        for i in range(1, len(self.beatmap.hit_objects)):
            prev_obj = self.beatmap.hit_objects[i-1]
            curr_obj = self.beatmap.hit_objects[i]
            angle_change = abs(curr_obj.angle - prev_obj.angle)
            # Normalize angle change to 0-180
            if angle_change > 180:
                angle_change = 360 - angle_change
            angles.append(angle_change)
        return angles

    def calculate_intervals(self) -> List[float]:
        """
        Calculate the time intervals between consecutive objects.
        """
        intervals = []
        for i in range(1, len(self.beatmap.hit_objects)):
            prev_obj = self.beatmap.hit_objects[i-1]
            curr_obj = self.beatmap.hit_objects[i]
            interval = curr_obj.start_time - prev_obj.start_time
            intervals.append(interval)
        return intervals