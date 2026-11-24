#version 330
#include "common.glsl"
in vec2 v_ndc;
out vec4 f_color;
uniform mat4 u_inv_viewproj;
uniform vec3 u_cam;
void main() {
    vec4 p = u_inv_viewproj * vec4(v_ndc, 1.0, 1.0);
    vec3 dir = normalize(p.xyz / p.w - u_cam);
    f_color = vec4(tonemap(sky_color(dir)), 1.0);
}
