#version 330
in vec3 in_pos;           // model space, pivot at the bottom center, front = +z
in vec3 in_nrm;
in vec2 in_uv;
in vec3 in_offset;        // per instance: world position of the pivot
in float in_rot;          // rotation about +y (radians)
in float in_scale;
in float in_shade;        // small brightness variation between copies
in float in_stretch;      // extra height-only scale, so one model gives tall and squat variants

uniform mat4 u_viewproj;

out vec3 v_world;
out vec3 v_nrm;
out float v_rel_h;        // 0 at the base, 1 at the top of the model
out float v_shade;
out vec2 v_uv;

uniform float u_height;

void main() {
    float c = cos(in_rot), s = sin(in_rot);
    mat3 rot = mat3(c, 0.0, -s,   0.0, 1.0, 0.0,   s, 0.0, c);   // columns
    vec3 sc = vec3(in_scale, in_scale * in_stretch, in_scale);
    v_world = in_offset + rot * (in_pos * sc);
    v_nrm = rot * (in_nrm / sc);                            // inverse-transpose of the scale
    v_rel_h = in_pos.y / max(u_height, 1e-3);
    v_shade = in_shade;
    v_uv = in_uv;
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
