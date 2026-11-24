"""Fixed-step simulation clock (TEC-04): the game updates at a steady 60 Hz,
rendering runs as fast as the display allows and interpolates between steps."""
from __future__ import annotations


class FixedStep:
    def __init__(self, hz: float = 60.0, max_steps: int = 5) -> None:
        self.dt = 1.0 / hz
        self.max_steps = max_steps
        self.accumulator = 0.0
        self.ticks = 0

    def advance(self, frame_seconds: float) -> int:
        """Add real time; returns how many simulation steps to run now."""
        self.accumulator += min(frame_seconds, self.dt * self.max_steps)
        steps = 0
        while self.accumulator >= self.dt and steps < self.max_steps:
            self.accumulator -= self.dt
            steps += 1
        self.ticks += steps
        return steps

    @property
    def alpha(self) -> float:
        """How far (0..1) the renderer is between the last two simulation steps."""
        return self.accumulator / self.dt
