"""
damp11113-library - A Utils library and Easy to use. For more info visit https://github.com/damp11113/damp11113-library/wiki
Copyright (C) 2021-present damp11113 (MIT)

Visit https://github.com/damp11113/damp11113-library

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math
from typing import Dict, List, Tuple, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

class InterpolationType(Enum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    CUBIC_BEZIER = "cubic_bezier"
    CUSTOM = "custom"

@dataclass
class Keyframe:
    """Represents a single keyframe with position, value, and interpolation settings."""
    id: str
    start_pos: float
    start_value: Any
    end_pos: float
    end_value: Any
    curve_function: Optional[Callable[[float], float]] = None
    interpolation_type: InterpolationType = InterpolationType.LINEAR

    def __post_init__(self):
        if self.start_pos > self.end_pos:
            raise ValueError("Start position cannot be greater than end position")

    @property
    def duration(self) -> float:
        return self.end_pos - self.start_pos

    def contains_position(self, position: float) -> bool:
        """Check if a position falls within this keyframe's range."""
        return self.start_pos <= position <= self.end_pos

    def get_normalized_position(self, position: float) -> float:
        """Get normalized position (0-1) within this keyframe."""
        if self.duration == 0:
            return 0.0
        return max(0.0, min(1.0, (position - self.start_pos) / self.duration))

    def interpolate(self, position: float) -> Any:
        """Interpolate value at given position using the assigned curve."""
        if position <= self.start_pos:
            return self.start_value
        if position >= self.end_pos:
            return self.end_value

        t = self.get_normalized_position(position)

        # Apply curve function if set
        if self.curve_function:
            t = self.curve_function(t)
        else:
            # Use built-in interpolation types
            t = self._apply_interpolation(t)

        # Handle different value types
        return self._interpolate_values(self.start_value, self.end_value, t)

    def _apply_interpolation(self, t: float) -> float:
        """Apply built-in interpolation curves."""
        if self.interpolation_type == InterpolationType.LINEAR:
            return t
        elif self.interpolation_type == InterpolationType.EASE_IN:
            return t * t
        elif self.interpolation_type == InterpolationType.EASE_OUT:
            return 1 - (1 - t) ** 2
        elif self.interpolation_type == InterpolationType.EASE_IN_OUT:
            return 3 * t * t - 2 * t * t * t
        return t

    def _interpolate_values(self, start_val: Any, end_val: Any, t: float) -> Any:
        """Interpolate between two values based on their types."""
        # Numeric interpolation
        if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
            return start_val + (end_val - start_val) * t

        # List/tuple interpolation (element-wise)
        if isinstance(start_val, (list, tuple)) and isinstance(end_val, (list, tuple)):
            if len(start_val) != len(end_val):
                raise ValueError("Cannot interpolate sequences of different lengths")
            result = []
            for s, e in zip(start_val, end_val):
                result.append(self._interpolate_values(s, e, t))
            return type(start_val)(result)

        # Dictionary interpolation (key-wise)
        if isinstance(start_val, dict) and isinstance(end_val, dict):
            result = {}
            all_keys = set(start_val.keys()) | set(end_val.keys())
            for key in all_keys:
                s = start_val.get(key, 0)
                e = end_val.get(key, 0)
                result[key] = self._interpolate_values(s, e, t)
            return result

        # For non-numeric types, switch at t=0.5
        return start_val if t < 0.5 else end_val


@dataclass
class StatementObject:
    """Represents a statement that holds static data within a time range."""
    id: str
    start_pos: float
    end_pos: float
    data: Any
    active: bool = True

    def __post_init__(self):
        if self.start_pos > self.end_pos:
            raise ValueError("Start position cannot be greater than end position")

    @property
    def duration(self) -> float:
        return self.end_pos - self.start_pos

    def contains_position(self, position: float) -> bool:
        """Check if a position falls within this statement's active range."""
        if not self.active:
            return False
        return self.start_pos <= position <= self.end_pos

    def get_data_at(self, position: float) -> Any:
        """Get the data if position is within range, otherwise return None."""
        if self.contains_position(position):
            return self.data
        return None

