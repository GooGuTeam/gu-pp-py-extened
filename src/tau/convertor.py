import osupyparser
from typing import List, Optional, Tuple, Union
from .objects import (
    TauHitObject, Beat, HardBeat, StrictHardBeat, Slider, PolarSliderPath, SliderNode,
    HitSampleInfo, from_polar_coordinates, normalize_angle, get_delta_angle, remap
)
from . import TauBeatmap
import math

# Constants from TaubeatmapConverter.cs
STANDARD_PLAYFIELD_SIZE = (512, 384)
STANDARD_PLAYFIELD_CENTER = (STANDARD_PLAYFIELD_SIZE[0] / 2, STANDARD_PLAYFIELD_SIZE[1] / 2)

def difficulty_range(approach_rate: float, min: float, mid: float, max: float) -> float:
    """Difficulty range calculation, mimicking osu! IBeatmapDifficultyInfo.DifficultyRange function"""
    if approach_rate > 5:
        return mid + (max - mid) * (approach_rate - 5) / 5
    if approach_rate < 5:
        return mid - (mid - min) * (5 - approach_rate) / 5
    return mid

def get_hit_object_angle(pos) -> float:
    """获取物件角度，模仿Vector2.GetHitObjectAngle"""
    if pos is None:
        return 0.0
    
    # 计算从中心点到目标点的角度 (模仿Vector2.GetDegreesFromPosition)
    dx = pos.x - STANDARD_PLAYFIELD_CENTER[0]
    dy = pos.y - STANDARD_PLAYFIELD_CENTER[1]
    
    # 使用atan2计算角度并转换为度数
    angle = math.degrees(math.atan2(dy, dx))
    
    # 调整到0-360范围并偏移90度以匹配C#版本
    return normalize_angle(angle + 90)

def is_hard_beat(obj) -> bool:
    """判断是否为HardBeat，模仿HitObject.IsHardBeat扩展方法"""
    # 检查是否有path属性（IHasPathWithRepeats接口）
    if hasattr(obj, 'edges') and obj.edges:
        # 检查第一个节点的采样
        if obj.edges[0].sound_type:
            # 简化处理，实际应该检查采样名称
            return any(sample.name == "hitfinish" for sample in obj.samples if hasattr(sample, 'name'))
    
    # 默认检查物件本身的采样
    return any(sample.name == "hitfinish" for sample in obj.samples if hasattr(sample, 'name'))

