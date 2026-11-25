"""Background music (AUD-07): exploration pieces with quiet gaps between them, and a combat
layer that crossfades in while enemies are after Rowan.

Exploration tracks play through once (they have their own endings), then there is a quiet
stretch of `gap_s` seconds before the next one, picked at random and never the same twice in a
row when there's a choice. When combat starts, the combat track fades in (looping) over `fade_s`
and the exploration music fades down underneath it, still playing so it picks up where it was.
Combat ends `combat_hold_s` after the last enemy gives up, and the two fade back.

`MusicDirector` holds the timing and volumes and talks to a small player interface, so it can be
tested without a sound card. `MixerPlayer` is that interface on pygame's mixer: each track is
decoded into memory on a background thread (no hitch at load or when a track starts), and
combat tracks are made into seamless loops (`make_loop`: generated pieces fade out at the end).
Settings live in data/audio/music.json; tracks that don't exist yet are skipped.
"""
from __future__ import annotations

import json
import random
import threading
from pathlib import Path
from typing import Protocol

import numpy as np

from lycantrope.core.paths import DATA, ROOT

LAYERS = ("explore", "combat")


def load_music_config(path: Path | None = None) -> dict:
    path = path or DATA / "audio" / "music.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for layer in LAYERS:
        cfg[layer] = [t for t in cfg.get(layer, []) if (ROOT / t).exists()]
    return cfg


class Player(Protocol):
    def ready(self, track: str) -> bool: ...
    def play(self, layer: str, track: str, loop: bool) -> None: ...
    def busy(self, layer: str) -> bool: ...
    def set_volume(self, layer: str, volume: float) -> None: ...
    def stop(self, layer: str) -> None: ...


class MusicDirector:
    def __init__(self, cfg: dict, player: Player, volume: float = 0.6, seed: int | None = None) -> None:
        self.cfg = cfg
        self.player = player
        self.volume = volume
        self.enabled = True
        self.rng = random.Random(seed)
        self.gap = float(cfg.get("first_delay_s", 4.0))     # seconds until the next exploration piece
        self.playing: dict[str, str | None] = {layer: None for layer in LAYERS}
        self.gain = {"explore": 1.0, "combat": 0.0}          # crossfade position of each layer
        self.combat = False
        self.calm_for = 0.0                                  # seconds since enemies last chased Rowan
        self.last_explore: str | None = None

    def _pick(self, layer: str) -> str | None:
        tracks = self.cfg.get(layer, [])
        if not tracks:
            return None
        choices = [t for t in tracks if t != self.last_explore] or tracks
        return self.rng.choice(choices)

    def update(self, dt: float, chased: bool) -> None:
        cfg, p = self.cfg, self.player
        # combat starts at once and ends a few seconds after the last chaser gives up
        self.calm_for = 0.0 if chased else self.calm_for + dt
        has_combat = bool(cfg.get("combat"))
        self.combat = has_combat and (chased or (self.combat and self.calm_for < cfg.get("combat_hold_s", 6.0)))

        # exploration: a piece, then a quiet gap, then another piece
        if self.playing["explore"] and not p.busy("explore"):
            self.playing["explore"] = None
            lo, hi = cfg.get("gap_s", [30.0, 90.0])
            self.gap = self.rng.uniform(lo, hi)
        if self.playing["explore"] is None:
            self.gap -= dt
            if self.gap <= 0:
                track = self._pick("explore")
                if track and p.ready(track):
                    p.play("explore", track, loop=False)
                    self.playing["explore"] = self.last_explore = track

        # combat layer: starts when needed, stops once faded out
        if self.combat and self.playing["combat"] is None:
            track = self._pick("combat")
            if track and p.ready(track):
                p.play("combat", track, loop=True)
                self.playing["combat"] = track
                self.gain["combat"] = 0.0

        step = dt / max(float(cfg.get("fade_s", 2.0)), 1e-3)
        fighting = self.combat and self.playing["combat"] is not None
        under = float(cfg.get("explore_under_combat", 0.0))
        self.gain["combat"] = min(1.0, self.gain["combat"] + step) if fighting else max(0.0, self.gain["combat"] - step)
        want = under if fighting else 1.0
        e = self.gain["explore"]
        self.gain["explore"] = min(want, e + step) if e < want else max(want, e - step)
        if not self.combat and self.playing["combat"] and self.gain["combat"] <= 0.0:
            p.stop("combat")
            self.playing["combat"] = None

        master = self.volume if self.enabled else 0.0
        for layer in LAYERS:
            p.set_volume(layer, master * self.gain[layer])


