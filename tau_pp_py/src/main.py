"""
Main entry point for the tau-pp-py library.
"""

from .model.beatmap import Beatmap
from .tau.difficulty.calculator import TauDifficultyCalculator
from .tau.performance.calculator import TauPerformanceCalculator
from .tau.convert.converter import TauBeatmapConverter


def calculate_difficulty(beatmap: Beatmap):
    """
    Calculate the difficulty of a beatmap.
    
    Args:
        beatmap: The beatmap to calculate difficulty for
        
    Returns:
        DifficultyAttributes: The calculated difficulty attributes
    """
    calculator = TauDifficultyCalculator(beatmap)
    return calculator.calculate()


def calculate_performance(difficulty, beatmap=None):
    """
    Calculate the performance points of a score.
    
    Args:
        difficulty: The difficulty attributes of the beatmap
        beatmap: Optional beatmap for more accurate calculation
        
    Returns:
        PerformanceAttributes: The calculated performance attributes
    """
    calculator = TauPerformanceCalculator(difficulty, beatmap)
    return calculator.calculate()


def convert_beatmap(original_beatmap: Beatmap) -> Beatmap:
    """
    Convert a standard beatmap to a tau beatmap.
    
    Args:
        original_beatmap: The original beatmap to convert
        
    Returns:
        Beatmap: The converted tau beatmap
    """
    converter = TauBeatmapConverter()
    return converter.convert(original_beatmap)