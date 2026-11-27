"""Player settings (TEC-23), stored as settings.json next to the game."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields

from lycantrope.core.paths import SETTINGS_FILE


@dataclass
class Settings:
    width: int = 1600
    height: int = 900
    fullscreen: bool = False
    vsync: bool = True
    low_latency: bool = False         # glFinish after swap: less mouse lag, but prevents CPU-GPU overlap
    fov_deg: float = 70.0
    pixel_scale: int = 1            # 1 = native; 2+ = pixelated (render at 1/N, upscale nearest)
    pixel_smooth: bool = False      # True: bilinear upscale (smooth); False: nearest (hard pixels)
    flat_shade: bool = False        # flat-shaded facets on characters and props (low-poly look)
    mouse_sensitivity: float = 0.003
    invert_y: bool = False
    # terrain level of detail: chunk distance (m) where LOD 1, 2, 3 and 4 start
    lod_distances_m: list[float] = field(default_factory=lambda: [110.0, 260.0, 560.0, 1200.0])
    view_distance_m: float = 6000.0
    music_volume: float = 0.6         # 0 = off, 1 = full
    sfx_volume: float = 0.8           # sound effects: 0 = off, 1 = full
    subtitles: bool = True            # show what NPCs say (UIX-10)

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        if SETTINGS_FILE.exists():
            try:
                raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                names = {f.name for f in fields(cls)}
                for k, v in raw.items():
                    if k in names:
                        setattr(s, k, v)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"settings.json ignored ({exc})")
        else:
            s.save()                                    # write defaults so they're easy to edit
        return s

    def save(self) -> None:
        try:
            SETTINGS_FILE.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"could not save settings: {exc}")
