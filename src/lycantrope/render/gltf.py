"""GLB loading for characters and items (TEC-08, ART-07): meshes, textures, skins and clips.

Animation clips are baked at load time into per-frame joint world matrices (30 fps), so
playing them costs one interpolation per frame. Clips can be retargeted between skeletons
that share joint names (Meshy's 24-joint biped rig): rotations are copied, the hips'
translation is scaled by the ratio of hip heights, and other joints keep their own rest
offsets. Root motion is removed so clips play in place; the code moves the character.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import pygltflib
from PIL import Image

_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
_DTYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
BAKE_FPS = 30.0


class Gltf:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.g = pygltflib.GLTF2().load(str(path))
        self.blob = self.g.binary_blob()

    def acc(self, i: int) -> np.ndarray:
        a = self.g.accessors[i]
        view = self.g.bufferViews[a.bufferView]
        comps = _COMPONENTS[a.type]
        dt = np.dtype(_DTYPES[a.componentType])
        start = (view.byteOffset or 0) + (a.byteOffset or 0)
        stride = view.byteStride or comps * dt.itemsize
        raw = np.frombuffer(self.blob, np.uint8, stride * (a.count - 1) + comps * dt.itemsize, start)
        rows = np.lib.stride_tricks.as_strided(raw, (a.count, comps * dt.itemsize), (stride, 1))
        out = np.ascontiguousarray(rows).view(dt).reshape(a.count, comps)
        if a.normalized and a.componentType in _NORM:
            out = out.astype(np.float32) / _NORM[a.componentType]
        return out

    def image(self, index: int) -> Image.Image:
        img = self.g.images[index]
        view = self.g.bufferViews[img.bufferView]
        start = view.byteOffset or 0
        return Image.open(io.BytesIO(self.blob[start:start + view.byteLength])).convert("RGB")

    def parents(self) -> dict[int, int]:
        return {c: i for i, n in enumerate(self.g.nodes) for c in (n.children or [])}


@lru_cache(maxsize=32)
def open_gltf(path: Path) -> Gltf:
    """Parsed GLBs are reused: one animation file holds many clips."""
    return Gltf(path)


# ---------------------------------------------------------------------------- #
@dataclass
class MeshData:
    pos: np.ndarray                     # (V, 3) float32, mesh space
    nrm: np.ndarray                     # (V, 3)
    uv: np.ndarray                      # (V, 2)
    idx: np.ndarray                     # (T*3,) uint32
    joints: np.ndarray | None = None    # (V, 4) int
    weights: np.ndarray | None = None   # (V, 4) float, sums to 1
    texture: Image.Image | None = None
    color: np.ndarray | None = None     # (V, 3) linear-ish tint, 1 = untinted


def _smooth_normals(pos: np.ndarray, idx: np.ndarray) -> np.ndarray:
    tri = idx.reshape(-1, 3)
    fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
    n = np.zeros_like(pos)
    for k in range(3):
        np.add.at(n, tri[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def load_mesh(path: Path, skinned: bool | None = None) -> MeshData:
    """All primitives of the first mesh merged. Static meshes get their node transforms baked in."""
    f = open_gltf(path)
    g = f.g
    node_i = next((i for i, n in enumerate(g.nodes) if n.mesh is not None and
                   (n.skin is not None or not skinned)), None)
    if node_i is None:
        raise ValueError(f"{path.name}: no mesh node")
    node = g.nodes[node_i]
    use_skin = node.skin is not None if skinned is None else skinned
    pos, nrm, uv, joints, weights, idx, base, tex = [], [], [], [], [], [], 0, None
    for prim in g.meshes[node.mesh].primitives:
        at = prim.attributes
        p = f.acc(at.POSITION).astype(np.float32)
        ix = (f.acc(prim.indices).ravel() if prim.indices is not None else np.arange(len(p))).astype(np.uint32)
        pos.append(p)
        nrm.append(f.acc(at.NORMAL).astype(np.float32) if at.NORMAL is not None else _smooth_normals(p, ix))
        uv.append(f.acc(at.TEXCOORD_0).astype(np.float32) if at.TEXCOORD_0 is not None
                  else np.zeros((len(p), 2), np.float32))
        if use_skin:
            joints.append(f.acc(at.JOINTS_0).astype(np.int64))
            weights.append(f.acc(at.WEIGHTS_0).astype(np.float32))
        idx.append(ix + base)
        base += len(p)
        if tex is None and prim.material is not None:
            pbr = g.materials[prim.material].pbrMetallicRoughness
            if pbr and pbr.baseColorTexture is not None:
                tex = f.image(g.textures[pbr.baseColorTexture.index].source)
    m = MeshData(np.concatenate(pos), np.concatenate(nrm), np.concatenate(uv), np.concatenate(idx), texture=tex)
    if use_skin:
        w = np.concatenate(weights)
        m.joints = np.concatenate(joints)
        m.weights = w / np.maximum(w.sum(axis=1, keepdims=True), 1e-8)
    else:                                   # bake the node's world transform into the vertices
        world = _node_world(f, node_i)
        m.pos = (m.pos @ world[:3, :3].T + world[:3, 3]).astype(np.float32)
        n = m.nrm @ np.linalg.inv(world[:3, :3])
        m.nrm = (n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)).astype(np.float32)
    return m


def _local_matrix(n) -> np.ndarray:
    if n.matrix:
        return np.array(n.matrix, float).reshape(4, 4).T
    return compose(np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float),
                   np.array(n.scale or [1, 1, 1], float))


def _node_world(f: Gltf, i: int) -> np.ndarray:
    par = f.parents()
    m = _local_matrix(f.g.nodes[i])
    while i in par:
        i = par[i]
        m = _local_matrix(f.g.nodes[i]) @ m
    return m


def quat_to_mat3(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def compose(t: np.ndarray, q: np.ndarray, s: np.ndarray) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = quat_to_mat3(q) * s
    m[:3, 3] = t
    return m


def slerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        q = a + t * (b - a)
    else:
        th = np.arccos(min(d, 1.0))
        q = (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)
    return q / np.linalg.norm(q)


# ---------------------------------------------------------------------------- #
@dataclass
class Clip:
    name: str
    world: np.ndarray            # (F, J, 4, 4) joint world matrices (character space, meters)
    duration: float
    loop: bool
    native_speed: float          # m/s the clip moved before root motion was removed
    speed: float = 1.0           # playback rate multiplier from data

    def sample(self, t: float) -> np.ndarray:
        """Joint world matrices at time t (seconds), linearly interpolated."""
        n = len(self.world)
        if n == 1:
            return self.world[0]
        if self.loop:
            t = t % self.duration
        x = min(max(t, 0.0), self.duration) * BAKE_FPS
        i = min(int(x), n - 1)
        j = (i + 1) % n if self.loop else min(i + 1, n - 1)
        u = x - int(x)
        return self.world[i] * (1 - u) + self.world[j] * u


@dataclass
class Skeleton:
    """A skinned character: joint names, hierarchy, rest pose and inverse bind matrices."""
    path: Path
    joint_nodes: list[int]
    names: list[str]
    ibm: np.ndarray                          # (J, 4, 4)
    rest: list[tuple]                        # per node (t, q, s, matrix or None)
    parent: dict[int, int]
    node_names: list[str]
    order: list[int] = field(default_factory=list)   # nodes, parents before children

    @classmethod
    def load(cls, path: Path) -> "Skeleton":
        f = open_gltf(path)
        g = f.g
        node = next(n for n in g.nodes if n.mesh is not None and n.skin is not None)
        skin = g.skins[node.skin]
        rest = []
        for n in g.nodes:
            rest.append((np.array(n.translation or [0, 0, 0], float), np.array(n.rotation or [0, 0, 0, 1], float),
                         np.array(n.scale or [1, 1, 1], float),
                         np.array(n.matrix, float).reshape(4, 4).T if n.matrix else None))
        par = f.parents()
        order, seen = [], set()

        def visit(i):
            if i in seen:
                return
            if i in par:
                visit(par[i])
            seen.add(i)
            order.append(i)
        for i in range(len(g.nodes)):
            visit(i)
        return cls(path, list(skin.joints), [g.nodes[j].name for j in skin.joints],
                   f.acc(skin.inverseBindMatrices).reshape(-1, 4, 4).transpose(0, 2, 1).copy(),
                   rest, par, [n.name or "" for n in g.nodes], order)

    def node_index(self, name: str) -> int:
        return self.node_names.index(name)

    def joint_index(self, name: str) -> int:
        return self.names.index(name)

    def world_from(self, trs: list) -> np.ndarray:
        """World matrices of every node from per-node (t, q, s, matrix) tuples."""
        world = [None] * len(trs)
        for i in self.order:
            t, q, s, mat = trs[i]
            local = mat if mat is not None else compose(t, q, s)
            world[i] = world[self.parent[i]] @ local if i in self.parent else local
        return np.stack(world)

    def bind_world(self) -> np.ndarray:
        """(J, 4, 4) joint world matrices in the bind pose."""
        w = self.world_from(self.rest)
        return w[self.joint_nodes]

    def bake(self, source: Path, clip_ref: str | int, loop: bool, retarget: bool = False,
             speed: float = 1.0, name: str = "") -> Clip:
        """Sample a clip from `source` onto this skeleton at BAKE_FPS."""
        if not retarget and Path(source) != Path(self.path):
            # Same character, different file: Meshy's animation files can order the joints
            # differently and rotate the armature, so bake on the file's own skeleton and
            # carry the skinning matrices over by joint name (the mesh space is the same).
            src = load_skeleton(Path(source))
            raw = src.bake(source, clip_ref, loop, retarget=False, speed=speed, name=name)
            pal_src = np.einsum("fjab,jbc->fjac", raw.world.astype(float), src.ibm)
            bind_pal = np.einsum("jab,jbc->jac", self.bind_world(), self.ibm)
            pal = np.empty((len(raw.world), len(self.names), 4, 4))
            for j, n in enumerate(self.names):
                pal[:, j] = pal_src[:, src.names.index(n)] if n in src.names else bind_pal[j]
            world = np.einsum("fjab,jbc->fjac", pal, np.linalg.inv(self.ibm))
            return Clip(raw.name, world.astype(np.float32), raw.duration, loop, raw.native_speed, speed)
        f = open_gltf(source)
        g = f.g
        if isinstance(clip_ref, int):
            anim = g.animations[clip_ref]
        else:
            anim = next(a for a in g.animations if a.name == clip_ref)
        src_names = [n.name or "" for n in g.nodes]
        hips = next((n for n in self.node_names if n.lower() == "hips"), "Hips")
        scale_hips = 1.0
        if retarget and hips in src_names and hips in self.node_names:
            src_h = np.array(g.nodes[src_names.index(hips)].translation or [0, 0, 0], float)
            dst_h = self.rest[self.node_index(hips)][0]
            scale_hips = float(dst_h[1] / src_h[1]) if abs(src_h[1]) > 1e-6 else 1.0
        channels = []
        for ch in anim.channels:
            nm = src_names[ch.target.node]
            if nm not in self.node_names:
                continue
            path = ch.target.path
            if retarget and path == "translation" and nm != hips:
                continue                            # keep this skeleton's own bone lengths
            if path == "scale":
                continue
            s = anim.samplers[ch.sampler]
            times = f.acc(s.input).ravel().astype(float)
            vals = f.acc(s.output).astype(float)
            if s.interpolation == "CUBICSPLINE":
                vals = vals.reshape(len(times), 3, -1)[:, 1]
            channels.append((self.node_index(nm), path, times, vals, s.interpolation))
        duration = max((c[2][-1] for c in channels), default=0.0)
        frames = max(1, int(round(duration * BAKE_FPS)) + (0 if loop else 1))
        hips_node = self.node_index(hips) if hips in self.node_names else None
        T = np.minimum(np.arange(frames) / BAKE_FPS, duration)

        # per node, per frame translation / rotation / scale (all frames at once)
        N = len(self.rest)
        tr = np.empty((N, frames, 3))
        rq = np.empty((N, frames, 4))
        sc = np.empty((N, frames, 3))
        fixed = {}
        for i, (t0, q0, s0, mat) in enumerate(self.rest):
            tr[i], rq[i], sc[i] = t0, q0, s0
            if mat is not None:
                fixed[i] = mat
        for node, path, times, vals, interp in channels:
            k = np.clip(np.searchsorted(times, T, side="right") - 1, 0, len(times) - 1)
            k1 = np.minimum(k + 1, len(times) - 1)
            span = np.where(k1 > k, times[k1] - times[k], 1.0)
            u = np.where((k1 > k) & (interp != "STEP"), (T - times[k]) / span, 0.0)
            u = np.clip(u, 0.0, 1.0)[:, None]
            a, b = vals[k], vals[k1]
            if path == "rotation":
                d = (a * b).sum(axis=1, keepdims=True)
                b = np.where(d < 0, -b, b)
                q = a + u * (b - a)                 # nlerp: fine at 30 fps keyframe spacing
                rq[node] = q / np.linalg.norm(q, axis=1, keepdims=True)
            else:
                v = a + u * (b - a)
                tr[node] = v * scale_hips if (retarget and node == hips_node) else v
            fixed.pop(node, None)

        def local(i: int) -> np.ndarray:
            if i in fixed:
                return np.broadcast_to(fixed[i], (frames, 4, 4))
            x, y, z, w = (rq[i][:, c] for c in range(4))
            m = np.zeros((frames, 4, 4))
            m[:, 0, 0] = 1 - 2 * (y * y + z * z); m[:, 0, 1] = 2 * (x * y - z * w); m[:, 0, 2] = 2 * (x * z + y * w)
            m[:, 1, 0] = 2 * (x * y + z * w); m[:, 1, 1] = 1 - 2 * (x * x + z * z); m[:, 1, 2] = 2 * (y * z - x * w)
            m[:, 2, 0] = 2 * (x * z - y * w); m[:, 2, 1] = 2 * (y * z + x * w); m[:, 2, 2] = 1 - 2 * (x * x + y * y)
            m[:, :3, :3] *= sc[i][:, None, :]
            m[:, :3, 3] = tr[i]
            m[:, 3, 3] = 1.0
            return m

        world: dict[int, np.ndarray] = {}
        for i in self.order:
            world[i] = world[self.parent[i]] @ local(i) if i in self.parent else local(i)
        worlds = np.stack([world[j] for j in self.joint_nodes], axis=1)
        hip_xz = world[hips_node][:, [0, 2], 3] if hips_node is not None else np.zeros((frames, 2))
        native = 0.0
        if hips_node is not None and duration > 0:
            native = float(np.linalg.norm(hip_xz[-1] - hip_xz[0]) / duration)
            drift = hip_xz - hip_xz[0]                  # play in place: code moves the character
            worlds[:, :, 0, 3] -= drift[:, None, 0]
            worlds[:, :, 2, 3] -= drift[:, None, 1]
        return Clip(name or str(clip_ref), worlds.astype(np.float32), max(duration, 1 / BAKE_FPS),
                    loop, native, speed)


@lru_cache(maxsize=None)
def load_skeleton(path: Path) -> Skeleton:
    return Skeleton.load(path)


# ---------------------------------------------------------------------------- #
# Armor fitting (ARS-05): copy skin weights from the body to an outfit, then sort both
# into the four equipment slots by which bone each part follows.

SLOT_OF_JOINT = {
    "Head": "head", "neck": "head", "head_end": "head", "headfront": "head",
    "LeftForeArm": "arms", "LeftHand": "arms", "RightForeArm": "arms", "RightHand": "arms",
    "Spine": "torso", "Spine01": "torso", "Spine02": "torso", "LeftShoulder": "torso",
    "RightShoulder": "torso", "LeftArm": "torso", "RightArm": "torso",
}
SLOTS = ("head", "arms", "torso", "legs")


def slot_of(name: str) -> str:
    return SLOT_OF_JOINT.get(name, "legs")


# finer body parts for NPC outfits (hands and feet apart, so a coat never hides a villager's hands)
PARTS = ("head", "arms", "hands", "torso", "legs", "feet")


def part_of(name: str) -> str:
    if name in ("Head", "neck", "head_end", "headfront"):
        return "head"
    if name.endswith("Hand"):
        return "hands"
    if name.endswith("ForeArm") or name in ("LeftArm", "RightArm"):
        return "arms"
    if name.endswith("Foot") or name.endswith("ToeBase"):
        return "feet"
    if name.endswith("UpLeg") or name.endswith("Leg"):
        return "legs"
    return "torso"


def nearest_neighbours(a: np.ndarray, b: np.ndarray, k: int = 4, chunk: int = 1024) -> tuple[np.ndarray, np.ndarray]:
    """For each point in a: indices and distances of its k nearest points in b.

    Uses scipy's k-d tree when it's installed (dev machines); otherwise brute force in chunks.
    """
    try:
        from scipy.spatial import cKDTree
        d, i = cKDTree(b).query(a, k=k)
        return i.astype(np.int64), d.astype(np.float32)
    except ImportError:
        pass
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    bb = (b * b).sum(axis=1)
    idx = np.empty((len(a), k), np.int64)
    dist = np.empty((len(a), k), np.float32)
    for s in range(0, len(a), chunk):
        aa = a[s:s + chunk]
        d2 = (aa * aa).sum(axis=1)[:, None] + bb[None, :] - 2.0 * aa @ b.T
        part = np.argpartition(d2, k, axis=1)[:, :k]
        pd = np.take_along_axis(d2, part, axis=1)
        o = np.argsort(pd, axis=1)
        idx[s:s + chunk] = np.take_along_axis(part, o, axis=1)
        dist[s:s + chunk] = np.sqrt(np.maximum(np.take_along_axis(pd, o, axis=1), 0.0))
    return idx, dist


def fit_outfit(body: MeshData, skel: Skeleton, outfit: MeshData) -> MeshData:
    """Scale the outfit onto the body's bind pose and give it the body's skin weights.

    Both must be in the same pose (Meshy A-pose). Returns the outfit as a skinned mesh in
    the body's mesh space, so it plays every clip the body plays.
    """
    bind = np.einsum("jab,jbc->jac", skel.bind_world(), skel.ibm)   # mesh space -> character (meters)
    m2w = bind[0]                                                     # same for every joint at bind
    body_w = body.pos @ m2w[:3, :3].T + m2w[:3, 3]
    lo, hi = body_w.min(axis=0), body_w.max(axis=0)
    olo, ohi = outfit.pos.min(axis=0), outfit.pos.max(axis=0)
    s = (hi[1] - lo[1]) / (ohi[1] - olo[1])
    o = (outfit.pos - [(olo[0] + ohi[0]) / 2, olo[1], (olo[2] + ohi[2]) / 2]) * s
    o += [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]
    # back into the body's mesh space so the same skinning matrices apply
    w2m = np.linalg.inv(m2w)
    o_mesh = o @ w2m[:3, :3].T + w2m[:3, 3]

    J = len(skel.names)
    dense = np.zeros((len(body.pos), J), np.float32)
    np.add.at(dense, (np.repeat(np.arange(len(body.pos)), 4), body.joints.ravel()), body.weights.ravel())
    nn, dd = nearest_neighbours(o, body_w, k=4)
    inv = 1.0 / np.maximum(dd, 1e-4)
    inv /= inv.sum(axis=1, keepdims=True)
    w = np.einsum("vk,vkj->vj", inv, dense[nn])
    top = np.argsort(-w, axis=1)[:, :4]
    tw = np.take_along_axis(w, top, axis=1)
    tw /= np.maximum(tw.sum(axis=1, keepdims=True), 1e-8)
    return MeshData(o_mesh.astype(np.float32), outfit.nrm.copy(), outfit.uv, outfit.idx,
                    top.astype(np.int64), tw.astype(np.float32), outfit.texture)


def triangle_parts(mesh: MeshData, joint_names: list[str]) -> np.ndarray:
    """Part index (into PARTS) of every triangle, by the majority of its vertices' main bone."""
    main = mesh.joints[np.arange(len(mesh.joints)), np.argmax(mesh.weights, axis=1)]
    vpart = np.array([PARTS.index(part_of(n)) for n in joint_names])[main]
    tri = vpart[mesh.idx.reshape(-1, 3)]
    out = tri[:, 0].copy()
    out[tri[:, 1] == tri[:, 2]] = tri[tri[:, 1] == tri[:, 2], 1]
    return out


def triangle_slots(mesh: MeshData, joint_names: list[str]) -> np.ndarray:
    """Slot index (into SLOTS) of every triangle, by the majority of its vertices' main bone."""
    main = mesh.joints[np.arange(len(mesh.joints)), np.argmax(mesh.weights, axis=1)]
    vslot = np.array([SLOTS.index(slot_of(n)) for n in joint_names])[main]
    tri = vslot[mesh.idx.reshape(-1, 3)]
    out = tri[:, 0].copy()
    out[tri[:, 1] == tri[:, 2]] = tri[tri[:, 1] == tri[:, 2], 1]
    return out
