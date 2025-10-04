from __future__ import annotations
from typing import Any, List, Optional, Sequence, Tuple
from math import atan2, hypot, fabs
import random

from .objects import (
    SentakkiObjectBase, Tap, Hold, Slide, SlideSegment, TouchHold,
    SlideBodyInfo, SlidePathPart,
    FLAG_BREAK, FLAG_EX, FLAG_TWIN, FLAG_FAN
)
from .slide_paths import PROTOTYPES, SlidePathPrototype
from .slide_geometry import part_angle, angle_to_lane_delta
from .flags import ConversionFlags, StreamDirection
from ..difficulty.beatmap_base import SentakkiBeatmap

try:  # External parser data structures
    from osu_std.hitobjects import SliderInfo, SpinnerInfo
except ImportError:  # type: ignore
    SliderInfo = SpinnerInfo = object  # type: ignore

LANE_COUNT = 8
CENTER_X = 256
CENTER_Y = 192
RING_RADIUS = 200  # synthetic radius for projecting slide end geometry

def _normalize_lane(l: int) -> int:
    return l % LANE_COUNT

def _angle_delta(a: float, b: float) -> float:
    """Return signed smallest angular difference (radians)."""
    d = (b - a) % (2*3.141592653589793)
    if d > 3.141592653589793:
        d -= 2*3.141592653589793
    return d

def _get_rotation_for_lane(lane: int) -> float:
    return (2*3.141592653589793 / LANE_COUNT) * lane

def _closest_lane_for(angle: float) -> int:
    angle = angle % (2*3.141592653589793)
    best_lane = 0
    best = 1e9
    for i in range(LANE_COUNT):
        delta = abs(_angle_delta(_get_rotation_for_lane(i), angle))
        if delta < best:
            best = delta
            best_lane = i
    return best_lane

class TwinPattern:
    """Structured twin lane offset pattern iterator (closer to official feel).

    Patterns are sequences of relative offsets. We cycle within one pattern;
    when reset() is called a new pattern (rotated) is chosen.
    """
    PATTERNS: List[List[int]] = [
        [1, -1, 2, -2],
        [2, 1, -1, -2],
        [1, 2, 3, -1],
        [2, -1, -2, 1],
    ]

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.pattern: List[int] = []
        self.index = 0
        self.reset()

    def reset(self):
        base = self.rng.choice(self.PATTERNS)
        # Random rotate pattern to vary starting offset
        rot = self.rng.randint(0, len(base) - 1)
        self.pattern = base[rot:] + base[:rot]
        self.index = 0

    def next_offset(self) -> int:
        if not self.pattern:
            self.reset()
        off = self.pattern[self.index]
        self.index = (self.index + 1) % len(self.pattern)
        return off

    def get_next_lane(self, current_lane: int) -> int:
        return (current_lane + self.next_offset()) % LANE_COUNT

