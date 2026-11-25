"""Character logic (no GPU): animation state, Rowan's controller, enemy behaviour, GLB math."""
import math

import numpy as np
import pytest

from lycantrope.world.actors import (Actor, AiParams, AnimState, ClipInfo, Enemy, Rowan, RowanInput,
                                     heading_to, separate, turn_towards)

CLIPS = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4), "run": ClipInfo(0.7, True, 1.0, 4.6),
         "sprint": ClipInfo(0.6, True, 1.0, 7.0), "light1": ClipInfo(1.0, False), "light2": ClipInfo(1.0, False),
         "light3": ClipInfo(1.0, False), "heavy": ClipInfo(1.5, False), "block": ClipInfo(3.0, True),
         "cast": ClipInfo(1.2, False), "hit": ClipInfo(0.8, False), "death": ClipInfo(2.0, False),
         "attack1": ClipInfo(0.9, False)}
SPEEDS = {"walk": 1.6, "run": 5.0, "sprint": 7.5}


def actor(kind="rowan", x=0.0, z=0.0, heading=0.0):
    return Actor(kind, x, z, heading, CLIPS, dict(SPEEDS))


def step(fn, n, dt=1 / 60):
    for _ in range(n):
        fn(dt)


def test_crossfade_and_restart():
    a = AnimState()
    a.play("walk")
    assert a.prev == "idle" and a.fade == 0.0
    a.update(0.075)
    assert 0.4 < a.fade < 0.6
    a.update(1.0)
    assert a.fade == 1.0
    t = a.time
    a.play("walk")                         # same clip: keeps playing
    assert a.time == t
    a.play("walk", restart=True)
    assert a.time == 0.0


def test_heading_convention():
    assert heading_to(0, 1) == pytest.approx(0.0)              # +z (south)
    assert heading_to(0, -1) == pytest.approx(math.pi)          # north
    assert turn_towards(0.0, math.pi / 2, 0.1) == pytest.approx(0.1)
    assert turn_towards(3.0, -3.0, 1.0) == pytest.approx(3.0 + (math.tau - 6.0))   # short way round


def test_rowan_moves_relative_to_camera_and_picks_clips():
    r = Rowan(actor(heading=math.pi))          # already facing north, so no turn on the spot
    inp = RowanInput(move_y=1.0)
    step(lambda dt: (r.update(inp, 0.0, dt), r.a.anim.update(dt)), 90)   # camera yaw 0 looks north
    assert r.a.z < -3.0 and abs(r.a.x) < 0.5
    assert r.a.anim.clip == "run" and r.a.speed == pytest.approx(5.0)
    inp.sprint = True
    step(lambda dt: r.update(inp, 0.0, dt), 30)
    assert r.a.anim.clip == "sprint"
    inp = RowanInput()
    step(lambda dt: r.update(inp, 0.0, dt), 60)
    assert r.a.anim.clip == "idle" and r.a.speed == 0.0


def test_turbo_is_four_times_faster_with_the_same_gait():
    from lycantrope.world.actors import TURBO
    r = Rowan(actor(heading=math.pi))
    step(lambda dt: (r.update(RowanInput(move_y=1.0, turbo=True), 0.0, dt), r.a.anim.update(dt)), 90)
    assert r.a.speed == pytest.approx(SPEEDS["run"] * TURBO)
    assert r.a.anim.clip == "run"                            # not bumped up to the sprint clip
    step(lambda dt: r.update(RowanInput(move_y=1.0), 0.0, dt), 60)
    assert r.a.speed == pytest.approx(SPEEDS["run"])        # off again: back to normal


def test_light_attack_chain():
    r = Rowan(actor())
    tick = lambda inp: (r.update(inp, 0.0, 1 / 60), r.a.anim.update(1 / 60))
    tick(RowanInput(light=True))
    assert r.a.state == "attack" and r.a.anim.clip == "light1"
    for _ in range(25):
        tick(RowanInput())
    tick(RowanInput(light=True))                # queue the second swing
    for _ in range(40):
        tick(RowanInput())
    assert r.a.anim.clip == "light2"
    for _ in range(70):
        tick(RowanInput())
    assert r.a.state == "move"                  # no third press: back to moving
    # no movement while swinging
    tick(RowanInput(light=True, move_y=1.0))
    z0 = r.a.z
    for _ in range(20):
        tick(RowanInput(move_y=1.0))
    assert r.a.z == pytest.approx(z0, abs=0.05)


def test_block_hold_and_death_toggle():
    r = Rowan(actor())
    r.update(RowanInput(block=True), 0.0, 1 / 60)
    assert r.a.state == "block" and r.a.anim.clip == "block"
    r.update(RowanInput(), 0.0, 1 / 60)
    assert r.a.state == "move"
    r.update(RowanInput(die=True), 0.0, 1 / 60)
    assert r.a.state == "dead" and r.a.anim.clip == "death"
    r.update(RowanInput(move_y=1.0), 0.0, 1 / 60)
    assert r.a.speed == 0.0
    r.update(RowanInput(die=True), 0.0, 1 / 60)
    assert r.a.state == "move"


