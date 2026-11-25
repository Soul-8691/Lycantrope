"""Animation made in code for humanoid rigs that have no clip for it yet (ART-04): swimming.

Poses are built by aiming bones (shoulder->elbow, elbow->wrist, hip->knee, ...) at directions given
in the character's own upright frame (y up, +z the way it faces, +x its left), each rotation
carrying the bone's children along. For the breaststroke the whole body is then pitched forward
about the hips, so "overhead" in the upright frame becomes "ahead" in the water. The result is an
ordinary looping Clip; a real swim clip in data/characters.json replaces it.
"""
from __future__ import annotations

import math

import numpy as np

from lycantrope.render.gltf import BAKE_FPS, Clip, Skeleton


def _rotation_between(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.9999:
        p = np.cross(a, [1.0, 0.0, 0.0])
        if np.linalg.norm(p) < 1e-6:
            p = np.cross(a, [0.0, 1.0, 0.0])
        p /= np.linalg.norm(p)
        return 2.0 * np.outer(p, p) - np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1.0 + c)


def _rot_x(deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def _norm(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


class Rig:
    """Joint hierarchy helpers on top of a Skeleton."""

    def __init__(self, skel: Skeleton) -> None:
        self.skel = skel
        self.names = skel.names
        node_to_joint = {n: j for j, n in enumerate(skel.joint_nodes)}
        self.parent = []
        for n in skel.joint_nodes:
            p = skel.parent.get(n)
            while p is not None and p not in node_to_joint:
                p = skel.parent.get(p)
            self.parent.append(node_to_joint[p] if p is not None else -1)
        J = len(self.names)
        self.below = []                                   # each joint and everything under it
        for j in range(J):
            out = [j]
            for k in range(J):
                p = self.parent[k]
                while p != -1:
                    if p == j:
                        out.append(k)
                        break
                    p = self.parent[p]
            self.below.append(np.array(sorted(set(out))))

    def has(self, *names: str) -> bool:
        return all(n in self.names for n in names)

    def j(self, name: str) -> int:
        return self.names.index(name)

    def rotate(self, W: np.ndarray, joint: int, R: np.ndarray) -> None:
        """Rotate a joint and everything below it by R (character space) about the joint."""
        p = W[joint, :3, 3].copy()
        idx = self.below[joint]
        W[idx, :3, :3] = np.einsum("ab,jbc->jac", R, W[idx, :3, :3])
        W[idx, :3, 3] = (W[idx, :3, 3] - p) @ R.T + p

    def aim(self, W: np.ndarray, joint: str, child: str, direction, pre: np.ndarray | None = None) -> None:
        """Point the bone joint->child along `direction` (given in the upright frame; `pre` maps
        it into the current frame)."""
        a, b = self.j(joint), self.j(child)
        cur = W[b, :3, 3] - W[a, :3, 3]
        d = _norm(direction)
        if pre is not None:
            d = pre @ d
        self.rotate(W, a, _rotation_between(cur, d))


def _keyed(keys: list[tuple[float, tuple]], u: float) -> np.ndarray:
    """Smoothly blend direction keyframes [(phase, dir), ...] around a loop at phase u."""
    keys = sorted(keys)
    for i, (k0, v0) in enumerate(keys):
        k1, v1 = keys[(i + 1) % len(keys)]
        span = (k1 - k0) % 1.0 or 1.0
        t = (u - k0) % 1.0
        if t <= span:
            f = t / span
            f = f * f * (3 - 2 * f)
            return _norm(np.asarray(v0, float) * (1 - f) + np.asarray(v1, float) * f)
    return _norm(keys[0][1])


# breaststroke, upright frame (before the body is laid forward): +y overhead = ahead in the water,
# +z the chest side = toward the bottom, -z the back = toward the surface. s = +1 left, -1 right.
ARM_UPPER = [(0.00, (0.12, 1.0, 0.10)), (0.25, (0.75, 0.75, 0.25)), (0.45, (0.85, 0.0, 0.55)),
             (0.62, (0.35, -0.35, 0.85)), (0.80, (0.15, 0.8, 0.5))]
ARM_FORE = [(0.00, (0.05, 1.0, 0.08)), (0.25, (0.75, 0.7, 0.30)), (0.45, (-0.2, 0.5, 0.8)),
            (0.62, (-0.6, 0.6, 0.5)), (0.80, (0.0, 1.0, 0.3))]
LEG_THIGH = [(0.00, (0.08, -1.0, 0.0)), (0.45, (0.08, -1.0, 0.0)), (0.62, (0.35, -0.85, 0.35)),
             (0.78, (0.30, -0.9, 0.10)), (0.92, (0.08, -1.0, 0.0))]
LEG_SHIN = [(0.00, (0.05, -1.0, -0.05)), (0.45, (0.05, -1.0, -0.05)), (0.62, (0.3, -0.25, -0.9)),
            (0.78, (0.5, -0.8, 0.1)), (0.92, (0.05, -1.0, -0.05))]
LEG_FOOT = [(0.00, (0.0, -1.0, -0.25)), (0.45, (0.0, -1.0, -0.25)), (0.62, (0.4, -0.1, -0.9)),
            (0.78, (0.4, -0.6, -0.2)), (0.92, (0.0, -1.0, -0.25))]


def _mirror(v, s: float) -> tuple:
    return (v[0] * s, v[1], v[2])


def swim_pose(rig: Rig, bind: np.ndarray, u: float, moving: bool) -> np.ndarray:
    """Joint world matrices at loop phase u: breaststroke (moving) or treading water (still)."""
    W = bind.astype(float).copy()
    wave = math.sin(math.tau * u)
    for side, s in (("Left", 1.0), ("Right", -1.0)):
        if moving:
            arm_u, arm_f = _keyed(ARM_UPPER, u), _keyed(ARM_FORE, u)
            th, sh, ft = _keyed(LEG_THIGH, u), _keyed(LEG_SHIN, u), _keyed(LEG_FOOT, u)
        else:
            # treading water: hands scull out and in just under the surface, legs cycle slowly
            k = math.sin(math.tau * u + (0 if s > 0 else math.pi))
            arm_u = _norm((0.8, -0.45, 0.35))
            arm_f = _norm((0.3 + 0.45 * wave, -0.15, 0.9))
            th = _norm((0.15, -0.8, 0.45 + 0.2 * k))
            sh = _norm((0.1, -1.0, -0.35 + 0.3 * math.cos(math.tau * u + (0 if s > 0 else math.pi))))
            ft = _norm((0.0, -0.4, 0.6))
        if rig.has(f"{side}Arm", f"{side}ForeArm", f"{side}Hand"):
            rig.aim(W, f"{side}Arm", f"{side}ForeArm", _mirror(arm_u, s))
            rig.aim(W, f"{side}ForeArm", f"{side}Hand", _mirror(arm_f, s))
        if rig.has(f"{side}UpLeg", f"{side}Leg", f"{side}Foot"):
            rig.aim(W, f"{side}UpLeg", f"{side}Leg", _mirror(th, s))
            rig.aim(W, f"{side}Leg", f"{side}Foot", _mirror(sh, s))
            if rig.has(f"{side}ToeBase"):
                rig.aim(W, f"{side}Foot", f"{side}ToeBase", _mirror(ft, s))
    hips = rig.j("Hips") if rig.has("Hips") else 0
    if moving:
        # lay the body forward (a little rise and dip with the stroke), then lift the head to look ahead
        rig.rotate(W, hips, _rot_x(72.0 + 6.0 * wave))
        if rig.has("neck", "Head"):
            rig.aim(W, "neck", "Head", (0.0, 0.8, 0.6))
        if rig.has("Head", "head_end"):
            rig.aim(W, "Head", "head_end", (0.0, 0.92, 0.38))
        W[:, 1, 3] += 0.03 * math.sin(math.tau * u - 0.6)
    else:
        rig.rotate(W, hips, _rot_x(10.0))
        if rig.has("Head", "head_end"):
            rig.aim(W, "Head", "head_end", (0.0, 1.0, 0.05))
        W[:, 1, 3] += 0.025 * wave                       # bobbing
    return W


def make_swim_clips(skel: Skeleton) -> dict[str, tuple[Clip, float]]:
    """{'swim': (clip, float_m), 'tread': (clip, float_m)}. float_m is how far below the joints'
    origin (the feet in the bind pose) the water surface sits when floating in that clip."""
    rig = Rig(skel)
    if not rig.has("Hips", "LeftArm", "RightArm", "LeftUpLeg", "RightUpLeg"):
        return {}
    bind = skel.bind_world()
    out = {}
    for name, moving, period in (("swim", True, 1.5), ("tread", False, 1.8)):
        n = int(round(period * BAKE_FPS))
        frames = np.stack([swim_pose(rig, bind, i / n, moving) for i in range(n)]).astype(np.float32)
        if moving:      # water just over the upper back: the head rides above it
            level = float(frames[:, rig.j("Spine"), 1, 3].mean()) + 0.05 if rig.has("Spine") else 1.1
        else:           # treading: water at the collarbones
            level = float(frames[:, rig.j("LeftArm"), 1, 3].mean()) - 0.06
        out[name] = (Clip(name, frames, n / BAKE_FPS, True, 0.0), level)
    return out
