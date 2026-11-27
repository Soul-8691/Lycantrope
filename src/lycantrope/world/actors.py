"""Characters on the CPU side: animation state, Rowan's controller and simple enemy behaviour.

Health, damage and who-hits-whom live in world/stats.py and world/combat.py; here Rowan only pays
stamina for what he does (when he has a Fighter), and enemies react to being staggered or killed.
Headings: a character's forward is (sin h, 0, cos h) in game coordinates (x east, z south),
so h = 0 faces south (+z, the way Meshy models face) and h = pi faces north.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from lycantrope.core.paths import DATA

FADE_S = 0.15
IDLE_DELAY_S = 3.0      # after stopping, hold still this long before the idle animation plays
TURBO = 4.0                                  # turbo hotkey: movement speed multiplier (Rowan and fly camera)
IDLE_CLIPS = ("idle", "idle2", "idle3")   # standing-still animations; one is picked at random
SWIM_SPEEDS = {"slow": 0.9, "swim": 1.5, "fast": 2.4}   # m/s in deep water (Ctrl, normal, Shift)
JUMP_V = 5.2               # take-off speed (m/s): about a 0.75 m hop
GRAVITY = 18.0             # m/s^2, a little heavier than real for a snappy game jump
AIR_CONTROL = 0.3          # how much Rowan can steer in the air (fraction of his ground acceleration)
LOCK_SIDE_SPEED = 1.9      # m/s strafing round a locked target (the side-step clip, sped up, matches it)
LOCK_BACK_SPEED = 1.7      # m/s backing away from it


@dataclass
class ClipInfo:
    duration: float          # seconds at speed 1
    loop: bool
    speed: float = 1.0       # playback rate from data
    move_speed: float = 0.0  # ground speed the loop was animated for (m/s), 0 = unknown


@dataclass
class AnimState:
    """Current clip and time, plus the previous clip while crossfading."""
    clip: str = "idle"
    time: float = 0.0
    rate: float = 1.0
    prev: str | None = None
    prev_time: float = 0.0
    prev_rate: float = 1.0
    fade: float = 1.0

    def play(self, name: str, restart: bool = False, rate: float = 1.0) -> None:
        if name == self.clip and not restart:
            self.rate = rate
            return
        self.prev, self.prev_time, self.prev_rate = self.clip, self.time, self.rate
        self.clip, self.time, self.rate, self.fade = name, 0.0, rate, 0.0

    def update(self, dt: float) -> None:
        self.time += dt * self.rate
        self.prev_time += dt * self.prev_rate
        self.fade = min(1.0, self.fade + dt / FADE_S)


def heading_to(dx: float, dz: float) -> float:
    return math.atan2(dx, dz)


def turn_towards(h: float, target: float, max_step: float) -> float:
    d = (target - h + math.pi) % math.tau - math.pi
    return h + max(-max_step, min(max_step, d))


@dataclass
class Actor:
    kind: str
    x: float
    z: float
    heading: float
    clips: dict[str, ClipInfo]
    speeds: dict[str, float]
    radius: float = 0.4
    y: float = 0.0
    speed: float = 0.0            # current ground speed (m/s)
    anim: AnimState = field(default_factory=AnimState)
    state: str = "move"
    timer: float = 0.0
    # previous position for render interpolation
    px: float = 0.0
    py: float = 0.0
    pz: float = 0.0
    ph: float = 0.0
    idle_wait: float = 0.0        # seconds spent standing still on the idle's first frame
    gait_scale: float = 1.0       # turbo: speed multiplier the walk/run/sprint choice ignores
    vy: float = 0.0               # vertical speed (m/s) while airborne
    travel: float | None = None   # direction of movement when it differs from facing (strafing)
    airborne: bool = False        # jumping or falling (the world sets y from the ground otherwise)
    fall_top: float | None = None  # highest point since leaving the ground (fall damage)

    def has(self, clip: str) -> bool:
        return clip in self.clips

    def clip_done(self) -> bool:
        info = self.clips.get(self.anim.clip)
        return info is not None and not info.loop and self.anim.time >= info.duration

    def progress(self) -> float:
        info = self.clips.get(self.anim.clip)
        return self.anim.time / info.duration if info and info.duration > 0 else 1.0

    def play(self, clip: str, restart: bool = False, rate: float = 1.0) -> None:
        if clip in self.clips:
            self.anim.play(clip, restart, rate * self.clips[clip].speed)
        else:                                   # rigless or missing clip: still track the name
            self.anim.play(clip, restart, rate)

    def locomotion(self) -> None:
        """Pick idle / walk / run / sprint for the current speed, synced to the clip's stride."""
        s = self.speed / self.gait_scale
        sp = self.speeds
        side = self.side_clip()
        if side and s >= 0.15:                       # locked on: side-step or back away, facing the target
            info = self.clips.get(side)
            rate = max(0.6, min(2.2, s / info.move_speed)) if info and info.move_speed > 0 else 1.0
            self.play(side, rate=rate)
            return
        if s < 0.15:
            if self.anim.clip not in IDLE_CLIPS:
                self.play("idle", rate=0.0)          # first frame (a plain stance) until the wait is over
                self.idle_wait = 0.0
            return
        if "sprint" in sp and s > (sp.get("run", 5) + sp["sprint"]) / 2 and self.has("sprint"):
            name = "sprint"
        elif s > (sp.get("walk", 1.5) + sp.get("run", 5)) / 2:
            name = "run"
        else:
            name = "walk"
        info = self.clips.get(name)
        rate = 1.0
        if info and info.move_speed > 0:
            rate = max(0.6, min(1.7, s / info.move_speed))
        self.play(name, rate=rate)

    def side_clip(self) -> str | None:
        """While strafing (travel differs from facing): 'strafe_left', 'strafe_right' or 'back',
        if this character has that clip; None when moving roughly forward."""
        if self.travel is None:
            return None
        rel = (self.travel - self.heading + math.pi) % math.tau - math.pi   # + = to his left (+x)
        if abs(rel) < math.radians(50):
            return None
        name = "back" if abs(rel) > math.radians(130) else ("strafe_left" if rel > 0 else "strafe_right")
        return name if name in self.clips else None

    def advance(self, dt: float) -> None:
        """Move the animation on; a freshly started idle stays on its first frame for IDLE_DELAY_S."""
        if self.anim.clip == "idle" and self.anim.rate == 0.0:
            self.idle_wait += dt
            if self.idle_wait >= IDLE_DELAY_S:
                choices = [c for c in IDLE_CLIPS if c in self.clips]
                pick = random.choice(choices) if len(choices) > 1 else "idle"
                if pick == "idle":
                    info = self.clips.get("idle")
                    self.anim.rate = info.speed if info else 1.0
                    self.anim.time = 0.0
                else:
                    self.play(pick, restart=True)
        self.anim.update(dt)

    def save_prev(self) -> None:
        self.px, self.py, self.pz, self.ph = self.x, self.y, self.z, self.heading


