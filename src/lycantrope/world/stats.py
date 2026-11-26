"""Stats, experience, health and damage (STA-24..28, CMB-37..45). Plain Python, tested without a window.

The numbers live in data/combat.json. This module turns them into:
- `derived(attrs, level)`: HP, stamina, equip load, defence, Rite power... with STA-05's soft caps;
- `damage(attack, defence, absorb)`: CMB-37's formula, per damage type;
- `landing(drop_m, ...)`: fall damage, stumbles, landing rolls, water and plunges (CMB-38..42);
- `Fighter`: anyone who can be hurt (HP with a trailing "damage" segment, stamina, poise, heals over time);
- `Progress`: Rowan's level, XP, attributes, flask and food, with a snapshot that a death rolls back to (STA-28).
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from lycantrope.core.paths import DATA

TYPES = ("slash", "strike", "pierce", "fire", "frost", "radiant")
PHYSICAL = ("slash", "strike", "pierce")

_CFG: dict | None = None


def load_combat(path: Path = DATA / "combat.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def config() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = load_combat()
    return _CFG


# ---------------------------------------------------------------------------- formulas
def soft(points: float, knots) -> float:
    """Attribute points counted through the soft caps: knots [[up_to, rate], ...]."""
    total, prev = 0.0, 0.0
    for upto, rate in knots:
        seg = min(points, upto) - prev
        if seg <= 0:
            break
        total += seg * rate
        prev = upto
    return total


def derived(attrs: dict, level: int, cfg: dict | None = None) -> dict[str, float]:
    """Every derived stat (STA-27) for these attributes at this level."""
    cfg = cfg or config()
    k = cfg["soft_caps"]
    f = {a: soft(v, k) for a, v in attrs.items()}
    out = {}
    for name, spec in cfg["derived"].items():
        out[name] = (spec["base"] + spec.get("per_level", 0.0) * level
                     + sum(w * f.get(a, 0.0) for a, w in spec["from"].items()))
    return out


def xp_to_next(level: int, cfg: dict | None = None) -> int:
    """STA-01: 100 * L^1.5."""
    x = (cfg or config())["xp"]
    return int(round(x["curve_base"] * level ** x["curve_power"]))


def kill_xp(base: float, enemy_level: int, rowan_level: int, cfg: dict | None = None) -> int:
    """STA-01: more for tougher foes, less for weaker ones (0.25x to 2x)."""
    x = (cfg or config())["xp"]
    mult = 1.0 + x["per_level_difference"] * (enemy_level - rowan_level)
    return int(round(base * max(x["min_multiplier"], min(x["max_multiplier"], mult))))


def weapon_attack(weapon: dict, attrs: dict, cfg: dict | None = None) -> dict[str, float]:
    """A weapon's damage per type with Rowan's attributes: physical parts scale with Might and Dexterity,
    the rest (radiant, fire...) with Faith, by the weapon's grades (STA-09)."""
    cfg = cfg or config()
    k, grades, pts = cfg["soft_caps"], cfg["scaling_grades"], cfg["scaling_points"]
    sc = weapon.get("scaling", {})

    def bonus(names):
        return sum(grades.get(sc.get(a, ""), 0.0) * soft(attrs.get(a, 0), k) / pts for a in names)
    phys, other = 1.0 + bonus(("might", "dexterity")), 1.0 + bonus(("faith",))
    return {t: v * (phys if t in PHYSICAL else other) for t, v in weapon["damage"].items()}


def damage(attack: dict, defence: dict, absorb: dict | None = None, min_fraction: float | None = None) -> float:
    """CMB-37, summed over damage types: atk * atk / (atk + def), times (1 - absorb), at least
    min_fraction of the attack."""
    if min_fraction is None:
        min_fraction = config()["min_fraction"]
    absorb = absorb or {}
    total = 0.0
    for t, atk in attack.items():
        if atk <= 0:
            continue
        d = max(0.0, defence.get(t, 0.0))
        dmg = atk * atk / (atk + d) * (1.0 - min(0.95, absorb.get(t, 0.0)))
        total += max(dmg, atk * min_fraction)
    return total


def scaled(attack: dict, k: float) -> dict:
    return {t: v * k for t, v in attack.items()}


def flat_defence(value: float) -> dict[str, float]:
    return {t: value for t in TYPES}


def fall_fraction(drop_m: float, cfg: dict | None = None) -> float:
    """CMB-38: the share of max HP a fall of drop_m costs (0 below the safe height, 1+ = deadly)."""
    f = (cfg or config())["fall"]
    if drop_m < f["safe_m"]:
        return 0.0
    if drop_m > f["kill_m"]:
        return 10.0
    ramp = f["ramp"]
    for (h0, v0), (h1, v1) in zip(ramp, ramp[1:]):
        if drop_m <= h1:
            return v0 + (v1 - v0) * (drop_m - h0) / (h1 - h0)
    return ramp[-1][1]


