// Shared lighting, procedural sky (ART-09) and fog. Pulled into other shaders by an include line (see shaders.py).
uniform vec3 u_sun_dir;        // normalized, points toward the sun
uniform vec3 u_sun_color;      // linear HDR
uniform vec3 u_zenith_color;
uniform vec3 u_horizon_color;
uniform vec3 u_ambient_sky;
uniform vec3 u_ambient_ground;
uniform float u_fog_density;   // per meter at height 0
uniform float u_fog_falloff;   // per meter of altitude
uniform int u_fog_enabled;

vec3 sky_color(vec3 dir) {
    float h = clamp(dir.y, -1.0, 1.0);
    vec3 col = mix(u_horizon_color, u_zenith_color, pow(clamp(h, 0.0, 1.0), 0.45));
    col = mix(col, u_horizon_color * 0.55, clamp(-h * 4.0, 0.0, 1.0));
    float s = max(dot(dir, u_sun_dir), 0.0);
    col += u_sun_color * (pow(s, 6.0) * 0.12 + pow(s, 64.0) * 0.35);
    col += u_sun_color * smoothstep(0.9993, 0.9997, s) * 6.0;   // sun disc
    return col;
}

vec3 apply_fog(vec3 col, vec3 cam, vec3 pos) {
    if (u_fog_enabled == 0) return col;
    vec3 d = pos - cam;
    float dist = length(d);
    vec3 dir = d / max(dist, 1e-4);
    float b = u_fog_falloff;
    float amount;
    if (abs(dir.y) < 1e-3) amount = u_fog_density * exp(-cam.y * b) * dist;
    else amount = (u_fog_density / b) * exp(-cam.y * b) * (1.0 - exp(-dist * dir.y * b)) / dir.y;
    float fog = 1.0 - exp(-max(amount, 0.0));
    vec3 fog_col = sky_color(normalize(vec3(dir.x, 0.04, dir.z)));
    return mix(col, fog_col, clamp(fog, 0.0, 1.0));
}

vec3 tonemap(vec3 x) {           // ACES filmic fit, then gamma
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    x = clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
    return pow(x, vec3(1.0 / 2.2));
}
