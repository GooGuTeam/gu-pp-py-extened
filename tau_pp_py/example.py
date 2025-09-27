"""
Example usage of the tau-pp-py library.
"""

from src.model.beatmap import Beatmap
from src.model.hit_object import Beat, HardBeat
from src.main import calculate_difficulty, calculate_performance, convert_beatmap


def create_example_beatmap():
    """
    Create an example beatmap for testing.
    """
    beatmap = Beatmap()
    beatmap.circle_size = 5.0
    beatmap.hp_drain_rate = 7.0
    beatmap.overall_difficulty = 8.0
    beatmap.approach_rate = 9.0
    
    # Create some example hit objects
    for i in range(10):
        beat = Beat()
        beat.start_time = i * 1000  # 1 beat per second
        beat.angle = i * 36  # Distribute evenly around the circle
        beat.combo_index = i
        beat.combo_color_index = i % 4
        beatmap.hit_objects.append(beat)
    
    # Add some hard beats
    for i in range(2):
        hard_beat = HardBeat()
        hard_beat.start_time = i * 5000 + 2500  # Every 5 seconds, in the middle
        hard_beat.angle = i * 180
        hard_beat.combo_index = i + 10
        hard_beat.combo_color_index = 4
        beatmap.hit_objects.append(hard_beat)
    
    return beatmap


def main():
    """
    Main example function.
    """
    print("Creating example beatmap...")
    beatmap = create_example_beatmap()
    
    print(f"Created beatmap with {len(beatmap.hit_objects)} hit objects")
    
    print("Calculating difficulty...")
    difficulty = calculate_difficulty(beatmap)
    print(f"Star rating: {difficulty.star_rating:.2f}")
    print(f"Max combo: {difficulty.max_combo}")
    print(f"Aim difficulty: {difficulty.aim_difficulty:.2f}")
    print(f"Speed difficulty: {difficulty.speed_difficulty:.2f}")
    print(f"Approach rate: {difficulty.approach_rate:.2f}")
    print(f"Overall difficulty: {difficulty.overall_difficulty:.2f}")
    
    print("\nCalculating performance...")
    performance = calculate_performance(difficulty, beatmap)
    print(f"Performance points: {performance.pp:.2f}")
    print(f"Aim PP: {performance.aim_pp:.2f}")
    print(f"Speed PP: {performance.speed_pp:.2f}")
    print(f"Accuracy PP: {performance.accuracy_pp:.2f}")
    print(f"Effective miss count: {performance.effective_miss_count:.2f}")
    
    print("\nConverting beatmap...")
    converted = convert_beatmap(beatmap)
    print(f"Converted beatmap with {len(converted.hit_objects)} hit objects")


if __name__ == "__main__":
    main()