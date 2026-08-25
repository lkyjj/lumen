"""Local media validation and encoding at provider boundaries."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from lumen.providers.base import ProviderResponseError, atomic_write

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MIN_IMAGE_SIDE = 240
MAX_IMAGE_SIDE = 8000
MAX_IMAGE_ASPECT_RATIO = 8.0
_ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "BMP", "WEBP"}


@dataclass(frozen=True)
class ImageDataURL:
    value: str
    width: int
    height: int
    encoded_bytes: int
    mime_type: str = "image/png"


def _rgb_frame(image: Image.Image) -> Image.Image:
    image.seek(0)
    if "A" in image.getbands():
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (0, 0, 0))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _validate_dimensions(width: int, height: int) -> None:
    if not MIN_IMAGE_SIDE <= width <= MAX_IMAGE_SIDE:
        raise ValueError(
            f"image width must be between {MIN_IMAGE_SIDE} and {MAX_IMAGE_SIDE} pixels"
        )
    if not MIN_IMAGE_SIDE <= height <= MAX_IMAGE_SIDE:
        raise ValueError(
            f"image height must be between {MIN_IMAGE_SIDE} and {MAX_IMAGE_SIDE} pixels"
        )
    ratio = max(width / height, height / width)
    if ratio > MAX_IMAGE_ASPECT_RATIO:
        raise ValueError(f"image aspect ratio must not exceed {MAX_IMAGE_ASPECT_RATIO}:1")


def image_to_data_url(path: str | Path) -> ImageDataURL:
    """Validate a local reference and encode a flattened RGB PNG Data URL."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError(f"source image exceeds {MAX_IMAGE_BYTES} bytes")
    try:
        with Image.open(source) as opened:
            image_format = (opened.format or "").upper()
            if image_format not in _ALLOWED_FORMATS:
                raise ValueError(f"unsupported image format: {image_format or 'unknown'}")
            opened.load()
            rgb = _rgb_frame(opened)
    except UnidentifiedImageError as exc:
        raise ValueError(f"not a supported image: {source}") from exc

    width, height = rgb.size
    _validate_dimensions(width, height)
    buffer = BytesIO()
    rgb.save(buffer, format="PNG", optimize=True)
    raw = buffer.getvalue()
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError(f"encoded image exceeds {MAX_IMAGE_BYTES} bytes")
    encoded = base64.b64encode(raw).decode("ascii")
    return ImageDataURL(
        value=f"data:image/png;base64,{encoded}",
        width=width,
        height=height,
        encoded_bytes=len(raw),
    )


def save_rgb_image(data: bytes, path: str | Path, *, provider: str) -> Path:
    """Decode generated image bytes and atomically save a non-alpha RGB image."""

    try:
        with Image.open(BytesIO(data)) as opened:
            opened.load()
            rgb = _rgb_frame(opened)
    except (UnidentifiedImageError, OSError) as exc:
        raise ProviderResponseError(
            "downloaded result is not a valid image",
            provider=provider,
            operation="download image",
        ) from exc

    target = Path(path)
    suffix = target.suffix.lower()
    output = BytesIO()
    if suffix in {".jpg", ".jpeg"}:
        rgb.save(output, format="JPEG", quality=95)
    else:
        rgb.save(output, format="PNG", optimize=True)
    return atomic_write(target, output.getvalue())
