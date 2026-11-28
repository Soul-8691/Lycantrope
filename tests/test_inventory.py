import json
import random

import pytest

from lycantrope.core.paths import DATA
from lycantrope.world.inventory import BACKPACK, GroundLoot, Inventory, LootTables, item_catalog, shortfalls
from lycantrope.world.stats import Progress, armor_stats, config, weapon_attack


@pytest.fixture(scope="module")
def catalog():
    return item_catalog(config())


def test_catalog_has_every_kind_and_every_loot_item(catalog):
    kinds = {i["kind"] for i in catalog.values()}
    assert {"weapon", "shield", "armor", "food", "currency", "material"} <= kinds
    assert catalog["dawnblade"]["bound"] and catalog["dawnblade"]["rarity"] == "legendary"
    assert catalog["trs_04"]["slot"] == "torso" and catalog["wooden_round_shield"]["slot"] == "offhand"
    tables = json.loads((DATA / "loot.json").read_text(encoding="utf-8"))["tables"]
    missing = {e["item"] for t in tables.values() for e in t} - set(catalog)
    assert not missing


def test_stacks_fill_up_then_new_slots_until_the_backpack_is_full(catalog):
    inv = Inventory(catalog)
    assert inv.add("apple", 25) == 25 and [s[1] for s in inv.bag] == [20, 5]
    for _ in range(BACKPACK - 2):
        assert inv.add("iron_shortsword") == 1
    assert len(inv.bag) == BACKPACK
    assert inv.add("flanged_mace") == 0                       # full
    assert inv.add("apple", 20) == 15                         # still fits in the half-full stack
    assert inv.add("copper", 500) == 500 and len(inv.bag) == BACKPACK   # currency takes no slot
    assert inv.remove("apple", 30) and inv.count("apple") == 10


def test_equip_swaps_with_whats_worn_and_unequip_needs_room(catalog):
    inv = Inventory(catalog)
    inv.put_on("trs_01")
    inv.add("trs_04")
    assert inv.equip(0)
    assert inv.equipped["torso"] == "trs_04" and inv.bag == [["trs_01", 1]]
    assert not inv.equip(5)
    inv.add("apple")
    assert not inv.equip(1)                                   # food has no slot
    assert inv.unequip("torso") and inv.equipped["torso"] is None
    while len(inv.bag) < BACKPACK:
        inv.add("iron_shortsword")
    inv.put_on("hed_02")
    assert not inv.unequip("head")


def test_progress_starts_with_his_kit_and_saves_the_inventory():
    p = Progress()
    assert p.inv.equipped["mainhand"] == "dawnblade" and p.shield is None
    assert set(p.armor) == set(p.cfg["rowan"]["armor"]) and p.food == p.cfg["food_start"]
    p.save()
    p.inv.add("iron_shortsword")
    p.inv.equip(len(p.inv.bag) - 1)
    p.inv.add("copper", 12)
    p.opened.add("chest_1")
    p.restore()                                               # death: back to the save
    assert p.inv.equipped["mainhand"] == "dawnblade" and p.inv.count("copper") == 0 and not p.opened


def test_an_old_save_without_an_inventory_still_loads():
    p = Progress()
    old = {"level": 21, "attrs": dict(p.attrs), "xp": 5, "flask": 2, "food": {"apple": 1, "bread": 2},
           "discovered": {"Mill"}, "armor": ["hed_02"], "shield": "wooden_round_shield"}
    p.restore(old)
    assert p.level == 21 and p.food == {"apple": 1, "bread": 2}
    assert set(p.armor) == set(p.cfg["rowan"]["armor"]) and p.inv.equipped["mainhand"] == "dawnblade"


def test_wpr03_a_weapon_below_its_requirements_loses_scaling_and_costs_more_stamina():
    p = Progress()
    assert p.stamina_multiplier() == 1.0
    mace = p.cfg["weapons"]["flanged_mace"]                   # needs Might 14
    p.inv.add("flanged_mace")
    p.inv.equip(len(p.inv.bag) - 1)
    full = p.fighter().attack["strike"]
    assert full == pytest.approx(weapon_attack(mace, p.attrs)["strike"])
    p.attrs["might"] = 10
    assert not p.weapon_ok() and p.stamina_multiplier() == 1.25
    assert p.fighter().attack["strike"] == pytest.approx(mace["damage"]["strike"])   # base only
    assert shortfalls(p.inv.catalog["flanged_mace"], p.attrs) == {"might": (14, 10)}


def test_ars01_unmet_armor_gives_half_and_weighs_more():
    cfg = config()
    piece = cfg["armor"]["trs_04"]                            # Fortune 12, Endurance 11
    fine = armor_stats(["trs_04"], cfg, {"fortune": 12, "endurance": 11})
    weak = armor_stats(["trs_04"], cfg, {"fortune": 5, "endurance": 11})
    assert fine["poise"] == piece["poise"] and weak["poise"] == piece["poise"] / 2
    assert weak["defence"]["slash"] == piece["defence"]["slash"] / 2
    assert weak["weight"] == pytest.approx(piece["weight"] * 1.5)


def test_roll_class_follows_equip_load():
    p = Progress()
    assert p.roll_class() == "fast"
    for iid in ("hed_13", "arm_13", "trs_13", "leg_13"):
        p.inv.put_on(iid)
    p.inv.put_on("dread_tower_shield")
    assert p.roll_class() in ("medium", "slow")
    used, cap = p.equip_load()
    assert used > 0.3 * cap


def test_loot_tables_and_picking_up(catalog):
    tables = LootTables({"t": [{"item": "copper", "chance": 1.0, "count": [3, 3]},
                               {"item": "apple", "chance": 0.0}]})
    assert tables.roll("t", random.Random(1)) == [["copper", 3]]
    assert tables.roll("nothing", random.Random(1)) == []
    ground, inv = GroundLoot(), Inventory(catalog)
    d = ground.spawn(5.0, 0.0, 5.0, [["copper", 3], ["iron_shortsword", 1]])
    assert ground.nearest(0.0, 0.0) is None and ground.nearest(5.5, 5.5) is d
    taken = ground.take(d, inv, tables, random.Random(1))
    assert taken == [("copper", 3), ("iron_shortsword", 1)] and d not in ground.drops


def test_a_chest_rolls_when_opened_and_keeps_what_doesnt_fit(catalog):
    from lycantrope.world.inventory import Drop
    tables = LootTables({"c": [{"item": "flanged_mace", "chance": 1.0, "count": [2, 2]}]})
    ground, inv = GroundLoot(), Inventory(catalog)
    while len(inv.bag) < BACKPACK - 1:
        inv.add("goblin_shiv")
    chest = Drop(0.0, 0.0, 0.0, [], "Wooden Chest", chest_id="c1", table="c")
    ground.drops.append(chest)
    assert ground.take(chest, inv, tables, random.Random(1)) == [("flanged_mace", 1)]
    assert chest.opened and chest.items == [["flanged_mace", 1]] and chest in ground.drops
    ground.spawn(1.0, 0.0, 1.0, [["apple", 1]])
    ground.clear_dropped()
    assert ground.drops == [chest]