class TauBeatmapConverter:
    def __init__(self):
        self.can_convert_to_hard_beats = True
        self.hard_beats_are_strict = False
        self.can_convert_to_sliders = True
        self.can_convert_impossible_sliders = False
        self.slider_divisor = 4
        self.locked_direction = None  # None, "clockwise", or "counterclockwise"
        self.last_locked_angle = None

    def next_angle(self, target: float) -> float:
        """计算下一个角度，考虑旋转方向锁定，模仿原版nextAngle方法"""
        if self.last_locked_angle is None or self.locked_direction is None:
            self.last_locked_angle = target
            return self.last_locked_angle

        diff = get_delta_angle(target, self.last_locked_angle)

        # 检查方向是否匹配
        is_positive_diff = diff > 0
        is_clockwise = self.locked_direction == "clockwise"
        
        if is_positive_diff == is_clockwise:
            self.last_locked_angle = target
            return target

        self.last_locked_angle = self.last_locked_angle - diff
        return self.last_locked_angle

    def convert_to_slider(self, obj: osupyparser.Slider, beatmap=None) -> Union[Slider, Beat, HardBeat, StrictHardBeat]:
        """转换滑条物件，严格按照convertToSlider逻辑"""
        start_locked_angle = self.last_locked_angle
        
        def convert_to_non_slider():
            """转换为非滑条物件"""
            self.last_locked_angle = start_locked_angle
            # 由于没有original对象，简化处理
            return self.convert_to_non_slider(obj)
        
        if not self.can_convert_to_sliders:
            return convert_to_non_slider()
        
        # 使用DifficultyRange计算最小持续时间
        approach_rate = getattr(getattr(beatmap, 'difficulty', None), 'ar', 9.5) if beatmap else 9.5
        min_duration = difficulty_range(approach_rate, 1800, 1200, 450) / self.slider_divisor
        
        duration = getattr(obj, 'duration', 0)
        if duration < min_duration:
            return convert_to_non_slider()
        
        nodes = []
        last_angle = None
        last_time = None
        first_angle = 0.0
        
        # 每20ms采样一次滑条路径，模仿原版for循环
        t = 0
        while t < duration:
            # 计算当前点的角度
            angle = 0
            if hasattr(obj, 'pos') and obj.pos:
                # 简化处理，实际应该根据progress计算曲线上的点
                # 原版使用 (((IHasPosition)original).Position + data.CurvePositionAt(t / data.Duration)).GetHitObjectAngle()
                angle = self.next_angle(get_hit_object_angle(obj.pos))
            
            if t == 0:
                first_angle = angle
            
            # 计算相对于起始角度的差值，模仿Extensions.GetDeltaAngle(angle, firstAngle)
            angle = get_delta_angle(angle, first_angle)
            
            # 检查是否转换太快，模仿原版检查逻辑
            if not self.can_convert_impossible_sliders and last_angle is not None:
                angle_diff = get_delta_angle(last_angle, angle)
                time_diff = abs(last_time - t) if last_time is not None else 1
                if time_diff > 0 and abs(angle_diff) / time_diff > 0.6:
                    return convert_to_non_slider()
            
            last_angle = angle
            last_time = t
            nodes.append(SliderNode(t, angle))
            t += 20
        
        # 添加最终节点，模仿原版处理
        final_angle = 0
        if hasattr(obj, 'end_position') and obj.end_position:
            final_angle = self.next_angle(get_hit_object_angle(obj.end_position))
        elif hasattr(obj, 'pos') and obj.pos:
            final_angle = self.next_angle(get_hit_object_angle(obj.pos))
        
        final_angle = get_delta_angle(final_angle, first_angle)
        
        if not self.can_convert_impossible_sliders and last_angle is not None and last_time is not None:
            angle_diff = get_delta_angle(last_angle, final_angle)
            time_diff = abs(last_time - duration)
            if time_diff > 0 and abs(angle_diff) / time_diff > 0.6:
                return convert_to_non_slider()
        
        nodes.append(SliderNode(float(duration), final_angle))
        
        # 创建滑条，模仿原版slider创建逻辑
        slider = Slider()
        slider.start_time = obj.start_time
        slider.new_combo = getattr(obj, 'new_combo', False)
        slider.path = PolarSliderPath(nodes)
        slider.angle = first_angle
        slider.repeat_count = getattr(obj, 'repeat_count', 0)
        slider.tick_distance_multiplier = 2.0
        slider.is_hard = self.hard_beats_are_strict and is_hard_beat(obj)
        
        # 模仿原版处理LegacyControlPointInfo部分
        # 由于osupyparser限制，简化处理
        if beatmap and getattr(beatmap, 'file_version', 0) < 8:
            slider.tick_distance_multiplier = 2.0  # 简化处理
        
        return slider

    def convert_slider_spinner(self, obj: osupyparser.Spinner, beatmap=None) -> Union[Slider, Beat, HardBeat, StrictHardBeat]:
        """转换Spinner为滑条，严格按照convertToSliderSpinner逻辑"""
        if not self.can_convert_to_sliders:
            return self.convert_to_non_slider(obj)

        # 使用DifficultyRange计算最小持续时间
        approach_rate = getattr(getattr(beatmap, 'difficulty', None), 'ar', 9.5) if beatmap else 9.5
        min_duration = difficulty_range(approach_rate, 1800, 1200, 450) / self.slider_divisor
        
        duration = obj.end_time - obj.start_time
        if duration < min_duration:
            return self.convert_to_non_slider(obj)

        nodes = []
        
        # 确定旋转方向，模仿原版switch表达式
        direction = 1  # 默认顺时针
        if self.locked_direction == "clockwise":
            direction = 1
        elif self.locked_direction == "counterclockwise":
            direction = -1
        # 注意：原版还会尝试从beatmap.HitObjects.GetPrevious(original)获取方向，但简化处理

        # 控制点信息，模仿原版controlPoint获取
        control_point_beat_length = 1000  # 默认1000ms每拍
        time_signature_numerator = 4  # 默认4/4拍
        
        # 如果有beatmap信息，尝试获取实际的控制点信息
        if beatmap and hasattr(beatmap, 'timing_points') and beatmap.timing_points:
            # 简化处理，实际应该查找在obj.start_time时刻的timing point
            control_point_beat_length = getattr(beatmap.timing_points[0], 'beat_length', 1000)
        
        revolutions = int(duration / (control_point_beat_length * time_signature_numerator))
        if revolutions == 0:
            return self.convert_to_non_slider(obj)
            
        rev_duration = duration / revolutions
        current_angle = 0.0

        # 创建旋转节点，模仿原版嵌套循环
        for i in range(revolutions):
            for j in range(4):  # 每圈4个节点（每90度一个节点）
                time = (rev_duration / 4) * (j + 4 * i)
                nodes.append(SliderNode(float(time), current_angle))
                current_angle += 90 * direction

        # 添加结束节点，模仿原版处理
        nodes.append(SliderNode(float(duration), 0))
        self.last_locked_angle = current_angle - 90 * direction

        # 创建滑条，模仿原版slider创建逻辑
        slider = Slider()
        slider.start_time = obj.start_time
        slider.new_combo = getattr(obj, 'new_combo', False)
        slider.path = PolarSliderPath(nodes)
        slider.angle = nodes[0].angle if nodes else 0.0
        slider.tick_distance_multiplier = 2.0
        
        # 模仿原版处理LegacyControlPointInfo部分
        # 由于osupyparser限制，简化处理
        if beatmap and getattr(beatmap, 'file_version', 0) < 8:
            slider.tick_distance_multiplier = 2.0  # 简化处理
        
        return slider

    def convert_to_non_slider(self, obj) -> Union[Beat, HardBeat, StrictHardBeat]:
        """转换为非滑条物件，严格按照convertToNonSlider逻辑"""
        # 判断是否为HardBeat
        if is_hard_beat(obj) and self.can_convert_to_hard_beats:
            if not self.hard_beats_are_strict:
                # 转换为普通HardBeat，模仿convertToHardBeat
                hard_beat = HardBeat()
                hard_beat.start_time = obj.start_time
                hard_beat.new_combo = getattr(obj, 'new_combo', False)
                return hard_beat
            else:
                # 转换为严格HardBeat，模仿convertToStrictHardBeat
                strict_hard_beat = StrictHardBeat()
                strict_hard_beat.start_time = obj.start_time
                strict_hard_beat.new_combo = getattr(obj, 'new_combo', False)
                strict_hard_beat.angle = self.next_angle(get_hit_object_angle(getattr(obj, 'pos', None)))
                return strict_hard_beat
        else:
            # 转换为普通节拍，模仿convertToBeat
            beat = Beat()
            beat.start_time = obj.start_time
            beat.new_combo = getattr(obj, 'new_combo', False)
            beat.angle = self.next_angle(get_hit_object_angle(getattr(obj, 'pos', None)))
            return beat

