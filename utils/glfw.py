import glfw


def init_glfw(wsize, wname):
    if not glfw.init():
        raise RuntimeError("failed to initialize GLFW")

    glfw.window_hint(glfw.VISIBLE, False)
    window = glfw.create_window(wsize[0], wsize[1], wname, None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("failed to create GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
    glfw.make_context_current(window)

    return window


def deinit_glfw():
    glfw.terminate()
