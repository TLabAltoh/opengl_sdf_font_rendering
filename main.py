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
import sys
import os
import glfw
import ctypes


def init_gl(win_size):
    global window, vbo, vao
    window = init_glfw(win_size, "font_sdf")

    # fmt: off
    data = np.array(
        [
            -1,  1,  0,  1,
             1,  1,  1,  1,
             1, -1,  1,  0,
            -1, -1,  0,  0,
        ],
        dtype=GLfloat,
    )
    # fmt: on

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(
        GL_ARRAY_BUFFER,
        data.itemsize * data.size,
        (GLfloat * data.size)(*data),
        GL_STATIC_DRAW,
    )

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    glEnableVertexAttribArray(0)
    glEnableVertexAttribArray(1)
    glEnableVertexAttribArray(2)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, sizeof(GLfloat) * 4, GLvoidp(0))
    glVertexAttribPointer(
        1,
        2,
        GL_FLOAT,
        GL_FALSE,
        sizeof(GLfloat) * 4,
        GLvoidp(ctypes.sizeof(GLfloat) * 2),
    )

    glClearColor(0, 0, 0, 1)


def init_gl_font():
    program = Shader()
    program.attach_shader("shaders/font.vert", GL_VERTEX_SHADER)
    program.attach_shader("shaders/font.frag", GL_FRAGMENT_SHADER)
    program.link()

    id_bounds = glGetUniformLocation(program.handle, "bounds")
    id_segment_num = glGetUniformLocation(program.handle, "segment_num")
    buf_splines = glGenBuffers(1)
    buf_lines = glGenBuffers(1)
    buf_segments = glGenBuffers(1)
    return {
        "program": program,
        "id_bounds": id_bounds,
        "id_segment_num": id_segment_num,
        "buf_splines": buf_splines,
        "buf_lines": buf_lines,
        "buf_segments": buf_segments,
    }


def deinit_gl():
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(1, [vbo])
    deinit_glfw()


def rendering_gl_font(handle, size, bounds, segments, splines, lines):
    global font_scale
    glClear(GL_COLOR_BUFFER_BIT)

    handle["program"].use()
    glViewport(0, 0, size[0], size[1])
    glUniform4f(handle["id_bounds"], bounds[0], bounds[1], bounds[2], bounds[3])

    if len(splines) > 0:
        data = np.array(splines, dtype=GLfloat)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, handle["buf_splines"])
        glBufferData(
            GL_SHADER_STORAGE_BUFFER,
            data.itemsize * data.size,
            (GLfloat * data.size)(*data.reshape(data.size)),
            GL_STATIC_DRAW,
        )
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, handle["buf_splines"])

    if len(lines) > 0:
        data = np.array(lines, dtype=GLfloat)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, handle["buf_lines"])
        glBufferData(
            GL_SHADER_STORAGE_BUFFER,
            data.itemsize * data.size,
            (GLfloat * data.size)(*data.reshape(data.size)),
            GL_STATIC_DRAW,
        )
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, handle["buf_lines"])

    if len(segments) > 0:
        data = np.array(segments, dtype=GLint)
        glUniform1i(handle["id_segment_num"], len(segments))
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, handle["buf_segments"])
        glBufferData(
            GL_SHADER_STORAGE_BUFFER,
            data.itemsize * data.size,
            (GLint * data.size)(*data.reshape(data.size)),
            GL_STATIC_DRAW,
        )
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, handle["buf_segments"])
    else:
        glUniform1i(handle["id_segment_num"], 0)

    glBindVertexArray(vao)
    glDrawArrays(GL_QUADS, 0, 4)
    glBindVertexArray(0)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)
    handle["program"].unuse()


def deinit_gl_handle(handle):
    glDeleteBuffers(
        3, [handle["buf_splines"], handle["buf_lines"], handle["buf_segments"]]
    )
    glDeleteProgram(handle["program"].handle)


def get_glyph(glyph_set, cmap, char):
    glyph_name = cmap[ord(char)]
    return glyph_set[glyph_name]


