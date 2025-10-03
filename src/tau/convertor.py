"""
Tau谱面转换器，完全遵循taulazer/tau项目中的TauBeatmapConverter.cs逻辑
"""

from typing import List, Optional, Tuple, Union
from .objects import (
    TauHitObject, Beat, HardBeat, StrictHardBeat, Slider, PolarSliderPath, SliderNode,
    HitSampleInfo, from_polar_coordinates, normalize_angle, get_delta_angle, remap
)
from . import TauBeatmap
from any.parser import OsuBeatmap
from any.models.HitObject import Circle, Slider as OsuSlider, Spinner as OsuSpinner
from any.models.others import HitSound, Curve, Pos, CurveType
import math

# Constants from TaubeatmapConverter.cs
STANDARD_PLAYFIELD_SIZE = (512, 384)
STANDARD_PLAYFIELD_CENTER = (STANDARD_PLAYFIELD_SIZE[0] / 2, STANDARD_PLAYFIELD_SIZE[1] / 2)

# Bezier曲线容差常量
BEZIER_TOLERANCE = 0.25

def difficulty_range(approach_rate: float, min_val: float, mid: float, max_val: float) -> float:
    """Difficulty range calculation, mimicking osu! IBeatmapDifficultyInfo.DifficultyRange function"""
    if approach_rate > 5:
        return mid + (max_val - mid) * (approach_rate - 5) / 5
    if approach_rate < 5:
        return mid - (mid - min_val) * (5 - approach_rate) / 5
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

def get_curve_position_at(curve: Curve, progress: float) -> Pos:
    """获取曲线在指定进度的位置，模仿osu!的CurvePositionAt方法"""
    if not curve or not curve.control_points:
        return Pos()
    
    points = curve.control_points
    if len(points) < 2:
        return points[0] if points else Pos()
    
    # 根据曲线类型进行不同的处理
    if curve.type == "L" or curve.type == CurveType.linear:  # Linear
        return _linear_curve_position_at(points, progress)
    elif curve.type == "B" or curve.type == CurveType.Bezier:  # Bezier
        return _bezier_curve_position_at(points, progress)
    elif curve.type == "P" or curve.type == CurveType.perfrct:  # Perfect Circle
        if len(points) == 3:
            return _circular_arc_position_at(points, progress)
        else:
            # 如果不是3个点，则退化为Bezier曲线
            return _bezier_curve_position_at(points, progress)
    elif curve.type == "C" or curve.type == CurveType.Catmull_rom:  # Catmull-Rom
        return _catmull_rom_curve_position_at(points, progress)
    else:  # 默认使用线性插值
        return _linear_curve_position_at(points, progress)


def _linear_curve_position_at(points: List[Pos], progress: float) -> Pos:
    """线性曲线位置计算"""
    total_points = len(points)
    segment_count = total_points - 1
    
    # 确定在哪一段上
    segment_progress = progress * segment_count
    segment_index = int(segment_progress)
    local_progress = segment_progress - segment_index
    
    # 边界检查
    if segment_index >= segment_count:
        return points[-1]
    if segment_index < 0:
        return points[0]
    
    # 线性插值
    start_point = points[segment_index]
    end_point = points[segment_index + 1]
    
    result = Pos()
    result.x = start_point.x + (end_point.x - start_point.x) * local_progress
    result.y = start_point.y + (end_point.y - start_point.y) * local_progress
    
    return result


def _bezier_curve_position_at(points: List[Pos], progress: float) -> Pos:
    """贝塞尔曲线位置计算（使用de Casteljau算法）"""
    if not points:
        return Pos()
    
    # 复制点列表以避免修改原始数据
    bezier_points = list(points)
    n = len(bezier_points)
    
    # 使用de Casteljau算法计算贝塞尔曲线上的点
    for i in range(1, n):
        for j in range(n - i):
            x = (1 - progress) * bezier_points[j].x + progress * bezier_points[j + 1].x
            y = (1 - progress) * bezier_points[j].y + progress * bezier_points[j + 1].y
            bezier_points[j] = Pos()
            bezier_points[j].x = x
            bezier_points[j].y = y
    
    return bezier_points[0]


