#version 330
#include "common.glsl"

in vec3 v_world;
in vec3 v_nrm;
in vec2 v_uv;
in vec3 v_color;
out vec4 f_color;

uniform vec3 u_cam;
uniform sampler2D u_tex;
uniform int u_has_tex;
uniform vec3 u_tint;           // per-character colour variation (1 = as modelled)
uniform int u_flat_shade;      // 1: face normals (low-poly look); 0: smooth vertex normals

void main() {
    vec3 v = normalize(u_cam - v_world);
    vec3 n = u_flat_shade == 1
        ? normalize(cross(dFdx(v_world), dFdy(v_world)))
        : normalize(v_nrm);
    if (dot(n, v) < 0.0) n = -n;

    vec3 albedo = v_color;
    if (u_has_tex == 1) albedo *= texture(u_tex, v_uv).rgb;
    albedo *= u_tint;
    albedo = pow(albedo, vec3(2.2));                   // sRGB -> linear

    float ndl = max(dot(n, u_sun_dir), 0.0);
    vec3 ambient = mix(u_ambient_ground, u_ambient_sky, n.y * 0.5 + 0.5);
    float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.25;   // helps characters read against grass
    vec3 col = albedo * (u_sun_color * ndl + ambient * 1.1) + u_ambient_sky * rim;
    col = apply_fog(col, u_cam, v_world);
    f_color = vec4(tonemap(col), 1.0);
}
