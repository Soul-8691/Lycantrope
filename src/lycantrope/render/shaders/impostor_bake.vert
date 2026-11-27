#version 330
in vec3 in_pos;           // model space, pivot at the bottom center
in vec3 in_nrm;
in vec2 in_uv;

uniform mat4 u_mvp;       // orthographic view of the model from one side
uniform float u_height;

out vec3 v_nrm;
out vec2 v_uv;
out float v_rel_h;

void main() {
    v_nrm = in_nrm;
    v_uv = in_uv;
    v_rel_h = in_pos.y / max(u_height, 1e-3);
    gl_Position = u_mvp * vec4(in_pos, 1.0);
}