class AnimationTrack:
    """Manages keyframes for a single property or object."""

    def __init__(self, name: str):
        self.name = name
        self.keyframes: List[Keyframe] = []
        self.statements: List[StatementObject] = []
        self._sorted_positions: List[float] = []

    def add_keyframe(self, keyframe: Keyframe):
        """Add a keyframe to the track."""
        # Check for overlapping keyframes
        for existing in self.keyframes:
            if (keyframe.start_pos < existing.end_pos and
                    keyframe.end_pos > existing.start_pos and
                    existing.id != keyframe.id):
                print(f"Warning: Keyframe {keyframe.id} overlaps with {existing.id}")

        # Remove existing keyframe with same id
        self.keyframes = [kf for kf in self.keyframes if kf.id != keyframe.id]

        # Add new keyframe
        self.keyframes.append(keyframe)
        self._update_sorted_positions()

    def add_statement(self, statement: StatementObject):
        """Add a statement object to the track."""
        # Remove existing statement with same id
        self.statements = [stmt for stmt in self.statements if stmt.id != statement.id]

        # Add new statement
        self.statements.append(statement)
        self._update_sorted_positions()

    def remove_keyframe(self, keyframe_id: str):
        """Remove a keyframe by ID."""
        self.keyframes = [kf for kf in self.keyframes if kf.id != keyframe_id]
        self._update_sorted_positions()

    def remove_statement(self, statement_id: str):
        """Remove a statement by ID."""
        self.statements = [stmt for stmt in self.statements if stmt.id != statement_id]
        self._update_sorted_positions()

    def get_keyframe(self, keyframe_id: str) -> Optional[Keyframe]:
        """Get a keyframe by ID."""
        for kf in self.keyframes:
            if kf.id == keyframe_id:
                return kf
        return None

    def get_statement(self, statement_id: str) -> Optional[StatementObject]:
        """Get a statement by ID."""
        for stmt in self.statements:
            if stmt.id == statement_id:
                return stmt
        return None

    def _update_sorted_positions(self):
        """Update sorted positions for efficient lookup."""
        positions = []
        for kf in self.keyframes:
            positions.extend([kf.start_pos, kf.end_pos])
        for stmt in self.statements:
            positions.extend([stmt.start_pos, stmt.end_pos])
        self._sorted_positions = sorted(set(positions))

    def get_value_at(self, position: float) -> Any:
        """Get interpolated value at a specific position."""
        # First check for statement data (statements take priority)
        for statement in self.statements:
            data = statement.get_data_at(position)
            if data is not None:
                return data

        # If no statement data, check keyframes
        if not self.keyframes:
            return None

        # Find active keyframe at this position
        for keyframe in self.keyframes:
            if keyframe.contains_position(position):
                return keyframe.interpolate(position)

        # If no active keyframe, find the nearest value
        return self._get_nearest_value(position)

    def _get_nearest_value(self, position: float) -> Any:
        """Get the nearest value when position is outside all keyframes."""
        if not self.keyframes:
            return None

        # Find closest keyframe
        closest_kf = min(self.keyframes,
                         key=lambda kf: min(abs(position - kf.start_pos),
                                            abs(position - kf.end_pos)))

        # Return appropriate edge value
        if position < closest_kf.start_pos:
            return closest_kf.start_value
        else:
            return closest_kf.end_value


class TimelineObject:
    """Represents an animated object with multiple properties/tracks."""

    def __init__(self, object_id: str):
        self.id = object_id
        self.tracks: Dict[str, AnimationTrack] = {}
        self.metadata: Dict[str, Any] = {}

    def add_track(self, track_name: str) -> AnimationTrack:
        """Add a new animation track for a property."""
        if track_name not in self.tracks:
            self.tracks[track_name] = AnimationTrack(track_name)
        return self.tracks[track_name]

    def get_track(self, track_name: str) -> Optional[AnimationTrack]:
        """Get an animation track by name."""
        return self.tracks.get(track_name)

    def remove_track(self, track_name: str):
        """Remove an animation track."""
        if track_name in self.tracks:
            del self.tracks[track_name]

    def get_state_at(self, position: float) -> Dict[str, Any]:
        """Get the state of all properties at a specific position."""
        state = {}
        for track_name, track in self.tracks.items():
            value = track.get_value_at(position)
            if value is not None:
                state[track_name] = value
        return state