def test_enemy_chases_attacks_and_gives_up():
    rowan = actor("rowan", 0.0, 0.0)
    gob = actor("goblin", 10.0, 0.0)
    e = Enemy(gob, (10.0, 0.0), AiParams(aggro_m=15, leash_m=30, reach_m=1.5, attack_every_s=(0.1, 0.2)), seed=1)
    states = set()
    for _ in range(400):
        e.update(rowan, True, 1 / 60)
        gob.anim.update(1 / 60)
        states.add(gob.state)
    assert {"chase", "engage", "attack"} <= states
    assert math.hypot(gob.x, gob.z) < 2.5
    rowan.x = 200.0                             # Rowan leaves: back home
    for _ in range(900):
        e.update(rowan, True, 1 / 60)
        gob.anim.update(1 / 60)
    assert gob.state == "wander"
    assert math.hypot(gob.x - 10.0, gob.z) < 12.0


def test_separate_pushes_overlaps_apart():
    a, b = actor(x=0.0), actor(x=0.3)
    separate([a, b])
    assert b.x - a.x == pytest.approx(a.radius + b.radius)


def test_nearest_neighbours_fallback_matches_brute_force(monkeypatch):
    import builtins
    from lycantrope.render import gltf
    real_import = builtins.__import__

    def no_scipy(name, *args, **kw):
        if name.startswith("scipy"):
            raise ImportError
        return real_import(name, *args, **kw)
    monkeypatch.setattr(builtins, "__import__", no_scipy)
    rng = np.random.default_rng(0)
    a, b = rng.random((50, 3)), rng.random((300, 3))
    idx, dist = gltf.nearest_neighbours(a, b, k=3, chunk=16)
    d = np.linalg.norm(a[:, None] - b[None], axis=2)
    assert np.array_equal(idx[:, 0], d.argmin(axis=1))
    assert np.allclose(dist[:, 0], d.min(axis=1), atol=1e-5)


def test_compose_matches_quaternion():
    from lycantrope.render.gltf import compose
    q = np.array([0.0, math.sin(math.pi / 4), 0.0, math.cos(math.pi / 4)])   # 90 degrees about +y
    m = compose(np.array([1.0, 2.0, 3.0]), q, np.array([2.0, 2.0, 2.0]))
    assert np.allclose(m[:3, :3] @ [0, 0, 1], [2, 0, 0], atol=1e-9)          # +z turns to +x, scaled
    assert np.allclose(m[:3, 3], [1, 2, 3])


def test_caster_keeps_range_casts_and_uses_blade_up_close():
    clips = dict(CLIPS, cast=ClipInfo(1.5, False), attack1=ClipInfo(0.9, False))
    rowan = Actor("rowan", 0.0, 0.0, 0.0, clips, dict(SPEEDS))
    mage = Actor("battlemage", 20.0, 0.0, 0.0, clips, {"walk": 1.4, "run": 4.8})
    ai = AiParams(aggro_m=24, leash_m=60, reach_m=1.8, cast_range_m=16, keep_away_m=7,
                  cast_every_s=(0.5, 0.6), attack_every_s=(0.5, 0.6), release_at=0.5)
    e = Enemy(mage, (20.0, 0.0), ai, seed=3)
    releases, states = 0, set()
    for _ in range(600):
        e.update(rowan, True, 1 / 60)
        mage.anim.update(1 / 60)
        releases += e.should_release()
        states.add(mage.state)
    assert "cast" in states and releases >= 2
    assert 6.0 < math.hypot(mage.x, mage.z) <= 16.5          # stayed at casting range
    assert "attack" not in states                            # never needed the blade at range
    mage.x, mage.z = 1.5, 0.0                                # Rowan steps right up to it
    for _ in range(200):
        e.update(rowan, True, 1 / 60)
        mage.anim.update(1 / 60)
        states.add(mage.state)
    assert "attack" in states


def test_idle_waits_a_few_seconds_after_stopping():
    from lycantrope.world.actors import IDLE_DELAY_S
    r = Rowan(actor(heading=math.pi))
    for _ in range(60):                                       # run for a second
        r.update(RowanInput(move_y=1.0), 0.0, 1 / 60)
        r.a.advance(1 / 60)
    for _ in range(40):                                       # stop
        r.update(RowanInput(), 0.0, 1 / 60)
        r.a.advance(1 / 60)
    assert r.a.anim.clip == "idle" and r.a.anim.time == 0.0   # holding the first frame
    for _ in range(int(IDLE_DELAY_S * 60)):
        r.update(RowanInput(), 0.0, 1 / 60)
        r.a.advance(1 / 60)
    assert r.a.anim.time > 0.0                                # now the idle plays
    r.update(RowanInput(move_y=1.0), 0.0, 1 / 60)             # moving again...
    for _ in range(30):
        r.update(RowanInput(), 0.0, 1 / 60)
        r.a.advance(1 / 60)
    assert r.a.anim.clip == "idle" and r.a.anim.time == 0.0   # ...restarts the wait
