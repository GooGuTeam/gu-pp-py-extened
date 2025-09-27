from enum import Enum
from osupyparser import OsuFile

class GamemodeExtended(str,Enum):
    TAU="tau"

class Beatmap:
    ogrinal_beatmap: OsuFile
    def __init__(self,beatmap:str) -> None:
        self.ogrinal_beatmap=OsuFile(beatmap)
        pass
    def convert_to(self,mode:GamemodeExtended):
        pass