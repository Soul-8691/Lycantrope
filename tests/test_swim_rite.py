"""Swimming (code-made strokes, Rowan's swim controls) and the Rite effect's timeline. No GPU."""
import numpy as np
import pytest

from lycantrope.core.paths import ASSETS
from lycantrope.world.actors import SWIM_SPEEDS, Actor, ClipInfo, Rowan, RowanInput

RIG = ASSETS / "models" / "meshy" / "HER-09" / "v1" / "rig" / "rigged.glb"


@pytest.mark.skipif(not RIG.exists(), reason="Rowan's rig isn't checked out")
def test_swim_clips_keep_bone_lengths_and_float_the_head():
    from lycantrope.render.gltf import load_skeleton
    from lycantrope.render.procedural import make_swim_clips
    skel = load_skeleton(RIG)
    clips = make_swim_clips(skel)
    assert set(clips) == {"swim", "tread"}
    bind = skel.bind_world()
    j = skel.joint_index
    for name, (clip, level) in clips.items():
        assert clip.loop and len(clip.world) > 30
        for a, b in (("LeftArm", "LeftForeArm"), ("RightForeArm", "RightHand"), ("LeftUpLeg", "LeftLeg")):
            rest = np.linalg.norm(bind[j(b), :3, 3] - bind[j(a), :3, 3])
            now = np.linalg.norm(clip.world[:, j(b), :3, 3] - clip.world[:, j(a), :3, 3], axis=1)
            assert np.allclose(now, rest, atol=1e-4)
        # the top of the head stays above the water the whole stroke
        assert clip.world[:, j("head_end"), 1, 3].min() > level + 0.15
    swim = clips["swim"][0].world
    assert swim[:, j("LeftHand"), 2, 3].max() > 0.6      # arms reach out ahead in the glide


def rowan():
    clips = {"idle": ClipInfo(2.0, True), "run": ClipInfo(0.8, True, 1.0, 4.6), "swim": ClipInfo(1.5, True),
             "tread": ClipInfo(1.8, True), "cast": ClipInfo(1.9, False), "light1": ClipInfo(0.6, False)}
    return Rowan(Actor("rowan", 0.0, 0.0, 0.0, clips, {"walk": 1.6, "run": 5.0, "sprint": 7.5}))


def test_rowan_swims_slower_and_cannot_fight_in_deep_water():
    r = rowan()
    r.swimming = True
    for _ in range(240):
        r.update(RowanInput(move_y=1.0, sprint=True, light=True, cast=True), 0.0, 1 / 60)
    a = r.a
    assert a.state == "swim" and a.anim.clip == "swim"
    assert a.speed == pytest.approx(SWIM_SPEEDS["fast"], abs=0.05)
    for _ in range(240):                                     # let go of the keys: tread water
        r.update(RowanInput(), 0.0, 1 / 60)
    assert a.anim.clip == "tread"
    r.swimming = False                                       # out of the water: back on his feet
    r.update(RowanInput(cast=True), 0.0, 1 / 60)
    assert a.state == "cast"


def test_rite_effect_gathers_flashes_and_fades():
    from lycantrope.render.rites import AFTER_S, RiteEffect
    fx = RiteEffect.__new__(RiteEffect)                      # timeline only: no GL objects needed
    fx.t, fx.release_s, fx.cancelled_at = -1.0, 0.6, -1.0
    fx.begin(0.6)
    fx.update(0.3)
    mid = fx.levels()
    assert 0.03 < mid["orb_r"] < 0.14 and mid["flash_s"] == 0 and mid["ward_s"] == 0
    fx.update(0.35)
    rel = fx.levels()
    assert rel["flash_s"] > 1.0 and rel["ward_s"] > 1.0 and rel["ring_s"] > mid["ring_s"]
    fx.update(AFTER_S)
    assert not fx.active
    fx.begin(0.6)                                            # interrupted before the release
    fx.update(0.2)
    fx.cancel()
    fx.update(0.3)
    assert not fx.active


@pytest.mark.skipif(not RIG.exists(), reason="Rowan's rig isn't checked out")
def test_mirrored_cast_uses_the_left_hand():
    from lycantrope.render.gltf import load_skeleton
    from lycantrope.render.procedural import mirror_clip
    skel = load_skeleton(RIG)
    src = RIG.with_name("animations_1.glb")
    clip = skel.bake(src, "mage_soell_cast", False)
    m = mirror_clip(skel, clip)
    assert np.abs(mirror_clip(skel, m).world - clip.world).max() < 1e-4     # twice = no change
    j = skel.joint_index
    assert m.world[:, j("LeftHand"), 1, 3].max() > m.world[:, j("RightHand"), 1, 3].max() + 0.5
    # the left hand now goes where the right hand went, across the middle
    i = int(np.argmax(clip.world[:, j("RightHand"), 1, 3]))
    a, b = m.world[i, j("LeftHand"), :3, 3], clip.world[i, j("RightHand"), :3, 3]
    assert np.allclose(a, b * [-1, 1, 1], atol=0.02)


