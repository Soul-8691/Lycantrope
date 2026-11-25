"""Skinned characters (TEC-08): Rowan, enemies, held items and worn armor.

Each character type has one mesh on the GPU; every character draws it with its own joint
matrices (computed from baked clips on the CPU, skinned in the vertex shader). Items are
rigid meshes attached to a joint. Armor (ARS-05) is the outfit mesh with Rowan's skin
weights, split into head/arms/torso/legs; the body parts it covers aren't drawn.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

from pyglm import glm
import moderngl
import numpy as np

from lycantrope.core.paths import ASSETS, ROOT
from lycantrope.render.camera import frustum_planes
from lycantrope.render.gltf import (SLOTS, Clip, MeshData, Skeleton, fit_outfit, load_mesh, load_skeleton,
                                    triangle_slots)
from lycantrope.render.shaders import ShaderLibrary, set_uniform
from lycantrope.world.actors import (Actor, AiParams, ClipInfo, Enemy, Rowan, load_character_data,
                                     load_spawns, separate)
from lycantrope.world.collision import Colliders
from lycantrope.world.heightfield import Heightfield

MODELS = ASSETS / "models" / "meshy"
CACHE = ROOT / "assets" / "cache"
MAX_JOINTS = 64
DRAW_DISTANCE = 300.0
WADE_DEPTH = 0.9           # meters, for a 1.75 m character (scaled by height)
STATIC_CLIPS = {"idle": ClipInfo(1.0, True), "walk": ClipInfo(1.0, True), "run": ClipInfo(1.0, True),
                "alert": ClipInfo(1.0, True), "attack1": ClipInfo(0.9, False), "attack2": ClipInfo(0.9, False),
                "hit": ClipInfo(0.5, False), "death": ClipInfo(1.0, False)}
RADIUS = {"rowan": 0.4, "goblin": 0.35, "wolf": 0.5, "bear": 0.9, "bruiser": 0.55, "battlemage": 0.4, "cow": 0.8, "villager_m": 0.35, "villager_f": 0.33, "farmer": 0.38}


# ---------------------------------------------------------------------------- #
@dataclass
class GpuMesh:
    vbo: moderngl.Buffer
    ibo: moderngl.Buffer
    ranges: list[tuple[int, int]]          # per slot (first index, count); one range if unsplit
    texture: moderngl.Texture | None
    vao: moderngl.VertexArray | None = None
    triangles: int = 0


def upload(ctx: moderngl.Context, m: MeshData, slots: np.ndarray | None = None) -> GpuMesh:
    V = len(m.pos)
    joints = m.joints.astype(np.float32) if m.joints is not None else np.zeros((V, 4), np.float32)
    weights = m.weights if m.weights is not None else np.tile([1.0, 0, 0, 0], (V, 1)).astype(np.float32)
    color = m.color if m.color is not None else np.ones((V, 3), np.float32)
    data = np.hstack([m.pos, m.nrm, m.uv, joints, weights, color]).astype("f4")
    tri = m.idx.reshape(-1, 3)
    ranges = []
    if slots is not None:
        order = np.argsort(slots, kind="stable")
        tri = tri[order]
        start = 0
        for s in range(len(SLOTS)):
            n = int((slots == s).sum()) * 3
            ranges.append((start, n))
            start += n
    else:
        ranges.append((0, tri.size))
    tex = None
    if m.texture is not None:
        img = m.texture
        tex = ctx.texture(img.size, 3, img.tobytes())
        tex.build_mipmaps()
        tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        tex.anisotropy = 4.0
    return GpuMesh(ctx.buffer(data.tobytes()), ctx.buffer(np.ascontiguousarray(tri, np.uint32).tobytes()),
                   ranges, tex, triangles=len(tri))


def normalized_static(m: MeshData, height: float) -> MeshData:
    """Feet on y = 0, centered in x/z, scaled to a height in meters."""
    lo, hi = m.pos.min(axis=0), m.pos.max(axis=0)
    s = height / (hi[1] - lo[1])
    m.pos = ((m.pos - [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]) * s).astype(np.float32)
    return m


# ---------------------------------------------------------------------------- #
@dataclass
class Item:
    gpu: GpuMesh


def load_item(ctx, spec: dict) -> tuple[MeshData, Item]:
    m = load_mesh(MODELS / spec["model"], skinned=False)
    p = m.pos.astype(np.float64)
    if "length_m" in spec:
        # blade/knife: put the grip at the origin, tip along +Y, edge along +Z
        axis = "xyz".index(spec.get("tip", "-x")[-1])
        sign = -1.0 if spec.get("tip", "-x").startswith("-") else 1.0
        along = p[:, axis] * sign                       # grows toward the tip
        length = along.max() - along.min()
        s = spec["length_m"] / length
        grip = along.min() + spec.get("grip_from_end", 0.1) * length
        others = [i for i in range(3) if i != axis]
        # thinner of the other two axes is the blade's thickness
        thick, edge = sorted(others, key=lambda i: np.ptp(p[:, i]))
        ctr = (p.max(axis=0) + p.min(axis=0)) / 2
        q = np.zeros_like(p)
        q[:, 1] = (along - grip) * s
        q[:, 2] = (p[:, edge] - ctr[edge]) * s
        q[:, 0] = (p[:, thick] - ctr[thick]) * s
        # keep the basis right-handed (mirror the thickness if needed)
        basis = np.zeros((3, 3))
        basis[thick, 0], basis[axis, 1], basis[edge, 2] = 1, sign, 1
        if np.linalg.det(basis) < 0:
            q[:, 0] = -q[:, 0]
        n = np.zeros_like(m.nrm)
        n[:, 1] = m.nrm[:, axis] * sign
        n[:, 2] = m.nrm[:, edge]
        n[:, 0] = m.nrm[:, thick] * (-1 if np.linalg.det(basis) < 0 else 1)
        m.pos, m.nrm = q.astype(np.float32), n.astype(np.float32)
        frac = (along - along.min()) / length
        c0 = np.array(spec.get("color", [0.6, 0.6, 0.6]), np.float32)
        c1 = np.array(spec.get("end_color", spec.get("color", [0.6, 0.6, 0.6])), np.float32)
        m.color = np.where((frac < spec.get("end_fraction", 0.0))[:, None], c1, c0).astype(np.float32)
    else:
        lo, hi = p.min(axis=0), p.max(axis=0)
        s = spec.get("height_m", 0.3) / (hi[1] - lo[1])
        m.pos = ((p - (lo + hi) / 2) * s).astype(np.float32)
    return m, Item(upload(ctx, m))


def look_basis(origin, y_dir, z_hint) -> np.ndarray:
    """4x4 with +Y along y_dir, +Z as close to z_hint as possible, right-handed."""
    y = np.asarray(y_dir, float)
    y /= np.linalg.norm(y)
    z = np.asarray(z_hint, float) - y * np.dot(z_hint, y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = x, y, z, origin
    return m


@dataclass
class Attachment:
    item: Item
    joint: int
    offset: np.ndarray            # joint world (bind) -> item, 4x4
    # two-handed weapons: where the other hand grips, in the item's frame (grip at the origin,
    # +Y toward the head), and that hand's joints (upper arm, forearm, hand)
    second_grip: np.ndarray | None = None
    second_chain: tuple[int, int, int] | None = None


def _rotation_between(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """3x3 rotation turning direction a onto direction b."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.9999:                                   # opposite: turn 180 degrees about any perpendicular
        p = np.cross(a, [1.0, 0.0, 0.0])
        if np.linalg.norm(p) < 1e-6:
            p = np.cross(a, [0.0, 1.0, 0.0])
        p /= np.linalg.norm(p)
        return 2.0 * np.outer(p, p) - np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1.0 + c)


