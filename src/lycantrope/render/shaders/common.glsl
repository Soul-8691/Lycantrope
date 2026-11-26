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
uniform float u_night;         // 0 day .. 1 full night (stars, moon)

float star_hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

vec3 sky_color(vec3 dir) {
    float h = clamp(dir.y, -1.0, 1.0);
    vec3 col = mix(u_horizon_color, u_zenith_color, pow(clamp(h, 0.0, 1.0), 0.45));
    col = mix(col, u_horizon_color * 0.55, clamp(-h * 4.0, 0.0, 1.0));
    float s = max(dot(dir, u_sun_dir), 0.0);
    col += u_sun_color * (pow(s, 6.0) * 0.12 + pow(s, 64.0) * 0.35);
    col += u_sun_color * smoothstep(0.9993, 0.9997, s) * mix(6.0, 9.0, u_night);   // sun (or moon) disc
    if (u_night > 0.0) {                                                           // stars, high in the sky
        vec3 cell = floor(dir * 260.0);
        float star = step(0.9965, star_hash(cell));
        col += vec3(0.9, 0.92, 1.0) * star * u_night * smoothstep(0.08, 0.35, h) * 0.9;
    }
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

// ---- value noise and the meadow colour field (shared by terrain and grass) ----
float hash12(vec2 p) {
    vec3 q = fract(vec3(p.xyx) * 0.1031);
    q += dot(q, q.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
}

float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
               mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm3(vec2 p) {
    return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.03 + 11.7) + 0.15 * vnoise(p * 4.11 - 5.3);
}

// Colour multiplier for grassy ground: big dry (straw) and lush (deep green) patches, plus
// finer brightness changes, so meadows and distant hills don't read as one flat green.
vec3 meadow_tint(vec2 xz) {
    float dry  = smoothstep(0.40, 0.66, fbm3(xz / 430.0));
    float lush = smoothstep(0.44, 0.70, fbm3(xz / 190.0 + 17.0));
    float fine = fbm3(xz / 37.0 - 4.0);
    vec3 c = mix(vec3(1.0), vec3(1.30, 1.10, 0.55), dry * 0.9);            // straw
    c = mix(c, vec3(0.62, 0.92, 0.62), lush * 0.7);                         // deep green
    return c * (0.78 + 0.44 * fine);
}

// Bare dirt patches (0..1) with ragged, soft edges: roughly one-twelfth of open ground.
float dirt_patch(vec2 xz) {
    float n = fbm3(xz / 58.0 + vec2(41.0, -7.0)) + 0.16 * (vnoise(xz / 5.5) - 0.5);
    return smoothstep(0.645, 0.725, n);
}

// Soil colour per patch (multiplies the dark mud texture): dusty tan, grey-brown,
// red earth or dark loam, with a little mottling inside each patch.
vec3 dirt_tint(vec2 xz) {
    float k = vnoise(xz / 120.0 + 3.7) * 4.0;
    vec3 tan_ = vec3(1.55, 1.38, 1.10), grey = vec3(1.30, 1.24, 1.14);
    vec3 red = vec3(1.42, 1.06, 0.84), loam = vec3(1.02, 0.94, 0.86);
    vec3 col = k < 1.0 ? mix(tan_, grey, smoothstep(0.75, 1.0, k))
             : k < 2.0 ? mix(grey, red, smoothstep(1.75, 2.0, k))
             : k < 3.0 ? mix(red, loam, smoothstep(2.75, 3.0, k)) : loam;
    return col * (0.88 + 0.24 * vnoise(xz / 7.0));
}
