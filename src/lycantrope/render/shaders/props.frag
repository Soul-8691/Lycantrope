#version 330
#include "common.glsl"

in vec3 v_world;
in vec3 v_nrm;
in float v_rel_h;
in float v_shade;
in vec2 v_uv;
uniform sampler2D u_tex;
uniform int u_has_tex;       // 1: use the Meshy texture instead of the flat colours
out vec4 f_color;

uniform vec3 u_cam;
uniform vec3 u_color;        // linear
uniform vec3 u_top_color;    // linear, used above u_top_from
uniform float u_top_from;    // fraction of the model height
uniform int u_flat_shade;    // 1: face normals (low-poly look); 0: smooth vertex normals

void main() {
    vec3 v = normalize(u_cam - v_world);
    vec3 n = u_flat_shade == 1
        ? normalize(cross(dFdx(v_world), dFdy(v_world)))
        : normalize(v_nrm);
    if (dot(n, v) < 0.0) n = -n;

    float top = smoothstep(u_top_from - 0.04, u_top_from + 0.04, v_rel_h);
    vec3 albedo = mix(u_color, u_top_color, top) * v_shade;
    if (u_has_tex == 1) albedo = pow(texture(u_tex, v_uv).rgb, vec3(2.2)) * v_shade;

    float ao = mix(0.55, 1.0, smoothstep(0.0, 0.25, v_rel_h));     // darker near the ground
    float ndl = max(dot(n, u_sun_dir), 0.0);
    vec3 ambient = mix(u_ambient_ground, u_ambient_sky, n.y * 0.5 + 0.5);
    vec3 col = albedo * (u_sun_color * ndl + ambient * ao);
    col = apply_fog(col, u_cam, v_world);
    f_color = vec4(tonemap(col), 1.0);
}
