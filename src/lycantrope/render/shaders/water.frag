#version 330
#include "common.glsl"
in vec3 v_world;
out vec4 f_color;
uniform sampler2D u_height;
uniform float u_world_size;
uniform vec3 u_cam;
uniform float u_time;

void main() {
    vec2 uv = (v_world.xz + 0.5 * u_world_size) / u_world_size;
    float depth = v_world.y - texture(u_height, uv).r;
    if (depth <= 0.0) discard;
    vec2 p = v_world.xz;
    float t = u_time;
    vec3 n = normalize(vec3(
        0.05 * sin(p.x * 0.35 + t * 1.3) + 0.03 * sin((p.x + p.y) * 0.9 - t * 1.7),
        1.0,
        0.05 * cos(p.y * 0.40 + t * 1.1) + 0.03 * cos((p.x - p.y) * 0.8 + t * 2.0)));
    vec3 v = normalize(u_cam - v_world);
    float fres = 0.02 + 0.98 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
    vec3 refl = sky_color(reflect(-v, n));
    vec3 body = mix(vec3(0.10, 0.15, 0.10), vec3(0.02, 0.05, 0.05), clamp(depth / 3.0, 0.0, 1.0));
    body *= u_sun_color * max(u_sun_dir.y, 0.0) * 0.6 + u_ambient_sky;
    vec3 col = mix(body, refl, fres);
    col += u_sun_color * pow(max(dot(reflect(-u_sun_dir, n), v), 0.0), 180.0) * 1.5;
    col = apply_fog(col, u_cam, v_world);
    float alpha = max(clamp(0.45 + depth * 0.35, 0.0, 0.93), fres);
    alpha *= smoothstep(0.0, 0.15, depth);               // soft shoreline
    f_color = vec4(tonemap(col), alpha);
}
