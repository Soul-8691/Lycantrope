r"""Reduce Meshy preview meshes to their triangle budget, locally and for free.

    .venv\Scripts\python.exe tools/meshy/reduce.py VIL-10 PLT-01          # budget from OBJECTS.md
    .venv\Scripts\python.exe tools/meshy/reduce.py PLT-01 --tris 3000     # pick a count yourself
    .venv\Scripts\python.exe tools/meshy/reduce.py --all                  # every downloaded preview

Writes model_<N>.glb and a model_<N>.png thumbnail next to model.glb in
assets/meshy/previews/<ID>/.../ and leaves the original alone, so you can try several
counts and compare the thumbnails. Shape only: textures come later.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).parent))
from batch import OUT_DIR, parse_entries  # noqa: E402
from thumbnail import render  # noqa: E402


def reduce_file(src: Path, target: int) -> Path:
    try:
        import fast_simplification
    except ImportError:
        sys.exit("Needs fast-simplification:  .venv\\Scripts\\python.exe -m pip install fast-simplification")

    mesh = trimesh.load(src, force="mesh")
    before = len(mesh.faces)
    if before <= target:
        out_mesh = mesh
    else:
        # In steps of about 8x: one huge jump (Meshy meshes are millions of triangles)
        # stalls the simplifier far above the target and mangles thin parts.
        verts = np.asarray(mesh.vertices, dtype=np.float32)
        faces = np.asarray(mesh.faces)
        while len(faces) > target:
            step = max(target, len(faces) // 8)
            verts, faces = fast_simplification.simplify(verts, faces, target_count=step, agg=5)
            if len(faces) > step * 1.5:
                print(f"  ! simplifier stalled at {len(faces):,} triangles")
                break
        out_mesh = trimesh.Trimesh(verts, faces, process=True)
    out = src.with_name(f"model_{target}.glb")
    out_mesh.export(out)
    thumb = render(out)
    print(f"  {src.parent.relative_to(OUT_DIR)}: {before:,} -> {len(out_mesh.faces):,} triangles"
          f"  ({out.stat().st_size / 1e6:.2f} MB)  {thumb.relative_to(OUT_DIR.parents[2])}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Reduce Meshy preview meshes")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--tris", type=int, help="target triangles (default: budget in the .md file)")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    entries = parse_entries()
    files = sorted(OUT_DIR.glob("*/**/model.glb"))
    if not args.all:
        if not args.ids:
            sys.exit("Name some IDs or use --all.")
        files = [f for f in files if f.relative_to(OUT_DIR).parts[0] in args.ids]
    if not files:
        sys.exit("No downloaded previews match.")
    for f in files:
        e = entries.get(f.relative_to(OUT_DIR).parts[0])
        target = args.tris or (e.tris if e and e.tris else 1500)
        reduce_file(f, target)


if __name__ == "__main__":
    main()
