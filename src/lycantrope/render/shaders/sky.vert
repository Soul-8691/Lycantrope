#version 330
out vec2 v_ndc;
void main() {
    // fullscreen triangle from the vertex id: (-1,-1) (3,-1) (-1,3)
    vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2)) * 2.0 - 1.0;
    v_ndc = p;
    gl_Position = vec4(p, 0.0, 1.0);
}
