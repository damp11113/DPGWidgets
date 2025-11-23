import time
import dearpygui.dearpygui as dpg
import sys

from .timeline import Timeline

class TimelineWidget:
    def __init__(self, canvas_id, timeline: Timeline, width=800, height=320):
        self.canvas_id = canvas_id
        self.width = width
        self.height = height
        self.timeline = timeline

        # Layout constants
        self.tracks_width = 180
        self.time_ruler_height = 20
        self.track_height = 25
        self.track_padding = 2

        # Timeline properties
        self.total_frames = 0
        self.frame_rate = 0
        self.current_time = 0.0
        self.current_frame = 0

        # Zoom and pan properties
        self.zoom_level = 1.0  # 1.0 = default zoom
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.scroll_x = 0  # horizontal scroll offset in pixels
        self.scroll_y = 0  # vertical scroll offset in pixels

        # Display properties
        self.display_mode = "frames"  # "frames" or "time"
        self.pixels_per_frame = 4.0  # Default pixels per frame
        self.update_pixels_per_frame()

        # Track visibility
        self.visible_tracks = []  # Will be populated with all tracks by default

        # Color scheme for different interpolation types
        self.colors = {
            "keyframe": [100, 180, 255, 200],
            "statement": [255, 150, 100, 200]
        }

        self.mouse_first_click_pos = (0, 0)
        self.past_x_pos = 0
        self.past_y_pos = 0
        self.last_frame_drag = 0
        self.is_mouse_dragging_playhead = False
        self.is_mouse_dragging_pos = False
        self.last_move_drag = (0, 0)
        self.is_play = False # help to reduce rendering during playback
        self.disable_dragging_playhead = False

        self.editor_mode_enabled = True
        self.editor_callback = None
        # Editor state tracking
        self.selected_clip = None
        self.drag_mode = None  # None, 'move', 'resize_front', 'resize_back'
        self.drag_start_frame = 0
        self.drag_start_clip_data = None
        self.last_double_click_time = 0
        self.last_double_click_clip = None

    def update_pixels_per_frame(self):
        """Update pixels per frame based on zoom level"""
        base_pixels_per_frame = (self.width - self.tracks_width) / max(self.total_frames, 1)
        self.pixels_per_frame = max(0.5, base_pixels_per_frame * self.zoom_level)

    def frame_to_x(self, frame):
        """Convert frame number to x coordinate"""
        return self.tracks_width + (frame * self.pixels_per_frame) - self.scroll_x

    def time_to_x(self, time):
        """Convert time to x coordinate"""
        frame = time * self.frame_rate
        return self.frame_to_x(frame)

    def x_to_frame(self, x):
        """Convert x coordinate to frame number"""
        return max(0, int((x - self.tracks_width + self.scroll_x) / self.pixels_per_frame))

    def x_to_time(self, x):
        """Convert x coordinate to time"""
        frame = self.x_to_frame(x)
        return frame / self.frame_rate

    def set_zoom(self, new_zoom, center_x=None):
        """Set zoom level, optionally centering on a specific x coordinate"""
        old_zoom = self.zoom_level
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, new_zoom))

        if center_x is not None and old_zoom != self.zoom_level:
            # Adjust scroll to keep the center point stable
            zoom_ratio = self.zoom_level / old_zoom
            self.scroll_x = (self.scroll_x + center_x - self.tracks_width) * zoom_ratio - (center_x - self.tracks_width)
            self.scroll_x = max(0, self.scroll_x)

        self.update_pixels_per_frame()

    def set_scroll_x(self, new_scroll_x):
        """Set horizontal scroll position"""
        max_scroll = max(0, (self.total_frames * self.pixels_per_frame) - (self.width - self.tracks_width))
        self.scroll_x = max(0, min(max_scroll, new_scroll_x))

    def set_scroll_y(self, new_scroll_y):
        """Set vertical scroll position"""
        max_scroll = max(0, len(self.visible_tracks) * (self.track_height + self.track_padding) - (
                    self.height - self.time_ruler_height))
        self.scroll_y = max(0, min(max_scroll, new_scroll_y))

    def get_visible_frame_range(self):
        """Get the range of frames currently visible"""
        start_frame = self.x_to_frame(self.tracks_width)
        end_frame = self.x_to_frame(self.width) + 1
        return start_frame, min(end_frame, self.total_frames)

    def get_visible_track_range(self):
        """Get the range of tracks currently visible"""
        start_track = max(0, int(self.scroll_y / (self.track_height + self.track_padding)))
        visible_height = self.height - self.time_ruler_height
        end_track = min(len(self.visible_tracks),
                        start_track + int(visible_height / (self.track_height + self.track_padding)) + 2)
        return start_track, end_track

    def get_flattened_tracks(self, timeline_data):
        """Convert nested object.track structure to flat track list for rendering"""
        flattened_tracks = []

        for obj_id, obj_info in timeline_data.get('objects', {}).items():
            for track_name, track_data in obj_info.get('tracks', {}).items():
                track_label = f"{obj_id}.{track_name}"

                clips = []
                for statement in track_data.get('keyframe_details', []):
                    start_frame = int(statement.get('start_pos', 0))
                    duration_frames = int(statement.get('duration', 1))
                    end_frame = start_frame + duration_frames

                    clip = {
                        "id": statement.get('id', ''),
                        "name": statement.get('id', track_name),
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "duration_frames": duration_frames,
                        "start": statement.get('start_pos', 0),
                        "end": statement.get('start_pos', 0) + statement.get('duration', 1),
                        "interpolation": statement.get('interpolation', 'linear'),
                        "has_custom_curve": statement.get('has_custom_curve', False),
                        "color": self.colors.get("keyframe", [100, 180, 255, 200])
                    }
                    clips.append(clip)

                for statement in track_data.get('statement_details', []):
                    start_frame = int(statement.get('start_pos', 0))
                    duration_frames = int(statement.get('duration', 1))
                    end_frame = start_frame + duration_frames

                    clip = {
                        "id": statement.get('id', ''),
                        "name": statement.get('id', track_name),
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "duration_frames": duration_frames,
                        "start": statement.get('start_pos', 0),
                        "end": statement.get('start_pos', 0) + statement.get('duration', 1),
                        "interpolation": None,
                        "has_custom_curve": False,
                        "color": self.colors.get("statement", [255, 150, 100, 200])
                    }
                    clips.append(clip)

                flattened_tracks.append({
                    "label": track_label,
                    "object": obj_id,
                    "track": track_name,
                    "clips": clips
                })

        return flattened_tracks

    def draw_time_ruler(self, timeline_data):
        """Draw the time ruler at the top showing frames or time"""
        # Background
        dpg.draw_rectangle(
            [self.tracks_width, 0],
            [self.width, self.time_ruler_height],
            parent=self.canvas_id,
            fill=[40, 45, 46, 255],
            color=[70, 75, 76, 255]
        )

        start_frame, end_frame = self.get_visible_frame_range()

        # Determine step size based on zoom level
        if self.pixels_per_frame >= 20:
            major_step = 1  # Show every frame
            minor_step = None
        elif self.pixels_per_frame >= 10:
            major_step = 2
            minor_step = 1
        elif self.pixels_per_frame >= 4:
            major_step = 5
            minor_step = 1
        elif self.pixels_per_frame >= 2:
            major_step = 10
            minor_step = 5
        elif self.pixels_per_frame >= 1:
            major_step = 30  # Every second at 30fps
            minor_step = 10
        else:
            major_step = int(30 / self.pixels_per_frame) * 30  # Adaptive
            minor_step = major_step // 3

        # Draw major ticks and labels
        for frame in range(start_frame, end_frame + 1, major_step):
            if frame > self.total_frames:
                break

            x = self.frame_to_x(frame)
            if self.tracks_width <= x <= self.width:
                # Major tick
                dpg.draw_line(
                    [x, 0], [x, self.time_ruler_height],
                    parent=self.canvas_id,
                    color=[200, 200, 200, 255],
                    thickness=1
                )

                # Frame/time label
                if self.display_mode == "frames":
                    label = str(frame)
                else:
                    time_seconds = frame / self.frame_rate
                    minutes = int(time_seconds // 60)
                    seconds = time_seconds % 60
                    label = f"{minutes:02d}:{seconds:05.2f}"

                dpg.draw_text(
                    [x + 2, 5], label,
                    parent=self.canvas_id,
                    color=[200, 200, 200, 255],
                    size=11
                )

        # Draw minor ticks
        if minor_step and self.pixels_per_frame >= 2:
            for frame in range(start_frame, end_frame + 1, minor_step):
                if frame > self.total_frames or frame % major_step == 0:
                    continue

                x = self.frame_to_x(frame)
                if self.tracks_width <= x <= self.width:
                    dpg.draw_line(
                        [x, self.time_ruler_height - 8],
                        [x, self.time_ruler_height],
                        parent=self.canvas_id,
                        color=[150, 150, 150, 255],
                        thickness=1
                    )

    def draw_tracks_panel(self, tracks):
        """Draw the tracks panel on the left"""
        # Background
        dpg.draw_rectangle(
            [0, self.time_ruler_height],
            [self.tracks_width, self.height],
            parent=self.canvas_id,
            fill=[58, 63, 64, 255],
            color=[70, 75, 76, 255]
        )

        start_track, end_track = self.get_visible_track_range()

        # Draw visible track labels
        for i in range(start_track, end_track):
            if i >= len(tracks):
                break

            track = tracks[i]
            y = self.time_ruler_height + (
                        i * (self.track_height + self.track_padding)) + self.track_padding - self.scroll_y

            # Skip if track is not visible
            if y + self.track_height < self.time_ruler_height or y > self.height:
                continue

            # Track background
            bg_color = [48, 53, 54, 255] if i % 2 == 0 else [53, 58, 59, 255]
            dpg.draw_rectangle(
                [0, y],
                [self.tracks_width, y + self.track_height],
                parent=self.canvas_id,
                fill=bg_color,
                color=[70, 75, 76, 255]
            )

            # Track name with keyframe count
            label = f"{track['label']}"
            dpg.draw_text(
                [5, y + 6], label,
                parent=self.canvas_id,
                color=[200, 200, 200, 255],
                size=11
            )

    def draw_timeline_area(self, tracks):
        timeline_start_x = self.tracks_width

        # Background
        dpg.draw_rectangle(
            [timeline_start_x, self.time_ruler_height],
            [self.width, self.height],
            parent=self.canvas_id,
            fill=[35, 38, 39, 255],
            color=[70, 75, 76, 255]
        )

        start_track, end_track = self.get_visible_track_range()
        start_frame, end_frame = self.get_visible_frame_range()

        # Draw vertical grid lines for frames
        grid_step = max(1, int(30 / self.pixels_per_frame))  # Adjust step for zoom
        for frame in range(start_frame, end_frame + 1, grid_step):
            x = self.frame_to_x(frame)
            if timeline_start_x <= x <= self.width:
                dpg.draw_line(
                    [x, self.time_ruler_height],
                    [x, self.height],
                    parent=self.canvas_id,
                    color=[80, 80, 80, 120],
                    thickness=1
                )

        # Existing track lanes and grid lines
        for i in range(start_track, end_track):
            if i >= len(tracks):
                break

            y = self.time_ruler_height + (i * (self.track_height + self.track_padding)) + self.track_padding - self.scroll_y

            if y + self.track_height < self.time_ruler_height or y > self.height:
                continue

            dpg.draw_line(
                [timeline_start_x, y + self.track_height],
                [self.width, y + self.track_height],
                parent=self.canvas_id,
                color=[60, 65, 66, 255],
                thickness=1
            )

    def draw_keyframes(self, tracks):
        """Draw keyframe clips on the timeline"""
        start_track, end_track = self.get_visible_track_range()
        start_frame, end_frame = self.get_visible_frame_range()

        for track_idx in range(start_track, end_track):
            if track_idx >= len(tracks):
                break

            track = tracks[track_idx]
            y = self.time_ruler_height + (
                        track_idx * (self.track_height + self.track_padding)) + self.track_padding - self.scroll_y

            # Skip if track is not visible
            if y + self.track_height < self.time_ruler_height or y > self.height:
                continue

            for clip in track["clips"]:
                # Check if clip is in visible frame range
                if clip["end_frame"] < start_frame or clip["start_frame"] > end_frame:
                    continue

                start_x = self.frame_to_x(clip["start_frame"])
                end_x = self.frame_to_x(clip["end_frame"])

                if start_x < self.width and end_x > self.tracks_width:
                    # Clip boundaries
                    clip_start_x = max(start_x, self.tracks_width)
                    clip_end_x = min(end_x, self.width)

                    # Keyframe clip rectangle
                    dpg.draw_rectangle(
                        [clip_start_x, y + 1],
                        [clip_end_x, y + self.track_height - 1],
                        parent=self.canvas_id,
                        fill=clip["color"],
                        color=[255, 255, 255, 150],
                        thickness=1
                    )

                    # Custom curve indicator
                    #if clip.get("has_custom_curve", False):
                    #    center_x = (clip_start_x + clip_end_x) / 2
                    #    center_y = y + self.track_height / 2
                    #    dpg.draw_circle(
                    #        [center_x, center_y], 3,
                    #        parent=self.canvas_id,
                    #        fill=[255, 255, 100, 255],
                    #        color=[255, 255, 100, 255]
                    #    )

                    # Keyframe name (if there's space and zoom allows)
                    if self.pixels_per_frame >= 2:
                        text_width = len(clip["name"]) * 6
                        clip_width = clip_end_x - clip_start_x
                        if clip_width > text_width + 10:
                            text_x = clip_start_x + 5
                            dpg.draw_text(
                                [text_x, y + 7],
                                clip["name"],
                                parent=self.canvas_id,
                                color=[255, 255, 255, 255],
                                size=9
                            )

                    # Draw keyframe markers at start and end (if zoom allows)
                    #if self.pixels_per_frame >= 1:
                    #    # Start keyframe marker
                    #    if start_x >= self.tracks_width:
                    #        dpg.draw_triangle(
                    #            [start_x, y + self.track_height / 2],
                    #            [start_x + 4, y + 2],
                    #            [start_x + 4, y + self.track_height - 2],
                    #            parent=self.canvas_id,
                    #            fill=[255, 255, 255, 255],
                    #            color=[255, 255, 255, 255]
                    #        )

                    #    # End keyframe marker
                    #    if end_x <= self.width:
                    #        dpg.draw_triangle(
                    #            [end_x, y + self.track_height / 2],
                    #            [end_x - 4, y + 2],
                    #            [end_x - 4, y + self.track_height - 2],
                    #            parent=self.canvas_id,
                    #            fill=[255, 255, 255, 255],
                    #            color=[255, 255, 255, 255]
                    #        )

    def draw_playhead(self, timeline_data):
        """Draw the playhead indicator"""
        current_frame = timeline_data.get('current_position', self.current_time)
        x = self.frame_to_x(current_frame)

        if self.tracks_width <= x <= self.width:
            # Playhead line
            dpg.draw_line(
                [x, 0], [x, self.height],
                parent=self.canvas_id,
                color=[255, 100, 100, 255],
                thickness=2
            )

            # Playhead triangle at top
            dpg.draw_triangle(
                [x, 0], [x - 6, 12], [x + 6, 12],
                parent=self.canvas_id,
                fill=[255, 100, 100, 255],
                color=[255, 100, 100, 255]
            )

    def handle_mouse_click(self, app_data):
        """Handle mouse clicks to move playhead"""
        if not dpg.is_item_hovered(self.canvas_id):
            return

        self.past_x_pos = self.scroll_x
        self.past_y_pos = self.scroll_y

        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_rect_min(self.canvas_id)

        mouse_x = mouse_pos[0] - canvas_pos[0]
        mouse_y = mouse_pos[1] - canvas_pos[1]

        self.mouse_first_click_pos = (mouse_x, mouse_y)

        if mouse_x > self.tracks_width and mouse_y < self.time_ruler_height and app_data == 0:
            frame = self.x_to_frame(mouse_x)

            if self.last_frame_drag != frame:
                self.current_time = frame / self.frame_rate
                self.current_frame = frame
                self.timeline.set_position(frame)
                self.on_drag_playhead(frame)

                self.last_frame_drag = frame

                if not self.is_play:
                    self.render()

        if self.editor_mode_enabled:
            tracks = self.get_flattened_tracks(self.timeline.get_timeline_info())
            if self.handle_editor_mouse_click(app_data, tracks):
                return

    def handle_mouse_release(self, app_data):
        if self.is_mouse_dragging_playhead and app_data == 0:
            self.is_mouse_dragging_playhead = False
        elif self.is_mouse_dragging_pos and app_data == 2:
            self.is_mouse_dragging_pos = False

    def handle_mouse_drag(self, app_data):
        if not dpg.is_item_hovered(self.canvas_id) and not (self.is_mouse_dragging_playhead or self.is_mouse_dragging_pos):
            return

        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_rect_min(self.canvas_id)
        mouse_x = mouse_pos[0] - canvas_pos[0]
        mouse_y = mouse_pos[1] - canvas_pos[1]

        past_x, past_y = self.mouse_first_click_pos

        if ((mouse_x > self.tracks_width and mouse_y > self.time_ruler_height) or self.is_mouse_dragging_pos) and app_data[0] == 2:
            self.is_mouse_dragging_pos = True

            if self.last_move_drag != (mouse_x, mouse_y):
                self.set_scroll_x(self.past_x_pos + (past_x - mouse_x))
                self.set_scroll_y(self.past_y_pos + (past_y - mouse_y))

                self.last_move_drag = (mouse_x, mouse_y)

                if not self.is_play:
                    self.render()

        if ((mouse_x > self.tracks_width and mouse_y < self.time_ruler_height) or self.is_mouse_dragging_playhead) and app_data[0] == 0 and not self.disable_dragging_playhead:
            frame = self.x_to_frame(mouse_x)
            self.is_mouse_dragging_playhead = True

            if self.last_frame_drag != frame:
                self.current_time = frame / self.frame_rate
                self.current_frame = frame
                self.timeline.set_position(frame)
                self.on_drag_playhead(frame)

                self.last_frame_drag = frame

                if not self.is_play:
                    self.render()

        if self.editor_mode_enabled:
            tracks = self.get_flattened_tracks(self.timeline.get_timeline_info())
            if self.handle_editor_mouse_drag(app_data, tracks):
                return

    def on_drag_playhead(self, delta_frames):
        pass

    def set_playhead_frame(self, frame):
        """Set playhead to specific frame"""
        self.current_frame = max(0, min(self.total_frames, frame))
        self.current_time = self.current_frame / self.frame_rate
        self.timeline.set_position(frame)

        self.render()

    def handle_mouse_wheel(self, wheel_delta):
        """Handle mouse wheel for zooming and scrolling"""
        if not dpg.is_item_hovered(self.canvas_id):
            return

        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_pos(self.canvas_id)
        mouse_x = mouse_pos[0] - canvas_pos[0]

        if mouse_x > self.tracks_width:  # Horizontal zoom/scroll
            if wheel_delta > 0:  # Zoom in
                self.set_zoom(self.zoom_level * 1.2, mouse_x)
            else:  # Zoom out
                self.set_zoom(self.zoom_level / 1.2, mouse_x)
        else:  # Vertical scroll
            scroll_speed = 20
            if wheel_delta > 0:
                self.set_scroll_y(self.scroll_y - scroll_speed)
            else:
                self.set_scroll_y(self.scroll_y + scroll_speed)

        if not self.is_play:
            self.render()

    def set_editor_mode(self, enabled):
        """
        Enable/disable editor mode for interactive keyframe editing

        Args:
            enabled (bool): True to enable editor mode, False to disable
            callback (callable): Callback function with signature:
                callback(action_type, object_id, track_name, clip_id, dragged_frame, dragged_front)

                action_type:
                    0 = move
                    1 = change length (extend/trim)
                    2 = double click

                object_id: The object ID the clip belongs to
                track_name: The track name
                clip_id: The clip/keyframe ID
                dragged_frame: Frame delta (positive=extend, negative=trim)
                dragged_front: True=front edge, False=back edge
        """
        self.editor_mode_enabled = enabled

    def get_clip_at_position(self, mouse_x, mouse_y, tracks):
        """
        Find the clip at the given mouse position

        Returns:
            tuple: (track_idx, clip_idx, edge_type) or (None, None, None)
            edge_type: 'front', 'back', 'middle', or None
        """
        if mouse_x <= self.tracks_width or mouse_y <= self.time_ruler_height:
            return None, None, None

        # Determine which track
        track_y_offset = mouse_y - self.time_ruler_height + self.scroll_y
        track_idx = int(track_y_offset / (self.track_height + self.track_padding))

        if track_idx < 0 or track_idx >= len(tracks):
            return None, None, None

        # Check if mouse is within track height
        track_y = self.time_ruler_height + (
                    track_idx * (self.track_height + self.track_padding)) + self.track_padding - self.scroll_y
        if mouse_y < track_y or mouse_y > track_y + self.track_height:
            return None, None, None

        # Find clip at this position
        frame = self.x_to_frame(mouse_x)
        track = tracks[track_idx]

        edge_threshold = max(3, min(8, self.pixels_per_frame * 2))  # Adaptive edge detection

        for clip_idx, clip in enumerate(track["clips"]):
            if clip["start_frame"] <= frame <= clip["end_frame"]:
                clip_start_x = self.frame_to_x(clip["start_frame"])
                clip_end_x = self.frame_to_x(clip["end_frame"])

                # Check if near front edge
                if abs(mouse_x - clip_start_x) <= edge_threshold:
                    return track_idx, clip_idx, 'front'
                # Check if near back edge
                elif abs(mouse_x - clip_end_x) <= edge_threshold:
                    return track_idx, clip_idx, 'back'
                # Middle of clip
                else:
                    return track_idx, clip_idx, 'middle'

        return None, None, None

    def handle_editor_mouse_click(self, app_data, tracks):
        """Handle mouse clicks in editor mode"""
        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_rect_min(self.canvas_id)
        mouse_x = mouse_pos[0] - canvas_pos[0]
        mouse_y = mouse_pos[1] - canvas_pos[1]

        # Left click only
        if app_data != 0:
            return False

        # Check for double-click
        current_time = time.time()
        is_double_click = False

        track_idx, clip_idx, edge_type = self.get_clip_at_position(mouse_x, mouse_y, tracks)


        if track_idx is not None and clip_idx is not None:
            clip = tracks[track_idx]["clips"][clip_idx]

            # Double-click detection (within 300ms)
            if (current_time - self.last_double_click_time < 0.3 and
                    self.last_double_click_clip == clip["id"]):
                is_double_click = True

                # Trigger double-click callback
                if self.editor_callback:
                    self.editor_callback(
                        action_type=2,  # Double click
                        is_curve=clip.get("interpolation") is not None,
                        object_id=tracks[track_idx]["object"],
                        track_name=tracks[track_idx]["track"],
                        clip_id=clip["id"],
                        dragged_frame=0,
                        dragged_front=False
                    )

                self.last_double_click_time = 0
                self.last_double_click_clip = None
                return True
            else:
                self.last_double_click_time = current_time
                self.last_double_click_clip = clip["id"]

            # Start drag operation
            self.selected_clip = {
                'track_idx': track_idx,
                'clip_idx': clip_idx,
                "is_curve": clip.get("interpolation") is not None,
                'track_object': tracks[track_idx]["object"],
                'track_name': tracks[track_idx]["track"],
                'clip_id': clip["id"]
            }

            self.drag_start_frame = self.x_to_frame(mouse_x)
            self.drag_start_clip_data = {
                'start_frame': clip["start_frame"],
                'end_frame': clip["end_frame"],
                'duration_frames': clip["duration_frames"]
            }

            # Determine drag mode based on edge
            if edge_type == 'front':
                self.drag_mode = 'resize_front'
            elif edge_type == 'back':
                self.drag_mode = 'resize_back'
            else:
                self.drag_mode = 'move'

            return True
        else:
            # Clicked on empty space - deselect
            self.selected_clip = None
            self.drag_mode = None

        return False

    def handle_editor_mouse_drag(self, app_data, tracks):
        """Handle mouse drag in editor mode"""
        if not self.drag_mode or not self.selected_clip:
            return False

        if app_data[0] != 0:  # Only handle left mouse button
            return False

        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_rect_min(self.canvas_id)
        mouse_x = mouse_pos[0] - canvas_pos[0]

        current_frame = self.x_to_frame(mouse_x)
        frame_delta = current_frame - self.drag_start_frame

        if frame_delta == 0:
            return False

        # Get the clip being dragged
        track_idx = self.selected_clip['track_idx']
        clip_idx = self.selected_clip['clip_idx']

        if track_idx >= len(tracks) or clip_idx >= len(tracks[track_idx]["clips"]):
            return False

        clip = tracks[track_idx]["clips"][clip_idx]

        # Calculate new positions based on drag mode
        if self.drag_mode == 'move':
            # Moving entire clip
            new_start = self.drag_start_clip_data['start_frame'] + frame_delta
            new_end = self.drag_start_clip_data['end_frame'] + frame_delta

            # Bounds checking
            #if new_start < 0:
            #    frame_delta = -self.drag_start_clip_data['start_frame']

            if frame_delta != 0 and self.editor_callback:
                self.editor_callback(
                    action_type=0,  # Move
                    is_curve=self.selected_clip['is_curve'],
                    object_id=self.selected_clip['track_object'],
                    track_name=self.selected_clip['track_name'],
                    clip_id=self.selected_clip['clip_id'],
                    dragged_frame=frame_delta,
                    dragged_front=False
                )

                # Update drag start for continuous dragging
                self.drag_start_frame = current_frame
                self.drag_start_clip_data['start_frame'] = new_start
                self.drag_start_clip_data['end_frame'] = new_end

            return True

        elif self.drag_mode == 'resize_front':
            # Resizing from front edge
            new_start = self.drag_start_clip_data['start_frame'] + frame_delta

            # Don't allow resizing past the end
            if new_start >= self.drag_start_clip_data['end_frame']:
                return False

            # Don't allow negative start
            if new_start < 0:
                frame_delta = -self.drag_start_clip_data['start_frame']

            if frame_delta != 0 and self.editor_callback:
                self.editor_callback(
                    action_type=1,  # Change length
                    is_curve=self.selected_clip['is_curve'],
                    object_id=self.selected_clip['track_object'],
                    track_name=self.selected_clip['track_name'],
                    clip_id=self.selected_clip['clip_id'],
                    dragged_frame=frame_delta,
                    dragged_front=True
                )

                # Update drag start for continuous dragging
                self.drag_start_frame = current_frame
                self.drag_start_clip_data['start_frame'] = new_start
                self.drag_start_clip_data['duration_frames'] = self.drag_start_clip_data['end_frame'] - new_start

            return True

        elif self.drag_mode == 'resize_back':
            # Resizing from back edge
            new_end = self.drag_start_clip_data['end_frame'] + frame_delta

            # Don't allow resizing past the start
            if new_end <= self.drag_start_clip_data['start_frame']:
                return False

            if frame_delta != 0 and self.editor_callback:
                self.editor_callback(
                    action_type=1,  # Change length
                    is_curve=self.selected_clip['is_curve'],
                    object_id=self.selected_clip['track_object'],
                    track_name=self.selected_clip['track_name'],
                    clip_id=self.selected_clip['clip_id'],
                    dragged_frame=frame_delta,
                    dragged_front=False
                )

                # Update drag start for continuous dragging
                self.drag_start_frame = current_frame
                self.drag_start_clip_data['end_frame'] = new_end
                self.drag_start_clip_data['duration_frames'] = new_end - self.drag_start_clip_data['start_frame']

            return True

        return False

    def handle_editor_mouse_release(self, app_data):
        """Handle mouse release in editor mode"""
        if not self.editor_mode_enabled:
            return False

        if app_data == 0:  # Left mouse button
            self.drag_mode = None
            self.drag_start_frame = 0
            self.drag_start_clip_data = None
            return True

        return False

    def update_editor_cursor(self, tracks):
        """Update cursor based on hover position in editor mode"""
        if not self.editor_mode_enabled or not dpg.is_item_hovered(self.canvas_id):
            return

        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_rect_min(self.canvas_id)
        mouse_x = mouse_pos[0] - canvas_pos[0]
        mouse_y = mouse_pos[1] - canvas_pos[1]

        track_idx, clip_idx, edge_type = self.get_clip_at_position(mouse_x, mouse_y, tracks)

        if edge_type in ['front', 'back']:
            set_cursor_windows(32644)  # IDC_SIZEWE (horizontal resize)
        elif edge_type == 'middle':
            set_cursor_windows(32646)  # IDC_SIZEALL (move)
        else:
            set_cursor_windows(32512)  # IDC_ARROW

    def draw_editor_highlights(self, tracks):
        """Draw visual highlights for selected clips in editor mode"""
        if not self.editor_mode_enabled or not self.selected_clip:
            return

        track_idx = self.selected_clip['track_idx']
        clip_idx = self.selected_clip['clip_idx']

        if track_idx >= len(tracks) or clip_idx >= len(tracks[track_idx]["clips"]):
            return

        clip = tracks[track_idx]["clips"][clip_idx]
        y = self.time_ruler_height + (
                    track_idx * (self.track_height + self.track_padding)) + self.track_padding - self.scroll_y

        start_x = self.frame_to_x(clip["start_frame"])
        end_x = self.frame_to_x(clip["end_frame"])

        # Draw selection highlight
        dpg.draw_rectangle(
            [max(start_x, self.tracks_width), y],
            [min(end_x, self.width), y + self.track_height],
            parent=self.canvas_id,
            color=[255, 255, 100, 255],
            thickness=2
        )

    def render(self):
        """Main render function"""
        # Clear canvas
        dpg.delete_item(self.canvas_id, children_only=True)

        # Get timeline data
        timeline_data = self.timeline.get_timeline_info()

        # Update timeline properties
        self.total_frames = timeline_data.get('total_frames', self.total_frames)
        self.frame_rate = timeline_data.get('frame_rate', self.frame_rate)
        self.update_pixels_per_frame()

        # Get tracks
        tracks = self.get_flattened_tracks(timeline_data)
        self.visible_tracks = tracks

        if self.editor_mode_enabled:
            self.draw_editor_highlights(tracks)

        # Draw all components
        self.draw_timeline_area(tracks)
        self.draw_time_ruler(timeline_data)
        self.draw_tracks_panel(tracks)
        self.draw_keyframes(tracks)
        self.draw_playhead(timeline_data)