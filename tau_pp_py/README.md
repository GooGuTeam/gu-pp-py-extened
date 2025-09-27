# tau-pp-py

Python implementation of tau mode difficulty and performance calculation, following the structure of rosu-pp.

This project implements the beatmap parsing, converter, difficulty calculation, and performance points calculation algorithms from [taulazer/tau](https://github.com/taulazer/tau) in Python, organized following the project structure of [rosu-pp](https://github.com/MaxOhn/rosu-pp).

## Features

- Beatmap parsing for tau mode
- Beatmap conversion from standard osu! beatmaps to tau mode
- Difficulty calculation
- Performance points (pp) calculation

## Structure

The project follows the structure of rosu-pp:

- `model/` - Data models for beatmaps, hit objects, etc.
- `tau/` - Main tau mode implementation
  - `difficulty/` - Difficulty calculation algorithms
  - `performance/` - Performance points calculation algorithms
  - `convert/` - Beatmap conversion from other modes

## Usage

TODO