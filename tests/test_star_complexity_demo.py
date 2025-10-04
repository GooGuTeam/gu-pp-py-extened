from sentakki.beatmaps.converter import SentakkiConverter
from sentakki.beatmaps.flags import ConversionFlags

from test_basic_conversion import FakeBeatmap

if __name__=='__main__':
    import copy
    bm = FakeBeatmap()
    c1 = SentakkiConverter(copy.deepcopy(bm), flags=ConversionFlags.NONE)
    r1 = c1.convert()
    c2 = SentakkiConverter(copy.deepcopy(bm), flags=ConversionFlags.FAN_SLIDES)
    r2 = c2.convert()
    print('star(no fan)=', r1.star_rating, 'star(fan enabled)=', r2.star_rating)
