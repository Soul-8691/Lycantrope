#version 330
#include "common.glsl"
in vec3 v_world;
in float v_t;
in vec3 v_tint;
out vec4 f_color;
uniform vec3 u_cam;

void main() {
    // darker at the roots (self-shadowed), lighter toward the sunlit tips
    vec3 base = vec3(0.25, 0.40, 0.13), tip = vec3(0.50, 0.68, 0.25);
    vec3 albedo = pow(mix(base, tip, v_t) * v_tint, vec3(2.2));
    vec3 n = vec3(0.0, 1.0, 0.0);                       // lit like the ground it grows on
    float ndl = max(dot(n, u_sun_dir), 0.0);
    vec3 col = albedo * (u_sun_color * ndl * mix(0.55, 1.0, v_t) + u_ambient_sky * mix(0.6, 1.1, v_t));
    col = apply_fog(col, u_cam, v_world);
    f_color = vec4(tonemap(col), 1.0);
}
