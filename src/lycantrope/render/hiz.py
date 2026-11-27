"""Hierarchical-Z occlusion buffer (OpenGL 4.3 compute shaders).

After the main depth pass, copies the low-res depth texture into a max-Z mip chain.
PropRenderer tests bounding spheres against last frame's chain before uploading instance
data — terrain and buildings thereby occlude distant props with zero extra draw calls.

The 1-frame lag is intentional and invisible at normal play speeds: the previous frame's
Hi-Z is used to cull the current frame's instances, and the new Hi-Z is built for the
next frame.  On frame 0, hiz_data is None and all instances pass through.
"""
from __future__ import annotations

import numpy as np
import moderngl
from pyglm import glm

# ---------------------------------------------------------------------- shaders

_COPY_VERT = """\
#version 430 core
in vec2 in_pos;
out vec2 v_uv;
void main() { v_uv = in_pos * 0.5 + 0.5; gl_Position = vec4(in_pos, 0.0, 1.0); }
"""

# Copies a depth texture into an R32F colour texture for compute access.
_COPY_FRAG = """\
#version 430 core
uniform sampler2D u_depth;
in vec2 v_uv;
out float out_depth;
void main() { out_depth = texture(u_depth, v_uv).r; }
"""

# Max-Z downsample: each output pixel = max of its 2×2 source block.
# Conservative: a region is only "clear" if ALL of it is in front of the sphere.
_DOWN_COMP = """\
#version 430 core
layout(local_size_x = 8, local_size_y = 8) in;
layout(r32f, binding = 0) readonly  uniform image2D u_src;
layout(r32f, binding = 1) writeonly uniform image2D u_dst;
void main() {
    ivec2 d  = ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz = imageSize(u_src) - 1;
    ivec2 s  = d * 2;
    float d0 = imageLoad(u_src, clamp(s,               ivec2(0), sz)).r;
    float d1 = imageLoad(u_src, clamp(s + ivec2(1, 0), ivec2(0), sz)).r;
    float d2 = imageLoad(u_src, clamp(s + ivec2(0, 1), ivec2(0), sz)).r;
    float d3 = imageLoad(u_src, clamp(s + ivec2(1, 1), ivec2(0), sz)).r;
    imageStore(u_dst, d, vec4(max(max(d0, d1), max(d2, d3))));
}
"""

_MIN_PIX = 16   # stop building mips when this small
_READ_MIP = 2   # download this mip level to CPU; mip 0 = full low-res render size


