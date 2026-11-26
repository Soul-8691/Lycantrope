"""Prop rendering (WLD-12, TEC-08): every copy of a prop is drawn in one instanced call.

Meshes come from assets/models/props/<key>.glb (built by tools/props/build.py). Until
textures exist, props are painted from the colors in data/props.json.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyglm import glm
import moderngl
import numpy as np
import pygltflib

from lycantrope.core.paths import ASSETS
from lycantrope.render.camera import frustum_planes
from lycantrope.render.shaders import ShaderLibrary, set_uniform
from lycantrope.world.collision import Colliders
from lycantrope.world.heightfield import Heightfield
from lycantrope.world.props import PropSpec, load_catalog, place_props

MODELS = ASSETS / "models" / "props"
LOD_M = 90.0                    # beyond this, props with a distant version draw it instead
_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
_DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def read_glb(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Positions (N,3) and triangle indices (M,3) of every primitive in a GLB, merged."""
    gltf = pygltflib.GLTF2().load(str(path))
    blob = gltf.binary_blob()

    def accessor(i: int) -> np.ndarray:
        acc = gltf.accessors[i]
        view = gltf.bufferViews[acc.bufferView]
        comps = _COMPONENTS[acc.type]
        dtype = np.dtype(_DTYPES[acc.componentType])
        start = (view.byteOffset or 0) + (acc.byteOffset or 0)
        stride = view.byteStride or comps * dtype.itemsize
        raw = np.frombuffer(blob, dtype=np.uint8, count=stride * (acc.count - 1) + comps * dtype.itemsize,
                            offset=start)
        rows = np.lib.stride_tricks.as_strided(raw, (acc.count, comps * dtype.itemsize), (stride, 1))
        return np.ascontiguousarray(rows).view(dtype).reshape(acc.count, comps)

    verts, faces, base = [], [], 0
    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            p = accessor(prim.attributes.POSITION).astype(np.float32)
            idx = (accessor(prim.indices).ravel() if prim.indices is not None
                   else np.arange(len(p))).astype(np.uint32)
            verts.append(p)
            faces.append(idx.reshape(-1, 3) + base)
            base += len(p)
    return np.concatenate(verts), np.concatenate(faces)


def flat_mesh(verts: np.ndarray, faces: np.ndarray, uv: np.ndarray | None = None) -> np.ndarray:
    """Unindexed (position, face normal, uv) rows for the faceted low-poly look."""
    tri = verts[faces]                                        # (M, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    t = uv[faces] if uv is not None else np.zeros((len(faces), 3, 2), np.float32)
    data = np.concatenate([tri, np.repeat(n[:, None, :], 3, axis=1), t], axis=2)
    return np.ascontiguousarray(data.reshape(-1, 8), dtype=np.float32)


def load_prop(path: Path):
    """Positions, faces, uv (or None) and texture image (or None) of a built prop GLB."""
    from lycantrope.render.gltf import load_mesh
    m = load_mesh(path, skinned=False)
    has_uv = m.texture is not None and np.any(m.uv)
    return m.pos, m.idx.reshape(-1, 3), (m.uv if has_uv else None), m.texture


@dataclass
class PropModel:
    spec: PropSpec
    vbo: moderngl.Buffer
    inst: moderngl.Buffer
    rows: np.ndarray            # (N, 7) x y z rot scale shade stretch
    radius: float               # bounding sphere radius at scale 1 (around mid-height)
    triangles: int
    draw_m: float
    vao: moderngl.VertexArray | None = None
    lod_vbo: moderngl.Buffer | None = None      # simpler distant version (TEC-11)
    lod_inst: moderngl.Buffer | None = None
    lod_tris: int = 0
    lod_vao: moderngl.VertexArray | None = None
    texture: moderngl.Texture | None = None     # Meshy texture, if the prop has one
    centers: np.ndarray | None = None           # per instance: middle of the prop (world)
    rad: np.ndarray | None = None               # per instance: bounding sphere radius
    box_lo: np.ndarray | None = None            # all instances: bounds, to skip far-off groups fast
    box_hi: np.ndarray | None = None

    def all_far(self, eye: np.ndarray) -> bool:
        nearest = np.clip(eye, self.box_lo, self.box_hi)
        return float(np.linalg.norm(nearest - eye)) > self.draw_m


