from glTextBox import glTextBox
from OpenGL.GL import *
from utils.glfw import deinit_glfw, init_glfw
import matplotlib.pyplot as plt
import numpy as np
import sys
import glfw


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


def deinit_gl():
    glDeleteVertexArrays(1, [vao])
    glDeleteBuffers(1, [vbo])
    deinit_glfw()


def main():
    print("font_path:", sys.argv[1], "text:", sys.argv[2], "font_size:", sys.argv[3])

    ""
    init_gl((10, 10))
    gl_text_box = glTextBox(
        window,
        vao,
        sys.argv[1],
        sys.argv[3],
        sys.argv[2],
        # text_outline_color=(0, 1, 0, 1),
        # text_outline_width=25,
        speech_box_margin=(10, 0, 10, 0),
        # speech_box_color=(1, 0, 1, 1),
        # speech_box_outline_color=(0, 0, 1, 1),
        # speech_box_outline_width=25,
        speech_box_radius=(20, 20, 20, 20),
    )
    plt.show()
    glfw.show_window(window)
    while glfw.window_should_close(window) == glfw.FALSE:
        gl_text_box.preview()
        glfw.wait_events()
    deinit_gl()
    ""


if __name__ == "__main__":
    main()
