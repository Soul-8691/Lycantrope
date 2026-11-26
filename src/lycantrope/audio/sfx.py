"""Character sound effects (AUD-05, AUD-06) with positional audio (AUD-08).

SfxDirector watches the characters each tick and turns what they do into cues: a new attack, cast,
hit or death clip; spotting Rowan; footfalls timed to the walk/run cycle; an occasional idle noise;
villagers and cows startled by a swing nearby; a caster's spell leaving the hand; spells in flight
(a loop) and where they land; swim strokes, splashing in and out of deep water, lapping water while
treading, and wading steps in the shallows. data/audio/sfx.json maps each character kind's events to sounds.

The director is plain Python (tested without a sound device). MixerSfx plays the cues through
pygame.mixer: a random take per sound (never the same twice running), quieter with distance and
panned left/right by the camera.
"""
from __future__ import annotations

import json
import math
import random
import threading

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path

from lycantrope.core.paths import ASSETS, DATA

SFX_DIR = ASSETS / "audio" / "sfx"
VO_DIR = ASSETS / "audio" / "vo"                 # NPC voice lines: vo/<voice>/<event>_<n>.mp3
GREET_M = 3.5                                    # an NPC greets Rowan when he comes this close
GREET_COOLDOWN_S = 45.0
CLIP_EVENTS = {"light1": "light", "light2": "light", "light3": "light", "heavy": "heavy",
               "attack1": "attack", "attack2": "attack", "cast": "cast", "hit": "hit", "death": "death",
               "jump": "jump"}
GAITS = ("walk", "run", "sprint")
ALERT_FROM = ("wander", "idle", "return")
STARTLE_M = 6.0
ALERT_COOLDOWN_S = 6.0
STARTLE_COOLDOWN_S = 5.0


TALK_FPS = 30                                    # loudness envelope rate for jaw movement


