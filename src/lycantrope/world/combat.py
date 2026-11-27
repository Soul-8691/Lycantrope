"""Hits: who strikes whom, for how much, and how they react (CMB-37, CMB-42, CMB-43, CMB-45).

A swing hurts during its active window (a fraction of the attack clip, from data/combat.json "moves"),
once per target per swing, if the target is within reach and inside the swing's arc in front of the
attacker. Rowan's swings hit enemies; enemies' swings and spells hit Rowan.

- Counter hits (CMB-45): striking someone during the wind-up of their own attack deals +25% damage and
  poise damage.
- Blocking (CMB-07, Rowan's weapon guard): hits from the front lose most of their physical damage, and
  the rest drains stamina; out of stamina, the guard breaks and he staggers.
- Poise (CMB-10): each hit chips poise; breaking it staggers.

Characters are duck-typed: anything with `.actor`, `.fighter` (stats.Fighter or None), `.brain` and `.t`
(with `.ai` and `.name`), so tests can use small stand-ins.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from lycantrope.world.stats import PHYSICAL, angle_between, config, damage, scaled, shield_block


NEAR_M = 40.0      # only fighters this close to Rowan can hit or be hit (everything far away is skipped)


@dataclass
class Hit:
    attacker: object | None      # the character, or None (a fall)
    target: object
    amount: float
    counter: bool = False
    crit: bool = False
    blocked: bool = False
    staggered: bool = False
    killed: bool = False
    kind: str = "melee"          # melee, spell, plunge, fall


def in_arc(a, b, reach: float, arc_deg: float) -> bool:
    """Is actor b within reach of actor a and inside a's swing arc (half-angle arc_deg)?"""
    dx, dz = b.x - a.x, b.z - a.z
    d = math.hypot(dx, dz)
    if d > reach:
        return False
    if d < 0.3:
        return True
    return math.degrees(angle_between(math.sin(a.heading), math.cos(a.heading), dx, dz)) <= arc_deg


def winding_up(a, cfg: dict) -> bool:
    """Is this actor in the wind-up of an attack (or a cast), before it can hurt?"""
    if a.state == "attack":
        mv = cfg["moves"].get(a.anim.clip)
        start = mv["active"][0] if mv and "active" in mv else cfg["counter"]["windup_before"]
        return a.progress() < start
    return a.state == "cast" and a.progress() < cfg["counter"]["windup_before"]


