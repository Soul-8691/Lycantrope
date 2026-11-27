#version 330
// Distant tree cut-out: one quad per instance, turned about +y to face the camera.
in vec2 in_q;             // x -1..1 across, y 0..1 up
in vec3 in_offset;        // per instance, same layout as props.vert
in float in_rot;
in float in_scale;
in float in_shade;
in float in_stretch;

uniform mat4 u_viewproj;
uniform vec3 u_cam;
uniform vec2 u_size;      // half-width and height of the model at scale 1

out vec3 v_world;
out vec2 v_q;
out float v_shade;
flat out float v_rot;
flat out float v_view;    // angle of the camera around the model, in model space

void main() {
    vec3 to = u_cam - in_offset;
    to.y = 0.0;
    float l = length(to);
    vec3 f = l > 1e-4 ? to / l : vec3(0.0, 0.0, 1.0);
    vec3 r = vec3(f.z, 0.0, -f.x);                          // cross(up, f)
    v_world = in_offset + r * (in_q.x * u_size.x * in_scale)
            + vec3(0.0, in_q.y * u_size.y * in_scale * in_stretch, 0.0);
    float c = cos(in_rot), s = sin(in_rot);
    v_view = atan(c * f.x - s * f.z, s * f.x + c * f.z);   // inverse instance rotation, then angle
    v_rot = in_rot;
    v_q = in_q;
    v_shade = in_shade;
    gl_Position = u_viewproj * vec4(v_world, 1.0);
}
