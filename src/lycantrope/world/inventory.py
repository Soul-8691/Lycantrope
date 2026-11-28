"""Rowan's things (UIX-07): the item catalogue, his backpack and equipment, loot tables (WLD-17) and what's
lying on the ground (UIX-26). Plain Python, tested without a window.

- `item_catalog(cfg)`: every item by id, from combat.json (weapons, shields, armor, food) and items.json.
- `Inventory`: a 20-slot backpack of stacks, six equipment slots and a purse of currency.
- `LootTables.roll(table, rng)`: what a dead enemy or an opened chest gives.
- `GroundLoot`: drops and chests in the world; Rowan takes from whatever is within PICKUP_M.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field

from lycantrope.core.paths import DATA

BACKPACK = 20
SLOTS = ("head", "torso", "arms", "legs", "mainhand", "offhand")
SLOT_LABELS = {"head": "Head", "torso": "Chest", "arms": "Arms", "legs": "Legs",
               "mainhand": "Main hand", "offhand": "Off hand"}
ARMOR_SLOTS = ("head", "torso", "arms", "legs")
PICKUP_M = 2.0
FISTS = {"name": "Fists", "damage": {"strike": 14}, "scaling": {"might": "E"}, "poise_damage": 4, "reach_m": 1.2,
         "arc_deg": 50, "weight": 0.0, "stamina": {"light": 10, "heavy": 20}, "requirements": {},
         "crit_multiplier": 1.2}


def load_items_file() -> dict:
    return json.loads((DATA / "items.json").read_text(encoding="utf-8"))


def item_catalog(cfg: dict, extra: dict | None = None) -> dict[str, dict]:
    """id -> {name, kind, slot, stack, weight, rarity, text, bound, requirements, spec} for every item."""
    extra = extra if extra is not None else load_items_file()
    out: dict[str, dict] = {}

    def add(iid: str, name: str, kind: str, slot: str | None, stack: int, spec: dict, rarity: str) -> None:
        out[iid] = {"id": iid, "name": name, "kind": kind, "slot": slot, "stack": stack,
                    "weight": float(spec.get("weight", 0.0)), "rarity": rarity, "text": "", "bound": False,
                    "requirements": dict(spec.get("requirements", {})), "spec": spec}

    for iid, w in cfg.get("weapons", {}).items():
        add(iid, w["name"], "weapon", "mainhand", 1, w, "uncommon")
    for iid, m in cfg.get("catalysts", {}).items():
        if not iid.startswith("_"):
            add(iid, m["name"], "catalyst", "offhand", 1, m, "uncommon")
    for iid, s in cfg.get("shields", {}).items():
        add(iid, s["name"], "shield", "offhand", 1, s, "uncommon")
    for iid, a in cfg.get("armor", {}).items():
        if not iid.startswith("_"):
            add(iid, a["name"], "armor", a["slot"], 1, a, "uncommon")
    for iid, f in cfg.get("food", {}).items():
        add(iid, f["name"], "food", None, 20, f, "common")
    for iid, it in extra.get("items", {}).items():
        add(iid, it["name"], it["kind"], None, int(it.get("stack", 1)), it, it.get("rarity", "common"))
    for iid, more in list(extra.get("items", {}).items()) + list(extra.get("extra", {}).items()):
        if iid in out:
            for k in ("rarity", "text", "bound"):
                if k in more:
                    out[iid][k] = more[k]
    return out


def shortfalls(item: dict | None, attrs: dict) -> dict[str, tuple[int, int]]:
    """Requirements Rowan doesn't meet: attribute -> (needed, has). Empty when he can use it fully."""
    if not item:
        return {}
    return {a: (int(n), int(attrs.get(a, 0))) for a, n in item["requirements"].items() if attrs.get(a, 0) < n}