def two_bone_ik(W: np.ndarray, chain: tuple[int, int, int], target: np.ndarray) -> None:
    """Bend an arm (upper arm, forearm, hand joint world matrices, in place) so the hand reaches
    target, keeping the elbow bending the way the animation had it."""
    i0, i1, i2 = chain
    S, E, H = W[i0][:3, 3].copy(), W[i1][:3, 3].copy(), W[i2][:3, 3].copy()
    a, b = np.linalg.norm(E - S), np.linalg.norm(H - E)
    to_t = target - S
    d = float(np.clip(np.linalg.norm(to_t), abs(a - b) + 1e-4, a + b - 1e-4))
    dir_t = to_t / max(np.linalg.norm(to_t), 1e-6)
    pole = (E - S) - dir_t * np.dot(E - S, dir_t)               # which way the elbow points now
    if np.linalg.norm(pole) < 1e-5:
        pole = np.cross(dir_t, [0.0, 1.0, 0.0])
    pole /= np.linalg.norm(pole)
    cos_s = (a * a + d * d - b * b) / (2 * a * d)                # law of cosines at the shoulder
    sin_s = np.sqrt(max(0.0, 1.0 - cos_s * cos_s))
    E2 = S + a * (dir_t * cos_s + pole * sin_s)
    H2 = S + dir_t * d
    R1 = _rotation_between(E - S, E2 - S)
    W[i0][:3, :3] = R1 @ W[i0][:3, :3]
    R2 = _rotation_between(R1 @ (H - E), H2 - E2)
    W[i1][:3, :3] = R2 @ R1 @ W[i1][:3, :3]
    W[i1][:3, 3] = E2
    W[i2][:3, :3] = R2 @ R1 @ W[i2][:3, :3]
    W[i2][:3, 3] = H2


