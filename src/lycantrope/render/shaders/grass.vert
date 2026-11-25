#version 330
#include "common.glsl"
in vec3 in_pos;            // tuft model space, 1 m tall
in float in_t;             // 0 at the blade base, 1 at the tip
in vec2 in_cell;           // per instance: cell offset from the camera's cell

uniform sampler2D u_height;
uniform sampler2D u_splat_a;
uniform sampler2D u_splat_b;
uniform sampler2D u_road;
uniform sampler2D u_water_tex;
uniform sampler2D u_patch_a;       // baked at load: rgb meadow tint / 2, a bare dirt
uniform sampler2D u_patch_b;       // baked at load: rgb soil tint / 2, a tall grass
uniform sampler2D u_bank;          // river banks (pebbles)
uniform float u_world_size;
uniform float u_cell;
uniform float u_radius;
uniform vec2 u_origin;         // camera position in whole cells
uniform vec3 u_cam;
uniform float u_time;
uniform float u_biome_grass[8];
uniform vec3 u_clearing;       // x, z, radius: mown grass in the village
uniform mat4 u_viewproj;

out vec3 v_world;
out float v_t;
out vec3 v_tint;

void main() {
    vec2 cell = u_origin + in_cell;
    float r1 = hash12(cell), r2 = hash12(cell + 71.3), r3 = hash12(cell - 19.7);
    vec2 xz = (cell + vec2(r1, r2)) * u_cell;
    vec2 uv = (xz + 0.5 * u_world_size) / u_world_size;
    float t = 1.0 / float(textureSize(u_height, 0).x);
    float h = textureLod(u_height, uv, 0.0).r;

    // where grass grows: biome, not steep, not on roads/paths, not under water
    vec4 sa = textureLod(u_splat_a, uv, 0.0), sb = textureLod(u_splat_b, uv, 0.0);
    float grow = dot(sa, vec4(u_biome_grass[0], u_biome_grass[1], u_biome_grass[2], u_biome_grass[3]))
               + dot(sb, vec4(u_biome_grass[4], u_biome_grass[5], u_biome_grass[6], u_biome_grass[7]));
    float hx = textureLod(u_height, uv + vec2(t, 0.0), 0.0).r - textureLod(u_height, uv - vec2(t, 0.0), 0.0).r;
    float hz = textureLod(u_height, uv + vec2(0.0, t), 0.0).r - textureLod(u_height, uv - vec2(0.0, t), 0.0).r;
    float slope = length(vec2(hx, hz)) * 0.5;                    // rise per meter (1 m per texel)
    grow *= smoothstep(0.9, 0.45, slope);
    grow *= 1.0 - smoothstep(0.08, 0.3, textureLod(u_road, uv, 0.0).r);
    grow *= smoothstep(0.1, 0.5, h - textureLod(u_water_tex, uv, 0.0).r);
    vec4 pa = textureLod(u_patch_a, uv, 0.0);
    grow *= 1.0 - smoothstep(0.2, 0.75, pa.a);                  // nothing grows on the bare dirt
    grow *= 1.0 - smoothstep(0.15, 0.6, textureLod(u_bank, uv, 0.0).r);   // or on the pebble banks
    grow *= step(r3, grow * 1.15);                               // thinner where it grows less

    // height: big patches of tall meadow, short lawn elsewhere; mown in the village
    float tall = textureLod(u_patch_b, uv, 0.0).a;
    float height = mix(0.22, 1.15, tall) * mix(0.7, 1.25, hash12(cell + 5.5));
    float dv = length(xz - u_clearing.xy);
    height *= mix(0.35, 1.0, smoothstep(u_clearing.z * 0.9, u_clearing.z * 1.4, dv));
    // fade out toward the edge of the grass radius so there's no visible ring
    float dist = length(xz - u_cam.xz);
    float fade = smoothstep(u_radius, u_radius * 0.7, dist);
    float s = height * grow * fade;

    float ang = r1 * 6.2831;
    float c = cos(ang), sn = sin(ang);
    // short grass is a smaller clump, not a flattened one: the spread shrinks with the height
    float spread = mix(0.8, 1.25, r2) * mix(0.45, 1.0, clamp(s, 0.0, 1.0)) * step(0.001, s);
    vec3 p = in_pos * vec3(spread, s, spread);
    p = vec3(c * p.x - sn * p.z, p.y, sn * p.x + c * p.z);
    // wind: gusts roll across the meadow, tips move most
    float gust = sin(dot(xz, vec2(0.11, 0.07)) - u_time * 1.6) * 0.5 + 0.5;
    float sway = (0.12 + 0.22 * gust) * in_t * in_t * s;
    p.xz += vec2(0.8, 0.6) * sway * (0.6 + 0.4 * sin(u_time * 3.1 + r3 * 6.28));

    v_world = vec3(xz.x, h - 0.03, xz.y) + p;
    v_t = in_t;
    v_tint = pa.rgb * 2.0 * mix(0.85, 1.12, r3) * mix(vec3(1.0), vec3(1.12, 1.05, 0.72), tall * 0.35);
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
