"""Cross-platform behaviour, mostly macOS.

ReelForge was written on Linux for a Linux box, and each of these covers a
place where that assumption had leaked into something that should be portable.
"""

from pathlib import Path

from core import hardware
from core.render import emoji, motion


# --------------------------------------------------------------------------
# emoji fonts
# --------------------------------------------------------------------------

def test_more_than_one_strike_size_is_tried():
    # Noto ships a 109px strike, Apple Color Emoji does not. A single
    # hardcoded size meant every emoji overlay was dropped on macOS, on a
    # machine that has a perfectly good colour emoji font.
    assert 109 in emoji.STRIKE_CANDIDATES
    assert 137 in emoji.STRIKE_CANDIDATES
    assert len(emoji.STRIKE_CANDIDATES) > 1


def test_a_font_is_loaded_at_whichever_strike_it_has():
    class OnlyOneSize:
        """Stands in for a bitmap font with a single available strike."""

        def truetype(self, path, size):
            if size != 137:
                raise OSError("invalid pixel size")
            return f"font@{size}"

    font, native = emoji._load_at_a_strike(OnlyOneSize(), Path("/f.ttc"))
    assert font == "font@137"
    assert native == 137


def test_a_font_with_no_usable_strike_gives_up_cleanly():
    class NeverLoads:
        def truetype(self, path, size):
            raise OSError("invalid pixel size")

    font, native = emoji._load_at_a_strike(NeverLoads(), Path("/f.ttc"))
    assert font is None and native == 0


def test_apple_emoji_font_is_a_candidate():
    assert any("Apple Color Emoji" in c for c in emoji.FONT_CANDIDATES)


# --------------------------------------------------------------------------
# browser discovery
# --------------------------------------------------------------------------

def test_mac_app_bundles_are_searched(tmp_path, monkeypatch):
    # Browsers on macOS live in app bundles and are never on PATH.
    bundle = tmp_path / "Applications/Google Chrome.app/Contents/MacOS"
    bundle.mkdir(parents=True)
    (bundle / "Google Chrome").write_text("#!/bin/sh\n")

    monkeypatch.delenv("REELFORGE_CHROMIUM", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setattr(motion.shutil, "which", lambda _n: None)
    monkeypatch.setattr(motion.Path, "home", staticmethod(lambda: tmp_path))

    found = motion.find_chromium()
    assert found is not None
    assert found.name == "Google Chrome"


def test_an_explicit_browser_wins(tmp_path, monkeypatch):
    explicit = tmp_path / "my-chrome"
    explicit.write_text("")
    monkeypatch.setenv("REELFORGE_CHROMIUM", str(explicit))
    assert motion.find_chromium() == explicit


# --------------------------------------------------------------------------
# hardware profile
# --------------------------------------------------------------------------

def test_apple_silicon_is_detected_only_on_arm_macs(monkeypatch):
    import platform

    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert hardware._apple_silicon()

    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    assert not hardware._apple_silicon()

    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert not hardware._apple_silicon()


def test_apple_silicon_uses_the_media_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(hardware, "_apple_silicon", lambda: True)
    monkeypatch.setattr(hardware, "_gpu", lambda: None)
    monkeypatch.setattr(hardware, "_has_encoder", lambda name: name == "h264_videotoolbox")
    monkeypatch.setattr(hardware, "_cores", lambda: 10)
    monkeypatch.setattr(hardware, "_ram_gb", lambda: 32.0)

    p = hardware.profile(tmp_path)
    assert p.encoder == "h264_videotoolbox"
    assert "-realtime" in p.draft_args          # draft trades bits for speed
    # A fixed-function encoder does not go faster with more parallel jobs --
    # they queue on the same silicon and starve memory bandwidth.
    assert p.render_parallelism <= 4


def test_a_mac_without_videotoolbox_falls_back_to_software(monkeypatch, tmp_path):
    monkeypatch.setattr(hardware, "_apple_silicon", lambda: True)
    monkeypatch.setattr(hardware, "_gpu", lambda: None)
    monkeypatch.setattr(hardware, "_has_encoder", lambda _name: False)
    monkeypatch.setattr(hardware, "_cores", lambda: 10)
    monkeypatch.setattr(hardware, "_ram_gb", lambda: 32.0)

    p = hardware.profile(tmp_path)
    assert p.encoder == "libx264"


def test_transcription_stays_on_cpu_on_apple_silicon(monkeypatch, tmp_path):
    # CTranslate2 has no Metal backend. Claiming a GPU device here would fail
    # at load time rather than merely being slow.
    monkeypatch.setattr(hardware, "_apple_silicon", lambda: True)
    monkeypatch.setattr(hardware, "_gpu", lambda: None)
    monkeypatch.setattr(hardware, "_has_encoder", lambda name: name == "h264_videotoolbox")
    monkeypatch.setattr(hardware, "_cores", lambda: 10)
    monkeypatch.setattr(hardware, "_ram_gb", lambda: 32.0)

    p = hardware.profile(tmp_path)
    assert p.whisper_device == "cpu"
    assert p.whisper_compute == "int8"


def test_an_nvidia_box_still_prefers_nvenc(monkeypatch, tmp_path):
    monkeypatch.setattr(hardware, "_apple_silicon", lambda: False)
    monkeypatch.setattr(hardware, "_gpu", lambda: "RTX 4090")
    monkeypatch.setattr(hardware, "_has_encoder", lambda name: name == "h264_nvenc")
    monkeypatch.setattr(hardware, "_cores", lambda: 16)
    monkeypatch.setattr(hardware, "_ram_gb", lambda: 64.0)

    p = hardware.profile(tmp_path)
    assert p.encoder == "h264_nvenc"
    assert p.whisper_device == "cuda"
