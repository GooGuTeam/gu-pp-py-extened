from sentakki.beatmaps.converter import SentakkiConverter
from sentakki.difficulty.difficultyCalculator import SentakkiDifficultyCalculator
from sentakki.beatmaps.flags import ConversionFlags
from test_basic_conversion import FakeBeatmap

if __name__=='__main__':
    import copy
    bm = FakeBeatmap()
    conv = SentakkiConverter(copy.deepcopy(bm), flags=ConversionFlags.FAN_SLIDES)
    s_bm = conv.convert()
    calc = SentakkiDifficultyCalculator(s_bm)
    attrs = calc.calculate()
    print('star=', attrs.star_rating)