def landing(drop_m: float, max_hp: float, rolled: bool = False, water_depth: float = 0.0,
            plunged: bool = False, cfg: dict | None = None) -> tuple[float, bool]:
    """(damage, stumble) for landing after a drop of drop_m metres (CMB-38..42).
    Deep water and a plunge onto an enemy cancel it; a landing roll halves it and skips the stumble."""
    f = (cfg or config())["fall"]
    if water_depth >= f["water_depth_m"] or plunged:
        return 0.0, False
    dmg = fall_fraction(drop_m, cfg) * max_hp
    if rolled:
        return dmg * f["roll_factor"], False
    return dmg, drop_m >= f["stumble_m"]


# ---------------------------------------------------------------------------- fighters
@dataclass
class Fighter:
    """Anyone who can be hurt. HP has a trailing pale segment (UIX-16); stamina is only used when
    max_stamina > 0 (Rowan)."""
    name: str
    level: int
    max_hp: float
    attack: dict
    defence: dict
    absorb: dict = field(default_factory=dict)
    poise_max: float = 10.0
    poise_damage: float = 10.0
    xp: float = 0.0
    weight: float = 1.0
    max_stamina: float = 0.0
    spell: dict = field(default_factory=dict)
    hp: float = -1.0
    trail: float = -1.0
    stamina: float = -1.0
    poise: float = -1.0
    since_hurt: float = 99.0
    since_spent: float = 99.0
    exhausted: bool = False
    heals: list = field(default_factory=list)         # [hp per second, seconds left]
    hit_from: tuple[float, float] | None = None       # where the last hit came from (x, z)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.hp = self.trail = self.max_hp
        self.stamina = self.max_stamina
        self.poise = self.poise_max
        self.since_hurt = self.since_spent = 99.0
        self.exhausted = False
        self.heals = []
        self.hit_from = None

    @property
    def alive(self) -> bool:
        return self.hp > 0.0

    def hurt(self, amount: float, poise_damage: float = 0.0, source: tuple[float, float] | None = None) -> bool:
        """Take damage; True if this broke the poise (a stagger)."""
        if not self.alive:
            return False
        self.trail = max(self.trail, self.hp)
        self.hp = max(0.0, self.hp - amount)
        self.since_hurt = 0.0
        self.hit_from = source
        self.poise -= poise_damage
        if self.poise <= 0.0:
            self.poise = self.poise_max
            return True
        return False

    def heal(self, amount: float, seconds: float = 0.0) -> None:
        if seconds <= 0:
            self.hp = min(self.max_hp, self.hp + amount)
        else:
            self.heals.append([amount / seconds, seconds])

    def spend(self, cost: float) -> bool:
        """Stamina for an action. Anything left lets the action happen (Dark Souls style); none, no."""
        if self.max_stamina <= 0:
            return True
        if self.stamina <= 0.0 or self.exhausted:
            return False
        self.stamina = max(0.0, self.stamina - cost)
        self.since_spent = 0.0
        if self.stamina <= 0.0:
            self.exhausted = True
        return True

    def drain(self, amount: float) -> bool:
        """Stamina drained without a cost check (sprinting, blocking a hit). False once it runs out."""
        if self.max_stamina <= 0:
            return True
        self.stamina = max(0.0, self.stamina - amount)
        self.since_spent = 0.0
        if self.stamina <= 0.0:
            self.exhausted = True
            return False
        return True

    def update(self, dt: float, regen: bool = True, cfg: dict | None = None) -> None:
        cfg = cfg or config()
        self.since_hurt += dt
        self.since_spent += dt
        if self.alive:
            for h in self.heals:
                step = min(dt, h[1])
                self.hp = min(self.max_hp, self.hp + h[0] * step)
                h[1] -= dt
            self.heals = [h for h in self.heals if h[1] > 0]
        tr = cfg["hp_trail"]
        if self.trail < self.hp:
            self.trail = self.hp
        elif self.since_hurt > tr["delay_s"]:
            self.trail = max(self.hp, self.trail - tr["drain_frac_per_s"] * self.max_hp * dt)
        if self.since_hurt > cfg["poise_regen_s"]:
            self.poise = self.poise_max
        if self.max_stamina > 0:
            st = cfg["stamina"]
            if regen and self.since_spent > st["regen_delay_s"]:
                self.stamina = min(self.max_stamina, self.stamina + st["regen_per_s"] * dt)
            if self.exhausted and self.stamina >= st["exhausted_until"] * self.max_stamina:
                self.exhausted = False


def enemy_fighter(kind: str, name: str, cfg: dict | None = None) -> Fighter | None:
    """A fighter for this enemy kind, or None if combat.json doesn't list it (townsfolk, animals)."""
    cfg = cfg or config()
    e = cfg["enemies"].get(kind)
    if e is None:
        return None
    d = e["defence"]
    return Fighter(name, e["level"], float(e["hp"]), dict(e["attack"]),
                   flat_defence(d) if isinstance(d, (int, float)) else dict(d), dict(e.get("absorb", {})),
                   float(e["poise"]), float(e["poise_damage"]), float(e["xp"]), float(e.get("weight", 1.0)),
                   spell=dict(e.get("spell", {})))