def loudness(samples: np.ndarray, rate: int) -> np.ndarray:
    """Loudness of a voice line, 0..1 at TALK_FPS, for the speaker's jaw (silence = closed)."""
    x = samples.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = max(1, rate // TALK_FPS)
    n = len(x) // hop
    if n == 0:
        return np.zeros(1, np.float32)
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    top = float(np.percentile(rms, 95)) or 1.0
    env = np.clip(rms / top, 0.0, 1.0)
    env[env < 0.12] = 0.0                           # breaths and room tone: mouth shut
    return env.astype(np.float32)


def load_sfx_config(path: Path | None = None) -> dict:
    return json.loads((path or DATA / "audio" / "sfx.json").read_text(encoding="utf-8"))


def spatial(listener: tuple[float, float, float], right: tuple[float, float, float],
            src: tuple[float, float, float], ref_m: float, max_m: float) -> tuple[float, float]:
    """(left, right) channel volumes for a sound at src: full within ref_m, fading to silence at
    max_m, and panned (never fully to one side) by where it is relative to the camera's right."""
    dx, dy, dz = src[0] - listener[0], src[1] - listener[1], src[2] - listener[2]
    d = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d >= max_m:
        return 0.0, 0.0
    gain = min(1.0, ref_m / max(d, 1e-6)) * (1.0 - d / max_m)
    flat = math.hypot(dx, dz)
    side = (dx * right[0] + dz * right[2]) / flat if flat > 0.5 else 0.0     # -1 left .. +1 right
    ang = (1.0 + 0.7 * max(-1.0, min(1.0, side))) * math.pi / 4               # equal-power pan
    k = math.sqrt(2.0) * gain
    return min(1.0, k * math.cos(ang)), min(1.0, k * math.sin(ang))


@dataclass
class Cue:
    sound: str                                  # "group/sound"
    pos: tuple[float, float, float] | None      # None: not positional (Rowan's own sounds)
    volume: float = 1.0
    at: float = 0.0                             # play when the director's clock reaches this
    speaker: int | None = None                  # voice lines: id() of the actor saying it


@dataclass
class Track:
    clip: str = ""
    time: float = 0.0
    state: str = ""
    fired: bool = True
    idle_in: float = 0.0
    alert_ok_at: float = 0.0
    startle_ok_at: float = 0.0
    near_rowan: bool = False
    air: bool = False
    greet_ok_at: float = 0.0


@dataclass
class SfxDirector:
    cfg: dict
    rng: random.Random = field(default_factory=random.Random)
    now: float = 0.0
    tracks: dict[int, Track] = field(default_factory=dict)
    last: dict[tuple[str, str], float] = field(default_factory=dict)
    pending: list[Cue] = field(default_factory=list)
    spells: dict[int, object] = field(default_factory=dict)      # in flight: id -> spell
    loops: dict = field(default_factory=dict)                     # this tick's clip loops

    def kind(self, k: str) -> dict:
        kinds = self.cfg.get("kinds", {})
        spec = kinds.get(k, {})
        if "like" in spec:                              # sounds borrowed from another kind
            spec = {**kinds.get(spec["like"], {}), **{key: v for key, v in spec.items() if key != "like"}}
        return spec

    # ------------------------------------------------------------------ cues
    def emit(self, kind: str, event: str, pos, out: list[Cue], ground=None, positional=True,
             voice: str | None = None, speaker: int | None = None) -> None:
        spec = self.kind(kind).get("events", {}).get(event)
        if event == "step" and ground and pos and "wade_step" in self.cfg and ground(pos[0], pos[2]) == "water":
            spec = self.cfg["wade_step"]                # splashing through the shallows
        if spec is None:
            return
        if event != "step":
            gap = float(self.cfg.get("min_gap_s", 0.3))
            if self.now - self.last.get((kind, event), -1e9) < gap:
                return                                  # a pack spotting you at once: one growl
            self.last[(kind, event)] = self.now
        items = spec if isinstance(spec, list) else [spec]
        items = [{"s": i} if isinstance(i, str) else i for i in items]
        chosen = [i for i in items if "chance" not in i]
        roll, acc = self.rng.random(), 0.0
        for i in items:
            if "chance" in i:
                acc += float(i["chance"])
                if roll < acc:
                    chosen.append(i)
                    break
        for i in chosen:
            name = i["s"]
            if "{voice}" in name:
                if not voice:
                    continue                            # no voice for this NPC: say nothing
                name = name.replace("{voice}", voice)
            if "{ground}" in name:
                name = name.replace("{ground}", ground(pos[0], pos[2]) if ground and pos else "grass")
            cue = Cue(name, pos if positional else None, float(i.get("volume", 1.0)),
                      self.now + float(i.get("delay_s", 0.0)), speaker if name.startswith("vo/") else None)
            (self.pending if i.get("delay_s") else out).append(cue)

    # ------------------------------------------------------------------ tick
    def update(self, chars, rowan, spells, listener, dt: float, ground=None) -> tuple[list[Cue], dict]:
        """chars: objects with .actor (and .brain); rowan: Rowan's actor or None; spells: projectiles
        with .pos and .burst. Returns (cues to play now, spell loops {id: (sound, pos, volume)})."""
        self.now += dt
        out: list[Cue] = []
        self.loops = {}
        lx, lz = listener[0], listener[2]
        max_m = float(self.cfg.get("max_m", 45.0))
        steps_m = float(self.cfg.get("steps_within_m", 22.0))
        rowan_moves: list[str] = []
        for c in chars:
            a = c.actor
            spec = self.kind(a.kind)
            t = self.tracks.get(id(a))
            if t is None:                               # first sight: nothing has "just started"
                t = self.tracks[id(a)] = Track(a.anim.clip, a.anim.time, a.state, True,
                                               self._idle_wait(spec))
            is_rowan = a is rowan
            positional = spec.get("positional", not is_rowan)
            near2 = (a.x - lx) ** 2 + (a.z - lz) ** 2
            audible = is_rowan or near2 < max_m * max_m
            pos = (a.x, a.y + 1.0, a.z)
            clip, time = a.anim.clip, a.anim.time
            started = clip != t.clip or time < t.time - 1e-6
            if started and clip in CLIP_EVENTS and audible:
                ev = CLIP_EVENTS[clip]
                self.emit(a.kind, ev, pos, out, ground, positional)
                if is_rowan and ev in ("light", "heavy", "cast"):
                    rowan_moves.append(ev)
            # footfalls: crossing each step point of the walk/run cycle
            if clip in GAITS and clip == t.clip and a.speed > 0.3 and (is_rowan or near2 < steps_m * steps_m):
                info = a.clips.get(clip)
                dur = info.duration if info and info.duration > 0 else 1.0
                n = int(spec.get("steps_per_cycle", 2))
                if math.floor(time / dur * n) != math.floor(t.time / dur * n):
                    self.emit(a.kind, "step", (a.x, a.y, a.z), out, ground, positional)
            # once per loop of a clip, at a set point (a swim stroke's splash)
            for ph, ev in spec.get("cycle_events", {}).get(clip, ()):
                info = a.clips.get(clip)
                dur = info.duration if info and info.duration > 0 else 1.0
                if clip == t.clip and audible and math.floor(time / dur - ph) != math.floor(t.time / dur - ph):
                    self.emit(a.kind, ev, pos, out, ground, positional)
            # entering or leaving a state (into the water, out of it)
            if a.state != t.state and t.state:
                se = spec.get("state_events", {})
                if a.state in se and "enter" in se[a.state] and audible:
                    self.emit(a.kind, se[a.state]["enter"], pos, out, ground, positional)
                if t.state in se and "leave" in se[t.state] and audible:
                    self.emit(a.kind, se[t.state]["leave"], pos, out, ground, positional)
            # a sound that keeps going while a clip plays (lapping water while treading)
            cl = spec.get("clip_loops", {}).get(clip)
            if cl and audible:
                self.loops[("clip", id(a))] = (cl["s"], pos if positional else None, float(cl.get("volume", 1.0)))
            # landing from a jump or a fall
            air = bool(getattr(a, "airborne", False))
            if t.air and not air and audible:
                self.emit(a.kind, "land", (a.x, a.y, a.z), out, ground, positional)
            t.air = air
            # spotting Rowan
            if a.state == "chase" and t.state in ALERT_FROM and self.now >= t.alert_ok_at:
                t.alert_ok_at = self.now + ALERT_COOLDOWN_S
                if audible:
                    self.emit(a.kind, "alert", pos, out, ground, positional)
            # a caster's spell leaves the hand
            b = getattr(c, "brain", None)
            if b is not None:
                if b.fired and not t.fired and audible:
                    self.emit(a.kind, "release", pos, out, ground, positional)
                t.fired = b.fired
            # now and then while wandering
            if "idle_every_s" in spec and a.state in ("wander", "idle"):
                t.idle_in -= dt
                if t.idle_in <= 0:
                    t.idle_in = self._idle_wait(spec)
                    if near2 < (0.8 * max_m) ** 2:
                        self.emit(a.kind, "idle", pos, out, ground, positional)
            # walking up to an NPC: a greeting in its own voice, now and then
            voice = getattr(c, "voice", None)
            if voice and rowan is not None and not is_rowan and "greet" in spec.get("events", {}):
                d2 = (a.x - rowan.x) ** 2 + (a.z - rowan.z) ** 2
                if not t.near_rowan and d2 < GREET_M ** 2:
                    t.near_rowan = True
                    if self.now >= t.greet_ok_at and a.state in ("wander", "idle"):
                        t.greet_ok_at = self.now + GREET_COOLDOWN_S
                        self.emit(a.kind, "greet", pos, out, ground, positional, voice, id(a))
                elif t.near_rowan and d2 > (GREET_M + 2.0) ** 2:
                    t.near_rowan = False
            t.clip, t.time, t.state = clip, time, a.state
        if rowan_moves and rowan is not None:          # villagers and cows flinch at a swing nearby
            for c in chars:
                a = c.actor
                if a is rowan or "startled" not in self.kind(a.kind).get("events", {}):
                    continue
                t = self.tracks[id(a)]
                if (a.x - rowan.x) ** 2 + (a.z - rowan.z) ** 2 < STARTLE_M ** 2 and self.now >= t.startle_ok_at:
                    t.startle_ok_at = self.now + STARTLE_COOLDOWN_S
                    self.emit(a.kind, "startled", (a.x, a.y + 1.0, a.z), out, ground,
                              voice=getattr(c, "voice", None), speaker=id(a))
        # delayed parts (a body hitting the ground after the death cry)
        due = [q for q in self.pending if q.at <= self.now]
        if due:
            self.pending = [q for q in self.pending if q.at > self.now]
            out += due
        loops = self._spells(spells or [], out)
        loops.update(self.loops)
        return out, loops

    def _idle_wait(self, spec: dict) -> float:
        lo, hi = spec.get("idle_every_s", (10, 30))
        return self.rng.uniform(float(lo), float(hi))

    def _spells(self, spells, out: list[Cue]) -> dict:
        sc = self.cfg.get("spell", {})
        loops, alive = {}, {}
        for s in spells:
            p = tuple(float(v) for v in s.pos)
            k = id(s)
            if s.burst < 0:
                alive[k] = s
                if sc.get("loop"):
                    loops[k] = (sc["loop"], p, float(sc.get("loop_volume", 0.5)))
            elif k in self.spells and sc.get("hit"):   # it just landed
                out.append(Cue(sc["hit"], p, 1.0, self.now))
        self.spells = alive
        return loops


# ---------------------------------------------------------------------------- #
class MixerSfx:
    """pygame.mixer playback: sounds decoded in the background, a free channel per cue."""

    def __init__(self, cfg: dict, volume: float, root: Path = SFX_DIR) -> None:
        import pygame
        self.pygame = pygame
        self.cfg = cfg
        self.volume = volume
        self.enabled = True
        self.voices = True                     # debug: NPC voice lines on or off (other sounds unaffected)
        self.sounds: dict[str, list] = {}
        self.last_take: dict[str, int] = {}
        self.loop_channels: dict = {}
        self.envelopes: dict[int, np.ndarray] = {}   # id(Sound) -> loudness 0..1 at TALK_FPS (voice lines)
        self.texts: dict[int, str] = {}              # id(Sound) -> what the line says (subtitles)
        self.loop_names: dict = {}
        if pygame.mixer.get_num_channels() < 32:
            pygame.mixer.set_num_channels(32)
        threading.Thread(target=self._load, args=(root,), daemon=True).start()

    def _load(self, root: Path) -> None:
        pg = self.pygame
        found: dict[str, list] = {}
        try:
            said = json.loads((VO_DIR / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            said = {}
        for prefix, base in (("", root), ("vo/", VO_DIR)):
            for f in sorted(base.glob("*/*.mp3")):
                stem, _, take = f.stem.rpartition("_")
                if not take.isdigit():
                    continue
                try:
                    snd = pg.mixer.Sound(str(f))
                    found.setdefault(f"{prefix}{f.parent.name}/{stem}", []).append(snd)
                    if prefix:
                        self.envelopes[id(snd)] = loudness(pg.sndarray.array(snd), pg.mixer.get_init()[0])
                        self.texts[id(snd)] = said.get(f"{f.parent.name}/{f.name}", {}).get("text", "")
                except (pg.error, OSError, ValueError) as exc:
                    print(f"sfx: could not load {f.name} ({exc})")
        self.sounds = found

    def _take(self, name: str):
        takes = self.sounds.get(name)
        if not takes:
            return None
        i = random.randrange(len(takes))
        if len(takes) > 1 and i == self.last_take.get(name):
            i = (i + 1 + random.randrange(len(takes) - 1)) % len(takes)
        self.last_take[name] = i
        return takes[i]

    def _levels(self, pos, volume: float, listener, right) -> tuple[float, float]:
        v = volume * self.volume * float(self.cfg.get("volume", 1.0))
        if pos is None:
            return min(1.0, v), min(1.0, v)
        l, r = spatial(listener, right, pos, float(self.cfg.get("ref_m", 4.0)), float(self.cfg.get("max_m", 45.0)))
        return min(1.0, l * v), min(1.0, r * v)

    def play(self, cues: list[Cue], loops: dict, listener, right) -> list[tuple[int, np.ndarray, str]]:
        """Play cues and loops; returns (speaker, loudness envelope, text) for each voice line started."""
        talking = []
        if not self.enabled:
            loops = {}
        for q in cues if self.enabled else ():
            if not self.voices and q.sound.startswith("vo/"):
                continue
            l, r = self._levels(q.pos, q.volume, listener, right)
            if l + r < 0.01:
                continue
            snd = self._take(q.sound)
            if snd is None:
                continue
            ch = self.pygame.mixer.find_channel(not q.sound.startswith("footsteps/"))   # steps never steal
            if ch is not None:
                ch.play(snd)
                ch.set_volume(l, r)
                if q.speaker is not None and id(snd) in self.envelopes:
                    talking.append((q.speaker, self.envelopes[id(snd)], self.texts.get(id(snd), "")))
        for k in [k for k in self.loop_channels if k not in loops or loops[k][0] != self.loop_names.get(k)]:
            self.loop_channels.pop(k).stop()
            self.loop_names.pop(k, None)
        for k, (name, pos, vol) in loops.items():
            ch = self.loop_channels.get(k)
            if ch is None:
                snd = self._take(name)
                ch = self.pygame.mixer.find_channel(True) if snd is not None else None
                if ch is None:
                    continue
                ch.play(snd, loops=-1)
                self.loop_channels[k] = ch
                self.loop_names[k] = name
            ch.set_volume(*self._levels(pos, vol, listener, right))
        return talking


class SfxSystem:
    def __init__(self, cfg: dict, player: MixerSfx) -> None:
        self.director = SfxDirector(cfg)
        self.player = player

    @property
    def enabled(self) -> bool:
        return self.player.enabled

    @enabled.setter
    def enabled(self, on: bool) -> None:
        self.player.enabled = on

    @property
    def voices(self) -> bool:
        return self.player.voices

    @voices.setter
    def voices(self, on: bool) -> None:
        self.player.voices = on

    def update(self, chars, rowan, spells, listener, right, dt: float, ground=None) -> list:
        """Returns (speaker actor id, loudness envelope, text) for every voice line that started."""
        cues, loops = self.director.update(chars, rowan, spells, listener, dt, ground)
        return self.player.play(cues, loops, listener, right) or []


def start_sfx(volume: float) -> SfxSystem | None:
    """Sound effects for the game, or None with no sound device or no sound files."""
    import pygame
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 2048)
    except pygame.error as exc:
        print(f"sound effects off: no audio device ({exc})")
        return None
    if not any(SFX_DIR.glob("*/*.mp3")):
        return None
    cfg = load_sfx_config()
    return SfxSystem(cfg, MixerSfx(cfg, volume))
