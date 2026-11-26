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
        if "like" in k:
            assert k["like"] in cfg["kinds"]
            continue
        for spec in k["events"].values():
            for i in spec if isinstance(spec, list) else [spec]:
                names.add(i if isinstance(i, str) else i["s"])
    names |= {cfg["spell"]["loop"], cfg["spell"]["hit"], cfg["wade_step"]["s"]}
    names |= {l["s"] for k in cfg["kinds"].values() for l in k.get("clip_loops", {}).values()}
    names = {n.replace("{ground}", g) for n in names for g in ("grass", "dirt")}
    names = {n for n in names if not n.startswith("vo/")}        # voice lines: made per voice, checked below
    missing = [n for n in sorted(names) if not list(SFX_DIR.glob(f"{n}_*.mp3"))]
    assert not missing, missing


def test_swimming_strokes_splashes_lapping_and_wading():
    cfg = load_sfx_config()
    d = SfxDirector(cfg, random.Random(1))
    r = char("rowan")
    a = r.actor
    a.clips = dict(CLIPS, swim=ClipInfo(1.5, True), tread=ClipInfo(1.8, True))
    a.state = "move"
    run(d, [r], rowan=a)
    a.state = "swim"                                   # into deep water
    a.play("tread")
    sounds, loops = run(d, [r], rowan=a)
    assert "water/splash_in" in sounds
    assert [v[0] for v in loops.values()] == ["water/tread_loop"]
    a.play("swim")
    a.speed = 1.5
    strokes = []
    for _ in range(90):                                # one stroke cycle = one splash
        a.anim.update(1 / 60)
        strokes += run(d, [r], rowan=a)[0]
    assert strokes.count("water/stroke") == 1
    a.state = "move"                                   # out again, wading in the shallows
    a.play("walk")
    assert "water/splash_out" in run(d, [r], rowan=a)[0]
    steps = []
    for _ in range(60):
        a.anim.update(1 / 60)
        steps += run(d, [r], rowan=a, ground=lambda x, z: "water")[0]
    assert steps == ["water/wade_step"] * 2


def test_npcs_greet_rowan_in_their_own_voice_once_in_a_while():
    cfg = load_sfx_config()
    d = SfxDirector(cfg, random.Random(1))
    r = char("rowan", 0.0, 0.0)
    v = char("villager_m", 10.0, 0.0)
    v.voice = "villager_man_2"
    mute = char("villager_m", -10.0, 0.0)                 # no voice: never speaks
    chars = [r, v, mute]
    run(d, chars, rowan=r.actor)
    v.actor.x, mute.actor.x = 3.0, -3.0                   # Rowan walks up to both
    sounds = run(d, chars, rowan=r.actor)[0]
    assert sounds == ["vo/villager_man_2/greet"]
    v.actor.x = 20.0                                      # walks off and comes straight back: too soon
    run(d, chars, rowan=r.actor)
    v.actor.x = 3.0
    assert run(d, chars, rowan=r.actor)[0] == []
    for _ in range(46 * 60):
        run(d, chars, rowan=r.actor)
    v.actor.x = 20.0
    run(d, chars, rowan=r.actor)
    v.actor.x = 3.0
    assert run(d, chars, rowan=r.actor)[0] == ["vo/villager_man_2/greet"]


def test_mixer_reports_who_started_talking(tmp_path, monkeypatch):
    """The player must hand back (speaker, loudness) for voice lines: that's what makes NPCs stop,
    face Rowan and move their jaw. Runs on SDL's silent 'dummy' audio driver."""
    import numpy as np
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame = pytest.importorskip("pygame")
    try:
        pygame.mixer.init(44100, -16, 2, 512)
    except pygame.error:
        pytest.skip("no audio driver")
    try:
        from lycantrope.audio import sfx as sfx_module
        from lycantrope.audio.sfx import Cue, MixerSfx
        monkeypatch.setattr(sfx_module, "VO_DIR", tmp_path)   # the background loader finds nothing to load
        p = MixerSfx({"ref_m": 4.0, "max_m": 45.0}, 1.0, root=tmp_path)
        import time
        time.sleep(0.2)
        tone = (np.sin(np.arange(4410) * 0.06) * 8000).astype(np.int16)
        snd = pygame.sndarray.make_sound(np.ascontiguousarray(np.stack([tone, tone], axis=1)))
        env = np.ones(3, np.float32)
        p.sounds = {"vo/villager_man_1/greet": [snd], "cow/moo": [snd]}
        p.envelopes = {id(snd): env}
        out = p.play([Cue("vo/villager_man_1/greet", None, speaker=42), Cue("cow/moo", None)], {}, (0, 0, 0), (1, 0, 0))
        assert len(out) == 1 and out[0][0] == 42 and out[0][1] is env and out[0][2] == ""
        p.voices = False                                    # F11: voices off, nobody talks
        assert p.play([Cue("vo/villager_man_1/greet", None, speaker=42)], {}, (0, 0, 0), (1, 0, 0)) == []
    finally:
        pygame.mixer.quit()


def test_every_speaking_npc_has_lines_in_its_own_voice():
    import json
    from lycantrope.core.paths import DATA, ROOT
    lines = json.loads((ROOT / "tools/voice/npc_lines.json").read_text(encoding="utf-8"))["roles"]
    chars = json.loads((DATA / "characters.json").read_text(encoding="utf-8"))["characters"]
    spawns = json.loads((DATA / "world/spawns.json").read_text(encoding="utf-8"))["groups"]
    for g in spawns:
        spec = chars.get(g["kind"], {})
        if not spec.get("voices"):
            continue
        role = g.get("lines") or spec.get("lines")
        assert role in lines, (g["name"], role)
        for v in spec["voices"]:
            assert v in lines[role]["voices"], (g["name"], role, v)
        assert lines[role]["lines"].get("greet"), role
