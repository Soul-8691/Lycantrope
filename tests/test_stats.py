"""Stats, XP, damage, falls and hits (STA-24..28, CMB-37..45): no window needed."""
import math
from types import SimpleNamespace

import pytest

from lycantrope.world.actors import Actor, ClipInfo, Enemy, AiParams, Rowan, RowanInput
from lycantrope.world.combat import Combat, in_arc
from lycantrope.world.stats import (Fighter, Progress, config, damage, derived, enemy_fighter, fall_fraction,
                                    kill_xp, landing, scaled, soft, xp_to_next)

CFG = config()
CLIPS = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4), "run": ClipInfo(0.7, True, 1.0, 4.6),
         "light1": ClipInfo(1.0, False), "light2": ClipInfo(1.0, False), "light3": ClipInfo(1.0, False),
         "heavy": ClipInfo(1.5, False), "block": ClipInfo(3.0, True), "hit": ClipInfo(0.8, False),
         "death": ClipInfo(2.0, False), "attack1": ClipInfo(1.0, False)}


def test_soft_caps_slow_down_past_20_and_40():
    k = CFG["soft_caps"]
    assert soft(10, k) == 10 and soft(20, k) == 20
    assert soft(30, k) == pytest.approx(27.5) and soft(40, k) == pytest.approx(35)
    assert soft(50, k) == pytest.approx(38.5)


def test_rowan_starts_as_a_fit_farmhand():
    p = Progress()
    assert p.level == 20 and p.attrs["vigor"] == 35 and p.attrs["endurance"] == 22 and p.attrs["might"] == 22
    d = p.stats()
    assert d["hp"] == pytest.approx(831.25) and d["stamina"] == pytest.approx(108.75)
    assert derived({**p.attrs, "vigor": 40}, 1)["hp"] == pytest.approx(925)          # "about 1,000"
    assert d["rite_power"] == pytest.approx(118)


def test_xp_curve_and_kill_xp():
    assert xp_to_next(1) == 100 and xp_to_next(4) == 800
    assert kill_xp(100, 5, 5) == 100
    assert kill_xp(100, 7, 5) == 130                        # tougher: more
    assert kill_xp(100, 1, 20) == 25                        # far weaker: the 0.25x floor
    assert kill_xp(100, 30, 1) == 200                       # the 2x ceiling


def test_levelling_spends_xp_one_point_per_level_up_to_the_cap():
    p = Progress()
    assert not p.ready()
    n = p.level
    p.gain(xp_to_next(n) + xp_to_next(n + 1) - 1)
    assert p.ready() and p.affordable() == 1                # one short of the second level-up
    assert not p.apply({"vigor": 2})
    assert p.apply({"vigor": 1}) and p.level == n + 1 and p.attrs["vigor"] == p.cfg["rowan"]["attributes"]["vigor"] + 1
    assert p.xp == xp_to_next(n + 1) - 1 and not p.ready()
    p.level = p.cap
    p.gain(10 ** 9)
    assert not p.ready() and p.affordable() == 0


def test_death_rolls_xp_back_to_the_last_save():
    p = Progress()
    p.gain(150)
    p.save()
    p.gain(500)
    p.apply({"might": 1})
    p.flask = 0
    p.discovered.add("Somewhere")
    p.restore()
    assert p.xp == 150 and p.level == 20 and p.attrs["might"] == 22 and p.flask == 3
    assert "Somewhere" not in p.discovered


def test_damage_formula_keeps_a_tenth_through_any_armor():
    assert damage({"slash": 40}, {"slash": 40}) == pytest.approx(20)
    assert damage({"slash": 40}, {"slash": 0}) == pytest.approx(40)
    assert damage({"slash": 10}, {"slash": 10000}) == pytest.approx(1.0)              # never below 10%
    assert damage({"fire": 40}, {"fire": 40}, {"fire": 0.5}) == pytest.approx(10)
    assert damage({"slash": 40, "radiant": 10}, {"slash": 40, "radiant": 0}) == pytest.approx(30)


def test_fall_damage_ramps_and_kills():
    assert fall_fraction(3.9) == 0.0
    assert fall_fraction(4.0) == pytest.approx(0.10)
    assert fall_fraction(8.0) == pytest.approx(0.45)
    assert fall_fraction(12.0) == pytest.approx(0.80)
    assert fall_fraction(16.0) >= 1.0
    assert landing(3.0, 300) == (0.0, True)                  # a stumble, no damage
    assert landing(1.0, 300) == (0.0, False)
    dmg, st = landing(8.0, 300)
    assert dmg == pytest.approx(135) and st
    dmg, st = landing(8.0, 300, rolled=True)                 # landing roll: half, no stumble
    assert dmg == pytest.approx(67.5) and not st
    assert landing(30.0, 300, water_depth=2.0) == (0.0, False)
    assert landing(30.0, 300, water_depth=1.0)[0] > 300     # shallow water doesn't save you
    assert landing(9.0, 300, plunged=True) == (0.0, False)