class SentakkiConverter:
    def __init__(self, osu_beatmap: Any, flags: ConversionFlags = ConversionFlags.NONE, seed: Optional[int] = None):
        self.osu = osu_beatmap
        self.flags = flags
        # Difficulty (for circle radius + seed)
        diff = getattr(osu_beatmap, 'difficulty', {})
        cs = diff.get('CircleSize') or getattr(osu_beatmap, 'cs', 5) or 5
        self.circle_radius: float = 54.4 - 4.48 * float(cs)

        # Official style seed approximation
        drain = diff.get('HPDrainRate') or getattr(osu_beatmap, 'hp', 5) or 5
        od = diff.get('OverallDifficulty') or getattr(osu_beatmap, 'od', 5) or 5
        ar = diff.get('ApproachRate') or getattr(osu_beatmap, 'ar', 5) or 5
        if seed is None:
            seed_val = int(round(float(drain) + float(cs))) * 20 + int(float(od) * 41.2) + int(round(float(ar)))
        else:
            seed_val = seed
        self._rng = random.Random(seed_val)

        # State
        self._current_lane: int = 0
        self._active_stream: StreamDirection = StreamDirection.NONE
        self._last_object_time: Optional[int] = None
        self._last_twin_time: float = -1.0
        self._new_combo_since_last_twin: bool = True

        # Pattern
        self._twin_pattern = TwinPattern(self._rng)

    # ---------------- Public API ----------------
    def convert(self) -> SentakkiBeatmap:
        objects = self._convert_objects()
        star = self._estimate_star(objects)
        if hasattr(self.osu, 'compute_max_combo'):
            try:
                max_combo = int(self.osu.compute_max_combo())
            except Exception:
                max_combo = len(objects)
        else:
            max_combo = len(objects)
        return SentakkiBeatmap(star_rating=star, max_combo=max_combo, approach_rate=getattr(self.osu, 'ar', 5.0), objects=objects)

    # ---------------- Core conversion ----------------
    def _convert_objects(self) -> List[SentakkiObjectBase]:
        hit_objects: List[Any] = list(getattr(self.osu, 'hit_objects', []))
        timing_points = sorted(getattr(self.osu, 'timing_points', []), key=lambda t: t.time)
        if self.flags & ConversionFlags.OLD_CONVERTER:
            return self._convert_old(hit_objects, timing_points)
        if not hit_objects:
            return []

        # Initialize current lane based on first object's angle
        first = hit_objects[0]
        fx, fy = getattr(first, 'x', CENTER_X), getattr(first, 'y', CENTER_Y)
        fang = atan2(fy - CENTER_Y, fx - CENTER_X)
        if fang < 0:
            fang += 2*3.141592653589793
        self._current_lane = _closest_lane_for(fang)

        result: List[SentakkiObjectBase] = []
        count = len(hit_objects)
        for idx, ho in enumerate(hit_objects):
            extras = getattr(ho, 'extras', {}) or {}
            hs = extras.get('hit_sounds', {})
            start_time = getattr(ho, 'time', 0)

            if getattr(ho, 'is_new_combo', False):
                self._new_combo_since_last_twin = True

            # Decide object type
            created: List[SentakkiObjectBase] = []
            if 'spinner' in extras:
                # Align closer to official: TouchHold, lane not advancing logic handled in lane updater
                spinner: SpinnerInfo = extras['spinner']  # type: ignore
                duration = max(200, int(spinner.end_time - start_time))
                flags = FLAG_BREAK if hs.get('finish') else 0
                created.append(TouchHold(time=start_time, lane=self._current_lane, duration=duration, flags=flags, x=CENTER_X, y=CENTER_Y))
            elif 'slider' in extras or hasattr(ho, 'slider'):
                slider: SliderInfo = extras.get('slider') or getattr(ho, 'slider')  # type: ignore
                duration = self._calculate_slider_duration(start_time, slider, timing_points)
                flags = 0
                if hs.get('finish'): flags |= FLAG_BREAK
                if hs.get('whistle'): flags |= FLAG_EX
                # curvature-aware lazy slider heuristic
                event_count = self._slider_event_count(slider, start_time, timing_points)
                pts = getattr(slider,'points', []) or []
                straight_ratio = 1.0
                if len(pts) >= 2:
                    chord_dx = pts[-1][0]-pts[0][0]; chord_dy = pts[-1][1]-pts[0][1]
                    chord_len = (chord_dx*chord_dx + chord_dy*chord_dy)**0.5 or 1.0
                    poly_len = 0.0
                    for (ax,ay),(bx,by) in zip(pts, pts[1:]):
                        dx=bx-ax; dy=by-ay; poly_len += (dx*dx+dy*dy)**0.5
                    straight_ratio = chord_len / max(poly_len,1.0)
                curvature_low = straight_ratio > 0.96
                is_lazy = (
                    slider.pixel_length < 90
                    or len(pts) <= 2
                    or event_count <= 3
                    or (curvature_low and slider.pixel_length < 240 and event_count < 6)
                )
                composite_allowed = not (self.flags & ConversionFlags.DISABLE_COMPOSITE_SLIDES)
                if (not is_lazy) and slider.pixel_length >= 120 and (slider.repeat <= 5) and composite_allowed:
                    slide_obj = self._convert_slider_to_composite(start_time, duration, slider, flags)
                    created.append(slide_obj)
                    # allClaps detection using node_hit_sounds
                    node_sounds = getattr(slider, 'node_hit_sounds', [])
                    all_claps = False
                    if node_sounds:
                        all_claps = all(ns.get('clap') for ns in node_sounds)

                    # Twin slide: only when all nodes clap + option enabled + has clap anywhere
                    if (self.flags & ConversionFlags.TWIN_SLIDES) and all_claps and any(ns.get('clap') for ns in node_sounds):
                        twin_lane = self._twin_next_lane_candidate(start_time)
                        if twin_lane is not None:
                            twin_copy = self._duplicate_slide_for_lane(slide_obj, twin_lane, extra_flags=FLAG_TWIN)
                            created.append(twin_copy)
                    else:
                        # Per-node twin taps for nodes with clap (excluding head & tail conditions after fan cut)
                        if node_sounds and (self.flags & ConversionFlags.TWIN_NOTES):
                            node_times = self._generate_slider_node_times(start_time, duration, slider.repeat + 1)
                            fan_cut_ms = None
                            if slide_obj.body and slide_obj.body.parts:
                                fan_part = next((p for p in slide_obj.body.parts if p.shape == 'fan' and p.fan_start_progress < 1.0), None)
                                if fan_part:
                                    fan_cut_ms = int(start_time + slide_obj.body.duration * fan_part.fan_start_progress)
                            # Iterate interior nodes (exclude first, allow tail only if before fan start)
                            for idx_node in range(1, len(node_times)):
                                if idx_node == len(node_times)-1:
                                    # tail node -> skip twin tap (官方行为用 slide 尾特性表达, 保守不加)
                                    continue
                                if idx_node >= len(node_sounds):
                                    break
                                if not node_sounds[idx_node].get('clap'):
                                    continue
                                nt = node_times[idx_node]
                                if fan_cut_ms is not None and nt >= fan_cut_ms:
                                    break
                                twin_lane = self._twin_next_lane_candidate(nt)
                                if twin_lane is not None:
                                    created.append(Tap(time=int(nt), lane=twin_lane, flags=FLAG_TWIN))
                else:
                    created.append(Hold(time=start_time, lane=self._current_lane, duration=duration, flags=flags))
            else:
                # Circle -> Tap
                flags = 0
                if hs.get('finish'): flags |= FLAG_BREAK
                if hs.get('whistle'): flags |= FLAG_EX
                tap = Tap(time=start_time, lane=self._current_lane, flags=flags)
                created.append(tap)
                if (self.flags & ConversionFlags.TWIN_NOTES) and hs.get('clap'):
                    twin_lane = self._twin_next_lane_candidate(start_time)
                    if twin_lane is not None:
                        created.append(Tap(time=start_time, lane=twin_lane, flags=flags | FLAG_TWIN))

            # Commit & update twin bookkeeping
            for obj in created:
                result.append(obj)
                if isinstance(obj, Tap) and (obj.flags & FLAG_TWIN):
                    self._last_twin_time = obj.time
                    self._new_combo_since_last_twin = False

            # Update lane for next object (look ahead)
            next_original = hit_objects[idx + 1] if idx + 1 < count else None
            second_next_original = hit_objects[idx + 2] if idx + 2 < count else None
            prev_original = hit_objects[idx - 1] if idx - 1 >= 0 else None
            if next_original is not None:
                self._update_current_lane(ho, prev_original, next_original, second_next_original)

            # Track last object time using end_time if available
            end_t = getattr(ho, 'end_time', None)
            self._last_object_time = end_t if end_t is not None else start_time

        result.sort(key=lambda o: (o.time, o.lane, o.kind))
        return result

    # ---------- Composite slide construction (Phase 2 partial) ----------
    def _convert_slider_to_composite(self, start_time: int, duration: int, slider: Any, base_flags: int) -> Slide:
        beat_len = self._beat_length_at_time(start_time) or 500
        shoot_beats = 1.0
        while shoot_beats * beat_len >= duration - 50:
            shoot_beats /= 2
            if shoot_beats < 0.25:
                return Slide(time=start_time, lane=self._current_lane, segments=[SlideSegment(end_lane=self._current_lane, duration=duration)], flags=base_flags)
        shoot_delay = int(shoot_beats * beat_len)

        allow_fan = bool(self.flags & ConversionFlags.FAN_SLIDES)
        remaining = duration - shoot_delay
        parts: List[SlidePathPart] = []

        # Build candidate list from PROTOTYPES
        # Copy so we can mark single-use parts consumed.
        candidates: List[SlidePathPrototype] = []
        for proto in PROTOTYPES:
            if proto.is_fan and not allow_fan:
                continue
            if proto.is_fan and getattr(slider, 'pixel_length', 0) < 220:
                continue
            candidates.append(proto)

        used_fan = False
        safety = 0
        accumulated_before_fan = 0
        accumulated_angle = 0.0
        while remaining > 150 and safety < 64 and candidates:
            safety += 1
            viable = [p for p in candidates if p.min_duration < remaining]
            if not viable:
                break
            # Weighted choice
            total_w = sum(p.weight for p in viable)
            r = self._rng.uniform(0, total_w)
            upto = 0
            chosen: SlidePathPrototype = viable[0]
            for p in viable:
                if upto + p.weight >= r:
                    chosen = p
                    break
                upto += p.weight
            # Allocation: min(min_duration*1.1, remaining - tail_guard)
            tail_guard = 120
            alloc = int(min(max(chosen.min_duration, chosen.min_duration * 1.1), max(chosen.min_duration, remaining - tail_guard)))
            alloc = max(chosen.min_duration, alloc)

            # Fan can't be first tiny leftover fragment; ensure at least 40% body left if selecting fan early
            if chosen.is_fan:
                if used_fan:
                    # Already have fan -> skip
                    candidates = [c for c in candidates if c != chosen]
                    continue
                if accumulated_before_fan < duration * 0.25 and remaining < duration * 0.55:
                    # delay fan selection if it would be too abrupt
                    candidates = [c for c in candidates if c != chosen] + [chosen]  # push to end
                    continue
                used_fan = True

            part = SlidePathPart(
                shape=chosen.name,
                duration=alloc,
                mirrored=bool(self._rng.randint(0, 1)),
                min_duration=chosen.min_duration,
                end_offset=0,
                fan_start_progress=1.0,  # will recompute if fan
            )
            parts.append(part)
            remaining -= alloc
            accumulated_angle += part_angle(part.shape, part.mirrored)
            if chosen.is_fan:
                # compute fan_start_progress dynamically: accumulated_before_fan / full duration
                part.fan_start_progress = max(0.0, min(1.0, accumulated_before_fan / duration))
                accumulated_before_fan += alloc  # (for completeness)
                break  # currently only one fan part allowed
            else:
                accumulated_before_fan += alloc
            if not chosen.allow_multiple:
                candidates = [c for c in candidates if c != chosen]

        # --- Geometry & complexity aggregation ---
        lane_delta_total = angle_to_lane_delta(accumulated_angle)
        complexity_acc = 0.0
        for part in parts:
            delta = self._lane_delta_for_part(part)  # keep legacy per-part delta for complexity weighting
            # base 1 per part + shape specific weight
            shape_weight = 1.0
            if 'circle' in part.shape:
                shape_weight = 1.25
            elif 'zigzag' in part.shape:
                shape_weight = 1.4
            elif 'fan' in part.shape:
                shape_weight = 1.8
            complexity_acc += shape_weight * (1 + 0.15 * max(0, abs(delta)))
        end_lane = _normalize_lane(self._current_lane + lane_delta_total)
        # Normalize complexity by part count
        if parts:
            complexity_acc /= len(parts)
        if any('fan' in p.shape for p in parts):
            complexity_acc *= 1.15
        body = SlideBodyInfo(
            parts=parts,
            duration=duration,
            shoot_delay=shoot_delay,
            fan_start_progress=min((p.fan_start_progress for p in parts if 'fan' in p.shape), default=1.0),
            end_lane=end_lane,
            complexity=complexity_acc
        )
        segs = [SlideSegment(end_lane=self._current_lane, duration=duration)]
        flags = base_flags
        if any('fan' in p.shape for p in parts):
            flags |= FLAG_FAN
        slide_obj = Slide(time=start_time, lane=self._current_lane, segments=segs, body=body, flags=flags)
        # Attach end lane hint back to original parser slider for later geometric end position queries
        try:
            setattr(slider, '__sentakki_end_lane', body.end_lane)
        except Exception:
            pass
        return slide_obj

    def _duplicate_slide_for_lane(self, slide: Slide, new_lane: int, extra_flags: int = 0) -> Slide:
        # Shallow copy of body & parts
        body_copy = None
        if slide.body:
            body_copy = SlideBodyInfo(parts=list(slide.body.parts), duration=slide.body.duration, shoot_delay=slide.body.shoot_delay, fan_start_progress=slide.body.fan_start_progress)
        segs = [SlideSegment(end_lane=new_lane, duration=s.duration, fan=s.fan) for s in slide.segments]
        return Slide(time=slide.time, lane=new_lane, segments=segs, body=body_copy, flags=slide.flags | extra_flags)

    def _convert_old(self, hit_objects: List[Any], timing_points: List[Any]) -> List[SentakkiObjectBase]:
        out: List[SentakkiObjectBase] = []
        for ho in hit_objects:
            lane = self._rng.randint(0, LANE_COUNT-1)
            extras = getattr(ho,'extras',{})
            hs = extras.get('hit_sounds',{})
            if 'spinner' in extras:
                spinner: SpinnerInfo = extras['spinner']  # type: ignore
                dur = max(150, int(spinner.end_time - ho.time))
                out.append(TouchHold(time=ho.time, lane=lane, duration=dur, flags=FLAG_BREAK if hs.get('finish') else 0, x=CENTER_X, y=CENTER_Y)); continue
            if 'slider' in extras:
                slider: SliderInfo = extras['slider']  # type: ignore
                dur = self._calculate_slider_duration(ho.time, slider, timing_points)
                if self._rng.random() < 0.4:
                    out.append(Hold(time=ho.time, lane=lane, duration=dur))
                else:
                    out.append(Slide(time=ho.time,lane=lane,segments=[SlideSegment(end_lane=lane,duration=dur)]))
                if (self.flags & ConversionFlags.TWIN_SLIDES) and hs.get('clap') and self._rng.random()<0.5:
                    twin_lane=(lane+4)%LANE_COUNT
                    out.append(Slide(time=ho.time,lane=twin_lane,segments=[SlideSegment(end_lane=twin_lane,duration=dur)], flags=FLAG_TWIN))
                continue
            base_flags = 0
            if hs.get('finish'): base_flags |= FLAG_BREAK
            out.append(Tap(time=ho.time,lane=lane,flags=base_flags))
            if (self.flags & ConversionFlags.TWIN_NOTES) and hs.get('clap') and self._rng.random()<0.5:
                out.append(Tap(time=ho.time,lane=(lane+4)%LANE_COUNT,flags=base_flags|FLAG_TWIN))
        out.sort(key=lambda o:(o.time,o.lane,o.kind))
        return out

    # -------- Lane update logic (Phase 1 alignment) --------
    def _update_current_lane(self, current: Any, previous: Optional[Any], nxt: Any, second_next: Optional[Any]):
        # If current was a composite slide we can start from its end lane for continuity
        cur_end_lane = getattr(getattr(current, 'body', None), 'end_lane', None)
        if cur_end_lane is not None:
            self._current_lane = int(cur_end_lane) % LANE_COUNT
        # If next note is not chronologically close: reset by angle
        if not self._is_chronologically_close_obj(current, nxt):
            nx, ny = getattr(nxt, 'x', CENTER_X), getattr(nxt, 'y', CENTER_Y)
            ang = atan2(ny - CENTER_Y, nx - CENTER_X)
            if ang < 0: ang += 2*3.141592653589793
            self._current_lane = _closest_lane_for(ang)
            self._active_stream = StreamDirection.NONE
            return

        # Jump check
        if self._is_jump(current, nxt):
            offset = self._jump_lane_offset(current, previous, nxt)
            self._current_lane = _normalize_lane(self._current_lane + offset)
            self._active_stream = StreamDirection.NONE
            return

        # Determine stream direction
        direction = self._get_stream_direction(current, previous, nxt, second_next)
        # If ambiguous (NONE) but we have second_next giving clearer direction, use that
        if direction == StreamDirection.NONE and second_next and self._is_chronologically_close_obj(nxt, second_next):
            alt_dir = self._get_stream_direction(nxt, current, second_next, None)
            if alt_dir != StreamDirection.NONE:
                direction = alt_dir
        self._active_stream = direction
        stream_offset = int(direction.value)

        # Basic overlap heuristic (approx) using start positions
        overlapping_end = self._is_overlapping(self._get_end_position(current), self._get_position(nxt))

        # For slides we would use endLane; at this phase slides keep same lane so allow normal flow
        if stream_offset:
            self._current_lane = _normalize_lane(self._current_lane + stream_offset)
        if not overlapping_end:
            self._current_lane = _normalize_lane(self._current_lane + (stream_offset if stream_offset != 0 else 1))

    # Helper geometry
    def _get_position(self, obj: Any) -> Tuple[float, float]:
        return getattr(obj, 'x', CENTER_X), getattr(obj, 'y', CENTER_Y)

    def _get_end_position(self, obj: Any) -> Tuple[float, float]:
        extras = getattr(obj, 'extras', None)
        if extras and 'slider' in extras:
            s = extras['slider']
            end_x = getattr(s, 'end_x', None)
            end_y = getattr(s, 'end_y', None)
            if end_x is not None and end_y is not None:
                # If we later converted this slider into composite, we project to geometric lane end
                comp_end_lane = getattr(s, '__sentakki_end_lane', None)
                if comp_end_lane is not None:
                    ang = _get_rotation_for_lane(comp_end_lane)
                    return CENTER_X + RING_RADIUS * 0.85 * float(__import__('math').cos(ang)), CENTER_Y + RING_RADIUS * 0.85 * float(__import__('math').sin(ang))
                return float(end_x), float(end_y)
        return self._get_position(obj)

    def _is_overlapping(self, a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        ax, ay = a; bx, by = b
        return (bx - ax)**2 + (by - ay)**2 <= (self.circle_radius * 2)**2

    def _is_jump(self, current: Any, nxt: Any) -> bool:
        cx, cy = self._get_end_position(current)
        nx, ny = self._get_position(nxt)
        return (nx - cx)**2 + (ny - cy)**2 >= 128*128

    def _jump_lane_offset(self, current: Any, previous: Optional[Any], nxt: Any) -> int:
        midpoint = self._midpoint(current, previous, nxt)
        cx, cy = self._get_end_position(current)
        nx, ny = self._get_position(nxt)
        c_angle = atan2(cy - midpoint[1], cx - midpoint[0])
        n_angle = atan2(ny - midpoint[1], nx - midpoint[0])
        return _closest_lane_for(n_angle) - _closest_lane_for(c_angle)

    def _midpoint(self, current: Any, previous: Optional[Any], nxt: Any) -> Tuple[float, float]:
        points = [self._get_end_position(current), self._get_position(nxt)]
        if previous is not None:
            points.append(self._get_end_position(previous))
        # if start != end we could add start again, omitted for now
        sx = sum(p[0] for p in points)
        sy = sum(p[1] for p in points)
        return sx/len(points), sy/len(points)

    def _get_stream_direction(self, current: Any, previous: Optional[Any], nxt: Any, second_next: Optional[Any]) -> StreamDirection:
        midpoint = self._midpoint(current, previous, nxt)
        cx, cy = self._get_end_position(current)
        nx, ny = self._get_position(nxt)
        c_angle = atan2(cy - midpoint[1], cx - midpoint[0])
        n_angle = atan2(ny - midpoint[1], nx - midpoint[0])
        d = _angle_delta(c_angle, n_angle)
        ad = fabs(d)
        # Approximate 5 deg ~ 0.0872665 rad; 180 deg ~ pi
        if ad <= 0.087:
            return self._active_stream
        if abs(ad - 3.141592653589793) <= 0.087:
            return StreamDirection.NONE
        return StreamDirection.CLOCKWISE if d > 0 else StreamDirection.COUNTERCLOCKWISE

    def _is_chronologically_close_obj(self, a: Any, b: Any) -> bool:
        at = getattr(a, 'end_time', getattr(a, 'time', 0))
        bt = getattr(b, 'time', 0)
        return self._is_chronologically_close_time(at, bt)

    def _is_chronologically_close_time(self, a: float, b: float) -> bool:
        beat = self._beat_length_at_time(int(b)) or 500
        return (b - a) <= beat

    def _beat_length_at_time(self, time_ms: int) -> Optional[float]:
        tps = getattr(self.osu,'timing_points',None)
        if not tps: return None
        base_beat = None; last_red = -1; sv_mul = 1.0
        for tp in sorted(tps, key=lambda tp: tp.time):
            if tp.time > time_ms: break
            if tp.uninherited:
                if tp.beat_length > 0:
                    base_beat = tp.beat_length; last_red = tp.time; sv_mul = 1.0
            else:
                if tp.beat_length < 0 and tp.time >= last_red and base_beat is not None:
                    sv_mul = 100.0 / -tp.beat_length
        return base_beat

    def _calculate_slider_duration(self, start_time: int, slider: Any, timing_points: List[Any]) -> int:
        diff = getattr(self.osu,'difficulty',{})
        slider_multiplier = float(diff.get('SliderMultiplier',1.0)) or 1.0
        base_beat = 500.0; sv = 1.0; last_red=-1
        for tp in timing_points:
            if tp.time > start_time: break
            if tp.uninherited:
                if tp.beat_length > 0:
                    base_beat = tp.beat_length; last_red = tp.time; sv = 1.0
            else:
                if tp.beat_length < 0 and tp.time >= last_red:
                    sv = 100.0 / -tp.beat_length
        scoring_distance = 100.0 * slider_multiplier * sv
        span_count = max(1, slider.repeat + 1)
        beats = slider.pixel_length / scoring_distance
        span_dur = beats * base_beat
        total = span_dur * span_count
        return int(max(150.0,total))

    # -------- Twin helper (new logic) --------
    def _twin_next_lane_candidate(self, target_time: int) -> Optional[int]:
        if not (self.flags & (ConversionFlags.TWIN_NOTES | ConversionFlags.TWIN_SLIDES)):
            return None
        # Pattern reset condition
        if (self._last_twin_time < 0 or not self._is_chronologically_close_time(self._last_twin_time, target_time)) and self._new_combo_since_last_twin:
            self._twin_pattern.reset()
        lane = self._twin_pattern.get_next_lane(self._current_lane)
        if lane == self._current_lane:
            return None
        self._last_twin_time = target_time
        self._new_combo_since_last_twin = False
        return lane

    def _generate_slider_node_times(self, start: int, total_duration: int, span_count: int) -> List[int]:
        if span_count <= 1:
            return [start, start + total_duration]
        span = total_duration / span_count
        return [int(start + span * i) for i in range(span_count + 1)]

    def _estimate_star(self, objects: Sequence[SentakkiObjectBase]) -> float:
        if not objects: return 0.0
        n = len(objects)
        base = (n ** 0.5) * 0.25
        times = sorted(o.time for o in objects)
        if len(times)>1:
            gaps=[b-a for a,b in zip(times,times[1:])]; avg_gap=sum(gaps)/len(gaps); density=min(1.5,1000.0/(avg_gap+1)*0.003)
        else:
            density=0
        lane_changes=sum(1 for a,b in zip(objects,objects[1:]) if a.lane!=b.lane)
        lane_factor=(lane_changes/max(1,n-1))*0.8
        hold_like=sum(1 for o in objects if isinstance(o,(Hold,Slide)))
        hold_ratio=hold_like/n
        ar = getattr(self.osu,'ar',5.0)
        # Slide complexity factor
        slides = [o for o in objects if isinstance(o, Slide) and getattr(o,'body', None)]
        if slides:
            avg_complexity = 0.0
            for o in slides:
                b = getattr(o,'body', None)
                if b is not None:
                    avg_complexity += getattr(b,'complexity', 0.0)
            avg_complexity /= max(1,len(slides))
        else:
            avg_complexity = 0.0
        complexity_factor = min(0.4, 0.12 * avg_complexity)  # cap influence
        star = base * (1 + 0.5*density + 0.3*lane_factor + 0.2*hold_ratio + complexity_factor)
        star *= (1 + (ar-5.0)*0.02)
        return round(star,4)

    # -------- Slider helpers (improved) --------
    def _slider_event_count(self, slider: Any, start_time: int, timing_points: List[Any]) -> int:
        """Approximate number of meaningful events (head + ticks + tail + repeats).
        If the count is very small treat as lazy slider.
        """
        # Simple heuristic using osu! ticks spacing: beatLength / slider_tick_rate
        diff = getattr(self.osu,'difficulty',{})
        tick_rate = float(diff.get('SliderTickRate',1.0)) or 1.0
        base_beat = self._beat_length_at_time(start_time) or 500
        scoring_distance = 100.0 * float(diff.get('SliderMultiplier',1.0))
        span_count = max(1, slider.repeat + 1)
        beats = slider.pixel_length / scoring_distance
        span_duration = beats * base_beat
        tick_spacing = base_beat / tick_rate
        ticks_per_span = max(0, int((span_duration - tick_spacing/8) / tick_spacing))
        events = 1 + span_count  # head + tails for repeats
        events += ticks_per_span * span_count
        return events

    # Lane delta mapping per part shape
    def _lane_delta_for_part(self, part: SlidePathPart) -> int:
        shape = part.shape
        mirrored = part.mirrored
        if shape == 'linear':
            return 0
        if shape == 'circle_cw':
            return 1
        if shape == 'circle_ccw':
            return -1
        if shape == 'zigzag':
            return 1 if not mirrored else -1
        if 'fan' in shape:
            return 2 if not mirrored else -2
        return 0

__all__ = ['SentakkiConverter']