# ---------------------------------------------------------------------------- #
@dataclass
class CharType:
    key: str
    skel: Skeleton | None
    body: GpuMesh
    clips: dict[str, Clip]
    info: dict[str, ClipInfo]
    speeds: dict[str, float]
    ai: AiParams | None
    attachments: list[Attachment] = field(default_factory=list)
    armor: GpuMesh | None = None
    armor_slots: tuple[str, ...] = ()
    height: float = 1.0           # in the world, after scale
    scale: float = 1.0            # rigs Meshy left at their own size (quadrupeds) -> height_m
    lift: float = 0.0             # raise the rig so its bind-pose feet sit on y = 0 (rig units)
    turn: float = 0.0             # radians about y so the model faces +z (Meshy doesn't always)
    spell: dict | None = None     # casters: projectile look (speed_m_s, radius_m, color)


def _fit_cached(body: MeshData, skel: Skeleton, outfit_path: Path, rig_path: Path) -> MeshData:
    outfit = load_mesh(outfit_path, skinned=False)
    h = hashlib.sha1(f"{outfit_path.stat().st_size}:{outfit_path.stat().st_mtime_ns}:"
                     f"{rig_path.stat().st_size}:{rig_path.stat().st_mtime_ns}:v1".encode()).hexdigest()[:16]
    cache = CACHE / f"armor_{outfit_path.parent.parent.parent.name}_{h}.npz"
    if cache.exists():
        d = np.load(cache)
        return MeshData(d["pos"], d["nrm"], outfit.uv, outfit.idx, d["joints"], d["weights"], outfit.texture)
    fit = fit_outfit(body, skel, outfit)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, pos=fit.pos, nrm=fit.nrm, joints=fit.joints, weights=fit.weights)
    return fit


def load_type(ctx, key: str, spec: dict, items: dict, armor_specs: dict) -> CharType:
    rig = MODELS / spec["rig"] if spec.get("rig") else None
    ai = AiParams(**{k: tuple(v) if isinstance(v, list) else v for k, v in spec["ai"].items()}) if "ai" in spec else None
    idle = spec.get("clips", {}).get("idle")
    animated = rig is not None and rig.exists() and idle is not None and (MODELS / idle["file"]).exists()
    if rig is not None and rig.exists() and not animated and "static" in spec:
        print(f"characters: {key} is rigged but has no idle clip yet; drawing the static model")
    if animated or (rig is not None and rig.exists() and "static" not in spec):
        skel = load_skeleton(rig)
        body = load_mesh(rig)
        if "skirt" in spec:
            soften_skirt(body, skel, spec["skirt"])
        clips, info = {}, {}
        for name, c in spec["clips"].items():
            f = MODELS / c["file"]
            if not f.exists():
                continue
            clip = skel.bake(f, c["clip"], loop=c.get("loop", False), retarget=c.get("retarget", False),
                             speed=c.get("speed", 1.0), name=name)
            clips[name] = clip
            info[name] = ClipInfo(clip.duration, clip.loop, clip.speed, c.get("move_speed", 0.0))
        bind = skel.bind_world()
        m2w = bind[0] @ skel.ibm[0]
        bind_y = body.pos @ m2w[:3, 1] + m2w[1, 3]
        height = float(np.ptp(bind_y))
        scale = spec["height_m"] / height if "height_m" in spec else 1.0
        # Meshy's quadruped rigs put the origin mid-body, so lift them onto the ground
        t = CharType(key, skel, None, clips, info, spec["speeds"], ai, height=height * scale, scale=scale,
                     lift=-float(bind_y.min()), turn=math.radians(spec.get("turn_deg", 0.0)))
        # armor first: it decides which body parts are drawn
        slots = None
        eq = spec.get("equipment", {})
        if "armor" in eq and eq["armor"] in armor_specs:
            a = armor_specs[eq["armor"]]
            outfit_path = MODELS / a["model"]
            if outfit_path.exists():
                fit = _fit_cached(body, skel, outfit_path, rig)
                t.armor = upload(ctx, fit, triangle_slots(fit, skel.names))
                t.armor_slots = tuple(a.get("slots", SLOTS))
                slots = triangle_slots(body, skel.names)
        t.body = upload(ctx, body, slots)
        # held and hung items
        for slot, item_id in eq.items():
            if slot == "armor" or item_id not in items:
                continue
            ispec = items[item_id]
            if not (MODELS / ispec["model"]).exists():
                continue
            _m, item = load_item(ctx, ispec)
            att = place_item(skel, bind, slot, item, body, ispec)
            if ispec.get("two_handed") and slot in ("right_hand", "left_hand"):
                other = "Left" if slot == "right_hand" else "Right"
                L = ispec["length_m"]
                # the second hand sits this far from the main grip, toward the end of the handle
                gap = (ispec.get("grip_from_end", 0.1) - ispec.get("second_grip_from_end", 0.08)) * L
                att.second_grip = np.array([0.0, -gap, 0.0, 1.0])
                att.second_chain = tuple(skel.joint_index(f"{other}{j}") for j in ("Arm", "ForeArm", "Hand"))
            t.attachments.append(att)
        return t
    # not rigged yet: a static mesh moved by code
    m = normalized_static(load_mesh(MODELS / spec["static"], skinned=False), spec.get("height_m", 1.0))
    return CharType(key, None, upload(ctx, m), {}, dict(STATIC_CLIPS), spec["speeds"], ai,
                    height=spec.get("height_m", 1.0))