class Combat:
    def __init__(self, cfg: dict | None = None, seed: int = 11) -> None:
        self.cfg = cfg or config()
        self.rng = random.Random(seed)
        self.swings: dict[int, list] = {}       # id(actor) -> [clip, last time, ids already hit]
        self.hits: list[Hit] = []               # this tick's hits (read by the world, the HUD and sounds)
        self.crit_chance = 0.0                  # Rowan's, in % (from Fortune)
        self.rowan_weapon: dict | None = None   # his equipped weapon (reach and arc); None: the config's

    # ------------------------------------------------------------------ swings
    def _active(self, a):
        """(move spec, ids already hit) while this actor's swing is in its active window, else None."""
        if a.state != "attack":
            self.swings.pop(id(a), None)
            return None
        mv = self.cfg["moves"].get(a.anim.clip)
        if not mv or "active" not in mv:
            return None
        rec = self.swings.get(id(a))
        if rec is None or rec[0] != a.anim.clip or a.anim.time < rec[1]:
            rec = self.swings[id(a)] = [a.anim.clip, a.anim.time, set()]   # a new swing
        rec[1] = a.anim.time
        lo, hi = mv["active"]
        return (mv, rec[2]) if lo <= a.progress() <= hi else None

    def update(self, chars, rowan_c) -> list[Hit]:
        """Resolve this tick's swings. Returns the hits (also kept in self.hits)."""
        self.hits = []
        r = rowan_c.actor if rowan_c is not None else None
        live = [c for c in chars if c.fighter is not None and c.fighter.alive and c.actor.state != "dead"
                and (r is None or (abs(c.actor.x - r.x) < NEAR_M and abs(c.actor.z - r.z) < NEAR_M))]
        rowan_ok = rowan_c is not None and rowan_c in live
        weapon = self.rowan_weapon or self.cfg["weapons"][self.cfg["rowan"]["weapon"]]
        for c in live:
            act = self._active(c.actor)
            if act is None:
                continue
            mv, done = act
            if c is rowan_c:
                targets = [t for t in live if t is not c]
                reach, arc = weapon["reach_m"], weapon["arc_deg"]
            else:
                if not rowan_ok:
                    continue
                targets = [rowan_c]
                ai = getattr(c.t, "ai", None)
                reach, arc = (ai.reach_m if ai else 1.5) * 1.25, 60.0
            for t in targets:
                if id(t) in done:
                    continue
                if in_arc(c.actor, t.actor, reach + t.actor.radius, arc):
                    done.add(id(t))
                    self.strike(c, t, c.fighter.attack, mv["damage"], mv["poise"], rowan_c)
        return self.hits

    # ------------------------------------------------------------------ hits
    def strike(self, att, tgt, attack: dict, mult: float, poise_mult: float, rowan_c, kind: str = "melee",
               source: tuple[float, float] | None = None) -> Hit:
        """att hits tgt with this attack (per-type values) scaled by mult; apply it and the reaction."""
        cfg = self.cfg
        g, ta = tgt.fighter, tgt.actor
        counter = kind == "melee" and winding_up(ta, cfg)
        if counter:
            k = cfg["counter"]["multiplier"]
            mult, poise_mult = mult * k, poise_mult * k
        crit = att is not None and att is rowan_c and kind != "fall" and self.rng.random() * 100 < self.crit_chance
        if crit:
            mult *= cfg["crit_multiplier"]
        atk = scaled(attack, mult)
        poise = (att.fighter.poise_damage if att is not None and att.fighter else 10.0) * poise_mult
        if tgt is rowan_c and ta.state == "attack":     # a committed swing shrugs off part of it (CMB-10)
            poise *= cfg["poise"]["attacking_mult"]
        src = source or ((att.actor.x, att.actor.z) if att is not None else None)
        blocked = guard_broken = False
        bl = cfg["block"]
        if tgt is rowan_c and ta.state == "block" and src is not None and kind in ("melee", "spell"):
            dx, dz = src[0] - ta.x, src[1] - ta.z
            if math.degrees(angle_between(math.sin(ta.heading), math.cos(ta.heading), dx, dz)) <= bl["front_deg"]:
                blocked = True
        if blocked:
            raw = damage(atk, g.defence, g.absorb)
            sh = getattr(tgt, "shield_data", None)
            if sh is not None:
                blk = shield_block(sh)
                amount = sum(
                    damage({t: v}, g.defence, g.absorb) * (1.0 - blk.get(t, 0.0))
                    for t, v in atk.items()
                )
                stamina_drain = sh.get("stamina_drain", bl["stamina_per_damage"])
            else:
                phys = {t: v for t, v in atk.items() if t in PHYSICAL}
                other = {t: v for t, v in atk.items() if t not in PHYSICAL}
                amount = (damage(phys, g.defence, g.absorb) * bl["physical"]
                          + damage(other, g.defence, g.absorb) * bl["other"])
                stamina_drain = bl["stamina_per_damage"]
            guard_broken = not g.drain(raw * stamina_drain)
            poise = 0.0
        else:
            amount = damage(atk, g.defence, g.absorb)
        staggered = g.hurt(amount, poise, src) or guard_broken
        hit = Hit(att, tgt, amount, counter, crit, blocked, staggered, not g.alive, kind)
        self.react(tgt, hit, rowan_c)
        self.hits.append(hit)
        return hit

    def fall(self, c, amount: float, stumble: bool, rowan_c) -> Hit | None:
        """Landing hurt (CMB-38/43): damage with no poise, then a stumble if it was a hard landing."""
        if c.fighter is None or not c.fighter.alive:
            return None
        if amount > 0:
            c.fighter.hurt(amount, 0.0, None)
        hit = Hit(None, c, amount, staggered=stumble, killed=not c.fighter.alive, kind="fall")
        self.react(c, hit, rowan_c)
        if amount > 0 or stumble:
            self.hits.append(hit)
        return hit

    @staticmethod
    def react(c, hit: Hit, rowan_c) -> None:
        """Put the target into its death, stagger or stumble, or just make it angry."""
        a = c.actor
        if hit.killed:
            a.state, a.speed = "dead", 0.0
            a.travel = None
            a.play("death", restart=True)
            return
        if hit.kind == "fall" and hit.staggered and c is rowan_c:
            a.state, a.speed = "stumble", 0.0
            a.play("hit", restart=True, rate=1.4)
            return
        if hit.staggered:
            a.state, a.speed = "hit", 0.0
            if a.has("hit"):
                a.play("hit", restart=True)
                info = a.clips["hit"]
                a.timer = info.duration / max(info.speed, 1e-3)
            else:
                a.play("idle" if not a.has("alert") else "alert")
                a.timer = 0.45
            return
        brain = getattr(c, "brain", None)
        if brain is not None and a.state in ("wander", "idle", "return"):
            a.state = "chase"                       # hit from afar: come and fight

    # ------------------------------------------------------------------ spells and plunges
    def spell_hits(self, spells, rowan_c) -> None:
        """Enemy spells that reach Rowan's body burst on him."""
        if rowan_c is None or rowan_c.fighter is None or not rowan_c.fighter.alive:
            return
        ra = rowan_c.actor
        for s in spells:
            dmg = getattr(s, "damage", None)
            if s.burst >= 0 or not dmg:
                continue
            dx, dy, dz = s.pos[0] - ra.x, s.pos[1] - (ra.y + 1.1), s.pos[2] - ra.z
            if dx * dx + dz * dz < (s.radius + 0.45) ** 2 and abs(dy) < 1.1:
                s.burst = 0.0
                self.strike(None, rowan_c, dmg, 1.0, 1.0, rowan_c, kind="spell", source=getattr(s, "origin", None))

    def plunge(self, rowan_c, chars) -> bool:
        """Rowan lands a plunge (CMB-13/42): the nearest live enemy under him takes a heavy hit."""
        reach = self.cfg["fall"]["plunge_reach_m"]
        ra = rowan_c.actor
        best, best_d = None, reach
        for c in chars:
            if c is rowan_c or c.fighter is None or not c.fighter.alive or c.actor.state == "dead":
                continue
            d = math.hypot(c.actor.x - ra.x, c.actor.z - ra.z) - c.actor.radius
            if d <= best_d:
                best, best_d = c, d
        if best is None:
            return False
        mv = self.cfg["moves"]["plunge"]
        self.strike(rowan_c, best, rowan_c.fighter.attack, mv["damage"], mv["poise"], rowan_c, kind="plunge")
        return True
