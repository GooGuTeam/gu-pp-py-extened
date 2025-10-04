"""Backward compatibility shim for the legacy path `sentakki.converter`.

Real implementation moved to `sentakki.beatmaps`.

Preferred usage:
    from sentakki.beatmaps import SentakkiConverter, ConversionFlags
"""
from .beatmaps import (
    SentakkiConverter, ConversionFlags,
    SentakkiObjectBase, Tap, Hold, Slide, SlideSegment, Touch, TouchHold,
    FLAG_BREAK, FLAG_EX, FLAG_TWIN, FLAG_FAN,
)

__all__ = [
    'SentakkiConverter', 'ConversionFlags',
    'SentakkiObjectBase', 'Tap', 'Hold', 'Slide', 'SlideSegment', 'Touch', 'TouchHold',
    'FLAG_BREAK', 'FLAG_EX', 'FLAG_TWIN', 'FLAG_FAN',
]