def hand_center(skel: Skeleton, body: MeshData, joint: int, bind: np.ndarray) -> np.ndarray | None:
    """Middle of the hand mesh in the bind pose: vertices that mostly follow the hand bone."""
    if body.joints is None:
        return None
    main = body.joints[np.arange(len(body.joints)), np.argmax(body.weights, axis=1)]
    pts = body.pos[main == joint]
    if len(pts) < 10:
        return None
    m2w = bind[0] @ skel.ibm[0]
    pts = pts @ m2w[:3, :3].T + m2w[:3, 3]
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    return (lo + hi) / 2                     # box center: fingers and thumb pull a mean around


def soften_skirt(body: MeshData, skel: Skeleton, cfg: dict) -> None:
    """Long skirts and robes: move most of the thigh/shin weight onto the hips, so the cloth
    hangs and sways instead of splitting with each stride. Feet keep their own weights."""
    legs = [skel.joint_index(n) for n in ("LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg", "LeftFoot",
                                          "RightFoot", "LeftToeBase", "RightToeBase") if n in skel.names]
    hips = skel.joint_index(cfg.get("to", "Hips"))
    amount = float(cfg.get("amount", 0.75))
    m2w = skel.bind_world()[0] @ skel.ibm[0]
    y = body.pos @ m2w[:3, 1] + m2w[1, 3]
    above = y > float(cfg.get("min_height_m", 0.2)) * (y.max() - y.min()) / 1.7 + y.min()
    # only cloth: vertices well away from the leg bones (the legs inside the skirt stay as they are)
    bw = skel.bind_world()
    pw = body.pos @ m2w[:3, :3].T + m2w[:3, 3]
    near_leg = np.full(len(pw), np.inf)
    for side in ("Left", "Right"):
        pts = [bw[skel.joint_index(f"{side}{n}")][:3, 3] for n in ("UpLeg", "Leg", "Foot")]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            d = p1 - p0
            t = np.clip(((pw - p0) @ d) / max(float(d @ d), 1e-9), 0.0, 1.0)
            near_leg = np.minimum(near_leg, np.linalg.norm(pw - (p0 + t[:, None] * d), axis=1))
    cloth = near_leg > float(cfg.get("cloth_from_m", 0.11)) * (y.max() - y.min()) / 1.7
    j, w = body.joints.copy(), body.weights.copy()
    moved = np.zeros(len(w), np.float32)
    for k in range(4):
        on_leg = np.isin(j[:, k], legs) & above & cloth
        take = w[:, k] * amount * on_leg
        w[:, k] -= take
        moved += take
    # put the moved weight on the hips: reuse a hips slot if there is one, else the smallest slot
    has_hips = j == hips
    slot = np.where(has_hips.any(axis=1), has_hips.argmax(axis=1), w.argmin(axis=1))
    rows = np.arange(len(w))
    give = moved > 0
    j[rows[give], slot[give]] = hips
    w[rows[give], slot[give]] += moved[give]
    body.joints, body.weights = j, w / np.maximum(w.sum(axis=1, keepdims=True), 1e-8)

    # webbing: Meshy sometimes joins the legs with mesh bound to both of them at once (under a long
    # skirt, near the ankles); it tears apart whenever the legs part, so drop those triangles
    def side_weight(side):
        ids = [skel.joint_index(f"{side}{n}") for n in ("UpLeg", "Leg", "Foot", "ToeBase") if f"{side}{n}" in skel.names]
        return (body.weights * np.isin(body.joints, ids)).sum(axis=1)
    both = (side_weight("Left") >= 0.2) & (side_weight("Right") >= 0.2)
    low = y < y.min() + float(cfg.get("web_below", 0.5)) * (y.max() - y.min())
    tri = body.idx.reshape(-1, 3)
    web = (both & low)[tri].any(axis=1)
    body.idx = np.ascontiguousarray(tri[~web].ravel())


