#version 330
// Glowing orb, drawn additively: brightest where you look straight through it, fading at the rim.
// With u_shell = 1 it's the other way round: a bubble that glows at its edge (a ward).
in vec3 v_world;
in vec3 v_nrm;
out vec4 f_color;
uniform vec3 u_cam;
uniform vec3 u_color;
uniform float u_strength;
uniform int u_shell;
void main() {
    vec3 v = normalize(u_cam - v_world);
    float facing = abs(dot(normalize(v_nrm), v));
    if (u_shell == 1) {
        float rim = pow(1.0 - facing, 3.0);
        f_color = vec4(u_color * (rim + 0.06) * u_strength, 1.0);
        return;
    }
    float glow = pow(facing, 2.5) * u_strength;
    vec3 col = u_color * glow + vec3(1.0, 0.95, 0.8) * pow(facing, 12.0) * u_strength * 0.6;   // hot centre
    f_color = vec4(col, 1.0);
}
