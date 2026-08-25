#!/usr/bin/env python3
"""Build the zero-network 15-second LUMEN concept trailer from approved stills."""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "projects" / "vanishing-light" / "03_bible" / "candidates"
DEFAULT_OUTPUT = (
    ROOT / "projects" / "vanishing-light" / "06_cut" / "generated" / "demo_15s_v1.mp4"
)
WIDTH, HEIGHT, FPS, DURATION = 1280, 720, 24, 15.0
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
)


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    raise FileNotFoundError("No CJK font found for trailer titles")


def _ease(value: float) -> float:
    value = min(1.0, max(0.0, value))
    return value * value * (3.0 - 2.0 * value)


def _cover(image: Image.Image, zoom: float, pan_x: float, pan_y: float) -> Image.Image:
    base_scale = max(WIDTH / image.width, HEIGHT / image.height) * zoom
    size = (math.ceil(image.width * base_scale), math.ceil(image.height * base_scale))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    overflow_x = max(0, resized.width - WIDTH)
    overflow_y = max(0, resized.height - HEIGHT)
    left = round(overflow_x * min(1.0, max(0.0, pan_x)))
    top = round(overflow_y * min(1.0, max(0.0, pan_y)))
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def _vignette() -> Image.Image:
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    nx = (xx - WIDTH / 2) / (WIDTH / 2)
    ny = (yy - HEIGHT / 2) / (HEIGHT / 2)
    radius = np.sqrt(nx * nx + ny * ny)
    alpha = np.clip((radius - 0.38) * 105, 0, 105).astype(np.uint8)
    layer = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    layer[..., 3] = alpha
    return Image.fromarray(layer, "RGBA")


VIGNETTE = _vignette()


