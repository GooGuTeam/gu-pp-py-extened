"""HitObject 相关数据结构与解析逻辑（从 parser.py 拆分）"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

@dataclass
class SliderInfo:
    curve_type: str
    points: List[Tuple[int, int]]
    repeat: int
    pixel_length: float
    edge_sounds: List[int] = field(default_factory=list)
    edge_sets: List[str] = field(default_factory=list)
    node_hit_sounds: List[Dict[str, Any]] = field(default_factory=list)  # decoded per-node flags
    end_x: int = 0  # approximate path end position (last control point)
    end_y: int = 0

@dataclass
class SpinnerInfo:
    end_time: int

@dataclass
class CircleInfo:
    """HitCircle 额外信息（目前仅标记是否为新连击开头，可继续扩展）"""
    new_combo: bool

@dataclass
class HitObject:
    x: int
    y: int
    time: int
    type: int
    hit_sound: int
    extras: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_circle(self) -> bool:
        return bool(self.type & 0b1)

    @property
    def is_slider(self) -> bool:
        return bool(self.type & 0b10)

    @property
    def is_spinner(self) -> bool:
        return bool(self.type & 0b1000)

    @property
    def is_new_combo(self) -> bool:
        return bool(self.type & 0b100)

# ---------------- Parsing ---------------- #

def _parse_slider_path(path_def: str) -> Tuple[str, List[Tuple[int, int]]]:
    parts = path_def.split('|')
    curve_type = parts[0]
    pts: List[Tuple[int, int]] = []
    for p in parts[1:]:
        if ':' not in p:
            continue
        xs, ys = p.split(':', 1)
        try:
            pts.append((int(xs), int(ys)))
        except ValueError:
            continue
    return curve_type, pts


def parse_hit_object(line: str) -> Optional[HitObject]:
    parts = line.split(',')
    if len(parts) < 5:
        return None
    try:
        x = int(parts[0]); y = int(parts[1]); time = int(parts[2]); type_flag = int(parts[3]); hit_sound_val = int(parts[4])
    except ValueError:
        return None

    extras: Dict[str, Any] = {}

    # 解析结尾 hitSample 字段（位置依赖于 hitobject 类型）
    # 格式: sampleSet:additionSet:customIndex:volume:filename  (filename 可为空)
    def parse_hit_sample(sample_str: str):
        segs = sample_str.split(':')
        while len(segs) < 5:
            segs.append('')
        try:
            sample_set = int(segs[0]) if segs[0] else 0
            addition_set = int(segs[1]) if segs[1] else 0
            custom_index = int(segs[2]) if segs[2] else 0
            volume = int(segs[3]) if segs[3] else 0
            filename = segs[4] if len(segs) > 4 else ''
        except ValueError:
            sample_set = addition_set = custom_index = volume = 0
            filename = ''
        return {
            'sample_set': sample_set,
            'addition_set': addition_set,
            'custom_index': custom_index,
            'volume': volume,
            'filename': filename
        }

    def decode_hit_sound_flags(v: int):
        # https://osu.ppy.sh/wiki/en/Client/File_formats/Osu_(file_format)#hitsounds
        return {
            'normal': bool(v & 0b1 == 0 or v & 0b1),  # 基础 normal 隐式存在，但仍保留标志
            'whistle': bool(v & 0b10),
            'finish': bool(v & 0b100),
            'clap': bool(v & 0b1000),
            'raw': v
        }

    extras['hit_sounds'] = decode_hit_sound_flags(hit_sound_val)

    # HitCircle (普通圆)
    if type_flag & 0b1 and not (type_flag & 0b10) and not (type_flag & 0b1000):
        extras["circle"] = CircleInfo(new_combo=bool(type_flag & 0b100))
        # hitSample 位置 index 5 (如果存在)
        if len(parts) > 5 and ':' in parts[5]:
            extras['sample'] = parse_hit_sample(parts[5])

    # Slider
    if type_flag & 0b10:
        if len(parts) >= 8:
            path_def = parts[5]
            try:
                repeat = int(parts[6])
                pixel_length = float(parts[7])
            except ValueError:
                repeat = 0
                pixel_length = 0.0
            curve_type, points = _parse_slider_path(path_def)
            edge_sounds = []
            edge_sets = []
            if len(parts) > 8 and parts[8]:
                try:
                    edge_sounds = [int(v) for v in parts[8].split('|') if v]
                except ValueError:
                    pass
            if len(parts) > 9 and parts[9]:
                edge_sets = parts[9].split('|')

            # Build per-node hit sounds (length should be repeat+1; pad/trim accordingly)
            node_count = repeat + 1
            node_hit_sounds: List[Dict[str, Any]] = []
            def decode_node(v: int):
                return {
                    'normal': bool(v & 0b1 == 0 or v & 0b1),
                    'whistle': bool(v & 0b10),
                    'finish': bool(v & 0b100),
                    'clap': bool(v & 0b1000),
                    'raw': v
                }
            if edge_sounds:
                # edge_sounds may include tail; spec: exactly node_count entries
                for i in range(node_count):
                    val = edge_sounds[i] if i < len(edge_sounds) else 0
                    node_hit_sounds.append(decode_node(val))
            else:
                node_hit_sounds = [decode_node(0) for _ in range(node_count)]

            # Approximate end position: last control point if exists else start (x,y)
            end_x = points[-1][0] if points else x
            end_y = points[-1][1] if points else y
            slider_info = SliderInfo(curve_type, points, repeat, pixel_length, edge_sounds, edge_sets, node_hit_sounds, end_x, end_y)
            extras["slider"] = slider_info
            # hitSample 位置 index 10 (overall sample for tail per osu format)
            if len(parts) > 10 and ':' in parts[10]:
                extras['sample'] = parse_hit_sample(parts[10])

    # Spinner
    if type_flag & 0b1000:
        if len(parts) >= 7:
            try:
                end_time = int(parts[5])
                extras["spinner"] = SpinnerInfo(end_time)
            except ValueError:
                pass
            # hitSample 位置 index 6
            if len(parts) > 6 and ':' in parts[6]:
                extras['sample'] = parse_hit_sample(parts[6])

    return HitObject(x, y, time, type_flag, hit_sound_val, extras)