def test_fighter_trail_heals_and_poise():
    f = Fighter("x", 1, 100.0, {"slash": 10}, {}, poise_max=20.0, max_stamina=80.0)
    assert not f.hurt(30, 10)
    assert f.hp == 70 and f.trail == 100
    f.update(0.5)
    assert f.trail == 100                                   # the pale segment waits...
    f.update(0.4)
    assert 70 < f.trail < 100                               # ...then drains
    assert f.hurt(5, 15)                                    # poise broken: a stagger
    f.heal(30, 3.0)
    for _ in range(4 * 60):
        f.update(1 / 60)
    assert f.hp == pytest.approx(95, abs=0.6)
    assert f.spend(70) and f.spend(20) and f.stamina == 0 and f.exhausted
    assert not f.spend(1)
    for _ in range(90):
        f.update(1 / 60)
    assert not f.exhausted and f.stamina > 20


def actor(kind="rowan", x=0.0, z=0.0, heading=0.0):
    return Actor(kind, x, z, heading, dict(CLIPS), {"walk": 1.6, "run": 5.0, "sprint": 7.5})


def char(a, fighter, brain=None, ai=None):
    return SimpleNamespace(actor=a, fighter=fighter, brain=brain, t=SimpleNamespace(ai=ai, name=fighter.name))


def setup_fight():
    p = Progress()
    ra = actor()
    r = Rowan(ra)
    r.sheathed = False                                      # sword already drawn
    rc = char(ra, p.fighter())
    r.fighter = rc.fighter
    ga = actor("goblin", 0.0, 1.5, math.pi)                 # in front of Rowan (he faces +z), facing him
    ai = AiParams()
    gc = char(ga, enemy_fighter("goblin", "Goblin"), Enemy(ga, (0.0, 1.5), ai, 1), ai)
    return r, rc, gc


def run_swing(combat, chars, rc, r, inp, ticks=70):
    hits = []
    for i in range(ticks):
        r.update(inp if i == 0 else RowanInput(), 0.0, 1 / 60)
        r.a.advance(1 / 60)
        hits += combat.update(chars, rc)
    return hits


def test_rowan_swing_hits_once_and_costs_stamina():
    r, rc, gc = setup_fight()
    r.costs = {"light1": 14}
    combat = Combat(seed=1)
    hits = run_swing(combat, [rc, gc], rc, r, RowanInput(light=True))
    assert len(hits) == 1 and hits[0].target is gc
    assert gc.fighter.hp == pytest.approx(90 - hits[0].amount) and 30 < hits[0].amount < 65
    assert rc.fighter.stamina == pytest.approx(rc.fighter.max_stamina - 14)
    assert gc.actor.state in ("chase", "hit")               # staggered or angry: either way it's coming


def test_swing_misses_behind_and_out_of_reach():
    r, rc, gc = setup_fight()
    gc.actor.z = -1.5                                       # behind him
    assert not run_swing(Combat(), [rc, gc], rc, r, RowanInput(light=True))
    gc.actor.z = 5.0                                        # too far
    assert not in_arc(rc.actor, gc.actor, 2.1, 70)


def test_counter_hit_during_windup_does_more():
    r, rc, gc = setup_fight()
    plain = run_swing(Combat(seed=1), [rc, gc], rc, r, RowanInput(light=True))[0]
    r, rc, gc = setup_fight()
    gc.actor.state = "attack"
    gc.actor.play("attack1", restart=True, rate=0.05)       # a very slow wind-up: still winding up when hit
    hit = run_swing(Combat(seed=1), [rc, gc], rc, r, RowanInput(light=True))[0]
    assert hit.counter and hit.amount > plain.amount
    assert hit.amount == pytest.approx(damage(scaled(rc.fighter.attack, 1.25), gc.fighter.defence))


