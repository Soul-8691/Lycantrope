"""Lycantrope entry point: window, fixed-step loop, free-fly/walk camera over the terrain.

Controls
--------
Click            capture the mouse (Esc releases it; Esc again quits)
WASD / QE        move / down-up              Shift: fast  ·  Ctrl: slow  ·  wheel: base speed
F1 wireframe · F2 fog · F3 overlay · F4 walk mode · F5 reload shaders
F6 debug view (normal / normals / rock-road-snow) · F12 screenshot

Command line
------------
python -m lycantrope [--cam X,Z,YAW,PITCH[,HEIGHT]] [--screenshot FILE] [--bench N] [--size WxH]
    --cam         start position: X/Z in meters (game coords: z = south), yaw/pitch in degrees,
                  HEIGHT above the ground (default 40)
    --screenshot  render a few frames, save a PNG and quit
    --bench       render N frames, print timing and quit
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time
from datetime import datetime

from pyglm import glm
import moderngl
import numpy as np
import pygame
from PIL import Image

from lycantrope.core.config import Settings
from lycantrope.core.paths import SCREENSHOTS
from lycantrope.core.timing import FixedStep
from lycantrope.render.camera import Camera
from lycantrope.render.environment import Sky, Water, default_environment
from lycantrope.render.props import PropRenderer
from lycantrope.render.shaders import ShaderLibrary
from lycantrope.render.terrain import TerrainRenderer
from lycantrope.ui.overlay import TextOverlay
from lycantrope.world.heightfield import Heightfield
from lycantrope.world.props import load_placements, paint_paths

EYE_HEIGHT = 1.7
WALK_SPEED, RUN_SPEED = 5.0, 11.0


def fit_to_desktop(size: tuple[int, int], margin: float = 0.9) -> tuple[int, int]:
    """Shrink a window size (keeping its aspect ratio) so it fits on the screen.

    With Windows display scaling (e.g. 125%), a 1920×1080 screen is only
    1536×864 to the game, so a 1600×900 window would hang off the edges.
    """
    try:
        dw, dh = pygame.display.get_desktop_sizes()[0]
    except (pygame.error, IndexError):
        return size
    w, h = size
    scale = min(1.0, dw * margin / w, dh * margin / h)
    return max(320, int(w * scale)), max(180, int(h * scale))


class App:
    def __init__(self, settings: Settings, args: argparse.Namespace) -> None:
        self.settings = settings
        self.args = args
        pygame.init()
        for attr, val in ((pygame.GL_CONTEXT_MAJOR_VERSION, 3), (pygame.GL_CONTEXT_MINOR_VERSION, 3),
                          (pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE),
                          (pygame.GL_DEPTH_SIZE, 24), (pygame.GL_DOUBLEBUFFER, 1)):
            pygame.display.gl_set_attribute(attr, val)
        size = (settings.width, settings.height)
        if args.size:
            size = tuple(int(v) for v in args.size.lower().split("x"))
        if not settings.fullscreen:
            size = fit_to_desktop(size)
            os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        flags = pygame.OPENGL | pygame.DOUBLEBUF | (pygame.FULLSCREEN if settings.fullscreen else pygame.RESIZABLE)
        vsync = 0 if (args.bench or not settings.vsync) else 1
        pygame.display.set_mode(size, flags, vsync=vsync)
        pygame.display.set_caption("Lycantrope")
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)

        t0 = time.perf_counter()
        self.shaders = ShaderLibrary(self.ctx)
        self.world = Heightfield()
        placements = load_placements()
        paint_paths(self.world, placements)          # before the terrain uploads the road map
        self.terrain = TerrainRenderer(self.ctx, self.shaders, self.world)
        self.props = PropRenderer(self.ctx, self.shaders, self.world, placements)
        self.sky = Sky(self.ctx, self.shaders)
        self.water = Water(self.ctx, self.shaders, self.world, self.terrain.tex_height)
        self.overlay = TextOverlay(self.ctx, self.shaders)
        self.load_seconds = time.perf_counter() - t0

        self.camera = Camera(fov_deg=settings.fov_deg, far=settings.view_distance_m)
        self.place_camera()
        self.clock = FixedStep(60)
        self.base_speed = 25.0
        self.walk = False
        self.fog = True
        self.show_overlay = True
        self.captured = False
        self.time_s = 0.0
        self.frame_times: list[float] = []
        self.overlay_timer = 0.0

    # ------------------------------------------------------------------ setup
    def place_camera(self) -> None:
        cam = self.camera
        if self.args.cam:
            vals = [float(v) for v in self.args.cam.split(",")]
            x, z, yaw, pitch = vals[:4]
            above = vals[4] if len(vals) > 4 else 40.0
            cam.position = glm.vec3(x, self.world.height_at(x, z) + above, z)
            cam.yaw, cam.pitch = math.radians(yaw), math.radians(pitch)
        else:                                   # above Brackenvale Village, Rowan's home
            v = next((p for p in self.world.landmarks if p.name == "Brackenvale Village"),
                     self.world.waystones[0])
            cam.position = glm.vec3(v.x + 55.0, v.height + 22.0, v.z + 75.0)
            cam.look_at((v.x - 5.0, v.height + 2.0, v.z + 5.0))
        cam.prev_position = glm.vec3(cam.position)

    # ------------------------------------------------------------------ input
    def set_capture(self, on: bool) -> None:
        self.captured = on
        if hasattr(pygame.mouse, "set_relative_mode"):
            pygame.mouse.set_relative_mode(on)
        else:
            pygame.event.set_grab(on)
            pygame.mouse.set_visible(not on)
        pygame.mouse.get_rel()

    def handle_events(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3) and not self.captured:
                self.set_capture(True)
            elif ev.type == pygame.MOUSEMOTION and self.captured:
                s = self.settings.mouse_sensitivity
                dy = ev.rel[1] * s * (1 if self.settings.invert_y else -1)
                self.camera.look(ev.rel[0] * s, dy)
            elif ev.type == pygame.MOUSEWHEEL:
                self.base_speed = min(400.0, max(2.0, self.base_speed * (1.25 ** ev.y)))
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.captured:
                        self.set_capture(False)
                    else:
                        return False
                elif ev.key == pygame.K_F1:
                    self.ctx.wireframe = not self.ctx.wireframe
                elif ev.key == pygame.K_F2:
                    self.fog = not self.fog
                elif ev.key == pygame.K_F3:
                    self.show_overlay = not self.show_overlay
                elif ev.key == pygame.K_F4:
                    self.walk = not self.walk
                elif ev.key == pygame.K_F5:
                    errors = self.shaders.reload()
                    print("shaders reloaded" if not errors else "shader errors:\n" + "\n".join(errors))
                elif ev.key == pygame.K_F6:
                    self.terrain.debug_view = (self.terrain.debug_view + 1) % 3
                elif ev.key == pygame.K_F12:
                    SCREENSHOTS.mkdir(exist_ok=True)
                    self.screenshot(SCREENSHOTS / f"lycantrope_{datetime.now():%Y%m%d_%H%M%S}.png")
        return True

    # ------------------------------------------------------------- simulation
    def update(self, dt: float) -> None:
        cam = self.camera
        cam.prev_position = glm.vec3(cam.position)
        keys = pygame.key.get_pressed()
        fwd = (keys[pygame.K_w] - keys[pygame.K_s])
        side = (keys[pygame.K_d] - keys[pygame.K_a])
        up = (keys[pygame.K_e] - keys[pygame.K_q])
        fast = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        slow = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        if self.walk:
            move = cam.flat_forward() * fwd + cam.right() * side
            if glm.length(move) > 0:
                move = glm.normalize(move) * (RUN_SPEED if fast else WALK_SPEED) * dt
            p = cam.position + move
            p.y = self.world.height_at(p.x, p.z) + EYE_HEIGHT
            cam.position = p
        else:
            move = cam.forward() * fwd + cam.right() * side + glm.vec3(0, 1, 0) * up
            if glm.length(move) > 0:
                speed = self.base_speed * (5.0 if fast else 1.0) * (0.2 if slow else 1.0)
                cam.position = cam.position + glm.normalize(move) * speed * dt
            floor = self.world.height_at(cam.position.x, cam.position.z) + 0.6
            if cam.position.y < floor:
                cam.position.y = floor
        lim = self.world.half - 1.0
        cam.position.x = min(max(cam.position.x, -lim), lim)
        cam.position.z = min(max(cam.position.z, -lim), lim)
        self.time_s += dt

    # ---------------------------------------------------------------- render
    def render(self, alpha: float) -> None:
        w, h = pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
        eye, _view, _proj, viewproj = self.camera.matrices(w / max(h, 1), alpha)
        env = default_environment(self.fog)
        wire = self.ctx.wireframe
        self.ctx.wireframe = False
        self.sky.render(eye, viewproj, env)
        self.ctx.wireframe = wire
        self.terrain.render(eye, viewproj, env, self.settings.lod_distances_m)
        self.props.render(eye, viewproj, env)
        self.ctx.wireframe = False
        self.water.render(eye, viewproj, env, self.time_s)
        if self.show_overlay:
            self.overlay.render(w, h)
        self.ctx.wireframe = wire

    def overlay_lines(self) -> list[str]:
        ft = self.frame_times[-60:] or [0.0]
        ms = 1000 * sum(ft) / len(ft)
        p = self.camera.position
        ground = self.world.height_at(p.x, p.z)
        st = self.terrain.stats
        mode = "WALK" if self.walk else f"FLY {self.base_speed:.0f} m/s"
        return [
            f"LYCANTROPE  terrain preview   {1000 / max(ms, 1e-3):5.0f} fps  {ms:5.1f} ms",
            f"pos  x {p.x:7.1f}  z {p.z:7.1f}  y {p.y:6.1f}   ground {ground:6.1f} m   (north = -z)",
            f"biome {self.world.biome_at(p.x, p.z):<18} {mode}",
            f"chunks LOD0-4 {st.per_lod}  of {st.chunks_total}   {st.triangles / 1000:.0f}k tris",
            f"props {self.props.drawn} of {self.props.count} drawn   {self.props.triangles / 1000:.0f}k tris",
            "click: mouse look  Esc: release  WASD QE  Shift/Ctrl  wheel: speed",
            "F1 wire  F2 fog  F3 overlay  F4 walk  F5 shaders  F6 debug  F12 shot",
        ]

    def screenshot(self, path) -> None:
        w, h = pygame.display.get_window_size()
        data = self.ctx.screen.read(viewport=(0, 0, w, h), components=3)
        Image.frombytes("RGB", (w, h), data).transpose(Image.FLIP_TOP_BOTTOM).save(path)
        print(f"screenshot saved: {path}")

    # ------------------------------------------------------------------ loop
    def run(self) -> int:
        print(f"world loaded in {self.load_seconds:.1f}s  ({self.world.size}² heightmap, "
              f"{self.terrain.stats.chunks_total} chunks)")
        frames = 0
        target = self.args.bench or (5 if self.args.screenshot else 0)
        last = time.perf_counter()
        running = True
        while running:
            now = time.perf_counter()
            dt = now - last
            last = now
            running = self.handle_events()
            for _ in range(self.clock.advance(dt)):
                self.update(self.clock.dt)
            self.render(self.clock.alpha)
            pygame.display.flip()
            frames += 1
            if frames > 2:
                self.frame_times.append(dt)
                del self.frame_times[:-600]
            self.overlay_timer -= dt
            if self.overlay_timer <= 0:
                self.overlay.set_lines(self.overlay_lines())
                self.overlay_timer = 0.25
            if target and frames >= target:
                if self.args.screenshot:
                    self.overlay.set_lines(self.overlay_lines())
                    self.render(1.0)
                    self.screenshot(self.args.screenshot)
                if self.args.bench:
                    ft = np.array(self.frame_times) * 1000
                    print(f"bench: {len(ft)} frames  mean {ft.mean():.2f} ms  p95 {np.percentile(ft, 95):.2f} ms  "
                          f"tris {self.terrain.stats.triangles}  LOD {self.terrain.stats.per_lod}")
                running = False
        pygame.quit()
        return 0


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lycantrope", description="Lycantrope terrain preview")
    ap.add_argument("--cam", help="X,Z,YAW,PITCH[,HEIGHT_ABOVE_GROUND]")
    ap.add_argument("--screenshot", help="save a PNG after a few frames and quit")
    ap.add_argument("--bench", type=int, default=0, help="render N frames, print timing, quit")
    ap.add_argument("--size", help="window size WxH")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    return App(Settings.load(), args).run()


if __name__ == "__main__":
    sys.exit(run())
