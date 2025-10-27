import dearpygui.dearpygui as dpg

font_a02 = [
    [0, 127, 62, 28, 8],  # 16 -
    [8, 28, 62, 127, 0],  # 17 -
    [48, 80, 0, 48, 80],  # 18 -
    [80, 96, 0, 80, 96],  # 19 -
    [17, 51, 119, 51, 17],  # 20 -
    [68, 102, 119, 102, 68],  # 21 -
    [28, 62, 62, 62, 28],  # 22 -
    [4, 14, 21, 4, 124],  # 23 -
    [16, 32, 127, 32, 16],  # 24 -
    [4, 2, 127, 2, 4],  # 25 -
    [8, 8, 42, 28, 8],  # 26 -
    [8, 28, 42, 8, 8],  # 27 -
    [1, 17, 41, 69, 1],  # 28 -
    [1, 69, 41, 17, 1],  # 29 -
    [2, 14, 62, 14, 2],  # 30 -
    [32, 56, 62, 56, 32],  # 31 -
    [0, 0, 0, 0, 0],  # 32 -
    [0, 0, 121, 0, 0],  # 33 - !
    [0, 112, 0, 112, 0],  # 34 - "
    [20, 127, 20, 127, 20],  # 35 - #
    [18, 42, 127, 42, 36],  # 36 - $
    [98, 100, 8, 19, 35],  # 37 - %
    [54, 73, 85, 34, 5],  # 38 - &
    [0, 80, 96, 0, 0],  # 39 - '
    [0, 28, 34, 65, 0],  # 40 - (
    [0, 65, 34, 28, 0],  # 41 - )
    [20, 8, 62, 8, 20],  # 42 - *
    [8, 8, 62, 8, 8],  # 43 - +
    [0, 5, 6, 0, 0],  # 44 - ,
    [8, 8, 8, 8, 8],  # 45 - -
    [0, 3, 3, 0, 0],  # 46 - .
    [2, 4, 8, 16, 32],  # 47 - /
    [62, 69, 73, 81, 62],  # 48 - 0
    [0, 33, 127, 1, 0],  # 49 - 1
    [33, 67, 69, 73, 49],  # 50 - 2
    [66, 65, 81, 105, 70],  # 51 - 3
    [12, 20, 36, 127, 4],  # 52 - 4
    [114, 81, 81, 81, 78],  # 53 - 5
    [30, 41, 73, 73, 6],  # 54 - 6
    [64, 71, 72, 80, 96],  # 55 - 7
    [54, 73, 73, 73, 54],  # 56 - 8
    [48, 73, 73, 74, 60],  # 57 - 9
    [0, 54, 54, 0, 0],  # 58 - :
    [0, 53, 54, 0, 0],  # 59 - ;
    [8, 20, 34, 65, 0],  # 60 - <
    [20, 20, 20, 20, 20],  # 61 - =
    [0, 65, 34, 20, 8],  # 62 - >
    [32, 64, 69, 72, 48],  # 63 - ?
    [38, 73, 79, 65, 62],  # 64 - @
    [31, 36, 68, 36, 31],  # 65 - A
    [127, 73, 73, 73, 54],  # 66 - B
    [62, 65, 65, 65, 34],  # 67 - C
    [127, 65, 65, 34, 28],  # 68 - D
    [127, 73, 73, 73, 65],  # 69 - E
    [127, 72, 72, 72, 64],  # 70 - F
    [62, 65, 73, 73, 47],  # 71 - G
    [127, 8, 8, 8, 127],  # 72 - H
    [0, 65, 127, 65, 0],  # 73 - I
    [2, 65, 65, 126, 0],  # 74 - J
    [127, 8, 20, 34, 65],  # 75 - K
    [127, 1, 1, 1, 1],  # 76 - L
    [127, 32, 24, 32, 127],  # 77 - M
    [127, 16, 8, 4, 127],  # 78 - N
    [62, 65, 65, 65, 62],  # 79 - O
    [127, 72, 72, 72, 48],  # 80 - P
    [62, 65, 69, 66, 61],  # 81 - Q
    [127, 72, 76, 74, 49],  # 82 - R
    [49, 73, 73, 73, 70],  # 83 - S
    [64, 64, 127, 64, 64],  # 84 - T
    [126, 1, 1, 1, 126],  # 85 - U
    [124, 2, 1, 2, 124],  # 86 - V
    [126, 1, 14, 1, 126],  # 87 - W
    [99, 20, 8, 20, 99],  # 88 - X
    [112, 8, 7, 8, 112],  # 89 - Y
    [67, 69, 73, 81, 97],  # 90 - Z
    [0, 127, 65, 65, 0],  # 91 - [
    [32, 16, 8, 4, 2],  # 92 - fwd slash
    [0, 65, 65, 127, 0],  # 93 - ]
    [16, 32, 64, 32, 16],  # 94 - ^
    [1, 1, 1, 1, 1],  # 95 - _
    [0, 64, 32, 16, 0],  # 96 - `
    [2, 21, 21, 21, 15],  # 97 - a
    [127, 9, 17, 17, 14],  # 98 - b
    [14, 17, 17, 17, 2],  # 99 - c
    [14, 17, 17, 9, 127],  # 100 - d
    [14, 21, 21, 21, 12],  # 101 - e
    [8, 63, 72, 64, 32],  # 102 - f
    [24, 37, 37, 37, 62],  # 103 - g
    [127, 8, 16, 16, 15],  # 104 - h
    [0, 9, 95, 1, 0],  # 105 - i
    [2, 1, 17, 94, 0],  # 106 - j
    [127, 4, 10, 17, 0],  # 107 - k
    [1, 65, 127, 1, 1],  # 108 - l
    [31, 16, 12, 16, 15],  # 109 - m
    [31, 8, 16, 16, 15],  # 110 - n
    [14, 17, 17, 17, 14],  # 111 - o
    [31, 20, 20, 20, 8],  # 112 - p
    [8, 20, 20, 12, 31],  # 113 - q
    [31, 8, 16, 16, 8],  # 114 - r
    [9, 21, 21, 21, 2],  # 115 - s
    [16, 126, 17, 1, 2],  # 116 - t
    [30, 1, 1, 2, 31],  # 117 - u
    [28, 2, 1, 2, 28],  # 118 - v
    [30, 1, 6, 1, 30],  # 119 - w
    [17, 10, 4, 10, 17],  # 120 - x
    [24, 5, 5, 5, 30],  # 121 - y
    [17, 19, 21, 25, 17],  # 122 - z
    [0, 8, 54, 65, 0],  # 123 - {
    [0, 0, 127, 0, 0],  # 124 - |
    [0, 65, 54, 8, 0],  # 125 - }
    [4, 8, 8, 4, 8],  # 126 - ~
    [30, 34, 66, 34, 30],  # 127 -
    [127, 73, 73, 73, 102],  # 128 -
    [15, 148, 228, 132, 255],  # 129 -
    [119, 8, 127, 8, 119],  # 130 -
    [65, 65, 73, 73, 54],  # 131 -
    [127, 4, 8, 16, 127],  # 132 -
    [63, 132, 72, 144, 63],  # 133 -
    [2, 65, 126, 64, 127],  # 134 -
    [127, 64, 64, 64, 127],  # 135 -
    [113, 10, 4, 8, 112],  # 136 -
    [126, 2, 2, 2, 127],  # 137 -
    [112, 8, 8, 8, 127],  # 138 -
    [63, 1, 63, 1, 63],  # 139 -
    [126, 2, 126, 2, 127],  # 140 -
    [64, 127, 9, 9, 6],  # 141 -
    [127, 9, 6, 0, 127],  # 142 -
    [34, 73, 81, 73, 62],  # 143 -
    [14, 17, 9, 6, 25],  # 144 -
    [3, 3, 127, 32, 24],  # 145 -
    [127, 64, 64, 64, 96],  # 146 -
    [17, 30, 16, 31, 17],  # 147 -
    [99, 85, 73, 65, 65],  # 148 -
    [14, 17, 17, 30, 16],  # 149 -
    [6, 6, 252, 163, 127],  # 150 -
    [8, 16, 30, 17, 32],  # 151 -
    [4, 60, 126, 60, 4],  # 152 -
    [62, 73, 73, 73, 62],  # 153 -
    [29, 35, 32, 35, 29],  # 154 -
    [6, 41, 81, 73, 38],  # 155 -
    [12, 20, 8, 20, 24],  # 156 -
    [28, 62, 31, 62, 28],  # 157 -
    [10, 21, 21, 17, 2],  # 158 -
    [63, 64, 64, 64, 63],  # 159 -
    [127, 127, 0, 127, 127],  # 160 -
    [0, 0, 79, 0, 0],  # 161 - ¡
    [28, 34, 127, 34, 4],  # 162 - ¢
    [9, 62, 73, 65, 2],  # 163 - £
    [34, 28, 20, 28, 34],  # 164 - ¤
    [84, 52, 31, 52, 84],  # 165 - ¥
    [0, 0, 119, 0, 0],  # 166 - ¦
    [2, 41, 85, 74, 32],  # 167 - §
    [10, 9, 62, 72, 40],  # 168 - ¨
    [127, 65, 93, 73, 127],  # 169 - ©
    [9, 85, 85, 85, 61],  # 170 - ª
    [8, 20, 42, 20, 34],  # 171 - «
    [127, 8, 62, 65, 62],  # 172 - ¬
    [49, 74, 76, 72, 127],  # 173 - ­
    [127, 65, 83, 69, 127],  # 174 - ®
    [0, 48, 80, 0, 0],  # 175 - ¯
    [112, 136, 136, 112, 0],  # 176 - °
    [17, 17, 125, 17, 17],  # 177 - ±
    [72, 152, 168, 72, 0],  # 178 - ²
    [136, 168, 168, 80, 0],  # 179 - ³
    [254, 160, 164, 79, 5],  # 180 - ´
    [127, 4, 4, 8, 124],  # 181 - µ
    [48, 72, 72, 127, 127],  # 182 - ¶
    [0, 12, 12, 0, 0],  # 183 - ·
    [14, 17, 6, 17, 14],  # 184 - ¸
    [72, 248, 8, 0, 0],  # 185 - ¹
    [57, 69, 69, 69, 57],  # 186 - º
    [34, 20, 42, 20, 8],  # 187 - »
    [232, 22, 42, 95, 130],  # 188 - ¼
    [232, 16, 41, 83, 141],  # 189 - ½
    [168, 248, 6, 10, 31],  # 190 - ¾
    [6, 9, 81, 1, 2],  # 191 - ¿
    [15, 148, 100, 20, 15],  # 192 - À
    [15, 20, 100, 148, 15],  # 193 - Á
    [15, 84, 148, 84, 15],  # 194 - Â
    [79, 148, 148, 84, 143],  # 195 - Ã
    [15, 148, 36, 148, 15],  # 196 - Ä
    [15, 84, 164, 84, 15],  # 197 - Å
    [31, 36, 127, 73, 73],  # 198 - Æ
    [120, 132, 133, 135, 72],  # 199 - Ç
    [31, 149, 85, 21, 17],  # 200 - È
    [31, 21, 85, 149, 17],  # 201 - É
    [31, 85, 149, 85, 17],  # 202 - Ê
    [31, 85, 21, 85, 17],  # 203 - Ë
    [0, 145, 95, 17, 0],  # 204 - Ì
    [0, 17, 95, 145, 0],  # 205 - Í
    [0, 81, 159, 81, 0],  # 206 - Î
    [0, 81, 31, 81, 0],  # 207 - Ï
    [8, 127, 73, 65, 62],  # 208 - Ð
    [95, 136, 132, 66, 159],  # 209 - Ñ
    [30, 161, 97, 33, 30],  # 210 - Ò
    [30, 33, 97, 161, 30],  # 211 - Ó
    [14, 81, 145, 81, 14],  # 212 - Ô
    [78, 145, 145, 81, 142],  # 213 - Õ
    [30, 161, 33, 161, 30],  # 214 - Ö
    [34, 20, 8, 20, 34],  # 215 - ×
    [8, 85, 127, 85, 8],  # 216 - Ø
    [62, 129, 65, 1, 62],  # 217 - Ù
    [62, 1, 65, 129, 62],  # 218 - Ú
    [30, 65, 129, 65, 30],  # 219 - Û
    [62, 129, 1, 129, 62],  # 220 - Ü
    [32, 16, 79, 144, 32],  # 221 - Ý
    [129, 255, 37, 36, 24],  # 222 - Þ
    [1, 62, 73, 73, 54],  # 223 - ß
    [2, 149, 85, 21, 15],  # 224 - à
    [2, 21, 85, 149, 15],  # 225 - á
    [2, 85, 149, 85, 15],  # 226 - â
    [66, 149, 149, 85, 143],  # 227 - ã
    [2, 85, 21, 85, 15],  # 228 - ä
    [2, 85, 181, 85, 15],  # 229 - å
    [38, 41, 30, 41, 26],  # 230 - æ
    [24, 37, 39, 36, 8],  # 231 - ç
    [14, 149, 85, 21, 12],  # 232 - è
    [14, 21, 85, 149, 12],  # 233 - é
    [14, 85, 149, 85, 12],  # 234 - ê
    [14, 85, 21, 85, 12],  # 235 - ë
    [0, 137, 95, 1, 0],  # 236 - ì
    [0, 9, 95, 129, 0],  # 237 - í
    [0, 73, 159, 65, 0],  # 238 - î
    [0, 73, 31, 65, 0],  # 239 - ï
    [82, 37, 85, 13, 6],  # 240 - ð
    [95, 136, 144, 80, 143],  # 241 - ñ
    [14, 145, 81, 17, 14],  # 242 - ò
    [14, 17, 81, 145, 14],  # 243 - ó
    [6, 41, 73, 41, 6],  # 244 - ô
    [38, 73, 73, 41, 70],  # 245 - õ
    [14, 81, 17, 81, 14],  # 246 - ö
    [8, 8, 42, 8, 8],  # 247 - ÷
    [8, 21, 62, 84, 8],  # 248 - ø
    [30, 129, 65, 2, 31],  # 249 - ù
    [30, 1, 65, 130, 31],  # 250 - ú
    [30, 65, 129, 66, 31],  # 251 - û
    [30, 65, 1, 66, 31],  # 252 - ü
    [24, 5, 69, 133, 30],  # 253 - ý
    [0, 65, 127, 21, 8],  # 254 - þ
    [24, 69, 5, 69, 30],  # 255 - ÿ
]