def test_npc_stops_and_faces_rowan_while_talking():
    import math
    from lycantrope.world.actors import AiParams, Enemy
    clips = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4)}
    a = Actor("villager_m", 0.0, 0.0, 0.0, clips, {"walk": 1.4, "run": 4.0})
    rowan_a = Actor("rowan", 3.0, 0.0, 0.0, clips, {"walk": 1.6, "run": 5.0})
    e = Enemy(a, (0.0, 0.0), AiParams(aggro_m=0, wander_m=20, pause_s=(0.3, 1.0)), seed=2)
    e.goal, a.timer, a.speed = (0.0, -20.0), 0.0, 1.4       # walking away from Rowan
    e.talk_s = 2.0
    for _ in range(90):
        e.update(rowan_a, True, 1 / 60)
    assert a.speed < 0.05
    assert abs((a.heading - math.atan2(3.0, 0.0) + math.pi) % math.tau - math.pi) < 0.1   # facing Rowan
    for _ in range(120):                                     # line over: back to their errand
        e.update(rowan_a, True, 1 / 60)
    assert e.talk_s <= 0 and a.speed > 0.3


def test_loudness_envelope_follows_the_line():
    from lycantrope.audio.sfx import TALK_FPS, loudness
    rate = 44100
    t = np.arange(rate) / rate
    tone = (np.sin(2 * np.pi * 220 * t) * 8000 * (t > 0.5)).astype(np.int16)   # silent, then speech
    env = loudness(np.stack([tone, tone], axis=1), rate)
    assert len(env) == TALK_FPS
    assert env[: TALK_FPS // 2 - 1].max() == 0.0 and env[TALK_FPS // 2 + 1:].min() > 0.9


@pytest.mark.skipif(not RIG.exists(), reason="Rowan's rig isn't checked out")
def test_jaw_takes_the_chin_and_keeps_weights_whole():
    from types import SimpleNamespace
    from lycantrope.render.characters import add_jaw, jaw_matrix
    from lycantrope.render.gltf import load_mesh, load_skeleton
    skel, body = load_skeleton(RIG), load_mesh(RIG)
    t = SimpleNamespace(jaw=-1, jaw_of=-1, jaw_pivot=None, jaw_axis=None)
    add_jaw(t, body, skel)
    assert t.jaw == len(skel.names)
    on_jaw = (body.joints == t.jaw).any(axis=1)
    assert 20 < on_jaw.sum() < len(body.pos) * 0.05            # some of the face, not the whole head
    assert np.allclose(body.weights.sum(axis=1), 1.0, atol=1e-4)
    assert np.allclose(jaw_matrix(t, 0.0), np.eye(4))


def test_rowan_jumps_about_three_quarters_of_a_metre_and_lands():
    from types import SimpleNamespace
    from lycantrope.render.characters import CharacterSystem
    r = rowan()
    a = r.a
    a.clips["jump"] = ClipInfo(0.6, False)
    world = SimpleNamespace(height_at=lambda x, z: 0.0, water_at=lambda x, z: -10.0)
    drops = []
    sysm = SimpleNamespace(world=world, colliders=None, _landed=lambda c, d: drops.append(d))
    c = SimpleNamespace(actor=a)
    r.update(RowanInput(jump=True), 0.0, 1 / 60)
    assert a.airborne and a.anim.clip == "jump"
    peak, steps = 0.0, 0
    while a.airborne and steps < 200:
        r.update(RowanInput(light=True), 0.0, 1 / 60)          # swinging mid-air starts no attack
        assert a.state == "move"
        CharacterSystem._fly(sysm, c, 1 / 60, 1000.0)
        peak, steps = max(peak, a.y), steps + 1
    assert 0.6 < peak < 0.9 and not a.airborne and a.y == 0.0
    assert 30 < steps < 45                                       # about 0.6 s in the air
    assert len(drops) == 1 and drops[0] == pytest.approx(peak, abs=0.01)   # the landing knows the drop
    assert r.plunging                                            # light while dropping: a plunge (no enemy below)
    r.update(RowanInput(jump=True), 0.0, 1 / 60)                 # and can jump again once down
    assert a.airborne


def test_subtitles_show_who_said_what_and_fade():
    from lycantrope.ui.overlay import Subtitles
    sub = Subtitles(text=None)
    sub.say("Merchant", "Morning! Fine weather for it.", 1.0)
    sub.say("Watch guard", "All quiet. For now.", 4.0)
    sub.say("Weaver", "Sit. Eat something.", 4.0)
    assert sub.shown() == ["Watch guard: All quiet. For now.", "Weaver: Sit. Eat something."]   # newest two
    sub.update(5.0)
    assert sub.shown() == []
