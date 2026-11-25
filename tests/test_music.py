"""Music timing (no sound card): pieces with gaps, combat crossfade, F9 mute."""
import pytest

from lycantrope.audio.music import MusicDirector, load_music_config


class FakePlayer:
    """Tracks 'play' for a fixed time; records volumes."""

    def __init__(self, length_s=10.0):
        self.length = length_s
        self.left = {}
        self.track = {}
        self.vol = {"explore": 0.0, "combat": 0.0}
        self.starts = []

    def ready(self, track):
        return True

    def play(self, layer, track, loop):
        self.left[layer] = float("inf") if loop else self.length
        self.track[layer] = track
        self.starts.append((layer, track))

    def busy(self, layer):
        return self.left.get(layer, 0) > 0

    def set_volume(self, layer, v):
        self.vol[layer] = v

    def stop(self, layer):
        self.left[layer] = 0

    def tick(self, dt):
        for k in self.left:
            self.left[k] -= dt


CFG = {"explore": ["a.mp3", "b.mp3"], "combat": ["fight.mp3"], "first_delay_s": 1.0, "gap_s": [5.0, 5.0],
       "fade_s": 2.0, "explore_under_combat": 0.0, "combat_hold_s": 3.0}


def run(d, p, seconds, chased=False, dt=0.1):
    for _ in range(int(round(seconds / dt))):
        d.update(dt, chased)
        p.tick(dt)


def test_pieces_with_quiet_gaps_and_no_repeats():
    p = FakePlayer(length_s=10.0)
    d = MusicDirector(CFG, p, volume=0.5, seed=1)
    run(d, p, 0.5)
    assert p.starts == []                         # first delay
    run(d, p, 1.0)
    assert len(p.starts) == 1
    run(d, p, 10.0 + 2.0)                         # piece over, inside the 5 s gap
    assert len(p.starts) == 1 and not p.busy("explore")
    run(d, p, 4.0)
    assert len(p.starts) == 2
    assert p.starts[0][1] != p.starts[1][1]      # never the same piece twice in a row
    assert p.vol["explore"] == pytest.approx(0.5)


def test_combat_crossfades_in_and_back_out():
    p = FakePlayer(length_s=1000.0)
    d = MusicDirector(CFG, p, volume=1.0, seed=2)
    run(d, p, 2.0)
    run(d, p, 1.0, chased=True)                   # halfway through the 2 s fade
    assert 0.3 < p.vol["combat"] < 0.7 and 0.3 < p.vol["explore"] < 0.7
    run(d, p, 2.0, chased=True)
    assert p.vol["combat"] == pytest.approx(1.0) and p.vol["explore"] == pytest.approx(0.0)
    assert p.busy("explore")                      # still playing underneath
    run(d, p, 2.0)                                # inside the hold: still combat
    assert p.vol["combat"] == pytest.approx(1.0)
    run(d, p, 4.0)                                # hold over, faded back
    assert p.vol["combat"] == pytest.approx(0.0) and p.vol["explore"] == pytest.approx(1.0)
    assert not p.busy("combat") and d.playing["combat"] is None


def test_no_combat_track_keeps_exploring_and_mute():
    p = FakePlayer(length_s=1000.0)
    d = MusicDirector(dict(CFG, combat=[]), p, volume=0.8, seed=3)
    run(d, p, 3.0, chased=True)
    assert p.vol["explore"] == pytest.approx(0.8) and "combat" not in p.left
    d.enabled = False                             # F9
    run(d, p, 0.1)
    assert p.vol["explore"] == 0.0


def test_config_skips_missing_tracks(tmp_path):
    f = tmp_path / "music.json"
    f.write_text('{"explore": ["data/audio/music.json", "assets/audio/music/not_made_yet.mp3"], "combat": []}')
    cfg = load_music_config(f)
    assert cfg["explore"] == ["data/audio/music.json"] and cfg["combat"] == []
