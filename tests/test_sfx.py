"""Character sound cues (no sound device): what triggers which sound, panning, and the data file."""
import random
from types import SimpleNamespace

import pytest

from lycantrope.audio.sfx import SFX_DIR, SfxDirector, load_sfx_config, spatial
from lycantrope.world.actors import Actor, ClipInfo

CLIPS = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4), "run": ClipInfo(0.8, True),
         "attack1": ClipInfo(0.9, False), "light1": ClipInfo(0.6, False), "cast": ClipInfo(1.0, False),
         "death": ClipInfo(1.5, False)}
CFG = {"max_m": 45.0, "steps_within_m": 22.0, "min_gap_s": 0.3,
       "spell": {"loop": "combat/fireball_loop", "hit": "combat/fireball_hit"},
       "kinds": {"rowan": {"positional": False, "events": {
                     "light": ["combat/swing_light", {"s": "rowan/attack_light", "chance": 0.0}],
                     "death": ["rowan/death", {"s": "combat/body_fall", "delay_s": 0.5}],
                     "step": "footsteps/boot_{ground}"}},
                 "wolf": {"steps_per_cycle": 2, "events": {"alert": "wolf/alert", "attack": "wolf/attack",
                                                           "step": "footsteps/paw"}},
                 "battlemage": {"events": {"cast": "battlemage/cast", "release": "combat/fireball_cast"}},
                 "cow": {"idle_every_s": [1, 1], "events": {"idle": "cow/moo", "startled": "cow/startled"}}}}


def char(kind, x=0.0, z=0.0, brain=None):
    a = Actor(kind, x, z, 0.0, CLIPS, {"walk": 1.4, "run": 5.0})
    if kind != "rowan":
        a.state = "wander"                             # as Enemy starts them
    return SimpleNamespace(actor=a, brain=brain)


def run(d, chars, rowan=None, spells=(), dt=1 / 60, ground=None):
    cues, loops = d.update(chars, rowan, list(spells), (0.0, 1.6, -4.0), dt, ground)
    return [q.sound for q in cues], loops


def test_attack_and_alert_fire_once_when_they_start():
    d, w = SfxDirector(CFG, random.Random(1)), char("wolf", 5.0, 0.0)
    assert run(d, [w]) == ([], {})                     # first sight: nothing "just started"
    w.actor.state = "chase"
    w.actor.play("attack1", restart=True)
    sounds, _ = run(d, [w])
    assert sorted(sounds) == ["wolf/alert", "wolf/attack"]
    w.actor.anim.update(0.1)
    assert run(d, [w])[0] == []                        # same swing, later frame: silent


def test_footsteps_follow_the_walk_cycle_and_the_ground():
    d, r = SfxDirector(CFG, random.Random(1)), char("rowan")
    a = r.actor
    a.play("walk")
    a.speed = 1.4
    run(d, [r], rowan=a)
    steps = []
    for _ in range(60):                                # one second = one walk cycle = two footfalls
        a.anim.update(1 / 60)
        steps += run(d, [r], rowan=a, ground=lambda x, z: "dirt")[0]
    assert steps == ["footsteps/boot_dirt"] * 2


def test_far_away_is_silent_and_rowan_is_not_positional():
    d = SfxDirector(CFG, random.Random(1))
    far, r = char("wolf", 500.0, 0.0), char("rowan")
    run(d, [far, r], rowan=r.actor)
    far.actor.play("attack1", restart=True)
    r.actor.play("light1", restart=True)
    cues, _ = d.update([far, r], r.actor, [], (0.0, 1.6, -4.0), 1 / 60)
    assert [q.sound for q in cues] == ["combat/swing_light"] and cues[0].pos is None


def test_delayed_body_fall_and_pack_gap():
    d = SfxDirector(CFG, random.Random(1))
    r = char("rowan")
    run(d, [r], rowan=r.actor)
    r.actor.play("death", restart=True)
    assert run(d, [r], rowan=r.actor)[0] == ["rowan/death"]
    later = []
    for _ in range(40):
        later += run(d, [r], rowan=r.actor)[0]
    assert later == ["combat/body_fall"]
    pack = [char("wolf", 3.0 + i, 0.0) for i in range(4)]
    run(d, pack)
    for w in pack:
        w.actor.state = "chase"
    assert run(d, pack)[0] == ["wolf/alert"]           # four wolves, one growl


def test_spell_release_loop_and_landing():
    d = SfxDirector(CFG, random.Random(1))
    brain = SimpleNamespace(fired=True)
    m = char("battlemage", 6.0, 0.0, brain)
    run(d, [m])
    m.actor.play("cast", restart=True)
    brain.fired = False
    assert run(d, [m])[0] == ["battlemage/cast"]
    brain.fired = True
    assert run(d, [m])[0] == ["combat/fireball_cast"]
    orb = SimpleNamespace(pos=(6.0, 1.5, 0.0), burst=-1.0)
    _, loops = run(d, [m], spells=[orb])
    assert [v[0] for v in loops.values()] == ["combat/fireball_loop"]
    orb.burst = 0.0
    sounds, loops = run(d, [m], spells=[orb])
    assert sounds == ["combat/fireball_hit"] and loops == {}


def test_cows_moo_now_and_then_and_flinch_at_a_swing():
    d = SfxDirector(CFG, random.Random(1))
    cow, r = char("cow", 2.0, 0.0), char("rowan")
    run(d, [cow, r], rowan=r.actor)
    heard = []
    for _ in range(130):
        heard += run(d, [cow, r], rowan=r.actor)[0]
    assert heard.count("cow/moo") == 2                  # idle_every_s is 1 s here
    r.actor.play("light1", restart=True)
    assert "cow/startled" in run(d, [cow, r], rowan=r.actor)[0]


def test_spatial_pans_and_fades():
    right = (1.0, 0.0, 0.0)
    l, r = spatial((0, 0, 0), right, (10, 0, 0), 4.0, 45.0)
    assert r > l > 0
    l2, r2 = spatial((0, 0, 0), right, (-10, 0, 0), 4.0, 45.0)
    assert l2 == pytest.approx(r) and r2 == pytest.approx(l)
    assert spatial((0, 0, 0), right, (0, 0, 50), 4.0, 45.0) == (0.0, 0.0)
    near = spatial((0, 0, 0), right, (0, 0, 2), 4.0, 45.0)
    assert near[0] == pytest.approx(near[1]) and near[0] > 0.9


def test_every_sound_in_the_data_file_exists():
    cfg = load_sfx_config()
    names = set()
    for k in cfg["kinds"].values():
        for spec in k["events"].values():
            for i in spec if isinstance(spec, list) else [spec]:
                names.add(i if isinstance(i, str) else i["s"])
    names |= {cfg["spell"]["loop"], cfg["spell"]["hit"]}
    names = {n.replace("{ground}", g) for n in names for g in ("grass", "dirt")}
    missing = [n for n in sorted(names) if not list(SFX_DIR.glob(f"{n}_*.mp3"))]
    assert not missing, missing
