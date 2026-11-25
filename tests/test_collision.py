"""Solid props (no GPU): box and circle push-out, rotation, heights, the camera line, stuck wanderers."""
import math
from types import SimpleNamespace

import numpy as np
import pytest

from lycantrope.world.collision import Colliders
from lycantrope.world.props import facing_to_rotation, rotate_xz


def world(rows_by_key, shapes, extents):
    cat = {k: SimpleNamespace(collide=shapes[k], extents=extents[k]) for k in rows_by_key}
    return Colliders.from_instances({k: np.array(v, float) for k, v in rows_by_key.items()}, cat)


def house(x=0.0, z=0.0, facing=180.0):
    # an 8 m (x) by 4 m (z) footprint, 5 m tall, placed like the game does
    return world({"H": [(x, 0.0, z, facing_to_rotation(facing), 1.0, 1.0, 1.0)]},
                 {"H": {"box": 1.0}}, {"H": (8.0, 5.0, 4.0)})


def test_box_pushes_out_along_the_nearest_face():
    c = house()
    x, z, hit = c.push_out(0.0, 1.8, 0.4)           # just inside the long side
    assert hit and z == pytest.approx(2.4, abs=1e-6) and x == pytest.approx(0.0, abs=1e-6)
    x, z, hit = c.push_out(4.2, 0.0, 0.4)           # touching the short side from outside
    assert hit and x == pytest.approx(4.4, abs=1e-6)
    assert c.push_out(0.0, 3.0, 0.4)[2] is False    # clear of it


def test_box_turns_with_the_prop():
    c = house(facing=90.0)                           # turned a quarter: now 4 m along x, 8 m along z
    lx, lz = rotate_xz(4.0, 0.0, facing_to_rotation(90.0))
    assert abs(lx) < 1e-6 and abs(lz) == pytest.approx(4.0)
    assert c.blocked(0.0, 3.5) and not c.blocked(3.5, 0.0)
    x, z, _ = c.push_out(0.0, 3.9, 0.4)
    assert z == pytest.approx(4.4, abs=1e-6)


def test_circles_scale_and_slide():
    c = world({"T": [(0.0, 0.0, 0.0, 0.0, 2.0, 1.0, 1.0)]}, {"T": {"circle": 0.5, "top": 0.35}}, {"T": (6.0, 10.0, 6.0)})
    x, z, hit = c.push_out(0.5, 0.5, 0.4)            # trunk radius 0.5 x scale 2 = 1 m
    assert hit and math.hypot(x, z) == pytest.approx(1.4, abs=1e-6)
    # only the trunk blocks the camera: it's 10 m x 2 x 0.35 = 7 m tall
    assert c.blocked(0.0, 0.0, y=5.0) and not c.blocked(0.0, 0.0, y=8.0)


def test_walking_into_a_wall_slides_along_it():
    c = house()
    x, z = -2.0, 3.0
    for _ in range(60):                              # walk diagonally into the wall
        x, z, _ = c.push_out(x + 0.05, z - 0.05, 0.4)
    assert z == pytest.approx(2.4, abs=1e-6) and x > 0.5   # stopped at the wall, kept sliding along it


def test_camera_line_stops_before_the_house():
    c = house()
    t = c.clear_distance((0.0, 1.5, 8.0), (0.0, 1.5, 0.0))
    assert 0.6 < t < 0.75                            # the wall is at z = 2, 6 m of the 8 m away
    assert c.clear_distance((0.0, 6.0, 8.0), (0.0, 6.0, 0.0)) == 1.0   # above the roof: clear


def test_stuck_wanderer_gives_up_its_goal():
    from lycantrope.world.actors import Actor, AiParams, ClipInfo, Enemy
    clips = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4)}
    a = Actor("cow", 0.0, 0.0, 0.0, clips, {"walk": 1.0, "run": 4.0})
    rowan = Actor("rowan", 500.0, 0.0, 0.0, clips, {"walk": 1.0, "run": 4.0})
    e = Enemy(a, (0.0, 0.0), AiParams(aggro_m=0, wander_m=20), seed=1)
    e.goal, a.timer = (0.0, 20.0), 0.0
    for _ in range(300):                             # a wall the world keeps pushing it back from
        e.update(rowan, True, 1 / 60)
        if a.z > 2.0:
            a.z = 2.0
            e.bumped += 1 / 60
    assert e.goal is None                            # gave up instead of pushing forever