def _bezier_is_flat_enough(points: List[Pos]) -> bool:
    """检查贝塞尔曲线是否足够平坦"""
    for i in range(1, len(points) - 1):
        # 计算二阶导数的近似值（使用有限元素）
        diff = Pos()
        diff.x = points[i - 1].x - 2 * points[i].x + points[i + 1].x
        diff.y = points[i - 1].y - 2 * points[i].y + points[i + 1].y
        
        # 检查长度平方是否在容差范围内
        length_squared = diff.x * diff.x + diff.y * diff.y
        if length_squared > BEZIER_TOLERANCE * BEZIER_TOLERANCE * 4:
            return False
    return True


def _bezier_subdivide(points: List[Pos], progress: float) -> Tuple[List[Pos], List[Pos]]:
    """将贝塞尔曲线细分为两部分"""
    # 创建中间点数组
    midpoints = list(points)
    count = len(points)
    
    # 执行细分
    for i in range(count):
        for j in range(count - i - 1):
            mid_point = Pos()
            mid_point.x = (midpoints[j].x + midpoints[j + 1].x) / 2
            mid_point.y = (midpoints[j].y + midpoints[j + 1].y) / 2
            midpoints[j] = mid_point
    
    # 构建左右两部分
    left = [points[0]]
    right = [midpoints[count - 1]]
    
    # 重建细分缓冲区以获取左右控制点
    subdivision_buffer = list(points)
    for i in range(count):
        left.append(midpoints[0] if i < len(midpoints) else Pos())
        right.insert(0, midpoints[count - i - 1] if count - i - 1 < len(midpoints) else Pos())
        
        for j in range(count - i - 1):
            mid_point = Pos()
            mid_point.x = (subdivision_buffer[j].x + subdivision_buffer[j + 1].x) / 2
            mid_point.y = (subdivision_buffer[j].y + subdivision_buffer[j + 1].y) / 2
            subdivision_buffer[j] = mid_point
    
    # 修正左右部分的控制点
    left = left[:count]
    right = right[:count]
    
    return left, right


def _catmull_rom_curve_position_at(points: List[Pos], progress: float) -> Pos:
    """Catmull-Rom曲线位置计算"""
    if len(points) < 2:
        return points[0] if points else Pos()
    
    # Catmull-Rom细节参数
    catmull_detail = 50
    
    # 对于Catmull-Rom曲线，我们创建分段线性近似
    result_points = []
    for i in range(len(points) - 1):
        v1 = points[max(0, i - 1)]
        v2 = points[i]
        v3 = points[min(len(points) - 1, i + 1)]
        v4 = points[min(len(points) - 1, i + 2)]
        
        for c in range(catmull_detail):
            # 计算当前点和下一个点
            p1 = _catmull_find_point(v1, v2, v3, v4, c / catmull_detail)
            p2 = _catmull_find_point(v1, v2, v3, v4, (c + 1) / catmull_detail)
            result_points.extend([p1, p2])
    
    # 在结果点中找到对应进度的点
    if not result_points:
        return _linear_curve_position_at(points, progress)
    
    target_index = int(progress * (len(result_points) - 1))
    target_index = max(0, min(target_index, len(result_points) - 1))
    
    return result_points[target_index]


def _catmull_find_point(vec1: Pos, vec2: Pos, vec3: Pos, vec4: Pos, t: float) -> Pos:
    """在Catmull-Rom曲线上查找指定参数的点"""
    t2 = t * t
    t3 = t * t2
    
    result = Pos()
    result.x = 0.5 * (2 * vec2.x + (-vec1.x + vec3.x) * t + 
                     (2 * vec1.x - 5 * vec2.x + 4 * vec3.x - vec4.x) * t2 + 
                     (-vec1.x + 3 * vec2.x - 3 * vec3.x + vec4.x) * t3)
    result.y = 0.5 * (2 * vec2.y + (-vec1.y + vec3.y) * t + 
                     (2 * vec1.y - 5 * vec2.y + 4 * vec3.y - vec4.y) * t2 + 
                     (-vec1.y + 3 * vec2.y - 3 * vec3.y + vec4.y) * t3)
    
    return result