def plot():
    global points, font_size
    if len(points) > 0:
        x, y = np.array(points).transpose() * font_scale
        plt.plot(x, y, marker='.')
        points = points[-1:]


def main():
    print("path:", sys.argv[1], "char:", sys.argv[2], "font_size:", sys.argv[3])

    path = sys.argv[1]
    font = TTFont(path)
    f_name, f_ext = os.path.splitext(path)
    if f_ext == ".ttf":
        removeOverlaps(font)

    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    recording_pen = RecordingPen()
    bounds_pen = BoundsPen(glyph_set)

    global font_size, font_scale
    font_size = int(sys.argv[3])
    font_scale = 16 / 1000 * font_size

    char = sys.argv[2]
    L = get_glyph(glyph_set, cmap, char)
    L.draw(recording_pen)
    L.draw(bounds_pen)

    bounds = bounds_pen.bounds
    rect_size = (
        int((bounds[2] - bounds[0]) * font_scale),
        int((bounds[3] - bounds[1]) * font_scale),
    )
    print("bound:", bounds, "rect_size:", rect_size, "lsb:", L.lsb, "tsb:", L.tsb, "width:", L.width, "height:", L.height)
    print()
    plt.figure(figsize=rect_size)
    plt.axes().set_aspect("equal")

    global points
    points = []
    splines = []
    lines = []
    prev_seg = [0, 0, 0, 0]
    segments = []
    for segment in recording_pen.value:
        segment_0 = segment[0]
        segment_1 = segment[1]
        print()
        print("segment[0]:", segment_0)
        print("segment[1]:", segment_1)

        if segment_0 == "closePath":
            ""
            if points[len(points) - 1] != start_point:
                points.append(start_point)
                lines = lines + points
                plot()
            ""
            prev_seg = [prev_seg[1], len(lines), prev_seg[3], len(splines)]
            segments = segments + prev_seg
            points.clear()

        if segment_0 == "moveTo":  # starting point
            start_point = segment_1[0]
            points.append(segment_1[0])

        if segment_0 == "lineTo":
            points.append(segment_1[0])
            lines = lines + points
            plot()

        if segment_0 == "qCurveTo":
            if len(segment_1) == 1:  # line
                for p in segment_1:
                    points.append(p)
                    lines = lines + points
                    plot()

            if len(segment_1) >= 2:  # quadratic-bezier
                decompose = decomposeQuadraticSegment(segment_1)
                print("decompose:", decompose)
                for d in decompose:
                    for p in d:
                        points.append(p)
                    splines = splines + points
                    plot()

        if segment_0 == "curveTo":
            if len(segment_1) == 1:  # line
                for p in segment_1:
                    points.append(p)
                    lines = lines + points
                    plot()

            if len(segment_1) == 2:  # quadratic-bezier
                for p in segment_1:
                    points.append(p)
                    splines = splines + points
                    plot()

            if len(segment_1) >= 3:  # cubic-bezier
                decompose = decomposeSuperBezierSegment(segment_1)
                print("decompose:", decompose)
                cu = [points[0]]
                for d_c in decompose:
                    for p in d_c:
                        cu.append(p)
                    qus = curve_to_quadratic(cu, 0.1)  # 0.001 is default
                    qus = decomposeQuadraticSegment(qus[1::])
                    for d in qus:
                        for p in d:
                            points.append(p)
                        splines = splines + points
                        plot()
                    cu.clear()

    print()
    print("splines:", splines)
    print()
    print("lines:", lines)
    print()
    print("segments:", segments)
    print()
    plt.show()

    ""
    init_gl(rect_size)
    handle = init_gl_font()
    while glfw.window_should_close(window) == glfw.FALSE:
        rendering_gl_font(handle, rect_size, bounds, segments, splines, lines)
        glfw.swap_buffers(window)
        glfw.wait_events()
    deinit_gl_handle(handle)
    deinit_gl()
    ""


if __name__ == "__main__":
    main()
