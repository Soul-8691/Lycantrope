"""Lock-on targeting (CMB-02, UIX-04).

Tab (or the middle mouse button) locks onto the enemy closest to where the camera is looking, within
RANGE_M of Rowan; pressing it again lets go. While locked, a quick sideways flick of the mouse switches
to the next enemy on that side. The lock drops by itself when the target dies, stops being hostile or
gets further than KEEP_M away.

Only the choosing and keeping of a target lives here (plain Python, tested without a window); the
camera, Rowan's facing and the reticle read `target`.
"""
from __future__ import annotations

import math

RANGE_M = 22.0           # how far away a new target can be
KEEP_M = 30.0            # a held lock lets go past this
CONE_DEG = 65.0          # a new target must be within this angle of the camera's view
FLICK_PX = 110.0         # sideways mouse travel that switches target
FLICK_WINDOW_S = 0.18    # ...within this long
SWITCH_COOLDOWN_S = 0.35


def hostile(c) -> bool:
    """Can this character be locked onto? Enemies that are alive (aggro_m > 0)."""
    t = getattr(c, "t", None)
    ai = getattr(t, "ai", None) if t is not None else None
    return ai is not None and ai.aggro_m > 0 and c.actor.state != "dead" and getattr(c, "brain", None) is not None


def _flat_angle(fx: float, fz: float, dx: float, dz: float) -> float:
    """Signed angle (radians) from direction f to direction d on the ground; positive = to the right."""
    return math.atan2(fx * dz - fz * dx, fx * dx + fz * dz)


class LockOn:
    def __init__(self) -> None:
        self.target = None
        self._flick = 0.0
        self._flick_t = 0.0
        self._cooldown = 0.0

    @property
    def locked(self) -> bool:
        return self.target is not None

    # -------------------------------------------------------------- choosing
    def candidates(self, chars, rowan, range_m: float = RANGE_M):
        out = []
        for c in chars:
            if c.actor is rowan or not hostile(c):
                continue
            d = math.hypot(c.actor.x - rowan.x, c.actor.z - rowan.z)
            if d <= range_m:
                out.append((c, d))
        return out

    def pick(self, chars, rowan, cam_x: float, cam_z: float, fwd_x: float, fwd_z: float):
        """The enemy nearest the middle of the view (angle first, then distance)."""
        best, score = None, 1e9
        for c, d in self.candidates(chars, rowan):
            ang = abs(_flat_angle(fwd_x, fwd_z, c.actor.x - cam_x, c.actor.z - cam_z))
            if math.degrees(ang) > CONE_DEG:
                continue
            s = ang + 0.5 * d / RANGE_M
            if s < score:
                best, score = c, s
        return best

    def toggle(self, chars, rowan, cam_x, cam_z, fwd_x, fwd_z) -> None:
        self.target = None if self.target is not None else self.pick(chars, rowan, cam_x, cam_z, fwd_x, fwd_z)

    def switch(self, side: int, chars, rowan, cam_x: float, cam_z: float) -> bool:
        """Move the lock to the nearest enemy to the right (side > 0) or left of the current one."""
        if self.target is None:
            return False
        t = self.target.actor
        tx, tz = t.x - cam_x, t.z - cam_z
        best, best_ang = None, 1e9
        for c, _d in self.candidates(chars, rowan):
            if c is self.target:
                continue
            ang = _flat_angle(tx, tz, c.actor.x - cam_x, c.actor.z - cam_z)
            if ang * side > 0 and abs(ang) < best_ang:
                best, best_ang = c, abs(ang)
        if best is not None:
            self.target = best
            return True
        return False

    # -------------------------------------------------------------- keeping
    def update(self, dt: float, rowan) -> None:
        self._cooldown = max(0.0, self._cooldown - dt)
        self._flick_t += dt
        if self._flick_t > FLICK_WINDOW_S:
            self._flick, self._flick_t = 0.0, 0.0
        c = self.target
        if c is None:
            return
        if not hostile(c) or math.hypot(c.actor.x - rowan.x, c.actor.z - rowan.z) > KEEP_M:
            self.target = None

    def mouse(self, dx: float, chars, rowan, cam_x: float, cam_z: float) -> None:
        """Sideways mouse travel while locked: a quick flick switches target."""
        if self.target is None or self._cooldown > 0:
            return
        self._flick += dx
        if abs(self._flick) >= FLICK_PX:
            if self.switch(1 if self._flick > 0 else -1, chars, rowan, cam_x, cam_z):
                self._cooldown = SWITCH_COOLDOWN_S
            self._flick, self._flick_t = 0.0, 0.0

    def yaw_to_target(self, rowan) -> float | None:
        """Camera yaw that looks from Rowan at the target (camera forward = (sin yaw, -cos yaw))."""
        if self.target is None:
            return None
        t = self.target.actor
        return math.atan2(t.x - rowan.x, -(t.z - rowan.z))