def place_item(skel: Skeleton, bind: np.ndarray, slot: str, item: Item, body: MeshData | None = None,
               spec: dict | None = None) -> Attachment:
    def pos(name):
        return bind[skel.joint_index(name)][:3, 3]
    spec = spec or {}
    if slot in ("right_hand", "left_hand"):
        side = "Right" if slot == "right_hand" else "Left"
        joint = skel.joint_index(f"{side}Hand")
        hand, fore = pos(f"{side}Hand"), pos(f"{side}ForeArm")
        arm = (hand - fore) / np.linalg.norm(hand - fore)
        grip = hand_center(skel, body, joint, bind) if body is not None else None
        if grip is None:
            grip = hand + arm * 0.075                   # palm center, a bit past the wrist
        if spec.get("hold") == "along_arm":
            # heavy two-handers: the haft runs along the forearm (head past the fingers), tipped a
            # little forward so the handle clears the arm; overhead swings then bring the head down
            fwd = np.array([0.0, 0.0, 1.0]) - arm * arm[2]
            fwd /= np.linalg.norm(fwd)
            t = np.radians(spec.get("tilt_deg", 18.0))
            blade = arm * np.cos(t) + fwd * np.sin(t)
            world = look_basis(grip, blade, fwd)
        else:
            # blade forward (and a little up), square to the forearm like a fist grip
            blade = np.array([0.0, 0.35, 1.0])
            blade = blade - arm * np.dot(blade, arm)
            world = look_basis(grip, blade, [0.0, 1.0, 0.0])
    else:                                               # hip_left / hip_right: hang beside the thigh
        side = "Left" if slot == "hip_left" else "Right"
        leg = pos(f"{side}UpLeg")
        out = np.sign(leg[0] - pos("Hips")[0]) or 1.0
        world = np.eye(4)
        world[:3, 0], world[:3, 1], world[:3, 2] = [0, 0, -1], [0, 1, 0], [1, 0, 0]
        world[:3, 3] = leg + [out * 0.17, -0.12, 0.02]
        joint = skel.joint_index("Hips")
    return Attachment(item, joint, np.linalg.inv(bind[joint]) @ world)


# ---------------------------------------------------------------------------- #
def rot_y(h: float) -> np.ndarray:
    c, s = math.cos(h), math.sin(h)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], float)


@dataclass
class Character:
    t: CharType
    actor: Actor
    brain: Enemy | None = None
    phase: float = 0.0            # static meshes: gait phase for the bob
    grip2: float = 0.0            # two-handed weapons: how much the second hand is on the haft (0..1)
    size: float = 1.0             # per-character height/build variation
    tint: tuple[float, float, float] = (1.0, 1.0, 1.0)   # per-character colour variation