# ---------------------------------------------------------------------------- Rowan's progress
class Progress:
    """Rowan's level, XP and attributes, his flask and food, and the places he has found.

    `snapshot()` is taken whenever the game saves; dying calls `restore()`, so XP is never dropped but
    goes back to what it was at the last save (STA-28)."""

    def __init__(self, cfg: dict | None = None) -> None:
        self.cfg = cfg = cfg or config()
        r = cfg["rowan"]
        self.level = int(r["level"])
        self.attrs: dict[str, int] = dict(r["attributes"])
        self.xp = 0
        self.flask = int(cfg["lifewater"]["charges"])
        self.food: dict[str, int] = dict(cfg.get("food_start", {}))
        self.discovered: set[str] = set()
        self._saved = self.snapshot()

    # levels
    @property
    def cap(self) -> int:
        return int(self.cfg["level_cap"])

    def xp_needed(self, level: int | None = None) -> int:
        return xp_to_next(self.level if level is None else level, self.cfg)

    def ready(self) -> bool:
        """Enough XP for at least one more level (UIX-20's mark)."""
        return self.level < self.cap and self.xp >= self.xp_needed()

    def gain(self, amount: int) -> int:
        self.xp += max(0, int(amount))
        return self.xp

    def plan_cost(self, points: int) -> int:
        """XP for `points` levels from the current one (one attribute point each, STA-24)."""
        return sum(self.xp_needed(self.level + i) for i in range(points))

    def affordable(self) -> int:
        """How many levels the XP pays for right now."""
        n = 0
        while self.level + n < self.cap and self.plan_cost(n + 1) <= self.xp:
            n += 1
        return n

    def apply(self, plan: dict[str, int]) -> bool:
        """Spend XP on the planned points (attribute -> points). False if it can't be afforded."""
        n = sum(max(0, v) for v in plan.values())
        if n == 0 or n > self.affordable():
            return False
        self.xp -= self.plan_cost(n)
        self.level += n
        for a, v in plan.items():
            self.attrs[a] = self.attrs.get(a, 0) + max(0, v)
        return True

    def stats(self, plan: dict[str, int] | None = None) -> dict[str, float]:
        attrs = dict(self.attrs)
        n = 0
        for a, v in (plan or {}).items():
            attrs[a] = attrs.get(a, 0) + v
            n += v
        return derived(attrs, self.level + n, self.cfg)

    # saves
    def snapshot(self) -> dict:
        return {"level": self.level, "attrs": dict(self.attrs), "xp": self.xp, "flask": self.flask,
                "food": dict(self.food), "discovered": set(self.discovered)}

    def save(self) -> None:
        self._saved = self.snapshot()

    def restore(self, snap: dict | None = None) -> None:
        s = copy.deepcopy(snap or self._saved)
        self.level, self.attrs, self.xp = s["level"], s["attrs"], s["xp"]
        self.flask, self.food, self.discovered = s["flask"], s["food"], s["discovered"]

    # Rowan as a fighter
    def fighter(self, name: str = "Rowan") -> Fighter:
        cfg = self.cfg
        d = self.stats()
        w = cfg["weapons"][cfg["rowan"]["weapon"]]
        return Fighter(name, self.level, d["hp"], weapon_attack(w, self.attrs, cfg), flat_defence(d["defence"]),
                       dict(cfg["rowan"].get("absorb", {})), float(cfg["rowan"]["poise"]), float(w["poise_damage"]),
                       max_stamina=d["stamina"])

    def refresh(self, f: Fighter) -> None:
        """After a level-up: new maximums and attack, keeping the same share of HP and stamina."""
        new = self.fighter(f.name)
        hp_share = f.hp / f.max_hp if f.max_hp else 1.0
        f.level, f.attack, f.defence = new.level, new.attack, new.defence
        gained = new.max_hp - f.max_hp
        f.max_hp, f.max_stamina = new.max_hp, new.max_stamina
        f.hp = min(f.max_hp, max(f.hp + max(0.0, gained), f.max_hp * hp_share))
        f.trail = max(f.trail, f.hp)
        f.stamina = min(f.stamina, f.max_stamina)

    def flask_heal(self, max_hp: float) -> float:
        lw = self.cfg["lifewater"]
        faith = soft(self.attrs.get("faith", 0), self.cfg["soft_caps"])
        return max_hp * lw["heal_frac"] * (1.0 + lw["faith_bonus_per_point"] * faith)

    def discover_xp(self, kind: str) -> int:
        return int(self.cfg["xp"]["discover_waystone" if kind == "waystone" else "discover_landmark"])


def angle_between(fx: float, fz: float, dx: float, dz: float) -> float:
    """Unsigned angle (radians) between two ground directions."""
    n = math.hypot(fx, fz) * math.hypot(dx, dz)
    if n < 1e-9:
        return 0.0
    return math.acos(max(-1.0, min(1.0, (fx * dx + fz * dz) / n)))
