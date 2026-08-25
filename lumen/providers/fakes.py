"""Deterministic, completely offline providers for tests and dry runs."""

from __future__ import annotations

import json
import wave
from collections.abc import Callable, Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from lumen.providers.base import (
    AudioResult,
    ImageResult,
    JsonObject,
    MessageContent,
    VideoResult,
    atomic_write,
    parse_json_object,
)


class FakeLLMProvider:
    """Return queued completions without opening sockets or resolving credentials."""

    def __init__(self, responses: Sequence[str | JsonObject] = ()) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def queue(self, response: str | JsonObject) -> None:
        self._responses.append(response)

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        api_key: str | None = None,
        **kwargs: Any,
    ) -> str:
        self.calls.append(
            {
                "operation": "chat",
                "model": model,
                "messages": [dict(message) for message in messages],
                "kwargs": dict(kwargs),
            }
        )
        if not self._responses:
            raise AssertionError("FakeLLMProvider has no queued response")
        response = self._responses.pop(0)
        if isinstance(response, dict):
            return json.dumps(response, ensure_ascii=False)
        return response

    def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: MessageContent,
        api_key: str | None = None,
        validator: Callable[[JsonObject], Any] | None = None,
        **kwargs: Any,
    ) -> JsonObject:
        raw = self.chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **kwargs,
        )
        parsed = parse_json_object(raw)
        if validator is not None:
            validator(parsed)
        return parsed


class FakeVLMProvider(FakeLLMProvider):
    def vision_json(
        self,
        *,
        model: str,
        system: str,
        text: str,
        image_data_urls: Sequence[str],
        api_key: str | None = None,
        **kwargs: Any,
    ) -> JsonObject:
        if not image_data_urls:
            raise ValueError("vision_json requires at least one image")
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        content.extend(
            {"type": "image_url", "image_url": {"url": value}} for value in image_data_urls
        )
        return self.chat_json(
            model=model,
            system=system,
            user=content,
            **kwargs,
        )


class FakeImageProvider:
    def __init__(self, *, model: str = "fake-image", size: tuple[int, int] = (320, 240)):
        self.model = model
        self.size = size
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        output_path: str | Path,
        **kwargs: Any,
    ) -> ImageResult:
        self.calls.append({"prompt": prompt, "output_path": str(output_path), **kwargs})
        image = Image.new("RGB", self.size, color=(24, 30, 48))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        path = atomic_write(output_path, buffer.getvalue())
        return ImageResult(path=path, model=self.model, cost_cny=0.0, request_id="fake")


class FakeVideoProvider:
    def __init__(self, *, model: str = "fake-video", content: bytes = b"FAKE-MP4") -> None:
        self.model = model
        self.content = bytes(content)
        self.calls: list[dict[str, Any]] = []

    def generate_from_image(
        self,
        prompt: str,
        image_path: str | Path,
        output_path: str | Path,
        **kwargs: Any,
    ) -> VideoResult:
        self.calls.append(
            {
                "prompt": prompt,
                "image_path": str(image_path),
                "output_path": str(output_path),
                **kwargs,
            }
        )
        path = atomic_write(output_path, self.content)
        return VideoResult(
            path=path,
            model=self.model,
            task_id="fake-task",
            cost_cny=0.0,
            request_id="fake",
        )


class FakeTTSProvider:
    def __init__(self, *, model: str = "fake-tts") -> None:
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def synthesize(
        self,
        text: str,
        output_path: str | Path,
        **kwargs: Any,
    ) -> AudioResult:
        self.calls.append({"text": text, "output_path": str(output_path), **kwargs})
        buffer = BytesIO()
        with wave.open(buffer, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(24_000)
            output.writeframes(b"\x00\x00" * 2_400)
        path = atomic_write(output_path, buffer.getvalue())
        return AudioResult(path=path, model=self.model, cost_cny=0.0, request_id="fake")
