#version 330
#include "common.glsl"
// Bakes the ground patch fields once at load, so terrain and grass read textures instead of
// running noise every frame. Colours are stored halved (they go above 1).
//   A: rgb = meadow tint / 2,  a = bare dirt amount
//   B: rgb = soil tint / 2,    a = tall-grass amount
in vec2 v_uv;
layout(location = 0) out vec4 out_a;
layout(location = 1) out vec4 out_b;
uniform float u_world_size;

void main() {
    vec2 xz = v_uv * u_world_size - 0.5 * u_world_size;
    out_a = vec4(meadow_tint(xz) * 0.5, dirt_patch(xz));
    out_b = vec4(dirt_tint(xz) * 0.5, smoothstep(0.38, 0.7, fbm3(xz / 55.0 + 3.1)));
}
