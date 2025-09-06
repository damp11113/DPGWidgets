import dearpygui.dearpygui as dpg
import math

class BezierWidget:
    def __init__(self, canvas_id):
        self.canvas_size = 256
        self.smoothness = 64
        self.curve_width = 4
        self.line_width = 1
        self.grab_radius = 8
        self.grab_border = 2
        self.dragging = False
        self.dragging_point = -1

        self.canvas_id = canvas_id

        # Bezier coefficients lookup table
        self._bezier_table = {}
        self.current_bezier = [0.0, 0.0, 0.0, 0.0]

    def _get_bezier_table(self, steps):
        """Get precomputed bezier coefficients for given steps"""
        if steps not in self._bezier_table:
            coeffs = []
            for step in range(steps + 1):
                t = step / steps
                coeffs.extend([
                    (1 - t) ** 3,  # * P0
                    3 * (1 - t) ** 2 * t,  # * P1
                    3 * (1 - t) * t ** 2,  # * P2
                    t ** 3  # * P3
                ])
            self._bezier_table[steps] = coeffs
        return self._bezier_table[steps]

    def bezier_value(self, dt01):
        """Get Y value for given X input (dt01) on bezier curve defined by P[4]"""
        steps = 256
        Q = [(0, 0), (self.current_bezier[0], self.current_bezier[1]), (self.current_bezier[2], self.current_bezier[3]),
             (1, 1)]
        results = self._compute_bezier_points(Q, steps)

        # Clamp dt01 to [0, 1] range
        dt01 = max(0, min(1, dt01))
        index = int(dt01 * steps)
        return results[index][1]

    def _compute_bezier_points(self, control_points, steps):
        """Compute bezier curve points"""
        coeffs = self._get_bezier_table(steps)
        results = []

        for step in range(steps + 1):
            base_idx = step * 4
            x = (coeffs[base_idx] * control_points[0][0] +
                 coeffs[base_idx + 1] * control_points[1][0] +
                 coeffs[base_idx + 2] * control_points[2][0] +
                 coeffs[base_idx + 3] * control_points[3][0])
            y = (coeffs[base_idx] * control_points[0][1] +
                 coeffs[base_idx + 1] * control_points[1][1] +
                 coeffs[base_idx + 2] * control_points[2][1] +
                 coeffs[base_idx + 3] * control_points[3][1])
            results.append((x, y))

        return results

    def _canvas_to_screen(self, x, y, canvas_pos):
        """Convert normalized canvas coordinates to screen coordinates"""
        # Canvas coordinates: (0,0) = bottom-left, (1,1) = top-right
        # Screen coordinates: canvas_pos = top-left of canvas
        screen_x = canvas_pos[0] + x * self.canvas_size
        screen_y = canvas_pos[1] + (1 - y) * self.canvas_size  # Flip Y for screen coords
        return (screen_x, screen_y)

    def _screen_to_canvas(self, screen_x, screen_y, canvas_pos):
        """Convert screen coordinates to normalized canvas coordinates"""
        # Convert back from screen to canvas coordinates
        x = (screen_x - canvas_pos[0]) / self.canvas_size
        y = 1 - (screen_y - canvas_pos[1]) / self.canvas_size  # Flip Y back
        return max(0, min(1, x)), max(0, min(1, y))

    def draw_bezier(self):
        """Draw the bezier curve widget"""
        # Clear previous drawings
        dpg.delete_item(self.canvas_id, children_only=True)
        canvas_pos = dpg.get_item_pos(self.canvas_id)

        # Draw background grid
        grid_color = [100, 100, 100, 255]
        for i in range(0, self.canvas_size + 1, self.canvas_size // 4):
            # Vertical lines
            dpg.draw_line(parent=self.canvas_id,
                          p1=[canvas_pos[0] + i, canvas_pos[1]],
                          p2=[canvas_pos[0] + i, canvas_pos[1] + self.canvas_size],
                          color=grid_color, thickness=1)
            # Horizontal lines
            dpg.draw_line(parent=self.canvas_id,
                          p1=[canvas_pos[0], canvas_pos[1] + i],
                          p2=[canvas_pos[0] + self.canvas_size, canvas_pos[1] + i],
                          color=grid_color, thickness=1)

        # Compute bezier curve points
        control_points = [(0, 0), (self.current_bezier[0], self.current_bezier[1]),
                          (self.current_bezier[2], self.current_bezier[3]), (1, 1)]
        curve_points = self._compute_bezier_points(control_points, self.smoothness)

        # Draw curve
        curve_color = [255, 255, 0, 255]  # Yellow
        for i in range(len(curve_points) - 1):
            p1 = self._canvas_to_screen(curve_points[i][0], curve_points[i][1], canvas_pos)
            p2 = self._canvas_to_screen(curve_points[i + 1][0], curve_points[i + 1][1], canvas_pos)
            dpg.draw_line(parent=self.canvas_id, p1=p1, p2=p2,
                          color=curve_color, thickness=self.curve_width)

        # Draw control lines and points
        white = [255, 255, 255, 255]
        pink = [255, 0, 191, 255]
        cyan = [0, 191, 255, 255]

        # Control point positions
        p1_screen = self._canvas_to_screen(self.current_bezier[0], self.current_bezier[1], canvas_pos)
        p2_screen = self._canvas_to_screen(self.current_bezier[2], self.current_bezier[3], canvas_pos)

        # Start and end points
        start_screen = self._canvas_to_screen(0, 0, canvas_pos)
        end_screen = self._canvas_to_screen(1, 1, canvas_pos)

        # Draw control lines
        dpg.draw_line(parent=self.canvas_id, p1=start_screen, p2=p1_screen,
                      color=white, thickness=self.line_width)
        dpg.draw_line(parent=self.canvas_id, p1=end_screen, p2=p2_screen,
                      color=white, thickness=self.line_width)

        # Draw control points (circles)
        dpg.draw_circle(parent=self.canvas_id, center=p1_screen, radius=self.grab_radius,
                        color=white, fill=white, thickness=0)
        dpg.draw_circle(parent=self.canvas_id, center=p1_screen, radius=self.grab_radius - self.grab_border,
                        color=pink, fill=pink, thickness=0)

        dpg.draw_circle(parent=self.canvas_id, center=p2_screen, radius=self.grab_radius,
                        color=white, fill=white, thickness=0)
        dpg.draw_circle(parent=self.canvas_id, center=p2_screen, radius=self.grab_radius - self.grab_border,
                        color=cyan, fill=cyan, thickness=0)

    def mouse_handle(self, type):
        """
        type: click, release, move
        """
        if type == "click":
            if dpg.is_item_hovered(self.canvas_id):
                mouse_pos_screen = dpg.get_mouse_pos()  # Mouse position in screen coords
                canvas_pos_screen = dpg.get_item_rect_min(self.canvas_id)  # Canvas top-left in screen coords

                # Convert control points to SCREEN coordinates
                p1_screen = self._canvas_to_screen(self.current_bezier[0], self.current_bezier[1],
                                                         canvas_pos_screen)
                p2_screen = self._canvas_to_screen(self.current_bezier[2], self.current_bezier[3],
                                                         canvas_pos_screen)
                # Calculate distances
                dist1 = math.sqrt((mouse_pos_screen[0] - p1_screen[0]) ** 2 + (mouse_pos_screen[1] - p1_screen[1]) ** 2)
                dist2 = math.sqrt((mouse_pos_screen[0] - p2_screen[0]) ** 2 + (mouse_pos_screen[1] - p2_screen[1]) ** 2)

                if dist1 <= self.grab_radius:
                    self.dragging = True
                    self.dragging_point = 0
                elif dist2 <= self.grab_radius:
                    self.dragging = True
                    self.dragging_point = 1

        elif type == "release":
            if self.dragging:
                self.dragging = False
                self.dragging_point = -1

        elif type == "move":
            if self.dragging and self.dragging_point >= 0:
                mouse_pos = dpg.get_mouse_pos()
                canvas_pos = dpg.get_item_rect_min(self.canvas_id)

                # Convert mouse position to canvas coordinates
                new_x, new_y = self._screen_to_canvas(mouse_pos[0], mouse_pos[1], canvas_pos)

                # Update the appropriate control point
                if self.dragging_point == 0:
                    self.current_bezier[0] = new_x
                    self.current_bezier[1] = new_y
                else:
                    self.current_bezier[2] = new_x
                    self.current_bezier[3] = new_y

                self.draw_bezier()