"""Day and night (no GPU): the clock, the sun's path and the light it gives."""
import pytest

from lycantrope.render.environment import default_environment, sky_config
from lycantrope.world.daytime import DayClock, sky_at, sun_angles


def test_clock_runs_on_play_time_and_wraps():
    c = DayClock({"start_hour": 23.0, "minutes_per_day": 48})
    c.update(60.0 * 2)                                   # 2 real minutes = 1 game hour at 48 min/day
    assert c.hour == pytest.approx(0.0, abs=1e-6) and c.days == 1
    c.set(25.5)
    assert c.hour == pytest.approx(1.5) and c.label() == "01:30" and c.is_night()


def test_sun_rises_east_peaks_south_sets_west():
    e6, a6 = sun_angles(6.0)
    e13, a13 = sun_angles(13.0)
    e20, a20 = sun_angles(20.0)
    assert abs(e6) < 1e-6 and a6 == pytest.approx(90.0)
    assert e13 > 50 and a13 == pytest.approx(180.0)
    assert abs(e20) < 1e-6 and a20 == pytest.approx(270.0)
    assert sun_angles(1.0)[0] < -20                      # deep night


def test_light_goes_from_day_to_moonlit_night():
    cfg = sky_config()
    noon, dusk, night = sky_at(13.0, cfg), sky_at(20.5, cfg), sky_at(1.0, cfg)
    bright = lambda c: sum(c["sun_color"])                # noqa: E731
    assert bright(noon) > bright(dusk) > bright(night)
    assert noon["night"] == 0.0 and night["night"] == 1.0
    assert night["sun_dir"][1] > 0.3                     # the moon lights it from above
    env = default_environment(True, 1.0)
    assert env["u_night"] == 1.0 and env["u_sun_dir"].y > 0
