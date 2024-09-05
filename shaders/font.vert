#version 450

layout(location = 0)in vec2 vertex;
layout(location = 1)in vec2 uv;

layout(location = 0)out vec2 out_uv;

uniform bool map_pixels;

void main() {
	gl_Position = vec4(vertex, 0, 1);
	
	out_uv = map_pixels ? vec2(uv.x, 1.0 - uv.y) : uv;
}

