# Tau-pp

PP and star calculation for the Tau osu! gamemode, organized in the style of [rosu-pp](https://github.com/MaxOhn/rosu-pp).

This library provides Python implementations for calculating difficulty and performance attributes for the Tau ruleset of osu!, similar to how rosu-pp works for other osu! gamemodes.

## Overview

Tau is a custom osu! ruleset featuring a paddle and notes. This library allows you to calculate star ratings and performance points (PP) for Tau beatmaps.

## Project Structure

The project is organized following the rosu-pp pattern:

```
src/
└── tau/
    ├── __init__.py              # Main module exports
    ├── objects/                 # Hit object definitions
    │   ├── tauHitObject.py      # Base hit object class
    │   ├── angledObject.py      # Angled hit objects
    │   ├── beat.py              # Beat objects
    │   └── slider.py            # Slider objects
    ├── difficulty/              # Difficulty calculation
    │   └── calculator.py        # Difficulty calculator and attributes
    └── performance/             # Performance calculation
        └── calculator.py        # Performance calculator and attributes
```

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/tau-pp-py.git
cd tau-pp-py

# Install dependencies
pip install -e .
```

## Usage

Example usage is provided in [tau_example.py](tau_example.py):

```python
from tau import TauDifficultyCalculator, TauPerformanceCalculator

# Create a beatmap (in a full implementation)
# beatmap = Beatmap.from_path("./path/to/beatmap.osu")

# Calculate difficulty
difficulty_calc = TauDifficultyCalculator(ruleset, beatmap)
difficulty_attrs = difficulty_calc.calculate()

# Calculate performance
performance_calc = TauPerformanceCalculator()
performance_attrs = performance_calc.calculate(difficulty_attrs, score)
```

## Object Types

Based on the original Tau ruleset, the following object types are implemented:

1. **TauHitObject** - Base class for all hit objects
2. **AngledTauHitObject** - Base class for objects with angle parameters
3. **Beat** - Basic hit object that needs to be hit at a specific time and angle
4. **Slider** - Sliding object with a path that needs to be followed
5. **HardBeat** - Special type of hit object (to be implemented)

## Calculation Modules

### Difficulty Calculation

The difficulty calculation is based on four main skills:
- **Aim** - Measures the spatial difficulty of the map
- **Aim (No Sliders)** - Measures aim difficulty excluding sliders
- **Speed** - Measures the temporal difficulty of the map
- **Complexity** - Measures the complexity of the map

### Performance Calculation

The performance calculation evaluates a score based on:
- **Aim Performance** - PP awarded for aim
- **Speed Performance** - PP awarded for speed
- **Accuracy Performance** - PP awarded for accuracy
- **Complexity Performance** - PP awarded for complexity

## API

### TauDifficultyCalculator

计算 beatmap 的难度属性。

```python
calculator = TauDifficultyCalculator(beatmap)
attrs = calculator.calculate(mods=[], clock_rate=1.0)
```

### TauPerformanceCalculator

计算分数的性能点数。

```python
calculator = TauPerformanceCalculator()
attrs = calculator.calculate(score, difficulty_attributes)
```

## Development Status

This is a work in progress. The current implementation includes:
- Basic object structure based on the Tau ruleset
- Skeleton of difficulty calculation system
- Skeleton of performance calculation system
- Example usage file

TODO:
- Complete implementation of all object types (HardBeat, etc.)
- Implement actual calculation algorithms
- Add beatmap parsing capabilities
- Add mod support
- Add proper testing

## Related Projects

- [rosu-pp](https://github.com/MaxOhn/rosu-pp) - The original Rust library this structure is based on
- [tau](https://github.com/taulazer/tau) - The original Tau ruleset for osu!
- [rosu-pp-py](https://github.com/MaxOhn/rosu-pp-py) - Python bindings for rosu-pp

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.