# ---------------------------------------------------------------------------- inventory
class Inventory:
    def __init__(self, catalog: dict[str, dict]) -> None:
        self.catalog = catalog
        self.bag: list[list] = []                 # [item_id, count], at most BACKPACK stacks
        self.equipped: dict[str, str | None] = {s: None for s in SLOTS}
        self.purse: dict[str, int] = {}           # currency: no backpack slot

    # -- contents -----------------------------------------------------------
    def count(self, iid: str) -> int:
        if self.catalog.get(iid, {}).get("kind") == "currency":
            return self.purse.get(iid, 0)
        return sum(n for i, n in self.bag if i == iid)

    def add(self, iid: str, n: int = 1) -> int:
        """Put up to n of an item in the backpack; returns how many fitted."""
        item = self.catalog.get(iid)
        if item is None or n <= 0:
            return 0
        if item["kind"] == "currency":
            self.purse[iid] = self.purse.get(iid, 0) + n
            return n
        left = n
        for stack in self.bag:
            if stack[0] == iid and stack[1] < item["stack"]:
                k = min(left, item["stack"] - stack[1])
                stack[1] += k
                left -= k
        while left > 0 and len(self.bag) < BACKPACK:
            k = min(left, item["stack"])
            self.bag.append([iid, k])
            left -= k
        return n - left

    def remove(self, iid: str, n: int = 1) -> bool:
        if self.count(iid) < n:
            return False
        if self.catalog.get(iid, {}).get("kind") == "currency":
            self.purse[iid] -= n
            return True
        for stack in reversed(self.bag):
            if stack[0] == iid and n > 0:
                k = min(n, stack[1])
                stack[1] -= k
                n -= k
        self.bag = [s for s in self.bag if s[1] > 0]
        return True

    def take_slot(self, index: int, n: int | None = None) -> tuple[str, int] | None:
        """Remove (part of) the stack at a backpack index; returns (id, count) taken."""
        if not 0 <= index < len(self.bag):
            return None
        iid, have = self.bag[index]
        k = have if n is None else min(n, have)
        self.bag[index][1] -= k
        if self.bag[index][1] <= 0:
            del self.bag[index]
        return iid, k

    # -- equipment ----------------------------------------------------------
    def equip(self, index: int) -> bool:
        """Equip the backpack item at index; whatever was in that slot goes back in its place."""
        if not 0 <= index < len(self.bag):
            return False
        iid = self.bag[index][0]
        slot = self.catalog[iid]["slot"]
        if slot is None:
            return False
        old = self.equipped[slot]
        if old is None:
            del self.bag[index]
        else:
            self.bag[index] = [old, 1]
        self.equipped[slot] = iid
        return True

    def unequip(self, slot: str) -> bool:
        iid = self.equipped.get(slot)
        if iid is None or len(self.bag) >= BACKPACK:
            return False
        self.equipped[slot] = None
        self.bag.append([iid, 1])
        return True

    def put_on(self, iid: str) -> None:
        """Equip an item straight away (starting kit, old saves), without it passing through the backpack."""
        item = self.catalog.get(iid)
        if item is not None and item["slot"]:
            self.equipped[item["slot"]] = iid

    def equipped_items(self) -> list[dict]:
        return [self.catalog[i] for i in self.equipped.values() if i in self.catalog]

    # -- saves --------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"bag": [list(s) for s in self.bag], "equipped": dict(self.equipped), "purse": dict(self.purse)}

    def from_dict(self, d: dict) -> None:
        self.bag = [[i, int(n)] for i, n in d.get("bag", []) if i in self.catalog and int(n) > 0][:BACKPACK]
        self.equipped = {s: None for s in SLOTS}
        for s, i in d.get("equipped", {}).items():
            if s in self.equipped and i in self.catalog:
                self.equipped[s] = i
        self.purse = {i: int(n) for i, n in d.get("purse", {}).items() if i in self.catalog}


# ---------------------------------------------------------------------------- loot
class LootTables:
    def __init__(self, tables: dict | None = None) -> None:
        if tables is None:
            tables = json.loads((DATA / "loot.json").read_text(encoding="utf-8"))["tables"]
        self.tables = tables

    def roll(self, name: str, rng: random.Random) -> list[list]:
        """[item_id, count] for everything the table gives this time (possibly nothing)."""
        out = []
        for e in self.tables.get(name, []):
            if rng.random() < float(e.get("chance", 1.0)):
                lo, hi = e.get("count", [1, 1])
                out.append([e["item"], rng.randint(int(lo), int(hi))])
        return out


@dataclass
class Drop:
    x: float
    y: float
    z: float
    items: list[list]                     # [item_id, count] still lying here
    name: str = ""                        # "Wooden Chest", or the dead enemy's name
    chest_id: str | None = None           # chests stay opened in the save
    table: str = ""                       # a closed chest's loot table, rolled when it opens
    opened: bool = False

    @property
    def is_chest(self) -> bool:
        return self.chest_id is not None


@dataclass
class GroundLoot:
    drops: list[Drop] = field(default_factory=list)

    def spawn(self, x: float, y: float, z: float, items: list[list], name: str = "") -> Drop | None:
        if not items:
            return None
        d = Drop(x, y, z, [list(i) for i in items], name)
        self.drops.append(d)
        return d

    def nearest(self, x: float, z: float, reach: float = PICKUP_M) -> Drop | None:
        best, best_d = None, reach
        for d in self.drops:
            if d.is_chest and d.opened and not d.items:
                continue
            dist = math.hypot(d.x - x, d.z - z)
            if dist <= best_d:
                best, best_d = d, dist
        return best

    def take(self, drop: Drop, inv: Inventory, tables: LootTables, rng: random.Random) -> list[tuple[str, int]]:
        """Open (if a chest) and take everything that fits; returns what was taken. Leftovers stay."""
        if drop.is_chest and not drop.opened:
            drop.opened = True
            drop.items = tables.roll(drop.table, rng)
        taken, left = [], []
        for iid, n in drop.items:
            got = inv.add(iid, n)
            if got:
                taken.append((iid, got))
            if got < n:
                left.append([iid, n - got])
        drop.items = left
        if not drop.is_chest and not left:
            self.drops.remove(drop)
        return taken

    def clear_dropped(self) -> None:
        """A reload: enemies' drops vanish with them; chests stay (their opened state comes from the save)."""
        self.drops = [d for d in self.drops if d.is_chest]
