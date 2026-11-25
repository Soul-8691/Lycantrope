#version 330
in vec2 in_grid;              // 0..1 across the chunk
in vec2 in_chunk;             // per instance: chunk origin (x, z)
uniform sampler2D u_water_tex;    // R32F water surface height (sea, lakes, rivers)
uniform float u_world_size;
uniform float u_chunk_size;
uniform mat4 u_viewproj;
out vec3 v_world;
void main() {
    vec2 xz = in_chunk + in_grid * u_chunk_size;
    vec2 uv = (xz + 0.5 * u_world_size) / u_world_size;
    v_world = vec3(xz.x, textureLod(u_water_tex, uv, 0.0).r, xz.y);
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
