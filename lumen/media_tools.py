"""Portable media-tool discovery for local runs and ModelScope CPU spaces."""

from __future__ import annotations

import shutil
from pathlib import Path

import imageio_ffmpeg


def resolve_ffmpeg(preferred: str = "ffmpeg") -> str:
    """Return a usable FFmpeg binary without requiring a system package."""

    discovered = shutil.which(preferred)
    if discovered:
        return discovered
    candidate = Path(preferred).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())
    bundled = Path(imageio_ffmpeg.get_ffmpeg_exe())
    if bundled.is_file():
        return str(bundled)
    raise FileNotFoundError("ffmpeg is unavailable (system and imageio-ffmpeg)")


def media_runtime() -> dict[str, str | bool]:
    """Describe the local/cloud-compatible media execution plane."""

    ffmpeg = resolve_ffmpeg()
    return {
        "ffmpeg": ffmpeg,
        "ffprobe": shutil.which("ffprobe") or "imageio-ffmpeg metadata reader",
        "portable": shutil.which("ffmpeg") is None,
    }
