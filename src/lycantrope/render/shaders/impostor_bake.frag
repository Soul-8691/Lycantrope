#version 330
// Captures one side view of a prop for its distant cut-out: colour, and the surface
// normal in that view's frame (right, up, toward the viewer) so it can still be lit.
in vec3 v_nrm;
in vec2 v_uv;
in float v_rel_h;

uniform sampler2D u_tex;
uniform int u_has_tex;
uniform vec3 u_color;        // linear
uniform vec3 u_top_color;    // linear
uniform float u_top_from;
uniform vec3 u_right;        // this view's right and toward-viewer axes, model space
uniform vec3 u_fwd;

layout(location = 0) out vec4 o_albedo;   // sRGB colour, alpha = coverage
layout(location = 1) out vec4 o_normal;   // view-frame normal * 0.5 + 0.5, alpha = coverage

void main() {
    float top = smoothstep(u_top_from - 0.04, u_top_from + 0.04, v_rel_h);
    vec3 albedo = mix(u_color, u_top_color, top);
    if (u_has_tex == 1) albedo = pow(texture(u_tex, v_uv).rgb, vec3(2.2));
    vec3 n = normalize(v_nrm);
    if (dot(n, u_fwd) < 0.0) n = -n;                       // two-sided, like props.frag
    o_albedo = vec4(pow(albedo, vec3(1.0 / 2.2)), 1.0);
    o_normal = vec4(vec3(dot(n, u_right), n.y, dot(n, u_fwd)) * 0.5 + 0.5, 1.0);
}
