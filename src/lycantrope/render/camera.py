"""Perspective camera with yaw/pitch, interpolation and frustum planes."""
from __future__ import annotations

import math

from pyglm import glm
import numpy as np


class Camera:
    def __init__(self, position=(0.0, 50.0, 0.0), yaw: float = 0.0, pitch: float = 0.0,
                 fov_deg: float = 70.0, near: float = 0.25, far: float = 3000.0) -> None:
        self.position = glm.vec3(*position)
        self.prev_position = glm.vec3(self.position)
        self.yaw = yaw            # radians; 0 looks north (-z), +pi/2 looks east (+x)
        self.pitch = pitch        # radians; positive looks up
        self.fov_deg = fov_deg
        self.near = near
        self.far = far

    # -- orientation -------------------------------------------------------- #
    def forward(self) -> glm.vec3:
        cp = math.cos(self.pitch)
        return glm.vec3(math.sin(self.yaw) * cp, math.sin(self.pitch), -math.cos(self.yaw) * cp)

    def flat_forward(self) -> glm.vec3:
        return glm.vec3(math.sin(self.yaw), 0.0, -math.cos(self.yaw))

    def right(self) -> glm.vec3:
        return glm.vec3(math.cos(self.yaw), 0.0, math.sin(self.yaw))

    def look(self, dx: float, dy: float) -> None:
        self.yaw = (self.yaw + dx) % math.tau
        self.pitch = max(-1.55, min(1.55, self.pitch + dy))

    def look_at(self, target) -> None:
        d = glm.vec3(*target) - self.position
        self.yaw = math.atan2(d.x, -d.z)
        self.pitch = math.atan2(d.y, math.hypot(d.x, d.z))

    # -- matrices ------------------------------------------------------------ #
    def interpolated(self, alpha: float) -> glm.vec3:
        return glm.mix(self.prev_position, self.position, alpha)

    def matrices(self, aspect: float, alpha: float = 1.0):
        eye = self.interpolated(alpha)
        view = glm.lookAt(eye, eye + self.forward(), glm.vec3(0, 1, 0))
        proj = glm.perspective(glm.radians(self.fov_deg), aspect, self.near, self.far)
        return eye, view, proj, proj * view


def frustum_planes(viewproj: glm.mat4) -> np.ndarray:
    """Six planes (a, b, c, d) with normals pointing inside, from a view-projection matrix."""
    m = np.array(viewproj.to_list(), dtype=np.float64).T     # row-major
    planes = np.array([m[3] + m[0], m[3] - m[0], m[3] + m[1], m[3] - m[1], m[3] + m[2], m[3] - m[2]])
    planes /= np.linalg.norm(planes[:, :3], axis=1, keepdims=True)
    return planes


def boxes_in_frustum(planes: np.ndarray, bmin: np.ndarray, bmax: np.ndarray) -> np.ndarray:
    """Boolean mask of axis-aligned boxes (N,3) that touch the frustum."""
    visible = np.ones(len(bmin), dtype=bool)
    for a, b, c, d in planes:
        px = np.where(a >= 0, bmax[:, 0], bmin[:, 0])
        py = np.where(b >= 0, bmax[:, 1], bmin[:, 1])
        pz = np.where(c >= 0, bmax[:, 2], bmin[:, 2])
        visible &= (a * px + b * py + c * pz + d) >= 0
    return visible