def _caption(
    frame: Image.Image,
    primary: str,
    secondary: str,
    opacity: float,
    *,
    y: int = 570,
) -> Image.Image:
    if opacity <= 0:
        return frame
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    alpha = round(255 * min(1.0, opacity))
    draw.text(
        (WIDTH // 2, y),
        primary,
        font=_font(35),
        fill=(235, 241, 242, alpha),
        stroke_width=2,
        stroke_fill=(0, 0, 0, alpha),
        anchor="mm",
    )
    draw.text(
        (WIDTH // 2, y + 48),
        secondary,
        font=_font(18),
        fill=(153, 190, 198, alpha),
        stroke_width=1,
        stroke_fill=(0, 0, 0, alpha),
        anchor="mm",
    )
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def _caption_opacity(local: float, length: float) -> float:
    return min(_ease(local / 0.45), _ease((length - local) / 0.45))


def _scene(
    image: Image.Image,
    local: float,
    length: float,
    *,
    zoom_from: float,
    zoom_to: float,
    pan_from: tuple[float, float],
    pan_to: tuple[float, float],
    caption: tuple[str, str] | None = None,
) -> Image.Image:
    progress = _ease(local / length)
    zoom = zoom_from + (zoom_to - zoom_from) * progress
    pan_x = pan_from[0] + (pan_to[0] - pan_from[0]) * progress
    pan_y = pan_from[1] + (pan_to[1] - pan_from[1]) * progress
    frame = _cover(image, zoom, pan_x, pan_y)
    frame = ImageEnhance.Color(frame).enhance(0.88)
    if caption:
        frame = _caption(frame, *caption, _caption_opacity(local, length))
    return frame


def _light_sweep(frame: Image.Image, local: float, length: float) -> Image.Image:
    progress = _ease(local / length)
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    center_x = round(-300 + progress * 1900)
    draw.polygon(
        [(center_x, 0), (center_x + 380, 0), (center_x + 110, HEIGHT), (center_x - 270, HEIGHT)],
        fill=(236, 193, 113, 68),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(42))
    bloom = Image.alpha_composite(frame.convert("RGBA"), overlay)
    return ImageEnhance.Brightness(bloom.convert("RGB")).enhance(1.08)


def _title_card(local: float) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), "#05080a")
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    opacity = min(_ease(local / 0.35), _ease((1.9 - local) / 0.3))
    alpha = round(255 * opacity)
    draw.text(
        (WIDTH // 2, 308),
        "消 失 的 光 芒",
        font=_font(55),
        fill=(235, 226, 204, alpha),
        anchor="mm",
    )
    draw.text(
        (WIDTH // 2, 376),
        "THE VANISHING LIGHT",
        font=_font(23),
        fill=(148, 183, 190, alpha),
        anchor="mm",
    )
    draw.line(
        (WIDTH // 2 - 105, 420, WIDTH // 2 + 105, 420),
        fill=(183, 146, 86, round(alpha * 0.75)),
        width=1,
    )
    draw.text(
        (WIDTH // 2, 455),
        "LUMEN · 一个人的 AI 电影剧组",
        font=_font(18),
        fill=(133, 145, 147, alpha),
        anchor="mm",
    )
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def _render_frame(images: dict[str, Image.Image], time_s: float, index: int) -> Image.Image:
    if time_s < 3.4:
        frame = _scene(
            images["back"],
            time_s,
            3.4,
            zoom_from=1.0,
            zoom_to=1.055,
            pan_from=(0.48, 0.5),
            pan_to=(0.53, 0.48),
            caption=("当世界失去最后一道光", "WHEN THE LAST LIGHT DISAPPEARS"),
        )
    elif time_s < 6.2:
        local = time_s - 3.4
        frame = _scene(
            images["front"],
            local,
            2.8,
            zoom_from=1.01,
            zoom_to=1.105,
            pan_from=(0.5, 0.46),
            pan_to=(0.5, 0.44),
            caption=("剩余能源：1", "POWER REMAINING: 1"),
        )
    elif time_s < 8.9:
        local = time_s - 6.2
        frame = _scene(
            images["hands"],
            local,
            2.7,
            zoom_from=1.01,
            zoom_to=1.075,
            pan_from=(0.45, 0.55),
            pan_to=(0.55, 0.48),
            caption=("进化，或点亮灯塔", "EVOLVE · OR LIGHT THE BEACON"),
        )
    elif time_s < 11.5:
        local = time_s - 8.9
        frame = _scene(
            images["eyes"],
            local,
            2.6,
            zoom_from=1.02,
            zoom_to=1.13,
            pan_from=(0.48, 0.46),
            pan_to=(0.52, 0.47),
            caption=("为了活下去，要交出多少人性？", "WHAT WOULD YOU SURRENDER TO SURVIVE?"),
        )
        if index % 19 == 0:
            frame = ImageEnhance.Contrast(frame).enhance(1.45)
    elif time_s < 13.1:
        local = time_s - 11.5
        frame = _scene(
            images["back"],
            local,
            1.6,
            zoom_from=1.055,
            zoom_to=1.02,
            pan_from=(0.53, 0.48),
            pan_to=(0.48, 0.5),
            caption=("……万一呢。", "WHAT IF SOMEONE IS STILL OUT THERE?"),
        )
        frame = _light_sweep(frame, local, 1.6)
    else:
        frame = _title_card(time_s - 13.1)

    if time_s < 0.55:
        frame = ImageEnhance.Brightness(frame).enhance(_ease(time_s / 0.55))
    frame = Image.alpha_composite(frame.convert("RGBA"), VIGNETTE).convert("RGB")
    rng = np.random.default_rng(20260826 + index)
    array = np.asarray(frame, dtype=np.int16)
    grain = rng.normal(0, 2.0, array.shape[:2])[..., None]
    array = np.clip(array + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(array, "RGB")


def _write_soundtrack(path: Path) -> None:
    sample_rate = 48_000
    sample_count = round(DURATION * sample_rate)
    times = np.arange(sample_count, dtype=np.float64) / sample_rate
    rng = np.random.default_rng(606)
    white = rng.normal(0, 1, sample_count + 800)
    cumulative = np.cumsum(np.pad(white, (1, 0)))
    wind = (cumulative[800:] - cumulative[:-800]) / 800
    wind = wind[:sample_count]
    wind /= max(np.max(np.abs(wind)), 1e-9)
    audio = wind * 0.105 + np.sin(2 * np.pi * 43 * times) * 0.025

    for start in (2.45, 5.25, 8.15, 10.75):
        local = times - start
        pulse = (local >= 0) & (local < 0.55)
        audio[pulse] += (
            np.sin(2 * np.pi * 54 * local[pulse])
            * np.exp(-local[pulse] * 10)
            * 0.20
        )
    for start, frequency in ((3.45, 820), (6.2, 615), (8.9, 1080)):
        local = times - start
        beep = (local >= 0) & (local < 0.22)
        audio[beep] += (
            np.sin(2 * np.pi * frequency * local[beep])
            * np.sin(np.pi * local[beep] / 0.22)
            * 0.12
        )
    reveal = np.clip((times - 11.5) / 1.3, 0, 1) * np.clip((13.2 - times) / 0.6, 0, 1)
    audio += reveal * (
        np.sin(2 * np.pi * 110 * times) * 0.07
        + np.sin(2 * np.pi * 165 * times) * 0.045
    )
    chime_local = times - 13.05
    chime = (chime_local >= 0) & (chime_local < 1.6)
    audio[chime] += (
        np.sin(2 * np.pi * 660 * chime_local[chime])
        * np.exp(-chime_local[chime] * 2.4)
        * 0.075
    )
    fade = np.ones_like(audio)
    fade[times < 0.6] = times[times < 0.6] / 0.6
    fade[times > 14.3] = np.clip((15 - times[times > 14.3]) / 0.7, 0, 1)
    audio *= fade
    audio /= max(np.max(np.abs(audio)) / 0.88, 1.0)
    stereo = np.column_stack((audio, audio * 0.97))
    pcm = (stereo * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def build(output: Path) -> Path:
    required = {
        "back": CANDIDATES / "anchor_A_lighthouse_back_v1.png",
        "front": CANDIDATES / "E06_front_v1.png",
        "hands": CANDIDATES / "E06_hands_v1.png",
        "eyes": CANDIDATES / "E06_evolved_eyes_v1.png",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing trailer anchors: " + ", ".join(missing))
    images = {name: Image.open(path).convert("RGB") for name, path in required.items()}
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="lumen-demo-") as temporary:
        temp = Path(temporary)
        silent = temp / "silent.mp4"
        soundtrack = temp / "soundtrack.wav"
        command = [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(silent),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
        if process.stdin is None:
            raise RuntimeError("ffmpeg stdin unavailable")
        for index in range(round(DURATION * FPS)):
            process.stdin.write(_render_frame(images, index / FPS, index).tobytes())
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("ffmpeg failed while encoding trailer picture")

        _write_soundtrack(soundtrack)
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(silent),
                "-i",
                str(soundtrack),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{DURATION:.3f}",
                "-movflags",
                "+faststart",
                "-metadata",
                "title=消失的光芒 · 15s Concept Trailer",
                str(output),
            ],
            check=True,
        )
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-ss",
                "12.15",
                "-i",
                str(output),
                "-frames:v",
                "1",
                str(output.with_suffix(".poster.png")),
            ],
            check=True,
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.output.expanduser().resolve())
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