class Timeline:
    """Advanced timeline system with object management and keyframe interpolation."""

    def __init__(self, total_frames: float = 320, fps=30.0):
        self.total_frames = total_frames
        self.current_position = 0.0
        self.objects: Dict[str, TimelineObject] = {}
        self.global_tracks: Dict[str, AnimationTrack] = {}
        self.frame_rate = fps
        self._callbacks: List[Callable[[float], None]] = []

    # Core object management
    def create_object(self, object_id: str) -> TimelineObject:
        """Create a new timeline object."""
        if object_id in self.objects:
            print(f"Warning: Object {object_id} already exists")
        self.objects[object_id] = TimelineObject(object_id)
        return self.objects[object_id]

    def get_object(self, object_id: str) -> Optional[TimelineObject]:
        """Get a timeline object by ID."""
        return self.objects.get(object_id)

    def remove_object(self, object_id: str):
        """Remove a timeline object."""
        if object_id in self.objects:
            del self.objects[object_id]

    def new_statement(self, object_id: str, track_name: str, start_pos: float,
                     end_pos: float, data: Any, statement_id: str = None,
                     active: bool = True) -> 'Timeline':
        """Create a new statement object that holds static data within a time range."""
        # Get or create object
        if object_id not in self.objects:
            self.create_object(object_id)

        obj = self.objects[object_id]
        track = obj.add_track(track_name)

        # Generate statement ID if not provided
        if statement_id is None:
            statement_id = f"{object_id}_{track_name}_stmt_{len(track.statements)}"

        # Create statement object
        statement = StatementObject(
            id=statement_id,
            start_pos=start_pos,
            end_pos=end_pos,
            data=data,
            active=active
        )

        track.add_statement(statement)
        return self

    def update_statement(self, object_id: str, track_name: str, statement_id: str,
                        data: Any = None, active: bool = None) -> 'Timeline':
        """Update an existing statement's data or active state."""
        obj = self.get_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")

        track = obj.get_track(track_name)
        if track is None:
            raise ValueError(f"Track {track_name} not found in object {object_id}")

        statement = track.get_statement(statement_id)
        if statement is None:
            raise ValueError(f"Statement {statement_id} not found in track {track_name}")

        # Update statement properties
        if data is not None:
            statement.data = data
        if active is not None:
            statement.active = active

        return self

    def remove_statement(self, object_id: str, track_name: str, statement_id: str) -> 'Timeline':
        """Remove a statement object."""
        obj = self.get_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")

        track = obj.get_track(track_name)
        if track is None:
            raise ValueError(f"Track {track_name} not found in object {object_id}")

        track.remove_statement(statement_id)
        return self

    # Keyframe management (main interface)
    def new_key(self, object_id: str, track_name: str, keyframe_id: str,
                start_pos: float, start_value: Any, end_pos: float, end_value: Any) -> 'Timeline':
        """Create a new keyframe with the requested interface."""
        # Get or create object and track
        if object_id not in self.objects:
            self.create_object(object_id)

        obj = self.objects[object_id]
        track = obj.add_track(track_name)

        # Create keyframe
        keyframe = Keyframe(
            id=keyframe_id,
            start_pos=start_pos,
            start_value=start_value,
            end_pos=end_pos,
            end_value=end_value
        )

        track.add_keyframe(keyframe)
        return self

    def set_curve(self, object_id: str, track_name: str, keyframe_id: str,
                  curve_function: Callable[[float], float]) -> 'Timeline':
        """Set a custom curve function for a keyframe."""
        obj = self.get_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")

        track = obj.get_track(track_name)
        if track is None:
            raise ValueError(f"Track {track_name} not found in object {object_id}")

        keyframe = track.get_keyframe(keyframe_id)
        if keyframe is None:
            raise ValueError(f"Keyframe {keyframe_id} not found in track {track_name}")

        keyframe.curve_function = curve_function
        keyframe.interpolation_type = InterpolationType.CUSTOM
        return self

    # Playback control
    def set_position(self, position: float):
        """Set the current playback position."""
        self.current_position = max(0, min(position, self.total_frames))
        self._trigger_callbacks()

    def play(self, start_pos: float = None, end_pos: float = None,
             callback: Callable[[float, Dict[str, Dict[str, Any]]], None] = None):
        """Play the timeline from start to end position."""
        start = start_pos if start_pos is not None else self.current_position
        end = end_pos if end_pos is not None else self.total_frames

        frame_duration = 1.0 / self.frame_rate
        position = start

        while position <= end:
            self.set_position(position)

            if callback:
                # Get state of all objects
                states = {}
                for obj_id, obj in self.objects.items():
                    states[obj_id] = obj.get_state_at(position)
                callback(position, states)

            position += frame_duration

    def get_scene_state(self, position: float = None) -> Dict[str, Dict[str, Any]]:
        """Get the state of all objects at a specific position."""
        pos = position if position is not None else self.current_position
        states = {}
        for obj_id, obj in self.objects.items():
            obj_state = obj.get_state_at(pos)
            # Only include objects that have data at this position
            if obj_state:  # This will be empty dict {} if no tracks have data
                states[obj_id] = obj_state
        return states

    # Utility methods
    def add_callback(self, callback: Callable[[float], None]):
        """Add a callback to be triggered on position changes."""
        self._callbacks.append(callback)

    def _trigger_callbacks(self):
        """Trigger all registered callbacks."""
        for callback in self._callbacks:
            callback(self.current_position)

    # Analysis methods
    def get_timeline_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the timeline."""
        info = {
            'total_frames': self.total_frames,
            'current_position': self.current_position,
            'frame_rate': self.frame_rate,
            'objects': {},
            'total_keyframes': 0,
            'total_statements': 0
        }

        for obj_id, obj in self.objects.items():
            obj_info = {
                'tracks': {},
                'metadata': obj.metadata
            }

            for track_name, track in obj.tracks.items():
                track_info = {
                    'keyframes': len(track.keyframes),
                    'statements': len(track.statements),
                    'keyframe_details': [],
                    'statement_details': []
                }

                for kf in track.keyframes:
                    track_info['keyframe_details'].append({
                        'id': kf.id,
                        'start_pos': kf.start_pos,
                        'end_pos': kf.end_pos,
                        'duration': kf.duration,
                        'interpolation': kf.interpolation_type.value,
                        'has_custom_curve': kf.curve_function is not None
                    })

                for stmt in track.statements:
                    track_info['statement_details'].append({
                        'id': stmt.id,
                        'start_pos': stmt.start_pos,
                        'end_pos': stmt.end_pos,
                        'duration': stmt.duration,
                        'active': stmt.active,
                        'data_type': type(stmt.data).__name__
                    })

                obj_info['tracks'][track_name] = track_info
                info['total_keyframes'] += track_info['keyframes']
                info['total_statements'] += track_info['statements']

            info['objects'][obj_id] = obj_info

        return info


# Built-in curve functions
class Curves:
    """Collection of common easing/curve functions."""

    @staticmethod
    def linear(t: float) -> float:
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        return 1 - (1 - t) ** 2

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) ** 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t ** 3

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t ** 3 if t < 0.5 else 1 - 4 * (1 - t) ** 3

    @staticmethod
    def bounce_out(t: float) -> float:
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def elastic_out(t: float) -> float:
        if t == 0 or t == 1:
            return t
        return 2 ** (-10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

    @staticmethod
    def bezier_cubic(p1: Tuple[float, float], p2: Tuple[float, float]):
        """Create a cubic bezier curve function."""

        def bezier(t: float) -> float:
            # Cubic bezier formula with control points
            u = 1 - t
            return (3 * u * u * t * p1[1] +
                    3 * u * t * t * p2[1] +
                    t * t * t)

        return bezier


# Example usage and demonstration
if __name__ == "__main__":
    # Create timeline
    timeline = Timeline(total_frames=10.0)

    # Example 1: Basic keyframe animation
    (timeline
     .new_key("sphere", "position_x", "move1", 0, 0, 3, 10)
     .new_key("sphere", "position_y", "jump1", 1, 0, 2, 5)
     .new_key("sphere", "position_y", "fall1", 2, 5, 4, 0)
     .new_key("sphere", "scale", "grow1", 0, 1, 5, 2))

    # Example 2: Add custom curves
    timeline.set_curve("sphere", "position_y", "jump1", Curves.ease_out_quad)
    timeline.set_curve("sphere", "position_y", "fall1", Curves.ease_in_quad)
    timeline.set_curve("sphere", "scale", "grow1", lambda t: t * t * t)  # Custom cubic

    # Example 3: Statement objects (static data within time ranges)
    (timeline
     .new_statement("ui_element", "text", 1.0, 3.0, {"content": "Hello World!", "font": "Arial"})
     .new_statement("ui_element", "visibility", 0.5, 4.0, True)
     .new_statement("background", "color", 2.0, 8.0, [0.2, 0.3, 0.8])
     .new_statement("audio", "sound_effect", 1.5, 2.5, {"file": "jump.wav", "volume": 0.8}))

    # Example 4: Complex animation with multiple objects
    (timeline
     .new_key("camera", "position", "cam_move", 0, [0, 0, 10], 8, [5, 2, 8])
     .new_key("camera", "rotation", "cam_rot", 2, 0, 6, 45)
     .set_curve("camera", "position", "cam_move", Curves.ease_in_out_cubic))

    # Example 5: Color animation
    (timeline
     .new_key("light", "color", "color_change", 0, [1, 1, 1], 5, [1, 0.5, 0.2])
     .new_key("light", "intensity", "dim", 6, 1.0, 9, 0.3)
     .set_curve("light", "intensity", "dim", Curves.ease_out_cubic))

    # Demonstrate usage
    print("Timeline Information:")
    print("=" * 50)
    info = timeline.get_timeline_info()
    print(f"Total frames: {info['total_frames']}")
    print(f"Frame rate: {info['frame_rate']} fps")
    print(f"Total keyframes: {info['total_keyframes']}")
    print(f"Total statements: {info['total_statements']}")

    for obj_id, obj_info in info['objects'].items():
        print(f"\nObject: {obj_id}")
        for track_name, track_info in obj_info['tracks'].items():
            print(f"  Track: {track_name}")
            if track_info['keyframes'] > 0:
                print(f"    Keyframes ({track_info['keyframes']}):")
                for kf_detail in track_info['keyframe_details']:
                    curve_info = "Custom" if kf_detail['has_custom_curve'] else kf_detail['interpolation']
                    print(f"      {kf_detail['id']}: {kf_detail['start_pos']:.1f}-{kf_detail['end_pos']:.1f}s ({curve_info})")

            if track_info['statements'] > 0:
                print(f"    Statements ({track_info['statements']}):")
                for stmt_detail in track_info['statement_details']:
                    active_str = "active" if stmt_detail['active'] else "inactive"
                    print(f"      {stmt_detail['id']}: {stmt_detail['start_pos']:.1f}-{stmt_detail['end_pos']:.1f}s ({stmt_detail['data_type']}, {active_str})")

    # Sample animation states at different times
    print("\n" + "=" * 50)
    print("Scene States Over Time:")
    print("=" * 50)
    for t in [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]:
        print(f"\nTime {t}s:")
        states = timeline.get_scene_state(t)
        if states:
            for obj_id, obj_state in states.items():
                print(f"  {obj_id}: {obj_state}")
        else:
            print("  No active objects")

    # Example of statement management
    print("\n" + "=" * 50)
    print("Statement Management Example:")
    print("=" * 50)

    # Update statement data
    timeline.update_statement("ui_element", "text", "ui_element_text_stmt_0",
                            {"content": "Updated Text!", "font": "Comic Sans"})

    # Check the updated state at time 2.0
    print("After updating ui_element text:")
    states = timeline.get_scene_state(2.0)
    print(f"State at 2.0s: {states.get('ui_element', {})}")

    # Deactivate a statement
    timeline.update_statement("background", "color", "background_color_stmt_0", active=False)
    print("\nAfter deactivating background color:")
    states = timeline.get_scene_state(5.0)
    print(f"State at 5.0s: {states}")