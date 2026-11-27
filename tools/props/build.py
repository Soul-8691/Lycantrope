r"""Build game-ready prop meshes from the chosen Meshy or Tripo3D previews (ART-07, first part).

    .venv\Scripts\python.exe tools/props/build.py            # every prop in data/props.json
    .venv\Scripts\python.exe tools/props/build.py VIL-01     # just some

For each prop: load its source GLB from assets/models/meshy/ (or, for "source": "code:<name>",
make it with tools/props/plants.py), scale it to height_m,
put the pivot at the bottom center, apply 'stretch', and write
assets/models/props/<key>.glb (a "/" in the key becomes "_"). Front stays +z.
"""
from __future__ import annotations

import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data" / "props.json"
PREVIEWS = ROOT / "assets" / "models" / "meshy"
OUT = ROOT / "assets" / "models" / "props"


def model_path(key: str) -> Path:
    return OUT / (key.replace("/", "_") + ".glb")


def _read_glb(path: Path) -> tuple[dict, bytes]:
    b = path.read_bytes()
    jlen = struct.unpack_from("<I", b, 12)[0]
    blen = struct.unpack_from("<I", b, 20 + jlen)[0]
    return json.loads(b[20:20 + jlen]), b[28 + jlen:28 + jlen + blen]


def source_jpeg(path: Path) -> bytes | None:
    """The texture of a one-texture GLB, if it is a JPEG (Tripo's are), byte for byte."""
    j, blob = _read_glb(path)
    imgs = j.get("images", [])
    if len(imgs) != 1 or imgs[0].get("mimeType") != "image/jpeg":
        return None
    v = j["bufferViews"][imgs[0]["bufferView"]]
    return blob[v.get("byteOffset", 0): v.get("byteOffset", 0) + v["byteLength"]]


def jpeg_textures(path: Path, original: bytes | None = None) -> None:
    """Store a built GLB's textures as JPEG: the source's own bytes when the texture is unchanged,
    otherwise re-encoded at high quality. trimesh writes PNG, about 5x larger in Git LFS."""
    j, blob = _read_glb(path)
    imgs = j.get("images", [])
    if not imgs:
        return
    by_view = {img["bufferView"]: i for i, img in enumerate(imgs)}
    out = bytearray()
    for vi, v in enumerate(j["bufferViews"]):
        start = v.get("byteOffset", 0)
        data = blob[start:start + v["byteLength"]]
        if vi in by_view:
            if original is not None and len(imgs) == 1:
                data = original
            elif imgs[by_view[vi]].get("mimeType") != "image/jpeg":
                buf = io.BytesIO()
                Image.open(io.BytesIO(data)).convert("RGB").save(buf, format="JPEG", quality=92)
                data = buf.getvalue()
            imgs[by_view[vi]]["mimeType"] = "image/jpeg"
        out += b"\0" * (-len(out) % 4)
        v["byteOffset"], v["byteLength"] = len(out), len(data)
        out += data
    out += b"\0" * (-len(out) % 4)
    j["buffers"] = [{"byteLength": len(out)}]
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out))
                     + struct.pack("<II", len(js), 0x4E4F534A) + js
                     + struct.pack("<II", len(out), 0x004E4942) + bytes(out))


