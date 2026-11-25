#version 330
// A glowing rune circle, drawn additively: two outer rings with a band of rune marks, and a sun
// inside (a small ring with rays of two lengths) that turns slowly. All from the polar position.
in vec2 v_uv;
in vec3 v_world;
out vec4 f_color;
uniform vec3 u_color;
uniform float u_strength;
uniform float u_rot;

float line(float d, float w) { return 1.0 - smoothstep(0.0, w, abs(d)); }

float rays(float r, float ang, float rot) {
    // 16 rays from the sun's ring outward, every other one shorter
    float n = 16.0;
    float s = (ang - rot) * n / 6.2831853;
    float k = floor(s + 0.5);
    float d = abs(s - k) * 6.2831853 / n * r;           // distance to the nearest ray, in uv units
    float len = mod(k, 2.0) < 0.5 ? 0.74 : 0.58;
    return line(d, 0.012) * step(0.36, r) * (1.0 - smoothstep(len - 0.04, len, r));
}

void main() {
    float r = length(v_uv);
    if (r > 1.0) discard;
    float ang = atan(v_uv.y, v_uv.x);
    float g = line(r - 0.95, 0.03) + 0.8 * line(r - 0.82, 0.018);
    g += 0.8 * line(r - 0.30, 0.016) + 0.75 * rays(r, ang, u_rot);
    // runes: short marks of three lengths in the band between the rings, turning the other way
    float seg = fract((ang - u_rot * 0.7) * 24.0 / 6.2831853);
    float band = step(0.845, r) * step(r, 0.925);
    float tall = step(0.42, seg) * step(seg, 0.52);
    float small = step(0.1, seg) * step(seg, 0.18) * step(r, 0.885);
    float wide = step(0.7, seg) * step(seg, 0.9) * step(0.87, r) * step(r, 0.895);
    g += 0.65 * band * (tall + small + wide);
    g += 0.18 * (1.0 - r);                                // soft light pooled in the middle
    f_color = vec4(u_color * g * u_strength, 1.0);
}
