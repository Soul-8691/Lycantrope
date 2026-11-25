"""Lycantrope entry point: window, fixed-step loop, Rowan in third person (or a free-fly camera).

Controls (play mode)
--------------------
Click            capture the mouse (Esc releases it; Esc again quits)
WASD             move (camera-relative)     Shift: sprint  ·  Ctrl: walk  ·  wheel: camera distance
Left click       light attack (click again during a swing to chain up to three)
Right mouse      hold to block              R: heavy attack  ·  Q: cast (off hand)
H / K            debug: hit reaction / die and get back up
F4 free-fly camera · F7 helmet on/off · F8 grass on/off · F9 music on/off · F10 sound effects on/off

Free-fly mode: WASD / QE move, Shift fast, Ctrl slow, wheel base speed.
Always: T turbo (4x speed, walking and flying) · F1 wireframe · F2 fog · F3 debug overlay ·
        F4 fly / back to Rowan · F5 reload shaders · F6 terrain debug view · F12 screenshot

Command line
------------
python -m lycantrope [--cam X,Z,YAW,PITCH[,HEIGHT]] [--screenshot FILE] [--bench N] [--size WxH]
    --cam         start in free-fly mode at X/Z (meters, z = south), yaw/pitch in degrees,
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

from lycantrope.audio.music import start_music
from lycantrope.audio.sfx import start_sfx
from lycantrope.core.config import Settings
from lycantrope.core.paths import SCREENSHOTS
from lycantrope.core.timing import FixedStep
from lycantrope.render.camera import Camera
from lycantrope.render.characters import CharacterSystem
from lycantrope.render.environment import Sky, Water, default_environment
from lycantrope.render.grass import Grass
from lycantrope.render.props import PropRenderer
from lycantrope.render.shaders import ShaderLibrary
from lycantrope.render.terrain import TerrainRenderer
from lycantrope.ui.overlay import TextOverlay
from lycantrope.world.actors import TURBO, RowanInput
from lycantrope.world.heightfield import Heightfield
from lycantrope.world.props import load_placements, paint_ground, paint_paths

CAM_PIVOT_HEIGHT = 1.55


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
        pygame.mixer.pre_init(44100, -16, 2, 2048)       # a roomy buffer: music without crackles
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
        paint_ground(self.world, placements)         # loose hay and other painted patches
        self.terrain = TerrainRenderer(self.ctx, self.shaders, self.world)
        self.props = PropRenderer(self.ctx, self.shaders, self.world, placements)
        self.grass = Grass(self.ctx, self.shaders, self.world, self.terrain)
        self.chars = CharacterSystem(self.ctx, self.shaders, self.world)
        self.chars.set_colliders(self.props.colliders)   # houses, trunks, fences and rocks are solid
        self.sky = Sky(self.ctx, self.shaders)
        self.water = Water(self.ctx, self.shaders, self.world, self.terrain.tex_height, self.terrain.tex_water)
        self.overlay = TextOverlay(self.ctx, self.shaders)
        self.load_seconds = time.perf_counter() - t0
        # no music for benchmarks and screenshots (timing and silence)
        quiet = args.bench or args.screenshot or settings.music_volume <= 0
        self.music = None if quiet else start_music(settings.music_volume)
        no_sfx = args.bench or args.screenshot or settings.sfx_volume <= 0
        self.sfx = None if no_sfx else start_sfx(settings.sfx_volume)

        self.camera = Camera(fov_deg=settings.fov_deg, far=settings.view_distance_m)
        self.play = self.chars.rowan is not None and not args.cam
        self.orbit_dist = 4.2
        self.orbit_pitch = -0.22
        self.orbit_yaw = math.pi - self.chars.rowan.a.heading if self.chars.rowan else 0.0
        self.place_camera()
        self.clock = FixedStep(60)
        self.base_speed = 25.0
        self.fog = True
        self.turbo = False
        self.show_overlay = True
        self.captured = False
        self.time_s = 0.0
        self.frame_times: list[float] = []
        self.overlay_timer = 0.0
        self.pressed: set[str] = set()                # one-shot actions since the last tick
        self.ticks = 0
        if args.orbit and self.chars.rowan:
            y, p, d = (float(v) for v in args.orbit.split(","))
            self.orbit_yaw = math.pi - self.chars.rowan.a.heading + math.radians(y)
            self.orbit_pitch, self.orbit_dist = math.radians(p), d
        if args.act and args.act.startswith("teleport:") and self.chars.rowan:
            x, z = (float(v) for v in args.act.split(":")[1].split(","))
            a = self.chars.rowan.a
            a.x, a.z = x, z
            a.y = self.world.height_at(x, z)
            a.save_prev()

    # ------------------------------------------------------------------ setup
    def place_camera(self) -> None:
        cam = self.camera
        if self.args.cam:
            vals = [float(v) for v in self.args.cam.split(",")]
            x, z, yaw, pitch = vals[:4]
            above = vals[4] if len(vals) > 4 else 40.0
            cam.position = glm.vec3(x, self.world.height_at(x, z) + above, z)
            cam.yaw, cam.pitch = math.radians(yaw), math.radians(pitch)
        elif self.chars.rowan is not None:
            self.follow_camera(1.0)
        else:                                   # above Brackenvale Village, Rowan's home
            v = next((p for p in self.world.landmarks if p.name == "Brackenvale Village"),
                     self.world.waystones[0])
            cam.position = glm.vec3(v.x + 55.0, v.height + 22.0, v.z + 75.0)
            cam.look_at((v.x - 5.0, v.height + 2.0, v.z + 5.0))
        cam.prev_position = glm.vec3(cam.position)

    def follow_camera(self, alpha: float) -> None:
        """Third-person orbit around Rowan, kept above the ground."""
        a = self.chars.rowan.a
        cam = self.camera
        pivot = glm.vec3(a.px + (a.x - a.px) * alpha, a.py + (a.y - a.py) * alpha + CAM_PIVOT_HEIGHT,
                         a.pz + (a.z - a.pz) * alpha)
        cam.yaw, cam.pitch = self.orbit_yaw, self.orbit_pitch
        pos = pivot - cam.forward() * self.orbit_dist
        # pull the camera in rather than let it end up inside a house or a trunk
        t = self.props.colliders.clear_distance((pivot.x, pivot.y, pivot.z), (pos.x, pos.y, pos.z))
        if t < 1.0:
            pos = pivot - cam.forward() * max(0.6, self.orbit_dist * t)
        floor = max(self.world.height_at(pos.x, pos.z) + 0.35, self.world.water_at(pos.x, pos.z) + 0.3)
        if pos.y < floor:                         # stay above the ground and the water
            pos.y = floor
            d = pivot - pos
            cam.yaw = math.atan2(d.x, -d.z)
            cam.pitch = math.atan2(d.y, math.hypot(d.x, d.z))
        cam.position = pos
        cam.prev_position = glm.vec3(pos)

    # ------------------------------------------------------------------ input
    def set_capture(self, on: bool) -> None:
        self.captured = on
        if hasattr(pygame.mouse, "set_relative_mode"):
            pygame.mouse.set_relative_mode(on)
        else:
            pygame.event.set_grab(on)
            pygame.mouse.set_visible(not on)
        pygame.mouse.get_rel()

    def mouse_look(self, rel) -> None:
        s = self.settings.mouse_sensitivity
        dy = rel[1] * s * (1 if self.settings.invert_y else -1)
        if self.play:
            self.orbit_yaw = (self.orbit_yaw + rel[0] * s) % math.tau
            self.orbit_pitch = max(-1.2, min(0.6, self.orbit_pitch + dy))
        else:
            self.camera.look(rel[0] * s, dy)

    def latest_mouse(self) -> None:
        """Mouse movement that arrived during the world update, so the frame shows it now."""
        for ev in pygame.event.get(pygame.MOUSEMOTION):
            if self.captured:
                self.mouse_look(ev.rel)

    def handle_events(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3) and not self.captured:
                self.set_capture(True)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.play:
                self.pressed.add("light")
            elif ev.type == pygame.MOUSEMOTION and self.captured:
                self.mouse_look(ev.rel)
            elif ev.type == pygame.MOUSEWHEEL:
                if self.play:
                    self.orbit_dist = min(12.0, max(1.8, self.orbit_dist * (0.9 ** ev.y)))
                else:
                    self.base_speed = min(400.0, max(2.0, self.base_speed * (1.25 ** ev.y)))
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    if self.captured:
                        self.set_capture(False)
                    else:
                        return False
                elif k == pygame.K_t:
                    self.turbo = not self.turbo
                    self.overlay_timer = 0.0                 # show the change straight away
                elif k == pygame.K_F1:
                    self.ctx.wireframe = not self.ctx.wireframe
                elif k == pygame.K_F2:
                    self.fog = not self.fog
                elif k == pygame.K_F3:
                    self.show_overlay = not self.show_overlay
                elif k == pygame.K_F4 and self.chars.rowan is not None:
                    self.play = not self.play
                    if not self.play:
                        self.camera.prev_position = glm.vec3(self.camera.position)
                elif k == pygame.K_F5:
                    errors = self.shaders.reload()
                    print("shaders reloaded" if not errors else "shader errors:\n" + "\n".join(errors))
                elif k == pygame.K_F6:
                    self.terrain.debug_view = (self.terrain.debug_view + 1) % 3
                elif k == pygame.K_F7:
                    self.chars.helmet = not self.chars.helmet
                elif k == pygame.K_F8:
                    self.grass.enabled = not self.grass.enabled
                elif k == pygame.K_F9 and self.music is not None:
                    self.music.enabled = not self.music.enabled
                elif k == pygame.K_F10 and self.sfx is not None:
                    self.sfx.enabled = not self.sfx.enabled
                elif k == pygame.K_F12:
                    SCREENSHOTS.mkdir(exist_ok=True)
                    self.screenshot(SCREENSHOTS / f"lycantrope_{datetime.now():%Y%m%d_%H%M%S}.png")
                elif self.play:
                    name = {pygame.K_r: "heavy", pygame.K_q: "cast", pygame.K_h: "hit", pygame.K_k: "die"}.get(k)
                    if name:
                        self.pressed.add(name)
        return True

    # ------------------------------------------------------------- simulation
    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        inp = RowanInput()
        if self.play:
            inp.move_x = keys[pygame.K_d] - keys[pygame.K_a]
            inp.move_y = keys[pygame.K_w] - keys[pygame.K_s]
            inp.sprint = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
            inp.walk = bool(keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])
            inp.turbo = self.turbo
            inp.block = bool(self.captured and pygame.mouse.get_pressed()[2])
            inp.light, inp.heavy = "light" in self.pressed, "heavy" in self.pressed
            inp.cast, inp.hit, inp.die = "cast" in self.pressed, "hit" in self.pressed, "die" in self.pressed
            self.pressed.clear()
            act = self.args.act or ""
            if act.startswith("teleport:"):              # teleport:X,Z[:action]
                parts = act.split(":")
                act = parts[2] if len(parts) > 2 else ""
            if act:                                      # --act: scripted input for screenshots
                inp.move_y = max(inp.move_y, 1.0 if act in ("run", "sprint", "walk") else 0.0)
                inp.sprint |= act == "sprint"
                inp.walk |= act == "walk"
                inp.block |= act == "block"
                first = self.ticks == 1
                inp.light |= (act == "light" and first) or (act == "combo" and self.ticks % 20 == 1)
                inp.heavy |= act == "heavy" and first
                inp.cast |= act == "cast" and first
                inp.hit |= act == "hit" and first
                inp.die |= act == "die" and first
            self.ticks += 1
        else:
            self.fly(dt, keys)
        self.chars.update(inp, self.orbit_yaw, dt)
        if self.music is not None:
            self.music.update(dt, self.chars.chased(self.music.cfg.get("combat_range_m", 45.0)))
        if self.sfx is not None:
            cam = self.camera
            p, r = cam.position, cam.right()
            self.sfx.update(self.chars.chars, self.chars.rowan.a if self.chars.rowan else None,
                            self.chars.spells.items, (p.x, p.y, p.z), (r.x, r.y, r.z), dt, self.ground_sound)
        self.time_s += dt

    def ground_sound(self, x: float, z: float) -> str:
        """Footstep surface: 'dirt' on paths and lanes, 'grass' elsewhere."""
        w = self.world
        c, r = w._px(x, z)
        ci, ri = int(round(c)), int(round(r))
        on_path = 0 <= ci < w.size and 0 <= ri < w.size and w.road[ri, ci] >= 120
        return "dirt" if on_path else "grass"

    def fly(self, dt: float, keys) -> None:
        cam = self.camera
        cam.prev_position = glm.vec3(cam.position)
        fwd = (keys[pygame.K_w] - keys[pygame.K_s])
        side = (keys[pygame.K_d] - keys[pygame.K_a])
        up = (keys[pygame.K_e] - keys[pygame.K_q])
        fast = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        slow = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        move = cam.forward() * fwd + cam.right() * side + glm.vec3(0, 1, 0) * up
        if glm.length(move) > 0:
            speed = self.base_speed * (5.0 if fast else 1.0) * (0.2 if slow else 1.0) * (TURBO if self.turbo else 1.0)
            cam.position = cam.position + glm.normalize(move) * speed * dt
        floor = self.world.height_at(cam.position.x, cam.position.z) + 0.6
        if cam.position.y < floor:
            cam.position.y = floor
        lim = self.world.half - 1.0
        cam.position.x = min(max(cam.position.x, -lim), lim)
        cam.position.z = min(max(cam.position.z, -lim), lim)

    # ---------------------------------------------------------------- render
    def render(self, alpha: float) -> None:
        w, h = pygame.display.get_window_size()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
        if self.play:
            self.follow_camera(alpha)
        eye, _view, _proj, viewproj = self.camera.matrices(w / max(h, 1), alpha)
        env = default_environment(self.fog)
        wire = self.ctx.wireframe
        self.ctx.wireframe = False
        self.sky.render(eye, viewproj, env)
        self.ctx.wireframe = wire
        self.terrain.render(eye, viewproj, env, self.settings.lod_distances_m)
        self.props.render(eye, viewproj, env)
        self.grass.render(eye, viewproj, env, self.time_s)
        self.chars.render(eye, viewproj, env, alpha)
        self.ctx.wireframe = False
        self.water.render(eye, viewproj, env, self.time_s)
        if self.show_overlay:
            self.overlay.render(w, h)
        self.ctx.wireframe = wire

    def overlay_lines(self) -> list[str]:
        ft = self.frame_times[-60:] or [0.0]
        ms = 1000 * sum(ft) / len(ft)
        p = self.camera.position
        st = self.terrain.stats
        counts = self.chars.counts()
        lines = [f"LYCANTROPE   {1000 / max(ms, 1e-3):5.0f} fps  {ms:5.1f} ms"
                 + (f"   TURBO x{TURBO:g}" if self.turbo else "") + ("" if self.fog else "   fog off")]
        if self.play and self.chars.rowan:
            a = self.chars.rowan.a
            lines.append(f"ROWAN  x {a.x:7.1f}  z {a.z:7.1f}   {a.state:<7} {a.anim.clip:<7} {a.speed:4.1f} m/s"
                         f"   biome {self.world.biome_at(a.x, a.z)}")
        else:
            lines.append(f"FLY {self.base_speed:.0f} m/s   x {p.x:7.1f}  z {p.z:7.1f}  y {p.y:6.1f}   (north = -z)")
        lines += [
            f"characters {self.chars.drawn} drawn of {sum(counts.values())}  "
            + "  ".join(f"{k} {v}" for k, v in counts.items()),
            f"terrain {st.triangles / 1000:.0f}k tris   props {self.props.drawn}/{self.props.count}",
        ]
        if self.play:
            lines += ["WASD move  Shift sprint  Ctrl walk  T turbo  LMB attack  RMB block  R heavy  Q cast",
                      "H hit  K die/revive  F7 helmet  F8 grass  F9 music  F10 sfx  wheel zoom  Esc mouse",
                      "F2 fog  F3 hide overlay  F4 fly"]
        else:
            lines += ["WASD QE fly  Shift/Ctrl speed  T turbo  wheel base speed  F4 back to Rowan",
                      "F1 wire  F2 fog  F3 hide overlay  F5 shaders  F6 debug  F9 music  F10 sfx  F12 shot"]
        return lines

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
        target = self.args.bench or (int(self.args.frames) if self.args.screenshot else 0)
        last = time.perf_counter()
        running = True
        while running:
            now = time.perf_counter()
            real_dt = now - last
            last = now
            # screenshots step the world exactly 1/60 s per frame so they're repeatable
            dt = 1 / 60 if self.args.screenshot else real_dt
            running = self.handle_events()
            for _ in range(self.clock.advance(dt)):
                self.update(self.clock.dt)
            self.latest_mouse()
            self.render(self.clock.alpha)
            pygame.display.flip()
            if self.settings.low_latency and not self.args.bench:
                self.ctx.finish()        # don't let the driver queue frames ahead: the camera answers sooner
            frames += 1
            if frames > 2:
                self.frame_times.append(real_dt)
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
    ap = argparse.ArgumentParser(prog="lycantrope", description="Lycantrope")
    ap.add_argument("--cam", help="free-fly start: X,Z,YAW,PITCH[,HEIGHT_ABOVE_GROUND]")
    ap.add_argument("--screenshot", help="save a PNG after a few frames and quit")
    ap.add_argument("--frames", default="5", help="frames to run before --screenshot (default 5)")
    ap.add_argument("--bench", type=int, default=0, help="render N frames, print timing, quit")
    ap.add_argument("--size", help="window size WxH")
    ap.add_argument("--orbit", help="testing: camera around Rowan as YAW,PITCH,DIST (yaw 0 = behind him)")
    ap.add_argument("--act", help="testing: what Rowan does from the start: run, sprint, walk, light, "
                                  "combo, heavy, block, cast, hit, die; or 'teleport:X,Z[:action]' to start elsewhere")
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    return App(Settings.load(), args).run()


if __name__ == "__main__":
    sys.exit(run())
