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
