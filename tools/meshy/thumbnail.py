r"""Render a grey, shaded thumbnail PNG of a GLB (like Meshy's preview thumbnails).

    .venv\Scripts\python.exe tools/meshy/thumbnail.py path/to/model.glb [more.glb ...] [--size 512]

Writes <name>.png next to each GLB. Uses an offscreen moderngl context, so no window opens.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import moderngl
import numpy as np
import trimesh
from PIL import Image
from pyglm import glm

VERT = """
#version 330
uniform mat4 u_mvp;
in vec3 in_pos;
in vec3 in_nrm;
out vec3 v_nrm;
void main() { v_nrm = in_nrm; gl_Position = u_mvp * vec4(in_pos, 1.0); }
"""
FRAG = """
#version 330
uniform vec3 u_eye_dir;
in vec3 v_nrm;
out vec4 f_color;
void main() {
    vec3 n = normalize(v_nrm);
    if (dot(n, u_eye_dir) < 0.0) n = -n;                  // Meshy meshes aren't always closed
    vec3 key = normalize(vec3(0.5, 0.8, 0.6));
    float d = max(dot(n, key), 0.0) * 0.65 + max(dot(n, u_eye_dir), 0.0) * 0.25;
    float sky = 0.5 + 0.5 * n.y;
    vec3 c = vec3(0.72) * (0.08 + d + 0.12 * sky);
    f_color = vec4(pow(c, vec3(1.0 / 1.6)), 1.0);
}
"""

_ctx = None


def _context() -> moderngl.Context:
    global _ctx
    if _ctx is None:
        _ctx = moderngl.create_standalone_context()
    return _ctx


def render(glb: Path, out: Path | None = None, size: int = 512) -> Path:
    mesh = trimesh.load(glb, force="mesh")
    lo, hi = mesh.bounds
    center = (lo + hi) / 2
    radius = float(np.linalg.norm(hi - lo)) / 2 or 1.0

    tris = mesh.vertices[mesh.faces].reshape(-1, 3)          # flat shading: one normal per face
    nrm = np.repeat(mesh.face_normals, 3, axis=0)
    data = np.hstack([tris - center, nrm]).astype("f4")

    ctx = _context()
    prog = ctx.program(vertex_shader=VERT, fragment_shader=FRAG)
    vbo = ctx.buffer(data.tobytes())
    vao = ctx.vertex_array(prog, [(vbo, "3f 3f", "in_pos", "in_nrm")])

    eye_dir = glm.normalize(glm.vec3(0.9, 0.55, 1.2))         # three-quarter view from the front right
    fov = 30.0
    dist = radius / np.sin(np.radians(fov / 2)) * 1.05
    view = glm.lookAt(eye_dir * dist, glm.vec3(0), glm.vec3(0, 1, 0))
    proj = glm.perspective(glm.radians(fov), 1.0, dist * 0.05, dist * 4)
    prog["u_mvp"].write(proj * view)
    prog["u_eye_dir"].value = tuple(eye_dir)

    ss = 2                                                  # render at 2x and downsample for smooth edges
    fbo = ctx.framebuffer(ctx.renderbuffer((size * ss, size * ss)),
                          ctx.depth_renderbuffer((size * ss, size * ss)))
    fbo.use()
    ctx.enable(moderngl.DEPTH_TEST)
    fbo.clear(1.0, 1.0, 1.0, 1.0)
    vao.render()
    img = Image.frombytes("RGB", (size * ss, size * ss), fbo.read(components=3))
    img = img.transpose(Image.FLIP_TOP_BOTTOM).resize((size, size), Image.LANCZOS)
    for r in (vao, vbo, prog, fbo):
        r.release()

    out = out or glb.with_suffix(".png")
    img.save(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Render GLB thumbnails")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--size", type=int, default=512)
    args = ap.parse_args()
    for f in args.files:
        print(f"  {render(f, size=args.size)}")


if __name__ == "__main__":
    main()