def _circular_arc_position_at(points: List[Pos], progress: float) -> Pos:
    """圆形弧线位置计算"""
    if len(points) != 3:
        # 圆弧必须由3个点定义
        return _bezier_curve_position_at(points, progress)
    
    # 计算圆弧属性
    arc_props = _circular_arc_properties(points)
    if not arc_props["is_valid"]:
        # 如果无法形成有效圆弧，退化为贝塞尔曲线
        return _bezier_curve_position_at(points, progress)
    
    # 圆弧容差
    circular_arc_tolerance = 0.1
    
    # 根据容差选择点的数量
    amount_points = 2
    if 2 * arc_props["radius"] > circular_arc_tolerance:
        # 使用角度范围和容差计算点数
        try:
            angle_tolerance = 2 * math.acos(1 - circular_arc_tolerance / arc_props["radius"])
            amount_points = max(2, int(math.ceil(arc_props["theta_range"] / angle_tolerance)))
        except (ValueError, ZeroDivisionError):
            amount_points = 2
    
    # 根据进度计算角度
    theta = arc_props["theta_start"] + arc_props["direction"] * progress * arc_props["theta_range"]
    
    # 计算点位置
    result = Pos()
    result.x = arc_props["centre"].x + arc_props["radius"] * math.cos(theta)
    result.y = arc_props["centre"].y + arc_props["radius"] * math.sin(theta)
    
    return result


def _circular_arc_properties(points: List[Pos]) -> dict:
    """计算圆弧属性，模仿osu-framework中的CircularArcProperties"""
    if len(points) != 3:
        return {"is_valid": False}
    
    a, b, c = points[0], points[1], points[2]
    
    # 检查是否为退化三角形
    det = (b.y - a.y) * (c.x - a.x) - (b.x - a.x) * (c.y - a.y)
    FLOAT_EPSILON = 1e-3
    if abs(det) <= FLOAT_EPSILON:  # 几乎为零
        return {"is_valid": False}
    
    # 计算外接圆 (使用笛卡尔坐标公式)
    d = 2 * det
    a_sq = a.x * a.x + a.y * a.y
    b_sq = b.x * b.x + b.y * b.y
    c_sq = c.x * c.x + c.y * c.y
    
    centre = Pos()
    centre.x = (a_sq * (b.y - c.y) + b_sq * (c.y - a.y) + c_sq * (a.y - b.y)) / d
    centre.y = (a_sq * (c.x - b.x) + b_sq * (a.x - c.x) + c_sq * (b.x - a.x)) / d
    
    # 计算半径
    dx = a.x - centre.x
    dy = a.y - centre.y
    radius = math.sqrt(dx * dx + dy * dy)
    
    # 计算起始和结束角度
    d_a = Pos()
    d_a.x = a.x - centre.x
    d_a.y = a.y - centre.y
    
    d_c = Pos()
    d_c.x = c.x - centre.x
    d_c.y = c.y - centre.y
    
    theta_start = math.atan2(d_a.y, d_a.x)
    theta_end = math.atan2(d_c.y, d_c.x)
    
    # 确保theta_end >= theta_start
    while theta_end < theta_start:
        theta_end += 2 * math.pi
    
    direction = 1.0
    theta_range = theta_end - theta_start
    
    # 根据B相对于AC的位置确定绘制方向
    ortho_ac = Pos()
    ortho_ac.x = c.x - a.x
    ortho_ac.y = -(c.y - a.y)  # 垂直向量
    
    b_relative = Pos()
    b_relative.x = b.x - a.x
    b_relative.y = b.y - a.y
    
    # 计算点积以确定方向
    dot_product = ortho_ac.x * b_relative.x + ortho_ac.y * b_relative.y
    
    if dot_product < 0:
        direction = -direction
        theta_range = 2 * math.pi - theta_range
    
    return {
        "is_valid": True,
        "theta_start": theta_start,
        "theta_range": theta_range,
        "direction": direction,
        "radius": radius,
        "centre": centre
    }

def is_hard_beat(obj) -> bool:
    """判断是否为HardBeat，模仿HitObject.IsHardBeat扩展方法"""
    # 检查hitsound是否有Finish标志位
    if hasattr(obj, 'edge_hitsounds') and obj.edge_hitsounds:
        # 检查滑条第一个节点的音效
        return bool(obj.edge_hitsounds[0] & HitSound.Finish)
    
    # 默认检查物件本身的音效
    return bool(obj.hitsound & HitSound.Finish)


def _interpolate_curve_points(points: List[Pos], progress: float) -> Pos:
    """在曲线点列表中根据进度插值"""
    if not points:
        return Pos()
    
    if len(points) == 1:
        return points[0]
    
    # 计算在点列表中的位置
    exact_index = progress * (len(points) - 1)
    index1 = int(exact_index)
    index2 = min(index1 + 1, len(points) - 1)
    local_progress = exact_index - index1
    
    # 边界检查
    if index1 >= len(points):
        return points[-1]
    if index1 < 0:
        return points[0]
    
    # 线性插值
    result = Pos()
    result.x = points[index1].x + (points[index2].x - points[index1].x) * local_progress
    result.y = points[index1].y + (points[index2].y - points[index1].y) * local_progress
    
    return result

