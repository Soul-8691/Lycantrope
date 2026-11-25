#version 330
#include "common.glsl"

in vec3 v_world;
out vec4 f_color;

uniform sampler2D u_height;
uniform sampler2D u_splat_a;
uniform sampler2D u_splat_b;
uniform sampler2D u_road;
uniform sampler2D u_water_tex;           // water surface height (sea, lakes, rivers)
uniform sampler2D u_patch_a;             // baked at load: rgb meadow tint / 2, a bare dirt
uniform sampler2D u_patch_b;             // baked at load: rgb soil tint / 2, a tall grass
uniform sampler2DArray u_ground;     // RGB albedo (sRGB), A = height for blending
uniform float u_world_size;
uniform float u_mpp;
uniform vec3 u_cam;
uniform float u_water;
uniform float u_snowline;
uniform float u_tile[8];
uniform int u_splat_layer[8];        // splat channel -> material layer (-1 = unused)
uniform int u_rock_layer;
uniform int u_road_layer;
uniform int u_snow_layer;
uniform int u_mud_layer;
uniform int u_debug_view;            // 0 normal, 1 normals, 2 rock/road/snow weights

float H(vec2 uv) { return texture(u_height, uv).r; }

vec4 planar(int layer, vec2 xz) {
    // two scales, the second one rotated, so the repeat doesn't show as a grid
    vec2 uv = xz / u_tile[layer];
    vec4 a = texture(u_ground, vec3(uv, float(layer)));
    vec2 r = mat2(0.8, -0.6, 0.6, 0.8) * uv * 0.31 + vec2(0.37, 0.71);
    vec4 b = texture(u_ground, vec3(r, float(layer)));
    return mix(a, b, 0.45);
}

vec4 triplanar(int layer, vec3 p, vec3 n) {
    vec3 w = pow(abs(n), vec3(4.0));
    w /= (w.x + w.y + w.z);
    float t = u_tile[layer];
    vec4 near = texture(u_ground, vec3(p.zy / t, float(layer))) * w.x
              + texture(u_ground, vec3(p.xz / t, float(layer))) * w.y
              + texture(u_ground, vec3(p.xy / t, float(layer))) * w.z;
    float T = t * 3.3;                                   // a second, larger scale against repetition
    vec4 far = texture(u_ground, vec3(p.zy / T + 0.3, float(layer))) * w.x
             + texture(u_ground, vec3(p.xz / T + 0.6, float(layer))) * w.y
             + texture(u_ground, vec3(p.xy / T + 0.1, float(layer))) * w.z;
    return mix(near, far, 0.5);
}

void main() {
    vec2 uv = (v_world.xz + 0.5 * u_world_size) / u_world_size;
    float t = 1.0 / float(textureSize(u_height, 0).x);
    float hl = H(uv - vec2(t, 0.0)), hr = H(uv + vec2(t, 0.0));
    float hd = H(uv - vec2(0.0, t)), hu = H(uv + vec2(0.0, t));
    vec3 n = normalize(vec3(hl - hr, 2.0 * u_mpp, hd - hu));

    // material weights: biome splat, then snow, steep rock, road, underwater
    float w[8];
    for (int i = 0; i < 8; i++) w[i] = 0.0;
    vec4 sa = texture(u_splat_a, uv);
    vec4 sb = texture(u_splat_b, uv);
    float sp[8] = float[8](sa.r, sa.g, sa.b, sa.a, sb.r, sb.g, sb.b, sb.a);
    for (int i = 0; i < 8; i++) {
        int L = u_splat_layer[i];
        if (L >= 0) w[L] += sp[i];
    }
    float macro = texture(u_ground, vec3(v_world.xz / 157.0, float(u_rock_layer))).g;
    float snow = smoothstep(u_snowline, u_snowline + 40.0, v_world.y + macro * 30.0) * smoothstep(0.70, 0.85, n.y);
    float rock = smoothstep(0.86, 0.72, n.y);
    float road = texture(u_road, uv).r * (1.0 - rock * 0.6);
    float wl = texture(u_water_tex, uv).r;
    float wet = smoothstep(wl + 0.6, wl - 0.4, v_world.y);
    for (int i = 0; i < 8; i++) w[i] *= (1.0 - snow);
    w[u_snow_layer] += snow;
    for (int i = 0; i < 8; i++) w[i] *= (1.0 - rock);
    w[u_rock_layer] += rock;
    for (int i = 0; i < 8; i++) w[i] *= (1.0 - road);
    w[u_road_layer] += road;
    // bare dirt patches on open ground (the mud layer, tinted per patch below)
    vec4 pa = texture(u_patch_a, uv), pb = texture(u_patch_b, uv);
    float bare = pa.a * (1.0 - rock) * (1.0 - snow) * (1.0 - road);
    for (int i = 0; i < 8; i++) w[i] *= (1.0 - bare);
    w[u_mud_layer] += bare;
    for (int i = 0; i < 8; i++) w[i] *= (1.0 - wet);
    w[u_mud_layer] += wet;

    // height-based blending: the taller texture wins where materials meet
    vec4 smp[8];
    float best = -1.0;
    for (int i = 0; i < 8; i++) {
        smp[i] = vec4(0.0);
        if (w[i] > 0.01) {
            smp[i] = (i == u_rock_layer) ? triplanar(i, v_world, n) : planar(i, v_world.xz);
            best = max(best, w[i] + smp[i].a * 0.5);
        }
    }
    vec3 albedo = vec3(0.0);
    float total = 0.0;
    for (int i = 0; i < 8; i++) {
        if (w[i] > 0.01) {
            float k = max(w[i] + smp[i].a * 0.5 - best + 0.2, 0.0);
            albedo += smp[i].rgb * k;
            total += k;
        }
    }
    albedo /= max(total, 1e-4);
    albedo *= 0.82 + 0.36 * macro;                       // break up tiling at a distance
    // meadow colour patches on grassy ground (not rock, road, snow or wet shore)
    float grassy = (1.0 - rock) * (1.0 - road) * (1.0 - snow) * (1.0 - wet) * (1.0 - bare);
    albedo *= mix(vec3(1.0), pa.rgb * 2.0, grassy);
    albedo *= mix(vec3(1.0), pb.rgb * 2.0, bare * (1.0 - wet));
    albedo = pow(albedo, vec3(2.2));                     // sRGB -> linear
    albedo *= mix(1.0, 0.55, smoothstep(wl + 1.5, wl, v_world.y));             // damp shoreline

    float ndl = max(dot(n, u_sun_dir), 0.0);
    vec3 ambient = mix(u_ambient_ground, u_ambient_sky, n.y * 0.5 + 0.5);
    vec3 col = albedo * (u_sun_color * ndl + ambient);
    col = apply_fog(col, u_cam, v_world);

    if (u_debug_view == 1) { f_color = vec4(n * 0.5 + 0.5, 1.0); return; }
    if (u_debug_view == 2) { f_color = vec4(rock, road, snow, 1.0); return; }
    f_color = vec4(tonemap(col), 1.0);
}