def test_blocking_from_the_front_soaks_and_breaks_the_guard():
    r, rc, gc = setup_fight()
    combat = Combat()
    rc.actor.state = "block"
    hit = combat.strike(gc, rc, gc.fighter.attack, 1.0, 1.0, rc)
    assert hit.blocked and not hit.staggered
    full = damage(gc.fighter.attack, rc.fighter.defence)
    assert hit.amount == pytest.approx(full * 0.4)
    rc.fighter.stamina = 1.0                                # nearly spent: the guard breaks
    rc.actor.state = "block"
    hit = combat.strike(gc, rc, gc.fighter.attack, 1.0, 1.0, rc)
    assert hit.blocked and hit.staggered and rc.actor.state == "hit"


def test_kill_puts_enemy_down_and_it_stops():
    r, rc, gc = setup_fight()
    combat = Combat()
    gc.fighter.hp = 1.0
    hit = combat.strike(rc, gc, rc.fighter.attack, 1.0, 1.0, rc)
    assert hit.killed and gc.actor.state == "dead" and gc.actor.anim.clip == "death"
    gc.brain.update(rc.actor, True, 1 / 60)
    assert gc.actor.state == "dead"


def test_stagger_then_back_to_the_fight():
    r, rc, gc = setup_fight()
    combat = Combat()
    gc.fighter.poise = 1.0
    hit = combat.strike(rc, gc, rc.fighter.attack, 1.0, 1.0, rc)
    assert hit.staggered and gc.actor.state == "hit"
    for _ in range(80):
        gc.brain.update(rc.actor, True, 1 / 60)
    assert gc.actor.state != "hit"


def test_plunge_hits_the_enemy_below():
    r, rc, gc = setup_fight()
    gc.actor.z = 1.0
    combat = Combat()
    assert combat.plunge(rc, [rc, gc])
    assert combat.hits[0].kind == "plunge" and combat.hits[0].amount > 60
    gc.actor.z = 6.0
    assert not Combat().plunge(rc, [rc, gc])


def test_exhausted_rowan_cannot_swing_or_sprint():
    r, rc, gc = setup_fight()
    r.costs = {"light1": 14, "sprint_per_s": 12}
    rc.fighter.stamina, rc.fighter.exhausted = 0.0, True
    r.update(RowanInput(light=True), 0.0, 1 / 60)
    assert r.a.state == "move"
    r.a.heading = math.pi
    for _ in range(60):
        r.update(RowanInput(move_y=1.0, sprint=True), 0.0, 1 / 60)
    assert r.a.speed == pytest.approx(5.0)                  # runs, can't sprint


def test_hud_fades_when_calm_and_points_at_the_attacker():
    import math as m
    from lycantrope.ui.hud import HudState, hp_bar_px
    assert hp_bar_px(300) == 185 and hp_bar_px(925) > 330           # the bar grows with max HP
    s = HudState()
    for _ in range(int(4.5 * 60)):
        s.update(1 / 60, full=True, fighting=False)
    assert s.alpha == 0.0                                           # full and quiet: faded out
    s.event(("hurt", 20.0, (0.0, -5.0), "melee"))
    s.update(1 / 60, full=False, fighting=True)
    assert s.alpha > 0.0 and s.arc_t > 0
    # camera looking north (yaw 0): an attacker to the north is straight up, one to the east is right
    assert HudState.arc_direction((0.0, -5.0), (0.0, 0.0), 0.0) == pytest.approx(0.0)
    assert HudState.arc_direction((5.0, 0.0), (0.0, 0.0), 0.0) == pytest.approx(m.pi / 2)
    s.event(("xp", 34, "Grey Wolf"))
    assert s.notes[-1][0] == "+34 XP   Grey Wolf"


def test_poise_refills_gradually_and_grace_stops_a_stun_lock():
    po = CFG["poise"]
    f = Fighter("Rowan", 1, 500.0, {"slash": 10}, {}, poise_max=20.0, max_stamina=80.0,
                stagger_grace=po["stagger_grace_s"])
    assert not f.hurt(1, 15) and f.poise == 5
    f.update(po["regen_delay_s"] * 0.9)
    assert f.poise == 5                                     # waits after a hit...
    f.update(0.2)
    assert 5 < f.poise < 20                                 # ...then refills bit by bit, not all at once
    assert f.hurt(1, 30)                                    # broken: a stagger
    assert not f.hurt(1, 30) and not f.hurt(1, 30)          # grace: no second stagger straight away
    for _ in range(int(po["stagger_grace_s"] * 60) + 2):
        f.update(1 / 60)
    assert f.hurt(1, 30)                                    # grace over
    e = Fighter("Wolf", 1, 80.0, {"pierce": 10}, {}, poise_max=8.0)
    assert e.hurt(1, 9) and e.hurt(1, 9)                    # enemies get no grace: combos still stagger them
