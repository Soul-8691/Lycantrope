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
from lycantrope.world.heightfield import Heightfield
from lycantrope.world.props import PropSpec, load_catalog, place_props

MODELS = ASSETS / "models" / "props"
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


def flat_mesh(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Unindexed (position, face normal) rows for the faceted low-poly look."""
    tri = verts[faces]                                        # (M, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    data = np.concatenate([tri, np.repeat(n[:, None, :], 3, axis=1)], axis=2)
    return np.ascontiguousarray(data.reshape(-1, 6), dtype=np.float32)


@dataclass
class PropModel:
    spec: PropSpec
    vbo: moderngl.Buffer
    inst: moderngl.Buffer
    rows: np.ndarray            # (N, 6) x y z rot scale shade
    radius: float               # bounding sphere radius at scale 1 (around mid-height)
    triangles: int
    draw_m: float
    vao: moderngl.VertexArray | None = None


class PropRenderer:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.catalog = load_catalog()
        meshes = {}
        for key, spec in self.catalog.items():
            path = MODELS / (key.replace("/", "_") + ".glb")
            if not path.exists():
                print(f"props: {path.name} not built yet (python tools/props/build.py)")
                continue
            v, f = read_glb(path)
            spec.extents = tuple(float(e) for e in v.max(axis=0) - v.min(axis=0))
            meshes[key] = (v, f)
        self.catalog = {k: s for k, s in self.catalog.items() if k in meshes}
        instances = place_props(world, self.catalog).arrays()

        self.models: list[PropModel] = []
        for key, rows in instances.items():
            v, f = meshes[key]
            spec = self.catalog[key]
            ex, ey, ez = spec.extents
            radius = 0.5 * float(np.sqrt(ex * ex + ey * ey + ez * ez))
            self.models.append(PropModel(
                spec, ctx.buffer(flat_mesh(v, f).tobytes()), ctx.buffer(rows.tobytes(), dynamic=True),
                rows, radius, len(f), draw_m=max(250.0, spec.height * 110.0)))
        self.count = sum(len(m.rows) for m in self.models)
        self.drawn = 0
        self.triangles = 0
        self._version = -1

    def _program(self) -> moderngl.Program:
        prog = self.shaders.get("props")
        if self._version != self.shaders.version:
            for m in self.models:
                m.vao = self.ctx.vertex_array(prog, [(m.vbo, "3f 3f", "in_pos", "in_nrm"),
                                                     (m.inst, "3f 1f 1f 1f/i", "in_offset", "in_rot",
                                                      "in_scale", "in_shade")])
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
            centers = r[:, :3] + np.outer(r[:, 4], [0.0, s.height * 0.5, 0.0])
            rad = m.radius * r[:, 4]
            vis = np.linalg.norm(centers - e, axis=1) < m.draw_m + rad
            for a, b, c, d in planes:
                vis &= centers @ np.array([a, b, c]) + d >= -rad
            n = int(vis.sum())
            if n == 0:
                continue
            m.inst.write(np.ascontiguousarray(r[vis]).tobytes())
            set_uniform(prog, "u_height", s.height)
            set_uniform(prog, "u_color", tuple(c ** 2.2 for c in s.color))
            set_uniform(prog, "u_top_color", tuple(c ** 2.2 for c in s.top_color))
            set_uniform(prog, "u_top_from", s.top_from)
            m.vao.render(moderngl.TRIANGLES, instances=n)
            drawn += n
            tris += n * m.triangles
        self.drawn, self.triangles = drawn, tris
