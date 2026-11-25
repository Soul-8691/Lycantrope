#version 330
#include "common.glsl"
in vec3 v_world;
out vec4 f_color;
uniform sampler2D u_height;
uniform sampler2D u_water_tex;
uniform float u_world_size;
uniform vec3 u_cam;
uniform float u_time;

void main() {
    vec2 uv = (v_world.xz + 0.5 * u_world_size) / u_world_size;
    float depth = v_world.y - texture(u_height, uv).r;
    if (depth <= 0.0) discard;

    // rivers: the surface slopes downhill, so ripples drift that way (lakes and sea stay still)
    float t = 1.0 / float(textureSize(u_water_tex, 0).x);
    vec2 grad = vec2(texture(u_water_tex, uv + vec2(t, 0.0)).r - texture(u_water_tex, uv - vec2(t, 0.0)).r,
                     texture(u_water_tex, uv + vec2(0.0, t)).r - texture(u_water_tex, uv - vec2(0.0, t)).r);
    float slope = length(grad);
    vec2 flow = slope > 0.004 && slope < 3.0 ? -grad / slope : vec2(0.0);
    float speed = slope < 3.0 ? clamp(slope * 40.0, 0.0, 1.6) : 0.0;
    vec2 p = v_world.xz - flow * u_time * speed;

    // ripples fade with distance, otherwise the sine pattern reads as a checkerboard
    float near = smoothstep(260.0, 40.0, length(u_cam - v_world));
    vec2 q = mat2(0.8, -0.6, 0.6, 0.8) * p;
    vec3 n = normalize(vec3(
        near * (0.05 * sin(p.x * 0.35 + u_time * 1.3) + 0.03 * sin((q.x + q.y) * 0.9 - u_time * 1.7)),
        1.0,
        near * (0.05 * cos(p.y * 0.40 + u_time * 1.1) + 0.03 * cos((q.x - q.y) * 0.8 + u_time * 2.0))));
    vec3 v = normalize(u_cam - v_world);
    float fres = 0.02 + 0.98 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
    vec3 refl = sky_color(reflect(-v, n));
    vec3 body = mix(vec3(0.10, 0.15, 0.10), vec3(0.02, 0.05, 0.05), clamp(depth / 3.0, 0.0, 1.0));
    body *= u_sun_color * max(u_sun_dir.y, 0.0) * 0.6 + u_ambient_sky;
    vec3 col = mix(body, refl, fres);
    col += u_sun_color * pow(max(dot(reflect(-u_sun_dir, n), v), 0.0), 180.0) * 1.5;
    // a little white water where a river runs fast and shallow
    float foam = smoothstep(0.35, 1.2, speed) * smoothstep(1.2, 0.2, depth)
               * (0.5 + 0.5 * sin(dot(p, vec2(1.7, 2.3)) + u_time * 3.0));
    col = mix(col, u_sun_color * 0.35 + u_ambient_sky, foam * 0.35);
    col = apply_fog(col, u_cam, v_world);
    float alpha = max(clamp(0.45 + depth * 0.35, 0.0, 0.93), fres);
    alpha *= smoothstep(0.0, 0.15, depth);               // soft shoreline
    f_color = vec4(tonemap(col), alpha);
}
