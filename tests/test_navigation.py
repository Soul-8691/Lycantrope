import math
from types import SimpleNamespace

import numpy as np

from lycantrope.ui.navigation import (DUSKHOLD, HINT_M, NEAR_M, RegionTracker, bearing, compass_markers,
                                      fmt_distance, map_image, wrap)
from lycantrope.world.heightfield import Place


def test_bearing_follows_camera_yaw():
    assert math.isclose(bearing((0, 0), (0, -10)), 0.0)                 # north is -z
    assert math.isclose(bearing((0, 0), (10, 0)), math.pi / 2)          # east
    assert math.isclose(abs(bearing((0, 0), (0, 10))), math.pi)         # south
    assert math.isclose(bearing((0, 0), (-10, 0)), -math.pi / 2)        # west


def test_wrap():
    assert math.isclose(wrap(3 * math.pi / 2), -math.pi / 2)
    assert math.isclose(wrap(-3 * math.pi / 2), math.pi / 2)


def test_fmt_distance():
    assert fmt_distance(240.4) == "240 m"
    assert fmt_distance(1250) == "1.2 km"


def _world():
    return SimpleNamespace(
        landmarks=[Place(DUSKHOLD, 0, -2000, 0, 140), Place("Mill", 100, 0, 0, 10), Place("Tower", 0, 200, 0, 10),
                   Place("Far Hut", NEAR_M + 500, 0, 0, 10)],
        waystones=[Place("Crossroads", 0, -50, 0, 9)])


def test_compass_markers():
    pos = (0.0, 0.0)
    kinds = {m.name: m.kind for m in compass_markers(_world(), {"Mill", "Far Hut"}, pos)}
    assert kinds[DUSKHOLD] == "duskhold"              # always, discovered or not
    assert kinds["Mill"] == "landmark"
    assert kinds["Tower"] == "hint"                   # undiscovered but close
    assert kinds["Crossroads"] == "hint"
    assert "Far Hut" not in kinds                     # discovered, but too far away
    far = (HINT_M + 400.0, 3000.0)
    assert {m.name for m in compass_markers(_world(), set(), far)} == {DUSKHOLD}
    inside_mill = (102.0, 0.0)
    assert "Mill" not in {m.name for m in compass_markers(_world(), {"Mill"}, inside_mill)}


def test_region_needs_to_settle():
    t = RegionTracker()
    assert t.update(0.1, "Brackenvale") == "Brackenvale"       # the first region shows at once
    assert t.update(0.5, "The Wolfwood") is None
    assert t.update(0.3, "Brackenvale") is None                # stepped back: no banner, timer resets
    assert t.update(0.6, "The Wolfwood") is None
    assert t.update(0.6, "The Wolfwood") == "The Wolfwood"
    assert t.current == "The Wolfwood"


def test_map_image():
    n = 64
    heights = np.tile(np.linspace(0, 200, n, dtype=np.float32), (n, 1))
    water = np.full((n, n), -1.0, np.float32)
    water[:8, :8] = 50.0
    w = SimpleNamespace(size=n, mpp=1.0, heights=heights, water_surface=water,
                        road=np.zeros((n, n), np.uint8), biome=np.ones((n, n), np.uint8))
    img = map_image(w, px=32)
    assert img.shape == (32, 32, 3) and img.dtype == np.uint8
    assert img[1, 1, 2] > img[1, 1, 0]                         # water is blue
    assert img[20, 20, 1] > img[20, 20, 2]                     # Brackenvale is green