# ---------------------------------------------------------------------------- #
@dataclass
class RowanInput:
    move_x: float = 0.0      # camera-relative: +x right
    move_y: float = 0.0      # camera-relative: +y forward
    sprint: bool = False
    walk: bool = False
    light: bool = False      # pressed this tick
    heavy: bool = False
    cast: bool = False
    block: bool = False      # held
    hit: bool = False        # debug: play the hit reaction
    die: bool = False        # debug: toggle death
    turbo: bool = False      # debug/travel: move TURBO times faster
    jump: bool = False       # pressed this tick
    sheathe: bool = False    # pressed this tick: put the sword away / draw it
    face: tuple[float, float] | None = None   # lock-on: keep facing this point (x, z) and strafe
    roll: bool = False       # pressed this tick: dodge (for now only the landing roll, CMB-40)


class Rowan:
    LIGHTS = ("light1", "light2", "light3")

    def __init__(self, actor: Actor) -> None:
        self.a = actor
        self.queued = False
        self.swimming = False    # in deep water (set by the world each tick): swim, no fighting
        self.sheathed = True     # sword on his back (he starts in town with it put away)
        self.fighter = None      # stats.Fighter: HP and stamina (None = unlimited, as in tests)
        self.costs: dict[str, float] = {}   # stamina per move ("light1", "heavy", "jump", "sprint_per_s")
        self.attack_rate = 1.0   # Dexterity's attack speed
        self.sprinting = False
        self.plunging = False    # light attack pressed while falling: a plunge on landing (CMB-13)
        self.roll_t = 0.0        # seconds left in which a landing counts as rolled (CMB-40)
        self.roll_window = 0.35

    def pay(self, what: str) -> bool:
        cost = self.costs.get(what, 0.0)
        return self.fighter is None or cost <= 0 or self.fighter.spend(cost)

    def update(self, inp: RowanInput, cam_yaw: float, dt: float) -> None:
        a = self.a
        self.roll_t = self.roll_window if inp.roll else max(0.0, self.roll_t - dt)
        if not a.airborne:
            self.plunging = False
        if inp.die:
            if a.state == "dead":
                a.state = "move"
                a.play("idle", restart=True)
            else:
                a.state = "dead"
                a.play("death", restart=True)
        if a.state == "dead":
            a.speed = 0.0
            return
        if inp.hit and not self.swimming:
            a.state = "hit"
            a.play("hit", restart=True)
        if self.swimming:
            a.state = "swim"                       # no swinging or casting while swimming
        elif a.state == "swim":
            a.state = "move"

        # sheathe / draw: the key toggles; swinging or blocking with it put away draws it first
        if inp.sheathe and a.state in ("move", "block", "swim"):
            self.sheathed = not self.sheathed
        if self.sheathed and (inp.light or inp.heavy or inp.block) and a.state == "move" and not a.airborne:
            self.sheathed = False
            inp = RowanInput(**{**inp.__dict__, "light": False, "heavy": False, "block": False})

        # jumping: from the ground, not mid-swing or in deep water
        if inp.jump and a.state in ("move", "block") and not a.airborne and not self.swimming and self.pay("jump"):
            a.state, a.vy, a.airborne = "move", JUMP_V * (1.0 if not inp.turbo else 1.2), True
            if a.has("jump"):
                a.play("jump", restart=True)
        # a light attack while dropping turns into a plunge (resolved when he lands)
        if inp.light and a.airborne and a.vy < -1.0 and a.state == "move" and not self.plunging:
            self.plunging = True
            if a.has("heavy"):
                a.play("heavy", restart=True, rate=0.6)

        # actions start from free movement (or blocking), on the ground
        if a.state in ("move", "block") and not a.airborne:
            if inp.light and self.pay("light1"):
                a.state, self.queued = "attack", False
                a.play("light1", restart=True, rate=self.attack_rate)
            elif inp.heavy and self.pay("heavy"):
                a.state = "attack"
                a.play("heavy", restart=True, rate=self.attack_rate)
            elif inp.cast:
                a.state = "cast"
                a.play("cast", restart=True)
            elif inp.block:
                if a.state != "block":
                    a.state = "block"
                    a.play("block", restart=True)
            elif a.state == "block":
                a.state = "move"
        elif a.state == "attack":
            if inp.light and a.anim.clip in self.LIGHTS[:2] and a.progress() > 0.3:
                self.queued = True
            if a.clip_done() or (self.queued and a.progress() > 0.8):
                nxt = self.LIGHTS[self.LIGHTS.index(a.anim.clip) + 1] if a.anim.clip in self.LIGHTS[:2] else ""
                if self.queued and nxt and self.pay(nxt):
                    self.queued = False
                    a.play(nxt, restart=True, rate=self.attack_rate)
                else:
                    a.state, self.queued = "move", False
        elif a.state in ("cast", "hit", "stumble", "roll") and a.clip_done():
            a.state = "move"

        # movement
        target = 0.0
        self.sprinting = False
        locked = inp.face is not None and not self.swimming and not inp.sprint   # sprinting breaks the strafe
        travel = a.heading
        if a.state == "roll":
            target = a.speed                            # carry through landing speed; decelerate naturally
        elif a.state in ("move", "swim"):
            mx, my = inp.move_x, inp.move_y
            m = math.hypot(mx, my)
            if m > 1e-3:
                mx, my = mx / m, my / m
                fx, fz = math.sin(cam_yaw), -math.cos(cam_yaw)       # camera forward (flat)
                rx, rz = math.cos(cam_yaw), math.sin(cam_yaw)        # camera right
                dx, dz = fx * my + rx * mx, fz * my + rz * mx
                if locked:
                    a.travel = heading_to(dx, dz)                # move that way, keep facing the target
                else:
                    a.heading = turn_towards(a.heading, heading_to(dx, dz), (5.0 if self.swimming else 12.0) * dt)
                    a.travel = None
                sprint = inp.sprint and (self.fighter is None or not self.fighter.exhausted)
                if self.swimming:
                    target = SWIM_SPEEDS["slow" if inp.walk else "fast" if sprint else "swim"]
                else:
                    target = a.speeds["walk"] if inp.walk else a.speeds["sprint"] if sprint else a.speeds["run"]
                self.sprinting = sprint and not inp.walk and not a.airborne
                if self.sprinting and self.fighter is not None:
                    self.fighter.drain(self.costs.get("sprint_per_s", 0.0) * dt)
                if locked and inp.face is not None:          # slower sideways and backward, like a guarded step
                    fx, fz = inp.face
                    rel = (a.travel - heading_to(fx - a.x, fz - a.z) + math.pi) % math.tau - math.pi
                    if abs(rel) > math.radians(130):
                        target = min(target, LOCK_BACK_SPEED)
                    elif abs(rel) > math.radians(50):
                        target = min(target, LOCK_SIDE_SPEED)
        a.gait_scale = TURBO if inp.turbo else 1.0       # same gait and stride, just covering more ground
        target *= a.gait_scale
        accel = (4.0 if self.swimming else 25.0 if target > a.speed else 30.0) * a.gait_scale
        if a.airborne:
            accel *= AIR_CONTROL                          # mostly keeps the speed he jumped with
        a.speed += max(-accel * dt, min(accel * dt, target - a.speed))
        if locked:
            fx, fz = inp.face
            turn = 20.0 if a.state in ("attack", "cast") and a.progress() < 0.35 else 10.0   # swings snap on
            if a.state in ("move", "block", "attack", "cast"):
                a.heading = turn_towards(a.heading, heading_to(fx - a.x, fz - a.z), turn * dt)
            if a.travel is not None and a.speed > 0.05:
                travel = a.travel
        else:
            a.travel = None
        a.x += math.sin(travel) * a.speed * dt
        a.z += math.cos(travel) * a.speed * dt
        if a.state == "move" and not a.airborne:
            a.locomotion()
        elif a.state == "swim":
            s = a.speed / a.gait_scale
            if s > 0.25:                                   # stroke faster the faster he swims
                a.play("swim", rate=max(0.7, min(1.6, s / SWIM_SPEEDS["swim"])))
            else:
                a.play("tread")


