#version 330
in vec2 in_xz;
uniform float u_water;
uniform mat4 u_viewproj;
out vec3 v_world;
void main() {
    v_world = vec3(in_xz.x, u_water, in_xz.y);
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
