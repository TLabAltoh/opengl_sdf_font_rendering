#version 450

layout(location = 0)in vec2 uv;

layout(location = 0)out vec4 out_color;

layout(std430, binding = 0)readonly buffer SEG_SPLINES {
    vec2 splines[];
};

layout(std430, binding = 1)readonly buffer SEG_LINES {
    vec2 lines[];
};

struct segment {
    int line_s;
    int line_e;
    int spline_s;
    int spline_e;
};

layout(std430, binding = 2)readonly buffer SEG_INDEX {
    segment segments[];
};

uniform int segment_num;
uniform vec4 bounds;
uniform vec4 radius;
uniform vec3 text_color;
uniform vec3 speech_box_color;

float sdRoundedBox(in vec2 p, in vec2 b, in vec4 r) {
    r.xy = (p.x > 0.0) ? r.xy : r.zw;
    r.x = (p.y > 0.0) ? r.x : r.y;
    vec2 q = abs(p) - b + r.x;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r.x;
}

float dot2(vec2 v) {
    return dot(v, v);
}

float cro(vec2 a, vec2 b) {
    return a.x * b.y - a.y * b.x;
}

float udSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p-a;
    vec2 ba = b-a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C) {
    vec2 a = B-A;
    vec2 b = A-2.0 * B+C;
    vec2 c = a*2.0;
    vec2 d = A-pos;
    
    float kk = 1.0 / dot(b, b);
    float kx = kk * dot(a, b);
    float ky = kk * (2.0 * dot(a, a) + dot(d, b)) / 3.0;
    float kz = kk * dot(d, a);
    
    float res = 0.0;
    float sgn = 0.0;
    
    float p = ky - kx * kx;
    float q = kx * (2.0 * kx * kx - 3.0 * ky) + kz;
    float p3 = p*p * p;
    float q2 = q*q;
    float h = q2 + 4.0 * p3;
    
    if (h >= 0.0) {// 1 root
        h = sqrt(h);
        vec2 x = (vec2(h, - h) - q) / 2.0;
        
        if (abs(abs(h / q) - 1.0) < 0.0001) {
            float k = (1.0 - p3 / q2) * p3 / q; // quadratic approx
            x = vec2(k, - k-q);
        }
        
        vec2 uv = sign(x) * pow(abs(x), vec2(1.0 / 3.0, 1.0 / 3.0));
        float t = clamp(uv.x + uv.y - kx, 0.0, 1.0);
        vec2 q = d+(c + b*t) * t;
        res = dot2(q);
        sgn = cro(c + 2.0 * b*t, q);
    }
    else {// 3 roots
        float z = sqrt(-p);
        float v = acos(q / (p * z*2.0)) / 3.0;
        float m = cos(v);
        float n = sin(v) * 1.732050808;
        vec3 t = clamp(vec3(m + m, - n-m, n - m) * z-kx, 0.0, 1.0);
        vec2 qx = d+(c + b*t.x) * t.x;
        float dx = dot2(qx), sx = cro(c + 2.0 * b*t.x, qx);
        vec2 qy = d+(c + b*t.y) * t.y;
        float dy = dot2(qy);
        float sy = cro(c + 2.0 * b*t.y, qy);
        if (dx < dy) {
            res = dx;
            sgn = sx;
        }
        else {
            res = dy;
            sgn = sy;
        }
    }
    
    return sqrt(res) * sign(sgn);
}

float windingSign(vec2 p, vec2 a, vec2 b) {
    vec2 e = b-a;
    vec2 w = p-a;
    
    bvec3 cond = bvec3(
    p.y >= a.y, p.y < b.y, e.x * w.y > e.y * w.x);
    if (all(cond)||all(!cond)) {
        return - 1.0;
    }
    else {
        return 1.0;
    }
}

void main() {
    float text_dist = (bounds.w - bounds.y) + (bounds.z - bounds.x), tmp, winding = 1.0;
    int idx, seg_idx;
    
    vec2 bounds_size = vec2(bounds.z - bounds.x, bounds.w - bounds.y);
    
    vec2 text_sampling_pos;
    text_sampling_pos.x = (1.0 - uv.x) * bounds.x + uv.x * bounds.z;
    text_sampling_pos.y = (1.0 - uv.y) * bounds.y + uv.y * bounds.w;
    
    for(seg_idx = 0; seg_idx < segment_num; seg_idx ++ ) {
        segment seg = segments[seg_idx];
        for(idx = seg.spline_s; idx < seg.spline_e; idx += 3) {
            vec2 v0 = splines[idx + 0];
            vec2 v1 = splines[idx + 1];
            vec2 v2 = splines[idx + 2];
            
            if (cro(v1 - v2, v1 - v0) == 0.0) {
                tmp = udSegment(text_sampling_pos, v0, v2);
                winding *= windingSign(text_sampling_pos, v0, v2);
            } else {
                tmp = sdBezier(text_sampling_pos, v0, v1, v2);
                if ((tmp > 0.0) == (cro(v1 - v2, v1 - v0) < 0.0)) {
                    winding *= windingSign(text_sampling_pos, v0, v1);
                    winding *= windingSign(text_sampling_pos, v1, v2);
                }
                else {
                    winding *= windingSign(text_sampling_pos, v0, v2);
                }
            }
            
            text_dist = min(text_dist, abs(tmp));
        }
        
        for(idx = seg.line_s; idx < seg.line_e; idx += 2) {
            vec2 v0 = lines[idx + 0];
            vec2 v1 = lines[idx + 1];
            
            tmp = udSegment(text_sampling_pos, v0, v1);
            
            winding *= windingSign(text_sampling_pos, v0, v1);
            
            text_dist = min(text_dist, abs(tmp));
        }
    }
    
    #define BLUR 0
    #define EXPAND 0
    
    text_dist *= winding;
    float text_delta = fwidth(text_dist) * 0.5;
    float text_alpha = 1-smoothstep(-text_delta + EXPAND - BLUR, text_delta + EXPAND, text_dist);
    vec4 out_text_color = vec4(text_color, 1) * text_alpha;
    
    vec2 speech_box_sampling_pos = (uv - 0.5) * bounds_size;
    float speech_box_dist = sdRoundedBox(speech_box_sampling_pos, bounds_size * 0.5, radius);
    float speech_box_delta = fwidth(speech_box_dist) * 0.5;
    float speech_box_alpha = 1-smoothstep(-speech_box_delta, speech_box_delta, speech_box_dist);
    vec4 out_speech_box_color = vec4(speech_box_color, 1) * speech_box_alpha * (1.0 - text_alpha);
    
    out_color = out_text_color + out_speech_box_color;
}
