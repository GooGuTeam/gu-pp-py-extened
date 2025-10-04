from enum import IntFlag, Enum

class ConversionFlags(IntFlag):
    NONE = 0
    TWIN_NOTES = 1 << 0
    TWIN_SLIDES = 1 << 1
    FAN_SLIDES = 1 << 2
    OLD_CONVERTER = 1 << 3
    DISABLE_COMPOSITE_SLIDES = 1 << 4

class StreamDirection(Enum):
    NONE = 0
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1

__all__ = ['ConversionFlags','StreamDirection']