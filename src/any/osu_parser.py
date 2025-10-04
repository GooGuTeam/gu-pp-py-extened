import re
from decimal import Decimal
from typing import List, Tuple
from any.models.HitObject import HitObject, Circle, Slider, Spinner
from any.models.TimePoint import TimePoint
from any.models.others import Pos, Curve, CurveType
from any.parser import OsuBeatmap


class OsuFileParser:
    """
    .osu文件解析器
    能够解析.osu文件内容并返回OsuBeatmap结构
    """

    def __init__(self):
        self.beatmap = OsuBeatmap()
        self.beatmap.timing_points = []
        self.beatmap.hit_objects = []

    def parse(self, osu_file_content: str) -> OsuBeatmap:
        """
        解析.osu文件内容
        
        Args:
            osu_file_content: .osu文件的字符串内容
            
        Returns:
            解析后的OsuBeatmap对象
        """
        lines = osu_file_content.splitlines()
        current_section = None

        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith("//"):
                continue

            # 检测章节
            if line.startswith("["):
                current_section = line.strip("[]").lower()
                continue

            # 根据当前章节解析内容
            if current_section == "general":
                self._parse_general(line)
            elif current_section == "metadata":
                self._parse_metadata(line)
            elif current_section == "difficulty":
                self._parse_difficulty(line)
            elif current_section == "timingpoints":
                self._parse_timing_point(line)
            elif current_section == "hitobjects":
                self._parse_hit_object(line)

        # 计算衍生属性
        self._calculate_derived_properties()
        
        return self.beatmap

    def _parse_general(self, line: str):
        """解析[General]部分"""
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # 我们可以在这里添加对General部分的解析，但目前不需要

    def _parse_metadata(self, line: str):
        """解析[Metadata]部分"""
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # 我们可以在这里添加对Metadata部分的解析，但目前不需要

    def _parse_difficulty(self, line: str):
        """解析[Difficulty]部分"""
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "circlesize":
                self.beatmap.cs = float(value)
            elif key == "approachrate":
                self.beatmap.ar = float(value)
            elif key == "overalldifficulty":
                self.beatmap.od = float(value)
            elif key == "hpdrainrate":
                self.beatmap.hp = float(value)
            elif key == "slidermultiplier":
                self.beatmap.slider_multiplier = float(value)
            elif key == "slidertickrate":
                self.beatmap.slider_tick_rate = float(value)

    def _parse_timing_point(self, line: str):
        """解析[TimingPoints]部分"""
        parts = line.split(",")
        if len(parts) >= 8:
            timing_point = TimePoint()
            timing_point.start_time = int(float(parts[0]))
            timing_point.beat_length = Decimal(parts[1])
            timing_point.meter = int(parts[2])
            
            # sample_set 和 sample_index (在osu文件格式中是parts[3]和parts[4])
            timing_point.sample_set = int(parts[3]) if parts[3] else 0
            timing_point.sample_index = int(parts[4]) if parts[4] else 0
            
            # volume (parts[5])
            timing_point.volume = int(parts[5]) if parts[5] else 100
            
            # uninherited (parts[6] == 1 表示非继承)
            timing_point.uninherited = (int(parts[6]) == 1)
            
            # effects (parts[7])
            timing_point.effects = int(parts[7]) if parts[7] else 0
            
            self.beatmap.timing_points.append(timing_point)

    def _parse_hit_object(self, line: str):
        """解析[HitObjects]部分"""
        parts = line.split(",")
        if len(parts) >= 5:
            x = int(parts[0])
            y = int(parts[1])
            time = int(parts[2])
            obj_type = int(parts[3])
            hitsound = int(parts[4])
            
            hit_object = None
            
            # 判断对象类型 (使用位运算检查类型标志)
            if obj_type & 1:  # Circle
                hit_object = Circle()
                self.beatmap.ncircles += 1
            elif obj_type & 2:  # Slider
                hit_object = Slider()
                self.beatmap.nsliders += 1
                
                # 初始化滑条特定字段
                hit_object.edge_hitsounds = []
                hit_object.edge_sets = []
                
                # 解析滑条特定数据
                if len(parts) > 5:
                    self._parse_slider_data(hit_object, parts[5], x, y)
                    
                # 解析滑条边缘音效
                if len(parts) > 8 and parts[8]:
                    try:
                        hit_object.edge_hitsounds = [int(x) for x in parts[8].split("|") if x]
                    except ValueError:
                        hit_object.edge_hitsounds = []
                    
                # 解析滑条边缘音效集
                if len(parts) > 9 and parts[9]:
                    hit_object.edge_sets = [x for x in parts[9].split("|") if x]
                    
            elif obj_type & 8:  # Spinner
                hit_object = Spinner()
                self.beatmap.nspinners += 1
                if len(parts) > 5:
                    hit_object.end_time = int(parts[5])
            
            # 设置通用属性
            if hit_object:
                hit_object.pos = Pos()
                hit_object.pos.x = x
                hit_object.pos.y = y
                hit_object.time = time
                hit_object.hitsound = hitsound
                hit_object.is_newcombo = bool(obj_type & 4)  # New combo flag
                hit_object.hit_sample = ""  # 默认值
                
                # 解析音效信息
                # Hit sample在不同对象类型中位置不同
                if (obj_type & 1) and len(parts) > 5:  # Circle
                    hit_object.hit_sample = parts[5]
                elif (obj_type & 2) and len(parts) > 7:  # Slider
                    # Slider的hitSample通常在最后
                    hit_object.hit_sample = parts[-1]
                elif (obj_type & 8) and len(parts) > 6:  # Spinner
                    hit_object.hit_sample = parts[6]
                
                self.beatmap.hit_objects.append(hit_object)
                self.beatmap.total_hits += 1

    def _parse_slider_data(self, slider: Slider, data: str, start_x: int, start_y: int):
        """解析滑条数据"""
        # 滑条数据格式: 曲线类型|控制点1|控制点2|...|重复次数|像素长度
        slider_parts = data.split("|")
        if len(slider_parts) >= 3:
            # 创建曲线对象
            curve = Curve()
            
            # 获取曲线类型
            curve_type_char = slider_parts[0][0] if slider_parts[0] else 'L'
            if curve_type_char == 'B':
                curve.type = CurveType.Bezier
            elif curve_type_char == 'C':
                curve.type = CurveType.Catmull_rom
            elif curve_type_char == 'L':
                curve.type = CurveType.linear
            elif curve_type_char == 'P':
                curve.type = CurveType.perfrct
            else:
                curve.type = CurveType.linear  # 默认线性
            
            # 解析控制点
            curve.control_points = []
            
            # 添加起始点
            start_point = Pos()
            start_point.x = start_x
            start_point.y = start_y
            curve.control_points.append(start_point)
            
            # 查找重复次数和长度的位置（它们是最后两个参数）
            if len(slider_parts) >= 3:
                repeat_count = slider_parts[-2]  # 倒数第二个是重复次数
                length = slider_parts[-1]        # 最后一个是长度
                
                # 控制点是中间的参数
                # 我们需要找到控制点部分（排除第一个和最后两个）
                control_points_data = slider_parts[1:-2] if len(slider_parts) > 3 else []
                
                # 添加其他控制点
                for point_str in control_points_data:
                    if point_str and ":" in point_str:
                        px, py = point_str.split(":")
                        point = Pos()
                        point.x = int(px)
                        point.y = int(py)
                        curve.control_points.append(point)
                
                slider.curves = curve
                
                # 解析重复次数
                try:
                    slider.repeat_count = int(repeat_count) if repeat_count else 1
                except ValueError:
                    slider.repeat_count = 1
                    
                # 解析像素长度
                try:
                    slider.length = int(float(length)) if length else 0
                except ValueError:
                    slider.length = 0

    def _calculate_derived_properties(self):
        """计算衍生属性"""
        if self.beatmap.hit_objects:
            # 计算播放时间
            first_obj = self.beatmap.hit_objects[0]
            last_obj = self.beatmap.hit_objects[-1]
            self.beatmap.play_time = (last_obj.time - first_obj.time) / 1000.0  # 转换为秒
            
            # 计算排水时间 (简化处理)
            self.beatmap.drain_time = self.beatmap.play_time
            
        # 计算BPM (基于第一个非继承时间点)
        for timing_point in self.beatmap.timing_points:
            if timing_point.uninherited and float(timing_point.beat_length) > 0:
                self.beatmap.bpm = int(60000 / float(timing_point.beat_length))
                break
            elif timing_point.uninherited and float(timing_point.beat_length) < 0:
                # 这是一个继承点，但我们需要找到它所继承的非继承点
                # 简化处理，跳过这种情况
                pass


def parse_osu_file(osu_file_content: str) -> OsuBeatmap:
    """
    解析.osu文件内容并返回OsuBeatmap结构
    
    Args:
        osu_file_content: .osu文件的字符串内容
        
    Returns:
        解析后的OsuBeatmap对象
    """
    parser = OsuFileParser()
    return parser.parse(osu_file_content)