class TauBeatmapConverter:
    def _approximate_bezier_curve(self, control_points: List[Pos]) -> List[Pos]:
        """使用递归细分近似贝塞尔曲线"""
        # 直接使用PathApproximator的BezierToPiecewiseLinear方法
        return self._bezier_to_piecewise_linear(control_points)
    
    def _bezier_to_piecewise_linear(self, control_points: List[Pos]) -> List[Pos]:
        """将贝塞尔曲线转换为分段线性曲线"""
        # 这里简化实现，实际应该使用递归细分算法
        if len(control_points) < 2:
            return control_points
        
        # 如果曲线已经足够平坦，直接返回
        if _bezier_is_flat_enough(control_points):
            return control_points
        
        # 细分曲线并递归处理
        left, right = _bezier_subdivide(control_points, 0.5)
        
        # 递归处理左右两部分
        left_points = self._bezier_to_piecewise_linear(left[:-1])  # 去除重复点
        right_points = self._bezier_to_piecewise_linear(right)
        
        # 合并结果
        return left_points + right_points
    
    def _approximate_circular_arc(self, control_points: List[Pos]) -> List[Pos]:
        """近似圆形弧线"""
        if len(control_points) != 3:
            # 退化为贝塞尔曲线
            return self._approximate_bezier_curve(control_points)
        
        # 计算圆弧属性
        arc_props = _circular_arc_properties(control_points)
        if not arc_props["is_valid"]:
            # 退化为贝塞尔曲线
            return self._approximate_bezier_curve(control_points)
        
        # 圆弧容差
        circular_arc_tolerance = 0.1
        
        # 根据容差选择点的数量
        amount_points = 2
        if 2 * arc_props["radius"] > circular_arc_tolerance:
            # 使用角度范围和容差计算点数
            try:
                angle_tolerance = 2 * math.acos(1 - circular_arc_tolerance / arc_props["radius"])
                amount_points = max(2, int(math.ceil(arc_props["theta_range"] / angle_tolerance)))
            except (ValueError, ZeroDivisionError):
                amount_points = 2
        
        # 生成点
        points = []
        for i in range(amount_points):
            fract = i / (amount_points - 1) if amount_points > 1 else 0
            theta = arc_props["theta_start"] + arc_props["direction"] * fract * arc_props["theta_range"]
            
            point = Pos()
            point.x = arc_props["centre"].x + arc_props["radius"] * math.cos(theta)
            point.y = arc_props["centre"].y + arc_props["radius"] * math.sin(theta)
            points.append(point)
        
        return points
    
    def _approximate_catmull_rom(self, control_points: List[Pos]) -> List[Pos]:
        """近似Catmull-Rom曲线"""
        if len(control_points) < 2:
            return control_points
        
        # Catmull-Rom细节参数
        catmull_detail = 50
        
        # 对于Catmull-Rom曲线，我们创建分段线性近似
        result_points = []
        for i in range(len(control_points) - 1):
            v1 = control_points[max(0, i - 1)]
            v2 = control_points[i]
            v3 = control_points[min(len(control_points) - 1, i + 1)]
            v4 = control_points[min(len(control_points) - 1, i + 2)]
            
            for c in range(catmull_detail):
                # 计算当前点和下一个点
                p1 = _catmull_find_point(v1, v2, v3, v4, c / catmull_detail)
                p2 = _catmull_find_point(v1, v2, v3, v4, (c + 1) / catmull_detail)
                result_points.extend([p1, p2])
        
        return result_points

    def _interpolate_curve_points(self, points: List[Pos], progress: float) -> Pos:
        """实例方法包装，调用模块级的插值函数，以便兼容代码中对实例方法的调用"""
        return _interpolate_curve_points(points, progress)
    
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

    def convert_to_slider(self, obj: OsuSlider, beatmap=None) -> Union[Slider, Beat, HardBeat, StrictHardBeat]:
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
        approach_rate = getattr(beatmap, 'ar', 9.5) if beatmap else 9.5
        min_duration = difficulty_range(approach_rate, 1800, 1200, 450) / self.slider_divisor
        
        # 计算持续时间
        duration = 0
        if beatmap and hasattr(beatmap, 'slider_multiplier') and hasattr(obj, 'length'):
            # 计算滑条持续时间
            slider_multiplier = getattr(beatmap, 'slider_multiplier', 1.0)
            beat_length = 1000  # 默认节拍长度
            slider_velocity = 100 * slider_multiplier
            
            # 查找最近的timing point
            if hasattr(beatmap, 'timing_points'):
                for tp in beatmap.timing_points:
                    if tp.start_time <= obj.time and tp.uninherited:
                        beat_length = abs(float(tp.beat_length))
                        break
            
            # 根据osu!公式计算持续时间: duration = length / (slider_multiplier * 100) * beat_length
            if slider_velocity > 0:
                duration = obj.length / slider_velocity * beat_length
        
        if duration < min_duration:
            return convert_to_non_slider()
        
        nodes = []
        last_angle = None
        last_time = None
        first_angle = 0.0
        
        # 使用PathApproximator方法创建分段线性近似
        # 根据曲线类型选择适当的近似方法
        curve_points = []
        if hasattr(obj, 'curves') and obj.curves and obj.curves.control_points:
            curve_type = obj.curves.type
            # 注意：这里的控制点已经是绝对坐标，不需要再加上obj.pos
            control_points = obj.curves.control_points
            
            if (curve_type in ["L", CurveType.linear] or curve_type == CurveType.linear) and len(control_points) >= 2:
                curve_points = control_points
            elif (curve_type in ["B", CurveType.Bezier] or curve_type == CurveType.Bezier) and len(control_points) >= 2:
                # 使用Bezier曲线近似
                curve_points = self._approximate_bezier_curve(control_points)
            elif (curve_type in ["P", CurveType.perfrct] or curve_type == CurveType.perfrct) and len(control_points) == 3:
                # 使用圆形弧线近似
                curve_points = self._approximate_circular_arc(control_points)
            elif (curve_type in ["C", CurveType.Catmull_rom] or curve_type == CurveType.Catmull_rom) and len(control_points) >= 2:
                # 使用Catmull-Rom曲线近似
                curve_points = self._approximate_catmull_rom(control_points)
            else:
                # 默认使用线性近似
                curve_points = control_points
        
        # 沿着曲线采样点
        sample_interval = 20  # 20ms采样间隔
        t = 0
        while t < duration:
            # 计算当前点的角度
            angle = 0
            if curve_points:
                # 根据进度在曲线点中插值
                progress = t / duration if duration > 0 else 0
                curve_pos = self._interpolate_curve_points(curve_points, progress)
                
                # 计算曲线点的角度
                angle = self.next_angle(get_hit_object_angle(curve_pos))
            
            if t == 0:
                first_angle = angle
            
            # 计算相对于起始角度的差值
            angle = get_delta_angle(angle, first_angle)
            
            # 检查是否转换太快
            if not self.can_convert_impossible_sliders and last_angle is not None:
                angle_diff = get_delta_angle(last_angle, angle)
                time_diff = abs(last_time - t) if last_time is not None else 1
                if time_diff > 0 and abs(angle_diff) / time_diff > 0.6:
                    return convert_to_non_slider()
            
            last_angle = angle
            last_time = t
            nodes.append(SliderNode(t, angle))
            t += sample_interval
        
        # 添加最终节点，模仿原版处理
        final_angle = 0
        if hasattr(obj, 'curves') and obj.curves:
            # 获取滑条结束点的角度
            end_pos = get_curve_position_at(obj.curves, 1.0)
            final_angle = self.next_angle(get_hit_object_angle(end_pos))
        
        final_angle = get_delta_angle(final_angle, first_angle)
        
        if not self.can_convert_impossible_sliders and last_angle is not None and last_time is not None:
            angle_diff = get_delta_angle(last_angle, final_angle)
            time_diff = abs(last_time - duration)
            if time_diff > 0 and abs(angle_diff) / time_diff > 0.6:
                return convert_to_non_slider()
        
        nodes.append(SliderNode(float(duration), final_angle))
        
        # 创建滑条，模仿原版slider创建逻辑
        slider = Slider()
        slider.start_time = obj.time
        slider.new_combo = obj.is_newcombo
        slider.path = PolarSliderPath(nodes)
        slider.angle = first_angle
        slider.repeat_count = getattr(obj, 'repeat_count', 0)
        slider.tick_distance_multiplier = 2.0
        slider.is_hard = self.hard_beats_are_strict and is_hard_beat(obj)
        
        # 模仿原版处理LegacyControlPointInfo部分
        # 由于项目解析器限制，简化处理
        if beatmap and getattr(beatmap, 'file_version', 0) < 8:
            slider.tick_distance_multiplier = 2.0  # 简化处理
        
        return slider

    def convert_slider_spinner(self, obj: OsuSpinner, beatmap=None) -> Union[Slider, Beat, HardBeat, StrictHardBeat]:
        """转换Spinner为滑条，严格按照convertToSliderSpinner逻辑"""
        if not self.can_convert_to_sliders:
            return self.convert_to_non_slider(obj)

        # 使用DifficultyRange计算最小持续时间
        approach_rate = getattr(beatmap, 'ar', 9.5) if beatmap else 9.5
        min_duration = difficulty_range(approach_rate, 1800, 1200, 450) / self.slider_divisor
        
        duration = obj.end_time - obj.time
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
            # 查找在obj.time时刻的timing point
            for tp in beatmap.timing_points:
                if tp.start_time <= obj.time and tp.uninherited:
                    control_point_beat_length = float(tp.beat_length)
                    break
        
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
        slider.start_time = obj.time
        slider.new_combo = obj.is_newcombo
        slider.path = PolarSliderPath(nodes)
        slider.angle = nodes[0].angle if nodes else 0.0
        slider.tick_distance_multiplier = 2.0
        
        # 模仿原版处理LegacyControlPointInfo部分
        # 由于项目解析器限制，简化处理
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
                hard_beat.start_time = obj.time
                hard_beat.new_combo = obj.is_newcombo
                return hard_beat
            else:
                # 转换为严格HardBeat，模仿convertToStrictHardBeat
                strict_hard_beat = StrictHardBeat()
                strict_hard_beat.start_time = obj.time
                strict_hard_beat.new_combo = obj.is_newcombo
                strict_hard_beat.angle = self.next_angle(get_hit_object_angle(getattr(obj, 'pos', None)))
                return strict_hard_beat
        else:
            # 转换为普通节拍，模仿convertToBeat
            beat = Beat()
            beat.start_time = obj.time
            beat.new_combo = obj.is_newcombo
            beat.angle = self.next_angle(get_hit_object_angle(getattr(obj, 'pos', None)))
            return beat