class CharacterSystem:
    def __init__(self, ctx: moderngl.Context, shaders: ShaderLibrary, world: Heightfield) -> None:
        self.ctx = ctx
        self.shaders = shaders
        self.world = world
        data = load_character_data()
        self.types: dict[str, CharType] = {}
        for key, spec in data["characters"].items():
            try:
                self.types[key] = load_type(ctx, key, spec, data["items"], data.get("armor", {}))
                self.types[key].spell = spec.get("spell")
            except (FileNotFoundError, KeyError, ValueError) as exc:
                print(f"characters: can't load {key}: {exc}")
        self.helmet = True
        from lycantrope.render.spells import Spells
        self.spells = Spells(ctx, shaders, world)
        self.chars: list[Character] = []
        self.rowan: Rowan | None = None
        self.colliders: Colliders | None = None     # solid props, set by set_colliders()
        self.spawn(load_spawns())
        self._version = -1
        self.drawn = 0

    def set_colliders(self, colliders: Colliders) -> None:
        """Make props solid: characters slide around them, wanderers don't aim inside them, and
        anyone who spawned overlapping one is nudged out."""
        self.colliders = colliders
        for c in self.chars:
            a = c.actor
            a.x, a.z, _ = colliders.push_out(a.x, a.z, a.radius, passes=4)
            a.y = self.world.height_at(a.x, a.z)
            a.save_prev()
            b = c.brain
            if b is not None and colliders.blocked(*b.home, a.radius):
                b.home = (a.x, a.z)                           # home was inside something: use where it stands
            if b is not None and b.goal_ok is None and not b.route:
                b.goal_ok = lambda _x0, _z0, x1, z1, r=a.radius: not colliders.blocked(x1, z1, r + 0.3)

    # ------------------------------------------------------------------ #
    def _actor(self, key: str, x: float, z: float, heading: float) -> Actor:
        t = self.types[key]
        a = Actor(key, x, z, heading, t.info, t.speeds, radius=RADIUS.get(key, 0.5))
        a.y = self.world.height_at(x, z)
        a.anim.rate = 0.0                     # start in the plain stance; the idle plays after a wait
        a.save_prev()
        return a

    def spawn(self, spawns: dict) -> None:
        anchors = {p.name: p for p in self.world.landmarks + self.world.waystones}
        r = spawns["rowan"]
        if "rowan" in self.types:
            an = anchors[r["anchor"]]
            f = math.radians(r.get("facing", 0))
            ra = self._actor("rowan", an.x + r["at"][0], an.z - r["at"][1], math.atan2(math.sin(f), -math.cos(f)))
            self.rowan = Rowan(ra)
            self.chars.append(Character(self.types["rowan"], ra))
        rng = random.Random(7)
        for gi, g in enumerate(spawns["groups"]):
            if g["kind"] not in self.types or g["anchor"] not in anchors:
                continue
            an = anchors[g["anchor"]]
            cx, cz = an.x + g["at"][0], an.z - g["at"][1]
            t = self.types[g["kind"]]
            route = [(an.x + e, an.z - n) for e, n in g.get("route", [])]
            for i in range(g["count"]):
                ang, rad = rng.uniform(0, math.tau), g.get("radius", 0) * math.sqrt(rng.random())
                x, z = cx + rad * math.cos(ang), cz + rad * math.sin(ang)
                start = rng.randrange(len(route)) if route else 0
                if route:                                    # travellers start somewhere along their road
                    x, z = route[start]
                elif t.ai is not None and t.ai.on_paths:     # path walkers start on a path
                    x, z = self.nearest_path(x, z)
                a = self._actor(g["kind"], x, z, rng.uniform(0, math.tau))
                brain = Enemy(a, (x, z), t.ai or AiParams(), seed=gi * 100 + i)
                ch = Character(t, a, brain)
                vary = g.get("vary", {})
                if vary:                                     # no two villagers quite alike
                    lo, hi = vary.get("height", (1.0, 1.0))
                    ch.size = rng.uniform(lo, hi)
                    k = float(vary.get("tint", 0.0))
                    base = rng.uniform(1 - k, 1 + k)
                    ch.tint = tuple(base * rng.uniform(1 - k / 2, 1 + k / 2) for _ in range(3))
                    plo, phi = vary.get("pace", (1.0, 1.0))
                    pace = rng.uniform(plo, phi)
                    a.speeds = {s: v * pace for s, v in a.speeds.items()}
                if route:
                    brain.set_route(route, start, rng.choice((-1, 1)))
                elif brain.ai.on_paths:
                    brain.goal_ok = self.path_walk_ok
                self.chars.append(ch)

    def nearest_path(self, x: float, z: float, max_m: float = 40.0) -> tuple[float, float]:
        """The closest point on a path (middle of it), searching outward up to max_m."""
        w = self.world
        for r in np.arange(0.0, max_m, 1.5):
            for k in range(max(1, int(r * 2))):
                t = k / max(1, int(r * 2)) * math.tau
                px, pz = x + r * math.cos(t), z + r * math.sin(t)
                c, rr = w._px(px, pz)
                ci, ri = int(round(c)), int(round(rr))
                if 0 <= ci < w.size and 0 <= ri < w.size and w.road[ri, ci] >= 170:
                    return px, pz
        return x, z

    def path_walk_ok(self, x0: float, z0: float, x1: float, z1: float) -> bool:
        """Is (x1, z1) on a path, and is the straight walk there along paths (or from off-path)?"""
        w = self.world

        def road(x, z):
            c, r = w._px(x, z)
            ci, ri = int(round(c)), int(round(r))
            return int(w.road[ri, ci]) if 0 <= ci < w.size and 0 <= ri < w.size else 0
        if road(x1, z1) < 120:
            return False
        start_on = road(x0, z0) >= 60
        steps = max(8, int(math.hypot(x1 - x0, z1 - z0) / 1.5))    # a check every 1.5 m
        for k in range(1, steps):
            t = k / steps
            if road(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) < (110 if start_on else 0):
                return False
        return True

    def chased(self, range_m: float) -> bool:
        """Is any enemy within range_m actively after Rowan (for the combat music)?"""
        if self.rowan is None or self.rowan.a.state == "dead":
            return False
        r = self.rowan.a
        return any(c.brain is not None and c.actor.state in ("chase", "engage", "attack", "cast")
                   and (c.actor.x - r.x) ** 2 + (c.actor.z - r.z) ** 2 < range_m * range_m
                   for c in self.chars)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.chars:
            out[c.actor.kind] = out.get(c.actor.kind, 0) + 1
        return out

    # ------------------------------------------------------------------ #
    def update(self, inp, cam_yaw: float, dt: float) -> None:
        if self.rowan is None:
            return
        ra = self.rowan.a
        for c in self.chars:
            c.actor.save_prev()
            want = 1.0 if c.actor.state == "attack" else 0.0      # both hands for the swing only
            c.grip2 += (want - c.grip2) * min(1.0, dt * 7.0)
        self.rowan.update(inp, cam_yaw, dt)
        alive = ra.state != "dead"
        near = [c.actor for c in self.chars                    # only these can bump into each other
                if abs(c.actor.x - ra.x) < 150 and abs(c.actor.z - ra.z) < 150]
        for c in self.chars:
            if c.brain is not None:
                far = math.hypot(c.actor.x - ra.x, c.actor.z - ra.z) > 300
                if far and c.actor.state == "wander" and c.brain.goal is None:
                    c.actor.timer -= dt                     # sleeping: just count down
                    continue
                c.brain.update(ra, alive, dt)
                if c.brain.should_release():                   # a caster lets its spell go
                    a, sp = c.actor, c.t.spell or {}
                    fwd = (math.sin(a.heading), math.cos(a.heading))
                    start = (a.x + fwd[0] * 0.6, a.y + c.t.height * 0.72, a.z + fwd[1] * 0.6)
                    target = (ra.x, ra.y + 1.2, ra.z)
                    self.spells.cast(start, target, float(sp.get("speed_m_s", 16)), float(sp.get("radius_m", 0.28)),
                                     sp.get("color", (1.0, 0.45, 0.12)))
        separate(near)
        self.spells.update(dt)
        lim = self.world.half - 5
        for c in self.chars:
            a = c.actor
            if a.x == a.px and a.z == a.pz:                   # didn't move: ground is the same
                a.advance(dt)
                continue
            a.x = min(max(a.x, -lim), lim)
            a.z = min(max(a.z, -lim), lim)
            if self.colliders is not None:                     # houses, trunks, fences, rocks
                a.x, a.z, hit = self.colliders.push_out(a.x, a.z, a.radius)
                if hit and c.brain is not None:
                    c.brain.bumped += dt
            # no swimming yet: wading is fine, deeper water stops you at the edge
            if self.world.water_depth(a.x, a.z) > WADE_DEPTH * (c.t.height / 1.75) and                     self.world.water_depth(a.x, a.z) > self.world.water_depth(a.px, a.pz):
                a.x, a.z = a.px, a.pz
                a.speed = 0.0
                if c.brain is not None:
                    c.brain.goal = None
            a.y = self.world.height_at(a.x, a.z)
            a.advance(dt)
            if c.t.skel is None:
                c.phase += a.speed * dt * 2.2

    # ------------------------------------------------------------------ #
    def _program(self) -> moderngl.Program:
        prog = self.shaders.get("skinned")
        if self._version != self.shaders.version:
            def vao(g: GpuMesh):
                g.vao = self.ctx.vertex_array(prog, [(g.vbo, "3f 3f 2f 4f 4f 3f", "in_pos", "in_nrm", "in_uv",
                                                      "in_joints", "in_weights", "in_color")],
                                              index_buffer=g.ibo, index_element_size=4)
            for t in self.types.values():
                vao(t.body)
                if t.armor:
                    vao(t.armor)
                for at in t.attachments:
                    vao(at.item.gpu)
            self._version = self.shaders.version
        return prog

    def joint_worlds(self, c: Character) -> np.ndarray:
        t, an = c.t, c.actor.anim
        cur = t.clips.get(an.clip) or t.clips.get("idle")
        w = cur.sample(an.time)
        if an.fade < 1.0 and an.prev in t.clips:
            f = an.fade * an.fade * (3 - 2 * an.fade)
            w = t.clips[an.prev].sample(an.prev_time) * (1 - f) + w * f
        for at in t.attachments:                     # two-handed weapons: pull the other hand onto the haft
            if at.second_chain is not None and c.grip2 > 0.01:
                base = w.astype(float, copy=True)
                ik = base.copy()
                target = (base[at.joint] @ at.offset @ at.second_grip)[:3]
                two_bone_ik(ik, at.second_chain, target)
                k = c.grip2 * c.grip2 * (3 - 2 * c.grip2)
                w = base + (ik - base) * k
        return w

    def _draw(self, prog, g: GpuMesh, slots_on: list[int] | None = None) -> None:
        if g.texture is not None:
            g.texture.use(5)
            set_uniform(prog, "u_tex", 5)
        set_uniform(prog, "u_has_tex", 1 if g.texture is not None else 0)
        ranges = g.ranges if slots_on is None else [g.ranges[i] for i in slots_on]
        for first, count in ranges:
            if count:
                g.vao.render(moderngl.TRIANGLES, vertices=count, first=first)

    def render(self, eye: glm.vec3, viewproj: glm.mat4, env: dict, alpha: float) -> None:
        if not self.chars:
            return
        prog = self._program()
        set_uniform(prog, "u_viewproj", viewproj)
        set_uniform(prog, "u_cam", eye)
        for k, v in env.items():
            set_uniform(prog, k, v)
        planes = frustum_planes(viewproj)
        e = np.array([eye.x, eye.y, eye.z])
        # cull everyone at once (one numpy pass), then only loop over who's on screen
        pos = np.array([(c.actor.x, c.actor.y + c.t.height * 0.5, c.actor.z) for c in self.chars])
        rad = np.array([max(c.t.height, 1.0) * 1.2 for c in self.chars])
        vis = np.linalg.norm(pos - e, axis=1) <= DRAW_DISTANCE
        vis &= ((pos @ planes[:, :3].T + planes[:, 3]) >= -rad[:, None] - 1.0).all(axis=1)
        drawn = 0
        for idx in np.nonzero(vis)[0]:
            c = self.chars[idx]
            a, t = c.actor, c.t
            x = a.px + (a.x - a.px) * alpha
            y = a.py + (a.y - a.py) * alpha
            z = a.pz + (a.z - a.pz) * alpha
            dh = (a.heading - a.ph + math.pi) % math.tau - math.pi
            h = a.ph + dh * alpha
            model = np.eye(4)
            model[:3, 3] = (x, y, z)
            model = model @ rot_y(h + t.turn)
            sc = t.scale * c.size
            if sc != 1.0:
                model = model @ np.diag([sc, sc, sc, 1.0])
            if abs(t.lift) > 1e-4:
                up = np.eye(4)
                up[1, 3] = t.lift
                model = model @ up
            drawn += 1
            if t.skel is None:
                self._draw_static(prog, c, model)
                continue
            W = self.joint_worlds(c)
            palette = np.einsum("jab,jbc->jac", W, t.skel.ibm)
            buf = np.zeros((MAX_JOINTS, 4, 4), np.float32)
            buf[:len(palette)] = palette
            prog["u_joints"].write(np.ascontiguousarray(buf.transpose(0, 2, 1)).tobytes())
            set_uniform(prog, "u_model", glm.mat4(*model.T.ravel()))
            set_uniform(prog, "u_skinned", 1)
            set_uniform(prog, "u_tint", glm.vec3(*c.tint))
            if t.armor is not None:
                covered = [SLOTS.index(s) for s in t.armor_slots if s != "head" or self.helmet]
                bare = [i for i in range(len(SLOTS)) if i not in covered]
                self._draw(prog, t.body, bare)
                self._draw(prog, t.armor, covered)
            else:
                self._draw(prog, t.body)
            set_uniform(prog, "u_skinned", 0)
            for at in t.attachments:
                m = model @ W[at.joint].astype(float) @ at.offset
                set_uniform(prog, "u_model", glm.mat4(*m.T.ravel()))
                self._draw(prog, at.item.gpu)
        self.drawn = drawn
        self.spells.render(eye, viewproj, env, alpha)

    def _draw_static(self, prog, c: Character, model: np.ndarray) -> None:
        """Rigless animals: a bob while moving, a lunge when attacking, lying down when dead."""
        set_uniform(prog, "u_tint", glm.vec3(*c.tint))
        a, t = c.actor, c.t
        h = t.height
        bob = abs(math.sin(c.phase)) * 0.035 * h * min(1.0, a.speed / 2.0)
        pitch, fwd = 0.0, 0.0
        if a.anim.clip.startswith("attack"):
            u = min(a.anim.time / 0.9, 1.0)
            fwd = 0.45 * h * math.sin(math.pi * u)
            pitch = -0.35 * math.sin(math.pi * u)
        local = np.eye(4)
        local[1, 3] = bob
        local[2, 3] = fwd
        if pitch:
            cp, sp = math.cos(pitch), math.sin(pitch)
            local = local @ np.array([[1, 0, 0, 0], [0, cp, -sp, 0], [0, sp, cp, 0], [0, 0, 0, 1]])
        m = model @ local
        set_uniform(prog, "u_skinned", 0)
        set_uniform(prog, "u_model", glm.mat4(*m.T.ravel()))
        self._draw(prog, t.body)
