#version 330
#include "common.glsl"

in vec3 v_world;
in vec2 v_q;
in float v_shade;
flat in float v_rot;
flat in float v_view;

uniform sampler2D u_albedo;   // u_views side views in a row (impostor_bake.frag)
uniform sampler2D u_normal;
uniform float u_views;
uniform vec3 u_cam;
uniform float u_fade_from;    // dither the cut-out away between these distances
uniform float u_fade_to;
out vec4 f_color;

const float TAU = 6.28318531;

vec2 view_uv(float k) {
    return vec2((k + v_q.x * 0.5 + 0.5) / u_views, v_q.y);
}

vec3 view_to_world(vec4 raw, float k) {
    vec3 nv = raw.xyz / max(raw.a, 1e-3) * 2.0 - 1.0;      // undo the edge blend with the empty background
    float a = k * TAU / u_views;
    vec3 nm = vec3(cos(a), 0.0, -sin(a)) * nv.x + vec3(0.0, nv.y, 0.0) + vec3(sin(a), 0.0, cos(a)) * nv.z;
    float c = cos(v_rot), s = sin(v_rot);
    return mat3(c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c) * nm;
}

void main() {
    float t = fract(v_view / TAU) * u_views;
    float k0 = floor(t);
    float k1 = mod(k0 + 1.0, u_views);
    float w = t - k0;
    vec4 alb = mix(texture(u_albedo, view_uv(k0)), texture(u_albedo, view_uv(k1)), w);

    float fade = 1.0 - smoothstep(u_fade_from, u_fade_to, distance(u_cam, v_world));
    float noise = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
    if (alb.a < 0.5 || noise > fade) discard;

    vec3 n = normalize(mix(view_to_world(texture(u_normal, view_uv(k0)), k0),
                           view_to_world(texture(u_normal, view_uv(k1)), k1), w));
    vec3 albedo = pow(alb.rgb / alb.a, vec3(2.2)) * v_shade;

    float ao = mix(0.55, 1.0, smoothstep(0.0, 0.25, v_q.y));
    float ndl = max(dot(n, u_sun_dir), 0.0);
    vec3 ambient = mix(u_ambient_ground, u_ambient_sky, n.y * 0.5 + 0.5);
    vec3 col = albedo * (u_sun_color * ndl + ambient * ao);
    col = apply_fog(col, u_cam, v_world);
    f_color = vec4(tonemap(col), 1.0);
}
