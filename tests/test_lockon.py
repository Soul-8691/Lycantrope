"""Lock-on targeting (no GPU): picking, switching, letting go, and Rowan strafing round the target."""
import math
from types import SimpleNamespace

import pytest

from lycantrope.world.actors import Actor, AiParams, ClipInfo, Rowan, RowanInput
from lycantrope.world.lockon import KEEP_M, LockOn

CLIPS = {"idle": ClipInfo(2.0, True), "walk": ClipInfo(1.0, True, 1.0, 1.4), "run": ClipInfo(0.8, True, 1.0, 4.6)}


def npc(kind, x, z, aggro=16.0):
    a = Actor(kind, x, z, 0.0, CLIPS, {"walk": 1.4, "run": 4.0})
    a.state = "wander"
    return SimpleNamespace(actor=a, brain=object(), t=SimpleNamespace(ai=AiParams(aggro_m=aggro), name=kind))


def scene():
    rowan = Actor("rowan", 0.0, 0.0, 0.0, CLIPS, {"walk": 1.6, "run": 5.0, "sprint": 7.5})
    ahead = npc("goblin", 0.0, -10.0)          # the camera looks north (-z)
    right = npc("wolf", 6.0, -9.0)
    left = npc("bandit_lean", -7.0, -8.0)
    behind = npc("bear", 0.0, 8.0)
    villager = npc("villager_m", 0.5, -4.0, aggro=0.0)
    far = npc("goblin", 0.0, -40.0)
    return rowan, [ahead, right, left, behind, villager, far]


def test_lock_picks_the_enemy_in_the_middle_of_the_view():
    rowan, chars = scene()
    lock = LockOn()
    lock.toggle(chars, rowan, 0.0, 4.0, 0.0, -1.0)         # camera behind Rowan, looking north
    assert lock.target is chars[0]                        # not the villager, not the bear behind, not the far one
    lock.toggle(chars, rowan, 0.0, 4.0, 0.0, -1.0)
    assert lock.target is None                            # pressing again lets go


def test_flick_switches_left_and_right():
    rowan, chars = scene()
    lock = LockOn()
    lock.toggle(chars, rowan, 0.0, 4.0, 0.0, -1.0)
    lock.mouse(130.0, chars, rowan, 0.0, 4.0)             # a quick flick to the right
    assert lock.target is chars[1]
    lock.update(0.5, rowan)                               # wait out the cooldown
    lock.mouse(-130.0, chars, rowan, 0.0, 4.0)
    assert lock.target is chars[0]
    lock.update(0.5, rowan)
    lock.mouse(-40.0, chars, rowan, 0.0, 4.0)             # a small nudge doesn't switch
    assert lock.target is chars[0]


def test_lock_lets_go_when_the_target_dies_or_gets_away():
    rowan, chars = scene()
    lock = LockOn()
    lock.toggle(chars, rowan, 0.0, 4.0, 0.0, -1.0)
    chars[0].actor.state = "dead"
    lock.update(1 / 60, rowan)
    assert lock.target is None
    lock.toggle(chars, rowan, 0.0, 4.0, 0.0, -1.0)
    lock.target.actor.z = -(KEEP_M + 5.0)
    lock.update(1 / 60, rowan)
    assert lock.target is None


def test_rowan_strafes_facing_the_target():
    a = Actor("rowan", 0.0, 0.0, 0.0, CLIPS, {"walk": 1.6, "run": 5.0, "sprint": 7.5})
    r = Rowan(a)
    target = (0.0, -10.0)                                  # north of him
    for _ in range(90):                                    # hold "right" with the camera looking north
        r.update(RowanInput(move_x=1.0, face=target), 0.0, 1 / 60)
    at_target = math.atan2(target[0] - a.x, target[1] - a.z)   # where the target is from where he stands
    assert abs((a.heading - at_target + math.pi) % math.tau - math.pi) < 0.1
    assert a.x > 3.0 and abs(a.z) < 0.5                     # moved east, sideways to his facing
    for _ in range(30):                                    # sprinting breaks the strafe: he turns to run
        r.update(RowanInput(move_x=1.0, sprint=True, face=target), 0.0, 1 / 60)
    assert abs((a.heading - math.atan2(1.0, 0.0) + math.pi) % math.tau - math.pi) < 0.2
