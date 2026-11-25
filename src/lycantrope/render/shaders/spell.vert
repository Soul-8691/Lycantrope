#version 330
in vec3 in_pos;               // unit sphere
uniform vec3 u_center;
uniform float u_radius;
uniform mat4 u_viewproj;
out vec3 v_world;
out vec3 v_nrm;
void main() {
    v_nrm = in_pos;
    v_world = u_center + in_pos * u_radius;
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
