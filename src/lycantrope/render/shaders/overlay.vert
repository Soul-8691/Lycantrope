#version 330
uniform vec4 u_rect;          // x0, y0, x1, y1 in NDC
out vec2 v_uv;
void main() {
    vec2 c = vec2(float(gl_VertexID & 1), float((gl_VertexID >> 1) & 1));   // triangle strip corners
    v_uv = c;
    gl_Position = vec4(mix(u_rect.xy, u_rect.zw, c), 0.0, 1.0);
}
