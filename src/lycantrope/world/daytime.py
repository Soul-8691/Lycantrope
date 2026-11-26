"""Day and night (WLD-11): a clock that runs on play time, and the light it gives.

The game day is compressed: `minutes_per_day` real minutes of play make one full day (data/world/sky.json,
"day"). The sun rises in the east at `sunrise`, arcs through the south and sets in the west at `sunset`;
after dark a cool moonlight takes over the same light, and the sky shows stars.

`sky_at(hour)` turns the time into the shared lighting uniforms (sun direction and colour, sky and
ambient colours, how much night there is), blending between night, twilight, golden hour and day by the
sun's height, so every shader that already uses the sun follows the clock with no changes.
"""
from __future__ import annotations

import math

KEYS = ("sun_color", "zenith_color", "horizon_color", "ambient_sky", "ambient_ground")

# lighting by sun elevation (degrees): night, twilight, golden hour, day (the day values are sky.json's)
NIGHT = {"sun_color": (0.10, 0.13, 0.22), "zenith_color": (0.006, 0.010, 0.030), "horizon_color": (0.025, 0.035, 0.070),
         "ambient_sky": (0.050, 0.065, 0.115), "ambient_ground": (0.020, 0.020, 0.028)}
TWILIGHT = {"sun_color": (0.55, 0.32, 0.36), "zenith_color": (0.05, 0.07, 0.20), "horizon_color": (0.42, 0.30, 0.38),
            "ambient_sky": (0.16, 0.15, 0.24), "ambient_ground": (0.06, 0.05, 0.05)}
GOLDEN = {"sun_color": (2.4, 1.45, 0.75), "zenith_color": (0.16, 0.26, 0.55), "horizon_color": (0.92, 0.62, 0.42),
          "ambient_sky": (0.30, 0.32, 0.42), "ambient_ground": (0.15, 0.11, 0.08)}


class DayClock:
    """The time of day (hours, 0..24), advanced by play time."""

    def __init__(self, cfg: dict | None = None) -> None:
        cfg = cfg or {}
        self.hour = float(cfg.get("start_hour", 8.0))
        self.minutes_per_day = float(cfg.get("minutes_per_day", 48.0))
        self.sunrise = float(cfg.get("sunrise", 6.0))
        self.sunset = float(cfg.get("sunset", 20.0))
        self.running = True
        self.days = 0

    def update(self, dt: float) -> None:
        """dt: seconds of play. One day takes minutes_per_day real minutes."""
        if not self.running or self.minutes_per_day <= 0:
            return
        self.hour += dt * 24.0 / (self.minutes_per_day * 60.0)
        while self.hour >= 24.0:
            self.hour -= 24.0
            self.days += 1

    def set(self, hour: float) -> None:
        self.hour = hour % 24.0

    def is_night(self) -> bool:
        return not (self.sunrise <= self.hour < self.sunset)

    def label(self) -> str:
        h = int(self.hour)
        m = int((self.hour - h) * 60)
        return f"{h:02d}:{m:02d}"


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _smooth(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def sun_angles(hour: float, sunrise: float = 6.0, sunset: float = 20.0, peak_deg: float = 58.0):
    """(elevation, azimuth) of the sun in degrees. Azimuth: 90 east at sunrise, 180 south at noon, 270
    west at sunset; at night the sun keeps going round below the horizon."""
    day_len = sunset - sunrise
    if sunrise <= hour <= sunset:
        f = (hour - sunrise) / day_len                         # 0..1 across the day
        elev = peak_deg * math.sin(math.pi * f)
        az = 90.0 + 180.0 * f
    else:
        night_len = 24.0 - day_len
        f = ((hour - sunset) % 24.0) / night_len               # 0..1 across the night
        elev = -peak_deg * 0.8 * math.sin(math.pi * f)
        az = 270.0 + 180.0 * f
    return elev, az % 360.0


def _direction(elev_deg: float, az_deg: float):
    e, a = math.radians(elev_deg), math.radians(az_deg)
    # x east, z south: azimuth 0 = north (-z), 90 = east (+x)
    return (math.sin(a) * math.cos(e), math.sin(e), -math.cos(a) * math.cos(e))


def sky_at(hour: float, day: dict, clock: DayClock | None = None) -> dict:
    """Lighting for this time. day: sky.json's daytime values (sun colour, sky colours, ambient)."""
    sunrise = clock.sunrise if clock else 6.0
    sunset = clock.sunset if clock else 20.0
    elev, az = sun_angles(hour, sunrise, sunset)
    DAY = {"sun_color": tuple(day["sun"]["color"]), "zenith_color": tuple(day["zenith_color"]),
           "horizon_color": tuple(day["horizon_color"]), "ambient_sky": tuple(day["ambient_sky"]),
           "ambient_ground": tuple(day["ambient_ground"])}
    # blend by the sun's height: below -8 night, -8..0 twilight, 0..12 golden, above 20 full day
    if elev <= -8:
        look, night = NIGHT, 1.0
    elif elev < 0:
        t = _smooth((elev + 8) / 8)
        look, night = {k: _lerp(NIGHT[k], TWILIGHT[k], t) for k in KEYS}, 1.0 - t
    elif elev < 12:
        t = _smooth(elev / 12)
        look, night = {k: _lerp(TWILIGHT[k], GOLDEN[k], t) for k in KEYS}, 0.0
    else:
        t = _smooth((elev - 12) / 8)
        look, night = {k: _lerp(GOLDEN[k], DAY[k], t) for k in KEYS}, 0.0
    if elev > 0:
        light = _direction(max(elev, 2.0), az)                # the sun (kept just above the horizon at dusk)
    else:
        # the moon lights the night: opposite the sun, high enough to cast soft light
        light = _direction(max(25.0, -elev * 0.8), (az + 180.0) % 360.0)
        if elev > -8:                                          # twilight: hand over from the sun's glow
            t = _smooth((elev + 8) / 8)
            sun = _direction(2.0, az)
            light = tuple(m * (1 - t) + s * t for m, s in zip(light, sun))
            n = math.sqrt(sum(c * c for c in light))
            light = tuple(c / n for c in light)
    return {**look, "sun_dir": light, "night": night, "elevation": elev}
