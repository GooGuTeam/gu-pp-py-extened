from decimal import Decimal

class TimePoint:
    start_time: int
    beat_length: Decimal
    meter: int
    uninherited: bool
    effects: int