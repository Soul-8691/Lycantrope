#version 330
in vec2 in_grid;          // 0..1 inside the chunk
in float in_skirt;        // 1 on the skirt ring that hides LOD cracks
in vec2 in_chunk;         // per instance: chunk origin (x, z) in meters

uniform sampler2D u_height;   // R32F, meters
uniform float u_world_size;
uniform float u_chunk_size;
uniform float u_skirt_depth;
uniform mat4 u_viewproj;

out vec3 v_world;

void main() {
    vec2 xz = in_chunk + in_grid * u_chunk_size;
    vec2 uv = (xz + 0.5 * u_world_size) / u_world_size;
    float h = textureLod(u_height, uv, 0.0).r - in_skirt * u_skirt_depth;
    v_world = vec3(xz.x, h, xz.y);
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
