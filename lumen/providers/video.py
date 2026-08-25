"""DashScope Wan video provider with generation-specific payload adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lumen.providers.base import (
    ProviderResponseError,
    UnsupportedModelError,
    VideoResult,
    atomic_write,
    download_bytes,
    find_nested_string,
    request_id,
)
from lumen.providers.dashscope import DashScopeHTTPProvider
from lumen.providers.media import image_to_data_url

VideoFamily = Literal["wan3", "wan2.7", "wan2.6-flash"]


@dataclass(frozen=True)
class VideoCapability:
    family: VideoFamily
    price_cny_per_second: dict[str, float]
    max_duration: int
    uses_media: bool
    supports_ratio: bool
    supports_silent_flag: bool


def video_capability(model: str) -> VideoCapability:
    if model == "wan3.0-video":
        return VideoCapability(
            family="wan3",
            price_cny_per_second={"480P": 0.30, "720P": 0.60, "1080P": 1.20},
            max_duration=30,
            uses_media=True,
            supports_ratio=True,
            supports_silent_flag=True,
        )
    if model == "wan3.0-video-prime":
        return VideoCapability(
            family="wan3",
            price_cny_per_second={"480P": 0.45, "720P": 0.90, "1080P": 1.80},
            max_duration=30,
            uses_media=True,
            supports_ratio=True,
            supports_silent_flag=True,
        )
    if model.startswith("wan2.7-i2v"):
        return VideoCapability(
            family="wan2.7",
            price_cny_per_second={"720P": 0.60, "1080P": 1.00},
            max_duration=15,
            uses_media=True,
            supports_ratio=False,
            supports_silent_flag=False,
        )
    if model == "wan2.6-i2v-flash":
        return VideoCapability(
            family="wan2.6-flash",
            price_cny_per_second={"720P": 0.15, "1080P": 0.25},
            max_duration=15,
            uses_media=False,
            supports_ratio=False,
            supports_silent_flag=True,
        )
    raise UnsupportedModelError(
        "no verified video payload capability is configured for this model",
        provider="dashscope",
        operation="select video model",
        code=model,
    )


class DashScopeVideoProvider(DashScopeHTTPProvider):
    endpoint = "services/aigc/video-generation/video-synthesis"
    max_download_bytes = 1024 * 1024 * 1024

    def __init__(self, *, model: str = "wan3.0-video", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.model = model
        self.capability = video_capability(model)

    def estimate_cost(self, *, resolution: str, duration: int) -> float:
        try:
            rate = self.capability.price_cny_per_second[resolution]
        except KeyError as exc:
            supported = ", ".join(sorted(self.capability.price_cny_per_second))
            raise ValueError(
                f"{self.model} does not support {resolution}; choose one of {supported}"
            ) from exc
        if not 2 <= duration <= self.capability.max_duration:
            raise ValueError(
                f"{self.model} duration must be between 2 and "
                f"{self.capability.max_duration} seconds"
            )
        return round(rate * duration, 2)

    def _payload(
        self,
        *,
        prompt: str,
        image_data_url: str,
        reference_type: str,
        resolution: str,
        duration: int,
        ratio: str,
        prompt_extend: bool,
        watermark: bool,
        seed: int | None,
    ) -> dict[str, object]:
        parameters: dict[str, object] = {
            "resolution": resolution,
            "duration": duration,
            "prompt_extend": prompt_extend,
            "watermark": watermark,
        }
        if seed is not None:
            if not 0 <= seed <= 2_147_483_647:
                raise ValueError("seed must be between 0 and 2147483647")
            parameters["seed"] = seed

        if self.capability.family == "wan3":
            if reference_type not in {"first_frame", "last_frame", "reference_image"}:
                raise ValueError("Wan3 local image input requires an image reference type")
            input_: dict[str, object] = {
                "prompt": prompt,
                "media": [{"type": reference_type, "url": image_data_url}],
            }
            parameters["ratio"] = ratio
            parameters["audio"] = False
        elif self.capability.family == "wan2.7":
            if reference_type not in {"first_frame", "last_frame"}:
                raise ValueError("Wan2.7 I2V supports first_frame or last_frame here")
            input_ = {
                "prompt": prompt,
                "media": [{"type": reference_type, "url": image_data_url}],
            }
        else:
            if reference_type != "first_frame":
                raise ValueError("Wan2.6 I2V accepts only a first-frame image")
            input_ = {"prompt": prompt, "img_url": image_data_url}
            parameters["audio"] = False
        return {"model": self.model, "input": input_, "parameters": parameters}

    def generate_from_image(
        self,
        prompt: str,
        image_path: str | Path,
        output_path: str | Path,
        *,
        resolution: str = "720P",
        duration: int = 5,
        ratio: str = "16:9",
        reference_type: str = "first_frame",
        prompt_extend: bool = True,
        watermark: bool = False,
        seed: int | None = None,
        api_key: str | None = None,
        poll_interval: float = 15,
        poll_timeout: float = 900,
    ) -> VideoResult:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        image = image_to_data_url(image_path)
        cost = self.estimate_cost(resolution=resolution, duration=duration)
        note = f"generate {duration}s {resolution} video"
        self.budget.check(cost, note=note)
        key = self._api_key(api_key)
        payload = self._payload(
            prompt=prompt,
            image_data_url=image.value,
            reference_type=reference_type,
            resolution=resolution,
            duration=duration,
            ratio=ratio,
            prompt_extend=prompt_extend,
            watermark=watermark,
            seed=seed,
        )
        created = self._request(
            "POST",
            self.endpoint,
            api_key=key,
            operation="create video task",
            payload=payload,
            asynchronous=True,
        )
        task_id = self._task_id(created)
        completed = self._poll_task(
            task_id,
            api_key=key,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        video_url = find_nested_string(completed, ("video_url",))
        if not video_url:
            raise ProviderResponseError(
                "successful video task is missing video_url",
                provider=self.provider_name,
                operation="complete video task",
            )
        response_id = request_id(completed) or request_id(created)
        usage = self._usage(completed)
        self.budget.charge(
            cost,
            agent="cinematographer",
            model=self.model,
            note=note,
            details={
                "request_id": response_id,
                "task_id": task_id,
                "resolution": resolution,
                "duration": duration,
            },
        )
        raw = download_bytes(
            self.session,
            video_url,
            provider=self.provider_name,
            operation="download video",
            api_key=key,
            timeout=self.download_timeout,
            max_bytes=self.max_download_bytes,
        )
        if not raw:
            raise ProviderResponseError(
                "downloaded video is empty",
                provider=self.provider_name,
                operation="download video",
            )
        path = atomic_write(output_path, raw)
        return VideoResult(
            path=path,
            model=self.model,
            task_id=task_id,
            cost_cny=cost,
            request_id=response_id,
            usage=usage,
        )
