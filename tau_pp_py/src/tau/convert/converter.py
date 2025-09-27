"""
Beatmap converter for tau mode.
"""

import math
from typing import List
from ...model.beatmap import Beatmap
from ...model.hit_object import HitObject, Beat, HardBeat, Slider


class TauBeatmapConverter:
    """
    Converts standard beatmaps to tau mode beatmaps.
    """
    def __init__(self):
        self.base_scoring_distance = 100.0
        self.circle_size = 5.0  # Default circle size
        self.playfield_radius = 200.0

    def convert(self, original_beatmap: Beatmap) -> Beatmap:
        """
        Convert a standard beatmap to a tau beatmap.
        """
        tau_beatmap = Beatmap()
        
        # Copy basic properties
        tau_beatmap.circle_size = original_beatmap.circle_size
        tau_beatmap.hp_drain_rate = original_beatmap.hp_drain_rate
        tau_beatmap.overall_difficulty = original_beatmap.overall_difficulty
        tau_beatmap.approach_rate = original_beatmap.approach_rate
        tau_beatmap.slider_multiplier = original_beatmap.slider_multiplier
        tau_beatmap.slider_tick_rate = original_beatmap.slider_tick_rate
        tau_beatmap.stack_leniency = original_beatmap.stack_leniency
        tau_beatmap.version = original_beatmap.version
        
        # Convert hit objects
        tau_beatmap.hit_objects = self.convert_hit_objects(original_beatmap.hit_objects)
        
        # Copy control points
        tau_beatmap.control_points = original_beatmap.control_points
        
        return tau_beatmap

    def convert_hit_objects(self, original_objects: List[HitObject]) -> List[HitObject]:
        """
        Convert hit objects to tau mode.
        """
        tau_objects = []
        
        for i, obj in enumerate(original_objects):
            # Calculate angle based on object time and position in beatmap
            # This is a simplified approach - in reality, this would depend on the original position
            angle = self.calculate_angle(obj.start_time, i, len(original_objects))
            
            if isinstance(obj, Beat):
                tau_obj = Beat()
                tau_obj.start_time = obj.start_time
                tau_obj.angle = angle
                tau_obj.combo_index = obj.combo_index
                tau_obj.combo_color_index = obj.combo_color_index
                tau_obj.combo_increase = obj.combo_increase
                tau_objects.append(tau_obj)
                
            elif isinstance(obj, HardBeat):
                tau_obj = HardBeat()
                tau_obj.start_time = obj.start_time
                tau_obj.angle = angle
                tau_obj.combo_index = obj.combo_index
                tau_obj.combo_color_index = obj.combo_color_index
                tau_obj.combo_increase = obj.combo_increase
                tau_objects.append(tau_obj)
                
            elif isinstance(obj, Slider):
                tau_obj = Slider()
                tau_obj.start_time = obj.start_time
                tau_obj.angle = angle
                tau_obj.combo_index = obj.combo_index
                tau_obj.combo_color_index = obj.combo_color_index
                tau_obj.combo_increase = obj.combo_increase
                tau_obj.end_time = obj.end_time
                tau_obj.duration = obj.duration
                tau_obj.repeats = obj.repeats
                tau_obj.distance = obj.distance
                tau_obj.velocity = obj.velocity
                tau_obj.tick_distance = obj.tick_distance
                tau_objects.append(tau_obj)
                
            else:
                # Default to beat for unknown object types
                tau_obj = Beat()
                tau_obj.start_time = obj.start_time
                tau_obj.angle = angle
                tau_obj.combo_index = obj.combo_index
                tau_obj.combo_color_index = obj.combo_color_index
                tau_obj.combo_increase = obj.combo_increase
                tau_objects.append(tau_obj)
                
        return tau_objects

    def calculate_angle(self, time: float, index: int, total: int) -> float:
        """
        Calculate the angle for a hit object in tau mode.
        """
        # This is a simplified algorithm that distributes objects evenly in a circle
        # More complex implementations would consider the original position and other factors
        
        # Distribute objects evenly around the circle
        angle = (index / max(1, total)) * 360.0
        
        # Add some variation based on time to make it more interesting
        time_factor = (time / 1000.0) % 360  # Cycle every second
        angle = (angle + time_factor) % 360.0
        
        return angle

    def calculate_approach_rate(self, ar: float) -> float:
        """
        Calculate the approach rate in milliseconds.
        """
        if ar <= 5:
            return 1800 - ar * 120
        else:
            return 1200 - (ar - 5) * 150