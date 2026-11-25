#version 330
// The Rite's circle on the ground: a small grid draped over the terrain each frame.
in vec3 in_pos;               // world position
in vec2 in_uv;                // -1..1 across the circle
uniform mat4 u_viewproj;
out vec2 v_uv;
out vec3 v_world;
void main() {
    v_uv = in_uv;
    v_world = in_pos;
    gl_Position = u_viewproj * vec4(in_pos, 1.0);
}