def build(key: str, spec: dict) -> None:
    if spec["source"].startswith("code:"):              # made in code (tools/props/plants.py), no Meshy model
        sys.path.insert(0, str(Path(__file__).parent))
        import plants
        mesh = plants.make(spec["source"][5:])
    else:
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
    if textured and spec.get("fruit"):  # fruit hung on the canopy (an apple tree made from an oak)
        out_mesh = add_fruit(v, mesh, spec["fruit"], spec["height_m"])
    elif textured:                     # keep the texture and its coordinates
        out_mesh = trimesh.Trimesh(v, mesh.faces, visual=mesh.visual.copy(), process=False)
    else:
        out_mesh = trimesh.Trimesh(v, mesh.faces, process=True)
    OUT.mkdir(parents=True, exist_ok=True)
    out = model_path(key)
    out_mesh.export(out)
    if textured:
        same_texture = not spec.get("fruit") and not spec["source"].startswith("code:")
        jpeg_textures(out, source_jpeg(PREVIEWS / spec["source"]) if same_texture else None)
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
                # nearest original vertex (fine for something drawn 90 m+ away). The game draws the
                # distant version with the main model's texture, so it only carries a placeholder.
                from scipy.spatial import cKDTree
                near = cKDTree(np.asarray(out_mesh.vertices)).query(v2)[1]
                stub = trimesh.visual.material.PBRMaterial(baseColorTexture=Image.new("RGB", (4, 4), (128, 128, 128)))
                vis = trimesh.visual.TextureVisuals(uv=np.asarray(out_mesh.visual.uv)[near], material=stub)
                trimesh.Trimesh(v2, f2, visual=vis, process=False).export(lod)
            else:
                trimesh.Trimesh(v2, f2, process=True).export(lod)
            print(f"  {'':<12} {len(f2):>6} tris   distant version {lod.relative_to(ROOT)}")
        except ImportError:
            print("    (no fast-simplification installed: skipping the distant version)")
    elif lod.exists():
        lod.unlink()


def add_fruit(v: np.ndarray, mesh, fruit: dict, height: float) -> trimesh.Trimesh:
    """Dot small low-poly fruit over the outside of a tree's canopy.

    fruit: {"count", "radius_m", "color" (0..1 RGB), "from" (fraction of the height where the
    canopy starts), "seed"}. The fruit's colour goes in a narrow strip added to the right of the
    texture (the old texture coordinates are squeezed to make room), so it stays one textured mesh.
    """
    from PIL import Image
    rng = np.random.default_rng(int(fruit.get("seed", 1)))
    base = trimesh.Trimesh(v, mesh.faces, process=False)
    normals = base.vertex_normals
    y0 = float(fruit.get("from", 0.45)) * height
    xz = np.linalg.norm(v[:, [0, 2]], axis=1)
    outward = (normals[:, 0] * v[:, 0] + normals[:, 2] * v[:, 2]) / np.maximum(xz, 1e-6)
    ok = (v[:, 1] > y0) & ((outward > 0.25) | (normals[:, 1] > 0.6))
    # outer canopy only: at least 60 % of the way out at that height
    rmax = np.zeros(len(v))
    bands = np.digitize(v[:, 1], np.linspace(y0, height, 8))
    for b in np.unique(bands):
        sel = bands == b
        rmax[sel] = xz[sel].max()
    ok &= xz > 0.6 * rmax
    cand = np.nonzero(ok)[0]
    r = float(fruit.get("radius_m", 0.1))
    picks: list[int] = []
    for i in rng.permutation(cand):                        # spread them out
        if all(np.linalg.norm(v[i] - v[j]) > 6 * r for j in picks):
            picks.append(i)
        if len(picks) >= int(fruit.get("count", 40)):
            break
    # texture with a fruit-coloured strip on the right
    img = mesh.visual.material.baseColorTexture.convert("RGB")
    w, h = img.size
    strip = 32
    big = Image.new("RGB", (w + strip, h), tuple(int(c * 255) for c in fruit.get("color", (0.7, 0.08, 0.06))))
    big.paste(img, (0, 0))
    uv = np.asarray(mesh.visual.uv, float).copy()
    uv[:, 0] *= w / (w + strip)
    fu = (w + strip / 2) / (w + strip)
    ico = trimesh.creation.icosahedron()
    verts, faces, uvs = [v], [np.asarray(mesh.faces)], [uv]
    n0 = len(v)
    for i in picks:
        c = v[i] + normals[i] * r * 0.6
        s = r * rng.uniform(0.85, 1.15)
        verts.append(ico.vertices * s + c)
        faces.append(ico.faces + n0)
        uvs.append(np.tile([fu, 0.5], (len(ico.vertices), 1)))
        n0 += len(ico.vertices)
    mat = trimesh.visual.material.PBRMaterial(baseColorTexture=big, metallicFactor=0.0, roughnessFactor=1.0)
    vis = trimesh.visual.TextureVisuals(uv=np.vstack(uvs), material=mat)
    return trimesh.Trimesh(np.vstack(verts), np.vstack(faces), visual=vis, process=False)


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
