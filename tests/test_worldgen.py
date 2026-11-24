"""Fast checks for the terrain generator (runs at 128 px, ~1 s)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
import terrain  # noqa: E402

LAYOUT = json.loads((ROOT / "data" / "world" / "layout.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def world():
    return terrain.generate(LAYOUT, 128, log=lambda *_: None)


def test_deterministic(world):
    again = terrain.generate(LAYOUT, 128, log=lambda *_: None)
    assert np.array_equal(world["H"], again["H"])
    assert np.array_equal(world["biome"], again["biome"])


def test_different_seed_differs(world):
    other = terrain.generate(LAYOUT, 128, seed=LAYOUT["seed"] + 1, log=lambda *_: None)
    assert not np.array_equal(world["H"], other["H"])


def test_heights_in_range(world):
    assert world["H"].min() >= 0.0
    assert world["H"].max() <= LAYOUT["max_height_m"]


def test_every_biome_present(world):
    ids = {b["id"] for b in LAYOUT["biomes"].values()} | {LAYOUT["boundary"]["id"]}
    assert ids <= set(np.unique(world["biome"]).tolist())


def test_pads_above_water(world):
    for pad in world["pads"]:
        assert pad["height_m"] > LAYOUT["water_level_m"], pad["name"]


def test_outputs_round_trip(world, tmp_path):
    from PIL import Image
    meta = terrain.write_outputs(LAYOUT, world, tmp_path, preview_size=128)
    h16 = np.asarray(Image.open(tmp_path / "height.png"))
    decoded = h16.astype(np.float32) / 65535 * meta["height"]["max_height_m"]
    assert np.abs(decoded - world["H"]).max() < 0.01
    assert (tmp_path / "preview.png").exists()
    assert len(meta["waystones"]) == len(LAYOUT["waystones"])
    a = np.asarray(Image.open(tmp_path / "splat_a.png"), np.float32)
    b = np.asarray(Image.open(tmp_path / "splat_b.png"), np.float32)
    total = (a.sum(-1) + b.sum(-1)) / 255
    assert np.abs(total - 1).max() < 0.03          # weights sum to ~1 everywhere


def test_noise_tiles():
    from noise import fbm
    x = np.linspace(0, 1, 50, dtype=np.float32)
    left = fbm(np.zeros_like(x) + 0.0, x * 4, 4, 7, period=4)
    right = fbm(np.zeros_like(x) + 4.0, x * 4, 4, 7, period=4)
    assert np.allclose(left, right, atol=1e-4)
