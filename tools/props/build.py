"""Build game-ready prop meshes from the chosen Meshy previews (ART-07, first part).

    python tools/props/build.py            # every prop in data/props.json
    python tools/props/build.py VIL-01     # just some

For each prop: load its source GLB from assets/meshy/previews/, scale it to height_m,
put the pivot at the bottom center, apply 'stretch', and write
assets/models/props/<key>.glb (a "/" in the key becomes "_"). Front stays +z.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data" / "props.json"
PREVIEWS = ROOT / "assets" / "meshy" / "previews"
OUT = ROOT / "assets" / "models" / "props"


def model_path(key: str) -> Path:
    return OUT / (key.replace("/", "_") + ".glb")


def build(key: str, spec: dict) -> None:
    src = PREVIEWS / spec["source"]
    if not src.exists():
        print(f"  ! {key}: missing {src.relative_to(ROOT)}")
        return
    mesh = trimesh.load(src, force="mesh")
    mesh = trimesh.Trimesh(mesh.vertices, mesh.faces, process=True)   # geometry only
    lo, hi = mesh.bounds
    v = mesh.vertices - [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]
    v *= spec["height_m"] / (hi[1] - lo[1])
    v *= np.asarray(spec.get("stretch", [1.0, 1.0, 1.0]))
    out_mesh = trimesh.Trimesh(v, mesh.faces, process=False)
    OUT.mkdir(parents=True, exist_ok=True)
    out = model_path(key)
    out_mesh.export(out)
    e = out_mesh.extents
    print(f"  {key:<12} {len(out_mesh.faces):>6} tris   {e[0]:5.1f} x {e[1]:4.1f} x {e[2]:5.1f} m   "
          f"{out.relative_to(ROOT)}")


def main() -> None:
    props = json.loads(CATALOG.read_text(encoding="utf-8"))["props"]
    keys = sys.argv[1:] or list(props)
    for k in keys:
        if k not in props:
            print(f"  ! {k}: not in data/props.json")
            continue
        build(k, props[k])


if __name__ == "__main__":
    main()
