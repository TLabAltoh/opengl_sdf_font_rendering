from OpenGL.GL import *
import ctypes
import sys

class Shader:
    def __init__(self):
        self.handle = glCreateProgram()


    def attach_shader(self, path, type):
        shader = glCreateShader(type)

        with open(path) as content:
            glShaderSource(shader, content)
            glCompileShader(shader)

            status = ctypes.c_uint(GL_UNSIGNED_INT)
            glGetShaderiv(shader, GL_COMPILE_STATUS, status)
            if not status:
                print(glGetShaderInfoLog(shader).decode('utf-8'), file=sys.stderr)
                glDeleteShader(shader)
                return False

            glAttachShader(self.handle, shader)
            glDeleteShader(shader)
            return True

        print('[error] file is not found: ', path)
        return False

    def link(self):
        glLinkProgram(self.handle)
        status = ctypes.c_uint(GL_UNSIGNED_INT)
        glGetProgramiv(self.handle, GL_LINK_STATUS, status)
        if not status:
            print(glGetProgramInfoLog(self.handle).decode('utf-8'), file=sys.stderr)
            return False

        return True

    def use(self):
        glUseProgram(self.handle)

    def unuse(self):
        glUseProgram(0)
