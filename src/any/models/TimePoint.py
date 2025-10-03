from decimal import Decimal

class TimePoint:
    start_time: int
    beat_length: Decimal
    meter: int
    # 新增音效相关字段
    sample_set: int = 0
    sample_index: int = 0
    volume: int = 0
    uninherited: bool
    effects: int