class HiZBuffer:
    """Max-Z hierarchical depth buffer for per-instance occlusion culling."""

    def __init__(self, ctx: moderngl.Context) -> None:
        self.ctx = ctx
        copy_prog = ctx.program(vertex_shader=_COPY_VERT, fragment_shader=_COPY_FRAG)
        copy_prog["u_depth"] = 0
        quad = np.array([(-1, -1), (1, -1), (1, 1), (-1, -1), (1, 1), (-1, 1)], np.float32)
        self._copy_vao = ctx.vertex_array(copy_prog, [(ctx.buffer(quad.tobytes()), "2f", "in_pos")])
        self._down = ctx.compute_shader(_DOWN_COMP)
        self._mips: list[tuple[moderngl.Texture, moderngl.Framebuffer]] = []
        self._pw = self._ph = 0
        # Previous-frame Hi-Z downloaded to CPU
        self._hiz: np.ndarray | None = None
        self._hiz_w = self._hiz_h = 0

    # ------------------------------------------------------------------ resize
    def _rebuild(self, pw: int, ph: int) -> None:
        for _, fb in self._mips:
            fb.release()
        for tex, _ in self._mips:
            tex.release()
        self._mips.clear()
        w, h = pw, ph
        while w >= _MIN_PIX and h >= _MIN_PIX:
            tex = self.ctx.texture((w, h), 1, dtype="f4")
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self._mips.append((tex, self.ctx.framebuffer([tex])))
            w, h = max(1, w // 2), max(1, h // 2)
        self._pw, self._ph = pw, ph

    # -------------------------------------------------------------------build
    def build(self, depth_tex: moderngl.Texture, pw: int, ph: int) -> None:
        """Build the Hi-Z chain from this frame's depth texture.

        Call AFTER all 3-D rendering is done.  Results are available on the
        NEXT frame via cull() — intentional 1-frame lag.
        """
        if pw != self._pw or ph != self._ph:
            self._rebuild(pw, ph)
        if not self._mips:
            return

        # Level 0: copy depth texture → R32F via a fullscreen quad
        tex0, fb0 = self._mips[0]
        fb0.use()
        self.ctx.viewport = (0, 0, *fb0.size)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.depth_write = False
        depth_tex.use(0)
        self._copy_vao.render(moderngl.TRIANGLES)
        self.ctx.depth_write = True
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Levels 1+: max-Z downsample via compute shader
        for i in range(1, len(self._mips)):
            src, _  = self._mips[i - 1]
            dst, _  = self._mips[i]
            dw, dh  = dst.size
            src.bind_to_image(0, read=True,  write=False)
            dst.bind_to_image(1, read=False, write=True)
            self._down.run(max(1, (dw + 7) // 8), max(1, (dh + 7) // 8))

        # Download the chosen small mip to CPU
        idx = min(_READ_MIP, len(self._mips) - 1)
        read_tex, _ = self._mips[idx]
        rw, rh = read_tex.size
        self._hiz   = np.frombuffer(read_tex.read(), dtype=np.float32).reshape(rh, rw)
        self._hiz_w = rw
        self._hiz_h = rh

    # -------------------------------------------------------------------- cull
    def cull(self, centers: np.ndarray, radii: np.ndarray,
             viewproj: glm.mat4, eye: np.ndarray) -> np.ndarray:
        """Return bool mask: True = may be visible (uses PREVIOUS frame's Hi-Z).

        Parameters
        ----------
        centers  : (N, 3) world-space bounding-sphere centres
        radii    : (N,)   bounding-sphere radii in world units
        viewproj : camera view-projection matrix (glm.mat4)
        eye      : (3,) camera world position
        """
        if self._hiz is None or len(centers) == 0:
            return np.ones(len(centers), dtype=bool)

        hiz = self._hiz
        hiz_w, hiz_h = self._hiz_w, self._hiz_h

        # --- find the near-face of each bounding sphere (closest point to camera)
        to_cam = (eye - centers).astype(np.float32)      # (N,3)
        dist   = np.linalg.norm(to_cam, axis=1)
        dist_s = dist.clip(1e-3)
        near_pts = centers + (to_cam / dist_s[:, None]) * radii[:, None]  # (N,3)

        # --- project through viewproj
        # glm.mat4.to_list() is column-major; reshape to (4,4) gives the matrix
        # such that (row_vec @ M) == (M_col_vec * col_vec)
        vp   = np.array(viewproj.to_list(), dtype=np.float32).reshape(4, 4)
        ones = np.ones((len(near_pts), 1), dtype=np.float32)
        pts  = np.concatenate([near_pts.astype(np.float32), ones], axis=1)  # (N,4)
        clip = pts @ vp                                   # (N,4) clip space

        w      = clip[:, 3]
        behind = w <= 0.0
        w_s    = np.where(behind, 1e-6, w)
        ndc    = clip[:, :3] / w_s[:, None]              # (N,3) NDC -1..1

        uv_x    = ndc[:, 0] * 0.5 + 0.5                 # 0=left   1=right
        uv_y    = ndc[:, 1] * 0.5 + 0.5                 # 0=bottom 1=top
        depth_z = ndc[:, 2] * 0.5 + 0.5                 # 0=near   1=far

        # Spheres partly or fully off-screen are always kept
        off = (uv_x < -0.05) | (uv_x > 1.05) | (uv_y < -0.05) | (uv_y > 1.05)

        # Hi-Z pixel lookup (OpenGL Y-up → flip for numpy row order)
        px = np.clip((uv_x * hiz_w).astype(np.int32), 0, hiz_w - 1)
        py = np.clip(((1.0 - uv_y) * hiz_h).astype(np.int32), 0, hiz_h - 1)
        hiz_d = hiz[py, px]

        # Visible if the sphere's near face is not behind everything already drawn.
        # +0.002 epsilon for depth precision / near-plane edge cases.
        return (depth_z <= hiz_d + 0.002) | behind | off
