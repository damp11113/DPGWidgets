import time

import dearpygui.dearpygui as dpg

class MLED:
    """Matrix LED device configuration"""

    def __init__(self, id, width=8, height=8, backgroundColor=(30, 30, 30), LEDColor=(255, 0, 0), label=None):
        self.id = id
        self.width = width
        self.height = height
        self.backgroundColor = backgroundColor
        self.LEDColor = LEDColor
        self.label = label if label is not None else f"D{id}"

class MatrixLEDWidget:
    def __init__(self, canvas_id, devices_matrix=None, window_width=880, window_height=450):
        self.canvas_id = canvas_id
        self.window_width = window_width
        self.window_height = window_height

        # Default to single device if not specified
        if devices_matrix is None:
            devices_matrix = [[MLED(0)]]

        self.devices_matrix = devices_matrix

        # Parse device configurations
        self.devices = {}  # Maps device ID to MLED object
        self.device_positions = {}  # Maps device ID to (grid_row, grid_col)

        for grid_row, row in enumerate(devices_matrix):
            for grid_col, mled in enumerate(row):
                self.devices[mled.id] = mled
                self.device_positions[mled.id] = (grid_row, grid_col)

        self.num_devices = len(self.devices)

        # State matrix for each device
        self.state = {}
        for device_id, mled in self.devices.items():
            self.state[device_id] = [[False for _ in range(mled.width)] for _ in range(mled.height)]

        # LED colors for each device (can be set individually)
        self.led_colors = {}
        for device_id, mled in self.devices.items():
            self.led_colors[device_id] = [[mled.LEDColor for _ in range(mled.width)]
                                          for _ in range(mled.height)]

        # Intensity for each device (0-15, like MAX7219)
        self.intensity = {device_id: 15 for device_id in self.devices.keys()}

        # Zoom and pan
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # Editor mode
        self.editor_mode = False
        self.editor_callback = None
        self.is_dragging = False
        self.last_edited_led = None

        # Calculate grid dimensions
        self.grid_rows = len(devices_matrix)
        self.grid_cols = max(len(row) for row in devices_matrix)

        # Base LED size (will be scaled by zoom)
        self.base_led_size = 8
        self.device_spacing = 15

        self.color_off = (40, 40, 40, 255)
        self.color_border = (80, 80, 80, 255)

        self.is_mouse_middle_down = False
        self.last_mouse_pos = (0, 0)
        self.past_pos = (0, 0)
        self.last_move_drag = None

        # Rendering protection flags
        self.is_rendering = False
        self.needs_render = True
        self.last_render_time = 0
        self.min_render_interval = 0.016  # ~60 FPS max

    def on_mouse_wheel(self, sender, app_data):
        """Handle mouse wheel for zooming"""
        if not dpg.is_item_hovered(self.canvas_id):
            return

        mouse_pos = dpg.get_mouse_pos(local=False)

        # Get canvas position
        canvas_pos = dpg.get_item_pos(self.canvas_id)

        # Check if mouse is over canvas
        if (canvas_pos[0] <= mouse_pos[0] <= canvas_pos[0] + self.window_width and
                canvas_pos[1] <= mouse_pos[1] <= canvas_pos[1] + self.window_height):
            # Calculate mouse position relative to canvas
            mouse_x = mouse_pos[0] - canvas_pos[0]
            mouse_y = mouse_pos[1] - canvas_pos[1]

            # Calculate world position before zoom
            world_x_before = (mouse_x - self.pan_x) / self.zoom
            world_y_before = (mouse_y - self.pan_y) / self.zoom

            # Update zoom
            zoom_delta = app_data * 0.1
            old_zoom = self.zoom
            self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + zoom_delta))

            # Calculate world position after zoom
            world_x_after = (mouse_x - self.pan_x) / self.zoom
            world_y_after = (mouse_y - self.pan_y) / self.zoom

            # Adjust pan to keep mouse position consistent
            self.pan_x += (world_x_after - world_x_before) * self.zoom
            self.pan_y += (world_y_after - world_y_before) * self.zoom

            self._safe_render()

    def on_mouse_drag(self, sender, app_data):
        """Handle middle mouse drag for panning"""
        if not dpg.is_item_hovered(self.canvas_id):
            return

        if app_data[0] == 0:
            if not self.editor_mode or self.editor_callback is None:
                return

            self.is_dragging = True
            self._handle_led_edit(app_data)

        if app_data[0] == 2:
            mouse_pos = dpg.get_mouse_pos(local=False)
            canvas_pos = dpg.get_item_rect_min(self.canvas_id)
            mouse_x = mouse_pos[0] - canvas_pos[0]
            mouse_y = mouse_pos[1] - canvas_pos[1]

            past_x, past_y = self.last_mouse_pos

            if self.last_move_drag != (mouse_x, mouse_y):
                self.last_move_drag = (mouse_x, mouse_y)

                self.pan_x = self.past_pos[0] - (past_x - mouse_x)
                self.pan_y = self.past_pos[1] - (past_y - mouse_y)

                # Mark for render instead of rendering immediately
                self.needs_render = True

    def on_mouse_click(self, sender, app_data):
        """Handle left mouse click for editing LEDs"""
        if not dpg.is_item_hovered(self.canvas_id):
            return

        if app_data == 2:
            mouse_pos = dpg.get_mouse_pos(local=False)
            canvas_pos = dpg.get_item_rect_min(self.canvas_id)

            mouse_x = mouse_pos[0] - canvas_pos[0]
            mouse_y = mouse_pos[1] - canvas_pos[1]

            self.last_mouse_pos = (mouse_x, mouse_y)

            self.past_pos = (self.pan_x, self.pan_y)

        if app_data == 0:
            if not self.editor_mode or self.editor_callback is None:
                return

            self._handle_led_edit(app_data)

    def on_mouse_release(self, sender, app_data):
        """Handle mouse release"""
        self.is_dragging = False
        self.last_edited_led = None

    def _handle_led_edit(self, app_data):
        """Handle LED editing at mouse position"""
        mouse_pos = dpg.get_mouse_pos(local=False)
        canvas_pos = dpg.get_item_pos(self.canvas_id)

        # Check if mouse is over canvas
        if not (canvas_pos[0] <= mouse_pos[0] <= canvas_pos[0] + self.window_width and
                canvas_pos[1] <= mouse_pos[1] <= canvas_pos[1] + self.window_height):
            return

        # Calculate mouse position relative to canvas with zoom and pan
        mouse_x = (mouse_pos[0] - canvas_pos[0] - self.pan_x) / self.zoom
        mouse_y = (mouse_pos[1] - canvas_pos[1] - self.pan_y) / self.zoom

        # Find which device and LED was clicked
        device_id, led_x, led_y = self._get_led_at_position(mouse_x, mouse_y)

        if device_id is not None:
            # Avoid editing same LED multiple times during drag
            current_led = (device_id, led_x, led_y)
            if self.is_dragging and current_led == self.last_edited_led:
                return

            self.last_edited_led = current_led

            # Toggle LED state
            current_state = self.state[device_id][led_y][led_x]
            new_state = not current_state
            self.state[device_id][led_y][led_x] = new_state

            # Call callback
            self.editor_callback(device_id, led_x, led_y, new_state)
            self._safe_render()

    def _get_led_at_position(self, x, y):
        """Get device and LED coordinates at given position"""
        for grid_row, row in enumerate(self.devices_matrix):
            for grid_col, mled in enumerate(row):
                device_id = mled.id

                # Calculate device bounds
                device_x, device_y = self._get_device_position(grid_row, grid_col)

                led_size = self.base_led_size
                device_width = mled.width * led_size
                device_height = mled.height * led_size

                # Check if point is within device
                if (device_x <= x <= device_x + device_width and
                        device_y <= y <= device_y + 10 + device_height):

                    led_x = int(((x - device_x)) / led_size)
                    led_y = int(((y - device_y) - 10) / led_size)

                    if 0 <= led_x < mled.width and 0 <= led_y < mled.height:
                        return device_id, led_x, led_y

        return None, None, None

    def _get_device_position(self, grid_row, grid_col):
        """Calculate device position in world coordinates"""
        x = 0
        y = grid_row * (self.base_led_size * 8 + self.device_spacing)

        # Calculate X based on previous devices in same row
        for col in range(grid_col):
            if col < len(self.devices_matrix[grid_row]):
                prev_mled = self.devices_matrix[grid_row][col]
                x += prev_mled.width * self.base_led_size + self.device_spacing

        return x, y

    def set_editor_mode(self, enabled):
        """Enable/disable editor mode with callback"""
        self.editor_mode = enabled
        self.is_dragging = False
        self.last_edited_led = None

    def setLEDColor(self, device, row, col, color):
        """Set color for a specific LED"""
        if device in self.devices and 0 <= row < self.devices[device].height and 0 <= col < self.devices[device].width:
            self.led_colors[device][row][col] = color
            self._safe_render()

    def clear(self):
        """Clear all LEDs on all devices"""
        for device_id, mled in self.devices.items():
            self.state[device_id] = [[False for _ in range(mled.width)] for _ in range(mled.height)]
        self._safe_render()

    def clearDevice(self, device):
        """Clear all LEDs on a specific device"""
        if device in self.state:
            mled = self.devices[device]
            self.state[device] = [[False for _ in range(mled.width)] for _ in range(mled.height)]
            self._safe_render()

    def setRow(self, device, row, value):
        """Set an entire row using a byte value"""
        if device in self.state:
            mled = self.devices[device]
            if 0 <= row < mled.height:
                for col in range(min(mled.width, 8)):
                    bit = (value >> (7 - col)) & 1
                    self.state[device][row][col] = bool(bit)
                self._safe_render()

    def setColumn(self, device, col, value):
        """Set an entire column using a byte value"""
        if device in self.state:
            mled = self.devices[device]
            if 0 <= col < mled.width:
                for row in range(min(mled.height, 8)):
                    bit = (value >> (7 - row)) & 1
                    self.state[device][row][col] = bool(bit)
                self._safe_render()

    def setLed(self, device, row, col, state):
        """Set a single LED at given row and column on specified device"""
        if device in self.state:
            mled = self.devices[device]
            if 0 <= row < mled.height and 0 <= col < mled.width:
                self.state[device][row][col] = state
                self._safe_render()

    def setPixel(self, x, y, state):
        """Set a single pixel (uses device 0)"""
        self.setLed(0, y, x, state)

    def drawBitmap(self, device, bitmap):
        """Draw a bitmap (array of bytes, each representing a row)"""
        if device in self.state:
            mled = self.devices[device]
            for row in range(min(mled.height, len(bitmap))):
                self.setRow(device, row, bitmap[row])

    def getRow(self, device, row):
        """Get the byte value of a row"""
        if device in self.state:
            mled = self.devices[device]
            if 0 <= row < mled.height:
                value = 0
                for col in range(min(mled.width, 8)):
                    if self.state[device][row][col]:
                        value |= (1 << (7 - col))
                return value
        return 0

    def setIntensity(self, intensity):
        """Set intensity for all devices (0-15)"""
        intensity = max(0, min(15, intensity))
        for device_id in self.intensity:
            self.intensity[device_id] = intensity
        self._safe_render()

    def setIntensityDevice(self, device, intensity):
        """Set intensity for a specific device (0-15)"""
        if device in self.intensity:
            self.intensity[device] = max(0, min(15, intensity))
            self._safe_render()

    def _get_led_color(self, device, row, col, is_on):
        """Calculate LED color based on state and intensity"""
        if not is_on:
            return self.color_off

        base_color = self.led_colors[device][row][col]
        intensity_scale = self.intensity[device] / 15.0
        r = int(base_color[0] * intensity_scale)
        g = int(base_color[1] * intensity_scale)
        b = int(base_color[2] * intensity_scale)

        if intensity_scale > 0:
            r = max(r, int(base_color[0] * 0.1))
            g = max(g, int(base_color[1] * 0.1))
            b = max(b, int(base_color[2] * 0.1))

        return (r, g, b, 255)

    def _safe_render(self):
        """Safe render that prevents recursion and rate-limits"""
        # Mark for render instead of rendering immediately
        self.needs_render = True

    def update(self):
        """Call this in your main loop to process pending renders"""
        if self.needs_render:
            current_time = time.time()
            # Rate limit rendering to prevent excessive calls
            if current_time - self.last_render_time >= self.min_render_interval:
                self.needs_render = False
                self.render()

    def render(self):
        """Render all LED matrices on the canvas"""
        # Prevent re-entrant calls
        if self.is_rendering:
            return

        self.is_rendering = True
        self.last_render_time = time.time()

        try:
            dpg.delete_item(self.canvas_id, children_only=True)

            # Draw background
            dpg.draw_rectangle(
                (0, 0),
                (self.window_width, self.window_height),
                color=(20, 20, 20, 255),
                fill=(20, 20, 20, 255),
                parent=self.canvas_id
            )

            # Apply zoom and pan
            led_size = self.base_led_size * self.zoom
            led_radius = led_size * 0.35

            # Draw each device
            for grid_row, row in enumerate(self.devices_matrix):
                for grid_col, mled in enumerate(row):
                    device_id = mled.id

                    if device_id not in self.state:
                        continue

                    # Calculate device position with zoom and pan
                    world_x, world_y = self._get_device_position(grid_row, grid_col)
                    device_x = world_x * self.zoom + self.pan_x
                    device_y = world_y * self.zoom + self.pan_y

                    device_width = mled.width * led_size
                    device_height = mled.height * led_size

                    # Draw device background
                    bg_color = mled.backgroundColor + (255,) if len(mled.backgroundColor) == 3 else mled.backgroundColor
                    dpg.draw_rectangle(
                        (device_x - 5, device_y - 5),
                        (device_x + device_width + 5, device_y + device_height + 5),
                        color=(60, 60, 60, 255),
                        fill=bg_color,
                        parent=self.canvas_id
                    )

                    # Draw device label
                    label_size = max(10, min(16, 12 * self.zoom))
                    dpg.draw_text(
                        (device_x + 2, device_y - 18 * self.zoom),
                        mled.label,
                        color=(150, 150, 150, 255),
                        size=label_size,
                        parent=self.canvas_id
                    )

                    # Draw LEDs for this device
                    for row_idx in range(mled.height):
                        for col_idx in range(mled.width):
                            x = device_x + col_idx * led_size + led_size / 2
                            y = device_y + row_idx * led_size + led_size / 2

                            is_on = self.state[device_id][row_idx][col_idx]
                            color = self._get_led_color(device_id, row_idx, col_idx, is_on)

                            # Draw outer border
                            dpg.draw_circle(
                                (x, y),
                                led_radius + 1,
                                color=self.color_border,
                                fill=self.color_border,
                                parent=self.canvas_id
                            )

                            # Draw LED
                            dpg.draw_circle(
                                (x, y),
                                led_radius,
                                color=color,
                                fill=color,
                                parent=self.canvas_id
                            )

                            # Add glow effect when ON
                            if is_on and self.intensity[device_id] > 5:
                                glow_alpha = int(50 * (self.intensity[device_id] / 15.0))
                                dpg.draw_circle(
                                    (x, y),
                                    led_radius * 1.3,
                                    color=(color[0], color[1], color[2], glow_alpha),
                                    fill=(color[0], color[1], color[2], glow_alpha),
                                    parent=self.canvas_id
                                )
        finally:
            self.is_rendering = False