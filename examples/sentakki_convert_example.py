"""示例: 将 osu!standard .osu 文本解析并转换为 sentakki 谱面再计算星级/pp"""
import os, sys
sys.path.append(os.path.join(os.getcwd(), 'src'))
from osu_std.parser import OsuFileParser
from sentakki import SentakkiConverter, SentakkiDifficultyCalculator, SentakkiPerformanceCalculator, SentakkiMods
from sentakki.converter import ConversionFlags, Tap, Hold, Slide

OSU_SAMPLE = """osu file format v14

[General]
AudioFilename: test.mp3

[Metadata]
Title:Sample
Artist:Me
Creator:You
Version:Hard

[Difficulty]
HPDrainRate:5
CircleSize:4
OverallDifficulty:7
ApproachRate:8
SliderMultiplier:1.4
SliderTickRate:1

[TimingPoints]
0,500,4,2,0,70,1,0

[HitObjects]
256,192,0,1,0,0:0:0:0:
128,192,500,1,8,0:0:0:0:
384,192,1000,2,0,B|384:256,1,180,0:0|0:0,0:0:0:0:
256,192,1800,12,0,2500,0:0:0:0:
256,96,2600,1,12,0:0:0:0:
"""

def main():
    parser = OsuFileParser()
    std_bm = parser.parse(OSU_SAMPLE)
    # 使用一组 flags 演示：双押 + 允许扇形 slide
    flags = ConversionFlags.TWIN_NOTES | ConversionFlags.FAN_SLIDES | ConversionFlags.TWIN_SLIDES
    sentakki_bm = SentakkiConverter(std_bm, flags=flags).convert()
    diff = SentakkiDifficultyCalculator(sentakki_bm, mods=SentakkiMods.NOMOD).calculate()
    score = {
        'accuracy': 0.97,
        'max_combo': sentakki_bm.max_combo - 2,
        'statistics': {'miss': 1},
        'maximum_achievable_combo': sentakki_bm.max_combo
    }
    perf = SentakkiPerformanceCalculator().calculate(score, diff)
    print('Converted objects:', len(sentakki_bm.objects))
    kinds = {type(o).__name__:0 for o in sentakki_bm.objects}
    for o in sentakki_bm.objects:
        kinds[type(o).__name__] += 1
    print('Type breakdown:', kinds)
    print('Estimated base star:', sentakki_bm.star_rating)
    print('Final SR (with clock & inflate):', diff.star_rating)
    print('PP:', perf.total)
    # 列出前几个对象
    for o in sentakki_bm.objects[:5]:  # type: ignore[attr-defined]
        # 运行期属性存在，这里忽略静态检查
        print('  ', type(o).__name__, 't=', getattr(o,'time',None), 'lane=', getattr(o,'lane',None), 'flags=', getattr(o,'flags',None))

if __name__ == '__main__':
    main()