# ---------------------------------------------------------------------------- #
@dataclass
class AiParams:
    aggro_m: float = 18.0
    leash_m: float = 40.0
    reach_m: float = 1.5
    attack_every_s: tuple[float, float] = (1.2, 2.0)
    wander_m: float = 10.0
    # casters: hold this distance and cast ("cast" clip), melee only when Rowan is in reach
    pause_s: tuple[float, float] = (2.0, 6.0)   # wandering: how long to stand between strolls
    on_paths: bool = False             # wander only along paths (villagers: keeps them out of buildings)
    cast_range_m: float = 0.0          # 0 = no ranged attack
    keep_away_m: float = 7.0           # back off a little if Rowan is closer than this (but not in reach)
    cast_every_s: tuple[float, float] = (2.2, 3.4)
    release_at: float = 0.55           # fraction of the cast clip where the spell leaves the hand


class Enemy:
    """Wander near home; chase Rowan when he comes close; swing at him; give up past the leash.
    Casters (cast_range_m > 0) stop at range and throw spells, and only use melee up close."""

    def __init__(self, actor: Actor, home: tuple[float, float], ai: AiParams, seed: int) -> None:
        self.a = actor
        self.home = home
        self.ai = ai
        self.rng = random.Random(seed)
        self.goal: tuple[float, float] | None = None
        self.cooldown = self.rng.uniform(*ai.attack_every_s)
        self.cast_cooldown = self.rng.uniform(0.5, 1.5)
        self.goal_ok = None          # optional check for wander goals: (x0, z0, x1, z1) -> bool
        self.bumped = 0.0            # seconds spent pushing against something solid (set by the world)
        self.route: list[tuple[float, float]] | None = None   # travellers: walk these points in turn
        self.route_i = 0
        self.route_dir = 1
        self.route_loop = False      # True: the route is a circuit; False: walk it back and forth
        self.fired = True
        self.talk_s = 0.0            # seconds left of a line being said to Rowan: stand and face him
        self.circle = self.rng.choice((-1.0, 1.0))
        self.a.state = "wander"
        self.a.timer = self.rng.uniform(0.5, 4.0)

    def should_release(self) -> bool:
        """True once per cast, when the spell leaves the hand (the renderer spawns the projectile)."""
        a = self.a
        if a.state == "cast" and not self.fired and a.progress() >= self.ai.release_at:
            self.fired = True
            return True
        return False

    def _move_to(self, gx: float, gz: float, speed: float, dt: float, turn: float) -> float:
        a = self.a
        dx, dz = gx - a.x, gz - a.z
        d = math.hypot(dx, dz)
        if d > 1e-3:
            a.heading = turn_towards(a.heading, heading_to(dx, dz), turn * dt)
        target = speed if d > 0.3 else 0.0
        a.speed += max(-12 * dt, min(12 * dt, target - a.speed))
        a.x += math.sin(a.heading) * a.speed * dt
        a.z += math.cos(a.heading) * a.speed * dt
        return d

    def set_route(self, points: list[tuple[float, float]], start: int, direction: int) -> None:
        """Travellers: walk the route's points in order; a circuit loops, a road is walked there and
        back with a pause at each end."""
        self.route = list(points)
        self.route_loop = len(points) > 2 and math.dist(points[0], points[-1]) < 3.0
        self.route_i = max(0, min(start, len(points) - 1))
        self.route_dir = 1 if direction >= 0 else -1
        self.goal = self.route[self.route_i]

    def _travel(self, dt: float, turn: float) -> None:
        a, ai, r = self.a, self.ai, self.route
        if self.goal is None:                               # resting at the end of the road
            a.timer -= dt
            a.speed = max(0.0, a.speed - 6 * dt)
            if a.timer <= 0:
                self.goal = r[self.route_i]
        elif self._move_to(*self.goal, a.speeds["walk"], dt, turn) < 1.2 or self.bumped > 2.0:
            self.bumped = 0.0                               # there (or blocked): on to the next point
            i = self.route_i + self.route_dir
            if self.route_loop:
                i %= len(r)
            elif not 0 <= i < len(r):                       # the end: rest, then head back
                self.route_dir = -self.route_dir
                i = self.route_i + self.route_dir
                self.goal = None
                a.timer = self.rng.uniform(*ai.pause_s)
            self.route_i = i
            if self.goal is not None:
                self.goal = r[i]
        a.locomotion()

    def update(self, rowan: Actor, rowan_alive: bool, dt: float) -> None:
        a, ai = self.a, self.ai
        if a.state == "dead":
            a.speed = 0.0
            return
        if a.state == "hit":                            # staggered: stand reeling, then back into the fight
            a.speed = max(0.0, a.speed - 10.0 * dt)
            a.timer -= dt
            if a.timer <= 0.0:
                a.state = "chase" if rowan_alive else "return"
            return
        turn = {"bear": 3.5, "wolf": 7.0}.get(a.kind, 8.0)
        to_r = math.hypot(rowan.x - a.x, rowan.z - a.z)
        from_home = math.hypot(a.x - self.home[0], a.z - self.home[1])
        self.cooldown -= dt
        self.cast_cooldown -= dt
        sp = a.speeds
        if self.talk_s > 0.0 and a.state in ("wander", "idle"):
            # saying something to Rowan: stop where they are and turn to him until the line is done
            self.talk_s -= dt
            a.speed = max(0.0, a.speed - 8.0 * dt)
            a.heading = turn_towards(a.heading, heading_to(rowan.x - a.x, rowan.z - a.z), 5.0 * dt)
            a.locomotion()
            return

        if a.state in ("wander", "idle") and rowan_alive and to_r < ai.aggro_m:
            a.state = "chase"
        if a.state in ("chase", "engage", "attack", "cast") and (not rowan_alive or from_home > ai.leash_m
                                                          or to_r > ai.aggro_m * 2.0):
            a.state, self.goal = "return", None

        if a.state == "wander" and self.route:
            self._travel(dt, turn)
        elif a.state == "wander":
            if self.goal is None:
                a.timer -= dt
                a.speed = max(0.0, a.speed - 6 * dt)
                if a.timer <= 0:
                    for k in range(48 if self.goal_ok is not None else 1):
                        ang = self.rng.uniform(0, math.tau)
                        near = 0.15 if k >= 24 else 0.3              # later tries look closer to home
                        r = self.rng.uniform(near, 1.0) * ai.wander_m
                        g = (self.home[0] + r * math.cos(ang), self.home[1] + r * math.sin(ang))
                        if self.goal_ok is None or self.goal_ok(a.x, a.z, *g):
                            self.goal = g
                            self.bumped = 0.0
                            break
                    else:
                        a.timer = min(self.rng.uniform(1.0, 3.0), ai.pause_s[1])   # nowhere good: try again soon
            else:
                arrived = self._move_to(*self.goal, sp["walk"], dt, turn) < 0.6
                if arrived or self.bumped > 1.5:                 # there, or stuck behind something: stop
                    self.goal = None
                    self.bumped = 0.0
                    a.timer = self.rng.uniform(*ai.pause_s)
            a.locomotion()
        elif a.state == "chase":
            if to_r <= ai.reach_m or (ai.cast_range_m and to_r <= ai.cast_range_m * 0.85):
                a.state = "engage"
            else:
                self._move_to(rowan.x, rowan.z, sp["run"], dt, turn)
                a.locomotion()
        elif a.state == "engage":
            # face Rowan; wolves circle him; swing when the cooldown is up
            dx, dz = rowan.x - a.x, rowan.z - a.z
            a.heading = turn_towards(a.heading, heading_to(dx, dz), turn * dt)
            caster = ai.cast_range_m > 0
            if to_r > (ai.cast_range_m if caster else ai.reach_m * 1.6):
                a.state = "chase"
            elif self.cooldown <= 0 and to_r <= ai.reach_m * 1.15:
                a.state = "attack"                      # in reach: melee (casters use their blade)
                a.speed = 0.0
                melee = ["attack1"] if caster else [c for c in ("attack1", "attack2") if a.has(c)]
                a.play(self.rng.choice(melee or ["attack1"]), restart=True)
            elif caster and self.cast_cooldown <= 0 and to_r > ai.reach_m * 1.6:
                a.state = "cast"                        # at range: throw a spell
                a.speed = 0.0
                self.fired = False
                a.play("cast", restart=True)
            elif caster and to_r < ai.keep_away_m and to_r > ai.reach_m * 1.6:
                # too close for comfort: step back while facing Rowan
                self._move_to(a.x - dx, a.z - dz, sp["walk"], dt, 0.0)
                a.heading = turn_towards(a.heading, heading_to(dx, dz), turn * dt)
                a.locomotion()
            elif a.kind == "wolf":
                # strafe sideways around Rowan at reach distance
                tx = rowan.x - dx / max(to_r, 1e-3) * ai.reach_m * 1.3 + (-dz / max(to_r, 1e-3)) * self.circle * 2.0
                tz = rowan.z - dz / max(to_r, 1e-3) * ai.reach_m * 1.3 + (dx / max(to_r, 1e-3)) * self.circle * 2.0
                self._move_to(tx, tz, sp["walk"] * 1.3, dt, turn * 2)
                a.heading = turn_towards(a.heading, heading_to(dx, dz), turn * dt)
                a.locomotion()
            else:
                a.speed = max(0.0, a.speed - 8 * dt)
                a.play("alert" if a.has("alert") else "idle")
        elif a.state == "cast":
            a.speed = 0.0
            dx, dz = rowan.x - a.x, rowan.z - a.z
            a.heading = turn_towards(a.heading, heading_to(dx, dz), turn * dt)
            if a.clip_done() or (not a.has("cast") and a.anim.time > 1.2):
                a.state = "engage"
                self.cast_cooldown = self.rng.uniform(*ai.cast_every_s)
        elif a.state == "attack":
            a.speed = 0.0
            if a.clip_done() or (not a.has(a.anim.clip) and a.anim.time > 0.9):
                a.state = "engage"
                self.cooldown = self.rng.uniform(*ai.attack_every_s)
                if a.kind == "wolf" and self.rng.random() < 0.4:
                    self.circle = -self.circle
        elif a.state == "return":
            if self._move_to(*self.home, sp["walk"] * 1.8, dt, turn) < 2.0 or self.bumped > 4.0:
                a.state, self.goal, a.timer = "wander", None, self.rng.uniform(1.0, 3.0)
                self.bumped = 0.0
            a.locomotion()


def separate(actors: list[Actor]) -> None:
    """Push overlapping characters apart (no physics yet). All pairs at once with numpy."""
    n = len(actors)
    if n < 2:
        return
    import numpy as np
    pos = np.array([(a.x, a.z) for a in actors])
    rad = np.array([a.radius for a in actors])
    d = pos[None, :, :] - pos[:, None, :]                       # [i, j] = j - i
    dist = np.hypot(d[..., 0], d[..., 1])
    overlap = (rad[:, None] + rad[None, :]) - dist
    np.fill_diagonal(overlap, 0.0)
    hit = (overlap > 0) & (dist > 1e-6)
    if not hit.any():
        return
    push = np.where(hit, overlap / 2 / np.maximum(dist, 1e-6), 0.0)
    move = -(d * push[..., None]).sum(axis=1)                    # away from every overlapping neighbour
    for a, (mx, mz) in zip(actors, move):
        if mx or mz:
            a.x += float(mx)
            a.z += float(mz)


def load_character_data(path: Path = DATA / "characters.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_spawns(path: Path = DATA / "world" / "spawns.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