def make_loop(samples: np.ndarray, rate: int, blend_s: float = 1.5, within_db: float = 8.0) -> np.ndarray:
    """Turn a generated piece (quiet lead-in, fade-out ending) into a seamless loop.

    Trims the start and end to where the music is at full strength (within `within_db` of its
    median loudness), then blends the last `blend_s` seconds into the opening, so the end runs
    straight into the start with no gap or dip. samples: (n,) or (n, channels).
    """
    x = samples.astype(np.float32)
    mono = x.mean(axis=1) if x.ndim > 1 else x
    win = max(1, rate // 20)                                  # 50 ms loudness windows
    n = len(mono) // win
    if n < 8:
        return samples
    rms = np.sqrt((mono[:n * win].reshape(n, win) ** 2).mean(axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    full = np.nonzero(db >= np.median(db) - within_db)[0]
    body = x[full[0] * win:(full[-1] + 1) * win]
    blend = min(int(blend_s * rate), len(body) // 4)
    if blend < 2:
        return body.astype(samples.dtype)
    t = np.linspace(0.0, 1.0, blend, dtype=np.float32)
    if body.ndim > 1:
        t = t[:, None]
    out = body[:-blend].copy()
    out[:blend] = body[-blend:] * np.cos(t * np.pi / 2) + body[:blend] * np.sin(t * np.pi / 2)   # equal power
    if np.issubdtype(samples.dtype, np.integer):
        info = np.iinfo(samples.dtype)
        out = np.clip(np.round(out), info.min, info.max)
    return out.astype(samples.dtype)


class MixerPlayer:
    """pygame.mixer: one channel per layer; tracks decoded in the background."""

    def __init__(self, tracks: list[str], loops: list[str] = ()) -> None:
        import pygame
        self.pygame = pygame
        self.sounds: dict[str, object] = {}
        self.channels = {layer: pygame.mixer.Channel(i) for i, layer in enumerate(LAYERS)}
        pygame.mixer.set_reserved(len(LAYERS))           # sound effects won't steal these
        threading.Thread(target=self._load, args=(list(tracks), set(loops)), daemon=True).start()

    def _load(self, tracks: list[str], loops: set[str]) -> None:
        pg = self.pygame
        for t in tracks:
            try:
                snd = pg.mixer.Sound(str(ROOT / t))
                if t in loops:                            # combat music: seamless loop
                    rate = pg.mixer.get_init()[0]
                    snd = pg.sndarray.make_sound(np.ascontiguousarray(make_loop(pg.sndarray.array(snd), rate)))
                self.sounds[t] = snd
            except (pg.error, OSError, ValueError) as exc:
                print(f"music: could not load {t} ({exc})")

    def ready(self, track: str) -> bool:
        return track in self.sounds

    def play(self, layer: str, track: str, loop: bool) -> None:
        self.channels[layer].play(self.sounds[track], loops=-1 if loop else 0)

    def busy(self, layer: str) -> bool:
        return self.channels[layer].get_busy()

    def set_volume(self, layer: str, volume: float) -> None:
        self.channels[layer].set_volume(max(0.0, min(1.0, volume)))

    def stop(self, layer: str) -> None:
        self.channels[layer].stop()


def start_music(volume: float) -> MusicDirector | None:
    """Music for the game, or None when there's no sound device or no tracks yet."""
    import pygame
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 2048)
    except pygame.error as exc:
        print(f"music off: no audio device ({exc})")
        return None
    cfg = load_music_config()
    tracks = cfg["explore"] + cfg["combat"]
    if not tracks:
        return None
    return MusicDirector(cfg, MixerPlayer(tracks, loops=cfg["combat"]), volume)
