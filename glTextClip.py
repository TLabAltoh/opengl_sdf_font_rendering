from OpenGL.GL import *
from utils.shader import *
from utils.glfw import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.cu2qu.ufo import *
from fontTools.cu2qu.cu2qu import *
from fontTools.pens.basePen import *
from fontTools.pens.boundsPen import *
from fontTools.pens.recordingPen import *
import matplotlib.pyplot as plt
import numpy as np
import os
import glfw


class glTextClip:
    def get_glyph(self, font: TTFont, char: str):
        glyph_set = font.getGlyphSet()
        cmap = font.getBestCmap()
        glyph_name = cmap[ord(char)]
        return glyph_set[glyph_name]

    def plot(self):
        if len(self.points) > 0:
            x, y = np.array(self.points).transpose() * self.font_scale
            plt.plot(x, y, marker=".")
            self.points = self.points[-1:]

    def update_segment(self):

        plt.figure(figsize=(5, 5))
        plt.axes().set_aspect("equal")

        font = self.font
        text = self.text
        font_scale = self.font_scale
        total_bounds = [0, 0, 0, 0]

        font.getGlyphSet()
        hhea = font.tables["hhea"]
        line_width = 0
        line_height = hhea.ascent - hhea.descent + hhea.lineGap

        self.points = []
        self.splines = []
        self.lines = []
        self.segments = []
        prev_seg = [0, 0, 0, 0]
        offset = [0, 0]

        for char in text:

            # fmt: off
            if char == "\n":    # There are cases where the font does not contain "\n" in the glyphs.
                offset[0] = 0
                line_width = 0
                offset[1] -= line_height
                total_bounds[1] -= line_height
                continue
            # fmt: on

            glyph = self.get_glyph(font, char)
            # fmt: off
            print(
                "lsb:",         glyph.lsb,
                "tsb:",         glyph.tsb,
                "width:",       glyph.width,
                "height:",      glyph.height,
            )
            # fmt: on
            print()

            offset[0] = line_width
            line_width += glyph.width
            total_bounds[2] = max(line_width, total_bounds[2])

            recording_pen = RecordingPen()
            bounds_pen = BoundsPen(font.getGlyphSet())

            glyph.draw(recording_pen)
            glyph.draw(bounds_pen)

            bounds = bounds_pen.bounds
            print("bound:", bounds)

            for segment in recording_pen.value:
                segment_0 = segment[0]
                segment_1 = segment[1]
                print()
                print("segment[0]:", segment_0)
                print("segment[1]:", segment_1)

                if segment_0 == "closePath":
                    """"""
                    if self.points[len(self.points) - 1] != start_point:
                        self.points.append(
                            (start_point[0] + offset[0], start_point[1] + offset[1])
                        )
                        self.lines = self.lines + self.points
                        self.plot()
                    ""
                    prev_seg = [
                        prev_seg[1],
                        len(self.lines),
                        prev_seg[3],
                        len(self.splines),
                    ]
                    self.segments = self.segments + prev_seg
                    self.points.clear()

                if segment_0 == "moveTo":  # starting point
                    start_point = segment_1[0]
                    self.points.append(
                        (segment_1[0][0] + offset[0], segment_1[0][1] + offset[1])
                    )

                if segment_0 == "lineTo":
                    self.points.append(
                        (segment_1[0][0] + offset[0], segment_1[0][1] + offset[1])
                    )
                    self.lines = self.lines + self.points
                    self.plot()

                if segment_0 == "qCurveTo":
                    if len(segment_1) == 1:  # line
                        for p in segment_1:
                            self.points.append((p[0] + offset[0], p[1] + offset[1]))
                            self.lines = self.lines + self.points
                            self.plot()

                    if len(segment_1) >= 2:  # quadratic-bezier
                        decompose = decomposeQuadraticSegment(segment_1)
                        print("decompose:", decompose)
                        for d in decompose:
                            for p in d:
                                self.points.append((p[0] + offset[0], p[1] + offset[1]))
                            self.splines = self.splines + self.points
                            self.plot()

                if segment_0 == "curveTo":
                    if len(segment_1) == 1:  # line
                        for p in segment_1:
                            self.points.append((p[0] + offset[0], p[1] + offset[1]))
                            self.lines = self.lines + self.points
                            self.plot()

                    if len(segment_1) == 2:  # quadratic-bezier
                        for p in segment_1:
                            self.points.append((p[0] + offset[0], p[1] + offset[1]))
                            self.splines = self.splines + self.points
                            self.plot()

                    if len(segment_1) >= 3:  # cubic-bezier
                        decompose = decomposeSuperBezierSegment(segment_1)
                        print("decompose:", decompose)
                        cu = [
                            [
                                self.points[0][0] - offset[0],
                                self.points[0][1] - offset[1],
                            ]
                        ]
                        for d_c in decompose:
                            for p in d_c:
                                cu.append(p)
                            qus = curve_to_quadratic(cu, 0.1)  # 0.001 is default
                            qus = decomposeQuadraticSegment(qus[1::])
                            for d in qus:
                                for p in d:
                                    self.points.append(
                                        (p[0] + offset[0], p[1] + offset[1])
                                    )
                                self.splines = self.splines + self.points
                                self.plot()
                            cu.clear()

        print()
        print("splines:", self.splines)
        print()
        print("lines:", self.lines)
        print()
        print("segments:", self.segments)
        print()

        total_bounds[1] += hhea.descent
        total_bounds[3] += hhea.ascent
        self.total_bounds = total_bounds
        rect_size = (
            int((total_bounds[2] - total_bounds[0]) * font_scale),
            int((total_bounds[3] - total_bounds[1]) * font_scale),
        )
        self.rect_size = rect_size

    def update_text(self, font_size: int, text: str):
        font_scale = 16 / 1000 * float(font_size)
        self.font_size = font_size
        self.text = text
        self.font_scale = font_scale

    def update_font(self, font_path: str):
        font = TTFont(font_path)
        self.font = font
        self.font_path = font_path
        f_name, f_ext = os.path.splitext(font_path)
        removeOverlaps(self.font)

    def __init__(self, window, vao, font_path: str, font_size: int, text: str):
        print("font_path:", font_path, "font_size:", font_size, "text:", text)

        self.window = window
        self.vao = vao

        self.update_font(font_path)
        self.update_text(font_size, text)
        self.update_segment()

    def preview(self):
        glfw.set_window_size(self.window, self.rect_size[0], self.rect_size[1])
        ""
        if glfw.window_should_close(self.window) == glfw.FALSE:
            self.rendering()
            glfw.swap_buffers(self.window)
        ""

    def init_gl_shader(self):
        program = Shader()
        program.attach_shader("shaders/font.vert", GL_VERTEX_SHADER)
        program.attach_shader("shaders/font.frag", GL_FRAGMENT_SHADER)
        program.link()
        self.program = program

        self.id_bounds = glGetUniformLocation(program.handle, "bounds")
        self.id_segment_num = glGetUniformLocation(program.handle, "segment_num")
        self.buf_splines = glGenBuffers(1)
        self.buf_lines = glGenBuffers(1)
        self.buf_segments = glGenBuffers(1)

    def deinit_gl_shader(self):
        glDeleteBuffers(3, [self.buf_splines, self.buf_lines, self.buf_segments])
        glDeleteProgram(self.program.handle)

    def rendering(self):
        self.init_gl_shader()

        glClear(GL_COLOR_BUFFER_BIT)

        self.program.use()
        glViewport(0, 0, self.rect_size[0], self.rect_size[1])
        glUniform4f(
            self.id_bounds,
            self.total_bounds[0],
            self.total_bounds[1],
            self.total_bounds[2],
            self.total_bounds[3],
        )

        if len(self.splines) > 0:
            data = np.array(self.splines, dtype=GLfloat)
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buf_splines)
            glBufferData(
                GL_SHADER_STORAGE_BUFFER,
                data.itemsize * data.size,
                (GLfloat * data.size)(*data.reshape(data.size)),
                GL_STATIC_DRAW,
            )
            glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, self.buf_splines)

        if len(self.lines) > 0:
            data = np.array(self.lines, dtype=GLfloat)
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buf_lines)
            glBufferData(
                GL_SHADER_STORAGE_BUFFER,
                data.itemsize * data.size,
                (GLfloat * data.size)(*data.reshape(data.size)),
                GL_STATIC_DRAW,
            )
            glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, self.buf_lines)

        if len(self.segments) > 0:
            data = np.array(self.segments, dtype=GLint)
            glUniform1i(self.id_segment_num, len(self.segments))
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.buf_segments)
            glBufferData(
                GL_SHADER_STORAGE_BUFFER,
                data.itemsize * data.size,
                (GLint * data.size)(*data.reshape(data.size)),
                GL_STATIC_DRAW,
            )
            glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, self.buf_segments)
        else:
            glUniform1i(self.id_segment_num, 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_QUADS, 0, 4)
        glBindVertexArray(0)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)
        self.program.unuse()

        self.deinit_gl_shader()