class LCDWidget:
    # Constants
    LCD_CHAR_W = 5
    LCD_CHAR_H = 8
    LCD_PIXEL_SIZE_W = 1
    LCD_PIXEL_SIZE_H = 2
    LCD_PIXEL_SPACE_Y = 0
    LCD_PIXEL_SPACE_X = 0
    LCD_CHAR_PIXEL_SIZE_W = LCD_CHAR_W * (LCD_PIXEL_SIZE_W + LCD_PIXEL_SPACE_X) - LCD_PIXEL_SPACE_X
    LCD_CHAR_PIXEL_SIZE_H = LCD_CHAR_H * (LCD_PIXEL_SIZE_H + LCD_PIXEL_SPACE_Y) - LCD_PIXEL_SPACE_Y
    LCD_CHAR_SPACE_X = 0
    LCD_CHAR_SPACE_Y = 0
    LCD_BORDER_SIZE = 5
    ROM_FONT_CHARS = 255
    CGRAM_STORAGE_CHARS = 16

    def __init__(self, parent, width=400, height=150, tag=None):
        # Default parameters
        self.column = 16
        self.row = 2

        # Colors (RGB normalized to 0-255)
        self.color_background_1 = (21, 31, 255, 255)
        self.color_background_2 = (19, 10, 233, 255)
        self.color_pixel = (230, 230, 245, 255)

        # Character storage
        self.char_ram = [[0] * self.LCD_CHAR_W for _ in range(self.ROM_FONT_CHARS + self.CGRAM_STORAGE_CHARS)]

        # Cursor and display
        self.cursor_pos_x = 0
        self.cursor_pos_y = 0

        # Display buffer
        self.display_char_buffer = None

        # Drawing dimensions
        self.widget_width = width
        self.widget_height = height

        # Create the drawlist
        self.tag = tag if tag else dpg.generate_uuid()
        with dpg.drawlist(width=width, height=height, parent=parent, tag=self.tag):
            pass

        self.calculate_display_size()
        self.copy_char_rom_to_ram()
        self.home()
        self.render()

    def calculate_display_size(self):
        # Calculate display dimensions
        self.display_size_w = (2 * self.LCD_BORDER_SIZE +
                               (self.column - 1) * self.LCD_CHAR_SPACE_X +
                               self.column * self.LCD_CHAR_PIXEL_SIZE_W)
        self.display_size_h = (2 * self.LCD_BORDER_SIZE +
                               (self.row - 1) * self.LCD_CHAR_SPACE_Y +
                               self.row * self.LCD_CHAR_PIXEL_SIZE_H)

        # Initialize display char buffer
        self.display_char_buffer = [ord(' ')] * (self.column * self.row)

        # Calculate scale factors
        self.scale_x = self.widget_width / self.display_size_w
        self.scale_y = self.widget_height / self.display_size_h

    def render(self):
        # Clear the drawlist
        dpg.delete_item(self.tag, children_only=True)

        # Draw background
        dpg.draw_rectangle(
            (0, 0),
            (self.widget_width, self.widget_height),
            fill=self.color_background_1,
            parent=self.tag
        )

        # Draw each character
        for y in range(self.row):
            for x in range(self.column):
                char = self.display_char_buffer[y * self.column + x]
                char_x = (x * (self.LCD_CHAR_PIXEL_SIZE_W + self.LCD_CHAR_SPACE_X)) + self.LCD_BORDER_SIZE
                char_y = (y * (self.LCD_CHAR_PIXEL_SIZE_H + self.LCD_CHAR_SPACE_Y)) + self.LCD_BORDER_SIZE
                self.draw_char(char_x, char_y, char)

    def draw_char(self, x, y, c):
        # Ensure that c is within bounds
        if c >= len(self.char_ram):
            print(f"Invalid character index: {c}")
            return

        for c_pos in range(5):
            y2 = y
            for y1 in range(self.LCD_CHAR_H):
                # Ensure that char_ram[c] is a valid row
                if c_pos >= len(self.char_ram[c]):
                    print(f"Invalid column index: {c_pos} for character {c}")
                    return

                # Determine pixel color based on character ROM data
                col = (self.color_pixel if
                       (self.char_ram[c][c_pos] >> (self.LCD_CHAR_H - y1 - 1)) & 1
                       else self.color_background_2)

                # Draw pixel as a rectangle
                pixel_x = x + c_pos * (self.LCD_PIXEL_SIZE_W + self.LCD_PIXEL_SPACE_X)

                # Scale coordinates
                scaled_x1 = pixel_x * self.scale_x
                scaled_y1 = y2 * self.scale_y
                scaled_x2 = (pixel_x + self.LCD_PIXEL_SIZE_W) * self.scale_x
                scaled_y2 = (y2 + self.LCD_PIXEL_SIZE_H) * self.scale_y

                dpg.draw_rectangle(
                    (scaled_x1, scaled_y1),
                    (scaled_x2, scaled_y2),
                    fill=col,
                    parent=self.tag
                )

                y2 += self.LCD_PIXEL_SIZE_H

                # Add vertical spacing
                if self.LCD_PIXEL_SPACE_Y > 0:
                    scaled_y1 = y2 * self.scale_y
                    scaled_y2 = (y2 + self.LCD_PIXEL_SPACE_Y) * self.scale_y

                    dpg.draw_rectangle(
                        (scaled_x1, scaled_y1),
                        (scaled_x2, scaled_y2),
                        fill=self.color_background_1,
                        parent=self.tag
                    )

                    y2 += self.LCD_PIXEL_SPACE_Y

    def copy_char_rom_to_ram(self):
        # Copy font to char_ram
        for i in range(min(len(font_a02), self.ROM_FONT_CHARS)):
            for j in range(self.LCD_CHAR_W):
                self.char_ram[i + self.CGRAM_STORAGE_CHARS][j] = font_a02[i][j]

    def home(self):
        self.cursor_pos_x = 0
        self.cursor_pos_y = 0

    def clear(self):
        self.display_char_buffer = [ord(' ')] * (self.column * self.row)
        self.home()
        self.render()

    def string(self, text):
        for c in text:
            idx = ord(c)

            if idx >= self.ROM_FONT_CHARS + self.CGRAM_STORAGE_CHARS:
                print(f"Character {c} with index {idx} is out of range. Skipping.")
                idx = 0

            buffer_idx = self.cursor_pos_y * self.column + self.cursor_pos_x
            self.display_char_buffer[buffer_idx] = idx

            self.cursor_pos_x += 1
            if self.cursor_pos_x == self.column:
                self.cursor_pos_x = 0
                self.cursor_pos_y += 1
                if self.cursor_pos_y == self.row:
                    self.cursor_pos_y = 0

        self.render()

    def setCursorTo(self, x, y):
        """Sets the cursor position"""
        if 0 <= x < self.column and 0 <= y < self.row:
            self.cursor_pos_x = x
            self.cursor_pos_y = y
        else:
            print(f"Invalid cursor position: ({x}, {y})")

    def data(self, char):
        """Write data to the current cursor position"""
        if 0 <= self.cursor_pos_x < self.column and 0 <= self.cursor_pos_y < self.row:
            idx = self.cursor_pos_y * self.column + self.cursor_pos_x
            self.display_char_buffer[idx] = char
            self.render()

    def setColumn(self, column):
        """Set the number of columns"""
        self.column = column
        self.calculate_display_size()
        self.render()

    def setRow(self, row):
        """Set the number of rows"""
        self.row = row
        self.calculate_display_size()
        self.render()

    def getCurrentColumn(self):
        """Get the current number of columns"""
        return self.column

    def getCurrentRow(self):
        """Get the current number of rows"""
        return self.row

    def getDisplayCharBuffer(self):
        """Get the display character buffer"""
        return self.display_char_buffer

    def getDisplayCharBufferLength(self):
        """Get the length of the display character buffer"""
        return len(self.display_char_buffer)

    def setUserChar(self, index, char_data):
        """
        Set a custom character in the CGRAM.

        :param index: The index of the character (0-15 for CGRAM).
        :param char_data: A list of 5 bytes representing the character.
        """
        if 0 <= index < self.CGRAM_STORAGE_CHARS:
            if len(char_data) == 5:
                if all(0 <= byte <= 31 for byte in char_data):
                    self.char_ram[self.ROM_FONT_CHARS + index] = char_data
                    print(f"User character {index} set.")
                    self.render()
                else:
                    print("Invalid character data. Each byte must be between 0 and 31.")
            else:
                print("Character data must be a list of 5 bytes.")
        else:
            print(f"Invalid index for CGRAM: {index}. Should be 0-{self.CGRAM_STORAGE_CHARS - 1}.")


# Example usage
if __name__ == "__main__":
    dpg.create_context()

    with dpg.window(label="LCD Display", width=500, height=250):
        lcd = LCDWidget(dpg.last_item(), width=600, height=150)
        lcd.string("Hello World!")
        lcd.setCursorTo(0, 1)
        lcd.string("DearPyGUI LCD")

    dpg.create_viewport(title='LCD Widget Demo', width=520, height=300)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()