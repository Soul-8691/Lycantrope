"""Loads GLSL programs from render/shaders, with #include and hot reload (TEC-02)."""
from __future__ import annotations

import re
from pathlib import Path

import moderngl

from lycantrope.core.paths import SHADERS

_INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"\s*$', re.M)


def set_uniform(prog: moderngl.Program, name: str, value) -> None:
    """Set a uniform if the compiler kept it (unused uniforms are optimized away)."""
    try:
        member = prog[name]
    except KeyError:
        return
    if "glm" in type(value).__module__:                # PyGLM vectors and matrices
        member.write(value.to_bytes())
    else:
        member.value = value


class ShaderLibrary:
    def __init__(self, ctx: moderngl.Context, folder: Path = SHADERS) -> None:
        self.ctx = ctx
        self.folder = folder
        self.programs: dict[str, moderngl.Program] = {}
        self.version = 0                               # bumps on every successful reload

    def _source(self, filename: str, seen: tuple[str, ...] = ()) -> str:
        if filename in seen:
            raise RuntimeError(f"circular #include of {filename}")
        text = (self.folder / filename).read_text(encoding="utf-8")
        return _INCLUDE.sub(lambda m: self._source(m.group(1), seen + (filename,)), text)

    def _build(self, name: str) -> moderngl.Program:
        return self.ctx.program(vertex_shader=self._source(f"{name}.vert"),
                                fragment_shader=self._source(f"{name}.frag"))

    def get(self, name: str) -> moderngl.Program:
        if name not in self.programs:
            self.programs[name] = self._build(name)
        return self.programs[name]

    def reload(self) -> list[str]:
        """Recompile every program. Broken shaders keep the old version; returns errors."""
        errors = []
        for name in list(self.programs):
            try:
                self.programs[name] = self._build(name)
            except Exception as exc:                   # moderngl.Error, OSError, ...
                errors.append(f"{name}: {exc}")
        self.version += 1
        return errors