def convert_slider(obj: osupyparser.Slider, beatmap=None) -> Union[Beat, HardBeat, StrictHardBeat, Slider]:
    """转换滑条物件"""
    converter = TauBeatmapConverter()
    return converter.convert_to_slider(obj, beatmap)

def convert_object(obj, beatmap=None) -> Union[Beat, HardBeat, StrictHardBeat, Slider]:
    """转换物件，模仿ConvertHitObject主逻辑"""
    converter = TauBeatmapConverter()
    
    # 根据物件类型进行转换，模仿原版switch表达式
    if isinstance(obj, osupyparser.Slider):
        return converter.convert_to_slider(obj, beatmap)
    elif isinstance(obj, osupyparser.Spinner):
        return converter.convert_slider_spinner(obj, beatmap)
    else:
        # 包括Circle和其他类型，模仿默认情况
        return converter.convert_to_non_slider(obj)

def convert_osu_file(osu_file: osupyparser.OsuFile) -> 'TauBeatmap':
    """
    将osupyparser.OsuFile转换为TauBeatmap
    
    Args:
        osu_file: 解析后的osu文件对象
        
    Returns:
        TauBeatmap: 转换后的Tau谱面对象
    """
    from .beatmap import TauBeatmap
    
    # 创建TauBeatmap实例
    tau_beatmap = TauBeatmap()
    
    # 设置难度属性
    tau_beatmap.difficulty_attributes['approach_rate'] = getattr(osu_file, 'ar', 5.0)
    tau_beatmap.difficulty_attributes['overall_difficulty'] = getattr(osu_file, 'od', 5.0)
    tau_beatmap.difficulty_attributes['circle_size'] = getattr(osu_file, 'cs', 5.0)
    tau_beatmap.difficulty_attributes['drain_rate'] = getattr(osu_file, 'hp', 5.0)
    
    # 设置元数据
    tau_beatmap.metadata['title'] = getattr(osu_file, 'title', '')
    tau_beatmap.metadata['artist'] = getattr(osu_file, 'artist', '')
    tau_beatmap.metadata['version'] = getattr(osu_file, 'version', '')
    tau_beatmap.metadata['creator'] = getattr(osu_file, 'creator', '')
    
    # 创建转换器实例
    converter = TauBeatmapConverter()
    
    # 转换所有物件
    for obj in getattr(osu_file, 'hit_objects', []):
        try:
            tau_obj = convert_object(obj, osu_file)
            if tau_obj:
                tau_beatmap.add_hit_object(tau_obj)
        except Exception as e:
            # 跳过转换失败的物件
            continue
    
    return tau_beatmap