class PropRenderer:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield,
                 placements: dict | None = None) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.catalog = load_catalog()
        meshes = {}
        for key, spec in self.catalog.items():
            path = MODELS / (key.replace("/", "_") + ".glb")
            if not path.exists():
                print(f"props: {path.name} not built yet (run tools/props/build.py)")
                continue
            v, f, uv, tex = load_prop(path)
            spec.extents = tuple(float(e) for e in v.max(axis=0) - v.min(axis=0))
            meshes[key] = (v, f, uv, tex)
        self.catalog = {k: s for k, s in self.catalog.items() if k in meshes}
        instances = place_props(world, self.catalog, placements).arrays()
        self.colliders = Colliders.from_instances(instances, self.catalog)   # what characters can't walk through

        self.models: list[PropModel] = []
        for key, rows in instances.items():
            v, f, uv, tex = meshes[key]
            spec = self.catalog[key]
            ex, ey, ez = spec.extents
            radius = 0.5 * float(np.sqrt(ex * ex + ey * ey + ez * ez))
            pm = PropModel(spec, ctx.buffer(flat_mesh(v, f, uv).tobytes()), ctx.buffer(rows.tobytes(), dynamic=True),
                           rows, radius, len(f), draw_m=min(900.0, max(250.0, spec.height * 110.0)))
            lod = MODELS / (key.replace("/", "_") + "_lod1.glb")
            if lod.exists():
                lv, lf, luv, _lt = load_prop(lod)
                pm.lod_vbo = ctx.buffer(flat_mesh(lv, lf, luv if uv is not None else None).tobytes())
                pm.lod_inst = ctx.buffer(rows.tobytes(), dynamic=True)
                pm.lod_tris = len(lf)
            pm.centers = rows[:, :3] + np.outer(rows[:, 4] * rows[:, 6], [0.0, spec.height * 0.5, 0.0])
            pm.rad = radius * rows[:, 4] * np.maximum(rows[:, 6], 1.0)
            pm.box_lo = (pm.centers - pm.rad[:, None]).min(axis=0)
            pm.box_hi = (pm.centers + pm.rad[:, None]).max(axis=0)
            if tex is not None and uv is not None:
                pm.texture = ctx.texture(tex.size, 3, tex.tobytes())
                pm.texture.build_mipmaps()
                pm.texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
                pm.texture.anisotropy = 4.0
            self.models.append(pm)
        self.count = sum(len(m.rows) for m in self.models)
        self.drawn = 0
        self.triangles = 0
        self._version = -1

    def _program(self) -> moderngl.Program:
        prog = self.shaders.get("props")
        if self._version != self.shaders.version:
            def vao(vbo, inst):
                return self.ctx.vertex_array(prog, [(vbo, "3f 3f 2f", "in_pos", "in_nrm", "in_uv"),
                                                    (inst, "3f 1f 1f 1f 1f/i", "in_offset", "in_rot",
                                                     "in_scale", "in_shade", "in_stretch")])
            for m in self.models:
                m.vao = vao(m.vbo, m.inst)
                if m.lod_vbo is not None:
                    m.lod_vao = vao(m.lod_vbo, m.lod_inst)
            self._version = self.shaders.version
        return prog

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict) -> None:
        if not self.models:
            return
        prog = self._program()
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_cam", eye)
        for k, v in env.items():
            set_uniform(prog, k, v)
        planes = frustum_planes(viewproj)
        e = np.array([eye.x, eye.y, eye.z], dtype=np.float32)
        drawn = tris = 0
        for m in self.models:
            s = m.spec
            r = m.rows
            centers, rad = m.centers, m.rad                    # props don't move: computed once
            if m.all_far(e):
                continue
            dist = np.linalg.norm(centers - e, axis=1)
            vis = dist < m.draw_m + rad
            vis &= ((centers @ planes[:, :3].T + planes[:, 3]) >= -rad[:, None]).all(axis=1)
            if not vis.any():
                continue
            set_uniform(prog, "u_height", s.height)
            set_uniform(prog, "u_color", tuple(c ** 2.2 for c in s.color))
            set_uniform(prog, "u_top_color", tuple(c ** 2.2 for c in s.top_color))
            set_uniform(prog, "u_top_from", s.top_from)
            if m.texture is not None:
                m.texture.use(0)
                set_uniform(prog, "u_tex", 0)
            set_uniform(prog, "u_has_tex", 1 if m.texture is not None else 0)
            near = vis & (dist < LOD_M + rad) if m.lod_vao is not None else vis
            for mask, inst, vao, t in ((near, m.inst, m.vao, m.triangles),
                                       (vis & ~near, m.lod_inst, m.lod_vao, m.lod_tris)):
                n = int(mask.sum())
                if n == 0 or vao is None:
                    continue
                inst.write(np.ascontiguousarray(r[mask]).tobytes())
                vao.render(moderngl.TRIANGLES, instances=n)
                drawn += n
                tris += n * t
        self.drawn, self.triangles = drawn, tris
