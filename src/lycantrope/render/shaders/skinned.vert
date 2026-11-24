#version 330
in vec3 in_pos;
in vec3 in_nrm;
in vec2 in_uv;
in vec4 in_joints;
in vec4 in_weights;
in vec3 in_color;

uniform mat4 u_joints[64];     // joint world * inverse bind, character space (meters)
uniform mat4 u_model;          // character space -> world
uniform mat4 u_viewproj;
uniform int u_skinned;         // 0: rigid (items, rigless animals)

out vec3 v_world;
out vec3 v_nrm;
out vec2 v_uv;
out vec3 v_color;

void main() {
    mat4 skin = mat4(1.0);
    if (u_skinned == 1) {
        skin = in_weights.x * u_joints[int(in_joints.x)]
             + in_weights.y * u_joints[int(in_joints.y)]
             + in_weights.z * u_joints[int(in_joints.z)]
             + in_weights.w * u_joints[int(in_joints.w)];
    }
    vec4 wp = u_model * skin * vec4(in_pos, 1.0);
    v_world = wp.xyz;
    v_nrm = mat3(u_model) * mat3(skin) * in_nrm;
    v_uv = in_uv;
    v_color = in_color;
    gl_Position = u_viewproj * wp;
}