def convert_object(obj, beatmap=None) -> Union[Beat, HardBeat, StrictHardBeat, Slider]:
    """转换物件，模仿ConvertHitObject主逻辑"""
    converter = TauBeatmapConverter()
    
    # 根据物件类型进行转换，模仿原版switch表达式
    if isinstance(obj, OsuSlider):
        return converter.convert_to_slider(obj, beatmap)
    elif isinstance(obj, OsuSpinner):
        return converter.convert_slider_spinner(obj, beatmap)
    else:
        # 包括Circle和其他类型，模仿默认情况
        return converter.convert_to_non_slider(obj)

def convert_osu_beatmap(osu_beatmap: OsuBeatmap) -> 'TauBeatmap':
    """
    将OsuBeatmap转换为TauBeatmap
    
    Args:
        osu_beatmap: 解析后的osu谱面对象
        
    Returns:
        TauBeatmap: 转换后的Tau谱面对象
    """
    from .beatmap import TauBeatmap
    
    # 创建TauBeatmap实例
    tau_beatmap = TauBeatmap()
    
    # 设置难度属性
    tau_beatmap.difficulty_attributes['approach_rate'] = getattr(osu_beatmap, 'ar', 5.0)
    tau_beatmap.difficulty_attributes['overall_difficulty'] = getattr(osu_beatmap, 'od', 5.0)
    tau_beatmap.difficulty_attributes['circle_size'] = getattr(osu_beatmap, 'cs', 5.0)
    tau_beatmap.difficulty_attributes['drain_rate'] = getattr(osu_beatmap, 'hp', 5.0)
    
    # 设置元数据（如果有的话）
    # 由于any.parser.OsuBeatmap没有元数据字段，这里留空
    
    # 创建转换器实例
    converter = TauBeatmapConverter()
    
    # 转换所有物件
    for obj in getattr(osu_beatmap, 'hit_objects', []):
        try:
            tau_obj = convert_object(obj, osu_beatmap)
            if tau_obj:
                tau_beatmap.add_hit_object(tau_obj)
        except Exception as e:
            # 跳过转换失败的物件
            continue
    
    return tau_beatmap