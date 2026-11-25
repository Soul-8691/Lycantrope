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
    mesh = trimesh.load(src, force="mesh", process=False)
    uv = getattr(mesh.visual, "uv", None)
    textured = uv is not None and getattr(mesh.visual, "material", None) is not None
    lo, hi = mesh.bounds
    v = mesh.vertices - [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]
    v *= spec["height_m"] / (hi[1] - lo[1])
    v *= np.asarray(spec.get("stretch", [1.0, 1.0, 1.0]))
    if textured:                       # keep the texture and its coordinates
        out_mesh = trimesh.Trimesh(v, mesh.faces, visual=mesh.visual.copy(), process=False)
    else:
        out_mesh = trimesh.Trimesh(v, mesh.faces, process=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out = model_path(key)
    out_mesh.export(out)
    e = out_mesh.extents
    print(f"  {key:<12} {len(out_mesh.faces):>6} tris   {e[0]:5.1f} x {e[1]:4.1f} x {e[2]:5.1f} m   "
          f"{out.relative_to(ROOT)}{'   (textured)' if textured else ''}")
    # distant version (TEC-11): about a third of the triangles, drawn beyond ~90 m
    lod = lod_path(key)
    if len(out_mesh.faces) >= 1500:
        try:
            import fast_simplification
            target = max(400, len(out_mesh.faces) // 3)
            welded = trimesh.Trimesh(out_mesh.vertices, out_mesh.faces, process=True)   # join seams first
            v2, f2 = fast_simplification.simplify(np.asarray(welded.vertices, np.float32),
                                                  np.asarray(welded.faces), target_count=target, agg=5)
            if textured:
                # the simplifier drops texture coordinates: borrow each new vertex's from the
                # nearest original vertex (fine for something drawn 90 m+ away)
                from scipy.spatial import cKDTree
                near = cKDTree(np.asarray(out_mesh.vertices)).query(v2)[1]
                vis = trimesh.visual.TextureVisuals(uv=np.asarray(uv)[near], material=mesh.visual.material)
                trimesh.Trimesh(v2, f2, visual=vis, process=False).export(lod)
            else:
                trimesh.Trimesh(v2, f2, process=True).export(lod)
            print(f"  {'':<12} {len(f2):>6} tris   distant version {lod.relative_to(ROOT)}")
        except ImportError:
            print("    (no fast-simplification installed: skipping the distant version)")
    elif lod.exists():
        lod.unlink()


def lod_path(key: str) -> Path:
    return OUT / (key.replace("/", "_") + "_lod1.glb")


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
